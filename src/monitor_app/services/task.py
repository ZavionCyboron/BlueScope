from __future__ import annotations
from PySide6.QtCore import QRunnable, Signal, QObject

class TaskSignals(QObject):
    result = Signal(object)
    error = Signal(str)


class Task(QRunnable):
    def __init__(self, fn):
        super(Task, self).__init__()
        self.fn = fn
        self.signals = TaskSignals()

    def run(self):
        try:
            out = self.fn()
            self.signals.result.emit(out)
        except Exception as e:
            self.signals.error.emit(str(e))