from __future__ import annotations

from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk
from typing import Callable


UI_ROOT = Path(__file__).resolve().parent
if str(UI_ROOT) not in sys.path:
    sys.path.insert(0, str(UI_ROOT))

from shell_routes import SHELL_FLOORS, normalize_floor


class FloorSelector(tk.Frame):
    """The shell's single active-floor selector."""

    def __init__(
        self,
        parent,
        *,
        active_floor: str = "Trinity",
        on_change: Callable[[str], None] | None = None,
        colors: dict | None = None,
    ) -> None:
        palette = colors or {}
        background = palette.get("bg_panel", "#082B4B")
        foreground = palette.get("text_white", "#F7F3E8")
        accent = palette.get("accent_cyan", "#30D5C8")
        super().__init__(parent, bg=background)
        self._on_change = on_change
        self._variable = tk.StringVar(value=normalize_floor(active_floor))

        tk.Label(
            self,
            text="ACTIVE FLOOR",
            bg=background,
            fg=accent,
            font=("Garamond", 9, "bold"),
        ).pack(side="left", padx=(0, 8))
        self.combobox = ttk.Combobox(
            self,
            state="readonly",
            textvariable=self._variable,
            values=SHELL_FLOORS,
            width=18,
            font=("Garamond", 11),
        )
        self.combobox.pack(side="left")
        self.combobox.bind("<<ComboboxSelected>>", self._selected)
        self.status = tk.Label(
            self,
            text="one context / one workspace",
            bg=background,
            fg=foreground,
            font=("Garamond", 9),
        )
        self.status.pack(side="left", padx=(10, 0))

    def _selected(self, _event=None) -> None:
        floor = normalize_floor(self._variable.get())
        if callable(self._on_change):
            self._on_change(floor)

    def set_floor(self, floor: str, *, notify: bool = False) -> None:
        normalized = normalize_floor(floor)
        self._variable.set(normalized)
        if notify and callable(self._on_change):
            self._on_change(normalized)

    def get_floor(self) -> str:
        return normalize_floor(self._variable.get())
