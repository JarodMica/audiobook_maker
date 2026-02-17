# AI Changelog Notes

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
