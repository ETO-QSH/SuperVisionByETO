from typing import Union

from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFrame, QWidget, QApplication, QVBoxLayout

from qfluentwidgets import FluentIcon, FluentStyleSheet, ScrollArea
from qfluentwidgets.components.settings.expand_setting_card import HeaderSettingCard, SpaceWidget, ExpandBorderWidget


class ExpandSettingCard(ScrollArea):
    def __init__(self, icon: Union[str, QIcon, FluentIcon], title: str, content: str = None, parent=None):
        super().__init__(parent=parent)
        self.isExpand = False

        self.scrollWidget = QFrame(self)
        self.view = QFrame(self.scrollWidget)
        self.card = HeaderSettingCard(icon, title, content, self)

        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.viewLayout = QVBoxLayout(self.view)
        self.spaceWidget = SpaceWidget(self.scrollWidget)
        self.borderWidget = ExpandBorderWidget(self)

        self.expandAni = QPropertyAnimation(self.verticalScrollBar(), b'value', self)
        self.__initWidget()

    def __initWidget(self):
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setFixedHeight(self.card.height())
        self.setViewportMargins(0, self.card.height(), 0, 0)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(0)
        self.scrollLayout.addWidget(self.view)
        self.scrollLayout.addWidget(self.spaceWidget)

        self.expandAni.setEasingCurve(QEasingCurve.OutQuad)
        self.expandAni.setDuration(200)

        self.view.setObjectName('view')
        self.scrollWidget.setObjectName('scrollWidget')
        self.setProperty('isExpand', False)
        FluentStyleSheet.EXPAND_SETTING_CARD.apply(self.card)
        FluentStyleSheet.EXPAND_SETTING_CARD.apply(self)

        self.card.installEventFilter(self)
        self.expandAni.valueChanged.connect(self._onExpandValueChanged)

    def addWidget(self, widget: QWidget):
        self.card.addWidget(widget)

    def wheelEvent(self, e):
        pass

    def setExpand(self, isExpand: bool):
        if self.isExpand == isExpand:
            return

        self.isExpand = isExpand
        self.setProperty('isExpand', isExpand)
        self.setStyle(QApplication.style())

        if isExpand:
            h = self.viewLayout.sizeHint().height()
            self.verticalScrollBar().setValue(h)
            self.expandAni.setStartValue(h)
            self.expandAni.setEndValue(0)
        else:
            self.expandAni.setStartValue(0)
            self.expandAni.setEndValue(self.verticalScrollBar().maximum())

        self.expandAni.start()

    def toggleExpand(self):
        self.setExpand(not self.isExpand)

    def resizeEvent(self, e):
        self.card.resize(self.width(), self.card.height())
        self.scrollWidget.resize(self.width(), self.scrollWidget.height())

    def _onExpandValueChanged(self):
        vh = self.viewLayout.sizeHint().height()
        h = self.viewportMargins().top()
        self.setFixedHeight(max(h + vh - self.verticalScrollBar().value(), h))

    def _adjustViewSize(self):
        h = self.viewLayout.sizeHint().height()
        self.spaceWidget.setFixedHeight(h)

        if self.isExpand:
            self.setFixedHeight(self.card.height()+h)
