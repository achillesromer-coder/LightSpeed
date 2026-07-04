"""
Task & Issue Tracker - H5
=========================

Comprehensive task and issue management system.

Features:
- Task creation and management
- Issue tracking
- Priority levels
- Status workflow
- Assignment and delegation
- Due dates and reminders
- Labels and tags
- Comments and attachments
- Time tracking
- Progress tracking
- Sprint planning
- Board views (Kanban)
- Export/import

Author: LightSpeed Platform
Date: December 19, 2025
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import json
import hashlib
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from enum import Enum


class TaskStatus(Enum):
    """Task status enum."""
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    ARCHIVED = "archived"


class TaskPriority(Enum):
    """Task priority enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskType(Enum):
    """Task type enum."""
    TASK = "task"
    BUG = "bug"
    FEATURE = "feature"
    IMPROVEMENT = "improvement"
    DOCUMENTATION = "documentation"


@dataclass
class Comment:
    """Task comment."""
    id: str
    author: str
    content: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'author': self.author,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Comment':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class Task:
    """Task/Issue definition."""
    id: str
    title: str
    description: str
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
    created_by: str = "user"
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    time_spent_minutes: int = 0
    estimated_hours: Optional[float] = None
    completed_at: Optional[datetime] = None
    sprint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type.value,
            'status': self.status.value,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'assigned_to': self.assigned_to,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'tags': self.tags,
            'comments': [c.to_dict() for c in self.comments],
            'time_spent_minutes': self.time_spent_minutes,
            'estimated_hours': self.estimated_hours,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'sprint': self.sprint
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create from dictionary."""
        data['task_type'] = TaskType(data['task_type'])
        data['status'] = TaskStatus(data['status'])
        data['priority'] = TaskPriority(data['priority'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])

        if data.get('due_date'):
            data['due_date'] = datetime.fromisoformat(data['due_date'])

        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])

        data['comments'] = [Comment.from_dict(c) for c in data.get('comments', [])]

        return cls(**data)

    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date:
            return False

        if self.status == TaskStatus.DONE:
            return False

        return datetime.now() > self.due_date

    def get_progress(self) -> float:
        """Get progress percentage."""
        status_progress = {
            TaskStatus.BACKLOG: 0.0,
            TaskStatus.TODO: 10.0,
            TaskStatus.IN_PROGRESS: 50.0,
            TaskStatus.IN_REVIEW: 80.0,
            TaskStatus.DONE: 100.0,
            TaskStatus.ARCHIVED: 100.0
        }
        return status_progress.get(self.status, 0.0)


class TaskTracker:
    """Manages tasks and issues."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)

        self.tasks: Dict[str, Task] = {}
        self.sprints: Dict[str, List[str]] = defaultdict(list)

        self._load_tasks()

    def create_task(
        self,
        title: str,
        description: str,
        task_type: TaskType,
        priority: TaskPriority,
        **kwargs
    ) -> Task:
        """Create new task."""
        task_id = hashlib.md5(
            f"{title}_{datetime.now().timestamp()}".encode()
        ).hexdigest()[:16]

        task = Task(
            id=task_id,
            title=title,
            description=description,
            task_type=task_type,
            status=TaskStatus.TODO,
            priority=priority,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            **kwargs
        )

        self.tasks[task_id] = task

        if task.sprint:
            self.sprints[task.sprint].append(task_id)

        self._save_tasks()

        return task

    def update_task(self, task_id: str, **kwargs):
        """Update task."""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]

        # Handle status change to DONE
        if 'status' in kwargs and kwargs['status'] == TaskStatus.DONE:
            if task.status != TaskStatus.DONE:
                kwargs['completed_at'] = datetime.now()

        # Update fields
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        task.updated_at = datetime.now()

        self._save_tasks()

    def delete_task(self, task_id: str):
        """Delete task."""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]

        if task.sprint:
            self.sprints[task.sprint].remove(task_id)

        del self.tasks[task_id]
        self._save_tasks()

    def add_comment(self, task_id: str, author: str, content: str):
        """Add comment to task."""
        if task_id not in self.tasks:
            return

        comment_id = hashlib.md5(
            f"{task_id}_{datetime.now().timestamp()}".encode()
        ).hexdigest()[:16]

        comment = Comment(
            id=comment_id,
            author=author,
            content=content,
            timestamp=datetime.now()
        )

        self.tasks[task_id].comments.append(comment)
        self.tasks[task_id].updated_at = datetime.now()

        self._save_tasks()

    def search_tasks(
        self,
        query: str = "",
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        task_type: Optional[TaskType] = None,
        assigned_to: Optional[str] = None,
        sprint: Optional[str] = None,
        tags: Optional[List[str]] = None,
        overdue_only: bool = False
    ) -> List[Task]:
        """Search tasks."""
        results = list(self.tasks.values())

        # Filter by query
        if query:
            query = query.lower()
            results = [
                t for t in results
                if query in t.title.lower() or query in t.description.lower()
            ]

        # Filter by status
        if status:
            results = [t for t in results if t.status == status]

        # Filter by priority
        if priority:
            results = [t for t in results if t.priority == priority]

        # Filter by type
        if task_type:
            results = [t for t in results if t.task_type == task_type]

        # Filter by assigned
        if assigned_to:
            results = [t for t in results if t.assigned_to == assigned_to]

        # Filter by sprint
        if sprint:
            results = [t for t in results if t.sprint == sprint]

        # Filter by tags
        if tags:
            results = [t for t in results if any(tag in t.tags for tag in tags)]

        # Filter overdue
        if overdue_only:
            results = [t for t in results if t.is_overdue()]

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get task statistics."""
        total = len(self.tasks)

        by_status = defaultdict(int)
        by_priority = defaultdict(int)
        by_type = defaultdict(int)

        overdue = 0
        completed_this_week = 0

        week_ago = datetime.now() - timedelta(days=7)

        for task in self.tasks.values():
            by_status[task.status.value] += 1
            by_priority[task.priority.value] += 1
            by_type[task.task_type.value] += 1

            if task.is_overdue():
                overdue += 1

            if task.completed_at and task.completed_at >= week_ago:
                completed_this_week += 1

        return {
            'total': total,
            'by_status': dict(by_status),
            'by_priority': dict(by_priority),
            'by_type': dict(by_type),
            'overdue': overdue,
            'completed_this_week': completed_this_week
        }

    def _load_tasks(self):
        """Load tasks from disk."""
        tasks_file = self.workspace / 'tasks.json'

        if not tasks_file.exists():
            return

        data = json.loads(tasks_file.read_text(encoding='utf-8'))

        self.tasks = {
            tid: Task.from_dict(task_data)
            for tid, task_data in data.get('tasks', {}).items()
        }

        # Rebuild sprint index
        self.sprints.clear()
        for task in self.tasks.values():
            if task.sprint:
                self.sprints[task.sprint].append(task.id)

    def _save_tasks(self):
        """Save tasks to disk."""
        data = {
            'tasks': {tid: task.to_dict() for tid, task in self.tasks.items()},
            'saved_at': datetime.now().isoformat()
        }

        tasks_file = self.workspace / 'tasks.json'
        tasks_file.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def export_tasks(self, filepath: Path, task_ids: Optional[List[str]] = None):
        """Export tasks."""
        if task_ids:
            tasks = {tid: self.tasks[tid].to_dict() for tid in task_ids if tid in self.tasks}
        else:
            tasks = {tid: t.to_dict() for tid, t in self.tasks.items()}

        data = {
            'tasks': tasks,
            'exported_at': datetime.now().isoformat()
        }

        filepath.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def import_tasks(self, filepath: Path):
        """Import tasks."""
        if not filepath.exists():
            return

        data = json.loads(filepath.read_text(encoding='utf-8'))

        for task_data in data.get('tasks', {}).values():
            task = Task.from_dict(task_data)
            self.tasks[task.id] = task

            if task.sprint:
                self.sprints[task.sprint].append(task.id)

        self._save_tasks()


class TaskTrackerGUI(tk.Frame):
    """Task & Issue Tracker GUI."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#1e1e1e')

        workspace = Path.home() / '.lightspeed' / 'tasks'
        self.tracker = TaskTracker(workspace)

        self.selected_task: Optional[str] = None

        self._build_ui()
        self._load_tasks()

    def _build_ui(self):
        """Build task tracker UI."""
        # Toolbar
        toolbar = tk.Frame(self, bg='#1e1e1e', height=50)
        toolbar.pack(side='top', fill='x')

        tk.Button(toolbar, text='➕ New Task', command=self._create_task,
                 bg='#00C49F', fg='white').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='✏️ Edit', command=self._edit_task,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='🗑️ Delete', command=self._delete_task,
                 bg='#FF8042', fg='white').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Label(toolbar, text='Filter:', bg='#1e1e1e', fg='white').pack(side='left', padx=5)

        self.status_filter = ttk.Combobox(toolbar,
                                         values=['All'] + [s.value for s in TaskStatus],
                                         width=12, state='readonly')
        self.status_filter.set('All')
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self._load_tasks())
        self.status_filter.pack(side='left', padx=5)

        self.priority_filter = ttk.Combobox(toolbar,
                                           values=['All'] + [p.value for p in TaskPriority],
                                           width=10, state='readonly')
        self.priority_filter.set('All')
        self.priority_filter.bind('<<ComboboxSelected>>', lambda e: self._load_tasks())
        self.priority_filter.pack(side='left', padx=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Button(toolbar, text='📊 Statistics', command=self._show_statistics,
                 bg='#FFBB28', fg='black').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='📤 Export', command=self._export_tasks,
                 bg='#858585', fg='white').pack(side='right', padx=5, pady=5)

        tk.Button(toolbar, text='📥 Import', command=self._import_tasks,
                 bg='#858585', fg='white').pack(side='right', padx=5, pady=5)

        # Main content - Notebook
        notebook = ttk.Notebook(self)
        notebook.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        # Tab 1: Task List
        list_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(list_frame, text='Task List')

        # Tasks tree
        columns = ('Type', 'Status', 'Priority', 'Assigned', 'Due Date')
        self.tasks_tree = ttk.Treeview(list_frame, columns=columns,
                                      show='tree headings', height=20)

        self.tasks_tree.heading('#0', text='Title')
        self.tasks_tree.column('#0', width=300)

        for col in columns:
            self.tasks_tree.heading(col, text=col)
            self.tasks_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical',
                                 command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)

        self.tasks_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')

        # Bind selection
        self.tasks_tree.bind('<<TreeviewSelect>>', self._on_task_select)

        # Tab 2: Task Details
        details_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(details_frame, text='Details')

        # Task info
        info_frame = tk.Frame(details_frame, bg='#2d2d2d')
        info_frame.pack(side='top', fill='x', padx=10, pady=10)

        self.task_title_label = tk.Label(info_frame, text='No task selected',
                                         bg='#2d2d2d', fg='white',
                                         font=('Arial', 14, 'bold'), anchor='w')
        self.task_title_label.pack(fill='x')

        self.task_info_text = scrolledtext.ScrolledText(info_frame, bg='#1e1e1e',
                                                        fg='white', wrap='word',
                                                        font=('Courier', 9), height=15)
        self.task_info_text.pack(fill='both', expand=True, pady=5)

        # Comments section
        comments_label_frame = tk.Frame(details_frame, bg='#2d2d2d')
        comments_label_frame.pack(side='top', fill='x', padx=10, pady=5)

        tk.Label(comments_label_frame, text='Comments', bg='#2d2d2d', fg='white',
                font=('Arial', 10, 'bold')).pack(side='left')

        tk.Button(comments_label_frame, text='➕ Add Comment',
                 command=self._add_comment, bg='#0088FE', fg='white').pack(side='right')

        self.comments_text = scrolledtext.ScrolledText(details_frame, bg='#1e1e1e',
                                                       fg='white', wrap='word',
                                                       font=('Courier', 9), height=10)
        self.comments_text.pack(fill='both', expand=True, padx=10, pady=5)

        # Tab 3: Kanban Board
        kanban_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(kanban_frame, text='Kanban Board')

        # Create columns for each status
        board_container = tk.Frame(kanban_frame, bg='#2d2d2d')
        board_container.pack(fill='both', expand=True, padx=5, pady=5)

        self.kanban_columns = {}
        statuses = [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW, TaskStatus.DONE]

        for i, status in enumerate(statuses):
            col_frame = tk.LabelFrame(board_container, text=status.value.replace('_', ' ').title(),
                                     bg='#2d2d2d', fg='white', font=('Arial', 10, 'bold'))
            col_frame.grid(row=0, column=i, sticky='nsew', padx=5, pady=5)

            listbox = tk.Listbox(col_frame, bg='#1e1e1e', fg='white',
                                font=('Arial', 9), height=25)
            listbox.pack(fill='both', expand=True, padx=5, pady=5)

            self.kanban_columns[status] = listbox

            board_container.grid_columnconfigure(i, weight=1)

        board_container.grid_rowconfigure(0, weight=1)

        # Status bar
        status_frame = tk.Frame(self, bg='#2d2d2d', height=30)
        status_frame.pack(side='bottom', fill='x')

        self.status_label = tk.Label(status_frame, text='Ready', bg='#2d2d2d',
                                     fg='#858585', font=('Arial', 9), anchor='w')
        self.status_label.pack(side='left', padx=10, fill='x', expand=True)

        self.task_count_label = tk.Label(status_frame, text='Tasks: 0', bg='#2d2d2d',
                                         fg='#858585', font=('Arial', 9))
        self.task_count_label.pack(side='right', padx=10)

    def _load_tasks(self):
        """Load and display tasks."""
        # Clear tree
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)

        # Clear kanban board
        for listbox in self.kanban_columns.values():
            listbox.delete(0, 'end')

        # Get filters
        status_filter = self.status_filter.get()
        priority_filter = self.priority_filter.get()

        # Search
        tasks = self.tracker.search_tasks(
            status=TaskStatus(status_filter) if status_filter != 'All' else None,
            priority=TaskPriority(priority_filter) if priority_filter != 'All' else None
        )

        # Sort by priority (critical first) then due date
        priority_order = {TaskPriority.CRITICAL: 0, TaskPriority.HIGH: 1,
                         TaskPriority.MEDIUM: 2, TaskPriority.LOW: 3}
        tasks.sort(key=lambda t: (priority_order[t.priority], t.due_date or datetime.max))

        # Add to tree
        for task in tasks:
            due_str = task.due_date.strftime('%Y-%m-%d') if task.due_date else 'None'

            # Color code overdue tasks
            tags = []
            if task.is_overdue():
                tags.append('overdue')

            self.tasks_tree.insert(
                '',
                'end',
                iid=task.id,
                text=task.title,
                values=(
                    task.task_type.value,
                    task.status.value,
                    task.priority.value,
                    task.assigned_to or 'Unassigned',
                    due_str
                ),
                tags=tags
            )

            # Add to kanban board
            if task.status in self.kanban_columns:
                display = f"[{task.priority.value[0].upper()}] {task.title}"
                self.kanban_columns[task.status].insert('end', display)

        # Configure tags
        self.tasks_tree.tag_configure('overdue', background='#4a2d2d')

        self.task_count_label.config(text=f'Tasks: {len(tasks)}')

    def _on_task_select(self, event):
        """Handle task selection."""
        selection = self.tasks_tree.selection()
        if not selection:
            return

        task_id = selection[0]
        self.selected_task = task_id

        task = self.tracker.tasks.get(task_id)
        if task:
            self.task_title_label.config(text=task.title)

            # Display task info
            self.task_info_text.delete('1.0', 'end')

            info = f"ID: {task.id}\n"
            info += f"Type: {task.task_type.value}\n"
            info += f"Status: {task.status.value}\n"
            info += f"Priority: {task.priority.value}\n\n"

            info += f"Description:\n{task.description}\n\n"

            info += f"Created: {task.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            info += f"Updated: {task.updated_at.strftime('%Y-%m-%d %H:%M')}\n"

            if task.due_date:
                info += f"Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n"

                if task.is_overdue():
                    info += "⚠️ OVERDUE\n"

            if task.assigned_to:
                info += f"Assigned To: {task.assigned_to}\n"

            if task.sprint:
                info += f"Sprint: {task.sprint}\n"

            if task.tags:
                info += f"Tags: {', '.join(task.tags)}\n"

            info += f"\nTime Spent: {task.time_spent_minutes} minutes\n"

            if task.estimated_hours:
                info += f"Estimated: {task.estimated_hours} hours\n"

            info += f"Progress: {task.get_progress():.0f}%\n"

            self.task_info_text.insert('1.0', info)

            # Display comments
            self.comments_text.delete('1.0', 'end')

            if task.comments:
                for comment in task.comments:
                    self.comments_text.insert('end',
                        f"{comment.author} ({comment.timestamp.strftime('%Y-%m-%d %H:%M')}):\n"
                    )
                    self.comments_text.insert('end', f"{comment.content}\n\n")
                    self.comments_text.insert('end', "-" * 80 + "\n\n")
            else:
                self.comments_text.insert('1.0', 'No comments')

    def _create_task(self):
        """Create new task."""
        dialog = tk.Toplevel(self)
        dialog.title('New Task')
        dialog.geometry('600x600')
        dialog.configure(bg='#2d2d2d')

        row = 0

        tk.Label(dialog, text='Title:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        title_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', width=50)
        title_entry.grid(row=row, column=1, padx=10, pady=5)
        row += 1

        tk.Label(dialog, text='Type:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        type_combo = ttk.Combobox(dialog, values=[t.value for t in TaskType], state='readonly')
        type_combo.set(TaskType.TASK.value)
        type_combo.grid(row=row, column=1, padx=10, pady=5, sticky='w')
        row += 1

        tk.Label(dialog, text='Priority:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        priority_combo = ttk.Combobox(dialog, values=[p.value for p in TaskPriority], state='readonly')
        priority_combo.set(TaskPriority.MEDIUM.value)
        priority_combo.grid(row=row, column=1, padx=10, pady=5, sticky='w')
        row += 1

        tk.Label(dialog, text='Description:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='nw')
        desc_text = scrolledtext.ScrolledText(dialog, bg='#1e1e1e', fg='white', height=15)
        desc_text.grid(row=row, column=1, padx=10, pady=5, sticky='nsew')
        row += 1

        dialog.grid_columnconfigure(1, weight=1)
        dialog.grid_rowconfigure(3, weight=1)

        def create():
            self.tracker.create_task(
                title=title_entry.get().strip(),
                description=desc_text.get('1.0', 'end-1c'),
                task_type=TaskType(type_combo.get()),
                priority=TaskPriority(priority_combo.get())
            )
            self._load_tasks()
            dialog.destroy()

        tk.Button(dialog, text='Create', command=create,
                 bg='#00C49F', fg='white').grid(row=row, column=1, padx=10, pady=10, sticky='e')

    def _edit_task(self):
        """Edit selected task."""
        if not self.selected_task:
            messagebox.showwarning('No Selection', 'Please select a task to edit')
            return

        task = self.tracker.tasks[self.selected_task]

        dialog = tk.Toplevel(self)
        dialog.title(f'Edit: {task.title}')
        dialog.geometry('600x500')
        dialog.configure(bg='#2d2d2d')

        row = 0

        tk.Label(dialog, text='Status:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        status_combo = ttk.Combobox(dialog, values=[s.value for s in TaskStatus], state='readonly')
        status_combo.set(task.status.value)
        status_combo.grid(row=row, column=1, padx=10, pady=5, sticky='w')
        row += 1

        tk.Label(dialog, text='Priority:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        priority_combo = ttk.Combobox(dialog, values=[p.value for p in TaskPriority], state='readonly')
        priority_combo.set(task.priority.value)
        priority_combo.grid(row=row, column=1, padx=10, pady=5, sticky='w')
        row += 1

        tk.Label(dialog, text='Assigned To:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        assigned_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', width=30)
        if task.assigned_to:
            assigned_entry.insert(0, task.assigned_to)
        assigned_entry.grid(row=row, column=1, padx=10, pady=5, sticky='w')
        row += 1

        def save():
            self.tracker.update_task(
                self.selected_task,
                status=TaskStatus(status_combo.get()),
                priority=TaskPriority(priority_combo.get()),
                assigned_to=assigned_entry.get().strip() or None
            )
            self._load_tasks()
            self._on_task_select(None)
            dialog.destroy()

        tk.Button(dialog, text='Save', command=save,
                 bg='#00C49F', fg='white').grid(row=row, column=1, padx=10, pady=20, sticky='e')

    def _delete_task(self):
        """Delete selected task."""
        if not self.selected_task:
            messagebox.showwarning('No Selection', 'Please select a task to delete')
            return

        task = self.tracker.tasks[self.selected_task]

        if messagebox.askyesno('Confirm Delete', f'Delete task "{task.title}"?'):
            self.tracker.delete_task(self.selected_task)
            self.selected_task = None
            self._load_tasks()

    def _add_comment(self):
        """Add comment to task."""
        if not self.selected_task:
            messagebox.showwarning('No Selection', 'Please select a task first')
            return

        comment = tk.simpledialog.askstring('Add Comment', 'Enter comment:')

        if comment:
            self.tracker.add_comment(self.selected_task, 'user', comment)
            self._on_task_select(None)

    def _show_statistics(self):
        """Show task statistics."""
        stats = self.tracker.get_statistics()

        msg = "Task Statistics:\n\n"
        msg += f"Total Tasks: {stats['total']}\n\n"

        msg += "By Status:\n"
        for status, count in stats['by_status'].items():
            msg += f"  {status}: {count}\n"

        msg += "\nBy Priority:\n"
        for priority, count in stats['by_priority'].items():
            msg += f"  {priority}: {count}\n"

        msg += f"\nOverdue: {stats['overdue']}\n"
        msg += f"Completed This Week: {stats['completed_this_week']}"

        messagebox.showinfo('Statistics', msg)

    def _export_tasks(self):
        """Export tasks."""
        filepath = filedialog.asksaveasfilename(
            title='Export Tasks',
            defaultextension='.json',
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')]
        )

        if filepath:
            self.tracker.export_tasks(Path(filepath))
            messagebox.showinfo('Exported', f'Tasks exported to:\n{filepath}')

    def _import_tasks(self):
        """Import tasks."""
        filepath = filedialog.askopenfilename(
            title='Import Tasks',
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')]
        )

        if filepath:
            self.tracker.import_tasks(Path(filepath))
            self._load_tasks()
            messagebox.showinfo('Imported', 'Tasks imported successfully')


# Demo/Test
if __name__ == '__main__':
    import tkinter.simpledialog

    root = tk.Tk()
    root.title('Task & Issue Tracker - H5 Demo')
    root.geometry('1600x900')

    tracker_gui = TaskTrackerGUI(root)
    tracker_gui.pack(fill='both', expand=True)

    root.mainloop()
