"""
Morpheus Portal Glass

Compact Morpheus review surface for the operator OS.
The runtime search/proofing adapter stays primary when available; this file
provides the hosted panel shell expected by floor bootstrap and the Morpheus UI.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Any


def _resolve_app(widget: tk.Misc | None) -> object | None:
    current = widget
    while current is not None:
        app = getattr(current, "app", None)
        if app is not None:
            return app
        current = getattr(current, "master", None)
    return None


def _open_path(path: Path) -> str:
    try:
        os.startfile(str(path))  # type: ignore[attr-defined]
        return f"Opened {path.name}."
    except Exception as exc:
        return f"Open failed: {exc}"


class MorpheusPortalGlass(ttk.Frame):
    """
    Compact hosted Morpheus panel.

    The panel keeps review/proofing actions grouped and lets the runtime-owned
    Morpheus surface mount directly when the application bridge is available.
    """

    def __init__(self, parent: tk.Misc | None = None):
        super().__init__(parent, padding=12)
        self.app = _resolve_app(parent)
        self.root_path = Path(__file__).resolve().parents[3]
        self.status_var = tk.StringVar(
            value="Morpheus review surface ready. Curated proof cards stay primary."
        )
        self._build()

    def _build(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Morpheus Review Console",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            header,
            text=(
                "Review knowledge, compare provenance, then route proofed results into "
                "Oracle promotion, Architect planning, or TheConstruct execution."
            ),
            justify="left",
        ).pack(fill="x", pady=(4, 8), anchor="w")

        actions = ttk.LabelFrame(self, text="Review Actions")
        actions.pack(fill="x", pady=(0, 10))

        ttk.Button(actions, text="Open Proofing Queue", command=self._open_queue).grid(
            row=0, column=0, padx=8, pady=8, sticky="w"
        )
        ttk.Button(actions, text="Open Catalog Shell", command=self._open_catalog).grid(
            row=0, column=1, padx=8, pady=8, sticky="w"
        )
        ttk.Button(
            actions,
            text="Open Query Layer",
            command=self._open_query_layer,
        ).grid(row=0, column=2, padx=8, pady=8, sticky="w")

        ttk.Label(
            actions,
            text="Grouped review actions replace older one-off feature buttons.",
            justify="left",
        ).grid(row=1, column=0, columnspan=3, padx=8, pady=(0, 8), sticky="w")

        mounted = self._mount_runtime_surface()
        if not mounted:
            fallback = ttk.LabelFrame(self, text="Curated Review Surface")
            fallback.pack(fill="both", expand=True)
            ttk.Label(
                fallback,
                text=(
                    "The runtime search adapter is unavailable in this context. "
                    "Use the grouped actions above to inspect the proofing queue, "
                    "catalog shell, and query layer."
                ),
                justify="left",
            ).pack(fill="x", padx=10, pady=(10, 8), anchor="w")

        ttk.Label(
            self,
            textvariable=self.status_var,
            justify="left",
        ).pack(fill="x", pady=(10, 0), anchor="w")

    def _mount_runtime_surface(self) -> bool:
        try:
            from lightspeed_runtime.desktop_adapters import mount_morpheus_runtime_search

            host = ttk.Frame(self)
            host.pack(fill="both", expand=True)
            if mount_morpheus_runtime_search(host, self.app):
                self.status_var.set(
                    "Runtime-backed Morpheus search mounted. Proof cards and provenance menus are active."
                )
                return True
            host.destroy()
        except Exception as exc:
            self.status_var.set(f"Runtime search unavailable: {exc}")
        return False

    def _open_queue(self) -> None:
        queue_path = (
            self.root_path
            / "Z Axis"
            / "Z-2_Oracle"
            / "data"
            / "knowns"
            / "knowns_proofing_queue.json"
        )
        self.status_var.set(_open_path(queue_path))

    def _open_catalog(self) -> None:
        catalog_path = (
            self.root_path
            / "Z Axis"
            / "Z-2_Oracle"
            / "data"
            / "catalog"
            / "dataset_catalog_shell.json"
        )
        self.status_var.set(_open_path(catalog_path))

    def _open_query_layer(self) -> None:
        query_path = (
            self.root_path
            / "Z Axis"
            / "Z-2_Oracle"
            / "data"
            / "datatables"
            / "query"
            / "scientific_query_layer.json"
        )
        self.status_var.set(_open_path(query_path))


def main() -> int:
    root = tk.Tk()
    root.title("Morpheus Portal Glass")
    root.geometry("1080x780")
    MorpheusPortalGlass(root).pack(fill="both", expand=True)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
