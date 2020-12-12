from ABookCore import ABookCore
from PySide2.QtWidgets import QWidget, QTreeWidget, QPushButton, QGridLayout, QTreeWidgetItem
from PySide2.QtGui import QImage, QStandardItem
from PySide2.QtCore import QObject, QThread, Qt, Signal
import requests
import os

from ProgressBarDialog import ProgressBarDialog

class CourseTreeWidgetSignals(QObject):
    clearFileListWidget = Signal()
    appendRowFileListWidget = Signal(QStandardItem)
    addDownloadTask = Signal(str, str, str)

class CourseTreeWidget(QWidget, ABookCore):

    def __init__(self, path, settings, session):
        QWidget.__init__(self)
        ABookCore.__init__(self, path, settings, session)

        self.signal = CourseTreeWidgetSignals()
        self.selected_list = []
        self.pd = ProgressBarDialog(0, 100, 0, 100)

        self.TreeWidget = QTreeWidget()
        self.TreeWidget.setHeaderLabels(['Name', "Course ID", "Chapter ID"])
        self.TreeWidget.itemChanged.connect(self.checkbox_toggled)
        self.TreeWidget.clicked.connect(self.loadResourceList)

        self.download_button = QPushButton("Download Selected")
        self.download_button.clicked.connect(self.addDownloadTask)

        self.refresh_button = QPushButton("Refresh Course List")
        self.refresh_button.clicked.connect(self.refresh_course_list_tree)

        main_layout = QGridLayout()
        main_layout.addWidget(self.TreeWidget, 0, 0, 1, 2)
        main_layout.addWidget(self.refresh_button, 1, 0)
        main_layout.addWidget(self.download_button, 1, 1)
        main_layout.setMargin(0)
        self.setLayout(main_layout)

        courseList = self.getCourseList()
        for course in courseList:
            courseId = course['courseInfoId']
            currentChapterList = self.getChapterList(courseId)
            self.createTree(self.TreeWidget, 'course', course, currentChapterList, courseId)
                    
        self.TreeWidget.resizeColumnToContents(0)
        self.TreeWidget.resizeColumnToContents(1)
        self.TreeWidget.resizeColumnToContents(2)

    def createTree(self, parentItem, itemType, itemData, chapterList, courseId):
        if itemType == 'course':
            courseName = itemData['courseTitle']
            courseId = itemData['courseInfoId']
            courseItem = self.createCourseTreeItem(courseName, courseId, 'None', True)
            parentItem.addTopLevelItem(courseItem)
            childChapterList = self.getChildChapterList(chapterList, {'id': 0})
            self.createTree(courseItem, 'chapter', childChapterList, chapterList, courseId)
        elif itemType == 'chapter':
            for chapter in itemData:
                childChapterList = self.getChildChapterList(chapterList, chapter)
                chapterName = chapter['name']
                chapterId = chapter['id']
                hasChild = len(childChapterList) > 0
                chapterItem = self.createCourseTreeItem(chapterName, courseId, chapterId, hasChild)
                parentItem.addChild(chapterItem)
                if hasChild:
                    self.createTree(chapterItem, 'chapter', childChapterList, chapterList, courseId)
        else:
            raise KeyError('Wrong TODO')

    def checkbox_toggled(self, node: QTreeWidgetItem, column: int):
        if node.checkState(column) == Qt.Checked:
            self.selected_list.append([node.text(0), node.text(1), node.text(2)])
        elif node.checkState(column) == Qt.Unchecked:
            if len(self.selected_list) > 1:
                self.selected_list.remove([node.text(0), node.text(1), node.text(2)])
            else:
                self.selected_list = []

    def createCourseTreeItem(self, name: str, courseId: str, chapterId: str, hasChild: bool):
        item = QTreeWidgetItem()
        item.setText(0, str(name))
        item.setText(1, str(courseId))
        item.setText(2, str(chapterId))
        if hasChild == True:
            item.setFlags(item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
        else:
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
        return item

    def addDownloadTask(self):
        for item in self.selected_list:
            if item[1] != "None" and item[2] != "None":
                courseId = item[1]
                chapterId = item[2]
                downloadList = self.getResourceList(courseId, chapterId)
                if downloadList != None:
                    for resource in downloadList:
                        fileDir, filePath, fileName, coursePath = self.getResourcePath(courseId, chapterId, resource["resourceInfoId"])
                        os.makedirs(fileDir, exist_ok=True)
                        self.signal.addDownloadTask.emit(fileName, filePath, "http://abook.hep.com.cn/ICourseFiles/" + resource["resFileUrl"])    

    def refresh_course_list_tree(self):
        worker = RefreshCourseListWorker(self)
        self.setDisabled(True)
        self.pd.show()
        worker.start()

    def loadResourceList(self):
        # When triggered on click, first adjust the width of the column
        self.TreeWidget.resizeColumnToContents(0)
        self.TreeWidget.resizeColumnToContents(1)
        self.TreeWidget.resizeColumnToContents(2)

        # Get the course_id and chapter_id
        courseId = self.sender().currentItem().text(1)
        chapterId = self.sender().currentItem().text(2)

        # Ignore the root nodes
        if courseId != "None" and chapterId != "None":

            # Get the resource list
            # resource_list = self.get_resource_info(courseId, chapterId)
            resourceList = self.getResourceList(courseId, chapterId)
            # Clear the FileListWidget
            self.signal.clearFileListWidget.emit()
            # If resource list is not empty
            if isinstance(resourceList, list):
                # Each resource item is a QStandardItem
                # data role -1 stores the url of the resource
                # data role -2 stores the url of the preview image of the resource
                # data role Qt.TooltipRole stores the url of the resource
                # data role Qt.DecorationRole stores the preview image of the resource
                # We need to lazy load and cache the preview image so that the main thread will not be blocked
                # 1. create items without the Qt.DecorationRole and add it to resourceItemList
                # 2. pass the resource_item_list to LoadPicWorker to cache and load
                resourceItemList = []
                for resource in resourceList:
                    resName = resource["resTitle"]
                    urlBase = "http://abook.hep.com.cn/ICourseFiles/"
                    resFileUrl = urlBase + resource["resFileUrl"]
                    resourceItem = QStandardItem(resName)
                    resourceItem.setData(resFileUrl, Qt.ToolTipRole)
                    resourceItem.setData(resFileUrl, -1)
                    resourceItem.setData(resource['picUrl'], -2)
                    self.signal.appendRowFileListWidget.emit(resourceItem)
                    resourceItemList.append(resourceItem)
                loadPicWorker = LoadPicWorker(resourceItemList, self)
                loadPicWorker.start()

class LoadPicWorker(QThread):

    def __init__(self, resourceItemList, parent=None) -> None:
        super(LoadPicWorker, self).__init__(parent)
        self.resourceItemList = resourceItemList
        self.urlBase = "http://abook.hep.com.cn/ICourseFiles/"
        self.parent = parent

    def run(self) -> None:
        for resourceItem in self.resourceItemList:
            # Read the url of the picture and the name of the pic
            picUrl = resourceItem.data(-2)
            picName = picUrl[picUrl.rfind('/') + 1:]
            cachePath = './temp/QImageCache/{}'.format(picName)
            if cachePath in self.parent.cache:
                resPic = self.parent.cache[cachePath]
            else:
                pic = self.parent.get('pic', [picUrl, picName])
                resPic = QImage()
                resPic.loadFromData(pic)
                self.parent.cache[cachePath] = resPic
            resourceItem.setData(resPic, Qt.DecorationRole)

class RefreshCourseListWorker(QThread):

    def __init__(self, parent=None):
        super(RefreshCourseListWorker, self).__init__(parent)
        self.parent = parent
    
    def run(self):
        courseList = self.parent.getCourseList()
        for i in range(len(courseList)):
            print("Updating #{} course with total {}".format(i + 1, len(courseList)))
            courseId = courseList[i]['courseInfoId']
            chapterList = self.parent.getChapterList(courseId)
            for j in range(len(chapterList)):
                print("Update #{} chapter with total {}".format(j + 1, len(chapterList)))
                chapterId = chapterList[j]['id']
                try:
                    self.parent.getResourceList(courseId, chapterId)
                except:
                    pass

        # self.parent.TreeWidget.clear()
        self.parent.setDisabled(False)