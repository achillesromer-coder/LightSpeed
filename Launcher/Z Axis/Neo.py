# Launcher/Z Axis/Neo.py
from __future__ import annotations

import json
import time
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
        b = ttk.Frame(root)
        b.pack(fill="x")
        self.inp = tk.Entry(b)
        self.inp.pack(side="left", fill="x", expand=True, padx=6, pady=6)
        self.inp.bind("<Return>", lambda e: self._send())
        ttk.Button(b, text="Send", command=self._send).pack(side="left")

    def _append_existing_project_history(self, message: str) -> None:
        """Append one event to an already-materialised project ledger.

        This legacy UI must not manufacture an `ai_logs/` tree or one file per
        message.  Explicit project creation owns local materialisation.  If the
        project/history ledger is absent, the UI remains display-only and leaves
        durable routing/receipt capture to the canonical LightSpeed runtime.
        """
        history = project_dir(self.company, self.project) / "history.jsonl"
        if not history.is_file():
            return
        event = {
            "ts": time.time(),
            "surface": "legacy_neo_ui",
            "actor": "user",
            "event": "message",
            "text": message,
        }
        with history.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")

    def _send(self):
        q = self.inp.get().strip()
        if not q:
            return
        self.inp.delete(0, "end")
        self.out.insert("end", f"You: {q}\n")
        self._append_existing_project_history(q)
        self.out.insert("end", "Neo: [stubbed] processing…\n\n")
        self.out.see("end")


def build(app, parent):
    return NeoUI(app, parent).frame
