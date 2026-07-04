#!/usr/bin/env python
"""
Enhanced Trinity Wizard - Complete Setup & Feature Showcase
Window-based wizard showing all implemented features non-interactively

This wizard provides:
- Complete feature overview (non-interactive display)
- Guided setup for all platform components
- Visual showcase of implemented functionality
- Settings configuration with smart defaults
- Feature verification and testing

Author: LightSpeed Team / ACHILLES
Version: 0.9.11+
Date: January 4, 2026
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# Setup paths
TRINITY_ROOT = Path(__file__).parent.resolve()
LIGHTSPEED_ROOT = TRINITY_ROOT.parent.parent
sys.path.insert(0, str(LIGHTSPEED_ROOT))

try:
    from core.config.paths import (
        TRINITY_SETTINGS, TRINITY_ROOT as TRINITY_PATH,
        NEO_ROOT, MORPHEUS_ROOT, ARCHITECT_ROOT, CONSTRUCT_ROOT,
        ORACLE_ROOT, SMITH_ROOT, MEROVINGIAN_ROOT
    )
    HAS_PATHS = True
except ImportError:
    print("[WARNING] Path configuration not available")
    HAS_PATHS = False
    TRINITY_SETTINGS = TRINITY_ROOT / "settings"

# Ensure settings directory exists
TRINITY_SETTINGS.mkdir(parents=True, exist_ok=True)


class EnhancedTrinityWizard:
    """
    Enhanced Trinity Setup Wizard

    Provides complete feature showcase and guided setup for LightSpeed platform.
    Non-interactive during feature display, interactive during configuration.
    """

    # Color scheme (matching platform theme)
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
        'error': '#FF0000'
    }

    def __init__(self, parent: Optional[tk.Tk] = None):
        """Initialize wizard"""
        self.parent = parent
        self.dialog = None
        self.current_page = 0
        self.settings = self._load_settings()

        # Wizard pages
        self.pages = [
            ("Welcome", self._create_welcome_page),
            ("Platform Overview", self._create_overview_page),
            ("Z-Floor Architecture", self._create_zfloor_page),
            ("Spatial UI Features", self._create_spatial_page),
            ("AI Integration", self._create_ai_page),
            ("Settings Configuration", self._create_settings_page),
            ("Feature Verification", self._create_verification_page),
            ("Completion", self._create_completion_page)
        ]

    def _load_settings(self) -> Dict[str, Any]:
        """Load existing settings or create defaults"""
        settings_file = TRINITY_SETTINGS / "wizard_config.json"

        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WIZARD] Failed to load settings: {e}")

        # Default settings
        return {
            'wizard_completed': False,
            'selected_floors': ['Z+2_Neo', 'Z0_TheConstruct', 'Z-2_Oracle', 'Z+3_Trinity'],
            'spatial_ui_enabled': True,
            'ai_enabled': True,
            'ollama_url': 'http://localhost:11434',
            'ollama_model': 'llama2',
            'theme': 'dark',
            'auto_save': True,
            'startup_floor': 'Z0_TheConstruct'
        }

    def _save_settings(self):
        """Save current settings"""
        settings_file = TRINITY_SETTINGS / "wizard_config.json"

        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            print(f"[WIZARD] Settings saved to {settings_file}")
        except Exception as e:
            print(f"[WIZARD] Failed to save settings: {e}")

    def open_wizard(self):
        """Open wizard window"""
        # Create dialog
        if self.parent:
            self.dialog = tk.Toplevel(self.parent)
        else:
            self.dialog = tk.Tk()

        self.dialog.title("LightSpeed Setup Wizard - Trinity Enhanced")
        self.dialog.geometry("1000x700")
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
        width = 1000
        height = 700
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')

    def _create_layout(self):
        """Create main wizard layout"""
        # Header
        header = tk.Frame(self.dialog, bg=self.COLORS['header'], height=80)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="LightSpeed Platform Setup",
            font=('Segoe UI', 20, 'bold'),
            bg=self.COLORS['header'],
            fg=self.COLORS['accent']
        ).pack(pady=10)

        self.subtitle_label = tk.Label(
            header,
            text="Welcome",
            font=('Segoe UI', 11),
            bg=self.COLORS['header'],
            fg=self.COLORS['text_dim']
        )
        self.subtitle_label.pack()

        # Progress bar
        progress_frame = tk.Frame(self.dialog, bg=self.COLORS['bg'], height=40)
        progress_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)
        progress_frame.pack_propagate(False)

        self.progress = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=960
        )
        self.progress.pack(fill=tk.X, pady=5)

        # Content area
        self.content_frame = tk.Frame(self.dialog, bg=self.COLORS['bg'])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Navigation buttons
        nav_frame = tk.Frame(self.dialog, bg=self.COLORS['bg'], height=60)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
        nav_frame.pack_propagate(False)

        self.prev_btn = tk.Button(
            nav_frame,
            text="← Previous",
            command=self._prev_page,
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 11),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = tk.Button(
            nav_frame,
            text="Next →",
            command=self._next_page,
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.next_btn.pack(side=tk.RIGHT, padx=5)

        # Page indicator
        self.page_label = tk.Label(
            nav_frame,
            text="Page 1 of 8",
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
        self.page_label.config(text=f"Page {page_index + 1} of {len(self.pages)}")

        # Update navigation buttons
        self.prev_btn.config(state=tk.NORMAL if page_index > 0 else tk.DISABLED)

        if page_index == len(self.pages) - 1:
            self.next_btn.config(text="Finish", command=self._finish)
        else:
            self.next_btn.config(text="Next →", command=self._next_page)

        # Create page content
        page_func()

    def _next_page(self):
        """Go to next page"""
        if self.current_page < len(self.pages) - 1:
            self._show_page(self.current_page + 1)

    def _prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self._show_page(self.current_page - 1)

    def _finish(self):
        """Finish wizard"""
        self.settings['wizard_completed'] = True
        self._save_settings()

        messagebox.showinfo(
            "Setup Complete",
            "LightSpeed platform setup is complete!\n\n"
            "You can now launch the platform components from the Main Launcher."
        )

        self.dialog.destroy()

    # ===== PAGE CREATORS =====

    def _create_welcome_page(self):
        """Create welcome page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        # Welcome message
        tk.Label(
            container,
            text="Welcome to LightSpeed V0.9.11+",
            font=('Segoe UI', 24, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(40, 20))

        tk.Label(
            container,
            text="Enhanced Spatial UI & Smart Systems Platform",
            font=('Segoe UI', 14),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=(0, 40))

        # Features card
        features_card = tk.Frame(container, bg=self.COLORS['card'], relief=tk.FLAT)
        features_card.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)

        tk.Label(
            features_card,
            text="What's New in This Version:",
            font=('Segoe UI', 16, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text']
        ).pack(pady=(20, 15))

        features = [
            "✓ Enhanced 3D Spatial UI with curved Bento grids",
            "✓ Ollama-powered AI wizard for intelligent tile creation",
            "✓ Smart Settings Hub with condensed, organized interface",
            "✓ Oracle Smart Floor auto-ingestion system",
            "✓ Project flowchart visualization",
            "✓ 3D environment rendering with fake LIDAR depth",
            "✓ Complete Z-Floor architecture integration",
            "✓ Trinity enhanced setup wizard (this wizard!)"
        ]

        for feature in features:
            tk.Label(
                features_card,
                text=feature,
                font=('Segoe UI', 12),
                bg=self.COLORS['card'],
                fg=self.COLORS['text'],
                anchor=tk.W
            ).pack(anchor=tk.W, padx=40, pady=5)

        tk.Label(
            features_card,
            text="",
            bg=self.COLORS['card']
        ).pack(pady=10)

        # Info message
        tk.Label(
            container,
            text="This wizard will guide you through the platform setup and showcase all features.",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=20)

    def _create_overview_page(self):
        """Create platform overview page (non-interactive showcase)"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Platform Overview",
            font=('Segoe UI', 18, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(10, 20))

        # Scrollable content
        canvas = tk.Canvas(container, bg=self.COLORS['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.COLORS['bg'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Component cards
        components = [
            {
                'name': 'Spatial UI',
                'status': 'Implemented',
                'features': [
                    '3D curved Bento grid (1.5m radius)',
                    'Glass morphism with depth-based thickness',
                    '10 tile types supported',
                    'Interactive hover and click handlers',
                    'Environment rendering with parallax layers'
                ]
            },
            {
                'name': 'AI Integration',
                'status': 'Implemented',
                'features': [
                    'Ollama-powered tile creation wizard',
                    'Context-aware suggestions',
                    'Floor-specific recommendations',
                    '8 pre-configured templates',
                    'Smart defaults for all configurations'
                ]
            },
            {
                'name': 'Smart Settings',
                'status': 'Implemented',
                'features': [
                    'Condensed to 3 main tabs',
                    'Collapsible sections with master toggles',
                    '51 platform settings organized',
                    'Import/Export configuration',
                    'Quick actions for common tasks'
                ]
            },
            {
                'name': 'Oracle Smart Floor',
                'status': 'Implemented',
                'features': [
                    'Continuous file ingestion (<5% CPU)',
                    'Auto-extraction of objects, functions, classes',
                    'Floor routing for extracted data',
                    'Multi-select and batch processing',
                    'Duplicate detection with SHA256'
                ]
            },
            {
                'name': 'Z-Floor Architecture',
                'status': 'Implemented',
                'features': [
                    '8 specialized floors (Neo to Trinity)',
                    'Centralized path configuration',
                    'Floor-specific functionality',
                    'Hierarchical organization',
                    'Complete inter-floor communication'
                ]
            }
        ]

        for comp in components:
            self._create_component_card(scrollable_frame, comp)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_component_card(self, parent, component: Dict):
        """Create component showcase card"""
        card = tk.Frame(parent, bg=self.COLORS['card'], relief=tk.FLAT)
        card.pack(fill=tk.X, padx=20, pady=10)

        # Header
        header_frame = tk.Frame(card, bg=self.COLORS['card'])
        header_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(
            header_frame,
            text=component['name'],
            font=('Segoe UI', 14, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text']
        ).pack(side=tk.LEFT)

        status_color = self.COLORS['success'] if component['status'] == 'Implemented' else self.COLORS['warning']
        tk.Label(
            header_frame,
            text=f"● {component['status']}",
            font=('Segoe UI', 10),
            bg=self.COLORS['card'],
            fg=status_color
        ).pack(side=tk.RIGHT)

        # Features
        for feature in component['features']:
            tk.Label(
                card,
                text=f"  • {feature}",
                font=('Segoe UI', 10),
                bg=self.COLORS['card'],
                fg=self.COLORS['text_dim'],
                anchor=tk.W
            ).pack(anchor=tk.W, padx=25, pady=2)

        tk.Label(card, text="", bg=self.COLORS['card']).pack(pady=5)

    def _create_zfloor_page(self):
        """Create Z-Floor architecture page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Z-Floor Architecture",
            font=('Segoe UI', 18, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(10, 20))

        tk.Label(
            container,
            text="8 specialized floors organized vertically:",
            font=('Segoe UI', 12),
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
            ('Z+2_Neo', '#FF0080', 'AI Orchestrator', 'Context tracking, AI conversations, smart suggestions'),
            ('Z-1_Morpheus', '#0080FF', 'Knowledge Layer', 'Documentation, learning resources, insights'),
            ('Z+1_Architect', '#00FF80', 'Design & Tools', 'Templates, design tools, project architecture'),
            ('Z0_TheConstruct', '#FFFF00', 'Physics & Render', 'Simulation engine, rendering, scene management'),
            ('Z-2_Oracle', '#FF8000', 'Archive & IP Vault', 'Documents, ingestion, vault, visual assets'),
            ('Z-3_Smith', '#FF0000', 'Background Tasks', 'Processes, logs, task management, automation'),
            ('Z-4_Merovingian', '#8000FF', 'System Health', 'Diagnostics, telemetry, performance profiling'),
            ('Z+3_Trinity', '#00FFFF', 'Settings & UI', 'Platform settings, persistence, configuration')
        ]

        for floor_id, color, role, description in floors:
            self._create_floor_card(scrollable_frame, floor_id, color, role, description)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_floor_card(self, parent, floor_id: str, color: str, role: str, description: str):
        """Create floor info card"""
        card = tk.Frame(parent, bg=self.COLORS['card'], relief=tk.FLAT)
        card.pack(fill=tk.X, padx=20, pady=5)

        # Color indicator
        indicator = tk.Frame(card, bg=color, width=8)
        indicator.pack(side=tk.LEFT, fill=tk.Y)

        # Content
        content = tk.Frame(card, bg=self.COLORS['card'])
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=10)

        tk.Label(
            content,
            text=floor_id,
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text']
        ).pack(anchor=tk.W)

        tk.Label(
            content,
            text=role,
            font=('Segoe UI', 10, 'bold'),
            bg=self.COLORS['card'],
            fg=color
        ).pack(anchor=tk.W, pady=(2, 5))

        tk.Label(
            content,
            text=description,
            font=('Segoe UI', 9),
            bg=self.COLORS['card'],
            fg=self.COLORS['text_dim'],
            wraplength=700,
            justify=tk.LEFT
        ).pack(anchor=tk.W)

    def _create_spatial_page(self):
        """Create Spatial UI features page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Spatial UI Features",
            font=('Segoe UI', 18, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(10, 20))

        # Feature grid
        features_frame = tk.Frame(container, bg=self.COLORS['bg'])
        features_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        features = [
            {
                'title': 'Enhanced Bento Grid',
                'desc': '1.5m locked radius curved surface with -50° to 50° FOV',
                'specs': ['Glass morphism', '10 tile types', 'Depth-based thickness (2-8px)']
            },
            {
                'title': 'Ollama AI Wizard',
                'desc': '5-step intelligent tile creation with context-aware suggestions',
                'specs': ['8 templates', 'Floor-specific', 'Smart defaults']
            },
            {
                'title': 'Environment Renderer',
                'desc': '3D backgrounds from images/videos with fake LIDAR depth',
                'specs': ['Parallax layers', 'Point cloud overlay', 'Depth estimation']
            },
            {
                'title': 'Flowchart Visualizer',
                'desc': 'Project structure on Y-axis hierarchy across curved surface',
                'specs': ['Auto-layout', 'Interactive navigation', 'Parent/child links']
            }
        ]

        row = 0
        col = 0
        for feature in features:
            self._create_feature_box(features_frame, feature, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

    def _create_feature_box(self, parent, feature: Dict, row: int, col: int):
        """Create feature box in grid"""
        box = tk.Frame(parent, bg=self.COLORS['card'], relief=tk.FLAT)
        box.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')

        parent.grid_rowconfigure(row, weight=1)
        parent.grid_columnconfigure(col, weight=1)

        tk.Label(
            box,
            text=feature['title'],
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['accent']
        ).pack(pady=(15, 5), padx=15)

        tk.Label(
            box,
            text=feature['desc'],
            font=('Segoe UI', 9),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            wraplength=350,
            justify=tk.CENTER
        ).pack(pady=5, padx=15)

        for spec in feature['specs']:
            tk.Label(
                box,
                text=f"• {spec}",
                font=('Segoe UI', 8),
                bg=self.COLORS['card'],
                fg=self.COLORS['text_dim']
            ).pack(anchor=tk.W, padx=25, pady=2)

        tk.Label(box, text="", bg=self.COLORS['card']).pack(pady=10)

    def _create_ai_page(self):
        """Create AI integration page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="AI Integration (Ollama)",
            font=('Segoe UI', 18, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(10, 20))

        # Info card
        info_card = tk.Frame(container, bg=self.COLORS['card'])
        info_card.pack(fill=tk.X, padx=40, pady=10)

        tk.Label(
            info_card,
            text="LightSpeed integrates with Ollama for intelligent AI suggestions throughout the platform.",
            font=('Segoe UI', 11),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            wraplength=800,
            justify=tk.CENTER
        ).pack(pady=15, padx=20)

        # Configuration section
        config_frame = tk.Frame(container, bg=self.COLORS['bg'])
        config_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        tk.Label(
            config_frame,
            text="Ollama Configuration:",
            font=('Segoe UI', 14, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text']
        ).pack(anchor=tk.W, pady=(0, 15))

        # URL field
        url_frame = tk.Frame(config_frame, bg=self.COLORS['bg'])
        url_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            url_frame,
            text="Ollama URL:",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text'],
            width=15,
            anchor=tk.W
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.ollama_url_var = tk.StringVar(value=self.settings.get('ollama_url', 'http://localhost:11434'))
        tk.Entry(
            url_frame,
            textvariable=self.ollama_url_var,
            font=('Segoe UI', 10),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['text'],
            relief=tk.FLAT,
            width=40
        ).pack(side=tk.LEFT, ipady=5, padx=5)

        # Model field
        model_frame = tk.Frame(config_frame, bg=self.COLORS['bg'])
        model_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            model_frame,
            text="Model:",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text'],
            width=15,
            anchor=tk.W
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.ollama_model_var = tk.StringVar(value=self.settings.get('ollama_model', 'llama2'))
        tk.Entry(
            model_frame,
            textvariable=self.ollama_model_var,
            font=('Segoe UI', 10),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['text'],
            relief=tk.FLAT,
            width=40
        ).pack(side=tk.LEFT, ipady=5, padx=5)

        # Test connection button
        tk.Button(
            config_frame,
            text="Test Connection",
            command=self._test_ollama,
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(anchor=tk.W, pady=15)

        self.ollama_status_label = tk.Label(
            config_frame,
            text="",
            font=('Segoe UI', 10),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        )
        self.ollama_status_label.pack(anchor=tk.W)

        # Info
        tk.Label(
            config_frame,
            text="Note: Ollama is optional. If not available, the platform will use fallback defaults.",
            font=('Segoe UI', 9),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim'],
            wraplength=800,
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(20, 0))

    def _test_ollama(self):
        """Test Ollama connection"""
        url = self.ollama_url_var.get()
        model = self.ollama_model_var.get()

        self.ollama_status_label.config(text="Testing connection...", fg=self.COLORS['warning'])
        self.dialog.update()

        try:
            import requests
            response = requests.get(f"{url}/api/version", timeout=3)
            if response.status_code == 200:
                self.ollama_status_label.config(
                    text=f"✓ Connected successfully to {url}",
                    fg=self.COLORS['success']
                )
                self.settings['ollama_url'] = url
                self.settings['ollama_model'] = model
                self.settings['ai_enabled'] = True
            else:
                self.ollama_status_label.config(
                    text=f"✗ Failed to connect (status {response.status_code})",
                    fg=self.COLORS['error']
                )
                self.settings['ai_enabled'] = False
        except Exception as e:
            self.ollama_status_label.config(
                text=f"✗ Connection failed: {str(e)}",
                fg=self.COLORS['error']
            )
            self.settings['ai_enabled'] = False

    def _create_settings_page(self):
        """Create settings configuration page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Platform Settings",
            font=('Segoe UI', 18, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(10, 20))

        # Settings form
        form_frame = tk.Frame(container, bg=self.COLORS['bg'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)

        # Startup floor
            self._create_setting_row(
                form_frame,
                "Startup Floor:",
                tk.OptionMenu,
                'startup_floor',
            *['Z+3_Trinity', 'Z+2_Neo', 'Z+1_Architect', 'Z0_TheConstruct',
              'Z-1_Morpheus', 'Z-2_Oracle', 'Z-3_Smith', 'Z-4_Merovingian']
        )

        # Theme
        self._create_setting_row(
            form_frame,
            "Theme:",
            tk.OptionMenu,
            'theme',
            'dark', 'light'
        )

        # Auto-save
        self._create_checkbox_row(form_frame, "Auto-save settings", 'auto_save')

        # Spatial UI enabled
        self._create_checkbox_row(form_frame, "Enable Spatial UI", 'spatial_ui_enabled')

    def _create_setting_row(self, parent, label: str, widget_type, setting_key: str, *options):
        """Create setting row with dropdown"""
        row = tk.Frame(parent, bg=self.COLORS['bg'])
        row.pack(fill=tk.X, pady=8)

        tk.Label(
            row,
            text=label,
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text'],
            width=20,
            anchor=tk.W
        ).pack(side=tk.LEFT)

        var = tk.StringVar(value=self.settings.get(setting_key, options[0]))

        dropdown = tk.OptionMenu(row, var, *options)
        dropdown.config(
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            highlightthickness=0,
            activebackground=self.COLORS['card_hover']
        )
        dropdown['menu'].config(
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 10)
        )
        dropdown.pack(side=tk.LEFT)

        # Save on change
        var.trace('w', lambda *args: self.settings.update({setting_key: var.get()}))

    def _create_checkbox_row(self, parent, label: str, setting_key: str):
        """Create checkbox setting row"""
        row = tk.Frame(parent, bg=self.COLORS['bg'])
        row.pack(fill=tk.X, pady=8)

        var = tk.BooleanVar(value=self.settings.get(setting_key, True))

        cb = tk.Checkbutton(
            row,
            text=label,
            variable=var,
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text'],
            selectcolor=self.COLORS['card'],
            activebackground=self.COLORS['bg'],
            activeforeground=self.COLORS['text'],
            cursor='hand2'
        )
        cb.pack(anchor=tk.W)

        # Save on change
        var.trace('w', lambda *args: self.settings.update({setting_key: var.get()}))

    def _create_verification_page(self):
        """Create feature verification page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Feature Verification",
            font=('Segoe UI', 18, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent']
        ).pack(pady=(10, 20))

        tk.Label(
            container,
            text="Verifying platform components...",
            font=('Segoe UI', 12),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=(0, 20))

        # Verification results
        results_frame = tk.Frame(container, bg=self.COLORS['bg'])
        results_frame.pack(fill=tk.BOTH, expand=True, padx=40)

        checks = [
            ('Spatial UI Module', self._check_spatial_ui),
            ('Settings Manager', self._check_settings),
            ('Z-Floor Structure', self._check_zfloors),
            ('Oracle Ingestion', self._check_oracle),
            ('Path Configuration', self._check_paths)
        ]

        for check_name, check_func in checks:
            status, message = check_func()
            self._create_verification_item(results_frame, check_name, status, message)

    def _create_verification_item(self, parent, name: str, status: bool, message: str):
        """Create verification result item"""
        item = tk.Frame(parent, bg=self.COLORS['card'])
        item.pack(fill=tk.X, pady=5)

        # Status indicator
        status_color = self.COLORS['success'] if status else self.COLORS['error']
        status_text = "✓" if status else "✗"

        tk.Label(
            item,
            text=status_text,
            font=('Segoe UI', 14, 'bold'),
            bg=self.COLORS['card'],
            fg=status_color,
            width=3
        ).pack(side=tk.LEFT, padx=10)

        # Content
        content = tk.Frame(item, bg=self.COLORS['card'])
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10, padx=10)

        tk.Label(
            content,
            text=name,
            font=('Segoe UI', 11, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text']
        ).pack(anchor=tk.W)

        tk.Label(
            content,
            text=message,
            font=('Segoe UI', 9),
            bg=self.COLORS['card'],
            fg=self.COLORS['text_dim']
        ).pack(anchor=tk.W)

    def _check_spatial_ui(self) -> tuple:
        """Check if spatial UI is available"""
        try:
            from core.ui.spatial import EnhancedBentoGrid, SpatialUIManager
            return (True, "Enhanced Bento Grid and Spatial UI Manager available")
        except ImportError:
            return (False, "Spatial UI modules not found")

    def _check_settings(self) -> tuple:
        """Check if settings managers are available"""
        try:
            from core.ui.enhanced_settings_manager import EnhancedSettingsManager
            from core.ui.smart_settings_hub import SmartSettingsHub
            return (True, "Enhanced and Smart Settings managers available")
        except ImportError:
            return (False, "Settings manager modules not found")

    def _check_zfloors(self) -> tuple:
        """Check Z-Floor structure"""
        if HAS_PATHS:
            floors = [NEO_ROOT, MORPHEUS_ROOT, ARCHITECT_ROOT, CONSTRUCT_ROOT,
                     ORACLE_ROOT, SMITH_ROOT, MEROVINGIAN_ROOT, TRINITY_PATH]
            existing = sum(1 for f in floors if f.exists())
            return (existing == 8, f"{existing}/8 Z-Floors found")
        return (False, "Path configuration not available")

    def _check_oracle(self) -> tuple:
        """Check Oracle ingestion"""
        try:
            oracle_candidates = [
                LIGHTSPEED_ROOT / "Z Axis" / "Z-2_Oracle" / "components" / "smart_floor_ingestion.py",
                LIGHTSPEED_ROOT / "Z Axis" / "Z-2_Oracle" / "legacy" / "Z-1_Oracle" / "smart_floor_ingestion.py",
            ]
            oracle_script = next((p for p in oracle_candidates if p.exists()), None)
            if oracle_script is not None:
                return (True, "Oracle smart floor ingestion system found")
            return (False, "Oracle ingestion script not found")
        except Exception:
            return (False, "Failed to check Oracle system")

    def _check_paths(self) -> tuple:
        """Check path configuration"""
        return (HAS_PATHS, "Path configuration available" if HAS_PATHS else "Path module not found")

    def _create_completion_page(self):
        """Create completion page"""
        container = tk.Frame(self.content_frame, bg=self.COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Setup Complete!",
            font=('Segoe UI', 24, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['success']
        ).pack(pady=(40, 20))

        tk.Label(
            container,
            text="Your LightSpeed platform is ready to use.",
            font=('Segoe UI', 14),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=(0, 40))

        # Summary card
        summary_card = tk.Frame(container, bg=self.COLORS['card'])
        summary_card.pack(fill=tk.BOTH, expand=True, padx=60, pady=20)

        tk.Label(
            summary_card,
            text="What's Next:",
            font=('Segoe UI', 16, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text']
        ).pack(pady=(20, 15))

        next_steps = [
            "1. Launch Spatial UI from Main Launcher to explore the 3D interface",
            "2. Open Smart Settings to customize your platform configuration",
            "3. Try the Ollama-powered Add New wizard to create your first tiles",
            "4. Explore the Z-Floor architecture and navigate between floors",
            "5. Start the Oracle ingestion to process your project files",
            "6. Use the flowchart visualizer to see your project structure"
        ]

        for step in next_steps:
            tk.Label(
                summary_card,
                text=step,
                font=('Segoe UI', 11),
                bg=self.COLORS['card'],
                fg=self.COLORS['text'],
                anchor=tk.W
            ).pack(anchor=tk.W, padx=40, pady=5)

        tk.Label(
            summary_card,
            text="",
            bg=self.COLORS['card']
        ).pack(pady=15)

        # Final message
        tk.Label(
            container,
            text="Click 'Finish' to close this wizard and start using LightSpeed!",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_dim']
        ).pack(pady=20)


def launch_trinity_wizard(parent: Optional[tk.Tk] = None):
    """Launch Trinity wizard"""
    wizard = EnhancedTrinityWizard(parent)
    wizard.open_wizard()


if __name__ == "__main__":
    launch_trinity_wizard()
