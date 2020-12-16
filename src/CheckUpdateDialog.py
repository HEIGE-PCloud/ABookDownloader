import sys
import requests
import pyperclip
from PySide2.QtGui import QDesktopServices
from PySide2.QtCore import QObject, QThread, Qt, Signal
from PySide2.QtWidgets import QApplication, QDialog, QGridLayout, QLabel, QPushButton, QTextEdit

class CheckUpdateWorker(QThread):

    def __init__(self, parent=None) -> None:
        super(CheckUpdateWorker, self).__init__(parent)
        self.api = "https://api.github.com/repos/HEIGE-PCloud/ABookDownloader/releases/latest"
        self.parent = parent

    def run(self):
        try:
            data = requests.get(self.api).json()
        except:
            self.parent.checkUpdatePushButton.setDisabled(False)
            self.parent.signal.versionInformationSignal.emit('Failed!')
        else:
            version = data['tag_name']
            if version != self.parent.current_version:
                description = data['body']
                url = data['assets'][0]['browser_download_url']
                self.parent.checkUpdatePushButton.setDisabled(False)
                self.parent.signal.versionInformationSignal.emit(description)
                self.parent.signal.versionLabelSignal.emit(version)
                self.parent.signal.downloadUrlSignal.emit(url)
            else:
                self.parent.signal.versionInformationSignal.emit('No new version detected.')
                self.parent.signal.versionLabelSignal.emit(version)

class CheckUpdateSignals(QObject):
    versionInformationSignal = Signal(str)
    versionLabelSignal = Signal(str)
    downloadUrlSignal = Signal(str)

class CheckUpdateDialog(QDialog):

    def __init__(self) -> None:
        QDialog.__init__(self)
        self.signal = CheckUpdateSignals()
        self.current_version = 'Dev'
        self.downloadUrl = ''
        currentVersionLabel = QLabel('Current Version: {}'.format(self.current_version))
        self.latestVersionLabel = QLabel('Latest Version: {}'.format('Unknown'))
        self.checkUpdatePushButton = QPushButton('Check Update')
        self.checkUpdatePushButton.clicked.connect(self.getUpdate)
        self.versionInformationBox = QTextEdit()
        self.versionInformationBox.setReadOnly(True)
        self.downloadButton = QPushButton('Download')
        self.downloadButton.setVisible(False)
        self.downloadButton.clicked.connect(self.downloadUpdate)
        self.copyUrlButton = QPushButton('Copy Download Url')
        self.copyUrlButton.setVisible(False)
        self.copyUrlButton.clicked.connect(self.copy)
        layout = QGridLayout()
        layout.addWidget(currentVersionLabel)
        layout.addWidget(self.latestVersionLabel)
        layout.addWidget(self.versionInformationBox)
        layout.addWidget(self.checkUpdatePushButton)
        layout.addWidget(self.downloadButton)
        layout.addWidget(self.copyUrlButton)
        self.versionInformationBox.setText('')
        self.signal.versionInformationSignal.connect(self.setVersionInformation)
        self.signal.versionLabelSignal.connect(self.setVersionLabel)
        self.signal.downloadUrlSignal.connect(self.updateDownloadUrl)
        self.setLayout(layout)
        self.setWindowTitle('Check Update')
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint)
        self.checkUpdatePushButton.click()

    def getUpdate(self):
        self.checkUpdatePushButton.setDisabled(True)
        worker = CheckUpdateWorker(self)
        worker.start()

    def setVersionLabel(self, text: str):
        self.latestVersionLabel.setText('Latest Version: {}'.format(text))

    def setVersionInformation(self, text: str):
        self.versionInformationBox.setText(text)

    def updateDownloadUrl(self, url: str):
        self.downloadButton.setVisible(True)
        self.copyUrlButton.setVisible(True)
        self.downloadUrl = url

    def downloadUpdate(self):
        QDesktopServices.openUrl(self.downloadUrl)

    def copy(self):
        pyperclip.copy(self.downloadUrl)
        self.copyUrlButton.setText('Copied!')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    update = CheckUpdateDialog()
    update.show()
    sys.exit(app.exec_())