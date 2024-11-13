# controller.py 
 
import sys 
from PySide6.QtWidgets import QApplication, QMessageBox 
from PySide6.QtCore import QThread, Signal, QObject
import os
import shutil
import time

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

    def __init__(self, function, directory_path, is_continue):
        super().__init__()
        self.function = function
        self.directory_path = directory_path
        self.is_continue = is_continue
        self._stop_requested = False
        # self.voice_parameters = voice_parameters

    def run(self):
        # Modify the function call to pass the sentence_generated_callback
        self.function(self.directory_path, self.is_continue, self.report_progress, self.sentence_generated_callback, self.should_stop)

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

class LoadTTSWorker(QThread):
    success_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, model, tts_engine_name, parameters):
        super().__init__()
        self.model = model
        self.tts_engine_name = tts_engine_name
        self.parameters = parameters

    def run(self):
        try:
            self.model.load_selected_tts_engine(
                chosen_tts_engine=self.tts_engine_name,
                **self.parameters
            )
            self.success_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))

class AudiobookController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.model = AudiobookModel()
        self.view = AudiobookMakerView()
        self.current_sentence_idx = 0
        self.tts_engine = None
        self.view.audio_finished_signal.connect(self.on_audio_finished)
        self.playing_sequence = False
        self.current_audio_index = 0
        self.current_audiobook_directory = None
        self.is_generating = False
        self.regen_mode = False

        
        self.debug = False  # Set this to True to enable debugging mode


        # Connect signals and slots
        self.connect_signals()

        # Populate initial data
        self.populate_initial_data()

        self.view.show()
        sys.exit(self.app.exec())

    def connect_signals(self):
        # Connect view signals to controller methods
        self.view.load_text_file_requested.connect(self.load_text_file)
        self.view.load_tts_requested.connect(self.load_tts_engine)
        self.view.start_generation_requested.connect(self.start_generation)
        self.view.play_selected_audio_requested.connect(self.play_selected_audio)
        self.view.pause_audio_requested.connect(self.pause_audio)
        self.view.play_all_from_selected_requested.connect(self.play_all_from_selected)
        self.view.regenerate_audio_for_sentence_requested.connect(self.regenerate_audio_for_sentence)
        self.view.continue_audiobook_generation_requested.connect(self.continue_audiobook_generation)
        self.view.load_existing_audiobook_requested.connect(self.load_existing_audiobook)
        self.view.update_audiobook_requested.connect(self.update_audiobook)
        self.view.export_audiobook_requested.connect(self.export_audiobook)
        self.view.set_background_image_requested.connect(self.set_background_image)
        self.view.set_background_clear_image_requested.connect(self.clear_background_image)
        self.view.tts_engine_changed.connect(self.on_tts_engine_changed)
        self.view.speakers_updated.connect(self.on_speakers_updated)
        self.view.regen_mode_activated.connect(self.change_regen_mode)

        self.view.sentence_speaker_changed.connect(self.assign_speaker_to_sentence)
        self.view.tableWidget.customContextMenuRequested.connect(self.allow_speaker_assignment)
        self.view.generation_settings_changed.connect(self.save_generation_settings)
        self.view.s2s_engine_changed.connect(self.on_s2s_engine_changed)
        self.view.stop_generation_requested.connect(self.stop_generation)


        # No need to connect font size and voice setting signals if they are handled in the view
        
    def change_regen_mode(self, regen_mode):
        if regen_mode:
            self.regen_mode = True
            self.view.clear_table()
            total_sentences = len(self.model.text_audio_map)
            self.view.tableWidget.setRowCount(total_sentences)  # Set the total number of rows upfront
            for idx_str in sorted(self.model.text_audio_map.keys(), key=lambda x: int(x)):
                item = self.model.text_audio_map[idx_str]
                sentence = item['sentence']
                row_position = int(idx_str)
                self.view.add_table_item(row_position, sentence)
                # Make this toggleable in the future
                # speaker_id = item.get('speaker_id', 1)  
                # self.view.set_row_speaker(row_position, speaker_id)
        else:
            self.regen_mode = False
            self.update_table_with_sentences()
            
        
        
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

        # print("Merged Parameters:", merged_parameters)
        # print("Updated Speakers:", speakers)
        return speakers

    def on_speakers_updated(self, speakers):
        speakers = self.set_up_settings(speakers)
        
        # Update the model with the new speakers configuration
        self.model.update_speakers(speakers)
        
        # Save the updated generation settings
        self.save_generation_settings()


    def on_s2s_engine_changed(self, s2s_engine_name):
        # You can perform additional actions here if needed
        pass

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
        speaker_id = self.view.get_current_speaker_id()
        self.view.assign_speaker_to_selected(speaker_id)
        # Update model accordingly
        selected_rows = self.view.tableWidget.selectionModel().selectedRows()
        for index in selected_rows:
            row = index.row()
            self.assign_speaker_to_sentence(row, speaker_id)


    def on_tts_engine_changed(self, speakers):
        self.on_speakers_updated(speakers)
        pass
    

    def assign_speaker_to_sentence(self, idx, speaker_id):
        self.model.assign_speaker_to_sentence(idx, speaker_id, self.regen_mode)
        # Save the updated text_audio_map
        directory_path = self.current_audiobook_directory
        if directory_path:
            self.model.save_text_audio_map(directory_path)
        else:
            # Handle the case where the audiobook directory is not set
            pass

    def save_generation_settings(self):
        self.model.update_speakers(self.view.speakers)
        if self.current_audiobook_directory:
            self.model.save_generation_settings(self.current_audiobook_directory, self.model.speakers)
        else:
            self.model.save_temp_generation_settings(self.model.speakers)

    
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
            

    def update_speakers(self, speakers):
        self.model.update_speakers(speakers)
        self.view.update_speaker_selection_combo()

        
    def load_text_file(self):
        if not self.check_and_reset_for_new_text_file('Load New Text File'):
            return

        filepath = self.view.get_open_file_name(
            "Select Text File", "", "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            self.model.filepath = filepath
            sentences = self.model.load_sentences(filepath)
            if sentences:
                self.model.create_audio_text_map("", sentences)
                self.update_table_with_sentences()
                self.view.enable_speaker_menu()
        else:
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
            self.view.toggle_regeneration_mode(False)
            self.model.reset()
            self.current_audiobook_directory = None
            self.is_generating = False
            self.view.reset()
            return True
        else:
            return True

        
    def load_tts_engine(self):
        engine_to_use = self.view.get_tts_engine()
        parameters = self.view.get_tts_engine_parameters()

        # Create and start the worker thread
        self.load_tts_worker = LoadTTSWorker(self.model, engine_to_use, parameters)
        self.load_tts_worker.success_signal.connect(self.on_tts_loaded_success)
        self.load_tts_worker.error_signal.connect(self.on_tts_loaded_error)
        self.load_tts_worker.finished.connect(lambda: self.view.set_load_tts_button_enabled(True))
        self.load_tts_worker.start()
    
    def create_audiobook_directory(self):
        book_name = self.view.get_book_name()
        

        if not book_name:
            self.view.show_message("Error", "Please enter a book name before proceeding.", icon=QMessageBox.Warning)
            return
        directory_path = os.path.join("audiobooks", book_name)
        self.current_audiobook_directory = directory_path  # Add this line
        self.view.set_audiobook_label(book_name)
        if os.path.exists(directory_path):
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
                    shutil.rmtree(directory_path)
                else:
                    return
            else:
                self.current_audiobook_directory = None
                self.view.set_audiobook_label("No Audio Book Set")
                return
        os.makedirs(directory_path)
        # Copy the text file to the audiobook directory
        text_file_destination = os.path.join(directory_path, "book_text.txt")
        if not os.path.exists(text_file_destination):
            shutil.copy2(self.model.filepath, text_file_destination)
        
        return directory_path

    def start_generation(self):
        self.view.toggle_regeneration_mode(False)
        if hasattr(self.model, 'filepath') and self.model.filepath:
            if not self.current_audiobook_directory:
                directory_path = self.create_audiobook_directory()

            directory_path = self.current_audiobook_directory

            # Copy the text file to the audiobook directory
            text_file_destination = os.path.join(directory_path, "book_text.txt")
            if not os.path.exists(text_file_destination):
                shutil.copy2(self.model.filepath, text_file_destination)

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
                self.view.disable_buttons()  # Disable buttons before starting
                self.model.generate_audio_for_sentence_threaded(
                    directory_path,
                    False,
                    self.view.set_progress,  # Progress callback
                    self.on_sentence_generated  # Sentence generated callback
                )
                self.view.enable_buttons()  # Re-enable buttons after finishing
                self.on_generation_finished()  # Perform any post-generation tasks
            else:
                # Start the worker thread
                self.worker = AudioGenerationWorker(
                    self.model.generate_audio_for_sentence_threaded,
                    directory_path,
                    False
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

    def stop_generation(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
        self.is_generating = False
        self.view.enable_buttons()
        self.view.on_disable_stop_button()
        
    def on_generation_started(self):
        self.is_generating = True
        self.view.on_enable_stop_button()
        self.view.disable_buttons()


    def on_sentence_generated(self, idx, sentence):
        row_position = int(idx)
        self.view.add_table_item(row_position, sentence)


    def on_generation_finished(self):
        self.is_generating = False
        self.view.start_generation_button.setEnabled(True)
        self.view.stop_generation_button.setEnabled(False)
        self.view.enable_buttons()
        self.update_table_with_sentences()


    def update_table_with_sentences(self):
        self.view.clear_table()
        total_sentences = len(self.model.text_audio_map)
        self.view.tableWidget.setRowCount(total_sentences)  # Set the total number of rows upfront
        for idx_str in sorted(self.model.text_audio_map.keys(), key=lambda x: int(x)):
            item = self.model.text_audio_map[idx_str]
            sentence = item['sentence']
            row_position = int(idx_str)
            self.view.add_table_item(row_position, sentence)
            speaker_id = item.get('speaker_id', 1)  
            self.view.set_row_speaker(row_position, speaker_id)


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

    def on_audio_finished(self):
        if self.playing_sequence:
            self.play_next_audio_in_sequence()


    def regenerate_audio_for_sentence(self):
        
        selected_row = self.view.get_selected_table_row()
        if selected_row == -1:
            self.view.show_message("Error", "Choose a sentence.", icon=QMessageBox.Warning)
            return

        self.view.toggle_regeneration_mode(False)
        map_key = str(selected_row)

        if not self.model.text_audio_map.get(map_key, {}).get('generated', False):
            self.view.show_message(
                "Error",
                'No audio path found, generate sentences with "Continue Audiobook" first before regenerating.',
                icon=QMessageBox.Warning
            )
            return

        # # Get the speaker_id from the combobox
        # speaker_id = self.view.get_current_speaker_id()

        selected_sentence = self.model.text_audio_map[map_key]['sentence']
        old_audio_path = self.model.text_audio_map[map_key]['audio_path']
        speaker_id = self.model.text_audio_map[map_key]['speaker_id']
        audio_path_parent = os.path.dirname(old_audio_path)
        generation_settings = self.model.load_generation_settings(audio_path_parent)
        # voice_parameters = generation_settings

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
        # Modify the connection to pass speaker_id to the handler
        # print(speaker_id)
        self.regen_worker.finished_signal.connect(
            lambda path, speaker_id=speaker_id: self.on_regeneration_finished(map_key, path, speaker_id)
        )
        self.regen_worker.error_signal.connect(self.on_regeneration_error)
        self.regen_worker.start()

        
    def on_regeneration_finished(self, map_key, new_audio_path, speaker_id):
        # Update the text_audio_map with the new audio path and speaker_id
        self.model.text_audio_map[map_key]['audio_path'] = new_audio_path
        self.model.text_audio_map[map_key]['speaker_id'] = speaker_id

        # Update the table row's background color to match the new speaker
        self.view.set_row_speaker(int(map_key), speaker_id)

        book_name = self.view.audiobook_label.text()
        directory_path = os.path.join("audiobooks", book_name)
        # Save the updated map back to the file
        self.model.save_text_audio_map(directory_path)
        print("Regeneration complete")


    def on_regeneration_error(self, error_message):
        self.view.show_message("Error", error_message, icon=QMessageBox.Warning)

    def continue_audiobook_generation(self):
        self.view.toggle_regeneration_mode(False)
        if not self.current_audiobook_directory:
            self.current_audiobook_directory = self.view.get_existing_directory("Select an Audiobook to Continue Generating")
        
        directory_path = self.current_audiobook_directory  # Add this line

        if not directory_path:
            return  # Exit the function if no directory was selected
        
        # Attempt to load the text file
        text_file_path = os.path.join(directory_path, "book_text.txt")
        if os.path.exists(text_file_path):
            sentence_list = self.model.load_sentences(text_file_path)
            self.model.filepath = text_file_path  # Update the model's filepath
        else:
            self.view.show_message("Error", "Text file not found in the audiobook directory.", icon=QMessageBox.Warning)
            return

        # Check if text_audio_map.json exists in the selected directory
        map_file_path = os.path.join(directory_path, "text_audio_map.json")
        if not os.path.exists(map_file_path):
            self.view.show_message(
                "Error", "The selected directory is not a valid Audiobook Directory.", icon=QMessageBox.Warning
            )
            return

        self.view.clear_table()
        self.model.text_audio_map.clear()

        dir_name = os.path.basename(directory_path)
        self.view.set_audiobook_label(dir_name)
        
        self.model.load_text_audio_map(directory_path)
            
        self.setup_interface(directory_path)

        is_continue = True
        # Start the worker thread
        self.worker = AudioGenerationWorker(
            self.model.generate_audio_for_sentence_threaded,
            directory_path,
            is_continue
        )
        self.worker.progress_signal.connect(self.view.set_progress)
        self.worker.started.connect(self.view.disable_buttons)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.sentence_generated_signal.connect(self.on_sentence_generated)
        self.worker.start()
        self.on_generation_started()  # Call this method after starting the worker


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
                self.model.create_audio_text_map("", sentences)
            else:
                self.view.show_message("Error", "Text file not found in the audiobook directory.", icon=QMessageBox.Warning)
                return
            
            self.model.load_text_audio_map(directory_path)
            
            self.setup_interface(directory_path)
        except Exception as e:
            self.view.show_message("Error", f"An error occurred: {str(e)}", icon=QMessageBox.Warning)


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
            text_file_destination = os.path.join(directory_path, "book_text.txt")
            shutil.copy2(filePath, text_file_destination)
            self.model.filepath = text_file_destination  # Update the model's filepath
            

            self.model.update_audiobook(
                directory_path, sentence_list
                )
            self.setup_interface(directory_path)
            
        except Exception as e:
            self.view.show_message("Error", f"An error occurred: {str(e)}", icon=QMessageBox.Warning)

    def setup_interface(self, directory_path):
        # Load generation settings, including speakers
        generation_settings = self.model.load_generation_settings(directory_path)
        # The model's speakers are already loaded in the above call
        self.view.update_generation_settings(generation_settings)

        # Now update the table with sentences
        self.update_table_with_sentences()
        self.view.enable_speaker_menu()

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

    def set_background_image(self): 
        file_name = self.view.get_open_file_name("", "", "Image Files (*.png *.jpg *.jpeg);;All Files (*)") 
        if file_name: 
            destination_path = self.model.set_background_image(file_name)
            self.view.set_background(destination_path)

    def clear_background_image(self):
        self.model.clear_background_image()
        self.view.background_label.clear()  # Clear the background in the view

if __name__ == '__main__':
    controller = AudiobookController()