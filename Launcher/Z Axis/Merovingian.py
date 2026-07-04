# Launcher/Z Axis/Merovingian.py
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

LAYER_ID = "Z-3"
LAYER_NAME = "Merovingian (Diagnostics)"

def _read_tail(p: Path, max_bytes: int = 200_000) -> str:
    if not p.exists():
        return ""
    data = p.read_bytes()
    return data[-max_bytes:].decode("utf-8", errors="ignore")

class MerovingianUI:
    def __init__(self, app, parent):
        self.app = app
        self.logs_dir = Path(__file__).resolve().parents[2] / "logs"  # project/logs
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self.frame = ttk.Frame(parent)
        self._build(self.frame)
        self._refresh()

    def _build(self, root: ttk.Frame):
        top = ttk.Frame(root); top.pack(fill="x")
        ttk.Button(top, text="Refresh", command=self._refresh).pack(side="left", padx=6)
        ttk.Button(top, text="Clear app.log", command=self._clear).pack(side="left")
        self.text = tk.Text(root, wrap="none")
        self.text.pack(fill="both", expand=True)

    def _refresh(self):
        app_log = self.logs_dir / "app.log"
        self.text.delete("1.0", "end")
        self.text.insert("end", _read_tail(app_log))

    def _clear(self):
        (self.logs_dir / "app.log").write_text("", encoding="utf-8")
        self._refresh()

def build(app, parent):
    return MerovingianUI(app, parent).frame
