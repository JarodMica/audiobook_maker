# controller.py

import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QThread, Signal, QObject

from model import AudiobookModel
from view import AudiobookMakerView

import os
import shutil
import time

class AudioGenerationWorker(QThread):
    progress_signal = Signal(int)
    sentence_generated_signal = Signal(int, str)  # Signal to indicate a sentence has been generated

    def __init__(self, function, directory_path, voice_parameters):
        super().__init__()
        self.function = function
        self.directory_path = directory_path
        self.voice_parameters = voice_parameters

    def run(self):
        # Modify the function call to pass the sentence_generated_callback
        self.function(self.directory_path, self.report_progress, self.voice_parameters, self.sentence_generated_callback)

    def report_progress(self, progress):
        self.progress_signal.emit(progress)

    def sentence_generated_callback(self, idx, sentence):
        self.sentence_generated_signal.emit(idx, sentence)
        
class RegenerateAudioWorker(QThread):
    finished_signal = Signal(str)  # Signal to indicate completion
    error_signal = Signal(str)     # Signal to report errors

    def __init__(self, model, old_audio_path, selected_sentence, voice_parameters, new_audio_path):
        super().__init__()
        self.model = model
        self.old_audio_path = old_audio_path
        self.selected_sentence = selected_sentence
        self.voice_parameters = voice_parameters
        self.new_audio_path = new_audio_path

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
        new_audio_temp_path = self.model.generate_audio(self.selected_sentence, self.voice_parameters)
        if not new_audio_temp_path:
            self.error_signal.emit("Failed to generate new audio.")
            return

        # Move new audio file to old path
        shutil.move(new_audio_temp_path, self.new_audio_path)

        # Emit finished signal
        self.finished_signal.emit(self.new_audio_path)


