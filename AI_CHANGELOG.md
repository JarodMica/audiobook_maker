# AI Changelog Notes

## 2026-02-18 Add-Engine Folder Section Simplification
- Simplified `docs/ADDING_INFERENCE_ENGINES.md` folder prerequisite section to remove rationale-heavy text.
- Kept only:
  - concise descriptions of `engines/<engine_key>/` and `voices/<engine_key>/`
  - direct step-by-step instructions for creating and wiring those folders.

## 2026-02-18 Add-Engine Folder Rationale Expansion
- Expanded `docs/ADDING_INFERENCE_ENGINES.md` filesystem prerequisite guidance with project-specific rationale.
- Added explicit linkage to:
  - GUI combobox path discovery in `src/view.py` (`create_widget_for_parameter`, `get_combobox_items`)
  - runtime adapter path resolution in `src/tts_engines.py` and `src/s2s_engines.py`
  - upload destination behavior in `src/model.py` `process_upload_items(...)`
- Clarified the distinct role of `engines/<engine_key>/` (model/runtime artifacts) vs `voices/<engine_key>/` (reference voice assets), and documented common failure modes when one side is missing.

## 2026-02-18 Add-Engine Filesystem Prerequisite Note
- Updated `docs/ADDING_INFERENCE_ENGINES.md` to document required folder setup when integrating new engines:
  - `engines/<engine_key>/`
  - `voices/<engine_key>/`
- Added rationale tying this requirement to config-driven combobox discovery in `src/view.py`.
- Extended the compatibility checklist to include filesystem path validation for new engine integrations.

## 2026-02-18 Inference Engines Doc Scope Cleanup
- Documentation update for inference engines:
  - Reworked `docs/INFERENCE_ENGINES.md` to cover all currently wired TTS/S2S engines, not only VibeVoice.
  - Added per-engine summaries (purpose, key config attributes, load/generate or load/process runtime flow).
  - Removed VibeVoice-specific implementation fix notes from that document to keep it focused on engine usage and mapping.

## 2026-02-18 VibeVoice Compatibility Patch (Modules)
- Patched `modules/VibeVoice-API` for inference stability on Windows:
  - Fixed `from __future__ import annotations` placement in `modules/VibeVoice-API/vibevoice/infer_api.py`.
  - Added `modules/VibeVoice-API/vibevoice/runtime_compat.py` with:
    - temporary DeepSpeed discovery suppression during transformers import
    - Diffusers PEFT gate disable helper (`_CHECK_PEFT=0`) for inference path.
  - Applied compatibility wrapper in:
    - `modules/VibeVoice-API/vibevoice/modular/modeling_vibevoice.py`
    - `modules/VibeVoice-API/vibevoice/modular/modeling_vibevoice_inference.py`
    - `modules/VibeVoice-API/vibevoice/modular/modeling_vibevoice_streaming.py`
    - `modules/VibeVoice-API/vibevoice/modular/modeling_vibevoice_streaming_inference.py`
    - `modules/VibeVoice-API/vibevoice/modular/modular_vibevoice_diffusion_head.py`
    - `modules/VibeVoice-API/vibevoice/modular/modular_vibevoice_tokenizer.py`
  - Enabled Diffusers PEFT check bypass before scheduler imports in:
    - `modules/VibeVoice-API/vibevoice/schedule/dpm_solver.py`.
- Reinstalled VibeVoice package from local modules path:
  - `.\\venv\\Scripts\\python.exe -m pip install -e modules/VibeVoice-API`
- Validation commands run:
  - `.\\venv\\Scripts\\python.exe -c "import vibevoice.infer_api as m; print('infer_api_ok', hasattr(m,'VibeVoiceInferencer'))"` -> pass
  - `.\\venv\\Scripts\\python.exe src\\unit_tests\\validate_tts_engine.py --engine vibevoice --output voices\\vibevoice\\validation_smoke\\vibevoice_smoke.wav` -> pass (`3/3`)

## 2026-02-17 VibeVoice TTS Engine Integration
- Added `vibevoice` TTS engine wiring in `src/tts_engines.py`:
  - New dispatch routes in `generate_audio(...)` and `load_tts_engine(...)`.
  - Added `load_with_vibevoice(...)` and `generate_with_vibevoice(...)`.
  - Added guarded `vibevoice.infer_api` import handling with explicit runtime error path.
- Added `vibevoice` engine schema to `configs/tts_config.json` with model/voice/device and generation controls.
- Extended smoke validator `src/unit_tests/validate_tts_engine.py` with built-in defaults for `--engine vibevoice`.
- Updated `docs/INFERENCE_ENGINES.md` with VibeVoice key, required params, load/generate flow, and caveats.
- Validation commands run:
  - `.\\venv\\Scripts\\python.exe src\\unit_tests\\validate_tts_engine.py --engine vibevoice --output voices\\vibevoice\\validation_smoke\\vibevoice_smoke.wav`
  - Result: fails currently due upstream VibeVoice package import/runtime blockers in `venv` (`infer_api.py` syntax error, DeepSpeed Windows `df` dependency path, and `peft>=0.17.0` requirement while environment had `peft==0.15.2`).

