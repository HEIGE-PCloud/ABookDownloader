from json.decoder import JSONDecodeError
import os
import json
import time
import logging
import requests
import tkinter.filedialog

session = requests.session()

COURSES_INFO_FILE = "./temp/course_info.json"
SETTINGS_INFO = "./temp/settings.json"
USER_INFO = "./temp/user_info.json"
DOWNLOAD_DIR = "./Downloads/"
ROOT = 0
courses_list = []
chapter_list = []
settings = []
current_user = ["", ""]


def safe_mkdir(dir_name):
    try:
        os.mkdir(str(dir_name))
    except FileExistsError:
        pass


def safe_remove(dir_name):
    try:
        os.remove(str(dir_name))
    except FileNotFoundError:
        pass


def validate_file_name(file_name: str):
    file_name = file_name.strip()
    key_word = ['/', ':', '*', '?', '"', '<', '>', '|']
    file_name = str(file_name)
    original_file_name = file_name
    for word in key_word:
        file_name = file_name.replace(word, '')
    if file_name != original_file_name:
        file_name = file_name + "(Renamed)"
    return file_name


def load_settings(file_name):
    global DOWNLOAD_DIR, settings
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            settings = json.load(file)
    except FileNotFoundError:
        settings = {'download_path': './Downloads/'}
        save_settings(file_name)
    DOWNLOAD_DIR = settings['download_path']


def save_settings(file_name):
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(settings, file, ensure_ascii=False, indent=4)
    logging.info("Settings saved.")


def change_download_path():
    global DOWNLOAD_DIR, settings
    new_download_path = tkinter.filedialog.askdirectory(title="Please select a folder:")
    new_download_path += "/"
    logging.info(new_download_path)
    DOWNLOAD_DIR = new_download_path
    settings['download_path'] = DOWNLOAD_DIR
    save_settings(SETTINGS_INFO)


def init():
    """
    This function will create temp and Downloads folders and display welcome.
    temp is for logs and information gathered while the program is running.
    The Downloads folder is where to save the downloaded file by default.
    """
    safe_mkdir("temp")
    safe_mkdir("Downloads")
    logger = logging.getLogger()
    logger.setLevel('DEBUG')
    chlr = logging.StreamHandler()
    chlr.setLevel('INFO')
    fhlr = logging.FileHandler('temp/ABookDownloaderLog.log')
    logger.addHandler(chlr)
    logger.addHandler(fhlr)
    logging.info("Started successfully!")
    load_settings(SETTINGS_INFO)

    print("ABookDownloader是由HEIGE-PCloud编写的开源Abook下载软件")
    print("当前版本 1.0.5.1 可前往项目主页检查更新")
    print("项目主页 https://github.com/HEIGE-PCloud/ABookDownloader")
    print("如果遇到任何问题，欢迎提交issue")
    print("如果这款软件帮到了您，欢迎前往该项目主页请作者喝奶茶QwQ")
    print("<========================================================>")


def file_downloader(file_name, url):
    headers = {'Proxy-Connection': 'keep-alive'}
    r = requests.get(url, stream=True, headers=headers)
    content_length = float(r.headers['content-length'])
    with open(file_name, 'wb') as file:
        downloaded_length = 0
        last_downloaded_length = 0
        time_start = time.time()
        for chunk in r.iter_content(chunk_size=512):
            if chunk:
                file.write(chunk)
                downloaded_length += len(chunk)
                if time.time() - time_start > 1:
                    percentage = downloaded_length / content_length * 100
                    speed = (downloaded_length -
                             last_downloaded_length) / 2097152
                    last_downloaded_length = downloaded_length
                    print("\r Downloading: " + file_name + ': ' + '{:.2f}'.format(
                        percentage) + '% Speed: ' + '{:.2f}'.format(speed) + 'MB/S', end="")
                    time_start = time.time()
    print("\nDownload {} successfully!".format(file_name))


def Abook_login(login_name, login_password):
    login_url = "http://abook.hep.com.cn/loginMobile.action"
    login_status_url = "http://abook.hep.com.cn/verifyLoginMobile.action"
    login_data = {"loginUser.loginName": login_name,
                  "loginUser.loginPassword": login_password}
    headers = {"User-Agent": "Chrome/83.0.4103.116"}
    session.post(url=login_url, data=login_data, headers=headers)
    if session.post(login_status_url).json()["message"] == "已登录":
        logging.info("Successfully login in!")
        current_user[0] = login_name
        current_user[1] = login_password
        return True
    else:
        logging.error("Login failed, please try again.")
        safe_remove("./temp/user_info.json")
        return False


