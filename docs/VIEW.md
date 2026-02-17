# VIEW

## Purpose
Document GUI-layer methods/signals and parameter usage in `src/view.py`; this layer owns rendering and user interaction only.

## Complete Function Parameter Inventory
This inventory is generated from current source signatures and is intended to map every discovered function/method parameter.

### `view.py` -> `AudiobookMakerView`

- `__init__(self: Any, global_settings: Any) -> Any`
  - Parameters:
    - `global_settings` (`Any`): Global runtime settings loaded from configs/settings.yaml.

- `_init_ui(self: Any) -> Any`
  - Parameters: none (instance context only).

- `add_table_item(self: Any, row: Any, text: Any, speaker_name: Any, regen_state: Any = False, delete_state: Any = False) -> Any`
  - Parameters:
    - `row` (`Any`): Table row index corresponding to a sentence entry.
    - `text` (`Any`): Input parameter used by this function for its operation.
    - `speaker_name` (`Any`): Input parameter used by this function for its operation.
    - `regen_state` (`Any`): Input parameter used by this function for its operation. Default: `False`.
    - `delete_state` (`Any`): Input parameter used by this function for its operation. Default: `False`.

- `ask_question(self: Any, title: Any, question: Any, buttons: Any = QMessageBox.Yes | QMessageBox.No, default_button: Any = QMessageBox.No) -> Any`
  - Parameters:
    - `title` (`Any`): Dialog title text.
    - `question` (`Any`): Prompt text displayed to user in confirmation dialogs.
    - `buttons` (`Any`): Qt button bitmask for confirmation dialogs. Default: `QMessageBox.Yes | QMessageBox.No`.
    - `default_button` (`Any`): Default Qt button for dialogs. Default: `QMessageBox.No`.

- `assign_speaker_to_selected(self: Any, speaker_id: Any, speaker_name: Any) -> Any`
  - Parameters:
    - `speaker_id` (`Any`): Numeric speaker identifier used in sentence assignment and settings lookup.
    - `speaker_name` (`Any`): Input parameter used by this function for its operation.

- `browse_file(self: Any, widget: Any, param: Any) -> Any`
  - Parameters:
    - `widget` (`Any`): Qt widget instance tied to a parameter/control.
    - `param` (`Any`): Engine parameter configuration dictionary from JSON config.

- `clear_layout(self: Any, layout: Any) -> Any`
  - Parameters:
    - `layout` (`Any`): Qt layout object being built or cleared.

- `clear_table(self: Any) -> Any`
  - Parameters: none (instance context only).

- `create_widget_for_parameter(self: Any, param: Any) -> Any`
  - Parameters:
    - `param` (`Any`): Engine parameter configuration dictionary from JSON config.

- `disable_buttons(self: Any) -> Any`
  - Parameters: none (instance context only).

- `disable_speaker_menu(self: Any) -> Any`
  - Parameters: none (instance context only).

- `enable_buttons(self: Any) -> Any`
  - Parameters: none (instance context only).

- `enable_speaker_menu(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_available_speakers(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_book_name(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_combobox_items(self: Any, param: Any) -> Any`
  - Parameters:
    - `param` (`Any`): Engine parameter configuration dictionary from JSON config.

- `get_current_speaker_attributes(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_deletion_checkboxes(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_existing_directory(self: Any, title: Any, directory: Any = '') -> Any`
  - Parameters:
    - `title` (`Any`): Dialog title text.
    - `directory` (`Any`): Input parameter used by this function for its operation. Default: `''`.

- `get_open_file_name(self: Any, title: Any, directory: Any = '', filter: Any = '') -> Any`
  - Parameters:
    - `title` (`Any`): Dialog title text.
    - `directory` (`Any`): Input parameter used by this function for its operation. Default: `''`.
    - `filter` (`Any`): Input parameter used by this function for its operation. Default: `''`.

- `get_pause_between_sentences(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_search_start(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_s2s_engine(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_s2s_engine_parameters(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_tts_engine(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_tts_engine_parameters(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_voice_parameters(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_selected_table_row(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_window_size(self: Any) -> Any`
  - Parameters: none (instance context only).

- `handle_sentence_changed(self: Any, item: Any) -> Any`
  - Parameters:
    - `item` (`Any`): Qt table/list item object tied to UI callbacks.

