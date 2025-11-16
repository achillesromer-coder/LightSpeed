# Launcher/Z Axis/Neo.py
from __future__ import annotations

import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from LightSpeed.tools.services.org import project_dir

LAYER_ID = "Z+3"
LAYER_NAME = "Neo (Assistant)"

INTRO = "G'day — how can I help?"

class NeoUI:
    def __init__(self, app, parent):
        self.app = app
        self.company = getattr(getattr(app, "session", object()), "company", "default_company")
        self.project = getattr(getattr(app, "session", object()), "project_id", "default_workspace")

        self.frame = ttk.Frame(parent)
        self._build(self.frame)

    def _build(self, root: ttk.Frame):
        self.out = tk.Text(root, height=16, wrap="word")
        self.out.pack(fill="both", expand=True, padx=6, pady=6)
        self.out.insert("end", f"Neo: {INTRO}\n\n")
        b = ttk.Frame(root); b.pack(fill="x")
        self.inp = tk.Entry(b)
        self.inp.pack(side="left", fill="x", expand=True, padx=6, pady=6)
        self.inp.bind("<Return>", lambda e: self._send())
        ttk.Button(b, text="Send", command=self._send).pack(side="left")

    def _send(self):
        q = self.inp.get().strip()
        if not q: return
        self.inp.delete(0, "end")
        self.out.insert("end", f"You: {q}\n")
        # Stub: echo & write log file (weekly roll-up happens elsewhere)
        ts = int(time.time())
        log_dir = project_dir(self.company, self.project) / "ai_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{ts}.txt").write_text(f"{q}\n", encoding="utf-8")
        self.out.insert("end", f"Neo: [stubbed] processing…\n\n")
        self.out.see("end")

def build(app, parent):
    return NeoUI(app, parent).frame
