from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QFileDialog

from qfluentwidgets import (
    SettingCardGroup, PushSettingCard, FluentIcon, ScrollArea, ExpandLayout,
    qconfig, FolderValidator, QConfig, ConfigItem, OptionsConfigItem, OptionsValidator, ComboBoxSettingCard
)

from supervision.card.ExpandComboCard import ExpandComboCard


class Config(QConfig):
    saveFolder = ConfigItem("DirectoryGroup", "save", "./output", FolderValidator())
    modelFolder = ConfigItem("DirectoryGroup", "model", "./model", FolderValidator())

    model_dir = Path("./model")
    pt_files = [f.name for f in model_dir.glob("*.pt")] if model_dir.exists() else []
    default_model = pt_files[0] if pt_files else "NULL"
    modelChoice = OptionsConfigItem(
        "ModelGroup", "choice", default_model,
        OptionsValidator(pt_files if pt_files else ["NULL"])
    )

    models_db = {
        "YOLO11n": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt",
        "YOLO11s": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s.pt",
        "YOLO11m": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11m.pt",
        "YOLO11l": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11l.pt",
        "YOLO11x": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11x.pt"
    }

    models_size = {
        "YOLO11n": 5613764, "YOLO11s": 19313732, "YOLO11m": 40684120, "YOLO11l": 51387343, "YOLO11x": 114636239
    }

    ultralytics_models = {}
    for k, v in models_db.items():
        if k.lower() + ".pt" not in pt_files:
            ultralytics_models[k] = v

    modelDownload = OptionsConfigItem(
        "ModelGroup", "download", "",
        OptionsValidator(list(ultralytics_models.keys()))
    )

    def refresh_local_models(self):
        model_dir = Path(self.modelFolder.value) if hasattr(self.modelFolder, "value") else Path("./model")
        pt_files = [p.name for p in model_dir.glob("*.pt")] if model_dir.exists() else []
        self.modelChoice.validator.options = pt_files if pt_files else ["NULL"]
        self.set(self.modelChoice, pt_files[0]) if pt_files else self.set(self.modelChoice, "NULL")
        self.refresh_ultralytics_models()

    def refresh_ultralytics_models(self):
        model_dir = Path(self.modelFolder.value) if hasattr(self.modelFolder, "value") else Path("./model")
        pt_files = [p.name.lower() for p in model_dir.glob("*.pt")] if model_dir.exists() else []
        filtered = {k: v for k, v in self.models_db.items() if (k.lower() + ".pt") not in pt_files}
        self.ultralytics_models = filtered


cfg = Config()
config_path = Path(r'./config/config.json')
qconfig.load(config_path, cfg)
if not config_path.exists():
    config_path.parent.mkdir(parents=True, exist_ok=True)
    qconfig.save()


