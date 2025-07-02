import os, yaml
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout,
    QComboBox, QDateEdit, QHBoxLayout, QMessageBox, QScrollArea, QWidget
)
from PySide6.QtCore import QDate, Qt, QThread, QTimer
from PySide6.QtGui import QFont, QPalette, QColor

from engine.autofill import load_autofill_data, clear_autofill_data, save_autofill_data
from widgets.table_input import TableInput
from engine.i18n import translate
from gui.pdf_preview_dialog import PDFPreviewDialog
from widgets.loading_overlay import LoadingOverlay
from engine.threading import ReportGenerationWorker, ReportPreviewWorker

class TaskDialog(QDialog):
    def __init__(self, template_filename=None, initial_data=None):
        super().__init__()
        self.template_filename = template_filename
        self.template_id = initial_data.get("num2") if initial_data else None
        self.fields = {}

        self.setWindowTitle("📝 " + translate("fill_report"))
        self.resize(900, 700)
        self.setMinimumSize(700, 500)

        self._cancelled = False
        self.thread = None
        self.worker = None

        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.raise_()
        self.loading_overlay.setVisible(False)
        self.loading_overlay.cancel_requested.connect(self.cancel_current_operation)

        self.config = self.load_field_config(template_filename)
        self.build_form(self.config, initial_data)

    def load_field_config(self, template_filename):
        with open("config/template_fields.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get(template_filename, [])

    def build_form(self, config, initial_data):
        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        font = QFont("Segoe UI", 11)

        for field in config:
            name = field["name"]
            field_type = field["type"]
            widget = None

            if field_type == "text":
                widget = QLineEdit()
                widget.setFont(font)
                widget.setMinimumHeight(32)
                if initial_data and name in initial_data:
                    widget.setText(initial_data[name])
            elif field_type == "combo":
                widget = QComboBox()
                widget.setFont(font)
                widget.setMinimumHeight(32)
                pal = widget.palette()
                pal.setColor(QPalette.Base, QColor("white"))
                widget.setPalette(pal)
                widget.addItems(field.get("options", []))
                if initial_data and name in initial_data:
                    idx = widget.findText(initial_data[name])
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
            elif field_type == "date":
                widget = QDateEdit()
                widget.setFont(font)
                widget.setMinimumHeight(32)
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate())
                if initial_data and name in initial_data:
                    for fmt in ["yyyy/MM/dd", "dd/MM/yyyy"]:
                        date_obj = QDate.fromString(initial_data[name], fmt)
                        if date_obj.isValid():
                            widget.setDate(date_obj)
                            break
            elif field_type == "table":
                widget = TableInput(field.get("columns", []))
                if initial_data and name in initial_data:
                    widget.set_data(initial_data[name])
            elif field_type == "multiweek":
                from widgets.multi_week_input import MultiWeekInput
                widget = MultiWeekInput()
                if initial_data and name in initial_data:
                    widget.set_data(initial_data[name])

            if widget:
                self.fields[name] = widget
                label = translate(name.replace("_", " ").capitalize())
                form_layout.addRow(label, widget)

        # Buttons
        self.autofill_button = QPushButton("🧠 " + translate("use_last_values"))
        self.clear_button = QPushButton("🗑️ " + translate("clear_last_values"))
        self.submit_button = QPushButton("✅ " + translate("generate_report"))
        self.preview_button = QPushButton("👁 Preview")

        for btn in [self.autofill_button, self.clear_button, self.submit_button, self.preview_button]:
            btn.setFont(font)
            btn.setMinimumHeight(36)

        self.autofill_button.clicked.connect(self.apply_autofill)
        self.clear_button.clicked.connect(self.clear_autofill)
        self.submit_button.clicked.connect(self.generate_report_threaded)
        self.preview_button.clicked.connect(self.preview_report_threaded)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.autofill_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.preview_button)

        scroll_widget = QWidget()
        scroll_widget.setLayout(form_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        main_layout.addWidget(scroll_area)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def get_data(self):
        data = {}
        for key, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                data[key] = widget.text()
            elif isinstance(widget, QComboBox):
                data[key] = widget.currentText()
            elif isinstance(widget, QDateEdit):
                data[key] = widget.date().toString("dd/MM/yyyy")
            elif hasattr(widget, 'get_data'):
                data[key] = widget.get_data()

        if "number" in data and data["number"].isdigit() and not data.get("num2"):
            data["num2"] = str(int(data["number"]) + 1)

        # ✅ Ensure fallback to self.template_id
        if not data.get("num2"):
            data["num2"] = self.template_id or "unknown"

        return data

    def apply_autofill(self):
        tid = self.fields.get("num2").text() if "num2" in self.fields else self.template_id
        if not tid:
            QMessageBox.information(self, translate("no_id"), translate("template_id_not_found"))
            return
        data = load_autofill_data(tid)
        for key, value in data.items():
            widget = self.fields.get(key)
            if not widget:
                continue
            if isinstance(widget, QLineEdit):
                widget.setText(value)
            elif isinstance(widget, QComboBox):
                idx = widget.findText(value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            elif isinstance(widget, QDateEdit):
                for fmt in ["yyyy/MM/dd", "dd/MM/yyyy"]:
                    date_obj = QDate.fromString(value, fmt)
                    if date_obj.isValid():
                        widget.setDate(date_obj)
                        break

    def clear_autofill(self):
        tid = self.fields.get("num2").text() if "num2" in self.fields else self.template_id
        if not tid:
            QMessageBox.information(self, translate("no_id"), translate("template_id_not_found"))
            return
        clear_autofill_data(tid)
        QMessageBox.information(self, translate("cleared"), translate("autofill_cleared_for").format(tid))

    def cancel_current_operation(self):
        self._cancelled = True
        if self.worker:
            self.worker.cancel()
        self.loading_overlay.label.setText("❌ Operation cancelled")
        QTimer.singleShot(1000, self.loading_overlay.stop)

    def generate_report_threaded(self):
        self._cancelled = False
        data = self.get_data()
        if not data.get("num2"):
            data["num2"] = self.template_id or "0"

        self.loading_overlay.label.setText("⏳ Generating report...")
        self.loading_overlay.start()

        self.thread = QThread()
        self.worker = ReportGenerationWorker(data, self.template_filename)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.loading_overlay.update_progress)
        self.worker.finished.connect(self.on_report_generated)
        self.worker.failed.connect(self.on_report_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.loading_overlay.cancel_requested.connect(self.worker.cancel)

        self.thread.start()

    def preview_report_threaded(self):
        self._cancelled = False
        data = self.get_data()
        if not data.get("num2"):
            data["num2"] = self.template_id or "0"

        self.loading_overlay.label.setText("👁 Generating preview...")
        self.loading_overlay.start()

        self.thread = QThread()
        self.worker = ReportPreviewWorker(data, self.template_filename)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.loading_overlay.update_progress)
        self.worker.finished.connect(self.on_preview_ready)
        self.worker.failed.connect(self.on_report_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.loading_overlay.cancel_requested.connect(self.worker.cancel)

        self.thread.start()

    def on_report_generated(self, docx_path, pdf_path):
        self.loading_overlay.stop()
        if self._cancelled:
            self.reject()
            return

        msg = QMessageBox(self)
        msg.setWindowTitle(translate("report_generated"))
        msg.setText(f"DOCX:\n{docx_path}\nPDF:\n{pdf_path}")
        msg.setStandardButtons(QMessageBox.Open | QMessageBox.Yes | QMessageBox.Cancel)
        msg.button(QMessageBox.Open).setText(translate("folder"))
        msg.button(QMessageBox.Yes).setText(translate("print"))
        msg.button(QMessageBox.Cancel).setText(translate("cancel"))
        result = msg.exec()



        if result == QMessageBox.Open:
            os.startfile(os.path.dirname(pdf_path))
        elif result == QMessageBox.Yes:
            from engine.exporter import print_file
            print_file(docx_path)

         # ✅ Save autofill data
        template_id = self.template_id or self.get_data().get("num2")
        save_autofill_data(template_id, self.get_data())

    def on_preview_ready(self, pdf_path):
        self.loading_overlay.stop()
        if self._cancelled:
            return
        dialog = PDFPreviewDialog(pdf_path)
        dialog.exec()
        try:
            QTimer.singleShot(3000, lambda: os.remove(pdf_path))
        except Exception:
            pass

    def on_report_failed(self, error_msg):
        self.loading_overlay.stop()
        QMessageBox.critical(self, "❌ Error", f"Operation failed:\n{error_msg}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.loading_overlay:
            self.loading_overlay.setGeometry(self.rect())
