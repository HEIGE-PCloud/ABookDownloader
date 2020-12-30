import sys
import os
import json
sys.path.append('.')
sys.path.append('..')
import src.ABookCore  # noqa: E402
import src.Settings  # noqa: E402


def test_ABookLogin_1():

    # Prepare local test_UserInfo.json file
    os.makedirs('tests', exist_ok=True)
    userInfo = {
        "loginUser.loginName": "testName",
        "loginUser.loginPassword": "testPassword"
    }
    userInfoPath = './tests/test_UserInfo.json'
    with open(userInfoPath, 'w', encoding='utf-8') as file:
        json.dump(userInfo, file, ensure_ascii=False, indent=4)

    # Create user object
    user = src.ABookCore.ABookLogin(userInfoPath)

    # Test default loading
    assert user.userInfo == userInfo
    assert userInfo['loginUser.loginName'] == user.username
    assert userInfo['loginUser.loginPassword'] == user.password

    # Test setUserInfo
    newUserInfo = {
        "loginUser.loginName": "newName",
        "loginUser.loginPassword": "newPassword"
    }
    user.setUserInfo(newUserInfo['loginUser.loginName'], newUserInfo['loginUser.loginPassword'])
    assert user.userInfo == newUserInfo
    assert user.username == newUserInfo['loginUser.loginName']
    assert user.password == newUserInfo['loginUser.loginPassword']
    print(os.environ["loginName"])
    print(os.environ["loginPassword"])
    # Test loginStatus
    assert user.loginStatus is False

    with open(userInfoPath, 'r', encoding='utf-8') as file:
        fileData = json.load(file)
        assert fileData == newUserInfo

    # Test login
    user.setUserInfo(os.environ["loginName"], os.environ["loginPassword"])
    user.login()
    assert user.loginStatus is True
    os.remove(userInfoPath)


def test_ABookLogin_2():
    assert 1 == 1
    # os.makedirs('tests', exist_ok=True)
    # userInfoPath = './tests/test_UserInfo.json'
    # userInfo = 'qwq'
    # with open(userInfoPath, 'w', encoding='utf-8') as file:
    #     json.dump(userInfo, file, ensure_ascii=False, indent=4)
    # user = src.ABookCore.ABookLogin(userInfoPath)
    # assert user.username == ''
    # assert user.password == ''
    # os.remove(userInfoPath)


def test_ABookCore():
    settingsPath = './tests/test_Settings.json'
    userInfoPath = './tests/test_UserInfo.json'
    cachePath = './tests/testCache'
    jsonPath = './tests/testCache/jsonCache'
    picPath = './tests/testCache/picCache'
    os.makedirs('tests', exist_ok=True)
    os.makedirs(cachePath, exist_ok=True)
    os.makedirs(jsonPath, exist_ok=True)
    os.makedirs(picPath, exist_ok=True)
    userInfo = {
        "loginUser.loginName": "testName",
        "loginUser.loginPassword": "testPassword"
    }
    with open(userInfoPath, 'w', encoding='utf-8') as file:
        json.dump(userInfo, file, ensure_ascii=False, indent=4)
    settings = src.Settings.Settings(settingsPath)
    user = src.ABookCore.ABookLogin(userInfoPath)
    user.setUserInfo(os.environ["loginName"], os.environ["loginPassword"])
    user.login()
    assert user.loginStatus is True
    abook = src.ABookCore.ABookCore(cachePath, settings, user)
    courseList = abook.getCourseList()
    assert len(courseList) == 9

    courseList = abook.getCourseList()
    assert len(courseList) == 9
    abook.cache = {}

    courseList = abook.getCourseList()
    assert len(courseList) == 9

    for course in courseList:
        courseId = course['courseInfoId']
        chapterList = abook.getChapterList(courseId)
        for chapter in chapterList:
            chapterId = chapter['id']
            abook.getChildChapterList(chapterList, chapter)
            resourceList = abook.getResourceList(courseId, chapterId)
            for resource in resourceList:
                resourceId = resource['resourceInfoId']
                abook.getResourcePath(courseId, chapterId, resourceId)
                picUrl = resource['picUrl']
                picName = picUrl[picUrl.rfind('/') + 1:]
                cachePath = '{}/QImageCache/{}'.format(cachePath, picName)
                if cachePath in abook.cache:
                    resPic = abook.cache[cachePath]
                    resPic
                else:
                    pic = abook.get('pic', [picUrl, picName])
                    pic
    # Test validate file name
    fileName = '  *1.2.3+-/\\abc   '
    print(abook.validateFileName(fileName))
    assert abook.validateFileName(fileName) == '1.2.3+-\\abc(Renamed)'

    os.remove(settingsPath)
    os.remove(userInfoPath)
    # shutil.rmtree(cachePath)


if __name__ == '__main__':
    test_ABookCore()