- `initialize_media_player(self: Any) -> Any`
  - Parameters: none (instance context only).

- `is_audio_playing(self: Any, audio_path: Any) -> Any`
  - Parameters:
    - `audio_path` (`Any`): Path to an audio file used for playback/generation/output.

- `load_speaker_settings(self: Any, speaker_id: Any) -> Any`
  - Parameters:
    - `speaker_id` (`Any`): Numeric speaker identifier used in sentence assignment and settings lookup.

- `load_tts_config(self: Any, config_path: Any) -> Any`
  - Parameters:
    - `config_path` (`Any`): Path to a JSON/YAML configuration file.

- `load_s2s_config(self: Any, config_path: Any) -> Any`
  - Parameters:
    - `config_path` (`Any`): Path to a JSON/YAML configuration file.

- `load_stylesheet(self: Any, font_size: Any = '14pt') -> Any`
  - Parameters:
    - `font_size` (`Any`): UI font size value emitted from slider/settings. Default: `'14pt'`.

- `pause_audio(self: Any) -> Any`
  - Parameters: none (instance context only).

- `play_audio(self: Any, audio_path: Any) -> Any`
  - Parameters:
    - `audio_path` (`Any`): Path to an audio file used for playback/generation/output.

- `on_audio_finished(self: Any, state: Any) -> Any`
  - Parameters:
    - `state` (`Any`): Boolean or state value emitted by Qt control interactions.

- `on_clear_regen_button_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_continue_button_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_current_speaker_changed(self: Any, index: Any) -> Any`
  - Parameters:
    - `index` (`Any`): Qt model index for row/column lookup.

- `on_delete_button_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_disable_stop_button(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_enable_stop_button(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_export_audiobook_triggered(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_export_pause_slider_changed(self: Any, value: Any) -> Any`
  - Parameters:
    - `value` (`Any`): Generic numeric/string value emitted by UI controls.

- `on_font_slider_changed(self: Any, value: Any) -> Any`
  - Parameters:
    - `value` (`Any`): Generic numeric/string value emitted by UI controls.

- `on_generate_button_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_global_settings_changed(self: Any, changes: dict) -> Any`
  - Parameters:
    - `changes` (`dict`): Dictionary of changed global settings values.

- `on_go_to_sentence(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_load_existing_audiobook_triggered(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_load_file_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_manage_speakers(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_next_search(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_parameter_changed(self: Any, attribute: Any, value: Any) -> Any`
  - Parameters:
    - `attribute` (`Any`): Input parameter used by this function for its operation.
    - `value` (`Any`): Generic numeric/string value emitted by UI controls.

- `on_pause_button_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_play_all_button_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_play_button_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_previous_search(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_regenerate_bulk_button_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_regenerate_button_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_set_background_clear_image_triggered(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_set_background_image_triggered(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_s2s_engine_changed(self: Any, engine_name: Any) -> Any`
  - Parameters:
    - `engine_name` (`Any`): Selected inference engine name from combobox.

- `on_stop_button_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_toggle_delete_action_triggered(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_tts_engine_changed(self: Any, engine_name: Any) -> Any`
  - Parameters:
    - `engine_name` (`Any`): Selected inference engine name from combobox.

- `on_update_audiobook_triggered(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_upload_voice_triggered(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_use_s2s_changed(self: Any, state: Any) -> Any`
  - Parameters:
    - `state` (`Any`): Boolean or state value emitted by Qt control interactions.

- `on_word_replacer_closed(self: Any) -> Any`
  - Parameters: none (instance context only).

- `open_upload_voice_window(self: Any, engines_list: Any) -> Any`
  - Parameters:
    - `engines_list` (`Any`): List of available TTS/S2S engine names for upload UI.

- `open_word_replacer_window(self: Any, parent: Any = None) -> Any`
  - Parameters:
    - `parent` (`Any`): Qt parent widget reference. Default: `None`.

- `open_settings_dialog(self: Any) -> Any`
  - Parameters: none (instance context only).

- `populate_s2s_engines(self: Any) -> Any`
  - Parameters: none (instance context only).

- `populate_tts_engines(self: Any) -> Any`
  - Parameters: none (instance context only).

