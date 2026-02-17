from PySide6.QtWidgets import QMainWindow, QTabWidget

from monitor_app.core.bus import AppBus
from monitor_app.ui.tabs.overview_tab import OverviewTab
from monitor_app.ui.tabs.processes_tab import ProcessesTab

class MainWindow(QMainWindow):

    def __init__(self, bus: AppBus) -> None:
        super().__init__()
        self.setWindowTitle("Advanced Task Manager")
        self.resize(1200, 700)

        tabs = QTabWidget()
        tabs.addTab(OverviewTab(bus), "Overview")
        tabs.addTab(ProcessesTab(bus), "Processes")

        self.setCentralWidget(tabs)