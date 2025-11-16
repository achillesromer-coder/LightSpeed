# Launcher/Z Axis/Oracle.py
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from LightSpeed.tools.services.indexer import ProjectIndexer
from LightSpeed.tools.services.org import project_dir
from LightSpeed.tools.services.notifications import NotificationCenter, Notice

LAYER_ID = "Z-1"
LAYER_NAME = "Oracle (Archives)"

class OracleUI:
    def __init__(self, app, parent):
        self.app = app
        self.company = getattr(getattr(app, "session", object()), "company", "default_company")
        self.project = getattr(getattr(app, "session", object()), "project_id", "default_workspace")
        self.clearance = getattr(getattr(app, "session", object()), "clearance", 1)

        self.root_dir = project_dir(self.company, self.project)
        (self.root_dir / "archives").mkdir(parents=True, exist_ok=True)

        self.idx = ProjectIndexer(self.company, self.project)
        self.idx.load() or self.idx.build()
        self.notify = NotificationCenter(self.company, self.project, user_clearance=self.clearance)

        self.frame = ttk.Frame(parent)
        self._build(self.frame)
        self._refresh()

    def _build(self, root: ttk.Frame):
        top = ttk.Frame(root); top.pack(fill="x")
        ttk.Button(top, text="Import…", command=self._import_files).pack(side="left", padx=6)
        ttk.Button(top, text="Refresh", command=self._refresh).pack(side="left")
        self.list = tk.Listbox(root); self.list.pack(fill="both", expand=True)
        self.list.bind("<Double-1>", self._open)

        self.preview = tk.Text(root, height=12, wrap="word")
        self.preview.pack(fill="both", expand=False)

    def _refresh(self):
        self.list.delete(0, "end")
        for p in sorted((self.root_dir/"archives").rglob("*")):
            if p.is_file():
                self.list.insert("end", str(p.relative_to(self.root_dir)))

    def _import_files(self):
        files = filedialog.askopenfilenames(title="Import to Archives")
        if not files:
            return
        imported = []
        for f in files:
            src = Path(f)
            dst = (self.root_dir / "archives" / src.name)
            try:
                if src.resolve() != dst.resolve():
                    dst.write_bytes(src.read_bytes())
                imported.append(dst)
                self.idx.update_asset(dst)
                self.notify.emit(Notice(ts=time.time(), company=self.company, project_id=self.project,
                                        event="asset.uploaded", title=src.name, body=str(dst), author_id="system"))
            except Exception as e:
                messagebox.showerror("Import", f"Failed {src.name}: {e}")
        if imported:
            self._refresh()
            self.app.log(f"Oracle: imported {len(imported)} file(s).")

    def _open(self, _e):
        sel = self.list.curselection()
        if not sel:
            return
        rel = self.list.get(sel[0])
        p = self.root_dir / rel
        try:
            text = ""
            if p.suffix.lower() in (".txt", ".md", ".py", ".csv", ".json", ".yaml", ".yml", ".log"):
                text = p.read_text(encoding="utf-8", errors="ignore")
            else:
                text = f"{p.name}\n\n{p.stat().st_size} bytes\n\n(Preview not supported)"
            self.preview.delete("1.0", "end"); self.preview.insert("end", text[:20000])
        except Exception as e:
            messagebox.showerror("Open", str(e))

def build(app, parent):
    return OracleUI(app, parent).frame
