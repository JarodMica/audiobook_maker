import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _src_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_json_params(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in params file, got {type(data).__name__}")
    return data


def _extract_json_object(text: str) -> dict | None:
    if not text:
        return None

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    starts = [idx for idx, char in enumerate(text) if char == "{"]
    for start in reversed(starts):
        candidate = text[start:].strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def _normalize_tts_name(name: str) -> str:
    lower_name = name.strip().lower()
    if "styletts2" in lower_name:
        return "styletts2"
    if "gpt" in lower_name and "sovits" in lower_name:
        return "gpt_sovits"
    if "f5" in lower_name:
        return "f5tts"
    if "pyttsx3" in lower_name:
        return "pyttsx3"
    if "tortoise" in lower_name:
        return "tortoise"
    if "vibevoice" in lower_name:
        return "vibevoice"
    if "xtts" in lower_name:
        return "xtts"
    return lower_name.replace(" ", "_")


def _discover_tts_engines(repo: Path) -> tuple[list[str], list[str]]:
    config_path = repo / "configs" / "tts_config.json"
    config = _load_json_params(config_path)
    discovered = []
    expected_skip = []
    for engine in config.get("tts_engines", []):
        raw_name = str(engine.get("name", ""))
        normalized = _normalize_tts_name(raw_name)
        if "in progress" in raw_name.lower():
            expected_skip.append(normalized)
            continue
        discovered.append(normalized)
    return sorted(set(discovered)), sorted(set(expected_skip))


def _run_single_case_in_process(
    tts_engines_module,
    engine_name: str,
    voice_params: dict,
    output_path: Path,
    text: str,
    case_name: str = "default",
) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    load_success = False
    returned_audio_path_pass = False
    file_size_pass = False
    returned_audio_path = None
    error_text = None

    try:
        tts_engine = tts_engines_module.load_tts_engine(engine_name, **voice_params)
        load_success = True

        returned_audio_path = tts_engines_module.generate_audio(
            tts_engine=tts_engine,
            sentence=text,
            voice_parameters=voice_params,
            tts_engine_name=engine_name,
            audio_path=str(output_path),
        )

        if isinstance(returned_audio_path, str) and returned_audio_path.strip():
            returned_audio_path_pass = True
        elif returned_audio_path:
            returned_audio_path_pass = True

        if output_path.exists() and output_path.stat().st_size > 0:
            file_size_pass = True
    except Exception as exc:  # pragma: no cover - smoke script
        error_text = str(exc)

    return {
        "engine": engine_name,
        "case": case_name,
        "checks": {
            "load_success": load_success,
            "returned_audio_path": returned_audio_path_pass,
            "output_file_nonempty": file_size_pass,
        },
        "score": f"{sum([load_success, returned_audio_path_pass, file_size_pass])}/3",
        "output_path": str(output_path),
        "returned_audio_path": returned_audio_path,
        "error": error_text,
        "status": (
            "passed"
            if all([load_success, returned_audio_path_pass, file_size_pass])
            else "failed"
        ),
    }


def _safe_case_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", value)


def _invoke_worker_subprocess(
    repo: Path,
    script_path: Path,
    python_executable: str,
    engine_name: str,
    case_name: str,
    voice_params: dict,
    output_path: Path,
    text: str,
    timeout_sec: int,
    temp_dir: Path,
) -> dict:
    params_path = temp_dir / f"params_{engine_name}_{_safe_case_token(case_name)}.json"
    params_path.write_text(json.dumps(voice_params), encoding="utf-8")

    command = [
        python_executable,
        str(script_path),
        "--_worker",
        "--engine",
        engine_name,
        "--case",
        case_name,
        "--params-json",
        str(params_path),
        "--output",
        str(output_path),
        "--text",
        text,
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "engine": engine_name,
            "case": case_name,
            "checks": {
                "load_success": False,
                "returned_audio_path": False,
                "output_file_nonempty": False,
            },
            "score": "0/3",
            "output_path": str(output_path),
            "returned_audio_path": None,
            "error": f"Timed out after {timeout_sec} seconds",
            "status": "timeout",
        }

    parsed = _extract_json_object(completed.stdout)
    if parsed is None:
        stderr_tail = (completed.stderr or "").strip()[-1200:]
        return {
            "engine": engine_name,
            "case": case_name,
            "checks": {
                "load_success": False,
                "returned_audio_path": False,
                "output_file_nonempty": False,
            },
            "score": "0/3",
            "output_path": str(output_path),
            "returned_audio_path": None,
            "error": (
                f"Worker returned code {completed.returncode} without parseable JSON. "
                f"Stderr tail: {stderr_tail}"
            ),
            "status": "crash",
        }

    status = parsed.get("status", "failed")
    if completed.returncode != 0 and status == "passed":
        status = "failed"
    parsed["status"] = status
    return parsed


def _count_status(results: list[dict], status: str) -> int:
    return sum(1 for item in results if item.get("status") == status)


def _build_run_all_cases(
    repo: Path, text: str
) -> tuple[list[dict], list[str], list[str], list[str], list[str], list[dict]]:
    defaults_path = repo / "src" / "unit_tests" / "engine_validation_defaults.json"
    defaults = _load_json_params(defaults_path)
    defaults_tts = defaults.get("tts", {})

    discovered, expected_skip = _discover_tts_engines(repo)
    new_in_config = sorted([name for name in discovered if name not in defaults_tts])
    stale_in_defaults = sorted([name for name in defaults_tts.keys() if name not in discovered])
    cases = []
    preflight_results = []

    for engine_name in discovered:
        if engine_name not in defaults_tts:
            preflight_results.append(
                {
                    "engine": engine_name,
                    "case": "default",
                    "checks": {
                        "load_success": False,
                        "returned_audio_path": False,
                        "output_file_nonempty": False,
                    },
                    "score": "0/3",
                    "output_path": "",
                    "returned_audio_path": None,
                    "error": (
                        f"Missing pinned defaults for engine '{engine_name}' in "
                        "src/unit_tests/engine_validation_defaults.json"
                    ),
                    "status": "preflight_failed",
                }
            )
            continue

        if engine_name == "gpt_sovits":
            matrix = defaults_tts["gpt_sovits"].get("matrix", {})
            versions = matrix.get("versions", [])
            languages = matrix.get("languages", [])
            base_params = defaults_tts["gpt_sovits"].get("base_params", {})
            for version in versions:
                for language in languages:
                    params = dict(base_params)
                    params["gpt_sovits_version"] = version
                    params["gpt_sovits_ref_lang"] = language
                    params["gpt_sovits_output_lang"] = language
                    case_name = f"{version}_{language}"
                    output_path = repo / "output_test" / f"engine_smoke_gpt_sovits_{case_name}.wav"
                    cases.append(
                        {
                            "engine": "gpt_sovits",
                            "case": case_name,
                            "params": params,
                            "output_path": output_path,
                            "text": text,
                        }
                    )
        else:
            params = defaults_tts[engine_name].get("params", {})
            output_path = repo / "output_test" / f"engine_smoke_{engine_name}.wav"
            cases.append(
                {
                    "engine": engine_name,
                    "case": "default",
                    "params": params,
                    "output_path": output_path,
                    "text": text,
                }
            )

    return (
        cases,
        expected_skip,
        discovered,
        new_in_config,
        stale_in_defaults,
        preflight_results,
    )


def _run_all(repo: Path, text: str, timeout_sec: int) -> int:
    script_path = Path(__file__).resolve()
    python_executable = sys.executable
    (
        cases,
        expected_skip,
        discovered,
        new_in_config,
        stale_in_defaults,
        preflight_results,
    ) = _build_run_all_cases(repo, text)

    results = list(preflight_results)
    total_cases = len(cases)
    start_time = time.time()

    progress_bar = None
    try:
        from tqdm import tqdm  # type: ignore

        progress_bar = tqdm(total=total_cases, desc="Engine cases", unit="case")
    except Exception:
        progress_bar = None

    if progress_bar is None:
        print(
            f"Starting engine validation: {total_cases} case(s), "
            f"{len(preflight_results)} preflight issue(s).",
            flush=True,
        )

    with tempfile.TemporaryDirectory(prefix="validate_tts_worker_") as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        for index, case in enumerate(cases, start=1):
            label = f"{case['engine']}:{case['case']}"
            if progress_bar is None:
                print(f"[{index}/{total_cases}] START {label}", flush=True)

            result = _invoke_worker_subprocess(
                repo=repo,
                script_path=script_path,
                python_executable=python_executable,
                engine_name=case["engine"],
                case_name=case["case"],
                voice_params=case["params"],
                output_path=case["output_path"],
                text=case["text"],
                timeout_sec=timeout_sec,
                temp_dir=temp_dir,
            )
            results.append(result)

            if progress_bar is not None:
                progress_bar.update(1)
                progress_bar.set_postfix_str(
                    f"{label} -> {result['status']}",
                    refresh=True,
                )
            else:
                elapsed = int(time.time() - start_time)
                passed = _count_status(results, "passed")
                failed = _count_status(results, "failed")
                timeout = _count_status(results, "timeout")
                crash = _count_status(results, "crash")
                preflight = _count_status(results, "preflight_failed")
                print(
                    f"[{index}/{total_cases}] DONE {label} -> {result['status']} "
                    f"(elapsed={elapsed}s, passed={passed}, failed={failed}, "
                    f"timeout={timeout}, crash={crash}, preflight_failed={preflight})",
                    flush=True,
                )

    if progress_bar is not None:
        progress_bar.close()
        print(
            f"Engine validation completed in {int(time.time() - start_time)}s.",
            flush=True,
        )

    summary = {
        "mode": "run_all",
        "python_executable": python_executable,
        "engines_tested": discovered,
        "expected_skip": expected_skip,
        "reconciliation": {
            "new_in_config": new_in_config,
            "stale_in_defaults": stale_in_defaults,
        },
        "counts": {
            "passed": sum(1 for item in results if item["status"] == "passed"),
            "failed": sum(1 for item in results if item["status"] == "failed"),
            "timeout": sum(1 for item in results if item["status"] == "timeout"),
            "crash": sum(1 for item in results if item["status"] == "crash"),
            "preflight_failed": sum(
                1 for item in results if item["status"] == "preflight_failed"
            ),
            "total": len(results),
        },
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    return (
        0
        if all(
            summary["counts"][key] == 0
            for key in ["failed", "timeout", "crash", "preflight_failed"]
        )
        else 1
    )


def _run_single_from_args(repo: Path, args) -> int:
    script_path = Path(__file__).resolve()
    python_executable = sys.executable

    engine_name = args.engine.lower()
    case_name = args.case if args.case else "default"
    output_path = (repo / args.output).resolve()

    if args.params_json:
        voice_params = _load_json_params((repo / args.params_json).resolve())
    else:
        defaults_path = repo / "src" / "unit_tests" / "engine_validation_defaults.json"
        defaults = _load_json_params(defaults_path)
        tts_defaults = defaults.get("tts", {})
        if engine_name == "gpt_sovits":
            voice_params = dict(tts_defaults.get("gpt_sovits", {}).get("base_params", {}))
        else:
            voice_params = dict(tts_defaults.get(engine_name, {}).get("params", {}))
        if not voice_params:
            raise ValueError(
                f"No defaults found for engine '{engine_name}'. Provide --params-json or update "
                "src/unit_tests/engine_validation_defaults.json."
            )

    with tempfile.TemporaryDirectory(prefix="validate_tts_single_") as temp_dir_raw:
        result = _invoke_worker_subprocess(
            repo=repo,
            script_path=script_path,
            python_executable=python_executable,
            engine_name=engine_name,
            case_name=case_name,
            voice_params=voice_params,
            output_path=output_path,
            text=args.text,
            timeout_sec=args.timeout_sec,
            temp_dir=Path(temp_dir_raw),
        )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


def _run_worker(repo: Path, args) -> int:
    src = _src_root()
    sys.path.insert(0, str(src))
    import tts_engines  # pylint: disable=import-error

    engine_name = args.engine.lower()
    if not args.params_json:
        raise ValueError("Worker mode requires --params-json.")
    voice_params = _load_json_params((repo / args.params_json).resolve())

    result = _run_single_case_in_process(
        tts_engines_module=tts_engines,
        engine_name=engine_name,
        voice_params=voice_params,
        output_path=(repo / args.output).resolve(),
        text=args.text,
        case_name=args.case if args.case else "default",
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke test TTS engines. Default behavior runs all configured engines."
    )
    parser.add_argument(
        "--engine",
        default="",
        help="Optional: run only one engine by dispatch name. If omitted, runs all engines.",
    )
    parser.add_argument(
        "--output",
        default="engine_smoke.wav",
        help="Output audio path for single-engine mode.",
    )
    parser.add_argument(
        "--params-json",
        default="",
        help="Optional JSON file containing voice parameters override (single-engine mode).",
    )
    parser.add_argument(
        "--text",
        default="This is a generic engine smoke test sentence.",
        help="Test sentence used for generation.",
    )
    parser.add_argument(
        "--case",
        default="default",
        help="Case label used in output JSON.",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=900,
        help="Per-case timeout in seconds for subprocess worker runs.",
    )
    parser.add_argument(
        "--_worker",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    repo = _repo_root()
    if args._worker:
        return _run_worker(repo, args)
    if args.engine.strip():
        return _run_single_from_args(repo, args)
    return _run_all(repo, args.text, args.timeout_sec)


if __name__ == "__main__":
    raise SystemExit(main())  
