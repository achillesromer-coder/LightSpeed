"""
Enhanced AI Context Manager - F1
================================

Advanced context management for AI interactions with full system state integration.

Features:
- System state context gathering
- Project context extraction
- Code context analysis
- Conversation history management
- Context priority weighting
- Token optimization
- Dynamic context updates
- Multi-source integration
- Z-layer awareness
- Neo AI integration

Author: LightSpeed Platform
Date: December 19, 2025
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json
import hashlib
import threading
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class ContextItem:
    """Individual context item with metadata."""
    id: str
    type: str  # 'system', 'project', 'code', 'conversation', 'file', 'z_layer'
    content: str
    priority: int  # 1-10, higher = more important
    timestamp: datetime
    source: str
    tokens: int
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextItem':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ContextManager:
    """Manages AI context collection and optimization."""

    def __init__(self):
        self.contexts: Dict[str, ContextItem] = {}
        self.context_history: List[Dict[str, Any]] = []
        self.max_tokens: int = 8000  # Default token limit
        self.active_sources: Dict[str, bool] = {
            'system': True,
            'project': True,
            'code': True,
            'conversation': True,
            'files': True,
            'z_layer': True
        }
        self.context_weights: Dict[str, float] = {
            'system': 0.8,
            'project': 0.9,
            'code': 1.0,
            'conversation': 0.95,
            'files': 0.85,
            'z_layer': 1.0
        }

    def add_context(
        self,
        context_type: str,
        content: str,
        priority: int = 5,
        source: str = "manual",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add context item."""
        context_id = hashlib.md5(
            f"{context_type}_{content}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        tokens = self._estimate_tokens(content)

        context = ContextItem(
            id=context_id,
            type=context_type,
            content=content,
            priority=priority,
            timestamp=datetime.now(),
            source=source,
            tokens=tokens,
            metadata=metadata or {}
        )

        self.contexts[context_id] = context
        return context_id

    def remove_context(self, context_id: str):
        """Remove context item."""
        if context_id in self.contexts:
            del self.contexts[context_id]

    def get_optimized_context(
        self,
        max_tokens: Optional[int] = None,
        include_types: Optional[List[str]] = None
    ) -> str:
        """Get optimized context within token limit."""
        limit = max_tokens or self.max_tokens

        # Filter by type
        if include_types:
            relevant = [c for c in self.contexts.values() if c.type in include_types]
        else:
            relevant = [c for c in self.contexts.values()
                       if self.active_sources.get(c.type, False)]

        # Sort by weighted priority
        def weighted_priority(ctx: ContextItem) -> float:
            weight = self.context_weights.get(ctx.type, 1.0)
            return ctx.priority * weight

        relevant.sort(key=weighted_priority, reverse=True)

        # Build context within token limit
        selected: List[ContextItem] = []
        total_tokens = 0

        for context in relevant:
            if total_tokens + context.tokens <= limit:
                selected.append(context)
                total_tokens += context.tokens
            elif total_tokens < limit * 0.9:  # Allow some overflow
                # Try to truncate
                remaining = limit - total_tokens
                truncated = self._truncate_content(context.content, remaining)
                if truncated:
                    context.content = truncated
                    context.tokens = self._estimate_tokens(truncated)
                    selected.append(context)
                break

        # Format context
        return self._format_context(selected)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # GPT-style: ~4 chars per token
        return len(text) // 4

    def _truncate_content(self, content: str, max_tokens: int) -> Optional[str]:
        """Truncate content to fit token limit."""
        max_chars = max_tokens * 4
        if len(content) <= max_chars:
            return content
        return content[:max_chars] + "... [truncated]"

    def _format_context(self, contexts: List[ContextItem]) -> str:
        """Format contexts into readable text."""
        sections = defaultdict(list)

        for ctx in contexts:
            sections[ctx.type].append(ctx)

        output = []

        # System context
        if 'system' in sections:
            output.append("=== SYSTEM CONTEXT ===")
            for ctx in sections['system']:
                output.append(ctx.content)
            output.append("")

        # Project context
        if 'project' in sections:
            output.append("=== PROJECT CONTEXT ===")
            for ctx in sections['project']:
                output.append(ctx.content)
            output.append("")

        # Code context
        if 'code' in sections:
            output.append("=== CODE CONTEXT ===")
            for ctx in sections['code']:
                output.append(f"Source: {ctx.metadata.get('file', 'unknown')}")
                output.append(ctx.content)
                output.append("")

        # Z-Layer context
        if 'z_layer' in sections:
            output.append("=== Z-LAYER CONTEXT ===")
            for ctx in sections['z_layer']:
                output.append(f"Layer: {ctx.metadata.get('layer', 'unknown')}")
                output.append(ctx.content)
                output.append("")

        # Conversation context
        if 'conversation' in sections:
            output.append("=== CONVERSATION HISTORY ===")
            for ctx in sections['conversation']:
                output.append(ctx.content)
            output.append("")

        return "\n".join(output)

    def gather_system_context(self) -> str:
        """Gather current system state context."""
        import platform
        import psutil

        context = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
            'memory_available': f"{psutil.virtual_memory().available / (1024**3):.1f} GB",
            'disk_usage': f"{psutil.disk_usage('/').percent}%"
        }

        content = "System Information:\n"
        for key, value in context.items():
            content += f"  {key}: {value}\n"

        context_id = self.add_context(
            'system',
            content,
            priority=5,
            source='system_monitor',
            metadata=context
        )

        return content

    def gather_project_context(self, project_path: Path) -> str:
        """Gather project structure and metadata."""
        if not project_path.exists():
            return ""

        context = {
            'project_path': str(project_path),
            'project_name': project_path.name,
            'files_count': 0,
            'directories': [],
            'file_types': defaultdict(int)
        }

        # Scan project structure
        for item in project_path.rglob('*'):
            if item.is_file():
                context['files_count'] += 1
                context['file_types'][item.suffix] += 1
            elif item.is_dir():
                rel_path = item.relative_to(project_path)
                if len(rel_path.parts) <= 2:  # Only top 2 levels
                    context['directories'].append(str(rel_path))

        content = f"Project: {context['project_name']}\n"
        content += f"Location: {context['project_path']}\n"
        content += f"Total Files: {context['files_count']}\n"
        content += "\nDirectories:\n"
        for dir_path in sorted(context['directories'])[:20]:
            content += f"  - {dir_path}\n"
        content += "\nFile Types:\n"
        for ext, count in sorted(context['file_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
            content += f"  {ext or '[no ext]'}: {count}\n"

        self.add_context(
            'project',
            content,
            priority=7,
            source='project_scanner',
            metadata=context
        )

        return content

    def gather_code_context(self, file_path: Path, line_range: Optional[Tuple[int, int]] = None) -> str:
        """Gather code context from file."""
        if not file_path.exists():
            return ""

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()

            if line_range:
                start, end = line_range
                lines = lines[start:end]
                context_content = '\n'.join(lines)
            else:
                context_content = content

            metadata = {
                'file': str(file_path),
                'language': file_path.suffix,
                'total_lines': len(lines),
                'line_range': line_range
            }

            formatted = f"File: {file_path.name}\n"
            formatted += f"Language: {file_path.suffix}\n"
            formatted += "```\n"
            formatted += context_content
            formatted += "\n```"

            self.add_context(
                'code',
                formatted,
                priority=8,
                source='code_analyzer',
                metadata=metadata
            )

            return formatted

        except Exception as e:
            return f"Error reading {file_path}: {str(e)}"

    def add_conversation_turn(self, role: str, message: str):
        """Add conversation turn to context."""
        content = f"{role.upper()}: {message}"

        self.add_context(
            'conversation',
            content,
            priority=9,
            source='conversation',
            metadata={'role': role, 'timestamp': datetime.now().isoformat()}
        )

    def gather_z_layer_context(self, layer_id: str, layer_data: Dict[str, Any]) -> str:
        """Gather Z-layer context."""
        content = f"Z-Layer: {layer_id}\n"
        content += f"Status: {layer_data.get('status', 'unknown')}\n"
        content += f"Components: {', '.join(layer_data.get('components', []))}\n"

        if 'state' in layer_data:
            content += "\nState:\n"
            for key, value in layer_data['state'].items():
                content += f"  {key}: {value}\n"

        self.add_context(
            'z_layer',
            content,
            priority=8,
            source='z_layer_monitor',
            metadata={'layer_id': layer_id, **layer_data}
        )

        return content

    def save_contexts(self, filepath: Path):
        """Save contexts to JSON."""
        data = {
            'contexts': {cid: ctx.to_dict() for cid, ctx in self.contexts.items()},
            'settings': {
                'max_tokens': self.max_tokens,
                'active_sources': self.active_sources,
                'context_weights': self.context_weights
            },
            'saved_at': datetime.now().isoformat()
        }

        filepath.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def load_contexts(self, filepath: Path):
        """Load contexts from JSON."""
        if not filepath.exists():
            return

        data = json.loads(filepath.read_text(encoding='utf-8'))

        self.contexts = {
            cid: ContextItem.from_dict(ctx_data)
            for cid, ctx_data in data.get('contexts', {}).items()
        }

        settings = data.get('settings', {})
        self.max_tokens = settings.get('max_tokens', self.max_tokens)
        self.active_sources = settings.get('active_sources', self.active_sources)
        self.context_weights = settings.get('context_weights', self.context_weights)


class AIContextGUI(tk.Frame):
    """Enhanced AI Context Manager GUI."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#1e1e1e')

        self.context_manager = ContextManager()
        self.project_path: Optional[Path] = None
        self.auto_update = tk.BooleanVar(value=False)
        self.update_interval = 30  # seconds
        self.update_thread: Optional[threading.Thread] = None
        self.running = False

        self._build_ui()
        self._load_default_contexts()

    def _build_ui(self):
        """Build AI context UI."""
        # Toolbar
        toolbar = tk.Frame(self, bg='#1e1e1e', height=50)
        toolbar.pack(side='top', fill='x')

        tk.Button(toolbar, text='🔄 Refresh', command=self._refresh_contexts,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='📂 Set Project', command=self._select_project,
                 bg='#00C49F', fg='white').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='➕ Add Context', command=self._add_manual_context,
                 bg='#FFBB28', fg='black').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Checkbutton(toolbar, text='Auto-Update', variable=self.auto_update,
                      command=self._toggle_auto_update,
                      bg='#1e1e1e', fg='white', selectcolor='#0088FE').pack(side='left', padx=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Label(toolbar, text='Max Tokens:', bg='#1e1e1e', fg='white').pack(side='left', padx=5)
        self.token_limit_entry = tk.Entry(toolbar, width=8, bg='#2d2d2d', fg='white')
        self.token_limit_entry.insert(0, str(self.context_manager.max_tokens))
        self.token_limit_entry.pack(side='left', padx=5)

        tk.Button(toolbar, text='💾 Save', command=self._save_contexts,
                 bg='#858585', fg='white').pack(side='right', padx=5, pady=5)

        tk.Button(toolbar, text='📤 Export', command=self._export_context,
                 bg='#858585', fg='white').pack(side='right', padx=5, pady=5)

        # Main content - Notebook
        notebook = ttk.Notebook(self)
        notebook.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        # Tab 1: Context Items
        items_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(items_frame, text='Context Items')

        # Context list
        list_frame = tk.Frame(items_frame, bg='#2d2d2d')
        list_frame.pack(side='left', fill='both', expand=True)

        tk.Label(list_frame, text='Active Contexts', bg='#2d2d2d', fg='white',
                font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=5)

        # Treeview for contexts
        columns = ('Type', 'Priority', 'Tokens', 'Source', 'Time')
        self.context_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)

        self.context_tree.heading('#0', text='ID')
        self.context_tree.column('#0', width=150)

        for col in columns:
            self.context_tree.heading(col, text=col)
            self.context_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.context_tree.yview)
        self.context_tree.configure(yscrollcommand=scrollbar.set)

        self.context_tree.pack(side='left', fill='both', expand=True, padx=5)
        scrollbar.pack(side='right', fill='y')

        # Bind selection
        self.context_tree.bind('<<TreeviewSelect>>', self._on_context_select)

        # Context details
        details_frame = tk.Frame(items_frame, bg='#2d2d2d', width=400)
        details_frame.pack(side='right', fill='both', padx=5, pady=5)
        details_frame.pack_propagate(False)

        tk.Label(details_frame, text='Context Details', bg='#2d2d2d', fg='white',
                font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=5)

        self.details_text = scrolledtext.ScrolledText(details_frame, bg='#1e1e1e', fg='white',
                                                      wrap='word', font=('Courier', 9))
        self.details_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 2: Optimized Context
        optimized_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(optimized_frame, text='Optimized Context')

        # Controls
        opt_controls = tk.Frame(optimized_frame, bg='#2d2d2d')
        opt_controls.pack(side='top', fill='x', padx=5, pady=5)

        tk.Button(opt_controls, text='🔧 Generate', command=self._generate_optimized,
                 bg='#0088FE', fg='white').pack(side='left', padx=5)

        tk.Label(opt_controls, text='Include:', bg='#2d2d2d', fg='white').pack(side='left', padx=5)

        # Source checkboxes
        self.source_vars = {}
        for source in ['system', 'project', 'code', 'conversation', 'z_layer']:
            var = tk.BooleanVar(value=self.context_manager.active_sources.get(source, True))
            self.source_vars[source] = var
            tk.Checkbutton(opt_controls, text=source.title(), variable=var,
                          bg='#2d2d2d', fg='white', selectcolor='#0088FE').pack(side='left', padx=5)

        # Optimized display
        self.optimized_text = scrolledtext.ScrolledText(optimized_frame, bg='#1e1e1e', fg='white',
                                                        wrap='word', font=('Courier', 9))
        self.optimized_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 3: Settings
        settings_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(settings_frame, text='Settings')

        # Context weights
        tk.Label(settings_frame, text='Context Type Weights', bg='#2d2d2d', fg='white',
                font=('Arial', 11, 'bold')).pack(anchor='w', padx=10, pady=10)

        weights_frame = tk.Frame(settings_frame, bg='#2d2d2d')
        weights_frame.pack(fill='x', padx=20, pady=5)

        self.weight_sliders = {}
        for ctx_type, weight in self.context_manager.context_weights.items():
            frame = tk.Frame(weights_frame, bg='#2d2d2d')
            frame.pack(fill='x', pady=5)

            tk.Label(frame, text=f"{ctx_type.title()}:", bg='#2d2d2d', fg='white',
                    width=15, anchor='w').pack(side='left')

            slider = tk.Scale(frame, from_=0, to=1.0, resolution=0.1, orient='horizontal',
                            bg='#2d2d2d', fg='white', highlightthickness=0,
                            length=200, troughcolor='#0088FE')
            slider.set(weight)
            slider.pack(side='left', padx=10)

            self.weight_sliders[ctx_type] = slider

        tk.Button(settings_frame, text='Apply Weights', command=self._apply_weights,
                 bg='#00C49F', fg='white').pack(pady=10)

        # Status bar
        status_frame = tk.Frame(self, bg='#2d2d2d', height=30)
        status_frame.pack(side='bottom', fill='x')

        self.status_label = tk.Label(status_frame, text='Ready', bg='#2d2d2d',
                                     fg='#858585', font=('Arial', 9), anchor='w')
        self.status_label.pack(side='left', padx=10, fill='x', expand=True)

        self.token_count_label = tk.Label(status_frame, text='Total Tokens: 0', bg='#2d2d2d',
                                          fg='#858585', font=('Arial', 9))
        self.token_count_label.pack(side='right', padx=10)

    def _load_default_contexts(self):
        """Load default system contexts."""
        self.context_manager.gather_system_context()
        self._refresh_display()

    def _refresh_contexts(self):
        """Refresh all contexts."""
        self.status_label.config(text='Refreshing contexts...')

        # Gather system context
        self.context_manager.gather_system_context()

        # Gather project context if set
        if self.project_path:
            self.context_manager.gather_project_context(self.project_path)

        self._refresh_display()
        self.status_label.config(text='Contexts refreshed')

    def _refresh_display(self):
        """Refresh context display."""
        # Clear tree
        for item in self.context_tree.get_children():
            self.context_tree.delete(item)

        # Add contexts
        total_tokens = 0
        for ctx_id, ctx in sorted(self.context_manager.contexts.items(),
                                  key=lambda x: x[1].priority, reverse=True):
            self.context_tree.insert(
                '',
                'end',
                iid=ctx_id,
                text=ctx_id,
                values=(
                    ctx.type,
                    ctx.priority,
                    ctx.tokens,
                    ctx.source,
                    ctx.timestamp.strftime('%H:%M:%S')
                )
            )
            total_tokens += ctx.tokens

        self.token_count_label.config(text=f'Total Tokens: {total_tokens:,}')

    def _on_context_select(self, event):
        """Handle context selection."""
        selection = self.context_tree.selection()
        if not selection:
            return

        ctx_id = selection[0]
        ctx = self.context_manager.contexts.get(ctx_id)

        if ctx:
            self.details_text.delete('1.0', 'end')
            self.details_text.insert('1.0', f"ID: {ctx.id}\n")
            self.details_text.insert('end', f"Type: {ctx.type}\n")
            self.details_text.insert('end', f"Priority: {ctx.priority}\n")
            self.details_text.insert('end', f"Tokens: {ctx.tokens}\n")
            self.details_text.insert('end', f"Source: {ctx.source}\n")
            self.details_text.insert('end', f"Timestamp: {ctx.timestamp}\n")
            self.details_text.insert('end', f"\nMetadata:\n{json.dumps(ctx.metadata, indent=2)}\n")
            self.details_text.insert('end', f"\n{'='*50}\n\nContent:\n{ctx.content}")

    def _select_project(self):
        """Select project directory."""
        path = filedialog.askdirectory(title='Select Project Directory')
        if path:
            self.project_path = Path(path)
            self.context_manager.gather_project_context(self.project_path)
            self._refresh_display()
            self.status_label.config(text=f'Project: {self.project_path.name}')

    def _add_manual_context(self):
        """Add manual context item."""
        dialog = tk.Toplevel(self)
        dialog.title('Add Context')
        dialog.geometry('600x400')
        dialog.configure(bg='#2d2d2d')

        tk.Label(dialog, text='Type:', bg='#2d2d2d', fg='white').grid(row=0, column=0, padx=10, pady=5, sticky='w')
        type_combo = ttk.Combobox(dialog, values=['system', 'project', 'code', 'conversation', 'z_layer', 'custom'])
        type_combo.set('custom')
        type_combo.grid(row=0, column=1, padx=10, pady=5, sticky='ew')

        tk.Label(dialog, text='Priority (1-10):', bg='#2d2d2d', fg='white').grid(row=1, column=0, padx=10, pady=5, sticky='w')
        priority_spin = tk.Spinbox(dialog, from_=1, to=10, bg='#1e1e1e', fg='white')
        priority_spin.delete(0, 'end')
        priority_spin.insert(0, '5')
        priority_spin.grid(row=1, column=1, padx=10, pady=5, sticky='ew')

        tk.Label(dialog, text='Content:', bg='#2d2d2d', fg='white').grid(row=2, column=0, padx=10, pady=5, sticky='nw')
        content_text = scrolledtext.ScrolledText(dialog, bg='#1e1e1e', fg='white', height=15)
        content_text.grid(row=2, column=1, padx=10, pady=5, sticky='nsew')

        dialog.grid_columnconfigure(1, weight=1)
        dialog.grid_rowconfigure(2, weight=1)

        def add():
            ctx_type = type_combo.get()
            priority = int(priority_spin.get())
            content = content_text.get('1.0', 'end').strip()

            if content:
                self.context_manager.add_context(ctx_type, content, priority, source='manual')
                self._refresh_display()
                dialog.destroy()

        tk.Button(dialog, text='Add', command=add, bg='#00C49F', fg='white').grid(row=3, column=1, padx=10, pady=10, sticky='e')

    def _generate_optimized(self):
        """Generate optimized context."""
        # Update active sources
        for source, var in self.source_vars.items():
            self.context_manager.active_sources[source] = var.get()

        # Update token limit
        try:
            self.context_manager.max_tokens = int(self.token_limit_entry.get())
        except ValueError:
            pass

        # Generate optimized context
        optimized = self.context_manager.get_optimized_context()

        self.optimized_text.delete('1.0', 'end')
        self.optimized_text.insert('1.0', optimized)

        tokens = self.context_manager._estimate_tokens(optimized)
        self.status_label.config(text=f'Optimized context generated: {tokens} tokens')

    def _apply_weights(self):
        """Apply weight settings."""
        for ctx_type, slider in self.weight_sliders.items():
            self.context_manager.context_weights[ctx_type] = slider.get()

        messagebox.showinfo('Settings', 'Context weights applied')

    def _toggle_auto_update(self):
        """Toggle auto-update."""
        if self.auto_update.get():
            self.running = True
            self.update_thread = threading.Thread(target=self._auto_update_loop, daemon=True)
            self.update_thread.start()
            self.status_label.config(text='Auto-update enabled')
        else:
            self.running = False
            self.status_label.config(text='Auto-update disabled')

    def _auto_update_loop(self):
        """Auto-update loop."""
        import time
        while self.running:
            time.sleep(self.update_interval)
            if self.running:
                self.after(0, self._refresh_contexts)

    def _save_contexts(self):
        """Save contexts to file."""
        filepath = filedialog.asksaveasfilename(
            title='Save Contexts',
            defaultextension='.json',
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')]
        )

        if filepath:
            self.context_manager.save_contexts(Path(filepath))
            messagebox.showinfo('Saved', f'Contexts saved to:\n{filepath}')

    def _export_context(self):
        """Export optimized context."""
        filepath = filedialog.asksaveasfilename(
            title='Export Context',
            defaultextension='.txt',
            filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')]
        )

        if filepath:
            optimized = self.context_manager.get_optimized_context()
            Path(filepath).write_text(optimized, encoding='utf-8')
            messagebox.showinfo('Exported', f'Context exported to:\n{filepath}')


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Enhanced AI Context Manager - F1 Demo')
    root.geometry('1400x800')

    context_gui = AIContextGUI(root)
    context_gui.pack(fill='both', expand=True)

    root.mainloop()
