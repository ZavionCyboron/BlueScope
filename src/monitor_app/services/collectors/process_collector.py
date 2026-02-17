from __future__ import annotations

from typing import List

import psutil

from monitor_app.domain.types import ProcessInfo


class ProcessCollector:

    def __init__(self):
        self._proc_cache: dict[int, psutil.Process] = {}
    def collect_fast(self) -> List[ProcessInfo]:
        rows: List[ProcessInfo] = []

        for p in psutil.process_iter(attrs=["pid", "name", "memory_info"]):
            try:
                mem_info = p.info.get("memory_info")
                mem_mb = (mem_info.rss / (1024 ** 2)) if mem_info else 0.0

                rows.append(ProcessInfo(
                    pid=int(p.info["pid"]),
                    name=str(p.info.get("name") or ""),
                    cpu_percent=None,     # <-- not computed here
                    mem_mb=float(mem_mb),
                    username="",
                    exe="",
                    create_time=None
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return rows

    def _get_proc(self, pid: int) -> psutil.Process:
        p = self._proc_cache.get(pid)
        if p is None:
            p = psutil.Process(pid)
            self._proc_cache[pid] = p
        return p

    def sample_cpu_for_pids(self, pids: list[int]) -> dict[int, float]:
        out: dict[int, float] = {}
        dead = []
        for pid in pids:
            try:
                p = self._get_proc(pid)
                out[pid] = float(p.cpu_percent(interval=None))  # now meaningful
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                dead.append(pid)
            except Exception:
                dead.append(pid)

        for pid in dead:
            self._proc_cache.pop(pid, None)
        return out