- `release_media_player_resources(self: Any) -> Any`
  - Parameters: none (instance context only).

- `reset(self: Any) -> Any`
  - Parameters: none (instance context only).

- `reset_settings_to_default(self: Any) -> Any`
  - Parameters: none (instance context only).

- `resizeEvent(self: Any, event: Any) -> Any`
  - Parameters:
    - `event` (`Any`): Qt event object for close/resize handlers.

- `resize_table(self: Any) -> Any`
  - Parameters: none (instance context only).

- `select_table_row(self: Any, row: Any) -> Any`
  - Parameters:
    - `row` (`Any`): Table row index corresponding to a sentence entry.

- `set_audiobook_label(self: Any, text: Any) -> Any`
  - Parameters:
    - `text` (`Any`): Input parameter used by this function for its operation.

- `set_background(self: Any, file_path: Any) -> Any`
  - Parameters:
    - `file_path` (`Any`): Path to a source file selected by the user.

- `set_progress(self: Any, value: Any) -> Any`
  - Parameters:
    - `value` (`Any`): Generic numeric/string value emitted by UI controls.

- `set_row_speaker(self: Any, row: Any, speaker_id: Any, speaker_name: Any) -> Any`
  - Parameters:
    - `row` (`Any`): Table row index corresponding to a sentence entry.
    - `speaker_id` (`Any`): Numeric speaker identifier used in sentence assignment and settings lookup.
    - `speaker_name` (`Any`): Input parameter used by this function for its operation.

- `set_row_speaker_color(self: Any, row: Any, speaker_id: Any) -> Any`
  - Parameters:
    - `row` (`Any`): Table row index corresponding to a sentence entry.
    - `speaker_id` (`Any`): Numeric speaker identifier used in sentence assignment and settings lookup.

- `set_s2s_parameters(self: Any, settings: Any) -> Any`
  - Parameters:
    - `settings` (`Any`): Settings dictionary for a speaker, engine, or UI context.

- `set_start_generation_button_text(self: Any, text: Any) -> Any`
  - Parameters:
    - `text` (`Any`): Input parameter used by this function for its operation.

- `set_tts_initial_index(self: Any) -> Any`
  - Parameters: none (instance context only).

- `set_tts_parameters(self: Any, settings: Any) -> Any`
  - Parameters:
    - `settings` (`Any`): Settings dictionary for a speaker, engine, or UI context.

- `set_tts_engines(self: Any, engines: Any) -> Any`
  - Parameters:
    - `engines` (`Any`): Input parameter used by this function for its operation.

- `show_message(self: Any, title: Any, message: Any, icon: Any = QMessageBox.Information) -> Any`
  - Parameters:
    - `title` (`Any`): Dialog title text.
    - `message` (`Any`): Input parameter used by this function for its operation.
    - `icon` (`Any`): Input parameter used by this function for its operation. Default: `QMessageBox.Information`.

- `skip_current_audio(self: Any) -> Any`
  - Parameters: none (instance context only).

- `stop_audio(self: Any) -> Any`
  - Parameters: none (instance context only).

- `toggle_delete_column(self: Any) -> Any`
  - Parameters: none (instance context only).

- `toggle_engines_column(self: Any) -> Any`
  - Parameters: none (instance context only).

- `toggle_word_replacer_window(self: Any, checked: Any) -> Any`
  - Parameters:
    - `checked` (`Any`): Qt checkbox toggle state.

- `update_background(self: Any) -> Any`
  - Parameters: none (instance context only).

- `update_current_speaker_setting(self: Any, attribute: Any, value: Any) -> Any`
  - Parameters:
    - `attribute` (`Any`): Input parameter used by this function for its operation.
    - `value` (`Any`): Generic numeric/string value emitted by UI controls.

- `update_font_size_from_slider(self: Any, value: Any) -> Any`
  - Parameters:
    - `value` (`Any`): Generic numeric/string value emitted by UI controls.

- `update_generation_settings(self: Any, settings: Any) -> Any`
  - Parameters:
    - `settings` (`Any`): Settings dictionary for a speaker, engine, or UI context.

- `update_speaker_selection_combo(self: Any) -> Any`
  - Parameters: none (instance context only).