def get_courses_info(file_name):
    """Get courses info from login, need pass through the path to save the json file of courses information."""

    course_info_url = "http://abook.hep.com.cn/selectMyCourseList.action?mobile=true&cur=1"
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(session.get(course_info_url).json(),
                  file, ensure_ascii=False, indent=4)
    logging.info("Courses info fetched!")


def load_courses_info(file_name):
    """Load courses info from file_name and store them into the global courses_list."""
    global courses_list
    courses_list = []
    with open(file_name, 'r', encoding='utf-8') as courses_info:
        try:
            courses_data: list = json.load(courses_info)[0]['myMobileCourseList']
        except JSONDecodeError:
            logging.error("Cannot load courses.")
            return
        print('There are {} course(s) available.'.format(len(courses_data)))
        for course in courses_data:
            course['courseTitle'] = validate_file_name(course['courseTitle'])
            courses_list.append(course)
    logging.info("Courses info loaded.")


def get_chapter_info(course_id):
    """Get the chapter info by course_id"""
    course_url = 'http://abook.hep.com.cn/resourceStructure.action?courseInfoId={}'.format(
        course_id)
    with open("./temp/" + str(course_id) + '.json', 'w', encoding='utf-8') as file:
        json.dump(session.post(course_url).json(),
                  file, ensure_ascii=False, indent=4)
    logging.info("Chapter for course {} fetched".format(course_id))


def load_chapter_info(course_id):
    """Load chapter info from local file and store it into globe variable chapter_list."""
    global chapter_list
    chapter_list = []
    with open("./temp/" + str(course_id) + '.json', 'r', encoding='utf-8') as chapter_info:
        chapter_data: list = json.load(chapter_info)
    for chapter in chapter_data:
        chapter['name'] = validate_file_name(chapter['name'])
        chapter_list.append(chapter)
    logging.info("Chapter for {} loaded.".format(course_id))


def display_courses_info():
    print("0 下载全部")
    for i in range(len(courses_list)):
        print(i + 1, courses_list[i]['courseTitle'])
    print("o 打开下载文件夹")
    print("s 更改保存目录")
    print("q 退出")


def display_chapter_info(title_name, pid):
    """Display chapter info by selected course and parrent id."""
    print("> " + title_name + ":")
    print("0 下载全部")
    for i in range(len(chapter_list)):
        if chapter_list[i]['pId'] == pid:
            print(i + 1, chapter_list[i]['name'])
    print("q 返回上一级")


def chapter_has_child(selected_chapter):
    child_chapter = []
    for chapter in chapter_list:
        if chapter['pId'] == selected_chapter['id']:
            child_chapter.append(chapter)
    return child_chapter


def download_course_from_root(root_chapter, course_id, path):
    # for chapter in root_chapter:
    child_list = chapter_has_child(root_chapter)
    if len(child_list) != 0:
        for child in child_list:
            safe_mkdir(path + child['name'])
            download_course_from_root(
                child, course_id, path + child['name'] + '/')
    else:
        cur = 1
        all_page_downloaded = False
        while all_page_downloaded is False:
            download_link_url = "http://abook.hep.com.cn/courseResourceList.action?courseInfoId={}&treeId={}&cur={}"\
                                .format(course_id, root_chapter['id'], cur)
            download_url_base = "http://abook.hep.com.cn/ICourseFiles/"
            while True:
                try:
                    info = session.get(download_link_url).json()[0]
                    break
                except requests.ConnectionError or JSONDecodeError:
                    logging.error(
                        "Info fetched failed, will restart in 5 seconds.")
                    Abook_login(current_user[0], current_user[1])
                    time.sleep(5)
            page = info['page']
            page_count = page["pageCount"]
            if page_count <= cur:
                all_page_downloaded = True
            cur += 1
            if 'myMobileResourceList' in info:
                course = info['myMobileResourceList']
                print(len(course), "downloadable items found!")
                for i in range(len(course)):
                    file_name = course[i]['resTitle']
                    file_url = course[i]['resFileUrl']
                    print(file_name)
                    url = download_url_base + file_url
                    print(url)
                    file_type = file_url[str(file_url).find('.'):]
                    location = path + str(file_name) + str(file_type)
                    while True:
                        try:
                            file_downloader(location, url)
                            break
                        except requests.ConnectionError:
                            logging.error(
                                "Download failed, will restart in 5 seconds.")
                            time.sleep(5)


