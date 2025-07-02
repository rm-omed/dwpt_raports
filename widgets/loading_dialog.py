from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication
from PySide6.QtCore import Qt, QTimer


class LoadingDialog(QDialog):
    def __init__(self, message="⏳ Generating report..."):
        super().__init__()
        self.setWindowTitle("Loading")
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(300, 100)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout()
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate progress bar

        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)
        QTimer.singleShot(0, self.center_on_parent)

    def center_on_parent(self):
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
        else:
            self.move(QApplication.primaryScreen().geometry().center() - self.rect().center())

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            parent_rect = self.parent().geometry()
            dialog_rect = self.frameGeometry()
            center_point = parent_rect.center() - dialog_rect.center()
            self.move(center_point)


