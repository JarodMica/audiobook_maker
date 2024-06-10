import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
runtime_dir = os.path.join(script_dir, 'runtime')
if os.path.exists(runtime_dir):
    import site
    user_site = site.getusersitepackages()
    global_sites = site.getsitepackages()
    sys.path = [p for p in sys.path if p != user_site and p not in global_sites]

    # Append local packages
    local_sites = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'runtime','lib', 'site-packages'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'runtime')]

    for sites in local_sites:
        if sites not in sys.path:
            sys.path.append(sites)
import shutil
import json

from pydub import AudioSegment
from PyQt5.QtWidgets import QSlider, QWidgetAction, QComboBox, QApplication, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QFileDialog, QLineEdit, QLabel, QWidget, QMessageBox, QHeaderView, QProgressBar, QHBoxLayout, QTableWidget, QTableWidgetItem, QAction, QDesktopWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QPixmap, QPalette, QBrush


# Get the directory of the currently executed script
script_directory = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_directory)

from tortoise_api.tortoise_api import load_sentences, load_config, call_api

from rvc_pipe.rvc_infer import rvc_convert

class AudioGenerationWorker(QThread):
    progress_signal = pyqtSignal(int)

    def __init__(self, function, directory_path):
        super().__init__()
        self.function = function
        self.directory_path = directory_path

    def run(self):
        self.function(self.directory_path, self.report_progress)

    def report_progress(self, progress):
        self.progress_signal.emit(progress)

