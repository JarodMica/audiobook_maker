# Author Notes

## Purpose
Define strict documentation constraints for `audiobook_maker` so updates stay aligned with the intended architecture and engine-modular design.

## Notes
- Treat this project as strict MVC:
- `src/view.py` owns GUI rendering, widgets, UI state, and user-facing interactions.
- `src/model.py` owns business logic, processing, persistence, and generation workflows.
- `src/controller.py` owns coordination/orchestration between view and model.
- Always document signal flow between view and controller when relevant:
- Show which view signals trigger controller actions.
- Show how controller reports progress/completion/errors back to view.
- Document controller-to-model calls for logic execution, then model-to-view outcomes via controller.
- Prioritize first-party code depth in `src/`, `configs/`, and engine adapter files.
- Emphasize the modular engine architecture as a core project concern:
- UI engine parameter forms are config-driven from `configs/tts_config.json` and `configs/s2s_config.json`.
- TTS runtime logic belongs in `src/tts_engines.py`.
- S2S runtime logic belongs in `src/s2s_engines.py`.
- Keep docs explicit about how config keys map to runtime parameters and behavior.
- When documenting inference parameters, note why some slider values are divided by `step`/a fixed number:
- PySide slider controls are integer-based, so decimal runtime values are represented by scaled integers in the UI and converted back in adapter logic.
- Cover vendored `modules/` at high level only unless explicitly requested.
- For `docs/MODEL.md`, `docs/VIEW.md`, and `docs/CONTROLLER.md`, use a full function inventory format:
- Map all discovered functions/methods present in the source file (do not provide only a subset).
- For each function, document every parameter with a variable-level description and expected type when inferable.
- Keep these files as implementation inventories, not high-level trackers.
- Do not keep per-file \"update tracker\" sections in these docs.
- Preserve the naming distinction between `speaker_settings` and `voice_parameters` in documentation:
- `speaker_settings` is the MVC-layer per-speaker configuration object.
- `voice_parameters` is the inference-call parameter dictionary used inside adapter generation functions.
- Treat this as intentional architecture, not inconsistent naming.
- Keep project release/history notes in `changelog.md`.
- Keep AI-generated documentation/session reconciliation notes in `AI_CHANGELOG.md` (do not append those to `changelog.md` unless explicitly requested).
- Do not modify this file unless explicitly asked to update author notes.

## Issues
- GPT-SoVITS validation matrix has known inference failures despite successful model load:
- `all_ko` cases (`v4_all_ko`, `v3_all_ko`, `v2_all_ko`, `v1_all_ko`) fail in runtime Korean processing with `exceptions must derive from BaseException` after `eunjeon` path checks.
- `v1_all_ja` fails during CUDA inference with `device-side assert triggered` in GPT-SoVITS decode/attention path.
- Treat these as engine/runtime-path issues for specific version/language combinations, not preflight path/config missing-file issues.
