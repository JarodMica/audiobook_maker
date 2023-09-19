import sys
import os
import shutil
from pydub import AudioSegment

from PyQt5.QtWidgets import QSlider, QWidgetAction, QComboBox, QApplication, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QFileDialog, QLineEdit, QLabel, QWidget, QMessageBox, QMenuBar, QAction, QInputDialog, QProgressBar, QHBoxLayout
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont


from tortoise_api import Tortoise_API
from tortoise_api import load_sentences
from rvc_infer import rvc_convert

class AudioGenerationWorker(QThread):
    progress_signal = pyqtSignal(int)

    def __init__(self, function, directory_path, sentence_list, start_idx=0):
        super().__init__()
        self.function = function
        self.directory_path = directory_path
        self.sentence_list = sentence_list
        self.start_idx = start_idx

    def run(self):
        total_sentences = len(self.sentence_list)
        for idx, sentence in enumerate(self.sentence_list[self.start_idx:], start=self.start_idx):
            self.function(self.directory_path, sentence, idx)
            
            # Emit progress update
            progress_percentage = int(((idx + 1) / total_sentences) * 100)

            self.progress_signal.emit(progress_percentage)


class AudiobookMaker(QMainWindow):

    def __init__(self):
        super().__init__()

        self.text_audio_map = {}
        self.setStyleSheet(self.load_stylesheet())
        self.media_player = QMediaPlayer()

        self.init_ui()

        self.tortoise = Tortoise_API()

    def init_ui(self):
        # Main Layout
        self.filepath = None
        main_layout = QHBoxLayout()
        
        # Left side Layout
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10) 
        left_container = QWidget(self)
        left_container.setLayout(left_layout)
        left_container.setMaximumWidth(500)
        main_layout.addWidget(left_container)

        self.load_text = QPushButton("Select Text File", self)
        self.load_text.clicked.connect(self.load_text_file)
        left_layout.addWidget(self.load_text)

        # Book Name Widget
        self.book_layout = QHBoxLayout()
        self.book_name_label = QLabel("Book Name:")
        self.book_layout.addWidget(self.book_name_label)
        self.book_name_input = QLineEdit(self)
        self.book_layout.addWidget(self.book_name_input)
        left_layout.addLayout(self.book_layout)

        # Voice widgets
        self.voice_name_layout = QHBoxLayout()
        self.voice_name_label = QLabel("Voice Model: ")
        self.voice_models_combo = QComboBox()
        self.voice_name_layout.addWidget(self.voice_name_label)
        self.voice_name_layout.addWidget(self.voice_models_combo,1)
        self.get_voice_models()
        left_layout.addLayout(self.voice_name_layout)

        self.generate_button = QPushButton("Start Audiobook Generation", self)
        self.generate_button.clicked.connect(self.start_generation)
        left_layout.addWidget(self.generate_button)

        self.play_button = QPushButton("Play Audio", self)
        self.play_button.clicked.connect(self.play_selected_audio)

        self.pause_button = QPushButton("Pause", self)
        self.pause_button.clicked.connect(self.pause_audio)

        # To arrange the play and pause buttons side by side:
        self.play_pause_layout = QHBoxLayout()
        self.play_pause_layout.addWidget(self.play_button)
        self.play_pause_layout.addWidget(self.pause_button)
        left_layout.addLayout(self.play_pause_layout)

        self.play_all_button = QPushButton("Play All from Selected", self)
        self.play_all_button.clicked.connect(self.play_all_from_selected)
        left_layout.addWidget(self.play_all_button)

        self.regenerate_button = QPushButton("Regenerate Audio", self)
        self.regenerate_button.clicked.connect(self.regenerate_audio_for_sentence)
        left_layout.addWidget(self.regenerate_button)

        self.load_audiobook_button = QPushButton("Load Existing Audiobook", self)
        self.load_audiobook_button.clicked.connect(self.load_existing_audiobook)
        left_layout.addWidget(self.load_audiobook_button)

        self.export_audiobook_button = QPushButton("Export Audiobook", self)
        self.export_audiobook_button.clicked.connect(self.export_audiobook)
        left_layout.addWidget(self.export_audiobook_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        left_layout.addWidget(self.progress_bar)
        left_layout.addStretch(1)  # Add stretchable empty space


        # Right side Widget (Sentences List)
        self.sentences_list = QListWidget(self)
        main_layout.addWidget(self.sentences_list)

        # Create a QWidget for the main window's central widget
        central_widget = QWidget(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Menu bar setup
        self.menu = self.menuBar()

        # Create a slider for font size
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setMinimum(8)
        self.font_slider.setMaximum(20)
        self.font_slider.setValue(14)
        self.font_slider.setTickPosition(QSlider.TicksBelow)
        self.font_slider.setTickInterval(1)
        self.font_slider.valueChanged.connect(self.update_font_size_from_slider)

        # Create a QWidgetAction to embed the slider in the menu
        slider_action = QWidgetAction(self)
        slider_action.setDefaultWidget(self.font_slider)

        self.font_menu = self.menu.addMenu("Font Size")

        # Add slider to the font_menu in the menu bar
        self.font_menu.addAction(slider_action)

        # Window settings
        self.setWindowTitle("Audiobook Maker")
        self.setGeometry(100, 100, 600, 600)

        self.current_sentence_idx = 0

    def get_voice_models(self):
        self.voice_folder_path = "voice_models"
        if os.path.exists(self.voice_folder_path) and os.path.isdir(self.voice_folder_path):
            voice_model_files = [file for file in os.listdir(self.voice_folder_path) if file.endswith(".pth")]
            self.voice_models_combo.addItems(voice_model_files)

    def load_stylesheet(self, font_size="14pt"):
        # Load the base stylesheet
        with open("base.css", "r") as file:
            stylesheet = file.read()

        # Wonky font replacement lol
        modified_stylesheet = stylesheet.replace("font-size: 14pt;", f"font-size: {font_size};")
        return modified_stylesheet
    
    def update_font_size_from_slider(self):
        font_size = str(self.font_slider.value()) + "pt"
        self.setStyleSheet(self.load_stylesheet(font_size))

    def update_metadata(self, directory_path, idx, status):
        meta_path = os.path.join(directory_path, "metadata.txt")
        with open(meta_path, 'a', encoding="utf-8") as meta_file:
            meta_file.write(f"{idx} {status}\n")


    def save_sentences_list(self, directory_path, sentences):
        with open(os.path.join(directory_path, "sentences_list.txt"), 'w', encoding="utf-8") as file:
            for sentence in sentences:
                file.write(sentence + '\n')

    def generate_audio(self, sentence):
        audio_path = self.tortoise.call_api(sentence)
        selected_voice = self.voice_models_combo.currentText()
        voice_model_path = os.path.join(self.voice_folder_path, selected_voice)
        audio_path = rvc_convert(model_path=voice_model_path, resample_sr=0, input_path=audio_path)
        if audio_path:
            return audio_path
        else:
            QMessageBox.warning(self, "Warning", "Failed to generate audio for the sentence: " + sentence)

    def generate_audio_for_sentence_threaded(self, directory_path, sentence, idx):
        audio_path = self.generate_audio(sentence)
        if audio_path:
            new_audio_path = os.path.join(directory_path, f"audio_{idx}.wav")
            os.rename(audio_path, new_audio_path)
            self.text_audio_map[sentence] = new_audio_path
            self.sentences_list.addItem(sentence)
            self.update_metadata(directory_path, idx, "generated")
        else:
            self.update_metadata(directory_path, idx, "failed")

    def start_generation(self):
        if self.filepath:    
        # Create directory based on the book name
            book_name = self.book_name_input.text().strip()
            if not book_name:
                QMessageBox.warning(self, "Error", "Please enter a book name before proceeding.")
                return
            directory_path = os.path.join(os.getcwd(), "audiobooks", book_name)
            if os.path.exists(directory_path):
                reply = QMessageBox.warning(self, 'Overwrite Existing Audiobook', "An audiobook with this name already exists. Do you want to overwrite it?", 
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    confirm_delete = QMessageBox.question(self, 'Confirm Deletion', "This cannot be undone, the audiobook will be lost forever. Proceed?", 
                                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if confirm_delete == QMessageBox.Yes:
                        # Delete the old audiobook directory and its contents
                        shutil.rmtree(directory_path)
                    else:
                        return
                else:
                    return
            os.makedirs(directory_path)
            self.sentences_list.clear()
            self.text_audio_map.clear()
            sentence_list = load_sentences(self.filepath)
            self.save_sentences_list(directory_path, sentence_list)

            self.worker = AudioGenerationWorker(self.generate_audio_for_sentence_threaded, directory_path, sentence_list)

            self.worker.started.connect(self.disable_buttons)
            self.regenerate_button.setStyleSheet("")
            self.worker.finished.connect(self.enable_buttons)

            self.worker.progress_signal.connect(self.progress_bar.setValue)
            self.worker.start()
        else:
            QMessageBox.warning(self, "Error", "Please pick a text file before generating audio.")
            return

    def load_text_file(self):
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Text File", "", "Text Files (*.txt);;All Files (*)", options=options)
        self.filepath = filepath
            
    def get_last_generated_index(self, directory_path):
        meta_path = os.path.join(directory_path, "metadata.txt")
        if not os.path.exists(meta_path):
            return -1  # If metadata doesn't exist, assume starting from scratch
        with open(meta_path, 'r', encoding="utf-8") as meta_file:
            lines = meta_file.readlines()
            if not lines:
                return -1
            last_line = lines[-1].strip()
            idx, status = last_line.split()
            if status == "generated":
                return int(idx)
            else:
                return -1
            
    def export_audiobook(self):
        directory_path = QFileDialog.getExistingDirectory(self, "Select an Audiobook Directory")
        if not directory_path:
            return  # Exit the function if no directory was selected
        
        dir_name = os.path.basename(directory_path)
        idx = 0

        # Ensure 'exported_audiobooks' directory exists
        exported_dir = os.path.join(directory_path, "exported_audiobooks")
        if not os.path.exists(exported_dir):
            os.makedirs(exported_dir)

        # Find a suitable audio file name with an incrementing suffix
        while True:
            new_audiobook_name = f"{dir_name}_audiobook_{idx}.wav"
            new_audiobook_path = os.path.join(exported_dir, new_audiobook_name)
            if not os.path.exists(new_audiobook_path):
                break  # Exit the loop once a suitable name is found
            idx += 1

        output_filename = new_audiobook_path
        
        # Combine the audio files
        audio_files = [file for file in os.listdir(directory_path) if file.startswith("audio_") and file.endswith(".wav")]
        audio_files.sort(key=lambda file_name: int(file_name.split('_')[1].split('.wav')[0]))  # Sort by the number in the filename
        
        combined_audio = AudioSegment.empty()  # Create an empty audio segment
        
        for audio_file in audio_files:
            audio_path = os.path.join(directory_path, audio_file)
            audio_segment = AudioSegment.from_wav(audio_path)
            combined_audio += audio_segment

        # Export the combined audio
        combined_audio.export(output_filename, format="wav")

        print(f"Combined audiobook saved as {output_filename}")
            

    def load_existing_audiobook(self):
        directory_path = QFileDialog.getExistingDirectory(self, "Select an Audiobook Directory")
        try:
            if os.path.exists(os.path.join(directory_path, "sentences_list.txt")):
                with open(os.path.join(directory_path, "sentences_list.txt"), 'r', encoding="utf-8") as file:
                    self.sentences_list.clear()
                    self.text_audio_map.clear()

                    missing_audio_sentences = []

                    for idx, line in enumerate(file):
                        sentence = line.strip()
                        audio_path = os.path.join(directory_path, f"audio_{idx}.wav")
                        if os.path.exists(audio_path):
                            self.sentences_list.addItem(sentence)
                            self.text_audio_map[sentence] = audio_path
                        else:
                            missing_audio_sentences.append(sentence)

                    if missing_audio_sentences:
                        missing_sentences_str = "\n".join(missing_audio_sentences)
                        QMessageBox.warning(self, "Error", f"Audio files missing for some sentences")
            last_generated_idx = self.get_last_generated_index(directory_path)
            sentence_list = load_sentences(os.path.join(directory_path, "sentences_list.txt"))
            if last_generated_idx > -1 and last_generated_idx + 1 < len(sentence_list):
                reply = QMessageBox.question(self, 'Resume Audio Generation', 
                                            f"Audio generation seems to have stopped at sentence {last_generated_idx + 1}. Would you like to continue from this point?", 
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.worker = AudioGenerationWorker(self.generate_audio_for_sentence_threaded, directory_path, sentence_list, start_idx=last_generated_idx + 1)
                    self.worker.started.connect(self.disable_buttons)
                    self.regenerate_button.setStyleSheet("")
                    self.worker.finished.connect(self.disable_buttons)
                    self.worker.progress_signal.connect(self.progress_bar.setValue)
                    self.worker.start()
        except:
            QMessageBox.warning(self, "Error", "The selected directory is not a valid Audiobook Directory.")

    def play_selected_audio(self):
        try:
            selected_sentence = self.sentences_list.currentItem().text()
            audio_path = self.text_audio_map[selected_sentence]
        except:
            QMessageBox.warning(self, "Error", 'Choose a sentence to play audio for')
            return
        
        try:
            self.media_player.stateChanged.disconnect(self.on_audio_finished)
        except:
            pass  # If the signal wasn't connected, it's fine
        
        self.pause_button.setStyleSheet("")
        self.media_player = QMediaPlayer()
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
        self.media_player.play()

    def play_all_from_selected(self):
        if self.sentences_list.count() == 0:
            return

        # If there's an active selection, play from that index.
        # Otherwise, play from the start.
        if self.sentences_list.currentRow() >= 0:
            self.current_sentence_idx = self.sentences_list.currentRow()
        else:
            self.current_sentence_idx = 0

        # Start playing the first audio
        self.pause_button.setStyleSheet("")
        self.play_audio_by_index(self.current_sentence_idx)


    def play_audio_by_index(self, idx):
        if idx < self.sentences_list.count():
            sentence = self.sentences_list.item(idx).text()
            audio_path = self.text_audio_map[sentence]
            self.sentences_list.setCurrentRow(idx)  # Highlight the sentence
            
            self.media_player = QMediaPlayer()
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
            self.media_player.play()

            # Connect the media player's stateChanged signal so that the next audio is played when the current one finishes
            self.media_player.stateChanged.connect(self.on_audio_finished)
    
    def pause_audio(self):
        if hasattr(self, 'media_player'):
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.media_player.pause()
                self.pause_button.setStyleSheet("background-color: #777;")  # Change the color code as needed

            elif self.media_player.state() == QMediaPlayer.PausedState:
                self.media_player.play()
                self.pause_button.setStyleSheet("")
    
    def on_audio_finished(self, state):
        # Check if the audio has finished playing
        if state == QMediaPlayer.StoppedState:
            # Increment the index to play the next audio
            self.current_sentence_idx += 1

            # Check if there's another audio file to play
            if self.current_sentence_idx < self.sentences_list.count():
                self.play_audio_by_index(self.current_sentence_idx)
            else:
                self.media_player.stateChanged.disconnect(self.on_audio_finished)

    def regenerate_audio_for_sentence(self):
        try:
            selected_sentence = self.sentences_list.currentItem().text()
            new_audio_path = self.generate_audio(selected_sentence)
        except:
            QMessageBox.warning(self, "Error", "Choose a sentence.")
            return
        if new_audio_path:
            # Get old audio path for selected sentence
            old_audio_path = self.text_audio_map[selected_sentence]

            # Remove the old audio file to make space for the new content
            if os.path.exists(old_audio_path):
                os.remove(old_audio_path)
            
            # Copy new audio to old audio path
            shutil.copy(new_audio_path, old_audio_path)

    def disable_buttons(self):
        buttons = [self.regenerate_button, 
                   self.generate_button, 
                   self.load_audiobook_button,
                   self.export_audiobook_button]
        for button in buttons:
            button.setDisabled(True)
            button.setStyleSheet("QPushButton { color: #A9A9A9; }")

    def enable_buttons(self):
        buttons = [self.regenerate_button, 
                   self.generate_button, 
                   self.load_audiobook_button,
                   self.export_audiobook_button]
        for button in buttons:
            button.setDisabled(False)
            button.setStyleSheet("")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = AudiobookMaker()
    main_window.show()
    sys.exit(app.exec_())