class AudiobookMaker(QMainWindow):

    def __init__(self):
        super().__init__()
        # Create a background label widget and set it up
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.background_label.lower()  # Lower the background so it's behind other widgets

        # Load user settings
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as json_file:
                settings = json.load(json_file)
                background_image = settings.get('background_image')
                if background_image and os.path.exists(background_image):
                    self.set_background(background_image)
                    
        self.text_audio_map = {}
        self.setStyleSheet(self.load_stylesheet())

        self.media_player = QMediaPlayer()

        self.init_ui()
        

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
        self.voice_index_layout.addWidget(self.voice_index_value_label)

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
        self.voice_pitch_layout.addWidget(self.voice_pitch_value_label)

        left_layout.addLayout(self.voice_pitch_layout)

        # -- Export Pause Slider
        pause=0
        self.export_pause_value_label = QLabel(f"{pause/10}")  # 0 is the initial value of the slider
        max_pause = "5"  # the maximum value the label will show
        estimated_width = len(max_pause) * 50
        self.export_pause_value_label.setFixedWidth(estimated_width)

        self.export_pause_layout = QHBoxLayout()
        self.export_pause_label = QLabel("Pause Between Sentences (sec): ")
        self.export_pause_slider = QSlider(Qt.Horizontal)
        self.export_pause_slider.setMinimum(0)
        self.export_pause_slider.setMaximum(50)
        self.export_pause_slider.setValue(pause)
        self.export_pause_slider.setTickPosition(QSlider.TicksBelow)
        self.export_pause_slider.setTickInterval(1)

        self.export_pause_slider.valueChanged.connect(self.updatePauseLabel)

        self.export_pause_layout.addWidget(self.export_pause_label)
        self.export_pause_layout.addWidget(self.export_pause_slider)
        self.export_pause_layout.addWidget(self.export_pause_value_label)

        left_layout.addLayout(self.export_pause_layout)

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

        self.continue_audiobook_button = QPushButton("Continue Audiobook Generation", self)
        self.continue_audiobook_button.clicked.connect(self.continue_audiobook_generation)
        left_layout.addWidget(self.continue_audiobook_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        left_layout.addWidget(self.progress_bar)
        left_layout.addStretch(1)  # Add stretchable empty space


        # Right side Widget
        right_layout = QVBoxLayout()

        # Audiobook label
        self.audiobook_name = "No Audio Book Set"
        self.audiobook_label = QLabel(self)
        self.audiobook_label.setText(f"{self.audiobook_name}")
        self.audiobook_label.setAlignment(Qt.AlignCenter)
        self.audiobook_label.setStyleSheet("font-size: 16pt; color: #eee;")
        right_layout.addWidget(self.audiobook_label)

        # Table widget
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setColumnCount(1)
        self.tableWidget.setHorizontalHeaderLabels(['Sentence'])
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        right_layout.addWidget(self.tableWidget)

        main_layout.addLayout(right_layout)

        # Create a QWidget for the main window's central widget
        central_widget = QWidget(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Menu bar setup
        self.menu = self.menuBar()

        # Create File menu
        self.file_menu = self.menu.addMenu("File")

        # Add Load Audiobook action to File menu
        self.load_audiobook_action = QAction("Load Existing Audiobook", self)
        self.load_audiobook_action.triggered.connect(self.load_existing_audiobook)
        self.file_menu.addAction(self.load_audiobook_action)

        # Add Update Audiobook Sentences action to File menu
        self.update_audiobook_action = QAction("Update Audiobook Sentences", self)
        self.update_audiobook_action.triggered.connect(self.update_audiobook)
        self.file_menu.addAction(self.update_audiobook_action)

        # Add Export Audiobook action to File menu
        self.export_audiobook_action = QAction("Export Audiobook", self)
        self.export_audiobook_action.triggered.connect(self.export_audiobook)
        self.file_menu.addAction(self.export_audiobook_action)

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

        self.background_menu = self.menu.addMenu("Background")

        # Add Set Background Image action to File menu
        self.set_background_action = QAction("Set Background Image", self)
        self.set_background_action.triggered.connect(self.set_background_image)
        self.background_menu.addAction(self.set_background_action)

         # Clear Background Image action to File menu
        self.set_background_clear_action = QAction("Clear Background Image", self)
        self.set_background_clear_action.triggered.connect(self.set_background_clear_image)
        self.background_menu.addAction(self.set_background_clear_action)

        # Window settings
        self.setWindowTitle("Audiobook Maker")
        screen = QDesktopWidget().screenGeometry()  # Get the screen geometry
        target_ratio = 16 / 9

        width = screen.width() * 0.8
        height = width / target_ratio  # calculate height based on the target aspect ratio

        if height > screen.height():
            height = screen.height() * 0.8 
            width = height * target_ratio  # calculate width based on the target aspect ratio

        # Set the calculated geometry for the window
        self.setGeometry(100, 100, int(width), int(height))

        self.current_sentence_idx = 0

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#   GUI Methods
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def load_text_file(self):
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Text File", "", "Text Files (*.txt);;All Files (*)", options=options)
        self.filepath = filepath

    def start_generation(self):
        if self.filepath:    
        # Create directory based on the book name
            book_name = self.book_name_input.text().strip()
            if not book_name:
                QMessageBox.warning(self, "Error", "Please enter a book name before proceeding.")
                return
            directory_path = os.path.join("audiobooks", book_name)
            self.audiobook_label.setText(f"{book_name}")
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
            self.tableWidget.setRowCount(0)
            self.text_audio_map.clear()
            sentence_list = load_sentences(self.filepath)
            text_audio_map_path = os.path.join(directory_path, "text_audio_map.json")
            generation_settings_path = os.path.join(directory_path, "generation_settings.json")
            self.create_audio_text_map(text_audio_map_path, sentence_list)
            self.create_generation_settings(generation_settings_path)

            self.worker = AudioGenerationWorker(self.generate_audio_for_sentence_threaded, directory_path)

            self.worker.started.connect(self.disable_buttons)
            self.regenerate_button.setStyleSheet("")
            self.worker.finished.connect(self.enable_buttons)

            self.worker.progress_signal.connect(self.progress_bar.setValue)
            self.worker.start()
        else:
            QMessageBox.warning(self, "Error", "Please pick a text file before generating audio.")
            return
        
    def play_selected_audio(self):
        selected_row = self.tableWidget.currentRow()
        if selected_row == -1:  # No row is selected
            QMessageBox.warning(self, "Error", 'Choose a sentence to play audio for')
            return

        map_key = str(selected_row)
        if not self.text_audio_map[map_key]["generated"]:
            QMessageBox.warning(self, "Error", f'Sentence has not been generated for sentence {selected_row + 1}')
            return

        audio_path = self.text_audio_map[map_key]['audio_path']

        try:
            if hasattr(self, 'media_player_connected') and self.media_player_connected:
                self.media_player.stateChanged.disconnect(self.on_audio_finished)
                self.media_player_connected = False
        except AttributeError:
            pass  # If the signal wasn't connected, it's fine

        self.pause_button.setStyleSheet("")
        self.media_player = QMediaPlayer()
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
        # Disconnect on_audio_finished for play_selected_audio
        try:
            self.media_player.stateChanged.disconnect(self.on_audio_finished)
        except TypeError:  # Handle the case where the signal was not connected
            pass
        self.media_player.play()

    def play_all_from_selected(self):
        if self.tableWidget.rowCount() == 0:
            return

        # If there's an active selection, play from that index.
        # Otherwise, play from the start.
        selected_row = self.tableWidget.currentRow()
        if selected_row >= 0:
            self.current_sentence_idx = selected_row
        else:
            self.current_sentence_idx = 0

        # Start playing the first audio
        self.pause_button.setStyleSheet("")
        self.play_audio_by_index(self.current_sentence_idx)

    def pause_audio(self):
        if hasattr(self, 'media_player'):
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.media_player.pause()
                self.pause_button.setStyleSheet("background-color: #777;")  # Change the color code as needed

            elif self.media_player.state() == QMediaPlayer.PausedState:
                self.media_player.play()
                self.pause_button.setStyleSheet("")


    def regenerate_audio_for_sentence(self):
        selected_row = self.tableWidget.currentRow()
        if selected_row == -1:  # No row is selected
            QMessageBox.warning(self, "Error", "Choose a sentence.")
            return

        map_key = str(selected_row)
        if not self.text_audio_map[map_key]['generated']:
            QMessageBox.warning(self, "Error", f'No audio path found, generate sentences with "Continue Audiobook" first before regenerating. This may have occured if you updated the audiobook and did not opt to generate new sentences')
            return

        selected_sentence = self.text_audio_map[map_key]['sentence']
        old_audio_path = self.text_audio_map[map_key]['audio_path']
        audio_path_parent = os.path.dirname(old_audio_path)
        generation_settings_path = os.path.join(audio_path_parent, "generation_settings.json")
        self.create_generation_settings(generation_settings_path)

        new_audio_path = self.generate_audio(selected_sentence)
        if not new_audio_path:
            QMessageBox.warning(self, "Error", "Failed to generate new audio.")
            return

        if os.path.exists(old_audio_path):
            os.remove(old_audio_path)
        self.text_audio_map[map_key]['audio_path'] = new_audio_path
        
        # Optionally: If you want to keep the file name the same, you might need to copy 
        # the new audio file back to the old file path and then delete the new one.
        shutil.copy(new_audio_path, old_audio_path)
        os.remove(new_audio_path)
        self.text_audio_map[map_key]['audio_path'] = old_audio_path

        book_name = self.audiobook_label.text()
        directory_path = os.path.join("audiobooks", book_name)
        # Save the updated map back to the file (implement this function)
        self.save_text_audio_map(directory_path)

    def load_existing_audiobook(self):
        directory_path = QFileDialog.getExistingDirectory(self, "Select an Audiobook Directory")
        if not directory_path:  # User cancelled the dialog
            return
        
        book_name = os.path.basename(directory_path)
        self.audiobook_label.setText(f"{book_name}")

        map_file_path = os.path.join(directory_path, "text_audio_map.json")
        generation_settings_path = os.path.join(directory_path, "generation_settings.json")

        # Check if text_audio_map.json exists in the selected directory
        if not os.path.exists(map_file_path):
            QMessageBox.warning(self, "Error", "The selected directory is not a valid Audiobook Directory.")
            return

        try:
            # Load text_audio_map.json
            with open(map_file_path, 'r', encoding="utf-8") as file:
                text_audio_map = json.load(file)

            self.load_and_set_generation_settings(generation_settings_path)

            # Clear existing items in the table widget and text_audio_map
            self.tableWidget.setRowCount(0)
            self.text_audio_map.clear()

            # Insert sentences and update text_audio_map
            for idx_str, item in text_audio_map.items():
                sentence = item['sentence']

                # Add item to QTableWidget
                sentence_item = QTableWidgetItem(sentence)
                sentence_item.setFlags(sentence_item.flags() & ~Qt.ItemIsEditable)
                row_position = self.tableWidget.rowCount()
                self.tableWidget.insertRow(row_position)
                self.tableWidget.setItem(row_position, 0, sentence_item)

                # Update text_audio_map
                self.text_audio_map[idx_str] = item


        except Exception as e:
            # Handle other exceptions (e.g., JSON decoding errors)
            QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")

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

        # Load the JSON file
        audio_map_path = os.path.join(directory_path, 'text_audio_map.json')
        if not os.path.exists(audio_map_path):
            QMessageBox.warning(self, "Error", "The selected directory is not a valid Audiobook Directory. Make sure the text_audio_map.json exists which comes from generating an audio book.")
            return
        
        with open(audio_map_path, 'r', encoding='utf-8') as file:
            text_audio_map = json.load(file)

        # Sort the keys (converted to int), then get the corresponding audio paths
        sorted_audio_paths = [text_audio_map[key]['audio_path'] for key in sorted(text_audio_map, key=lambda k: int(k))]
        
        combined_audio = AudioSegment.empty()  # Create an empty audio segment

        pause_length = (self.export_pause_slider.value()/10) * 1000 # convert to milliseconds
        silence = AudioSegment.silent(duration=pause_length)  # Create a silent audio segment of pause_length

        for audio_path in sorted_audio_paths:
            audio_segment = AudioSegment.from_wav(audio_path)
            combined_audio += audio_segment + silence  # Append the audio segment followed by silence

        # If you don't want silence after the last segment, you might need to trim it
        if pause_length > 0:
            combined_audio = combined_audio[:-pause_length]

        # Export the combined audio
        combined_audio.export(output_filename, format="wav")

        print(f"Combined audiobook saved as {output_filename}")


    def update_audiobook(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        filePath, _ = QFileDialog.getOpenFileName(self, "Choose a Text file to update the current audiobook with", "", "Text Files (*.txt);;All Files (*)", options=options)
        if not filePath:  # User cancelled the dialog
            return

        self.tableWidget.setRowCount(0)
        self.text_audio_map.clear()
        sentence_list = load_sentences(filePath)
        
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
        self.audiobook_label.setText(f"{dir_basename}")

        if not os.path.exists(audio_map_path):
            QMessageBox.warning(self, "Error", "The selected directory is not a valid Audiobook Directory. Start by generating an audio book first before updating.")
            return
        # Load existing text_audio_map
        with open(audio_map_path, 'r', encoding='utf-8') as file:
            text_audio_map = json.load(file)

        reverse_map = {item['sentence']: idx for idx, item in text_audio_map.items()}

        generate_new_audio_reply = QMessageBox.question(self, 
                                    'Generate New Audio', 
                                    "Would you like to generate new audio for all new sentences?", 
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.No  # Default is 'No'
                                )
        
        # Generate updated map
        new_text_audio_map = {}
        deleted_sentences = set(text_audio_map.keys()) 
        for new_idx, sentence in enumerate(sentence_list):
            if sentence in reverse_map:  # Sentence exists in old map
                old_idx = reverse_map[sentence]
                new_text_audio_map[str(new_idx)] = text_audio_map[old_idx]
                deleted_sentences.discard(old_idx)  # Remove index from set of deleted sentences
            else:  # New sentence
                generated = False
                new_audio_path = ""
                new_text_audio_map[str(new_idx)] = {"sentence": sentence, "audio_path": new_audio_path, "generated": generated}
                self.save_json(audio_map_path, new_text_audio_map)

        # Handle deleted sentences and their audio files
        for old_idx in deleted_sentences:
            old_audio_path = text_audio_map[old_idx]['audio_path']
            if os.path.exists(old_audio_path):
                os.remove(old_audio_path)  # Delete the audio file
        self.save_json(audio_map_path, new_text_audio_map)

        if generate_new_audio_reply == QMessageBox.Yes:
            use_old_settings_reply = QMessageBox.question(self, 
                                    'Use Previouis Settings', 
                                    "Do you want to use the same settings from the previous generation of this audiobook?", 
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.No  # Default is 'No'
                                )
            generation_settings_path = os.path.join(directory_path, "generation_settings.json")
            if use_old_settings_reply == QMessageBox.Yes:
                self.load_and_set_generation_settings(generation_settings_path)
            else:
                self.create_generation_settings(generation_settings_path)

            self.worker = AudioGenerationWorker(self.generate_audio_for_sentence_threaded, audiobook_path)

            self.worker.started.connect(self.disable_buttons)
            self.regenerate_button.setStyleSheet("")
            self.worker.finished.connect(self.enable_buttons)

            self.worker.progress_signal.connect(self.progress_bar.setValue)
            self.worker.start()

    def continue_audiobook_generation(self):
        directory_path = QFileDialog.getExistingDirectory(self, "Select an Audiobook to Continue Generating")
        if not directory_path:
            return  # Exit the function if no directory was selected
        
        # Check if text_audio_map.json exists in the selected directory
        map_file_path = os.path.join(directory_path, "text_audio_map.json")
        if not os.path.exists(map_file_path):
            QMessageBox.warning(self, "Error", "The selected directory is not a valid Audiobook Directory.")
            return
        
        self.tableWidget.setRowCount(0)
        self.text_audio_map.clear()
        
        dir_name = os.path.basename(directory_path)
        audiobook_path = os.path.join('audiobooks', dir_name)
        self.audiobook_label.setText(f"{dir_name}")

        use_old_settings_reply = QMessageBox.question(self, 
                                    'Use Previouis Settings', 
                                    "Do you want to use the same settings from the previous generation of this audiobook?", 
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.No  # Default is 'No'
                                )
        
        generation_settings_path = os.path.join(directory_path, "generation_settings.json")
        if use_old_settings_reply == QMessageBox.Yes:
            self.load_and_set_generation_settings(generation_settings_path)
        else:
            self.create_generation_settings(generation_settings_path)

        self.worker = AudioGenerationWorker(self.generate_audio_for_sentence_threaded, audiobook_path)

        self.worker.started.connect(self.disable_buttons)
        self.regenerate_button.setStyleSheet("")
        self.worker.finished.connect(self.enable_buttons)

        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.start()


    def set_background_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self,"", "","Image Files (*.png *.jpg *.jpeg);;All Files (*)", options=options)
        if file_name:
            if not os.path.exists('image_backgrounds'):
                os.makedirs('image_backgrounds')
            image_name = os.path.basename(file_name)
            destination_path = os.path.join('image_backgrounds', image_name)
            if os.path.abspath(file_name) != os.path.abspath(destination_path):
                shutil.copy2(file_name, destination_path)
            self.set_background(destination_path)
            with open('settings.json', 'w') as json_file:
                json.dump({"background_image": destination_path}, json_file)

    def set_background_clear_image(self):
        # Reset the background pixmap attribute
        if hasattr(self, 'background_pixmap'):
            del self.background_pixmap
        
        self.background_label.clear()  # Clear the existing pixmap on the label

        # Update settings.json to remove the background image setting
        if os.path.exists('settings.json'):
            with open('settings.json', 'w') as json_file:
                json.dump({"background_image": None}, json_file)
                
        self.update_background()





#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#   Audio Generation Utilities
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def generate_audio_for_sentence_threaded(self, directory_path, progress_callback):
        # Load the existing text_audio_map
        audio_map_path = os.path.join(directory_path, 'text_audio_map.json')
        with open(audio_map_path, 'r', encoding='utf-8') as file:
            text_audio_map = json.load(file)

        total_sentences = len(text_audio_map)
        generated_count = sum(1 for entry in text_audio_map.values() if entry['generated'])

        # Iterate through each entry in the map
        for idx, entry in text_audio_map.items():
            sentence = entry['sentence']
            new_audio_path = entry['audio_path']
            generated = entry['generated']
            
            # Check if audio is already generated
            if not generated:
                # Generate audio for the sentence
                audio_path = self.generate_audio(sentence)
                
                # Check if audio is successfully generated
                print(audio_path)
                if audio_path:
                    file_idx = 0
                    new_audio_path = os.path.join(directory_path, f"audio_{file_idx}.wav")
                    while os.path.exists(new_audio_path):
                        file_idx += 1
                        new_audio_path = os.path.join(directory_path, f"audio_{file_idx}.wav")
                    os.rename(audio_path, new_audio_path)
                    # Update the audio path and set generated to true
                    text_audio_map[idx]['audio_path'] = new_audio_path
                    text_audio_map[idx]['generated'] = True
                    
                    # Increment the generated_count
                    generated_count += 1
                    
                    # Save the updated map back to the file
                    with open(audio_map_path, 'w', encoding='utf-8') as file:
                        json.dump(text_audio_map, file, ensure_ascii=False, indent=4)

            # If generated is true (either was already or just now), add to table
            if text_audio_map[idx]['generated']:
                sentence_item = QTableWidgetItem(sentence)
                sentence_item.setFlags(sentence_item.flags() & ~Qt.ItemIsEditable)
                row_position = self.tableWidget.rowCount()
                self.tableWidget.insertRow(row_position)
                self.tableWidget.setItem(row_position, 0, sentence_item)
                self.text_audio_map[str(idx)] = {"sentence": sentence, "audio_path": new_audio_path, "generated": text_audio_map[idx]['generated']}
            
            # Report progress
            progress_percentage = int((generated_count / total_sentences) * 100)
            progress_callback(progress_percentage)\
            
    def generate_audio(self, sentence):
        tort_setup = os.path.join(script_dir, "tort.yaml")
        parameters = load_config(tort_setup)
        audio_path = call_api(sentence, **parameters)
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

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#   Audio Play Utilities
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
        

    def play_audio_by_index(self, idx):
        if idx < self.tableWidget.rowCount():
            # Retrieve the sentence from the table
            item = self.tableWidget.item(idx, 0)  # Assuming the sentence is in column 0
            if item:  # Check if item is not None
                sentence = item.text()
                map_key = str(idx)
                if map_key in self.text_audio_map:
                    audio_path = self.text_audio_map[map_key]['audio_path']
                    
                    # Set the selected row in the table
                    self.tableWidget.selectRow(idx)
                    
                    # Set up and play the audio
                    self.media_player = QMediaPlayer()
                    self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
                    self.media_player.play()
                    self.media_player.stateChanged.connect(self.on_audio_finished)

    def on_audio_finished(self, state):
        # Check if the audio has finished playing
        if state == QMediaPlayer.StoppedState:
            # Increment the index to play the next audio
            self.current_sentence_idx += 1

            # Check if there's another audio file to play
            if self.current_sentence_idx < self.tableWidget.rowCount():  # Updated this line
                self.play_audio_by_index(self.current_sentence_idx)
            else:
                try:
                    self.media_player.stateChanged.disconnect(self.on_audio_finished)
                except TypeError:  # Handle the case where the signal was not connected
                    pass
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#   Function Utilities
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

    def save_json(self, audio_map_path, new_text_audio_map):
        with open(audio_map_path, 'w', encoding='utf-8') as file:
            json.dump(new_text_audio_map, file, ensure_ascii=False, indent=4)

    def create_audio_text_map(self, audio_map_path, sentences_list):
        new_text_audio_map = {}
        for idx, sentence in enumerate(sentences_list):
            generated = False
            audio_path = ""
            new_text_audio_map[str(idx)] = {"sentence": sentence, "audio_path": audio_path, "generated": generated}
            self.save_json(audio_map_path, new_text_audio_map)

    def create_generation_settings(self, generation_settings_path):
        selected_voice = self.voice_models_combo.currentText()
        selected_index = self.voice_index_combo.currentText()
        f0_pitch = self.voice_pitch_slider.value()
        index_rate = self.voice_index_slider.value()
        generation_settings = {"selected_voice":selected_voice, "selected_index":selected_index, "f0_pitch":f0_pitch, "index_rate":index_rate}
        self.save_json(generation_settings_path, generation_settings)

    def load_and_set_generation_settings(self, generation_settings_path):
        try:
            with open(generation_settings_path, 'r') as file:
                data = json.load(file)
                selected_voice = data.get('selected_voice', '')
                selected_index = data.get('selected_index', '')
                f0_pitch = data.get('f0_pitch', 0)
                index_rate = data.get('index_rate', 0)
                
                index_voice = self.voice_models_combo.findText(selected_voice)
                if index_voice >= 0:
                    self.voice_models_combo.setCurrentIndex(index_voice)
        
                index_index = self.voice_index_combo.findText(selected_index)
                if index_index >= 0:
                    self.voice_index_combo.setCurrentIndex(index_index)
        
                self.voice_pitch_slider.setValue(f0_pitch)
                self.voice_index_slider.setValue(index_rate)
        except FileNotFoundError:
            print(f"{generation_settings_path} not found.")
        except json.JSONDecodeError:
            print(f"{generation_settings_path} is not a valid JSON file.")
    
    def set_background(self, file_path):
        # Set the pixmap for the background label
        pixmap = QPixmap(file_path)
        self.background_pixmap = pixmap  # Save the pixmap as an attribute
        self.update_background()

    def resizeEvent(self, event):
        # Update background label geometry when window is resized
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.update_background()  # Update the background pixmap scaling
        super().resizeEvent(event)  # Call the superclass resize event method

    def update_background(self):
        # Check if background pixmap is set, then scale and set it
        if hasattr(self, 'background_pixmap'):
            scaled_pixmap = self.background_pixmap.scaled(self.background_label.size(), Qt.KeepAspectRatioByExpanding)
            self.background_label.setPixmap(scaled_pixmap)
            self.background_label.show()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#   GUI Utilites
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
    
    def updatePauseLabel(self, value):
        value = (self.export_pause_slider.value() / 10)
        self.export_pause_value_label.setText(str(value))

    def disable_buttons(self):
        buttons = [self.regenerate_button, 
                self.generate_button, 
                self.continue_audiobook_button]
        actions = [self.load_audiobook_action,
                self.export_audiobook_action,
                self.update_audiobook_action]

        for button in buttons:
            button.setDisabled(True)
            button.setStyleSheet("QPushButton { color: #A9A9A9; }")

        for action in actions:
            action.setDisabled(True)

    def enable_buttons(self):
        buttons = [self.regenerate_button, 
                self.generate_button, 
                self.continue_audiobook_button]
        actions = [self.load_audiobook_action,
                self.export_audiobook_action,
                self.update_audiobook_action]

        for button in buttons:
            button.setDisabled(False)
            button.setStyleSheet("")

        for action in actions:
            action.setDisabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = AudiobookMaker()
    main_window.show()
    sys.exit(app.exec_())
