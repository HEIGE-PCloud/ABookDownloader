import os
import sys
import json
import logging
import requests

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
from UserLoginDialog import UserLoginDialog
from Settings import Settings
from FileDownloader import *


class ABook(object):
    def __init__(self, path: str, settings: Settings, user: UserLoginDialog):
        super().__init__()
        self.settings = settings
        self.session = user.session
        self.path = path

        self.course_list = []
        self.course_list_path = '{}course_list({}).json'.format(self.path, user.user_info['loginUser.loginName'])
        

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

if __name__ == "__main__":
    pass