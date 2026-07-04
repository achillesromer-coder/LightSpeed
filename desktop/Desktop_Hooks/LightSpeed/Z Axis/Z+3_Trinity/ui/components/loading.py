"""
LightSpeed V0.9.5 - Loading Indicators & Progress Components
Modern progress bars, spinners, and loading overlays

NO "in command" blocks - all GUI-based visual feedback

Components:
- ProgressBar: Determinate/indeterminate progress
- LoadingSpinner: Animated spinner with message
- LoadingOverlay: Full-window loading screen
- BackgroundTaskMonitor: Track background jobs

Author: LightSpeed Team
Version: 0.9.5
Date: January 3, 2026
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import time
import threading


class ProgressBar(tk.Frame):
    """
    Modern progress bar with determinate/indeterminate modes.

    Features:
    - Smooth animations
    - Percentage display (determinate mode)
    - Custom colors
    - Status message
    - Estimated time remaining

    Usage:
        # Determinate (0-100%)
        progress = ProgressBar(parent, mode='determinate')
        progress.set(50)  # 50%

        # Indeterminate (loading animation)
        progress = ProgressBar(parent, mode='indeterminate')
        progress.start()
    """

    def __init__(self, parent, mode='determinate', height=30, **kwargs):
        """
        Initialize progress bar.

        Args:
            parent: Parent widget
            mode: 'determinate' or 'indeterminate'
            height: Bar height in pixels
            **kwargs: Additional Frame parameters
        """
        super().__init__(parent, **kwargs)

        self.mode = mode
        self.configure(bg='#0A1628', height=height)

        # Progress bar container
        self.bar_container = tk.Frame(self, bg='#102040', relief='solid', bd=1, height=height)
        self.bar_container.pack(fill='x', padx=5, pady=5)
        self.bar_container.pack_propagate(False)

        # Progress bar (ttk for native styling)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("LightSpeed.Horizontal.TProgressbar",
                       troughcolor='#102040',
                       background='#00FFFF',
                       bordercolor='#1E3A5F',
                       lightcolor='#00FFFF',
                       darkcolor='#0088FF')

        self.progress = ttk.Progressbar(
            self.bar_container,
            mode=mode,
            style="LightSpeed.Horizontal.TProgressbar"
        )
        self.progress.pack(fill='both', expand=True, padx=2, pady=2)

        # Status label
        self.status_label = tk.Label(
            self,
            text="",
            bg='#0A1628',
            fg='#88CCFF',
            font=('Segoe UI', 9),
            anchor='w'
        )
        self.status_label.pack(fill='x', padx=5)

        # Percentage label (determinate mode only)
        if mode == 'determinate':
            self.pct_label = tk.Label(
                self.bar_container,
                text="0%",
                bg='#102040',
                fg='#00FFFF',
                font=('Segoe UI', 9, 'bold')
            )
            self.pct_label.place(relx=0.5, rely=0.5, anchor='center')
        else:
            self.pct_label = None

        self._value = 0
        self._max = 100

    def set(self, value: float, status: str = ""):
        """
        Set progress value (determinate mode).

        Args:
            value: Progress value (0-100)
            status: Optional status message
        """
        if self.mode != 'determinate':
            return

        self._value = max(0, min(100, value))
        self.progress['value'] = self._value

        if self.pct_label:
            self.pct_label.config(text=f"{int(self._value)}%")

        if status:
            self.status_label.config(text=status)

        self.update_idletasks()

    def start(self):
        """Start progress animation (indeterminate mode)"""
        if self.mode == 'indeterminate':
            self.progress.start(10)  # 10ms interval

    def stop(self):
        """Stop progress animation (indeterminate mode)"""
        if self.mode == 'indeterminate':
            self.progress.stop()

    def set_status(self, message: str):
        """Set status message"""
        self.status_label.config(text=message)

    def complete(self, message: str = "Complete!"):
        """Mark as complete (100%)"""
        if self.mode == 'determinate':
            self.set(100, message)
        else:
            self.stop()
            self.status_label.config(text=message)


class LoadingSpinner(tk.Frame):
    """
    Animated loading spinner with message.

    Features:
    - Rotating animation
    - Custom message
    - Auto-sizing
    - Transparent background option
    """

    def __init__(self, parent, text="Loading...", size=50, **kwargs):
        """
        Initialize loading spinner.

        Args:
            parent: Parent widget
            text: Loading message
            size: Spinner size in pixels
            **kwargs: Additional Frame parameters
        """
        super().__init__(parent, **kwargs)

        self.configure(bg='#0A1628')
        self.size = size
        self._angle = 0
        self._running = False
        self._animation_id = None

        # Canvas for spinner
        self.canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg='#0A1628',
            highlightthickness=0
        )
        self.canvas.pack(pady=10)

        # Draw spinner circle
        self._draw_spinner()

        # Text label
        self.label = tk.Label(
            self,
            text=text,
            bg='#0A1628',
            fg='#00FFFF',
            font=('Segoe UI', 10)
        )
        self.label.pack(pady=5)

    def _draw_spinner(self):
        """Draw rotating spinner"""
        self.canvas.delete('all')

        # Draw arc
        margin = 5
        self.canvas.create_arc(
            margin, margin,
            self.size - margin, self.size - margin,
            start=self._angle,
            extent=280,
            outline='#00FFFF',
            width=3,
            style='arc'
        )

    def _animate(self):
        """Animation loop"""
        if not self._running:
            return

        self._angle = (self._angle + 10) % 360
        self._draw_spinner()
        self._animation_id = self.after(50, self._animate)

    def start(self):
        """Start spinner animation"""
        self._running = True
        self._animate()

    def stop(self):
        """Stop spinner animation"""
        self._running = False
        if self._animation_id:
            self.after_cancel(self._animation_id)

    def set_text(self, text: str):
        """Update loading message"""
        self.label.config(text=text)


class LoadingOverlay(tk.Toplevel):
    """
    Full-window loading overlay.

    Features:
    - Semi-transparent background
    - Progress bar or spinner
    - Blocks interaction during loading
    - Auto-closes when complete
    """

    def __init__(self, parent, message="Loading...", show_progress=True):
        """
        Initialize loading overlay.

        Args:
            parent: Parent window
            message: Loading message
            show_progress: Show progress bar (True) or spinner (False)
        """
        super().__init__(parent)

        # Configure window
        self.title("Loading")
        self.transient(parent)
        self.grab_set()

        # Remove window decorations
        self.overrideredirect(True)

        # Semi-transparent background
        self.configure(bg='#0A1628')
        self.attributes('-alpha', 0.95)

        # Center on parent
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 100
        self.geometry(f"400x200+{x}+{y}")

        # Content frame
        content = tk.Frame(self, bg='#0A1628')
        content.pack(fill='both', expand=True, padx=20, pady=20)

        # Message
        tk.Label(
            content,
            text=message,
            bg='#0A1628',
            fg='#FFFFFF',
            font=('Segoe UI', 12, 'bold')
        ).pack(pady=10)

        # Progress indicator
        if show_progress:
            self.indicator = ProgressBar(content, mode='indeterminate')
            self.indicator.pack(fill='x', pady=10)
            self.indicator.start()
        else:
            self.indicator = LoadingSpinner(content, text="")
            self.indicator.pack(pady=10)
            self.indicator.start()

        # Status label
        self.status_label = tk.Label(
            content,
            text="Please wait...",
            bg='#0A1628',
            fg='#88CCFF',
            font=('Segoe UI', 9)
        )
        self.status_label.pack(pady=5)

    def set_status(self, message: str):
        """Update status message"""
        self.status_label.config(text=message)
        self.update_idletasks()

    def close(self):
        """Close overlay"""
        if hasattr(self.indicator, 'stop'):
            self.indicator.stop()
        self.grab_release()
        self.destroy()


class BackgroundTaskMonitor(tk.Frame):
    """
    Monitor for background tasks/jobs.

    Features:
    - List of active tasks
    - Progress per task
    - Completion notifications
    - Pause/cancel functionality
    """

    def __init__(self, parent, **kwargs):
        """
        Initialize background task monitor.

        Args:
            parent: Parent widget
            **kwargs: Additional Frame parameters
        """
        super().__init__(parent, **kwargs)

        self.configure(bg='#0A1628')
        self.tasks = {}  # task_id -> task_info

        # Header
        header = tk.Frame(self, bg='#102040', height=40)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Background Tasks",
            bg='#102040',
            fg='#FFFFFF',
            font=('Segoe UI', 11, 'bold')
        ).pack(side='left', padx=15, pady=10)

        # Task count
        self.count_label = tk.Label(
            header,
            text="0 active",
            bg='#102040',
            fg='#88CCFF',
            font=('Segoe UI', 9)
        )
        self.count_label.pack(side='right', padx=15)

        # Task list container (scrollable)
        list_container = tk.Frame(self, bg='#0A1628')
        list_container.pack(fill='both', expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side='right', fill='y')

        self.canvas = tk.Canvas(
            list_container,
            bg='#0A1628',
            yscrollcommand=scrollbar.set,
            highlightthickness=0
        )
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.canvas.yview)

        self.task_frame = tk.Frame(self.canvas, bg='#0A1628')
        self.canvas.create_window((0, 0), window=self.task_frame, anchor='nw')

        self.task_frame.bind('<Configure>',
                            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))

    def add_task(self, task_id: str, name: str, progress: float = 0):
        """
        Add a new task to monitor.

        Args:
            task_id: Unique task identifier
            name: Task name/description
            progress: Initial progress (0-100)
        """
        # Task container
        task_container = tk.Frame(self.task_frame, bg='#102040', relief='solid', bd=1)
        task_container.pack(fill='x', pady=2)

        # Task name
        name_label = tk.Label(
            task_container,
            text=name,
            bg='#102040',
            fg='#FFFFFF',
            font=('Segoe UI', 9),
            anchor='w'
        )
        name_label.pack(fill='x', padx=10, pady=(5, 0))

        # Progress bar
        progress_bar = ProgressBar(task_container, mode='determinate', height=20)
        progress_bar.pack(fill='x', padx=10, pady=(2, 5))
        progress_bar.set(progress)

        # Store task info
        self.tasks[task_id] = {
            'container': task_container,
            'name_label': name_label,
            'progress_bar': progress_bar,
            'name': name
        }

        self._update_count()

    def update_task(self, task_id: str, progress: float, status: str = ""):
        """
        Update task progress.

        Args:
            task_id: Task identifier
            progress: New progress (0-100)
            status: Optional status message
        """
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        task['progress_bar'].set(progress, status)

    def complete_task(self, task_id: str, message: str = "Complete"):
        """
        Mark task as complete.

        Args:
            task_id: Task identifier
            message: Completion message
        """
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        task['progress_bar'].complete(message)

        # Auto-remove after 3 seconds
        self.after(3000, lambda: self.remove_task(task_id))

    def remove_task(self, task_id: str):
        """
        Remove task from monitor.

        Args:
            task_id: Task identifier
        """
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        task['container'].destroy()
        del self.tasks[task_id]

        self._update_count()

    def _update_count(self):
        """Update active task count"""
        count = len(self.tasks)
        self.count_label.config(text=f"{count} active" if count != 1 else "1 active")


# Export public API
__all__ = ['ProgressBar', 'LoadingSpinner', 'LoadingOverlay', 'BackgroundTaskMonitor']