- `updatePauseLabel(self: Any, value: Any) -> Any`
  - Parameters:
    - `value` (`Any`): Generic numeric/string value emitted by UI controls.

- `update_s2s_options(self: Any, engine_name: Any) -> Any`
  - Parameters:
    - `engine_name` (`Any`): Selected inference engine name from combobox.

- `update_tts_options(self: Any, engine_name: Any) -> Any`
  - Parameters:
    - `engine_name` (`Any`): Selected inference engine name from combobox.

### `view.py` -> `AudiobookMakerView.create_widget_for_parameter`

- `update_items_based_on_dependency(_: Any) -> Any`
  - Parameters:
    - `_` (`Any`): Input parameter used by this function for its operation.

- `handle_slider_change(value: Any, attr: Any = attribute, lbl: Any = value_label, step: Any = step) -> Any`
  - Parameters:
    - `value` (`Any`): Generic numeric/string value emitted by UI controls.
    - `attr` (`Any`): Input parameter used by this function for its operation. Default: `attribute`.
    - `lbl` (`Any`): Input parameter used by this function for its operation. Default: `value_label`.
    - `step` (`Any`): Input parameter used by this function for its operation. Default: `step`.

### `view.py` -> `AudiobookSettingsDialog`

- `__init__(self: Any, global_settings: Any, parent: Any = None) -> Any`
  - Parameters:
    - `global_settings` (`Any`): Global runtime settings loaded from configs/settings.yaml.
    - `parent` (`Any`): Qt parent widget reference. Default: `None`.

- `update_global_settings(self: Any, checked: bool) -> Any`
  - Parameters:
    - `checked` (`bool`): Qt checkbox toggle state.

### `view.py` -> `MultiLineDelegate`

- `createEditor(self: Any, parent: Any, option: Any, index: Any) -> Any`
  - Parameters:
    - `parent` (`Any`): Qt parent widget reference.
    - `option` (`Any`): Qt style/delegate option object.
    - `index` (`Any`): Qt model index for row/column lookup.

- `setEditorData(self: Any, editor: Any, index: Any) -> Any`
  - Parameters:
    - `editor` (`Any`): Input parameter used by this function for its operation.
    - `index` (`Any`): Qt model index for row/column lookup.

- `setModelData(self: Any, editor: Any, model: Any, index: Any) -> Any`
  - Parameters:
    - `editor` (`Any`): Input parameter used by this function for its operation.
    - `model` (`Any`): Qt model object used by delegate/editor callbacks.
    - `index` (`Any`): Qt model index for row/column lookup.

- `updateEditorGeometry(self: Any, editor: Any, option: Any, index: Any) -> Any`
  - Parameters:
    - `editor` (`Any`): Input parameter used by this function for its operation.
    - `option` (`Any`): Qt style/delegate option object.
    - `index` (`Any`): Qt model index for row/column lookup.

### `view.py` -> `SpeakerManagementDialog`

- `__init__(self: Any, parent: Any = None, speakers: Any = None) -> Any`
  - Parameters:
    - `parent` (`Any`): Qt parent widget reference. Default: `None`.
    - `speakers` (`Any`): Speaker mapping keyed by speaker ID. Default: `None`.

- `populate_speaker_list(self: Any) -> Any`
  - Parameters: none (instance context only).

- `add_speaker(self: Any) -> Any`
  - Parameters: none (instance context only).

- `edit_speaker(self: Any, item: Any) -> Any`
  - Parameters:
    - `item` (`Any`): Qt table/list item object tied to UI callbacks.

- `delete_speaker(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_speakers(self: Any) -> Any`
  - Parameters: none (instance context only).

### `view.py` -> `UploadDialog`

- `__init__(self: Any, parent: Any = None, engines_list: Any = None) -> Any`
  - Parameters:
    - `parent` (`Any`): Qt parent widget reference. Default: `None`.
    - `engines_list` (`Any`): List of available TTS/S2S engine names for upload UI. Default: `None`.

- `_init_ui(self: Any) -> Any`
  - Parameters: none (instance context only).

- `_init_engine(self: Any) -> Any`
  - Parameters: none (instance context only).

