from __future__ import annotations

from datetime import datetime
import os
import time
import psutil

from monitor_app.domain.types import SystemInfo

class SystemCollector:
    def __init__(self) -> None:
        # Prime CPU so next call returns meaningful %
        psutil.cpu_percent(interval=None)

        # Prime network counters so first UI update can show rates soon
        self._last_net = psutil.net_io_counters()
        self._last_net_t = time.time()

        self._primed = False

        self._disk_path = os.environ.get("SystemDrive", "C:") + "\\"

    def collect(self) -> SystemInfo:
        now = datetime.now()

        cpu = float(psutil.cpu_percent(interval=None))

        vm = psutil.virtual_memory()
        mem_total_gb = vm.total / (1024**3)
        mem_used_gb = (vm.total - vm.available) / (1024**3)
        mem_percent = float(vm.percent)

        du = psutil.disk_usage(self._disk_path)
        disk_total_gb = du.total / (1024**3)
        disk_used_gb = du.used / (1024**3)
        disk_percent = float(du.percent)

        net = psutil.net_io_counters()
        t = time.time()

        dt = t - self._last_net_t

        sent_mbps = 0.0
        recv_mbps = 0.0
        if dt >= 0.25:  # avoid nonsense rates when dt is tiny
            sent_bps = (net.bytes_sent - self._last_net.bytes_sent) * 8.0 / dt
            recv_bps = (net.bytes_recv - self._last_net.bytes_recv) * 8.0 / dt
            sent_mbps = sent_bps / 1_000_000.0
            recv_mbps = recv_bps / 1_000_000.0

        self._last_net = net
        self._last_net_t = t

        return SystemInfo(
            timestamp=now,
            cpu_percent=cpu,
            mem_used_gb=float(mem_used_gb),
            mem_total_gb=float(mem_total_gb),
            mem_percent=mem_percent,
            disk_used_gb=float(disk_used_gb),
            disk_total_gb=float(disk_total_gb),
            disk_percent=disk_percent,
            net_sent_mbps=float(sent_mbps),
            net_recv_mbps=float(recv_mbps),
        )