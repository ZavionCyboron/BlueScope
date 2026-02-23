import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QThread
import faulthandler

from monitor_app.core.bus import AppBus
from monitor_app.services.worker import CollectorWorker
from monitor_app.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    faulthandler.enable()

    app.setStyleSheet("""
    QWidget {
        background-color: #1e1e1e;
        color: white;
    }
    
    QTableView {
        gridline-color: #333;
    }
    
    QHeaderView::section {
        background-color: #2a2a2a;
    }
    """)

    def excepthook(exc_type, exc, tb):
        import traceback
        traceback.print_exception(exc_type, exc, tb)

    sys.excepthook = excepthook

    bus = AppBus()

    thread = QThread(app)          # ✅ parented
    worker = CollectorWorker(bus)
    worker.moveToThread(thread)
    thread.started.connect(worker.start)
    thread.start()

    window = MainWindow(bus)
    window.show()

    def shutdown():
        try:
            worker.stop()          # ✅ stop timers
        except Exception:
            pass
        thread.quit()
        thread.wait(2000)

    app.aboutToQuit.connect(shutdown)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())