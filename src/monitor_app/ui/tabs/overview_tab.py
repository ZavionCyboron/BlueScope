from __future__ import annotations

from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt

from monitor_app.core.bus import AppBus
from monitor_app.domain.types import SystemInfo

class OverviewTab(QWidget):
    def __init__(self, bus: AppBus) -> None:
        super().__init__()
        self.bus = bus

        self.cpu_label = QLabel("CPU: -- %")
        self.mem_label = QLabel("Memory: -- / -- GB (--%)")
        self.disk_label = QLabel("Disk: -- / -- GB (--%)")
        self.net_label = QLabel("Network: ↑ -- Mbps   ↓ -- Mbps")
        self.time_label = QLabel("Updated: --")

        self.cpu_bar = QProgressBar()
        self.mem_bar = QProgressBar()
        self.disk_bar = QProgressBar()

        for bar in (self.cpu_bar, self.mem_bar, self.disk_bar):
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(True)

        layout = QGridLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(QLabel("<b>System Overview</b>"), 0, 0, 1, 2)

        layout.addWidget(self.cpu_label, 1, 0)
        layout.addWidget(self.cpu_bar, 1, 1)

        layout.addWidget(self.mem_label, 2, 0)
        layout.addWidget(self.mem_bar, 2, 1)

        layout.addWidget(self.disk_label, 3, 0)
        layout.addWidget(self.disk_bar, 3, 1)

        layout.addWidget(self.net_label, 4, 0, 1, 2)
        layout.addWidget(self.time_label, 5, 0, 1, 2)

        self.setLayout(layout)

        self.bus.system_updated.connect(self.on_system_updated)

    def on_system_updated(self, info: SystemInfo) -> None:
        cpu = info.cpu_percent
        if cpu < 1.0:
            self.cpu_label.setText("CPU: Idle (<1%)")
        else:
            self.cpu_label.setText(f"CPU: {cpu:.1f} %")
        self.cpu_bar.setValue(int(round(cpu)))

        self.mem_label.setText(
            f"Memory: {info.mem_used_gb:.2f} / {info.mem_total_gb:.2f} GB ({info.mem_percent:.1f}%)"
        )
        self.mem_bar.setValue(int(round(info.mem_percent)))

        self.disk_label.setText(
            f"Disk: {info.disk_used_gb:.1f} / {info.disk_total_gb:.1f} GB ({info.disk_percent:.1}%)"
        )
        self.disk_bar.setValue(int(round(info.disk_percent)))

        self.net_label.setText(
            f"Network: ↑ {info.net_sent_mbps:.2f} Mbps   ↓ {info.net_recv_mbps:.2f} Mbps"
        )
        self.time_label.setText(f"Updated: {info.timestamp.strftime('%I:%M:%S %p').strip("0")}")