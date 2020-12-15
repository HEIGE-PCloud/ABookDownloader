import os
import sys
import time 
from PySide2.QtCore import QObject, QThread, Qt, Signal
from PySide2.QtWidgets import QApplication, QCheckBox, QGridLayout, QProgressBar, QPushButton, QTableWidget, QTableWidgetItem, QWidget
import logging

import requests

class FileDownloaderSignals(QObject):
    startDownload = Signal(bool)
    cancelDownload = Signal(int)
    downloadSpeed = Signal(int, str)
    downloadStatus = Signal(int, str)
    progressBarValue = Signal(int, int)

class FileDownloaderWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.id = 1
        self.signals = FileDownloaderSignals()
        self.tableWidget = QTableWidget()       
        self.startDownloadButton = QPushButton('Start Download')
        self.clearListButton = QPushButton('Clear Download List')
        self.hideFinishedCheckBox = QCheckBox('Hide Finished')
        self.TASKID = 0
        self.FILENAME = 1
        self.PROGRESSBAR = 2
        self.SPEED = 3
        self.STATUS = 4
        self.URL = 5
        self.FILEPATH = 6
        self.CANCEL = 7
        self.RETRY = 8
        self.DELETE = 9
        self.startDownloadButton.clicked.connect(self.startDownload)
        self.clearListButton.clicked.connect(self.clearDownloadList)
        self.hideFinishedCheckBox.clicked.connect(self.hideFinished)
        self.createTable()
        layout = QGridLayout()
        layout.addWidget(self.tableWidget, 0, 0, 1, 2)
        layout.addWidget(self.hideFinishedCheckBox, 1, 0, 1, 1)
        layout.addWidget(self.startDownloadButton, 2, 0, 1, 1)
        layout.addWidget(self.clearListButton, 2, 1, 1, 1)
        self.setLayout(layout)
        self.resize(1920, 1080)

    def createTable(self):
        # taskId | fileName | progressBar | speed | status | url | filePath | cancel | retry | delete
        tableItemList = ['Task ID', 'File Name', 'Progress Bar', 'Download Speed', 'Download Status', 'Url', 'File Path', 'Cancel', 'Retry', 'Delete']
        self.tableWidget.setColumnCount(len(tableItemList))
        self.tableWidget.setRowCount(0)
        for i in range(len(tableItemList)):
            self.tableWidget.setHorizontalHeaderItem(i, QTableWidgetItem(tableItemList[i]))
        
    def addDownloadItem(self, taskId: str, fileName: str, filePath: str, url: str):
        row = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(row + 1)

        taskIdItem = QTableWidgetItem(taskId)
        fileNameItem = QTableWidgetItem(fileName)
        progressBarItem = QTableWidgetItem()
        downloadSpeedItem = QTableWidgetItem("0 MB/s")
        downloadStatusItem = QTableWidgetItem("Pending")
        downloadUrlItem = QTableWidgetItem(url)
        filePathItem = QTableWidgetItem(filePath)
        cancelItem = QTableWidgetItem()
        retryItem = QTableWidgetItem()
        deleteItem = QTableWidgetItem()

        taskIdItem.setFlags(Qt.ItemIsEnabled)
        fileNameItem.setFlags(Qt.ItemIsEnabled)
        progressBarItem.setFlags(Qt.ItemIsEnabled)
        downloadSpeedItem.setFlags(Qt.ItemIsEnabled)
        downloadStatusItem.setFlags(Qt.ItemIsEnabled)
        downloadUrlItem.setFlags(Qt.ItemIsEnabled)
        filePathItem.setFlags(Qt.ItemIsEnabled)
        cancelItem.setFlags(Qt.ItemIsEnabled)
        retryItem.setFlags(Qt.ItemIsEnabled)
        deleteItem.setFlags(Qt.ItemIsEnabled)

        progressBar = QProgressBar()
        progressBar.setMinimum(0)
        progressBar.setMaximum(100)
        progressBar.setValue(0)
        progressBar.setAlignment(Qt.AlignCenter)
        progressBar.setFormat(str(progressBar.value()) + ' %')

        cancelButton = QPushButton('Cancel')
        cancelButton.clicked.connect(self.cancelTask)

        retryButton = QPushButton('Retry')
        retryButton.clicked.connect(self.retryTask)

        deleteButton = QPushButton('Delete')
        deleteButton.clicked.connect(self.deleteTask)

        self.tableWidget.setItem(row, 0, taskIdItem)
        self.tableWidget.setItem(row, 1, fileNameItem)
        self.tableWidget.setItem(row, 2, progressBarItem)
        self.tableWidget.setCellWidget(row, 2, progressBar)
        self.tableWidget.setItem(row, 3, downloadSpeedItem)
        self.tableWidget.setItem(row, 4, downloadStatusItem)
        self.tableWidget.setItem(row, 5, downloadUrlItem)
        self.tableWidget.setItem(row, 6, filePathItem)
        self.tableWidget.setItem(row, 7, cancelItem)
        self.tableWidget.setCellWidget(row, 7, cancelButton)
        self.tableWidget.setItem(row, 8, retryItem)
        self.tableWidget.setCellWidget(row, 8, retryButton)
        self.tableWidget.setItem(row, 9, deleteItem)
        self.tableWidget.setCellWidget(row, 9, deleteButton)
        
    def hideFinished(self):
        """
        hideFinished() is triggered when the hideFinishedCheckbox is clicked
        It will hide all rows with Cancelled or Finished status and leave
        Pending or Downloading items visible.
        """
        rowListCancel = self.rowOfValue('Cancelled', self.STATUS)
        rowListFinished = self.rowOfValue('Finished', self.STATUS)
        rowList = rowListCancel + rowListFinished
        logging.debug("rowList: {}".format(rowList))
        for row in rowList:
            if self.hideFinishedCheckBox.isChecked() == True:
                self.tableWidget.hideRow(row)
            else:
                self.tableWidget.showRow(row)

    def addDownloadTask(self, fileName: str, filePath: str, url: str):
        """
        addDownloadTask(fileName: str, filePath: str, url: str) is an interface
        to be called externally to add a download task to the widget.
        """
        self.addDownloadItem(str(self.id), fileName, filePath, url)
        self.id += 1

    def startDownload(self):
        """
        startTask() will find the first task in the table with Pending
        status and start it.
        """
        row = self.rowOfValue('Pending', self.STATUS)
        if (len(row) > 0):
            row = row[0]
            self.startTask(int(self.tableWidget.item(row, self.TASKID).text()))

    def startTask(self, taskId: int):
        """
        startTask(taskId: int) starts a DownloadWorker and starts the task
        with taskId. It will not check if the task has started before
        or has cancelled.
        """
        row = self.rowOfValue(taskId, self.TASKID)
        if (len(row) > 0):
            row = row[0]
            filePath = self.tableWidget.item(row, self.FILEPATH).text()
            url = self.tableWidget.item(row, self.URL).text()
            worker = DownloadWorker(taskId, filePath, url, self)
            worker.start()

    def cancelTask(self):
        row = self.rowOfWidget(self.sender(), self.CANCEL)
        taskId = int(self.tableWidget.item(row, self.TASKID).text())
        self.tableWidget.item(row, 4).setText('Cancelled')
        self.signals.cancelDownload.emit(taskId)

    def retryTask(self):
        row = self.rowOfWidget(self.sender(), self.RETRY)
        taskId = int(self.tableWidget.item(row, self.TASKID).text())
        self.signals.cancelDownload.emit(taskId)
        self.tableWidget.item(row, self.STATUS).setText('Pending')
        self.startTask(taskId)

    def deleteTask(self):
        row = self.rowOfWidget(self.sender(), self.DELETE)
        taskId = int(self.tableWidget.item(row, self.TASKID).text())
        self.signals.cancelDownload.emit(taskId)
        self.tableWidget.removeRow(row)

    def clearDownloadList(self):
        """
        clearDownloadList() emits a signal to cancell all downloading
        items and directly recreate the table.
        """
        self.signals.cancelDownload.emit(-1)
        self.createTable()

    def rowOfWidget(self, item: QWidget, itemType: int):
        """
        rowOfWidget(item, itemType) is used to locate the embedded
        widget in self.tableWidget. It will compare item with those
        in the itemType column and return the first row number where
        it finds the matched item.
        """
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.cellWidget(row, itemType) == item:
                return row

    def rowOfValue(self, value, itemType: int):
        """
        rowOfValue(value, itemType: str) takes two parameters.
        It will look into self.tableWidget for the itemType(column)
        to find the value. It returns a list of row number where the
        values are.
        """
        rowList = []
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row, itemType).text() == str(value):
                rowList.append(row)
        return rowList

    def updateProgressBar(self, taskId: int, value: int):
        row = self.rowOfValue(taskId, self.TASKID)
        if len(row) > 0:
            row = row[0]
            logging.debug("updateProgressBar of row {} with value {}".format(row, value))
            self.tableWidget.cellWidget(row, self.PROGRESSBAR).setValue(value)
            self.tableWidget.cellWidget(row, self.PROGRESSBAR).setFormat(str(value) + " %")

    def updateDownloadSpeed(self, taskId: int, value: str):
        row = self.rowOfValue(taskId, self.TASKID)
        if len(row) > 0:
            row = row[0]
            logging.debug("updateDownloadSpeed of row {} with value {}".format(row, value))
            self.tableWidget.item(row, self.SPEED).setText(value)

    def updateDownloadStatus(self, taskId: int, value: str):
        row = self.rowOfValue(taskId, self.TASKID)
        if len(row) > 0:
            row = row[0]
            logging.debug("updateDownloadStatus of row {} with value {}".format(row, value))
            self.tableWidget.item(row, self.STATUS).setText(value)


