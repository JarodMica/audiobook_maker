# controller.py 
 
import sys 
from PySide6.QtWidgets import QApplication, QMessageBox 
from PySide6.QtCore import QThread, Signal, QObject
import os
import shutil
import time
import traceback

if os.path.exists("runtime"):
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Add this directory to sys.path
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        
try:
    import styletts2
    espeak_path = os.path.join(os.path.dirname(__file__), '..', 'espeak NG')
    espeak_library = os.path.join(os.path.dirname(__file__), '..', 'espeak NG', 'libespeak-ng.dll')
    espeak_data_path = os.path.join(espeak_path, 'espeak-ng-data')
    os.environ['PHONEMIZER_ESPEAK_PATH'] = espeak_path
    os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = espeak_library
    os.environ['ESPEAK_DATA_PATH'] = espeak_data_path    
except:
    # Styletts2 not installed, so espeak not added to path
    pass

from model import AudiobookModel
from view import AudiobookMakerView


class AudioGenerationWorker(QThread):
    progress_signal = Signal(int)
    sentence_generated_signal = Signal(int, str)  # Signal to indicate a sentence has been generated

    def __init__(self, function, directory_path, is_continue, is_regen_only):
        super().__init__()
        self.function = function
        self.directory_path = directory_path
        self.is_continue = is_continue
        self.is_regen_only = is_regen_only
        self._stop_requested = False
        # self.voice_parameters = voice_parameters

    def run(self):
        # Modify the function call to pass the sentence_generated_callback
        self.function(self.directory_path, self.is_continue, self.is_regen_only, self.report_progress, self.sentence_generated_callback, self.should_stop)

    def stop(self):
        self._stop_requested = True  # Set the stop flag

    def should_stop(self):
        return self._stop_requested  # Return the stop flag

    def report_progress(self, progress):
        self.progress_signal.emit(progress)

    def sentence_generated_callback(self, idx, sentence):
        self.sentence_generated_signal.emit(idx, sentence)
        
class RegenerateAudioWorker(QThread):
    finished_signal = Signal(str, int)  # Signal to indicate completion
    error_signal = Signal(str)     # Signal to report errors

    def __init__(self, model, old_audio_path, selected_sentence, combined_parameters, new_audio_path, speaker_id):
        super().__init__()
        self.model = model
        self.old_audio_path = old_audio_path
        self.selected_sentence = selected_sentence
        self.combined_parameters = combined_parameters
        self.new_audio_path = new_audio_path
        self.speaker_id = speaker_id

    def run(self):
        # Wait until the media player has released the file
        max_retries = 10
        for i in range(max_retries):
            try:
                # Attempt to delete old audio file
                if os.path.exists(self.old_audio_path):
                    os.remove(self.old_audio_path)
                break  # Success, exit the loop
            except Exception as e:
                # If the exception is due to file in use, wait and retry
                time.sleep(0.1)  # Wait 100ms
                if i == max_retries - 1:
                    # Max retries reached, report the error
                    self.error_signal.emit(f"Failed to delete old audio file: {str(e)}")
                    return

        # Generate new audio
        print(f"regeneration id: {self.speaker_id}")
        tts_engine_name = self.combined_parameters.get('tts_engine')
        self.model.load_selected_tts_engine(tts_engine_name, self.speaker_id, **self.combined_parameters)
        
        speaker = self.model.speakers.get(self.speaker_id, {})
        speaker_settings = speaker.get('settings', {})
        use_s2s = speaker_settings.get('use_s2s', False)
        if use_s2s:
            s2s_engine_name = speaker_settings.get('s2s_engine', None)
            if s2s_engine_name:
                s2s_parameters = speaker_settings.copy()
                s2s_validated = self.model.load_selected_s2s_engine(s2s_engine_name, self.speaker_id, **s2s_parameters)
            else:
                s2s_validated = False
        else:
            s2s_validated = False
        new_audio_temp_path = self.model.generate_audio_proxy(self.selected_sentence, self.combined_parameters, s2s_validated)
        if not new_audio_temp_path:
            self.error_signal.emit("Failed to generate new audio.")
            return

        # Move new audio file to old path
        shutil.move(new_audio_temp_path, self.new_audio_path)

        # Emit finished signal
        print(f"regeneration id: {self.speaker_id}")

        self.finished_signal.emit(self.new_audio_path, self.speaker_id)

