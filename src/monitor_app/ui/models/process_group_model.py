from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from monitor_app.domain.types import ProcessGroupInfo

class ProcessGroupTableModel(QAbstractTableModel):
    HEADERS = ["Name", "Group Count", "CPU %", "Mem (MB)"]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[ProcessGroupInfo] = []

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

        # Sort keys
        if role == Qt.ItemDataRole.UserRole:
            if col == 1: return int(row.count)
            if col == 2: return float(row.cpu_percent)
            if col == 3: return float(row.mem_mb)
            return row.name

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return row.name
            if col == 1: return row.count
            if col == 2:
                if row.cpu_percent < 0.5:
                    return f"Idle ({row.cpu_percent:.2f}%)"
                return f"{row.cpu_percent:.1f}%"
            if col == 3: return f"{row.mem_mb:.1f}"

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (1, 2, 3):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        return None

    def set_rows(self, rows: list[ProcessGroupInfo]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()
