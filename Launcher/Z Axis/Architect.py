# Launcher/Z Axis/Architect.py
from __future__ import annotations

import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from LightSpeed.tools.services.canvas2d import GraphStore
from LightSpeed.tools.services.pipelines import Publisher, hook_notarise_ip, hook_webhook
from LightSpeed.tools.services.notifications import NotificationCenter, Notice

LAYER_ID = "Z+1"
LAYER_NAME = "Architect"

STATUSES = ["Todo", "In Progress", "Review", "Done"]


class ArchitectUI:
    def __init__(self, app, parent):
        self.app = app
        self.company = getattr(getattr(app, "session", object()), "company", "default_company")
        self.project = getattr(getattr(app, "session", object()), "project_id", "default_workspace")
        self.clearance = getattr(getattr(app, "session", object()), "clearance", 1)

        self.gs = GraphStore(self.company, self.project)
        self.notify = NotificationCenter(self.company, self.project, user_clearance=self.clearance)

        self.frame = ttk.Frame(parent)
        self._build(self.frame)
        self._reload_lists()

    def _build(self, root: ttk.Frame):
        top = ttk.Frame(root); top.pack(fill="x")
        ttk.Label(top, text="Floor").pack(side="left", padx=6)
        self.floor = tk.IntVar(value=0)
        sp = ttk.Spinbox(top, from_=-9, to=9, width=4, textvariable=self.floor, command=self._reload_lists)
        sp.pack(side="left")
        ttk.Button(top, text="Publish…", command=self._publish).pack(side="right", padx=6)

        body = ttk.Frame(root); body.pack(fill="both", expand=True, padx=4, pady=4)
        self.lsts = {}
        for i, st in enumerate(STATUSES):
            col = ttk.Frame(body)
            col.grid(row=0, column=i, sticky="nsew", padx=4)
            body.grid_columnconfigure(i, weight=1)
            ttk.Label(col, text=st, anchor="center").pack(fill="x")
            lb = tk.Listbox(col, height=18)
            lb.pack(fill="both", expand=True)
            lb.bind("<Double-1>", lambda e, S=st: self._promote(S))
            self.lsts[st] = lb

    def _reload_lists(self):
        for lb in self.lsts.values():
            lb.delete(0, "end")
        for n in self.gs.list_nodes(floor=self.floor.get()):
            if n.type != "Task":
                continue
            st = n.status or "Todo"
            self.lsts[st].insert("end", f"{n.id}  |  {n.title}")

    def _promote(self, current: str):
        lb = self.lsts[current]
        sel = lb.curselection()
        if not sel:
            return
        line = lb.get(sel[0])
        nid = line.split("|", 1)[0].strip()
        idx = STATUSES.index(current)
        nxt = STATUSES[min(idx + 1, len(STATUSES)-1)]
        self.gs.update_node(nid, status=nxt)
        self.notify.emit(Notice(ts=time.time(), company=self.company, project_id=self.project,
                                event="task.status", title=f"{nxt}", body=f"{nid}", author_id="system"))
        self._reload_lists()

    def _publish(self):
        if self.clearance < 3:
            messagebox.showwarning("Publish", "Insufficient clearance.")
            return
        pub = Publisher(self.company, self.project)
        pub.add_hook(hook_notarise_ip)
        pub.add_hook(hook_webhook)
        man = pub.publish(author_id=getattr(getattr(self.app, "session", object()), "user_id", "system"),
                          notes="Manual publish from Architect")
        self.notify.emit(Notice(ts=time.time(), company=self.company, project_id=self.project,
                                event="doc.published", title="Publish Complete",
                                body=str(man), author_id="system", severity="success"))
        messagebox.showinfo("Publish", f"Release created:\n{man}")


def build(app, parent):
    return ArchitectUI(app, parent).frame
