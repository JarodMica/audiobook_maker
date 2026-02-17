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
- `configs/tts_config.json`
- `configs/s2s_config.json`