class DownloadWorker(QThread):

    def __init__(self, taskId, filePath, url, parent=None):
        QThread.__init__(self, parent)
        
        self.taskId = taskId
        self.filePath = filePath
        self.dirPath = os.path.dirname(self.filePath)
        self.parent = parent
        self.url = url
        self.signals = FileDownloaderSignals()
        self.signals.progressBarValue.connect(parent.updateProgressBar)
        self.signals.downloadStatus.connect(parent.updateDownloadStatus)
        self.signals.downloadSpeed.connect(parent.updateDownloadSpeed)
        parent.signals.cancelDownload.connect(self.cancelDownload)
        self.cancel = False

    def cancelDownload(self, taskId):
        if taskId == -1 or taskId == self.taskId:
            logging.debug("{} has been cancelled".format(taskId))
            self.cancel = True

    def run(self):
        os.makedirs(self.dirPath, exist_ok=True)
        logging.debug("taskId: {}, filePath: {}, url: {}".format(self.taskId, self.filePath, self.url))
        self.signals.downloadStatus.emit(self.taskId, 'Downloading')
        headers = {'Proxy-Connection': 'keep-alive'}
        request = requests.get(self.url, stream=True, headers=headers)
        contentLength = float(request.headers['content-length'])
        with open(self.filePath, 'wb') as file:
            downloadLength = 0
            lastDownloadedLength = 0
            timeStart = time.time()
            for chunk in request.iter_content(chunk_size=512):
                if self.cancel:
                    self.signals.progressBarValue.emit(self.taskId, 0)
                    self.disconnectSignals()
                    return
                if chunk:
                    file.write(chunk)
                    downloadLength += len(chunk)
                    if time.time() - timeStart > 1:
                        percentage = int(downloadLength / contentLength * 100)
                        self.signals.progressBarValue.emit(self.taskId, percentage)
                        speed = (downloadLength - lastDownloadedLength) / 2097152
                        self.signals.downloadSpeed.emit(self.taskId, '{:.2f}'.format(speed) + 'MB/S')
                        lastDownloadedLength = downloadLength
                        timeStart = time.time()
        self.signals.progressBarValue.emit(self.taskId, 100)
        self.signals.downloadStatus.emit(self.taskId, 'Finished')
        self.disconnectSignals()
        self.exit(0)

    def disconnectSignals(self):
        return
        self.signals.progressBarValue.disconnect(self.parent.updateProgressBar)
        self.signals.downloadStatus.disconnect(self.parent.updateDownloadStatus)
        self.signals.downloadSpeed.disconnect(self.parent.updateDownloadSpeed)
        self.parent.signals.cancelDownload.disconnect(self.cancelDownload)

if __name__ == '__main__': 
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logging.info("init")
    app = QApplication(sys.argv) 
    downloader = FileDownloaderWidget() 
    downloader.show()
    downloader.addDownloadTask("test1", "C:\\Users\\HEIGE\\Documents\\test1.bin", "https://lon-gb-ping.vultr.com/vultr.com.100MB.bin")
    downloader.addDownloadTask("test2", "C:\\Users\\HEIGE\\Documents\\test2.bin", "https://lon-gb-ping.vultr.com/vultr.com.100MB.bin")
    downloader.addDownloadTask("test3", "C:\\Users\\HEIGE\\Documents\\test3.bin", "https://lon-gb-ping.vultr.com/vultr.com.100MB.bin")

    sys.exit(app.exec_()) 