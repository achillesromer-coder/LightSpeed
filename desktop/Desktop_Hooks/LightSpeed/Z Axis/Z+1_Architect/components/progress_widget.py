"""
Progress Tracking Widgets - B5
================================

Comprehensive progress tracking widgets for visualizing task completion and status.

Features:
- Linear progress bar
- Circular progress indicator
- Step-by-step progress tracker
- Multi-progress dashboard
- Timeline progress
- Task completion checklist
- Percentage display
- Estimated time remaining
- Color-coded status

Author: LightSpeed Platform
Date: December 16, 2025
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Optional, Callable, Any, Tuple
import math
from datetime import datetime, timedelta
import json
import sqlite3
from pathlib import Path


def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
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


def _db_path(ls_root: Path) -> Path:
    cfg = ls_root / "config" / "unified_config.json"
    try:
        d = json.loads(cfg.read_text(encoding="utf-8"))
        rel = (d.get("database") or {}).get("path")
        if rel:
            return (ls_root / rel).resolve()
    except Exception:
        pass
    return (ls_root / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db").resolve()


class LinearProgress(tk.Frame):
    """Linear progress bar with percentage and label."""

    def __init__(self, parent, label: str = '', **kwargs):
        super().__init__(parent, bg=kwargs.get('bg', '#2d2d2d'))
        self.label_text = label
        self.progress = 0  # 0-100
        self.show_percentage = kwargs.get('show_percentage', True)
        self.color = kwargs.get('color', '#00C49F')
        self.height = kwargs.get('height', 30)

        self._build_ui()

    def _build_ui(self):
        """Build progress bar UI."""
        # Label
        if self.label_text:
            self.label = tk.Label(
                self,
                text=self.label_text,
                bg='#2d2d2d',
                fg='white',
                font=('Arial', 10),
                anchor='w'
            )
            self.label.pack(side='top', fill='x', pady=(0, 5))

        # Progress frame
        progress_frame = tk.Frame(self, bg='#2d2d2d')
        progress_frame.pack(side='top', fill='x')

        # Progress bar canvas
        self.canvas = tk.Canvas(
            progress_frame,
            height=self.height,
            bg='#404040',
            highlightthickness=0
        )
        self.canvas.pack(side='left', fill='x', expand=True)

        # Percentage label
        if self.show_percentage:
            self.percentage_label = tk.Label(
                progress_frame,
                text='0%',
                bg='#2d2d2d',
                fg='white',
                font=('Arial', 10, 'bold'),
                width=6
            )
            self.percentage_label.pack(side='right', padx=(5, 0))

        self._draw()

    def _draw(self):
        """Draw progress bar."""
        self.canvas.delete('all')

        width = self.canvas.winfo_width()
        if width <= 1:
            width = 300

        # Calculate fill width
        fill_width = int(width * (self.progress / 100))

        # Draw filled portion
        if fill_width > 0:
            self.canvas.create_rectangle(
                0, 0, fill_width, self.height,
                fill=self.color,
                outline=''
            )

        # Draw percentage text on bar
        if self.show_percentage:
            self.percentage_label.config(text=f'{int(self.progress)}%')

    def set_progress(self, value: float):
        """Set progress value (0-100)."""
        self.progress = max(0, min(100, value))
        self.after(10, self._draw)  # Delay to ensure canvas has size

    def update_label(self, text: str):
        """Update label text."""
        if hasattr(self, 'label'):
            self.label.config(text=text)


class StepProgress(tk.Frame):
    """Step-by-step progress tracker."""

    def __init__(self, parent, steps: List[str], **kwargs):
        super().__init__(parent, bg=kwargs.get('bg', '#2d2d2d'))
        self.steps = steps
        self.current_step = 0
        self.completed_color = kwargs.get('completed_color', '#00C49F')
        self.active_color = kwargs.get('active_color', '#0088FE')
        self.pending_color = kwargs.get('pending_color', '#858585')

        self._build_ui()


class DBTaskBoard(tk.Frame):
    """
    Database-backed task board (Merovingian DB → Architect planning surface).

    Shows tasks created from doc marker scans + any manually created tasks.
    Supports status changes with immediate persistence.
    """

    def __init__(self, parent, *, lightspeed_root: Optional[Path] = None, db_path: Optional[Path] = None, **kwargs):
        super().__init__(parent, bg=kwargs.get("bg", "#2d2d2d"))
        self.lightspeed_root = lightspeed_root or _find_lightspeed_root(Path(__file__))
        self.db_path = (db_path or _db_path(self.lightspeed_root)).resolve()

        self._companies: List[Tuple[Optional[int], str]] = [(None, "All Companies")]
        self._rows: List[Dict[str, Any]] = []

        self._build_ui()
        self._load_companies()
        self.refresh()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
        return conn

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top = tk.Frame(self, bg=self["bg"])
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        top.columnconfigure(5, weight=1)

        tk.Label(top, text="Company", bg=self["bg"], fg="white").grid(row=0, column=0, sticky="w")
        self.company_var = tk.StringVar(value="All Companies")
        self.company_combo = ttk.Combobox(top, textvariable=self.company_var, state="readonly", width=20)
        self.company_combo.grid(row=0, column=1, sticky="w", padx=(6, 12))
        self.company_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        tk.Label(top, text="Status", bg=self["bg"], fg="white").grid(row=0, column=2, sticky="w")
        self.status_var = tk.StringVar(value="open")
        self.status_combo = ttk.Combobox(top, textvariable=self.status_var, state="readonly", width=12, values=["open", "pending", "in_progress", "done", "all"])
        self.status_combo.grid(row=0, column=3, sticky="w", padx=(6, 12))
        self.status_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        tk.Label(top, text="Search", bg=self["bg"], fg="white").grid(row=0, column=4, sticky="w")
        self.search_var = tk.StringVar(value="")
        self.search_entry = ttk.Entry(top, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=5, sticky="ew", padx=(6, 12))
        self.search_entry.bind("<Return>", lambda _e: self.refresh())

        ttk.Button(top, text="Refresh", command=self.refresh).grid(row=0, column=6, sticky="e")

        body = tk.Frame(self, bg=self["bg"])
        body.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(body, bg="#1f1f1f", fg="white", selectbackground="#00d4ff", activestyle="dotbox")
        self.listbox.grid(row=0, column=0, sticky="nsew")
        self.listbox.bind("<<ListboxSelect>>", lambda _e: self._on_select())

        scroll = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=0, sticky="nse")

        right = tk.Frame(body, bg=self["bg"])
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self.detail_title = tk.Label(right, text="Select a task", bg=self["bg"], fg="white", font=("Arial", 12, "bold"), anchor="w")
        self.detail_title.grid(row=0, column=0, sticky="ew")

        self.detail_text = tk.Text(right, bg="#141414", fg="white", wrap="word")
        self.detail_text.grid(row=1, column=0, sticky="nsew", pady=(8, 8))
        self.detail_text.configure(state="disabled")

        btns = tk.Frame(right, bg=self["bg"])
        btns.grid(row=2, column=0, sticky="ew")

        self.btn_pending = ttk.Button(btns, text="Pending", command=lambda: self._set_selected_status("pending"))
        self.btn_inprog = ttk.Button(btns, text="In Progress", command=lambda: self._set_selected_status("in_progress"))
        self.btn_done = ttk.Button(btns, text="Done", command=lambda: self._set_selected_status("done"))
        self.btn_pending.pack(side="left", padx=(0, 8))
        self.btn_inprog.pack(side="left", padx=(0, 8))
        self.btn_done.pack(side="left")

        self.footer = tk.Label(self, text=str(self.db_path), bg=self["bg"], fg="#aaaaaa", anchor="w")
        self.footer.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))

    def _load_companies(self) -> None:
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM companies ORDER BY name")
                rows = cur.fetchall() or []
                self._companies = [(None, "All Companies")] + [(int(r[0]), str(r[1])) for r in rows if r and r[0] is not None]
        except Exception:
            self._companies = [(None, "All Companies")]

        self.company_combo["values"] = [name for _id, name in self._companies]
        if self.company_var.get() not in self.company_combo["values"]:
            self.company_var.set("All Companies")

    def _selected_company_id(self) -> Optional[int]:
        selected = self.company_var.get()
        for cid, name in self._companies:
            if name == selected:
                return cid
        return None

    def refresh(self) -> None:
        self.listbox.delete(0, tk.END)
        self._rows = []

        cid = self._selected_company_id()
        status = (self.status_var.get() or "open").strip().lower()
        q = (self.search_var.get() or "").strip()

        where = []
        params: List[Any] = []
        if cid is not None:
            # Treat NULL as "shared" tasks visible to all company views.
            where.append("(company_id=? OR company_id IS NULL)")
            params.append(cid)

        if status == "open":
            where.append("status IN ('pending','in_progress')")
        elif status != "all":
            where.append("status=?")
            params.append(status)

        if q:
            where.append("(title LIKE ? OR description LIKE ? OR metadata_json LIKE ?)")
            pat = f"%{q}%"
            params.extend([pat, pat, pat])

        sql = "SELECT id, title, status, priority, updated_at, description FROM tasks"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY CASE status WHEN 'in_progress' THEN 0 WHEN 'pending' THEN 1 WHEN 'done' THEN 2 ELSE 3 END, updated_at DESC, id DESC LIMIT 500"

        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(sql, params)
                rows = cur.fetchall() or []
        except Exception as e:
            self._set_details(f"Database error: {e}", "(error)")
            return

        for r in rows:
            tid, title, st, pr, upd, desc = r
            title = str(title or "").strip() or "(untitled)"
            st = str(st or "pending")
            label = f"[{st}] {title}"
            self.listbox.insert(tk.END, label)
            self._rows.append({"id": int(tid), "title": title, "status": st, "priority": pr, "updated_at": upd, "description": desc})

        self._set_details("", "Select a task")

    def _on_select(self) -> None:
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self._rows):
            return
        row = self._rows[idx]
        text = (row.get("description") or "").strip()
        if not text:
            text = "(No description)"
        self._set_details(text, f"{row.get('title')}  •  {row.get('status')}")

    def _set_details(self, text: str, title: str) -> None:
        self.detail_title.config(text=title)
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)
        if text:
            self.detail_text.insert(tk.END, text)
        self.detail_text.configure(state="disabled")

    def _set_selected_status(self, new_status: str) -> None:
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self._rows):
            return
        task_id = self._rows[idx]["id"]
        now = datetime.now().isoformat()
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE tasks SET status=?, updated_at=? WHERE id=?", (new_status, now, int(task_id)))
                conn.commit()
        except Exception:
            return
        self.refresh()

    def _build_ui(self):
        """Build step progress UI."""
        self.step_frames = []

        for i, step in enumerate(self.steps):
            # Step container
            step_container = tk.Frame(self, bg='#2d2d2d')
            step_container.pack(side='left', fill='x', expand=True, padx=5)

            # Step indicator (circle)
            indicator_frame = tk.Frame(step_container, bg='#2d2d2d')
            indicator_frame.pack(side='top')

            indicator = tk.Canvas(
                indicator_frame,
                width=40,
                height=40,
                bg='#2d2d2d',
                highlightthickness=0
            )
            indicator.pack()

            # Draw circle
            color = self.pending_color
            if i < self.current_step:
                color = self.completed_color
            elif i == self.current_step:
                color = self.active_color

            indicator.create_oval(5, 5, 35, 35, fill=color, outline='')

            # Step number or checkmark
            if i < self.current_step:
                text = '✓'
            else:
                text = str(i + 1)

            indicator.create_text(
                20, 20,
                text=text,
                fill='white',
                font=('Arial', 14, 'bold')
            )

            # Step label
            label = tk.Label(
                step_container,
                text=step,
                bg='#2d2d2d',
                fg='white' if i <= self.current_step else '#858585',
                font=('Arial', 9),
                wraplength=100
            )
            label.pack(side='top', pady=(5, 0))

            # Connector line (except for last step)
            if i < len(self.steps) - 1:
                line = tk.Canvas(
                    step_container,
                    height=2,
                    bg='#2d2d2d',
                    highlightthickness=0
                )
                line.pack(side='top', fill='x', pady=10)
                line.create_line(
                    0, 1, 200, 1,
                    fill=self.completed_color if i < self.current_step else self.pending_color,
                    width=2
                )

            self.step_frames.append((indicator, label))

    def set_step(self, step_index: int):
        """Set current step."""
        self.current_step = step_index
        # Rebuild UI to update colors
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def complete_step(self):
        """Mark current step as complete and move to next."""
        if self.current_step < len(self.steps) - 1:
            self.set_step(self.current_step + 1)

    def get_progress_percentage(self) -> float:
        """Get progress as percentage."""
        return (self.current_step / len(self.steps)) * 100


class MultiProgress(tk.Frame):
    """Multi-task progress dashboard."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=kwargs.get('bg', '#2d2d2d'))
        self.tasks: Dict[str, LinearProgress] = {}
        self._build_ui()

    def _build_ui(self):
        """Build multi-progress UI."""
        # Header
        header = tk.Frame(self, bg='#1e1e1e', height=40)
        header.pack(side='top', fill='x')

        tk.Label(
            header,
            text='Task Progress Dashboard',
            bg='#1e1e1e',
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack(side='left', padx=10, pady=10)

        # Overall progress
        self.overall_label = tk.Label(
            header,
            text='Overall: 0%',
            bg='#1e1e1e',
            fg='#00C49F',
            font=('Arial', 10, 'bold')
        )
        self.overall_label.pack(side='right', padx=10)

        # Scrollable task list
        canvas = tk.Canvas(self, bg='#2d2d2d', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        self.task_frame = tk.Frame(canvas, bg='#2d2d2d')

        self.task_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        canvas.create_window((0, 0), window=self.task_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def add_task(self, task_id: str, label: str, initial_progress: float = 0):
        """Add a task to track."""
        progress_bar = LinearProgress(self.task_frame, label=label, show_percentage=True)
        progress_bar.pack(fill='x', padx=10, pady=5)
        progress_bar.set_progress(initial_progress)

        self.tasks[task_id] = progress_bar
        self._update_overall()

    def update_task(self, task_id: str, progress: float):
        """Update task progress."""
        if task_id in self.tasks:
            self.tasks[task_id].set_progress(progress)
            self._update_overall()

    def remove_task(self, task_id: str):
        """Remove a task."""
        if task_id in self.tasks:
            self.tasks[task_id].destroy()
            del self.tasks[task_id]
            self._update_overall()

    def _update_overall(self):
        """Update overall progress."""
        if not self.tasks:
            self.overall_label.config(text='Overall: 0%')
            return

        total_progress = sum(task.progress for task in self.tasks.values())
        overall = total_progress / len(self.tasks)

        self.overall_label.config(text=f'Overall: {int(overall)}%')


class TimelineProgress(tk.Frame):
    """Timeline progress with milestones."""

    def __init__(self, parent, milestones: List[Dict], **kwargs):
        super().__init__(parent, bg=kwargs.get('bg', '#2d2d2d'))
        self.milestones = milestones  # [{'date': datetime, 'label': str, 'completed': bool}]
        self.start_date = kwargs.get('start_date', datetime.now())
        self.end_date = kwargs.get('end_date', datetime.now() + timedelta(days=30))

        self._build_ui()

    def _build_ui(self):
        """Build timeline UI."""
        # Timeline canvas
        self.canvas = tk.Canvas(self, height=150, bg='#2d2d2d', highlightthickness=0)
        self.canvas.pack(fill='x', padx=20, pady=20)

        self._draw_timeline()

    def _draw_timeline(self):
        """Draw timeline with milestones."""
        self.canvas.delete('all')

        width = self.canvas.winfo_width()
        if width <= 1:
            width = 600

        height = 150

        # Timeline line
        y_line = height // 2
        self.canvas.create_line(50, y_line, width - 50, y_line, fill='#858585', width=3)

        # Start and end markers
        self.canvas.create_text(
            50, y_line + 30,
            text=self.start_date.strftime('%m/%d'),
            fill='white',
            font=('Arial', 9)
        )
        self.canvas.create_text(
            width - 50, y_line + 30,
            text=self.end_date.strftime('%m/%d'),
            fill='white',
            font=('Arial', 9)
        )

        # Milestones
        total_days = (self.end_date - self.start_date).days
        timeline_width = width - 100

        for milestone in self.milestones:
            # Calculate position
            days_from_start = (milestone['date'] - self.start_date).days
            x = 50 + (days_from_start / total_days) * timeline_width

            # Milestone marker
            color = '#00C49F' if milestone['completed'] else '#FF8042'
            self.canvas.create_oval(
                x - 8, y_line - 8, x + 8, y_line + 8,
                fill=color,
                outline='white',
                width=2
            )

            # Label
            label_y = y_line - 30 if len(self.milestones) % 2 == 0 else y_line - 40
            self.canvas.create_text(
                x, label_y,
                text=milestone['label'],
                fill='white',
                font=('Arial', 8),
                width=80
            )

            # Date
            self.canvas.create_text(
                x, y_line + 20,
                text=milestone['date'].strftime('%m/%d'),
                fill='#858585',
                font=('Arial', 8)
            )


class TaskChecklist(tk.Frame):
    """Task completion checklist with progress."""

    def __init__(self, parent, tasks: List[str], **kwargs):
        super().__init__(parent, bg=kwargs.get('bg', '#2d2d2d'))
        self.tasks = tasks
        self.task_vars: List[tk.BooleanVar] = []
        self.on_change: Optional[Callable] = kwargs.get('on_change')

        self._build_ui()

    def _build_ui(self):
        """Build checklist UI."""
        # Header with progress
        header = tk.Frame(self, bg='#1e1e1e')
        header.pack(side='top', fill='x')

        tk.Label(
            header,
            text='Task Checklist',
            bg='#1e1e1e',
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack(side='left', padx=10, pady=10)

        self.progress_label = tk.Label(
            header,
            text='0 / 0 (0%)',
            bg='#1e1e1e',
            fg='#00C49F',
            font=('Arial', 10, 'bold')
        )
        self.progress_label.pack(side='right', padx=10)

        # Progress bar
        self.progress_bar = LinearProgress(self, label='', show_percentage=False, height=10)
        self.progress_bar.pack(fill='x', padx=10, pady=5)

        # Task list
        task_frame = tk.Frame(self, bg='#2d2d2d')
        task_frame.pack(fill='both', expand=True, padx=10, pady=10)

        for i, task in enumerate(self.tasks):
            var = tk.BooleanVar(value=False)
            self.task_vars.append(var)

            cb = tk.Checkbutton(
                task_frame,
                text=task,
                variable=var,
                command=self._on_task_toggle,
                bg='#2d2d2d',
                fg='white',
                selectcolor='#0088FE',
                font=('Arial', 10),
                anchor='w'
            )
            cb.pack(fill='x', pady=2)

        self._update_progress()

    def _on_task_toggle(self):
        """Handle task toggle."""
        self._update_progress()

        if self.on_change:
            self.on_change(self.get_completed_count(), len(self.tasks))

    def _update_progress(self):
        """Update progress display."""
        completed = sum(1 for var in self.task_vars if var.get())
        total = len(self.tasks)
        percentage = (completed / total * 100) if total > 0 else 0

        self.progress_label.config(text=f'{completed} / {total} ({int(percentage)}%)')
        self.progress_bar.set_progress(percentage)

    def get_completed_count(self) -> int:
        """Get number of completed tasks."""
        return sum(1 for var in self.task_vars if var.get())

    def get_progress_percentage(self) -> float:
        """Get progress percentage."""
        return (self.get_completed_count() / len(self.tasks) * 100) if self.tasks else 0


class EstimatedTimeProgress(tk.Frame):
    """Progress with estimated time remaining."""

    def __init__(self, parent, label: str = '', total_time: int = 100, **kwargs):
        super().__init__(parent, bg=kwargs.get('bg', '#2d2d2d'))
        self.label_text = label
        self.total_time = total_time  # seconds
        self.elapsed_time = 0
        self.start_time: Optional[datetime] = None
        self.running = False

        self._build_ui()

    def _build_ui(self):
        """Build time progress UI."""
        # Label
        if self.label_text:
            tk.Label(
                self,
                text=self.label_text,
                bg='#2d2d2d',
                fg='white',
                font=('Arial', 10, 'bold')
            ).pack(side='top', anchor='w', pady=(0, 5))

        # Progress bar
        self.progress_bar = LinearProgress(self, label='', show_percentage=True, height=25)
        self.progress_bar.pack(fill='x')

        # Time info
        time_frame = tk.Frame(self, bg='#2d2d2d')
        time_frame.pack(side='top', fill='x', pady=(5, 0))

        self.elapsed_label = tk.Label(
            time_frame,
            text='Elapsed: 0s',
            bg='#2d2d2d',
            fg='#858585',
            font=('Arial', 9)
        )
        self.elapsed_label.pack(side='left')

        self.remaining_label = tk.Label(
            time_frame,
            text='Remaining: 0s',
            bg='#2d2d2d',
            fg='#858585',
            font=('Arial', 9)
        )
        self.remaining_label.pack(side='right')

    def start(self):
        """Start timer."""
        self.start_time = datetime.now()
        self.running = True
        self._update_time()

    def stop(self):
        """Stop timer."""
        self.running = False

    def reset(self):
        """Reset timer."""
        self.elapsed_time = 0
        self.start_time = None
        self.running = False
        self._update_display()

    def _update_time(self):
        """Update elapsed time."""
        if self.running and self.start_time:
            self.elapsed_time = (datetime.now() - self.start_time).total_seconds()

            self._update_display()

            # Continue updating
            self.after(1000, self._update_time)

    def _update_display(self):
        """Update display."""
        # Calculate progress
        progress = min(100, (self.elapsed_time / self.total_time) * 100)
        self.progress_bar.set_progress(progress)

        # Update labels
        self.elapsed_label.config(text=f'Elapsed: {self._format_time(self.elapsed_time)}')

        remaining = max(0, self.total_time - self.elapsed_time)
        self.remaining_label.config(text=f'Remaining: {self._format_time(remaining)}')

    def _format_time(self, seconds: float) -> str:
        """Format seconds to readable string."""
        if seconds < 60:
            return f'{int(seconds)}s'
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f'{minutes}m {secs}s'
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f'{hours}h {minutes}m'


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Progress Tracking Widgets - B5 Demo')
    root.geometry('900x800')
    root.configure(bg='#1e1e1e')

    # Create scrollable frame
    canvas = tk.Canvas(root, bg='#1e1e1e', highlightthickness=0)
    scrollbar = ttk.Scrollbar(root, orient='vertical', command=canvas.yview)
    demo_frame = tk.Frame(canvas, bg='#1e1e1e')

    demo_frame.bind(
        '<Configure>',
        lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
    )

    canvas.create_window((0, 0), window=demo_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side='left', fill='both', expand=True, padx=10, pady=10)
    scrollbar.pack(side='right', fill='y')

    # Demo widgets
    # 1. Linear Progress
    section1 = tk.LabelFrame(demo_frame, text='Linear Progress', bg='#2d2d2d', fg='white',
                            font=('Arial', 11, 'bold'), padx=15, pady=15)
    section1.pack(fill='x', pady=10, padx=10)

    progress1 = LinearProgress(section1, label='Task 1: Processing Data', color='#00C49F')
    progress1.pack(fill='x', pady=5)
    progress1.set_progress(75)

    progress2 = LinearProgress(section1, label='Task 2: Uploading Files', color='#0088FE')
    progress2.pack(fill='x', pady=5)
    progress2.set_progress(45)

    # 2. Step Progress
    section2 = tk.LabelFrame(demo_frame, text='Step Progress', bg='#2d2d2d', fg='white',
                            font=('Arial', 11, 'bold'), padx=15, pady=15)
    section2.pack(fill='x', pady=10, padx=10)

    steps = ['Initialize', 'Process', 'Validate', 'Complete']
    step_progress = StepProgress(section2, steps)
    step_progress.pack(fill='x')
    step_progress.set_step(2)

    # 3. Multi Progress
    section3 = tk.LabelFrame(demo_frame, text='Multi-Task Dashboard', bg='#2d2d2d', fg='white',
                            font=('Arial', 11, 'bold'), padx=15, pady=15)
    section3.pack(fill='both', expand=True, pady=10, padx=10)

    multi_progress = MultiProgress(section3)
    multi_progress.pack(fill='both', expand=True)
    multi_progress.add_task('task1', 'Database Migration', 60)
    multi_progress.add_task('task2', 'File Conversion', 30)
    multi_progress.add_task('task3', 'Report Generation', 85)

    # 4. Task Checklist
    section4 = tk.LabelFrame(demo_frame, text='Task Checklist', bg='#2d2d2d', fg='white',
                            font=('Arial', 11, 'bold'), padx=15, pady=15)
    section4.pack(fill='x', pady=10, padx=10)

    checklist = TaskChecklist(
        section4,
        ['Setup environment', 'Install dependencies', 'Configure settings', 'Run tests', 'Deploy']
    )
    checklist.pack(fill='x')

    # 5. Estimated Time Progress
    section5 = tk.LabelFrame(demo_frame, text='Time-Based Progress', bg='#2d2d2d', fg='white',
                            font=('Arial', 11, 'bold'), padx=15, pady=15)
    section5.pack(fill='x', pady=10, padx=10)

    time_progress = EstimatedTimeProgress(section5, label='Backup Process', total_time=120)
    time_progress.pack(fill='x')

    btn_frame = tk.Frame(section5, bg='#2d2d2d')
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text='▶️ Start', command=time_progress.start,
             bg='#00C49F', fg='white').pack(side='left', padx=5)
    tk.Button(btn_frame, text='⏸️ Stop', command=time_progress.stop,
             bg='#FF8042', fg='white').pack(side='left', padx=5)
    tk.Button(btn_frame, text='🔄 Reset', command=time_progress.reset,
             bg='#858585', fg='white').pack(side='left', padx=5)

    root.mainloop()
