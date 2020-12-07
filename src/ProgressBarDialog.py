from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDialog, QProgressBar, QVBoxLayout, QApplication
import sys

class ProgressBarDialog(QDialog):
    def __init__(self, min_value_1: int, max_value_1: int, min_value_2: int, max_value_2: int):
        QDialog.__init__(self)
        flags = self.windowFlags()
        self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        self.progress_bar_1 = QProgressBar()
        self.progress_bar_2 = QProgressBar()
        self.setMinimum_1(min_value_1)
        self.setMaximum_1(max_value_1)
        self.setMinimum_2(min_value_2)
        self.setMaximum_2(max_value_2)
        layout = QVBoxLayout()
        layout.addWidget(self.progress_bar_1)
        layout.addWidget(self.progress_bar_2)
        self.setLayout(layout)
        # self.show()
    def setMinimum_1(self, value: int):
        self.progress_bar_1.setMinimum(value)
    def setMaximum_1(self, value: int):
        self.progress_bar_1.setMaximum(value)
    def setValue_1(self, value: int):
        self.progress_bar_1.setValue(value)
    def setMinimum_2(self, value: int):
        self.progress_bar_2.setMinimum(value)
    def setMaximum_2(self, value: int):
        self.progress_bar_2.setMaximum(value)
    def setValue_2(self, value: int):
        self.progress_bar_2.setValue(value)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pd = ProgressBarDialog(0, 100, 2, 50)
    pd.setValue_1(100)
    pd.setValue_2(43)
    
    sys.exit(app.exec_())