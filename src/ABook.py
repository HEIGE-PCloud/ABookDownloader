import os
import sys
import json
import logging
from PySide2.QtCore import QObject, Signal
from PySide2.QtWidgets import QApplication
import requests

from UserLoginDialog import UserLoginDialog
from Settings import Settings

class RefreshCourseListSignals(QObject):
    courseSignal = Signal(int, int)
    chapterSignal = Signal(str, int, int)


class ABook(object):
    def __init__(self, path: str, settings: Settings, user: UserLoginDialog):
        super().__init__()
        self.settings = settings
        self.session = user.session
        self.user = user
        self.path = path
        self.cache = {}
        self.courseListUrl = "http://abook.hep.com.cn/selectMyCourseList.action?mobile=true&cur={}"
        self.chapterListUrl = "http://abook.hep.com.cn/resourceStructure.action?courseInfoId={}"
        self.resourceListUrl = "http://abook.hep.com.cn/courseResourceList.action?courseInfoId={}&treeId={}&cur={}"
        self.course_list = []
        self.course_list_path = '{}course_list({}).json'.format(self.path, user.user_info['loginUser.loginName'])
        self.refresh_course_list_signals = RefreshCourseListSignals()        

        if os.path.exists(self.course_list_path):
            with open(self.course_list_path, 'r', encoding='utf-8') as file:
                self.course_list = json.load(file)

    # Interfaces:
    # refresh(): get all courses and chapter information again
    # getCourseList(): return all courses' name and id in a list [{'course_id': course_id, 'course_name': course_name}]
    # getChapterList(course_id): return all chapters' name and id in a list [{'chapter_id': chapter_id, 'chapter_name': chapter_name}]
    # getResList(course_id, chapter_id): return all information of the downloadable resources in a chapter in a list
    # getResPath()

    def get(self, type, content):
        if type == 'courseList':
            urlBase = self.courseListUrl
            cur = content
            username = self.user.user_info['loginUser.loginName']
            cachePath = './temp/courseList({})({}).json'.format(username, cur)
            return self.getData(cachePath, urlBase, [cur])
            # if os.path.exists(cachePath):
            #     return self.load_json_from_file(cachePath)
            # else:
            #     data = self.session.get(urlBase.format(cur)).json()
            #     self.save_json_to_file(cachePath, data)
            #     return data

        elif type == 'chapterList':
            urlBase = self.chapterListUrl
            courseId = content
            cachePath = './temp/chapterList({}).json'.format(courseId)
            return self.getData(cachePath, urlBase, [courseId])
            # if os.path.exists(cachePath):
            #     return self.load_json_from_file(cachePath)
            # else:
            #     data = self.session.get(urlBase.format(courseId)).json()
            #     self.save_json_to_file(cachePath, data)
            #     return data

        elif type == 'resourceList':
            urlBase = self.resourceListUrl
            courseId = content[0]
            chapterId = content[1]
            cur = content[2]
            cachePath = './temp/resourceList({})({})({}).json'.format(courseId, chapterId, cur)
            return self.getData(cachePath, urlBase, [courseId, chapterId, cur])
            # if os.path.exists(cachePath):
            #     return self.load_json_from_file(cachePath)
            # else:
            #     data = self.session.get(urlBase.format(courseId, chapterId, cur)).json()
            #     self.save_json_to_file(cachePath, data)
            #     return data
        else:
            raise IndexError('Wrong! TODO')

    def getData(self, cachePath: str, urlBase: str, urlArgs: list):
        if cachePath in self.cache:
            return self.cache[cachePath]
        elif os.path.exists(cachePath):
            data = self.load_json_from_file(cachePath)
            self.cache[cachePath] = data
            return data
        else:
            data = self.session.get(urlBase.format(*urlArgs)).json()
            self.cache[cachePath] = data
            self.save_json_to_file(cachePath, data)
            return data

    def getCourseList(self):
        cur = 1
        courseList = []
        courseListPage = self.get('courseList', str(cur))
        for course in courseListPage[0]['myMobileCourseList']:
            courseList.append(course)
        while courseListPage[0]['page']['pageCount'] > cur:
            cur += 1
            courseListPage = self.get('courseList', str(cur))
            for course in courseListPage[0]['myMobileCourseList']:
                courseList.append(course)
        return courseList
        
    def getChapterList(self, courseId):
        chapterList = self.get('chapterList', courseId)
        return chapterList

    def getResourceList(self, courseId, chapterId):
        cur = 1
        resourceList = []
        resourceListPage = self.get('resourceList', [courseId, chapterId, cur])
        for resource in resourceListPage[0]['myMobileResourceList']:
            resourceList.append(resource)
        while resourceListPage[0]['page']['pageCount'] > cur:
            cur += 1
            resourceListPage = self.get('resourceList', str(cur))
            for resource in resourceListPage[0]['myMobileResourceList']:
                resourceList.append(resource)
        return resourceList

    def getCourse(self, courseId):
        courseList = self.getCourseList()
        for course in courseList:
            if course['courseInfoId'] == courseId:
                return course
    def getChapter(self, courseId, chapterId):
        chapterList = self.getChapterList(courseId)
        for chapter in chapterList:
            if chapter['id'] == chapterId:
                return chapter

    def getResource(self, courseId, chapterId, resourceId):
        resourceList = self.getResourceList(courseId, chapterId)
        for resource in resourceList:
            if resource['resourceInfoId'] == resourceId:
                return resource

    def getChildChapterList(self, chapterList, rootChapter):
        childChapter = []
        for chapter in chapterList:
            if chapter['pId'] == rootChapter['id']:
                childChapter.append(chapter)
        return childChapter

    def getResourcePath(self, courseId, chapterId, resourceId):
        courseName = self.getCourse(courseId)['courseTitle']
        chapter = self.getChapter(courseId, chapterId)
        chapterPid = chapter['pId']
        chapterName = chapter['name']
        resource = self.getResource(courseId, chapterId, resourceId)
        resourceName = resource['resTitle']
        resourceUrl = resource['resFileUrl']
        resourceType = resourceUrl[resourceUrl.find('.'):]
        # print(chapterPid)
        # print(type(chapterPid))
        while chapterPid != 0:
            chapter = self.getChapter(courseId, chapterPid)
            chapterName = chapter['name'] + '/' + chapterName
            chapterPid = chapter['pId']
        downloadPath = self.settings['download_path']
        dirPath = downloadPath + courseName + '/' + chapterName + '/'
        filePath = dirPath + resourceName + resourceType
        return (dirPath, filePath, resourceName)
        # print(courseName)
        # print(chapterName)
        # print(resourceName)
        # print(resourceType)


    def refresh_course_list(self):
        self.get_courses_info()
        
        for index in range(len(self.course_list)):
            print("Fetching course #{} as total of {} course(s).".format(index + 1, len(self.course_list)))
            self.refresh_course_list_signals.courseSignal.emit(index + 1, len(self.course_list))
            self.get_chapter_info(index)

        self.save_json_to_file(self.course_list_path, self.course_list)

    def get_courses_info(self):

        courseListUrl = "http://abook.hep.com.cn/selectMyCourseList.action?mobile=true&cur=1"
        self.course_list = self.session.get(courseListUrl).json()

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
            self.refresh_course_list_signals.chapterSignal.emit(course_id, chapter_index + 1, len(chapter_list))
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
        return (self.settings['download_path'] + course_name + '/' + chapter_name + '/', self.settings['download_path'] + course_name + '/' + chapter_name + '/' + resource_name, resource_name)

    def save_json_to_file(self, path, data):
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def load_json_from_file(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    
if __name__ == "__main__":
    settings = Settings('./temp/settings.json')
    app = QApplication()
    user = UserLoginDialog()
    user.exec_()
    if user.login_status == False:
        exit(0)
    abook = ABook('./temp/', settings, user)
    # courseList = abook.getCourseList()
    # print(len(courseList))
    # print(courseList[0])

    # chapterList = abook.getChapterList(5000003293)

    # resourceList = abook.getResourceList(5000003293, 5000343805)
    # print(resourceList)

    # abook.getResourcePath(5000003293, 5000343805, 5000295100)



