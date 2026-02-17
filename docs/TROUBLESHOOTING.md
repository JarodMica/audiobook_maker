# TROUBLESHOOTING

## Purpose
Capture common failures in GUI startup, inference loading, and generation/export workflows, with checks tied to current MVC/inference architecture.

## GUI Fails to Start
Symptoms:
- `python src/controller.py` exits with import errors.

Checks:
- Confirm active environment and dependencies: `pip install -r requirements.txt`.
- Confirm PySide6 install is healthy.

Likely fixes:
- Recreate environment and reinstall requirements.
- Retry start from repo root to preserve relative paths.

Related files:
- `src/controller.py`
- `requirements.txt`

## Engine Import Not Available
Symptoms:
- Console prints adapter import messages (for example Tortoise/StyleTTS/F5/GPT-SoVITS/RVC not available).

Checks:
- Verify engine package is installed from `modules/` where applicable.
- Verify model/tokenizer/checkpoint assets exist in expected paths from config.

Likely fixes:
- Install missing engine package.
- Re-upload model assets using upload workflow.
- Confirm `configs/tts_config.json` and `configs/s2s_config.json` paths match filesystem.

Related files:
- `src/tts_engines.py`
- `src/s2s_engines.py`
- `configs/tts_config.json`
- `configs/s2s_config.json`

## Generation Stalls or Produces No Audio
Symptoms:
- Progress bar does not advance.
- `audio_path` remains empty for rows.

Checks:
- Confirm active speaker has `tts_engine` set.
- Confirm voice/model-related attributes are populated for that engine.
- Confirm output audiobook directory exists and is writable.

Likely fixes:
- Reopen speaker settings and reselect engine-specific parameters.
- Run single sentence regenerate first to isolate parameter errors.

Related files:
- `src/model.py`
- `src/controller.py`
- `src/view.py`

## S2S (RVC) Issues
Symptoms:
- S2S load fails or converted output missing.

Checks:
- Confirm `selected_voice` exists under `engines/rvc`.
- Confirm fairseq dependency is installed and compatible.
- Confirm RVC settings (`f0method`, `index_rate`, `protect`, etc.) are valid.

Likely fixes:
- Reinstall RVC dependencies and retry load.
- Re-upload model + index files under one voice folder.

Related files:
- `src/s2s_engines.py`
- `configs/s2s_config.json`

## Export Fails
Symptoms:
- Export dialog returns error.

Checks:
- Verify selected directory contains `text_audio_map.json`.
- Verify each mapped `audio_path` exists.
- Verify ffmpeg/ffprobe are available.

Likely fixes:
- Regenerate missing sentence audio.
- Install or repair ffmpeg/ffprobe path.

Related files:
- `src/model.py`

## File Locked During Regeneration
Symptoms:
- Old audio cannot be deleted/overwritten.

Checks:
- Confirm playback is stopped in UI.

Likely fixes:
- Stop audio and retry.
- Retry after short delay (worker already includes retry loop).

Related files:
- `src/controller.py`
- `src/view.py`
