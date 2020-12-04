import json
from PySide2.QtCore import QThread, Qt, Signal, Slot
from PySide2.QtWidgets import QApplication, QCheckBox, QDialog, QGridLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget
import requests
import sys

class ABookLogin(object):

    def __init__(self) -> None:
        super().__init__()
        self.login_status = False
        self.user_info = {'loginUser.loginName': '', 'loginUser.loginPassword': ''}
        self.path = './temp/user_info.json'
        self.session = requests.session()
        self.login_url = "http://abook.hep.com.cn/loginMobile.action"
        self.login_status_url = "http://abook.hep.com.cn/verifyLoginMobile.action"
        self.headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.64"}

        self.read_user_info_from_file()
    
    def read_user_info_from_file(self) -> bool:
        try:
            with open(self.path, 'r', encoding='utf-8') as file:
                self.user_info = json.load(file)
                self.username = self.user_info['loginUser.loginName']
                self.password = self.user_info['loginUser.loginPassword']
            return True
        except:
            return False
        
    def save_user_info_to_file(self) -> None:
        with open(self.path, 'w', encoding='utf-8') as file:
            json.dump(self.user_info, file, ensure_ascii=False, indent=4)

class LoginWidget(QWidget):

    def __init__(self, parent=None) -> None:
        super(LoginWidget, self).__init__(parent)

        self.initLayout()

    def initLayout(self) -> None:

        # username
        self.usernameLabel = QLabel("Username: ")
        self.usernameLineEdit = QLineEdit(self.parent().user_info['loginUser.loginName'])

        # password
        self.passwordLabel = QLabel("Password: ")
        self.passwordLineEdit = QLineEdit(self.parent().user_info['loginUser.loginPassword'])
        self.passwordLineEdit.setEchoMode(QLineEdit.Password)

        # login button
        self.loginButton = QPushButton("Login")
        self.loginButton.clicked.connect(self.parent().login)

        # checkbox
        def CheckBoxStateChanged(state) -> None:
            if state == Qt.Checked:
                self.passwordLineEdit.setEchoMode(QLineEdit.Normal)
            else:
                self.passwordLineEdit.setEchoMode(QLineEdit.Password)

        self.checkBox = QCheckBox("Show Password")
        self.checkBox.stateChanged.connect(CheckBoxStateChanged)
        
        # layout
        layout = QGridLayout()
        layout.addWidget(self.usernameLabel, 0, 0)
        layout.addWidget(self.usernameLineEdit, 0, 1)
        layout.addWidget(self.passwordLabel, 1, 0)
        layout.addWidget(self.passwordLineEdit, 1, 1)
        layout.addWidget(self.checkBox, 2, 1, Qt.AlignRight)
        layout.addWidget(self.loginButton, 3, 1)

        self.setLayout(layout)
    
class LoginWorker(QThread):

    update_status = Signal(str)
    login_response = Signal(bool)

    def __init__(self, parent=None) -> None:
        super(LoginWorker, self).__init__(parent)
        self.update_status.connect(self.parent().handleLoginStatus)
        self.login_response.connect(self.parent().handleLoginResponse)

    def run(self) -> None:

        try:
            # Step 1: save user info to local file
            self.update_status.emit("Saving user's info to file... (Step 1/3)")
            self.parent().save_user_info_to_file()

            # Step 2: post user info to ABook
            self.update_status.emit("Posting user's info to ABook... (Step 2/3)")        
            self.parent().session.post(url=self.parent().login_url, data=self.parent().user_info, headers=self.parent().headers)

            # Step 3: check login status
            self.update_status.emit("Checking login status... (Step 3/3)")
            login_status_msg = self.parent().session.post(self.parent().login_status_url).json()
            
            # send login status signal
            self.login_response.emit(login_status_msg["message"] == "已登录")
        except:
            self.login_response.emit(False)

class UserLoginDialog(QDialog, ABookLogin):

    def __init__(self) -> None:
        QDialog.__init__(self)
        ABookLogin.__init__(self)
        self.initLayout()
        self.exec_()
    
    def initLayout(self):
        self.login_widget =  LoginWidget(self)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.login_widget)
        self.setLayout(self.layout)
        self.setWindowTitle("ABook Login")

    def login(self):
        self.user_info['loginUser.loginName'] = self.login_widget.usernameLineEdit.text()
        self.user_info['loginUser.loginPassword'] = self.login_widget.passwordLineEdit.text()
        self.login_widget.setDisabled(True)
        worker = LoginWorker(self)
        worker.start()

    @Slot(str)
    def handleLoginStatus(self, status):
        print(status)

    @Slot(bool)
    def handleLoginResponse(self, response):
        print(response)
        if response:
            self.login_status = True
            self.close()
        else:
            QMessageBox.critical(self, 'Error', 'Login failed.')
            self.login_widget.setDisabled(False)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    login = UserLoginDialog()