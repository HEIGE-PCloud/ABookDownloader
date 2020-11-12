import sys 
import time
import requests
from PySide2.QtWidgets import * 
from PySide2.QtCore import *
                    
   
class DownloadSignals(QObject):
    download_speed = Signal(list)
    progress_value = Signal(list)
    download_status = Signal(list)
    download_next = Signal(None)
    cancel_download = Signal(None)

class FileDownloaderWidget(QWidget): 
    def __init__(self): 
        super().__init__() 

        self.signals = DownloadSignals()
        self.task_list = []
        self.tableWidget = QTableWidget() 
        
        self.startDownloadButton = QPushButton("Start Download")
        self.startDownloadButton.clicked.connect(self.start_download)
        self.clearDownloadListButton = QPushButton("Clear List")
        self.clearDownloadListButton.clicked.connect(self.clear_download_list)
        self.hideFinishedCheckBox = QCheckBox("Hide Finished")
        self.hideFinishedCheckBox.toggled.connect(self.hide_finished)
        self.createTable() 

        self.layout = QVBoxLayout() 
        self.layout.setMargin(0)
        self.layout.addWidget(self.tableWidget) 
        self.layout.addWidget(self.hideFinishedCheckBox)
        self.layout.addWidget(self.startDownloadButton)
        self.layout.addWidget(self.clearDownloadListButton)
        self.setLayout(self.layout) 
      
    def createTable(self): 
  
        # File name | Progress Bar | Speed | Status | Url | File Path
        self.tableWidget.setColumnCount(6) 
        self.tableWidget.setRowCount(0)
        self.tableWidget.setHorizontalHeaderItem(0, QTableWidgetItem("File Name"))
        self.tableWidget.setHorizontalHeaderItem(1, QTableWidgetItem("Progress Bar"))
        self.tableWidget.setHorizontalHeaderItem(2, QTableWidgetItem("Speed"))
        self.tableWidget.setHorizontalHeaderItem(3, QTableWidgetItem("Status"))
        self.tableWidget.setHorizontalHeaderItem(4, QTableWidgetItem("Url"))
        self.tableWidget.setHorizontalHeaderItem(5, QTableWidgetItem("File Path"))
        #Table will fit the screen horizontally 
        self.tableWidget.horizontalHeader().setStretchLastSection(True) 
        # self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) 
        
    def addDownloadItem(self, file_name: str, file_path: str, url: str) -> int:
        row = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
        fileNameItem = QTableWidgetItem(file_name)
        fileNameItem.setFlags(Qt.ItemIsEnabled)
        progressBarItem = QTableWidgetItem("")
        progressBarItem.setFlags(Qt.ItemIsEnabled)
        downloadSpeedItem = QTableWidgetItem("0 MB/S")
        downloadSpeedItem.setFlags(Qt.ItemIsEnabled)
        downloadStatusItem = QTableWidgetItem("Pending")
        downloadStatusItem.setFlags(Qt.ItemIsEnabled)
        downloadUrlItem = QTableWidgetItem(url)
        downloadUrlItem.setFlags(Qt.ItemIsEnabled)
        filePathItem = QTableWidgetItem(file_path)
        filePathItem.setFlags(Qt.ItemIsEnabled)
        progressBar = QProgressBar()
        progressBar.setMinimum(0)
        progressBar.setMaximum(100)
        progressBar.setValue(0)
        progressBar.setAlignment(Qt.AlignCenter)
        progressBar.setFormat(str(progressBar.value()) + " %")

        self.tableWidget.setItem(row, 0, fileNameItem)
        self.tableWidget.setItem(row, 1, progressBarItem)
        self.tableWidget.setCellWidget(row, 1, progressBar)
        self.tableWidget.setItem(row, 2, downloadSpeedItem)
        self.tableWidget.setItem(row, 3, downloadStatusItem)
        self.tableWidget.setItem(row, 4, downloadUrlItem)
        self.tableWidget.setItem(row, 5, filePathItem)
        return row

    def addDownloadTask(self, file_name: str, file_path: str, url: str) -> None:
        row = self.addDownloadItem(file_name, file_path, url)
        self.task_list.append([row, file_name, file_path, url])

    def start_download(self):
        if len(self.task_list) > 0:
            task = self.task_list[0]
            self.task_list.pop(0)
            worker = DownloadWorker(self, task)
            worker.start()
    
    def clear_download_list(self):
        self.createTable()
        self.task_list.clear()
        self.signals.cancel_download.emit()

    def hide_finished(self):
        if self.hideFinishedCheckBox.isChecked():
            for row in range(0, self.tableWidget.rowCount()):
                if self.tableWidget.item(row, 3).text() == "Done":
                    self.tableWidget.hideRow(row)
        else:
            for row in range(0, self.tableWidget.rowCount()):
                self.tableWidget.showRow(row)

    @Slot(list)
    def update_progress_bar(self, message):
        row = message[0]
        value = message[1]
        self.tableWidget.cellWidget(row, 1).setValue(value)
        self.tableWidget.cellWidget(row, 1).setFormat(str(value) + " %")

    @Slot(list)
    def update_download_speed(self, message):
        row = message[0]
        value = message[1]
        self.tableWidget.item(row, 2).setText(value)

    @Slot(list)
    def update_download_status(self, message):
        row = message[0]
        value = message[1]
        self.tableWidget.item(row, 3).setText(value)

