from PySide2.QtWidgets import QGridLayout, QTextEdit, QWidget
from PySide2.QtCore import Qt

class ErrorMessageBox(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.error = ''
        self.errorInformationBox = QTextEdit()
        layout = QGridLayout()
        layout.addWidget(self.errorInformationBox)
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
