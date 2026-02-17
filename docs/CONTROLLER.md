# CONTROLLER

## Purpose
Document `src/controller.py` orchestration methods, worker callbacks, and signal-routing parameters between view and model.

## Complete Function Parameter Inventory
This inventory is generated from current source signatures and is intended to map every discovered function/method parameter.

### `controller.py` -> `AudioGenerationWorker`

- `__init__(self: Any, function: Any, directory_path: Any, is_continue: Any, is_regen_only: Any) -> Any`
  - Parameters:
    - `function` (`Any`): Callable passed into worker thread for generation execution.
    - `directory_path` (`Any`): Path to target audiobook directory.
    - `is_continue` (`Any`): If true, skip already-generated sentences.
    - `is_regen_only` (`Any`): If true, process only sentences marked for regeneration.

- `run(self: Any) -> Any`
  - Parameters: none (instance context only).

- `stop(self: Any) -> Any`
  - Parameters: none (instance context only).

- `should_stop(self: Any) -> Any`
  - Parameters: none (instance context only).

- `report_progress(self: Any, progress: Any) -> Any`
  - Parameters:
    - `progress` (`Any`): Progress percentage value emitted by generation worker.

- `sentence_generated_callback(self: Any, idx: Any, sentence: Any) -> Any`
  - Parameters:
    - `idx` (`Any`): Sentence index (table row / map key position).
    - `sentence` (`Any`): Sentence text content to process, render, or synthesize.

### `controller.py` -> `AudiobookController`

- `__init__(self: Any) -> Any`
  - Parameters: none (instance context only).

- `allow_speaker_assignment(self: Any, position: Any) -> Any`
  - Parameters:
    - `position` (`Any`): UI position value (for example context menu request position).

- `assign_speaker_to_sentence(self: Any, idx: Any, speaker_id: Any) -> Any`
  - Parameters:
    - `idx` (`Any`): Sentence index (table row / map key position).
    - `speaker_id` (`Any`): Numeric speaker identifier used in sentence assignment and settings lookup.

- `check_and_reset_for_new_file(self: Any, action_description: Any) -> Any`
  - Parameters:
    - `action_description` (`Any`): User-facing message describing a pending reset/operation.

- `clear_background_image(self: Any) -> Any`
  - Parameters: none (instance context only).

- `clear_regen_checkboxes(self: Any) -> Any`
  - Parameters: none (instance context only).

- `connect_signals(self: Any) -> Any`
  - Parameters: none (instance context only).

- `connect_signals_replacer(self: Any) -> Any`
  - Parameters: none (instance context only).

- `connect_signals_upload_voice(self: Any) -> Any`
  - Parameters: none (instance context only).

- `continue_audiobook_generation(self: Any) -> Any`
  - Parameters: none (instance context only).

- `create_audiobook_directory(self: Any) -> Any`
  - Parameters: none (instance context only).

- `deletion_prompt(self: Any) -> Any`
  - Parameters: none (instance context only).

- `export_audiobook(self: Any) -> Any`
  - Parameters: none (instance context only).

- `extract_text(self: Any, idx: int, concat_sentences: bool, length_search_text: int) -> str`
  - Parameters:
    - `idx` (`int`): Sentence index (table row / map key position).
    - `concat_sentences` (`bool`): If true, include adjacent sentence text while searching.
    - `length_search_text` (`int`): Length budget used for concatenated search preview.

- `global_settings_changed(self: Any, changes: dict) -> Any`
  - Parameters:
    - `changes` (`dict`): Dictionary of changed global settings values.

- `load_existing_audiobook(self: Any) -> Any`
  - Parameters: none (instance context only).

- `load_global_settings(self: Any) -> Any`
  - Parameters: none (instance context only).

- `load_file(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_audio_finished(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_font_size_changed(self: Any, font_size: Any) -> Any`
  - Parameters:
    - `font_size` (`Any`): UI font size value emitted from slider/settings.

- `on_generation_finished(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_generation_started(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_regeneration_error(self: Any, error_message: Any) -> Any`
  - Parameters:
    - `error_message` (`Any`): Input parameter used by this function for its operation.

- `on_regeneration_finished(self: Any, map_key: Any, new_audio_path: Any, speaker_id: Any) -> Any`
  - Parameters:
    - `map_key` (`Any`): String key for selected sentence entry in text_audio_map.
    - `new_audio_path` (`Any`): Output path for regenerated or newly generated audio.
    - `speaker_id` (`Any`): Numeric speaker identifier used in sentence assignment and settings lookup.

- `on_s2s_engine_changed(self: Any, s2s_engine_name: Any) -> Any`
  - Parameters:
    - `s2s_engine_name` (`Any`): Selected speech-to-speech engine name.

- `on_speakers_updated(self: Any, speakers: Any) -> Any`
  - Parameters:
    - `speakers` (`Any`): Speaker mapping keyed by speaker ID.

- `on_sentence_generated(self: Any, idx: Any, sentence: Any) -> Any`
  - Parameters:
    - `idx` (`Any`): Sentence index (table row / map key position).
    - `sentence` (`Any`): Sentence text content to process, render, or synthesize.

