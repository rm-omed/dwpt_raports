import os
import sys

import app
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # ✅ Set app-wide icon
    icon_path = os.path.join("assets", "logo.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()  # <- This is essential!
    sys.exit(app.exec())  # <- Keeps the app running

if __name__ == "__main__":
    main()


app.setStyleSheet("""
    QMainWindow {
        background-color: #f9f9f9;
    }
    QPushButton {
        background-color: #3498db;
        color: white;
        border-radius: 6px;
    }
    QPushButton:hover {
        background-color: #2980b9;
    }
    QLineEdit, QComboBox, QDateEdit {
        padding: 5px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }
""")
