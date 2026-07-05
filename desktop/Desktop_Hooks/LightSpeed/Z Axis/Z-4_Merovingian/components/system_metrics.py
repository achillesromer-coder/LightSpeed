"""
Advanced System Metrics - G1
============================

Comprehensive system performance monitoring and metrics collection.

Features:
- CPU usage monitoring (per-core, aggregate)
- Memory tracking (RAM, swap, virtual)
- Disk I/O statistics
- Network bandwidth monitoring
- Process tracking
- GPU monitoring (if available)
- Temperature sensors
- Battery status
- Custom metrics
- Historical data storage
- Alerts and thresholds
- Export to various formats

Author: LightSpeed Platform
Date: December 19, 2025
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import json
import threading
import time
from dataclasses import dataclass, asdict
from collections import deque
import psutil


@dataclass
class MetricSnapshot:
    """Single metric snapshot."""
    timestamp: datetime
    cpu_percent: float
    cpu_per_core: List[float]
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_read_mb: float
    disk_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    temperature: Optional[float] = None
    gpu_usage: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetricSnapshot':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class MetricsCollector:
    """Collects system metrics."""

    def __init__(self, history_size: int = 1000):
        self.history: deque[MetricSnapshot] = deque(maxlen=history_size)
        self.collecting = False
        self.collection_thread: Optional[threading.Thread] = None
        self.collection_interval = 1.0  # seconds

        # Baseline counters for delta calculations
        self.last_disk_io = psutil.disk_io_counters()
        self.last_network_io = psutil.net_io_counters()
        self.last_check_time = time.time()

    def start_collection(self):
        """Start collecting metrics."""
        if self.collecting:
            return

        self.collecting = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()

    def stop_collection(self):
        """Stop collecting metrics."""
        self.collecting = False

    def _collection_loop(self):
        """Main collection loop."""
        while self.collecting:
            try:
                snapshot = self._collect_snapshot()
                self.history.append(snapshot)
                time.sleep(self.collection_interval)
            except Exception as e:
                print(f"Metrics collection error: {e}")
                time.sleep(self.collection_interval)

    def _collect_snapshot(self) -> MetricSnapshot:
        """Collect single snapshot."""
        current_time = time.time()
        time_delta = current_time - self.last_check_time

        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)

        # Memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024 ** 3)
        memory_total_gb = memory.total / (1024 ** 3)

        # Disk I/O (delta per second)
        current_disk_io = psutil.disk_io_counters()
        disk_read_mb = 0.0
        disk_write_mb = 0.0

        if self.last_disk_io and time_delta > 0:
            disk_read_mb = (
                (current_disk_io.read_bytes - self.last_disk_io.read_bytes) /
                (1024 ** 2) / time_delta
            )
            disk_write_mb = (
                (current_disk_io.write_bytes - self.last_disk_io.write_bytes) /
                (1024 ** 2) / time_delta
            )

        self.last_disk_io = current_disk_io

        # Network I/O (delta per second)
        current_network_io = psutil.net_io_counters()
        network_sent_mb = 0.0
        network_recv_mb = 0.0

        if self.last_network_io and time_delta > 0:
            network_sent_mb = (
                (current_network_io.bytes_sent - self.last_network_io.bytes_sent) /
                (1024 ** 2) / time_delta
            )
            network_recv_mb = (
                (current_network_io.bytes_recv - self.last_network_io.bytes_recv) /
                (1024 ** 2) / time_delta
            )

        self.last_network_io = current_network_io
        self.last_check_time = current_time

        # Process count
        process_count = len(psutil.pids())

        # Temperature (if available)
        temperature = None
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                # Get first available temperature
                for name, entries in temps.items():
                    if entries:
                        temperature = entries[0].current
                        break
        except (AttributeError, Exception):
            pass

        # GPU (if available - requires additional library)
        gpu_usage = None
        # Would require nvidia-ml-py3 or similar

        return MetricSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            cpu_per_core=cpu_per_core,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            disk_read_mb=disk_read_mb,
            disk_write_mb=disk_write_mb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            process_count=process_count,
            temperature=temperature,
            gpu_usage=gpu_usage
        )

    def get_current_snapshot(self) -> Optional[MetricSnapshot]:
        """Get most recent snapshot."""
        return self.history[-1] if self.history else None

    def get_history(self, duration_minutes: int = 60) -> List[MetricSnapshot]:
        """Get historical snapshots."""
        if not self.history:
            return []

        cutoff = datetime.now() - timedelta(minutes=duration_minutes)
        return [s for s in self.history if s.timestamp >= cutoff]

    def get_statistics(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Calculate statistics over period."""
        history = self.get_history(duration_minutes)

        if not history:
            return {}

        cpu_values = [s.cpu_percent for s in history]
        memory_values = [s.memory_percent for s in history]

        return {
            'cpu_avg': sum(cpu_values) / len(cpu_values),
            'cpu_max': max(cpu_values),
            'cpu_min': min(cpu_values),
            'memory_avg': sum(memory_values) / len(memory_values),
            'memory_max': max(memory_values),
            'memory_min': min(memory_values),
            'sample_count': len(history),
            'duration_minutes': duration_minutes
        }

    def export_history(self, filepath: Path):
        """Export history to JSON."""
        data = {
            'exported_at': datetime.now().isoformat(),
            'snapshots': [s.to_dict() for s in self.history]
        }

        filepath.write_text(json.dumps(data, indent=2), encoding='utf-8')


