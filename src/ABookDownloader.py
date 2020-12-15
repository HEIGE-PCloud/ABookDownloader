import os
import sys
from PySide2.QtWidgets import QAction, QApplication, QGridLayout, QMainWindow, QMenu, QWidget
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
        self.course_tree_widget = CourseTreeWidget(path, settings, session)
        self. file_list_widget = FileListWidget()
        self.download_dir_tree_widget = DownloadDirTreeWidget(settings['download_path'])
        self.file_downloader = FileDownloaderWidget()
        mainWidget = QWidget(self)
        mainLayout = QGridLayout()
        mainWidget.setLayout(mainLayout)
        mainLayout.addWidget(self.course_tree_widget, 0, 0)
        mainLayout.addWidget(self.file_list_widget, 0, 1)
        mainLayout.addWidget(self.download_dir_tree_widget, 1, 0)
        mainLayout.addWidget(self.file_downloader, 1, 1)
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

        self.menuBar().setNativeMenuBar(True)
        fileMenu = QMenu('About')
        fileMenu.addAction
        fileMenu.addAction(exitAction)
        fileMenu.addAction(aboutQtAction)
        fileMenu.addAction(updateAction)
        fileMenu.addAction(debugAction)
        self.menuBar().addMenu(fileMenu)

    def checkUpdate(self):
        checkUpdateDialog = CheckUpdateDialog()
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
    user = UserLoginDialog()
    if settings['debug'] == False:
        user.exec_()
        if user.loginStatus == False:
            exit(0)
    abook = ABookDownloaderMainWindow('./temp/', settings, user)
    abook.show()
    if settings['debug'] == True:
        abook.course_tree_widget.refresh_button.setDisabled(True)
    sys.exit(app.exec_())
