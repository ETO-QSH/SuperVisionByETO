from functools import singledispatchmethod
from typing import Union, List

from PyQt5.QtCore import pyqtProperty, QSize, Qt, QPropertyAnimation, pyqtSignal
from PyQt5.QtGui import QWheelEvent, QImage, QPixmap
from PyQt5.QtWidgets import QListWidgetItem, QListWidget

from qfluentwidgets import FluentIcon, FluentStyleSheet, FlipImageDelegate, SmoothScrollBar
from qfluentwidgets.components.widgets.flip_view import ScrollButton


class FlipView(QListWidget):
    currentIndexChanged = pyqtSignal(int)

    @singledispatchmethod
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.orientation = Qt.Horizontal
        self._postInit()

    @__init__.register
    def _(self, orientation: Qt.Orientation, parent=None):
        super().__init__(parent=parent)
        self.orientation = orientation
        self._postInit()

    def _postInit(self):
        self.isHover = False
        self._currentIndex = -1
        self._aspectRatioMode = Qt.AspectRatioMode.IgnoreAspectRatio
        self._itemSize = QSize(480, 270)  # 16:9

        self.delegate = FlipImageDelegate(self)
        self.scrollBar = SmoothScrollBar(self.orientation, self)

        self.scrollBar.setScrollAnimation(500)
        self.scrollBar.setForceHidden(True)

        self.setMinimumSize(self.itemSize)
        self.setItemDelegate(self.delegate)
        self.setMovement(QListWidget.Static)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        FluentStyleSheet.FLIP_VIEW.apply(self)

        if self.isHorizontal():
            self.setFlow(QListWidget.LeftToRight)
            self.preButton = ScrollButton(FluentIcon.CARE_LEFT_SOLID, self)
            self.nextButton = ScrollButton(FluentIcon.CARE_RIGHT_SOLID, self)
            self.preButton.setFixedSize(16, 38)
            self.nextButton.setFixedSize(16, 38)
        else:
            self.preButton = ScrollButton(FluentIcon.CARE_UP_SOLID, self)
            self.nextButton = ScrollButton(FluentIcon.CARE_DOWN_SOLID, self)
            self.preButton.setFixedSize(38, 16)
            self.nextButton.setFixedSize(38, 16)

        self.preButton.clicked.connect(self.scrollPrevious)
        self.nextButton.clicked.connect(self.scrollNext)

    def isHorizontal(self):
        return self.orientation == Qt.Horizontal

    def setItemSize(self, size: QSize):
        if size == self.itemSize:
            return

        self._itemSize = size

        for i in range(self.count()):
            self._adjustItemSize(self.item(i))

        self.viewport().update()

    def getItemSize(self):
        return self._itemSize

    def setBorderRadius(self, radius: int):
        self.delegate.setBorderRadius(radius)

    def getBorderRadius(self):
        return self.delegate.borderRadius

    def scrollPrevious(self):
        self.setCurrentIndex(self.currentIndex() - 1)

    def scrollNext(self):
        self.setCurrentIndex(self.currentIndex() + 1)

    def setCurrentIndex(self, index: int):
        if not 0 <= index < self.count() or index == self.currentIndex():
            return

        self.scrollToIndex(index)

        if index == 0:
            self.preButton.fadeOut()
        elif self.preButton.isTransparent() and self.isHover:
            self.preButton.fadeIn()

        if index == self.count() - 1:
            self.nextButton.fadeOut()
        elif self.nextButton.isTransparent() and self.isHover:
            self.nextButton.fadeIn()

        self.currentIndexChanged.emit(index)

    def scrollToIndex(self, index):
        if not 0 <= index < self.count():
            return

        self._currentIndex = index

        if self.isHorizontal():
            value = sum(self.item(i).sizeHint().width() for i in range(index))
        else:
            value = sum(self.item(i).sizeHint().height() for i in range(index))

        value += (2 * index + 1) * self.spacing()
        self.scrollBar.setValue(value)
        self._updateScrollButtons()

    def currentIndex(self):
        return self._currentIndex

    def image(self, index: int):
        if not 0 <= index < self.count():
            return QImage()

        return self.item(index).data(Qt.UserRole)

    def addImage(self, image: Union[QImage, QPixmap, str]):
        self.addImages([image])

    def addImages(self, images: List[Union[QImage, QPixmap, str]], image_ids=None):
        if not images:
            return

        N = self.count()
        self.addItems([''] * len(images))

        for i in range(N, self.count()):
            img = images[i - N]
            iid = image_ids[i - N] if image_ids else None
            self.setItemImage(i, img, image_id=iid)

        if self.currentIndex() < 0 and self.count() > 0:
            self.setCurrentIndex(0)

    def setItemImage(self, index: int, image: Union[QImage, QPixmap, str], image_id=None):
        if not 0 <= index < self.count():
            return
        item = self.item(index)

        if isinstance(image, str):
            qimage = QImage(image)
        elif isinstance(image, QPixmap):
            qimage = image.toImage()
        else:
            qimage = image

        item.setData(Qt.UserRole, qimage)
        item.setData(Qt.UserRole + 1, image_id)

        self._adjustItemSize(item)

    def _adjustItemSize(self, item: QListWidgetItem):
        image = self.itemImage(self.row(item))

        if self.aspectRatioMode == Qt.AspectRatioMode.KeepAspectRatio:
            if self.isHorizontal():
                h = self.itemSize.height()
                w = int(image.width() * h / image.height())
            else:
                w = self.itemSize.width()
                h = int(image.height() * w / image.width())
        else:
            w, h = self.itemSize.width(), self.itemSize.height()

        item.setSizeHint(QSize(w, h))

    def itemImage(self, index: int) -> QImage:
        if not 0 <= index < self.count():
            return QImage()
        item = self.item(index)
        data = item.data(Qt.UserRole)
        return data if isinstance(data, QImage) else QImage()

    def indexOfImageId(self, image_id) -> int:
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole + 1) == image_id:
                return i
        return -1

    def resizeEvent(self, e):
        w, h = self.width(), self.height()
        bw, bh = self.preButton.width(), self.preButton.height()

        if self.isHorizontal():
            self.preButton.move(2, int(h / 2 - bh / 2))
            self.nextButton.move(w - bw - 2, int(h / 2 - bh / 2))
        else:
            self.preButton.move(int(w / 2 - bw / 2), 2)
            self.nextButton.move(int(w / 2 - bw / 2), h - bh - 2)

    def enterEvent(self, e):
        super().enterEvent(e)
        self.isHover = True

        if self.currentIndex() > 0:
            self.preButton.fadeIn()

        if self.currentIndex() < self.count() - 1:
            self.nextButton.fadeIn()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self.isHover = False
        self.preButton.fadeOut()
        self.nextButton.fadeOut()

    def showEvent(self, e):
        self.scrollBar.duration = 0
        self.scrollToIndex(self.currentIndex())
        self.scrollBar.duration = 500

    def wheelEvent(self, e: QWheelEvent):
        e.setAccepted(True)
        if self.scrollBar.ani.state() == QPropertyAnimation.Running:
            return

        if e.angleDelta().y() < 0:
            self.scrollNext()
        else:
            self.scrollPrevious()

    def getAspectRatioMode(self):
        return self._aspectRatioMode

    def setAspectRatioMode(self, mode: Qt.AspectRatioMode):
        if mode == self.aspectRatioMode:
            return

        self._aspectRatioMode = mode

        for i in range(self.count()):
            self._adjustItemSize(self.item(i))

        self.viewport().update()

    itemSize = pyqtProperty(QSize, getItemSize, setItemSize)
    borderRadius = pyqtProperty(int, getBorderRadius, setBorderRadius)
    aspectRatioMode = pyqtProperty(bool, getAspectRatioMode, setAspectRatioMode)

    def removeImageAt(self, index: int):
        if not 0 <= index < self.count():
            return

        self.takeItem(index)

        if self._currentIndex >= index:
            self._currentIndex = max(0, min(self._currentIndex - 1, self.count() - 1))

        if self.count() > 0:
            self.scrollToIndex(self._currentIndex)
        else:
            self._currentIndex = -1

        self._updateScrollButtons()
        self.currentIndexChanged.emit(self._currentIndex)

    def _updateScrollButtons(self):
        index = self.currentIndex()
        if index <= 0:
            self.preButton.fadeOut()
        else:
            if self.isHover:
                self.preButton.fadeIn()

        if index >= self.count() - 1:
            self.nextButton.fadeOut()
        else:
            if self.isHover:
                self.nextButton.fadeIn()


class HorizontalFlipView(FlipView):
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)


class VerticalFlipView(FlipView):
    def __init__(self, parent=None):
        super().__init__(Qt.Vertical, parent)
