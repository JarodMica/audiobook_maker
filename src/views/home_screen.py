# views/home_screen.py
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from views.audiobook_maker import AudiobookMakerView
from views.audiobook_trainer import AudiobookTrainerView

class HomeScreen(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Home")
        self._init_ui()
    
    def _init_ui(self):
        # Create a central widget with a vertical layout and two buttons.
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        self.maker_button = QPushButton("Audiobook Maker")
        self.trainer_button = QPushButton("Audiobook Trainer")
        
        layout.addWidget(self.maker_button)
        layout.addWidget(self.trainer_button)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Connect the buttons to open the corresponding windows.
        self.maker_button.clicked.connect(self.open_maker)
        self.trainer_button.clicked.connect(self.open_trainer)
    
    def open_maker(self):
        # Instantiate the existing AudiobookMakerView.
        # (No functionality is changed in the maker view.)
        from views.audiobook_maker import AudiobookMakerView  # import here if necessary
        self.maker_view = AudiobookMakerView()
        self.maker_view.show()
        self.hide()
        # When the maker view is closed, show this home screen again.
        self.maker_view.destroyed.connect(self.show)
    
    def open_trainer(self):
        # Instantiate the new AudiobookTrainerView.
        self.trainer_view = AudiobookTrainerView()
        self.trainer_view.show()
        self.hide()
        self.trainer_view.destroyed.connect(self.show)