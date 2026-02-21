from __future__ import annotations

import gc
import json
import re
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium
import torch
from PIL import Image
from transformers import (
    AutoModelForImageTextToText,
    AutoProcessor,
    Qwen3VLForConditionalGeneration,
)

GLM_MODEL_PATH = "zai-org/GLM-OCR"
QWEN_MODEL_PATH = "Qwen/Qwen3-VL-4B-Instruct"
TEXT_PROMPT = "Text Recognition:"


def _load_pdf_pages(pdf_path: Path, scale: float, max_pages: int | None) -> list[Image.Image]:
    doc = pdfium.PdfDocument(str(pdf_path))
    total = len(doc)
    limit = total if max_pages is None else min(max_pages, total)
    pages: list[Image.Image] = []
    for i in range(limit):
        pages.append(doc[i].render(scale=scale).to_pil().convert("RGB"))
    return pages


def _clean_decoded_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").strip()
    stop_markers = [
        "<|user|>",
        "<|assistant|>",
        "<|system|>",
        "<|endoftext|>",
        "</s>",
    ]
    for marker in stop_markers:
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[0].strip()
    cleaned = re.sub(r"<\|[^|>]+?\|>", "", cleaned).strip()
    return cleaned


def _run_glm(
    processor: AutoProcessor,
    model: AutoModelForImageTextToText,
    image: Image.Image,
    prompt_text: str,
    max_new_tokens: int,
    repetition_penalty: float,
    clean_output: bool,
) -> str:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt_text},
            ],
        }
    ]
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device)
    inputs.pop("token_type_ids", None)
    generated_ids = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        repetition_penalty=repetition_penalty,
    )
    decoded = processor.decode(
        generated_ids[0][inputs["input_ids"].shape[1] :],
        skip_special_tokens=True,
    )
    return _clean_decoded_text(decoded) if clean_output else decoded


def _qwen_prompt(page_num: int, source_text: str) -> str:
    return (
        f"Page {page_num}\n\n"
        "Clean the OCR text for audiobook narration.\n"
        "Return only cleaned markdown content that should be narrated.\n"
        "Do not include analysis, rules, explanations, or meta text.\n"
        "If you output anything outside the cleaned text, the response is invalid.\n"
        "Wrap the final answer exactly like this:\n"
        "<cleaned_markdown>\n"
        "...cleaned markdown...\n"
        "</cleaned_markdown>\n\n"
        "Requirements for cleaned content:\n"
        "- Fix broken words and line wraps.\n"
        "- Remove OCR junk and duplicates.\n"
        "- Keep heading/paragraph structure.\n"
        "- Convert every formula/equation into natural spoken text. Do NOT output LaTeX.\n"
        "- Keep variable names but verbalize operators. Example: x^2 + y^2 = z^2 -> "
        "'x squared plus y squared equals z squared'.\n"
        "- Example: p = W_num h(T) -> 'p equals W num times h of T'.\n"
        "- Example: sum_(t=0)^T log q(y_t) -> 'the sum from t equals zero to T of "
        "log q of y sub t'.\n"
        "- Preserve all important content on this page; do not summarize unless page is mostly references/tables/figures.\n"
        "- If page is mostly references/tables/figures, provide a short narration-friendly summary.\n\n"
        "OCR text starts below:\n"
        f"{source_text}\n"
    )


