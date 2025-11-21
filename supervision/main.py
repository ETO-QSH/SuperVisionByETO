import os
import sys

if getattr(sys, 'frozen', False):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')

import shutil
from pathlib import Path

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, QUrl, QTimer, QSize
from PyQt5.QtGui import QDesktopServices, QIcon
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout

from qfluentwidgets import (
    NavigationItemPosition, setTheme, Theme, MSFluentWindow, SubtitleLabel,
    setFont, setThemeColor, FluentIcon, SplashScreen
)

from card.MainInterface import MainInterface
from card.Document import Document
from card.Setting import Setting


class Widget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class Window(MSFluentWindow):
    def __init__(self):
        super().__init__()

        self.titleInterface = Widget("这是预留的标题页喵\n建议是改成模型训练页喵", self)
        self.mainInterface = MainInterface()
        self.settingInterface = Setting()
        self.documentInterface = Document()

        self.initNavigation()
        self.initWindow()

        QTimer.singleShot(2500, self.splashScreen.finish)

    def initNavigation(self):
        self.addSubInterface(
            self.titleInterface, FluentIcon.HOME, '标题', FluentIcon.HOME
        )
        self.addSubInterface(
            self.mainInterface, FluentIcon.LABEL, '管理', FluentIcon.LABEL
        )
        self.addSubInterface(
            self.settingInterface, FluentIcon.SETTING, '设置',
            FluentIcon.SETTING, NavigationItemPosition.BOTTOM
        )
        self.addSubInterface(
            self.documentInterface, FluentIcon.HELP, '文档',
            FluentIcon.HELP, NavigationItemPosition.BOTTOM
        )
        self.navigationInterface.addItem(
            routeKey='Github',
            icon=FluentIcon.GITHUB,
            text='源码',
            onClick=self.toGithub,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

    def initWindow(self):
        self.setGeometry(QtCore.QRect(0, 0, 900, 700))

        self.titleBar.maxBtn.hide()
        self.titleBar.setDoubleClickEnabled(False)

        icon = QtGui.QIcon(r".\src\Sprite-0001.ico")
        self.titleBar.iconLabel.setPixmap(icon.pixmap(25, 25))
        self.titleBar.iconLabel.setFixedSize(36, 36)

        self.titleBar.hBoxLayout.insertSpacing(0, 4)
        self.titleBar.titleLabel.setText('SuperVisionByETO')

        titleLabelStyle = """
            QLabel {
                font-family: '萝莉体';
                font-size: 16px;
            }
        """
        self.titleBar.titleLabel.setStyleSheet(titleLabelStyle)

        self.splashScreen = SplashScreen(QIcon(r'.\src\setup.jpg'), self)
        self.splashScreen.setIconSize(QSize(self.width(), self.height()))
        self.splashScreen.setGeometry(0, 0, self.width(), self.height())
        self.splashScreen.raise_()

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def toGithub(self):
        QDesktopServices.openUrl(QUrl("https://github.com/ETO-QSH/SuperVisionByETO"))


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    setTheme(Theme.DARK)
    setThemeColor("#ffffbfbf")

    out_dir = Path('./output')
    shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    w = Window()
    w.show()
    app.exec_()
