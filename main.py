import sys
import os
import random
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDir, Qt, QPointF
from PyQt5 import QtCore, QtGui
from ui import MainWindow

if __name__ == "__main__":
    # Устанавливаем рабочую директорию
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(application_path)
    
    # Создаем папку для иконок, если её нет
    icons_dir = "icons"
    if not os.path.exists(icons_dir):
        os.makedirs(icons_dir)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())