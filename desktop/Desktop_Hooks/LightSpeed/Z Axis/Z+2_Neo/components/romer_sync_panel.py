"""
Romer Sync Panel (Neo)

UI for:
- Opening Romer Industries web workspaces (operations, Achilles, and project pages).
- Syncing remote pages into local cache (best-effort; supports cookie auth).

This panel intentionally avoids embedding secrets. If the site is password-
protected (Squarespace lock screen), set `ROMER_COOKIE` in the environment with
your browser cookie string after unlocking the site.
"""

from __future__ import annotations

import os
import webbrowser
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk


class RomerSyncPanel(ttk.Frame):
    def __init__(self, parent: tk.Misc, app: Optional[object] = None):
        super().__init__(parent)
        self.app = app

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        title = ttk.Label(self, text="Romer Industries — Web Workspaces", font=("Segoe UI", 12, "bold"))
        title.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        controls = ttk.Frame(self)
        controls.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="Cookie (optional):").grid(row=0, column=0, sticky="w")
        self.cookie_var = tk.StringVar(value=os.environ.get("ROMER_COOKIE", ""))
        cookie_entry = ttk.Entry(controls, textvariable=self.cookie_var)
        cookie_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        ttk.Button(controls, text="Apply → ENV", command=self._apply_cookie_env).grid(row=0, column=2, sticky="e")

        btns = ttk.Frame(controls)
        btns.grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))

        ttk.Button(btns, text="Open Operations", command=lambda: webbrowser.open("https://romer.industries/operations")).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Open Achilles", command=lambda: webbrowser.open("https://romer.industries/achilles")).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Open /data/achilles", command=lambda: webbrowser.open("https://romer.industries/data/achilles")).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Open Workspace Pages", command=self._open_w_workspaces).pack(side="left", padx=(0, 6))

        ttk.Button(btns, text="Open Achilles Desktop (local)", command=self._open_local_achilles_desktop).pack(side="left", padx=(0, 6))

        ttk.Button(btns, text="Sync Now", command=self._sync).pack(side="left", padx=(12, 6))
        ttk.Button(btns, text="Open Cache Folder", command=self._open_cache_folder).pack(side="left")

        self.output = tk.Text(self, height=18, wrap="word")
        self.output.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self._append("Set `ROMER_COOKIE` to enable authenticated sync (if required).\n")

    def _append(self, text: str) -> None:
        try:
            self.output.insert("end", text)
            self.output.see("end")
        except Exception:
            pass

    def _apply_cookie_env(self) -> None:
        os.environ["ROMER_COOKIE"] = (self.cookie_var.get() or "").strip()
        self._append("Applied cookie to ENV: ROMER_COOKIE\n")

    def _open_w_workspaces(self) -> None:
        for w in ("w1", "w2", "w3", "w4", "w5", "w6"):
            webbrowser.open(f"https://romer.industries/{w}")

    def _open_local_achilles_desktop(self) -> None:
        try:
            root = Path(__file__).resolve().parents[3]
            path = root / "Z Axis" / "Z+3_Trinity" / "assets" / "web" / "achilles_desktop.html"
            webbrowser.open(path.as_uri())
            self._append(f"Opened local Achilles Desktop: {path}\n")
        except Exception as e:
            self._append(f"[ERROR] Failed to open local Achilles Desktop: {e}\n")

    def _cache_dir(self) -> Path:
        try:
            from core.config.paths import MEROVINGIAN_DATA  # type: ignore
            return Path(MEROVINGIAN_DATA) / "romer_sync"
        except Exception:
            return Path.cwd() / "Z Axis" / "Z-4_Merovingian" / "data" / "romer_sync"

    def _open_cache_folder(self) -> None:
        try:
            d = self._cache_dir()
            d.mkdir(parents=True, exist_ok=True)
            os.startfile(str(d))  # type: ignore[attr-defined]
        except Exception as e:
            self._append(f"[ERROR] Could not open cache folder: {e}\n")

    def _sync(self) -> None:
        try:
            from .romer_industries_connector import RomerIndustriesConnector, RomerAuth
        except Exception as e:
            self._append(f"[ERROR] Connector unavailable: {e}\n")
            return

        cookie = (self.cookie_var.get() or "").strip() or None
        auth = RomerAuth(cookie_header=cookie)
        connector = RomerIndustriesConnector()
        self._append("Syncing romer.industries targets...\n")
        report = connector.sync_targets(auth=auth)

        ok = 0
        need_auth = 0
        total = 0
        for _name, meta in (report.get("targets") or {}).items():
            total += 1
            status = meta.get("status")
            if status == 200:
                ok += 1
            if status == 401:
                need_auth += 1

        self._append(f"Sync complete: {ok}/{total} OK; {need_auth} require auth.\n")
        for name, meta in (report.get("targets") or {}).items():
            if "error" in meta:
                self._append(f"- {name}: ERROR {meta.get('error')}\n")
            else:
                self._append(f"- {name}: {meta.get('status')} ({meta.get('bytes')} bytes)\n")
        self._append("\n")
