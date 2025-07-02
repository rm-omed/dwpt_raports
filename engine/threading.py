
import time
from datetime import datetime
from PySide6.QtCore import QObject, Signal
from engine.autofill import load_autofill_data
from engine.docx_filler import fill_template
from engine.exporter import docx_to_pdf
from engine.database import log_task_completion
import traceback


class ReportGenerationWorker(QObject):
    finished = Signal(str, str)
    failed = Signal(str)
    progress = Signal(int)
    cancel_requested = False

    def __init__(self, data, filename):
        super().__init__()
        self.data = data
        self.filename = filename
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self.progress.emit(10)
            if self._cancelled: return
            docx_path = fill_template(self.data, self.filename)
            self.progress.emit(50)
            if self._cancelled: return
            pdf_path = docx_to_pdf(docx_path)
            self.progress.emit(100)
            if self._cancelled: return
            self.finished.emit(docx_path, pdf_path)
        except Exception as e:
            self.failed.emit(str(e))


class ReportPreviewWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)
    progress = Signal(int)

    def __init__(self, data, filename):
        super().__init__()
        self.data = data
        self.filename = filename
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            self.progress.emit(20)
            if self._cancel: return
            docx_path = fill_template(self.data, self.filename, preview_mode=True)
            self.progress.emit(60)
            if self._cancel: return
            pdf_path = docx_to_pdf(docx_path)
            self.progress.emit(100)
            if self._cancel: return
            self.finished.emit(pdf_path)
        except Exception as e:
            self.failed.emit(str(e))


class ExportWorker(QObject):
    finished = Signal(int, int)       # (exported, skipped)
    progress = Signal(int)            # percentage 0–100
    failed = Signal(str)
    canceled = Signal()               # emitted if user cancels

    def __init__(self, templates, mode):
        super().__init__()
        self.templates = templates
        self.mode = mode
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            today = datetime.today()
            day = today.day
            weekday = today.weekday()
            month = today.month

            # ⛳ Filter templates
            to_export = []
            for t in self.templates:
                sched = t.get("schedule", {})
                if isinstance(sched, str):
                    sched = {"type": sched}

                s_type = sched.get("type", "daily")
                s_days = sched.get("days", [])
                s_months = sched.get("months", [])

                is_due = False
                if self.mode in ["all_today", "Today"]:
                    is_due = (
                        s_type == "daily"
                        or (s_type == "weekly" and weekday in s_days)
                        or (s_type == "monthly" and (day in s_days if s_days else day == 1))
                        or (s_type == "yearly" and day in s_days and month in s_months)
                        or (s_type == "semi_annual" and month in [1, 7] and day in s_days)
                    )
                elif self.mode == "This Week":
                    is_due = s_type in ["daily", "weekly"]
                elif self.mode == "Monthly":
                    is_due = s_type == "monthly"

                if is_due:
                    to_export.append(t)

            total = len(to_export)
            if total == 0 or self._cancelled:
                self.canceled.emit()
                return

            exported = 0
            skipped = 0

            for i, template in enumerate(to_export):
                if self._cancelled:
                    self.canceled.emit()
                    return

                try:
                    template_id = str(template["id"])
                    data = load_autofill_data(template_id)

                    if not data:
                        skipped += 1
                        continue

                    data["num2"] = template_id

                    if self._cancelled:
                        self.canceled.emit()
                        return

                    docx_path = fill_template(data, template["filename"])

                    if self._cancelled:
                        self.canceled.emit()
                        return

                    pdf_path = docx_to_pdf(docx_path)

                    if self._cancelled:
                        self.canceled.emit()
                        return

                    log_task_completion(template["id"], docx_path)
                    exported += 1

                except Exception as e:
                    print(f"[ERROR] Failed to export {template['filename']}: {e}")
                    print(traceback.format_exc())
                    skipped += 1

                self.progress.emit(int((i + 1) / total * 100))

            if self._cancelled:
                self.canceled.emit()
            else:
                self.finished.emit(exported, skipped)

        except Exception as e:
            error_message = f"Critical error in export worker:\n{str(e)}"
            print(error_message)
            print(traceback.format_exc())
            self.failed.emit(error_message)
