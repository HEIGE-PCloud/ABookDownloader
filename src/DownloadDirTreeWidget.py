import os
import sys
from PySide2.QtWidgets import QApplication, QCompleter, QFileDialog, QFileSystemModel, QGridLayout, QLineEdit, QPushButton, QSizePolicy, QTreeView, QWidget
import subprocess

class DownloadDirTreeWidget(QWidget):

    def __init__(self, root_path) -> None:
        QWidget.__init__(self)

        # self.index stores the index of the latest item which is clicked 
        # self.root_path is the path to the folder currently showing
        self.index = None
        self.root_path = os.path.abspath(root_path)

        self.dir_view = QTreeView()
        self.model = QFileSystemModel(self.dir_view)
        self.model.setRootPath(self.root_path)
        self.dir_view.clicked.connect(self.onFileItemClicked)
        self.dir_view.doubleClicked.connect(self.onFileItemDoubleClicked)
        self.dir_view.setModel(self.model)
        self.dir_view.setRootIndex(self.model.index(self.root_path))
        
        open_button = QPushButton("Open")
        open_button.clicked.connect(self.openFile)
        
        open_in_file_explorer_button = QPushButton("Open in File Explorer")
        open_in_file_explorer_button.clicked.connect(self.openInFileExplorer)

        self.root_path_line_edit = QLineEdit(self.root_path)
        self.root_path_line_edit.returnPressed.connect(self.onChangeLineEditReturned)
        self.root_path_line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.root_path_line_edit.adjustSize()

        change_path_button = QPushButton('Change Directory')
        change_path_button.clicked.connect(self.onChangeButtonClicked)
        
        addressCompleter = QCompleter()
        addressCompleter.setModel(self.model)
        self.root_path_line_edit.setCompleter(addressCompleter)

        # Set layout
        layout = QGridLayout()
        layout.addWidget(self.root_path_line_edit, 0, 0, 1, 1)
        layout.addWidget(change_path_button, 0, 1, 1, 1)
        layout.addWidget(self.dir_view, 1, 0, 1, 2)
        layout.addWidget(open_button, 2, 0, 1, 1)
        layout.addWidget(open_in_file_explorer_button, 2, 1, 1, 1)
        layout.setMargin(0)
        self.setLayout(layout)
 
    def setRootPath(self, root_path):
        self.root_path = os.path.abspath(root_path)

    def openFile(self):
        if self.index != None:
            file_path = self.model.filePath(self.index).replace('/', '\\')
            is_dir = self.model.isDir(self.index)
            # If is file, open with default program
            # If is directory, open with file explorer
            if is_dir == False:
                os.startfile(file_path, 'open')
            else:
                subprocess.run(['explorer', file_path])

    def openInFileExplorer(self):
        if self.index != None:
            file_path = self.model.filePath(self.index).replace('/', '\\')
            subprocess.run(['explorer', '/select,', file_path])

    def onFileItemClicked(self, index):
        # When clicked, resize and update self.index
        self.dir_view.resizeColumnToContents(0)
        self.index = index

    def onFileItemDoubleClicked(self, index):
        # When double clicked, update self.index and open the file directly
        self.index = index
        if self.sender().model().isDir(index) == False:
            self.openFile()

    def onChangeButtonClicked(self):
        new_path = QFileDialog.getExistingDirectory(self, 'Change Directory', self.root_path)
        self.changeRootPath(new_path)

    def onChangeLineEditReturned(self):
        new_path = self.root_path_line_edit.text()
        if os.path.isdir(new_path):
            self.changeRootPath(new_path)
        else:
            subprocess.run(['explorer', new_path])
            self.root_path_line_edit.setText(self.root_path)

    def changeRootPath(self, new_path: str):
        if os.path.exists(new_path):
            self.root_path = os.path.abspath(new_path)
            self.dir_view.setRootIndex(self.model.index(self.root_path))
            self.root_path_line_edit.setText(self.root_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tree_view = DownloadDirTreeWidget('.')

    tree_view.resize(1920, 1080)
    tree_view.show()
    sys.exit(app.exec_())