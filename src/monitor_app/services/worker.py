from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Slot, QThreadPool

from monitor_app.core.bus import AppBus
from monitor_app.core.scheduler import PROCESS_REFRESH_MS, SYSTEM_REFRESH_MS, TOP_CPU_PIDS, PROCESS_CPU_REFRESH_MS
from monitor_app.services.collectors.process_collector import ProcessCollector
from monitor_app.services.collectors.system_collector import SystemCollector
from monitor_app.services.task import Task
from monitor_app.domain.types import ProcessGroupInfo
from collections import deque

class CollectorWorker(QObject):
    def __init__(self, bus: AppBus) -> None:
        super().__init__()
        self.bus = bus

        # Keep collectors, but don't do heavy work in __init__
        self.process_collector = ProcessCollector()
        self.system_collector = SystemCollector()

        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(1)

        self._process_timer: QTimer | None = None
        self._system_timer: QTimer | None = None
        self._cpu_timer: QTimer | None = None
        self._cpu_delay_ms = PROCESS_CPU_REFRESH_MS

        self._latest_rows = []
        self._process_running = False
        self._system_running = False
        self._cpu_running = False
        self._cpu_primed_pids: set[int]= set()

        self._cpu_hist: dict[int, deque[float]] = {}
        self._cpu_hist_len = 4  # ~2 seconds if CPU tick is 500ms
        self._cpu_smoothed: dict[int, float] = {}  # pid -> smoothed cpu

        self._filter_text = ""
        self.bus.filter_text_changed.connect(lambda t: setattr(self, "_filter_text", t))

    @Slot()
    def start(self) -> None:
        self._system_timer = QTimer(self)
        self._system_timer.setInterval(SYSTEM_REFRESH_MS)
        self._system_timer.timeout.connect(self._kick_system)
        self._system_timer.start()

        self._process_timer = QTimer(self)
        self._process_timer.setInterval(PROCESS_REFRESH_MS)
        self._process_timer.timeout.connect(self._kick_processes)
        self._process_timer.start()

        self._cpu_timer = QTimer(self)
        self._cpu_timer.setSingleShot(True)
        self._cpu_timer.timeout.connect(self._kick_process_cpu)
        self._cpu_timer.start(self._cpu_delay_ms)

        # Run quickly after UI paints
        QTimer.singleShot(0, self._kick_system)
        QTimer.singleShot(200, self._kick_processes)

    @Slot()
    def stop(self):
        if self._system_timer: self._system_timer.stop()
        if self._process_timer: self._process_timer.stop()
        if self._cpu_timer: self._cpu_timer.stop()

    def _kick_system(self) -> None:
        if self._system_running:
            return
        self._system_running = True

        task = Task(self.system_collector.collect)
        task.signals.result.connect(self._on_system)
        task.signals.error.connect(lambda msg: self._on_error(f"System collection failed: {msg}"))
        self.pool.start(task)

    def _kick_processes(self) -> None:
        if self._process_running:
            return
        self._process_running = True

        task = Task(self.process_collector.collect_fast)
        task.signals.result.connect(self._on_processes)
        task.signals.error.connect(lambda msg: self._on_error(f"Process collection failed: {msg}"))
        self.pool.start(task)

    def _kick_process_cpu(self) -> None:
        if self._cpu_running or not self._latest_rows:
            return

        top = sorted(self._latest_rows, key=lambda p: p.mem_mb, reverse=True)[:TOP_CPU_PIDS]
        pids = [p.pid for p in top]

        to_prime = [pid for pid in pids if pid not in self._cpu_primed_pids]
        if to_prime:
            self._cpu_primed_pids.update(to_prime)
            task = Task(lambda: self.process_collector.sample_cpu_for_pids(to_prime))
            task.signals.result.connect(lambda _: self._on_cpu_primed(pids))
            task.signals.error.connect(lambda m: self._on_error(f"CPU prime failed: {m}"))
            self.pool.start(task)
            return

        task = Task(lambda: self.process_collector.sample_cpu_for_pids(pids))
        task.signals.result.connect(self._on_cpu_map)
        task.signals.error.connect(lambda m: self._on_error(f"Process CPU failed: {m}"))
        self.pool.start(task)

    def _on_system(self, info) -> None:
        self._system_running = False
        self.bus.system_updated.emit(info)

    def _on_processes(self, processes) -> None:
        self._latest_rows = processes
        print("SET _latest_rows len=", len(self._latest_rows))
        self._process_running = False
        self.bus.processes_updated.emit(processes)

        self.bus.process_groups_updated.emit((self._build_groups()))

        QTimer.singleShot(0, self._kick_process_cpu)

    def _on_cpu_map(self, cpu_by_pid) -> None:
        self._cpu_running = False
        self._update_cpu_smoothing(cpu_by_pid)

        smoothed_subset = {pid: self._cpu_smoothed.get(pid, v) for pid, v in cpu_by_pid.items()}
        self.bus.process_cpu_updated.emit((smoothed_subset, self._cpu_primed_pids))

        # grouped refresh at CPU cadence
        if self._latest_rows:
            self.bus.process_groups_updated.emit(self._build_groups())

        # if you're using single-shot CPU timer, restart it here
        if getattr(self, "_cpu_timer", None):
            self._cpu_timer.start(self._cpu_delay_ms)
    def _on_cpu_primed(self, pids: list[int]) -> None:
        task = Task(lambda: self.process_collector.sample_cpu_for_pids(pids))
        task.signals.result.connect(self._on_cpu_map)
        task.signals.error.connect(lambda m: self._on_error(f"Process CPU failed: {m}"))
        self.pool.start(task)

    def _update_cpu_smoothing(self, cpu_by_pid: dict[int, float]) -> None:
        dead = []
        for pid, v in cpu_by_pid.items():
            q = self._cpu_hist.get(pid)
            if q is None:
                q = deque(maxlen=self._cpu_hist_len)
                self._cpu_hist[pid] = q
            q.append(float(v))
            self._cpu_smoothed[pid] = sum(q) / len(q)

    def _build_groups(self) -> list[ProcessGroupInfo]:
        groups: dict[str, dict[str, float | int]] = {}
        for p in self._latest_rows:
            name = (p.name or "").strip() or "<unknown>"
            g = groups.get(name)
            if g is None:
                g = {"count": 0, "cpu": 0.0, "mem": 0.0}
                groups[name] = g

            g["count"] += 1
            g["mem"] += float(p.mem_mb)

            g["cpu"] += float(self._cpu_smoothed.get(p.pid, 0.0))

        out: list[ProcessGroupInfo] = []
        for name, g in groups.items():
            out.append(ProcessGroupInfo(
                name=name,
                count=int(g["count"]),
                cpu_percent=float(g["cpu"]),
                mem_mb=float(g["mem"])
            ))
        return out

    def _on_error(self, msg: str) -> None:
        # Clear flags so timers can retry
        self._system_running = False
        self._process_running = False
        self._cpu_running = False
        self.bus.error.emit(msg)
        if self._cpu_timer:
            self._cpu_timer.start(self._cpu_delay_ms)
