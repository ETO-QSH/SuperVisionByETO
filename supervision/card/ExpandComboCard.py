from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtWidgets import QPushButton, QAction

from qfluentwidgets import SettingCard, MenuAnimationType
from qfluentwidgets.components.widgets.combo_box import ComboBoxMenu


class ExpandComboCard(SettingCard):
    optionSelected = pyqtSignal(str)

    def __init__(self, configItem, icon, title, content=None, texts=None, parent=None):
        super().__init__(icon, title, content, parent)

        self.configItem = configItem
        self.original_texts = texts or []

        self.button = QPushButton(self.tr("展开"), self)
        self.button.setFixedHeight(32)
        self.button.setFixedWidth(108)
        self.button.setProperty("isComboBox", True)
        self.button.setProperty("isOpen", False)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.button.clicked.connect(self._onButtonClicked)

        self.dropMenu = None

    def _onButtonClicked(self):
        if self.dropMenu:
            self._closeMenu()
        else:
            self._showMenu()

    def _showMenu(self):
        self.dropMenu = ComboBoxMenu(self.button)

        for text in self.original_texts:
            action = QAction(text, self.dropMenu)
            action.triggered.connect(lambda checked=False, t=text: self._onOptionSelected(t))
            self.dropMenu.addAction(action)

        self.dropMenu.setMaxVisibleItems(8)
        self.dropMenu.closedSignal.connect(self._onMenuClosed)

        self.dropMenu.view.setMinimumWidth(self.button.width())
        self.dropMenu.view.setMaximumWidth(self.button.width())

        self.button.setProperty("isOpen", True)
        self.button.setStyle(self.button.style())

        pos = self.button.mapToGlobal(QPoint(0, self.button.height()))
        self.dropMenu.exec(pos, aniType=MenuAnimationType.DROP_DOWN)

    def _onOptionSelected(self, text: str):
        self.optionSelected.emit(text)
        self._closeMenu()

    def _onMenuClosed(self):
        self.dropMenu = None
        self.button.setProperty("isOpen", False)
        self.button.setStyle(self.button.style())

    def _closeMenu(self):
        if self.dropMenu:
            self.dropMenu.close()
            self.dropMenu = None

    def setOptions(self, texts):
        self.original_texts = texts
