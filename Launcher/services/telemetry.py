# Launcher/services/telemetry.py
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, asdict
from typing import Callable, Optional, Dict

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None  # handled below

try:
    import GPUtil  # type: ignore
except Exception:  # pragma: no cover
    GPUtil = None


@dataclass
class TelemetrySnapshot:
    ts: float
    fps: float
    active_floor: str = ""
    entities: int = 0
    cpu_percent: float = 0.0
    gpu_percent: Optional[float] = None
    ram_used_mb: int = 0
    ram_total_mb: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)


class TelemetrySampler:
    """
    Background sampler; call `start()` with a callback to receive snapshots.
    Push frame ticks via `mark_frame()` if you want FPS; otherwise FPS stays 0.
    """
    def __init__(self, interval_ms: int = 500):
        self.interval = max(200, min(2000, int(interval_ms))) / 1000.0
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._cb: Optional[Callable[[TelemetrySnapshot], None]] = None

        # FPS state
        self._last_frame_ts: Optional[float] = None
        self._ema_fps: Optional[float] = None  # exponential moving avg

        # Exposed live fields (owner may set these)
        self.active_floor = ""
        self.entities = 0

    # --------- Public API ---------
    def start(self, on_snapshot: Callable[[TelemetrySnapshot], None]) -> None:
        self._cb = on_snapshot
        self._stop.clear()
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="TelemetrySampler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def mark_frame(self) -> None:
        """Call once per rendered frame (from your draw loop if available)."""
        now = time.perf_counter()
        if self._last_frame_ts is None:
            self._last_frame_ts = now
            return
        dt = now - self._last_frame_ts
        self._last_frame_ts = now
        if dt <= 0:
            return
        fps = 1.0 / dt
        # Smooth with EMA (alpha ~ 0.15)
        self._ema_fps = fps if self._ema_fps is None else (0.85 * self._ema_fps + 0.15 * fps)

    # --------- Internals ---------
    def _run(self) -> None:
        while not self._stop.is_set():
            snap = self._collect()
            if self._cb:
                try:
                    self._cb(snap)
                except Exception:
                    # never crash the sampler on UI callback errors
                    pass
            time.sleep(self.interval)

    def _collect(self) -> TelemetrySnapshot:
        ts = time.time()
        fps = float(self._ema_fps or 0.0)

        cpu = 0.0
        ram_used = ram_total = 0
        if psutil:
            try:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory()
                ram_used = int(mem.used / (1024 * 1024))
                ram_total = int(mem.total / (1024 * 1024))
            except Exception:
                pass

        gpu = None
        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    # take the busiest adapter
                    gpu = max(g.load for g in gpus) * 100.0
            except Exception:
                gpu = None

        return TelemetrySnapshot(
            ts=ts,
            fps=round(fps, 1),
            active_floor=str(self.active_floor),
            entities=int(self.entities or 0),
            cpu_percent=float(cpu),
            gpu_percent=(None if gpu is None else round(float(gpu), 1)),
            ram_used_mb=ram_used,
            ram_total_mb=ram_total,
        )
