# view.py

from PySide6.QtWidgets import (
    QSlider, QWidgetAction, QComboBox, QApplication, QMainWindow, QPushButton,
    QVBoxLayout, QLineEdit, QLabel, QWidget, QMessageBox, QCheckBox,
    QHeaderView, QProgressBar, QHBoxLayout, QTableWidget, QTableWidgetItem, QFileDialog, QScrollArea,
    QSizePolicy, QSpinBox, QSplitter, QDialog, QListWidget, QListWidgetItem, QColorDialog, QMenu
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QPixmap, QAction, QScreen

import os
import json
import fnmatch


from PySide6.QtWidgets import (
    QDialog, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QPushButton, QInputDialog, QColorDialog, QMessageBox
)
from PySide6.QtGui import QColor

class SpeakerManagementDialog(QDialog):
    def __init__(self, parent=None, speakers=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Speakers")
        self.setModal(True)
        self.speakers = speakers or {}

        # Layouts and widgets
        self.layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        # Populate the list
        self.populate_speaker_list()

        # Add buttons to add, edit, delete speakers
        self.add_button = QPushButton("Add Speaker")
        self.delete_button = QPushButton("Delete Speaker")
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.delete_button)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

        # Connect signals
        self.add_button.clicked.connect(self.add_speaker)
        self.delete_button.clicked.connect(self.delete_speaker)
        self.list_widget.itemDoubleClicked.connect(self.edit_speaker)

    def populate_speaker_list(self):
        self.list_widget.clear()
        for speaker_id, speaker in self.speakers.items():
            item = QListWidgetItem(f"Speaker {speaker_id}: {speaker['name']}")
            color = speaker.get('color', Qt.gray)
            if isinstance(color, str):
                color = QColor(color)  # Convert string to QColor
            item.setBackground(color)
            item.setData(Qt.UserRole, speaker_id)  # Store speaker_id in item
            self.list_widget.addItem(item)

    def add_speaker(self):
        new_speaker_id = max(self.speakers.keys()) + 1 if self.speakers else 2  # Start from 2
        speaker_name, ok = QInputDialog.getText(self, "Add Speaker", "Enter Speaker Name:")
        if ok and speaker_name:
            # Let user select a color
            color = QColorDialog.getColor()
            if color.isValid():
                speaker = {
                    'name': speaker_name,
                    'color': color,
                    'settings': {}  # Empty settings initially
                }
                self.speakers[new_speaker_id] = speaker
                self.populate_speaker_list()
        else:
            # User canceled input
            pass

    def edit_speaker(self, item):
        speaker_id = item.data(Qt.UserRole)
        speaker = self.speakers.get(speaker_id)
        if speaker:
            # Let user edit name
            speaker_name, ok = QInputDialog.getText(self, "Edit Speaker", "Enter Speaker Name:", text=speaker['name'])
            if ok and speaker_name:
                speaker['name'] = speaker_name
                # Let user select a color
                color = QColorDialog.getColor(initial=speaker.get('color', Qt.gray))
                if color.isValid():
                    speaker['color'] = color
                self.populate_speaker_list()

    def delete_speaker(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Delete Speaker", "Please select a speaker to delete.")
            return
        for item in selected_items:
            speaker_id = item.data(Qt.UserRole)
            if speaker_id == 1:
                QMessageBox.warning(self, "Delete Speaker", "Cannot delete the default speaker.")
                continue
            # Remove the speaker
            del self.speakers[speaker_id]
        self.populate_speaker_list()

    def get_speakers(self):
        # Convert QColor to hex string for serialization
        for speaker in self.speakers.values():
            color = speaker.get('color', Qt.gray)
            if isinstance(color, QColor):
                speaker['color'] = color.name()
        return self.speakers



class AudiobookMakerView(QMainWindow):

    # Define signals for user actions
    load_text_file_requested = Signal()
    load_tts_requested = Signal()
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
    tts_engine_changed = Signal(object)
    s2s_engine_changed = Signal(str)
    audio_finished_signal = Signal()
    speakers_updated = Signal(object)
    sentence_speaker_changed = Signal(int, int)
    # current_speaker_changed = Signal(int)
    generation_settings_changed = Signal()
    stop_generation_requested = Signal()
    regen_mode_activated = Signal(bool)



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
        
        self.speakers_updated.connect(self.update_speaker_selection_combo)


        self.tts_config = self.load_tts_config('configs/tts_config.json')
        self.s2s_config = self.load_s2s_config('configs/s2s_config.json')
        self.speakers = {
                1: {'name': 'Narrator', 'color': Qt.gray, 'settings': {}}
            }

        # Initialize UI components
        self.init_ui()
        
    def reset(self):
        self.clear_table()
        self.set_audiobook_label("No Audio Book Set")
        self.speakers = {
            1: {'name': 'Narrator', 'color': Qt.gray, 'settings': {}}
        }
        self.update_speaker_selection_combo()
        self.disable_speaker_menu()

        # Reset TTS and s2s options
        self.tts_engine_combo.setCurrentIndex(0)
        self.update_tts_options(self.get_tts_engine())
        self.s2s_engine_combo.setCurrentIndex(0)
        self.update_s2s_options(self.get_s2s_engine())
        self.use_s2s_checkbox.setChecked(False)
        self.export_pause_slider.setValue(0)
        self.updatePauseLabel(0)

    def init_ui(self):
        # Main Layout as Vertical Layout to stack main content and bottom box
        self.filepath = None
        main_layout = QVBoxLayout()

        # Main Content Layout (Horizontal)
        main_content_layout = QHBoxLayout()

        # Left side Layout
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10) 
        left_container = QWidget(self)
        left_container.setLayout(left_layout)
        left_container.setMaximumWidth(500)
        main_content_layout.addWidget(left_container)

        # Initialize TTS Options
        self.tts_options_widget = QWidget()
        self.tts_options_layout = QVBoxLayout()
        self.tts_options_widget.setLayout(self.tts_options_layout)
        self.tts_options_widget.setVisible(False)  # Initially hidden

        # Make the TTS options scrollable
        self.tts_options_scroll_area = QScrollArea()
        self.tts_options_scroll_area.setWidgetResizable(True)
        self.tts_options_scroll_area.setWidget(self.tts_options_widget)
        self.tts_options_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tts_options_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Initialize s2s Options
        self.s2s_options_widget = QWidget()
        self.s2s_options_layout = QVBoxLayout()
        self.s2s_options_widget.setLayout(self.s2s_options_layout)
        self.s2s_options_widget.setVisible(False)  # Initially hidden

        # Make the s2s options scrollable
        self.s2s_options_scroll_area = QScrollArea()
        self.s2s_options_scroll_area.setWidgetResizable(True)
        self.s2s_options_scroll_area.setWidget(self.s2s_options_widget)
        self.s2s_options_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Update options layout
        self.options_layout = QVBoxLayout()
        self.options_layout.addWidget(self.s2s_options_scroll_area, stretch=1)
        self.options_layout.addWidget(self.tts_options_scroll_area, stretch=1)

        # -- TTS Engine Combo Box
        self.tts_engine_layout = QHBoxLayout()
        self.tts_engine_label = QLabel("TTS Engine: ")
        self.tts_engine_combo = QComboBox()
        self.tts_engine_layout.addWidget(self.tts_engine_label)
        self.tts_engine_layout.addWidget(self.tts_engine_combo, 1)
        self.tts_engine_combo.currentTextChanged.connect(self.on_tts_engine_changed)
        left_layout.addLayout(self.tts_engine_layout)
        
        # -- s2s Engine Combo Box
        self.s2s_engine_layout = QHBoxLayout()
        self.s2s_engine_label = QLabel("S2S Engine: ")
        self.s2s_engine_combo = QComboBox()
        self.s2s_engine_layout.addWidget(self.s2s_engine_label)
        self.s2s_engine_layout.addWidget(self.s2s_engine_combo, 1)
        self.s2s_engine_combo.currentTextChanged.connect(self.on_s2s_engine_changed)
        left_layout.addLayout(self.s2s_engine_layout)
        
        if self.tts_engine_combo.count() > 0:
            self.tts_engine_combo.setCurrentIndex(0)

        self.use_s2s_checkbox = QCheckBox("Use s2s Engine", self)
        left_layout.addWidget(self.use_s2s_checkbox)
        self.use_s2s_checkbox.stateChanged.connect(self.on_use_s2s_changed)

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

        # -- Start and Stop Buttons
        self.generation_buttons_layout = QHBoxLayout()
        self.start_generation_button = QPushButton("Start Audiobook Generation", self)
        self.start_generation_button.clicked.connect(self.on_generate_button_clicked)
        self.stop_generation_button = QPushButton("Stop", self)
        self.stop_generation_button.clicked.connect(self.on_stop_button_clicked)
        self.stop_generation_button.setEnabled(False)  # Disabled initially
        self.stop_generation_button.setStyleSheet("QPushButton { color: #A9A9A9; }")
        self.generation_buttons_layout.addWidget(self.start_generation_button)
        self.generation_buttons_layout.addWidget(self.stop_generation_button)
        left_layout.addLayout(self.generation_buttons_layout)

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
        self.regenerate_button = QPushButton("Regenerate Chosen Sentence", self)
        self.regenerate_button.clicked.connect(self.on_regenerate_button_clicked)
        left_layout.addWidget(self.regenerate_button)

        self.continue_audiobook_button = QPushButton("Regenerate/Continue Audiobook Generation", self)
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

        # Create a horizontal layout to hold the table and options
        right_inner_layout = QHBoxLayout()

        # Table widget
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setColumnCount(1)
        self.tableWidget.setHorizontalHeaderLabels(['Sentence'])
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tableWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow table to expand
        right_inner_layout.addWidget(self.tableWidget)

        # Add the options layout
        right_inner_layout.addLayout(self.options_layout)

        # Set Stretch Factors: Table = 3, Options = 1
        right_inner_layout.setStretch(0, 3)  # Table takes 3 parts
        right_inner_layout.setStretch(1, 1)  # Options take 1 part

        right_layout.addLayout(right_inner_layout)
        main_content_layout.addLayout(right_layout)

        # Add the main content layout to the main vertical layout
        main_layout.addLayout(main_content_layout)

        # Create the bottom rectangular box for Regeneration Mode
        self.regen_mode_widget = QWidget(self)
        self.regen_mode_widget.setStyleSheet("background-color: green;")
        self.regen_mode_layout = QHBoxLayout()
        self.regen_mode_label = QLabel("Regeneration mode is on", self)
        self.regen_mode_label.setStyleSheet("color: white; font-weight: bold;")
        self.regen_mode_label.setAlignment(Qt.AlignCenter)
        self.regen_mode_layout.addWidget(self.regen_mode_label)
        self.regen_mode_widget.setLayout(self.regen_mode_layout)
        self.regen_mode_widget.setVisible(False)  # Initially hidden
        self.regen_mode_widget.setFixedHeight(50)  # Set a fixed height for the box

        # Add the regen mode widget to the main layout
        main_layout.addWidget(self.regen_mode_widget)

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

        # Add Set Background Image action to Background menu
        self.set_background_action = QAction("Set Background Image", self)
        self.set_background_action.triggered.connect(self.on_set_background_image_triggered)
        self.background_menu.addAction(self.set_background_action)

        # Clear Background Image action to Background menu
        self.set_background_clear_action = QAction("Clear Background Image", self)
        self.set_background_clear_action.triggered.connect(self.on_set_background_clear_image_triggered)
        self.background_menu.addAction(self.set_background_clear_action)
        
        self.speaker_menu = self.menu.addMenu("Speakers")
        self.speaker_menu.setEnabled(False) 
        
        self.speaker_selection_layout = QHBoxLayout()
        self.speaker_selection_label = QLabel("Current Speaker: ")
        self.speaker_selection_combo = QComboBox()
        self.speaker_selection_layout.addWidget(self.speaker_selection_label)
        self.speaker_selection_layout.addWidget(self.speaker_selection_combo, 1)
        self.speaker_selection_combo.currentIndexChanged.connect(self.on_current_speaker_changed)
        left_layout.addLayout(self.speaker_selection_layout)

        # After initializing self.speakers
        self.update_speaker_selection_combo()
        self.populate_s2s_engines()

        # Add Manage Speakers action to Speakers menu
        self.manage_speakers_action = QAction("Manage Speakers", self)
        self.manage_speakers_action.triggered.connect(self.on_manage_speakers)
        self.speaker_menu.addAction(self.manage_speakers_action)
        
        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)

        # Create Tools menu
        self.tools_menu = self.menu.addMenu("Tools")

        # Add Regeneration Mode action
        self.regen_mode_action = QAction("Regeneration Mode", self, checkable=True)
        self.regen_mode_action.setChecked(False)
        self.regen_mode_action.triggered.connect(self.toggle_regeneration_mode)
        self.tools_menu.addAction(self.regen_mode_action)

        # Window settings
        self.setWindowTitle("Audiobook Maker")
        screen = QScreen().availableGeometry()  # Get the available screen geometry
        target_ratio = 16 / 9

        width = screen.width() * 0.8  # Adjusted to fit within the screen
        height = width / target_ratio  # calculate height based on the target aspect ratio

        if height > screen.height() * 0.8:
            height = screen.height() * 0.8
            width = height * target_ratio  # calculate width based on the target aspect ratio

        # Set the calculated geometry for the window
        self.setGeometry(100, 100, int(width), int(height))
        
    def toggle_regeneration_mode(self, checked):
        if checked:
            self.regen_mode_widget.setVisible(True)
            self.regen_mode_activated.emit(True)
            self.regen_mode_action.setChecked(True)
        else:
            self.regen_mode_widget.setVisible(False)
            self.regen_mode_activated.emit(False)
            self.regen_mode_action.setChecked(False)
        
    def populate_s2s_engines(self):
        s2s_config = self.load_s2s_config('configs/s2s_config.json')
        engines = [engine['name'] for engine in s2s_config.get('s2s_engines', [])]
        self.s2s_engine_combo.addItems(engines)
        self.s2s_config = s2s_config  # Store for later use


    def update_speaker_selection_combo(self):
        self.speaker_selection_combo.blockSignals(True)  # Prevent signal during update
        self.speaker_selection_combo.clear()
        for speaker_id, speaker in self.speakers.items():
            self.speaker_selection_combo.addItem(f"{speaker['name']}", userData=speaker_id)
        self.speaker_selection_combo.blockSignals(False)
        
    def enable_speaker_menu(self):
        self.speaker_menu.setEnabled(True)


    def disable_speaker_menu(self):
        self.speaker_menu.setEnabled(False)

    # In on_current_speaker_changed method
    def on_current_speaker_changed(self, index):
        speaker_id = self.speaker_selection_combo.itemData(index)
        if speaker_id is not None:
            if speaker_id in self.speakers:
                self.load_speaker_settings(speaker_id)
                # Emit a signal to notify the controller or model
                # self.current_speaker_changed.emit(speaker_id)
            else:
                self.reset_settings_to_default()
        else:
            self.reset_settings_to_default()
            
    def reset_settings_to_default(self):
        default_speaker_id = 1
        if default_speaker_id in self.speakers:
            self.load_speaker_settings(default_speaker_id)
            self.speaker_selection_combo.setCurrentIndex(
                self.speaker_selection_combo.findData(default_speaker_id)
            )
            # Emit the signal to notify any listeners about the change
            # self.current_speaker_changed.emit(default_speaker_id)
        else:
            self.show_message("Error", "Default speaker not found.", QMessageBox.Critical)

    def update_current_speaker_setting(self, attribute, value):
        current_speaker_id = self.get_current_speaker_id()
        if current_speaker_id in self.speakers:
            speaker = self.speakers[current_speaker_id]
            speaker_settings = speaker.setdefault('settings', {})
            speaker_settings[attribute] = value
        else:
            pass

    def get_current_speaker_id(self):
        index = self.speaker_selection_combo.currentIndex()
        speaker_id = self.speaker_selection_combo.itemData(index)
        if speaker_id is not None:
            return speaker_id
        else:
            return 1  # Default speaker



    def assign_speaker_to_selected(self, speaker_id):
        selected_rows = self.tableWidget.selectionModel().selectedRows()
        for index in selected_rows:
            row = index.row()
            self.set_row_speaker(row, speaker_id)
            self.sentence_speaker_changed.emit(row, speaker_id)

    
    def on_manage_speakers(self):
        # Open the speaker management dialog
        dialog = SpeakerManagementDialog(self, self.speakers)
        dialog.exec()
        # Update speakers after the dialog is closed
        self.speakers = dialog.get_speakers()
        # print("Before emitting, speakers:", self.speakers)
        self.speakers_updated.emit(self.speakers)


    def set_row_speaker(self, row, speaker_id):
        speaker = self.speakers.get(str(speaker_id), None)
        if not speaker: # HOT FIX, should figure out why speaker_id needs to be a string for one check, and then int for another for color
            speaker = self.speakers.get(speaker_id, None)
        color = speaker.get('color', Qt.gray)
        if isinstance(color, str):
            color = QColor(color)
        for col in range(self.tableWidget.columnCount()):
            item = self.tableWidget.item(row, col)
            if item:
                item.setBackground(color)
                
    def load_speaker_settings(self, speaker_id):
        speaker = self.speakers.get(speaker_id, {})
        settings = speaker.get('settings', {})
        # Update TTS engine
        tts_engine = settings.get('tts_engine', self.tts_engine_combo.currentText())
        index_tts = self.tts_engine_combo.findText(tts_engine)
        self.tts_engine_combo.blockSignals(True)  # Block signals
        if index_tts >= 0:
            self.tts_engine_combo.setCurrentIndex(index_tts)
        else:
            self.tts_engine_combo.setCurrentIndex(0)  # Default to first TTS engine
        self.tts_engine_combo.blockSignals(False)  # Unblock signals

        # Update TTS options
        self.update_tts_options(tts_engine)
        # Set TTS parameters
        self.set_tts_parameters(settings)

        # Update s2s engine
        s2s_engine = settings.get('s2s_engine', self.s2s_engine_combo.currentText())
        index_s2s = self.s2s_engine_combo.findText(s2s_engine)
        self.s2s_engine_combo.blockSignals(True)  # Block signals
        if index_s2s >= 0:
            self.s2s_engine_combo.setCurrentIndex(index_s2s)
        else:
            self.s2s_engine_combo.setCurrentIndex(0)  # Default to first s2s engine
        self.s2s_engine_combo.blockSignals(False)  # Unblock signals

        # Update s2s options
        self.update_s2s_options(s2s_engine)
        # Set s2s parameters
        self.set_s2s_parameters(settings)

        # Update Use s2s checkbox
        use_s2s = settings.get('use_s2s', False)
        self.use_s2s_checkbox.blockSignals(True)
        self.use_s2s_checkbox.setChecked(use_s2s)
        self.use_s2s_checkbox.blockSignals(False)

    def set_s2s_parameters(self, settings):
        s2s_engine = self.get_s2s_engine()
        engine_config = next(
            (engine for engine in self.s2s_config.get('s2s_engines', []) if engine['name'] == s2s_engine),
            None
        )
        if engine_config:
            for param in engine_config.get('parameters', []):
                attribute = param['attribute']
                widget = getattr(self, f"{attribute}_widget", None)
                if widget:
                    value = settings.get(attribute, None)
                    if value is not None:
                        if param['type'] in ('text', 'file'):
                            widget.setText(str(value))
                        elif param['type'] == 'spinbox':
                            widget.setValue(value)
                        elif param['type'] == 'checkbox':
                            widget.setChecked(bool(value))
                        elif param['type'] == 'combobox':
                            index = widget.findText(str(value))
                            if index >= 0:
                                widget.setCurrentIndex(index)
                            else:
                                widget.setCurrentIndex(0)  # Default to first item
                        elif param['type'] == 'slider':
                            widget.setValue(value)
                    else:
                        if param['type'] == 'combobox':
                            widget.setCurrentIndex(0)


    def set_tts_parameters(self, settings):
        tts_engine = self.get_tts_engine()
        engine_config = next(
            (engine for engine in self.tts_config.get('tts_engines', []) if engine['name'] == tts_engine),
            None
        )
        if engine_config:
            for param in engine_config.get('parameters', []):
                attribute = param['attribute']
                widget = getattr(self, f"{attribute}_widget", None)
                if widget:
                    value = settings.get(attribute, None)
                    if value is not None:
                        if param['type'] in ('text', 'file'):
                            widget.setText(str(value))
                        elif param['type'] == 'spinbox':
                            widget.setValue(value)
                        elif param['type'] == 'checkbox':
                            widget.setChecked(bool(value))
                        elif param['type'] == 'combobox':
                            index = widget.findText(str(value))
                            if index >= 0:
                                widget.setCurrentIndex(index)
                            else:
                                widget.setCurrentIndex(0)  # Default to first item
                        elif param['type'] == 'slider':
                            widget.setValue(value)
                    else:
                        if param['type'] == 'combobox':
                            widget.setCurrentIndex(0)  # Default to first item when value is None


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


    def on_export_pause_slider_changed(self, value):
        pause_duration = value / 10.0
        self.updatePauseLabel(pause_duration)
        self.update_current_speaker_setting('pause_duration', pause_duration)
        # self.pause_between_sentences_changed.emit(pause_duration)
        
    def on_s2s_engine_changed(self, engine_name):
        self.update_s2s_options(engine_name)
        self.update_current_speaker_setting('s2s_engine', engine_name)
        
    def on_stop_button_clicked(self):
        confirm = self.ask_question(
            "Stop Generation",
            "Are you sure you want to stop the generation?",
            buttons=QMessageBox.Yes | QMessageBox.No,
            default_button=QMessageBox.No
        )
        if confirm:
            self.stop_generation_requested.emit()


    def updatePauseLabel(self, value):
        self.export_pause_value_label.setText(str(value))

    def update_font_size_from_slider(self, value):
        font_size = f"{value}pt"
        self.setStyleSheet(self.load_stylesheet(font_size))
        
    def populate_tts_engines(self):
        engines = [engine['name'] for engine in self.tts_config.get('tts_engines')]
        self.tts_engine_combo.addItems(engines)
    
    def load_tts_config(self, config_path):
        if not os.path.exists(config_path):
            self.show_message("Error", f"Configuration file {config_path} not found.", QMessageBox.Critical)
            return {}
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def load_s2s_config(self, config_path):
        if not os.path.exists(config_path):
            self.show_message("Error", f"s2s configuration file {config_path} not found.", QMessageBox.Critical)
            return {}
        with open(config_path, 'r') as f:
            return json.load(f)
    

    def load_stylesheet(self, font_size="14pt"):
        # Load the base stylesheet
        with open("base.css", "r") as file:
            stylesheet = file.read()

        # Replace font-size
        modified_stylesheet = stylesheet.replace("font-size: 14pt;", f"font-size: {font_size};")
        return modified_stylesheet

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

    def disable_buttons(self):
        buttons = [self.regenerate_button,
                   self.start_generation_button,
                   self.continue_audiobook_button]
        actions = [self.load_audiobook_action,
                   self.export_audiobook_action,
                   self.update_audiobook_action]

        for button in buttons:
            button.setDisabled(True)
            button.setStyleSheet("QPushButton { color: #A9A9A9; }")

        for action in actions:
            action.setDisabled(True)

    def on_disable_stop_button(self):
        self.stop_generation_button.setEnabled(False)
        self.stop_generation_button.setStyleSheet("QPushButton { color: #A9A9A9; }")
        
    def on_enable_stop_button(self):
        self.stop_generation_button.setEnabled(True)
        self.stop_generation_button.setStyleSheet("")

    def enable_buttons(self):
        buttons = [self.regenerate_button,
                   self.start_generation_button,
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
    
    def set_start_generation_button_text(self, text):
        self.start_generation_button.setText(text)

    def clear_table(self):
        self.tableWidget.setRowCount(0)

    def add_table_item(self, row, text):
        # Ensure the table has enough rows
        current_row_count = self.tableWidget.rowCount()
        if current_row_count <= row:
            self.tableWidget.setRowCount(row + 1)
        sentence_item = QTableWidgetItem(text)
        sentence_item.setFlags(sentence_item.flags() & ~Qt.ItemIsEditable)
        self.tableWidget.setItem(row, 0, sentence_item)


    def get_selected_table_row(self):
        return self.tableWidget.currentRow()

    def select_table_row(self, row):
        self.tableWidget.selectRow(row)

    # Methods to retrieve data from UI elements
    def get_book_name(self):
        return self.book_name_input.text().strip()

    def get_pause_between_sentences(self):
        return self.export_pause_slider.value() / 10.0

    def get_tts_engine(self):
        return self.tts_engine_combo.currentText()
    
    def get_s2s_engine(self):
        return self.s2s_engine_combo.currentText()
    
    def on_use_s2s_changed(self, state):
        is_checked = self.use_s2s_checkbox.isChecked()
        self.update_current_speaker_setting('use_s2s', is_checked)
        self.generation_settings_changed.emit()
    
    def set_tts_engines(self, engines):
        self.tts_engine_combo.clear()
        self.tts_engine_combo.addItems(engines)
        
    def on_tts_engine_changed(self, engine_name):
        # self.set_load_tts_button_color("")  # Reset color when TTS engine changes
        self.update_tts_options(engine_name)  # Update the TTS options in the view
        self.update_current_speaker_setting('tts_engine', engine_name)
        self.tts_engine_changed.emit(self.speakers)
        # self.speakers_updated.emit(self.speakers)

    def update_s2s_options(self, engine_name):
        if not engine_name:
            self.s2s_options_widget.setVisible(False)
            return

        # Clear existing widgets and layouts
        self.clear_layout(self.s2s_options_layout)

        # Find the engine config
        engine_config = next(
            (engine for engine in self.s2s_config.get('s2s_engines', []) if engine['name'] == engine_name),
            None
        )

        if not engine_config:
            self.show_message("Error", f"No configuration found for s2s engine: {engine_name}", QMessageBox.Critical)
            self.s2s_options_widget.setVisible(False)
            return

        # Create a label for the s2s engine
        engine_label = QLabel(engine_config.get('label', f"{engine_name} Settings"))
        engine_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.s2s_options_layout.addWidget(engine_label)

        # Iterate over parameters and create widgets
        for param in engine_config.get('parameters', []):
            widget_layout = self.create_widget_for_parameter(param)
            if widget_layout:
                self.s2s_options_layout.addLayout(widget_layout)

        self.s2s_options_layout.addStretch()
        self.s2s_options_widget.setVisible(True)



    def update_tts_options(self, engine_name):
        if not engine_name:
            # If engine_name is empty, simply hide the TTS options without showing an error
            self.tts_options_widget.setVisible(False)
            return

        # Clear existing widgets and layouts
        self.clear_layout(self.tts_options_layout)
        
        # Find the engine config using a for loop
        engine_config = None
        for engine in self.tts_config.get('tts_engines', []):
            if engine['name'].lower() == engine_name.lower():
                engine_config = engine
                break

        if not engine_config:
            self.show_message("Error", f"No configuration found for TTS engine: {engine_name}", QMessageBox.Critical)
            self.tts_options_widget.setVisible(False)
            return
        
        # Create a label for the TTS engine
        engine_label = QLabel(f"{engine_name} Settings")
        engine_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.tts_options_layout.addWidget(engine_label)
        
        # Iterate over parameters and create widgets
        for param in engine_config.get('parameters', []):
            widget = self.create_widget_for_parameter(param)
            if widget:
                self.tts_options_layout.addLayout(widget)
        
        self.tts_options_layout.addStretch()
        self.tts_options_widget.setVisible(True)

        
    def create_widget_for_parameter(self, param):
        layout = QHBoxLayout()
        label = QLabel(param['label'] + ": ")
        layout.addWidget(label)
        
        param_type = param['type']
        attribute = param['attribute']
        relies_on = param.get("relies_on", None)
        
        if param_type == 'text':
            widget = QLineEdit()
            widget.textChanged.connect(lambda text, attr=attribute: self.on_parameter_changed(attr, text))
            layout.addWidget(widget)
        elif param_type == 'file':
            widget = QLineEdit()
            widget.textChanged.connect(lambda text, attr=attribute: self.on_parameter_changed(attr, text))
            browse_button = QPushButton("Browse")
            browse_button.clicked.connect(lambda _, w=widget, p=param: self.browse_file(w, p))
            layout.addWidget(widget)
            layout.addWidget(browse_button)
        elif param_type == 'spinbox':
            widget = QSpinBox()
            widget.setMinimum(param.get('min', 0))
            widget.setMaximum(param.get('max', 100))
            widget.setValue(param.get('default', 0))
            widget.valueChanged.connect(lambda value, attr=attribute: self.on_parameter_changed(attr, value))
            layout.addWidget(widget)
        elif param_type == 'checkbox':
            widget = QCheckBox()
            widget.stateChanged.connect(lambda state, attr=attribute: self.on_parameter_changed(attr, bool(state)))
            layout.addWidget(widget)
        elif param_type == 'combobox':
            widget = QComboBox()
            widget.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            widget.setMinimumContentsLength(10)  # Adjust the value as needed
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            function_name = param.get('function')
            get_items_func = lambda: self.get_combobox_items(param)

            if relies_on:
            # Get the widget of the parameter it relies on
                relies_on_widget = getattr(self, f"{relies_on}_widget", None)
                if relies_on_widget:
                    # Define a slot method that updates items
                    def update_items_based_on_dependency(_):
                        items = get_items_func()
                        widget.blockSignals(True)
                        widget.clear()
                        widget.addItems(items)
                        # Needed to update generation settings based on dependent combobox
                        if items:
                            widget.setCurrentIndex(0)
                            value = widget.currentText()
                            self.on_parameter_changed(attribute, value)
                        else:
                            self.on_parameter_changed(attribute, None)
                        widget.blockSignals(False)
                        widget.blockSignals(False)
                    # Connect the slot to the currentTextChanged signal of the relies_on widget
                    relies_on_widget.currentTextChanged.connect(update_items_based_on_dependency)
                    # Initially populate the combobox
                    items = get_items_func()
                    widget.addItems(items)
                else:
                    self.show_message("Error", f"Parameter '{attribute}' relies on unknown parameter '{relies_on}'", QMessageBox.Warning)
            else:
                if function_name == 'get_combobox_items':
                    items = get_items_func()
                    widget.addItems(items)
                else:
                    self.show_message("Error", f"Unknown function {function_name} for combobox parameter", QMessageBox.Warning)
            widget.currentTextChanged.connect(lambda text, attr=attribute: self.on_parameter_changed(attr, text))
            layout.addWidget(widget)
        elif param_type == 'slider':
            # Create the slider
            widget = QSlider(Qt.Horizontal)
            widget.setMinimum(param.get('min', 0))
            widget.setMaximum(param.get('max', 100))
            widget.setValue(param.get('default', 0))
            widget.setTickPosition(QSlider.TicksBelow)
            widget.setTickInterval(1)
            
            # Create the value label
            # max_val = param.get('max', 100)
            # max_val_length = len(str(max_val))
            # estimated_width = max_val_length * 10  # Adjust multiplier as needed
            
            # To update the gui to display decimal
            step = param.get("step", 1)
            value_label = QLabel(str(widget.value()/step))
            # value_label.setFixedWidth(estimated_width)
            
            value_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            
            
            # Define a handler to update the label and emit the parameter changed signal
            def handle_slider_change(value, attr=attribute, lbl=value_label, step=step):
                lbl.setText(str(value/step))
                self.on_parameter_changed(attr, value)
            
            # Connect the slider's valueChanged signal to the handler
            widget.valueChanged.connect(handle_slider_change)
            
            # Add the slider and the value label to the layout
            layout.addWidget(widget, stretch=1)
            layout.addWidget(value_label)
            
            # Store references to the slider and value label for later use
            setattr(self, f"{attribute}_widget", widget)
            setattr(self, f"{attribute}_value_label", value_label)
        else:
            self.show_message("Error", f"Unknown parameter type: {param_type}", QMessageBox.Warning)
            return None
        
        # Optionally store the widget reference for later use
        setattr(self, f"{attribute}_widget", widget)
        return layout
    
    def get_combobox_items(self, param):
        folder_path = param.get('folder_path', '.')
        look_for = param.get('look_for', 'folders')  # 'folders' or 'files'
        file_filter = param.get('file_filter', '*')  # e.g., '*.txt'
        include_none_option = param.get('include_none_option', False)
        none_option_label = param.get('none_option_label', 'Default')  # Label for the None option
        custom_options = param.get('custom_options', None)
        relies_on = param.get('relies_on', None)
        
        if relies_on:
            # Get the value of the relied-on parameter
            relies_on_widget = getattr(self, f"{relies_on}_widget", None)
            if relies_on_widget:
                # Get the current value
                relied_value = relies_on_widget.currentText()
                # Adjust folder_path
                folder_path = os.path.join(folder_path, relied_value)
            else:
                self.show_message("Error", f"Parameter relies on unknown parameter '{relies_on}'", QMessageBox.Warning)

        # Expand any environment variables and user variables
        folder_path = os.path.expandvars(os.path.expanduser(folder_path))

        # Convert to absolute path
        folder_path = os.path.abspath(folder_path)

        items = []

        if include_none_option:
            items.append(none_option_label)

        if not os.path.exists(folder_path):
            self.show_message("Error", f"Folder {folder_path} does not exist.", QMessageBox.Warning)
            return items  # Return items, which may contain the 'Default' option

        if look_for == 'folders':
            try:
                for entry in os.scandir(folder_path):
                    if entry.is_dir():
                        items.append(entry.name)
            except Exception as e:
                self.show_message("Error", f"Error reading directory {folder_path}: {e}", QMessageBox.Warning)
                return items
        elif look_for == 'files':
            patterns = file_filter.split(';')
            try:
                for entry in os.scandir(folder_path):
                    if any(fnmatch.fnmatch(entry.name, pattern) for pattern in patterns):
                        items.append(entry.name)
            except Exception as e:
                self.show_message("Error", f"Error reading directory {folder_path}: {e}", QMessageBox.Warning)
                return items
        elif look_for == 'custom':
            for item in custom_options:
                items.append(item)
        else:
            self.show_message("Error", f"Invalid look_for value: {look_for}", QMessageBox.Warning)
            return items

        return items

    
    def on_parameter_changed(self, attribute, value):
        if value == 'Default':
            value = None
        self.update_current_speaker_setting(attribute, value)
        self.generation_settings_changed.emit()
    
    def browse_file(self, widget, param):
        file_path = self.get_open_file_name("Select File", "", param.get('file_filter', 'All Files (*)'))
        if file_path:
            widget.setText(file_path)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
                item.layout().deleteLater()  
    
    def get_tts_engine_parameters(self):
        engine_name = self.get_tts_engine()
        engine_config = next((engine for engine in self.tts_config.get('tts_engines', []) if engine['name'] == engine_name), None)
        if not engine_config:
            return {}
        
        parameters = {'tts_engine': engine_name}
        for param in engine_config.get('parameters', []):
            attribute = param['attribute']
            widget = getattr(self, f"{attribute}_widget", None)
            if widget:
                if param['type'] == 'text' or param['type'] == 'file':
                    parameters[attribute] = widget.text()
                elif param['type'] == 'spinbox':
                    parameters[attribute] = widget.value()
                elif param['type'] == 'checkbox':
                    parameters[attribute] = widget.isChecked()
                elif param['type'] == 'combobox':
                    parameters[attribute] = widget.currentText()
                elif param['type'] == 'slider':
                    parameters[attribute] = widget.value()
        return parameters

    
    def get_s2s_engine_parameters(self):
        engine_name = self.get_s2s_engine()
        engine_config = next((engine for engine in self.s2s_config.get('s2s_engines', []) if engine['name'] == engine_name), None)
        if not engine_config:
            return {}

        use_s2s = self.use_s2s_checkbox.isChecked()

        parameters = {'use_s2s': use_s2s, 's2s_engine': engine_name}
        for param in engine_config.get('parameters', []):
            attribute = param['attribute']
            widget = getattr(self, f"{attribute}_widget", None)
            if widget:
                if param['type'] in ('text', 'file'):
                    parameters[attribute] = widget.text()
                elif param['type'] == 'spinbox':
                    parameters[attribute] = widget.value()
                elif param['type'] == 'checkbox':
                    parameters[attribute] = widget.isChecked()
                elif param['type'] == 'combobox':
                    parameters[attribute] = widget.currentText()
                elif param['type'] == 'slider':
                    parameters[attribute] = widget.value()
        return parameters


    
    def get_voice_parameters(self):
        tts_engine_name = self.get_tts_engine()
        s2s_engine_name = self.get_s2s_engine()
        voice_parameters = {}

        voice_parameters['tts_engine'] = tts_engine_name
        voice_parameters['s2s_engine'] = s2s_engine_name
        voice_parameters['use_s2s'] = self.use_s2s_checkbox.isChecked()
        voice_parameters['pause_duration'] = self.get_pause_between_sentences()

        # Get s2s engine-specific parameters dynamically
        s2s_engine_parameters = self.get_s2s_engine_parameters()
        voice_parameters.update(s2s_engine_parameters)

        # Get TTS engine-specific parameters dynamically
        tts_engine_parameters = self.get_tts_engine_parameters()
        voice_parameters.update(tts_engine_parameters)

        return voice_parameters

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
        selected_directory = QFileDialog.getExistingDirectory(self, title, directory, options)
        if selected_directory:
            # Get the parent root (you can customize this to point to your desired parent root)
            parent_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # One level up

            # Get the relative path from the parent root to the selected directory
            relative_directory = os.path.relpath(selected_directory, parent_root)

            return relative_directory

        return None

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

    def on_audio_finished(self, state):
        if state == QMediaPlayer.EndOfMedia or state == QMediaPlayer.StoppedState:
            self.current_audio_path = None  # Clear current audio path
            self.release_media_player_resources()
            self.audio_finished_signal.emit()  # Emit the signal
            
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
        # Set the speakers from the settings
        self.speakers = settings.get('speakers', {})
        # Convert speaker IDs to integers if they are strings
        self.speakers = {int(k): v for k, v in self.speakers.items()}

        # Update speaker selection combo box
        self.update_speaker_selection_combo()

        # General settings
        pause_duration = settings.get('pause_duration', 0)
        self.export_pause_slider.setValue(int(pause_duration * 10))

        # Set current speaker to default (e.g., speaker ID 1)
        default_speaker_id = 1
        index = self.speaker_selection_combo.findData(default_speaker_id)
        if index >= 0:
            self.speaker_selection_combo.setCurrentIndex(index)
        else:
            self.speaker_selection_combo.setCurrentIndex(0)  # Default to first speaker

        # Load settings for current speaker
        self.load_speaker_settings(default_speaker_id)