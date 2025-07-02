import fitz  # PyMuPDF
from PySide6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QScrollArea,
    QHBoxLayout, QPushButton, QWidget
)
from PySide6.QtGui import QPixmap, QImage, QCursor
from PySide6.QtCore import Qt


class PDFPreviewDialog(QDialog):
    def __init__(self, pdf_path: str):
        super().__init__()
        self.setWindowTitle("📄 PDF Preview")
        self.resize(1000, 800)
        self.pdf_path = pdf_path
        self.zoom_level = 1.0

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.container_widget = QWidget()
        self.container_layout = QVBoxLayout(self.container_widget)
        self.scroll.setWidget(self.container_widget)

        self.load_images()

        zoom_in_btn = QPushButton("🔍 Zoom In")
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_out_btn = QPushButton("🔎 Zoom Out")
        zoom_out_btn.clicked.connect(self.zoom_out)
        reset_btn = QPushButton("↩ Reset")
        reset_btn.clicked.connect(self.reset_zoom)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(zoom_in_btn)
        btn_layout.addWidget(zoom_out_btn)
        btn_layout.addWidget(reset_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.scroll)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_images(self):
        self.setCursor(QCursor(Qt.WaitCursor))
        doc = fitz.open(self.pdf_path)

        # Clear previous images
        while self.container_layout.count():
            child = self.container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for page in doc:
            zoom_matrix = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=zoom_matrix)
            fmt = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
            lbl = QLabel()
            lbl.setPixmap(QPixmap.fromImage(img))
            lbl.setAlignment(Qt.AlignHCenter)
            self.container_layout.addWidget(lbl)

        doc.close()
        self.unsetCursor()

    def zoom_in(self):
        self.zoom_level += 0.2
        self.load_images()

    def zoom_out(self):
        self.zoom_level = max(0.2, self.zoom_level - 0.2)
        self.load_images()

    def reset_zoom(self):
        self.zoom_level = 1.0
        self.load_images()