## 2026-02-17 Documentation Verification Pass 2
- Inconsistencies found:
  - `README.md` referenced `config\setting.yaml`; actual repo path is `configs/settings.yaml`.
  - `docs/OPERATIONS.md` stated documentation updates should be logged in `changelog.md`, which conflicted with current author-note policy for AI-generated doc session notes.
- Documentation updates applied:
  - Updated GPT-SoVITS install note path and wording in `README.md`.
  - Updated documentation maintenance rule in `docs/OPERATIONS.md` to separate `changelog.md` (project history) and `AI_CHANGELOG.md` (AI doc sessions).

## 2026-02-17 Step-Key Clarification Update
- Updated `docs/ADDING_INFERENCE_ENGINES.md` `slider` type section with a detailed explanation of what `step` means.
- Added explicit integer-UI to decimal-runtime conversion guidance and a concrete numeric example.

## 2026-02-17 Add-Engine Guide Schema-Focus Pass
- Removed `Small Debugging Session`, `Anti-Patterns`, and `Confusion Map` sections from `docs/ADDING_INFERENCE_ENGINES.md`.
- Removed the real-project walkthrough section to improve guide flow.
- Reworked the document to focus on a complete config schema reference driven by actual `src/view.py` behavior.
- Added explicit support matrix for parameter `type` values and the available/expected keys for each type.
- Added detailed combobox option-resolution behavior (`look_for`, `folder_path`, `file_filter`, `custom_options`, `relies_on`, none-option keys).
- Expanded upload schema documentation for `upload_params` and mode-specific field handling.

## 2026-02-17 Add-Engine Guide Concrete Walkthrough Pass
- Expanded `docs/ADDING_INFERENCE_ENGINES.md` with a real project walkthrough using the GPT-SoVITS integration path.
- Added a minimal required keys checklist for TTS/S2S config compatibility and adapter-side requirements.
- Added explicit clarification that `speaker_settings` (MVC) and `voice_parameters` (inference adapter call context) are intentionally different names with linked roles.
- Added anti-pattern guidance to prevent hardcoded widget/parameter coupling and dispatch bypasses.

## 2026-02-17 Add-Engine Guide Clarification Pass
- Expanded `docs/ADDING_INFERENCE_ENGINES.md` with a conceptual step-by-step trace showing how config attributes move from GUI view into model and adapter runtime calls.
- Added a concrete single-parameter journey example (`mytts_speed`) to show slider value capture and `step` normalization before inference.
- Added explicit note that TTS and S2S follow the same integration pattern (different runtime function names only).
- Added confusion map and a short optional debugging flow for integration troubleshooting.

## 2026-02-17 Add-Engine Guide Update
- Added `docs/ADDING_INFERENCE_ENGINES.md` as a dedicated conceptual + implementation guide for integrating new TTS/S2S inference engines.
- Documented the required config-driven GUI schema path and adapter implementation path (`load_*` plus `generate/process_*`).
- Updated `README.md` documentation index to include the new guide.

## 2026-02-17 Documentation Verification
- Inconsistencies found:
  - No new doc/code mismatches detected across `README.md`, `docs/`, and root markdown docs in this verification pass.
- Verification checks performed:
  - Confirmed full function coverage in `docs/MODEL.md`, `docs/VIEW.md`, `docs/CONTROLLER.md`, and `docs/INFERENCE_ENGINES.md` against current source files.
  - Confirmed no stale references to removed `docs/API.md` outside historical changelog notes.
- Documentation updates applied:
  - Added this verification record to `changelog.md`.

## 2026-02-17 Documentation Inventory Pass
- Removed per-file \"Update Tracker\" sections from documentation files; changelog remains the single update history location.
- Reworked `docs/MODEL.md`, `docs/VIEW.md`, and `docs/CONTROLLER.md` into complete function inventories sourced from code signatures.
- Added per-function parameter mapping entries with variable-level descriptions for all discovered methods/functions in those files.
- Reworked `docs/INFERENCE_ENGINES.md` to include full adapter function inventories for both TTS (`src/tts_engines.py`) and S2S (`src/s2s_engines.py`).
- Updated README documentation index wording to reflect full function/parameter inventories.

## 2026-02-17 Documentation Standards Update
- Reworked project docs to align with strict MVC boundaries:
  - Updated `docs/ARCHITECTURE.md`, `docs/MODEL.md`, `docs/VIEW.md`, and `docs/CONTROLLER.md` with explicit ownership and flow details.
- Added parameter and type-oriented documentation for first-party MVC code paths and method signatures.
- Added `docs/INFERENCE_ENGINES.md` to document config-driven inference modularity and TTS/S2S adapter mappings.
- Updated operational and support docs:
  - `docs/CONFIG.md`
  - `docs/OPERATIONS.md`
  - `docs/TROUBLESHOOTING.md`
- Updated README documentation index to reference `INFERENCE_ENGINES` and remove API doc references.
- Removed `docs/API.md` because this project is GUI-driven and does not expose an HTTP/CLI API surface.
