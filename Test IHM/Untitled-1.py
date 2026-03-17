
import sys
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QTabWidget, QWidget,QMainWindow


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        uic.loadUi("untitled.ui",self)


        self.show()



app = QApplication(sys.argv)
UIWindows= UI()
app.exec ()