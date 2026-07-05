"""
Performance Profiler - G2
=========================

Comprehensive performance profiling for code execution analysis.

Features:
- Function call profiling
- CPU time tracking
- Memory profiling
- Call graph visualization
- Hot path detection
- Bottleneck identification
- Flame graph generation (text-based)
- Profile comparison
- Export profiling data
- Decorators for easy profiling

Author: LightSpeed Platform
Date: December 19, 2025
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
import json
import time
import threading
import tracemalloc
from dataclasses import dataclass, asdict
from collections import defaultdict
import functools


@dataclass
class FunctionProfile:
    """Profile data for a function."""
    name: str
    calls: int = 0
    total_time: float = 0.0
    cumulative_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    memory_delta: int = 0  # bytes

    def update(self, execution_time: float, memory_delta: int = 0):
        """Update profile with new execution."""
        self.calls += 1
        self.total_time += execution_time
        self.avg_time = self.total_time / self.calls
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.memory_delta += memory_delta

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class Profiler:
    """Performance profiler."""

    def __init__(self):
        self.profiles: Dict[str, FunctionProfile] = {}
        self.call_stack: List[str] = []
        self.enabled = False
        self.track_memory = False

    def enable(self, track_memory: bool = False):
        """Enable profiler."""
        self.enabled = True
        self.track_memory = track_memory
        if track_memory:
            tracemalloc.start()

    def disable(self):
        """Disable profiler."""
        self.enabled = False
        if self.track_memory:
            tracemalloc.stop()

    def reset(self):
        """Reset all profiles."""
        self.profiles.clear()
        self.call_stack.clear()

    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile a function."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)

            func_name = f"{func.__module__}.{func.__name__}"

            # Track memory if enabled
            mem_before = 0
            if self.track_memory:
                mem_before = tracemalloc.get_traced_memory()[0]

            # Time execution
            start_time = time.perf_counter()

            try:
                self.call_stack.append(func_name)
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                execution_time = end_time - start_time

                # Calculate memory delta
                mem_delta = 0
                if self.track_memory:
                    mem_after = tracemalloc.get_traced_memory()[0]
                    mem_delta = mem_after - mem_before

                # Update profile
                if func_name not in self.profiles:
                    self.profiles[func_name] = FunctionProfile(name=func_name)

                self.profiles[func_name].update(execution_time, mem_delta)

                if self.call_stack and self.call_stack[-1] == func_name:
                    self.call_stack.pop()

        return wrapper

    def get_hot_paths(self, top_n: int = 10) -> List[FunctionProfile]:
        """Get hottest execution paths."""
        sorted_profiles = sorted(
            self.profiles.values(),
            key=lambda p: p.total_time,
            reverse=True
        )
        return sorted_profiles[:top_n]

    def get_call_statistics(self) -> Dict[str, Any]:
        """Get overall call statistics."""
        if not self.profiles:
            return {}

        total_calls = sum(p.calls for p in self.profiles.values())
        total_time = sum(p.total_time for p in self.profiles.values())

        return {
            'total_functions': len(self.profiles),
            'total_calls': total_calls,
            'total_time': total_time,
            'avg_time_per_call': total_time / total_calls if total_calls > 0 else 0
        }

    def export_profile(self, filepath: Path):
        """Export profile data."""
        data = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.get_call_statistics(),
            'profiles': {name: prof.to_dict() for name, prof in self.profiles.items()}
        }

        filepath.write_text(json.dumps(data, indent=2), encoding='utf-8')


class PerformanceProfilerGUI(tk.Frame):
    """Performance Profiler GUI."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#1e1e1e')

        self.profiler = Profiler()
        self.profiling_active = False

        self._build_ui()

    def _build_ui(self):
        """Build profiler UI."""
        # Toolbar
        toolbar = tk.Frame(self, bg='#1e1e1e', height=50)
        toolbar.pack(side='top', fill='x')

        self.start_button = tk.Button(toolbar, text='▶️ Start Profiling',
                                      command=self._start_profiling,
                                      bg='#00C49F', fg='white')
        self.start_button.pack(side='left', padx=5, pady=5)

        self.stop_button = tk.Button(toolbar, text='⏹️ Stop Profiling',
                                     command=self._stop_profiling,
                                     bg='#FF8042', fg='white', state='disabled')
        self.stop_button.pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='🗑️ Reset', command=self._reset_profiler,
                 bg='#858585', fg='white').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Button(toolbar, text='🔥 Hot Paths', command=self._show_hot_paths,
                 bg='#FFBB28', fg='black').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='📊 Statistics', command=self._show_statistics,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        self.memory_tracking_var = tk.BooleanVar(value=False)
        tk.Checkbutton(toolbar, text='Track Memory', variable=self.memory_tracking_var,
                      bg='#1e1e1e', fg='white', selectcolor='#0088FE').pack(side='left', padx=5)

        tk.Button(toolbar, text='💾 Export', command=self._export_profile,
                 bg='#858585', fg='white').pack(side='right', padx=5, pady=5)

        # Main content - Notebook
        notebook = ttk.Notebook(self)
        notebook.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        # Tab 1: Function Profiles
        profiles_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(profiles_frame, text='Function Profiles')

        # Sort controls
        sort_frame = tk.Frame(profiles_frame, bg='#2d2d2d')
        sort_frame.pack(side='top', fill='x', padx=5, pady=5)

        tk.Label(sort_frame, text='Sort by:', bg='#2d2d2d', fg='white').pack(side='left', padx=5)
        self.sort_combo = ttk.Combobox(sort_frame,
                                      values=['Total Time', 'Calls', 'Avg Time', 'Max Time', 'Memory'],
                                      width=12, state='readonly')
        self.sort_combo.set('Total Time')
        self.sort_combo.bind('<<ComboboxSelected>>', lambda e: self._refresh_profiles())
        self.sort_combo.pack(side='left', padx=5)

        tk.Button(sort_frame, text='🔄 Refresh', command=self._refresh_profiles,
                 bg='#0088FE', fg='white').pack(side='left', padx=5)

        # Profiles tree
        columns = ('Calls', 'Total Time', 'Avg Time', 'Min Time', 'Max Time', 'Memory')
        self.profiles_tree = ttk.Treeview(profiles_frame, columns=columns,
                                         show='tree headings', height=20)

        self.profiles_tree.heading('#0', text='Function Name')
        self.profiles_tree.column('#0', width=300)

        for col in columns:
            self.profiles_tree.heading(col, text=col)
            self.profiles_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(profiles_frame, orient='vertical',
                                 command=self.profiles_tree.yview)
        self.profiles_tree.configure(yscrollcommand=scrollbar.set)

        self.profiles_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')

        # Tab 2: Hot Paths
        hotpaths_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(hotpaths_frame, text='Hot Paths')

        tk.Label(hotpaths_frame, text='Execution Hot Paths (Slowest Functions)',
                bg='#2d2d2d', fg='white', font=('Arial', 10, 'bold')).pack(anchor='w',
                                                                          padx=5, pady=5)

        self.hotpaths_text = scrolledtext.ScrolledText(hotpaths_frame, bg='#1e1e1e',
                                                       fg='white', wrap='word',
                                                       font=('Courier', 9))
        self.hotpaths_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 3: Flame Graph (text-based)
        flamegraph_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(flamegraph_frame, text='Flame Graph')

        tk.Button(flamegraph_frame, text='Generate Flame Graph',
                 command=self._generate_flame_graph,
                 bg='#FF8042', fg='white').pack(side='top', anchor='w', padx=5, pady=5)

        self.flamegraph_text = scrolledtext.ScrolledText(flamegraph_frame, bg='#1e1e1e',
                                                         fg='white', wrap='none',
                                                         font=('Courier', 8))
        self.flamegraph_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 4: Code Examples
        examples_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(examples_frame, text='Usage Examples')

        tk.Label(examples_frame, text='How to Use the Profiler', bg='#2d2d2d',
                fg='white', font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=5)

        examples_text = scrolledtext.ScrolledText(examples_frame, bg='#1e1e1e',
                                                  fg='white', wrap='word',
                                                  font=('Courier', 9))
        examples_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Add usage examples
        examples_content = """
# Using the Performance Profiler

## 1. Decorator-based Profiling

from core.services.performance_profiler import profiler

@profiler.profile_function
def my_function():
    # Your code here
    time.sleep(0.1)
    return "result"

## 2. Start/Stop Profiling

# Enable profiler
profiler.enable(track_memory=True)

# Run your code
my_function()
other_function()

# Stop profiler
profiler.disable()

# View results in the GUI

## 3. Context Manager (Advanced)

class ProfileContext:
    def __enter__(self):
        profiler.enable()
        return profiler

    def __exit__(self, *args):
        profiler.disable()

with ProfileContext():
    # Code to profile
    process_data()

## 4. Export Results

profiler.export_profile(Path("profile_results.json"))

## Tips:
- Use memory tracking sparingly (adds overhead)
- Focus on hot paths for optimization
- Compare profiles before/after changes
- Profile realistic workloads
"""

        examples_text.insert('1.0', examples_content)
        examples_text.configure(state='disabled')

        # Status bar
        status_frame = tk.Frame(self, bg='#2d2d2d', height=30)
        status_frame.pack(side='bottom', fill='x')

        self.status_label = tk.Label(status_frame, text='Profiler ready', bg='#2d2d2d',
                                     fg='#858585', font=('Arial', 9), anchor='w')
        self.status_label.pack(side='left', padx=10, fill='x', expand=True)

        self.profile_count_label = tk.Label(status_frame, text='Functions: 0', bg='#2d2d2d',
                                           fg='#858585', font=('Arial', 9))
        self.profile_count_label.pack(side='right', padx=10)

    def _start_profiling(self):
        """Start profiling."""
        track_memory = self.memory_tracking_var.get()
        self.profiler.enable(track_memory=track_memory)
        self.profiling_active = True

        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')

        self.status_label.config(text='Profiling active...')

        # Run demo profiling
        self._run_demo_profiling()

    def _stop_profiling(self):
        """Stop profiling."""
        self.profiler.disable()
        self.profiling_active = False

        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

        self.status_label.config(text='Profiling stopped')
        self._refresh_profiles()

    def _reset_profiler(self):
        """Reset profiler data."""
        self.profiler.reset()
        self._refresh_profiles()
        self.status_label.config(text='Profiler reset')

    def _refresh_profiles(self):
        """Refresh profile display."""
        for item in self.profiles_tree.get_children():
            self.profiles_tree.delete(item)

        # Sort profiles
        sort_by = self.sort_combo.get()
        profiles = list(self.profiler.profiles.values())

        if sort_by == 'Total Time':
            profiles.sort(key=lambda p: p.total_time, reverse=True)
        elif sort_by == 'Calls':
            profiles.sort(key=lambda p: p.calls, reverse=True)
        elif sort_by == 'Avg Time':
            profiles.sort(key=lambda p: p.avg_time, reverse=True)
        elif sort_by == 'Max Time':
            profiles.sort(key=lambda p: p.max_time, reverse=True)
        elif sort_by == 'Memory':
            profiles.sort(key=lambda p: p.memory_delta, reverse=True)

        # Add to tree
        for profile in profiles:
            self.profiles_tree.insert(
                '',
                'end',
                text=profile.name,
                values=(
                    profile.calls,
                    f"{profile.total_time:.4f}s",
                    f"{profile.avg_time:.6f}s",
                    f"{profile.min_time:.6f}s",
                    f"{profile.max_time:.6f}s",
                    f"{profile.memory_delta / 1024:.2f} KB" if profile.memory_delta else "N/A"
                )
            )

        self.profile_count_label.config(text=f'Functions: {len(profiles)}')

    def _show_hot_paths(self):
        """Show hot execution paths."""
        hot_paths = self.profiler.get_hot_paths(top_n=20)

        self.hotpaths_text.delete('1.0', 'end')

        if not hot_paths:
            self.hotpaths_text.insert('1.0', 'No profile data available')
            return

        self.hotpaths_text.insert('end', 'Top 20 Hot Paths (by total execution time)\n')
        self.hotpaths_text.insert('end', '=' * 80 + '\n\n')

        for i, profile in enumerate(hot_paths, 1):
            self.hotpaths_text.insert('end', f"{i}. {profile.name}\n")
            self.hotpaths_text.insert('end', f"   Total Time: {profile.total_time:.4f}s\n")
            self.hotpaths_text.insert('end', f"   Calls: {profile.calls}\n")
            self.hotpaths_text.insert('end', f"   Avg Time: {profile.avg_time:.6f}s\n")
            self.hotpaths_text.insert('end', f"   Min/Max: {profile.min_time:.6f}s / {profile.max_time:.6f}s\n")
            if profile.memory_delta:
                self.hotpaths_text.insert('end', f"   Memory: {profile.memory_delta / 1024:.2f} KB\n")
            self.hotpaths_text.insert('end', '\n')

    def _show_statistics(self):
        """Show profiling statistics."""
        stats = self.profiler.get_call_statistics()

        if not stats:
            messagebox.showinfo('Statistics', 'No profile data available')
            return

        msg = "Profiling Statistics:\n\n"
        msg += f"Total Functions Profiled: {stats['total_functions']}\n"
        msg += f"Total Function Calls: {stats['total_calls']}\n"
        msg += f"Total Execution Time: {stats['total_time']:.4f}s\n"
        msg += f"Average Time per Call: {stats['avg_time_per_call']:.6f}s"

        messagebox.showinfo('Statistics', msg)

    def _generate_flame_graph(self):
        """Generate text-based flame graph."""
        hot_paths = self.profiler.get_hot_paths(top_n=30)

        self.flamegraph_text.delete('1.0', 'end')

        if not hot_paths:
            self.flamegraph_text.insert('1.0', 'No profile data available')
            return

        self.flamegraph_text.insert('end', 'Flame Graph (ASCII)\n')
        self.flamegraph_text.insert('end', '=' * 100 + '\n\n')

        # Find max time for scaling
        max_time = max(p.total_time for p in hot_paths)

        for profile in hot_paths:
            # Calculate bar width (0-80 chars)
            bar_width = int((profile.total_time / max_time) * 80)
            bar = '█' * bar_width

            # Function name (truncated)
            func_name = profile.name[-40:] if len(profile.name) > 40 else profile.name

            self.flamegraph_text.insert('end',
                f"{func_name:40} |{bar:80}| {profile.total_time:.4f}s ({profile.calls} calls)\n"
            )

    def _run_demo_profiling(self):
        """Run demo profiling in background."""
        def demo():
            @self.profiler.profile_function
            def fast_function():
                time.sleep(0.001)
                return sum(range(100))

            @self.profiler.profile_function
            def medium_function():
                time.sleep(0.01)
                return sum(range(1000))

            @self.profiler.profile_function
            def slow_function():
                time.sleep(0.05)
                result = []
                for i in range(100):
                    result.append(fast_function())
                return result

            # Run demo workload
            for _ in range(10):
                fast_function()
                medium_function()
                slow_function()

                if not self.profiling_active:
                    break

                time.sleep(0.1)

            self.after(0, lambda: self._refresh_profiles())

        threading.Thread(target=demo, daemon=True).start()

    def _export_profile(self):
        """Export profile data."""
        if not self.profiler.profiles:
            messagebox.showwarning('No Data', 'No profile data to export')
            return

        filepath = filedialog.asksaveasfilename(
            title='Export Profile',
            defaultextension='.json',
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')]
        )

        if filepath:
            self.profiler.export_profile(Path(filepath))
            messagebox.showinfo('Exported', f'Profile exported to:\n{filepath}')


# Global profiler instance
profiler = Profiler()


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Performance Profiler - G2 Demo')
    root.geometry('1400x800')

    profiler_gui = PerformanceProfilerGUI(root)
    profiler_gui.pack(fill='both', expand=True)

    root.mainloop()
