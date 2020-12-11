import sys
import requests
from PySide2.QtCore import QObject, QThread, Signal
from PySide2.QtWidgets import QApplication, QDialog, QGridLayout, QLabel, QPushButton, QTextEdit

class CheckUpdateWorker(QThread):

    def __init__(self, parent=None) -> None:
        super(CheckUpdateWorker, self).__init__(parent)
        self.api = "https://api.github.com/repos/HEIGE-PCloud/ABookDownloader/releases/latest"
        self.parent = parent

    def run(self):
        try:
            proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
            data = requests.get(self.api, proxies=proxies).json()
        except:
            self.parent.checkUpdatePushButton.setDisabled(False)
            self.parent.signal.versionInformationSignal.emit('Failed!')
        else:
            version = data['tag_name']
            description = data['body']
            url = data['assets'][0]['browser_download_url']
            self.parent.checkUpdatePushButton.setDisabled(False)
            self.parent.signal.versionInformationSignal.emit(description)

class CheckUpdateSignals(QObject):
    versionInformationSignal = Signal(str)

class CheckUpdateDialog(QDialog):

    def __init__(self) -> None:
        QDialog.__init__(self)
        self.signal = CheckUpdateSignals()
        self.current_version = 'Dev'
        currentVersionLabel = QLabel('Current Version: {}'.format(self.current_version))
        self.checkUpdatePushButton = QPushButton('Check Update')
        self.checkUpdatePushButton.clicked.connect(self.getUpdate)
        self.versionInformationBox = QTextEdit()
        layout = QGridLayout()
        layout.addWidget(currentVersionLabel)
        layout.addWidget(self.checkUpdatePushButton)
        layout.addWidget(self.versionInformationBox)
        self.versionInformationBox.setText('qwq')
        self.signal.versionInformationSignal.connect(self.setText)
        self.setLayout(layout)

    def getUpdate(self):
        self.checkUpdatePushButton.setDisabled(True)
        worker = CheckUpdateWorker(self)
        worker.start()

    def setText(self, text: str):
        self.versionInformationBox.setText(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    update = CheckUpdateDialog()
    update.show()
    sys.exit(app.exec_())