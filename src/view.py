# view.py
import sys

from PySide6.QtWidgets import (
    QSlider, QWidgetAction, QComboBox, QApplication, QMainWindow, QPushButton,
    QVBoxLayout, QLineEdit, QLabel, QWidget, QMessageBox, QCheckBox,
    QHeaderView, QProgressBar, QGridLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QFileDialog, QScrollArea,
    QSizePolicy, QSpinBox, QSplitter, QDialog, QListWidget, QListWidgetItem, QColorDialog, QMenu, QAbstractItemView, QStyledItemDelegate, QPlainTextEdit
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import Signal, Qt, QUrl, QSize
from PySide6.QtGui import QPixmap, QAction, QScreen, QTextOption, QGuiApplication

import os
import json
import fnmatch
import yaml
import re


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
            color = speaker.get('color', Qt.black)
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
                color = QColorDialog.getColor(initial=speaker.get('color', Qt.black))
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
            color = speaker.get('color', Qt.black)
            if isinstance(color, QColor):
                speaker['color'] = color.name()
        return self.speakers

class MultiLineDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QPlainTextEdit(parent)
        # Turn off scrollbars
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Enable word wrap
        editor.setWordWrapMode(QTextOption.WordWrap)
        # Make background fully opaque and set color
        editor.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: rgba(51, 51, 51, 1.0);
                color: #eee;
                border: 1px solid #888;
                font-size: 14pt;
            }
            """
        )
        return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.EditRole)
        if text is None:
            text = ""
        editor.setPlainText(str(text))

    def setModelData(self, editor, model, index):
        new_text = editor.toPlainText()
        model.setData(index, new_text, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        # Fill the entire cell
        editor.setGeometry(option.rect)

class UploadDialog(QDialog):
    upload_requested = Signal(str, list)
    def __init__(self, parent=None, engines_list=None):
        super().__init__(parent)
        self.setWindowTitle("Upload Voice")
        self.setGeometry(100, 100, 600, 400)
        self.engines_list = engines_list
        self.tts_config = self.load_tts_config('configs/tts_config.json')
        self.s2s_config = self.load_s2s_config('configs/s2s_config.json')
        self.all_engines = []
        if 'tts_engines' in self.tts_config:
            self.all_engines.extend(self.tts_config['tts_engines'])
        if 's2s_engines' in self.s2s_config:
            self.all_engines.extend(self.s2s_config['s2s_engines'])
        self._init_ui()
        self._init_engine()
        
    def _init_ui(self):
        self.main_layout = QVBoxLayout()
        self.engine_config_layout = QVBoxLayout()
        
        self.combobox_layout = QHBoxLayout()
        
        self.upload_button = QPushButton("Upload")
        self.upload_button.clicked.connect(self.on_upload_clicked)
                
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(self.engines_list)
        self.engine_combo.currentIndexChanged.connect(self.on_engine_changed)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["AI Models", "Voice Reference File"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        
        self.engine_label = QLabel("Engine:")
        self.mode_label = QLabel("Mode:")
        
        self.combobox_layout.addWidget(self.mode_label)
        self.combobox_layout.addWidget(self.mode_combo)
        self.combobox_layout.addWidget(self.engine_label)
        self.combobox_layout.addWidget(self.engine_combo)
        
        self.main_layout.addLayout(self.combobox_layout)
        self.main_layout.addLayout(self.engine_config_layout)
        self.main_layout.addWidget(self.upload_button)

        self.setLayout(self.main_layout)

    def _init_engine(self):
        first_engine = self.engines_list[0]
        first_mode = self.mode_combo.itemText(0)
        self.build_engine_widgets(first_engine, first_mode)
    def browse_file(self, widget, param):
        file_path = self.get_open_file_name("Select File", "", param.get('file_filter', 'All Files (*)'))
        if file_path:
            widget.setText(file_path)
        
    def build_engine_widgets(self, engine, mode):
        self.clear_layout(self.engine_config_layout)
        for item in self.all_engines:
            if item['name'] == engine:
                parameters = item["upload_params"]
                param_dict = parameters.get(mode, None)
                if param_dict:
                    for param in param_dict:
                        widget = self.create_widget_for_parameter(param)
                        if widget: 
                            self.engine_config_layout.addLayout(widget)
    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
                item.layout().deleteLater() 
    
    def create_widget_for_parameter(self, param):
        layout = QHBoxLayout()
        label = QLabel(param['label'] + ": ")
        layout.addWidget(label)
        
        param_type = param['type']
        attribute = param['attribute']
        relies_on = param.get("relies_on", None)
        
        if param_type == 'text':
            widget = QLineEdit()
            layout.addWidget(widget)
        elif param_type == 'file':
            widget = QLineEdit()
            browse_button = QPushButton("Browse")
            browse_button.clicked.connect(lambda _, w=widget, p=param: self.browse_file(w, p))
            layout.addWidget(widget)
            layout.addWidget(browse_button)
        else:
            self.show_message("Error", f"Unknown parameter type: {param_type}", QMessageBox.Warning)
            return None
        
        # Optionally store the widget reference for later use
        setattr(self, f"{attribute}_widget", widget)
        return layout
    def get_current_widget(self):
        current_engine = self.engine_combo.currentText()
        current_mode = self.mode_combo.currentText()
        
    def get_open_file_name(self, title, directory='', filter=''):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        filepath, _ = QFileDialog.getOpenFileName(self, title, directory, filter, options=options)
        return filepath
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

    
    def on_engine_changed(self):
        self.build_engine_widgets(self.engine_combo.currentText(), self.mode_combo.currentText())
    def on_mode_changed(self):
        self.build_engine_widgets(self.engine_combo.currentText(), self.mode_combo.currentText())
    def on_upload_clicked(self):
        engine = self.engine_combo.currentText()
        mode   = self.mode_combo.currentText()
        engine_cfg = next(e for e in self.all_engines if e['name'] == engine)

        params = engine_cfg['upload_params'].get(mode, [])
        save_items = []
        for param in params:
            attr = param['attribute']
            widget = getattr(self, f"{attr}_widget", None)
            if widget is None:
                continue

            value = widget.text().strip()
            if not value:
                continue
            
            type = param['type']
            if type == 'file':
                save_dict = {"type" : type,
                            "target_path" : param['save_path'],
                            "source_path" : value,
                            "save_format" : param['save_format']}
                save_items.append(save_dict)
            elif type == 'text' and param.get('save_path', None) is not None:
                save_dict = {"type" : type,
                            "target_path" : param['save_path'],
                            "source_text" : value,
                            "save_format" : param['save_format']}
                save_items.append(save_dict)
            elif type == 'text' and param.get('save_path', None) is None:
                save_dict = {"name": value}
                save_items.append(save_dict)
                
        self.upload_requested.emit(mode, save_items)


class WordReplacerView(QMainWindow): 
    # Define signals for user actions
    extra_wrs = Signal(bool)
    test_repl_s = Signal(str, str)
    window_closed = Signal()
    save_list_requested = Signal()
    start_wr_requested = Signal()
     
    rplwords = [["", ""]]
    extra_replacement = False
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widgets = parent
        self.setStyleSheet(self.load_stylesheet())
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.word_path = None
        self.file_path = None
        
        self._init_ui()

    def _init_ui(self):
        # Set the title and initial window size
        self.setWindowTitle("Word Replacer")
        self.setGeometry(100, 100, 600, 400)  # Increased size for better visibility

        # Create the main layout
        layout = QVBoxLayout()
        layout.setSpacing(10) 

        # Open File list to load replacement word List.
        self.load_word_list_action = QAction("Load List", self)
        self.load_word_list_action.triggered.connect(self.load_word_list)
         
        self.list_name_label = QLabel("List Name:")
        self.list_name_input = QLineEdit(self)
        
        self.load_word_name_layout = QHBoxLayout()
        self.load_word_name_layout.addWidget(self.list_name_label)
        self.load_word_name_layout.addWidget(self.list_name_input)

        self.save_list_as_button = QAction("Save as", self)
        self.save_list_as_button.triggered.connect(self.save_list_as)
        
        self.save_list_button = QAction("Save", self)
        self.save_list_button.triggered.connect(self.on_save_list_clicked)

        self.new_list_button = QAction("New List", self)
        self.new_list_button.triggered.connect(self.new_list)

        # Setup the menu bar
        self.menu = self.menuBar()
        
        self.file_menu = self.menu.addMenu("File")
        self.file_menu.addAction(self.new_list_button)
        self.file_menu.addAction(self.load_word_list_action)
        self.file_menu.addAction(self.save_list_button)
        self.file_menu.addAction(self.save_list_as_button)
        
        
        self.test_button = QPushButton("Test Word", self)
        self.test_button.clicked.connect(self.test_repl)

        self.add_word_button = QPushButton("Add Word", self)
        self.add_word_button.clicked.connect(self.add_word_to_list)

        self.sort_list_button = QPushButton("Sort List", self)
        self.sort_list_button.clicked.connect(self.sort_list)
        
        self.speakers_layout = QHBoxLayout()
        self.speakers_label = QLabel("Speakers Available")
        self.speakers_combo = QComboBox(None)
        self.speakers_layout.addWidget(self.speakers_label)
        self.speakers_layout.addWidget(self.speakers_combo)
        self.speakers_layout.addWidget(self.test_button)
        
        self.start_wr_button = QPushButton("Start Word Replacement")
        self.start_wr_button.clicked.connect(self.on_start_wr_clicked)

        self.del_word_button = QPushButton("Delete Word", self)
        self.del_word_button.clicked.connect(self.del_word_in_list)

        self.add_word_name_layout = QHBoxLayout()
        self.add_word_name_layout.addWidget(self.add_word_button)
        self.add_word_name_layout.addWidget(self.sort_list_button)
        self.add_word_name_layout.addWidget(self.del_word_button)

        # Include extra replacements i.e. mr. ->mister, and remove <>\/ etc.
        self.extra_replacement_checkbox = QCheckBox("Do Extras i.e abbreviations, <>, etc.", self)
        self.extra_replacement_checkbox.setStyleSheet("""
            QCheckBox {
                color: white; /* Change text color */
            }
        """)
        self.extra_replacement_checkbox.stateChanged.connect(self.do_extra)

        # Word widget
        self.word_widget = QTableWidget(self)
        self.word_widget.setColumnCount(2)
        self.word_widget.setHorizontalHeaderLabels(['Original Word','New Word'])
        self.word_widget.horizontalHeader().resizeSection(0, int(self.width()/2))
        self.word_widget.horizontalHeader().resizeSection(1, int(self.width()/2))
        self.word_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)        
        self.word_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.word_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) 
        self.word_widget.setStyleSheet("""
            QTableView QLineEdit {
                background-color: #555555;;
            }
        """)
        
        # Add all layouts and widgets to the main layout
        layout.addLayout(self.load_word_name_layout)
        layout.addLayout(self.add_word_name_layout)
        layout.addLayout(self.speakers_layout)
        layout.addWidget(self.extra_replacement_checkbox)
        layout.addWidget(self.word_widget)
        layout.addWidget(self.start_wr_button)
        
        # Create a central widget and set the main layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        
        # Set the central widget of the QMainWindow
        self.setCentralWidget(central_widget)

    def add_word_to_list(self):
        #Add empty line for a new word to be entered
        word_item = QTableWidgetItem('')
        repl_item = QTableWidgetItem('')
        #word_item.setFlags(word_item.flags() & ~Qt.ItemIsEditable)
        row_position = self.word_widget.rowCount()
        self.word_widget.insertRow(row_position)
        self.word_widget.setItem(row_position, 0, word_item)
        self.word_widget.setItem(row_position, 1, repl_item)
        self.word_widget.sortItems(0, order=Qt.AscendingOrder)
        #self.AddWord2ListS.emit()
        
    def close_event(self, event):
        self.window_closed.emit()  # Emit the signal when the window is closed
        super().closeEvent(event)  # Call the superclass method
    
    def del_word_in_list(self):
        #Remove selected word from word list
        selected_row = self.word_widget.currentRow()
        if selected_row == -1:  # No row is selected
            QMessageBox.warning(self, "Error", 'Choose a to Delete')
            return
        self.word_widget.removeRow(selected_row)
        self.word_widget.sortItems(0, order=Qt.AscendingOrder)
        #self.DelWordInListS.emit()
    def do_extra(self):
        if self.extra_replacement_checkbox.isChecked():
            self.extra_replacement = True
        else:
            self.extra_replacement = False
        self.extra_wrs.emit(self.extra_replacement)
    def get_current_list_name(self):
        return self.list_name_input.text()
    def get_extra(self):
        return self.extra_replacement_checkbox.isChecked()
    def get_new_list(self):
        rplwords = []
        self.list_name_input.setText(os.path.basename(self.word_path))
        
        new_wordlist = {}
        num_rows = self.word_widget.rowCount()
        
        for idx in range(num_rows):
            orig_word_item = self.word_widget.item(idx, 0)
            replacement_word_item = self.word_widget.item(idx, 1)
            
            if orig_word_item and replacement_word_item:
                orig_word = orig_word_item.text()
                replacement_word = replacement_word_item.text()
                
                new_wordlist[str(idx)] = {
                    "orig_word": orig_word, 
                    "replacement_word": replacement_word
                }
                
                rplwords.append([orig_word, replacement_word])
            else:
                # Handle the case where an item might be None
                print(f"Missing item at row {idx}")
        self.rplwords = rplwords
        
        return new_wordlist
    
    def load_stylesheet(self, font_size="14pt"):
        # Load the base stylesheet
        with open("base.css", "r") as file:
            stylesheet = file.read()

        # Replace font-size
        modified_stylesheet = stylesheet.replace("font-size: 14pt;", f"font-size: {font_size};")
        return modified_stylesheet    
    def load_word_list(self):
        #Load list of words to be replaced by something else
        options = QFileDialog.Options()
        self.word_path, _ = QFileDialog.getOpenFileName(self, "Select Wordlist File", "", "JSON Files (*.json);;All Files (*)", options=options)
        self.list_name_input.setText(os.path.basename(self.word_path))
        # Clear rplwords, this will contain words for replacement
        rplwords = []
        # Check if wordlist.json exists in the selected directory
        if not os.path.exists(self.word_path):
            QMessageBox.warning(self, "Error", "The selected directory does not contain a wordlist.")
            return
        try:
            # Load text_audio_map.json
            with open(self.word_path, 'r', encoding="utf-8") as file:
                wordlist = json.load(file)

            # Clear existing items from the wordlist table widget
            self.word_widget.setRowCount(0)

            # Insert sentences and update wordlist
            for idx_str, item in wordlist.items():
                orig_word = item['orig_word']
                replacement_word = item['replacement_word']
                # Add item to WordWidget
                word_item = QTableWidgetItem(orig_word)
                repl_item = QTableWidgetItem(replacement_word)
                #word_item.setFlags(word_item.flags() & ~Qt.ItemIsEditable)
                word_item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsEditable)
                repl_item.setFlags(repl_item.flags()|Qt.ItemIsEditable)
                #repl_item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsEditable)
                row_position = self.word_widget.rowCount()
                self.word_widget.insertRow(row_position)
                self.word_widget.setItem(row_position, 0, word_item)
                self.word_widget.setItem(row_position, 1, repl_item)
                #Add the same word to rplwords for use in substitution.
                rplwords.append([word_item.text(), repl_item.text()])
                
            self.word_widget.sortItems(0, order=Qt.AscendingOrder)
           
        except Exception as e:
            # Handle other exceptions (e.g., JSON decoding errors)
            QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")
        
        self.rplwords = rplwords
    
    def new_list(self):
        if self.word_widget.rowCount() >= 1:
            confirm_continue = self.prompt_question("Start New List", 
                                 "A list is already loaded in. Please save it if you want to save your progress or else this will start from scratch.",
                                 default_button=QMessageBox.No
                                 )
            if not confirm_continue:
                return
        #Clear wordlist
        self.list_name_input.setText("NewList.json")
        self.word_widget.clearContents()
        self.word_widget.setRowCount(0)
        self.rplwords = []
        
    def on_save_list_clicked(self):
        self.save_list_requested.emit()
    def on_start_wr_clicked(self):
        self.start_wr_requested.emit()
        
    def prompt_question(self, title, question, buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No):
        reply = QMessageBox.question(self, title, question, buttons, default_button)
        return reply == QMessageBox.Yes

    def save_list_as(self):
        # Save wordlist and update internal list for substitution.
        
        self.word_widget.sortItems(0, order=Qt.AscendingOrder)
        
        options = QFileDialog.Options()
        self.word_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Wordlist File", 
            self.list_name_input.text(), 
            "JSON Files (*.json);;All Files (*)", 
            options=options
        )
        
        if self.word_path:  # Ensure a file path was selected
            new_wordlist = self.get_new_list()
            self.save_json(self.word_path, new_wordlist)
            
        else:
            print("No file selected for saving.")
        
    def save_json(self, audio_map_path, new_text_audio_map):
        with open(audio_map_path, 'w', encoding='utf-8') as file:
            json.dump(new_text_audio_map, file, ensure_ascii=False, indent=4)
    def sort_list(self):
        #Sort word list alphabetically
        self.word_widget.sortItems(0, order=Qt.AscendingOrder)
        #self.SortListS.emit()
 
    def test_repl(self):
        #Test word to hear how it will be pronounced.
        selected_row = self.word_widget.currentRow()
        selected_col = self.word_widget.currentColumn()
        selected_speaker = self.speakers_combo.currentText()
        if selected_row == -1 or selected_col == -1:  # No row is selected
            QMessageBox.warning(self, "Error", 'Choose a row and column to test')
            return
        
        wordstr = self.word_widget.item(selected_row, selected_col).text()
        
        self.test_repl_s.emit(wordstr, selected_speaker)
    
    def update_speaker_selection_combo(self, list_of_speakers):
        self.speakers_combo.blockSignals(True)  # Prevent signal during update
        self.speakers_combo.clear()
        for speaker_id, speaker in list_of_speakers:
            self.speakers_combo.addItem(f"{speaker['name']}", userData=speaker_id)
        self.speakers_combo.blockSignals(False)
        
class AudiobookMakerView(QMainWindow):

    # Define signals for user actions (alphabetical order)
    audio_finished_signal = Signal()
    clear_regen_requested = Signal()
    continue_audiobook_generation_requested = Signal()
    # current_speaker_changed = Signal(int)
    delete_requested = Signal()
    export_audiobook_requested = Signal()
    font_size_changed = Signal(int)
    generation_settings_changed = Signal()
    load_existing_audiobook_requested = Signal()
    load_text_file_requested = Signal()
    # load_tts_requested = Signal()
    pause_audio_requested = Signal()
    play_all_from_selected_requested = Signal()
    play_selected_audio_requested = Signal()
    regen_checkbox_toggled = Signal(int, bool)
    regenerate_audio_for_sentence_requested = Signal()
    regenerate_bulk_requested = Signal()
    search_sentences_requested = Signal(int, bool, str, bool)
    sentence_speaker_changed = Signal(int, int)
    set_background_clear_image_requested = Signal()
    set_background_image_requested = Signal()
    s2s_engine_changed = Signal(str)
    speakers_updated = Signal(object)
    start_generation_requested = Signal()
    stop_generation_requested = Signal()
    text_item_changed = Signal(int, str)
    toggle_delete_action_requested = Signal()
    tts_engine_changed = Signal(object)
    update_audiobook_requested = Signal()
    upload_voice_window_requested = Signal()
    word_replacer_window_requested = Signal(bool)
    word_replacer_window_closed = Signal()

    def __init__(self, global_settings):
        super().__init__()
        self.global_settings = global_settings

        # Create a background label widget and set it up
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.background_label.lower()  # Lower the background so it's behind other widgets

        # Load user settings
        self.loaded_font_size = 14
        
        background_image = self.global_settings.get('background_image')
        if background_image and os.path.exists(background_image):
            self.set_background(background_image)
        if self.global_settings.get('font_size'):
            self.loaded_font_size = self.global_settings['font_size']
        if self.global_settings.get('version'):
            self.version = self.global_settings['version']

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
        self.word_replacer_window = None
        
        self.speakers_updated.connect(self.update_speaker_selection_combo)


        self.tts_config = self.load_tts_config('configs/tts_config.json')
        self.s2s_config = self.load_s2s_config('configs/s2s_config.json')
        self.speakers = {
                1: {'name': 'Narrator', 'color': Qt.black, 'settings': {}}
            }

        # Initialize UI components
        self.filepath = None
        self._init_ui()
        # Apply loaded font size to font slider and stylesheet
        self.font_slider.setValue(self.loaded_font_size)
        self.update_font_size_from_slider(self.loaded_font_size)

        self.update_speaker_selection_combo()
        self.populate_s2s_engines()
        self.set_tts_initial_index()

    def _init_ui(self):
        # QVBoxLayouts
        main_layout = QVBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        right_layout = QVBoxLayout()
        sentence_area = QVBoxLayout()
        self.tts_options_layout = QVBoxLayout()
        self.s2s_options_layout = QVBoxLayout()
        self.options_layout = QVBoxLayout()
        
        # QHboxlayouts
        main_content_layout = QHBoxLayout()
        search_layout = QHBoxLayout()
        self.tts_engine_layout = QHBoxLayout()
        self.book_layout = QHBoxLayout()
        self.s2s_engine_layout = QHBoxLayout()
        self.export_pause_layout = QHBoxLayout()
        self.generation_buttons_layout = QHBoxLayout()
        self.play_pause_layout = QHBoxLayout()
        self.regenerate_bulk_layout = QHBoxLayout()
        self.audiobook_label_layout = QHBoxLayout()
        self.speaker_selection_layout = QHBoxLayout()
        right_inner_layout = QHBoxLayout()
        right_inner_layout.setStretch(0, 2)
        
        # QWidgets
        left_container = QWidget(self)
        left_container.setLayout(left_layout)
        left_container.setMaximumWidth(500)
        self.tts_options_widget = QWidget()        
        self.tts_options_widget.setLayout(self.tts_options_layout)
        self.tts_options_widget.setVisible(False)  # Initially hidden
        self.tts_options_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.s2s_options_widget = QWidget()
        self.s2s_options_widget.setVisible(False)  # Initially hidden
        self.options_widget = QWidget()
        self.options_widget.setLayout(self.options_layout)
        self.options_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.options_widget.setVisible(False)  # Initially hidden
        central_widget = QWidget(self)
        
        # QActions
        self.load_audiobook_action = QAction("Load Existing Audiobook", self)
        self.load_audiobook_action.triggered.connect(self.on_load_existing_audiobook_triggered)
        self.update_audiobook_action = QAction("Update Audiobook Sentences", self)
        self.update_audiobook_action.triggered.connect(self.on_update_audiobook_triggered)
        self.export_audiobook_action = QAction("Export Audiobook", self)
        self.export_audiobook_action.triggered.connect(self.on_export_audiobook_triggered)
        self.set_background_action = QAction("Set Background Image", self)
        self.set_background_action.triggered.connect(self.on_set_background_image_triggered)
        self.set_background_clear_action = QAction("Clear Background Image", self)
        self.set_background_clear_action.triggered.connect(self.on_set_background_clear_image_triggered)
        self.manage_speakers_action = QAction("Manage Speakers", self)
        self.manage_speakers_action.triggered.connect(self.on_manage_speakers)
        self.toggle_delete_action = QAction("Toggle Delete Column", self)
        self.toggle_delete_action.setCheckable(True)
        self.toggle_delete_action.triggered.connect(self.on_toggle_delete_action_triggered)
        self.upload_voices_action = QAction("Upload Models/Voices", self)
        self.upload_voices_action.triggered.connect(self.on_upload_voice_triggered)
        self.word_replacer_action = QAction("Open Word Replacer Window", self)
        self.word_replacer_action.setCheckable(True)
        self.word_replacer_action.setChecked(False)
        self.word_replacer_action.toggled.connect(self.toggle_word_replacer_window)
        
        # QPushButtons
        self.clear_regen_button = QPushButton("Clear Regen Checkboxes", self)
        self.clear_regen_button.clicked.connect(self.on_clear_regen_button_clicked)
        self.continue_audiobook_button = QPushButton("Continue Audiobook Generation", self)
        self.continue_audiobook_button.clicked.connect(self.on_continue_button_clicked)
        self.delete_button = QPushButton("Delete Sentences")
        self.delete_button.setHidden(True)
        self.delete_button.setMaximumWidth(200)
        self.delete_button.clicked.connect(self.on_delete_button_clicked)
        self.go_to_sentence = QPushButton("Go to sentence number:")
        self.go_to_sentence.clicked.connect(self.on_go_to_sentence)
        self.load_text = QPushButton("Select Text File", self)
        self.load_text.clicked.connect(self.on_load_text_clicked)
        self.next_search = QPushButton("Search next")
        self.next_search.clicked.connect(self.on_next_search)
        self.start_generation_button = QPushButton("Start Audiobook Generation", self)
        self.start_generation_button.clicked.connect(self.on_generate_button_clicked)
        self.stop_generation_button = QPushButton("Stop", self)
        self.stop_generation_button.clicked.connect(self.on_stop_button_clicked)
        self.stop_generation_button.setEnabled(False)  # Disabled initially
        self.stop_generation_button.setStyleSheet("QPushButton { color: #A9A9A9; }")
        self.pause_button = QPushButton("Pause", self)
        self.pause_button.clicked.connect(self.on_pause_button_clicked)
        self.play_all_button = QPushButton("Play All from Selected", self)
        self.play_all_button.clicked.connect(self.on_play_all_button_clicked)
        self.play_button = QPushButton("Play Audio", self)
        self.play_button.clicked.connect(self.on_play_button_clicked)
        self.regenerate_button = QPushButton("Regenerate Chosen Sentence", self)
        self.regenerate_button.clicked.connect(self.on_regenerate_button_clicked)
        self.regenerate_bulk_button = QPushButton("Regenerate in Bulk", self)
        self.regenerate_bulk_button.clicked.connect(self.on_regenerate_bulk_button_clicked)
        self.previous_search = QPushButton("Search previous")
        self.previous_search.clicked.connect(self.on_previous_search)
        self.toggle_engines_button = QPushButton("Toggle TTS/S2S")
        self.toggle_engines_button.clicked.connect(self.toggle_engines_column)

        # QCheckBoxes
        self.use_s2s_checkbox = QCheckBox("Use s2s Engine", self)
        self.use_s2s_checkbox.stateChanged.connect(self.on_use_s2s_changed)
        self.search_across_sentences = QCheckBox("Search across sentences limits")
        self.search_across_sentences.setChecked(False)
        
        # QComboBoxes
        self.s2s_engine_combo = QComboBox()
        self.s2s_engine_combo.currentTextChanged.connect(self.on_s2s_engine_changed)
        self.speaker_selection_combo = QComboBox()
        self.speaker_selection_combo.currentIndexChanged.connect(self.on_current_speaker_changed)
        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.currentTextChanged.connect(self.on_tts_engine_changed)

        # QLabels
        self.audiobook_label = QLabel(self)
        self.audiobook_label.setText("No Audio Book Set")
        self.audiobook_label.setAlignment(Qt.AlignCenter)
        self.audiobook_label.setStyleSheet("font-size: 16pt; color: #eee;")
        self.book_name_label = QLabel("Book Name:")
        pause = 0
        max_pause = "5"  # the maximum value the label will show
        estimated_width = len(max_pause) * 50
        self.export_pause_value_label = QLabel(f"{pause / 10}")
        self.export_pause_value_label.setFixedWidth(estimated_width)
        self.export_pause_label = QLabel("Pause Between Sentences (sec): ")
        self.s2s_engine_label = QLabel("S2S Engine: ")
        self.speaker_selection_label = QLabel("Current Speaker: ")
        self.tts_engine_label = QLabel("TTS Engine: ")

        # QLineEdits
        self.book_name_input = QLineEdit(self)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for")

        # QProgressBar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        
        # QScrollAreas
        self.s2s_options_scroll_area = QScrollArea()
        self.s2s_options_scroll_area.setWidgetResizable(True)
        self.s2s_options_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tts_options_scroll_area = QScrollArea()
        self.tts_options_scroll_area.setWidgetResizable(True)
        self.tts_options_scroll_area.setWidget(self.tts_options_widget)
        self.tts_options_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # QSliders
        self.export_pause_slider = QSlider(Qt.Horizontal)
        self.export_pause_slider.setMinimum(0)
        self.export_pause_slider.setMaximum(50)
        self.export_pause_slider.setValue(pause)
        self.export_pause_slider.setTickPosition(QSlider.TicksBelow)
        self.export_pause_slider.setTickInterval(1)
        self.export_pause_slider.valueChanged.connect(self.on_export_pause_slider_changed)
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setMinimum(8)
        self.font_slider.setMaximum(20)
        self.font_slider.setValue(14)
        self.font_slider.setTickPosition(QSlider.TicksBelow)
        self.font_slider.setTickInterval(1)
        self.font_slider.valueChanged.connect(self.on_font_slider_changed)
        
        # QSpinBoxes
        self.go_to_sentence_input = QSpinBox()
        self.go_to_sentence_input.setMinimum(1)
        self.go_to_sentence_input.setMaximum(2**31 - 1) # necessary so that the field has a decent size

        # QTableWidget
        self.tableWidget = QTableWidget(self)
        self.tableWidget.itemChanged.connect(self.handle_sentence_changed)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(['Sentence', 'Speaker', 'Regen?', 'Delete'])
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.setColumnHidden(3, True)
        self.tableWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow table to expand
        self.tableWidget.setWordWrap(True)
        self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableWidget.setColumnWidth(1, 150)  # Speaker
        self.tableWidget.setColumnWidth(2, 100)  # Regen
        self.tableWidget.setColumnWidth(3, 100)  # Delete
        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)

        # QWidgetActions
        slider_action = QWidgetAction(self)
        slider_action.setDefaultWidget(self.font_slider)
        
        # Menu Bar
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")
        self.font_menu = self.menu.addMenu("Font Size")
        self.background_menu = self.menu.addMenu("Background")
        self.speaker_menu = self.menu.addMenu("Speakers")
        self.speaker_menu.setEnabled(False) 
        self.tools_menu = self.menu.addMenu("Tools")
        
        self.file_menu.addAction(self.upload_voices_action)
        self.file_menu.addAction(self.load_audiobook_action)
        self.file_menu.addAction(self.update_audiobook_action)
        self.file_menu.addAction(self.export_audiobook_action)

        self.font_menu.addAction(slider_action)

        self.background_menu.addAction(self.set_background_action)
        self.background_menu.addAction(self.set_background_clear_action)
        
        self.speaker_menu.addAction(self.manage_speakers_action)

        self.tools_menu.addAction(self.toggle_delete_action)
        self.tools_menu.addAction(self.word_replacer_action)

        ### Object/widget dependent "sets"
        delegate = MultiLineDelegate(self.tableWidget)
        self.tableWidget.setItemDelegateForColumn(0, delegate)

        self.s2s_options_widget.setLayout(self.s2s_options_layout)        
        self.s2s_options_scroll_area.setWidget(self.s2s_options_widget)

        # Layout organization
        self.book_layout.addWidget(self.book_name_label)
        self.book_layout.addWidget(self.book_name_input)

        self.export_pause_layout.addWidget(self.export_pause_label)
        self.export_pause_layout.addWidget(self.export_pause_slider)
        self.export_pause_layout.addWidget(self.export_pause_value_label)

        self.generation_buttons_layout.addWidget(self.start_generation_button)
        self.generation_buttons_layout.addWidget(self.stop_generation_button)

        self.play_pause_layout.addWidget(self.play_button)
        self.play_pause_layout.addWidget(self.pause_button)
    
        self.regenerate_bulk_layout.addWidget(self.regenerate_bulk_button)
        self.regenerate_bulk_layout.addWidget(self.clear_regen_button)
        
        self.audiobook_label_layout.addWidget(self.audiobook_label)
        self.audiobook_label_layout.addWidget(self.delete_button)

        self.s2s_engine_layout.addWidget(self.s2s_engine_label)
        self.s2s_engine_layout.addWidget(self.s2s_engine_combo, 1)
        self.tts_engine_layout.addWidget(self.tts_engine_label)
        self.tts_engine_layout.addWidget(self.tts_engine_combo, 1)

        sentence_area.addWidget(self.tableWidget)

        right_layout.addLayout(self.audiobook_label_layout)
        
        self.options_layout.addLayout(self.s2s_engine_layout)
        self.options_layout.addWidget(self.use_s2s_checkbox)
        self.options_layout.addWidget(self.s2s_options_scroll_area, stretch=1)
        self.options_layout.addLayout(self.tts_engine_layout)
        self.options_layout.addWidget(self.tts_options_scroll_area, stretch=1)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.previous_search)
        search_layout.addWidget(self.next_search)
        search_layout.addWidget(self.search_across_sentences)
        search_layout.addWidget(self.go_to_sentence)
        search_layout.addWidget(self.go_to_sentence_input)
        search_layout.addWidget(self.toggle_engines_button)
        
        self.speaker_selection_layout.addWidget(self.speaker_selection_label)
        self.speaker_selection_layout.addWidget(self.speaker_selection_combo, 1)

        right_inner_layout.addLayout(sentence_area)
        right_inner_layout.addWidget(self.options_widget)

        # Main GUI organization
        main_content_layout.addWidget(left_container)
        left_layout.addLayout(self.book_layout)
        left_layout.addWidget(self.load_text)
        left_layout.addLayout(self.generation_buttons_layout)
        left_layout.addLayout(self.play_pause_layout)
        left_layout.addWidget(self.play_all_button)
        left_layout.addWidget(self.regenerate_button)
        left_layout.addLayout(self.regenerate_bulk_layout)
        left_layout.addWidget(self.continue_audiobook_button)
        left_layout.addWidget(self.progress_bar)
        left_layout.addLayout(self.export_pause_layout)
        left_layout.addStretch(1)  # Add stretchable empty space
        right_layout.addLayout(right_inner_layout)
        main_content_layout.addLayout(right_layout)
        main_layout.addLayout(main_content_layout)
        main_layout.addLayout(search_layout)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        left_layout.addLayout(self.speaker_selection_layout)

        # Window settings
        self.setWindowTitle(f"Audiobook Maker v{self.version}")
        width, height = self.get_window_size()
        self.setGeometry(100, 100, int(width), int(height))
        
    def add_table_item(self, row, text, speaker_name, regen_state=False, delete_state=False):
        self.tableWidget.blockSignals(True)
        # Ensure the table has enough rows
        current_row_count = self.tableWidget.rowCount()
        if current_row_count <= row:
            self.tableWidget.setRowCount(row + 1)
            
        # 1) Sentence column
        sentence_item = QTableWidgetItem(text)
        sentence_item.setText(text)
        
        # 2) Speaker column
        speaker_item = QTableWidgetItem(speaker_name)
        speaker_item.setFlags(speaker_item.flags() & ~Qt.ItemIsEditable)
        speaker_item.setTextAlignment(Qt.AlignCenter)
        
        # 3) Regen? column (checkbox)
        regen_check_box = QCheckBox()
        regen_check_box.setChecked(regen_state)
        regen_check_box_widget = QWidget()
        regen_check_box_layout = QHBoxLayout(regen_check_box_widget)
        regen_check_box_layout.setContentsMargins(0, 0, 0, 0)
        regen_check_box_layout.setAlignment(Qt.AlignCenter)
        regen_check_box_layout.addWidget(regen_check_box)
        
        regen_check_box.stateChanged.connect(
            lambda state, row=row: self.regen_checkbox_toggled.emit(row, bool(state))
        )
        
        # 4) Delete column (checkbox)
        delete_check_box = QCheckBox()
        delete_check_box.setChecked(delete_state)
        delete_check_box_widget = QWidget()
        delete_check_box_layout = QHBoxLayout(delete_check_box_widget)
        delete_check_box_layout.setContentsMargins(0, 0, 0, 0)
        delete_check_box_layout.setAlignment(Qt.AlignCenter)
        delete_check_box_layout.addWidget(delete_check_box)
        
        self.tableWidget.setItem(row, 0, sentence_item)
        self.tableWidget.setItem(row, 1, speaker_item)
        self.tableWidget.setCellWidget(row, 2, regen_check_box_widget)
        self.tableWidget.setCellWidget(row, 3, delete_check_box_widget)
        
        # self.tableWidget.resizeRowToContents(row)
        self.tableWidget.blockSignals(False)

    def ask_question(self, title, question, buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No):
        reply = QMessageBox.question(self, title, question, buttons, default_button)
        return reply == QMessageBox.Yes
    def assign_speaker_to_selected(self, speaker_id, speaker_name):
        selected_rows = self.tableWidget.selectionModel().selectedRows()
        for index in selected_rows:
            row = index.row()
            self.set_row_speaker(row, speaker_id, speaker_name)
            self.sentence_speaker_changed.emit(row, speaker_id)
    
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
    def clear_table(self):
        self.tableWidget.setRowCount(0)
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
    
    def disable_buttons(self):
        buttons = [self.regenerate_button,
                   self.regenerate_bulk_button,
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
    def disable_speaker_menu(self):
        self.speaker_menu.setEnabled(False)
    
    def enable_buttons(self):
        buttons = [self.regenerate_button,
                   self.regenerate_bulk_button,
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
    def enable_speaker_menu(self):
        self.speaker_menu.setEnabled(True)
    
    def get_available_speakers(self):
        return self.speakers.items()
    def get_book_name(self):
        return self.book_name_input.text().strip()
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
            patterns = []
            if file_filter:
                # Parse Qt-style file dialog filters like "Model Files (*.pth, *.ckpt);;All Files (*)"
                filter_parts = file_filter.split(';;')
                for part in filter_parts:
                    # Extract patterns from within parentheses
                    pattern_match = re.search(r'\((.*?)\)', part)
                    if pattern_match:
                        inner_patterns = pattern_match.group(1).split()
                        for pattern in inner_patterns:
                            # Remove commas and clean up the pattern
                            clean_pattern = pattern.strip().rstrip(',')
                            if clean_pattern and clean_pattern != '*':  # Skip generic '*' pattern
                                patterns.append(clean_pattern)
            if not patterns:
                patterns = ['*']
                
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
    def get_current_speaker_attributes(self):
        index = self.speaker_selection_combo.currentIndex()
        speaker_id = self.speaker_selection_combo.itemData(index)
        speaker_name = self.speaker_selection_combo.itemText(index)
        if speaker_id is not None:
            return speaker_id, speaker_name
        else:
            return 1  # Default speaker
    def get_deletion_checkboxes(self):
        checked_rows = []
        delete_column = 3  # table col

        for row in range(self.tableWidget.rowCount()):
            cell_widget = self.tableWidget.cellWidget(row, delete_column)
            if cell_widget:
                layout = cell_widget.layout()
                if layout:
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item:
                            checkbox = item.widget()
                            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                                checked_rows.append(row)
                                checkbox.blockSignals(True)
                                checkbox.setChecked(False)
                                checkbox.blockSignals(False)
                                break
        return checked_rows
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
    def get_open_file_name(self, title, directory='', filter=''):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        filepath, _ = QFileDialog.getOpenFileName(self, title, directory, filter, options=options)
        return filepath
    def get_pause_between_sentences(self):
        return self.export_pause_slider.value() / 10.0
    def get_search_start(self):
        selected_rows = self.tableWidget.selectionModel().selectedRows()
        if selected_rows:
            return selected_rows[0].row()
        return 0
    def get_s2s_engine(self):
        return self.s2s_engine_combo.currentText()
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
    def get_tts_engine(self):
        return self.tts_engine_combo.currentText()
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
    def get_selected_table_row(self):
        return self.tableWidget.currentRow()
    def get_window_size(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()  # Get the available screen geometry
        target_ratio = 16 / 9
        width = screen.width() * 0.8  # Adjusted to fit within the screen
        height = width / target_ratio  # calculate height based on the target aspect ratio
        if height > screen.height() * 0.8:
            height = screen.height() * 0.8
            width = height * target_ratio  # calculate width based on the target aspect ratio
        return width, height
    def handle_sentence_changed(self, item):
        if item.column() == 0:
            row = item.row()
            new_text = item.text()
            self.tableWidget.blockSignals(True)
            try:
                # Perform any updates to the item if necessary
                pass
            finally:
                self.tableWidget.blockSignals(False)
            self.text_item_changed.emit(row, new_text)

    def initialize_media_player(self):
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.mediaStatusChanged.connect(self.on_audio_finished)
    def is_audio_playing(self, audio_path):
        return self.current_audio_path == audio_path
    
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
    
    def pause_audio(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        elif self.media_player.playbackState() == QMediaPlayer.PausedState:
            self.media_player.play()
    def play_audio(self, audio_path):
        if not audio_path:
            return
        self.initialize_media_player()
        self.media_player.setSource(QUrl.fromLocalFile(audio_path))
        self.media_player.play()
        self.current_audio_path = audio_path  # Update current audio path
    def on_audio_finished(self, state):
        if state == QMediaPlayer.EndOfMedia or state == QMediaPlayer.StoppedState:
            self.current_audio_path = None  # Clear current audio path
            self.release_media_player_resources()
            self.audio_finished_signal.emit()  # Emit the signal
    def on_clear_regen_button_clicked(self):
        self.clear_regen_requested.emit()
    def on_continue_button_clicked(self):
        self.continue_audiobook_generation_requested.emit()
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
    def on_delete_button_clicked(self):
        self.delete_requested.emit()
    def on_disable_stop_button(self):
        self.stop_generation_button.setEnabled(False)
        self.stop_generation_button.setStyleSheet("QPushButton { color: #A9A9A9; }")
    def on_enable_stop_button(self):
        self.stop_generation_button.setEnabled(True)
        self.stop_generation_button.setStyleSheet("")
    def on_export_audiobook_triggered(self):
        self.export_audiobook_requested.emit()
    def on_export_pause_slider_changed(self, value):
        pause_duration = value / 10.0
        self.updatePauseLabel(pause_duration)
        self.update_current_speaker_setting('pause_duration', pause_duration)
        # self.pause_between_sentences_changed.emit(pause_duration)
    def on_font_slider_changed(self, value):
        self.font_size_changed.emit(value)
    def on_generate_button_clicked(self):
        self.start_generation_requested.emit()
    def on_go_to_sentence(self):
        self.select_table_row(min(self.tableWidget.rowCount(), self.go_to_sentence_input.value()) - 1)
    def on_load_existing_audiobook_triggered(self):
        self.load_existing_audiobook_requested.emit()
    def on_load_text_clicked(self):
        self.load_text_file_requested.emit()
    def on_manage_speakers(self):
        # Open the speaker management dialog
        dialog = SpeakerManagementDialog(self, self.speakers)
        dialog.exec()
        # Update speakers after the dialog is closed
        self.speakers = dialog.get_speakers()
        # print("Before emitting, speakers:", self.speakers)
        self.speakers_updated.emit(self.speakers)
    def on_next_search(self):
        self.search_sentences_requested.emit(self.get_search_start(), True, self.search_input.text(), self.search_across_sentences.isChecked())
    def on_parameter_changed(self, attribute, value):
        if value == 'Default':
            value = None
        self.update_current_speaker_setting(attribute, value)
        self.generation_settings_changed.emit()
    def on_pause_button_clicked(self):
        self.pause_audio_requested.emit()
    def on_play_all_button_clicked(self):
        self.play_all_from_selected_requested.emit()
    def on_play_button_clicked(self):
        self.play_selected_audio_requested.emit()
    def on_previous_search(self):
        self.search_sentences_requested.emit(self.get_search_start(), False, self.search_input.text(), self.search_across_sentences.isChecked())
    def on_regenerate_bulk_button_clicked(self):
        self.regenerate_bulk_requested.emit()
    def on_regenerate_button_clicked(self):
        self.regenerate_audio_for_sentence_requested.emit()
    def on_set_background_clear_image_triggered(self):
        self.set_background_clear_image_requested.emit()
    def on_set_background_image_triggered(self):
        self.set_background_image_requested.emit()
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
    def on_toggle_delete_action_triggered(self):
        self.toggle_delete_action_requested.emit()
    def on_tts_engine_changed(self, engine_name):
        # self.set_load_tts_button_color("")  # Reset color when TTS engine changes
        self.update_tts_options(engine_name)  # Update the TTS options in the view
        self.update_current_speaker_setting('tts_engine', engine_name)
        self.tts_engine_changed.emit(self.speakers)
        # self.speakers_updated.emit(self.speakers)
    def on_update_audiobook_triggered(self):
        self.update_audiobook_requested.emit()
    def on_upload_voice_triggered(self):
        self.upload_voice_window_requested.emit()

    def on_use_s2s_changed(self, state):
        is_checked = self.use_s2s_checkbox.isChecked()
        self.update_current_speaker_setting('use_s2s', is_checked)
        self.generation_settings_changed.emit()
    def on_word_replacer_closed(self):
        self.word_replacer_window_closed.emit()
    def open_upload_voice_window(self, engines_list):
        self.upload_voice_window = UploadDialog(self, engines_list)
        self.upload_voice_window.show()
        self.upload_voice_window.raise_()
        self.upload_voice_window.activateWindow()
    def open_word_replacer_window(self, parent=None):
        self.word_replacer_window = WordReplacerView(parent=parent)
        self.word_replacer_window.setWindowFlag(Qt.Window, True)
        self.word_replacer_window.window_closed.connect(self.on_word_replacer_closed)
        
    def populate_s2s_engines(self):
        s2s_config = self.load_s2s_config('configs/s2s_config.json')
        engines = [engine['name'] for engine in s2s_config.get('s2s_engines', [])]
        self.s2s_engine_combo.addItems(engines)
        self.s2s_config = s2s_config  # Store for later use
    def populate_tts_engines(self):
        engines = [engine['name'] for engine in self.tts_config.get('tts_engines')]
        self.tts_engine_combo.addItems(engines)
    
    def release_media_player_resources(self):
        # Reinitialize the media player to release any file handles
        # This way is NECESSARY to prevent the gui from freezing (for some unknown reason)
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.mediaStatusChanged.connect(self.on_audio_finished)
    def reset(self):
        self.clear_table()
        self.set_audiobook_label("No Audio Book Set")
        self.speakers = {
            1: {'name': 'Narrator', 'color': Qt.black, 'settings': {}}
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
    def resizeEvent(self, event):
        # Update background label geometry when window is resized
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.update_background()  # Update the background pixmap scaling
        super().resizeEvent(event)  # Call the superclass resize event method
    def resize_table(self):
        self.tableWidget.resizeRowsToContents()
    
    def select_table_row(self, row):
        self.tableWidget.selectRow(row)
    def set_audiobook_label(self, text):
        self.audiobook_label.setText(text)
    def set_background(self, file_path):
        # Set the pixmap for the background label
        pixmap = QPixmap(file_path)
        self.background_pixmap = pixmap  # Save the pixmap as an attribute
        self.update_background()
    def set_progress(self, value):
        self.progress_bar.setValue(value)
    def set_row_speaker(self, row, speaker_id, speaker_name):
        self.set_row_speaker_color(row, speaker_id)
        speaker_item = QTableWidgetItem(speaker_name)
        speaker_item.setFlags(speaker_item.flags() & ~Qt.ItemIsEditable)
        self.tableWidget.setItem(row, 1, speaker_item)
    def set_row_speaker_color(self, row, speaker_id):
        self.tableWidget.blockSignals(True)
        speaker = self.speakers.get(str(speaker_id), None)
        if not speaker: # HOT FIX, should figure out why speaker_id needs to be a string for one check, and then int for another for color
            speaker = self.speakers.get(speaker_id, None)
        color = speaker.get('color', Qt.black)
        if isinstance(color, str):
            color = QColor(color)
        item = self.tableWidget.item(row, 0) # Explicit sentence column
        if item:
            item.setBackground(color)
        self.tableWidget.blockSignals(False)
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
    def set_start_generation_button_text(self, text):
        self.start_generation_button.setText(text)
    def set_tts_initial_index(self):
        if self.tts_engine_combo.count() > 0:
            self.tts_engine_combo.setCurrentIndex(0)
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
    def set_tts_engines(self, engines):
        self.tts_engine_combo.clear()
        self.tts_engine_combo.addItems(engines)
    def show_message(self, title, message, icon=QMessageBox.Information):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.exec()
    def skip_current_audio(self):
        if self.playing_sequence:
            self.media_player.stop()
            self.release_media_player_resources()
            self.media_player.setSource(QUrl())
            self.current_audio_path = None
            self.on_audio_finished(QMediaPlayer.EndOfMedia)
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

    def toggle_delete_column(self):
        is_hidden = self.tableWidget.isColumnHidden(3)
        is_button_hidden = self.delete_button.isHidden()
        self.tableWidget.setColumnHidden(3, not is_hidden)
        self.delete_button.setHidden(not is_button_hidden)
    def toggle_engines_column(self):
        is_visible = self.options_widget.isVisible()
        self.options_widget.setVisible(not is_visible)
        if is_visible:
            self.toggle_engines_button.setText("Show TTS/S2S")
        else:
            self.toggle_engines_button.setText("Hide TTS/S2S")
    def toggle_word_replacer_window(self, checked):
        self.word_replacer_window_requested.emit(checked)
    
    def update_background(self):
        # Check if background pixmap is set, then scale and set it
        if hasattr(self, 'background_pixmap'):
            scaled_pixmap = self.background_pixmap.scaled(self.background_label.size(), Qt.KeepAspectRatioByExpanding)
            self.background_label.setPixmap(scaled_pixmap)
            self.background_label.show()
    def update_current_speaker_setting(self, attribute, value):
        current_speaker_id, _ = self.get_current_speaker_attributes()
        if current_speaker_id in self.speakers:
            speaker = self.speakers[current_speaker_id]
            speaker_settings = speaker.setdefault('settings', {})
            speaker_settings[attribute] = value
        else:
            pass
    def update_font_size_from_slider(self, value):
        font_size = f"{value}pt"
        self.setStyleSheet(self.load_stylesheet(font_size))
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
    def update_speaker_selection_combo(self):
        self.speaker_selection_combo.blockSignals(True)  # Prevent signal during update
        self.speaker_selection_combo.clear()
        for speaker_id, speaker in self.speakers.items():
            self.speaker_selection_combo.addItem(f"{speaker['name']}", userData=speaker_id)
        self.speaker_selection_combo.blockSignals(False)
    def updatePauseLabel(self, value):
        self.export_pause_value_label.setText(str(value))
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
