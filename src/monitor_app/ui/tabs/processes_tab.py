from PySide6.QtWidgets import (
QWidget, QVBoxLayout,
QLineEdit, QTableView, QLabel,
QHeaderView
)
from PySide6.QtCore import QSortFilterProxyModel, Qt, QRegularExpression
from PySide6.QtWidgets import QCheckBox

from monitor_app.core.bus import AppBus
from monitor_app.ui.models.process_model import ProcessTableModel
from monitor_app.ui.models.process_group_model import ProcessGroupTableModel

class ProcessesTab(QWidget):
    def __init__(self, bus: AppBus) -> None:
        super().__init__()
        self.bus = bus

        self.model = ProcessTableModel()
        self.model_group = ProcessGroupTableModel()

        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(1)

        self.group_toggle = QCheckBox("Group by name")
        self.group_toggle.toggled.connect(self._set_grouped)

        self.search = QLineEdit()
        self.search.setPlaceholderText("filter processes...")
        self.search.textChanged.connect(self._on_filter)

        self.table = QTableView()
        self.table.setModel(self.proxy)

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSortingEnabled(True)
        self.table.sortByColumn(2, Qt.SortOrder.DescendingOrder)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.status = QLabel("")

        layout = QVBoxLayout(self)
        layout.addWidget(self.group_toggle)
        layout.addWidget(self.search)
        layout.addWidget(self.table)
        layout.addWidget(self.status)

        self.bus.processes_updated.connect(self._on_update)
        self.bus.process_cpu_updated.connect(self._on_cpu_update)
        self.bus.process_groups_updated.connect(self._on_update_group)
        self.bus.error.connect(self.status.setText)

        self._apply_header_modes(False)

    def _set_grouped(self, on: bool) -> None:
        self.proxy.setSourceModel(self.model_group if on else self.model)
        self._apply_header_modes(on)

        # Reapply filter
        self._on_filter(self.search.text())

        # Default sort by CPU desc (column 2 in BOTH models)
        self.proxy.sort(2, Qt.SortOrder.DescendingOrder)

    def _on_update(self, rows):
        if self.group_toggle.isChecked():
            return
        sorting = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)
        self.model.set_rows(rows)
        self.table.setSortingEnabled(sorting)

    def _on_cpu_update(self, payload):
        if self.group_toggle.isChecked():
            return
        cpu_by_pid, sampled_pids = payload
        self.model.update_cpu_map(cpu_by_pid, sampled_pids)

    def _on_update_group(self, rows):
        if not self.group_toggle.isChecked():
            return
        self.model_group.set_rows(rows)
        self.status.setText(f"Groups: {len(rows)}")

    def _on_filter(self, text: str):
        pattern = QRegularExpression.escape(text)
        self.bus.filter_text_changed.emit(text)
        self.proxy.setFilterRegularExpression(QRegularExpression(pattern))

    def _apply_header_modes(self, grouped: bool) -> None:
        header = self.table.horizontalHeader()
        if grouped:
            # ["Name", "Count", "CPU %", "Mem (MB)"]
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        else:
            # ["PID","Name","CPU %","Mem","User","Exe"]
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        