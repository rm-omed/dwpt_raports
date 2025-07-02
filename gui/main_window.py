import os
import yaml
from datetime import datetime
from PySide6.QtCore import Qt, QTimer, QTime, QThread
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout,
    QListWidget, QListWidgetItem, QMessageBox, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtGui import QPixmap

from engine.threading import ExportWorker
from engine.utils import get_next_due_date
from engine.autofill import save_autofill_data, load_autofill_data
from gui.task_dialog import TaskDialog
from engine.docx_filler import fill_template
from engine.exporter import docx_to_pdf, print_file
from engine.scheduler import start_schedule
from engine.database import (
    init_db, log_task_completion,
    get_completed_template_ids, get_all_completed_tasks, clear_all_completed_tasks
)
from engine.i18n import load_language, translate, current_lang
from widgets.loading_overlay import LoadingOverlay

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        load_language("fr")
        self.setWindowTitle("📋 DWPT Report Dashboard")
        self.setMinimumSize(1000, 700)

        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.setVisible(False)

        self.templates = self.load_templates()
        self.init_ui()
        start_schedule(self.templates)

    def load_templates(self):
        with open("config/task_rules.yaml", "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            print("[DEBUG] Loaded templates:", data)
            return data.get("templates", [])

    def init_ui(self):
        old_widget = self.centralWidget()
        if old_widget:
            old_widget.setParent(None)

        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)
        self.setCentralWidget(self.main_widget)

        self.clock_label = QLabel()
        self.clock_label.setFont(QFont("Consolas", 14))
        self.clock_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.clock_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

        self.lang_switch = QPushButton("🇫🇷 / 🇩🇿")
        self.lang_switch.clicked.connect(self.toggle_language)

        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("🌍 " + translate("language")))
        lang_layout.addWidget(self.lang_switch)
        lang_layout.addStretch()
        self.layout.addLayout(lang_layout)

        title = QLabel(translate("title"))
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title)



        self.filter_buttons = {}
        filter_layout = QHBoxLayout()
        for label in ["All", "Daily", "Weekly", "Monthly", "Yearly"]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, lbl=label: self.apply_filter(lbl))
            filter_layout.addWidget(btn)
            self.filter_buttons[label] = btn
        self.filter_buttons["All"].setChecked(True)
        self.active_filter = "All"
        self.layout.addLayout(filter_layout)

        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        self.reload_template_list()

        batch_layout = QHBoxLayout()
        for label in [("📤 Export All Due Today", "Today"),
                      ("📤 Export This Week", "This Week"),
                      ("📤 Export Monthly Reports", "Monthly")]:
            btn = QPushButton(label[0])
            btn.clicked.connect(lambda _, m=label[1]: self.export_due(m))
            batch_layout.addWidget(btn)
        self.layout.addLayout(batch_layout)

        controls_layout = QHBoxLayout()
        open_btn = QPushButton("📝 " + translate("open_selected"))
        open_btn.clicked.connect(self.open_selected_template)
        history_btn = QPushButton("📊 " + translate("view_history"))
        history_btn.clicked.connect(self.show_history_view)
        controls_layout.addWidget(open_btn)
        controls_layout.addWidget(history_btn)
        self.layout.addLayout(controls_layout)

    def update_clock(self):
        self.clock_label.setText("🕒 " + QTime.currentTime().toString("hh:mm:ss"))

    def toggle_language(self):
        load_language("ar" if current_lang() == "fr" else "fr")
        self.init_ui()

    def apply_filter(self, filter_name):
        self.active_filter = filter_name
        for name, btn in self.filter_buttons.items():
            btn.setChecked(name == filter_name)
        self.reload_template_list()

    def reload_template_list(self):
        self.list_widget.clear()
        completed_ids = get_completed_template_ids()
        now = datetime.today()

        for template in self.templates:
            tid = str(template["id"])
            title = template["title"]
            sched = template.get("schedule", {})
            if isinstance(sched, str):
                sched = {"type": sched}

            s_type = sched.get("type", "daily")
            s_days = sched.get("days", [])
            s_months = sched.get("months", [])

            show = (self.active_filter == "All") or (self.active_filter.lower() == s_type)
            if not show:
                continue

            due_today = (
                (s_type == "daily") or
                (s_type == "weekly" and now.weekday() in s_days) or
                (s_type == "monthly" and (now.day in s_days if s_days else now.day == 1)) or
                (s_type == "semi_annual" and now.month in [1, 7] and now.day in s_days) or
                (s_type == "yearly" and now.day in s_days and now.month in s_months)
            )

            label = f"{'✅' if tid in completed_ids else '🔔'} {tid} - {title}"
            if due_today:
                label += "   📅 Due Today"

            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, template)
            item.setForeground(Qt.darkGreen if tid in completed_ids else Qt.red)

            next_due = get_next_due_date(sched)
            tooltip = f"{s_type.capitalize()} — Next: {next_due.strftime('%Y-%m-%d')}"
            item.setToolTip(tooltip)

            self.list_widget.addItem(item)

    def open_selected_template(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "⚠", translate("no_selection"))
            return

        template = item.data(Qt.UserRole)
        tid = str(template["id"])
        last_data = load_autofill_data(tid)

        dialog = TaskDialog(template["filename"], initial_data=last_data)
        if dialog.exec():
            self.reload_template_list()

    def export_due(self, mode):
        self.loading_overlay.label.setText(f"⏳ Exporting reports for: {mode}")
        self.loading_overlay.start()

        self.export_thread = QThread()
        self.export_worker = ExportWorker(self.templates, mode)
        self.export_worker.moveToThread(self.export_thread)

        self.export_thread.started.connect(self.export_worker.run)
        self.export_worker.progress.connect(self.loading_overlay.update_progress)
        self.export_worker.finished.connect(self.on_export_finished)
        self.export_worker.failed.connect(self.on_export_failed)
        self.export_worker.canceled.connect(self.on_export_canceled)

        self.export_worker.finished.connect(self.export_thread.quit)
        self.export_worker.finished.connect(self.export_worker.deleteLater)
        self.export_worker.canceled.connect(self.export_thread.quit)
        self.export_worker.canceled.connect(self.export_worker.deleteLater)
        self.export_thread.finished.connect(self.export_thread.deleteLater)

        self.loading_overlay.cancel_requested.connect(self.export_worker.cancel)

        self.export_thread.start()

    def on_export_finished(self, exported, skipped):
        self.loading_overlay.stop()
        QMessageBox.information(self, "✅ Export Complete", f"Exported: {exported}\nSkipped: {skipped}")
        self.reload_template_list()

    def on_export_canceled(self):
        self.loading_overlay.stop()
        QMessageBox.information(self, "❌ Cancelled", "Export was cancelled.")
        self.reload_template_list()

    def on_export_failed(self, msg):
        self.loading_overlay.stop()
        QMessageBox.critical(self, "❌ Export Failed", msg)

    def show_history_view(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(translate("view_history"))
        dialog.resize(800, 450)

        table = QTableWidget()
        history = get_all_completed_tasks()
        table.setColumnCount(3)
        table.setRowCount(len(history))
        table.setHorizontalHeaderLabels(["Template ID", "Filename", "Completed At"])

        for i, (tid, filename, ts) in enumerate(history):
            table.setItem(i, 0, QTableWidgetItem(str(tid)))
            table.setItem(i, 1, QTableWidgetItem(filename))
            table.setItem(i, 2, QTableWidgetItem(ts))

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        clear_btn = QPushButton("🗑️ " + translate("clear_history"))
        clear_btn.clicked.connect(lambda: self.confirm_clear_history(dialog, table))

        layout = QVBoxLayout()
        layout.addWidget(table)
        layout.addWidget(clear_btn)
        dialog.setLayout(layout)
        dialog.exec()

    def confirm_clear_history(self, parent_dialog, table_widget):
        if QMessageBox.question(self, "❓", translate("confirm_clear_history"),
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            clear_all_completed_tasks()
            table_widget.setRowCount(0)
            QMessageBox.information(self, translate("done"), translate("history_cleared"))
            self.reload_template_list()
            parent_dialog.accept()
