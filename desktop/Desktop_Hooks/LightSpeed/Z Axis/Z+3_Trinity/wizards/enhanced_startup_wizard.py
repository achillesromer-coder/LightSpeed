#!/usr/bin/env python
"""
Enhanced Startup Wizard - Complete First-Run Experience
All facets, tailorables, smart scene setup, and wizard hub

This is the master startup wizard that provides:
- Complete first-run configuration
- All platform facets and customizations
- Smart scene setup and templates
- Access to all specialized wizards
- User profile creation
- Platform initialization

Author: LightSpeed Team / ACHILLES
Version: 0.9.11+
Date: January 4, 2026
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

# Setup paths
LIGHTSPEED_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(LIGHTSPEED_ROOT))

try:
    from core.config.paths import (
        TRINITY_SETTINGS, MEROVINGIAN_ROOT, NEO_ROOT,
        CONSTRUCT_ROOT, ORACLE_ROOT
    )
    HAS_PATHS = True
except ImportError:
    print("[WARNING] Path configuration not available")
    HAS_PATHS = False
    TRINITY_SETTINGS = LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "settings"
    MEROVINGIAN_ROOT = LIGHTSPEED_ROOT / "Z Axis" / "Z-4_Merovingian"

# Ensure directories exist
TRINITY_SETTINGS.mkdir(parents=True, exist_ok=True)
MEROVINGIAN_ROOT.mkdir(parents=True, exist_ok=True)


class EnhancedStartupWizard:
    """
    Enhanced Startup Wizard - Complete First-Run Experience

    Provides comprehensive platform initialization including:
    - User profile setup
    - All platform facets configuration
    - Smart scene templates
    - Tailorable preferences
    - Wizard hub access
    - Complete platform initialization
    """

    # Color scheme
    COLORS = {
        'bg': '#0A1628',
        'header': '#102040',
        'card': '#1E3A5F',
        'card_hover': '#2A5A8F',
        'accent': '#00FFFF',
        'text': '#FFFFFF',
        'text_dim': '#AAAAAA',
        'success': '#00FF00',
        'warning': '#FFAA00',
        'error': '#FF0000',
        'neo': '#FF0080',
        'morpheus': '#0080FF',
        'architect': '#00FF80',
        'construct': '#FFFF00',
        'oracle': '#FF8000',
        'smith': '#FF0000',
        'merovingian': '#8000FF',
        'trinity': '#00FFFF'
    }

    # Smart scene templates
    SCENE_TEMPLATES = [
        {
            'id': 'data_science',
            'name': 'Data Science Workspace',
            'description': 'Python environments, Jupyter notebooks, data visualization tools',
            'floors': ['Z+2_Neo', 'Z+1_Architect', 'Z0_TheConstruct', 'Z-2_Oracle'],
            'components': ['venv_python', 'jupyter', 'pandas_viz', 'ml_tools'],
            'color': '#0080FF'
        },
        {
            'id': 'web_dev',
            'name': 'Web Development',
            'description': 'Frontend/backend tools, live preview, component library',
            'floors': ['Z+1_Architect', 'Z0_TheConstruct', 'Z-3_Smith'],
            'components': ['node_venv', 'react_tools', 'api_designer', 'live_preview'],
            'color': '#00FF80'
        },
        {
            'id': 'creative',
            'name': 'Creative Studio',
            'description': '3D visualization, image processing, animation tools',
            'floors': ['Z0_TheConstruct', 'Z-2_Oracle', 'Z+1_Architect'],
            'components': ['blender_integration', 'image_tools', 'video_editor', '3d_viewer'],
            'color': '#FF8000'
        },
        {
            'id': 'research',
            'name': 'Research Lab',
            'description': 'Documentation, knowledge management, AI research tools',
            'floors': ['Z+2_Neo', 'Z-1_Morpheus', 'Z-2_Oracle'],
            'components': ['ai_research', 'doc_manager', 'citation_tools', 'paper_analyzer'],
            'color': '#8000FF'
        },
        {
            'id': 'custom',
            'name': 'Custom Setup',
            'description': 'Manually configure all components',
            'floors': [],
            'components': [],
            'color': '#AAAAAA'
        }
    ]

    def __init__(self, parent: Optional[tk.Tk] = None):
        """Initialize startup wizard"""
        self.parent = parent
        self.dialog = None
        self.current_page = 0

        # User configuration
        self.user_config = self._load_user_config()

        # Temporary storage for wizard data
        self.wizard_data = {
            'user_name': '',
            'user_email': '',
            'workspace_path': str(LIGHTSPEED_ROOT),
            'selected_scene': 'custom',
            'enabled_floors': [],
            'custom_preferences': {},
            'ai_settings': {},
            'ui_preferences': {},
            'advanced_settings': {}
        }

        # Wizard pages
        self.pages = [
            ("Welcome", self._create_welcome_page),
            ("User Profile", self._create_profile_page),
            ("Scene Selection", self._create_scene_page),
            ("Floor Configuration", self._create_floors_page),
            ("UI Preferences", self._create_ui_prefs_page),
            ("AI Configuration", self._create_ai_config_page),
            ("Advanced Settings", self._create_advanced_page),
            ("Tailorables", self._create_tailorables_page),
            ("Wizard Hub", self._create_wizard_hub_page),
            ("Initialization", self._create_init_page),
            ("Complete", self._create_complete_page)
        ]

    def _load_user_config(self) -> Dict[str, Any]:
        """Load existing user configuration"""
        config_file = MEROVINGIAN_ROOT / "user_profile.json"

        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[STARTUP] Failed to load user config: {e}")

        return {
            'first_run': True,
            'created_at': None,
            'last_updated': None
        }

    def _save_user_config(self):
        """Save user configuration"""
        config_file = MEROVINGIAN_ROOT / "user_profile.json"

        # Merge wizard data with user config
        self.user_config.update({
            'first_run': False,
            'last_updated': datetime.now().isoformat(),
            **self.wizard_data
        })

        if self.user_config.get('created_at') is None:
            self.user_config['created_at'] = datetime.now().isoformat()

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_config, f, indent=2)
            print(f"[STARTUP] User config saved to {config_file}")
        except Exception as e:
            print(f"[STARTUP] Failed to save user config: {e}")

    def open_wizard(self):
        """Open startup wizard"""
        # Create dialog
        if self.parent:
            self.dialog = tk.Toplevel(self.parent)
        else:
            self.dialog = tk.Tk()

        self.dialog.title("LightSpeed Startup Wizard - Complete Platform Setup")
        self.dialog.geometry("1100x750")
        self.dialog.configure(bg=self.COLORS['bg'])

        # Center window
        self._center_window()

        # Create main layout
        self._create_layout()

        # Show first page
        self._show_page(0)

        # Make modal if has parent
        if self.parent:
            self.dialog.transient(self.parent)
            self.dialog.grab_set()

        self.dialog.mainloop()

    def _center_window(self):
        """Center window on screen"""
        self.dialog.update_idletasks()
        width = 1100
        height = 750
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')

    def _create_layout(self):
        """Create main wizard layout"""
        # Header
        header = tk.Frame(self.dialog, bg=self.COLORS['header'], height=90)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="LightSpeed Platform",
            font=('Segoe UI', 22, 'bold'),
            bg=self.COLORS['header'],
            fg=self.COLORS['accent']
        ).pack(pady=(12, 5))

        self.subtitle_label = tk.Label(
            header,
            text="Enhanced Startup Wizard",
            font=('Segoe UI', 12),
            bg=self.COLORS['header'],
            fg=self.COLORS['text_dim']
        )
        self.subtitle_label.pack()

        # Progress bar
        progress_frame = tk.Frame(self.dialog, bg=self.COLORS['bg'], height=45)
        progress_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)
        progress_frame.pack_propagate(False)

        self.progress = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=1060
        )
        self.progress.pack(fill=tk.X, pady=5)

        # Content area
        self.content_frame = tk.Frame(self.dialog, bg=self.COLORS['bg'])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Navigation buttons
        nav_frame = tk.Frame(self.dialog, bg=self.COLORS['bg'], height=65)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=12)
        nav_frame.pack_propagate(False)

        self.prev_btn = tk.Button(
            nav_frame,
            text="← Previous",
            command=self._prev_page,
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 11),
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor='hand2'
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.skip_btn = tk.Button(
            nav_frame,
            text="Skip Setup",
            command=self._skip_wizard,
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim'],
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        self.skip_btn.pack(side=tk.LEFT, padx=20)

        self.next_btn = tk.Button(
            nav_frame,
            text="Next →",
            command=self._next_page,
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor='hand2'
        )
        self.next_btn.pack(side=tk.RIGHT, padx=5)

        # Page indicator
        self.page_label = tk.Label(
            nav_frame,
            text="Step 1 of 11",
            font=('Segoe UI', 10),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        )
        self.page_label.pack(side=tk.RIGHT, padx=20)

    def _show_page(self, page_index: int):
        """Show specific page"""
        if page_index < 0 or page_index >= len(self.pages):
            return

        self.current_page = page_index

        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Update header
        page_title, page_func = self.pages[page_index]
        self.subtitle_label.config(text=page_title)

        # Update progress
        progress_value = ((page_index + 1) / len(self.pages)) * 100
        self.progress['value'] = progress_value

        # Update page label
        self.page_label.config(text=f"Step {page_index + 1} of {len(self.pages)}")

        # Update navigation buttons
        self.prev_btn.config(state=tk.NORMAL if page_index > 0 else tk.DISABLED)

        # Hide skip button on last pages
        if page_index >= len(self.pages) - 2:
            self.skip_btn.pack_forget()
        else:
            self.skip_btn.pack(side=tk.LEFT, padx=20)

        if page_index == len(self.pages) - 1:
            self.next_btn.config(text="Finish & Launch", command=self._finish)
        else:
            self.next_btn.config(text="Next →", command=self._next_page)

        # Create page content
        page_func()

    def _next_page(self):
        """Go to next page"""
        # Validate current page before proceeding
        if self.current_page == 1:  # Profile page
            if not self.wizard_data.get('user_name'):
                messagebox.showwarning("Required Field", "Please enter your name")
                return

        if self.current_page < len(self.pages) - 1:
            self._show_page(self.current_page + 1)

    def _prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self._show_page(self.current_page - 1)

    def _skip_wizard(self):
        """Skip wizard with minimal setup"""
        result = messagebox.askyesno(
            "Skip Setup",
            "Are you sure you want to skip the setup wizard?\n\n"
            "Default settings will be used."
        )

        if result:
            # Apply minimal defaults
            self.wizard_data.update({
                'user_name': 'User',
                'selected_scene': 'custom',
                'enabled_floors': ['Z0_TheConstruct', 'Z+3_Trinity']
            })
            self._finish()

    def _finish(self):
        """Finish wizard and save configuration"""
        # Save all settings
        self._save_user_config()
        self._save_platform_settings()

        messagebox.showinfo(
            "Setup Complete",
            "LightSpeed platform has been configured successfully!\n\n"
            "The platform will now launch."
        )

        self.dialog.destroy()

    def _save_platform_settings(self):
        """Save platform settings"""
        settings_file = TRINITY_SETTINGS / "platform_config.json"

        config = {
            'initialized': True,
            'initialization_date': datetime.now().isoformat(),
            'scene_template': self.wizard_data.get('selected_scene'),
            'enabled_floors': self.wizard_data.get('enabled_floors', []),
            'ui_preferences': self.wizard_data.get('ui_preferences', {}),
            'ai_settings': self.wizard_data.get('ai_settings', {}),
            'advanced_settings': self.wizard_data.get('advanced_settings', {})
        }

        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            print(f"[STARTUP] Platform config saved to {settings_file}")
        except Exception as e:
            print(f"[STARTUP] Failed to save platform config: {e}")

    # ===== PAGE CREATORS =====

    def _create_welcome_page(self):
        """Create welcome page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Welcome to LightSpeed",
            font=('Segoe UI', 26, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(50, 15))

        tk.Label(
            container,
            text="Version 0.9.11+ - Enhanced Spatial UI & Smart Systems",
            font=('Segoe UI', 13),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=(0, 50))

        # Welcome card
        card = tk.Frame(container, bg=self.COLORS['card'])
        card.pack(fill=tk.BOTH, expand=True, padx=60, pady=20)

        tk.Label(
            card,
            text="This wizard will help you:",
            font=('Segoe UI', 16, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text']
        ).pack(pady=(25, 20))

        features = [
            "✓ Create your user profile",
            "✓ Select a smart scene template",
            "✓ Configure platform facets and preferences",
            "✓ Set up AI integration",
            "✓ Customize your workspace",
            "✓ Access all specialized wizards",
            "✓ Initialize the complete platform"
        ]

        for feature in features:
            tk.Label(
                card,
                text=feature,
                font=('Segoe UI', 12),
                bg=self.COLORS['card'],
                fg=self.COLORS['text'],
                anchor=tk.W
            ).pack(anchor=tk.W, padx=50, pady=6)

        tk.Label(card, text="", bg=self.COLORS['card']).pack(pady=15)

        # Estimated time
        tk.Label(
            container,
            text="Estimated time: 5-10 minutes",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=25)

    def _create_profile_page(self):
        """Create user profile page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="User Profile",
            font=('Segoe UI', 20, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(20, 10))

        tk.Label(
            container,
            text="Tell us about yourself to personalize your experience",
            font=('Segoe UI', 12),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=(0, 30))

        # Form
        form_frame = tk.Frame(container, bg=self.COLORS['bg'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=80)

        # Name
        self._create_form_field(
            form_frame,
            "Full Name *",
            "Enter your name",
            'user_name'
        )

        # Email
        self._create_form_field(
            form_frame,
            "Email",
            "your.email@example.com (optional)",
            'user_email'
        )

        # Workspace path
        path_row = tk.Frame(form_frame, bg=self.COLORS['bg'])
        path_row.pack(fill=tk.X, pady=15)

        tk.Label(
            path_row,
            text="Workspace Location",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text']
        ).pack(anchor=tk.W, pady=(0, 5))

        path_input_frame = tk.Frame(path_row, bg=self.COLORS['bg'])
        path_input_frame.pack(fill=tk.X)

        self.workspace_path_var = tk.StringVar(value=self.wizard_data.get('workspace_path', ''))

        path_entry = tk.Entry(
            path_input_frame,
            textvariable=self.workspace_path_var,
            font=('Segoe UI', 11),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['text'],
            relief=tk.FLAT
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))

        tk.Button(
            path_input_frame,
            text="Browse...",
            command=self._browse_workspace,
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side=tk.RIGHT)

        self.workspace_path_var.trace('w', lambda *args: self.wizard_data.update({
            'workspace_path': self.workspace_path_var.get()
        }))

    def _create_form_field(self, parent, label: str, placeholder: str, data_key: str):
        """Create form input field"""
        row = tk.Frame(parent, bg=self.COLORS['bg'])
        row.pack(fill=tk.X, pady=15)

        tk.Label(
            row,
            text=label,
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text']
        ).pack(anchor=tk.W, pady=(0, 5))

        var = tk.StringVar(value=self.wizard_data.get(data_key, ''))

        entry = tk.Entry(
            row,
            textvariable=var,
            font=('Segoe UI', 11),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['text'],
            relief=tk.FLAT
        )
        entry.pack(fill=tk.X, ipady=8)

        # Placeholder effect
        if not var.get():
            entry.insert(0, placeholder)
            entry.config(fg=self.COLORS['text_dim'])

            def on_focus_in(event):
                if entry.get() == placeholder:
                    entry.delete(0, tk.END)
                    entry.config(fg=self.COLORS['text'])

            def on_focus_out(event):
                if not entry.get():
                    entry.insert(0, placeholder)
                    entry.config(fg=self.COLORS['text_dim'])

            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)

        # Save to wizard data
        var.trace('w', lambda *args: self.wizard_data.update({
            data_key: var.get() if var.get() != placeholder else ''
        }))

    def _browse_workspace(self):
        """Browse for workspace directory"""
        directory = filedialog.askdirectory(
            title="Select Workspace Location",
            initialdir=self.workspace_path_var.get()
        )

        if directory:
            self.workspace_path_var.set(directory)

    def _create_scene_page(self):
        """Create scene selection page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Smart Scene Template",
            font=('Segoe UI', 20, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(15, 8))

        tk.Label(
            container,
            text="Choose a pre-configured scene or start with custom setup",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=(0, 20))

        # Scene grid
        scenes_frame = tk.Frame(container, bg=self.COLORS['bg'])
        scenes_frame.pack(fill=tk.BOTH, expand=True, padx=30)

        self.selected_scene_var = tk.StringVar(value=self.wizard_data.get('selected_scene', 'custom'))

        row = 0
        col = 0
        for template in self.SCENE_TEMPLATES:
            self._create_scene_card(scenes_frame, template, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

    def _create_scene_card(self, parent, template: Dict, row: int, col: int):
        """Create scene template card"""
        is_selected = self.selected_scene_var.get() == template['id']

        card = tk.Frame(
            parent,
            bg=template['color'] if is_selected else self.COLORS['card'],
            relief=tk.FLAT,
            highlightthickness=2,
            highlightbackground=template['color'] if is_selected else self.COLORS['card']
        )
        card.grid(row=row, column=col, padx=8, pady=8, sticky='nsew')

        parent.grid_rowconfigure(row, weight=1)
        parent.grid_columnconfigure(col, weight=1)

        # Radio button
        radio = tk.Radiobutton(
            card,
            text="",
            variable=self.selected_scene_var,
            value=template['id'],
            bg=template['color'] if is_selected else self.COLORS['card'],
            activebackground=template['color'] if is_selected else self.COLORS['card'],
            selectcolor=template['color'],
            command=lambda: self._on_scene_selected(template['id'])
        )
        radio.pack(anchor=tk.NE, padx=10, pady=10)

        tk.Label(
            card,
            text=template['name'],
            font=('Segoe UI', 13, 'bold'),
            bg=template['color'] if is_selected else self.COLORS['card'],
            fg=self.COLORS['text']
        ).pack(pady=(5, 8), padx=15)

        tk.Label(
            card,
            text=template['description'],
            font=('Segoe UI', 9),
            bg=template['color'] if is_selected else self.COLORS['card'],
            fg=self.COLORS['text'],
            wraplength=220,
            justify=tk.CENTER
        ).pack(pady=5, padx=15)

        if template['floors']:
            tk.Label(
                card,
                text=f"Floors: {len(template['floors'])}",
                font=('Segoe UI', 8),
                bg=template['color'] if is_selected else self.COLORS['card'],
                fg=self.COLORS['text_dim']
            ).pack(pady=(10, 5))

        tk.Label(card, text="", bg=template['color'] if is_selected else self.COLORS['card']).pack(pady=8)

        # Make clickable
        def on_click(event):
            self.selected_scene_var.set(template['id'])
            self._on_scene_selected(template['id'])

        card.bind('<Button-1>', on_click)
        for child in card.winfo_children():
            child.bind('<Button-1>', on_click)

    def _on_scene_selected(self, scene_id: str):
        """Handle scene selection"""
        self.wizard_data['selected_scene'] = scene_id

        # Update enabled floors based on template
        for template in self.SCENE_TEMPLATES:
            if template['id'] == scene_id:
                self.wizard_data['enabled_floors'] = template['floors'].copy()
                break

        # Refresh page to update visuals
        self._show_page(self.current_page)

    def _create_floors_page(self):
        """Create floor configuration page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Z-Floor Configuration",
            font=('Segoe UI', 20, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(15, 8))

        tk.Label(
            container,
            text="Select which floors to enable (based on your scene template)",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=(0, 20))

        # Scrollable floor list
        canvas = tk.Canvas(container, bg=self.COLORS['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.COLORS['bg'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        floors = [
            ('Z+2_Neo', 'neo', 'AI Orchestrator - Context tracking, conversations'),
            ('Z-1_Morpheus', 'morpheus', 'Knowledge Layer - Documentation, learning'),
            ('Z+1_Architect', 'architect', 'Design & Tools - Templates, architecture'),
            ('Z0_TheConstruct', 'construct', 'Physics & Render - Simulation, scene'),
            ('Z-2_Oracle', 'oracle', 'Archive & IP Vault - Documents, ingestion'),
            ('Z-3_Smith', 'smith', 'Background Tasks - Processes, automation'),
            ('Z-4_Merovingian', 'merovingian', 'System Health - Diagnostics, telemetry'),
            ('Z+3_Trinity', 'trinity', 'Settings & UI - Platform configuration')
        ]

        self.floor_vars = {}

        for floor_id, color_key, description in floors:
            var = tk.BooleanVar(value=floor_id in self.wizard_data.get('enabled_floors', []))
            self.floor_vars[floor_id] = var

            self._create_floor_checkbox(
                scrollable_frame,
                floor_id,
                self.COLORS[color_key],
                description,
                var
            )

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=30)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_floor_checkbox(self, parent, floor_id: str, color: str, description: str, var: tk.BooleanVar):
        """Create floor checkbox item"""
        card = tk.Frame(parent, bg=self.COLORS['card'])
        card.pack(fill=tk.X, pady=6, padx=10)

        # Color indicator
        indicator = tk.Frame(card, bg=color, width=6)
        indicator.pack(side=tk.LEFT, fill=tk.Y)

        # Checkbox
        cb = tk.Checkbutton(
            card,
            text=floor_id,
            variable=var,
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            selectcolor=self.COLORS['card'],
            activebackground=self.COLORS['card'],
            activeforeground=self.COLORS['text'],
            cursor='hand2',
            command=lambda: self._update_enabled_floors()
        )
        cb.pack(side=tk.LEFT, padx=15, pady=12)

        tk.Label(
            card,
            text=description,
            font=('Segoe UI', 9),
            bg=self.COLORS['card'],
            fg=self.COLORS['text_dim']
        ).pack(side=tk.LEFT, padx=(0, 15))

    def _update_enabled_floors(self):
        """Update enabled floors list"""
        self.wizard_data['enabled_floors'] = [
            floor_id for floor_id, var in self.floor_vars.items() if var.get()
        ]

    def _create_ui_prefs_page(self):
        """Create UI preferences page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="UI Preferences",
            font=('Segoe UI', 20, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(15, 8))

        tk.Label(
            container,
            text="Customize your visual experience",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=(0, 25))

        # Preferences form
        form_frame = tk.Frame(container, bg=self.COLORS['bg'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=60)

        # Theme
        theme_frame = tk.Frame(form_frame, bg=self.COLORS['bg'])
        theme_frame.pack(fill=tk.X, pady=12)

        tk.Label(
            theme_frame,
            text="Theme:",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text'],
            width=25,
            anchor=tk.W
        ).pack(side=tk.LEFT)

        theme_var = tk.StringVar(value=self.wizard_data.get('ui_preferences', {}).get('theme', 'dark'))
        for theme in ['dark', 'light', 'auto']:
            tk.Radiobutton(
                theme_frame,
                text=theme.capitalize(),
                variable=theme_var,
                value=theme,
                bg=self.COLORS['bg'],
                fg=self.COLORS['text'],
                selectcolor=self.COLORS['card'],
                activebackground=self.COLORS['bg'],
                font=('Segoe UI', 10),
                command=lambda: self._update_ui_pref('theme', theme_var.get())
            ).pack(side=tk.LEFT, padx=10)

        # Accent color
        color_frame = tk.Frame(form_frame, bg=self.COLORS['bg'])
        color_frame.pack(fill=tk.X, pady=12)

        tk.Label(
            color_frame,
            text="Accent Color:",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text'],
            width=25,
            anchor=tk.W
        ).pack(side=tk.LEFT)

        self.accent_color_var = tk.StringVar(
            value=self.wizard_data.get('ui_preferences', {}).get('accent_color', '#00FFFF')
        )

        color_display = tk.Label(
            color_frame,
            text="     ",
            bg=self.accent_color_var.get(),
            relief=tk.FLAT,
            width=5
        )
        color_display.pack(side=tk.LEFT, padx=10)

        tk.Button(
            color_frame,
            text="Choose Color",
            command=lambda: self._choose_accent_color(color_display),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=15,
            pady=6,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)

        # Font size
        font_frame = tk.Frame(form_frame, bg=self.COLORS['bg'])
        font_frame.pack(fill=tk.X, pady=12)

        tk.Label(
            font_frame,
            text="Font Size:",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text'],
            width=25,
            anchor=tk.W
        ).pack(side=tk.LEFT)

        font_size_var = tk.IntVar(value=self.wizard_data.get('ui_preferences', {}).get('font_size', 11))

        tk.Scale(
            font_frame,
            from_=9,
            to=16,
            orient=tk.HORIZONTAL,
            variable=font_size_var,
            bg=self.COLORS['bg'],
            fg=self.COLORS['text'],
            highlightthickness=0,
            troughcolor=self.COLORS['card'],
            activebackground=self.COLORS['accent'],
            command=lambda v: self._update_ui_pref('font_size', int(v))
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Checkboxes
        checkbox_options = [
            ('enable_animations', 'Enable animations'),
            ('show_tooltips', 'Show tooltips'),
            ('compact_mode', 'Compact mode'),
            ('show_minimap', 'Show dollhouse minimap')
        ]

        for key, label in checkbox_options:
            var = tk.BooleanVar(value=self.wizard_data.get('ui_preferences', {}).get(key, True))

            tk.Checkbutton(
                form_frame,
                text=label,
                variable=var,
                font=('Segoe UI', 11),
                bg=self.COLORS['bg'],
                fg=self.COLORS['text'],
                selectcolor=self.COLORS['card'],
                activebackground=self.COLORS['bg'],
                command=lambda k=key, v=var: self._update_ui_pref(k, v.get())
            ).pack(anchor=tk.W, pady=8)

    def _update_ui_pref(self, key: str, value: Any):
        """Update UI preference"""
        if 'ui_preferences' not in self.wizard_data:
            self.wizard_data['ui_preferences'] = {}
        self.wizard_data['ui_preferences'][key] = value

    def _choose_accent_color(self, display_label):
        """Choose accent color"""
        color = colorchooser.askcolor(
            title="Choose Accent Color",
            initialcolor=self.accent_color_var.get()
        )

        if color[1]:
            self.accent_color_var.set(color[1])
            display_label.config(bg=color[1])
            self._update_ui_pref('accent_color', color[1])

    def _create_ai_config_page(self):
        """Create AI configuration page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="AI Configuration (Ollama)",
            font=('Segoe UI', 20, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(15, 25))

        # Configuration form
        form_frame = tk.Frame(container, bg=self.COLORS['bg'])
        form_frame.pack(fill=tk.X, padx=60)

        # Enable AI
        enable_var = tk.BooleanVar(value=self.wizard_data.get('ai_settings', {}).get('enabled', True))

        tk.Checkbutton(
            form_frame,
            text="Enable AI Integration",
            variable=enable_var,
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text'],
            selectcolor=self.COLORS['card'],
            command=lambda: self._update_ai_setting('enabled', enable_var.get())
        ).pack(anchor=tk.W, pady=15)

        # Ollama URL
        url_frame = tk.Frame(form_frame, bg=self.COLORS['bg'])
        url_frame.pack(fill=tk.X, pady=10)

        tk.Label(
            url_frame,
            text="Ollama URL:",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text'],
            width=20,
            anchor=tk.W
        ).pack(side=tk.LEFT)

        url_var = tk.StringVar(value=self.wizard_data.get('ai_settings', {}).get('ollama_url', 'http://localhost:11434'))
        tk.Entry(
            url_frame,
            textvariable=url_var,
            font=('Segoe UI', 10),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['text'],
            relief=tk.FLAT,
            width=40
        ).pack(side=tk.LEFT, ipady=6)

        url_var.trace('w', lambda *args: self._update_ai_setting('ollama_url', url_var.get()))

        # Model
        model_frame = tk.Frame(form_frame, bg=self.COLORS['bg'])
        model_frame.pack(fill=tk.X, pady=10)

        tk.Label(
            model_frame,
            text="Model:",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text'],
            width=20,
            anchor=tk.W
        ).pack(side=tk.LEFT)

        model_var = tk.StringVar(value=self.wizard_data.get('ai_settings', {}).get('model', 'llama2'))
        tk.Entry(
            model_frame,
            textvariable=model_var,
            font=('Segoe UI', 10),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['text'],
            relief=tk.FLAT,
            width=40
        ).pack(side=tk.LEFT, ipady=6)

        model_var.trace('w', lambda *args: self._update_ai_setting('model', model_var.get()))

    def _update_ai_setting(self, key: str, value: Any):
        """Update AI setting"""
        if 'ai_settings' not in self.wizard_data:
            self.wizard_data['ai_settings'] = {}
        self.wizard_data['ai_settings'][key] = value

    def _create_advanced_page(self):
        """Create advanced settings page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Advanced Settings",
            font=('Segoe UI', 20, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(15, 25))

        form_frame = tk.Frame(container, bg=self.COLORS['bg'])
        form_frame.pack(fill=tk.X, padx=60)

        # Advanced checkboxes
        advanced_options = [
            ('auto_save', 'Auto-save settings', True),
            ('telemetry', 'Enable telemetry (anonymous usage data)', False),
            ('auto_update', 'Check for updates automatically', True),
            ('debug_mode', 'Enable debug mode', False),
            ('performance_mode', 'Performance mode (reduce animations)', False)
        ]

        for key, label, default in advanced_options:
            var = tk.BooleanVar(value=self.wizard_data.get('advanced_settings', {}).get(key, default))

            tk.Checkbutton(
                form_frame,
                text=label,
                variable=var,
                font=('Segoe UI', 11),
                bg=self.COLORS['bg'],
                fg=self.COLORS['text'],
                selectcolor=self.COLORS['card'],
                command=lambda k=key, v=var: self._update_advanced_setting(k, v.get())
            ).pack(anchor=tk.W, pady=10)

    def _update_advanced_setting(self, key: str, value: Any):
        """Update advanced setting"""
        if 'advanced_settings' not in self.wizard_data:
            self.wizard_data['advanced_settings'] = {}
        self.wizard_data['advanced_settings'][key] = value

    def _create_tailorables_page(self):
        """Create tailorables/customization page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Tailorables & Customization",
            font=('Segoe UI', 20, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(15, 10))

        tk.Label(
            container,
            text="Fine-tune your platform experience with custom preferences",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=(0, 20))

        # Info message
        info_card = tk.Frame(container, bg=self.COLORS['card'])
        info_card.pack(fill=tk.X, padx=50, pady=15)

        tk.Label(
            info_card,
            text="Tailorables allow you to customize specific behaviors and preferences.\n"
                 "These can be adjusted later in the Settings panel.",
            font=('Segoe UI', 10),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            justify=tk.LEFT
        ).pack(padx=20, pady=15)

        # Customization options
        custom_frame = tk.Frame(container, bg=self.COLORS['bg'])
        custom_frame.pack(fill=tk.BOTH, expand=True, padx=60)

        customizations = [
            ('default_floor', 'Default startup floor', ['Z0_TheConstruct', 'Z+2_Neo', 'Z+3_Trinity']),
            ('grid_size', 'Bento grid size', ['Small (3x3)', 'Medium (5x5)', 'Large (7x7)']),
            ('parallax_strength', 'Parallax effect strength', ['Low', 'Medium', 'High'])
        ]

        for key, label, options in customizations:
            row = tk.Frame(custom_frame, bg=self.COLORS['bg'])
            row.pack(fill=tk.X, pady=12)

            tk.Label(
                row,
                text=label + ":",
                font=('Segoe UI', 11, 'bold'),
                bg=self.COLORS['bg'],
                fg=self.COLORS['text'],
                width=25,
                anchor=tk.W
            ).pack(side=tk.LEFT)

            var = tk.StringVar(value=options[0])

            dropdown = tk.OptionMenu(row, var, *options)
            dropdown.config(
                bg=self.COLORS['card'],
                fg=self.COLORS['text'],
                font=('Segoe UI', 10),
                relief=tk.FLAT
            )
            dropdown.pack(side=tk.LEFT)

            var.trace('w', lambda *args, k=key, v=var: self._update_custom_pref(k, v.get()))

    def _update_custom_pref(self, key: str, value: str):
        """Update custom preference"""
        if 'custom_preferences' not in self.wizard_data:
            self.wizard_data['custom_preferences'] = {}
        self.wizard_data['custom_preferences'][key] = value

    def _create_wizard_hub_page(self):
        """Create wizard hub access page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Wizard Hub",
            font=('Segoe UI', 20, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(15, 10))

        tk.Label(
            container,
            text="Access specialized wizards for advanced configuration",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=(0, 20))

        # Wizard cards
        wizards_frame = tk.Frame(container, bg=self.COLORS['bg'])
        wizards_frame.pack(fill=tk.BOTH, expand=True, padx=40)

        wizards = [
            {
                'name': 'Trinity Wizard',
                'desc': 'Complete feature showcase and settings configuration',
                'action': self._launch_trinity_wizard
            },
            {
                'name': 'Spatial UI Wizard',
                'desc': 'Configure 3D interface and Bento grid settings',
                'action': self._launch_spatial_wizard
            },
            {
                'name': 'AI Setup Wizard',
                'desc': 'Advanced Ollama configuration and model selection',
                'action': self._launch_ai_wizard
            },
            {
                'name': 'Floor Configuration',
                'desc': 'Detailed Z-Floor setup and customization',
                'action': self._launch_floor_wizard
            }
        ]

        for wizard in wizards:
            self._create_wizard_card(wizards_frame, wizard)

    def _create_wizard_card(self, parent, wizard: Dict):
        """Create wizard access card"""
        card = tk.Frame(parent, bg=self.COLORS['card'])
        card.pack(fill=tk.X, pady=8)

        content_frame = tk.Frame(card, bg=self.COLORS['card'])
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=15)

        tk.Label(
            content_frame,
            text=wizard['name'],
            font=('Segoe UI', 13, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text']
        ).pack(anchor=tk.W)

        tk.Label(
            content_frame,
            text=wizard['desc'],
            font=('Segoe UI', 10),
            bg=self.COLORS['card'],
            fg=self.COLORS['text_dim']
        ).pack(anchor=tk.W, pady=(5, 0))

        tk.Button(
            card,
            text="Launch →",
            command=wizard['action'],
            bg=self.COLORS['card_hover'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2'
        ).pack(side=tk.RIGHT, padx=15)

    def _launch_trinity_wizard(self):
        """Launch Trinity wizard"""
        messagebox.showinfo("Trinity Wizard", "Trinity wizard will be launched after setup completes")

    def _launch_spatial_wizard(self):
        """Launch Spatial UI wizard"""
        messagebox.showinfo("Spatial UI Wizard", "Spatial UI wizard available in Settings after setup")

    def _launch_ai_wizard(self):
        """Launch AI wizard"""
        messagebox.showinfo("AI Wizard", "AI configuration wizard available in Settings")

    def _launch_floor_wizard(self):
        """Launch Floor wizard"""
        messagebox.showinfo("Floor Wizard", "Floor configuration wizard available in Settings")

    def _create_init_page(self):
        """Create initialization page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Initializing Platform...",
            font=('Segoe UI', 20, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(30, 20))

        # Progress info
        self.init_status_label = tk.Label(
            container,
            text="Preparing to initialize...",
            font=('Segoe UI', 12),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        )
        self.init_status_label.pack(pady=20)

        # Initialize button
        tk.Button(
            container,
            text="Initialize Now",
            command=self._run_initialization,
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 14, 'bold'),
            relief=tk.FLAT,
            padx=40,
            pady=15,
            cursor='hand2'
        ).pack(pady=30)

        # Results
        self.init_results_frame = tk.Frame(container, bg=self.COLORS['bg'])
        self.init_results_frame.pack(fill=tk.BOTH, expand=True, padx=60)

    def _run_initialization(self):
        """Run platform initialization"""
        self.init_status_label.config(text="Initializing...", fg=self.COLORS['warning'])
        self.dialog.update()

        steps = [
            ("Creating directory structure", self._init_directories),
            ("Saving configuration files", self._init_config_files),
            ("Setting up enabled floors", self._init_floors),
            ("Initializing components", self._init_components),
            ("Finalizing setup", self._init_finalize)
        ]

        for step_name, step_func in steps:
            self._add_init_result(step_name, "running")
            self.dialog.update()

            success = step_func()

            self._update_init_result(step_name, "success" if success else "error")
            self.dialog.update()

        self.init_status_label.config(text="✓ Initialization complete!", fg=self.COLORS['success'])

    def _add_init_result(self, step: str, status: str):
        """Add initialization result"""
        result_frame = tk.Frame(self.init_results_frame, bg=self.COLORS['card'])
        result_frame.pack(fill=tk.X, pady=3)
        result_frame._step_name = step

        status_colors = {
            'running': self.COLORS['warning'],
            'success': self.COLORS['success'],
            'error': self.COLORS['error']
        }

        status_symbols = {
            'running': '⏳',
            'success': '✓',
            'error': '✗'
        }

        tk.Label(
            result_frame,
            text=status_symbols.get(status, ''),
            font=('Segoe UI', 12),
            bg=self.COLORS['card'],
            fg=status_colors.get(status, self.COLORS['text']),
            width=3
        ).pack(side=tk.LEFT, padx=10)

        tk.Label(
            result_frame,
            text=step,
            font=('Segoe UI', 10),
            bg=self.COLORS['card'],
            fg=self.COLORS['text']
        ).pack(side=tk.LEFT, padx=5, pady=8)

    def _update_init_result(self, step: str, status: str):
        """Update initialization result"""
        for frame in self.init_results_frame.winfo_children():
            if hasattr(frame, '_step_name') and frame._step_name == step:
                # Update status symbol
                status_symbols = {'success': '✓', 'error': '✗'}
                status_colors = {'success': self.COLORS['success'], 'error': self.COLORS['error']}

                label = frame.winfo_children()[0]
                label.config(
                    text=status_symbols.get(status, ''),
                    fg=status_colors.get(status, self.COLORS['text'])
                )
                break

    def _init_directories(self) -> bool:
        """Initialize directory structure"""
        try:
            TRINITY_SETTINGS.mkdir(parents=True, exist_ok=True)
            MEROVINGIAN_ROOT.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"[INIT] Directory creation failed: {e}")
            return False

    def _init_config_files(self) -> bool:
        """Initialize configuration files"""
        try:
            self._save_user_config()
            self._save_platform_settings()
            return True
        except Exception as e:
            print(f"[INIT] Config save failed: {e}")
            return False

    def _init_floors(self) -> bool:
        """Initialize enabled floors"""
        try:
            # Create floor marker files
            for floor_id in self.wizard_data.get('enabled_floors', []):
                # Floor initialization would go here
                pass
            return True
        except Exception as e:
            print(f"[INIT] Floor setup failed: {e}")
            return False

    def _init_components(self) -> bool:
        """Initialize components"""
        try:
            # Component initialization would go here
            return True
        except Exception as e:
            print(f"[INIT] Component initialization failed: {e}")
            return False

    def _init_finalize(self) -> bool:
        """Finalize initialization"""
        try:
            # Mark as initialized
            init_marker = TRINITY_SETTINGS / "initialized.flag"
            init_marker.write_text(datetime.now().isoformat())
            return True
        except Exception as e:
            print(f"[INIT] Finalization failed: {e}")
            return False

    def _create_complete_page(self):
        """Create completion page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Setup Complete!",
            font=('Segoe UI', 26, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['success']
        ).pack(pady=(50, 20))

        tk.Label(
            container,
            text=f"Welcome to LightSpeed, {self.wizard_data.get('user_name', 'User')}!",
            font=('Segoe UI', 15),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text']
        ).pack(pady=(0, 40))

        # Summary card
        summary_card = tk.Frame(container, bg=self.COLORS['card'])
        summary_card.pack(fill=tk.BOTH, expand=True, padx=70, pady=20)

        tk.Label(
            summary_card,
            text="Your Configuration:",
            font=('Segoe UI', 16, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text']
        ).pack(pady=(20, 15))

        summary_items = [
            f"Scene Template: {self.wizard_data.get('selected_scene', 'custom').replace('_', ' ').title()}",
            f"Enabled Floors: {len(self.wizard_data.get('enabled_floors', []))} floors",
            f"Theme: {self.wizard_data.get('ui_preferences', {}).get('theme', 'dark').capitalize()}",
            f"AI Integration: {'Enabled' if self.wizard_data.get('ai_settings', {}).get('enabled', False) else 'Disabled'}"
        ]

        for item in summary_items:
            tk.Label(
                summary_card,
                text=f"• {item}",
                font=('Segoe UI', 11),
                bg=self.COLORS['card'],
                fg=self.COLORS['text'],
                anchor=tk.W
            ).pack(anchor=tk.W, padx=40, pady=6)

        tk.Label(summary_card, text="", bg=self.COLORS['card']).pack(pady=15)

        # Final message
        tk.Label(
            container,
            text="Click 'Finish & Launch' to start using LightSpeed!",
            font=('Segoe UI', 12),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=25)


def launch_startup_wizard(parent: Optional[tk.Tk] = None):
    """Launch enhanced startup wizard"""
    wizard = EnhancedStartupWizard(parent)
    wizard.open_wizard()


if __name__ == "__main__":
    launch_startup_wizard()
