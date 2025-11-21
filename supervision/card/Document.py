from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QFrame

from qfluentwidgets import SmoothScrollArea, PixmapLabel

from supervision.utils import resource_path


class DocumentUI(SmoothScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.label = PixmapLabel(self)
        self.pixmap = QPixmap(resource_path(r".\src\dark.jpeg"))
        self.setWidget(self.label)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        pixmapWidth = self.width()
        pixmapHeight = int(self.pixmap.height() * pixmapWidth / self.pixmap.width())
        scaledPixmap = self.pixmap.scaled(pixmapWidth, pixmapHeight, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaledPixmap)


class Document(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("DocumentInterface")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.document_ui = DocumentUI()
        layout.addWidget(self.document_ui)

        self.document_ui.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.document_ui.setWidgetResizable(False)
        self.document_ui.setStyleSheet("background: transparent;")
        self.document_ui.setFrameShape(QFrame.NoFrame)
