from PySide6.QtCore import QObject, Signal

class AppBus(QObject):
    processes_updated = Signal(list)
    process_groups_updated = Signal(object)
    process_cpu_updated = Signal(object)
    system_updated = Signal(object)
    filter_text_changed = Signal(str)
    error = Signal(str)