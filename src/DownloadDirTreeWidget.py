
from logging import root
import os
import sys
from PySide2.QtWidgets import QApplication, QFileSystemModel, QGridLayout, QPushButton, QTreeView, QWidget
import subprocess

class DownloadDirTreeWidget(QWidget):

    def __init__(self, root_path) -> None:
        QWidget.__init__(self)
        self.root_path = root_path
        dir_view = QTreeView()
        dir_view.clicked.connect(self.onClicked)
        dir_view.doubleClicked.connect(self.onDoubleClicked)
        self.model = QFileSystemModel(dir_view)
        self.model.setRootPath(self.root_path)

        dir_view.setModel(self.model)
        dir_view.setRootIndex(self.model.index(self.root_path))
        open_button = QPushButton("Open")
        open_button.clicked.connect(self.open_file)
        open_in_file_explorer_button = QPushButton("Open in File Explorer")
        open_in_file_explorer_button.clicked.connect(self.open_in_file_explorer)
        self.index = None

        layout = QGridLayout()
        layout.addWidget(dir_view, 0, 0, 1, 2)
        layout.addWidget(open_button, 1, 0)
        layout.addWidget(open_in_file_explorer_button, 1, 1)
        layout.setMargin(0)
        self.setLayout(layout)
        self.show()

    def setRootPath(self, root_path):
        self.root_path = os.path.abspath(root_path)

    def open_file(self):
        file_path = self.model.filePath(self.index).replace('/', '\\')
        is_dir = self.model.isDir(self.index)
        if is_dir == False:
            os.startfile(file_path, 'open')
        else:
            subprocess.run(['explorer', file_path])

    def open_in_file_explorer(self):
        file_path = self.model.filePath(self.index).replace('/', '\\')
        subprocess.run(['explorer', '/select,', file_path])

    def onClicked(self, index):
        self.index = index

    def onDoubleClicked(self, index):
        self.index = index
        if self.sender().model().isDir(index) == False:
            self.open_file()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tree_view = DownloadDirTreeWidget('.')
    tree_view.resize(1920, 1080)

    sys.exit(app.exec_())