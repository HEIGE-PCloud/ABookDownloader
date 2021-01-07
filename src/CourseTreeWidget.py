from PySide2.QtCore import QObject, Qt, QThread, Signal
from PySide2.QtGui import QImage, QStandardItem
from PySide2.QtWidgets import (QGridLayout, QPushButton, QTreeWidget,
                               QTreeWidgetItem, QWidget)

from ABookCore import ABookCore
from ImportCourseWizard import ImportCourseWizard


class CourseTreeWidgetSignals(QObject):
    clearFileListWidget = Signal()
    appendRowFileListWidget = Signal(QStandardItem)
    addDownloadTask = Signal(str, str, str)


class CourseTreeWidget(QWidget, ABookCore):

    def __init__(self, path, settings, session):
        QWidget.__init__(self)
        ABookCore.__init__(self, path, settings, session)

        self.signal = CourseTreeWidgetSignals()
        self.selectedList = []

        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderLabels(['Name', "Course ID", "Chapter ID"])
        self.treeWidget.itemChanged.connect(self.checkbox_toggled)
        self.treeWidget.clicked.connect(self.loadResourceList)

        self.addDownloadTaskButton = QPushButton("Add to Downloader")
        self.addDownloadTaskButton.clicked.connect(self.addDownloadTask)

        self.importCourseButton = QPushButton("Import Courses")
        self.importCourseButton.clicked.connect(self.startImportCourseWidget)

        main_layout = QGridLayout()
        main_layout.addWidget(self.treeWidget, 0, 0, 1, 2)
        main_layout.addWidget(self.importCourseButton, 1, 0)
        main_layout.addWidget(self.addDownloadTaskButton, 1, 1)
        main_layout.setMargin(0)
        self.setLayout(main_layout)

        if settings['first_launch'] is True:
            settings['first_launch'] = False
            self.importCourseButton.click()
        else:
            self.createTreeRoot()

    def createTreeRoot(self):
        courseList = self.getCourseList()
        for course in courseList:
            courseId = course['courseInfoId']
            currentChapterList = self.getChapterList(courseId)
            self.createTree(self.treeWidget, 'course', course, currentChapterList, courseId)

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
            self.selectedList.append([node.text(0), node.text(1), node.text(2)])
        elif node.checkState(column) == Qt.Unchecked:
            if len(self.selectedList) > 1:
                self.selectedList.remove([node.text(0), node.text(1), node.text(2)])
            else:
                self.selectedList = []

    def createCourseTreeItem(self, name: str, courseId: str, chapterId: str, hasChild: bool):
        item = QTreeWidgetItem()
        item.setText(0, str(name))
        item.setText(1, str(courseId))
        item.setText(2, str(chapterId))
        if hasChild is True:
            item.setFlags(item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
        else:
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
        return item

    def addDownloadTask(self):
        for item in self.selectedList:
            if item[1] != "None" and item[2] != "None":
                courseId = item[1]
                chapterId = item[2]
                downloadList = self.getResourceList(courseId, chapterId)
                if downloadList is not None:
                    for resource in downloadList:
                        fileDir, filePath, fileName, coursePath = self.getResourcePath(
                            courseId, chapterId, resource["resourceInfoId"])
                        self.signal.addDownloadTask.emit(
                            fileName, filePath, "http://abook.hep.com.cn/ICourseFiles/" + resource["resFileUrl"])

    def startImportCourseWidget(self):
        wizard = ImportCourseWizard(self)
        wizard.show()

    def loadResourceList(self):
        # When triggered on click, first adjust the width of the column
        self.treeWidget.resizeColumnToContents(0)
        self.treeWidget.resizeColumnToContents(1)
        self.treeWidget.resizeColumnToContents(2)

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
