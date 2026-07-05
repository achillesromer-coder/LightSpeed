# Launcher/Z Axis/Smith.py
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

from LightSpeed.tools.services.org import project_dir

LAYER_ID = "Z-2"
LAYER_NAME = "Smith (SOP)"

class SmithUI:
    def __init__(self, app, parent):
        self.app = app
        self.company = getattr(getattr(app, "session", object()), "company", "default_company")
        self.project = getattr(getattr(app, "session", object()), "project_id", "default_workspace")
        self.dir = project_dir(self.company, self.project) / "sops"
        self.dir.mkdir(parents=True, exist_ok=True)

        self.frame = ttk.Frame(parent)
        self._build(self.frame)
        self._refresh()

    def _build(self, root: ttk.Frame):
        top = ttk.Frame(root); top.pack(fill="x")
        ttk.Button(top, text="New SOP…", command=self._new).pack(side="left", padx=6)
        ttk.Button(top, text="Save", command=self._save).pack(side="left")
        ttk.Button(top, text="Refresh", command=self._refresh).pack(side="left")
        self.list = tk.Listbox(root, width=28)
        self.list.pack(side="left", fill="y")
        self.list.bind("<<ListboxSelect>>", self._load)

        self.text = tk.Text(root, wrap="word")
        self.text.pack(side="left", fill="both", expand=True)

    def _refresh(self):
        self.list.delete(0, "end")
        for p in sorted(self.dir.glob("*.md")):
            self.list.insert("end", p.stem)

    def _new(self):
        name = simpledialog.askstring("New SOP", "File name (no spaces):")
        if not name: return
        p = self.dir / f"{name}.md"
        if p.exists():
            messagebox.showerror("Exists", "File already exists.")
            return
        p.write_text("# SOP Title\n\nSteps:\n1.\n2.\n3.\n", encoding="utf-8")
        self._refresh()

    def _load(self, _e=None):
        sel = self.list.curselection()
        if not sel: return
        p = self.dir / f"{self.list.get(sel[0])}.md"
        try:
            self.text.delete("1.0", "end")
            self.text.insert("end", p.read_text(encoding="utf-8"))
        except Exception as e:
            messagebox.showerror("Open", str(e))

    def _save(self):
        sel = self.list.curselection()
        if not sel: return
        p = self.dir / f"{self.list.get(sel[0])}.md"
        p.write_text(self.text.get("1.0", "end"), encoding="utf-8")
        self.app.log("SOP saved.")

def build(app, parent):
    return SmithUI(app, parent).frame
