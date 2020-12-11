import os
import json
import logging
from PySide2.QtWidgets import QApplication

from UserLoginDialog import UserLoginDialog
from Settings import Settings

class ABookCore(object):
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

    def getData(self, cachePath: str, urlBase: str, urlArgs: list):
        """
        GetData() takes three inputs: cachePath, urlBase and urlArgs.
        getData() will first try to get data from variable self.cache,
        self.cache is a dict type variable, and the cachePath acts as the key.
        If the data is not cached in the memory, getData() will then try to
        find the data on local file at the cachePath.
        If there is no local cache, getData() will visit the url you pass.
        It will generate the url by url = urlbase.format(*urlArgs) so you can
        pass some Args into it.
        """
        
        # Check the memory cache first
        if cachePath in self.cache:
            return self.cache[cachePath]
        
        # If not in memory cache, then check the local file 
        if os.path.exists(cachePath):
            # If the local json file is broken, then fallback to web api
            try:
                data = self.loadJsonFromFile(cachePath)
                self.cache[cachePath] = data
                return data
            except:
                pass

        # If nothing is working correctly, use the web api
        data = self.session.get(urlBase.format(*urlArgs)).json()
        self.cache[cachePath] = data
        try:
            self.saveJsonToFile(cachePath, data)
        except:
            pass

        return data

    def get(self, type, argv):
        """
        get() function returns courseList/chapterList/resourceList.
        The 'type' is an str used to identify the type of data.
        The 'argv' is an str or a list based on the type of data you request
        For courseList
            type = 'courseList'
            argv = cur
        For chapterList
            type = 'chapterList'
            argv = courseId
        for resourceList
            type = 'resourceList'
            argv = [courseId, chapterId, cur]
        """

        if type == 'courseList':
            urlBase = self.courseListUrl
            cur = argv
            username = self.user.user_info['loginUser.loginName']
            cachePath = './temp/jsonCache/courseList({})({}).json'.format(username, cur)
            return self.getData(cachePath, urlBase, [cur])

        elif type == 'chapterList':
            urlBase = self.chapterListUrl
            courseId = argv
            cachePath = './temp/jsonCache/chapterList({}).json'.format(courseId)
            return self.getData(cachePath, urlBase, [courseId])

        elif type == 'resourceList':
            urlBase = self.resourceListUrl
            courseId = argv[0]
            chapterId = argv[1]
            cur = argv[2]
            cachePath = './temp/jsonCache/resourceList({})({})({}).json'.format(courseId, chapterId, cur)
            return self.getData(cachePath, urlBase, [courseId, chapterId, cur])

        else:
            raise IndexError("Wrong Index! Only 'courseList', 'chapterList', 'resourceList' are accepted.")

    def getCourseList(self):
        """
        getCourseList() returns the courseList of the current user.
        """
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
        """
        getChapterList() returns the chapterList under the courseId
        """
        chapterList = self.get('chapterList', courseId)
        return chapterList

    def getResourceList(self, courseId, chapterId):
        """
        getResourceList() returns the resourceList under the courseId and ChapterId
        """
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
        """
        getCourse() returns the course with courseId
        """
        courseList = self.getCourseList()
        for course in courseList:
            if course['courseInfoId'] == courseId:
                return course
                
    def getChapter(self, courseId, chapterId):
        """
        getChapter() returns the chapter under courseId with chapterId
        """
        chapterList = self.getChapterList(courseId)
        for chapter in chapterList:
            if chapter['id'] == chapterId:
                return chapter

    def getResource(self, courseId, chapterId, resourceId):
        """
        getResource() returns the resource under courseId and chapterId
        with resourceId 
        """
        resourceList = self.getResourceList(courseId, chapterId)
        for resource in resourceList:
            if resource['resourceInfoId'] == resourceId:
                return resource

    def getChildChapterList(self, chapterList, rootChapter):
        """
        getChildChapterList() takes a chapterList and a rootChapter
        and it returns all child chapters of the rootChapter as a list
        """
        childChapter = []
        for chapter in chapterList:
            if chapter['pId'] == rootChapter['id']:
                childChapter.append(chapter)
        return childChapter

    def getResourcePath(self, courseId, chapterId, resourceId):
        """
        getResourcePath() calculates the file system path to the download
        resource
        It takes courseId, chapterId, resourceId and returns (the directory
        of the file, the path of the file, the file name) as a tuple
        """
        courseName = self.getCourse(courseId)['courseTitle']
        chapter = self.getChapter(courseId, chapterId)
        chapterPid = chapter['pId']
        chapterName = chapter['name']
        resource = self.getResource(courseId, chapterId, resourceId)
        resourceName = resource['resTitle']
        resourceUrl = resource['resFileUrl']
        resourceType = resourceUrl[resourceUrl.find('.'):]
        while chapterPid != 0:
            chapter = self.getChapter(courseId, chapterPid)
            chapterName = chapter['name'] + '/' + chapterName
            chapterPid = chapter['pId']
        downloadPath = self.settings['download_path']
        dirPath = downloadPath + courseName + '/' + chapterName + '/'
        filePath = dirPath + resourceName + resourceType
        return (dirPath, filePath, resourceName)

    def saveJsonToFile(self, path, data):
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def loadJsonFromFile(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    
if __name__ == "__main__":
    settings = Settings('./temp/settings.json')
    app = QApplication()
    user = UserLoginDialog()
    user.exec_()
    if user.login_status == False:
        exit(0)
    abook = ABookCore('./temp/', settings, user)

    # Simple tests
    courseList = abook.getCourseList()
    # Excepted 3
    print(len(courseList))
    
    print(courseList[0])

    chapterList = abook.getChapterList(5000003293)

    resourceList = abook.getResourceList(5000003293, 5000343805)
    print(resourceList)

    abook.getResourcePath(5000003293, 5000343805, 5000295100)
