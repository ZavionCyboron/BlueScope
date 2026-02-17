from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from monitor_app.domain.types import ProcessInfo
from dataclasses import replace


class ProcessTableModel(QAbstractTableModel):

    HEADERS = ["PID", "Name", "CPU %", "Mem (MB)", "User", "Exe"]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[ProcessInfo] = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index, role):
        if not index.isValid():
            return None

        row = self._rows[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.UserRole:
            if col == 2:  # CPU sort key
                return -1.0 if row.cpu_percent is None else float(row.cpu_percent)
            if col == 3:  # Mem sort key (so MB sorts numerically too)
                return float(row.mem_mb)
            if col == 0:  # PID sort key
                return int(row.pid)
            return None

        if role ==  Qt.ItemDataRole.DisplayRole:
            if col == 0: return row.pid
            if col == 1: return row.name
            if col == 2:
                if row.cpu_percent is None:
                    return ""
                if row.cpu_percent < 0.5:
                    return f"Idle ({row.cpu_percent:.2f}%)"
                return f"{row.cpu_percent:.1f}%"
            if col == 3: return f"{row.mem_mb:.1f}"
            if col == 4: return row.username
            if col == 5: return row.exe

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (0, 2, 3):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        return None

    def set_rows(self, rows: list[ProcessInfo]) -> None:
        # Preserve previously sampled CPU% values by PID
        old_cpu = {p.pid: p.cpu_percent for p in self._rows if p.cpu_percent is not None}

        new_rows = [
            replace(r, cpu_percent=old_cpu.get(r.pid, r.cpu_percent))
            for r in rows
        ]

        self.beginResetModel()
        self._rows = new_rows
        self.endResetModel()

    def update_cpu_map(self, cpu_by_pid: dict[int, float], sampled_pids: set[int]) -> None:
        for r, proc in enumerate(self._rows):
            if proc.pid in sampled_pids:
                new_cpu = cpu_by_pid.get(proc.pid, proc.cpu_percent)
            else:
                new_cpu = None  # ✅ not sampled => show "--"

            if proc.cpu_percent != new_cpu:
                self._rows[r] = replace(proc, cpu_percent=new_cpu)
                idx = self.index(r, 2)
                self.dataChanged.emit(idx, idx, [Qt.ItemDataRole.DisplayRole])