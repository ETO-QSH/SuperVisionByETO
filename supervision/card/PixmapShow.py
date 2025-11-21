from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPainter, QPixmap, QContextMenuEvent
from PyQt5.QtWidgets import QWidget, QGridLayout

from qfluentwidgets import HorizontalPipsPager
from supervision.card.FlipView import HorizontalFlipView


class DIDshow(QWidget):
    PLACEHOLDER_ID = "__placeholder__"
    imageRightClicked = pyqtSignal(str)

    def __init__(self, width, height):
        super().__init__()
        self.flipView = HorizontalFlipView(self)
        self.pager = HorizontalPipsPager(self)
        self.width = width
        self.height = height

        self.flipView.setItemSize(QSize(width, height))
        self.flipView.setFixedSize(QSize(width, height))
        self.pager._visibleNumber = 3

        self.images = {}

        self.placeholder_pixmap = self._create_placeholder()

        self._addPlaceholder()

        self.pager.setPageNumber(self.flipView.count())
        self.pager.currentIndexChanged.connect(self.flipView.setCurrentIndex)

        self.flipView.installEventFilter(self)
        self.flipView.currentIndexChanged.connect(self.pager.setCurrentIndex)

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        layout.addWidget(self.flipView, 1, 1, Qt.AlignCenter)
        layout.addWidget(self.pager, 2, 1, Qt.AlignCenter)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 0)
        layout.setColumnStretch(2, 1)

        layout.setRowStretch(0, 1)
        layout.setRowStretch(3, 1)

        self.setLayout(layout)

        # self.flipView.setStyleSheet("""
        #     border: 2px solid red;
        #     background: transparent;
        #     border-radius: 6px;
        # """)

        # self.pager.setStyleSheet("""
        #     border: 2px solid blue;
        #     background: transparent;
        #     border-radius: 6px;
        # """)

    def _create_placeholder(self) -> QPixmap:
        src = QPixmap(r"./src/None.png")

        canvas = QPixmap(self.width, self.height)
        canvas.fill(Qt.transparent)

        scaled = src.scaled(
            self.width, self.height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        x = (self.width - scaled.width()) // 2
        y = (self.height - scaled.height()) // 2

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap(x, y, scaled)
        painter.end()

        return canvas

    def _addPlaceholder(self):
        self.flipView.addImages([self.placeholder_pixmap], image_ids=[self.PLACEHOLDER_ID])
        self.images[self.PLACEHOLDER_ID] = "placeholder"
        self.pager.setPageNumber(self.flipView.count())

    def _removePlaceholder(self):
        if self.PLACEHOLDER_ID not in self.images:
            return
        index = self.flipView.indexOfImageId(self.PLACEHOLDER_ID)

        if index != -1:
            self.flipView.removeImageAt(index)
            del self.images[self.PLACEHOLDER_ID]
            self.pager.setPageNumber(self.flipView.count())

    def addImage(self, ind, image_path):
        if ind == self.PLACEHOLDER_ID:
            return

        if ind in self.images:
            self.deleteImage(ind)

        if self.flipView.count() == 1 and self.PLACEHOLDER_ID in self.images:
            self._removePlaceholder()

        pixmap = QPixmap(image_path)
        canvas = QPixmap(self.width, self.height)
        canvas.fill(Qt.transparent)
        scaled = pixmap.scaled(canvas.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        x = (canvas.width() - scaled.width()) // 2
        y = (canvas.height() - scaled.height()) // 2

        painter = QPainter(canvas)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        painter.drawPixmap(x, y, scaled)
        painter.end()

        self.images[ind] = image_path
        self.flipView.addImages([canvas], image_ids=[ind])
        self.pager.setPageNumber(self.flipView.count())
        self.flipView.setCurrentIndex(self.flipView.count() - 1)

    def deleteImage(self, ind):
        if ind not in self.images or ind == self.PLACEHOLDER_ID:
            return

        index = self.flipView.indexOfImageId(ind)
        if index == -1:
            del self.images[ind]
            return

        current_display = self.flipView.currentIndex()

        current_count = self.flipView.count()

        if index == current_display:
            next_index = -1
            if current_count > 1:
                next_index = index if index < current_count - 1 else index - 1

            self.flipView.removeImageAt(index)
            del self.images[ind]
            self.pager.setPageNumber(self.flipView.count())

            if self.flipView.count() == 0:
                self._addPlaceholder()
            else:
                if next_index >= 0:
                    self.pager.setCurrentIndex(next_index)
        else:
            self.flipView.removeImageAt(index)
            del self.images[ind]
            self.pager.setPageNumber(self.flipView.count())

            if index < current_display:
                adjusted = max(0, current_display - 1)
            else:
                adjusted = current_display

            if self.flipView.count() == 0:
                self._addPlaceholder()
            else:
                adjusted = max(0, min(adjusted, self.flipView.count() - 1))
                self.pager.setCurrentIndex(adjusted)

    def hasRealImages(self):
        return self.flipView.count() > 0 and self.PLACEHOLDER_ID not in self.images

    def currentImagePath(self):
        current_index = self.flipView.currentIndex()
        if current_index < 0:
            return None

        item = self.flipView.item(current_index)
        image_id = item.data(Qt.UserRole + 1)

        return self.images.get(image_id) if image_id != self.PLACEHOLDER_ID else None

    def go_to_by_id(self, ind):
        idx = self.flipView.indexOfImageId(ind)
        self.pager.setCurrentIndex(idx)
        self.flipView.setCurrentIndex(idx)

    def eventFilter(self, obj, event):
        if obj is self.flipView and isinstance(event, QContextMenuEvent):
            path = self.currentImagePath()
            print("QContextMenuEvent:", path)
            if path:
                self.imageRightClicked.emit(path)
            return True
        return super().eventFilter(obj, event)

    def clear_all(self):
        for ind in list(self.images.keys()):
            if ind == self.PLACEHOLDER_ID:
                continue
                
            try:
                self.deleteImage(ind)
            except Exception:
                try:
                    del self.images[ind]
                except Exception:
                    pass

        if self.FLACEHOLDER_ID if False else False:
            pass
        if self.PLACEHOLDER_ID not in self.images:
            self._addPlaceholder()