class Setting(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.setObjectName("SettingInterface")
        self.expandLayout = ExpandLayout(self.scrollWidget)

        self.modelGroup = SettingCardGroup(self.tr('Model management'), self.scrollWidget)
        self.directoryGroup = SettingCardGroup(self.tr('Directory management'), self.scrollWidget)

        self.modelFolderCard = PushSettingCard(
            self.tr('更改'),
            FluentIcon.FOLDER,
            self.tr("模型目录"),
            self.tr(" "),
            parent=self.directoryGroup
        )
        self.__updateModelFolderDescription()
        self.modelFolderCard.button.setMaximumWidth(84)
        self.modelFolderCard.button.setMinimumWidth(84)
        self.modelFolderCard.button.setStyleSheet("padding: 5px 0px;")

        self.saveFolderCard = PushSettingCard(
            self.tr('更改'),
            FluentIcon.ZIP_FOLDER,
            self.tr("保存目录"),
            self.tr(" "),
            parent=self.directoryGroup
        )
        self.__updateSaveFolderDescription()
        self.saveFolderCard.button.setMaximumWidth(84)
        self.saveFolderCard.button.setMinimumWidth(84)
        self.saveFolderCard.button.setStyleSheet("padding: 5px 0px;")

        self.modelChoiceCard = ComboBoxSettingCard(
            cfg.modelChoice,
            FluentIcon.IOT,
            self.tr("模型选择"),
            self.tr('选择标注用的模型'),
            texts=list(cfg.modelChoice.validator.options),
            parent=self.modelGroup
        )

        self.modelDownloadCard = ExpandComboCard(
            cfg.modelDownload,
            FluentIcon.DOWNLOAD,
            self.tr("模型下载"),
            self.tr('下载官方标注模型'),
            texts=list(cfg.ultralytics_models.keys()),
            parent=self.modelGroup
        )

        self.modelDownloadCard.optionSelected.connect(self.download_model)

        self.__initWidget()
        self.setObjectName('SettingInterface')

    def __initWidget(self):
        self.resize(540, 810)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self.__setQss()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.directoryGroup.addSettingCard(self.modelFolderCard)
        self.directoryGroup.addSettingCard(self.saveFolderCard)
        self.modelGroup.addSettingCard(self.modelChoiceCard)
        self.modelGroup.addSettingCard(self.modelDownloadCard)

        self.expandLayout.setSpacing(30)
        self.expandLayout.setContentsMargins(30, 15, 30, 15)
        self.expandLayout.addWidget(self.modelGroup)
        self.expandLayout.addWidget(self.directoryGroup)

    def __setQss(self):
        self.scrollWidget.setObjectName('scrollWidget')
        with open(f'./config/setting.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def __onSaveFolderCardClicked(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr("选择文件夹"), "./")
        if not folder or cfg.get(cfg.saveFolder) == folder:
            return

        cfg.set(cfg.saveFolder, folder)
        self.saveFolderCard.setContent(folder)
        qconfig.save()

    def __onModelFolderCardClicked(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr("选择文件夹"), "./")
        if not folder or cfg.get(cfg.modelFolder) == folder:
            return

        cfg.set(cfg.modelFolder, folder)
        self.modelFolderCard.setContent(folder)
        qconfig.save()

    def cnSwitchButton(self, switch):
        switch.setOnText("开启")
        switch.setOffText("关闭")
        switch.checkedChanged.connect(lambda: switch.setText(switch.onText if switch.isChecked() else switch.offText))

    def __updateSaveFolderDescription(self):
        text = self.tr(cfg.saveFolder.value)
        self.saveFolderCard.contentLabel.setText(text)

    def __updateModelFolderDescription(self):
        text = self.tr(cfg.modelFolder.value)
        self.modelFolderCard.contentLabel.setText(text)

    def __connectSignalToSlot(self):
        self.saveFolderCard.clicked.connect(self.__onSaveFolderCardClicked)
        self.modelFolderCard.clicked.connect(self.__onModelFolderCardClicked)

    def refreshCards(self):
        """ 刷新两个卡片的选项 """
        new_texts = list(cfg.modelChoice.validator.options)
        self.modelChoiceCard.comboBox.clear()
        for text in new_texts:
            self.modelChoiceCard.comboBox.addItem(text)

        current = cfg.modelChoice.value
        if current in new_texts:
            self.modelChoiceCard.comboBox.setCurrentText(current)
        else:
            if new_texts:
                cfg.set(cfg.modelChoice, new_texts[0])

        new_download_texts = list(cfg.ultralytics_models.keys())
        self.modelDownloadCard.setOptions(new_download_texts)
        if self.modelDownloadCard.dropMenu:
            self.modelDownloadCard._closeMenu()

    def download_model(self, model_name):
        url = cfg.models_db[model_name]
        size = cfg.models_size[model_name]
        name = f"{model_name.lower()}.pt"

        from supervision.card.Download import show_download_dialog
        show_download_dialog(self, url, size, name)

        cfg.refresh_local_models()
        self.refreshCards()
