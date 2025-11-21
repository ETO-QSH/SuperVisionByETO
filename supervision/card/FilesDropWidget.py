from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen, QFont, QFontDatabase
from PyQt5.QtWidgets import QWidget, QLabel

from qfluentwidgets import TeachingTip, TeachingTipTailPosition, InfoBarIcon, isDarkTheme

from supervision.utils import resource_path


class FilesDropWidget(QWidget):
    pathChanged = pyqtSignal(str)

    def __init__(self, file_types, parent=None):
        super().__init__(parent)
        self.file_types = file_types
        self.target_card = None
        self._hover = False

        self.setFixedSize(360, 120)
        self.setObjectName("FilesDropWidget")

        self.font_id = QFontDatabase.addApplicationFont(resource_path(r".\src\Lolita.ttf"))
        if self.font_id != -1:
            self.font_family = QFontDatabase.applicationFontFamilies(self.font_id)[0]
            self.font_18 = QFont(self.font_family)
            self.font_18.setPixelSize(18)
        else:
            print("Failed to load font")

        self.text_label = QLabel(self)
        self.text_label.setText("拖  放  文  件\n到  此  区  域")
        self.text_label.setFont(self.font_18)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setGeometry(15, 15, 330, 90)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color: gray;")

        self.setAcceptDrops(True)
        self.setAttribute(Qt.WA_Hover)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        path = QPainterPath()
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        path.addRoundedRect(rect, 15, 15)  # 圆角半径

        border_color = QColor("#3AA3FF" if self._hover else "#A0A0A0")
        if isDarkTheme():
            border_color = QColor("#3AA3FF" if self._hover else "#707070")

        pen = QPen(border_color, 3)
        pen.setDashPattern([4, 4])
        painter.setPen(pen)
        painter.drawPath(path)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self._hover = True
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                file_suffix = Path(path).suffix.lower()

                if file_suffix not in self.file_types:
                    self._show_error_tip("无效文件类型", f"{file_suffix} 不是支持的文件类型")
                    continue
                self.pathChanged.emit(path)

            event.accept()
            self._hover = False
            self.update()
            return

        event.ignore()
        self._hover = False
        self.update()

    def bindFileListSettingCard(self, card):
        self.target_card = card
        self.pathChanged.connect(self.__update_file_list)

    def __update_file_list(self, path):
        if self.target_card:
            self.target_card.updateFile(path)

    def _show_error_tip(self, title, content):
        TeachingTip.create(
            target=self,
            icon=InfoBarIcon.ERROR,
            title=title,
            content=content,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            duration=3000,
            parent=self.window()
        )
