#WordReplacer.py

import sys
from random import randint

from PySide6.QtWidgets import (
    QSlider, QWidgetAction, QComboBox, QApplication, QMainWindow, QPushButton,
    QVBoxLayout, QLineEdit, QLabel, QWidget, QMessageBox, QCheckBox,
    QHeaderView, QProgressBar, QHBoxLayout, QTableWidget, QTableWidgetItem, QFileDialog, QScrollArea, QInputDialog, QSizePolicy, QSpinBox, QSplitter, QDialog, QListWidget, QListWidgetItem, QColorDialog, QMenu
)

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QPixmap, QAction, QScreen, QColor

import os
import json
import fnmatch
import re

from model import AudiobookModel
from view import AudiobookMakerView

#class WordReplacerView(QMainWindow):
class WordReplacerView(QWidget):

    rplwords = [["", ""]]
    extraReplacement = False

    '''
    # Define signals for user actions
    WordListS = Signal(list)
    AddWord2ListS = Signal()
    SortListS = Signal()
    DelWordInListS = Signal()
    ExtraWRS = Signal(bool)
    '''
    TestReplS = Signal(str)

    
    def __init__(self):
        super().__init__()
        self.setStyleSheet(self.load_stylesheet())
        self.model = AudiobookModel()
        self.view = AudiobookMakerView()
        self.init_ui()

    def init_ui(self):

        # Window Layout
        self.filepath = None

        main_layout = QVBoxLayout()
        
        # set the title and inital window size
        self.setWindowTitle("Word Replacer")
        self.setGeometry(100, 100, 400, 400)     

        
        #Layout
        layout = QVBoxLayout()
        layout.setSpacing(10) 
        container = QWidget(self)
        container.setLayout(layout)
        container.setMinimumWidth(600)
        container.setMaximumWidth(800)
        main_layout.addWidget(container)

        #Open File list to load replacement word List.
        self.LoadWordListButton = QPushButton("Load List", self)
        self.LoadWordListButton.clicked.connect(self.LoadWordList)
         
        # List Name Widget
        self.ListNamelabel = QLabel("List Name:")
        self.ListNameInput = QLineEdit(self)
        
        # To arrange the Load List and List Name line side by side:
        self.LoadWordNameLayout = QHBoxLayout()
        self.LoadWordNameLayout.addWidget(self.LoadWordListButton)
        self.LoadWordNameLayout.addWidget(self.ListNamelabel)
        self.LoadWordNameLayout.addWidget(self.ListNameInput)
        layout.addLayout(self.LoadWordNameLayout)

        # -- Save List Button
        self.SaveListButton = QPushButton("Update + Save", self)
        self.SaveListButton.clicked.connect(self.SaveList)
        
        # -- New List Button
        self.NewListButton = QPushButton("New List", self)
        self.NewListButton.clicked.connect(self.NewList)
        
        # Test Word Sound
        self.TestButton = QPushButton("Test Word", self)
        self.TestButton.clicked.connect(self.TestRepl)

        # To arrange the Save, New List, and Test Word line side by side:
        self.SaveEtcLayout = QHBoxLayout()
        self.SaveEtcLayout.addWidget(self.NewListButton)
        self.SaveEtcLayout.addWidget(self.SaveListButton)
        self.SaveEtcLayout.addWidget(self.TestButton)
        layout.addLayout(self.SaveEtcLayout)

        # -- Add Word Button
        self.AddWordButton = QPushButton("Add Word", self)
        self.AddWordButton.clicked.connect(self.AddWord2List)
        
        # -- Sort Word Button
        self.SortListButton = QPushButton("Sort List", self)
        self.SortListButton.clicked.connect(self.SortList)

        # -- Delete Word Button
        self.DelWordButton = QPushButton("Delete Word", self)
        self.DelWordButton.clicked.connect(self.DelWordInList)

        # To arrange the Add, Sort, and Delete Word side by side:
        self.AddWordNameLayout = QHBoxLayout()
        self.AddWordNameLayout.addWidget(self.AddWordButton)
        self.AddWordNameLayout.addWidget(self.SortListButton)
        self.AddWordNameLayout.addWidget(self.DelWordButton)
        layout.addLayout(self.AddWordNameLayout)
        
        # Include extra replacements i.e. mr. ->mister, and remove <>\/ etc.
        self.extraReplacement_checkbox = QCheckBox("Do Extras i.e abbreviations, <>, etc.", self)
        self.extraReplacement_checkbox.setStyleSheet("""
            QCheckBox {
                color: white; /* Change text color */
            }
        """)
        self.extraReplacement_checkbox.stateChanged.connect(self.DoExtra)
        layout.addWidget(self.extraReplacement_checkbox)
        
        
        # Word widget
        self.WordWidget = QTableWidget(self)
        self.WordWidget.setColumnCount(2)
        self.WordWidget.setHorizontalHeaderLabels(['Original Word','New Word'])
        self.WordWidget.horizontalHeader().resizeSection(0, int(self.width()/2))
        self.WordWidget.horizontalHeader().resizeSection(1, int(self.width()/2))
        self.WordWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)        
        self.WordWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.WordWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) 
        self.WordWidget.setStyleSheet("""
            QTableView QLineEdit {
                background-color: #555555;;
            }
        """)
        layout.addWidget(self.WordWidget)
        
        self.setLayout(layout)
        #self.show()
        self.hide()

    def DoExtra(self):
        if self.extraReplacement_checkbox.isChecked():
            self.extraReplacement = True
        else:
            self.extraReplacement = False
        #self.ExtraWRS.emit(self.extraReplacement)
    
    def load_stylesheet(self, font_size="14pt"):
        # Load the base stylesheet
        with open("base.css", "r") as file:
            stylesheet = file.read()

        # Replace font-size
        modified_stylesheet = stylesheet.replace("font-size: 14pt;", f"font-size: {font_size};")
        return modified_stylesheet
        
    def LoadWordList(self):
        #Load list of words to be replaced by something else
        options = QFileDialog.Options()
        Wordpath, _ = QFileDialog.getOpenFileName(self, "Select Wordlist File", "", "JSON Files (*.json);;All Files (*)", options=options)
        self.ListNameInput.setText(os.path.basename(Wordpath))
        self.wordpath = Wordpath
        # Clear rplwords, this will contain words for replacement
        rplwords = []
        # Check if wordlist.json exists in the selected directory
        if not os.path.exists(Wordpath):
            QMessageBox.warning(self, "Error", "The selected directory does not contain a wordlist.")
            return

        try:
            # Load text_audio_map.json
            with open(Wordpath, 'r', encoding="utf-8") as file:
                wordlist = json.load(file)

            # Clear existing items from the wordlist table widget
            self.WordWidget.setRowCount(0)

            # Insert sentences and update wordlist
            for idx_str, item in wordlist.items():
                OrigWord = item['OrigWord']
                ReplacementWord = item['ReplacementWord']
                # Add item to WordWidget
                word_item = QTableWidgetItem(OrigWord)
                repl_item = QTableWidgetItem(ReplacementWord)
                #word_item.setFlags(word_item.flags() & ~Qt.ItemIsEditable)
                word_item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsEditable)
                repl_item.setFlags(repl_item.flags()|Qt.ItemIsEditable)
                #repl_item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsEditable)
                row_position = self.WordWidget.rowCount()
                self.WordWidget.insertRow(row_position)
                self.WordWidget.setItem(row_position, 0, word_item)
                self.WordWidget.setItem(row_position, 1, repl_item)
                #Add the same word to rplwords for use in substitution.
                rplwords.append([word_item.text(), repl_item.text()])
                
            self.WordWidget.sortItems(0, order=Qt.AscendingOrder)
           
        except Exception as e:
            # Handle other exceptions (e.g., JSON decoding errors)
            QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")
        
        self.rplwords = rplwords
        #self.WordListS.emit(rplwords)
        
    def NewList(self):
        #Clear wordlist
        self.ListNameInput.setText("NewList.json")
        self.WordWidget.clearContents()
        self.WordWidget.setRowCount(0)
        self.rplwords = []
        #self.WordListS.emit(rplwords)

    def save_json(self, audio_map_path, new_text_audio_map):
        with open(audio_map_path, 'w', encoding='utf-8') as file:
            json.dump(new_text_audio_map, file, ensure_ascii=False, indent=4)
        
    def SaveList(self):
        #Save wordlist and update internal list for substitution.
        rplwords = []
        self.WordWidget.sortItems(0, order=Qt.AscendingOrder)
        
        options = QFileDialog.Options()
        wordPath, _ = QFileDialog.getSaveFileName(self, "Save Wordlist File", self.ListNameInput.text(), "JSON Files (*.json);;All Files (*)", options=options)
        self.ListNameInput.setText(os.path.basename(wordPath))
        self.wordPath = wordPath
        
        #wordPath = os.path.join(os.getcwd(),self.ListNameInput.text())
        newwordlist = {}
        numRows = self.WordWidget.rowCount()
        idx=0
        
        while (idx<numRows):
            newwordlist[str(idx)] = {"OrigWord": self.WordWidget.item(idx, 0).text(), "ReplacementWord": self.WordWidget.item(idx, 1).text()}
            self.save_json(wordPath, newwordlist)
            rplwords.append([self.WordWidget.item(idx, 0).text(), self.WordWidget.item(idx, 1).text()])
            idx=idx+1
        #self.WordListS.emit(rplwords)
        
    def TestRepl(self):
        #Test word to hear how it will be pronounced.
        selected_row = self.WordWidget.currentRow()
        selected_col = self.WordWidget.currentColumn()
        if selected_row == -1|selected_col == -1:  # No row is selected
            QMessageBox.warning(self, "Error", 'Choose a row and column to test')
            return
        
        wordstr = self.WordWidget.item(selected_row, selected_col).text()
        self.TestReplS.emit(wordstr)
        
    def AddWord2List(self):
        #Add empty line for a new word to be entered
        word_item = QTableWidgetItem('')
        repl_item = QTableWidgetItem('')
        #word_item.setFlags(word_item.flags() & ~Qt.ItemIsEditable)
        row_position = self.WordWidget.rowCount()
        self.WordWidget.insertRow(row_position)
        self.WordWidget.setItem(row_position, 0, word_item)
        self.WordWidget.setItem(row_position, 1, repl_item)
        self.WordWidget.sortItems(0, order=Qt.AscendingOrder)
        #self.AddWord2ListS.emit()
        
    def SortList(self):
        #Sort word list alphabetically
        self.WordWidget.sortItems(0, order=Qt.AscendingOrder)
        #self.SortListS.emit()
        
    def DelWordInList(self):
        #Remove selected word from word list
        selected_row = self.WordWidget.currentRow()
        if selected_row == -1:  # No row is selected
            QMessageBox.warning(self, "Error", 'Choose a to Delete')
            return
        self.WordWidget.removeRow(selected_row)
        self.WordWidget.sortItems(0, order=Qt.AscendingOrder)
        #self.DelWordInListS.emit()

    def load_sentencesWR(self,file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            paragraphs = content.split('\n\n')  # Split content into paragraphs
            filtered_sentences = []
            for paragraph in paragraphs:
                
                #replace words before splitting sentences
                for item in self.rplwords:
                    paragraph = paragraph.replace(item[0],item[1])

                if self.extraReplacement:
                    filtered_list = self.Paragraph2Sentence(paragraph)
                else:
                    filtered_list = self.model.filter_paragraph(paragraph)  
                    
                filtered_sentences.extend(filtered_list)
        return filtered_sentences

    def Paragraph2Sentence(self,paragraph) -> list:
        paragraph = re.sub('\n|-', ' ', re.sub('\[|\]|\*|\\|\<|\>|_|\"|\“|\”', '', paragraph))
        paragraph = re.sub('…', '-', paragraph)
        
        # Substitutions for some abbreviations, can just be in rplwords, but these are common
        paragraph = paragraph.replace('Mr.','Mister')
        paragraph = paragraph.replace('Mrs.','Misses')
        paragraph = paragraph.replace('Ms.','Miz')
        paragraph = paragraph.replace('Dr.','Doctor')
        #add space before period, to improve end of sentence audio
        paragraph = paragraph.replace(r'. ', ' .*%')
        
        #This removes excess spaces.  
        #These occur with indented paragraphs without periods.
        #Included poems for example.
        paragraph = paragraph.replace(r'     ', ' ')
        paragraph = paragraph.replace(r'    ', ' ')
        paragraph = paragraph.replace(r'   ', ' ')
        paragraph = paragraph.replace(r'  ', ' ')

        sentence_list = [s.strip() for s in paragraph.split('*%') if (s.strip()!='.' and s.strip()!='')]
        return sentence_list
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = WordReplacerView()
    main_window.show()
    sys.exit(app.exec())      