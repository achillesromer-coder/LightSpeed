"""
Dev Tools Portal - Glass UI Edition - V1.0.0
Development Tools & Environment Portal (consolidated into Z+1_Architect)

Note: This component originated as the standalone Z+1_Tank floor and was
consolidated to keep Z+1 reserved for Architect while preserving all tooling.

Author: LightSpeed Team
Date: December 27, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import sys
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import subprocess
import os

# Add core paths
def _find_lightspeed_root() -> Path:
    here = Path(__file__).resolve()
    for cand in (here, *here.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return here.parents[3]


PROJECT_ROOT = _find_lightspeed_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
Z_AXIS_ROOT = PROJECT_ROOT / "Z Axis"
if Z_AXIS_ROOT.exists() and str(Z_AXIS_ROOT) not in sys.path:
    sys.path.insert(0, str(Z_AXIS_ROOT))
_MEROV = Z_AXIS_ROOT / "Z-4_Merovingian"
if _MEROV.exists() and str(_MEROV) not in sys.path:
    sys.path.insert(0, str(_MEROV))

from core.ui.glass_ui import GlassUIManager, GLASS_MATERIALS, ROMER_GLASS_COLORS
from core.ui.enhanced_spherical_glass_ui import EnhancedSphericalGlassUI, AchillesBubble
from core.ui.icon_library_glass import IconLibraryManager


# ==============================================================================
# Development Environment Data Structures
# ==============================================================================

@dataclass
class DevEnvironment:
    """Development environment configuration"""
    env_id: str
    name: str
    env_type: str  # 'python', 'node', 'java', 'cpp', 'rust'
    path: Path
    active: bool
    version: str
    packages: List[str]


@dataclass
class DevTool:
    """Development tool configuration"""
    tool_id: str
    name: str
    category: str  # 'editor', 'terminal', 'debugger', 'version_control', 'testing'
    command: str
    icon: str
    color: str
    enabled: bool = True


# ==============================================================================
# Dev Tools Portal (legacy "Tank")
# ==============================================================================

class TankPortalGlass(tk.Toplevel):
    """
    Glass-themed Development Tools & Environment Portal (Z+1)

    Features:
    - Environment management (Python venv, Node.js, etc.)
    - Integrated terminal
    - Git version control interface
    - Package manager
    - Quick tool launcher
    - Code snippets library
    - 120° FOV spherical interface
    - Interactive Achilles Bubble
    """

    def __init__(self, parent=None):
        """Initialize Dev Tools portal (Architect Z+1)."""
        super().__init__(parent)

        self.title("Z+1 Architect - Development Tools & Environment")
        self.geometry("1600x1000")

        # Managers
        self.glass_ui = GlassUIManager()
        self.icon_library = IconLibraryManager()

        # State
        self.environments: Dict[str, DevEnvironment] = {}
        self.dev_tools: List[DevTool] = []
        self.terminal_processes: Dict[str, subprocess.Popen] = {}

        # Setup
        self._setup_window()
        self._load_environments()
        self._load_dev_tools()
        self._build_ui()

    def _setup_window(self):
        """Setup window"""
        self.configure(bg=ROMER_GLASS_COLORS['glass_bg'])

        # Icon
        try:
            icon = self.icon_library.get_icon('tool_workspace', 32, 'romer_premium')
            if icon:
                self.iconphoto(True, icon)
        except:
            pass

    def _load_environments(self):
        """Load development environments"""
        # Mock environments for V1.0.0
        self.environments = {
            'lightspeed_venv': DevEnvironment(
                env_id='lightspeed_venv',
                name='LightSpeed Virtual Environment',
                env_type='python',
                path=PROJECT_ROOT / '.venv',
                active=True,
                version='Python 3.11',
                packages=['tkinter', 'psutil', 'Pillow', 'PyPDF2']
            ),
            'system_python': DevEnvironment(
                env_id='system_python',
                name='System Python',
                env_type='python',
                path=Path(sys.executable).parent,
                active=False,
                version=f'Python {sys.version.split()[0]}',
                packages=[]
            ),
        }

    def _load_dev_tools(self):
        """Load development tools"""
        self.dev_tools = [
            DevTool('git', 'Git', 'version_control', 'git', 'tool_git', '#f05032'),
            DevTool('terminal', 'Terminal', 'terminal', 'cmd' if os.name == 'nt' else 'bash', 'tool_terminal', '#10b981'),
            DevTool('python', 'Python REPL', 'interpreter', 'python', 'code_python', '#3776ab'),
            DevTool('pip', 'Package Manager', 'package', 'pip', 'tool_package', '#3b82f6'),
            DevTool('editor', 'Universal Editor', 'editor', 'internal', 'tool_editor', '#8b5cf6'),
            DevTool('debugger', 'Debugger', 'debugger', 'pdb', 'tool_debug', '#ef4444'),
        ]

    def _build_ui(self):
        """Build portal UI"""
        # Main container
        main_container = tk.Frame(self, bg=ROMER_GLASS_COLORS['glass_bg'])
        main_container.pack(fill=tk.BOTH, expand=True)

        # Header
        self._create_header(main_container)

        # Content area
        content_frame = tk.Frame(main_container, bg=ROMER_GLASS_COLORS['glass_bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left panel: Environments
        left_panel = self._create_environments_panel(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        # Center: Spherical tools interface
        center_panel = self._create_center_panel(content_frame)
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # Right panel: Terminal & Output
        right_panel = self._create_terminal_panel(content_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(10, 0))

        # Footer
        self._create_footer(main_container)

    def _create_header(self, parent):
        """Create portal header"""
        header = tk.Canvas(parent, height=80, bg=ROMER_GLASS_COLORS['glass_bg'],
                          highlightthickness=0)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))

        self.glass_ui.apply_glass_effect(
            header,
            material=GLASS_MATERIALS['romer_premium'],
            rounded_corners=12,
            double_border=True
        )

        # Floor ID
        header.create_text(
            40, 25,
            text="Z+1",
            font=('Segoe UI', 24, 'bold'),
            fill='#10b981',
            anchor=tk.W
        )

        # Title
        header.create_text(
            40, 55,
            text="TANK - Development Tools & Environment",
            font=('Segoe UI', 16, 'bold'),
            fill=ROMER_GLASS_COLORS['text_primary'],
            anchor=tk.W
        )

        # Active environment indicator
        active_env = next((env for env in self.environments.values() if env.active), None)
        if active_env:
            header.create_text(
                header.winfo_reqwidth() - 200 if header.winfo_reqwidth() > 0 else 1400,
                25,
                text="Active Environment",
                font=('Segoe UI', 10),
                fill=ROMER_GLASS_COLORS['text_secondary'],
                anchor=tk.W
            )

            header.create_text(
                header.winfo_reqwidth() - 200 if header.winfo_reqwidth() > 0 else 1400,
                50,
                text=active_env.version,
                font=('Segoe UI', 14, 'bold'),
                fill='#10b981',
                anchor=tk.W
            )

    def _create_environments_panel(self, parent) -> tk.Frame:
        """Create environments management panel"""
        panel = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_bg'], width=320)

        # Panel header
        header = tk.Label(
            panel,
            text="ENVIRONMENTS",
            font=('Segoe UI', 14, 'bold'),
            fg='#10b981',
            bg=ROMER_GLASS_COLORS['glass_panel'],
            pady=10
        )
        header.pack(fill=tk.X)
        self.glass_ui.apply_glass_effect(header, material=GLASS_MATERIALS['romer_premium'])

        # Environment list
        env_container = tk.Frame(panel, bg=ROMER_GLASS_COLORS['glass_bg'])
        env_container.pack(fill=tk.BOTH, expand=True, pady=10)

        for env_id, env in self.environments.items():
            self._create_env_card(env_container, env)

        # Create new environment button
        create_btn = tk.Button(
            env_container,
            text="+ Create New Environment",
            font=('Segoe UI', 10),
            fg=ROMER_GLASS_COLORS['primary'],
            bg=ROMER_GLASS_COLORS['glass_panel'],
            relief=tk.FLAT,
            cursor='hand2',
            command=self._create_environment
        )
        create_btn.pack(fill=tk.X, padx=5, pady=(20, 5))
        self.glass_ui.apply_glass_effect(create_btn, material=GLASS_MATERIALS['romer_premium'])

        return panel

    def _create_env_card(self, parent, env: DevEnvironment):
        """Create environment card"""
        card = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_panel'])
        card.pack(fill=tk.X, padx=5, pady=5)

        self.glass_ui.apply_glass_effect(
            card,
            material=GLASS_MATERIALS['standard'],
            rounded_corners=8
        )

        content = tk.Frame(card, bg=ROMER_GLASS_COLORS['glass_panel'])
        content.pack(fill=tk.BOTH, padx=15, pady=12)

        # Name and status
        header_frame = tk.Frame(content, bg=ROMER_GLASS_COLORS['glass_panel'])
        header_frame.pack(fill=tk.X)

        tk.Label(
            header_frame,
            text=env.name,
            font=('Segoe UI', 11, 'bold'),
            fg=ROMER_GLASS_COLORS['text_primary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        ).pack(side=tk.LEFT)

        if env.active:
            tk.Label(
                header_frame,
                text="● Active",
                font=('Segoe UI', 9),
                fg='#10b981',
                bg=ROMER_GLASS_COLORS['glass_panel']
            ).pack(side=tk.RIGHT)

        # Version
        tk.Label(
            content,
            text=env.version,
            font=('Segoe UI', 9),
            fg=ROMER_GLASS_COLORS['text_secondary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        ).pack(anchor=tk.W, pady=(2, 0))

        # Path
        tk.Label(
            content,
            text=str(env.path)[:40] + "..." if len(str(env.path)) > 40 else str(env.path),
            font=('Consolas', 8),
            fg=ROMER_GLASS_COLORS['text_secondary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        ).pack(anchor=tk.W, pady=(2, 5))

        # Actions
        actions_frame = tk.Frame(content, bg=ROMER_GLASS_COLORS['glass_panel'])
        actions_frame.pack(fill=tk.X, pady=(5, 0))

        if not env.active:
            activate_btn = tk.Button(
                actions_frame,
                text="Activate",
                font=('Segoe UI', 9),
                fg=ROMER_GLASS_COLORS['primary'],
                bg=ROMER_GLASS_COLORS['glass_bg'],
                relief=tk.FLAT,
                cursor='hand2',
                command=lambda e=env: self._activate_environment(e)
            )
            activate_btn.pack(side=tk.LEFT, padx=(0, 5))

        info_btn = tk.Button(
            actions_frame,
            text="Info",
            font=('Segoe UI', 9),
            fg=ROMER_GLASS_COLORS['text_secondary'],
            bg=ROMER_GLASS_COLORS['glass_bg'],
            relief=tk.FLAT,
            cursor='hand2',
            command=lambda e=env: self._show_env_info(e)
        )
        info_btn.pack(side=tk.LEFT)

    def _create_center_panel(self, parent) -> tk.Frame:
        """Create center panel with spherical tools interface"""
        panel = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_bg'])

        # Spherical canvas
        self.spherical_ui = EnhancedSphericalGlassUI(
            panel,
            width=600,
            height=700,
            fov=120.0
        )
        self.spherical_ui.canvas.pack(fill=tk.BOTH, expand=True)

        # Achilles Bubble
        self.achilles_bubble = AchillesBubble(
            self.spherical_ui.canvas,
            radius=60,
            center_x=300,
            center_y=350
        )

        # Add development tools
        self._populate_dev_tools()

        return panel

    def _populate_dev_tools(self):
        """Populate spherical UI with development tools"""
        num_tools = len(self.dev_tools)
        angle_step = 360 / num_tools

        for i, tool in enumerate(self.dev_tools):
            if not tool.enabled:
                continue

            theta = i * angle_step
            phi = 0
            depth = 0.8

            # Create tool button
            btn = tk.Button(
                self.spherical_ui.canvas,
                text=tool.name,
                font=('Segoe UI', 11, 'bold'),
                fg=tool.color,
                bg=ROMER_GLASS_COLORS['glass_panel'],
                relief=tk.FLAT,
                padx=20,
                pady=12,
                cursor='hand2',
                command=lambda t=tool: self._launch_tool(t)
            )

            self.glass_ui.apply_glass_effect(
                btn,
                material=GLASS_MATERIALS['romer_premium']
            )

            # Add to spherical layout
            widget_id = tool.tool_id
            self.spherical_ui.add_widget(widget_id, btn, theta, phi, depth)

    def _create_terminal_panel(self, parent) -> tk.Frame:
        """Create terminal and output panel"""
        panel = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_bg'], width=420)

        # Panel header
        header = tk.Label(
            panel,
            text="TERMINAL & OUTPUT",
            font=('Segoe UI', 14, 'bold'),
            fg='#10b981',
            bg=ROMER_GLASS_COLORS['glass_panel'],
            pady=10
        )
        header.pack(fill=tk.X)
        self.glass_ui.apply_glass_effect(header, material=GLASS_MATERIALS['romer_premium'])

        # Tabs
        notebook = ttk.Notebook(panel)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Terminal tab
        terminal_frame = tk.Frame(notebook, bg=ROMER_GLASS_COLORS['glass_bg'])
        notebook.add(terminal_frame, text="Terminal")

        self.terminal_output = scrolledtext.ScrolledText(
            terminal_frame,
            font=('Consolas', 9),
            bg='#0a0e14',
            fg='#10b981',
            relief=tk.FLAT,
            wrap=tk.WORD,
            insertbackground='#10b981'
        )
        self.terminal_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))
        self.glass_ui.apply_glass_effect(self.terminal_output,
                                        material=GLASS_MATERIALS['standard'])

        # Command input
        cmd_frame = tk.Frame(terminal_frame, bg=ROMER_GLASS_COLORS['glass_panel'])
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(
            cmd_frame,
            text="$",
            font=('Consolas', 10, 'bold'),
            fg='#10b981',
            bg=ROMER_GLASS_COLORS['glass_panel']
        ).pack(side=tk.LEFT, padx=(5, 5))

        self.terminal_input = tk.Entry(
            cmd_frame,
            font=('Consolas', 10),
            bg=ROMER_GLASS_COLORS['glass_bg'],
            fg=ROMER_GLASS_COLORS['text_primary'],
            relief=tk.FLAT,
            insertbackground=ROMER_GLASS_COLORS['primary']
        )
        self.terminal_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.terminal_input.bind('<Return>', lambda e: self._execute_command())

        # Output tab
        output_frame = tk.Frame(notebook, bg=ROMER_GLASS_COLORS['glass_bg'])
        notebook.add(output_frame, text="Output")

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            font=('Consolas', 9),
            bg=ROMER_GLASS_COLORS['glass_panel'],
            fg=ROMER_GLASS_COLORS['text_primary'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            state='disabled'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.glass_ui.apply_glass_effect(self.output_text,
                                        material=GLASS_MATERIALS['standard'])

        # Snippets tab
        snippets_frame = tk.Frame(notebook, bg=ROMER_GLASS_COLORS['glass_bg'])
        notebook.add(snippets_frame, text="Snippets")

        self._create_snippets_library(snippets_frame)

        return panel

    def _create_snippets_library(self, parent):
        """Create code snippets library"""
        snippets = [
            ("Python venv", "python -m venv .venv"),
            ("Activate venv (Win)", ".venv\\Scripts\\activate"),
            ("Activate venv (Unix)", "source .venv/bin/activate"),
            ("Install requirements", "pip install -r requirements.txt"),
            ("Freeze packages", "pip freeze > requirements.txt"),
            ("Git init", "git init"),
            ("Git status", "git status"),
            ("Git add all", "git add ."),
            ("Git commit", "git commit -m \"message\""),
            ("Git push", "git push origin main"),
        ]

        for title, command in snippets:
            snippet_card = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_panel'])
            snippet_card.pack(fill=tk.X, padx=5, pady=3)

            self.glass_ui.apply_glass_effect(snippet_card,
                                            material=GLASS_MATERIALS['standard'],
                                            rounded_corners=6)

            content = tk.Frame(snippet_card, bg=ROMER_GLASS_COLORS['glass_panel'])
            content.pack(fill=tk.X, padx=10, pady=8)

            tk.Label(
                content,
                text=title,
                font=('Segoe UI', 9, 'bold'),
                fg=ROMER_GLASS_COLORS['text_primary'],
                bg=ROMER_GLASS_COLORS['glass_panel']
            ).pack(anchor=tk.W)

            cmd_label = tk.Label(
                content,
                text=command,
                font=('Consolas', 8),
                fg=ROMER_GLASS_COLORS['text_secondary'],
                bg=ROMER_GLASS_COLORS['glass_panel'],
                cursor='hand2'
            )
            cmd_label.pack(anchor=tk.W)

            # Click to copy/use
            cmd_label.bind('<Button-1>',
                          lambda e, cmd=command: self._use_snippet(cmd))

    def _create_footer(self, parent):
        """Create portal footer"""
        footer = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_panel'], height=40)
        footer.pack(fill=tk.X, padx=20, pady=(10, 20))

        self.glass_ui.apply_glass_effect(
            footer,
            material=GLASS_MATERIALS['romer_premium'],
            rounded_corners=8
        )

        # Status text
        self.status_label = tk.Label(
            footer,
            text="⚙ Development environment ready",
            font=('Segoe UI', 10),
            fg=ROMER_GLASS_COLORS['text_primary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        )
        self.status_label.pack(side=tk.LEFT, padx=15)

        # Working directory
        self.dir_label = tk.Label(
            footer,
            text=f"Working Dir: {os.getcwd()}",
            font=('Segoe UI', 9),
            fg=ROMER_GLASS_COLORS['text_secondary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        )
        self.dir_label.pack(side=tk.RIGHT, padx=15)

    def _activate_environment(self, env: DevEnvironment):
        """Activate development environment"""
        # Deactivate all others
        for e in self.environments.values():
            e.active = False

        # Activate selected
        env.active = True

        self._log_output(f"Activated environment: {env.name} ({env.version})")
        messagebox.showinfo("Environment Activated",
                          f"{env.name} is now active.\n\nVersion: {env.version}")

        # Rebuild UI to reflect changes
        self._build_ui()

    def _show_env_info(self, env: DevEnvironment):
        """Show environment information"""
        info = f"""Environment: {env.name}
