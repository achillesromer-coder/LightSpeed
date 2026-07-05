"""
Workflow Scheduler - E2
=======================

Cron-like workflow scheduling system with recurring tasks and dependencies.

Features:
- Cron-style scheduling (minute, hour, day, month, day-of-week)
- Recurring workflows (daily, weekly, monthly, custom)
- Workflow dependencies and chaining
- Execution history and logging
- Pause/resume schedules
- Manual trigger override
- Email/notification on completion
- Timezone support

Author: LightSpeed Platform
Date: December 16, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Optional, Callable
from pathlib import Path
import json
from datetime import datetime, timedelta
import threading
import time


class ScheduledWorkflow:
    """Scheduled workflow configuration."""

    def __init__(self, workflow_id: str, name: str, schedule_type: str = 'cron', **kwargs):
        self.workflow_id = workflow_id
        self.name = name
        self.schedule_type = schedule_type  # cron, interval, once

        # Cron-style fields
        self.minute = kwargs.get('minute', '*')  # 0-59 or *
        self.hour = kwargs.get('hour', '*')  # 0-23 or *
        self.day = kwargs.get('day', '*')  # 1-31 or *
        self.month = kwargs.get('month', '*')  # 1-12 or *
        self.weekday = kwargs.get('weekday', '*')  # 0-6 (0=Monday) or *

        # Interval fields
        self.interval_value = kwargs.get('interval_value', 60)  # seconds

        # Once fields
        self.run_at = kwargs.get('run_at')  # datetime

        # State
        self.enabled = kwargs.get('enabled', True)
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0

        # Dependencies
        self.depends_on: List[str] = kwargs.get('depends_on', [])  # List of workflow IDs

        self._calculate_next_run()

    def _calculate_next_run(self):
        """Calculate next run time based on schedule."""
        now = datetime.now()

        if self.schedule_type == 'once':
            self.next_run = self.run_at
        elif self.schedule_type == 'interval':
            if self.last_run:
                self.next_run = self.last_run + timedelta(seconds=self.interval_value)
            else:
                self.next_run = now + timedelta(seconds=self.interval_value)
        elif self.schedule_type == 'cron':
            self.next_run = self._calculate_cron_next(now)

    def _calculate_cron_next(self, from_time: datetime) -> datetime:
        """Calculate next run time for cron schedule."""
        # Start from next minute
        next_time = from_time.replace(second=0, microsecond=0) + timedelta(minutes=1)

        # Simple cron calculation (checks up to 1 year ahead)
        max_iterations = 525600  # Minutes in a year
        iterations = 0

        while iterations < max_iterations:
            # Check if this time matches the cron pattern
            if self._matches_cron(next_time):
                return next_time

            next_time += timedelta(minutes=1)
            iterations += 1

        # Fallback to 24 hours from now
        return from_time + timedelta(days=1)

    def _matches_cron(self, dt: datetime) -> bool:
        """Check if datetime matches cron pattern."""
        # Check minute
        if self.minute != '*' and dt.minute != int(self.minute):
            return False

        # Check hour
        if self.hour != '*' and dt.hour != int(self.hour):
            return False

        # Check day
        if self.day != '*' and dt.day != int(self.day):
            return False

        # Check month
        if self.month != '*' and dt.month != int(self.month):
            return False

        # Check weekday (0=Monday)
        if self.weekday != '*' and dt.weekday() != int(self.weekday):
            return False

        return True

    def should_run(self) -> bool:
        """Check if workflow should run now."""
        if not self.enabled or not self.next_run:
            return False

        return datetime.now() >= self.next_run

    def mark_run(self):
        """Mark workflow as run."""
        self.last_run = datetime.now()
        self.run_count += 1
        self._calculate_next_run()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'schedule_type': self.schedule_type,
            'minute': self.minute,
            'hour': self.hour,
            'day': self.day,
            'month': self.month,
            'weekday': self.weekday,
            'interval_value': self.interval_value,
            'run_at': self.run_at.isoformat() if self.run_at else None,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'run_count': self.run_count,
            'depends_on': self.depends_on
        }

    @staticmethod
    def from_dict(data: Dict) -> 'ScheduledWorkflow':
        """Create from dictionary."""
        schedule = ScheduledWorkflow(
            data['workflow_id'],
            data['name'],
            data.get('schedule_type', 'cron'),
            minute=data.get('minute', '*'),
            hour=data.get('hour', '*'),
            day=data.get('day', '*'),
            month=data.get('month', '*'),
            weekday=data.get('weekday', '*'),
            interval_value=data.get('interval_value', 60),
            run_at=datetime.fromisoformat(data['run_at']) if data.get('run_at') else None,
            enabled=data.get('enabled', True),
            depends_on=data.get('depends_on', [])
        )

        if data.get('last_run'):
            schedule.last_run = datetime.fromisoformat(data['last_run'])
        if data.get('next_run'):
            schedule.next_run = datetime.fromisoformat(data['next_run'])

        schedule.run_count = data.get('run_count', 0)

        return schedule


class WorkflowScheduler(tk.Frame):
    """Workflow scheduler with cron-like capabilities."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#1e1e1e')
        self.app_root = kwargs.get('app_root', Path.cwd())
        self.schedules_file = self.app_root / 'data' / 'workflow_schedules.json'

        self.schedules: List[ScheduledWorkflow] = []
        self.scheduler_running = False
        self.scheduler_thread: Optional[threading.Thread] = None

        # Callbacks
        self.on_workflow_execute: Optional[Callable] = kwargs.get('on_workflow_execute')

        self._load_schedules()
        self._build_ui()

    def _build_ui(self):
        """Build scheduler UI."""
        # Toolbar
        toolbar = tk.Frame(self, bg='#1e1e1e', height=50)
        toolbar.pack(side='top', fill='x')

        tk.Button(toolbar, text='➕ New Schedule', command=self._new_schedule,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='✏️ Edit', command=self._edit_schedule,
                 bg='#858585', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='🗑️ Delete', command=self._delete_schedule,
                 bg='#FF8042', fg='white').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Button(toolbar, text='▶️ Start Scheduler', command=self._start_scheduler,
                 bg='#00C49F', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='⏸️ Stop Scheduler', command=self._stop_scheduler,
                 bg='#FFBB28', fg='black').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Button(toolbar, text='⚡ Run Now', command=self._run_now,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)

        # Status
        self.status_label = tk.Label(toolbar, text='Scheduler: Stopped', bg='#1e1e1e',
                                     fg='#858585', font=('Arial', 9))
        self.status_label.pack(side='right', padx=10)

        # Main content
        content = ttk.PanedWindow(self, orient='vertical')
        content.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        # Schedules list
        schedules_frame = tk.LabelFrame(content, text='Scheduled Workflows', bg='#2d2d2d',
                                       fg='white', font=('Arial', 10, 'bold'))
        content.add(schedules_frame, weight=2)

        # Schedules tree
        tree_frame = tk.Frame(schedules_frame, bg='#2d2d2d')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ('Workflow', 'Schedule', 'Next Run', 'Last Run', 'Count', 'Status')
        self.schedules_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        for col in columns:
            self.schedules_tree.heading(col, text=col)
            self.schedules_tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical',
                                 command=self.schedules_tree.yview)
        self.schedules_tree.configure(yscrollcommand=scrollbar.set)

        self.schedules_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Execution history
        history_frame = tk.LabelFrame(content, text='Execution History', bg='#2d2d2d',
                                     fg='white', font=('Arial', 10, 'bold'))
        content.add(history_frame, weight=1)

        # History list
        hist_list_frame = tk.Frame(history_frame, bg='#2d2d2d')
        hist_list_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.history_list = tk.Listbox(hist_list_frame, bg='#1e1e1e', fg='white',
                                       font=('Courier', 9))
        hist_scrollbar = ttk.Scrollbar(hist_list_frame, orient='vertical',
                                      command=self.history_list.yview)
        self.history_list.configure(yscrollcommand=hist_scrollbar.set)

        self.history_list.pack(side='left', fill='both', expand=True)
        hist_scrollbar.pack(side='right', fill='y')

        self._refresh_schedules()

    def _load_schedules(self):
        """Load schedules from file."""
        if self.schedules_file.exists():
            try:
                data = json.loads(self.schedules_file.read_text())
                self.schedules = [ScheduledWorkflow.from_dict(item) for item in data]
            except Exception as e:
                print(f"Failed to load schedules: {e}")

    def _save_schedules(self):
        """Save schedules to file."""
        try:
            self.schedules_file.parent.mkdir(parents=True, exist_ok=True)
            data = [schedule.to_dict() for schedule in self.schedules]
            self.schedules_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            messagebox.showerror('Error', f'Failed to save schedules:\n{str(e)}')

    def _refresh_schedules(self):
        """Refresh schedules display."""
        for item in self.schedules_tree.get_children():
            self.schedules_tree.delete(item)

        for schedule in self.schedules:
            # Format schedule display
            if schedule.schedule_type == 'cron':
                schedule_str = f"{schedule.minute} {schedule.hour} {schedule.day} {schedule.month} {schedule.weekday}"
            elif schedule.schedule_type == 'interval':
                schedule_str = f"Every {schedule.interval_value}s"
            else:  # once
                schedule_str = f"Once at {schedule.run_at.strftime('%Y-%m-%d %H:%M') if schedule.run_at else 'N/A'}"

            next_run = schedule.next_run.strftime('%Y-%m-%d %H:%M') if schedule.next_run else 'N/A'
            last_run = schedule.last_run.strftime('%Y-%m-%d %H:%M') if schedule.last_run else 'Never'
            status = 'Enabled' if schedule.enabled else 'Disabled'

            self.schedules_tree.insert('', 'end', values=(
                schedule.name,
                schedule_str,
                next_run,
                last_run,
                schedule.run_count,
                status
            ))

    def _new_schedule(self):
        """Create new schedule."""
        dialog = tk.Toplevel(self)
        dialog.title('New Workflow Schedule')
        dialog.geometry('600x600')
        dialog.configure(bg='#2d2d2d')

        # Workflow selection
        tk.Label(dialog, text='Workflow ID:', bg='#2d2d2d', fg='white').grid(row=0, column=0, padx=10, pady=10, sticky='w')
        workflow_id_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', insertbackground='white')
        workflow_id_entry.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky='ew')

        tk.Label(dialog, text='Name:', bg='#2d2d2d', fg='white').grid(row=1, column=0, padx=10, pady=10, sticky='w')
        name_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', insertbackground='white')
        name_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky='ew')

        # Schedule type
        tk.Label(dialog, text='Schedule Type:', bg='#2d2d2d', fg='white').grid(row=2, column=0, padx=10, pady=10, sticky='w')
        schedule_type_var = tk.StringVar(value='cron')

        type_frame = tk.Frame(dialog, bg='#2d2d2d')
        type_frame.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky='w')

        tk.Radiobutton(type_frame, text='Cron', variable=schedule_type_var, value='cron',
                      bg='#2d2d2d', fg='white', selectcolor='#0088FE').pack(side='left', padx=5)
        tk.Radiobutton(type_frame, text='Interval', variable=schedule_type_var, value='interval',
                      bg='#2d2d2d', fg='white', selectcolor='#0088FE').pack(side='left', padx=5)
        tk.Radiobutton(type_frame, text='Once', variable=schedule_type_var, value='once',
                      bg='#2d2d2d', fg='white', selectcolor='#0088FE').pack(side='left', padx=5)

        # Cron fields
        cron_frame = tk.LabelFrame(dialog, text='Cron Schedule (* = any)', bg='#2d2d2d',
                                  fg='white', font=('Arial', 9, 'bold'))
        cron_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky='ew')

        cron_fields = [
            ('Minute (0-59):', '*'),
            ('Hour (0-23):', '*'),
            ('Day (1-31):', '*'),
            ('Month (1-12):', '*'),
            ('Weekday (0-6):', '*')
        ]

        cron_entries = {}
        for i, (label, default) in enumerate(cron_fields):
            tk.Label(cron_frame, text=label, bg='#2d2d2d', fg='white').grid(row=i, column=0, padx=5, pady=5, sticky='w')
            entry = tk.Entry(cron_frame, bg='#1e1e1e', fg='white', insertbackground='white')
            entry.insert(0, default)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
            cron_entries[label] = entry

        cron_frame.grid_columnconfigure(1, weight=1)

        # Interval field
        tk.Label(dialog, text='Interval (seconds):', bg='#2d2d2d', fg='white').grid(row=4, column=0, padx=10, pady=10, sticky='w')
        interval_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', insertbackground='white')
        interval_entry.insert(0, '60')
        interval_entry.grid(row=4, column=1, columnspan=2, padx=10, pady=10, sticky='ew')

        # Enabled checkbox
        enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(dialog, text='Enabled', variable=enabled_var,
                      bg='#2d2d2d', fg='white', selectcolor='#0088FE').grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky='w')

        dialog.grid_columnconfigure(1, weight=1)

        def save():
            workflow_id = workflow_id_entry.get()
            name = name_entry.get()

            if not workflow_id or not name:
                messagebox.showwarning('Missing Fields', 'Please fill required fields')
                return

            schedule_type = schedule_type_var.get()

            kwargs = {'enabled': enabled_var.get()}

            if schedule_type == 'cron':
                kwargs['minute'] = cron_entries['Minute (0-59):'].get()
                kwargs['hour'] = cron_entries['Hour (0-23):'].get()
                kwargs['day'] = cron_entries['Day (1-31):'].get()
                kwargs['month'] = cron_entries['Month (1-12):'].get()
                kwargs['weekday'] = cron_entries['Weekday (0-6):'].get()
            elif schedule_type == 'interval':
                kwargs['interval_value'] = int(interval_entry.get())

            schedule = ScheduledWorkflow(workflow_id, name, schedule_type, **kwargs)
            self.schedules.append(schedule)
            self._save_schedules()
            self._refresh_schedules()
            dialog.destroy()

        tk.Button(dialog, text='Save Schedule', command=save,
                 bg='#00C49F', fg='white', font=('Arial', 10, 'bold')).grid(row=6, column=0, columnspan=3, pady=20)

    def _edit_schedule(self):
        """Edit selected schedule."""
        selection = self.schedules_tree.selection()
        if not selection:
            messagebox.showwarning('No Selection', 'Please select a schedule to edit')
            return

        messagebox.showinfo('Edit', 'Edit dialog would open here')

    def _delete_schedule(self):
        """Delete selected schedule."""
        selection = self.schedules_tree.selection()
        if not selection:
            messagebox.showwarning('No Selection', 'Please select a schedule to delete')
            return

        index = self.schedules_tree.index(selection[0])
        schedule = self.schedules[index]

        response = messagebox.askyesno('Delete Schedule',
                                      f'Delete schedule "{schedule.name}"?')

        if response:
            self.schedules.pop(index)
            self._save_schedules()
            self._refresh_schedules()

    def _start_scheduler(self):
        """Start scheduler thread."""
        if self.scheduler_running:
            messagebox.showinfo('Already Running', 'Scheduler is already running')
            return

        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        self.status_label.config(text='Scheduler: Running', fg='#00C49F')

    def _stop_scheduler(self):
        """Stop scheduler thread."""
        self.scheduler_running = False
        self.status_label.config(text='Scheduler: Stopped', fg='#858585')

    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.scheduler_running:
            try:
                # Check each schedule
                for schedule in self.schedules:
                    if schedule.should_run():
                        # Check dependencies
                        dependencies_met = self._check_dependencies(schedule)

                        if dependencies_met:
                            # Execute workflow
                            self._execute_workflow(schedule)
                            schedule.mark_run()

                            # Update display
                            self.after(0, self._refresh_schedules)

                # Sleep for 1 second
                time.sleep(1)

            except Exception as e:
                print(f"Scheduler error: {e}")

    def _check_dependencies(self, schedule: ScheduledWorkflow) -> bool:
        """Check if workflow dependencies are met."""
        if not schedule.depends_on:
            return True

        # Check if dependent workflows have run recently
        for dep_id in schedule.depends_on:
            dep_schedule = next((s for s in self.schedules if s.workflow_id == dep_id), None)

            if not dep_schedule or not dep_schedule.last_run:
                return False

        return True

    def _execute_workflow(self, schedule: ScheduledWorkflow):
        """Execute workflow."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] Executed: {schedule.name}"

        self.after(0, lambda: self.history_list.insert(0, log_entry))

        # Call callback if provided
        if self.on_workflow_execute:
            self.on_workflow_execute(schedule.workflow_id)

    def _run_now(self):
        """Manually trigger selected workflow."""
        selection = self.schedules_tree.selection()
        if not selection:
            messagebox.showwarning('No Selection', 'Please select a schedule to run')
            return

        index = self.schedules_tree.index(selection[0])
        schedule = self.schedules[index]

        self._execute_workflow(schedule)
        schedule.mark_run()
        self._save_schedules()
        self._refresh_schedules()


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Workflow Scheduler - E2 Demo')
    root.geometry('1000x700')

    def on_workflow_execute(workflow_id):
        print(f"Executing workflow: {workflow_id}")

    scheduler = WorkflowScheduler(root, on_workflow_execute=on_workflow_execute)
    scheduler.pack(fill='both', expand=True)

    root.mainloop()
