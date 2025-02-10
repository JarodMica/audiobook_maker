# views/audiobook_trainer.py
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel

class AudiobookTrainerView(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Audiobook Trainer")
        self._init_ui()
    
    def _init_ui(self):
        # Create a simple layout with a placeholder label and a Back button.
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        self.trainer_label = QLabel("Audiobook Trainer – Features not yet defined")
        layout.addWidget(self.trainer_label)
        
        self.back_button = QPushButton("Back")
        # When Back is clicked, simply close this window.
        self.back_button.clicked.connect(self.close)
        layout.addWidget(self.back_button)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)