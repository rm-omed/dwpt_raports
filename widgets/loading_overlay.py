from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt, QSize, Signal


class LoadingOverlay(QWidget):
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.setStyleSheet("""
            background-color: rgba(0, 0, 0, 100);  /* semi-transparent overlay */
        """)

        # Spinner
        self.spinner = QLabel()
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner.setFixedSize(200, 200)
        self.movie = QMovie("assets/spinner.gif")
        self.movie.setScaledSize(QSize(200, 200))
        self.spinner.setMovie(self.movie)

        # Labels and Button
        self.label = QLabel("⏳ Please wait...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; font-size: 16px;")

        self.progress_label = QLabel("0%")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: white; font-size: 14px;")

        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.setFixedHeight(34)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #aa3333;
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc4444;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)

        # Layout (centered content)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        layout.addWidget(self.label)
        layout.addWidget(self.spinner)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.cancel_btn)
        self.setLayout(layout)

        self.setVisible(False)

    def start(self):
        self.movie.start()
        self.setVisible(True)
        self.raise_()

    def stop(self):
        self.movie.stop()
        self.setVisible(False)

    def update_progress(self, percent: int):
        self.progress_label.setText(f"{percent}%")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
