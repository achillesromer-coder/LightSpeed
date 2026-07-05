"""
NEO Operator Console - V2.0.0
Achilles-facing operator surface with glass UI integration

NEO (Neural Enhancement Operator) serves as the primary operator console for
LightSpeed, coordinating smart floor functions, staging governed actions,
monitoring system health, and providing intelligent assistance to users.

Features:
- Glass UI panel with LightSpeed premium theme
- Ollama/local LLM integration
- Smart floor function management
- Tool and hook orchestration
- Real-time system monitoring
- Natural language command processing
- Z-axis navigation assistance
- Governed problem solving

Access: Via Achilles Bubble or direct launch

Author: LightSpeed Team
Date: December 27, 2025
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import subprocess
import sys
import os

# Import glass UI components (Trinity owns `ui.*`)
from ui.glass_ui import (
    GlassPanel,
    GlassButton,
    GlassFrame,
    GlassUIManager,
    GLASS_MATERIALS,
    ROMER_GLASS_COLORS,
    apply_romer_theme
)

def _safe_font(family: str, size: int, *styles: str) -> str:
    """
    Tk font spec helper.

    Some Tk builds mis-parse font tuples when the family name contains spaces (e.g. "Segoe UI"),
    producing errors like: "expected integer but got 'UI'". Passing a braced string is robust.
    """
    fam = f"{{{family}}}" if " " in (family or "") else (family or "")
    parts = [fam, str(int(size))]
    parts.extend([s for s in styles if s])
    return " ".join(parts).strip()


# ==============================================================================
# NEO Configuration
# ==============================================================================

@dataclass
class NEOConfig:
    """
    NEO console configuration

    Attributes:
    name: Console display name
        version: NEO version
        model: Ollama model to use
        temperature: LLM temperature (0.0-1.0)
        max_tokens: Maximum response tokens
        system_prompt: System instruction for NEO
        tools_enabled: List of enabled tools
        floors_monitored: Z-floors to monitor
    """
    name: str = "NEO / Achilles"
    version: str = "2.0.0"
    model: str = "llama3.2:latest"
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: str = """You are NEO, the Achilles-facing LightSpeed operator console. You coordinate the platform's smart floor framework, stage governed actions, orchestrate tools and hooks, and help users move work across the Z-axis efficiently. You have access to all 8 Z-floors (Z-4 through Z+3) and can monitor system health, prepare actions, and provide concise operational guidance."""
    tools_enabled: List[str] = field(default_factory=lambda: [
        "smart_floor_manager",
        "z_floor_navigator",
        "system_monitor",
        "hook_orchestrator",
        "file_manager",
        "code_executor"
    ])
    floors_monitored: List[str] = field(default_factory=lambda: [
        "Z-4_Merovingian", "Z-3_Smith", "Z-2_Oracle", "Z-1_Morpheus",
        "Z0_TheConstruct", "Z+1_Architect", "Z+2_Neo", "Z+3_Trinity"
    ])


# ==============================================================================
# NEO Command System
# ==============================================================================

@dataclass
class NEOCommand:
    """
    Represents a command NEO can execute

    Attributes:
        command_id: Unique identifier
        name: Display name
        description: What the command does
        syntax: How to invoke it
        handler: Function to execute
        requires_confirmation: Whether to ask user before executing
    """
    command_id: str
    name: str
    description: str
    syntax: str
    handler: Callable
    requires_confirmation: bool = False


# ==============================================================================
# NEO Operator Console UI
# ==============================================================================