class AudiobookController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.model = AudiobookModel()
        self.view = AudiobookMakerView()
        self.view_word_replacer = None
        self.current_sentence_idx = 0
        self.tts_engine = None
        self.view.audio_finished_signal.connect(self.on_audio_finished)
        self.playing_sequence = False
        self.current_audio_index = 0
        self.current_audiobook_directory = None
        self.is_generating = False

        
        self.debug = False  # Set this to True to enable debugging mode

        # Connect signals and slots
        self.connect_signals()

        # Populate initial data
        self.populate_initial_data()

        self.view.show()
        sys.exit(self.app.exec())

    def allow_speaker_assignment(self, position):
        """
        Assigns the current selected speaker to the selected sentences when right-clicked.
        """
        if not self.current_audiobook_directory or not os.path.exists(self.current_audiobook_directory):
            # Prompt the user to create the audiobook directory
            reply = self.view.ask_question(
                "Create Audiobook Directory",
                "Please create an audiobook directory before assigning speakers. Do you want to create it now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply:
                # Initiate the audiobook directory creation process
                self.create_audiobook_directory()
            else:
                # User chose not to create the directory; do nothing or handle accordingly
                return
        
        # Audiobook directory exists; assign current speaker to selected sentences
        speaker_id, speaker_name = self.view.get_current_speaker_attributes()
        self.view.assign_speaker_to_selected(speaker_id, speaker_name)
        # Update model accordingly
        selected_rows = self.view.tableWidget.selectionModel().selectedRows(0)
        for index in selected_rows:
            row = index.row()
            self.assign_speaker_to_sentence(row, speaker_id)
    def assign_speaker_to_sentence(self, idx, speaker_id):
        self.model.assign_speaker_to_sentence(idx, speaker_id)
        if self.current_audiobook_directory:
            self.model.save_text_audio_map(self.current_audiobook_directory)
        else:
            # Handle the case where the audiobook directory is not set
            pass

    def check_and_reset_for_new_text_file(self, action_description):
        if self.model.filepath or self.model.text_audio_map:
            proceed = self.view.ask_question(
                action_description,
                f"A text file is currently loaded. {action_description} will reset all settings. Proceed?",
                buttons=QMessageBox.Yes | QMessageBox.No,
                default_button=QMessageBox.No
            )
            if not proceed:
                return False

            # Reset model and view
            self.model.reset()
            self.current_audiobook_directory = None
            self.is_generating = False
            self.view.reset()
            return True
        else:
            return True
    def clear_background_image(self):
        self.model.clear_background_image()
        self.view.background_label.clear()  # Clear the background in the view
    def clear_regen_checkboxes(self):
        if not self.current_audiobook_directory:
            self.popup_load_audiobook()
            return
        
        confirm_continue = self.view.ask_question(
            'Confirm Erasure',
            "Are you sure you want to remove ALL regen checkboxes?  If you click yes, it will clear all toggled checkboxes for regen.\n\nStill want to proceed?",
            default_button=QMessageBox.No
        )
        if not confirm_continue:
            return #stop erasure
        
        self.model.reset_regen_in_text_audio_map()
        self.model.save_text_audio_map(self.current_audiobook_directory)
        self.update_table_with_sentences()
    def connect_signals(self):
        # Connect view signals to controller methods
        self.view.clear_regen_requested.connect(self.clear_regen_checkboxes)
        self.view.continue_audiobook_generation_requested.connect(self.continue_audiobook_generation)
        self.view.delete_requested.connect(self.deletion_prompt)
        self.view.export_audiobook_requested.connect(self.export_audiobook)
        self.view.font_size_changed.connect(self.on_font_size_changed)
        self.view.generation_settings_changed.connect(self.save_generation_settings)
        self.view.load_existing_audiobook_requested.connect(self.load_existing_audiobook)
        self.view.load_text_file_requested.connect(self.load_text_file)
        # self.view.load_tts_requested.connect(self.load_tts_engine)
        self.view.pause_audio_requested.connect(self.pause_audio)
        self.view.play_all_from_selected_requested.connect(self.play_all_from_selected)
        self.view.play_selected_audio_requested.connect(self.play_selected_audio)
        self.view.regen_checkbox_toggled.connect(self.regen_checkbox_toggled)
        self.view.regenerate_audio_for_sentence_requested.connect(self.regenerate_audio_for_sentence)
        self.view.regenerate_bulk_requested.connect(self.regenerate_in_bulk)
        self.view.search_sentences_requested.connect(self.search_sentences)
        self.view.sentence_speaker_changed.connect(self.assign_speaker_to_sentence)
        self.view.set_background_clear_image_requested.connect(self.clear_background_image)
        self.view.set_background_image_requested.connect(self.set_background_image)
        self.view.s2s_engine_changed.connect(self.on_s2s_engine_changed)
        self.view.speakers_updated.connect(self.on_speakers_updated)
        self.view.start_generation_requested.connect(self.start_generation)
        self.view.stop_generation_requested.connect(self.stop_generation)
        self.view.tableWidget.customContextMenuRequested.connect(self.allow_speaker_assignment)
        self.view.text_item_changed.connect(self.update_sentence)
        self.view.toggle_delete_action_requested.connect(self.toggle_delete_column)
        self.view.tts_engine_changed.connect(self.on_tts_engine_changed)
        self.view.update_audiobook_requested.connect(self.update_audiobook)
        self.view.upload_voice_window_requested.connect(self.toggle_upload_voice_window)
        self.view.word_replacer_window_requested.connect(self.toggle_word_replacer_window)
        self.view.word_replacer_window_closed.connect(self.word_replacer_closed)
    def connect_signals_replacer(self):
        self.view.word_replacer_window.save_list_requested.connect(self.save_list)
        self.view.word_replacer_window.start_wr_requested.connect(self.start_wr)
        self.view.word_replacer_window.test_repl_s.connect(self.test_single_word)
    def connect_signals_upload_voice(self):
        self.view.upload_voice_window.upload_requested.connect(self.upload_requested)
    def continue_audiobook_generation(self):
        if not self.current_audiobook_directory:
            self.popup_load_audiobook()
            return
        
        # Attempt to load the text file
        text_file_path = os.path.join(self.current_audiobook_directory, "book_text.txt")
        if os.path.exists(text_file_path):
            # sentence_list = self.model.load_sentences(text_file_path)
            self.model.filepath = text_file_path  # Update the model's filepath
        else:
            self.view.show_message("Error", "Text file not found in the audiobook directory.", icon=QMessageBox.Warning)
            return

        # Check if text_audio_map.json exists in the selected directory
        map_file_path = os.path.join(self.current_audiobook_directory, "text_audio_map.json")
        if not os.path.exists(map_file_path):
            self.view.show_message(
                "Error", "The selected directory is not a valid Audiobook Directory.", icon=QMessageBox.Warning
            )
            return

        self.view.clear_table()
        self.model.text_audio_map.clear()

        dir_name = os.path.basename(self.current_audiobook_directory)
        self.view.set_audiobook_label(dir_name)
        
        self.model.load_text_audio_map(self.current_audiobook_directory)
            
        self.setup_interface(self.current_audiobook_directory)

        is_continue = True
        # Start the worker thread
        self.worker = AudioGenerationWorker(
            self.model.generate_audio_for_sentence_threaded,
            self.current_audiobook_directory,
            is_continue,
            False
        )
        
        self.worker.progress_signal.connect(self.view.set_progress)
        self.worker.started.connect(self.view.disable_buttons)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.sentence_generated_signal.connect(self.on_sentence_generated)
        self.worker.start()
        self.on_generation_started()  # Call this method after starting the worker
    def create_audiobook_directory(self):
        book_name = self.view.get_book_name()
        
        if not book_name:
            self.view.show_message("Error", "Please enter a book name before proceeding.", icon=QMessageBox.Warning)
            return
        directory_path = os.path.join("audiobooks", book_name)
        self.current_audiobook_directory = directory_path  # Add this line
        self.view.set_audiobook_label(book_name)
        if os.path.exists(self.current_audiobook_directory):
            overwrite = self.view.ask_question(
                'Overwrite Existing Audiobook',
                "An audiobook with this name already exists. Do you want to overwrite it?",
                default_button=QMessageBox.No
            )
            if overwrite:
                confirm_delete = self.view.ask_question(
                    'Confirm Deletion',
                    "This cannot be undone, the audiobook will be lost forever. Proceed?",
                    default_button=QMessageBox.No
                )
                if confirm_delete:
                    shutil.rmtree(self.current_audiobook_directory)
                else:
                    return
            else:
                self.current_audiobook_directory = None
                self.view.set_audiobook_label("No Audio Book Set")
                return
        os.makedirs(self.current_audiobook_directory)
        # Copy the text file to the audiobook directory
        book_text_file_destination = os.path.join(self.current_audiobook_directory, "book_text.txt")
        original_text_file = os.path.join(self.current_audiobook_directory, "original_text_file.txt")
        if not os.path.exists(book_text_file_destination):
            shutil.copy2(self.model.filepath, original_text_file)
            self.model.create_book_text_file(self.current_audiobook_directory)
        
        return self.current_audiobook_directory

    def deletion_prompt(self):
        if not self.current_audiobook_directory:
            self.popup_load_audiobook()
            return
        
        confirm_continue = self.view.ask_question(
            'Confirm Deletion',
            "You are about to delete all selected sentences.\n\nStill want to proceed?",
            default_button=QMessageBox.No
        )
        if not confirm_continue:
            return #stop generation
        
        rows_list = self.view.get_deletion_checkboxes()
        self.model.delete_sentences(rows_list)
        self.model.save_text_audio_map(self.current_audiobook_directory)
        self.model.create_book_text_file(self.current_audiobook_directory)
        self.update_table_with_sentences()
                
    def export_audiobook(self):
        directory_path = self.view.get_existing_directory("Select an Audiobook Directory")
        if not directory_path:
            return  # Exit the function if no directory was selected

        pause_duration = self.view.get_pause_between_sentences()
        try:
            output_filename = self.model.export_audiobook(directory_path, pause_duration)
            self.view.show_message("Success", f"Combined audiobook saved as {output_filename}", icon=QMessageBox.Information)
        except FileNotFoundError as e:
            self.view.show_message("Error", str(e), icon=QMessageBox.Warning)
    def extract_text(self, idx: int, concat_sentences:bool, length_search_text: int) -> str:
        text = self.model.text_audio_map[str(idx)]['sentence']
        if concat_sentences:
            additional_text =  ""
            offset = 1
            while len(additional_text) < length_search_text and idx+offset < len(self.model.text_audio_map):
                text_at_offset = self.model.text_audio_map[str(idx+offset)]['sentence']
                if len(text_at_offset) < length_search_text:
                    additional_text += text_at_offset
                    length_search_text -= len(text_at_offset)
                else:
                    additional_text += text_at_offset[:length_search_text - 1]
                    ## adding only so much to the sentence, that the search result can be found only if it overlaps with the sentence border.
                    ## and not if it is completely within the next sentence
                    break
                offset += 1
            text += additional_text
        return text.lower()

    def load_existing_audiobook(self):
        if not self.check_and_reset_for_new_text_file('Load Existing Audiobook'):
            return
        
        directory_path = self.view.get_existing_directory("Select an Audiobook Directory")
        self.current_audiobook_directory = directory_path 

        if not directory_path:
            return

        book_name = os.path.basename(directory_path)
        self.view.set_audiobook_label(book_name)

        try:
            # Attempt to load the text file
            text_file_path = os.path.join(directory_path, "book_text.txt")
            if os.path.exists(text_file_path):
                sentences = self.model.load_sentences(text_file_path)
                self.model.filepath = text_file_path  # Update the model's filepath
                # self.model.create_audio_text_map("", sentences)
            else:
                self.view.show_message("Error", "Text file not found in the audiobook directory.", icon=QMessageBox.Warning)
                return
            
            self.model.load_text_audio_map(directory_path)
            
            self.setup_interface(directory_path)
        except Exception as e:
            self.view.show_message("Error", f"An error occurred: {str(e)}", icon=QMessageBox.Warning)
    def load_text_file(self):
        if not self.check_and_reset_for_new_text_file('Load New Text File'):
            return
        book_name = self.view.get_book_name()
        if not book_name:
            self.view.show_message("Error", "Please enter a book name before proceeding.", icon=QMessageBox.Warning)
            return

        filepath = self.view.get_open_file_name(
            "Select Text File", "", "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            self.model.filepath = filepath
            sentences = self.model.load_sentences(filepath)
            if sentences:
                self.model.create_audio_text_map("", sentences)
                if not self.current_audiobook_directory:
                    if_continue = self.create_audiobook_directory()
                    if not if_continue:
                        return
                self.update_table_with_sentences()
                self.view.enable_speaker_menu()
                self.save_generation_settings()
                self.model.save_text_audio_map(self.current_audiobook_directory)
        else:
            pass

    def on_audio_finished(self):
        if self.playing_sequence:
            self.play_next_audio_in_sequence()
    def on_font_size_changed(self, font_size):
        self.view.update_font_size_from_slider(font_size)
        settings_dict = {'font_size': font_size}
        self.model.save_settings(settings_dict)
    def on_generation_finished(self):
        self.is_generating = False
        self.view.start_generation_button.setEnabled(True)
        self.view.stop_generation_button.setEnabled(False)
        self.view.enable_buttons()
        self.update_table_with_sentences()
    def on_generation_started(self):
        self.is_generating = True
        self.view.on_enable_stop_button()
        self.view.disable_buttons()
    def on_regeneration_error(self, error_message):
        self.view.show_message("Error", error_message, icon=QMessageBox.Warning)
    def on_regeneration_finished(self, map_key, new_audio_path, speaker_id):
        # Update the text_audio_map with the new audio path and speaker_id
        self.model.text_audio_map[map_key]['audio_path'] = new_audio_path
        self.model.text_audio_map[map_key]['speaker_id'] = speaker_id

        # Update the table row's background color to match the new speaker
        self.view.set_row_speaker_color(int(map_key), speaker_id)

        book_name = self.view.audiobook_label.text()
        directory_path = os.path.join("audiobooks", book_name)
        # Save the updated map back to the file
        self.model.save_text_audio_map(directory_path)
        print("Regeneration complete")
    def on_s2s_engine_changed(self, s2s_engine_name):
        # You can perform additional actions here if needed
        pass
    def on_speakers_updated(self, speakers):
        speakers = self.set_up_settings(speakers)
        
        # Update the model with the new speakers configuration
        self.model.update_speakers(speakers)
        
        # Save the updated generation settings
        self.save_generation_settings()
    def on_sentence_generated(self, idx, sentence):
        row_position = int(idx)
        item = self.model.text_audio_map[str(row_position)]
        speaker_id = item.get('speaker_id', 1)
        speaker_name = self.model.get_speaker_name(speaker_id)
        self.view.add_table_item(row_position, sentence, speaker_name)
        # self.view.resize_table()
    def on_test_word_finished(self, audio_path):
        self.view.play_audio(audio_path)
    def on_tts_engine_changed(self, speakers):
        self.on_speakers_updated(speakers)
        pass
        
    def pause_audio(self):
        self.view.pause_audio()
    def play_all_from_selected(self):
        if self.view.tableWidget.rowCount() == 0:
            return

        selected_row = self.view.get_selected_table_row()
        if selected_row >= 0:
            self.current_audio_index = selected_row
        else:
            self.current_audio_index = 0

        self.playing_sequence = True
        self.play_next_audio_in_sequence()
    def play_next_audio_in_sequence(self):
        while True:
            map_key = str(self.current_audio_index)
            if map_key in self.model.text_audio_map and self.model.text_audio_map[map_key]["generated"]:
                audio_path = self.model.text_audio_map[map_key]['audio_path']
                self.view.play_audio(audio_path)
                self.view.select_table_row(self.current_audio_index)
                self.current_audio_index += 1
                break
            else:
                # No generated audio at this index, check next
                if self.current_audio_index >= len(self.model.text_audio_map):
                    # Reached end of sentences
                    self.playing_sequence = False
                    self.current_audio_index = 0
                    break
                else:
                    self.current_audio_index += 1
    def play_selected_audio(self):
        selected_row = self.view.get_selected_table_row()
        if selected_row == -1:
            self.view.show_message("Error", "Choose a sentence to play audio for", icon=QMessageBox.Warning)
            return
        map_key = str(selected_row)
        if not self.model.text_audio_map[map_key]["generated"]:
            self.view.show_message(
                "Error", f"Sentence has not been generated for sentence {selected_row + 1}", icon=QMessageBox.Warning
            )
            return
        audio_path = self.model.text_audio_map[map_key]['audio_path']
        # Use view's media player to play audio
        self.view.play_audio(audio_path)
    def populate_initial_data(self):
        # Load settings
        settings = self.model.load_settings()
        background_image = settings.get('background_image')
        if background_image:
            self.view.set_background(background_image)

        # Populate TTS engines
        tts_engines = self.model.get_tts_engines()
        self.view.set_tts_engines(tts_engines)
        
        # **Set Default TTS Engine Selection in the Controller**
        if self.view.tts_engine_combo.count() > 0:
            self.view.tts_engine_combo.setCurrentIndex(0)
    def popup_load_audiobook(self):
        self.view.show_message("Error", "An audiobook should be loaded first", icon=QMessageBox.Warning)
    
    def regen_checkbox_toggled(self, row, state):
        self.model.change_regen_state(row, state)
        self.model.save_text_audio_map(self.current_audiobook_directory)
    def regenerate_audio_for_sentence(self):
        selected_row = self.view.get_selected_table_row()
        if selected_row == -1:
            self.view.show_message("Error", "Choose a sentence.", icon=QMessageBox.Warning)
            return

        map_key = str(selected_row)

        if not self.model.text_audio_map.get(map_key, {}).get('generated', False):
            self.view.show_message(
                "Error",
                'No audio path found, generate sentences with "Continue Audiobook" first before regenerating.',
                icon=QMessageBox.Warning
            )
            return

        selected_sentence = self.model.text_audio_map[map_key]['sentence']
        old_audio_path = self.model.text_audio_map[map_key]['audio_path']
        speaker_id = self.model.text_audio_map[map_key]['speaker_id']
        audio_path_parent = os.path.dirname(old_audio_path)
        generation_settings = self.model.load_generation_settings(audio_path_parent)

        # Check if the audio file is being played
        if self.view.is_audio_playing(old_audio_path):
            if self.view.playing_sequence:
                # Skip to next audio in sequence
                self.view.skip_current_audio()
            else:
                # Stop playback
                self.view.stop_audio()

        # Prepare new audio path (use a temporary file)
        new_audio_path = old_audio_path  # We'll overwrite the old file

        # Get speaker settings
        speaker = self.model.speakers.get(speaker_id, {})
        combined_parameters = speaker.get('settings', {})

        # Start the regeneration worker
        self.regen_worker = RegenerateAudioWorker(
            self.model,
            old_audio_path,
            selected_sentence,
            combined_parameters,
            new_audio_path,
            speaker_id
        )
        self.regen_worker.finished_signal.connect(
            lambda path, speaker_id=speaker_id: self.on_regeneration_finished(map_key, path, speaker_id)
        )
        self.regen_worker.error_signal.connect(self.on_regeneration_error)
        self.regen_worker.start()
    def regenerate_in_bulk(self):
        if not self.current_audiobook_directory:
            self.popup_load_audiobook()
            return
        
        is_continue = False
        is_regen_only = True
        # Start the worker thread
        self.worker = AudioGenerationWorker(
            self.model.generate_audio_for_sentence_threaded,
            self.current_audiobook_directory,
            is_continue,
            is_regen_only
        )
        
        self.worker.progress_signal.connect(self.view.set_progress)
        self.worker.started.connect(self.view.disable_buttons)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.sentence_generated_signal.connect(self.on_sentence_generated)
        self.worker.start()
        self.on_generation_started()  # Call this method after starting the worker

    def save_generation_settings(self):
        self.model.update_speakers(self.view.speakers)
        if self.current_audiobook_directory:
            self.model.save_generation_settings(self.current_audiobook_directory, self.model.speakers)
        else:
            self.model.save_temp_generation_settings(self.model.speakers)
    def save_list(self):
        list_name = self.view.word_replacer_window.get_current_list_name()
        save_location = os.path.join(self.current_audiobook_directory, list_name)
        if list_name == '':
            self.view.show_message('No Name', "Please enter a name for the list or create a new list.")
            return
        if save_location and list_name != "":
            continue_q = self.view.ask_question("List Exists", f"A list in this Audibook's directory already exists with the name '{list_name}'.\n\nContinue and overwrite the old list?")
            if not continue_q:
                return
        
        new_wordlist = self.view.word_replacer_window.get_new_list()
        self.view.word_replacer_window.save_json(save_location, new_wordlist)        
    def search_sentences(self, start_idx:int, forward:bool, search_text:str, concat_sentences:bool):
        if not search_text:
            return
        length_search_text = len(search_text)
        search_text = search_text.lower()
        if forward:
            for idx in range(start_idx + 1, len(self.model.text_audio_map)):
                if search_text in self.extract_text(idx, concat_sentences, length_search_text):
                    self.view.select_table_row(idx)
                    return
            for idx in range(0, start_idx):
                if search_text in self.extract_text(idx, concat_sentences, length_search_text):
                    self.view.select_table_row(idx)
                    return
        else:
            for idx in range(start_idx - 1, -1, -1):
                if search_text in self.extract_text(idx, concat_sentences, length_search_text):
                    self.view.select_table_row(idx)
                    return
            for idx in range(len(self.model.text_audio_map)-1, start_idx, -1):
                if search_text in self.extract_text(idx, concat_sentences, length_search_text):
                    self.view.select_table_row(idx)
                    return
    def set_background_image(self): 
        file_name = self.view.get_open_file_name("", "", "Image Files (*.png *.jpg *.jpeg);;All Files (*)") 
        if file_name: 
            destination_path = self.model.set_background_image(file_name)
            self.view.set_background(destination_path)
    def set_up_settings(self, speakers=None):
        if not speakers:
            speakers = self.view.speakers
        tts_parameters = self.view.get_tts_engine_parameters()
        s2s_parameters = self.view.get_s2s_engine_parameters()
        merged_parameters = {**tts_parameters, **s2s_parameters}
        
        for speaker_id, speaker in speakers.items():
            # Iterate over each key-value pair in the merged parameters
            for key, value in merged_parameters.items():
                # Add the key to the speaker's settings if it doesn't already exist
                if key not in speaker['settings']:
                    speaker['settings'][key] = value

        return speakers
    def setup_interface(self, directory_path):
        # Load generation settings, including speakers
        generation_settings = self.model.load_generation_settings(directory_path)
        # The model's speakers are already loaded in the above call
        self.view.update_generation_settings(generation_settings)

        # Now update the table with sentences
        self.update_table_with_sentences()
        self.view.enable_speaker_menu()
    def start_generation(self):
        if hasattr(self.model, 'filepath') and self.model.filepath:
            if not self.current_audiobook_directory:
                directory_path = self.create_audiobook_directory()

            directory_path = self.current_audiobook_directory

            # Copy the text file to the audiobook directory
            book_text_file_destination = os.path.join(directory_path, "book_text.txt")
            original_text_file = os.path.join(directory_path, "original_text_file.txt")
            if not os.path.exists(book_text_file_destination):
                shutil.copy2(self.model.filepath, original_text_file)
                self.model.create_book_text_file(self.current_audiobook_directory)

            # Load existing text_audio_map if it exists
            map_file_path = os.path.join(directory_path, "text_audio_map.json")
            if os.path.exists(map_file_path):
                self.model.load_text_audio_map(directory_path)
                if self.model.text_audio_map["0"]["generated"]:
                    confirm_continue = self.view.ask_question(
                        'Confirm Start',
                        "WAIT! You've already started generating an audiobook.  If you click yes, it will start and OVERRIDE existing audio files.  If you want to continue generation from where you left off, please click 'Continue Audiobook Generation' instead.\n\nStill want to proceed?",
                        default_button=QMessageBox.No
                    )
                    if not confirm_continue:
                        return #stop generation
            else:
                self.model.text_audio_map.clear()

            sentence_list = self.model.load_sentences(self.model.filepath)

            # Update text_audio_map with new sentences
            self.model.update_text_audio_map(sentence_list)

            # Save the updated map
            self.model.save_text_audio_map(directory_path)

            # Update the view's table
            self.update_table_with_sentences()

            # Save generation settings if needed
            if self.model.load_generation_settings(directory_path) == {}: #no generation settings saved
                self.view.speakers = self.set_up_settings()
                self.save_generation_settings()
                
            if self.debug:
                # Run in main thread for debugging
                self.view.disable_buttons()
                try:
                    self.model.generate_audio_for_sentence_threaded(
                        directory_path,
                        False,  # is continue
                    False,  # is regen
                    self.view.set_progress,  # Progress callback
                    self.on_sentence_generated,  # Sentence generated callback
                    lambda: False  # should_stop_callback always returns False in debug mode
                    )
                except Exception as e:
                    traceback.print_exc()
                    self.view.enable_buttons()
                    return
                self.view.enable_buttons()
                
                self.on_generation_finished()
            else:
                # Start the worker thread
                self.worker = AudioGenerationWorker(
                    self.model.generate_audio_for_sentence_threaded,
                    directory_path,
                    False, # is continue
                    False # is regen
                )
                self.worker.progress_signal.connect(self.view.set_progress)
                self.worker.started.connect(self.view.disable_buttons)
                self.worker.finished.connect(self.on_generation_finished)
                self.worker.sentence_generated_signal.connect(self.on_sentence_generated)
                self.worker.start()
                self.on_generation_started()  # Call this method after starting the worker

        else:
            self.view.show_message("Error", "Please pick a text file before generating audio.", icon=QMessageBox.Warning)
            return
    def start_wr(self):
        replacement_list_name = self.view.word_replacer_window.list_name_input.text()
        replacement_list_path = os.path.join(self.current_audiobook_directory, replacement_list_name)
        extra = self.view.word_replacer_window.get_extra()
        if not os.path.exists(replacement_list_path) or replacement_list_name == "":
            self.view.show_message("List Missing", "List not saved to current directory, please save it first then run this.")
            return
        continue_wr = self.view.ask_question("Word Replacement", "This will begin word replacement for all items in the list, meaning all instances found in the audiobook will be replaced\n\nProceed?", default_button=QMessageBox.No)
        if not continue_wr:
            return
        self.model.replace_words_from_list(replacement_list_path, extra)
        self.model.save_text_audio_map(self.current_audiobook_directory)
        self.update_table_with_sentences()
    def stop_generation(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
        self.is_generating = False
        self.view.enable_buttons()
        self.view.on_disable_stop_button()

    def update_audiobook(self):
        if not self.check_and_reset_for_new_text_file('Update Audiobook'):
            return
        directory_path = self.view.get_existing_directory("Select an Audiobook Directory")
        self.current_audiobook_directory = directory_path  # Add this line

        if not directory_path:
            return
        
        filePath = self.view.get_open_file_name(
            "Choose a Text file to update with", "", "Text Files (*.txt);;All Files (*)"
        )
        if not filePath:
            return

        self.view.clear_table()
        self.model.text_audio_map.clear()
        sentence_list = self.model.load_sentences(filePath)

        proceed = self.view.ask_question(
            'Update Existing Audiobook',
            "This will delete audio for existing sentences if they have been modified as well. Do you want to proceed?",
            default_button=QMessageBox.No
        )
        if not proceed:
            return
    
        dir_basename = os.path.basename(directory_path)
        audiobook_path = os.path.join("audiobooks", dir_basename)
        self.view.set_audiobook_label(dir_basename)

        try:
            book_text_file_destination = os.path.join(directory_path, "book_text.txt")
            # shutil.copy2(filePath, text_file_destination)
            self.model.create_book_text_file(self.current_audiobook_directory)
            self.model.filepath = book_text_file_destination  # Update the model's filepath
            
            self.model.update_audiobook(
                directory_path, sentence_list
                )
            self.setup_interface(directory_path)
            
        except Exception as e:
            self.view.show_message("Error", f"An error occurred: {str(e)}", icon=QMessageBox.Warning)
    def update_sentence(self, row, new_text):
        self.model.update_sentence_in_text_audio_map(row, new_text)
        self.model.save_text_audio_map(self.current_audiobook_directory)
        self.model.create_book_text_file(self.current_audiobook_directory)
        self.update_table_with_sentences()
    def update_speakers(self, speakers):
        self.model.update_speakers(speakers)
        self.view.update_speaker_selection_combo()

    def update_table_with_sentences(self):
        self.view.clear_table()
        total_sentences = len(self.model.text_audio_map)
        self.view.tableWidget.setRowCount(total_sentences)  # Set the total number of rows upfront
        for idx_str in sorted(self.model.text_audio_map.keys(), key=lambda x: int(x)):
            sentence, row_position, speaker_id, speaker_name, regen_state = self.model.get_map_keys_and_values(idx_str)
            self.view.add_table_item(row_position, sentence, speaker_name, regen_state)
            self.view.set_row_speaker_color(row_position, speaker_id)
        self.view.resize_table()
    def upload_requested(self, mode, save_items):
        try:
            self.model.process_upload_items(mode, save_items)
            new_name = None
            for item in save_items:
                if 'name' in item:
                    new_name = item['name']
                    break
            if new_name:
                speaker_id, _ = self.view.get_current_speaker_attributes()
                self.view.speakers.setdefault(speaker_id, {}).setdefault('settings', {})['gpt_sovits_voice'] = new_name
                self.view.load_speaker_settings(speaker_id)
                self.save_generation_settings()
            self.view.show_message("Upload Complete", "File upload complete.")
        except Exception as e:
            self.view.show_message("Upload Error", f"{str(e)}", icon=QMessageBox.Warning)
    def test_single_word(self, chosen_word, speaker):
        testdir = os.path.join(os.getcwd(),'test')
        if os.path.exists(testdir) == False:os.mkdir(testdir)
        testpath = os.path.join(testdir,'test.wav')
        
        speakers_dict = self.model.speakers
        for key in speakers_dict:
            if speakers_dict[key]['name'] == speaker:
                speaker_id = key

        if self.view.is_audio_playing(testpath):
            self.view.stop_audio()
        speaker = self.model.speakers.get(speaker_id, {})
        combined_parameters = speaker.get('settings', {})
        
        self.regen_worker = RegenerateAudioWorker(
            model=self.model,
            old_audio_path=testpath,
            selected_sentence=chosen_word,
            combined_parameters=combined_parameters,
            new_audio_path=testpath,
            speaker_id=speaker_id
        )
        
        self.regen_worker.finished_signal.connect(self.on_test_word_finished)
        self.regen_worker.error_signal.connect(self.on_regeneration_error)
        self.regen_worker.start()
    def toggle_delete_column(self):
        self.view.toggle_delete_column()   
    def toggle_upload_voice_window(self):
        tts_engines = self.model.get_tts_engines()
        s2s_engines = self.model.get_s2s_engines()
        engines_list = tts_engines + s2s_engines
        self.view.open_upload_voice_window(engines_list)
        self.connect_signals_upload_voice()

    def toggle_word_replacer_window(self, checked):
        if self.current_audiobook_directory == None:
            self.view.show_message("Replacer Window Error", "Please load an audiobook first.")
            self.word_replacer_closed()
            return
        if checked:
            if self.view.word_replacer_window is None:
                self.view.open_word_replacer_window(parent=self.view)
                self.view.word_replacer_window.update_speaker_selection_combo(self.view.get_available_speakers())
            self.view.word_replacer_window.show()
            self.view.word_replacer_window.raise_()
            self.view.word_replacer_window.activateWindow()
            self.connect_signals_replacer()
        else:
            if self.view.word_replacer_window is not None:
                self.view.word_replacer_window.blockSignals(True)
                self.view.word_replacer_window.close()
                self.view.word_replacer_window.blockSignals(False)
                self.view.word_replacer_window = None
                
    def word_replacer_closed(self):
        self.view.word_replacer_window = None
        # Uncheck the QAction without triggering the toggled signal again
        self.view.word_replacer_action.blockSignals(True)
        self.view.word_replacer_action.setChecked(False)
        self.view.word_replacer_action.blockSignals(False)
        



if __name__ == '__main__':
    
    controller = AudiobookController()
