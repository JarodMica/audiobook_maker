# OPERATIONS

## Purpose
Define practical run/update workflows with emphasis on MVC-safe operation and config-driven inference setup.

## Local Run (Developer)
Key inputs/config:
- Python environment with `requirements.txt` installed.
- Optional engine packages installed from `modules/` as needed.

Key outputs/behavior:
- Starts GUI controller process and initializes MVC runtime.

Commands:
```powershell
pip install -r requirements.txt
python src/controller.py
```

Related files:
- `README.md`
- `requirements.txt`
- `src/controller.py`

## Runtime Directories
- `audiobooks/`: per-project generated state and exported audiobooks.
- `voices/`: uploaded voice references grouped by engine.
- `engines/`: local model/tokenizer/vocoder assets.
- `configs/`: global settings and engine UI schemas.

Operational note:
- Back up `audiobooks/<book>/` to preserve work-in-progress sentence map, settings, and generated audio.

## Engine Operations (Config-Driven)
- Engine controls shown in GUI come from:
  - `configs/tts_config.json`
  - `configs/s2s_config.json`
- Upload operations save into config-defined target paths via controller -> model flow.
- Runtime inference should be implemented only in:
  - `src/tts_engines.py`
  - `src/s2s_engines.py`

## Generation Operations
- Start generation:
  - Creates/loads audiobook directory.
  - Saves/updates `text_audio_map.json` and `generation_settings.json`.
  - Runs worker-thread generation to keep GUI responsive.
- Continue generation:
  - Skips already generated entries.
- Bulk regenerate:
  - Uses `regen` flags in map entries.
- Single regenerate:
  - Rebuilds one sentence audio file using active speaker settings.

## Update Workflow
Commands:
```powershell
git pull
git submodule update
```

Notes:
- Run after upstream updates.
- Recheck engine imports after updates because third-party package changes can affect inference adapters.

## Unit Testing
Purpose:
- Define repeatable terminal testing for inference engines using the project venv and pinned defaults.

### Engine Validation
Key inputs/config:
- `src/unit_tests/validate_tts_engine.py`: runner for smoke-style TTS testing.
- `src/unit_tests/engine_validation_defaults.json`: pinned per-engine parameters and GPT-SoVITS matrix values.
- `configs/tts_config.json`: dynamic source of engine discovery (engines marked `in progress` are expected skip).
- Runtime interpreter used to launch workers: active Python executable (recommended: `venv\Scripts\python.exe`).

Key outputs/behavior:
- Produces per-engine (and per-case matrix) JSON results with:
  - `load_success`
  - `returned_audio_path`
  - `output_file_nonempty`
- Isolates each test case in a fresh subprocess to prevent CUDA/runtime state contamination across engines.
- Emits status categories per case:
  - `passed`
  - `failed`
  - `timeout`
  - `crash`
  - `preflight_failed`
- In no-argument run-all mode, writes engine-specific output wav files under `output_test/`.
- In single-engine mode, default output is repo-root `engine_smoke.wav` unless `--output` is provided.
- Prints live terminal progress while running:
  - Uses `tqdm` progress bar if available.
  - Falls back to line-by-line `START`/`DONE` progress messages with rolling counts.

Commands:
```powershell
venv\Scripts\python.exe src\unit_tests\validate_tts_engine.py
```

Optional targeted command:
```powershell
venv\Scripts\python.exe src\unit_tests\validate_tts_engine.py --engine styletts2
```

Operational notes:
- Run from repo root so relative config/asset paths resolve correctly.
- Keep `engine_validation_defaults.json` updated whenever engines are added/removed or renamed in config.
- Use `--timeout-sec` to adjust per-case subprocess timeout for heavier models.
- Treat failures in a subset of matrix cases as runtime-path issues unless preflight reports missing defaults or files.

## Documentation Maintenance Rule
- Keep `docs/MODEL.md`, `docs/VIEW.md`, `docs/CONTROLLER.md`, and `docs/INFERENCE_ENGINES.md` aligned with code changes.
- Record project release/history notes in `changelog.md`.
- Record AI-generated documentation verification/session notes in `AI_CHANGELOG.md` unless explicitly requested otherwise.

## Related Files
- `src/controller.py`
- `src/model.py`
- `src/view.py`
- `src/tts_engines.py`
- `src/s2s_engines.py`
- `src/unit_tests/validate_tts_engine.py`
- `src/unit_tests/engine_validation_defaults.json`
- `configs/tts_config.json`
- `configs/s2s_config.json`
