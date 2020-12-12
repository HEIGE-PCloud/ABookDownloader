import subprocess
from PySide2.QtCore import QObject, Signal

import pyperclip
from PySide2.QtWidgets import QMessageBox, QWidget



class ErrorMessageBox(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.error = ''

        self.messageBox = QMessageBox()
        self.messageBox.setIcon(QMessageBox.Critical)
        self.messageBox.setText("Encountered an error")
        self.messageBox.setInformativeText("Click show details to learn more")
        self.messageBox.setWindowTitle("Error")
        self.messageBox.setDetailedText("")

    def write(self, message):
        print(message, end='')
        with open('./temp/error.log', 'a', encoding='utf-8') as file:
            file.write(message)
        self.error += message
        # self.messageBox.setDetailedText(self.error)
        # self.messageBox.show()

    def copy(self):
        pyperclip.copy(self.errorInformationBox.toPlainText())

    def open(self):
        subprocess.run(['explorer', '.\\temp\\error.log'])
