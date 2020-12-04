from ABook import ABook
from PySide2.QtWidgets import QWidget, QTreeWidget, QPushButton, QGridLayout, QTreeWidgetItem
from PySide2.QtGui import QImage, QStandardItem
from PySide2.QtCore import QObject, Qt, Signal
import requests
import os

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
        
        self.TreeWidget = QTreeWidget()
        self.TreeWidget.setHeaderLabels(['Name', "Course ID", "Chapter ID"])
        # self.TreeWidget.setAlternatingRowColors(True)
        self.TreeWidget.itemChanged.connect(self.checkbox_toggled)
        self.TreeWidget.doubleClicked.connect(self.get_resource_info_from_item)

        self.download_button = QPushButton("Download Selected")
        self.download_button.clicked.connect(self.download_selected)

        self.refresh_button = QPushButton("Refresh Course List")
        self.refresh_button.clicked.connect(self.refresh_course_list_tree)

        self.debug_button = QPushButton("Debug")
        self.debug_button.clicked.connect(self.debug)
    
        main_layout = QGridLayout()
        main_layout.addWidget(self.TreeWidget, 0, 0, 1, 2)
        main_layout.addWidget(self.refresh_button, 1, 0)
        main_layout.addWidget(self.download_button, 1, 1)
        # main_layout.addWidget(self.debug_button, 4, 0, 1, 1)
        main_layout.setMargin(0)
        self.setLayout(main_layout)

        if self.course_list == []:
            pass
            # self.refresh_course_list_tree()
        else:
            try:
                for index in range(len(self.course_list)):
                    self.create_tree(self.TreeWidget, self.course_list[index], 'course', index)
            except:
                pass
                # self.refresh_course_list_tree()

    def checkbox_toggled(self, node: QTreeWidgetItem, column: int):
        if node.checkState(column) == Qt.Checked:
            self.selected_list.append([node.text(0), node.text(1), node.text(2)])
        elif node.checkState(column) == Qt.Unchecked:
            if len(self.selected_list) > 1:
                self.selected_list.remove([node.text(0), node.text(1), node.text(2)])
            else:
                self.selected_list = []

    def create_item(self, node_name: str, course_id: str, chapter_id: str, has_child: bool):
        item = QTreeWidgetItem()
        item.setText(0, str(node_name))
        item.setText(1, str(course_id))
        item.setText(2, str(chapter_id))
        if has_child == True:
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
            tree_item = self.create_item(node_data['courseTitle'], node_data['courseInfoId'], None, True)
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
    
    def download_selected(self):
        for item in self.selected_list:
            if item[1] != "None" and item[2] != "None":
                download_list = self.get_resource_info(item[1], item[2])
                if download_list != None:
                    for resource in download_list:
                        download_dir, download_path, file_name = self.get_resource_path(item[1], item[2], resource["resourceInfoId"], resource["resTitle"], resource["resFileUrl"])
                        if os.path.exists(download_dir) == False:
                            os.system("mkdir \"" + download_dir + "\"")
                        # self.fileDownloadWidget.addDownloadTask(file_name, download_path, "http://abook.hep.com.cn/ICourseFiles/" + resource["resFileUrl"])
                        self.signal.addDownloadTask.emit(file_name, download_path, "http://abook.hep.com.cn/ICourseFiles/" + resource["resFileUrl"])    

    def refresh_course_list_tree(self):
        self.refresh_course_list()
        self.TreeWidget.clear()
        for index in range(len(self.course_list)):
            self.create_tree(self.TreeWidget, self.course_list[index], 'course', index)

    def get_resource_info_from_item(self):
        course_id = self.sender().currentItem().text(1)
        chapter_id = self.sender().currentItem().text(2)
        if course_id != "None" and chapter_id != "None":
            resource_list = self.get_resource_info(course_id, chapter_id)
            self.signal.clearFileListWidget.emit()
            # self.fileListWidget.clear()
            if isinstance(resource_list, list):
                for resource in resource_list:
                    res_name = resource["resTitle"]
                    url_base = "http://abook.hep.com.cn/ICourseFiles/"
                    res_file_url = url_base + resource["resFileUrl"]
                    res_logo_url = url_base + resource["picUrl"]
                    logo = requests.get(res_logo_url).content
                    res_logo = QImage()
                    res_logo.loadFromData(logo)
                    resource_item = QStandardItem(res_name)
                    resource_item.setData(res_logo, Qt.DecorationRole)
                    resource_item.setData(res_file_url, Qt.ToolTipRole)
                    resource_item.setData(res_file_url, -1)
                    # self.fileListWidget.appendRow(resource_item)
                    self.signal.appendRowFileListWidget.emit(resource_item)
    
    def debug(self):
        print(self.selected_list)