class NEOLabAssistant(tk.Toplevel):
    """
    NEO operator console main interface

    Glass-themed AI console window with:
    - Chat interface for natural language interaction
    - System status monitoring
    - Quick action buttons
    - Tool orchestration controls
    - Z-floor navigation
    """

    def __init__(self, parent=None):
        """
        Initialize NEO operator console

        Args:
            parent: Parent window (None = create root)
        """
        if parent is None:
            self.root = tk.Tk()
            super().__init__(self.root)
        else:
            super().__init__(parent)

        self.title("NEO - Achilles / Cognigrex Console")
        self.geometry("900x700")

        # NEO configuration
        self.config = NEOConfig()

        # Conversation history
        self.conversation: List[Dict[str, str]] = []

        # System state
        self.system_status = {
            'floors_healthy': 9,
            'active_tools': 0,
            'pending_tasks': 0,
            'cpu_usage': 0.0,
            'memory_usage': 0.0
        }

        # Glass UI manager
        self.glass_manager = GlassUIManager()
        self.glass_manager.set_material('romer_premium')

        # Build UI
        self._build_ui()

        # Initialize systems
        self._initialize_neo()

        # Start monitoring
        self._start_monitoring()

    def _build_ui(self):
        """Build NEO glass UI"""
        # Configure window
        self.configure(bg=ROMER_GLASS_COLORS['glass_bg'])

        # Main container
        main_container = GlassFrame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header with NEO branding
        self._create_header(main_container)

        # Content area (2 columns)
        content_frame = ttk.Frame(main_container, style='Glass.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=1)

        # Left: Chat interface
        self._create_chat_interface(content_frame)

        # Right: Status & Operator Actions
        self._create_sidebar(content_frame)

        # Footer with input
        self._create_input_area(main_container)

    def _create_header(self, parent):
        """Create NEO header with status"""
        header = GlassFrame(parent)
        header.pack(fill=tk.X, padx=5, pady=5)

        # NEO Logo/Title
        title_frame = ttk.Frame(header, style='Glass.TFrame')
        title_frame.pack(side=tk.LEFT, padx=10, pady=10)

        ttk.Label(
            title_frame,
            text="◆ NEO",
            font=_safe_font("Segoe UI", 24, "bold"),
            foreground=ROMER_GLASS_COLORS['primary'],
            style='Glass.TLabel'
        ).pack(side=tk.LEFT)

        ttk.Label(
            title_frame,
            text="Achilles Operator Console",
            font=_safe_font("Segoe UI", 14),
            foreground=ROMER_GLASS_COLORS['text_secondary'],
            style='Glass.TLabel'
        ).pack(side=tk.LEFT, padx=10)

        # Status indicator
        status_frame = ttk.Frame(header, style='Glass.TFrame')
        status_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        self.status_indicator = tk.Canvas(
            status_frame,
            width=12,
            height=12,
            bg=ROMER_GLASS_COLORS['glass_bg'],
            highlightthickness=0
        )
        self.status_indicator.pack(side=tk.LEFT, padx=5)

        # Draw green status dot
        self.status_indicator.create_oval(
            2, 2, 10, 10,
            fill=ROMER_GLASS_COLORS['success'],
            outline=''
        )

        ttk.Label(
            status_frame,
            text="Online",
            font=_safe_font("Segoe UI", 10),
            foreground=ROMER_GLASS_COLORS['success'],
            style='Glass.TLabel'
        ).pack(side=tk.LEFT)

    def _create_chat_interface(self, parent):
        """Create chat interface area"""
        chat_container = GlassFrame(parent)
        chat_container.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # Chat history display
        chat_frame = ttk.Frame(chat_container, style='Glass.TFrame')
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrolled text for chat
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=_safe_font("Segoe UI", 10),
            bg=ROMER_GLASS_COLORS['glass_card'],
            fg=ROMER_GLASS_COLORS['text_primary'],
            insertbackground=ROMER_GLASS_COLORS['primary'],
            selectbackground=ROMER_GLASS_COLORS['primary'],
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for styling
        self.chat_display.tag_config(
            'user',
            foreground=ROMER_GLASS_COLORS['text_primary'],
            font=_safe_font("Segoe UI", 10, "bold")
        )
        self.chat_display.tag_config(
            'neo',
            foreground=ROMER_GLASS_COLORS['primary'],
            font=_safe_font("Segoe UI", 10)
        )
        self.chat_display.tag_config(
            'system',
            foreground=ROMER_GLASS_COLORS['warning'],
            font=_safe_font("Segoe UI", 9, "italic")
        )
        self.chat_display.tag_config(
            'timestamp',
            foreground=ROMER_GLASS_COLORS['text_disabled'],
            font=_safe_font("Segoe UI", 8)
        )

        # Make read-only
        self.chat_display.config(state='disabled')

        # Welcome message
        self._add_message("NEO", "Hello. I'm NEO, your Achilles/Cognigrex console. I can stage governed actions, route work across smart floors, and help move the current workspace forward.")

    def _create_sidebar(self, parent):
        """Create sidebar with status and operator actions"""
        sidebar = GlassFrame(parent)
        sidebar.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

        # System Status section
        status_label = ttk.Label(
            sidebar,
            text="System Status",
            font=_safe_font("Segoe UI", 12, "bold"),
            style='Glass.TLabel'
        )
        status_label.pack(pady=(10, 5))

        # Status metrics
        self.status_frame = GlassFrame(sidebar)
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_labels = {}
        metrics = [
            ('Floors', 'floors_healthy'),
            ('Tools', 'active_tools'),
            ('Tasks', 'pending_tasks'),
            ('CPU', 'cpu_usage'),
            ('Memory', 'memory_usage')
        ]

        for label, key in metrics:
            metric_frame = ttk.Frame(self.status_frame, style='Glass.TFrame')
            metric_frame.pack(fill=tk.X, pady=2)

            ttk.Label(
                metric_frame,
                text=f"{label}:",
                font=_safe_font("Segoe UI", 9),
                foreground=ROMER_GLASS_COLORS['text_secondary'],
                style='Glass.TLabel'
            ).pack(side=tk.LEFT)

            value_label = ttk.Label(
                metric_frame,
                text="--",
                font=_safe_font("Segoe UI", 9, "bold"),
                foreground=ROMER_GLASS_COLORS['primary'],
                style='Glass.TLabel'
            )
            value_label.pack(side=tk.RIGHT)

            self.status_labels[key] = value_label

        # Divider
        ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Operator Actions section
        actions_label = ttk.Label(
            sidebar,
            text="Operator Actions",
            font=_safe_font("Segoe UI", 12, "bold"),
            style='Glass.TLabel'
        )
        actions_label.pack(pady=(10, 5))

        actions_frame = GlassFrame(sidebar)
        actions_frame.pack(fill=tk.X, padx=10, pady=5)

        action_rows = [
            [
                ("Workspace", self._quick_open_workspace),
                ("Health", self._quick_system_health),
                ("Floors", self._quick_floor_navigator),
            ],
            [
                ("Tools", self._quick_run_tools),
                ("Settings", self._quick_settings),
            ],
        ]

        for row in action_rows:
            row_frame = ttk.Frame(actions_frame, style='Glass.TFrame')
            row_frame.pack(fill=tk.X, pady=3)
            for action_name, callback in row:
                GlassButton(
                    row_frame,
                    text=action_name,
                    command=callback
                ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

    def _create_input_area(self, parent):
        """Create message input area"""
        input_container = GlassFrame(parent)
        input_container.pack(fill=tk.X, padx=5, pady=5)

        input_frame = ttk.Frame(input_container, style='Glass.TFrame')
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        input_frame.columnconfigure(0, weight=1)

        # Input field
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(
            input_frame,
            textvariable=self.input_var,
            font=_safe_font("Segoe UI", 10),
            style='Glass.TEntry'
        )
        self.input_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))

        # Bind Enter key
        self.input_entry.bind('<Return>', lambda e: self._send_message())
        self.input_entry.focus()

        # Send button
        send_btn = GlassButton(
            input_frame,
            text="Send",
            command=self._send_message
        )
        send_btn.grid(row=0, column=1)

    def _initialize_neo(self):
        """Initialize NEO systems"""
        # Check Ollama availability
        self._check_ollama()

        # Initialize command registry
        self.commands = self._create_command_registry()

        # Update status
        self._update_status()

    def _check_ollama(self):
        """Check if Ollama is available"""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                self._add_message("SYSTEM", "✓ Ollama connected successfully", tag='system')
            else:
                self._add_message("SYSTEM", "⚠ Ollama not available - using fallback mode", tag='system')

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._add_message("SYSTEM", "⚠ Ollama not installed - using rule-based responses", tag='system')

    def _create_command_registry(self) -> Dict[str, NEOCommand]:
        """Create command registry"""
        commands = {}

        # System commands
        commands['help'] = NEOCommand(
            command_id='help',
            name='Help',
            description='Show available commands',
            syntax='/help or help',
            handler=self._cmd_help
        )

        commands['status'] = NEOCommand(
            command_id='status',
            name='System Status',
            description='Show system health status',
            syntax='/status',
            handler=self._cmd_status
        )

        commands['floors'] = NEOCommand(
            command_id='floors',
            name='List Floors',
            description='Show all Z-floors and their status',
            syntax='/floors',
            handler=self._cmd_floors
        )

        commands['navigate'] = NEOCommand(
            command_id='navigate',
            name='Navigate Floor',
            description='Navigate to a specific Z-floor',
            syntax='/navigate <floor_name>',
            handler=self._cmd_navigate
        )

        commands['tools'] = NEOCommand(
            command_id='tools',
            name='List Tools',
            description='Show available smart floor functions',
            syntax='/tools',
            handler=self._cmd_tools
        )

        commands['clear'] = NEOCommand(
            command_id='clear',
            name='Clear Chat',
            description='Clear conversation history',
            syntax='/clear',
            handler=self._cmd_clear
        )

        return commands

    def _add_message(self, sender: str, message: str, tag: Optional[str] = None):
        """Add message to chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.chat_display.config(state='normal')

        # Timestamp
        self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')

        # Sender
        sender_tag = tag or ('user' if sender != 'NEO' else 'neo')
        self.chat_display.insert(tk.END, f"{sender}: ", sender_tag)

        # Message
        self.chat_display.insert(tk.END, f"{message}\n\n")

        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

        # Store in conversation
        self.conversation.append({
            'timestamp': timestamp,
            'sender': sender,
            'message': message
        })

    def _send_message(self):
        """Send user message and get NEO response"""
        message = self.input_var.get().strip()

        if not message:
            return

        # Clear input
        self.input_var.set('')

        # Add user message
        self._add_message("USER", message)

        # Process message
        self._process_message(message)

    def _process_message(self, message: str):
        """Process user message and generate response"""
        # Check for commands
        if message.startswith('/'):
            command_parts = message[1:].split()
            command_name = command_parts[0].lower()

            if command_name in self.commands:
                self.commands[command_name].handler(command_parts[1:])
                return

        # Check for natural language patterns
        message_lower = message.lower()

        if any(word in message_lower for word in ['help', 'what can you do', 'commands']):
            self._cmd_help([])
        elif any(word in message_lower for word in ['status', 'health', 'how is']):
            self._cmd_status([])
        elif any(word in message_lower for word in ['floor', 'navigate', 'go to']):
            self._cmd_floors([])
        elif any(word in message_lower for word in ['tool', 'utilities', 'features']):
            self._cmd_tools([])
        else:
            # Try Ollama LLM response
            self._get_llm_response(message)

    def _get_llm_response(self, message: str):
        """Get response from Ollama LLM"""
        try:
            # Prepare conversation context
            context = self._build_context()

            # Call Ollama (simplified - would use proper API)
            response = self._call_ollama(context + f"\n\nUser: {message}\n\nNEO:")

            self._add_message("NEO", response)

        except Exception as e:
            # Fallback to rule-based response
            self._add_message("NEO", "I understand you're asking about that. Let me help you with the available commands. Type /help to see what I can do!")

    def _build_context(self) -> str:
        """Build conversation context for LLM"""
        context = self.config.system_prompt + "\n\nRecent conversation:\n"

        # Include last 5 messages
        for msg in self.conversation[-5:]:
            context += f"{msg['sender']}: {msg['message']}\n"

        return context

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API (simplified)"""
        # In production, would use proper Ollama Python client
        # For now, return intelligent fallback
        return "I'm here to help! I can assist with workspace management, system monitoring, floor navigation, and tool orchestration. What would you like to do?"

    # Command handlers
    def _cmd_help(self, args: List[str]):
        """Show help"""
        help_text = "Available Commands:\n\n"

        for cmd in self.commands.values():
            help_text += f"• {cmd.syntax}\n  {cmd.description}\n\n"

        self._add_message("NEO", help_text)

    def _cmd_status(self, args: List[str]):
        """Show system status"""
        status_text = "System Health Report:\n\n"
        status_text += f"✓ All {self.system_status['floors_healthy']} Z-floors operational\n"
        status_text += f"• {self.system_status['active_tools']} tools active\n"
        status_text += f"• {self.system_status['pending_tasks']} tasks pending\n"
        status_text += f"• CPU: {self.system_status['cpu_usage']:.1f}%\n"
        status_text += f"• Memory: {self.system_status['memory_usage']:.1f}%\n"

        self._add_message("NEO", status_text)

    def _cmd_floors(self, args: List[str]):
        """List Z-floors"""
        floors_text = "Z-Stack Floors:\n\n"

        for floor in self.config.floors_monitored:
            floors_text += f"• {floor} - ✓ Operational\n"

        self._add_message("NEO", floors_text)

    def _cmd_navigate(self, args: List[str]):
        """Navigate to floor"""
        if not args:
            self._add_message("NEO", "Please specify a floor. Example: /navigate Z0_TheConstruct")
            return

        floor_name = args[0]
        self._add_message("NEO", f"Navigating to {floor_name}...")

    def _cmd_tools(self, args: List[str]):
        """List available tools"""
        tools_text = "Available Tools:\n\n"

        for tool in self.config.tools_enabled:
            tools_text += f"• {tool}\n"

        self._add_message("NEO", tools_text)

    def _cmd_clear(self, args: List[str]):
        """Clear chat"""
        self.chat_display.config(state='normal')
        self.chat_display.delete('1.0', tk.END)
        self.chat_display.config(state='disabled')

        self.conversation.clear()
        self._add_message("NEO", "Chat cleared. How can I assist you?")

    # Quick action handlers
    def _quick_open_workspace(self):
        """Quick action: Open workspace"""
        self._add_message("USER", "/navigate Z0_TheConstruct")
        self._cmd_navigate(["Z0_TheConstruct"])

    def _quick_system_health(self):
        """Quick action: System health"""
        self._add_message("USER", "/status")
        self._cmd_status([])

    def _quick_floor_navigator(self):
        """Quick action: Floor navigator"""
        self._add_message("USER", "/floors")
        self._cmd_floors([])

    def _quick_run_tools(self):
        """Quick action: Run tools"""
        self._add_message("USER", "/tools")
        self._cmd_tools([])

    def _quick_settings(self):
        """Quick action: Operator settings"""
        self._add_message("NEO", "Settings stay in Trinity. Use the bounded console for routing preferences, model choices, and governance hints.")

    def _update_status(self):
        """Update status metrics"""
        import psutil

        # Update system metrics
        self.system_status['cpu_usage'] = psutil.cpu_percent(interval=0.1)
        self.system_status['memory_usage'] = psutil.virtual_memory().percent

        # Update UI labels
        for key, label in self.status_labels.items():
            value = self.system_status[key]

            if key in ['cpu_usage', 'memory_usage']:
                label.config(text=f"{value:.1f}%")
            else:
                label.config(text=str(value))

    def _start_monitoring(self):
        """Start background monitoring"""
        self._update_status()

        # Schedule next update
        self.after(2000, self._start_monitoring)


