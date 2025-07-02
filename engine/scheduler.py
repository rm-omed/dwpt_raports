from datetime import datetime
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox


_reminder_timers = []

def start_schedule(templates):
    clear_schedule()

    for template in templates:
        reminder = template.get("reminder_time")
        if not reminder:
            continue

        try:
            hours, minutes = map(int, reminder.split(":"))
        except:
            continue

        now = datetime.now()
        reminder_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        if reminder_time < now:
            reminder_time = reminder_time.replace(day=now.day + 1)

        ms_until = int((reminder_time - now).total_seconds() * 1000)

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda t=template: show_reminder_popup(t))
        timer.start(ms_until)

        _reminder_timers.append(timer)

def clear_schedule():
    global _reminder_timers
    for timer in _reminder_timers:
        if timer.isActive():
            timer.stop()
    _reminder_timers.clear()

def show_reminder_popup(template):
    title = template.get("title", "Unnamed Report")
    msg = f"⏰ Reminder: It's time to fill the report:\n\n{title}"
    alert = QMessageBox()
    alert.setWindowTitle("⏰ Report Reminder")
    alert.setText(msg)
    alert.setStandardButtons(QMessageBox.Ok)
    alert.exec()
