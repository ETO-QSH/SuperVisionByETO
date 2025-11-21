from pathlib import Path

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QSizePolicy

from qfluentwidgets import ConfigItem, PushButton, FluentIcon, ToolButton, FluentStyleSheet
from supervision.card.ExpandSettingCard import ExpandSettingCard


class FileItem(QFrame):
    removed = pyqtSignal(object)
    clicked = pyqtSignal()

    def __init__(self, path: str, parent=None):
        super().__init__(parent=parent)
        self.path = path

        self.pathLabel = QLabel(Path(path).name)

        self.removeButton = ToolButton(FluentIcon.CLOSE, self)
        self.removeButton.setFixedSize(32, 22)
        self.removeButton.setIconSize(QSize(9, 9))
        self.removeButton.clicked.connect(lambda: self.removed.emit(self))

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(24, 20, 26, 0)
        self.hBoxLayout.addWidget(self.pathLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(30)
        self.hBoxLayout.addWidget(self.removeButton, 0, Qt.AlignRight)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)

        self.setFixedHeight(45)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        FluentStyleSheet.SETTING_CARD.apply(self)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class FileListSettingCard(ExpandSettingCard):
    filesChanged = pyqtSignal(list)
    fileClicked = pyqtSignal(int)

    def __init__(self, configItem: ConfigItem, title: str, content: str = None, directory="./", parent=None):
        super().__init__(FluentIcon.DOCUMENT, title, content, parent)
        self.configItem = configItem
        self._dialogDirectory = directory
        self.addButton = PushButton(self.tr('打开'), self)
        self.addButton.setMaximumWidth(80)
        self.addButton.setMinimumWidth(80)
        self.card.iconLabel.setFixedSize(20, 20)
        self.card.hBoxLayout.insertSpacing(0, 5)

        self.setMinimumSize(QtCore.QSize(400, 540))
        self.setMaximumSize(QtCore.QSize(400, 5400))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

        self.files = []
        self.file_items = []

        self.__initWidget()

    def __initWidget(self):
        self.card.expandButton.hide()
        self.addWidget(self.addButton)

        self.viewLayout.setSpacing(1)
        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.addButton.clicked.connect(self.__showFileDialog)

    def __showFileDialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("选择多个文件"),
            self._dialogDirectory,
            self.tr("Image files (*.png *.jpg)")
        )

        if not files:
            return

        for path in files:
            self.updateFile(path)

    def __addFileItem(self, path: str):
        idx = len(self.file_items)
        item = FileItem(path, self.view)
        item.removed.connect(lambda itm=item: self.__removeFile(itm))
        
        item.clicked.connect(lambda i=idx: self.fileClicked.emit(i))
        self.file_items.append(item)
        self.files.append(path)
        self.viewLayout.addWidget(item)
        
        item.show()
        self.filesChanged.emit(self.files)

    def __removeFile(self, item):
        if item not in self.file_items:
            return
        idx = self.file_items.index(item)

        self.files[idx] = ''
        self.file_items[idx] = None
        self.viewLayout.removeWidget(item)

        item.deleteLater()
        self.filesChanged.emit(self.files)

    def clear_files(self):
        for itm in list(self.file_items):
            if itm:
                try:
                    self.viewLayout.removeWidget(itm)
                    itm.deleteLater()
                except Exception:
                    pass
        self.file_items = []
        self.files = []
        self.filesChanged.emit(self.files)

    def updateFile(self, path: str):
        ext = Path(path).suffix.lower()
        if ext not in ['.png', '.jpg']:
            return

        full_path = str(Path(path).resolve())
        self.__addFileItem(full_path)