def download_course(download_dir, selected_course, selected_root):
    safe_mkdir(download_dir + selected_course['courseTitle'])
    safe_mkdir(download_dir +
               selected_course['courseTitle'] + "/" + selected_root['name'])
    download_course_from_root(selected_root, selected_course['courseInfoId'], DOWNLOAD_DIR +
                              selected_course['courseTitle'] + "/" + selected_root['name'] + "/")


def read_login_info(file_name):
    """
    Read the local login info from file. Pass through the file name.
    Return user_info as json if succeed, or return boolean False if failed.
    """
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            try:
                login_info: list = json.load(file)
                logging.info("Successfully read the local user info.")
                return login_info
            except json.decoder.JSONDecodeError:
                return False
    except FileNotFoundError:
        logging.info("Did not find local user info. Ask for input instead.")
        return False


def write_login_info(user_info, file_name):
    """Write the user_info as json to file_name file."""
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(user_info, file, ensure_ascii=False, indent=4)
        logging.info("Login details saved.")


def select_chapter(title_name, pid):
    while True:
        display_chapter_info(title_name, pid)
        choice = input("Enter the chapter index to choose: ")
        if str(choice) == '0':
            return True
        if str(choice).isnumeric():
            choice = int(choice)
            selected_chapter = chapter_list[choice - 1]
            result = select_chapter(
                selected_chapter['name'], selected_chapter['id'])
            if result is False:
                continue
            elif result is True:
                return selected_chapter
            else:
                return result
        if str(choice) == 'q':
            return False


if __name__ == "__main__":
    init()
    # First check if there is user information stored locally.
    # If there is, then ask whether the user will use it or not.
    # If there isn't, ask user type in information directly.
    user_info = read_login_info(USER_INFO)

    if user_info is not False:
        choice = input("User {} founded! Do you want to log in as {}? (y/n) ".format(
            user_info['loginUser.loginName'], user_info['loginUser.loginName']))
        if choice == 'n':
            user_info = False

    if user_info is False:
        login_name = input("Please input login name: ")
        login_password = input("Please input login password: ")
        user_info = {'loginUser.loginName': login_name,
                     'loginUser.loginPassword': login_password}
        write_login_info(user_info, USER_INFO)

    # User login
    while True:
        if Abook_login(user_info['loginUser.loginName'], user_info['loginUser.loginPassword']):
            break
        login_name = input("Please input login name: ")
        login_password = input("Please input login password: ")
        user_info = {'loginUser.loginName': login_name,
                     'loginUser.loginPassword': login_password}
        write_login_info(user_info, USER_INFO)

    # Get and load courses infomation
    get_courses_info(COURSES_INFO_FILE)
    load_courses_info(COURSES_INFO_FILE)

    while True:
        display_courses_info()

        choice = input("Enter course index to choose: ")
        try:
            choice = int(choice)
        except ValueError:
            if choice == 'o':
                os.system("explorer " + DOWNLOAD_DIR.replace('/', '\\'))
                continue
            elif choice == 's':
                change_download_path()
                continue
            else:
                logging.info("Bye~")
            break

        # Download All!
        if choice == 0:
            for selected_course in courses_list:
                get_chapter_info(selected_course['courseInfoId'])
                load_chapter_info(selected_course['courseInfoId'])
                root_list = []
                for chapter in chapter_list:
                    if chapter['pId'] == 0:
                        root_list.append(chapter)
                for chapter in root_list:
                    download_course(DOWNLOAD_DIR, selected_course, chapter)
        else:
            try:
                selected_course = courses_list[choice - 1]
            except IndexError:
                print("Wrong Index!")
                continue
            # Get and load chapter information
            get_chapter_info(selected_course['courseInfoId'])
            load_chapter_info(selected_course['courseInfoId'])

            # select_chapter(selected_course['courseTitle'], ROOT)
            # selected_root
            #               = True when user choose to download the entire course
            #               = course_info when user choose to download a specific sub-chapter
            selected_root = select_chapter(
                selected_course['courseTitle'], ROOT)

            if selected_root is False:
                continue
            if selected_root is True:
                root_list = []
                for chapter in chapter_list:
                    if chapter['pId'] == 0:
                        root_list.append(chapter)
                for chapter in root_list:
                    download_course(DOWNLOAD_DIR, selected_course, chapter)
            else:
                download_course(DOWNLOAD_DIR, selected_course, selected_root)