def _extract_cleaned_markdown(text: str) -> str:
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[-1].strip()
    match = re.search(
        r"<cleaned_markdown>\s*(.*?)\s*</cleaned_markdown>",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned_lines: list[str] = []
    skip_prefixes = (
        "we are given",
        "rules:",
        "analysis:",
        "steps:",
        "approach:",
        "plan:",
    )
    for line in lines:
        if line.strip().lower().startswith(skip_prefixes):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def _finalize_tts_markdown(text: str, page_num: int) -> str:
    cleaned = text.strip()
    cleaned = cleaned.replace("<cleaned_markdown>", "").replace("</cleaned_markdown>", "")
    cleaned = re.sub(
        rf"^\s*page\s+{page_num}\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE | re.MULTILINE,
    ).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def _run_qwen_cleanup(
    processor: AutoProcessor,
    model: Qwen3VLForConditionalGeneration,
    page_num: int,
    source_text: str,
    max_new_tokens: int,
) -> str:
    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You are an OCR cleanup engine. Output only final cleaned markdown.",
                }
            ],
        },
        {
            "role": "user",
            "content": [{"type": "text", "text": _qwen_prompt(page_num, source_text)}],
        },
    ]
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device)
    inputs.pop("token_type_ids", None)
    generated_ids = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
    )
    trimmed = generated_ids[:, inputs["input_ids"].shape[1] :]
    output = processor.batch_decode(
        trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    extracted = _extract_cleaned_markdown(output)
    return _finalize_tts_markdown(extracted, page_num=page_num)


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for match in re.finditer(r"[^.!?]+[.!?](?:\s+|$)", text, flags=re.DOTALL):
        start, end = match.span()
        if text[start:end].strip():
            spans.append((start, end))
    if not spans and text.strip():
        stripped_start = len(text) - len(text.lstrip())
        stripped_end = len(text.rstrip())
        spans.append((stripped_start, stripped_end))
    return spans


def _first_sentence(text: str) -> tuple[str | None, tuple[int, int] | None]:
    spans = _sentence_spans(text)
    if not spans:
        return None, None
    start, end = spans[0]
    return text[start:end].strip(), (start, end)


def _last_sentence(text: str) -> tuple[str | None, tuple[int, int] | None]:
    spans = _sentence_spans(text)
    if not spans:
        return None, None
    start, end = spans[-1]
    return text[start:end].strip(), (start, end)


def _leading_fragment_or_first_sentence(
    text: str, short_word_threshold: int = 4
) -> tuple[str | None, tuple[int, int] | None]:
    stripped_start = len(text) - len(text.lstrip())
    working = text[stripped_start:]
    if not working:
        return None, None
    first_punct = re.search(r"[.!?]", working)
    if first_punct:
        end = first_punct.end()
        fragment = working[:end].strip()
        words = len(re.findall(r"\b[\w-]+\b", fragment))
        if fragment and words <= short_word_threshold:
            return fragment, (stripped_start, stripped_start + end)
    return _first_sentence(text)


def _trailing_fragment_or_last_sentence(text: str) -> tuple[str | None, tuple[int, int] | None]:
    stripped_end = len(text.rstrip())
    if stripped_end == 0:
        return None, None
    working = text[:stripped_end]
    if not re.search(r"[.!?]\s*$", working):
        last_punct = None
        for m in re.finditer(r"[.!?]", working):
            last_punct = m
        start = 0 if last_punct is None else last_punct.end()
        fragment = working[start:].strip()
        if fragment:
            return fragment, (start, stripped_end)
    return _last_sentence(text)


def _extract_first_json_object(text: str) -> dict[str, Any] | None:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def _run_qwen_sentence_boundary_decision(
    processor: AutoProcessor,
    model: Qwen3VLForConditionalGeneration,
    prev_sentence: str,
    next_sentence: str,
    max_new_tokens: int,
) -> dict[str, str]:
    prompt = (
        "You are checking sentence continuity across a page break for TTS text.\n"
        "You will receive two sentences:\n"
        "- previous_page_last_sentence\n"
        "- next_page_first_sentence\n\n"
        "Task:\n"
        "- If they should stay separate, return no_change.\n"
        "- If they are actually one continued sentence or have duplicate overlap, return merge with a revised single sentence.\n"
        "- Prefer minimal edits: keep original wording and only repair the boundary join.\n"
        "- Do not rewrite whole paragraphs or restate nearby content.\n"
        "- Do not add any extra text.\n\n"
        "Return ONLY valid JSON with this schema:\n"
        "{\"action\":\"no_change|merge\",\"revised_sentence\":\"...\"}\n\n"
        f"previous_page_last_sentence: {prev_sentence}\n"
        f"next_page_first_sentence: {next_sentence}\n"
    )
    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": "Return strict JSON only."}],
        },
        {"role": "user", "content": [{"type": "text", "text": prompt}]},
    ]
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device)
    inputs.pop("token_type_ids", None)
    generated_ids = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
    )
    trimmed = generated_ids[:, inputs["input_ids"].shape[1] :]
    output = processor.batch_decode(
        trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    parsed = _extract_first_json_object(output)
    if not parsed:
        return {"action": "no_change", "revised_sentence": ""}
    action = str(parsed.get("action", "no_change")).strip().lower()
    revised_sentence = str(parsed.get("revised_sentence", "")).strip()
    if action not in {"no_change", "merge"}:
        action = "no_change"
    return {"action": action, "revised_sentence": revised_sentence}


def _run_qwen_sentence_boundary_decision_with_raw_fallback(
    processor: AutoProcessor,
    model: Qwen3VLForConditionalGeneration,
    cleaned_prev_sentence: str,
    cleaned_next_sentence: str,
    raw_prev_candidate: str,
    raw_next_candidate: str,
    max_new_tokens: int,
) -> dict[str, str]:
    prompt = (
        "You are checking sentence continuity across a page break for TTS text.\n"
        "You will receive cleaned boundary sentences and raw OCR boundary candidates.\n\n"
        "Task:\n"
        "- If no boundary fix is needed, return no_change.\n"
        "- If the boundary should be merged, return merge and provide one revised sentence.\n"
        "- You may use raw OCR candidates to recover dropped words at the page boundary.\n"
        "- Prefer minimal edits: keep cleaned_previous_page_last_sentence wording and only patch missing boundary words.\n"
        "- Do not rewrite whole paragraphs or restate nearby content.\n"
        "- Do not add any extra text.\n\n"
        "Return ONLY valid JSON with this schema:\n"
        "{\"action\":\"no_change|merge\",\"revised_sentence\":\"...\"}\n\n"
        f"cleaned_previous_page_last_sentence: {cleaned_prev_sentence}\n"
        f"cleaned_next_page_first_sentence: {cleaned_next_sentence}\n"
        f"raw_previous_page_boundary_candidate: {raw_prev_candidate}\n"
        f"raw_next_page_boundary_candidate: {raw_next_candidate}\n"
    )
    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": "Return strict JSON only."}],
        },
        {"role": "user", "content": [{"type": "text", "text": prompt}]},
    ]
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device)
    inputs.pop("token_type_ids", None)
    generated_ids = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
    )
    trimmed = generated_ids[:, inputs["input_ids"].shape[1] :]
    output = processor.batch_decode(
        trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    parsed = _extract_first_json_object(output)
    if not parsed:
        return {"action": "no_change", "revised_sentence": ""}
    action = str(parsed.get("action", "no_change")).strip().lower()
    revised_sentence = str(parsed.get("revised_sentence", "")).strip()
    if action not in {"no_change", "merge"}:
        action = "no_change"
    return {"action": action, "revised_sentence": revised_sentence}


def _normalize_for_match(text: str) -> str:
    compact = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", compact).strip().lower()


def _paragraph_blocks(text: str) -> list[str]:
    blocks = re.split(r"\n\s*\n+", text.strip())
    return [b.strip() for b in blocks if b.strip()]


def _dedupe_redundant_sentences(text: str) -> str:
    blocks = _paragraph_blocks(text)
    if len(blocks) < 2:
        return text
    out_blocks: list[str] = []
    i = 0
    while i < len(blocks):
        current = blocks[i]
        if i < len(blocks) - 1:
            nxt = blocks[i + 1]
            norm_cur = _normalize_for_match(current)
            norm_nxt = _normalize_for_match(nxt)
            if norm_cur and norm_nxt:
                if norm_cur == norm_nxt:
                    out_blocks.append(current)
                    i += 2
                    continue
                if norm_nxt.startswith(norm_cur) and len(norm_nxt) >= int(len(norm_cur) * 1.1):
                    out_blocks.append(nxt)
                    i += 2
                    continue
                if norm_cur.startswith(norm_nxt) and len(norm_cur) >= int(len(norm_nxt) * 1.1):
                    out_blocks.append(current)
                    i += 2
                    continue
        out_blocks.append(current)
        i += 1
    deduped = "\n\n".join(out_blocks).strip()
    return deduped if deduped else text


def _split_sentences_for_dedupe(paragraph: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(\"])", paragraph.strip())
    return [p.strip() for p in parts if p.strip()]


def _dedupe_inline_sentence_expansions(text: str) -> str:
    paragraphs = _paragraph_blocks(text)
    if not paragraphs:
        return text
    out_paragraphs: list[str] = []
    for para in paragraphs:
        sents = _split_sentences_for_dedupe(para)
        if len(sents) < 2:
            out_paragraphs.append(para)
            continue
        out_sents: list[str] = []
        i = 0
        while i < len(sents):
            cur = sents[i]
            if i < len(sents) - 1:
                nxt = sents[i + 1]
                norm_cur = _normalize_for_match(cur)
                norm_nxt = _normalize_for_match(nxt)
                if norm_cur and norm_nxt:
                    if norm_nxt.startswith(norm_cur) and len(norm_nxt) >= int(len(norm_cur) * 1.1):
                        out_sents.append(nxt)
                        i += 2
                        continue
                    if norm_cur == norm_nxt:
                        out_sents.append(cur)
                        i += 2
                        continue
            out_sents.append(cur)
            i += 1
        out_paragraphs.append(" ".join(out_sents))
    rebuilt = "\n\n".join(out_paragraphs).strip()
    return rebuilt if rebuilt else text


def _release_model(model: Any) -> None:
    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def process_pdf_to_tts_markdown(
    input_pdf: str | Path,
    output_markdown: str | Path,
    *,
    temp_dir: str | Path = "temp",
    write_artifacts: bool = False,
    max_pages: int | None = None,
    scale: float = 2.0,
    glm_model: str = GLM_MODEL_PATH,
    qwen_model: str = QWEN_MODEL_PATH,
    ocr_max_new_tokens: int = 4096,
    qwen_max_new_tokens: int = 4096,
    qwen_boundary_max_new_tokens: int = 768,
    ocr_repetition_penalty: float = 1.05,
    clean_output: bool = True,
) -> Path:
    input_path = Path(input_pdf)
    output_path = Path(output_markdown)
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = Path(temp_dir)
    temp_path.mkdir(parents=True, exist_ok=True)

    pages = _load_pdf_pages(input_path, scale=scale, max_pages=max_pages)
    glm_processor = AutoProcessor.from_pretrained(glm_model)
    glm_model_obj = AutoModelForImageTextToText.from_pretrained(
        pretrained_model_name_or_path=glm_model,
        torch_dtype="auto",
        device_map="auto",
    )

    raw_json_pages: list[dict[str, Any]] = []
    raw_md_lines: list[str] = []
    for idx, page_img in enumerate(pages, start=1):
        raw_output = _run_glm(
            processor=glm_processor,
            model=glm_model_obj,
            image=page_img,
            prompt_text=TEXT_PROMPT,
            max_new_tokens=ocr_max_new_tokens,
            repetition_penalty=ocr_repetition_penalty,
            clean_output=clean_output,
        )
        raw_md_lines.append(f"## Page {idx}")
        raw_md_lines.append(raw_output.strip())
        raw_md_lines.append("")
        raw_json_pages.append({"page": idx, "task": "text", "raw_output": raw_output})

    if write_artifacts:
        source_stem = input_path.stem
        (temp_path / f"{source_stem}_text.md").write_text(
            "\n".join(raw_md_lines).strip() + "\n", encoding="utf-8"
        )
        (temp_path / f"{source_stem}_text.json").write_text(
            json.dumps(
                {
                    "source": str(input_path),
                    "task": "text",
                    "prompt": TEXT_PROMPT,
                    "num_pages": len(raw_json_pages),
                    "pages": raw_json_pages,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    _release_model(glm_model_obj)
    qwen_processor = AutoProcessor.from_pretrained(qwen_model)
    qwen_model_obj = Qwen3VLForConditionalGeneration.from_pretrained(
        qwen_model, dtype="auto", device_map="auto"
    )

    raw_page_texts = [str(p["raw_output"]) for p in raw_json_pages]
    stitched_tts_pages: list[str] = []
    cleaned_pages_payload: list[dict[str, Any]] = []
    for idx, page in enumerate(raw_json_pages):
        page_num = int(page["page"])
        cleaned = _run_qwen_cleanup(
            processor=qwen_processor,
            model=qwen_model_obj,
            page_num=page_num,
            source_text=raw_page_texts[idx],
            max_new_tokens=qwen_max_new_tokens,
        )
        cleaned = _dedupe_redundant_sentences(cleaned)
        cleaned = _dedupe_inline_sentence_expansions(cleaned)
        stitched_tts_pages.append(cleaned)
        cleaned_pages_payload.append(
            {
                "page": page_num,
                "source_text": raw_page_texts[idx],
                "tts_markdown": cleaned,
            }
        )

    boundary_debug: list[dict[str, Any]] = []
    for i in range(len(stitched_tts_pages) - 1):
        left_text = stitched_tts_pages[i]
        right_text = stitched_tts_pages[i + 1]
        left_sentence, left_span = _trailing_fragment_or_last_sentence(left_text)
        right_sentence, right_span = _leading_fragment_or_first_sentence(right_text)
        raw_left = raw_page_texts[i]
        raw_right = raw_page_texts[i + 1]
        raw_left_candidate, _ = _trailing_fragment_or_last_sentence(raw_left)
        raw_right_candidate, _ = _leading_fragment_or_first_sentence(raw_right)
        entry: dict[str, Any] = {
            "left_page": i + 1,
            "right_page": i + 2,
            "left_last_sentence_before": left_sentence,
            "right_first_sentence_before": right_sentence,
            "decision_action_final": "not_run",
            "decision_revised_sentence_final": "",
            "applied": False,
            "merge_source": "",
        }
        if not left_sentence or not left_span or not right_sentence or not right_span:
            entry["decision_action_final"] = "no_change"
            boundary_debug.append(entry)
            continue

        decision = _run_qwen_sentence_boundary_decision(
            processor=qwen_processor,
            model=qwen_model_obj,
            prev_sentence=left_sentence,
            next_sentence=right_sentence,
            max_new_tokens=qwen_boundary_max_new_tokens,
        )
        final_decision = dict(decision)
        merge_source = "cleaned"
        if (
            final_decision.get("action") != "merge"
            and raw_left_candidate
            and raw_right_candidate
        ):
            fallback_decision = _run_qwen_sentence_boundary_decision_with_raw_fallback(
                processor=qwen_processor,
                model=qwen_model_obj,
                cleaned_prev_sentence=left_sentence,
                cleaned_next_sentence=right_sentence,
                raw_prev_candidate=raw_left_candidate,
                raw_next_candidate=raw_right_candidate,
                max_new_tokens=qwen_boundary_max_new_tokens,
            )
            if fallback_decision.get("action") == "merge":
                final_decision = fallback_decision
                merge_source = "raw_fallback"

        entry["decision_action_final"] = final_decision.get("action", "no_change")
        entry["decision_revised_sentence_final"] = final_decision.get(
            "revised_sentence", ""
        )
        if final_decision.get("action") != "merge":
            boundary_debug.append(entry)
            continue
        revised = final_decision.get("revised_sentence", "").strip()
        if not revised:
            boundary_debug.append(entry)
            continue

        left_start, left_end = left_span
        left_prefix = left_text[:left_start]
        left_suffix = left_text[left_end:]
        if left_prefix and not left_prefix.endswith((" ", "\n")) and revised and revised[0].isalnum():
            left_prefix += " "
        stitched_tts_pages[i] = (left_prefix + revised + left_suffix).strip()

        right_start, right_end = right_span
        cleaned_right_candidate = right_sentence.strip()
        right_words = len(re.findall(r"\b[\w-]+\b", cleaned_right_candidate))
        normalized_revised = _normalize_for_match(revised)
        normalized_right_candidate = _normalize_for_match(cleaned_right_candidate)
        should_remove_right = (
            merge_source == "cleaned"
            or (
                cleaned_right_candidate
                and normalized_right_candidate in normalized_revised
                and (
                    right_words <= 6
                    or normalized_revised.startswith(_normalize_for_match(left_sentence))
                )
            )
        )
        if (
            should_remove_right
            and cleaned_right_candidate
            and right_text[right_start:right_end].strip() == cleaned_right_candidate
        ):
            stitched_tts_pages[i + 1] = (
                right_text[:right_start] + right_text[right_end:]
            ).strip()

        entry["applied"] = True
        entry["merge_source"] = merge_source
        boundary_debug.append(entry)

    for idx, page_text in enumerate(stitched_tts_pages):
        page_text = _dedupe_redundant_sentences(page_text)
        page_text = _dedupe_inline_sentence_expansions(page_text)
        stitched_tts_pages[idx] = page_text
        cleaned_pages_payload[idx]["tts_markdown"] = page_text

    _release_model(qwen_model_obj)

    final_md = "\n\n".join([p for p in stitched_tts_pages if p.strip()]).strip() + "\n"
    output_path.write_text(final_md, encoding="utf-8")

    if write_artifacts:
        source_stem = input_path.stem
        (temp_path / f"{source_stem}_tts.json").write_text(
            json.dumps(
                {
                    "source": str(input_path),
                    "task": "tts_cleanup",
                    "num_pages": len(cleaned_pages_payload),
                    "pages": cleaned_pages_payload,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (temp_path / f"{source_stem}_boundary_debug.json").write_text(
            json.dumps(
                {
                    "source": str(input_path),
                    "num_boundaries": len(boundary_debug),
                    "boundaries": boundary_debug,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    return output_path
