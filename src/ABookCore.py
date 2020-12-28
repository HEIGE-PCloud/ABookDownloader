import os
import json
import requests
from json import JSONDecodeError
# from Settings import Settings


class ABookLogin(object):

    def __init__(self, userInfoPath='./temp/user_info') -> None:
        super().__init__()
        self.loginStatus = False
        self.userInfo = {
            'loginUser.loginName': '', 'loginUser.loginPassword': ''}
        self.username = ''
        self.password = ''
        self.userInfoPath = userInfoPath
        self.session = requests.session()
        self.loginUrl = "http://abook.hep.com.cn/loginMobile.action"
        self.loginStatusUrl = "http://abook.hep.com.cn/verifyLoginMobile.action"
        self.headers = {"User-Agent": "Chrome/83.0.4103.116"}

        self.readUserInfoFromFile()

    def readUserInfoFromFile(self):
        try:
            with open(self.userInfoPath, 'r', encoding='utf-8') as file:
                self.userInfo = json.load(file)
                self.username = self.userInfo['loginUser.loginName']
                self.password = self.userInfo['loginUser.loginPassword']
        except JSONDecodeError or FileNotFoundError or TypeError:
            pass

    def setUserInfo(self, username: str, password: str):
        self.username = username
        self.password = password
        self.userInfo['loginUser.loginName'] = username
        self.userInfo['loginUser.loginPassword'] = password
        self.saveUserInfoToFile()

    def saveUserInfoToFile(self) -> None:
        with open(self.userInfoPath, 'w', encoding='utf-8') as file:
            json.dump(self.userInfo, file, ensure_ascii=False, indent=4)

    def login(self):
        response = self.session.post(self.loginUrl, self.userInfo, headers=self.headers)
        print(response.json()[0]['message'])
        self.loginStatus = (response.json()[0]['message'] == 'successful')


