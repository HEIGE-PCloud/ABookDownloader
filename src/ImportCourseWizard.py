import sys
from PySide2.QtCore import QObject, QThread, Qt, Signal
from PySide2.QtWidgets import QApplication, QGridLayout, QLabel, QListWidget, QListWidgetItem, QProgressBar, QWizard, QWizardPage



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
        label = QLabel("QAQ")
        layout = QGridLayout()
        layout.addWidget(label)
        self.setLayout(layout)

class SelectCoursePage(QWizardPage):

    def __init__(self, parent=None):
        super(SelectCoursePage, self).__init__(parent)
        self.setTitle("Course")
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
        self.courseProgressBar = QProgressBar()
        self.chapterProgressBar = QProgressBar()
        self.worker = RefreshCourseListWorker(parent)
        self.worker.signals.updateCourse.connect(self.updateCourseProgressBar)
        self.worker.signals.updateChapter.connect(self.updateChapterProgressBar)
        self.worker.signals.isComplete.connect(self.updateStatus)
        self.completeStatus = False
        # self.isComplete()
        layout = QGridLayout()
        layout.addWidget(self.courseProgressBar)
        layout.addWidget(self.chapterProgressBar)
        self.setLayout(layout)

    def initializePage(self) -> None:
        self.worker.start()

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
        label = QLabel("QWQ")
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
    isComplete = Signal()
    
class RefreshCourseListWorker(QThread):

    def __init__(self, parent=None):
        super(RefreshCourseListWorker, self).__init__(parent)
        self.parent = parent
        self.signals = RefreshCourseListSignals()
    
    def run(self):
        courseList = self.parent.getCourseList()
        for i in range(len(courseList)):
            print("Updating #{} course with total {}".format(i + 1, len(courseList)))
            courseId = courseList[i]['courseInfoId']
            chapterList = self.parent.getChapterList(courseId)
            for j in range(len(chapterList)):
                print("Update #{} chapter with total {}".format(j + 1, len(chapterList)))
                self.signals.updateChapter.emit(j + 1, len(chapterList))
                chapterId = chapterList[j]['id']
                try:
                    self.parent.getResourceList(courseId, chapterId)
                except:
                    pass
            self.signals.updateCourse.emit(i + 1, len(courseList))
        self.signals.isComplete.emit()
        # self.parent.TreeWidget.clear()
        # self.parent.setDisabled(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    wizard = ImportCourseWizard()
    wizard.show()
    sys.exit(app.exec_())