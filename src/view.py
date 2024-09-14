# view.py

from PySide6.QtWidgets import (
    QSlider, QWidgetAction, QComboBox, QApplication, QMainWindow, QPushButton,
    QVBoxLayout, QLineEdit, QLabel, QWidget, QMessageBox,
    QHeaderView, QProgressBar, QHBoxLayout, QTableWidget, QTableWidgetItem, QFileDialog
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QPixmap, QAction, QScreen

import os
import json


class AudiobookMakerView(QMainWindow):

    # Define signals for user actions
    load_text_file_requested = Signal()
    start_generation_requested = Signal()
    play_selected_audio_requested = Signal()
    pause_audio_requested = Signal()
    play_all_from_selected_requested = Signal()
    regenerate_audio_for_sentence_requested = Signal()
    continue_audiobook_generation_requested = Signal()
    load_existing_audiobook_requested = Signal()
    update_audiobook_requested = Signal()
    export_audiobook_requested = Signal()
    set_background_image_requested = Signal()
    set_background_clear_image_requested = Signal()
    font_size_changed = Signal(int)
    voice_model_changed = Signal(str)
    voice_index_changed = Signal(str)
    voice_pitch_changed = Signal(int)
    voice_index_effect_changed = Signal(float)
    pause_between_sentences_changed = Signal(float)

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

        self.setStyleSheet(self.load_stylesheet())

        # Initialize media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player_connected = False
        self.playing_sequence = False  # Add this flag
        self.current_audio_index = 0  # Initialize current_audio_index
        self.audio_paths = []
        self.indices = []
        self.media_player.mediaStatusChanged.connect(self.on_audio_finished)
        self.current_audio_path = None  # Track the current audio file being played


        # Initialize UI components
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
        self.load_text.clicked.connect(self.on_load_text_clicked)
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
        self.voice_name_layout.addWidget(self.voice_models_combo, 1)
        self.voice_models_combo.currentTextChanged.connect(self.on_voice_model_changed)
        left_layout.addLayout(self.voice_name_layout)

        # -- Voice Index Combo Box
        self.voice_index_layout = QHBoxLayout()
        self.voice_index_label = QLabel("Voice Index: ")
        self.voice_index_combo = QComboBox()
        self.voice_index_layout.addWidget(self.voice_index_label)
        self.voice_index_layout.addWidget(self.voice_index_combo, 1)
        self.voice_index_combo.currentTextChanged.connect(self.on_voice_index_changed)
        left_layout.addLayout(self.voice_index_layout)

        # -- Voice Index Slider
        index = 0
        self.voice_index_value_label = QLabel(f"{index / 100}")  # 0 is the initial value of the slider
        max_index_str = "1"  # the maximum value the label will show
        estimated_width = len(max_index_str) * 50
        self.voice_index_value_label.setFixedWidth(estimated_width)

        self.voice_index_slider_layout = QHBoxLayout()
        self.voice_index_slider_label = QLabel("Index Effect: ")
        self.voice_index_slider = QSlider(Qt.Horizontal)
        self.voice_index_slider.setMinimum(0)
        self.voice_index_slider.setMaximum(100)
        self.voice_index_slider.setValue(index)
        self.voice_index_slider.setTickPosition(QSlider.TicksBelow)
        self.voice_index_slider.setTickInterval(1)

        self.voice_index_slider.valueChanged.connect(self.on_voice_index_slider_changed)

        self.voice_index_slider_layout.addWidget(self.voice_index_slider_label)
        self.voice_index_slider_layout.addWidget(self.voice_index_slider)
        self.voice_index_slider_layout.addWidget(self.voice_index_value_label)

        left_layout.addLayout(self.voice_index_slider_layout)

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

        self.voice_pitch_slider.valueChanged.connect(self.on_voice_pitch_slider_changed)

        self.voice_pitch_layout.addWidget(self.voice_pitch_label)
        self.voice_pitch_layout.addWidget(self.voice_pitch_slider)
        self.voice_pitch_layout.addWidget(self.voice_pitch_value_label)

        left_layout.addLayout(self.voice_pitch_layout)

        # -- Export Pause Slider
        pause = 0
        self.export_pause_value_label = QLabel(f"{pause / 10}")  # 0 is the initial value of the slider
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

        self.export_pause_slider.valueChanged.connect(self.on_export_pause_slider_changed)

        self.export_pause_layout.addWidget(self.export_pause_label)
        self.export_pause_layout.addWidget(self.export_pause_slider)
        self.export_pause_layout.addWidget(self.export_pause_value_label)

        left_layout.addLayout(self.export_pause_layout)

        # -- Start Audiobook Button
        self.generate_button = QPushButton("Start Audiobook Generation", self)
        self.generate_button.clicked.connect(self.on_generate_button_clicked)
        left_layout.addWidget(self.generate_button)

        # -- Play Audio Button
        self.play_button = QPushButton("Play Audio", self)
        self.play_button.clicked.connect(self.on_play_button_clicked)

        # -- Pause Audio Button
        self.pause_button = QPushButton("Pause", self)
        self.pause_button.clicked.connect(self.on_pause_button_clicked)

        # Arrange the play and pause buttons side by side
        self.play_pause_layout = QHBoxLayout()
        self.play_pause_layout.addWidget(self.play_button)
        self.play_pause_layout.addWidget(self.pause_button)
        left_layout.addLayout(self.play_pause_layout)

        # -- Play All Audio Button
        self.play_all_button = QPushButton("Play All from Selected", self)
        self.play_all_button.clicked.connect(self.on_play_all_button_clicked)
        left_layout.addWidget(self.play_all_button)

        # -- Regen Audio Button
        self.regenerate_button = QPushButton("Regenerate Audio", self)
        self.regenerate_button.clicked.connect(self.on_regenerate_button_clicked)
        left_layout.addWidget(self.regenerate_button)

        self.continue_audiobook_button = QPushButton("Continue Audiobook Generation", self)
        self.continue_audiobook_button.clicked.connect(self.on_continue_button_clicked)
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
        self.load_audiobook_action.triggered.connect(self.on_load_existing_audiobook_triggered)
        self.file_menu.addAction(self.load_audiobook_action)

        # Add Update Audiobook Sentences action to File menu
        self.update_audiobook_action = QAction("Update Audiobook Sentences", self)
        self.update_audiobook_action.triggered.connect(self.on_update_audiobook_triggered)
        self.file_menu.addAction(self.update_audiobook_action)

        # Add Export Audiobook action to File menu
        self.export_audiobook_action = QAction("Export Audiobook", self)
        self.export_audiobook_action.triggered.connect(self.on_export_audiobook_triggered)
        self.file_menu.addAction(self.export_audiobook_action)

        # Create a slider for font size
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setMinimum(8)
        self.font_slider.setMaximum(20)
        self.font_slider.setValue(14)
        self.font_slider.setTickPosition(QSlider.TicksBelow)
        self.font_slider.setTickInterval(1)
        self.font_slider.valueChanged.connect(self.on_font_slider_changed)

        # Create a QWidgetAction to embed the slider in the menu
        slider_action = QWidgetAction(self)
        slider_action.setDefaultWidget(self.font_slider)

        self.font_menu = self.menu.addMenu("Font Size")

        # Add slider to the font_menu in the menu bar
        self.font_menu.addAction(slider_action)

        self.background_menu = self.menu.addMenu("Background")

        # Add Set Background Image action to File menu
        self.set_background_action = QAction("Set Background Image", self)
        self.set_background_action.triggered.connect(self.on_set_background_image_triggered)
        self.background_menu.addAction(self.set_background_action)

        # Clear Background Image action to File menu
        self.set_background_clear_action = QAction("Clear Background Image", self)
        self.set_background_clear_action.triggered.connect(self.on_set_background_clear_image_triggered)
        self.background_menu.addAction(self.set_background_clear_action)

        # Window settings
        self.setWindowTitle("Audiobook Maker")
        screen = QScreen().geometry()  # Get the screen geometry
        target_ratio = 16 / 9

        width = screen.width() * 0.8
        height = width / target_ratio  # calculate height based on the target aspect ratio

        if height > screen.height():
            height = screen.height() * 0.8
            width = height * target_ratio  # calculate width based on the target aspect ratio

        # Set the calculated geometry for the window
        self.setGeometry(100, 100, int(width), int(height))

    # Methods for handling UI actions and emitting signals

    def on_load_text_clicked(self):
        self.load_text_file_requested.emit()

    def on_generate_button_clicked(self):
        self.start_generation_requested.emit()

    def on_play_button_clicked(self):
        self.play_selected_audio_requested.emit()

    def on_pause_button_clicked(self):
        self.pause_audio_requested.emit()

    def on_play_all_button_clicked(self):
        self.play_all_from_selected_requested.emit()

    def on_regenerate_button_clicked(self):
        self.regenerate_audio_for_sentence_requested.emit()

    def on_continue_button_clicked(self):
        self.continue_audiobook_generation_requested.emit()

    def on_load_existing_audiobook_triggered(self):
        self.load_existing_audiobook_requested.emit()

    def on_update_audiobook_triggered(self):
        self.update_audiobook_requested.emit()

    def on_export_audiobook_triggered(self):
        self.export_audiobook_requested.emit()

    def on_set_background_image_triggered(self):
        self.set_background_image_requested.emit()

    def on_set_background_clear_image_triggered(self):
        self.set_background_clear_image_requested.emit()

    def on_font_slider_changed(self, value):
        self.font_size_changed.emit(value)
        self.update_font_size_from_slider(value)

    def on_voice_model_changed(self, text):
        self.voice_model_changed.emit(text)

    def on_voice_index_changed(self, text):
        self.voice_index_changed.emit(text)

    def on_voice_pitch_slider_changed(self, value):
        self.updateVoicePitchLabel(value)
        self.voice_pitch_changed.emit(value)

    def on_voice_index_slider_changed(self, value):
        value = value / 100.0
        self.updateVoiceIndexLabel(value)
        self.voice_index_effect_changed.emit(value)

    def on_export_pause_slider_changed(self, value):
        value = value / 10.0
        self.updatePauseLabel(value)
        self.pause_between_sentences_changed.emit(value)

    # Methods to update the UI
    def updateVoicePitchLabel(self, value):
        self.voice_pitch_value_label.setText(str(value))

    def updateVoiceIndexLabel(self, value):
        self.voice_index_value_label.setText(str(value))

    def updatePauseLabel(self, value):
        self.export_pause_value_label.setText(str(value))

    def update_font_size_from_slider(self, value):
        font_size = f"{value}pt"
        self.setStyleSheet(self.load_stylesheet(font_size))

    # Method to load stylesheet
    def load_stylesheet(self, font_size="14pt"):
        # Load the base stylesheet
        with open("base.css", "r") as file:
            stylesheet = file.read()

        # Replace font-size
        modified_stylesheet = stylesheet.replace("font-size: 14pt;", f"font-size: {font_size};")
        return modified_stylesheet

    # Method to set background
    def set_background(self, file_path):
        # Set the pixmap for the background label
        pixmap = QPixmap(file_path)
        self.background_pixmap = pixmap  # Save the pixmap as an attribute
        self.update_background()

    def update_background(self):
        # Check if background pixmap is set, then scale and set it
        if hasattr(self, 'background_pixmap'):
            scaled_pixmap = self.background_pixmap.scaled(self.background_label.size(), Qt.KeepAspectRatioByExpanding)
            self.background_label.setPixmap(scaled_pixmap)
            self.background_label.show()

    # Override resizeEvent to update background
    def resizeEvent(self, event):
        # Update background label geometry when window is resized
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.update_background()  # Update the background pixmap scaling
        super().resizeEvent(event)  # Call the superclass resize event method

    # Methods to enable/disable buttons
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

    # Methods to update UI elements, which can be called by the controller
    def set_audiobook_label(self, text):
        self.audiobook_label.setText(text)

    def set_progress(self, value):
        self.progress_bar.setValue(value)

    def clear_table(self):
        self.tableWidget.setRowCount(0)

    def add_table_item(self, row, text):
        sentence_item = QTableWidgetItem(text)
        sentence_item.setFlags(sentence_item.flags() & ~Qt.ItemIsEditable)
        self.tableWidget.insertRow(row)
        self.tableWidget.setItem(row, 0, sentence_item)

    def get_selected_table_row(self):
        return self.tableWidget.currentRow()

    def select_table_row(self, row):
        self.tableWidget.selectRow(row)

    # Methods to retrieve data from UI elements
    def get_book_name(self):
        return self.book_name_input.text().strip()

    def get_voice_model(self):
        return self.voice_models_combo.currentText()

    def get_voice_index(self):
        return self.voice_index_combo.currentText()

    def get_voice_pitch(self):
        return self.voice_pitch_slider.value()

    def get_voice_index_effect(self):
        return self.voice_index_slider.value() / 100.0

    def get_pause_between_sentences(self):
        return self.export_pause_slider.value() / 10.0

    # Methods to populate combo boxes
    def set_voice_models(self, models):
        self.voice_models_combo.clear()
        self.voice_models_combo.addItems(models)

    def set_voice_indexes(self, indexes):
        self.voice_index_combo.clear()
        self.voice_index_combo.addItems(indexes)

    # Methods for showing message boxes and file dialogs
    def show_message(self, title, message, icon=QMessageBox.Information):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.exec()

    def ask_question(self, title, question, buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No):
        reply = QMessageBox.question(self, title, question, buttons, default_button)
        return reply == QMessageBox.Yes

    def get_open_file_name(self, title, directory='', filter=''):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        filepath, _ = QFileDialog.getOpenFileName(self, title, directory, filter, options=options)
        return filepath

    def get_existing_directory(self, title, directory=''):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, title, directory, options)
        return directory

    # Media player methods
    def initialize_media_player(self):
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.mediaStatusChanged.connect(self.on_audio_finished)

    def play_audio(self, audio_path):
        if not audio_path:
            return
        self.initialize_media_player()
        self.media_player.setSource(QUrl.fromLocalFile(audio_path))
        self.media_player.play()
        self.current_audio_path = audio_path  # Update current audio path

    def pause_audio(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        elif self.media_player.playbackState() == QMediaPlayer.PausedState:
            self.media_player.play()

    def stop_audio(self):
        if self.media_player.playbackState() != QMediaPlayer.StoppedState:
            self.media_player.stop()
            self.release_media_player_resources()
            self.media_player.setSource(QUrl())
            self.media_player.mediaStatusChanged.disconnect(self.on_audio_finished)
            self.current_audio_path = None  # Clear current audio path
            # Reset playing sequence and related variables here
            self.playing_sequence = False
            self.current_audio_index = 0
            self.audio_paths = []
            self.indices = []

    def play_audio_sequence(self, audio_paths, indices):
        self.audio_paths = audio_paths
        self.indices = indices
        self.current_audio_index = 0
        self.playing_sequence = True  # Set the flag to True
        if self.current_audio_index < len(self.audio_paths):
            self.play_audio(self.audio_paths[self.current_audio_index])
            self.select_table_row(self.indices[self.current_audio_index])

    def on_audio_finished(self, state):
        if state == QMediaPlayer.EndOfMedia or state == QMediaPlayer.StoppedState:
            self.current_audio_path = None  # Clear current audio path
            if self.playing_sequence:
                self.current_audio_index += 1
                if self.current_audio_index < len(self.audio_paths):
                    self.play_audio(self.audio_paths[self.current_audio_index])
                    self.select_table_row(self.indices[self.current_audio_index])
                else:
                    # Sequence finished
                    self.playing_sequence = False
                    self.current_audio_index = 0
                    self.audio_paths = []
                    self.indices = []
            else:
                # Do nothing for single audio playback
                pass
            
    def is_audio_playing(self, audio_path):
        return self.current_audio_path == audio_path
    
    def skip_current_audio(self):
        if self.playing_sequence:
            self.media_player.stop()
            self.release_media_player_resources()
            self.media_player.setSource(QUrl())
            self.current_audio_path = None
            self.on_audio_finished(QMediaPlayer.EndOfMedia)
    
    def release_media_player_resources(self):
        # Reinitialize the media player to release any file handles
        # This way is NECESSARY to prevent the gui from freezing (for somne unknown reason)
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.mediaStatusChanged.connect(self.on_audio_finished)

    def update_generation_settings(self, settings):
        selected_voice = settings.get('selected_voice', '')
        selected_index = settings.get('selected_index', '')
        f0_pitch = settings.get('f0_pitch', 0)
        index_rate = settings.get('index_rate', 0)

        index_voice = self.voice_models_combo.findText(selected_voice)
        if index_voice >= 0:
            self.voice_models_combo.setCurrentIndex(index_voice)

        index_index = self.voice_index_combo.findText(selected_index)
        if index_index >= 0:
            self.voice_index_combo.setCurrentIndex(index_index)

        self.voice_pitch_slider.setValue(f0_pitch)
        self.voice_index_slider.setValue(int(index_rate * 100))