class AudiobookController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.model = AudiobookModel()
        self.view = AudiobookMakerView()
        self.current_sentence_idx = 0

        # Connect signals and slots
        self.connect_signals()

        # Populate initial data
        self.populate_initial_data()

        self.view.show()
        sys.exit(self.app.exec())

    def connect_signals(self):
        # Connect view signals to controller methods
        self.view.load_text_file_requested.connect(self.load_text_file)
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
        # No need to connect font size and voice setting signals if they are handled in the view

    def populate_initial_data(self):
        # Load background image from settings
        background_image = self.model.load_settings()
        if background_image:
            self.view.set_background(background_image)

        # Populate voice models and indexes
        voice_models = self.model.get_voice_models()
        self.view.set_voice_models(voice_models)
        voice_indexes = self.model.get_voice_indexes()
        self.view.set_voice_indexes(voice_indexes)

    def load_text_file(self):
        filepath = self.view.get_open_file_name(
            "Select Text File", "", "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            self.model.filepath = filepath
        else:
            # Handle case where no file is selected
            pass

    def start_generation(self):
        if hasattr(self.model, 'filepath') and self.model.filepath:
            book_name = self.view.get_book_name()
            if not book_name:
                self.view.show_message("Error", "Please enter a book name before proceeding.", icon=QMessageBox.Warning)
                return
            directory_path = os.path.join("audiobooks", book_name)
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
                        # Delete the old audiobook directory and its contents
                        shutil.rmtree(directory_path)
                    else:
                        return
                else:
                    return
            os.makedirs(directory_path)
            self.view.clear_table()
            self.model.text_audio_map.clear()
            sentence_list = self.model.load_sentences(self.model.filepath)
            self.model.create_audio_text_map(directory_path, sentence_list)
            # Save generation settings
            voice_parameters = {
                'selected_voice': self.view.get_voice_model(),
                'selected_index': self.view.get_voice_index(),
                'f0_pitch': self.view.get_voice_pitch(),
                'index_rate': self.view.get_voice_index_effect(),
            }
            self.model.save_generation_settings(directory_path, voice_parameters)

            # Start the worker thread
            self.worker = AudioGenerationWorker(
                self.model.generate_audio_for_sentence_threaded,
                directory_path,
                voice_parameters
            )
            self.worker.progress_signal.connect(self.view.set_progress)
            self.worker.started.connect(self.view.disable_buttons)
            self.worker.finished.connect(self.on_generation_finished)
            # Connect the new signal
            self.worker.sentence_generated_signal.connect(self.on_sentence_generated)
            self.worker.start()
        else:
            self.view.show_message("Error", "Please pick a text file before generating audio.", icon=QMessageBox.Warning)
            return

    def on_sentence_generated(self, idx, sentence):
        # Update the table with the new sentence
        row_position = int(idx)
        self.view.add_table_item(row_position, sentence)

    def on_generation_finished(self):
        self.view.enable_buttons()
        # The table has already been updated during generation

    def update_table_with_sentences(self):
        self.view.clear_table()
        for idx_str, item in self.model.text_audio_map.items():
            sentence = item['sentence']
            row_position = int(idx_str)
            self.view.add_table_item(row_position, sentence)

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
            self.current_sentence_idx = selected_row
        else:
            self.current_sentence_idx = 0

        # Prepare the list of audio paths and corresponding indices
        sorted_audio_paths = []
        indices = []
        for idx in range(self.current_sentence_idx, len(self.model.text_audio_map)):
            map_key = str(idx)
            if map_key in self.model.text_audio_map:
                if self.model.text_audio_map[map_key]["generated"]:
                    audio_path = self.model.text_audio_map[map_key]['audio_path']
                    sorted_audio_paths.append(audio_path)
                    indices.append(idx)

        # Use view's media player to play audio sequence and highlight sentences
        self.view.play_audio_sequence(sorted_audio_paths, indices)

    def regenerate_audio_for_sentence(self):
        selected_row = self.view.get_selected_table_row()
        if selected_row == -1:
            self.view.show_message("Error", "Choose a sentence.", icon=QMessageBox.Warning)
            return

        map_key = str(selected_row)
        if not self.model.text_audio_map[map_key]['generated']:
            self.view.show_message(
                "Error",
                'No audio path found, generate sentences with "Continue Audiobook" first before regenerating.',
                icon=QMessageBox.Warning
            )
            return

        selected_sentence = self.model.text_audio_map[map_key]['sentence']
        old_audio_path = self.model.text_audio_map[map_key]['audio_path']
        audio_path_parent = os.path.dirname(old_audio_path)
        generation_settings = self.model.load_generation_settings(audio_path_parent)
        voice_parameters = generation_settings

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

        # Start the regeneration worker
        self.regen_worker = RegenerateAudioWorker(
            self.model,
            old_audio_path,
            selected_sentence,
            voice_parameters,
            new_audio_path
        )
        self.regen_worker.finished_signal.connect(lambda path: self.on_regeneration_finished(map_key, path))
        self.regen_worker.error_signal.connect(self.on_regeneration_error)
        self.regen_worker.start()
        
    def on_regeneration_finished(self, map_key, new_audio_path):
        # Update the text_audio_map with the new audio path
        self.model.text_audio_map[map_key]['audio_path'] = new_audio_path

        book_name = self.view.audiobook_label.text()
        directory_path = os.path.join("audiobooks", book_name)
        # Save the updated map back to the file
        self.model.save_text_audio_map(directory_path)
        print("Regeneration complete")

    def on_regeneration_error(self, error_message):
        self.view.show_message("Error", error_message, icon=QMessageBox.Warning)

    def continue_audiobook_generation(self):
        directory_path = self.view.get_existing_directory("Select an Audiobook to Continue Generating")
        if not directory_path:
            return  # Exit the function if no directory was selected

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
        audiobook_path = os.path.join('audiobooks', dir_name)
        self.view.set_audiobook_label(dir_name)

        use_old_settings = self.view.ask_question(
            'Use Previous Settings',
            "Do you want to use the same settings from the previous generation of this audiobook?",
            default_button=QMessageBox.No
        )

        if use_old_settings:
            voice_parameters = self.model.load_generation_settings(directory_path)
        else:
            voice_parameters = {
                'selected_voice': self.view.get_voice_model(),
                'selected_index': self.view.get_voice_index(),
                'f0_pitch': self.view.get_voice_pitch(),
                'index_rate': self.view.get_voice_index_effect(),
            }
            self.model.save_generation_settings(directory_path, voice_parameters)

        # Start the worker thread
        self.worker = AudioGenerationWorker(
            self.model.generate_audio_for_sentence_threaded,
            audiobook_path,
            voice_parameters
        )
        self.worker.progress_signal.connect(self.view.set_progress)
        self.worker.started.connect(self.view.disable_buttons)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.sentence_generated_signal.connect(self.on_sentence_generated)
        self.worker.start()

    def load_existing_audiobook(self):
        directory_path = self.view.get_existing_directory("Select an Audiobook Directory")
        if not directory_path:
            return

        book_name = os.path.basename(directory_path)
        self.view.set_audiobook_label(book_name)

        try:
            self.model.load_text_audio_map(directory_path)
            self.update_table_with_sentences()
            # Optionally load generation settings
            generation_settings = self.model.load_generation_settings(directory_path)
            # Update the view with these settings
            self.view.update_generation_settings(generation_settings)
        except Exception as e:
            self.view.show_message("Error", f"An error occurred: {str(e)}", icon=QMessageBox.Warning)

    def update_audiobook(self):
        filePath = self.view.get_open_file_name(
            "Choose a Text file to update the current audiobook with", "", "Text Files (*.txt);;All Files (*)"
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

        directory_path = self.view.get_existing_directory("Select an Audiobook Directory")
        if not directory_path:
            return

        dir_basename = os.path.basename(directory_path)
        audiobook_path = os.path.join("audiobooks", dir_basename)
        self.view.set_audiobook_label(dir_basename)

        try:
            generate_new_audio = self.view.ask_question(
                'Generate New Audio',
                "Would you like to generate new audio for all new sentences?",
                default_button=QMessageBox.No
            )

            if generate_new_audio:
                use_old_settings = self.view.ask_question(
                    'Use Previous Settings',
                    "Do you want to use the same settings from the previous generation of this audiobook?",
                    default_button=QMessageBox.No
                )
                if use_old_settings:
                    voice_parameters = self.model.load_generation_settings(directory_path)
                else:
                    voice_parameters = {
                        'selected_voice': self.view.get_voice_model(),
                        'selected_index': self.view.get_voice_index(),
                        'f0_pitch': self.view.get_voice_pitch(),
                        'index_rate': self.view.get_voice_index_effect(),
                    }
                    self.model.save_generation_settings(directory_path, voice_parameters)
            else:
                voice_parameters = {}

            self.model.update_audiobook(
                directory_path, sentence_list, generate_new_audio, voice_parameters
            )
            self.update_table_with_sentences()
        except Exception as e:
            self.view.show_message("Error", f"An error occurred: {str(e)}", icon=QMessageBox.Warning)

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
