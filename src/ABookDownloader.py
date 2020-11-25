import sys
from PySide2.QtWidgets import QApplication, QMainWindow

class ABookDownloaderMainWindow(QMainWindow):

    def __init__(self) -> None:
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)

    sys.exit(app.exec_())