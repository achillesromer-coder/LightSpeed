#!/usr/bin/env python
"""
Architect (Z+1) - Project Planning & Management Floor
Complete Floor Coordinator with Projects, Timelines, and Task Management

Architect is THE primary project planning layer. It holds:
- Project definitions and architectures
- Development timelines and milestones
- Task queues and work breakdown structures
- Resource allocation and planning
- Progress tracking and reporting

Variables Held:
- active_projects: Current project definitions
- timelines: Project schedules and milestones
- task_queue: Pending and active tasks
- resource_allocations: Team and resource assignments
- progress_metrics: Project completion tracking

Renders:
- Project portal (glass UI dashboard)
- Task checklist and management
- Timeline visualization (Gantt-style)
- Resource allocation charts
- Progress reports
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Optional, Dict, List, Any
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import threading
import queue


def _load_symbol(rel_path: str, symbol: str):
    """Load a symbol (class/function) from a file by relative path"""
    root = Path(__file__).resolve().parents[1]
    path = (root / rel_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    mod_name = f"lightspeed_dynamic_{path.stem}_{abs(hash(str(path)))%1_000_000}"
    spec = spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    mod = module_from_spec(spec)
    # Ensure dataclasses/type evaluation can resolve __module__ via sys.modules.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, symbol):
        raise AttributeError(f"{symbol} not found in {path}")
    return getattr(mod, symbol)


# Backwards compatibility
_load_class = _load_symbol


class ArchitectFloorState:
    """
    State manager for Architect floor

    This class holds all state variables for project planning and management
    """

    def __init__(self):
        # Project state
        self.active_projects: Dict[str, Dict[str, Any]] = {}
        self.project_count = 0
        self.default_project: Optional[str] = None

        # Timeline state
        self.timelines: Dict[str, List[Dict]] = {}
        self.milestones: List[Dict[str, Any]] = []
        self.deadlines: List[Dict[str, Any]] = []

        # Task management
        self.task_queue: List[Dict[str, Any]] = []
        self.completed_tasks: List[Dict] = []
        self.blocked_tasks: List[Dict] = []

        # Resource allocation
        self.resource_allocations: Dict[str, Any] = {}
        self.team_members: List[str] = []
        self.resource_availability: Dict[str, float] = {}

        # Progress tracking
        self.progress_metrics: Dict[str, float] = {}
        self.completion_percentage = 0.0
        self.active_sprints: List[Dict] = []

        # Architecture documentation
        self.design_docs: List[Dict[str, Any]] = []
        self.architecture_decisions: List[Dict] = []

    def add_project(self, name: str, config: Dict[str, Any]):
        """Add a new project"""
        self.active_projects[name] = config
        self.project_count += 1
        if self.default_project is None:
            self.default_project = name

    def add_task(self, task: Dict[str, Any]):
        """Add a task to the queue"""
        self.task_queue.append(task)

    def complete_task(self, task_id: str):
        """Mark a task as completed"""
        for task in self.task_queue:
            if task.get('id') == task_id:
                self.task_queue.remove(task)
                self.completed_tasks.append(task)
                break


class ArchitectUI(ttk.Frame):
    """
    Primary Architect UI - Project Planning & Management

    Architect owns all project planning, task management, timelines, and resource allocation.
    It provides comprehensive project oversight and progress tracking.
    """

    def __init__(self, parent: tk.Misc, app: Optional[object] = None, *, compact: bool = False, **_ignored):
        super().__init__(parent)
        self.app = app
        self.compact = bool(compact)
        self.state = ArchitectFloorState()
        self.project_manager = None
        self.shell_bridge = getattr(app, "trinity_shell_bridge", None)

        try:
            from core.services import get_db, get_event_bus, get_storage
            self.db = getattr(app, "db", None) or get_db()
            self.event_bus = getattr(app, "event_bus", None) or get_event_bus()
            self.storage = getattr(app, "storage", None) or get_storage()
        except Exception:
            self.db = None
            self.event_bus = None
            self.storage = None


        # ProjectManager (projects live under TheConstruct; keep consistent with IT Portal).
        try:
            from core.project_manager import create_project_manager  # type: ignore
            try:
                from core.config.paths import CONSTRUCT_ROOT  # type: ignore
                projects_root = Path(CONSTRUCT_ROOT) / "projects"
            except Exception:
                projects_root = Path.cwd() / "projects"
            self.project_manager = getattr(app, "project_manager", None) or create_project_manager(str(projects_root))
        except Exception:
            self.project_manager = getattr(app, "project_manager", None)

        # Register Bento widgets
        self._register_bento_widgets()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Tabs
        self._tabs: Dict[str, ttk.Frame] = {}
        self._builders: Dict[str, Any] = {}
        self._tab_group: Dict[str, str] = {}
        self._tab_container: Dict[str, Any] = {}
        self._group_frames: Dict[str, ttk.Frame] = {}

        if self.compact:
            self._build_compact_shell()
        else:
            self._build_full_shell()

    def _build_full_shell(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self._register_tab("Portal", self._build_portal)
        self._register_tab("Projects", self._build_projects)
        self._register_tab("Project Manager", self._build_project_manager)
        self._register_tab("Tasks", self._build_tasks)
        self._register_tab("Timeline", self._build_timeline)
        self._register_tab("Resources", self._build_resources)
        self._register_tab("Z Direct Registry", self._build_z_direct_registry)

        self._ensure_built("Portal")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _build_compact_shell(self) -> None:
        """
        Compact embedding for IT Portal:
        - Portal (single surface)
        - Work (projects/PM/resources)
        - Planning (tasks/timeline)
        - Registry (Z Direct)
        """
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        portal_group = ttk.Frame(self.notebook)
        work_group = ttk.Frame(self.notebook)
        planning_group = ttk.Frame(self.notebook)
        reg_group = ttk.Frame(self.notebook)

        self.notebook.add(portal_group, text="Portal")
        self.notebook.add(work_group, text="Work")
        self.notebook.add(planning_group, text="Planning")
        self.notebook.add(reg_group, text="Registry")

        self._group_frames = {
            "Portal": portal_group,
            "Work": work_group,
            "Planning": planning_group,
            "Registry": reg_group,
        }

        self._tabs["Portal"] = portal_group
        self._builders["Portal"] = self._build_portal
        self._tab_group["Portal"] = "Portal"
        self._tab_container["Portal"] = None

        work_nb = ttk.Notebook(work_group)
        work_nb.pack(fill="both", expand=True)
        self._register_tab("Projects", self._build_projects, notebook=work_nb, group="Work")
        self._register_tab("Project Manager", self._build_project_manager, notebook=work_nb, group="Work")
        self._register_tab("Resources", self._build_resources, notebook=work_nb, group="Work")

        plan_nb = ttk.Notebook(planning_group)
        plan_nb.pack(fill="both", expand=True)
        self._register_tab("Tasks", self._build_tasks, notebook=plan_nb, group="Planning")
        self._register_tab("Timeline", self._build_timeline, notebook=plan_nb, group="Planning")

        reg_nb = ttk.Notebook(reg_group)
        reg_nb.pack(fill="both", expand=True)
        self._register_tab("Z Direct Registry", self._build_z_direct_registry, notebook=reg_nb, group="Registry")

        self._ensure_built("Portal")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_group_tab_changed)
        work_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        plan_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        reg_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _register_tab(self, title: str, builder, *, notebook: Optional[ttk.Notebook] = None, group: str = "Portal"):
        """Register a lazy-loaded tab (supports nested notebooks in compact mode)."""
        nb = notebook or self.notebook
        frame = ttk.Frame(nb)
        nb.add(frame, text=title)
        self._tabs[title] = frame
        self._builders[title] = builder
        self._tab_group[title] = group
        self._tab_container[title] = nb

    def _ensure_built(self, title: str):
        """Ensure tab is built"""
        frame = self._tabs.get(title)
        builder = self._builders.get(title)
        if frame is None or builder is None:
            return
        if getattr(frame, "_built", False):
            return
        builder(frame)
        setattr(frame, "_built", True)

    def _on_tab_changed(self, event):
        """Handle tab change - lazy load content"""
        nb = getattr(event, "widget", None) or self.notebook
        current_tab = nb.select()
        tab_text = nb.tab(current_tab, "text")
        self._ensure_built(tab_text)

    def _on_group_tab_changed(self, _event):
        """When switching compact groups, ensure the visible leaf is built."""
        try:
            group = self.notebook.tab(self.notebook.select(), "text")
        except Exception:
            return
        if group == "Portal":
            self._ensure_built("Portal")
            return
        try:
            grp_frame = self._group_frames.get(group)
            if grp_frame is None:
                return
            children = [w for w in grp_frame.winfo_children() if isinstance(w, ttk.Notebook)]
            if not children:
                return
            nb = children[0]
            leaf = nb.tab(nb.select(), "text")
            self._ensure_built(leaf)
        except Exception:
            return

    def select_tab(self, title: str) -> None:
        """Select a leaf tab by title, regardless of compact/full shell."""
        if title not in self._tabs:
            return
        if not self.compact:
            try:
                self.notebook.select(self._tabs[title])
            except Exception:
                pass
            self._ensure_built(title)
            return
        group = self._tab_group.get(title) or "Portal"
        try:
            self.notebook.select(self._group_frames[group])
        except Exception:
            pass
        if group == "Portal":
            self._ensure_built("Portal")
            return
        nb = self._tab_container.get(title)
        if nb is not None:
            try:
                nb.select(self._tabs[title])
            except Exception:
                pass
        self._ensure_built(title)

    def _build_portal(self, parent: ttk.Frame):
        """Build portal dashboard tab"""
        try:
            from core.ui.base_portal_glass import mount_smart_ops_strip  # type: ignore

            mount_smart_ops_strip(parent, app=self.app, floor_channel="Z+1", it_portal=self.compact, title="Architect Ops")
        except Exception:
            pass
        try:
            from lightspeed_runtime.desktop_adapters import build_architect_workbench_panel

            panel = build_architect_workbench_panel(parent, self.app)
            if panel is not None:
                panel.pack(fill="x", padx=12, pady=(0, 10))
        except Exception:
            pass

        actions = ttk.Frame(parent)
        actions.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Label(
            actions,
            text="Primary Architect workbench: plan here first, then expand the specific project surface you need.",
            justify="left",
        ).pack(side="left", padx=(0, 12))
        ttk.Button(actions, text="Projects", command=lambda: self.select_tab("Projects")).pack(side="left")
        ttk.Button(actions, text="Project Manager", command=lambda: self.select_tab("Project Manager")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Tasks", command=lambda: self.select_tab("Tasks")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Timeline", command=lambda: self.select_tab("Timeline")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Z Direct", command=lambda: self.select_tab("Z Direct Registry")).pack(side="left", padx=(8, 0))
        try:
            Portal = _load_class("Z Axis/Z+1_Architect/components/architect_portal_glass.py", "ArchitectPortalGlass")
            ui = Portal(parent)
            ui.pack(fill="both", expand=True)
        except Exception as e:
            ttk.Label(parent, text=f"Architect Portal unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_projects(self, parent: ttk.Frame):
        """Build projects management tab"""
        ttk.Label(parent, text="Project Management", font=("Consolas", 14, "bold")).pack(pady=10)

        # Project summary
        ttk.Label(parent, text=f"Active Projects: {self.state.project_count}").pack(pady=5)
        ttk.Label(parent, text=f"Default: {self.state.default_project or 'None'}").pack(pady=5)

        ttk.Button(parent, text="Create New Project", command=self._create_project).pack(pady=10)
        try:
            from lightspeed_runtime.desktop_adapters import mount_architect_publish_center

            mount_architect_publish_center(parent, self.app)
        except Exception:
            pass


    def _build_project_manager(self, parent: ttk.Frame):
        """Floor-owned Project Manager surface (was previously a Trinity IT Portal tools tab)."""
        ttk.Label(parent, text="Project Manager (Architect)", font=("Consolas", 14, "bold")).pack(pady=(10, 6))
        ttk.Label(
            parent,
            text="This is the canonical projects/workspaces manager. Use Trinity IT Portal only for governance approvals.",
            justify="left",
        ).pack(padx=12, pady=(0, 10), anchor="w")

        pm = self.project_manager
        if pm is None:
            ttk.Label(parent, text="ProjectManager unavailable in this environment.", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )
            return

        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        stats = ttk.Frame(container)
        stats.pack(fill="x", pady=(0, 8))

        self._pm_stats_var = tk.StringVar(value="Scanning projects...")
        ttk.Label(stats, textvariable=self._pm_stats_var).pack(side="left")

        btns = ttk.Frame(stats)
        btns.pack(side="right")

        ttk.Button(btns, text="Refresh", command=self._pm_refresh_list).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Create Project", command=self._pm_create_project).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Repair Duplicates", command=self._pm_repair_duplicates).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Sync Registry", command=self._pm_sync_registry).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Open Folder", command=self._pm_open_selected).pack(side="left")

        cols = ("files", "size_mb", "modified")
        tree = ttk.Treeview(container, columns=cols, show="tree headings", height=16)
        tree.heading("#0", text="Project")
        tree.heading("files", text="Files")
        tree.heading("size_mb", text="Size (MB)")
        tree.heading("modified", text="Modified")
        tree.column("#0", width=340, anchor="w")
        tree.column("files", width=90, anchor="e")
        tree.column("size_mb", width=90, anchor="e")
        tree.column("modified", width=160, anchor="w")
        tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)

        self._pm_tree = tree
        self._pm_rows = []

        self._pm_refresh_list()

    def _pm_refresh_list(self) -> None:
        pm = self.project_manager
        tree = getattr(self, "_pm_tree", None)
        if pm is None or tree is None:
            return

        # Cancel any in-flight stats scan; we'll restart from the new view.
        try:
            ev = getattr(self, "_pm_scan_cancel", None)
            if ev is not None:
                ev.set()
        except Exception:
            pass

        try:
            tree.delete(*tree.get_children())
        except Exception:
            pass

        try:
            base_path = Path(str(getattr(pm, "base_path", "")))
        except Exception:
            base_path = None

        rows = []
        project_dirs = []
        try:
            if base_path and base_path.exists():
                project_dirs = [p for p in base_path.iterdir() if p.is_dir() and not p.name.startswith(".")]
        except Exception:
            project_dirs = []

        # Populate quickly first; compute file/size stats asynchronously to keep UI responsive.
        item_by_name: Dict[str, str] = {}
        for p in sorted(project_dirs, key=lambda x: x.name.lower()):
            try:
                import datetime as _dt
                mod_s = _dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            except Exception:
                mod_s = ""

            row = {"name": p.name, "path": str(p), "files": None, "size_mb": None, "modified": mod_s}
            rows.append(row)
            try:
                item = tree.insert("", "end", text=p.name, values=("-", "-", mod_s))
                item_by_name[p.name] = item
            except Exception:
                pass

        self._pm_rows = rows
        self._pm_item_by_name = item_by_name
        try:
            self._pm_stats_var.set(
                f"Projects: {len(rows)}    Root: {base_path or ''}    (computing size/file counts...)"
            )
        except Exception:
            pass

        # Background stats worker (files + bytes) with incremental UI updates.
        cancel = threading.Event()
        self._pm_scan_cancel = cancel
        q: "queue.Queue[object]" = queue.Queue()
        self._pm_scan_queue = q

        def _scan(paths: List[Path]) -> None:
            skip_dirs = {".venv", "__pycache__", ".git", "node_modules", "dist", "build"}
            for proj_dir in paths:
                if cancel.is_set():
                    return
                files = 0
                size = 0
                try:
                    for root, dirs, filenames in os.walk(proj_dir):
                        if cancel.is_set():
                            return
                        # Prune heavy/irrelevant directories early.
                        dirs[:] = [d for d in dirs if d not in skip_dirs]
                        for fn in filenames:
                            files += 1
                            try:
                                size += int(os.stat(os.path.join(root, fn)).st_size)
                            except Exception:
                                pass
                except Exception:
                    pass
                q.put((proj_dir.name, files, size))
            q.put(None)  # sentinel

        t = threading.Thread(target=_scan, args=(sorted(project_dirs, key=lambda x: x.name.lower()),), daemon=True)
        self._pm_scan_thread = t
        try:
            t.start()
        except Exception:
            return

        self._pm_scan_totals = {"files": 0, "bytes": 0, "done": 0, "count": len(project_dirs), "root": str(base_path or "")}

        def _poll() -> None:
            tree_local = getattr(self, "_pm_tree", None)
            if tree_local is None:
                return
            if cancel.is_set():
                return
            totals = getattr(self, "_pm_scan_totals", None) or {}
            processed_any = False
            try:
                while True:
                    item = q.get_nowait()
                    if item is None:
                        break
                    if not isinstance(item, tuple) or len(item) != 3:
                        continue
                    name, fcount, bcount = item
                    processed_any = True
                    try:
                        totals["files"] = int(totals.get("files", 0)) + int(fcount)
                        totals["bytes"] = int(totals.get("bytes", 0)) + int(bcount)
                        totals["done"] = int(totals.get("done", 0)) + 1
                    except Exception:
                        pass
                    try:
                        item_id = (getattr(self, "_pm_item_by_name", {}) or {}).get(str(name))
                        if item_id:
                            tree_local.set(item_id, "files", str(int(fcount)))
                            tree_local.set(item_id, "size_mb", f"{(float(bcount) / (1024 * 1024)):.1f}")
                    except Exception:
                        pass
            except queue.Empty:
                pass

            try:
                done = int(totals.get("done", 0) or 0)
                count = int(totals.get("count", 0) or 0)
                size_mb = float(totals.get("bytes", 0) or 0) / (1024 * 1024)
                if done >= count and count > 0:
                    self._pm_stats_var.set(
                        f"Projects: {len(rows)}    Files: {int(totals.get('files', 0) or 0)}    Size: {size_mb:.1f} MB    Root: {totals.get('root','')}"
                    )
                elif processed_any:
                    self._pm_stats_var.set(
                        f"Projects: {len(rows)}    Scanned: {done}/{count}    Files: {int(totals.get('files', 0) or 0)}    Size: {size_mb:.1f} MB"
                    )
            except Exception:
                pass

            if int(totals.get("done", 0) or 0) >= int(totals.get("count", 0) or 0):
                return
            try:
                self.after(120, _poll)
            except Exception:
                pass

        try:
            self.after(120, _poll)
        except Exception:
            pass

    def _pm_selected(self):
        tree = getattr(self, "_pm_tree", None)
        if tree is None:
            return None
        try:
            sel = tree.selection()
            if not sel:
                return None
            idx = tree.index(sel[0])
            rows = getattr(self, "_pm_rows", [])
            if 0 <= idx < len(rows):
                return rows[idx]
        except Exception:
            return None
        return None

    def _pm_open_selected(self) -> None:
        it = self._pm_selected()
        if not it:
            messagebox.showwarning("Project Manager", "Select a project first.", parent=self.winfo_toplevel())
            return
        try:
            os.startfile(str(it.get("path") or ""))  # type: ignore[attr-defined]
        except Exception as e:
            messagebox.showerror("Project Manager", f"Open failed:\\n{e}", parent=self.winfo_toplevel())

    def _pm_create_project(self) -> None:
        pm = self.project_manager
        if pm is None:
            return
        name = simpledialog.askstring("Create Project", "Project name:", parent=self.winfo_toplevel())
        if not name:
            return
        name = name.strip()
        if not name:
            return
        try:
            res = pm.create_project(name=name)
            if isinstance(res, dict) and not res.get("success", True):
                messagebox.showerror("Create Project", str(res.get("error") or "Create failed"), parent=self.winfo_toplevel())
            else:
                messagebox.showinfo("Create Project", f"Created project: {name}", parent=self.winfo_toplevel())
        except Exception as e:
            messagebox.showerror("Create Project", f"Create failed:\\n{e}", parent=self.winfo_toplevel())
        self._pm_refresh_list()

    def _pm_repair_duplicates(self) -> None:
        """Repair duplicate project rows (DB hygiene) caused by older double-persist paths."""
        pm = self.project_manager
        if pm is None:
            return

        try:
            report = pm.repair_duplicate_project_rows(dry_run=True)
        except Exception as e:
            messagebox.showerror("Repair Duplicates", f"Failed to scan duplicates:\n{e}", parent=self.winfo_toplevel())
            return

        if not isinstance(report, dict) or not report.get("success", False):
            messagebox.showerror("Repair Duplicates", str(report.get("error") if isinstance(report, dict) else report), parent=self.winfo_toplevel())
            return

        groups = int(report.get("duplicate_groups", 0) or 0)
        if groups <= 0:
            messagebox.showinfo("Repair Duplicates", "No duplicate project rows found.", parent=self.winfo_toplevel())
            return

        # Show a compact preview (avoid dumping huge JSON into a modal).
        actions = report.get("actions") or []
        preview_lines = []
        for a in actions[:10]:
            try:
                preview_lines.append(f"- {a.get('name')}: keep #{a.get('keep_id')} delete={len(a.get('delete_ids') or [])} move_tasks={sum((a.get('tasks_to_move') or {}).values())}")
            except Exception:
                continue
        if len(actions) > 10:
            preview_lines.append(f"... and {len(actions) - 10} more")

        msg = (
            f"Found duplicate project rows in DB: {groups} name group(s).\n\n"
            "Preview:\n" + "\n".join(preview_lines) + "\n\n"
            "Apply repair now? (merges missing fields into the keeper row, reassigns tasks, deletes redundant rows)"
        )
        if not messagebox.askyesno("Repair Duplicates", msg, parent=self.winfo_toplevel()):
            return

        # Prefer Smith background execution when available (keeps UI responsive).
        try:
            smith_queue = getattr(getattr(self, "app", None), "smith_queue", None)
            if smith_queue is not None and hasattr(smith_queue, "add_task"):
                task_id = smith_queue.add_task(
                    task_type="projects.repair_duplicates",
                    parameters={"dry_run": False},
                    source_floor="Z+1_Architect",
                    priority=2,
                )
                messagebox.showinfo(
                    "Repair Duplicates",
                    f"Queued duplicate repair as Smith task #{task_id}.\n\n"
                    "Monitor progress in Smith -> Jobs Monitor (or Trinity/Smith jobs widget).",
                    parent=self.winfo_toplevel(),
                )
                return
        except Exception:
            pass

        try:
            applied = pm.repair_duplicate_project_rows(dry_run=False)
        except Exception as e:
            messagebox.showerror("Repair Duplicates", f"Repair failed:\n{e}", parent=self.winfo_toplevel())
            return

        if not isinstance(applied, dict) or not applied.get("success", False):
            messagebox.showerror("Repair Duplicates", str(applied.get("error") if isinstance(applied, dict) else applied), parent=self.winfo_toplevel())
            return

        messagebox.showinfo(
            "Repair Duplicates",
            f"Repair complete.\nDeleted rows: {applied.get('deleted_rows', 0)}\nUpdated rows: {applied.get('updated_rows', 0)}\nTasks moved: {applied.get('moved_tasks', 0)}",
            parent=self.winfo_toplevel(),
        )
        self._pm_refresh_list()

    def _pm_sync_registry(self) -> None:
        """Sync projects registry (DB) with filesystem (non-destructive by default)."""
        pm = self.project_manager
        if pm is None:
            return

        try:
            report = pm.sync_registry_with_filesystem(dry_run=True)
        except Exception as e:
            messagebox.showerror("Sync Registry", f"Failed to scan registry:\n{e}", parent=self.winfo_toplevel())
            return

        if not isinstance(report, dict) or not report.get("success", False):
            messagebox.showerror("Sync Registry", str(report.get("error") if isinstance(report, dict) else report), parent=self.winfo_toplevel())
            return

        add_n = int(report.get("would_add", 0) or 0)
        miss_n = int(report.get("would_mark_missing", 0) or 0)
        if add_n == 0 and miss_n == 0:
            messagebox.showinfo("Sync Registry", "Registry already matches filesystem (no changes).", parent=self.winfo_toplevel())
            return

        msg = (
            "Sync projects registry with filesystem?\n\n"
            f"- Would add DB rows: {add_n}\n"
            f"- Would mark missing-on-disk: {miss_n}\n\n"
            "This is safe and non-destructive to project folders.\n"
            "Proceed?"
        )
        if not messagebox.askyesno("Sync Registry", msg, parent=self.winfo_toplevel()):
            return

        # Prefer Smith background execution when available (keeps UI responsive).
        try:
            smith_queue = getattr(getattr(self, "app", None), "smith_queue", None)
            if smith_queue is not None and hasattr(smith_queue, "add_task"):
                task_id = smith_queue.add_task(
                    task_type="projects.sync_registry",
                    parameters={"dry_run": False},
                    source_floor="Z+1_Architect",
                    priority=3,
                )
                messagebox.showinfo(
                    "Sync Registry",
                    f"Queued registry sync as Smith task #{task_id}.\n\n"
                    "Monitor progress in Smith -> Jobs Monitor, then Refresh this view.",
                    parent=self.winfo_toplevel(),
                )
                return
        except Exception:
            pass

        try:
            applied = pm.sync_registry_with_filesystem(dry_run=False)
        except Exception as e:
            messagebox.showerror("Sync Registry", f"Sync failed:\n{e}", parent=self.winfo_toplevel())
            return

        if not isinstance(applied, dict) or not applied.get("success", False):
            messagebox.showerror("Sync Registry", str(applied.get("error") if isinstance(applied, dict) else applied), parent=self.winfo_toplevel())
            return

        messagebox.showinfo(
            "Sync Registry",
            f"Sync complete.\nAdded: {applied.get('added', 0)}\nMarked missing: {applied.get('marked_missing', 0)}",
            parent=self.winfo_toplevel(),
        )
        self._pm_refresh_list()

    def _build_tasks(self, parent: ttk.Frame):
        """Build tasks tab"""
        try:
            Checklist = _load_class("Z Axis/Z+1_Architect/components/progress_widget.py", "TaskChecklistWidget")
            ui = Checklist(parent)
            ui.pack(fill="both", expand=True)
        except Exception as e:
            ttk.Label(parent, text=f"Task Checklist unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_timeline(self, parent: ttk.Frame):
        """Build timeline visualization tab"""
        ttk.Label(parent, text="Project Timeline", font=("Consolas", 14, "bold")).pack(pady=10)
        ttk.Label(parent, text=f"Milestones: {len(self.state.milestones)}").pack(pady=5)
        ttk.Label(parent, text=f"Deadlines: {len(self.state.deadlines)}").pack(pady=5)

    def _build_resources(self, parent: ttk.Frame):
        """Build resource allocation tab"""
        ttk.Label(parent, text="Resource Allocation", font=("Consolas", 14, "bold")).pack(pady=10)
        ttk.Label(parent, text=f"Team Members: {len(self.state.team_members)}").pack(pady=5)

    def _build_z_direct_registry(self, parent: ttk.Frame):
        """
        Z Direct Registry (Architect): browse committed objects for interactability.

        Trinity is the approval gate for commits; this view reads the durable registry:
        `Z Axis/Z+1_Architect/Z Direct/objects.json`.
        """
        ttk.Label(parent, text="Z Direct Registry (Committed Objects)", font=("Consolas", 14, "bold")).pack(pady=10)

        try:
            from core.services import get_z_direct  # type: ignore
            z_direct = get_z_direct()
        except Exception as e:
            ttk.Label(parent, text=f"Z Direct unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )
            return

        outer = ttk.Frame(parent)
        outer.pack(fill="both", expand=True, padx=10, pady=10)
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=2)
        outer.rowconfigure(0, weight=1)

        left = ttk.Frame(outer)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right = ttk.Frame(outer)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        listbox = tk.Listbox(left, height=20, font=("Consolas", 10))
        listbox.pack(fill="both", expand=True)

        details = tk.Text(right, wrap="word", font=("Consolas", 10))
        details.pack(fill="both", expand=True)

        btns = ttk.Frame(parent)
        btns.pack(fill="x", padx=10, pady=(0, 10))

        state: Dict[str, Any] = {"items": []}

        def _render_details(item: Any) -> None:
            try:
                details.delete("1.0", "end")
            except Exception:
                pass
            try:
                details.insert("1.0", json.dumps(item, indent=2, ensure_ascii=True))
            except Exception:
                details.insert("1.0", str(item))

        def _load() -> None:
            try:
                items = z_direct.read_registry("Z+1", name="objects")
            except Exception:
                items = []
            state["items"] = items or []
            listbox.delete(0, "end")
            for it in state["items"]:
                if not isinstance(it, dict):
                    listbox.insert("end", str(it))
                    continue
                kind = it.get("kind") or "object"
                oid = it.get("id") or ""
                title = it.get("title") or it.get("name") or ""
                listbox.insert("end", f"{kind} {oid} {title}".strip())
            _render_details({"count": len(state["items"]), "channel": "Z+1"})

        def _open_selected() -> None:
            try:
                sel = listbox.curselection()
                if not sel:
                    messagebox.showwarning("Registry", "Select an item first.", parent=self.winfo_toplevel())
                    return
                it = state["items"][int(sel[0])]
                if not isinstance(it, dict):
                    messagebox.showwarning("Registry", "Invalid item selection.", parent=self.winfo_toplevel())
                    return
                p = it.get("path") or it.get("source_path")
                if not isinstance(p, str) or not p.strip():
                    messagebox.showwarning("Registry", "No file path on this object.", parent=self.winfo_toplevel())
                    return
                fp = Path(p)
                if not fp.exists():
                    messagebox.showwarning("Registry", f"File not found:\n{fp}", parent=self.winfo_toplevel())
                    return
                os.startfile(str(fp))  # type: ignore[attr-defined]
            except Exception as e:
                messagebox.showerror("Registry", f"Open failed:\n{e}", parent=self.winfo_toplevel())

        def _on_select(_evt=None) -> None:
            try:
                sel = listbox.curselection()
                if not sel:
                    return
                it = state["items"][int(sel[0])]
                _render_details(it)
            except Exception:
                return

        ttk.Button(btns, text="Refresh", command=_load).pack(side="left")
        ttk.Button(btns, text="Open File", command=_open_selected).pack(side="left", padx=(8, 0))

        listbox.bind("<<ListboxSelect>>", _on_select)
        _load()

    def _register_bento_widgets(self):
        """Register Architect widgets with Bento system"""
        try:
            import sys
            trinity_path = Path(__file__).parent / "Z+3_Trinity"
            if str(trinity_path) not in sys.path:
                sys.path.insert(0, str(trinity_path))

            from ui.universal_bento_system import register_floor_widgets, BentoWidget, BentoWidgetType

            widgets = [
                BentoWidget(
                    id="architect_projects",
                    title="Projects",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z+1_Architect",
                    callback=lambda w: self._open_projects(),
                    config={"icon": "PROJ", "description": "Manage projects"}
                ),
                BentoWidget(
                    id="architect_timeline",
                    title="Timeline",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z+1_Architect",
                    callback=lambda w: self._open_timeline(),
                    config={"icon": "TIME", "description": "View project timeline"}
                ),
                BentoWidget(
                    id="architect_tasks",
                    title="Task Queue",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z+1_Architect",
                    callback=lambda w: self._open_tasks(),
                    config={"icon": "TASK", "description": "Task management"}
                ),
                BentoWidget(
                    id="architect_project_manager",
                    title="Project Manager",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z+1_Architect",
                    callback=lambda w: self._open_project_manager(),
                    config={"icon": "PM", "description": "Project/workspace management"}
                )
            ]

            register_floor_widgets("Z+1_Architect", widgets)
            print("[Architect] Registered Architect Bento widgets")
        except Exception as e:
            print(f"[Architect] Could not register Bento widgets: {e}")

    def _open_projects(self):
        """Open projects tab"""
        print("[Architect] Opening Projects...")
        self.select_tab("Projects")

    def _open_timeline(self):
        """Open timeline tab"""
        print("[Architect] Opening Timeline...")
        self.select_tab("Timeline")

    def _open_tasks(self):
        """Open tasks tab"""
        print("[Architect] Opening Tasks...")
        self.select_tab("Tasks")

    def _open_project_manager(self):
        """Open Project Manager tab."""
        print("[Architect] Opening Project Manager...")
        self.select_tab("Project Manager")

    def _create_project(self):
        """Create a new project (routes to Project Manager)."""
        self._pm_create_project()


def create_gui(*args, **kwargs):
    """
    N.py / IT Portal integration entry point.

    Supported call shapes:
    - create_gui(parent, colors)
    - create_gui(app, parent, colors)
    """
    app = None
    parent = None
    if args and isinstance(args[0], tk.Misc):
        parent = args[0]
    elif len(args) >= 2 and isinstance(args[1], tk.Misc):
        app = args[0]
        parent = args[1]
    if parent is None:
        return None
    compact = bool(kwargs.get("compact") or kwargs.get("it_portal"))
    return ArchitectUI(parent, app=app, compact=compact)


def build(*args, **kwargs):
    """Alias for legacy floor loaders."""
    return create_gui(*args, **kwargs)


# ---------------------------------------------------------------------------
# Floor boot hook (used by FloorLoader)
# ---------------------------------------------------------------------------

_ARCHITECT_INITIALIZED = False
ARCHITECT_RUNTIME: Dict[str, Any] = {}


def initialize(*, components: Optional[Dict[str, Any]] = None, dependencies: Optional[Dict[str, Any]] = None, **_kwargs) -> bool:
    """
    Initialize Architect floor runtime services.

    This runs during floor bootstrap (no UI) and ensures Architect's
    background services and integrations are active.

    Args:
        components: Pre-loaded component classes/instances
        dependencies: Shared services (db, event_bus, storage, logger)
        **_kwargs: Additional platform parameters

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    global _ARCHITECT_INITIALIZED, ARCHITECT_RUNTIME
    if _ARCHITECT_INITIALIZED:
        return True
    _ARCHITECT_INITIALIZED = True

    try:
        # Core services are provided by the Merovingian floor (`Z Axis/Z-4_Merovingian/core`).
        # Use the stable namespace import path (`core.services`) and avoid invalid module names
        # such as `Z-4_Merovingian`.
        from core.services import get_db, get_event_bus, get_storage, get_logger  # type: ignore

        db = get_db()
        event_bus = get_event_bus()
        storage = get_storage()
        logger = get_logger()
    except Exception as e:
        print(f"[Architect] Failed to load core services: {e}")
        db = None
        event_bus = None
        storage = None
        logger = None

    ARCHITECT_RUNTIME["db"] = db
    ARCHITECT_RUNTIME["event_bus"] = event_bus
    ARCHITECT_RUNTIME["storage"] = storage
    ARCHITECT_RUNTIME["logger"] = logger

    # Floor-specific initialization

    # Register mission planning UI components (no UI instantiation during bootstrap).
    try:
        DBTaskBoard = _load_symbol("Z Axis/Z+1_Architect/components/progress_widget.py", "DBTaskBoard")
        ARCHITECT_RUNTIME["task_board_cls"] = DBTaskBoard
        ARCHITECT_RUNTIME["task_board_available"] = True
    except Exception as e:
        ARCHITECT_RUNTIME["task_board_error"] = str(e)


    # Subscribe to relevant events
    if event_bus:
        try:
            event_bus.subscribe("system.health.check", _on_health_check)
        except Exception as e:
            if logger:
                logger.warning(f"[Architect] Event subscription failed: {e}")

    # Publish floor ready event
    if event_bus:
        try:
            event_bus.publish("architect.floor.ready", {
                "floor": "Architect",
                "z_level": 1,
                "capabilities": ['mission_planning', 'project_management', 'goals', 'okrs', 'roadmaps']
            })
        except Exception as e:
            if logger:
                logger.warning(f"[Architect] Failed to publish ready event: {e}")

    if logger:
        logger.info("[Architect] Floor initialized successfully")

    return True


def _on_health_check(event):
    """Respond to health check events"""
    event_bus = ARCHITECT_RUNTIME.get("event_bus")
    if event_bus:
        try:
            event_bus.publish("architect.health.status", {
                "floor": "Architect",
                "status": "operational",
                "z_level": 1
            })
        except Exception:
            pass

def main() -> int:
    root = tk.Tk()
    root.title("Architect (Z+1) - Planning")
    root.geometry("1200x800")
    ArchitectUI(root).pack(fill="both", expand=True)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