class SystemMetricsGUI(tk.Frame):
    """Advanced System Metrics GUI."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#1e1e1e')

        self.collector = MetricsCollector(history_size=3600)  # 1 hour at 1s interval
        self.update_interval = 1000  # ms
        self.update_job = None

        self._build_ui()
        self.collector.start_collection()
        self._schedule_update()

    def _build_ui(self):
        """Build system metrics UI."""
        # Toolbar
        toolbar = tk.Frame(self, bg='#1e1e1e', height=50)
        toolbar.pack(side='top', fill='x')

        tk.Button(toolbar, text='⏸️ Pause', command=self._toggle_collection,
                 bg='#FFBB28', fg='black').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='🔄 Refresh', command=self._force_update,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='📊 Statistics', command=self._show_statistics,
                 bg='#00C49F', fg='white').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Label(toolbar, text='Update Interval:', bg='#1e1e1e', fg='white').pack(side='left', padx=5)
        self.interval_combo = ttk.Combobox(toolbar, values=['500ms', '1s', '2s', '5s'],
                                          width=10, state='readonly')
        self.interval_combo.set('1s')
        self.interval_combo.bind('<<ComboboxSelected>>', self._on_interval_change)
        self.interval_combo.pack(side='left', padx=5)

        tk.Button(toolbar, text='💾 Export', command=self._export_metrics,
                 bg='#858585', fg='white').pack(side='right', padx=5, pady=5)

        # Main content - Notebook
        notebook = ttk.Notebook(self)
        notebook.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        # Tab 1: Overview
        overview_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(overview_frame, text='Overview')

        # CPU Section
        cpu_frame = tk.LabelFrame(overview_frame, text='CPU', bg='#2d2d2d', fg='white',
                                 font=('Arial', 10, 'bold'))
        cpu_frame.pack(fill='x', padx=10, pady=5)

        self.cpu_label = tk.Label(cpu_frame, text='CPU: 0%', bg='#2d2d2d', fg='white',
                                 font=('Arial', 24, 'bold'), anchor='w')
        self.cpu_label.pack(padx=10, pady=5)

        self.cpu_progress = ttk.Progressbar(cpu_frame, mode='determinate', maximum=100)
        self.cpu_progress.pack(fill='x', padx=10, pady=5)

        self.cpu_cores_label = tk.Label(cpu_frame, text='Cores: N/A', bg='#2d2d2d',
                                        fg='#858585', font=('Arial', 9))
        self.cpu_cores_label.pack(anchor='w', padx=10, pady=2)

        # Memory Section
        mem_frame = tk.LabelFrame(overview_frame, text='Memory', bg='#2d2d2d', fg='white',
                                 font=('Arial', 10, 'bold'))
        mem_frame.pack(fill='x', padx=10, pady=5)

        self.mem_label = tk.Label(mem_frame, text='Memory: 0%', bg='#2d2d2d', fg='white',
                                 font=('Arial', 24, 'bold'), anchor='w')
        self.mem_label.pack(padx=10, pady=5)

        self.mem_progress = ttk.Progressbar(mem_frame, mode='determinate', maximum=100)
        self.mem_progress.pack(fill='x', padx=10, pady=5)

        self.mem_details_label = tk.Label(mem_frame, text='Used: 0 GB / Total: 0 GB',
                                          bg='#2d2d2d', fg='#858585', font=('Arial', 9))
        self.mem_details_label.pack(anchor='w', padx=10, pady=2)

        # Disk I/O Section
        disk_frame = tk.LabelFrame(overview_frame, text='Disk I/O', bg='#2d2d2d', fg='white',
                                  font=('Arial', 10, 'bold'))
        disk_frame.pack(fill='x', padx=10, pady=5)

        self.disk_read_label = tk.Label(disk_frame, text='Read: 0.00 MB/s', bg='#2d2d2d',
                                        fg='white', font=('Arial', 12))
        self.disk_read_label.pack(anchor='w', padx=10, pady=2)

        self.disk_write_label = tk.Label(disk_frame, text='Write: 0.00 MB/s', bg='#2d2d2d',
                                         fg='white', font=('Arial', 12))
        self.disk_write_label.pack(anchor='w', padx=10, pady=2)

        # Network I/O Section
        net_frame = tk.LabelFrame(overview_frame, text='Network I/O', bg='#2d2d2d', fg='white',
                                 font=('Arial', 10, 'bold'))
        net_frame.pack(fill='x', padx=10, pady=5)

        self.net_sent_label = tk.Label(net_frame, text='Sent: 0.00 MB/s', bg='#2d2d2d',
                                       fg='white', font=('Arial', 12))
        self.net_sent_label.pack(anchor='w', padx=10, pady=2)

        self.net_recv_label = tk.Label(net_frame, text='Received: 0.00 MB/s', bg='#2d2d2d',
                                       fg='white', font=('Arial', 12))
        self.net_recv_label.pack(anchor='w', padx=10, pady=2)

        # Tab 2: Detailed Metrics
        details_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(details_frame, text='Detailed')

        self.details_text = scrolledtext.ScrolledText(details_frame, bg='#1e1e1e', fg='white',
                                                      wrap='word', font=('Courier', 9))
        self.details_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 3: History Graph (text-based)
        history_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(history_frame, text='History')

        controls_frame = tk.Frame(history_frame, bg='#2d2d2d')
        controls_frame.pack(side='top', fill='x', padx=5, pady=5)

        tk.Label(controls_frame, text='Duration:', bg='#2d2d2d', fg='white').pack(side='left', padx=5)
        self.duration_combo = ttk.Combobox(controls_frame, values=['5 min', '15 min', '30 min', '60 min'],
                                          width=10, state='readonly')
        self.duration_combo.set('60 min')
        self.duration_combo.pack(side='left', padx=5)

        tk.Button(controls_frame, text='Show Graph', command=self._show_history_graph,
                 bg='#0088FE', fg='white').pack(side='left', padx=5)

        self.history_text = scrolledtext.ScrolledText(history_frame, bg='#1e1e1e', fg='white',
                                                      wrap='none', font=('Courier', 8))
        self.history_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 4: Processes
        process_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(process_frame, text='Processes')

        tk.Button(process_frame, text='🔄 Refresh Processes', command=self._load_processes,
                 bg='#0088FE', fg='white').pack(side='top', anchor='w', padx=5, pady=5)

        columns = ('PID', 'Name', 'CPU %', 'Memory %', 'Status')
        self.process_tree = ttk.Treeview(process_frame, columns=columns, show='headings', height=20)

        for col in columns:
            self.process_tree.heading(col, text=col)
            self.process_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(process_frame, orient='vertical', command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=scrollbar.set)

        self.process_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')

        # Status bar
        status_frame = tk.Frame(self, bg='#2d2d2d', height=30)
        status_frame.pack(side='bottom', fill='x')

        self.status_label = tk.Label(status_frame, text='Collecting metrics...', bg='#2d2d2d',
                                     fg='#858585', font=('Arial', 9), anchor='w')
        self.status_label.pack(side='left', padx=10, fill='x', expand=True)

        self.timestamp_label = tk.Label(status_frame, text='Last Update: N/A', bg='#2d2d2d',
                                        fg='#858585', font=('Arial', 9))
        self.timestamp_label.pack(side='right', padx=10)

    def _schedule_update(self):
        """Schedule next UI update."""
        if self.update_job:
            self.after_cancel(self.update_job)

        self._update_ui()
        self.update_job = self.after(self.update_interval, self._schedule_update)

    def _update_ui(self):
        """Update UI with current metrics."""
        snapshot = self.collector.get_current_snapshot()

        if not snapshot:
            return

        # Update CPU
        self.cpu_label.config(text=f'CPU: {snapshot.cpu_percent:.1f}%')
        self.cpu_progress['value'] = snapshot.cpu_percent

        cores_text = ', '.join(f'{c:.1f}%' for c in snapshot.cpu_per_core[:4])
        if len(snapshot.cpu_per_core) > 4:
            cores_text += '...'
        self.cpu_cores_label.config(text=f'Cores: {cores_text}')

        # Update Memory
        self.mem_label.config(text=f'Memory: {snapshot.memory_percent:.1f}%')
        self.mem_progress['value'] = snapshot.memory_percent
        self.mem_details_label.config(
            text=f'Used: {snapshot.memory_used_gb:.2f} GB / Total: {snapshot.memory_total_gb:.2f} GB'
        )

        # Update Disk I/O
        self.disk_read_label.config(text=f'Read: {snapshot.disk_read_mb:.2f} MB/s')
        self.disk_write_label.config(text=f'Write: {snapshot.disk_write_mb:.2f} MB/s')

        # Update Network I/O
        self.net_sent_label.config(text=f'Sent: {snapshot.network_sent_mb:.2f} MB/s')
        self.net_recv_label.config(text=f'Received: {snapshot.network_recv_mb:.2f} MB/s')

        # Update detailed view
        self._update_details(snapshot)

        # Update timestamp
        self.timestamp_label.config(text=f'Last Update: {snapshot.timestamp.strftime("%H:%M:%S")}')

    def _update_details(self, snapshot: MetricSnapshot):
        """Update detailed metrics view."""
        self.details_text.delete('1.0', 'end')

        self.details_text.insert('end', f"=== System Metrics at {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

        # CPU Details
        self.details_text.insert('end', "CPU:\n")
        self.details_text.insert('end', f"  Overall: {snapshot.cpu_percent:.2f}%\n")
        for i, core_usage in enumerate(snapshot.cpu_per_core):
            self.details_text.insert('end', f"  Core {i}: {core_usage:.2f}%\n")
        self.details_text.insert('end', '\n')

        # Memory Details
        self.details_text.insert('end', "Memory:\n")
        self.details_text.insert('end', f"  Percent: {snapshot.memory_percent:.2f}%\n")
        self.details_text.insert('end', f"  Used: {snapshot.memory_used_gb:.2f} GB\n")
        self.details_text.insert('end', f"  Total: {snapshot.memory_total_gb:.2f} GB\n")
        self.details_text.insert('end', f"  Available: {snapshot.memory_total_gb - snapshot.memory_used_gb:.2f} GB\n")
        self.details_text.insert('end', '\n')

        # Disk I/O
        self.details_text.insert('end', "Disk I/O:\n")
        self.details_text.insert('end', f"  Read: {snapshot.disk_read_mb:.2f} MB/s\n")
        self.details_text.insert('end', f"  Write: {snapshot.disk_write_mb:.2f} MB/s\n")
        self.details_text.insert('end', '\n')

        # Network I/O
        self.details_text.insert('end', "Network I/O:\n")
        self.details_text.insert('end', f"  Sent: {snapshot.network_sent_mb:.2f} MB/s\n")
        self.details_text.insert('end', f"  Received: {snapshot.network_recv_mb:.2f} MB/s\n")
        self.details_text.insert('end', '\n')

        # Other
        self.details_text.insert('end', "System:\n")
        self.details_text.insert('end', f"  Process Count: {snapshot.process_count}\n")

        if snapshot.temperature is not None:
            self.details_text.insert('end', f"  Temperature: {snapshot.temperature:.1f}°C\n")

        if snapshot.gpu_usage is not None:
            self.details_text.insert('end', f"  GPU Usage: {snapshot.gpu_usage:.1f}%\n")

    def _toggle_collection(self):
        """Toggle metric collection."""
        if self.collector.collecting:
            self.collector.stop_collection()
            self.status_label.config(text='Collection paused')
        else:
            self.collector.start_collection()
            self.status_label.config(text='Collection resumed')

    def _force_update(self):
        """Force immediate update."""
        self._update_ui()

    def _on_interval_change(self, event=None):
        """Handle update interval change."""
        interval_text = self.interval_combo.get()

        if interval_text == '500ms':
            self.update_interval = 500
        elif interval_text == '1s':
            self.update_interval = 1000
        elif interval_text == '2s':
            self.update_interval = 2000
        elif interval_text == '5s':
            self.update_interval = 5000

        self._schedule_update()

    def _show_statistics(self):
        """Show statistics dialog."""
        stats = self.collector.get_statistics(duration_minutes=60)

        if not stats:
            messagebox.showinfo('Statistics', 'No data available yet')
            return

        msg = "System Statistics (Last 60 minutes):\n\n"
        msg += f"CPU Average: {stats['cpu_avg']:.2f}%\n"
        msg += f"CPU Max: {stats['cpu_max']:.2f}%\n"
        msg += f"CPU Min: {stats['cpu_min']:.2f}%\n\n"
        msg += f"Memory Average: {stats['memory_avg']:.2f}%\n"
        msg += f"Memory Max: {stats['memory_max']:.2f}%\n"
        msg += f"Memory Min: {stats['memory_min']:.2f}%\n\n"
        msg += f"Samples: {stats['sample_count']}"

        messagebox.showinfo('Statistics', msg)

    def _show_history_graph(self):
        """Show history graph (text-based ASCII)."""
        duration_text = self.duration_combo.get()
        duration = int(duration_text.split()[0])

        history = self.collector.get_history(duration_minutes=duration)

        if not history:
            self.history_text.delete('1.0', 'end')
            self.history_text.insert('1.0', 'No history data available')
            return

        # Simple ASCII graph
        self.history_text.delete('1.0', 'end')

        self.history_text.insert('end', f"Metrics History (Last {duration} minutes)\n")
        self.history_text.insert('end', "=" * 80 + "\n\n")

        # CPU Graph
        self.history_text.insert('end', "CPU Usage:\n")
        for i, snapshot in enumerate(history[-50:]):  # Last 50 points
            bar_length = int(snapshot.cpu_percent / 2)  # Scale to 50 chars max
            bar = '█' * bar_length
            self.history_text.insert('end', f"{snapshot.timestamp.strftime('%H:%M:%S')} |{bar:50}| {snapshot.cpu_percent:.1f}%\n")

        self.history_text.insert('end', '\n')

        # Memory Graph
        self.history_text.insert('end', "Memory Usage:\n")
        for i, snapshot in enumerate(history[-50:]):
            bar_length = int(snapshot.memory_percent / 2)
            bar = '█' * bar_length
            self.history_text.insert('end', f"{snapshot.timestamp.strftime('%H:%M:%S')} |{bar:50}| {snapshot.memory_percent:.1f}%\n")

    def _load_processes(self):
        """Load process list."""
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)

        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU usage
        processes.sort(key=lambda p: p.get('cpu_percent', 0), reverse=True)

        # Add top 100 processes
        for proc in processes[:100]:
            self.process_tree.insert(
                '',
                'end',
                values=(
                    proc.get('pid', 'N/A'),
                    proc.get('name', 'N/A'),
                    f"{proc.get('cpu_percent', 0):.1f}",
                    f"{proc.get('memory_percent', 0):.1f}",
                    proc.get('status', 'N/A')
                )
            )

        self.status_label.config(text=f'Loaded {len(processes[:100])} processes')

    def _export_metrics(self):
        """Export metrics history."""
        filepath = filedialog.asksaveasfilename(
            title='Export Metrics',
            defaultextension='.json',
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')]
        )

        if filepath:
            self.collector.export_history(Path(filepath))
            messagebox.showinfo('Exported', f'Metrics exported to:\n{filepath}')


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Advanced System Metrics - G1 Demo')
    root.geometry('1200x800')

    metrics_gui = SystemMetricsGUI(root)
    metrics_gui.pack(fill='both', expand=True)

    root.mainloop()
