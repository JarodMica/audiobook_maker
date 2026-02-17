# CONFIG

## Purpose
Document configuration files that control GUI behavior, engine parameter widgets, and runtime inference loading.

## `configs/settings.yaml`
Key inputs/config:
- `auto_download_gpt_sovits` (`bool`): If `true`, GPT-SoVITS resources may auto-download; runtime uses inverse `local_files_only` flag.
- `background_image` (`str | null`): Saved GUI background image path.
- `debug_mode` (`bool`): Controller can run generation logic inline instead of worker threading.
- `font_size` (`int`): View stylesheet font size baseline.
- `no_filter` (`bool`): Controls sentence filtering mode in `model.load_sentences(...)` and `model.filter_paragraph(...)`.
- `version` (`str | float`): Display/version marker.

Key outputs/behavior:
- Read during controller startup and passed into model/view.
- Updated via settings actions (`model.save_settings(...)`).

Related files:
- `src/controller.py`
- `src/model.py`
- `src/view.py`

## `configs/tts_config.json`
Key inputs/config:
- `tts_engines[]` (`list[dict]`): Declarative engine schema.
- Engine `parameters[]` entries define widget type and runtime attribute key:
  - `type` (for example `combobox`, `spinbox`, `slider`, `checkbox`, `file`, `text`)
  - `attribute` (key persisted in speaker settings and passed into engine loader/generator)
  - Optional constraints: `min`, `max`, `default`, `step`, `folder_path`, `custom_options`.
- Engine `upload_params` drives upload dialog forms and target paths.

Key outputs/behavior:
- View dynamically builds controls from this schema (`create_widget_for_parameter`, `update_tts_options`).
- Controller/model persist these attributes under per-speaker `settings`.
- `src/tts_engines.py` resolves the attributes into engine-specific arguments.

Related files:
- `src/view.py`
- `src/controller.py`
- `src/model.py`
- `src/tts_engines.py`

## `configs/s2s_config.json`
Key inputs/config:
- `s2s_engines[]` (`list[dict]`) with same declarative widget pattern.
- For RVC, key runtime attributes include:
  - `selected_voice`, `f0method`, `index_rate`, `f0pitch`, `resample_sr`, `rms_mix_rate`, `protect`, `filter_radius`.

Key outputs/behavior:
- View builds S2S controls dynamically (`update_s2s_options`).
- Model passes selected attributes to `s2s_engines.load_s2s_engine(...)`.
- `src/s2s_engines.py` normalizes slider values using `step` where needed.

Related files:
- `src/view.py`
- `src/model.py`
- `src/s2s_engines.py`

## `engines/gpt_sovits/tts_configs.yaml`
Key inputs/config:
- Versioned GPT-SoVITS defaults (`v1`, `v2`, `v3`, `v4`).
- Default model/vocoder paths consumed when UI overrides are not selected.

Key outputs/behavior:
- Merged into `TTS_Config.default_configs` in `load_with_gpt_sovits(...)`.
- Supports both explicit user-selected checkpoints and version fallback behavior.

Related files:
- `src/tts_engines.py`
- `engines/gpt_sovits/tts_configs.yaml`

## Per-Audiobook Runtime State
Key inputs/config:
- `audiobooks/<book>/generation_settings.json`:
  - `speakers` mapping with per-speaker color/name/settings.
- `audiobooks/<book>/text_audio_map.json`:
  - Per sentence `sentence`, `audio_path`, `generated`, `speaker_id`, `regen`.

Key outputs/behavior:
- Enables continue generation, bulk regenerate, and reload/update of existing audiobook projects.

Related files:
- `src/model.py`
- `src/controller.py`
