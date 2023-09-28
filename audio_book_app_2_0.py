import sys
import os
import shutil
import json
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

        # -- Voice Name Combo Box
        self.voice_name_layout = QHBoxLayout()
        self.voice_name_label = QLabel("Voice Model: ")
        self.voice_models_combo = QComboBox()
        self.voice_name_layout.addWidget(self.voice_name_label)
        self.voice_name_layout.addWidget(self.voice_models_combo,1)
        self.get_voice_models()
        left_layout.addLayout(self.voice_name_layout)

        # -- Voice Index Combo Box
        self.voice_index_layout = QHBoxLayout()
        self.voice_index_label = QLabel("Voice Index: ")
        self.voice_index_combo = QComboBox()
        self.voice_index_layout.addWidget(self.voice_index_label)
        self.voice_index_layout.addWidget(self.voice_index_combo,1)
        self.get_voice_indexes()
        left_layout.addLayout(self.voice_index_layout)

        # -- Voice Index Slider
        index=0
        self.voice_index_value_label = QLabel(f"{index/100}")  # 0 is the initial value of the slider
        max_index_str = "1"  # the maximum value the label will show
        estimated_width = len(max_index_str) * 50

        self.voice_index_value_label.setFixedWidth(estimated_width)
        self.voice_index_layout = QHBoxLayout()
        self.voice_index_label = QLabel("Index Effect: ")
        self.voice_index_slider = QSlider(Qt.Horizontal)
        self.voice_index_slider.setMinimum(0)
        self.voice_index_slider.setMaximum(100)
        self.voice_index_slider.setValue(index)
        self.voice_index_slider.setTickPosition(QSlider.TicksBelow)
        self.voice_index_slider.setTickInterval(1)

        self.voice_index_slider.valueChanged.connect(self.updateVoiceIndexLabel)

        self.voice_index_layout.addWidget(self.voice_index_label)
        self.voice_index_layout.addWidget(self.voice_index_slider)
        self.voice_index_layout.addWidget(self.voice_index_value_label)  # Step 3: Add the value label to the layout

        left_layout.addLayout(self.voice_index_layout)

        # -- Voice Pitch Slider
        self.voice_pitch_value_label = QLabel("0")  # 0 is the initial value of the slider
        max_value_str = "16"  # the maximum value the label will show
        estimated_width = len(max_value_str) * 20

        self.voice_pitch_value_label.setFixedWidth(estimated_width)
        self.voice_pitch_layout = QHBoxLayout()
        self.voice_pitch_label = QLabel("Voice Pitch: ")
        self.voice_pitch_slider = QSlider(Qt.Horizontal)
        self.voice_pitch_slider.setMinimum(-16)
        self.voice_pitch_slider.setMaximum(16)
        self.voice_pitch_slider.setValue(0)
        self.voice_pitch_slider.setTickPosition(QSlider.TicksBelow)
        self.voice_pitch_slider.setTickInterval(1)

        self.voice_pitch_slider.valueChanged.connect(self.updateVoicePitchLabel)

        self.voice_pitch_layout.addWidget(self.voice_pitch_label)
        self.voice_pitch_layout.addWidget(self.voice_pitch_slider)
        self.voice_pitch_layout.addWidget(self.voice_pitch_value_label)  # Step 3: Add the value label to the layout

        left_layout.addLayout(self.voice_pitch_layout)

        # -- Start Audiobook Button
        self.generate_button = QPushButton("Start Audiobook Generation", self)
        self.generate_button.clicked.connect(self.start_generation)
        left_layout.addWidget(self.generate_button)

        # -- Play Audio Button
        self.play_button = QPushButton("Play Audio", self)
        self.play_button.clicked.connect(self.play_selected_audio)

        # -- Pause Audio Button
        self.pause_button = QPushButton("Pause", self)
        self.pause_button.clicked.connect(self.pause_audio)

        # To arrange the play and pause buttons side by side:
        self.play_pause_layout = QHBoxLayout()
        self.play_pause_layout.addWidget(self.play_button)
        self.play_pause_layout.addWidget(self.pause_button)
        left_layout.addLayout(self.play_pause_layout)

        # -- Play All Audio Button
        self.play_all_button = QPushButton("Play All from Selected", self)
        self.play_all_button.clicked.connect(self.play_all_from_selected)
        left_layout.addWidget(self.play_all_button)

        # -- Regen Audio Button
        self.regenerate_button = QPushButton("Regenerate Audio", self)
        self.regenerate_button.clicked.connect(self.regenerate_audio_for_sentence)
        left_layout.addWidget(self.regenerate_button)

        # -- Load Audiobook Button
        self.load_audiobook_button = QPushButton("Load Existing Audiobook", self)
        self.load_audiobook_button.clicked.connect(self.load_existing_audiobook)
        left_layout.addWidget(self.load_audiobook_button)

        # -- Export Audiobook Button
        self.export_audiobook_button = QPushButton("Export Audiobook", self)
        self.export_audiobook_button.clicked.connect(self.export_audiobook)
        left_layout.addWidget(self.export_audiobook_button)

        self.update_audiobook_button = QPushButton("Update Audiobook", self)
        self.update_audiobook_button.clicked.connect(self.update_audiobook)
        left_layout.addWidget(self.update_audiobook_button)

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
        self.setGeometry(100, 100, 750, 600)

        self.current_sentence_idx = 0

    def get_voice_models(self):
        self.voice_folder_path = "voice_models"
        if os.path.exists(self.voice_folder_path) and os.path.isdir(self.voice_folder_path):
            voice_model_files = [file for file in os.listdir(self.voice_folder_path) if file.endswith(".pth")]
            self.voice_models_combo.addItems(voice_model_files)

    def get_voice_indexes(self):
        self.index_folder_path = "voice_indexes"
        if os.path.exists(self.index_folder_path) and os.path.isdir(self.index_folder_path):
            voice_index_files = [file for file in os.listdir(self.index_folder_path) if file.endswith(".index")]
            self.voice_index_combo.addItems(voice_index_files)

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

    def updateVoicePitchLabel(self, value):
        self.voice_pitch_value_label.setText(str(value))
    
    def updateVoiceIndexLabel(self, value):
        value = (self.voice_index_slider.value() / 100)
        self.voice_index_value_label.setText(str(value))

    def update_metadata(self, directory_path, idx, status):
        meta_path = os.path.join(directory_path, "metadata.txt")
        with open(meta_path, 'a', encoding="utf-8") as meta_file:
            meta_file.write(f"{idx} {status}\n")


    def save_sentences_list(self, directory_path, sentences):
        s_list_dir = os.path.join(directory_path, "sentences_list.txt")
        if os.path.exists(s_list_dir):
            os.remove(s_list_dir)
        with open(os.path.join(directory_path, "sentences_list.txt"), 'w', encoding="utf-8") as file:
            for sentence in sentences:
                file.write(sentence + '\n')

    def save_text_audio_map(self, directory_path):
        # Specify the path for the text_audio_map file
        map_file_path = os.path.join(directory_path, "text_audio_map.json")

        # Open the file in write mode (this will overwrite the file if it already exists)
        with open(map_file_path, 'w', encoding="utf-8") as map_file:
            # Convert the text_audio_map dictionary to a JSON string and write it to the file
            json.dump(self.text_audio_map, map_file, ensure_ascii=False, indent=4)

    def generate_audio(self, sentence):
        audio_path = self.tortoise.call_api(sentence)
        selected_voice = self.voice_models_combo.currentText()
        selected_index = self.voice_index_combo.currentText()
        voice_model_path = os.path.join(self.voice_folder_path, selected_voice)
        voice_index_path = os.path.join(self.index_folder_path, selected_index)
        
        f0_pitch = self.voice_pitch_slider.value()
        index_rate = (self.voice_index_slider.value()/100)
        audio_path = rvc_convert(model_path=voice_model_path, 
                                 f0_up_key=f0_pitch, 
                                 resample_sr=0, 
                                 file_index=voice_index_path,
                                 index_rate=index_rate,
                                 input_path=audio_path)
        if audio_path:
            return audio_path
        else:
            QMessageBox.warning(self, "Warning", "Failed to generate audio for the sentence: " + sentence)

    # def generate_audio_for_sentence_threaded(self, directory_path, sentence, idx):
    #     audio_path = self.generate_audio(sentence)
    #     if audio_path:
    #         new_audio_path = os.path.join(directory_path, f"audio_{idx}.wav")
    #         os.rename(audio_path, new_audio_path)
    #         self.text_audio_map[sentence] = new_audio_path
    #         self.sentences_list.addItem(sentence)
    #         self.update_metadata(directory_path, idx, "generated")

    #         # Save text_audio_map to a file
    #         self.save_text_audio_map(directory_path)
    #     else:
    #         self.update_metadata(directory_path, idx, "failed")

    def generate_audio_for_sentence_threaded(self, directory_path, sentence, idx):
        audio_path = self.generate_audio(sentence)
        if audio_path:
            new_audio_path = os.path.join(directory_path, f"audio_{idx}.wav")
            os.rename(audio_path, new_audio_path)
            self.text_audio_map[str(idx)] = {"sentence": sentence, "audio_path": new_audio_path}
            self.sentences_list.addItem(sentence)
            self.update_metadata(directory_path, idx, "generated")

            # Save text_audio_map to a file
            self.save_text_audio_map(directory_path)
        else:
            self.update_metadata(directory_path, idx, "failed")

    def start_generation(self):
        if self.filepath:    
        # Create directory based on the book name
            book_name = self.book_name_input.text().strip()
            if not book_name:
                QMessageBox.warning(self, "Error", "Please enter a book name before proceeding.")
                return
            directory_path = os.path.join("audiobooks", book_name)
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

    def update_audiobook(self):
        if self.filepath:    
            self.sentences_list.clear()
            self.text_audio_map.clear()
            sentence_list = load_sentences(self.filepath)
        else:
            QMessageBox.warning(self, "Error", "Please pick a text file before generating audio.")
            return
        
        reply = QMessageBox.warning(self, 'Update Existing Audiobook', "This will delete audio for existing sentences if they have been modified as well. Do you want to proceed?", 
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            pass
        else:
            return
        
        directory_path = QFileDialog.getExistingDirectory(self, "Select an Audiobook Directory")
        if not directory_path:  # User cancelled the dialog
            return
        
        dir_basename = os.path.basename(directory_path)
        audiobook_path = os.path.join("audiobooks",dir_basename)
        audio_map_path = os.path.join(directory_path, 'text_audio_map.json')
        new_audio_map_path = os.path.join(directory_path, 'text_audio_map_new.json')
        sentences_list_path = os.path.join(directory_path, 'sentences_list.txt')
        self.save_sentences_list(audiobook_path, sentence_list)
    

        # Step 1: Load existing text_audio_map
        with open(audio_map_path, 'r', encoding='utf-8') as file:
            text_audio_map = json.load(file)

        reverse_map = {item['sentence']: idx for idx, item in text_audio_map.items()}

        # Step 2: Load new sentences list
        with open(sentences_list_path, 'r', encoding='utf-8') as file:
            sentences_list = [line.strip() for line in file.readlines() if line.strip()]
        
        # Step 3: Generate updated map
        new_text_audio_map = {}
        deleted_sentences = set(text_audio_map.keys())  # Initialize with all old indices
        for new_idx, sentence in enumerate(sentences_list):
            if sentence in reverse_map:  # Sentence exists in old map
                old_idx = reverse_map[sentence]
                new_text_audio_map[str(new_idx)] = text_audio_map[old_idx]
                deleted_sentences.discard(old_idx)  # Remove index from set of deleted sentences
            else:  # New sentence
                audio_path = self.generate_audio(sentence)
                if audio_path:
                    idx = 0
                    base_filename = f"audio_{idx}"
                    extension = ".wav"
                    
                    while os.path.exists(os.path.join(directory_path, f"{base_filename}{extension}")):
                        idx += 1
                        base_filename = f"audio_{idx}"
                    new_audio_path = os.path.join(audiobook_path, f"{base_filename}{extension}")
                    os.rename(audio_path, new_audio_path)
                new_text_audio_map[str(new_idx)] = {"sentence": sentence, "audio_path": new_audio_path}

        # Step 4: Handle deleted sentences and their audio files
        for old_idx in deleted_sentences:
            old_audio_path = text_audio_map[old_idx]['audio_path']
            if os.path.exists(old_audio_path):
                os.remove(old_audio_path)  # Delete the audio file
        
        # Step 5: Save updated text_audio_map
        with open(new_audio_map_path, 'w', encoding='utf-8') as file:
            json.dump(new_text_audio_map, file, ensure_ascii=False, indent=4)

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
