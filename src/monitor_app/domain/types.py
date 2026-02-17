from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: Optional[float]
    mem_mb: float
    username: str
    exe: str
    create_time: Optional[datetime]

@dataclass(frozen=True)
class SystemInfo:
    timestamp: datetime
    cpu_percent: float

    mem_used_gb: float
    mem_total_gb: float
    mem_percent: float

    disk_used_gb: float
    disk_total_gb: float
    disk_percent: float

    net_sent_mbps: float
    net_recv_mbps: float

@dataclass(frozen=True)
class ProcessGroupInfo:
    name: str
    count: str
    cpu_percent: float # grouped (smoothed) CPU sum
    mem_mb: float
