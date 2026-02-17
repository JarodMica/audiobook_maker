# MODEL

## Purpose
Document `src/model.py` parameters and method usage in the strict MVC design where model owns logic, processing, and persistence.

## Complete Function Parameter Inventory
This inventory is generated from current source signatures and is intended to map every discovered function/method parameter.

### `model.py` -> `AudiobookModel`

- `__init__(self: Any, global_settings: Any) -> Any`
  - Parameters:
    - `global_settings` (`Any`): Global runtime settings loaded from configs/settings.yaml.

- `assign_speaker_to_sentence(self: Any, idx: Any, speaker_id: Any) -> Any`
  - Parameters:
    - `idx` (`Any`): Sentence index (table row / map key position).
    - `speaker_id` (`Any`): Numeric speaker identifier used in sentence assignment and settings lookup.

- `change_regen_state(self: Any, idx: Any, state: Any) -> Any`
  - Parameters:
    - `idx` (`Any`): Sentence index (table row / map key position).
    - `state` (`Any`): Boolean or state value emitted by Qt control interactions.

- `clear_background_image(self: Any) -> Any`
  - Parameters: none (instance context only).

- `create_audio_text_map(self: Any, directory_path: Any, sentences_list: Any) -> Any`
  - Parameters:
    - `directory_path` (`Any`): Path to target audiobook directory.
    - `sentences_list` (`Any`): Ordered list of sentence strings for map construction or updates.

- `create_book_text_file(self: Any, text_file_destination: Any) -> Any`
  - Parameters:
    - `text_file_destination` (`Any`): Directory where book_text.txt should be generated.

- `delete_sentences(self: Any, rows_list: Any) -> Any`
  - Parameters:
    - `rows_list` (`Any`): List of table row indexes used for bulk operations.

- `default_text_audio_map_format(self: Any, **kwargs: Any) -> Any`
  - Parameters:
    - `**kwargs` (`Any`): Engine-specific keyword arguments forwarded from speaker settings.

- `execute_subprocess(self: Any, cmd: Any) -> Any`
  - Parameters:
    - `cmd` (`Any`): Subprocess command list used for external tool execution.

- `export_audiobook(self: Any, directory_path: Any, pause_duration: Any) -> Any`
  - Parameters:
    - `directory_path` (`Any`): Path to target audiobook directory.
    - `pause_duration` (`Any`): Pause duration between sentences during export.

- `filter_paragraph(self: Any, paragraph: Any, no_filter: Any = False) -> Any`
  - Parameters:
    - `paragraph` (`Any`): Raw paragraph text before sentence filtering/splitting.
    - `no_filter` (`Any`): If true, disables heuristic sentence filtering and uses simpler splitting. Default: `False`.

- `generate_audio_for_sentence_threaded(self: Any, directory_path: Any, is_continue: Any, is_regen_only: Any, report_progress_callback: Any, sentence_generated_callback: Any, should_stop_callback: Any = None) -> Any`
  - Parameters:
    - `directory_path` (`Any`): Path to target audiobook directory.
    - `is_continue` (`Any`): If true, skip already-generated sentences.
    - `is_regen_only` (`Any`): If true, process only sentences marked for regeneration.
    - `report_progress_callback` (`Any`): Callback invoked with integer generation progress.
    - `sentence_generated_callback` (`Any`): Callback invoked after a sentence audio file is generated.
    - `should_stop_callback` (`Any`): Callback returning whether generation should stop. Default: `None`.

- `generate_audio_proxy(self: Any, sentence: Any, voice_parameters: Any, s2s_validated: Any) -> Any`
  - Parameters:
    - `sentence` (`Any`): Sentence text content to process, render, or synthesize.
    - `voice_parameters` (`Any`): Per-speaker settings dictionary used by TTS/S2S adapters.
    - `s2s_validated` (`Any`): Input parameter used by this function for its operation.

- `get_map_keys_and_values(self: Any, idx_str: Any) -> Any`
  - Parameters:
    - `idx_str` (`Any`): Sentence index represented as a string key in text_audio_map.

- `get_s2s_engines(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_speaker_name(self: Any, speaker_id: Any) -> Any`
  - Parameters:
    - `speaker_id` (`Any`): Numeric speaker identifier used in sentence assignment and settings lookup.

- `get_tts_engines(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_voice_indexes(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_voice_models(self: Any) -> Any`
  - Parameters: none (instance context only).

- `load_config(self: Any, config_path: Any) -> Any`
  - Parameters:
    - `config_path` (`Any`): Path to a JSON/YAML configuration file.

- `load_generation_settings(self: Any, directory_path: Any) -> Any`
  - Parameters:
    - `directory_path` (`Any`): Path to target audiobook directory.

- `load_json(self: Any, file_path: Any) -> Any`
  - Parameters:
    - `file_path` (`Any`): Path to a source file selected by the user.

- `load_pdf(self: Any) -> Any`
  - Parameters: none (instance context only).

