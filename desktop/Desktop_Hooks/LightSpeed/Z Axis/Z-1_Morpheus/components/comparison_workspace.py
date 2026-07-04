from __future__ import annotations

import difflib
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext


MAX_TEXT_BYTES = 2 * 1024 * 1024


class ComparisonWorkspace(tk.Frame):
    """Bounded two-artifact comparison surface owned by Morpheus."""

    def __init__(self, parent, *, colors: dict | None = None) -> None:
        palette = colors or {}
        self._bg = palette.get("bg_dark", "#031A2D")
        self._panel = palette.get("bg_panel", "#082B4B")
        self._text = palette.get("text_white", "#F7F3E8")
        self._accent = palette.get("accent_cyan", "#30D5C8")
        super().__init__(parent, bg=self._bg)
        self.left_path = tk.StringVar()
        self.right_path = tk.StringVar()

        tk.Label(
            self,
            text="MORPHEUS REVIEW / TWO-ARTIFACT COMPARISON",
            bg=self._bg,
            fg=self._accent,
            font=("Garamond", 15, "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 4))
        tk.Label(
            self,
            text="Text comparison is capped at 2 MB per artifact; source files remain unchanged.",
            bg=self._bg,
            fg=self._text,
            font=("Garamond", 10),
        ).pack(anchor="w", padx=16, pady=(0, 12))

        controls = tk.Frame(self, bg=self._panel)
        controls.pack(fill="x", padx=16, pady=(0, 10))
        self._path_row(controls, "A", self.left_path, 0)
        self._path_row(controls, "B", self.right_path, 1)
        tk.Button(
            controls,
            text="COMPARE",
            command=self.compare,
            bg=self._accent,
            fg=self._bg,
            relief="flat",
            font=("Garamond", 10, "bold"),
        ).grid(row=0, column=3, rowspan=2, padx=10, pady=8, sticky="ns")
        controls.grid_columnconfigure(1, weight=1)

        self.output = scrolledtext.ScrolledText(
            self,
            wrap="none",
            bg=self._bg,
            fg=self._text,
            insertbackground=self._accent,
            relief="flat",
            font=("Consolas", 9),
        )
        self.output.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _path_row(self, parent, label: str, variable: tk.StringVar, row: int) -> None:
        tk.Label(
            parent,
            text=label,
            bg=self._panel,
            fg=self._accent,
            font=("Garamond", 10, "bold"),
        ).grid(row=row, column=0, padx=(10, 6), pady=5)
        tk.Entry(
            parent,
            textvariable=variable,
            bg=self._bg,
            fg=self._text,
            insertbackground=self._accent,
            relief="flat",
        ).grid(row=row, column=1, sticky="ew", pady=5)
        tk.Button(
            parent,
            text="Browse",
            command=lambda: self._browse(variable),
            bg=self._panel,
            fg=self._text,
            relief="flat",
        ).grid(row=row, column=2, padx=6, pady=5)

    @staticmethod
    def _browse(variable: tk.StringVar) -> None:
        path = filedialog.askopenfilename(title="Select comparison artifact")
        if path:
            variable.set(path)

    @staticmethod
    def _read(path_value: str) -> tuple[Path, list[str]]:
        path = Path(path_value).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size > MAX_TEXT_BYTES:
            raise ValueError(f"{path.name} exceeds the 2 MB review limit")
        return path, path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines(keepends=True)

    def compare(self) -> None:
        try:
            left_path, left = self._read(self.left_path.get())
            right_path, right = self._read(self.right_path.get())
        except Exception as exc:
            messagebox.showerror("Comparison unavailable", str(exc), parent=self)
            return
        diff = difflib.unified_diff(
            left,
            right,
            fromfile=str(left_path),
            tofile=str(right_path),
            n=3,
        )
        text = "".join(diff) or "No textual differences."
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
