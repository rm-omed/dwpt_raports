# widgets/multi_week_input.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, QLabel
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class MultiWeekInput(QWidget):
    def __init__(self):
        super().__init__()
        self.fields = []  # List of week field dicts

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        for i in range(4):
            group = QGroupBox(f"📅 Week {i + 1}")
            group.setFont(QFont("Segoe UI", 10, QFont.Bold))
            form = QFormLayout()
            week_fields = {}

            for field_name in ["visits", "incidents", "repairs"]:
                label = field_name.capitalize()
                field = QLineEdit()
                field.setPlaceholderText(f"Enter {field_name}")
                field.setMinimumHeight(30)
                form.addRow(label, field)
                week_fields[field_name] = field

            group.setLayout(form)
            layout.addWidget(group)
            self.fields.append(week_fields)

        self.setLayout(layout)

    def get_data(self):
        result = []
        for week_fields in self.fields:
            entry = {}
            for key, widget in week_fields.items():
                entry[key] = widget.text()
            result.append(entry)
        return result

    def set_data(self, data_list):
        if not isinstance(data_list, list) or len(data_list) != 4:
            return
        for i, week_fields in enumerate(self.fields):
            for key in week_fields:
                week_fields[key].setText(data_list[i].get(key, ""))
