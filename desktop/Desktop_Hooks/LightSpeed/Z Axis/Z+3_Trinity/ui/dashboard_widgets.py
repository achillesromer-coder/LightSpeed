"""
LightSpeed Dashboard Widgets
Consolidated from: setup_wizard.py, lightspeed_complete_gui.py
Features: OKRs, Tasks, Calendar, Notices, Quick Links
"""

import importlib.util
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime, timedelta
import calendar
import json
import sqlite3
from pathlib import Path
import sys


def _find_lightspeed_root(start: Optional[Path] = None) -> Path:
    start = (start or Path(__file__)).resolve()
    for candidate in (start, *start.parents):
        try:
            if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
                return candidate
        except Exception:
            continue
        try:
            if (candidate / "LightSpeed" / "N.py").exists() and (candidate / "LightSpeed" / "Z Axis").exists():
                return (candidate / "LightSpeed").resolve()
        except Exception:
            continue
    return start


def _load_unified_config(ls_root: Path) -> Dict[str, Any]:
    cfg_path = ls_root / "config" / "unified_config.json"
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _db_path(ls_root: Optional[Path] = None) -> Path:
    root = ls_root or _find_lightspeed_root()
    cfg = _load_unified_config(root)
    rel = (cfg.get("database") or {}).get("path")
    if rel:
        return (root / rel).resolve()
    return (root / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db").resolve()


def _connect_db(db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    return conn


def _try_get_user_preferences(user_id: Optional[str]):
    """
    Best-effort adapter to Merovingian's UserPreferences service.

    This keeps dashboard widgets usable even in partial installs and respects
    the "no implicit schema creation" rule (service degrades if table missing).
    """
    if not isinstance(user_id, str) or not user_id.strip():
        return None
    try:
        ls_root = _find_lightspeed_root()
        merov = (ls_root / "Z Axis" / "Z-4_Merovingian").resolve()
        if merov.exists() and str(merov) not in sys.path:
            sys.path.insert(0, str(merov))
        from core.services import get_user_preferences  # type: ignore

        return get_user_preferences(user_id.strip())
    except Exception:
        return None


class OKRWidget(ttk.Frame):
    """
    Objectives and Key Results widget.
    Displays company/project OKRs with progress tracking.
    """

    def __init__(self, parent, *, user_id: Optional[str] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.okrs: List[Dict] = []
        self.user_id: Optional[str] = user_id
        self._prefs = _try_get_user_preferences(user_id)

        self._create_ui()
        self._load_okrs()

    def _create_ui(self):
        """Create OKR widget UI."""
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(header, text="Objectives & Key Results",
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        ttk.Button(header, text="+ Add OKR",
                  command=self._add_okr_dialog).pack(side=tk.RIGHT)

        # OKR List (scrollable)
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas for scrolling
        self.canvas = tk.Canvas(list_frame, yscrollcommand=scrollbar.set,
                               highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.canvas.yview)

        # Inner frame for OKR cards
        self.okr_container = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.okr_container, anchor="nw")

        self.okr_container.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def set_user_id(self, user_id: Optional[str]) -> None:
        self.user_id = user_id
        self._prefs = _try_get_user_preferences(user_id)
        self._load_okrs()

    def _load_okrs(self) -> None:
        """
        Load OKRs from per-user preferences (tailoring), if available.
        This intentionally does not write to durable registries.
        """
        try:
            if self._prefs is None or not hasattr(self._prefs, "get_preference"):
                self._refresh_display()
                return
            data = self._prefs.get_preference("okr.okrs", default=[])
            if isinstance(data, list):
                self.okrs = [x for x in data if isinstance(x, dict)]
        except Exception:
            pass
        self._refresh_display()

    def _save_okrs(self) -> None:
        try:
            if self._prefs is None or not hasattr(self._prefs, "set_preference"):
                return
            self._prefs.set_preference("okr.okrs", list(self.okrs or []))
        except Exception:
            return

    def add_okr(self, objective: str, key_results: List[Dict], target_date: str = "") -> None:
        """
        Add OKR to widget.

        Args:
            objective: Objective description
            key_results: List of key results with 'description' and 'target_value'
            target_date: Target completion date
        """
        okr = {
            "objective": objective,
            "key_results": key_results,
            "target_date": target_date,
            "created_date": datetime.now().isoformat(),
        }
        self.okrs.append(okr)
        self._save_okrs()
        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh OKR display."""
        # Clear existing cards
        for widget in self.okr_container.winfo_children():
            widget.destroy()

        # Create OKR cards
        for i, okr in enumerate(self.okrs):
            self._create_okr_card(okr, i)

    def _create_okr_card(self, okr: Dict, index: int) -> None:
        """Create individual OKR card."""
        card = ttk.LabelFrame(self.okr_container, text=f"Objective: {okr['objective']}",
                             padding=10)
        card.pack(fill=tk.X, padx=5, pady=5)

        # Target date
        if okr.get("target_date"):
            ttk.Label(card, text=f"Target: {okr['target_date']}",
                     font=("Arial", 9)).pack(anchor="w")

        # Key results
        ttk.Label(card, text="Key Results:", font=("Arial", 9, "bold")).pack(
            anchor="w", pady=(10, 5))

        for kr in okr["key_results"]:
            kr_frame = ttk.Frame(card)
            kr_frame.pack(fill=tk.X, pady=2)

            ttk.Label(kr_frame, text=f"• {kr['description']}").pack(side=tk.LEFT)

            # Progress bar
            progress = kr.get("progress", 0)
            prog_bar = ttk.Progressbar(kr_frame, length=100, mode='determinate',
                                      value=progress)
            prog_bar.pack(side=tk.RIGHT, padx=(10, 0))

            ttk.Label(kr_frame, text=f"{progress}%").pack(side=tk.RIGHT)

    def _add_okr_dialog(self) -> None:
        """Show dialog to add new OKR."""
        dialog = tk.Toplevel(self)
        dialog.title("Add OKR")
        dialog.geometry("500x400")

        ttk.Label(dialog, text="Objective:", font=("Arial", 10, "bold")).pack(
            anchor="w", padx=10, pady=(10, 5))
        objective_entry = ttk.Entry(dialog, width=60)
        objective_entry.pack(padx=10, pady=5)

        ttk.Label(dialog, text="Key Results (one per line):",
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(15, 5))

        kr_text = tk.Text(dialog, height=10, width=60)
        kr_text.pack(padx=10, pady=5)

        ttk.Label(dialog, text="Target Date (YYYY-MM-DD):", font=("Arial", 10, "bold")).pack(
            anchor="w", padx=10, pady=(15, 5))
        date_entry = ttk.Entry(dialog, width=20)
        date_entry.pack(anchor="w", padx=10, pady=5)

        def save_okr():
            obj = objective_entry.get().strip()
            kr_lines = kr_text.get("1.0", "end-1c").strip().split("\n")
            target = date_entry.get().strip()

            if obj and kr_lines:
                key_results = [{"description": kr, "progress": 0, "target_value": 100}
                              for kr in kr_lines if kr.strip()]
                self.add_okr(obj, key_results, target)
                dialog.destroy()

        ttk.Button(dialog, text="Save", command=save_okr).pack(pady=10)


class NotesWidget(ttk.Frame):
    """
    Per-user notes widget.

    Notes are treated as tailoring (stored in user_preferences). They are not
    written into Oracle vault / durable registries automatically.
    """

    def __init__(self, parent, *, user_id: Optional[str] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.user_id: Optional[str] = user_id
        self._prefs = _try_get_user_preferences(user_id)
        self.notes: List[Dict[str, Any]] = []
        self._selected_index: Optional[int] = None

        self._create_ui()
        self._load_notes()

    def set_user_id(self, user_id: Optional[str]) -> None:
        self.user_id = user_id
        self._prefs = _try_get_user_preferences(user_id)
        self._load_notes()

    def _create_ui(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(header, text="Notes", font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        ttk.Button(header, text="+ New", command=self._new_note).pack(side=tk.RIGHT)
        ttk.Button(header, text="Save", command=self._save_current).pack(side=tk.RIGHT, padx=(0, 6))

        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=3)

        self.note_list = tk.Listbox(left, height=10)
        self.note_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        sb = ttk.Scrollbar(left, orient="vertical", command=self.note_list.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.note_list.configure(yscrollcommand=sb.set)
        self.note_list.bind("<<ListboxSelect>>", self._on_select)

        ttk.Label(right, text="Title:", font=("Arial", 9, "bold")).pack(anchor="w")
        self.title_var = tk.StringVar(value="")
        self.title_entry = ttk.Entry(right, textvariable=self.title_var)
        self.title_entry.pack(fill=tk.X, pady=(2, 10))

        ttk.Label(right, text="Body:", font=("Arial", 9, "bold")).pack(anchor="w")
        self.body_text = tk.Text(right, height=10, wrap=tk.WORD)
        self.body_text.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

    def _load_notes(self) -> None:
        try:
            if self._prefs is None or not hasattr(self._prefs, "get_preference"):
                self._refresh_list()
                return
            data = self._prefs.get_preference("notes.entries", default=[])
            if isinstance(data, list):
                self.notes = [x for x in data if isinstance(x, dict)]
        except Exception:
            pass
        self._refresh_list()

    def _persist_notes(self) -> None:
        try:
            if self._prefs is None or not hasattr(self._prefs, "set_preference"):
                return
            self._prefs.set_preference("notes.entries", list(self.notes or []))
        except Exception:
            return

    def _refresh_list(self) -> None:
        try:
            self.note_list.delete(0, tk.END)
            for n in self.notes:
                title = str(n.get("title") or "Untitled").strip()
                ts = str(n.get("updated_at") or n.get("created_at") or "")
                label = f"{title}" + (f"  ({ts[:10]})" if ts else "")
                self.note_list.insert(tk.END, label)
        except Exception:
            pass

    def _new_note(self) -> None:
        note = {
            "title": "New Note",
            "body": "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self.notes.insert(0, note)
        self._selected_index = 0
        self._persist_notes()
        self._refresh_list()
        self.note_list.selection_clear(0, tk.END)
        self.note_list.selection_set(0)
        self._load_into_editor(note)

    def _on_select(self, _event=None) -> None:
        try:
            idxs = self.note_list.curselection()
            if not idxs:
                return
            idx = int(idxs[0])
        except Exception:
            return
        if not (0 <= idx < len(self.notes)):
            return
        self._selected_index = idx
        self._load_into_editor(self.notes[idx])

    def _load_into_editor(self, note: Dict[str, Any]) -> None:
        try:
            self.title_var.set(str(note.get("title") or ""))
        except Exception:
            pass
        try:
            self.body_text.delete("1.0", tk.END)
            self.body_text.insert("1.0", str(note.get("body") or ""))
        except Exception:
            pass

    def _save_current(self) -> None:
        if self._selected_index is None:
            return
        if not (0 <= self._selected_index < len(self.notes)):
            return
        try:
            note = dict(self.notes[self._selected_index])
            note["title"] = str(self.title_var.get() or "").strip() or "Untitled"
            note["body"] = self.body_text.get("1.0", "end-1c")
            note["updated_at"] = datetime.now().isoformat()
            self.notes[self._selected_index] = note
        except Exception:
            return
        self._persist_notes()
        self._refresh_list()


class TaskListWidget(ttk.Frame):
    """
    Task list widget with filtering and status updates (Merovingian DB-backed).

    Schema used: `tasks(title, description, company_id?, status, priority, metadata_json)`
    - Due date is stored in metadata_json under `due_date` (best-effort).
    """

    def __init__(self, parent, *, db_path: Optional[Path] = None, company_id: Optional[int] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self._db_path = (db_path or _db_path()).resolve()
        self.company_id = company_id
        self.filter_status = "all"  # all/pending/in_progress/done
        self.tasks: List[Dict[str, Any]] = []

        self._create_ui()
        self._refresh_display()

    def set_company_id(self, company_id: Optional[int]) -> None:
        self.company_id = company_id
        self._refresh_display()

    def _create_ui(self):
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(header, text="Tasks", font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        ttk.Button(header, text="+ Add Task", command=self._add_task_dialog).pack(side=tk.RIGHT)

        # Filter buttons
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        self.filter_var = tk.StringVar(value="all")
        for status in ["all", "pending", "in_progress", "done"]:
            ttk.Radiobutton(
                filter_frame,
                text=status.replace("_", " ").title(),
                variable=self.filter_var,
                value=status,
                command=lambda s=status: self._filter_tasks(s),
            ).pack(side=tk.LEFT, padx=5)

        # Task tree
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("status", "priority", "due"),
            yscrollcommand=scrollbar.set,
            show="tree headings",
        )
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        self.tree.heading("status", text="Status")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("due", text="Due Date")

        self.tree.column("#0", width=260)
        self.tree.column("status", width=110)
        self.tree.column("priority", width=90)
        self.tree.column("due", width=110)

        self.tree.bind("<Double-1>", self._edit_task)
        self.tree.bind("<Button-3>", self._open_status_menu)

    def add_task(self, title: str, status: str = "pending", priority: str = "normal", due_date: str = "", description: str = "") -> None:
        status = (status or "pending").strip().lower()
        if status == "completed":
            status = "done"
        priority = (priority or "normal").strip().lower()
        now = datetime.now().isoformat()

        meta: Dict[str, Any] = {}
        if due_date:
            meta["due_date"] = due_date

        try:
            with _connect_db(self._db_path) as conn:
                cur = conn.cursor()
                cur.execute("PRAGMA table_info(tasks)")
                cols = {str(r[1]) for r in (cur.fetchall() or []) if r and r[1]}
                if "company_id" in cols:
                    cur.execute(
                        """
                        INSERT INTO tasks (title, description, company_id, status, priority, created_at, updated_at, metadata_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            title,
                            description,
                            self.company_id,
                            status,
                            priority,
                            now,
                            now,
                            json.dumps(meta, ensure_ascii=False) if meta else None,
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO tasks (title, description, status, priority, created_at, updated_at, metadata_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (title, description, status, priority, now, now, json.dumps(meta, ensure_ascii=False) if meta else None),
                    )
                conn.commit()
        except Exception:
            return

        self._refresh_display()

    def _fetch_tasks(self) -> List[Dict[str, Any]]:
        where = []
        params: List[Any] = []
        if self.company_id is not None:
            # Treat NULL as "shared" tasks visible to all company lobbies.
            where.append("(company_id=? OR company_id IS NULL)")
            params.append(int(self.company_id))
        if self.filter_status != "all":
            where.append("status=?")
            params.append(self.filter_status)

        sql = "SELECT id, title, status, priority, description, metadata_json, updated_at FROM tasks"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY CASE status WHEN 'in_progress' THEN 0 WHEN 'pending' THEN 1 WHEN 'done' THEN 2 ELSE 3 END, updated_at DESC, id DESC LIMIT 200"

        try:
            with _connect_db(self._db_path) as conn:
                cur = conn.cursor()
                cur.execute(sql, params)
                rows = cur.fetchall() or []
        except Exception:
            rows = []

        out: List[Dict[str, Any]] = []
        for r in rows:
            tid, title, status, priority, desc, meta_json, updated_at = r
            meta = {}
            due = ""
            try:
                meta = json.loads(meta_json) if meta_json else {}
                due = str(meta.get("due_date") or "")
            except Exception:
                meta = {}
            out.append(
                {
                    "id": int(tid),
                    "title": str(title or "").strip() or "(untitled)",
                    "status": str(status or "pending").strip(),
                    "priority": str(priority or "normal").strip(),
                    "description": str(desc or ""),
                    "metadata": meta,
                    "due_date": due,
                    "updated_at": str(updated_at or ""),
                }
            )
        return out

    def _refresh_display(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.tasks = self._fetch_tasks()
        for t in self.tasks:
            self.tree.insert("", "end", text=t["title"], values=(t["status"], t["priority"], t["due_date"]))

    def _filter_tasks(self, status: str) -> None:
        self.filter_status = status
        self._refresh_display()

    def _add_task_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Add Task")
        dialog.geometry("450x350")

        ttk.Label(dialog, text="Title:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        title_entry = ttk.Entry(dialog, width=40)
        title_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Status:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        status_var = tk.StringVar(value="pending")
        ttk.Combobox(dialog, textvariable=status_var, values=["pending", "in_progress", "done"], width=37).grid(
            row=1, column=1, padx=10, pady=5
        )

        ttk.Label(dialog, text="Priority:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        priority_var = tk.StringVar(value="normal")
        ttk.Combobox(dialog, textvariable=priority_var, values=["low", "normal", "high", "critical"], width=37).grid(
            row=2, column=1, padx=10, pady=5
        )

        ttk.Label(dialog, text="Due Date:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        due_entry = ttk.Entry(dialog, width=40)
        due_entry.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Description:").grid(row=4, column=0, sticky="nw", padx=10, pady=5)
        desc_text = tk.Text(dialog, height=8, width=40)
        desc_text.grid(row=4, column=1, padx=10, pady=5)

        def save_task():
            title = title_entry.get().strip()
            if title:
                self.add_task(
                    title,
                    status_var.get(),
                    priority_var.get(),
                    due_entry.get().strip(),
                    desc_text.get("1.0", "end-1c").strip(),
                )
                dialog.destroy()

        ttk.Button(dialog, text="Save", command=save_task).grid(row=5, column=1, pady=10, sticky="e", padx=10)

    def _edit_task(self, _event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = selection[0]
        idx = self.tree.index(item)
        if idx < 0 or idx >= len(self.tasks):
            return
        t = self.tasks[idx]
        task_id = t.get("id")

        dialog = tk.Toplevel(self)
        dialog.title("Edit Task")
        dialog.geometry("450x380")

        ttk.Label(dialog, text="Title:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        title_entry = ttk.Entry(dialog, width=40)
        title_entry.insert(0, t.get("title") or "")
        title_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Status:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        status_var = tk.StringVar(value=t.get("status") or "pending")
        ttk.Combobox(dialog, textvariable=status_var, values=["pending", "in_progress", "done", "blocked"], width=37).grid(
            row=1, column=1, padx=10, pady=5
        )

        ttk.Label(dialog, text="Priority:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        priority_var = tk.StringVar(value=t.get("priority") or "normal")
        ttk.Combobox(dialog, textvariable=priority_var, values=["low", "normal", "high", "critical"], width=37).grid(
            row=2, column=1, padx=10, pady=5
        )

        ttk.Label(dialog, text="Due Date:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        due_entry = ttk.Entry(dialog, width=40)
        due_entry.insert(0, t.get("due_date") or "")
        due_entry.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Description:").grid(row=4, column=0, sticky="nw", padx=10, pady=5)
        desc_text = tk.Text(dialog, width=40, height=8)
        desc_text.insert("1.0", t.get("description") or "")
        desc_text.grid(row=4, column=1, padx=10, pady=5)

        def update_task():
            title = title_entry.get().strip()
            if not title or task_id is None:
                return
            now = datetime.now().isoformat()
            meta = dict(t.get("metadata") or {})
            due = due_entry.get().strip()
            if due:
                meta["due_date"] = due
            else:
                meta.pop("due_date", None)
            try:
                with _connect_db(self._db_path) as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE tasks SET title=?, description=?, status=?, priority=?, updated_at=?, metadata_json=? WHERE id=?",
                        (
                            title,
                            desc_text.get("1.0", "end-1c").strip(),
                            status_var.get(),
                            priority_var.get(),
                            now,
                            json.dumps(meta, ensure_ascii=False) if meta else None,
                            int(task_id),
                        ),
                    )
                    conn.commit()
            except Exception:
                pass
            self._refresh_display()
            dialog.destroy()

        ttk.Button(dialog, text="Update", command=update_task).grid(row=5, column=1, pady=10, sticky="e", padx=10)

    def _open_status_menu(self, event) -> None:
        try:
            item = self.tree.identify_row(event.y)
            if not item:
                return
            self.tree.selection_set(item)
            menu = tk.Menu(self, tearoff=0)
            for st in ("pending", "in_progress", "done"):
                menu.add_command(label=f"Set: {st}", command=lambda s=st: self._quick_set_status(s))
            menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass

    def _quick_set_status(self, status: str) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        idx = self.tree.index(selection[0])
        if idx < 0 or idx >= len(self.tasks):
            return
        task_id = self.tasks[idx].get("id")
        if task_id is None:
            return
        now = datetime.now().isoformat()
        try:
            with _connect_db(self._db_path) as conn:
                cur = conn.cursor()
                cur.execute("UPDATE tasks SET status=?, updated_at=? WHERE id=?", (status, now, int(task_id)))
                conn.commit()
        except Exception:
            return
        self._refresh_display()


class CalendarWidget(ttk.Frame):
    """
    Calendar widget with event display.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.events: Dict[str, List[str]] = {}  # date -> list of events
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year

        self._create_ui()

    def _create_ui(self):
        """Create calendar UI."""
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(header, text="◀", width=3,
                  command=self._prev_month).pack(side=tk.LEFT)

        self.month_label = ttk.Label(header, text="", font=("Arial", 12, "bold"))
        self.month_label.pack(side=tk.LEFT, expand=True)

        ttk.Button(header, text="▶", width=3,
                  command=self._next_month).pack(side=tk.RIGHT)

        # Calendar grid
        self.calendar_frame = ttk.Frame(self)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._refresh_calendar()

    def _refresh_calendar(self):
        """Refresh calendar display."""
        # Clear existing calendar
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        # Update month label
        month_name = calendar.month_name[self.current_month]
        self.month_label.config(text=f"{month_name} {self.current_year}")

        # Day headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            ttk.Label(self.calendar_frame, text=day, font=("Arial", 9, "bold")).grid(
                row=0, column=i, padx=2, pady=2)

        # Calendar days
        cal = calendar.monthcalendar(self.current_year, self.current_month)

        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue

                date_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                has_events = date_str in self.events

                # Create day button
                btn_text = str(day)
                if has_events:
                    btn_text += f"\n●"

                btn = ttk.Button(self.calendar_frame, text=btn_text,
                               command=lambda d=date_str: self._show_day_events(d))
                btn.grid(row=week_num+1, column=day_num, sticky="nsew", padx=1, pady=1)

        # Configure grid weights
        for i in range(7):
            self.calendar_frame.columnconfigure(i, weight=1)

    def _prev_month(self):
        """Go to previous month."""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._refresh_calendar()

    def _next_month(self):
        """Go to next month."""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._refresh_calendar()

    def add_event(self, date: str, event: str) -> None:
        """
        Add event to calendar.

        Args:
            date: Date in YYYY-MM-DD format
            event: Event description
        """
        if date not in self.events:
            self.events[date] = []
        self.events[date].append(event)
        self._refresh_calendar()

    def _show_day_events(self, date: str) -> None:
        """Show events for specific day."""
        if date not in self.events or not self.events[date]:
            return

        # Create dialog to show events
        dialog = tk.Toplevel(self)
        dialog.title(f"Events - {date}")
        dialog.geometry("400x300")

        # Header
        header = ttk.Frame(dialog)
        header.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(header, text=f"Events for {date}",
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        # Events list
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        events_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                    font=("Arial", 10))
        events_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=events_listbox.yview)

        # Add events to listbox
        for event in self.events[date]:
            events_listbox.insert(tk.END, f"• {event}")

        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)


class NoticesWidget(ttk.Frame):
    """
    Notices/announcements widget.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.notices: List[Dict] = []

        self._create_ui()

    def _create_ui(self):
        """Create notices UI."""
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(header, text="📢 Notices", font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        ttk.Button(header, text="+ Add Notice",
                  command=self._add_notice_dialog).pack(side=tk.RIGHT)

        # Notices list (scrollable)
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.listbox.yview)

    def add_notice(self, title: str, message: str, priority: str = "normal") -> None:
        """Add notice to widget."""
        notice = {
            "title": title,
            "message": message,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
        }
        self.notices.insert(0, notice)  # New notices at top
        self._refresh_display()

    def _refresh_display(self):
        """Refresh notices display."""
        self.listbox.delete(0, tk.END)

        for notice in self.notices:
            icon = "🔴" if notice["priority"] == "high" else "🟡" if notice["priority"] == "medium" else "🟢"
            timestamp = datetime.fromisoformat(notice["timestamp"]).strftime("%Y-%m-%d %H:%M")
            self.listbox.insert(tk.END, f"{icon} [{timestamp}] {notice['title']}")

    def _add_notice_dialog(self):
        """Show dialog to add notice."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Notice")
        dialog.geometry("400x300")

        ttk.Label(dialog, text="Title:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        title_entry = ttk.Entry(dialog, width=40)
        title_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Priority:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        priority_var = tk.StringVar(value="normal")
        ttk.Combobox(dialog, textvariable=priority_var,
                    values=["low", "normal", "medium", "high"], width=37).grid(
            row=1, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Message:").grid(row=2, column=0, sticky="nw", padx=10, pady=5)
        message_text = tk.Text(dialog, height=10, width=40)
        message_text.grid(row=2, column=1, padx=10, pady=5)

        def save_notice():
            title = title_entry.get().strip()
            message = message_text.get("1.0", "end-1c").strip()
            if title and message:
                self.add_notice(title, message, priority_var.get())
                dialog.destroy()

        ttk.Button(dialog, text="Save", command=save_notice).grid(
            row=3, column=1, pady=10, sticky="e", padx=10)


class QuickLinksWidget(ttk.Frame):
    """
    Quick links/shortcuts widget.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.links: List[Dict] = []

        self._create_ui()

    def _create_ui(self):
        """Create quick links UI."""
        # Header
        ttk.Label(self, text="Quick Links", font=("Arial", 12, "bold")).pack(
            anchor="w", padx=5, pady=5)

        # Links container
        self.links_frame = ttk.Frame(self)
        self.links_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def add_link(self, name: str, action: Callable, icon: str = "•") -> None:
        """
        Add quick link.

        Args:
            name: Link display name
            action: Callable to execute on click
            icon: Icon/emoji for link
        """
        self.links.append({"name": name, "action": action, "icon": icon})
        self._refresh_display()

    def _refresh_display(self):
        """Refresh links display."""
        for widget in self.links_frame.winfo_children():
            widget.destroy()

        for link in self.links:
            btn = ttk.Button(self.links_frame,
                           text=f"{link['icon']} {link['name']}",
                           command=link['action'])
            btn.pack(fill=tk.X, pady=2)


class BackgroundJobsWidget(ttk.Frame):
    """
    Background jobs monitor (Smith/Merovingian).

    Uses DB table: jobs(job_type, status, params_json, metadata_json, result_json, error, updated_at).
    """

    def __init__(self, parent, *, db_path: Optional[Path] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self._db_path = (db_path or _db_path()).resolve()
        self._rows: List[Dict[str, Any]] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(top, text="Background Jobs", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side=tk.RIGHT)

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left = ttk.Frame(body)
        right = ttk.Frame(body)

        self.tree = ttk.Treeview(left, columns=("status", "type", "updated"), show="tree headings")
        self.tree.heading("#0", text="ID")
        self.tree.heading("status", text="Status")
        self.tree.heading("type", text="Type")
        self.tree.heading("updated", text="Updated")
        self.tree.column("#0", width=70)
        self.tree.column("status", width=100)
        self.tree.column("type", width=160)
        self.tree.column("updated", width=140)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._show_selected())

        sb = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.detail = tk.Text(right, wrap="word")
        self.detail.pack(fill=tk.BOTH, expand=True)
        self.detail.configure(state="disabled")

        btns = ttk.Frame(right)
        btns.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btns, text="Mark Done", command=lambda: self._set_status("completed")).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btns, text="Cancel", command=lambda: self._set_status("canceled")).pack(side=tk.LEFT)

        body.add(left, weight=2)
        body.add(right, weight=3)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self._rows = []
        try:
            with _connect_db(self._db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT id, job_type, status, updated_at, created_at, started_at, completed_at, params_json, metadata_json, result_json, error
                    FROM jobs
                    ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
                    LIMIT 200
                    """
                )
                rows = cur.fetchall() or []
        except Exception:
            rows = []

        for r in rows:
            jid, job_type, status, updated_at, created_at, started_at, completed_at, params_json, metadata_json, result_json, error = r
            row = {
                "id": int(jid),
                "job_type": str(job_type or ""),
                "status": str(status or "pending"),
                "updated_at": str(updated_at or created_at or ""),
                "started_at": started_at,
                "completed_at": completed_at,
                "params_json": params_json,
                "metadata_json": metadata_json,
                "result_json": result_json,
                "error": error,
            }
            self._rows.append(row)
            self.tree.insert("", "end", text=str(row["id"]), values=(row["status"], row["job_type"], row["updated_at"]))

        self._set_detail("Select a job to view details.")

    def _selected_job(self) -> Optional[Dict[str, Any]]:
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        if idx < 0 or idx >= len(self._rows):
            return None
        return self._rows[idx]

    def _show_selected(self):
        row = self._selected_job()
        if not row:
            return
        payload = {
            "id": row["id"],
            "job_type": row["job_type"],
            "status": row["status"],
            "updated_at": row["updated_at"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "params": _safe_json(row.get("params_json")),
            "metadata": _safe_json(row.get("metadata_json")),
            "result": _safe_json(row.get("result_json")),
            "error": row.get("error"),
        }
        self._set_detail(json.dumps(payload, indent=2, ensure_ascii=False))

    def _set_status(self, status: str):
        row = self._selected_job()
        if not row:
            return
        now = datetime.now().isoformat()
        try:
            with _connect_db(self._db_path) as conn:
                cur = conn.cursor()
                cur.execute("UPDATE jobs SET status=?, updated_at=? WHERE id=?", (status, now, int(row["id"])))
                conn.commit()
        except Exception:
            return
        self.refresh()

    def _set_detail(self, text: str):
        self.detail.configure(state="normal")
        self.detail.delete("1.0", tk.END)
        self.detail.insert(tk.END, text or "")
        self.detail.configure(state="disabled")


class OracleIngestionWidget(ttk.Frame):
    """
    Oracle ingestion queue monitor (Oracle/Smith).

    Uses DB table: oracle_ingestion_tasks(vault_id, task_type, priority, status, created_at, started_at, completed_at, ...)
    Joins: files(id, name, path) for display.
    """

    def __init__(self, parent, *, db_path: Optional[Path] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self._db_path = (db_path or _db_path()).resolve()
        self._rows: List[Dict[str, Any]] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(top, text="Oracle Ingestion Queue", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(top, text="Scan Inbox Markers", command=self._scan_inbox_markers).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(top, text="Process Next", command=self._process_next).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(top, text="Ingest Inbox", command=self._ingest_inbox).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(top, text="Ingest Folder…", command=self._ingest_folder).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side=tk.RIGHT)

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left = ttk.Frame(body)
        right = ttk.Frame(body)

        self.tree = ttk.Treeview(left, columns=("status", "type", "prio", "file", "ts"), show="headings")
        self.tree.heading("status", text="Status")
        self.tree.heading("type", text="Type")
        self.tree.heading("prio", text="P")
        self.tree.heading("file", text="File")
        self.tree.heading("ts", text="When")
        self.tree.column("status", width=110, anchor="w")
        self.tree.column("type", width=140, anchor="w")
        self.tree.column("prio", width=40, anchor="center")
        self.tree.column("file", width=260, anchor="w")
        self.tree.column("ts", width=160, anchor="w")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._show_selected())

        sb = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.detail = tk.Text(right, wrap="word")
        self.detail.pack(fill=tk.BOTH, expand=True)
        self.detail.configure(state="disabled")

        btns = ttk.Frame(right)
        btns.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btns, text="Retry", command=self._retry_selected).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btns, text="Cancel", command=self._cancel_selected).pack(side=tk.LEFT)

        body.add(left, weight=3)
        body.add(right, weight=4)

    def _load_oracle_integrator(self):
        ls_root = _find_lightspeed_root()
        file_path = (ls_root / "Z Axis" / "Z-2_Oracle" / "components" / "oracle_smart_floor_integrator.py").resolve()
        module_name = f"lightspeed_dynamic_oracle_integrator_{file_path.stem}_{abs(hash(str(file_path)))}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load spec for {file_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.OracleSmartFloorIntegrator()

    def _ingest_inbox(self):
        try:
            from core.config.paths import ORACLE_ARCHIVE  # type: ignore
            inbox = (Path(ORACLE_ARCHIVE) / "inbox").resolve()
        except Exception:
            inbox = (_find_lightspeed_root() / "Z Axis" / "Z-2_Oracle" / "archive" / "inbox").resolve()

        if not inbox.exists():
            messagebox.showinfo("Oracle Ingest", f"Inbox folder not found:\n{inbox}", parent=self)
            return

        try:
            integrator = self._load_oracle_integrator()
            # Default to document-like formats to prevent accidental ingestion of huge binaries.
            res = integrator.ingest_directory(
                str(inbox),
                recursive=True,
                include_extensions=[".txt", ".md", ".json", ".csv", ".py", ".pdf"],
            )
        except Exception as e:
            messagebox.showerror("Oracle Ingest", f"Failed ingesting inbox:\n{e}", parent=self)
            return

        messagebox.showinfo(
            "Oracle Ingest",
            f"Inbox: {inbox}\n\n"
            f"Files: {res.get('files_total')}\n"
            f"Ingested: {res.get('files_ingested')}\n"
            f"Deduped: {res.get('files_deduped')}\n"
            f"Failed: {res.get('files_failed')}",
            parent=self,
        )
        self.refresh()

    def _load_doc_scanner(self):
        ls_root = _find_lightspeed_root()
        file_path = (ls_root / "Z Axis" / "Z-3_Smith" / "tools" / "scan_docs_to_tasks.py").resolve()
        module_name = f"lightspeed_dynamic_scan_docs_{file_path.stem}_{abs(hash(str(file_path)))}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load spec for {file_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.scan_docs_to_db

    def _scan_inbox_markers(self):
        try:
            from core.config.paths import ORACLE_ARCHIVE  # type: ignore
            inbox = (Path(ORACLE_ARCHIVE) / "inbox").resolve()
        except Exception:
            inbox = (_find_lightspeed_root() / "Z Axis" / "Z-2_Oracle" / "archive" / "inbox").resolve()

        if not inbox.exists():
            messagebox.showinfo("Doc Scan", f"Inbox folder not found:\n{inbox}", parent=self)
            return

        try:
            scan_docs_to_db = self._load_doc_scanner()
            res = scan_docs_to_db(
                db_path=self._db_path,
                scan_root=inbox,
                include_exts=(".md", ".txt"),
                # Inbox lives under `archive/`; allow scanning it.
                exclude_dirs=(".git", "__pycache__", ".venv", "venv", "node_modules", "ai_logs", "logs", "legacy", "conversations"),
                create_tasks=True,
            )
        except Exception as e:
            messagebox.showerror("Doc Scan", f"Failed scanning inbox:\n{e}", parent=self)
            return

        messagebox.showinfo(
            "Doc Scan",
            f"Scan root: {inbox}\n\n"
            f"Files scanned: {res.files_scanned}\n"
            f"Markers found: {res.markers_found}\n"
            f"Markers inserted: {res.markers_inserted}\n"
            f"Tasks created: {res.tasks_created}",
            parent=self,
        )

    def _ingest_folder(self):
        folder = filedialog.askdirectory(title="Select folder to ingest into Oracle vault")
        if not folder:
            return
        try:
            integrator = self._load_oracle_integrator()
            res = integrator.ingest_directory(str(folder), recursive=True)
        except Exception as e:
            messagebox.showerror("Oracle Ingest", f"Failed ingesting folder:\n{e}", parent=self)
            return
        messagebox.showinfo(
            "Oracle Ingest",
            f"Folder: {folder}\n\n"
            f"Files: {res.get('files_total')}\n"
            f"Ingested: {res.get('files_ingested')}\n"
            f"Deduped: {res.get('files_deduped')}\n"
            f"Failed: {res.get('files_failed')}",
            parent=self,
        )
        self.refresh()

    def _process_next(self):
        try:
            integrator = self._load_oracle_integrator()
            results = integrator.process_pending_tasks(max_tasks=10)
        except Exception as e:
            messagebox.showerror("Oracle Process", f"Failed processing tasks:\n{e}", parent=self)
            return

        ok = sum(1 for r in results if r and r.get("success") is True)
        messagebox.showinfo("Oracle Process", f"Processed {len(results)} task(s).\nSuccess: {ok}", parent=self)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self._rows = []

        try:
            with _connect_db(self._db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT
                        t.id,
                        t.status,
                        t.task_type,
                        t.priority,
                        COALESCE(t.completed_at, t.started_at, t.created_at) AS ts,
                        t.created_at,
                        t.started_at,
                        t.completed_at,
                        t.vault_id,
                        f.name,
                        f.path,
                        t.file_metadata_json,
                        t.routing_results_json,
                        t.encyclopedia_updates,
                        t.error
                    FROM oracle_ingestion_tasks t
                    LEFT JOIN files f ON f.id = t.vault_id
                    ORDER BY COALESCE(t.completed_at, t.started_at, t.created_at) DESC, t.id DESC
                    LIMIT 250
                    """
                )
                rows = cur.fetchall() or []
        except Exception as e:
            self._set_detail(f"Oracle ingestion queue unavailable:\n{e}")
            return

        for r in rows:
            (
                tid,
                status,
                task_type,
                priority,
                ts,
                created_at,
                started_at,
                completed_at,
                vault_id,
                fname,
                fpath,
                file_meta_json,
                routing_json,
                encyclopedia_updates,
                error,
            ) = r
            file_label = (fname or (str(fpath).split("\\")[-1] if fpath else "")) or f"vault:{vault_id}"
            row = {
                "id": int(tid),
                "status": str(status or "queued"),
                "task_type": str(task_type or ""),
                "priority": int(priority or 0),
                "ts": str(ts or ""),
                "created_at": str(created_at or ""),
                "started_at": started_at,
                "completed_at": completed_at,
                "vault_id": vault_id,
                "file_name": fname,
                "file_path": fpath,
                "file_metadata_json": file_meta_json,
                "routing_results_json": routing_json,
                "encyclopedia_updates": encyclopedia_updates,
                "error": error,
            }
            self._rows.append(row)
            self.tree.insert(
                "",
                "end",
                values=(row["status"], row["task_type"], row["priority"], file_label, row["ts"]),
            )

        self._set_detail("Select an ingestion task to view details.")

    def _selected(self) -> Optional[Dict[str, Any]]:
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        if idx < 0 or idx >= len(self._rows):
            return None
        return self._rows[idx]

    def _show_selected(self):
        row = self._selected()
        if not row:
            return
        payload = {
            "id": row["id"],
            "status": row["status"],
            "task_type": row["task_type"],
            "priority": row["priority"],
            "ts": row["ts"],
            "created_at": row["created_at"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "vault_id": row["vault_id"],
            "file": {"name": row.get("file_name"), "path": row.get("file_path")},
            "file_metadata": _safe_json(row.get("file_metadata_json")),
            "routing_results": _safe_json(row.get("routing_results_json")),
            "encyclopedia_updates": row.get("encyclopedia_updates"),
            "error": row.get("error"),
        }
        self._set_detail(json.dumps(payload, indent=2, ensure_ascii=False))

    def _retry_selected(self):
        row = self._selected()
        if not row:
            return
        try:
            with _connect_db(self._db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE oracle_ingestion_tasks SET status='queued', started_at=NULL, completed_at=NULL, error=NULL WHERE id=?",
                    (int(row["id"]),),
                )
                conn.commit()
        except Exception:
            return
        self.refresh()

    def _cancel_selected(self):
        row = self._selected()
        if not row:
            return
        try:
            with _connect_db(self._db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE oracle_ingestion_tasks SET status='canceled', completed_at=? WHERE id=?",
                    (datetime.now().isoformat(), int(row["id"])),
                )
                conn.commit()
        except Exception:
            return
        self.refresh()

    def _set_detail(self, text: str):
        self.detail.configure(state="normal")
        self.detail.delete("1.0", tk.END)
        self.detail.insert(tk.END, text or "")
        self.detail.configure(state="disabled")


class DocTaskMarkersWidget(ttk.Frame):
    """
    Doc marker browser (TODO/FIXME/TBD/etc).

    Reads `doc_task_markers` and can create a task for a selected marker.
    """

    def __init__(self, parent, *, db_path: Optional[Path] = None, limit: int = 500, **kwargs):
        super().__init__(parent, **kwargs)
        self._db_path = (db_path or _db_path()).resolve()
        self._limit = int(limit)
        self._rows: List[Dict[str, Any]] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(top, text="Doc Markers", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(top, text="Open File", command=self._open_file).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(top, text="Create Task", command=self._create_task).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side=tk.RIGHT)

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left = ttk.Frame(body)
        right = ttk.Frame(body)

        self.tree = ttk.Treeview(left, columns=("marker", "file", "line", "ts"), show="headings")
        self.tree.heading("marker", text="Marker")
        self.tree.heading("file", text="File")
        self.tree.heading("line", text="Line")
        self.tree.heading("ts", text="When")
        self.tree.column("marker", width=120, anchor="w")
        self.tree.column("file", width=320, anchor="w")
        self.tree.column("line", width=60, anchor="center")
        self.tree.column("ts", width=160, anchor="w")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._show_selected())

        sb = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.detail = tk.Text(right, wrap="word")
        self.detail.pack(fill=tk.BOTH, expand=True)
        self.detail.configure(state="disabled")

        body.add(left, weight=3)
        body.add(right, weight=4)

    def _selected_row(self) -> Optional[Dict[str, Any]]:
        sel = self.tree.selection()
        if not sel:
            return None
        iid = sel[0]
        for r in self._rows:
            if str(r.get("id")) == str(iid):
                return r
        return None

    def _set_detail(self, text: str):
        self.detail.configure(state="normal")
        self.detail.delete("1.0", tk.END)
        self.detail.insert(tk.END, text or "")
        self.detail.configure(state="disabled")

    def _show_selected(self):
        row = self._selected_row()
        if not row:
            return
        payload = {
            "id": row.get("id"),
            "marker": row.get("marker"),
            "file_path": row.get("file_path"),
            "line_no": row.get("line_no"),
            "content": row.get("content"),
            "hash_sha256": row.get("hash_sha256"),
            "created_at": row.get("created_at"),
        }
        self._set_detail(json.dumps(payload, indent=2, ensure_ascii=False))

    def _open_file(self):
        row = self._selected_row()
        if not row:
            return
        fp = row.get("file_path") or ""
        if not fp:
            return
        try:
            import os

            os.startfile(fp)  # type: ignore[attr-defined]
        except Exception as e:
            messagebox.showerror("Open File", f"Failed opening file:\n{e}", parent=self)

    def _create_task(self):
        row = self._selected_row()
        if not row:
            return
        marker_hash = row.get("hash_sha256")
        file_path = row.get("file_path") or ""
        line_no = row.get("line_no")
        marker = row.get("marker") or "MARKER"
        content = row.get("content") or ""
        if not marker_hash:
            return

        now = datetime.now().isoformat()
        meta = {
            "source": "doc_task_markers_ui",
            "doc_marker_hash": marker_hash,
            "doc_marker_file": file_path,
            "doc_marker_line": line_no,
            "doc_marker": marker,
        }
        title = f"Resolve {marker}: {Path(file_path).name}:{line_no}"
        desc = f"{content}\n\nSource: {file_path}:{line_no}"

        try:
            with _connect_db(self._db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id FROM tasks WHERE metadata_json LIKE ? LIMIT 1",
                    (f'%\"doc_marker_hash\": \"{marker_hash}\"%',),
                )
                if cur.fetchone() is not None:
                    messagebox.showinfo("Create Task", "Task already exists for this marker.", parent=self)
                    return

                company_id = None
                try:
                    cur.execute("SELECT id, name FROM companies")
                    companies = {str(r[1]).strip().lower(): int(r[0]) for r in (cur.fetchall() or [])}
                    low = (file_path or "").lower()
                    if "emassc" in low:
                        company_id = companies.get("emassc")
                    elif "romer" in low or "römer" in low:
                        company_id = companies.get("romer industries") or companies.get("römer industries")
                except Exception:
                    company_id = None

                cur.execute(
                    """
                    INSERT INTO tasks (title, description, company_id, status, priority, created_at, updated_at, metadata_json)
                    VALUES (?, ?, ?, 'pending', 'normal', ?, ?, ?)
                    """,
                    (title, desc, company_id, now, now, json.dumps(meta, ensure_ascii=False)),
                )
                conn.commit()
        except Exception as e:
            messagebox.showerror("Create Task", f"Failed creating task:\n{e}", parent=self)
            return

        messagebox.showinfo("Create Task", "Task created.", parent=self)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self._rows = []

        try:
            with _connect_db(self._db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT id, file_path, line_no, marker, content, hash_sha256, created_at
                    FROM doc_task_markers
                    ORDER BY created_at DESC, id DESC
                    LIMIT ?
                    """,
                    (self._limit,),
                )
                rows = cur.fetchall() or []
        except Exception as e:
            self._set_detail(f"Doc markers unavailable:\n{e}")
            return

        for r in rows:
            mid, fp, line_no, marker, content, h, created_at = r
            label = Path(fp).name if fp else ""
            self.tree.insert("", tk.END, iid=str(mid), values=(marker, label, line_no, created_at))
            self._rows.append(
                {
                    "id": mid,
                    "file_path": fp,
                    "line_no": line_no,
                    "marker": marker,
                    "content": content,
                    "hash_sha256": h,
                    "created_at": created_at,
                }
            )

        if self._rows:
            self.tree.selection_set(str(self._rows[0]["id"]))
            self._show_selected()


class APITogglesWidget(ttk.Frame):
    """
    Trinity-facing API toggle surface backed by `config/unified_config.json`.
    """

    def __init__(self, parent, *, lightspeed_root: Optional[Path] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.ls_root = lightspeed_root or _find_lightspeed_root()
        self.cfg_path = (self.ls_root / "config" / "unified_config.json").resolve()
        self.cfg: Dict[str, Any] = {}
        self.vars: Dict[str, tk.BooleanVar] = {}
        self._build_ui()
        self._load()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(top, text="APIs", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(top, text="Reload", command=self._load).pack(side=tk.RIGHT)
        ttk.Button(top, text="Apply", command=self._apply).pack(side=tk.RIGHT, padx=(0, 6))
        ttk.Button(top, text="Manage…", command=self._open_api_manager).pack(side=tk.RIGHT, padx=(0, 6))

        self.body = ttk.Frame(self)
        self.body.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.status = ttk.Label(self, text=str(self.cfg_path))
        self.status.pack(fill=tk.X, padx=5, pady=(0, 5))

    def _load(self):
        try:
            self.cfg = json.loads(self.cfg_path.read_text(encoding="utf-8"))
        except Exception:
            self.cfg = {}

        for w in self.body.winfo_children():
            w.destroy()
        self.vars = {}

        api_keys = self.cfg.get("api_keys") or {}
        for key, section in api_keys.items():
            if not isinstance(section, dict):
                continue
            enabled = bool(section.get("enabled", False))
            v = tk.BooleanVar(value=enabled)
            self.vars[key] = v
            row = ttk.Frame(self.body)
            row.pack(fill=tk.X, pady=2)
            ttk.Checkbutton(row, text=key, variable=v).pack(side=tk.LEFT)

    def _apply(self):
        api_keys = self.cfg.get("api_keys") or {}
        for key, var in self.vars.items():
            section = api_keys.get(key)
            if isinstance(section, dict):
                section["enabled"] = bool(var.get())
        self.cfg["api_keys"] = api_keys
        try:
            self.cfg_path.write_text(json.dumps(self.cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            return

    def _open_api_manager(self):
        try:
            from core.api.api_manager import APIManager  # type: ignore
            mgr = APIManager()
            mgr.create_wizard_window(self.winfo_toplevel())
        except Exception as e:
            try:
                messagebox.showerror("API Manager", f"Could not open API Manager:\n{e}", parent=self.winfo_toplevel())
            except Exception:
                return


class DependencyMapWidget(ttk.Frame):
    """
    Quick dependency/service overview (dataindex + service registry).
    """

    def __init__(self, parent, *, lightspeed_root: Optional[Path] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.ls_root = lightspeed_root or _find_lightspeed_root()
        self.depmap_path = (self.ls_root / "dataindex" / "depmap.json").resolve()
        # Registry lives under TheConstruct floor (authoritative), not in root config.
        self.service_registry_path = (self.ls_root / "Z Axis" / "Z0_TheConstruct" / "Config" / "service_registry.json").resolve()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(top, text="Dependencies", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side=tk.RIGHT)

        self.text = tk.Text(self, wrap="word")
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.text.configure(state="disabled")

    def refresh(self):
        dep = {}
        reg = {}
        try:
            dep = json.loads(self.depmap_path.read_text(encoding="utf-8"))
        except Exception:
            dep = {}
        try:
            reg = json.loads(self.service_registry_path.read_text(encoding="utf-8"))
        except Exception:
            reg = {}

        nodes = dep.get("nodes")
        edges = dep.get("edges")
        issues = dep.get("issues") or {}

        enabled = []
        disabled = []
        for k, v in (reg or {}).items():
            if not isinstance(v, dict):
                continue
            if v.get("enabled", False):
                enabled.append(k)
            else:
                disabled.append(k)

        summary = {
            "depmap": str(self.depmap_path),
            "nodes": nodes,
            "edges": edges,
            "issues": {
                "missing_files": len(issues.get("missing_files") or []),
                "unresolvable_modules": len(issues.get("unresolvable_modules") or []),
                "invalid_module_names": len(issues.get("invalid_module_names") or []),
                "missing_manifests": len(issues.get("missing_manifests") or []),
            },
            "services": {"enabled": len(enabled), "disabled": len(disabled)},
        }
        self._set_text(json.dumps(summary, indent=2, ensure_ascii=False))

    def _set_text(self, text: str):
        self.text.configure(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, text or "")
        self.text.configure(state="disabled")


class DatabaseStatsWidget(ttk.Frame):
    """
    Database overview widget (SQLite).

    Shows:
    - DB path + file size
    - table count
    - row counts for key tables (fast COUNT(*))
    """

    def __init__(self, parent, *, lightspeed_root: Optional[Path] = None, db_path: Optional[Path] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.ls_root = lightspeed_root or _find_lightspeed_root()
        self.db_path = (db_path or _db_path(self.ls_root)).resolve()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(top, text="Database", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side=tk.RIGHT)

        self.text = tk.Text(self, wrap="word")
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.text.configure(state="disabled")

    def refresh(self):
        info: Dict[str, Any] = {
            "db_path": str(self.db_path),
            "exists": bool(self.db_path.exists()),
        }

        if self.db_path.exists():
            try:
                info["size_bytes"] = int(self.db_path.stat().st_size)
            except Exception:
                info["size_bytes"] = None

        tables: List[str] = []
        counts: Dict[str, Any] = {}
        if self.db_path.exists():
            try:
                with _connect_db(self.db_path) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                    tables = [str(r[0]) for r in (cur.fetchall() or []) if r and r[0]]

                    for t in ("companies", "projects", "files", "tasks", "jobs"):
                        if t not in tables:
                            continue
                        try:
                            cur.execute(f"SELECT COUNT(*) FROM {t}")
                            counts[t] = int((cur.fetchone() or [0])[0])
                        except Exception:
                            counts[t] = None
            except Exception as e:
                info["error"] = str(e)

        info["tables"] = len(tables)
        info["row_counts"] = counts
        self._set_text(json.dumps(info, indent=2, ensure_ascii=False))

    def _set_text(self, text: str):
        self.text.configure(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, text or "")
        self.text.configure(state="disabled")


class RecentActivityWidget(ttk.Frame):
    """
    Recent activity feed (DB-backed).

    Pulls a small, best-effort timeline from:
    - tasks (created/updated)
    - jobs (created/updated)
    - projects (created/updated)
    - files (created)
    """

    def __init__(self, parent, *, db_path: Optional[Path] = None, company_id: Optional[int] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self._db_path = (db_path or _db_path()).resolve()
        self.company_id = company_id
        self._rows: List[Dict[str, Any]] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(top, text="Recent Activity", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side=tk.RIGHT)

        self.tree = ttk.Treeview(self, columns=("kind", "summary", "ts"), show="headings", height=8)
        self.tree.heading("kind", text="Kind")
        self.tree.heading("summary", text="Summary")
        self.tree.heading("ts", text="When")
        self.tree.column("kind", width=110, anchor="w")
        self.tree.column("summary", width=420, anchor="w")
        self.tree.column("ts", width=160, anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def set_company_id(self, company_id: Optional[int]) -> None:
        self.company_id = company_id
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self._rows = []

        def parse_ts(value: Any) -> float:
            if not value:
                return 0.0
            try:
                return datetime.fromisoformat(str(value)).timestamp()
            except Exception:
                return 0.0

        items: List[Dict[str, Any]] = []
        try:
            with _connect_db(self._db_path) as conn:
                cur = conn.cursor()

                # Tasks
                try:
                    where = ""
                    params: List[Any] = []
                    if self.company_id is not None:
                        where = "WHERE (company_id=? OR company_id IS NULL)"
                        params.append(int(self.company_id))
                    cur.execute(
                        f"""
                        SELECT id, title, status, COALESCE(updated_at, created_at) AS ts
                        FROM tasks
                        {where}
                        ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
                        LIMIT 25
                        """,
                        params,
                    )
                    for (tid, title, status, ts) in (cur.fetchall() or []):
                        items.append(
                            {
                                "kind": "task",
                                "summary": f"{title} ({status})",
                                "ts": str(ts or ""),
                                "_sort": parse_ts(ts),
                            }
                        )
                except Exception:
                    pass

                # Jobs
                try:
                    cur.execute(
                        """
                        SELECT id, job_type, status, COALESCE(updated_at, created_at) AS ts
                        FROM jobs
                        ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
                        LIMIT 25
                        """
                    )
                    for (jid, job_type, status, ts) in (cur.fetchall() or []):
                        items.append(
                            {
                                "kind": "job",
                                "summary": f"{job_type} ({status})",
                                "ts": str(ts or ""),
                                "_sort": parse_ts(ts),
                            }
                        )
                except Exception:
                    pass

                # Projects
                try:
                    where = ""
                    params = []
                    if self.company_id is not None:
                        where = "WHERE company_id=?"
                        params.append(int(self.company_id))
                    cur.execute(
                        f"""
                        SELECT id, name, status, COALESCE(updated_at, created_at) AS ts
                        FROM projects
                        {where}
                        ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
                        LIMIT 25
                        """,
                        params,
                    )
                    for (pid, name, status, ts) in (cur.fetchall() or []):
                        items.append(
                            {
                                "kind": "project",
                                "summary": f"{name} ({status})",
                                "ts": str(ts or ""),
                                "_sort": parse_ts(ts),
                            }
                        )
                except Exception:
                    pass

                # Files (best-effort company scoping via project join)
                try:
                    if self.company_id is not None:
                        cur.execute(
                            """
                            SELECT f.id, f.name, f.path, f.created_at
                            FROM files f
                            JOIN projects p ON p.id = f.project_id
                            WHERE p.company_id = ?
                            ORDER BY f.created_at DESC, f.id DESC
                            LIMIT 25
                            """,
                            (int(self.company_id),),
                        )
                    else:
                        cur.execute(
                            """
                            SELECT id, name, path, created_at
                            FROM files
                            ORDER BY created_at DESC, id DESC
                            LIMIT 25
                            """
                        )
                    for (fid, name, path, ts) in (cur.fetchall() or []):
                        label = name or (str(path).split("\\")[-1] if path else "file")
                        items.append(
                            {
                                "kind": "file",
                                "summary": str(label),
                                "ts": str(ts or ""),
                                "_sort": parse_ts(ts),
                            }
                        )
                except Exception:
                    pass
        except Exception:
            items = []

        items_sorted = sorted(items, key=lambda x: float(x.get("_sort") or 0.0), reverse=True)[:20]
        for it in items_sorted:
            self.tree.insert("", "end", values=(it.get("kind"), it.get("summary"), it.get("ts")))
            self._rows.append(it)


def _safe_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


class ChatConversationsWidget(ttk.Frame):
    """Browse imported chat conversations (e.g., GPT exports) from the unified DB."""

    def __init__(self, parent, *, ls_root: Optional[Path] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.ls_root = ls_root or _find_lightspeed_root()
        self.db_path = _db_path(self.ls_root)

        self.var_query = tk.StringVar(value="")
        self.var_company = tk.StringVar(value="All")
        self.var_limit = tk.StringVar(value="50")

        self._create_ui()
        self.refresh_conversations()

    def _create_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(header, text="Chat Conversations", font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        controls = ttk.Frame(self)
        controls.pack(fill=tk.X, padx=6, pady=(0, 6))

        ttk.Label(controls, text="Search").pack(side=tk.LEFT)
        q = ttk.Entry(controls, textvariable=self.var_query, width=36)
        q.pack(side=tk.LEFT, padx=(6, 10))
        q.bind("<Return>", lambda _e: self.refresh_conversations())

        ttk.Label(controls, text="Company").pack(side=tk.LEFT)
        company = ttk.Combobox(
            controls,
            textvariable=self.var_company,
            state="readonly",
            width=14,
            values=["All", "Romer Industries", "EMASSC"],
        )
        company.pack(side=tk.LEFT, padx=(6, 10))

        ttk.Label(controls, text="Limit").pack(side=tk.LEFT)
        ttk.Entry(controls, textvariable=self.var_limit, width=6).pack(side=tk.LEFT, padx=(6, 10))

        ttk.Button(controls, text="Refresh", command=self.refresh_conversations).pack(side=tk.LEFT)
        ttk.Button(controls, text="Export Markdown", command=self.export_selected_markdown).pack(side=tk.LEFT, padx=(8, 0))

        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

        cols = ("id", "title", "company", "source", "msgs")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=14)
        for col, title, width in [
            ("id", "ID", 60),
            ("title", "Title", 260),
            ("company", "Company", 140),
            ("source", "Source", 140),
            ("msgs", "Msgs", 60),
        ]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._load_messages())

        right = ttk.LabelFrame(body, text="Messages")
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        self.messages = tk.Text(right, wrap="word", height=18)
        self.messages.grid(row=0, column=0, sticky="nsew")
        sb2 = ttk.Scrollbar(right, orient="vertical", command=self.messages.yview)
        sb2.grid(row=0, column=1, sticky="ns")
        self.messages.configure(yscrollcommand=sb2.set)

        footer = ttk.Frame(self)
        footer.pack(fill=tk.X, padx=6, pady=(0, 6))
        self.status = ttk.Label(footer, text="")
        self.status.pack(side=tk.LEFT)

    def _company_filter_clause(self) -> tuple[str, list[Any]]:
        if self.var_company.get() == "All":
            return "", []
        return " AND lower(co.name)=lower(?) ", [self.var_company.get()]

    def refresh_conversations(self):
        if not self.db_path.exists():
            self.status.config(text=f"DB not found: {self.db_path}")
            return

        query = (self.var_query.get() or "").strip().lower()
        like = f"%{query}%"
        try:
            limit = max(1, min(500, int(str(self.var_limit.get() or "50").strip())))
        except Exception:
            limit = 50

        company_clause, company_params = self._company_filter_clause()

        sql = (
            "SELECT cc.id, cc.title, co.name, cc.source, cc.message_count "
            "FROM chat_conversations cc "
            "LEFT JOIN companies co ON cc.company_id=co.id "
            "WHERE 1=1 "
        )
        params: list[Any] = []
        if query:
            sql += " AND (lower(COALESCE(cc.title,'')) LIKE ? OR lower(COALESCE(cc.metadata_json,'')) LIKE ?) "
            params.extend([like, like])
        sql += company_clause
        params.extend(company_params)
        sql += " ORDER BY COALESCE(cc.update_time_ts, cc.create_time_ts) DESC, cc.id DESC LIMIT ? "
        params.append(limit)

        try:
            with _connect_db(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(sql, params)
                rows = cur.fetchall()
        except Exception as exc:
            self.status.config(text=f"Query failed: {exc}")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in rows:
            self.tree.insert(
                "",
                "end",
                iid=str(r["id"]),
                values=(r["id"], r["title"] or "", r["name"] or "", r["source"] or "", r["message_count"] or 0),
            )

        self.status.config(text=f"{len(rows)} conversations")
        try:
            self.messages.delete("1.0", "end")
        except Exception:
            pass

    def _selected_conversation_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except Exception:
            return None

    def _load_messages(self):
        cid = self._selected_conversation_id()
        if cid is None or not self.db_path.exists():
            return

        try:
            with _connect_db(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(
                    "SELECT role, author_name, create_time_ts, content_text "
                    "FROM chat_messages WHERE conversation_id=? "
                    "ORDER BY COALESCE(create_time_ts, 0) ASC, id ASC LIMIT 5000",
                    (cid,),
                )
                rows = cur.fetchall()
        except Exception as exc:
            self.status.config(text=f"Load messages failed: {exc}")
            return

        self.messages.delete("1.0", "end")
        for r in rows:
            role = (r["role"] or "unknown").strip()
            author = (r["author_name"] or "").strip()
            ts = r["create_time_ts"]
            try:
                ts_str = datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M") if ts else ""
            except Exception:
                ts_str = ""
            header = f"[{ts_str}] {role}{(':'+author) if author else ''}"
            self.messages.insert("end", header + "\n", ("hdr",))
            text = (r["content_text"] or "").strip()
            if len(text) > 12000:
                text = text[:12000] + "\n…(truncated)…"
            self.messages.insert("end", text + "\n\n")
        try:
            self.messages.tag_configure("hdr", font=("Consolas", 10, "bold"))
        except Exception:
            pass

        self.status.config(text=f"Loaded {len(rows)} messages")

    def export_selected_markdown(self):
        cid = self._selected_conversation_id()
        if cid is None:
            messagebox.showinfo("Export", "Select a conversation first.")
            return
        if not self.db_path.exists():
            messagebox.showerror("Export", f"DB not found: {self.db_path}")
            return

        default_dir = (self.ls_root / "Z Axis" / "Z-2_Oracle" / "archive" / "conversations" / "exports_md")
        try:
            default_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        out_path = filedialog.asksaveasfilename(
            title="Export conversation to Markdown",
            initialdir=str(default_dir) if default_dir.exists() else str(self.ls_root),
            initialfile=f"conversation_{cid}.md",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("All files", "*.*")],
        )
        if not out_path:
            return

        try:
            with _connect_db(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(
                    "SELECT cc.id, cc.title, cc.source, cc.message_count, cc.imported_at, co.name AS company "
                    "FROM chat_conversations cc LEFT JOIN companies co ON cc.company_id=co.id WHERE cc.id=? LIMIT 1",
                    (cid,),
                )
                conv = cur.fetchone()
                cur.execute(
                    "SELECT role, author_name, create_time_ts, content_text "
                    "FROM chat_messages WHERE conversation_id=? "
                    "ORDER BY COALESCE(create_time_ts, 0) ASC, id ASC",
                    (cid,),
                )
                msgs = cur.fetchall()
        except Exception as exc:
            messagebox.showerror("Export", f"Export query failed:\n{exc}")
            return

        lines: list[str] = []
        lines.append(f"# Conversation {cid}")
        if conv:
            lines.append("")
            lines.append(f"- Title: {conv['title'] or ''}")
            lines.append(f"- Company: {conv['company'] or ''}")
            lines.append(f"- Source: {conv['source'] or ''}")
            lines.append(f"- Imported: {conv['imported_at'] or ''}")
            lines.append(f"- Messages: {conv['message_count'] or 0}")
            lines.append("")
        lines.append("---")
        lines.append("")
        for r in msgs:
            role = (r["role"] or "unknown").strip()
            author = (r["author_name"] or "").strip()
            ts = r["create_time_ts"]
            try:
                ts_str = datetime.fromtimestamp(float(ts)).isoformat(sep=" ", timespec="minutes") if ts else ""
            except Exception:
                ts_str = ""
            lines.append(f"## {role}{(':'+author) if author else ''} {ts_str}".strip())
            lines.append("")
            lines.append((r["content_text"] or "").strip())
            lines.append("")

        try:
            Path(out_path).write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
            messagebox.showinfo("Export", f"Exported to:\n{out_path}")
        except Exception as exc:
            messagebox.showerror("Export", f"Write failed:\n{exc}")


def launch_chat_browser(parent: Optional[tk.Misc] = None):
    """Convenience launcher for the chat browser widget."""
    win = tk.Toplevel(parent) if parent is not None else tk.Tk()
    win.title("Chat Conversations Browser")
    win.geometry("1200x800")
    widget = ChatConversationsWidget(win)
    widget.pack(fill=tk.BOTH, expand=True)
    return win
