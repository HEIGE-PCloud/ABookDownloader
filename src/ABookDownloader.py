import os
import sys
from PySide2.QtWidgets import QAction, QApplication, QGridLayout, QMainWindow, QMenu, QWidget
from CheckUpdateDialog import CheckUpdateDialog
from CourseTreeWidget import CourseTreeWidget
from DownloadDirTreeWidget import DownloadDirTreeWidget
from ErrorMessageBox import ErrorMessageBox
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
        course_tree_widget.signal.addDownloadTask.connect(file_downloader.addDownloadTask)
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
    if os.path.exists('./Downloads') == False:
        os.mkdir('Downloads')
    if os.path.exists('temp') == False:
        os.mkdir('temp')
    if os.path.exists('./temp/cache') == False:
        os.mkdir('./temp/cache')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    init()
    settings = Settings('./temp/settings.json')
    user = UserLoginDialog()
    if settings['debug'] == False:
        user.exec_()
        if user.login_status == False:
            exit(0)
    abook = ABookDownloaderMainWindow('./temp/', settings, user)
    abook.show()
    sys.exit(app.exec_())
