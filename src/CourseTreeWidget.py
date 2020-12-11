from json import load
from ABook import ABook
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

class CourseTreeWidget(QWidget, ABook):

    def __init__(self, path, settings, session):
        QWidget.__init__(self)
        ABook.__init__(self, path, settings, session)

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

        # if self.course_list == []:
        #     pass
        #     # self.refresh_course_list_tree()
        # else:
        #     try:
                # for index in range(len(self.course_list)):
                #     self.createTree(self.TreeWidget, self.course_list[index], 'course', index)
        courseList = self.getCourseList()
        for course in courseList:
            # courseName = course['courseTitle']
            # courseId = course['courseInfoId']
            # courseItem = self.createCourseTreeItem(courseName, courseId, 'None', True)
            # self.createTree(self.TreeWidget, 'course')
            # self.TreeWidget.addTopLevelItem(courseItem)
            courseId = course['courseInfoId']
            currentChapterList = self.getChapterList(courseId)
            self.createTree(self.TreeWidget, 'course', course, currentChapterList, courseId)
                    
            # except:
            #     pass
                # self.refresh_course_list_tree()
        self.TreeWidget.resizeColumnToContents(0)
        self.TreeWidget.resizeColumnToContents(1)
        self.TreeWidget.resizeColumnToContents(2)
        # self.setContextMenuPolicy(Qt.ActionsContextMenu)
        # action = QAction(self.TreeWidget)
        # action.setText('qwq')
        # self.TreeWidget.addAction(action)
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
                    self.createTree(chapterItem, 'course', childChapterList, chapterList, courseId)
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

    def child(self, chapter_list, parrent_chapter):
        child_chapter = []
        for chapter in chapter_list:
            if chapter['pId'] == parrent_chapter['id']:
                child_chapter.append(chapter)
        return child_chapter
            
    def create_tree(self, parent_node, node_data, node_type, course_index):
        if node_type == 'course':
            tree_item = self.createCourseTreeItem(node_data['courseTitle'], node_data['courseInfoId'], None, True)
            parent_node.addTopLevelItem(tree_item)
            root_chapter = {'id': 0}
            child_chapter = self.child(self.course_list[course_index]['chapter'], root_chapter)
            self.create_tree(tree_item, child_chapter, 'chapter', course_index)
        elif node_type == 'chapter':
            for item in node_data:
                child_chapter = self.child(self.course_list[course_index]['chapter'], item)
                tree_item = self.create_item(item['name'], self.course_list[course_index]['courseInfoId'], item['id'], len(child_chapter) > 0)
                parent_node.addChild(tree_item)
                if len(child_chapter) > 0:
                    self.create_tree(tree_item, child_chapter, 'chapter', course_index)
    
    def addDownloadTask(self):
        for item in self.selected_list:
            if item[1] != "None" and item[2] != "None":
                # download_list = self.get_resource_info(item[1], item[2])
                courseId = item[1]
                chapterId = item[2]
                downloadList = self.getResourceList(courseId, chapterId)
                if downloadList != None:
                    for resource in downloadList:
                        # fileDir, filePath, fileName = self.get_resource_path(item[1], item[2], resource["resourceInfoId"], resource["resTitle"], resource["resFileUrl"])
                        fileDir, filePath, fileName = self.getResourcePath(courseId, chapterId, resource["resourceInfoId"])
                        if os.path.exists(fileDir) == False:
                            os.mkdir(fileDir)
                            # os.system("mkdir \"" + fileDir + "\"")
                        self.signal.addDownloadTask.emit(fileName, filePath, "http://abook.hep.com.cn/ICourseFiles/" + resource["resFileUrl"])    

    def refresh_course_list_tree(self):
        worker = RefreshCourseListWorker(self)
        print("qwq")
        self.setDisabled(True)
        self.pd.show()
        worker.start()
        # self.refresh_course_list()
        # self.TreeWidget.clear()
        # for index in range(len(self.course_list)):
        #     self.create_tree(self.TreeWidget, self.course_list[index], 'course', index)

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
                # 1. create items without the Qt.DecorationRole and add it to resource_item_list
                # 2. pass the resource_item_list to LoadPicWorker to cache and load
                resourceItemList = []
                for resource in resourceList:
                    res_name = resource["resTitle"]
                    urlBase = "http://abook.hep.com.cn/ICourseFiles/"
                    resFileUrl = urlBase + resource["resFileUrl"]
                    resourceItem = QStandardItem(res_name)
                    resourceItem.setData(resFileUrl, Qt.ToolTipRole)
                    resourceItem.setData(resFileUrl, -1)
                    resourceItem.setData(resource['picUrl'], -2)
                    self.signal.appendRowFileListWidget.emit(resourceItem)
                    resourceItemList.append(resourceItem)
                loadPicWorker = LoadPicWorker(resourceItemList, self)
                loadPicWorker.start()

class LoadPicWorker(QThread):

    def __init__(self, resource_item_list, parent=None) -> None:
        super(LoadPicWorker, self).__init__(parent)
        self.resource_item_list = resource_item_list
        self.url_base = "http://abook.hep.com.cn/ICourseFiles/"

    def run(self) -> None:
        for resource_item in self.resource_item_list:
            # Read the url of the picture and the name of the logo
            pic_url = resource_item.data(-2)
            logo_name = pic_url[pic_url.rfind('/') + 1:]
            # Check if it has been cached before
            if os.path.exists('./temp/cache/{}'.format(logo_name)):
                with open('./temp/cache/{}'.format(logo_name), 'rb') as file:
                    logo = file.read()
            else:
                # Get and save the picture
                res_logo_url = self.url_base + pic_url
                logo = requests.get(res_logo_url).content
                with open('./temp/cache/{}'.format(logo_name), 'wb') as file:
                    file.write(logo)
            # Set the image for Qt.DecorationRole
            res_logo = QImage()
            res_logo.loadFromData(logo)
            resource_item.setData(res_logo, Qt.DecorationRole)

class RefreshCourseListWorker(QThread):

    def __init__(self, parent=None):
        super(RefreshCourseListWorker, self).__init__(parent)
        self.parent = parent
    
    def run(self):
        pass
        self.parent.refresh_course_list_signals.courseSignal.connect(self.handleCourseSignal)
        self.parent.refresh_course_list_signals.chapterSignal.connect(self.handleChapterSignal)
        self.parent.refresh_course_list()
        self.parent.pd.close()
        self.parent.TreeWidget.clear()
        for index in range(len(self.parent.course_list)):
            self.parent.create_tree(self.parent.TreeWidget, self.parent.course_list[index], 'course', index)
        self.parent.setDisabled(False)


    def handleCourseSignal(self, cur: int, max: int):
        self.parent.pd.setValue_1(cur)
        self.parent.pd.setMaximum_1(max)

    def handleChapterSignal(self, name: str, cur: int, max: int):
        self.parent.pd.setValue_2(cur)
        self.parent.pd.setMaximum_2(max)