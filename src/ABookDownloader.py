import sys
from PySide2.QtWidgets import QAction, QApplication, QGridLayout, QMainWindow, QMessageBox, QWidget

from CourseTreeWidget import CourseTreeWidget
from DownloadDirTreeWidget import DownloadDirTreeWidget
from FileDownloader import FileDownloaderWidget
from FileListWidget import FileListWidget
from Settings import Settings
from UserLoginDialog import UserLoginDialog

class ABookDownloaderMainWindow(QMainWindow):

    def __init__(self, path, settings, session):
        QMainWindow.__init__(self)
        course_tree_widget = CourseTreeWidget(path, settings, session)
        file_list_widget = FileListWidget()
        download_dir_tree_widget = DownloadDirTreeWidget(settings['download_path'])
        file_downloader = FileDownloaderWidget()
        mainWidget = QWidget(self)
        mainLayout = QGridLayout()
        mainWidget.setLayout(mainLayout)
        mainLayout.addWidget(course_tree_widget, 0, 0)
        mainLayout.addWidget(file_list_widget, 0, 1)
        mainLayout.addWidget(download_dir_tree_widget, 1, 0)
        mainLayout.addWidget(file_downloader, 1, 1)
        course_tree_widget.signal.clearFileListWidget.connect(file_list_widget.clear)
        course_tree_widget.signal.appendRowFileListWidget.connect(file_list_widget.appendRow)
        self.setCentralWidget(mainWidget)
        self.init_menubar()
        self.setWindowTitle("ABookDownloader Dev")
        self.resize(1920, 1080)

    def init_menubar(self):
        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Alt+F4')
        exitAction.setStatusTip('Quit')
        exitAction.triggered.connect(self.close)
        
        aboutAction = QAction('About', self)
        aboutAction.setStatusTip('About')
        
        self.menuBar().setNativeMenuBar(True)
        fileMenu = self.menuBar().addMenu('About')
        fileMenu.addAction(exitAction)

        aboutQtAct = QAction("About &Qt", self, triggered=QApplication.aboutQt)
        fileMenu.addAction(aboutQtAct)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    user = UserLoginDialog()
    settings = Settings('./temp/settings.json')
    abook = ABookDownloaderMainWindow('./temp/', settings, user)
    abook.show()
    sys.exit(app.exec_())
