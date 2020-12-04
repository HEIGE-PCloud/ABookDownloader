import os
import sys
from PySide2.QtGui import QDesktopServices, QStandardItem, QStandardItemModel
from PySide2.QtWidgets import QAbstractItemView, QApplication, QGridLayout, QListView, QPushButton, QWidget
from PySide2.QtCore import QModelIndex, Qt
class FileListWidget(QWidget):

    def __init__(self) -> None:
        QWidget.__init__(self)
        self.index = None
        file_view = QListView()
        self.model = QStandardItemModel()
        file_view.setModel(self.model)
        file_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        file_view.clicked.connect(self.onClicked)
        file_view.doubleClicked.connect(self.onDoubleClicked)
        open_file_button = QPushButton('Open')
        open_file_button.clicked.connect(self.onOpenFile)
        preview_file_button = QPushButton('Preview')
        preview_file_button.clicked.connect(self.onPreviewFile)
        layout = QGridLayout()
        layout.addWidget(file_view, 0, 0, 1, 2)
        layout.addWidget(open_file_button, 1, 0, 1, 1)
        layout.addWidget(preview_file_button, 1, 1, 1, 1)
        layout.setMargin(0)
        self.setLayout(layout)
        
    def clear(self):
        self.model.clear()

    def appendRow(self, item: QStandardItem):
        self.model.appendRow(item)

    def onDoubleClicked(self, index: QModelIndex):
        self.index = index
        item = self.model.itemFromIndex(self.index)
        url = item.data(-1)
        QDesktopServices.openUrl(url)

    def onClicked(self, index: QModelIndex):
        self.index = index

    def onOpenFile(self):
        if self.index != None:
            item = self.model.itemFromIndex(self.index)
            url = item.data(-1)
            QDesktopServices.openUrl(url)

    def onPreviewFile(self):
        if self.index != None:
            item = self.model.itemFromIndex(self.index)
            url = 'http://view.officeapps.live.com/op/view.aspx?src=' + item.data(-1)
            print(url)
            QDesktopServices.openUrl(url)

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