- `browse_file(self: Any, widget: Any, param: Any) -> Any`
  - Parameters:
    - `widget` (`Any`): Qt widget instance tied to a parameter/control.
    - `param` (`Any`): Engine parameter configuration dictionary from JSON config.

- `build_engine_widgets(self: Any, engine: Any, mode: Any) -> Any`
  - Parameters:
    - `engine` (`Any`): Input parameter used by this function for its operation.
    - `mode` (`Any`): Operational mode selected in UI (for example upload mode).

- `clear_layout(self: Any, layout: Any) -> Any`
  - Parameters:
    - `layout` (`Any`): Qt layout object being built or cleared.

- `create_widget_for_parameter(self: Any, param: Any) -> Any`
  - Parameters:
    - `param` (`Any`): Engine parameter configuration dictionary from JSON config.

- `get_current_widget(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_open_file_name(self: Any, title: Any, directory: Any = '', filter: Any = '') -> Any`
  - Parameters:
    - `title` (`Any`): Dialog title text.
    - `directory` (`Any`): Input parameter used by this function for its operation. Default: `''`.
    - `filter` (`Any`): Input parameter used by this function for its operation. Default: `''`.

- `load_tts_config(self: Any, config_path: Any) -> Any`
  - Parameters:
    - `config_path` (`Any`): Path to a JSON/YAML configuration file.

- `load_s2s_config(self: Any, config_path: Any) -> Any`
  - Parameters:
    - `config_path` (`Any`): Path to a JSON/YAML configuration file.

- `on_engine_changed(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_mode_changed(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_upload_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

### `view.py` -> `WordReplacerView`

- `__init__(self: Any, parent: Any = None) -> Any`
  - Parameters:
    - `parent` (`Any`): Qt parent widget reference. Default: `None`.

- `_init_ui(self: Any) -> Any`
  - Parameters: none (instance context only).

- `add_word_to_list(self: Any) -> Any`
  - Parameters: none (instance context only).

- `close_event(self: Any, event: Any) -> Any`
  - Parameters:
    - `event` (`Any`): Qt event object for close/resize handlers.

- `del_word_in_list(self: Any) -> Any`
  - Parameters: none (instance context only).

- `do_extra(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_current_list_name(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_extra(self: Any) -> Any`
  - Parameters: none (instance context only).

- `get_new_list(self: Any) -> Any`
  - Parameters: none (instance context only).

- `load_stylesheet(self: Any, font_size: Any = '14pt') -> Any`
  - Parameters:
    - `font_size` (`Any`): UI font size value emitted from slider/settings. Default: `'14pt'`.

- `load_word_list(self: Any) -> Any`
  - Parameters: none (instance context only).

- `new_list(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_save_list_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `on_start_wr_clicked(self: Any) -> Any`
  - Parameters: none (instance context only).

- `prompt_question(self: Any, title: Any, question: Any, buttons: Any = QMessageBox.Yes | QMessageBox.No, default_button: Any = QMessageBox.No) -> Any`
  - Parameters:
    - `title` (`Any`): Dialog title text.
    - `question` (`Any`): Prompt text displayed to user in confirmation dialogs.
    - `buttons` (`Any`): Qt button bitmask for confirmation dialogs. Default: `QMessageBox.Yes | QMessageBox.No`.
    - `default_button` (`Any`): Default Qt button for dialogs. Default: `QMessageBox.No`.

- `save_list_as(self: Any) -> Any`
  - Parameters: none (instance context only).

- `save_json(self: Any, audio_map_path: Any, new_text_audio_map: Any) -> Any`
  - Parameters:
    - `audio_map_path` (`Any`): Path to sentence/audio mapping JSON file.
    - `new_text_audio_map` (`Any`): Updated sentence/audio mapping object to persist.

- `sort_list(self: Any) -> Any`
  - Parameters: none (instance context only).

- `test_repl(self: Any) -> Any`
  - Parameters: none (instance context only).

- `update_speaker_selection_combo(self: Any, list_of_speakers: Any) -> Any`
  - Parameters:
    - `list_of_speakers` (`Any`): Input parameter used by this function for its operation.

## Related Files
- `src/model.py`
- `src/view.py`
- `src/controller.py`
- `src/tts_engines.py`
- `src/s2s_engines.py`
- `configs/tts_config.json`
- `configs/s2s_config.json`