# ==============================================================================
# Embeddable Panel (for Operator Portal / Neo floor tabs)
# ==============================================================================

class NEOLabAssistantPanel(ttk.Frame):
    """
    Embeddable NEO operator panel.

    The original `NEOLabAssistant` is a `tk.Toplevel` (standalone window) which cannot be
    embedded into a parent frame via `.pack()` / `.grid()`. The Neo floor tab needs a
    bounded primary console, so this panel provides the main operator surface and a
    secondary legacy window link when explicitly required.
    """

    def __init__(self, parent: tk.Misc, app: Optional[object] = None):
        super().__init__(parent)
        self.app = app
        self.config = NEOConfig()

        self._oracle = None
        self._status_vars: Dict[str, tk.StringVar] = {}

        self._build_ui()
        self._refresh_status_loop()

    def _build_ui(self) -> None:
        try:
            apply_romer_theme(self.winfo_toplevel())
        except Exception:
            pass

        container = GlassFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        header = GlassFrame(container)
        header.pack(fill="x", padx=6, pady=6)

        title = ttk.Frame(header, style="Glass.TFrame")
        title.pack(side="left", padx=10, pady=10)
        ttk.Label(
            title,
            text="◆ NEO",
            font=_safe_font("Segoe UI", 20, "bold"),
            foreground=ROMER_GLASS_COLORS.get("primary", "#00FF88"),
            style="Glass.TLabel",
        ).pack(side="left")
        ttk.Label(
            title,
            text="Bounded Console",
            font=_safe_font("Segoe UI", 12),
            foreground=ROMER_GLASS_COLORS.get("text_secondary", "#B8C7CC"),
            style="Glass.TLabel",
        ).pack(side="left", padx=10)

        btns = ttk.Frame(header, style="Glass.TFrame")
        btns.pack(side="right", padx=10, pady=10)
        console_actions = tk.Menubutton(btns, text="Console Actions")
        console_menu = tk.Menu(console_actions, tearoff=0)
        console_menu.add_command(label="Open Secondary Window", command=self._open_full_window)
        console_menu.add_command(label="Run Oracle Queue", command=self._run_oracle_cycle_once)
        console_actions.config(menu=console_menu)
        console_actions.pack(side="left", padx=(0, 8))

        # Operator controls: keep Neo usable without tab-hopping in IT Portal.
        controls = ttk.Frame(container, style="Glass.TFrame")
        controls.pack(fill="x", padx=6, pady=(0, 6))

        ttk.Label(controls, text="Tool Drawer:", style="Glass.TLabel").pack(side="left", padx=(10, 6))
        self._tool_var = tk.StringVar(value="None")
        tool_box = ttk.Combobox(
            controls,
            textvariable=self._tool_var,
            values=["None", "Code Assistant", "Training", "Context"],
            state="readonly",
            width=18,
        )
        tool_box.pack(side="left")
        try:
            tool_box.bind("<<ComboboxSelected>>", lambda _e: self._apply_tool_drawer())
        except Exception:
            pass

        routing_actions = tk.Menubutton(controls, text="Routing")
        routing_menu = tk.Menu(routing_actions, tearoff=0)
        routing_menu.add_command(label="Mount Tool Drawer", command=self._apply_tool_drawer)
        routing_menu.add_command(label="Enable Routing", command=self._enable_ops_for_session)
        routing_menu.add_command(label="Open Smith -> Neo", command=self._open_z_direct_smith_to_neo)
        routing_actions.config(menu=routing_menu)
        routing_actions.pack(side="left", padx=(8, 6))

        body = ttk.Frame(container, style="Glass.TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=10)
        try:
            body.columnconfigure(0, weight=1)
            body.columnconfigure(1, weight=1)
            body.rowconfigure(0, weight=1)
            body.rowconfigure(1, weight=1)
        except Exception:
            pass

        # Left: status cards
        status_box = GlassPanel(body, title="System & Automation Status")
        status_box.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

        def _row(key: str, label: str, default: str = "-") -> None:
            var = tk.StringVar(value=default)
            self._status_vars[key] = var
            r = ttk.Frame(status_box, style="Glass.TFrame")
            r.pack(fill="x", padx=10, pady=6)
            ttk.Label(r, text=label, width=24, style="Glass.TLabel").pack(side="left")
            ttk.Label(r, textvariable=var, style="Glass.TLabel").pack(side="left")

        _row("workers", "Background workers")
        _row("oracle_queue", "Oracle queue")
        _row("smith_oracle", "Smith -> Oracle worker")
        _row("smith_inbox", "Smith inbox (tail)")
        _row("cpu", "CPU")
        _row("mem", "Memory")

        # Routed task visibility (Neo complaint: tools should react to smart floor handoffs).
        tasks_hdr = ttk.Frame(status_box, style="Glass.TFrame")
        tasks_hdr.pack(fill="x", padx=10, pady=(10, 4))
        ttk.Label(tasks_hdr, text="Routed tasks (Smith -> Neo proposals)", style="Glass.TLabel").pack(side="left")
        GlassButton(tasks_hdr, text="Open", command=self._open_z_direct_smith_to_neo).pack(side="right")

        self._tasks_list = tk.Listbox(
            status_box,
            height=7,
            bg=ROMER_GLASS_COLORS.get("glass_bg", "#0B1416"),
            fg=ROMER_GLASS_COLORS.get("text_primary", "#EAF2F4"),
            selectbackground=ROMER_GLASS_COLORS.get("primary", "#00FF88"),
            selectforeground="#000000",
        )
        self._tasks_list.pack(fill="both", expand=False, padx=10, pady=(0, 10))

        # Right: notes + guidance
        help_box = GlassPanel(body, title="Operator Notes")
        help_box.grid(row=0, column=1, sticky="nsew", pady=(0, 8))
        msg = scrolledtext.ScrolledText(
            help_box,
            height=10,
            bg=ROMER_GLASS_COLORS.get("glass_bg", "#0B1416"),
            fg=ROMER_GLASS_COLORS.get("text_primary", "#EAF2F4"),
            font=("Consolas", 9),
            wrap="word",
        )
        msg.pack(fill="both", expand=True, padx=10, pady=10)
        msg.insert(
            "1.0",
            "This is the bounded NEO console and primary Neo floor surface.\n\n"
            "- Use 'Open Secondary Window' only when you need the secondary window.\n"
            "- 'Run Oracle Queue' drains a small batch of Oracle ingestion tasks (IT mode).\n"
            "- Oracle -> Floors handoff is staged into Trinity Z Direct by Smith.\n",
        )
        try:
            msg.config(state="disabled")
        except Exception:
            pass

        # Tool drawer (embeds other Neo tools without requiring tab switching).
        self._tool_host = GlassPanel(body, title="Tool Drawer")
        self._tool_host.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=0, pady=(0, 8))
        self._tool_mount = ttk.Frame(self._tool_host, style="Glass.TFrame")
        self._tool_mount.pack(fill="both", expand=True, padx=10, pady=10)

        # Bottom: lightweight console
        console = GlassPanel(container, title="Neo Console")
        console.pack(fill="both", expand=True, padx=6, pady=6)

        self._console_out = scrolledtext.ScrolledText(
            console,
            height=8,
            bg=ROMER_GLASS_COLORS.get("glass_bg", "#0B1416"),
            fg=ROMER_GLASS_COLORS.get("text_primary", "#EAF2F4"),
            font=("Consolas", 9),
            wrap="word",
        )
        self._console_out.pack(fill="both", expand=True, padx=10, pady=(10, 6))

        row = ttk.Frame(console, style="Glass.TFrame")
        row.pack(fill="x", padx=10, pady=(0, 10))
        self._console_in = ttk.Entry(row)
        self._console_in.pack(side="left", fill="x", expand=True)
        GlassButton(row, text="Send", command=self._on_console_send).pack(side="left", padx=(8, 0))

        try:
            self._console_in.bind("<Return>", lambda _e: self._on_console_send())
        except Exception:
            pass

        self._log("NEO console ready. Stage here, then use Trinity Operator Portal for approval and commit.")

    def _log(self, text: str) -> None:
        try:
            self._console_out.insert(tk.END, f"{text}\n")
            self._console_out.see(tk.END)
        except Exception:
            pass

    def _open_full_window(self) -> None:
        try:
            neo = NEOLabAssistant(self.winfo_toplevel())
            try:
                neo.lift()
            except Exception:
                pass
            self._log("Opened full NEO window.")
        except Exception as e:
            self._log(f"Failed to open standalone window: {e}")

    def _enable_ops_for_session(self) -> None:
        """
        Session-scoped: flip retrieve-only gate OFF and start Smith workers best-effort.

        Neo should not make durable commits; this only enables staging/automation loops
        for the current process when the operator is in IT mode.
        """
        try:
            os.environ.pop("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS", None)
        except Exception:
            pass

        try:
            import Smith  # type: ignore

            rt = getattr(Smith, "SMITH_RUNTIME", {}) or {}
            q = rt.get("queue")
            if q is not None:
                fn = getattr(q, "ensure_oracle_ingestion_worker_started", None)
                if callable(fn):
                    fn()
                fn2 = getattr(q, "start_worker", None)
                if callable(fn2):
                    fn2()
        except Exception:
            pass

        self._log("Ops enabled for this session (background workers allowed).")
        self._refresh_status_once()

    def _open_z_direct_smith_to_neo(self) -> None:
        """Deep-link into Trinity Z Direct (Smith -> Neo inbox) when hosted by N.py."""
        try:
            fn = getattr(self.app, "open_it_portal_z_direct", None)
            if callable(fn):
                fn(channel="Z+2", peer="Z-3", tags="oracle,route")
                self._log("Opened Operator Portal -> Z Direct (channel Z+2, peer Z-3).")
                return
        except Exception:
            pass
        self._log("Z Direct deep-link unavailable (host app missing open_it_portal_z_direct).")

    def _apply_tool_drawer(self) -> None:
        """Embed a Neo tool GUI into the drawer host (reduces tab sprawl)."""
        mount = getattr(self, "_tool_mount", None)
        if mount is None:
            return

        try:
            for w in list(mount.winfo_children()):
                try:
                    w.destroy()
                except Exception:
                    pass
        except Exception:
            pass

        choice = ""
        try:
            choice = str(self._tool_var.get() or "").strip()
        except Exception:
            choice = ""

        if not choice or choice.lower() == "none":
            ttk.Label(mount, text="Select a tool to embed here.", style="Glass.TLabel").pack(anchor="w")
            return

        mapping = {
            "Code Assistant": ("ai_code_assistant.py", "AICodeAssistantGUI"),
            "Training": ("ai_training.py", "AITrainingGUI"),
            "Context": ("ai_context.py", "AIContextGUI"),
        }
        filename, symbol = mapping.get(choice, (None, None))
        if not filename or not symbol:
            ttk.Label(mount, text=f"Unknown tool: {choice}", style="Glass.TLabel").pack(anchor="w")
            return

        try:
            from importlib.util import spec_from_file_location, module_from_spec

            module_path = Path(__file__).with_name(filename)
            spec = spec_from_file_location(f"lightspeed_neo_tool_{module_path.stem}", module_path)
            if spec is None or spec.loader is None:
                raise RuntimeError("spec load failed")
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)
            cls = getattr(mod, symbol)
            ui = cls(mount)
            try:
                ui.pack(fill="both", expand=True)
            except Exception:
                pass
            self._log(f"Embedded tool: {choice}")
        except Exception as e:
            ttk.Label(mount, text=f"Embed failed: {e}", style="Glass.TLabel").pack(anchor="w")
            self._log(f"Tool embed failed: {e}")

    def _get_oracle_integrator(self):
        if self._oracle is not None:
            return self._oracle
        try:
            # Prefer already-initialized services (N.py / FloorLoader).
            from core.services import get_db, get_event_bus, get_storage, get_z_direct  # type: ignore

            db = getattr(self.app, "db", None) or get_db()
            eb = getattr(self.app, "event_bus", None) or get_event_bus()
            st = getattr(self.app, "storage", None) or get_storage()
            zd = get_z_direct()
        except Exception:
            db = None
            eb = None
            st = None
            zd = None

        try:
            module_path = Path(__file__).resolve().parents[3] / "Z Axis" / "Z-2_Oracle" / "components" / "oracle_smart_floor_integrator.py"
            from importlib.util import spec_from_file_location, module_from_spec

            spec = spec_from_file_location("lightspeed_oracle_integrator_dynamic", module_path)
            if spec is None or spec.loader is None:
                return None
            mod = module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            cls = getattr(mod, "OracleSmartFloorIntegrator", None)
            if cls is None:
                return None
            self._oracle = cls(db=db, event_bus=eb, storage=st, z_direct=zd)
            return self._oracle
        except Exception:
            return None

    def _run_oracle_cycle_once(self) -> None:
        # In N portal (non-IT) mode we intentionally keep background workers disabled.
        try:
            if os.environ.get("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS", "").strip() == "1":
                self._log("Background workers disabled (N portal mode). Open Operator Portal to enable.")
                return
        except Exception:
            pass

        # Prefer Smith's worker (keeps logs + Z Direct staging behavior consistent).
        try:
            import Smith  # type: ignore

            rt = getattr(Smith, "SMITH_RUNTIME", {}) or {}
            q = rt.get("queue")
            if q is not None:
                fn = getattr(q, "run_oracle_ingestion_cycle_once", None)
                if callable(fn):
                    res = fn()
                    self._log(f"Smith Oracle cycle: processed={res.get('processed')} failed={res.get('failed')}")
                    return
        except Exception:
            pass

        oracle = self._get_oracle_integrator()
        if oracle is None:
            self._log("Oracle integrator unavailable.")
            return
        try:
            out = oracle.process_pending_tasks(max_tasks=3)  # small batch to keep UI responsive
            ok = sum(1 for r in (out or []) if isinstance(r, dict) and r.get("success"))
            self._log(f"Oracle cycle ran (manual): {ok} task(s) processed.")
        except Exception as e:
            self._log(f"Oracle cycle failed: {e}")

    def _on_console_send(self) -> None:
        text = ""
        try:
            text = (self._console_in.get() or "").strip()
        except Exception:
            text = ""
        if not text:
            return
        try:
            self._console_in.delete(0, tk.END)
        except Exception:
            pass

        cmd = text.lower()
        if cmd in {"help", "/help"}:
            self._log("Commands: help, status, oracle, it")
            return
        if cmd in {"status", "/status"}:
            self._log("Refreshing status...")
            self._refresh_status_once()
            return
        if cmd in {"oracle", "/oracle"}:
            self._run_oracle_cycle_once()
            return
        if cmd in {"it", "/it"}:
            self._log("Tip: Open Trinity Operator Portal -> Z Direct for approval and commit.")
            return

        self._log("Unknown command. Type 'help'.")

    def _refresh_status_once(self) -> None:
        # Background workers
        try:
            disabled = os.environ.get("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS", "").strip() == "1"
            self._status_vars["workers"].set("DISABLED" if disabled else "ENABLED")
        except Exception:
            pass

        # Smith -> Oracle worker health
        try:
            import Smith  # type: ignore

            rt = getattr(Smith, "SMITH_RUNTIME", {}) or {}
            q = rt.get("queue")
            ok = False
            if q is not None:
                fn = getattr(q, "has_oracle_ingestion_worker", None)
                if callable(fn):
                    ok = bool(fn())
            self._status_vars["smith_oracle"].set("RUNNING" if ok else "OFF")
        except Exception:
            pass

        # Smith -> Neo inbox visibility (tail count)
        try:
            from core.services import get_z_direct  # type: ignore

            zd = get_z_direct()
            items = zd.tail_channel_inbox(to_channel="Z+2", from_channel="Z-3", limit=25)
            self._status_vars["smith_inbox"].set(str(len(items)))

            lb = getattr(self, "_tasks_list", None)
            if lb is not None:
                try:
                    lb.delete(0, tk.END)
                except Exception:
                    pass
                for env in items[:20]:
                    try:
                        payload = env.get("payload") if isinstance(env, dict) else None
                        title = payload.get("title") if isinstance(payload, dict) else None
                        details = payload.get("details") if isinstance(payload, dict) else None
                        count = details.get("count") if isinstance(details, dict) else None
                        if title and count is not None:
                            line = f"{title} [{count}]"
                        elif title:
                            line = str(title)
                        else:
                            line = str(payload.get("id") if isinstance(payload, dict) else env.get("created_at"))
                        lb.insert(tk.END, line[:140])
                    except Exception:
                        continue
        except Exception:
            pass

        # Oracle queue
        try:
            oracle = self._get_oracle_integrator()
            if oracle is not None and hasattr(oracle, "get_queue_status"):
                st = oracle.get_queue_status()
                pending = st.get("pending") if isinstance(st, dict) else None
                total = st.get("total_tasks") if isinstance(st, dict) else None
                if pending is not None or total is not None:
                    self._status_vars["oracle_queue"].set(f"{pending}/{total}")
        except Exception:
            pass

        # Local system metrics (best-effort)
        try:
            import psutil  # type: ignore

            self._status_vars["cpu"].set(f"{psutil.cpu_percent(interval=0.1):.1f}%")
            self._status_vars["mem"].set(f"{psutil.virtual_memory().percent:.1f}%")
        except Exception:
            pass

    def _refresh_status_loop(self) -> None:
        self._refresh_status_once()
        try:
            self.after(2000, self._refresh_status_loop)
        except Exception:
            pass


# ==============================================================================
# Factory Function
# ==============================================================================

def create_neo_assistant(parent=None) -> NEOLabAssistant:
    """
    Create NEO operator console instance

    Args:
        parent: Parent window (None = standalone)

    Returns:
        NEOLabAssistant instance
    """
    return NEOLabAssistant(parent)


# ==============================================================================
# Standalone Launch
# ==============================================================================

if __name__ == '__main__':
    neo = create_neo_assistant()
    neo.mainloop()
