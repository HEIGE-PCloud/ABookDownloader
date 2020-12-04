import sys
from PySide2.QtWidgets import QAction, QApplication, QMainWindow, QMessageBox

from CourseTreeWidget import CourseTreeWidget
from Settings import Settings
from UserLoginDialog import UserLoginDialog

class ABookDownloaderMainWindow(QMainWindow):

    def __init__(self, path, settings, session):
        QMainWindow.__init__(self)
        course_tree_widget = CourseTreeWidget(path, settings, session)


        self.statusBar().showMessage('Here is the status bar')

        self.init_menubar()

        self.setCentralWidget(course_tree_widget)

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

        # aboutMenu = self.menuBar().addMenu("&About")
        aboutQtAct = QAction("About &Qt", self, triggered=QApplication.aboutQt)
        fileMenu.addAction(aboutQtAct)

    def about_msgbox(self):
        QMessageBox()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    user = UserLoginDialog()
    settings = Settings('./temp/settings.json')
    abook = ABookDownloaderMainWindow('./temp/', settings, user)
    abook.show()
    sys.exit(app.exec_())
