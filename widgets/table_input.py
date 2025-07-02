from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QPushButton,
    QHBoxLayout, QComboBox, QLineEdit, QGridLayout,
    QFileDialog, QTableWidgetItem, QTableWidget,
)
from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QGuiApplication, QIntValidator, QShortcut
from PySide6.QtWidgets import QDateEdit
import openpyxl


class CellEditor(QWidget):
    def __init__(self, text="", align="left", field_type="text",options=None):
        super().__init__()

        self.options = options or []
        self.align_combo = QComboBox()
        self.align_combo.addItems(["left", "center", "right"])
        self.align_combo.setCurrentText(align)

        if field_type == "date":
            self.input = QDateEdit()
            self.input.setCalendarPopup(True)
            self.input.setDate(QDate.currentDate())
            if text:
                parsed = QDate.fromString(text, "dd/MM/yyyy")
                if parsed.isValid():
                    self.input.setDate(parsed)
        elif field_type == "combo":
            self.input = QComboBox()
            self.input.addItems(self.options if hasattr(self, "options") else [])
            self.input.setCurrentText(text)
        else:
            self.input = QLineEdit(text)
            if field_type == "number":
                self.input.setValidator(QIntValidator())


        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.input, 0, 0)
        layout.addWidget(self.align_combo, 0, 1)
        self.setLayout(layout)

    def get_text(self):
        if isinstance(self.input, QDateEdit):
            return self.input.date().toString("dd/MM/yyyy")
        elif isinstance(self.input, QComboBox):
            return self.input.currentText()
        return self.input.text()

    def set_text(self, text):
        if isinstance(self.input, QDateEdit):
            date = QDate.fromString(text, "dd/MM/yyyy")
            if date.isValid():
                self.input.setDate(date)
        elif isinstance(self.input, QComboBox):
            index = self.input.findText(text)
            if index >= 0:
                self.input.setCurrentIndex(index)
            else:
                self.input.setCurrentText(text)
        else:
            self.input.setText(text)

    def get_align(self):
        return self.align_combo.currentText()

    def set_align(self, align):
        self.align_combo.setCurrentText(align)


class TableInput(QWidget):
    def __init__(self, columns):
        super().__init__()
        self.columns = columns  # list of dicts: [{name, type, align}]
        self.table = QTableWidget(0, len(columns))

        headers = [col["name"].capitalize() for col in columns]
        self.table.setHorizontalHeaderLabels(headers)

        # Buttons
        add_btn = QPushButton("➕ Add Row")
        add_btn.clicked.connect(self.add_row)

        remove_btn = QPushButton("➖ Remove Selected")
        remove_btn.clicked.connect(self.remove_selected)

        paste_btn = QPushButton("📋 Paste from Excel")
        paste_btn.clicked.connect(self.handle_paste)

        import_btn = QPushButton("📂 Import .xlsx")
        import_btn.clicked.connect(self.import_from_xlsx)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(paste_btn)
        btn_layout.addWidget(import_btn)

        layout = QVBoxLayout()
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.enable_paste_shortcut()

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        for col in range(self.table.columnCount()):
            col_info = self.columns[col]
            col_type = col_info.get("type", "text")
            default_align = col_info.get("align", "left")
            options = col_info.get("options", [])
            cell_widget = CellEditor(field_type=col_type, align=default_align, options=options)
            self.table.setCellWidget(row, col, cell_widget)

    def remove_selected(self):
        selected = self.table.selectionModel().selectedRows()
        for index in sorted(selected, reverse=True):
            self.table.removeRow(index.row())

    def get_data(self):
        rows = []
        for r in range(self.table.rowCount()):
            row_data = {}
            for c, col in enumerate(self.columns):
                name = col["name"]
                cell_widget = self.table.cellWidget(r, c)
                if isinstance(cell_widget, CellEditor):
                    row_data[name] = {
                        "text": cell_widget.get_text(),
                        "align": cell_widget.get_align()
                    }
            rows.append(row_data)
        return rows

    def set_data(self, rows):
        for row_data in rows:
            self.add_row()
            r = self.table.rowCount() - 1
            for c, col in enumerate(self.columns):
                name = col["name"]
                val = row_data.get(name, "")

                if isinstance(val, dict):
                    text = val.get("text", "")
                    align = val.get("align", "left")
                else:
                    text = str(val)
                    align = "left"

                cell_widget = self.table.cellWidget(r, c)
                if isinstance(cell_widget, CellEditor):
                    cell_widget.set_text(text)
                    cell_widget.set_align(align)

    def enable_paste_shortcut(self):
        paste = QShortcut(QKeySequence("Ctrl+V"), self)
        paste.activated.connect(self.handle_paste)

    def handle_paste(self):
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text()
        if not text:
            return

        rows = [line.split('\t') for line in text.strip().splitlines()]
        for row_data in rows:
            self.add_row()
            r = self.table.rowCount() - 1
            for c, cell_text in enumerate(row_data):
                if c >= self.table.columnCount():
                    break
                cell_widget = self.table.cellWidget(r, c)
                field_type = self.columns[c].get("type", "text")
                if isinstance(cell_widget, CellEditor):
                    cell_widget.set_text(cell_text.strip())
                    cell_widget.set_align("left")

    def import_from_xlsx(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx)")
        if not file_path:
            return

        wb = openpyxl.load_workbook(file_path)
        ws = wb.active

        for row in ws.iter_rows(values_only=True):
            self.add_row()
            r = self.table.rowCount() - 1
            for c, cell_value in enumerate(row):
                if c >= self.table.columnCount():
                    break
                text = str(cell_value) if cell_value is not None else ""
                cell_widget = self.table.cellWidget(r, c)
                field_type = self.columns[c].get("type", "text")
                if isinstance(cell_widget, CellEditor):
                    cell_widget.set_text(text)
                    cell_widget.set_align("left")
