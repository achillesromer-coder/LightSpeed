# Launcher/services/notifications.py
from __future__ import annotations

import json
import time
import threading
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Callable, Optional, Literal

APP_ROOT = Path(__file__).resolve().parents[1]            # .../Launcher
DATA_DIR = APP_ROOT.parent / "data"                       # .../data
NOTIFY_DIR = DATA_DIR / "notify"
NOTIFY_DIR.mkdir(parents=True, exist_ok=True)

DigestFreq = Literal["daily", "weekly", "monthly"]

@dataclass
class Notice:
    ts: float
    company: str
    project_id: str
    event: str             # e.g., "asset.uploaded", "doc.published"
    title: str
    body: str
    author_id: str
    severity: Literal["info", "success", "warning", "error"] = "info"
    min_clearance: int = 1
    tags: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tags"] = d.get("tags") or []
        return d


class NotificationCenter:
    """
    File-backed notification stream with live callbacks and digest collation.
    UI can subscribe via on_push() to render toast or side-panel entries.
    """
    def __init__(self, company: str, project_id: str, user_clearance: int = 1):
        self.company = company
        self.project_id = project_id
        self.user_clearance = int(user_clearance)
        self._callbacks: List[Callable[[Notice], None]] = []
        self._digest_callbacks: List[Callable[[DigestFreq, List[Notice]], None]] = []
        self._lock = threading.RLock()
        self._digester: Optional[threading.Thread] = None
        self._stop = threading.Event()
        # default schedule windows (UTC-ish, simple timer cadence)
        self._digest_freqs: Dict[DigestFreq, int] = {"daily": 24*3600, "weekly": 7*24*3600, "monthly": 30*24*3600}
        self._last_emit: Dict[DigestFreq, float] = {k: 0.0 for k in self._digest_freqs}

        self.stream_path = NOTIFY_DIR / f"{self.company}__{self.project_id}.jsonl"
        self.stream_path.parent.mkdir(parents=True, exist_ok=True)
        self.stream_path.touch(exist_ok=True)

    # ---------- subscriptions ----------
    def on_push(self, cb: Callable[[Notice], None]) -> None:
        self._callbacks.append(cb)

    def on_digest(self, cb: Callable[[DigestFreq, List[Notice]], None]) -> None:
        self._digest_callbacks.append(cb)

    # ---------- emit/stream ----------
    def emit(self, notice: Notice) -> None:
        """Append a notice and deliver to live subscribers if clearance allows."""
        with self._lock:
            with self.stream_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(notice.to_dict(), ensure_ascii=False) + "\n")
        if notice.min_clearance <= self.user_clearance:
            for cb in list(self._callbacks):
                try:
                    cb(notice)
                except Exception:
                    pass

    def read_tail(self, max_items: int = 200) -> List[Notice]:
        """Read most-recent N notices (used to seed the panel on open)."""
        lines = []
        try:
            with self.stream_path.open("r", encoding="utf-8") as f:
                for line in f.readlines()[-max_items:]:
                    lines.append(json.loads(line))
        except Exception:
            return []
        out = []
        for rec in lines:
            if int(rec.get("min_clearance", 1)) <= self.user_clearance:
                out.append(Notice(**{**rec, "tags": rec.get("tags") or []}))
        return out

    # ---------- digests ----------
    def start_digests(self, enabled: Dict[DigestFreq, bool] | None = None) -> None:
        self._stop.clear()
        if enabled:
            for k, v in enabled.items():
                if v is False:
                    self._digest_freqs.pop(k, None)
        if self._digester and self._digester.is_alive():
            return
        self._digester = threading.Thread(target=self._run_digests, name="NotifyDigest", daemon=True)
        self._digester.start()

    def stop(self) -> None:
        self._stop.set()

    def _run_digests(self) -> None:
        # crude cadence loop – good enough for in-app digests
        while not self._stop.is_set():
            now = time.time()
            for freq, period in list(self._digest_freqs.items()):
                if (now - self._last_emit.get(freq, 0.0)) >= period:
                    batch = self._collect_since(self._last_emit.get(freq, 0.0))
                    if batch:
                        for cb in list(self._digest_callbacks):
                            try:
                                cb(freq, batch)
                            except Exception:
                                pass
                    self._last_emit[freq] = now
            time.sleep(30)

    def _collect_since(self, ts_from: float) -> List[Notice]:
        out: List[Notice] = []
        try:
            with self.stream_path.open("r", encoding="utf-8") as f:
                for line in f:
                    rec = json.loads(line)
                    if float(rec.get("ts", 0)) > ts_from and int(rec.get("min_clearance", 1)) <= self.user_clearance:
                        out.append(Notice(**{**rec, "tags": rec.get("tags") or []}))
        except Exception:
            pass
        return out
