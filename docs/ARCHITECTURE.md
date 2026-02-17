# ARCHITECTURE

## Purpose
Define the concrete MVC boundaries, signal flow, and inference pipeline used by Audiobook Maker so documentation stays aligned with the code.

## MVC Boundaries (Strict)
- `src/view.py` (`AudiobookMakerView` and dialogs):
  - Owns GUI widgets, layouts, dynamic engine parameter controls, table rendering, and media playback UI behavior.
  - Emits user-intent signals; does not run business logic/inference.
- `src/controller.py` (`AudiobookController` + workers):
  - Owns orchestration between view and model.
  - Converts UI signals into model calls and updates view when work completes/fails.
- `src/model.py` (`AudiobookModel`):
  - Owns data state (`text_audio_map`, speakers, settings), persistence, text/sentence processing, generation loops, and export logic.

## Primary Runtime Flow
1. Entry: `python src/controller.py`.
2. Controller loads settings (`load_global_settings`), instantiates model/view, wires signals (`connect_signals`).
3. User loads text; controller asks model to parse sentences and build/update `text_audio_map`.
4. User starts generation; controller starts `AudioGenerationWorker`.
5. Worker calls `model.generate_audio_for_sentence_threaded(...)`.
6. Model loads selected TTS (and optional S2S), generates sentence audio, persists map updates.
7. Worker emits progress/sentence events; controller updates view row/progress.
8. Export path calls `model.export_audiobook(...)` to concatenate sentence audio.

## Signal and Worker Flow
- View -> Controller:
  - Start/stop generation, load file/audiobook, regenerate, bulk regenerate, export, settings changes, speaker updates, uploads, table edits, playback actions.
- Controller -> Model:
  - Sentence assignment, generation settings save/load, map updates, engine loading, audio generation, export, upload handling.
- Controller -> View:
  - Progress updates, row refreshes, playback sequencing, dialogs/messages, button enable/disable state.
- Worker classes in controller:
  - `AudioGenerationWorker(function, directory_path, is_continue, is_regen_only)`
  - `RegenerateAudioWorker(model, old_audio_path, selected_sentence, combined_parameters, new_audio_path, speaker_id)`

## Inference Architecture (Config-Driven)
- UI control generation is driven by:
  - `configs/tts_config.json`
  - `configs/s2s_config.json`
- Inference execution logic is isolated to:
  - `src/tts_engines.py`
  - `src/s2s_engines.py`
- Model delegates engine load/generate calls through those adapters.

## Data and Persistence Paths
- Global config:
  - `configs/settings.yaml`
  - `configs/tts_config.json`
  - `configs/s2s_config.json`
  - `engines/gpt_sovits/tts_configs.yaml`
- Per-audiobook state:
  - `audiobooks/<book>/book_text.txt`
  - `audiobooks/<book>/text_audio_map.json`
  - `audiobooks/<book>/generation_settings.json`
  - `audiobooks/<book>/audio_<idx>.wav`
  - `audiobooks/<book>/exported_audiobooks/*.mp3`

## Modules (High-Level Only)
- `modules/` contains vendored third-party projects used as installable runtime dependencies.
- First-party behavior and integration points are documented primarily in `src/` and `configs/` docs.

## Related Files
- `src/controller.py`
- `src/view.py`
- `src/model.py`
- `src/tts_engines.py`
- `src/s2s_engines.py`
- `configs/tts_config.json`
- `configs/s2s_config.json`
- `configs/settings.yaml`