- `on_test_word_finished(self: Any, audio_path: Any) -> Any`
  - Parameters:
    - `audio_path` (`Any`): Path to an audio file used for playback/generation/output.

- `on_tts_engine_changed(self: Any, speakers: Any) -> Any`
  - Parameters:
    - `speakers` (`Any`): Speaker mapping keyed by speaker ID.

- `pause_audio(self: Any) -> Any`
  - Parameters: none (instance context only).

- `play_all_from_selected(self: Any) -> Any`
  - Parameters: none (instance context only).

- `play_next_audio_in_sequence(self: Any) -> Any`
  - Parameters: none (instance context only).

- `play_selected_audio(self: Any) -> Any`
  - Parameters: none (instance context only).

- `populate_initial_data(self: Any) -> Any`
  - Parameters: none (instance context only).

- `popup_load_audiobook(self: Any) -> Any`
  - Parameters: none (instance context only).

- `regen_checkbox_toggled(self: Any, row: Any, state: Any) -> Any`
  - Parameters:
    - `row` (`Any`): Table row index corresponding to a sentence entry.
    - `state` (`Any`): Boolean or state value emitted by Qt control interactions.

- `regenerate_audio_for_sentence(self: Any) -> Any`
  - Parameters: none (instance context only).

- `regenerate_in_bulk(self: Any) -> Any`
  - Parameters: none (instance context only).

- `save_generation_settings(self: Any) -> Any`
  - Parameters: none (instance context only).

- `save_list(self: Any) -> Any`
  - Parameters: none (instance context only).

- `search_sentences(self: Any, start_idx: int, forward: bool, search_text: str, concat_sentences: bool) -> Any`
  - Parameters:
    - `start_idx` (`int`): Starting row index for search traversal.
    - `forward` (`bool`): Search direction flag (forward/backward).
    - `search_text` (`str`): User-provided text query used for sentence navigation.
    - `concat_sentences` (`bool`): If true, include adjacent sentence text while searching.

- `set_background_image(self: Any) -> Any`
  - Parameters: none (instance context only).

- `set_up_settings(self: Any, speakers: Any = None) -> Any`
  - Parameters:
    - `speakers` (`Any`): Speaker mapping keyed by speaker ID. Default: `None`.

- `setup_interface(self: Any, directory_path: Any) -> Any`
  - Parameters:
    - `directory_path` (`Any`): Path to target audiobook directory.

- `start_generation(self: Any) -> Any`
  - Parameters: none (instance context only).

- `start_wr(self: Any) -> Any`
  - Parameters: none (instance context only).

- `stop_generation(self: Any) -> Any`
  - Parameters: none (instance context only).

- `update_audiobook(self: Any) -> Any`
  - Parameters: none (instance context only).

- `update_sentence(self: Any, row: Any, new_text: Any) -> Any`
  - Parameters:
    - `row` (`Any`): Table row index corresponding to a sentence entry.
    - `new_text` (`Any`): Edited replacement sentence text.

- `update_speakers(self: Any, speakers: Any) -> Any`
  - Parameters:
    - `speakers` (`Any`): Speaker mapping keyed by speaker ID.

- `update_table_with_sentences(self: Any) -> Any`
  - Parameters: none (instance context only).

- `upload_requested(self: Any, mode: Any, save_items: Any) -> Any`
  - Parameters:
    - `mode` (`Any`): Operational mode selected in UI (for example upload mode).
    - `save_items` (`Any`): Structured upload payload list describing files/text and destinations.

- `test_single_word(self: Any, chosen_word: Any, speaker: Any) -> Any`
  - Parameters:
    - `chosen_word` (`Any`): Selected word used for one-word synthesis testing.
    - `speaker` (`Any`): Speaker name or speaker object/value for lookup.

- `toggle_delete_column(self: Any) -> Any`
  - Parameters: none (instance context only).

- `toggle_upload_voice_window(self: Any) -> Any`
  - Parameters: none (instance context only).

- `toggle_word_replacer_window(self: Any, checked: Any) -> Any`
  - Parameters:
    - `checked` (`Any`): Qt checkbox toggle state.

- `word_replacer_closed(self: Any) -> Any`
  - Parameters: none (instance context only).

### `controller.py` -> `RegenerateAudioWorker`

- `__init__(self: Any, model: Any, old_audio_path: Any, selected_sentence: Any, combined_parameters: Any, new_audio_path: Any, speaker_id: Any) -> Any`
  - Parameters:
    - `model` (`Any`): Qt model object used by delegate/editor callbacks.
    - `old_audio_path` (`Any`): Existing sentence audio path to be replaced during regeneration.
    - `selected_sentence` (`Any`): Current sentence text selected for regeneration/test.
    - `combined_parameters` (`Any`): Merged speaker settings dictionary used for regeneration.
    - `new_audio_path` (`Any`): Output path for regenerated or newly generated audio.
    - `speaker_id` (`Any`): Numeric speaker identifier used in sentence assignment and settings lookup.

- `run(self: Any) -> Any`
  - Parameters: none (instance context only).

## Related Files
- `src/model.py`
- `src/view.py`
- `src/controller.py`
- `src/tts_engines.py`
- `src/s2s_engines.py`
- `configs/tts_config.json`
- `configs/s2s_config.json`
