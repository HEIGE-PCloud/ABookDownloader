import os
import sys
import json
import logging
import requests

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
from UserLogin import UserLoginDialog
from Settings import Settings
from FileDownloader import *


class ABook(object):
    def __init__(self, path: str, settings: Settings, user: UserLoginDialog):
        super().__init__()
        self.settings = settings
        self.session = user.login_worker.session
        self.path = path

        self.course_list = []
        self.course_list_path = '{}course_list({}).json'.format(self.path, user.login_worker.user_info['loginUser.loginName'])
        

        if os.path.exists(self.course_list_path):
            with open(self.course_list_path, 'r', encoding='utf-8') as file:
                self.course_list = json.load(file)
        # else:
        #     self.refresh_course_list()

    def run(self):
        self.refresh_course_list()

    def refresh_course_list(self):
        self.get_courses_info()
        
        for index in range(len(self.course_list)):
            print("Fetching course #{} as total of {} course(s).".format(index + 1, len(self.course_list)))
            self.get_chapter_info(index)

        self.save_json_to_file(self.course_list_path, self.course_list)

    def get_courses_info(self):

        course_list_url = "http://abook.hep.com.cn/selectMyCourseList.action?mobile=true&cur=1"
        self.course_list = self.session.get(course_list_url).json()

        try:
            self.course_list = self.course_list[0]['myMobileCourseList']
            logging.info("Courses info fetched!")
        except:
            pass

    def get_chapter_info(self, index):
        course_id = self.course_list[index]['courseInfoId']        
        course_url = 'http://abook.hep.com.cn/resourceStructure.action?courseInfoId={}'.format(course_id)
        chapter_list = self.session.post(course_url).json()
        for chapter_index in range(len(chapter_list)):
            print("Course: {}. Fetching chapter #{} as total of {} chapter(s).".format(course_id, chapter_index + 1, len(chapter_list)))
            resource_url = "http://abook.hep.com.cn/courseResourceList.action?courseInfoId={}&treeId={}&cur=1".format(course_id, chapter_list[chapter_index]['id'])
            resource_list = self.session.post(resource_url).json()
            try:
                resource_list = resource_list[0]["myMobileResourceList"]
            except:
                resource_list = None
            chapter_list[chapter_index]['resource'] = resource_list
        self.course_list[index]['chapter'] = chapter_list

    def get_resource_info(self, course_id: str, chapter_id: str):
        resource_list = self.course_list
        for course in resource_list:
            if str(course["courseInfoId"]) == course_id:
                resource_list = course["chapter"]
                break
        for chapter in resource_list:
            if str(chapter["id"]) == chapter_id:
                resource_list = chapter["resource"]
                break
        return resource_list

    def get_resource_path(self, course_id: str, chapter_id: str, resource_id: str, resource_name: str, resource_url: str):
        resource = self.course_list
        course_name = ""
        chapter_name = ""
        resource_name += resource_url[str(resource_url).find('.'):]
        for course in resource:
            if str(course["courseInfoId"]) == course_id:
                course_name = course["courseTitle"]
                resource = course["chapter"]                
                break
        chapter_pid = "0"
        for chapter in resource:
            if str(chapter["id"]) == chapter_id:
                chapter_pid = str(chapter["pId"])
                chapter_name = chapter["name"] + chapter_name
                break

        while chapter_pid != "0":
            chapter_id = chapter_pid
            for chapter in resource:
                if str(chapter["id"]) == chapter_id:
                    chapter_pid = str(chapter["pId"])
                    chapter_name = chapter["name"] + "/" + chapter_name
        # print(self.settings.settings['download_path'] + course_name + '/' + chapter_name + '/' + resource_name)
        return (self.settings.settings['download_path'] + course_name + '/' + chapter_name + '/', self.settings.settings['download_path'] + course_name + '/' + chapter_name + '/' + resource_name, resource_name)

    def save_json_to_file(self, path, data):
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

