import os
import sys
from PySide2.QtCore import Qt
from PySide2.QtGui import QGuiApplication
from PySide2.QtWidgets import QAction, QApplication, QGridLayout, QMainWindow, QMenu, QSplitter, QWidget
from CheckUpdateDialog import CheckUpdateDialog
from CourseTreeWidget import CourseTreeWidget
from DownloadDirTreeWidget import DownloadDirTreeWidget
from ErrorMessageBox import ErrorMessageBox
from FileDownloaderWidget import FileDownloaderWidget
from FileListWidget import FileListWidget
from Settings import Settings
from UserLoginDialog import UserLoginDialog


class ABookDownloaderMainWindow(QMainWindow):

    def __init__(self, path, settings, session):
        QMainWindow.__init__(self)
        self.settings = settings
        self.course_tree_widget = CourseTreeWidget(path, settings, session)
        self.file_list_widget = FileListWidget()
        self.download_dir_tree_widget = DownloadDirTreeWidget(settings['download_path'])
        self.file_downloader = FileDownloaderWidget()
        self.vSplitter = QSplitter(Qt.Vertical)
        self.hSplitter1 = QSplitter(Qt.Horizontal)
        self.hSplitter2 = QSplitter(Qt.Horizontal)
        self.hSplitter1.addWidget(self.course_tree_widget)
        self.hSplitter1.addWidget(self.file_list_widget)
        self.hSplitter2.addWidget(self.download_dir_tree_widget)
        self.hSplitter2.addWidget(self.file_downloader)
        self.vSplitter.addWidget(self.hSplitter1)
        self.vSplitter.addWidget(self.hSplitter2)
        self.maxWidth = QGuiApplication.primaryScreen().size().width()
        self.maxHeight = QGuiApplication.primaryScreen().size().height()
        self.hSplitter1.setSizes([self.maxWidth, self.maxWidth])
        self.hSplitter2.setSizes([self.maxWidth, self.maxWidth])
        self.vSplitter.setSizes([self.maxHeight, self.maxHeight])
        mainWidget = QWidget(self)
        mainLayout = QGridLayout()
        mainWidget.setLayout(mainLayout)
        mainLayout.addWidget(self.vSplitter)
        self.course_tree_widget.signal.clearFileListWidget.connect(self.file_list_widget.clear)
        self.course_tree_widget.signal.appendRowFileListWidget.connect(self.file_list_widget.appendRow)
        self.course_tree_widget.signal.addDownloadTask.connect(self.file_downloader.addDownloadTask)
        self.setCentralWidget(mainWidget)
        self.init_menubar()
        self.setFont('Microsoft YaHei UI')
        self.setWindowTitle("ABookDownloader Dev")
        self.showMaximized()
        sys.stderr = ErrorMessageBox()

    def init_menubar(self):
        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Alt+F4')
        exitAction.setStatusTip('Quit')
        exitAction.triggered.connect(self.close)

        aboutAction = QAction('About', self)
        aboutAction.setStatusTip('About')

        updateAction = QAction('Check Updates', self)
        updateAction.setStatusTip('Check Update')
        updateAction.triggered.connect(self.checkUpdate)

        aboutQtAction = QAction("About Qt", self)
        aboutQtAction.triggered.connect(QApplication.aboutQt)

        debugAction = QAction('Debug', self)
        debugAction.triggered.connect(self.debug)

        maximizeCourseWindow = QAction('Maximize Course Window', self)
        maximizeCourseWindow.triggered.connect(self.maximizeCourse)
        maximizeCourseWindow.setShortcut('Alt+D')
        maximizeResourceWindow = QAction('Maximize Resource Window', self)
        maximizeResourceWindow.triggered.connect(self.maximizeResource)
        maximizeResourceWindow.setShortcut('Alt+F')
        maximizeLocalFilesWindow = QAction('Maximize Local Files Window', self)
        maximizeLocalFilesWindow.triggered.connect(self.maximizeLocalFiles)
        maximizeLocalFilesWindow.setShortcut('Alt+C')
        maximizeDownloaderWindow = QAction('Maximize Downloader Window', self)
        maximizeDownloaderWindow.triggered.connect(self.maximizeDownloader)
        maximizeDownloaderWindow.setShortcut('Alt+V')
        resetWindow = QAction('Reset Window Layout', self)
        resetWindow.triggered.connect(self.resetWindow)
        resetWindow.setShortcut('Alt+R')

        self.menuBar().setNativeMenuBar(True)
        fileMenu = QMenu('About')
        fileMenu.addAction(exitAction)
        fileMenu.addAction(aboutQtAction)
        fileMenu.addAction(updateAction)
        fileMenu.addAction(debugAction)

        windowMenu = QMenu('Window')
        windowMenu.addAction(maximizeCourseWindow)
        windowMenu.addAction(maximizeResourceWindow)
        windowMenu.addAction(maximizeLocalFilesWindow)
        windowMenu.addAction(maximizeDownloaderWindow)
        windowMenu.addAction(resetWindow)

        self.menuBar().addMenu(fileMenu)
        self.menuBar().addMenu(windowMenu)

    def maximizeCourse(self):
        self.hSplitter1.setSizes([self.maxWidth, 0])
        self.vSplitter.setSizes([self.maxHeight, 0])

    def maximizeResource(self):
        self.hSplitter1.setSizes([0, self.maxWidth])
        self.vSplitter.setSizes([self.maxHeight, 0])

    def maximizeLocalFiles(self):
        self.hSplitter2.setSizes([self.maxWidth, 0])
        self.vSplitter.setSizes([0, self.maxHeight])

    def maximizeDownloader(self):
        self.hSplitter2.setSizes([0, self.maxWidth])
        self.vSplitter.setSizes([0, self.maxHeight])

    def resetWindow(self):
        self.hSplitter1.setSizes([self.maxWidth, self.maxWidth])
        self.hSplitter2.setSizes([self.maxWidth, self.maxWidth])
        self.vSplitter.setSizes([self.maxHeight, self.maxHeight])

    def checkUpdate(self):
        checkUpdateDialog = CheckUpdateDialog(self.settings)
        checkUpdateDialog.exec_()

    def debug(self):
        raise SystemError


def init():
    dirList = ['./Downloads', './temp', './temp/jsonCache', './temp/picCache']
    for dir in dirList:
        os.makedirs(dir, exist_ok=True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    init()
    settings = Settings('./temp/settings.json')
    user = UserLoginDialog(settings)
    if settings['debug'] is False:
        user.exec_()
        if user.loginStatus is False:
            exit(0)
    abook = ABookDownloaderMainWindow('./temp/', settings, user)
    abook.show()
    if settings['debug'] is True:
        abook.course_tree_widget.importCourseButton.setDisabled(True)
    sys.exit(app.exec_())
