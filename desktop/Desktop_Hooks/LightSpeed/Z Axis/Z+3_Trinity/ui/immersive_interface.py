#!/usr/bin/env python
"""
LightSpeed Immersive Interface - Unified GUI Integration
Combines all UI elements into cohesive immersive experience:
- Spherical 360° Z-floor navigation
- Glass UI overlays and HUD
- Floor transition animations
- Neo AI assistant panel
- Encyclopedia quick-access
- Task queue visualization
- Smart floor expansion panels

Author: LightSpeed Team / Romer Industries
Version: 5.1.2
Date: April 8, 2026
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional, Callable
from datetime import datetime
from pathlib import Path
import sys

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from glass_theme_manager import GlassTheme, HUDOverlay, GlassPanel, FloorTransition, SmartFloorPanel
from spherical_projection import SphericalProjection, SphericalFloorLayout


class ImmersiveInterface(tk.Frame):
    """
    Unified Immersive Interface for LightSpeed Platform

    Stacks UI elements in layers:
    - Layer 0 (Background): Main content area
    - Layer 1 (Mid): Spherical Z-floor navigation
    - Layer 2 (Foreground): Floor-specific content
    - Layer 3 (Overlay): HUD, notifications, panels
    - Layer 4 (Modal): Dialogs, AI assistant, encyclopedia
    """

    def __init__(self, parent, db=None, event_bus=None, logger=None):
        """Initialize immersive interface"""
        super().__init__(parent, bg=GlassTheme.BG_DARKEST)

        self.parent = parent
        self.db = db
        self.event_bus = event_bus
        self.logger = logger

        # Current state
        self.current_floor = 'Z0_TheConstruct'
        self.floor_data = {}
        self.panels = {}
        self.overlays = {}

        # Configure window
        self.pack(fill='both', expand=True)

        # Create layered UI
        self._create_layers()
        self._create_spherical_nav()
        self._create_hud()
        self._create_side_panels()
        self._create_modals()

        # Bind keyboard shortcuts
        self._setup_shortcuts()

        # Initial state
        self._navigate_to_floor('Z0_TheConstruct')

        if self.logger:
            self.logger.info("[ImmersiveUI] Immersive interface initialized")

    def _create_layers(self):
        """Create layered canvas system"""
        # Layer 0: Background
        self.layer_background = tk.Frame(self, bg=GlassTheme.BG_DARKEST)
        self.layer_background.place(x=0, y=0, relwidth=1, relheight=1)

        # Layer 1: Spherical navigation canvas
        self.layer_spherical = tk.Canvas(self.layer_background,
                                        bg=GlassTheme.BG_DARKEST,
                                        highlightthickness=0)
        self.layer_spherical.place(x=0, y=0, relwidth=1, relheight=1)

        # Layer 2: Floor content area
        self.layer_content = tk.Frame(self, bg='black')  # Transparent in real implementation
        self.layer_content.place(x=250, y=120, width=900, height=650)

        # Layer 3: HUD overlay (transparent canvas)
        self.layer_hud = tk.Canvas(self, bg=GlassTheme.BG_DARKEST, highlightthickness=0)
        self.layer_hud.place(x=0, y=0, relwidth=1, relheight=1)

        # Layer 4: Modal layer (hidden by default)
        self.layer_modal = tk.Frame(self, bg=GlassTheme.BG_DARKEST)
        self.layer_modal.place_forget()  # Hidden initially

    def _create_spherical_nav(self):
        """Create spherical 360° navigation"""
        # Initialize spherical projection on spherical layer canvas
        self.spherical = SphericalProjection(
            canvas=self.layer_spherical,
            radius=300,
            center=(700, 450)  # Center of screen
        )

        # Setup Z-floor positions
        SphericalFloorLayout.setup_floor_projection(self.spherical)

        # Bind click events for floor navigation
        self.layer_spherical.bind('<Button-1>', self._on_spherical_click)

        # Initial render
        self.spherical.render()

        # Auto-rotate demo (can be disabled)
        self._auto_rotate_spherical()

    def _auto_rotate_spherical(self):
        """Auto-rotate spherical view (subtle continuous rotation)"""
        # Rotate 0.5° per second
        self.spherical.rotate(0.2, 0)

        # Schedule next rotation
        self.after(100, self._auto_rotate_spherical)

    def _on_spherical_click(self, event):
        """Handle click on spherical navigation"""
        # Check if clicked on a floor element
        # (Simplified - real implementation would use element hit detection)
        clicked_items = self.layer_spherical.find_overlapping(
            event.x - 10, event.y - 10,
            event.x + 10, event.y + 10
        )

        if clicked_items:
            # Determine which floor was clicked (simplified)
            # In real implementation, would map click to floor based on spherical projection
            floors = list(SphericalFloorLayout.FLOOR_POSITIONS.keys())

            # For demo, cycle through floors on any click
            current_idx = floors.index(self.current_floor) if self.current_floor in floors else 0
            next_floor = floors[(current_idx + 1) % len(floors)]

            self._navigate_to_floor(next_floor)

    def _create_hud(self):
        """Create heads-up display overlay"""
        # HUD overlay on hud layer
        self.hud = HUDOverlay(self.layer_hud, width=1400, height=900)
        self.hud.pack(fill='both', expand=True)

        # Update HUD with current status
        self.hud.update_floor(self.current_floor, 'OPERATIONAL')
        self.hud.update_status('18/18', 0)

        # Bind HUD navigation clicks
        floor_to_zid = {
            "Trinity": "Z+3_Trinity",
            "Neo": "Z+2_Neo",
            "Architect": "Z+1_Architect",
            "TheConstruct": "Z0_TheConstruct",
            "Morpheus": "Z-1_Morpheus",
            "Oracle": "Z-2_Oracle",
            "Smith": "Z-3_Smith",
            "Merovingian": "Z-4_Merovingian",
        }
        for item_id, txt_id, floor in self.hud.nav_items:
            zid = floor_to_zid.get(floor)
            if not zid:
                continue
            self.hud.tag_bind(
                f"nav_btn_{floor}",
                "<Button-1>",
                lambda e, f=zid: self._navigate_to_floor(f),
            )

    def _create_side_panels(self):
        """Create collapsible side panels"""
        # Right side: Encyclopedia quick-access
        self.encyclopedia_panel = self._create_encyclopedia_panel()

        # Bottom: Task queue visualization
        self.task_queue_panel = self._create_task_queue_panel()

    def _create_encyclopedia_panel(self):
        """Create encyclopedia quick-access panel"""
        panel = GlassPanel(self, width=300, height=600, title='Encyclopedia')
        panel.place(x=1070, y=120)

        # Search box
        search_frame = tk.Frame(panel.content, bg=GlassTheme.BG_PANEL)
        search_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(search_frame, text='Search:',
                bg=GlassTheme.BG_PANEL, fg=GlassTheme.TEXT_CYAN,
                font=(GlassTheme.FONT_FAMILY, 9)).pack(side='left')

        search_entry = tk.Entry(search_frame,
                               bg=GlassTheme.BG_HOVER, fg=GlassTheme.TEXT_WHITE,
                               font=(GlassTheme.FONT_FAMILY, 9),
                               insertbackground=GlassTheme.ACCENT_CYAN)
        search_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Volume tabs
        volume_frame = tk.Frame(panel.content, bg=GlassTheme.BG_PANEL)
        volume_frame.pack(fill='x', padx=10, pady=5)

        for vol in ['Empirical', 'Economic', 'Applied']:
            tk.Button(volume_frame, text=vol,
                     bg=GlassTheme.BG_HOVER, fg=GlassTheme.TEXT_CYAN,
                     font=(GlassTheme.FONT_FAMILY, 8),
                     relief='flat',
                     command=lambda v=vol: self._switch_encyclopedia_volume(v)
                     ).pack(side='left', padx=2)

        # Entries list
        entries_frame = tk.Frame(panel.content, bg=GlassTheme.BG_PANEL)
        entries_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Scrollbar
        scrollbar = tk.Scrollbar(entries_frame, bg=GlassTheme.BG_HOVER)
        scrollbar.pack(side='right', fill='y')

        # Listbox
        self.encyclopedia_list = tk.Listbox(entries_frame,
                                           bg=GlassTheme.BG_HOVER,
                                           fg=GlassTheme.TEXT_WHITE,
                                           font=(GlassTheme.FONT_FAMILY, 9),
                                           selectbackground=GlassTheme.ACCENT_CYAN,
                                           selectforeground=GlassTheme.BG_DARKEST,
                                           yscrollcommand=scrollbar.set)
        self.encyclopedia_list.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.encyclopedia_list.yview)

        # Populate with sample entries
        sample_entries = [
            'Speed of Light',
            'Planck Constant',
            'Gravitational Constant',
            'Boltzmann Constant',
            'Avogadro Constant',
            'Fine Structure Constant'
        ]
        for entry in sample_entries:
            self.encyclopedia_list.insert(tk.END, entry)

        return panel

    def _create_task_queue_panel(self):
        """Create task queue visualization panel"""
        panel = GlassPanel(self, width=600, height=200, title='Task Queue - Smith Coordinator')
        panel.place(x=30, y=670)

        # Task stats
        stats_frame = tk.Frame(panel.content, bg=GlassTheme.BG_PANEL)
        stats_frame.pack(fill='x', padx=10, pady=5)

        stats = [
            ('Total:', '0', GlassTheme.TEXT_CYAN),
            ('Pending:', '0', GlassTheme.TEXT_YELLOW),
            ('Active:', '0', GlassTheme.SUCCESS_GREEN),
            ('Completed:', '0', GlassTheme.TEXT_GRAY)
        ]

        for label, value, color in stats:
            stat_frame = tk.Frame(stats_frame, bg=GlassTheme.BG_PANEL)
            stat_frame.pack(side='left', padx=10)

            tk.Label(stat_frame, text=label,
                    bg=GlassTheme.BG_PANEL, fg=GlassTheme.TEXT_GRAY,
                    font=(GlassTheme.FONT_FAMILY, 8)).pack(side='left')

            tk.Label(stat_frame, text=value,
                    bg=GlassTheme.BG_PANEL, fg=color,
                    font=(GlassTheme.FONT_FAMILY, 10, 'bold')).pack(side='left', padx=3)

        # Task list (horizontal progress bar style)
        tasks_canvas = tk.Canvas(panel.content, bg=GlassTheme.BG_HOVER,
                                height=100, highlightthickness=0)
        tasks_canvas.pack(fill='both', expand=True, padx=10, pady=10)

        # Sample task visualization
        tasks_canvas.create_text(
            300, 50,
            text='No active tasks',
            fill=GlassTheme.TEXT_GRAY,
            font=(GlassTheme.FONT_FAMILY, 10)
        )

        return panel

    def _create_modals(self):
        """Create modal dialogs (hidden initially)"""
        # Neo AI Assistant modal
        self.neo_assistant_modal = self._create_neo_assistant()

        # Encyclopedia detail modal
        self.encyclopedia_detail_modal = self._create_encyclopedia_detail()

    def _create_neo_assistant(self):
        """Create Neo AI assistant modal"""
        modal = tk.Frame(self.layer_modal, bg=GlassTheme.BG_PANEL,
                        highlightbackground=GlassTheme.ACCENT_MAGENTA,
                        highlightthickness=3)

        # Title bar
        title_bar = tk.Frame(modal, bg=GlassTheme.BG_DARK, height=50)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='NEO AI ASSISTANT',
                bg=GlassTheme.BG_DARK, fg=GlassTheme.ACCENT_MAGENTA,
                font=(GlassTheme.FONT_FAMILY, 14, 'bold')).pack(side='left', padx=20)

        close_btn = tk.Button(title_bar, text='✕',
                             bg=GlassTheme.BG_DARK, fg=GlassTheme.ERROR_RED,
                             font=(GlassTheme.FONT_FAMILY, 16, 'bold'),
                             relief='flat',
                             command=self._hide_neo_assistant)
        close_btn.pack(side='right', padx=10)

        # Chat area
        chat_frame = tk.Frame(modal, bg=GlassTheme.BG_PANEL)
        chat_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Scrollable chat history
        chat_scroll = tk.Scrollbar(chat_frame)
        chat_scroll.pack(side='right', fill='y')

        self.neo_chat_display = tk.Text(chat_frame,
                                        bg=GlassTheme.BG_HOVER,
                                        fg=GlassTheme.TEXT_WHITE,
                                        font=(GlassTheme.FONT_FAMILY, 10),
                                        wrap='word',
                                        yscrollcommand=chat_scroll.set,
                                        state='disabled')
        self.neo_chat_display.pack(side='left', fill='both', expand=True)
        chat_scroll.config(command=self.neo_chat_display.yview)

        # Input area
        input_frame = tk.Frame(modal, bg=GlassTheme.BG_PANEL, height=60)
        input_frame.pack(fill='x', padx=20, pady=(0, 20))
        input_frame.pack_propagate(False)

        self.neo_input = tk.Entry(input_frame,
                                 bg=GlassTheme.BG_HOVER, fg=GlassTheme.TEXT_WHITE,
                                 font=(GlassTheme.FONT_FAMILY, 11),
                                 insertbackground=GlassTheme.ACCENT_CYAN)
        self.neo_input.pack(side='left', fill='both', expand=True, padx=(0, 10), pady=10)

        send_btn = tk.Button(input_frame, text='Send',
                            bg=GlassTheme.ACCENT_MAGENTA, fg=GlassTheme.BG_DARKEST,
                            font=(GlassTheme.FONT_FAMILY, 10, 'bold'),
                            relief='flat', width=10,
                            command=self._send_neo_message)
        send_btn.pack(side='right', pady=10)

        return modal

    def _create_encyclopedia_detail(self):
        """Create encyclopedia detail modal"""
        modal = tk.Frame(self.layer_modal, bg=GlassTheme.BG_PANEL,
                        highlightbackground=GlassTheme.ACCENT_CYAN,
                        highlightthickness=3)

        # Title bar
        title_bar = tk.Frame(modal, bg=GlassTheme.BG_DARK, height=50)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        self.encyclopedia_detail_title = tk.Label(title_bar, text='ENCYCLOPEDIA ENTRY',
                                                 bg=GlassTheme.BG_DARK, fg=GlassTheme.ACCENT_CYAN,
                                                 font=(GlassTheme.FONT_FAMILY, 14, 'bold'))
        self.encyclopedia_detail_title.pack(side='left', padx=20)

        close_btn = tk.Button(title_bar, text='✕',
                             bg=GlassTheme.BG_DARK, fg=GlassTheme.ERROR_RED,
                             font=(GlassTheme.FONT_FAMILY, 16, 'bold'),
                             relief='flat',
                             command=self._hide_encyclopedia_detail)
        close_btn.pack(side='right', padx=10)

        # Content
        content_frame = tk.Frame(modal, bg=GlassTheme.BG_PANEL)
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Definition
        self.encyclopedia_detail_text = tk.Text(content_frame,
                                               bg=GlassTheme.BG_HOVER,
                                               fg=GlassTheme.TEXT_WHITE,
                                               font=(GlassTheme.FONT_FAMILY, 11),
                                               wrap='word',
                                               height=15,
                                               state='disabled')
        self.encyclopedia_detail_text.pack(fill='both', expand=True)

        return modal

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Neo assistant: Ctrl+N
        self.parent.bind('<Control-n>', lambda e: self._show_neo_assistant())

        # Encyclopedia: Ctrl+E
        self.parent.bind('<Control-e>', lambda e: self._toggle_encyclopedia())

        # Floor navigation: F1-F8
        floor_keys = [
            ('<F1>', 'Z+3_Trinity'),
            ('<F2>', 'Z+2_Neo'),
            ('<F3>', 'Z+1_Architect'),
            ('<F4>', 'Z0_TheConstruct'),
            ('<F5>', 'Z-1_Morpheus'),
            ('<F6>', 'Z-2_Oracle'),
            ('<F7>', 'Z-3_Smith'),
            ('<F8>', 'Z-4_Merovingian')
        ]

        for key, floor in floor_keys:
            self.parent.bind(key, lambda e, f=floor: self._navigate_to_floor(f))

    def _navigate_to_floor(self, floor_name: str):
        """Navigate to specific Z-floor"""
        # Update current floor
        self.current_floor = floor_name

        # Update HUD
        self.hud.update_floor(floor_name, 'OPERATIONAL')
        self.hud.add_notification(f'Navigated to {floor_name}', 'info')

        # Update floor content area (load floor-specific content)
        self._load_floor_content(floor_name)

        # Optional: Trigger transition animation
        # (Simplified - real implementation would use FloorTransition)

        if self.logger:
            self.logger.info(f"[ImmersiveUI] Navigated to {floor_name}")

    def _load_floor_content(self, floor_name: str):
        """Load floor-specific content"""
        # Clear current content
        for widget in self.layer_content.winfo_children():
            widget.destroy()

        # Create floor content (placeholder - would load actual floor UI)
        floor_panel = GlassPanel(self.layer_content, width=880, height=630,
                                title=f'{floor_name} - Floor Control')
        floor_panel.pack(fill='both', expand=True)

        # Floor-specific widgets (simplified)
        tk.Label(floor_panel.content, text=f'Welcome to {floor_name}',
                bg=GlassTheme.BG_PANEL, fg=GlassTheme.ACCENT_CYAN,
                font=(GlassTheme.FONT_FAMILY, 16, 'bold')).pack(pady=20)

        # Floor capabilities
        capabilities_text = f"Floor capabilities: knowledge, analysis, coordination"
        tk.Label(floor_panel.content, text=capabilities_text,
                bg=GlassTheme.BG_PANEL, fg=GlassTheme.TEXT_GRAY,
                font=(GlassTheme.FONT_FAMILY, 10)).pack(pady=10)

        # Quick actions
        actions_frame = tk.Frame(floor_panel.content, bg=GlassTheme.BG_PANEL)
        actions_frame.pack(pady=20)

        actions = ['View Tasks', 'Browse Files', 'Open Tools', 'Settings']
        for action in actions:
            tk.Button(actions_frame, text=action,
                     bg=GlassTheme.BG_HOVER, fg=GlassTheme.ACCENT_CYAN,
                     font=(GlassTheme.FONT_FAMILY, 10),
                     relief='flat', width=15, height=2,
                     command=lambda a=action: self._floor_action(a)
                     ).pack(pady=5)

    def _floor_action(self, action: str):
        """Handle floor-specific action"""
        self.hud.add_notification(f'Action: {action}', 'info')

    def _show_neo_assistant(self):
        """Show Neo AI assistant modal"""
        self.layer_modal.place(x=0, y=0, relwidth=1, relheight=1)
        self.neo_assistant_modal.place(relx=0.5, rely=0.5, anchor='center',
                                      width=800, height=600)

        # Add welcome message
        self._add_neo_message('NEO', 'Hello! I am Neo, your AI assistant. How can I help you today?')

        self.neo_input.focus()

    def _hide_neo_assistant(self):
        """Hide Neo AI assistant modal"""
        self.neo_assistant_modal.place_forget()
        self.layer_modal.place_forget()

    def _send_neo_message(self):
        """Send message to Neo AI"""
        message = self.neo_input.get().strip()
        if not message:
            return

        # Add user message
        self._add_neo_message('YOU', message)

        # Clear input
        self.neo_input.delete(0, tk.END)

        # Simulate AI response (would integrate with actual AI)
        self.after(1000, lambda: self._add_neo_message('NEO',
                   f'I received your message: "{message}". This is a demo response. '
                   f'In production, this would connect to Ollama/GPT.'))

    def _add_neo_message(self, sender: str, message: str):
        """Add message to Neo chat display"""
        self.neo_chat_display.config(state='normal')

        color = GlassTheme.ACCENT_MAGENTA if sender == 'NEO' else GlassTheme.ACCENT_CYAN
        timestamp = datetime.now().strftime('%H:%M')

        self.neo_chat_display.insert(tk.END, f'[{timestamp}] {sender}:\n', 'sender')
        self.neo_chat_display.insert(tk.END, f'{message}\n\n', 'message')

        self.neo_chat_display.tag_config('sender', foreground=color, font=(GlassTheme.FONT_FAMILY, 9, 'bold'))
        self.neo_chat_display.tag_config('message', foreground=GlassTheme.TEXT_WHITE)

        self.neo_chat_display.config(state='disabled')
        self.neo_chat_display.see(tk.END)

    def _toggle_encyclopedia(self):
        """Toggle encyclopedia panel visibility"""
        if self.encyclopedia_panel.winfo_viewable():
            self.encyclopedia_panel.place_forget()
        else:
            self.encyclopedia_panel.place(x=1070, y=120)

    def _switch_encyclopedia_volume(self, volume: str):
        """Switch encyclopedia volume"""
        self.hud.add_notification(f'Switched to {volume} volume', 'info')
        # Would load entries from selected volume

    def _show_encyclopedia_detail(self):
        """Show encyclopedia detail modal"""
        self.layer_modal.place(x=0, y=0, relwidth=1, relheight=1)
        self.encyclopedia_detail_modal.place(relx=0.5, rely=0.5, anchor='center',
                                            width=700, height=500)

    def _hide_encyclopedia_detail(self):
        """Hide encyclopedia detail modal"""
        self.encyclopedia_detail_modal.place_forget()
        self.layer_modal.place_forget()


# Standalone test
if __name__ == '__main__':
    root = tk.Tk()
    root.title("LightSpeed 5.1.2 - Immersive Interface")
    root.geometry("1400x900")
    root.configure(bg=GlassTheme.BG_DARKEST)

    # Configure TTK style
    GlassTheme.configure_ttk_style()

    # Create immersive interface
    interface = ImmersiveInterface(root)

    # Instructions
    print("\n" + "="*70)
    print("LIGHTSPEED IMMERSIVE INTERFACE - DEMO")
    print("="*70)
    print("\nKeyboard Shortcuts:")
    print("  Ctrl+N      : Open Neo AI Assistant")
    print("  Ctrl+E      : Toggle Encyclopedia Panel")
    print("  F1-F8       : Navigate to Z-floors (F1=Trinity, F4=TheConstruct, etc.)")
    print("  Click HUD   : Click floor names in left navigation")
    print("  Click Sphere: Click spherical navigation (center)")
    print("\n" + "="*70)

    root.mainloop()
