import sys
import traceback
from PySide2.QtCore import QObject, Signal
from PySide2.QtWidgets import QApplication, QMessageBox
import pyperclip


def showExceptionBox(logMessage):
    if QApplication.instance() is not None:
        errorBox = QMessageBox()
        errorBox.setWindowTitle('Error')
        errorBox.setText("Oops. An unexpected error occurred:\n{0}".format(logMessage))
        errorBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Close)
        buttonCopy = errorBox.button(QMessageBox.Ok)
        buttonCopy.setText('Copy exception log...')
        buttonCopy.clicked.connect(lambda: pyperclip.copy(logMessage))
        errorBox.exec_()


class UncaughtHook(QObject):
    ExceptionCaught = Signal(object)

    def __init__(self, *args, **kwargs):
        super(UncaughtHook, self).__init__(*args, **kwargs)

        sys.excepthook = self.exceptionhook
        self.ExceptionCaught.connect(showExceptionBox)

    def exceptionhook(self, excType, excValue, excTraceback):
        if issubclass(excType, KeyboardInterrupt):
            sys.__excepthook__(excType, excValue, excTraceback)
        else:
            # exc_info = (exc_type, exc_value, exc_traceback)
            logMessage = '\n'.join([''.join(traceback.format_tb(excTraceback)),
                                   '{}: {}'.format(excType.__name__, excValue)])
            # log.critical("Uncaught exception:\n {0}".format(log_msg), exc_info=exc_info)
            self.ExceptionCaught.emit(logMessage)
