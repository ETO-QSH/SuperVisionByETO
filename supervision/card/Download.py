import os
import time
import httpx

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtGui import QFont

from qfluentwidgets import MessageBoxBase, SubtitleLabel, InfoBar, InfoBarPosition, ProgressBar, StrongBodyLabel

from supervision.card.Setting import cfg


class DownloadWorker(QThread):
    progressChanged = pyqtSignal(int)
    speedChanged = pyqtSignal(str)
    timeChanged = pyqtSignal(str)
    downloadFinished = pyqtSignal()
    downloadError = pyqtSignal(str)

    def __init__(self, url, totalSize, fileName, parent=None):
        super().__init__(parent)
        self.url = url
        self.totalSize = totalSize
        self.fileName = fileName
        self._is_running = True

    def run(self):
        try:
            with httpx.stream("GET", self.url, follow_redirects=True) as response:
                response.raise_for_status()
                total_size = self.totalSize
                downloaded_size = 0
                start_time = time.time()

                with open(os.path.join(cfg.get(cfg.modelFolder), self.fileName), 'wb') as f:
                    for chunk in response.iter_bytes():
                        if not self._is_running:
                            break
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            progress = int(100 * downloaded_size / total_size) if total_size > 0 else 0
                            self.progressChanged.emit(progress)

                            elapsed_time = time.time() - start_time
                            elapsed_time = max(1e-6, elapsed_time)
                            bytes_per_sec = downloaded_size / elapsed_time
                            speed_text = format_speed(bytes_per_sec)
                            self.speedChanged.emit(speed_text)

                        remaining = (total_size - downloaded_size) / bytes_per_sec if bytes_per_sec > 0 else 0

                        mins, secs = divmod(remaining, 60)
                        time_text = f"{int(mins)}分{int(secs)}秒"
                        self.timeChanged.emit(time_text)

                if self._is_running:
                    self.downloadFinished.emit()

        except Exception as e:
            self.downloadError.emit(str(e))

        finally:
            self._is_running = False

    def stop(self):
        self._is_running = False


class DownloadWindow(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.url = None
        self.totalSize = None
        self.fileName = None

        self.downloadThread = None
        self.download_success = False
        self.cancelButton.setVisible(False)

        self.yesButton.setText("取 消 下 载")
        self.yesButton.setFont(QFont('萝莉体', 10))
        self.yesButton.clicked.disconnect()
        self.yesButton.clicked.connect(self._handle_cancel)

        self._init_widgets()
        self._setup_layout()

    def _init_widgets(self):
        self.titleLabel = SubtitleLabel("文件下载")
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setFixedSize(240, 30)

        self.speedLabel = StrongBodyLabel("计算中...")
        self.speedLabel.setAlignment(Qt.AlignLeft)

        self.timeLabel = StrongBodyLabel("计算中...")
        self.speedLabel.setAlignment(Qt.AlignRight)

        self.infoLayout = QHBoxLayout()
        self.infoLayout.addStretch(1)
        self.infoLayout.addWidget(self.speedLabel, 0, Qt.AlignLeft)
        self.infoLayout.addStretch(1)
        self.infoLayout.addWidget(self.timeLabel, 0, Qt.AlignRight)
        self.infoLayout.addStretch(1)

        self.progressBar = ProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

    def _setup_layout(self):
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(15)
        self.viewLayout.addWidget(self.progressBar)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addLayout(self.infoLayout)

    def setDownloadUrl(self, url, totalSize, fileName):
        self.url = url
        self.totalSize = totalSize
        self.fileName = fileName

    def startDownload(self):
        self.downloadThread = DownloadWorker(self.url, self.totalSize, self.fileName)
        self.downloadThread.progressChanged.connect(self.progressBar.setValue)
        self.downloadThread.speedChanged.connect(lambda s: self.speedLabel.setText(f"{s}"))
        self.downloadThread.timeChanged.connect(lambda t: self.timeLabel.setText(f"{t}"))
        self.downloadThread.downloadFinished.connect(self._download_success)
        self.downloadThread.downloadError.connect(self._show_error)
        self.downloadThread.start()
        self.exec_()
        return self.download_success

    def _handle_cancel(self):
        if self.downloadThread and self.downloadThread.isRunning():
            self.downloadThread.stop()
            self.downloadThread.quit()
            self.downloadThread.wait(3000)

        InfoBar.warning(
            title="下载已取消",
            content="用户中断了下载过程",
            parent=self.parent(),
            duration=3000,
            position=InfoBarPosition.TOP
        )

        super().reject()

    def _download_success(self):
        self.accept()

        InfoBar.success(
            title="下载完成",
            content="模型文件已保存",
            parent=self.parent(),
            duration=3000,
            position=InfoBarPosition.TOP
        )

        self.download_success = True

    def _show_error(self, message):
        InfoBar.error(
            title="下载错误",
            content=message,
            parent=self.parent(),
            duration=3000,
            position=InfoBarPosition.TOP
        )
        self.reject()


def format_speed(bytes_per_sec):
    if bytes_per_sec is None or bytes_per_sec <= 0:
        return "0 B/s"

    units = ["B", "KB", "MB"]
    val = float(bytes_per_sec)
    unit_idx = 0

    while val >= 1000 and unit_idx < len(units) - 1:
        val /= 1024.0
        unit_idx += 1
    unit = units[unit_idx]

    int_part = int(abs(val))
    int_len = len(str(int_part)) if int_part != 0 else 0

    decimals = 0 if int_len >= 4 else max(0, min(3, 4 - int_len))
    fmt = f"{{:.{decimals}f}}".format(val)
    return f"{fmt} {unit}/s"


def show_download_dialog(parent, url, totalSize, fileName):
    window = DownloadWindow(parent)
    window.setDownloadUrl(url, totalSize, fileName)
    return window.startDownload()
