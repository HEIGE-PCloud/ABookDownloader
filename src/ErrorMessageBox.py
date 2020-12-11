import os
import subprocess
from PySide2.QtWidgets import QGridLayout, QPushButton, QTextEdit, QWidget
from PySide2.QtCore import Qt
import pyperclip

class ErrorMessageBox(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.error = ''
        self.errorInformationBox = QTextEdit()
        self.errorInformationBox.setReadOnly(True)
        openFileButton = QPushButton('Open Log File')
        openFileButton.clicked.connect(self.open)
        copyButton = QPushButton('Copy')
        copyButton.clicked.connect(self.copy)
        layout = QGridLayout()
        layout.addWidget(self.errorInformationBox, 0, 0, 1, 2)
        layout.addWidget(openFileButton, 1, 0, 1, 1)
        layout.addWidget(copyButton, 1, 1, 1, 1)
        layout.setMargin(0)
        self.setLayout(layout)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Error Message')

    def write(self, message):
        print(message, end='')
        with open('./temp/error.log', 'a', encoding='utf-8') as file:
            file.write(message)
        self.error += message
        self.errorInformationBox.setText(self.error)
        self.errorInformationBox.verticalScrollBar().setValue(self.errorInformationBox.verticalScrollBar().maximum())
        self.show()

    def copy(self):
        pyperclip.copy(self.errorInformationBox.toPlainText())

    def open(self):
        subprocess.run(['explorer', '.\\temp\\error.log'])