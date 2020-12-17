from PySide2.QtCore import QThread, Qt, Signal, Slot
from PySide2.QtWidgets import QApplication, QCheckBox, QDialog, QGridLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget
import sys

from ABookCore import ABookLogin

class LoginWidget(QWidget):

    def __init__(self, parent=None) -> None:
        super(LoginWidget, self).__init__(parent)

        self.initLayout()

    def initLayout(self) -> None:

        # username
        self.usernameLabel = QLabel("Username: ")
        self.usernameLineEdit = QLineEdit(self.parent().userInfo['loginUser.loginName'])

        # password
        self.passwordLabel = QLabel("Password: ")
        self.passwordLineEdit = QLineEdit(self.parent().userInfo['loginUser.loginPassword'])
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

        self.setFont('Microsoft YaHei UI')
    
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
            self.update_status.emit("Saving user's info to file... (Step 1/2)")
            self.parent().saveUserInfoToFile()

            # Step 2: post user info to ABook
            self.update_status.emit("Posting user's info to ABook... (Step 2/2)")        
            response = self.parent().session.post(url=self.parent().loginUrl, data=self.parent().userInfo, headers=self.parent().headers)

            # send login status signal
            self.login_response.emit(response.json()[0]['message'] == 'successful')
        except:
            self.login_response.emit(False)

class UserLoginDialog(QDialog, ABookLogin):

    def __init__(self, settings) -> None:
        QDialog.__init__(self)
        ABookLogin.__init__(self)
        self.initLayout()
        if settings['auto_login']:
            self.login_widget.loginButton.click()
    
    def initLayout(self):
        self.login_widget =  LoginWidget(self)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.login_widget)
        self.setLayout(self.layout)
        self.setWindowTitle("ABook Login")
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint)

    def login(self):
        self.userInfo['loginUser.loginName'] = self.login_widget.usernameLineEdit.text()
        self.userInfo['loginUser.loginPassword'] = self.login_widget.passwordLineEdit.text()
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
            self.loginStatus = True
            self.close()
        else:
            QMessageBox.critical(self, 'Error', 'Login failed.')
            self.login_widget.setDisabled(False)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    login = UserLoginDialog()
    login.exec_()