- `load_selected_s2s_engine(self: Any, chosen_s2s_engine: Any, speaker_id: Any, **kwargs: Any) -> Any`
  - Parameters:
    - `chosen_s2s_engine` (`Any`): Requested S2S engine to load in model cache.
    - `speaker_id` (`Any`): Numeric speaker identifier used in sentence assignment and settings lookup.
    - `**kwargs` (`Any`): Engine-specific keyword arguments forwarded from speaker settings.

- `load_selected_tts_engine(self: Any, chosen_tts_engine: Any, speaker_id: Any, **kwargs: Any) -> Any`
  - Parameters:
    - `chosen_tts_engine` (`Any`): Requested TTS engine to load in model cache.
    - `speaker_id` (`Any`): Numeric speaker identifier used in sentence assignment and settings lookup.
    - `**kwargs` (`Any`): Engine-specific keyword arguments forwarded from speaker settings.

- `load_sentences(self: Any, file_path: Any, no_filter: Any, file_ext: Any) -> Any`
  - Parameters:
    - `file_path` (`Any`): Path to a source file selected by the user.
    - `no_filter` (`Any`): If true, disables heuristic sentence filtering and uses simpler splitting.
    - `file_ext` (`Any`): Detected file extension used to route loading logic.

- `load_text_audio_map(self: Any, directory_path: Any) -> Any`
  - Parameters:
    - `directory_path` (`Any`): Path to target audiobook directory.

- `paragraph_to_sentence(self: Any, paragraph: Any) -> list`
  - Parameters:
    - `paragraph` (`Any`): Raw paragraph text before sentence filtering/splitting.

- `process_pdf(self: Any) -> Any`
  - Parameters: none (instance context only).

- `process_upload_items(self: Any, mode: Any, save_items: Any) -> Any`
  - Parameters:
    - `mode` (`Any`): Operational mode selected in UI (for example upload mode).
    - `save_items` (`Any`): Structured upload payload list describing files/text and destinations.

- `replace_default_with_none(self: Any, data: Any) -> Any`
  - Parameters:
    - `data` (`Any`): Generic dictionary/list payload for normalization or serialization.

- `replace_words_from_list(self: Any, replacement_file_path: Any, extra: Any) -> Any`
  - Parameters:
    - `replacement_file_path` (`Any`): Path to word replacement list JSON file.
    - `extra` (`Any`): Extra cleanup/replacement toggle for word replacer logic.

- `reset(self: Any) -> Any`
  - Parameters: none (instance context only).

- `reset_regen_in_text_audio_map(self: Any) -> Any`
  - Parameters: none (instance context only).

- `save_settings(self: Any, settings_dict: Any) -> Any`
  - Parameters:
    - `settings_dict` (`Any`): Dictionary of setting keys and values to persist.

- `save_generation_settings(self: Any, directory_path: Any, speakers: Any = None) -> Any`
  - Parameters:
    - `directory_path` (`Any`): Path to target audiobook directory.
    - `speakers` (`Any`): Speaker mapping keyed by speaker ID. Default: `None`.

- `save_json(self: Any, file_path: Any, data: Any) -> Any`
  - Parameters:
    - `file_path` (`Any`): Path to a source file selected by the user.
    - `data` (`Any`): Generic dictionary/list payload for normalization or serialization.

- `save_temp_generation_settings(self: Any, speakers: Any = None) -> Any`
  - Parameters:
    - `speakers` (`Any`): Speaker mapping keyed by speaker ID. Default: `None`.

- `save_text_audio_map(self: Any, directory_path: Any) -> Any`
  - Parameters:
    - `directory_path` (`Any`): Path to target audiobook directory.

- `set_background_image(self: Any, file_name: Any) -> Any`
  - Parameters:
    - `file_name` (`Any`): Source filename selected in file dialogs.

- `update_audiobook(self: Any, directory_path: Any, new_sentences_list: Any) -> Any`
  - Parameters:
    - `directory_path` (`Any`): Path to target audiobook directory.
    - `new_sentences_list` (`Any`): Updated sentence list used to remap existing audiobook entries.

- `update_sentence_in_text_audio_map(self: Any, idx: Any, new_text: Any) -> Any`
  - Parameters:
    - `idx` (`Any`): Sentence index (table row / map key position).
    - `new_text` (`Any`): Edited replacement sentence text.

- `update_speakers(self: Any, speakers: Any) -> Any`
  - Parameters:
    - `speakers` (`Any`): Speaker mapping keyed by speaker ID.

- `update_text_audio_map(self: Any, sentences_list: Any) -> Any`
  - Parameters:
    - `sentences_list` (`Any`): Ordered list of sentence strings for map construction or updates.

### `model.py` -> `AudiobookModel.export_audiobook`

- `probe_audio_properties(file_path: Any) -> Any`
  - Parameters:
    - `file_path` (`Any`): Path to a source file selected by the user.

### `model.py` -> `AudiobookModel.save_json`

- `default_serializer(obj: Any) -> Any`
  - Parameters:
    - `obj` (`Any`): Input parameter used by this function for its operation.

## Related Files
- `src/model.py`
- `src/view.py`
- `src/controller.py`
- `src/tts_engines.py`
- `src/s2s_engines.py`
- `configs/tts_config.json`
- `configs/s2s_config.json`