class CourseTreeWidget(QtWidgets.QWidget, ABook):

    def __init__(self, path, settings, session):
        QtWidgets.QWidget.__init__(self)
        ABook.__init__(self, path, settings, session)
        self.selected_list = []
        
        self.TreeWidget = QtWidgets.QTreeWidget()
        self.TreeWidget.setHeaderLabels(['Name', "Course ID", "Chapter ID"])
        # self.TreeWidget.setAlternatingRowColors(True)
        self.TreeWidget.itemChanged.connect(self.checkbox_toggled)
        self.TreeWidget.doubleClicked.connect(self.get_resource_info_from_item)

        self.download_button = QtWidgets.QPushButton("Download Selected")
        self.download_button.clicked.connect(self.download_selected)

        self.refresh_button = QtWidgets.QPushButton("Refresh Course List")
        self.refresh_button.clicked.connect(self.refresh_course_list_tree)

        self.debug_button = QtWidgets.QPushButton("Debug")
        self.debug_button.clicked.connect(self.debug)

        self.ListView = QtWidgets.QListView()
        # self.ListView.setViewMode(QtWidgets.QListView.IconMode)
        self.resource_list = QtGui.QStandardItemModel()
        self.ListView.setModel(self.resource_list)
        self.ListView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ListView.doubleClicked.connect(self.open_resource)

        # os.path.abspath(self.settings["download_path"])
        print(QDir.currentPath())
        tree_view = QTreeView()
        filesystem_model = QFileSystemModel(tree_view)
        filesystem_model.setRootPath(os.path.abspath(self.settings["download_path"]))
        tree_view.setModel(filesystem_model)
        tree_view.setRootIndex(filesystem_model.index(os.path.abspath(self.settings["download_path"])))

        self.fileDownloadWidget = FileDownloaderWidget()
        main_layout = QtWidgets.QGridLayout()
        main_layout.addWidget(self.TreeWidget, 0, 0, 1, 2)
        main_layout.addWidget(self.ListView, 0, 2, 1, 2)
        main_layout.addWidget(tree_view, 1, 0, 1, 2)
        main_layout.addWidget(self.fileDownloadWidget, 1, 2, 1, 2)
        main_layout.addWidget(self.refresh_button, 2, 0, 1, 1)
        main_layout.addWidget(self.download_button, 3, 0, 1, 1)
        main_layout.addWidget(self.debug_button, 4, 0, 1, 1)
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

    def checkbox_toggled(self, node: QtWidgets.QTreeWidgetItem, column: int):
        if node.checkState(column) == QtCore.Qt.Checked:
            self.selected_list.append([node.text(0), node.text(1), node.text(2)])
        elif node.checkState(column) == QtCore.Qt.Unchecked:
            if len(self.selected_list) > 1:
                self.selected_list.remove([node.text(0), node.text(1), node.text(2)])
            else:
                self.selected_list = []

    def create_item(self, node_name: str, course_id: str, chapter_id: str, has_child: bool):
        item = QtWidgets.QTreeWidgetItem()
        item.setText(0, str(node_name))
        item.setText(1, str(course_id))
        item.setText(2, str(chapter_id))
        if has_child == True:
            item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
        else:
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(0, QtCore.Qt.Unchecked)
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
                        self.fileDownloadWidget.addDownloadTask(file_name, download_path, "http://abook.hep.com.cn/ICourseFiles/" + resource["resFileUrl"])
                    
    
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
            self.resource_list.clear()
            if isinstance(resource_list, list):
                for resource in resource_list:
                    res_name = resource["resTitle"]
                    url_base = "http://abook.hep.com.cn/ICourseFiles/"
                    res_file_url = url_base + resource["resFileUrl"]
                    res_logo_url = url_base + resource["picUrl"]
                    logo = requests.get(res_logo_url).content
                    res_logo = QtGui.QImage()
                    res_logo.loadFromData(logo)
                    resource_item = QtGui.QStandardItem(res_name)
                    resource_item.setData(res_logo, QtCore.Qt.DecorationRole)
                    resource_item.setData(res_file_url, QtCore.Qt.ToolTipRole)
                    self.resource_list.appendRow(resource_item)

    def open_resource(self):
        item = self.resource_list.itemFromIndex(self.sender().currentIndex())
        url = item.data(QtCore.Qt.ToolTipRole)
        os.system("explorer " + url)
    
    def debug(self):
        print(self.selected_list)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, path, settings, session):
        QtWidgets.QMainWindow.__init__(self)
        course_tree_widget = CourseTreeWidget(path, settings, session)


        self.statusBar().showMessage('Here is the status bar')

        self.init_menubar()

        self.setCentralWidget(course_tree_widget)

        self.setWindowTitle("ABookDownloader Dev")
        self.resize(1920, 1080)

    def init_menubar(self):
        exitAction = QtWidgets.QAction('Exit', self)
        exitAction.setShortcut('Alt+F4')
        exitAction.setStatusTip('Quit')
        exitAction.triggered.connect(self.close)
        
        aboutAction = QtWidgets.QAction('About', self)
        aboutAction.setStatusTip('About')
        
        
        self.menuBar().setNativeMenuBar(True)
        fileMenu = self.menuBar().addMenu('About')
        fileMenu.addAction(exitAction)

        # aboutMenu = self.menuBar().addMenu("&About")
        aboutQtAct = QtWidgets.QAction("About &Qt", self, triggered=qApp.aboutQt)
        fileMenu.addAction(aboutQtAct)

    def about_msgbox(self):
        QtWidgets.QMessageBox()


if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QtWidgets.QApplication(os.sys.argv)
    user = UserLoginDialog()
    settings = Settings('./temp/settings.json')
    abook = MainWindow('./temp/', settings, user)
    abook.show()
    sys.exit(app.exec_())
