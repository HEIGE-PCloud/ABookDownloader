import os
import sys
from PySide2.QtGui import QStandardItem, QStandardItemModel
from PySide2.QtWidgets import QAbstractItemView, QApplication, QFileDialog, QFileSystemModel, QGridLayout, QLineEdit, QListView, QPushButton, QTreeView, QWidget
import subprocess
from PySide2.QtCore import QDir, Qt
class FileListWidget(QWidget):

    def __init__(self) -> None:
        QWidget.__init__(self)
        file_view = QListView()
        self.model = QStandardItemModel()
        file_view.setModel(self.model)
        file_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        file_view.doubleClicked.connect(self.onDoubleClicked)
        layout = QGridLayout()
        layout.addWidget(file_view)
        layout.setMargin(0)
        self.setLayout(layout)
        
    def clear(self):
        self.model.clear()

    def appendRow(self, item: QStandardItem):
        self.model.appendRow(item)

    def onDoubleClicked(self, index):
        item = self.model.itemFromIndex(index)
        print(item.data(-1))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    list_widget = FileListWidget()
    list_widget.show()
    item1 = QStandardItem('item 1')
    list_widget.appendRow(item1)
    item2 = QStandardItem('item 2')
    item2.setData('Data Role', -1)
    item2.setData('Display Role', Qt.DisplayRole)
    
    list_widget.appendRow(item2)
    
    sys.exit(app.exec_())