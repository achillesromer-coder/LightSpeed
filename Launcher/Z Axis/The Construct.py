# Launcher/Z Axis/The Construct.py
from __future__ import annotations

import json
import math
import time
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Optional, Tuple

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog

from LightSpeed.tools.services.canvas2d import GraphStore, Node
from LightSpeed.tools.services.indexer import ProjectIndexer
from LightSpeed.tools.services.notifications import NotificationCenter, Notice
from LightSpeed.tools.services.org import project_dir

LAYER_ID = "Z"
LAYER_NAME = "The Construct"

NODE_COLORS = {
    "Task": "#68b5ff",
    "Asset": "#ffd166",
    "Doc": "#bdb2ff",
    "API": "#80ed99",
    "Portal": "#f4978e",
    "Custom": "#9e9e9e",
}
STATUS_BADGE = {
    None: "",
    "Todo": "•",
    "In Progress": "▶",
    "Review": "✓?",
    "Done": "✓",
}


class ConstructUI:
    def __init__(self, app, parent):
        self.app = app
        self.company = getattr(getattr(app, "session", object()), "company", "default_company")
        self.project = getattr(getattr(app, "session", object()), "project_id", "default_workspace")

        self.gs = GraphStore(self.company, self.project, snap_px=24, max_nodes_per_floor=500, max_edges=2000)
        self.index = ProjectIndexer(self.company, self.project)
        self.index.load() or self.index.build()
        self.notify = NotificationCenter(self.company, self.project, user_clearance=getattr(getattr(app, "session", object()), "clearance", 1))

        self._drag: Optional[Tuple[str, int, int]] = None  # (node_id, dx, dy)
        self._selected: Optional[str] = None
        self._link_start: Optional[str] = None
        self._floor = tk.IntVar(value=0)

        self.frame = ttk.Frame(parent)
        self._build_toolbar(self.frame)
        self._build_canvas(self.frame)
        self._load_floor()

    # ------------- UI -------------
    def _build_toolbar(self, root: ttk.Frame):
        bar = ttk.Frame(root); bar.pack(fill="x")
        ttk.Label(bar, text="Floor").pack(side="left", padx=6)
        sp = ttk.Spinbox(bar, from_=-9, to=9, width=4, textvariable=self._floor, command=self._load_floor)
        sp.pack(side="left")
        ttk.Button(bar, text="+ Node", command=self._new_node_popup).pack(side="left", padx=4)
        ttk.Button(bar, text="Link", command=self._toggle_link).pack(side="left", padx=4)
        ttk.Button(bar, text="Rebuild Index", command=self._rebuild_index).pack(side="left", padx=12)
        self.find_var = tk.StringVar()
        ent = ttk.Entry(bar, textvariable=self.find_var, width=28)
        ent.pack(side="right", padx=6)
        ent.bind("<Return>", lambda e: self._do_search())
        ttk.Button(bar, text="Search", command=self._do_search).pack(side="right")

    def _build_canvas(self, root: ttk.Frame):
        self.canvas = tk.Canvas(root, bg="#111417", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._redraw_grid())
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._context_menu)

    # ------------- data ops -------------
    def _load_floor(self):
        self.canvas.delete("all")
        self._draw_grid()
        self._id2rect: Dict[str, int] = {}
        nodes = self.gs.list_nodes(floor=self._floor.get())
        for n in nodes:
            self._paint_node(n)
        for e in self.gs.list_edges():
            a = self._id2rect.get(e.src); b = self._id2rect.get(e.dst)
            if a and b:
                self._paint_edge(a, b, e.label)

    def _rebuild_index(self):
        self.index.build()
        self.app.log("Construct: index rebuilt")

    # ------------- drawing -------------
    def _grid_spacing(self) -> int:
        return self.gs.snap

    def _draw_grid(self):
        self.canvas.delete("grid")
        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 600
        s = self._grid_spacing()
        for x in range(0, w, s):
            self.canvas.create_line(x, 0, x, h, fill="#1c2127", width=1, tags="grid")
        for y in range(0, h, s):
            self.canvas.create_line(0, y, w, y, fill="#1c2127", width=1, tags="grid")

    def _redraw_grid(self):
        self._draw_grid()
        # redraw nodes to stay on top
        for nid in list(self._id2rect.keys()):
            self._repaint_node(nid)

    def _paint_node(self, n: Node):
        w, h = 150, 46
        x0, y0 = n.x - w//2, n.y - h//2
        col = NODE_COLORS.get(n.type, "#888")
        r = self.canvas.create_rectangle(x0, y0, x0+w, y0+h, fill=col, outline="#0b0f13", width=2)
        txt = f"{STATUS_BADGE.get(n.status)} {n.title}"
        t = self.canvas.create_text(n.x, n.y, text=txt, fill="#0b0f13", font=("Segoe UI", 10, "bold"))
        self._id2rect[n.id] = r
        self.canvas.tag_bind(r, "<Button-1>", lambda e, nid=n.id: self._select(nid))
        self.canvas.tag_bind(t, "<Button-1>", lambda e, nid=n.id: self._select(nid))

    def _repaint_node(self, node_id: str):
        n = next((x for x in self.gs.list_nodes(self._floor.get()) if x.id == node_id), None)
        if not n:
            return
        r = self._id2rect.get(node_id)
        if not r:
            return
        w, h = 150, 46
        x0, y0 = n.x - w//2, n.y - h//2
        self.canvas.coords(r, x0, y0, x0+w, y0+h)
        for it in self.canvas.find_withtag("current"):
            pass
        # text is separate; simplest is delete & recreate nearby
        self.canvas.delete(f"txt_{node_id}")
        txt = f"{STATUS_BADGE.get(n.status)} {n.title}"
        t = self.canvas.create_text(n.x, n.y, text=txt, fill="#0b0f13", font=("Segoe UI", 10, "bold"),
                                    tags=(f"txt_{node_id}",))
        self.canvas.tag_bind(t, "<Button-1>", lambda e, nid=n.id: self._select(nid))

    def _paint_edge(self, rect_a: int, rect_b: int, label: str):
        ax0, ay0, ax1, ay1 = self.canvas.coords(rect_a)
        bx0, by0, bx1, by1 = self.canvas.coords(rect_b)
        ax = (ax0 + ax1) / 2; ay = (ay0 + ay1) / 2
        bx = (bx0 + bx1) / 2; by = (by0 + by1) / 2
        self.canvas.create_line(ax, ay, bx, by, fill="#2e3742", width=2, arrow=tk.LAST)
        if label:
            mx, my = (ax+bx)/2, (ay+by)/2
            self.canvas.create_text(mx, my-6, text=label, fill="#6b7785", font=("Segoe UI", 9))

    # ------------- interactions -------------
    def _select(self, node_id: str):
        self._selected = node_id

    def _on_click(self, e):
        # begin drag if clicked inside a node
        pt = (e.x, e.y)
        for nid, rid in self._id2rect.items():
            x0, y0, x1, y1 = self.canvas.coords(rid)
            if x0 <= pt[0] <= x1 and y0 <= pt[1] <= y1:
                self._selected = nid
                self._drag = (nid, e.x, e.y)
                return
        self._selected = None

    def _on_drag(self, e):
        if not self._drag:
            return
        nid, sx, sy = self._drag
        n = next((x for x in self.gs.list_nodes(self._floor.get()) if x.id == nid), None)
        if not n:
            return
        nx = n.x + (e.x - sx)
        ny = n.y + (e.y - sy)
        # snap preview
        nsx = self.gs._snap(nx); nsy = self.gs._snap(ny)
        n.x, n.y = nsx, nsy
        self._drag = (nid, e.x, e.y)
        self._repaint_node(nid)

    def _on_release(self, e):
        if not self._drag:
            return
        nid, *_ = self._drag
        self._drag = None
        n = next((x for x in self.gs.list_nodes(self._floor.get()) if x.id == nid), None)
        if n:
            self.gs.update_node_pos(n.id, n.x, n.y)

    def _toggle_link(self):
        if self._link_start is None:
            self._link_start = self._selected
            self.app.log("Select another node to complete link…")
        else:
            if self._selected and self._selected != self._link_start:
                self.gs.create_edge(self._link_start, self._selected, label="")
                self._link_start = None
                self._load_floor()
                self.app.log("Edge created.")
            else:
                self._link_start = None

    def _context_menu(self, e):
        m = tk.Menu(self.canvas, tearoff=0)
        m.add_command(label="New Node…", command=lambda: self._new_node_popup((e.x, e.y)))
        if self._selected:
            m.add_command(label="Edit…", command=self._edit_node_popup)
            m.add_command(label="Delete", command=self._delete_selected)
        m.tk_popup(e.x_root, e.y_root)

    def _new_node_popup(self, pos: Optional[Tuple[int, int]] = None):
        pos = pos or (self.canvas.winfo_width()//2, 80)
        title = simpledialog.askstring("New Node", "Title:")
        if not title:
            return
        ntype = simpledialog.askstring("Type", "Task | Asset | Doc | API | Portal | Custom", initialvalue="Task")
        n = self.gs.create_node(title=title, ntype=(ntype or "Task"), floor=self._floor.get(), x=pos[0], y=pos[1])
        self.index.update_node(n.id, asdict(n))
        self.notify.emit(Notice(ts=time.time(), company=self.company, project_id=self.project,
                                event="node.created", title=title, body=f"Type={n.type}", author_id="system"))
        self._paint_node(n)

    def _edit_node_popup(self):
        nid = self._selected
        if not nid:
            return
        n = next((x for x in self.gs.list_nodes(self._floor.get()) if x.id == nid), None)
        if not n:
            return
        new_title = simpledialog.askstring("Edit Title", "Title:", initialvalue=n.title)
        if new_title:
            self.gs.update_node(n.id, title=new_title)
            self.index.update_node(n.id, asdict(n))
            self._repaint_node(n.id)

    def _delete_selected(self):
        nid = self._selected
        if not nid:
            return
        if messagebox.askyesno("Delete", "Delete selected node?"):
            self.gs.delete_node(nid)
            self._load_floor()

    def _do_search(self):
        q = self.find_var.get().strip()
        if not q:
            return
        res = self.index.search(q, k=15)
        if not res:
            messagebox.showinfo("Search", "No results.")
            return
        txt = "\n".join([f"{score:5.2f}  {ref.kind} :: {ref.title}  —  {ref.path}" for score, ref in res])
        messagebox.showinfo("Search Results", txt)


def build(app, parent):
    ui = ConstructUI(app, parent)
    return ui.frame
