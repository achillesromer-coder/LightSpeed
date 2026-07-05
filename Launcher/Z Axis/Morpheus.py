# Launcher/Z Axis/Morpheus.py
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from LightSpeed.tools.services.indexer import ProjectIndexer

LAYER_ID = "Z+2"
LAYER_NAME = "Morpheus (Knowledge)"

class MorpheusUI:
    def __init__(self, app, parent):
        self.app = app
        self.company = getattr(getattr(app, "session", object()), "company", "default_company")
        self.project = getattr(getattr(app, "session", object()), "project_id", "default_workspace")
        self.idx = ProjectIndexer(self.company, self.project)
        self.idx.load() or self.idx.build()

        self.frame = ttk.Frame(parent)
        self._build(self.frame)

    def _build(self, root: ttk.Frame):
        top = ttk.Frame(root); top.pack(fill="x")
        self.q = tk.StringVar()
        ent = ttk.Entry(top, textvariable=self.q)
        ent.pack(side="left", fill="x", expand=True, padx=6, pady=6)
        ent.bind("<Return>", lambda e: self._search())
        ttk.Button(top, text="Search", command=self._search).pack(side="left", padx=4)
        ttk.Button(top, text="Rebuild", command=self._rebuild).pack(side="left")

        self.list = tk.Listbox(root); self.list.pack(fill="both", expand=True)
        self.list.bind("<Double-1>", self._open)

    def _rebuild(self):
        self.idx.build()
        self.app.log("Morpheus: index rebuilt.")

    def _search(self):
        q = self.q.get().strip()
        if not q:
            return
        self.list.delete(0, "end")
        for score, ref in self.idx.search(q, k=50):
            self.list.insert("end", f"{score:5.2f}  {ref.kind}  {ref.title}  —  {ref.path}")

    def _open(self, _e):
        sel = self.list.curselection()
        if not sel: return
        msg = self.list.get(sel[0])
        messagebox.showinfo("Open", msg)

def build(app, parent):
    return MorpheusUI(app, parent).frame
