import sys

from PySide2.QtCore import QObject, Qt, QThread, Signal
from PySide2.QtWidgets import (QApplication, QGridLayout, QLabel, QListWidget,
                               QListWidgetItem, QProgressBar, QWizard,
                               QWizardPage)


class ImportCourseWizard(QWizard):

    def __init__(self, parent=None):
        super(ImportCourseWizard, self).__init__(parent)
        self.addPage(StartPage(parent))
        self.addPage(SelectCoursePage(parent))
        self.addPage(ImportPage(parent))
        self.addPage(EndPage(parent))
        self.setWindowFlag(Qt.WindowStaysOnTopHint)


class StartPage(QWizardPage):

    def __init__(self, parent=None):
        super(StartPage, self).__init__(parent)
        self.setTitle("Start")
        label = QLabel("Click next to continue")
        layout = QGridLayout()
        layout.addWidget(label)
        self.setLayout(layout)


class SelectCoursePage(QWizardPage):

    def __init__(self, parent=None):
        super(SelectCoursePage, self).__init__(parent)
        self.setTitle("Courses")
        self.courseList = parent.getCourseList()
        self.courseListWidget = QListWidget()
        # self.courseListWidget.setDisabled(True)
        layout = QGridLayout()
        layout.addWidget(self.courseListWidget)
        self.setLayout(layout)

    def initializePage(self) -> None:
        for course in self.courseList:
            courseItem = QListWidgetItem()
            courseItem.setText(course['courseTitle'])
            courseItem.setData(-1, course)
            # courseItem.setFlags(courseItem.flags() | Qt.ItemIsUserCheckable)
            # courseItem.setCheckState(Qt.Checked)
            self.courseListWidget.addItem(courseItem)


class ImportPage(QWizardPage):

    def __init__(self, parent=None):
        super(ImportPage, self).__init__(parent)
        self.setTitle("Importing")
        self.courseProgressLabel = QLabel("Pending")
        self.chapterProgressLabel = QLabel("Pending")
        self.courseProgressBar = QProgressBar()
        self.chapterProgressBar = QProgressBar()
        self.worker = RefreshCourseListWorker(parent)
        self.worker.signals.updateCourseLabel.connect(self.updateCourseLabel)
        self.worker.signals.updateChapterLabel.connect(self.updateChapterLabel)
        self.worker.signals.updateCourse.connect(self.updateCourseProgressBar)
        self.worker.signals.updateChapter.connect(self.updateChapterProgressBar)
        self.worker.signals.isComplete.connect(self.updateStatus)
        self.completeStatus = False
        layout = QGridLayout()
        layout.addWidget(self.courseProgressLabel)
        layout.addWidget(self.courseProgressBar)
        layout.addWidget(self.chapterProgressLabel)
        layout.addWidget(self.chapterProgressBar)
        self.setLayout(layout)

    def initializePage(self) -> None:
        self.worker.start()

    def updateCourseLabel(self, value: str):
        self.courseProgressLabel.setText(value)

    def updateChapterLabel(self, value: str):
        self.chapterProgressLabel.setText(value)

    def updateCourseProgressBar(self, value: int, total: int):
        self.courseProgressBar.setMaximum(total)
        self.courseProgressBar.setValue(value)

    def updateChapterProgressBar(self, value: int, total: int):
        self.chapterProgressBar.setMaximum(total)
        self.chapterProgressBar.setValue(value)

    def isComplete(self) -> bool:
        print(self.completeStatus)
        return self.completeStatus

    def updateStatus(self):
        print("update {}".format(self.completeStatus))
        self.completeStatus = True
        self.completeChanged.emit()


class EndPage(QWizardPage):

    def __init__(self, parent=None):
        super(EndPage, self).__init__(parent)
        self.setTitle("End")
        label = QLabel("All courses are successfully imported. Click Finish to continue.")
        layout = QGridLayout()
        layout.addWidget(label)
        self.setLayout(layout)
        self.parent = parent

    def initializePage(self) -> None:
        self.parent.treeWidget.clear()
        self.parent.createTreeRoot()


class RefreshCourseListSignals(QObject):
    updateCourse = Signal(int, int)
    updateChapter = Signal(int, int)
    updateCourseLabel = Signal(str)
    updateChapterLabel = Signal(str)
    isComplete = Signal()


class RefreshCourseListWorker(QThread):

    def __init__(self, parent=None):
        super(RefreshCourseListWorker, self).__init__(parent)
        self.parent = parent
        self.signals = RefreshCourseListSignals()

    def run(self):
        courseList = self.parent.getCourseList()
        for i in range(len(courseList)):
            courseId = courseList[i]['courseInfoId']
            chapterList = self.parent.getChapterList(courseId)
            for j in range(len(chapterList)):
                print("Updated chapter {}/{}".format(j + 1, len(chapterList)))
                self.signals.updateChapterLabel.emit("Updated chapter {}/{}".format(j + 1, len(chapterList)))
                self.signals.updateChapter.emit(j + 1, len(chapterList))
                chapterId = chapterList[j]['id']
                self.parent.getResourceList(courseId, chapterId)
            print("Updated course {}/{}".format(i + 1, len(courseList)))
            self.signals.updateCourseLabel.emit("Updated course {}/{}".format(i + 1, len(courseList)))
            self.signals.updateCourse.emit(i + 1, len(courseList))
        self.signals.isComplete.emit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wizard = ImportCourseWizard()
    wizard.show()
    sys.exit(app.exec_())