Type: {env.env_type}
Version: {env.version}
Path: {env.path}
Active: {'Yes' if env.active else 'No'}
Packages: {len(env.packages)} installed
"""
        messagebox.showinfo(f"{env.name} Info", info)

    def _create_environment(self):
        """Create new environment"""
        win = tk.Toplevel(self)
        win.title("Create Environment")
        win.geometry("720x420")
        win.minsize(640, 380)

        container = ttk.Frame(win, padding=14)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="New Virtual Environment", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(
            container,
            text="Creates a Python `venv` at the selected path and registers it in Architect (Dev Tools).",
            wraplength=680,
            justify="left",
        ).pack(anchor="w", pady=(6, 12))

        form = ttk.Frame(container)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        name_var = tk.StringVar(value="LightSpeed Venv")
        path_var = tk.StringVar(value=str(PROJECT_ROOT / ".venv"))

        ttk.Label(form, text="Name").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(form, textvariable=name_var).grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Path").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(form, textvariable=path_var).grid(row=1, column=1, sticky="ew", pady=6)

        def browse():
            try:
                p = filedialog.askdirectory(parent=win, initialdir=str(PROJECT_ROOT))
                if p:
                    path_var.set(p)
            except Exception:
                return

        ttk.Button(form, text="Browse", command=browse).grid(row=1, column=2, padx=(10, 0), pady=6)

        status = tk.StringVar(value="")
        ttk.Label(container, textvariable=status, foreground="#00AA88").pack(anchor="w", pady=(10, 0))

        def create():
            import subprocess
            import sys
            env_path = Path(path_var.get()).expanduser().resolve()
            if env_path.exists() and any(env_path.iterdir()):
                if not messagebox.askyesno(
                    "Path Not Empty",
                    f"The target path already exists and is not empty:\n\n{env_path}\n\nContinue anyway?",
                    parent=win,
                ):
                    return
            try:
                env_path.parent.mkdir(parents=True, exist_ok=True)
                status.set(f"Creating venv at {env_path} ...")
                win.update_idletasks()
                subprocess.run([sys.executable, "-m", "venv", str(env_path)], check=True)
                status.set("Environment created.")
                # Record environment (basic)
                try:
                    env = DevEnvironment(
                        env_id=f"env_{int(datetime.now().timestamp())}",
                        name=name_var.get().strip() or "Environment",
                        env_type="venv",
                        version="python",
                        path=str(env_path),
                        active=False,
                        packages=[],
                    )
                    self.environments[env.env_id] = env
                    self._build_ui()
                except Exception:
                    pass
                messagebox.showinfo("Environment Created", f"Created: {env_path}", parent=win)
                win.destroy()
            except Exception as e:
                messagebox.showerror("Create Failed", str(e), parent=win)

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(14, 0))
        ttk.Button(actions, text="Create", command=create).pack(side="left")
        ttk.Button(actions, text="Cancel", command=win.destroy).pack(side="right")

    def _launch_tool(self, tool: DevTool):
        """Launch development tool"""
        self._log_output(f"Launching {tool.name}...")

        if tool.command == 'internal':
            # Internal tools
            if tool.tool_id == 'editor':
                self._open_universal_editor()
        else:
            # External command
            if tool.tool_id == 'terminal':
                self._open_terminal()
            elif tool.tool_id == 'python':
                self._open_python_repl()
            else:
                self._execute_tool_command(tool.command)

    def _execute_command(self):
        """Execute terminal command"""
        command = self.terminal_input.get().strip()
        if not command:
            return

        # Add to terminal
        self.terminal_output.insert(tk.END, f"$ {command}\n", 'command')
        self.terminal_input.delete(0, tk.END)

        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Show output
            if result.stdout:
                self.terminal_output.insert(tk.END, result.stdout, 'output')
            if result.stderr:
                self.terminal_output.insert(tk.END, result.stderr, 'error')

            self.terminal_output.insert(tk.END, "\n")
            self.terminal_output.see(tk.END)

        except subprocess.TimeoutExpired:
            self.terminal_output.insert(tk.END, "Command timed out\n", 'error')
        except Exception as e:
            self.terminal_output.insert(tk.END, f"Error: {e}\n", 'error')

        # Configure tags
        self.terminal_output.tag_config('command', foreground='#10b981')
        self.terminal_output.tag_config('output', foreground='#e0f7fa')
        self.terminal_output.tag_config('error', foreground='#ef4444')

    def _use_snippet(self, command: str):
        """Use code snippet"""
        self.terminal_input.delete(0, tk.END)
        self.terminal_input.insert(0, command)
        self.terminal_input.focus_set()

    def _log_output(self, message: str):
        """Log to output panel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.output_text.config(state='normal')
        self.output_text.insert('1.0', log_entry)
        self.output_text.config(state='disabled')

    def _open_universal_editor(self):
        """Open Universal Editor"""
        try:
            from core.universal_editor.universal_editor import UniversalEditor

            editor_window = tk.Toplevel(self)
            editor_window.title("Universal Editor")
            editor_window.geometry("1200x800")

            editor = UniversalEditor(editor_window)
            editor.pack(fill=tk.BOTH, expand=True)

            self._log_output("Opened Universal Editor")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open editor: {e}")

    def _open_terminal(self):
        """Open system terminal"""
        try:
            if os.name == 'nt':
                subprocess.Popen(['cmd.exe'], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(['x-terminal-emulator'])

            self._log_output("Opened system terminal")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open terminal: {e}")

    def _open_python_repl(self):
        """Open Python REPL"""
        self.terminal_output.insert(tk.END, f"Python {sys.version}\n", 'output')
        self.terminal_output.insert(tk.END, "Type Python commands below:\n\n", 'output')
        self._log_output("Started Python REPL mode")

    def _execute_tool_command(self, command: str):
        """Execute tool command"""
        self.terminal_input.delete(0, tk.END)
        self.terminal_input.insert(0, f"{command} --help")
        self._execute_command()


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Launch Dev Tools portal (legacy entrypoint name retained)"""
    root = tk.Tk()
    root.withdraw()

    app = TankPortalGlass()
    app.mainloop()


# Backwards/forwards compatible alias used by manifests/launchers
DevToolsPortalGlass = TankPortalGlass


if __name__ == "__main__":
    main()