class DownloadWorker(QThread):
    def __init__(self, parent, task: list):
        QThread.__init__(self, parent)

        self.task = task
        self.row = task[0]
        self.signals = DownloadSignals()
        self.signals.progress_value.connect(parent.update_progress_bar)
        self.signals.download_speed.connect(parent.update_download_speed)
        self.signals.download_status.connect(parent.update_download_status)
        self.signals.download_next.connect(parent.start_download)
        self.signals.download_next.connect(parent.hide_finished)
        parent.signals.cancel_download.connect(self.terminate)

    def run(self):
        self.signals.download_status.emit([self.row, "Downloading"])
        self.signals.progress_value.emit([self.row, 0])

        file_path = self.task[2]
        url = self.task[3]

        headers = {'Proxy-Connection': 'keep-alive'}
        r = requests.get(url, stream=True, headers=headers)
        content_length = float(r.headers['content-length'])

        with open(file_path, 'wb') as file:
            downloaded_length = 0
            last_downloaded_length = 0
            time_start = time.time()
            for chunk in r.iter_content(chunk_size=512):
                if chunk:
                    file.write(chunk)
                    downloaded_length += len(chunk)
                    if time.time() - time_start > 1:
                        percentage = int(downloaded_length / content_length * 100)
                        self.signals.progress_value.emit([self.row, percentage])
                        speed = (downloaded_length - last_downloaded_length) / 2097152
                        self.signals.download_speed.emit([self.row, '{:.2f}'.format(speed) + 'MB/S'])
                        last_downloaded_length = downloaded_length
                        time_start = time.time()
        self.signals.progress_value.emit([self.row, 100])

        
        self.signals.download_status.emit([self.row, "Done"])
        self.signals.download_next.emit()
                

if __name__ == '__main__': 
    app = QApplication(sys.argv) 
    download_widget = FileDownloaderWidget() 
    download_widget.show()
    download_widget.addDownloadTask("Vultr", "C:\\Users\\HEIGE\\OneDrive\\Documents\\Code\\Sol\\test.bin", "https://lon-gb-ping.vultr.com/vultr.com.100MB.bin")
    download_widget.addDownloadTask("Vultr2", "C:\\Users\\HEIGE\\OneDrive\\Documents\\Code\\Sol\\test2.bin", "https://lon-gb-ping.vultr.com/vultr.com.100MB.bin")

    sys.exit(app.exec_()) 
