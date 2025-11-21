import os
import time
import zipfile
import threading
from pathlib import Path

from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QGridLayout, QWidget, QVBoxLayout, QFileDialog

from qfluentwidgets import (
    ConfigItem, SimpleCardWidget, TeachingTip, TeachingTipTailPosition,
    FluentIcon, InfoBar, InfoBarPosition, PushButton, ToolButton
)

from supervision.card.FileListSettingCard import FileListSettingCard
from supervision.card.FilesDropWidget import FilesDropWidget
from supervision.tool import process_files_threaded, clear_processed_cache
from supervision.card.PixmapShow import DIDshow
from supervision.utils import resource_path
from supervision.card.Setting import cfg


class MainInterface(QWidget):
    processingFinished = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MainInterface")
        self.resize(720, 560)

        self.font_id = QFontDatabase.addApplicationFont(resource_path(r".\src\Lolita.ttf"))
        if self.font_id != -1:
            self.font_family = QFontDatabase.applicationFontFamilies(self.font_id)[0]
            self.font_20 = QFont(self.font_family)
            self.font_20.setPixelSize(20)
        else:
            print("Failed to load font")

        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        main_layout.setRowStretch(0, 1)
        main_layout.setRowStretch(1, 0)
        main_layout.setRowStretch(2, 0)
        main_layout.setRowStretch(3, 0)
        main_layout.setRowStretch(4, 1)

        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 0)
        main_layout.setColumnStretch(2, 0)
        main_layout.setColumnStretch(3, 0)
        main_layout.setColumnStretch(4, 1)

        self.FilesDropWidget = FilesDropWidget(file_types=[".png", ".jpg"])
        self.FilesDropWidget.setFixedSize(360, 120)
        self.FilesDropWidget.setObjectName("FilesDropWidget")
        main_layout.addWidget(self.FilesDropWidget, 3, 1, 1, 1, alignment=Qt.AlignCenter)

        self.FileListSettingCardWidget = FileListSettingCard(
            ConfigItem("ModelFiles", "Path", ""),
            title="选择图片文件",
            content="添加图片文件（*.png, *.jpg）",
            directory="./"
        )
        self.FileListSettingCardWidget.setFixedSize(360, 420)
        self.FileListSettingCardWidget.setObjectName("FileListSettingCardWidget")
        main_layout.addWidget(self.FileListSettingCardWidget, 1, 1, 1, 1, alignment=Qt.AlignCenter)

        self.FilesDropWidget.bindFileListSettingCard(self.FileListSettingCardWidget)
        self.FileListSettingCardWidget.fileClicked.connect(self.on_file_clicked)

        self._prev_files = []
        self.FileListSettingCardWidget.filesChanged.connect(self.on_files_changed)

        self.rightCard1 = SimpleCardWidget()
        self.rightCard1.setFixedSize(360, 420)
        self.rightCard1.setObjectName("rightCard1")

        self.didshow = DIDshow(300, 360)
        self.didshow.setFixedSize(300, 360)
        self.didshow.imageRightClicked.connect(self._on_didshow_right_click)

        card_layout1 = QVBoxLayout(self.rightCard1)
        card_layout1.addWidget(self.didshow, alignment=Qt.AlignCenter)
        self.rightCard1.setLayout(card_layout1)
        main_layout.addWidget(self.rightCard1, 1, 3, 1, 1, alignment=Qt.AlignCenter)

        self.rightCard2 = QWidget(self)
        self.rightCard2.setFixedSize(360, 120)
        self.rightCard2.setObjectName("rightCard2")

        self.btn_start = PushButton("   开 始 标 注")
        self.btn_start.setIcon(FluentIcon.BRUSH)
        self.btn_start.setFont(self.font_20)
        self.btn_start.setFixedSize(180, 60)
        self.btn_start.setIconSize(QSize(32, 32))
        self.btn_start.setObjectName("btn_start")
        self.btn_start.clicked.connect(self.btn_start_clicked)

        self.btn_clear = ToolButton(FluentIcon.DELETE, self)
        self.btn_clear.setFixedSize(60, 60)
        self.btn_clear.setIconSize(QSize(24, 24))
        self.btn_clear.setObjectName("btn_clear")
        self.btn_clear.clicked.connect(self.btn_clear_clicked)

        self.btn_save = ToolButton(FluentIcon.SAVE, self)
        self.btn_save.setFixedSize(60, 60)
        self.btn_save.setIconSize(QSize(24, 24))
        self.btn_save.setObjectName("btn_save")
        self.btn_save.clicked.connect(self.btn_save_clicked)

        card_layout2 = QGridLayout()
        card_layout2.setContentsMargins(12, 12, 12, 12)
        card_layout2.setSpacing(12)

        card_layout2.addWidget(self.btn_clear, 1, 1, alignment=Qt.AlignCenter)
        card_layout2.addWidget(self.btn_start, 1, 2, alignment=Qt.AlignCenter)
        card_layout2.addWidget(self.btn_save, 1, 3, alignment=Qt.AlignCenter)

        self.rightCard2.setLayout(card_layout2)
        main_layout.addWidget(self.rightCard2, 3, 3, 1, 1, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

        self.processingFinished.connect(self._on_processing_finished)

    def on_file_clicked(self, idx: int):
        self.didshow.go_to_by_id(idx + 1)
        path = self.FileListSettingCardWidget.files[idx]
        print(f"Clicked index {idx}: {Path(path).name}")

    def on_files_changed(self, new_files):
        self._prev_files = new_files.copy()

    def btn_start_clicked(self):
        indices = []
        files_payload = []
        files = self.FileListSettingCardWidget.files

        for i, p in enumerate(files):
            if p:
                indices.append(i + 1)
                files_payload.append(p)

        if not indices:
            TeachingTip.create(target=self.btn_start, parent=self, title="提示", content="没有可处理的图片")
            return

        self.btn_start.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.btn_start.setText("   处 理 中 ...")

        def worker():
            try:
                result = process_files_threaded(indices, files_payload, max_workers=4, model=None, extra_args=None)
            except Exception as e:
                result = []
                print("process_files_threaded error:", e)
            self.processingFinished.emit(result)

        threading.Thread(target=worker, daemon=True).start()

    def _on_processing_finished(self, results):
        for ind, outp in results:
            try:
                self.didshow.addImage(ind, outp)
            except Exception as e:
                print(f"Failed to add image {ind}: {e}")

        if results:
            self.createSuccessInfoBar()

        self.btn_start.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.btn_save.setEnabled(True)
        self.btn_start.setText("   开 始 标 注")

    def _on_didshow_right_click(self, image_path):
        TeachingTip.create(
            target=self, parent=self, duration=-1, isClosable=True, image=image_path,
            title=f"{Path(image_path).name}",
            content=f"标注使用模型：{cfg.get(cfg.modelChoice)}",
            tailPosition=TeachingTipTailPosition.BOTTOM,
        )

    def btn_clear_clicked(self):
        try:
            self.FileListSettingCardWidget.clear_files()
        except Exception as e:
            print("clear FileListSettingCard failed:", e)
        try:
            self.didshow.clear_all()
        except Exception as e:
            print("clear DIDshow failed:", e)
        try:
            clear_processed_cache()
        except Exception as e:
            print("clear processed cache failed:", e)

        TeachingTip.create(target=self.btn_clear, parent=self, title="数据清空", content="索引已重置", duration=2000)

    def btn_save_clicked(self):
        pairs = []
        missing = []
        files = self.FileListSettingCardWidget.files

        for i, src in enumerate(files):
            if not src:
                continue
            ind = i + 1
            res = self.didshow.images.get(ind)
            if not res:
                missing.append(ind)
            else:
                pairs.append((ind, src, res))

        if missing:
            TeachingTip.create(
                target=self.btn_save, parent=self, title="未完成处理",
                content=f"以下索引尚未处理：{missing}",
                tailPosition=TeachingTipTailPosition.BOTTOM,
                duration=3000
            )
            return

        if not pairs:
            TeachingTip.create(
                target=self.btn_save, parent=self, title="没有文件",
                content="没有可打包的图片",
                tailPosition=TeachingTipTailPosition.BOTTOM,
                duration=2000
            )
            return

        f_name = f"output_{str(time.ctime()).replace(' ', '_').replace(':', '_')}.zip"
        path, _ = QFileDialog.getSaveFileName(self, "保存为 ZIP 文件", str(Path.cwd() / f_name), "Zip Files (*.zip)")

        if not path:
            return
        if not path.lower().endswith(".zip"):
            path += ".zip"

        try:
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
                for ind, src, res in pairs:

                    try:
                        arc_src = os.path.join("src", Path(src).name)
                        z.write(src, arcname=arc_src)
                    except Exception as e:
                        print(f"add src failed for {src}: {e}")

                    try:
                        arc_res = os.path.join("res", Path(res).name)
                        z.write(res, arcname=arc_res)
                    except Exception as e:
                        print(f"add res failed for {res}: {e}")

        except Exception as e:
            TeachingTip.create(
                target=self.btn_save, parent=self, title="打包失败",
                content=f"保存 ZIP 失败：{e}",
                tailPosition=TeachingTipTailPosition.BOTTOM,
                duration=3000
            )
            return

        TeachingTip.create(
            target=self.btn_save, parent=self, title="已保存",
            content=f"已保存至：{path}",
            tailPosition=TeachingTipTailPosition.BOTTOM,
            duration=3000
        )

    def createSuccessInfoBar(self):
        InfoBar.success(
            title='Success',
            content="已完成全部标注！",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2500,
            parent=self
        )