class ABookCore(object):
    def __init__(self, cachePath: str, settings, user):
        super().__init__()
        self.settings = settings
        self.session = user.session
        self.user = user
        self.cachePath = cachePath
        self.cache = {}
        self.courseListUrl = "http://abook.hep.com.cn/selectMyCourseList.action?mobile=true&cur={}"
        self.chapterListUrl = "http://abook.hep.com.cn/resourceStructure.action?courseInfoId={}"
        self.resourceListUrl = "http://abook.hep.com.cn/courseResourceList.action?courseInfoId={}&treeId={}&cur={}"
        self.fileUrl = "http://abook.hep.com.cn/ICourseFiles/{}"

    def getData(self, cachePath: str, urlBase: str, urlArgs: list, forceRefresh=False):
        """
        getData() takes three inputs: cachePath, urlBase, urlArgs and forceRefresh.
        getData() will first try to get data from variable self.cache,
        self.cache is a dict type variable, and the cachePath acts as the key.
        If the data is not cached in the memory, getData() will then try to
        find the data on local file at the cachePath.
        If there is no local cache, getData() will visit the url you pass.
        It will generate the url by url = urlbase.format(*urlArgs) so you can
        pass some Args into it.
        If forceRefresh is True, then getData() will fetch from web api directly.
        """

        if forceRefresh is False:

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
                except JSONDecodeError or UnicodeDecodeError:
                    with open(cachePath, 'rb') as file:
                        data = file.read()
                    return data

        # If nothing is working correctly, use the web api
        data = self.session.get(urlBase.format(*urlArgs))
        try:
            jsonData = data.json()
            self.saveJsonToFile(cachePath, jsonData)
            self.cache[cachePath] = jsonData
            return jsonData
        except JSONDecodeError:
            data = data.content
            with open(cachePath, 'wb') as file:
                file.write(data)
            self.cache[cachePath] = data
            return data

    def get(self, type, argv, forceRefresh=False):
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
            username = self.user.userInfo['loginUser.loginName']
            cachePath = '{}/jsonCache/courseList({})({}).json'.format(self.cachePath, username, cur)
            return self.getData(cachePath, urlBase, [cur], forceRefresh)

        elif type == 'chapterList':
            urlBase = self.chapterListUrl
            courseId = argv
            cachePath = '{}/jsonCache/chapterList({}).json'.format(self.cachePath, courseId)
            return self.getData(cachePath, urlBase, [courseId], forceRefresh)

        elif type == 'resourceList':
            urlBase = self.resourceListUrl
            courseId = argv[0]
            chapterId = argv[1]
            cur = argv[2]
            cachePath = '{}/jsonCache/resourceList({})({})({}).json'.format(self.cachePath, courseId, chapterId, cur)
            return self.getData(cachePath, urlBase, [courseId, chapterId, cur], forceRefresh)

        elif type == 'pic':
            urlBase = self.fileUrl
            picUrl = argv[0]
            picName = argv[1]
            cachePath = '{}/picCache/{}'.format(self.cachePath, picName)
            return self.getData(cachePath, urlBase, [picUrl], forceRefresh)
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
        if type(resourceListPage) != list:
            return None
        if 'myMobileResourceList' in resourceListPage[0]:
            for resource in resourceListPage[0]['myMobileResourceList']:
                resourceList.append(resource)
        while resourceListPage[0]['page']['pageCount'] > cur:
            cur += 1
            resourceListPage = self.get('resourceList', [courseId, chapterId, cur])
            for resource in resourceListPage[0]['myMobileResourceList']:
                resourceList.append(resource)
        return resourceList

    def getCourse(self, courseId):
        """
        getCourse() returns the course with courseId
        """
        courseList = self.getCourseList()
        for course in courseList:
            if course['courseInfoId'] == int(courseId):
                return course

    def getChapter(self, courseId, chapterId):
        """
        getChapter() returns the chapter under courseId with chapterId
        """
        chapterList = self.getChapterList(courseId)
        for chapter in chapterList:
            if chapter['id'] == int(chapterId):
                return chapter

    def getResource(self, courseId, chapterId, resourceId):
        """
        getResource() returns the resource under courseId and chapterId
        with resourceId
        """
        resourceList = self.getResourceList(courseId, chapterId)
        for resource in resourceList:
            if resource['resourceInfoId'] == int(resourceId):
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
        courseName = self.validateFileName(courseName)
        chapter = self.getChapter(courseId, chapterId)
        chapterPid = chapter['pId']
        chapterName = chapter['name']
        resource = self.getResource(courseId, chapterId, resourceId)
        resourceName = resource['resTitle']
        resourceName = self.validateFileName(resourceName)
        resourceUrl = resource['resFileUrl']
        resourceType = resourceUrl[resourceUrl.find('.'):]
        while chapterPid != 0:
            chapter = self.getChapter(courseId, chapterPid)
            chapterName = self.validateFileName(chapter['name']) + '/' + chapterName
            chapterPid = chapter['pId']
        downloadPath = self.settings['download_path']
        dirPath = downloadPath + courseName + '/' + chapterName + '/'
        filePath = dirPath + resourceName + resourceType
        coursePath = downloadPath + courseName
        return (dirPath, filePath, resourceName, coursePath)

    def saveJsonToFile(self, path, data):
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def loadJsonFromFile(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def validateFileName(self, name: str):
        name = name.strip()
        keywords = ['/', ':', '*', '?', '"', '<', '>', '|']
        originalName = name
        for word in keywords:
            name = name.replace(word, '')
        if name != originalName:
            name = name + "(Renamed)"
        return name


# if __name__ == "__main__":
#     settings = Settings('./temp/settings.json')
#     user = ABookLogin()
#     user.login()
#     abook = ABookCore('./temp', settings, user)

#     # Simple tests
#     courseList = abook.getCourseList()
#     # Excepted 3
#     print(len(courseList))

#     print(courseList[0])

#     chapterList = abook.getChapterList(5000003293)

#     resourceList = abook.getResourceList(5000003293, 5000343805)
#     print(resourceList)

#     abook.getResourcePath(5000003293, 5000343805, 5000295100)
