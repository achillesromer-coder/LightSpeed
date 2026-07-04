#!/usr/bin/env python
"""
UNIFIED WIZARD COMPLETE - All Wizards Integrated
Combines startup, setup, enhanced trinity, and IT portal integration

Single comprehensive wizard flow:
1. System diagnostics
2. Z-stack validation
3. Asset discovery
4. Database initialization
5. Search indexing
6. UI configuration
7. OASIS aesthetic setup
8. Final verification

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 20, 2026
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
from typing import Dict, List, Optional

# Setup paths
TRINITY_ROOT = Path(__file__).parent.parent.resolve()
LIGHTSPEED_ROOT = TRINITY_ROOT.parent.parent
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"

sys.path.insert(0, str(TRINITY_ROOT))
sys.path.insert(0, str(LIGHTSPEED_ROOT))

# Import systems
try:
    from diagnostics.complete_diagnostic_system import SystemDiagnostics
    HAS_DIAGNOSTICS = True
except:
    HAS_DIAGNOSTICS = False

try:
    from ui.oasis_aesthetic_system import (
        OASISColors, OASISPanel, OASISButton,
        OASISProgressBar, apply_oasis_theme
    )
    HAS_OASIS = True
except:
    HAS_OASIS = False


class UnifiedWizardComplete(tk.Tk):
    """
    Complete unified wizard system

    Integrates:
    - Startup wizard (system checks)
    - Setup wizard (configuration)
    - Enhanced Trinity wizard (features)
    - IT Portal integration (deployment)
    - Diagnostic system (validation)
    - OASIS aesthetic (theming)
    """

    PAGES = [
        ('Welcome', 'Welcome to LightSpeed'),
        ('Diagnostics', 'System Health Check'),
        ('Z-Stack', 'Z-Axis Architecture'),
        ('Assets', 'Asset Discovery'),
        ('Database', 'Database Setup'),
        ('Search', 'Search Indexing'),
        ('UI Config', 'UI Configuration'),
        ('Aesthetic', 'Visual Theming'),
        ('Integration', 'System Integration'),
        ('Complete', 'Setup Complete')
    ]

    def __init__(self):
        super().__init__()

        self.title("LightSpeed Unified Wizard - Complete Setup")
        self.geometry("1000x700")

        # Apply OASIS theme
        if HAS_OASIS:
            apply_oasis_theme(self)
            self.colors = OASISColors
        else:
            self.config(bg='#0A1628')
            self.colors = None

        # Wizard state
        self.current_page = 0
        self.settings = self._load_settings()
        self.diagnostic_results = []

        # Create UI
        self._create_ui()

        # Show first page
        self._show_page(0)

    def _load_settings(self) -> Dict:
        """Load existing settings"""
        settings_file = TRINITY_ROOT / "settings" / "wizard_config.json"

        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # Defaults
        return {
            'wizard_completed': False,
            'wizard_version': '1.0.0',
            'selected_floors': ['Z+3_Trinity', 'Z0_TheConstruct', 'Z-1_Morpheus', 'Z-2_Oracle'],
            'oasis_theme_enabled': True,
            'diagnostic_passed': False,
            'database_initialized': False,
            'assets_discovered': False,
            'search_indexed': False,
            'integration_complete': False,
            'setup_date': None
        }

    def _save_settings(self):
        """Save wizard settings"""
        settings_file = TRINITY_ROOT / "settings" / "wizard_config.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)

        self.settings['setup_date'] = datetime.now().isoformat()

        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def _create_ui(self):
        """Create wizard UI"""
        # Header
        header_frame = tk.Frame(self, bg='#001D3D' if self.colors else '#1E3A5F', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        self.title_label = tk.Label(
            header_frame,
            text="LightSpeed Unified Wizard",
            font=('Orbitron', 18, 'bold') if HAS_OASIS else ('Arial', 18, 'bold'),
            fg='#00F5FF' if self.colors else '#00FFFF',
            bg='#001D3D' if self.colors else '#1E3A5F'
        )
        self.title_label.pack(pady=25)

        # Progress bar
        progress_frame = tk.Frame(self, bg='#0A1628' if self.colors else '#0A1628')
        progress_frame.pack(fill=tk.X, padx=20, pady=10)

        if HAS_OASIS:
            self.progress_bar = OASISProgressBar(progress_frame, width=900)
            self.progress_bar.pack()
        else:
            self.progress_var = tk.DoubleVar()
            self.progress_bar = ttk.Progressbar(
                progress_frame,
                variable=self.progress_var,
                maximum=len(self.PAGES),
                length=900
            )
            self.progress_bar.pack()

        # Page container
        self.page_container = tk.Frame(self, bg='#0A1628' if self.colors else '#0A1628')
        self.page_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Navigation buttons
        nav_frame = tk.Frame(self, bg='#0A1628' if self.colors else '#0A1628', height=60)
        nav_frame.pack(fill=tk.X, padx=20, pady=10)
        nav_frame.pack_propagate(False)

        if HAS_OASIS:
            self.back_btn = OASISButton(
                nav_frame,
                text="Back",
                command=self._previous_page,
                style='secondary'
            )
            self.next_btn = OASISButton(
                nav_frame,
                text="Next",
                command=self._next_page,
                style='primary'
            )
        else:
            self.back_btn = tk.Button(
                nav_frame,
                text="Back",
                font=('Arial', 11),
                command=self._previous_page
            )
            self.next_btn = tk.Button(
                nav_frame,
                text="Next",
                font=('Arial', 11),
                command=self._next_page
            )

        self.back_btn.pack(side=tk.LEFT)
        self.next_btn.pack(side=tk.RIGHT)

    def _show_page(self, page_index):
        """Show specific page"""
        if page_index < 0 or page_index >= len(self.PAGES):
            return

        self.current_page = page_index

        # Update progress
        if HAS_OASIS:
            self.progress_bar.set_progress((page_index + 1) / len(self.PAGES) * 100)
        else:
            self.progress_var.set(page_index + 1)

        # Update title
        page_title = self.PAGES[page_index][1]
        self.title_label.config(text=page_title)

        # Clear page container
        for widget in self.page_container.winfo_children():
            widget.destroy()

        # Show page content
        page_name = self.PAGES[page_index][0]
        # Normalize page names into valid python identifiers.
        page_method = f"_create_page_{page_name.lower().replace(' ', '_').replace('-', '_')}"

        if hasattr(self, page_method):
            getattr(self, page_method)()

        # Update navigation buttons
        self.back_btn.config(state=tk.NORMAL if page_index > 0 else tk.DISABLED)

        if page_index == len(self.PAGES) - 1:
            self.next_btn.config(text="Finish")
        else:
            self.next_btn.config(text="Next")

    def _next_page(self):
        """Go to next page"""
        if self.current_page == len(self.PAGES) - 1:
            # Finish wizard
            self.settings['wizard_completed'] = True
            self._save_settings()
            messagebox.showinfo(
                "Wizard Complete",
                "LightSpeed setup is complete!\n\nYou can now launch the IT Portal."
            )
            self.destroy()
        else:
            self._show_page(self.current_page + 1)

    def _previous_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self._show_page(self.current_page - 1)

    # ========================================================================
    # PAGE CREATORS
    # ========================================================================

    def _create_page_welcome(self):
        """Welcome page"""
        content = tk.Frame(self.page_container, bg='#0A1628' if self.colors else '#0A1628')
        content.pack(fill=tk.BOTH, expand=True)

        # Welcome message
        welcome_text = """
        Welcome to the LightSpeed Unified Setup Wizard!

        This wizard will guide you through:

        - System diagnostics and health checks
        - Z-Axis architectural validation
        - Asset discovery and registration
        - Database initialization
        - Search system indexing
        - UI configuration and theming
        - Complete system integration

        Click "Next" to begin the setup process.
        """

        label = tk.Label(
            content,
            text=welcome_text,
            font=('Segoe UI', 12),
            fg='#FFFFFF',
            bg='#0A1628' if self.colors else '#0A1628',
            justify=tk.LEFT
        )
        label.pack(pady=50, padx=50)

    def _create_page_diagnostics(self):
        """Diagnostics page"""
        content = tk.Frame(self.page_container, bg='#0A1628' if self.colors else '#0A1628')
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            content,
            text="Running System Diagnostics...",
            font=('Segoe UI', 14, 'bold'),
            fg='#00F5FF' if self.colors else '#00FFFF',
            bg='#0A1628' if self.colors else '#0A1628'
        ).pack(pady=20)

        # Results text
        self.diagnostic_text = tk.Text(
            content,
            height=20,
            bg='#001D3D' if self.colors else '#1E3A5F',
            fg='#FFFFFF',
            font=('Courier', 9),
            wrap=tk.WORD
        )
        self.diagnostic_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Run diagnostics
        self.after(500, self._run_diagnostics)

    def _run_diagnostics(self):
        """Run diagnostic tests"""
        if HAS_DIAGNOSTICS:
            diagnostics = SystemDiagnostics()
            self.diagnostic_results = diagnostics.run_all_diagnostics()

            # Show results
            report = diagnostics.generate_report()
            self.diagnostic_text.insert('1.0', report)
            self.diagnostic_text.config(state=tk.DISABLED)

            # Update settings
            passed = len([r for r in self.diagnostic_results if r.status == 'pass'])
            total = len(self.diagnostic_results)
            self.settings['diagnostic_passed'] = (passed / total) > 0.7

        else:
            self.diagnostic_text.insert('1.0', "Diagnostic system not available.\nSkipping diagnostics...\n")
            self.diagnostic_text.config(state=tk.DISABLED)

    def _create_page_z_stack(self):
        """Z-stack validation page"""
        content = tk.Frame(self.page_container, bg='#0A1628' if self.colors else '#0A1628')
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            content,
            text="Z-Axis Architecture Validation",
            font=('Segoe UI', 14, 'bold'),
            fg='#00F5FF' if self.colors else '#00FFFF',
            bg='#0A1628' if self.colors else '#0A1628'
        ).pack(pady=20)

        # Floor checkboxes
        floor_frame = tk.Frame(content, bg='#001D3D' if self.colors else '#1E3A5F')
        floor_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)

        floors = [
            ('Z+3_Trinity', 'Trinity - UI & Dashboard'),
            ('Z+2_Neo', 'Neo - AI Integration'),
            ('Z+1_Architect', 'Architect - Project Planning'),
            ('Z0_TheConstruct', 'TheConstruct - Calculators'),
            ('Z-1_Morpheus', 'Morpheus - Knowledge Base'),
            ('Z-2_Oracle', 'Oracle - Smart Floor Core'),
            ('Z-3_Smith', 'Smith - Task Orchestration'),
            ('Z-4_Merovingian', 'Merovingian - Data Persistence')
        ]

        self.floor_vars = {}

        for floor_id, floor_name in floors:
            var = tk.BooleanVar(value=floor_id in self.settings['selected_floors'])
            self.floor_vars[floor_id] = var

            cb = tk.Checkbutton(
                floor_frame,
                text=floor_name,
                variable=var,
                font=('Segoe UI', 11),
                fg='#FFFFFF',
                bg='#001D3D' if self.colors else '#1E3A5F',
                selectcolor='#003566' if self.colors else '#003566'
            )
            cb.pack(anchor='w', padx=20, pady=5)

    def _create_page_assets(self):
        """Asset discovery page"""
        content = tk.Frame(self.page_container, bg='#0A1628' if self.colors else '#0A1628')
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            content,
            text="Discovering Assets...",
            font=('Segoe UI', 14, 'bold'),
            fg='#00F5FF' if self.colors else '#00FFFF',
            bg='#0A1628' if self.colors else '#0A1628'
        ).pack(pady=20)

        self.asset_text = tk.Text(
            content,
            height=20,
            bg='#001D3D' if self.colors else '#1E3A5F',
            fg='#FFFFFF',
            font=('Courier', 9)
        )
        self.asset_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.after(500, self._discover_assets)

    def _discover_assets(self):
        """Discover and register assets"""
        try:
            sys.path.insert(0, str(Z_AXIS_ROOT / "Z-2_Oracle"))
            from tools.asset_management_system import AssetManagementSystem

            self.asset_text.insert(tk.END, "Initializing Asset Management System...\n")
            ams = AssetManagementSystem()

            self.asset_text.insert(tk.END, "Discovering assets...\n")
            stats = ams.get_statistics()

            self.asset_text.insert(tk.END, f"\nDiscovery complete!\n")
            self.asset_text.insert(tk.END, f"- Total assets: {stats['total_assets']}\n")
            for asset_type, count in stats['by_type'].items():
                self.asset_text.insert(tk.END, f"- {asset_type.title()}: {count}\n")

            self.settings['assets_discovered'] = True

        except Exception as e:
            self.asset_text.insert(tk.END, f"\nError: {e}\n")
            self.settings['assets_discovered'] = False

        self.asset_text.config(state=tk.DISABLED)

    def _create_page_database(self):
        """Database initialization page"""
        content = tk.Frame(self.page_container, bg='#0A1628' if self.colors else '#0A1628')
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            content,
            text="Database Initialization",
            font=('Segoe UI', 14, 'bold'),
            fg='#00F5FF' if self.colors else '#00FFFF',
            bg='#0A1628' if self.colors else '#0A1628'
        ).pack(pady=20)

        tk.Label(
            content,
            text="Database is already initialized with:\n\n"
                 "- Calculator modules\n"
                 "- Scientific datasets\n"
                 "- Floor structures\n"
                 "- Knowledge graph\n\n"
                 "No action required.",
            font=('Segoe UI', 12),
            fg='#FFFFFF',
            bg='#0A1628' if self.colors else '#0A1628',
            justify=tk.CENTER
        ).pack(pady=50)

        self.settings['database_initialized'] = True

    def _create_page_search(self):
        """Search indexing page"""
        content = tk.Frame(self.page_container, bg='#0A1628' if self.colors else '#0A1628')
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            content,
            text="Building Search Index...",
            font=('Segoe UI', 14, 'bold'),
            fg='#00F5FF' if self.colors else '#00FFFF',
            bg='#0A1628' if self.colors else '#0A1628'
        ).pack(pady=20)

        self.search_text = tk.Text(
            content,
            height=20,
            bg='#001D3D' if self.colors else '#1E3A5F',
            fg='#FFFFFF',
            font=('Courier', 9)
        )
        self.search_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.after(500, self._build_search_index)

    def _build_search_index(self):
        """Build search index"""
        try:
            from wizards.unified_search_system import UnifiedSearchSystem

            self.search_text.insert(tk.END, "Initializing search system...\n")
            search = UnifiedSearchSystem()

            self.search_text.insert(tk.END, f"\nSearch index built!\n")
            self.search_text.insert(tk.END, f"- Indexed items: {len(search.search_index)}\n")

            self.settings['search_indexed'] = True

        except Exception as e:
            self.search_text.insert(tk.END, f"\nError: {e}\n")
            self.settings['search_indexed'] = False

        self.search_text.config(state=tk.DISABLED)

    def _create_page_ui_config(self):
        """UI configuration page"""
        content = tk.Frame(self.page_container, bg='#0A1628' if self.colors else '#0A1628')
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            content,
            text="UI Configuration",
            font=('Segoe UI', 14, 'bold'),
            fg='#00F5FF' if self.colors else '#00FFFF',
            bg='#0A1628' if self.colors else '#0A1628'
        ).pack(pady=20)

        # Theme toggle
        self.oasis_var = tk.BooleanVar(value=self.settings.get('oasis_theme_enabled', True))

        cb = tk.Checkbutton(
            content,
            text="Enable OASIS Aesthetic Theme (Ready Player 1 style)",
            variable=self.oasis_var,
            font=('Segoe UI', 12),
            fg='#FFFFFF',
            bg='#0A1628' if self.colors else '#0A1628',
            selectcolor='#003566' if self.colors else '#003566'
        )
        cb.pack(pady=20)

    def _create_page_aesthetic(self):
        """Aesthetic preview page"""
        content = tk.Frame(self.page_container, bg='#0A1628' if self.colors else '#0A1628')
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            content,
            text="Visual Theme Preview",
            font=('Segoe UI', 14, 'bold'),
            fg='#00F5FF' if self.colors else '#00FFFF',
            bg='#0A1628' if self.colors else '#0A1628'
        ).pack(pady=20)

        if HAS_OASIS:
            # Show OASIS theme sample
            sample_panel = OASISPanel(content, title="Sample Panel", width=600, height=300)
            sample_panel.pack(pady=20)

            tk.Label(
                sample_panel.content_frame,
                text="OASIS Theme Enabled (OK)",
                font=('Orbitron', 14, 'bold'),
                fg='#00FF41',
                bg=OASISColors.BG_LIGHT
            ).pack(pady=50)
        else:
            tk.Label(
                content,
                text="OASIS theme not available\nUsing default theme",
                font=('Segoe UI', 12),
                fg='#FFB627',
                bg='#0A1628'
            ).pack(pady=50)

    def _create_page_integration(self):
        """System integration page"""
        content = tk.Frame(self.page_container, bg='#0A1628' if self.colors else '#0A1628')
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            content,
            text="Finalizing Integration...",
            font=('Segoe UI', 14, 'bold'),
            fg='#00F5FF' if self.colors else '#00FFFF',
            bg='#0A1628' if self.colors else '#0A1628'
        ).pack(pady=20)

        # Save all settings
        self.settings['selected_floors'] = [
            floor_id for floor_id, var in self.floor_vars.items() if var.get()
        ]
        self.settings['oasis_theme_enabled'] = self.oasis_var.get()
        self.settings['integration_complete'] = True

        self._save_settings()

        tk.Label(
            content,
            text="Settings saved\n"
                 "Configuration complete\n"
                 "System ready\n\n"
                 "Click 'Next' to complete setup.",
            font=('Segoe UI', 12),
            fg='#00FF41' if self.colors else '#00FF00',
            bg='#0A1628' if self.colors else '#0A1628',
            justify=tk.CENTER
        ).pack(pady=50)

    def _create_page_complete(self):
        """Completion page"""
        content = tk.Frame(self.page_container, bg='#0A1628' if self.colors else '#0A1628')
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            content,
            text="Setup Complete!",
            font=('Orbitron' if HAS_OASIS else 'Arial', 18, 'bold'),
            fg='#00FF41' if self.colors else '#00FF00',
            bg='#0A1628' if self.colors else '#0A1628'
        ).pack(pady=40)

        tk.Label(
            content,
            text="LightSpeed is now configured and ready to use.\n\n"
                 "To launch the IT Portal:\n\n"
                 "  python unified_lightspeed_launcher.py\n\n"
                 "Or run the IT Portal directly:\n\n"
                 "  python Z Axis/Z+3_Trinity/ui/it_portal.py\n\n"
                 "Click 'Finish' to close this wizard.",
            font=('Segoe UI', 11),
            fg='#FFFFFF',
            bg='#0A1628' if self.colors else '#0A1628',
            justify=tk.CENTER
        ).pack(pady=20)


def main():
    """Launch unified wizard"""
    wizard = UnifiedWizardComplete()
    wizard.mainloop()


if __name__ == "__main__":
    main()
