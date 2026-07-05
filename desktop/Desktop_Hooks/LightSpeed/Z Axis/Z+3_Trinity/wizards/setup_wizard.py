#!/usr/bin/env python
"""
SETUP WIZARD - Comprehensive First-Run Configuration
Configures complete LightSpeed platform with auto-detection

This wizard sets up:
1. User profile and authentication
2. Company information
3. Project settings
4. AI backend (Ollama/Achilles)
5. Available libraries and functions
6. Widget layouts with drag-drop builder
7. Template selection
8. Dashboard preferences
9. Z-floor integration
10. OKRs and goals

Clean Code: Single comprehensive wizard replacing multiple setup scripts
Consolidates: setup_wizard.py, first_run_setup.py, config wizards
Version: 0.9.5 - Complete Auto-Detection & Integration
Date: December 20, 2025
"""

import sys
import os
import json
import sqlite3
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in (start, *start.parents):
        try:
            if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
                return candidate
        except Exception:
            continue
    try:
        cwd = Path.cwd().resolve()
        if (cwd / "N.py").exists() and (cwd / "Z Axis").exists():
            return cwd
    except Exception:
        pass
    return start.parent


LIGHTSPEED_ROOT = _find_lightspeed_root(Path(__file__))
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"

for _p in (LIGHTSPEED_ROOT, Z_AXIS_ROOT, Z_AXIS_ROOT / "core", Z_AXIS_ROOT / "wizards"):
    try:
        if _p.exists():
            sys.path.insert(0, str(_p))
    except Exception:
        pass

try:
    for _floor in sorted(Z_AXIS_ROOT.iterdir(), key=lambda p: p.name.lower()):
        if _floor.is_dir() and (_floor / "_FLOOR_MANIFEST.json").exists():
            sys.path.insert(0, str(_floor))
except Exception:
    pass


def _safe_tk_parent(parent=None):
    """Return (root, owner) where owner is a widget to parent Toplevels under."""
    try:
        import tkinter as tk  # local import to keep CLI-only usage lightweight
    except Exception:
        return None, None

    if parent is None:
        root = tk.Tk()
        root.withdraw()
        return root, root

    return None, parent


# Singleton window handle (prevents Tk widget path errors from overlapping launches).
_ACTIVE_SETUP_WIZARD_WINDOW = None


class SetupWizard:
    """
    Interactive setup wizard for complete platform configuration.

    Features:
    - Auto-detect available libraries and functions
    - AI backend detection (Ollama/Achilles)
    - Widget layout builder
    - Template gallery
    - Z-floor integration
    - Complete first-run setup
    """

    def __init__(self):
        self.root = LIGHTSPEED_ROOT
        self.config = {}
        # Use the unified DB location (Merovingian floor during migration); never create a legacy root `Data/` DB.
        try:
            from core.services import get_db  # type: ignore
            self.db_path = Path(get_db().db_path)
        except Exception:
            self.db_path = self.root / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db"

        # Auto-detection results
        self.detected_libraries = {}
        self.detected_functions = {}
        self.ai_backends_available = {}
        self.available_widgets = []
        self.available_templates = []

        # Integration systems
        self.floor_loader = None
        self.ai_orchestrator = None

    def run(self) -> Optional[Dict]:
        """Run interactive setup wizard"""

        print("\n" + "=" * 70)
        print("LIGHTSPEED PLATFORM SETUP WIZARD v3.0.0")
        print("=" * 70 + "\n")
        print("Welcome! This wizard will configure your complete LightSpeed platform.")
        print("\nDetecting system capabilities...")

        # Step 0: Auto-Detection
        self._auto_detect_system()

        print("\nSetup steps:")
        print("  1. User profile and authentication")
        print("  2. Company information")
        print("  3. AI backend configuration (Ollama/Achilles)")
        print("  4. Project settings")
        print("  5. Widget layout builder")
        print("  6. Dashboard preferences")
        print("  7. OKRs and goals (optional)")
        print("  8. Z-floor integration\n")

        input("Press Enter to begin setup...")

        # Step 1: User Profile
        print("=" * 70)
        print("STEP 1: USER PROFILE")
        print("=" * 70 + "\n")
        user = self._setup_user_profile()
        if not user:
            return None

        # Step 2: Company
        print("\n" + "=" * 70)
        print("STEP 2: COMPANY INFORMATION")
        print("=" * 70 + "\n")
        company = self._setup_company()
        if not company:
            return None

        # Step 3: AI Backend Configuration
        print("\n" + "=" * 70)
        print("STEP 3: AI BACKEND CONFIGURATION")
        print("=" * 70 + "\n")
        ai_config = self._setup_ai_backend()

        # Step 4: Projects
        print("\n" + "=" * 70)
        print("STEP 4: PROJECTS")
        print("=" * 70 + "\n")
        projects = self._setup_projects()

        # Step 5: Widget Layout Builder
        print("\n" + "=" * 70)
        print("STEP 5: WIDGET LAYOUT & DASHBOARD")
        print("=" * 70 + "\n")
        widgets = self._setup_widget_layout()

        # Step 6: OKRs (Optional)
        print("\n" + "=" * 70)
        print("STEP 6: OBJECTIVES & KEY RESULTS (Optional)")
        print("=" * 70 + "\n")
        okrs = self._setup_okrs()

        # Step 7: Z-Floor Integration
        print("\n" + "=" * 70)
        print("STEP 7: Z-FLOOR INTEGRATION")
        print("=" * 70 + "\n")
        floor_config = self._setup_floor_integration()

        # Compile configuration
        self.config = {
            'user': user,
            'company': company,
            'ai_backend': ai_config,
            'projects': projects,
            'widgets': widgets,
            'okrs': okrs,
            'floors': floor_config,
            'detected_libraries': self.detected_libraries,
            'detected_functions': self.detected_functions,
            'setup_date': datetime.now().isoformat(),
            'version': '3.0.0'
        }

        # Save to database
        self._save_to_database()

        # Save config file
        self._save_config_file()

        # Show summary
        self._show_setup_summary()

        return self.config

    # ======================== AUTO-DETECTION METHODS ========================

    def _auto_detect_system(self):
        """Auto-detect available libraries, functions, and AI backends"""
        print("\n[1/4] Detecting Python libraries...")
        self._detect_libraries()

        print("[2/4] Scanning for LightSpeed functions...")
        self._detect_functions()

        print("[3/4] Checking AI backends...")
        self._detect_ai_backends()

        print("[4/4] Discovering widgets and templates...")
        self._detect_widgets_and_templates()

        print("\n[OK] System detection complete!")
        self._show_detection_summary()

    def _detect_libraries(self):
        """Detect installed Python libraries"""
        common_libs = [
            'numpy', 'pandas', 'matplotlib', 'scipy', 'sklearn',
            'tkinter', 'PIL', 'requests', 'flask', 'fastapi',
            'sqlalchemy', 'psycopg2', 'pymongo', 'redis',
            'celery', 'pytest', 'black', 'pylint'
        ]

        for lib in common_libs:
            spec = importlib.util.find_spec(lib)
            if spec is not None:
                try:
                    mod = importlib.import_module(lib)
                    version = getattr(mod, '__version__', 'unknown')
                    self.detected_libraries[lib] = {
                        'available': True,
                        'version': version,
                        'location': spec.origin if spec.origin else 'unknown'
                    }
                except:
                    self.detected_libraries[lib] = {'available': False}
            else:
                self.detected_libraries[lib] = {'available': False}

    def _detect_functions(self):
        """Scan LightSpeed codebase for available functions"""
        function_categories = {
            'data_processing': [],
            'visualization': [],
            'ai_ml': [],
            'database': [],
            'api': [],
            'testing': [],
            'automation': []
        }

        # Scan Z-floors for capabilities
        z_axis_path = self.root / "Z Axis"
        if z_axis_path.exists():
            for floor_path in z_axis_path.iterdir():
                if floor_path.is_dir() and floor_path.name.startswith('Z'):
                    manifest_path = floor_path / "_FLOOR_MANIFEST.json"
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                manifest = json.load(f)
                                floor_name = manifest.get('floor_name', 'Unknown')
                                components = manifest.get('components', [])

                                for comp in components:
                                    comp_id = comp.get('id', 'unknown')
                                    category = comp.get('category', 'data_processing')

                                    if category in function_categories:
                                        function_categories[category].append({
                                            'id': comp_id,
                                            'floor': floor_name,
                                            'module': comp.get('module', '')
                                        })
                        except:
                            pass

        self.detected_functions = function_categories

    def _detect_ai_backends(self):
        """Detect available AI backends (Ollama, Achilles)"""
        # Check Ollama (prefer stdlib HTTP; avoid depending on `curl`)
        ollama_host = 'http://localhost:11434'
        try:
            import urllib.request
            import urllib.error

            req = urllib.request.Request(f"{ollama_host}/api/version", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                payload = resp.read().decode("utf-8", errors="replace")
                if resp.status >= 200 and resp.status < 300 and payload:
                    version_info = None
                    try:
                        version_info = json.loads(payload)
                    except Exception:
                        version_info = {"raw": payload.strip()}

                    self.ai_backends_available['ollama'] = {
                        'available': True,
                        'host': ollama_host,
                        'status': 'connected',
                        'version': version_info
                    }
                else:
                    self.ai_backends_available['ollama'] = {
                        'available': False,
                        'host': ollama_host,
                        'status': 'not_running'
                    }
        except Exception:
            self.ai_backends_available['ollama'] = {
                'available': False,
                'host': ollama_host,
                'status': 'not_running'
            }

        # Check for Achilles (future)
        achilles_path = self.root / "Z Axis" / "Z+2_Neo" / "components" / "achilles_connector.py"
        self.ai_backends_available['achilles'] = {
            'available': achilles_path.exists(),
            'status': 'pending' if achilles_path.exists() else 'not_available',
            'transition_date': '2025-Q2'
        }

    def _detect_widgets_and_templates(self):
        """Detect available widgets and layout templates"""
        # ------------------------------------------------------------------
        # Widget discovery (floor-native; best-effort, never crash wizard)
        # ------------------------------------------------------------------
        self.available_widgets = []

        try:
            linker_path = (self.root / "Z Axis" / "Z0_TheConstruct" / "tools" / "ComponentLinker.py").resolve()
            if linker_path.exists():
                spec = importlib.util.spec_from_file_location("lightspeed_component_linker", linker_path)
                if spec is not None and spec.loader is not None:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = mod
                    spec.loader.exec_module(mod)
                    ComponentLinker = getattr(mod, "ComponentLinker")
                    linker = ComponentLinker(self.root)
                    components = linker.discover_all_components()

                    for info in components.values():
                        if getattr(info, "component_type", "") != "ui":
                            continue
                        name = getattr(info, "name", "") or getattr(info, "key", "ui")
                        key = getattr(info, "key", name)
                        path = getattr(info, "path", "")
                        self.available_widgets.append(
                            {
                                "name": str(name),
                                "id": str(key),
                                "path": str(path),
                                "category": "ui",
                            }
                        )
        except Exception:
            pass

        # Fallback: look for legacy *_widget.py patterns if linker isn't available.
        if not self.available_widgets:
            widget_paths = [
                self.root / "Z Axis" / "Z+3_Trinity" / "components",
                self.root / "Z Axis" / "Z+3_Trinity" / "widgets",
                self.root / "Z Axis" / "Z0_TheConstruct" / "ui",
            ]

            for widget_path in widget_paths:
                if widget_path.exists():
                    for file in widget_path.glob("*_widget.py"):
                        widget_name = file.stem.replace("_widget", "").replace("_", " ").title()
                        self.available_widgets.append(
                            {
                                "name": widget_name,
                                "id": file.stem,
                                "path": str(file),
                                "category": "dashboard",
                            }
                        )

        # ------------------------------------------------------------------
        # Template discovery (registry-backed; falls back to a few defaults)
        # ------------------------------------------------------------------
        self.available_templates = []
        try:
            from core.services.template_system import get_template_registry  # type: ignore

            registry = get_template_registry()
            for template_name in registry.list_templates():
                try:
                    tmpl = registry.get_template(template_name)
                    meta = getattr(tmpl, "metadata", None)
                    self.available_templates.append(
                        {
                            "name": str(template_name),
                            "id": str(template_name),
                            "description": getattr(meta, "description", "") if meta else "",
                            "category": getattr(meta, "category", "") if meta else "",
                            "version": getattr(meta, "version", "") if meta else "",
                        }
                    )
                except Exception:
                    self.available_templates.append(
                        {"name": str(template_name), "id": str(template_name), "description": "", "category": "", "version": ""}
                    )
        except Exception:
            self.available_templates = [
                {
                    "name": "Default Layout",
                    "id": "default",
                    "description": "Standard dashboard layout",
                    "category": "ui",
                    "version": "1.0",
                }
            ]

    def _show_detection_summary(self):
        """Show detection results summary"""
        print("\n" + "-" * 70)
        print("DETECTION SUMMARY")
        print("-" * 70)

        # Libraries
        available_libs = [k for k, v in self.detected_libraries.items() if v.get('available')]
        print(f"  Libraries:  {len(available_libs)}/{len(self.detected_libraries)} available")

        # Functions
        total_funcs = sum(len(v) for v in self.detected_functions.values())
        print(f"  Functions:  {total_funcs} discovered across Z-floors")

        # AI Backends
        ai_available = [k for k, v in self.ai_backends_available.items() if v.get('available')]
        print(f"  AI Backends: {', '.join(ai_available) if ai_available else 'None detected'}")

        # Widgets
        print(f"  Widgets:     {len(self.available_widgets)} available")
        print(f"  Templates:   {len(self.available_templates)} layouts")

        print("-" * 70 + "\n")

    # ======================== SETUP METHODS ========================

    def _setup_user_profile(self) -> Optional[Dict]:
        """Setup user profile"""

        print("Create your user profile:\n")

        # Username
        while True:
            username = input("Username (lowercase, no spaces): ").strip().lower()
            if username and ' ' not in username:
                break
            print("  Invalid username. Try again.")

        # Full name
        full_name = input("Full name: ").strip()

        # Email
        email = input("Email (optional): ").strip()

        # Role
        print("\nSelect your role:")
        print("  1. Founder/Owner")
        print("  2. IT Administrator")
        print("  3. Project Manager")
        print("  4. Engineer/Developer")
        print("  5. Analyst/Researcher")
        print("  6. Other")

        role_map = {
            '1': 'founder',
            '2': 'admin',
            '3': 'project_manager',
            '4': 'engineer',
            '5': 'analyst',
            '6': 'user'
        }

        role_choice = input("Choice (1-6): ").strip()
        role = role_map.get(role_choice, 'user')

        user = {
            'username': username,
            'full_name': full_name,
            'email': email or None,
            'role': role,
            'clearance_level': 5 if role in ['founder', 'admin'] else 3
        }

        print(f"\n[OK] User profile created: {username} ({role})")

        return user

    def _setup_company(self) -> Optional[Dict]:
        """Setup company information"""

        print("Company information:\n")

        # Company name
        company_name = input("Company name (or press Enter to skip): ").strip()
        if not company_name:
            company_name = "Default Organization"

        # Industry
        print("\nSelect industry:")
        print("  1. Space Technology")
        print("  2. Green Technology")
        print("  3. Software/IT")
        print("  4. Research/Academia")
        print("  5. Consulting")
        print("  6. Other")

        industry_map = {
            '1': 'space_tech',
            '2': 'green_tech',
            '3': 'software',
            '4': 'research',
            '5': 'consulting',
            '6': 'other'
        }

        industry_choice = input("Choice (1-6, or Enter for Other): ").strip()
        industry = industry_map.get(industry_choice, 'other')

        company = {
            'name': company_name,
            'industry': industry,
            'established': datetime.now().year
        }

        print(f"\n[OK] Company configured: {company_name}")

        return company

    def _setup_projects(self) -> List[Dict]:
        """Setup initial projects"""

        print("Projects:\n")
        print("LightSpeed organizes work into projects.\n")

        projects = []

        # At least one project
        while True:
            project_name = input(f"Project #{len(projects)+1} name (or Enter to finish): ").strip()

            if not project_name:
                if len(projects) == 0:
                    print("  You need at least one project.")
                    continue
                else:
                    break

            # Project type
            print(f"\nType for '{project_name}':")
            print("  1. Research & Development")
            print("  2. Operations")
            print("  3. Analysis")
            print("  4. Planning")

            ptype_map = {
                '1': 'r_and_d',
                '2': 'operations',
                '3': 'analysis',
                '4': 'planning'
            }

            ptype_choice = input("Choice (1-4): ").strip()
            ptype = ptype_map.get(ptype_choice, 'operations')

            projects.append({
                'name': project_name,
                'type': ptype,
                'status': 'active',
                'created': datetime.now().isoformat()
            })

            print(f"  [OK] Added project: {project_name}")

        print(f"\n[OK] Configured {len(projects)} project(s)")

        return projects

    def _setup_ai_backend(self) -> Dict:
        """Setup AI backend configuration (Ollama/Achilles)"""
        print("AI Backend Configuration:\n")

        ai_config = {
            'backend': 'none',
            'ollama': {'enabled': False},
            'achilles': {'enabled': False},
            'mode': 'clippy'
        }

        # Show detected backends
        if self.ai_backends_available.get('ollama', {}).get('available'):
            print("[OK] Ollama detected and running")
            print("    Host: http://localhost:11434\n")

            use_ollama = input("Enable Ollama integration? (y/n): ").strip().lower()
            if use_ollama == 'y':
                ai_config['backend'] = 'ollama'
                ai_config['ollama']['enabled'] = True
                ai_config['ollama']['host'] = 'http://localhost:11434'

                # Model selection
                print("\nAvailable models:")
                print("  1. llama3.2 (recommended)")
                print("  2. codellama")
                print("  3. mistral")
                print("  4. phi3")
                print("  5. Custom (enter model name)")

                model_choice = input("Select model (1-5): ").strip()
                model_map = {
                    '1': 'llama3.2',
                    '2': 'codellama',
                    '3': 'mistral',
                    '4': 'phi3'
                }

                if model_choice in model_map:
                    ai_config['ollama']['model'] = model_map[model_choice]
                elif model_choice == '5':
                    custom_model = input("Enter model name: ").strip()
                    ai_config['ollama']['model'] = custom_model
                else:
                    ai_config['ollama']['model'] = 'llama3.2'

                # Mode selection
                print("\nAI Mode:")
                print("  1. Clippy - Friendly assistant for clients")
                print("  2. Orchestrator - Technical assistant for IT/Founder")

                mode_choice = input("Select mode (1-2): ").strip()
                ai_config['mode'] = 'orchestrator' if mode_choice == '2' else 'clippy'

                print(f"\n[OK] Ollama configured: {ai_config['ollama']['model']} in {ai_config['mode']} mode")
        else:
            print("[!] Ollama not detected")
            print("    To install: https://ollama.com/download")
            print("    After installation, run: ollama pull llama3.2\n")

        # Achilles (future)
        if self.ai_backends_available.get('achilles', {}).get('available'):
            print("\n[INFO] Achilles AI framework detected")
            print(f"      Transition planned for: {self.ai_backends_available['achilles'].get('transition_date')}")
            print("      Currently in development mode\n")
        else:
            print("\n[INFO] Achilles AI: Coming in 2025 Q2")
            print("      Advanced custom AI with Cognigrex integration\n")

        return ai_config

    def _setup_widget_layout(self) -> Dict:
        """Setup widget layout with template selection"""

        print("Widget Layout Builder:\n")

        # Show available templates
        print("Layout Templates:\n")
        for i, template in enumerate(self.available_templates, 1):
            print(f"  {i}. {template['name']}")
            print(f"     {template['description']}")
            print(f"     Widgets: {', '.join(template['widgets'])}\n")

        print(f"  {len(self.available_templates) + 1}. Custom - Build your own layout")

        template_choice = input(f"\nSelect template (1-{len(self.available_templates) + 1}): ").strip()

        # Template selection
        if template_choice.isdigit() and 1 <= int(template_choice) <= len(self.available_templates):
            selected_template = self.available_templates[int(template_choice) - 1]
            print(f"\n[OK] Selected template: {selected_template['name']}")

            widgets = {w: True for w in selected_template['widgets']}
            layout_type = selected_template['id']
        else:
            # Custom layout builder
            print("\nCustom Layout Builder:\n")
            print("Available widgets:")
            print("  1. System Status (CPU, memory, health)")
            print("  2. Fleet Monitoring (Mark III/V units)")
            print("  3. Simulation Results (recent runs)")
            print("  4. AI Recommendations (Cognigrex)")
            print("  5. Project Tasks (current tasks)")
            print("  6. Database Stats (table counts, sizes)")
            print("  7. Code Analysis (Morpheus insights)")
            print("  8. Network Graph (component connections)")

            # Additional discovered widgets
            if self.available_widgets:
                print(f"  9. OKR Widget")
                print(f"  10. Calendar Widget")
                for i, widget in enumerate(self.available_widgets[:5], 11):
                    print(f"  {i}. {widget['name']}")

            selected = input("\nSelect widgets (e.g., 1,2,4,5 or 'all'): ").strip().lower()

            widget_map = {
                '1': 'system_status',
                '2': 'fleet_monitoring',
                '3': 'simulation_results',
                '4': 'ai_recommendations',
                '5': 'project_tasks',
                '6': 'database_stats',
                '7': 'code_analysis',
                '8': 'network_graph',
                '9': 'okr_widget',
                '10': 'calendar_widget'
            }

            if selected == 'all':
                widgets = {name: True for name in widget_map.values()}
            else:
                widgets = {name: False for name in widget_map.values()}
                for choice in selected.replace(' ', '').split(','):
                    if choice in widget_map:
                        widgets[widget_map[choice]] = True

            layout_type = 'custom'

        enabled_count = sum(1 for v in widgets.values() if v)
        print(f"\n[OK] Enabled {enabled_count} widget(s)")

        # Layout configuration
        print("\nLayout Grid:")
        print("  1. 2-Column (wide widgets)")
        print("  2. 3-Column (balanced)")
        print("  3. 4-Column (compact)")

        grid_choice = input("Select grid (1-3, default 3-column): ").strip()
        grid_map = {'1': 2, '2': 3, '3': 4}
        grid_columns = grid_map.get(grid_choice, 3)

        return {
            'enabled_widgets': widgets,
            'layout_type': layout_type,
            'grid_columns': grid_columns,
            'template_based': layout_type != 'custom'
        }

    def _setup_okrs(self) -> List[Dict]:
        """Setup OKRs (optional)"""

        print("Objectives & Key Results (OKRs):\n")
        print("OKRs help track goals and metrics.\n")

        setup_okrs = input("Would you like to set up OKRs now? (y/n): ").strip().lower()

        if setup_okrs != 'y':
            print("  Skipped - You can add OKRs later from Settings")
            return []

        okrs = []

        print("\nExample OKR:")
        print("  Objective: Launch Mark III extraction mission")
        print("    Key Result 1: Complete simulator testing (0/100)")
        print("    Key Result 2: Identify 3 target asteroids (0/3)")
        print("    Key Result 3: Secure $5M funding (0/$5M)\n")

        while True:
            objective = input(f"Objective #{len(okrs)+1} (or Enter to finish): ").strip()

            if not objective:
                break

            # Key results
            key_results = []
            while True:
                kr = input(f"  Key Result #{len(key_results)+1} (or Enter to finish): ").strip()
                if not kr:
                    break

                # Target value
                target = input(f"    Target value (e.g., 100, $5M, 3 units): ").strip()

                key_results.append({
                    'description': kr,
                    'target': target,
                    'current': 0,
                    'unit': 'count'
                })

            if key_results:
                okrs.append({
                    'objective': objective,
                    'key_results': key_results,
                    'quarter': f"Q{(datetime.now().month-1)//3 + 1} {datetime.now().year}",
                    'status': 'active'
                })

                print(f"  [OK] Added OKR: {objective}")

        print(f"\n[OK] Configured {len(okrs)} OKR(s)")

        return okrs

    def _setup_floor_integration(self) -> Dict:
        """Setup Z-floor integration"""
        print("Z-Floor Integration:\n")
        print("LightSpeed uses an 8-layer Z-stack architecture (Z-4 to Z+3).\n")

        floor_config = {
            'auto_initialize': True,
            'initialization_order': 'inside_out',  # Z-4 to Z+3
            'enabled_floors': [],
            'floor_loader_enabled': True
        }

        # Show detected floors
        z_axis_path = self.root / "Z Axis"
        if z_axis_path.exists():
            detected_floors = []
            for floor_path in z_axis_path.iterdir():
                if floor_path.is_dir() and floor_path.name.startswith('Z'):
                    manifest_path = floor_path / "_FLOOR_MANIFEST.json"
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                manifest = json.load(f)
                                detected_floors.append({
                                    'id': manifest.get('floor_id'),
                                    'name': manifest.get('floor_name'),
                                    'z_level': manifest.get('z_level'),
                                    'components': len(manifest.get('components', []))
                                })
                        except:
                            pass

            # Sort by z_level
            detected_floors.sort(key=lambda f: f['z_level'])

            print(f"Detected {len(detected_floors)} Z-floors:\n")
            for floor in detected_floors:
                print(f"  {floor['id']:6s} - {floor['name']:15s} ({floor['components']} components)")

            floor_config['enabled_floors'] = [f['id'] for f in detected_floors]
            floor_config['total_floors'] = len(detected_floors)
            floor_config['total_components'] = sum(f['components'] for f in detected_floors)

            print(f"\n[OK] All {len(detected_floors)} floors will be initialized")
            print(f"    Initialization order: Inside-out (Z-4 -> Z+3)")
            print(f"    Total components: {floor_config['total_components']}")
        else:
            print("[!] Z Axis directory not found")
            floor_config['floor_loader_enabled'] = False

        # Integration systems
        print("\nIntegration Systems:")
        integration_systems = [
            ('FloorLoader', 'Dynamic Z-floor component discovery'),
            ('Data Accumulation Engine', '10 data types with automatic floor assignment'),
            ('Smart Floor Expansion', 'Autonomous capability development'),
            ('AI Orchestrator', 'Unified AI management (Ollama + Achilles)')
        ]

        for system, description in integration_systems:
            print(f"  [OK] {system}")
            print(f"      {description}")

        floor_config['integration_systems'] = [s[0] for s in integration_systems]

        print("\n[OK] Z-floor integration configured")

        return floor_config

    def _save_to_database(self):
        """Save configuration to database"""

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            # Save user (upsert by username)
            user = self.config.get("user") or {}
            username = (user.get("username") or "").strip()
            if username:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO users (username, fullname, email, role, clearance, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        username,
                        user.get("fullname"),
                        user.get("email"),
                        user.get("role") or "user",
                        int(user.get("clearance") or 1),
                        now,
                        now,
                    ),
                )
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                user_id = int(row[0]) if row else None
                if user_id is not None:
                    cursor.execute(
                        """
                        UPDATE users
                        SET fullname = ?, email = ?, role = ?, clearance = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            user.get("fullname"),
                            user.get("email"),
                            user.get("role") or "user",
                            int(user.get("clearance") or 1),
                            now,
                            user_id,
                        ),
                    )
            else:
                user_id = None

            # Save company (select-or-insert by name)
            company = self.config.get("company") or {}
            company_name = (company.get("name") or "").strip()
            company_id = None
            if company_name:
                cursor.execute("SELECT id FROM companies WHERE name = ? LIMIT 1", (company_name,))
                row = cursor.fetchone()
                if row:
                    company_id = int(row[0])
                    cursor.execute(
                        "UPDATE companies SET industry = ?, updated_at = ? WHERE id = ?",
                        (company.get("industry"), now, company_id),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO companies (name, industry, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (company_name, company.get("industry"), now, now),
                    )
                    company_id = cursor.lastrowid

            # Save projects (insert if missing; otherwise update status/metadata)
            for project in (self.config.get("projects") or []):
                pname = (project.get("name") or "").strip()
                if not pname:
                    continue
                status = project.get("status") or "active"
                created_at = project.get("created") or now
                ptype = project.get("type")

                if company_id is not None:
                    cursor.execute(
                        "SELECT id FROM projects WHERE name = ? AND company_id = ? LIMIT 1",
                        (pname, company_id),
                    )
                    prow = cursor.fetchone()
                else:
                    cursor.execute("SELECT id FROM projects WHERE name = ? LIMIT 1", (pname,))
                    prow = cursor.fetchone()

                if prow:
                    pid = int(prow[0])
                    cursor.execute(
                        "UPDATE projects SET status = ?, type = ?, updated_at = ? WHERE id = ?",
                        (status, ptype, now, pid),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO projects (name, company_id, status, type, owner_id, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (pname, company_id, status, ptype, user_id, created_at, now),
                    )

            conn.commit()
            conn.close()

            print("\n[OK] Saved to database")

        except Exception as e:
            print(f"\n[!] Database save error: {e}")

    def _save_config_file(self):
        """Save configuration to file"""

        config_dir = self.root / "config"
        config_dir.mkdir(exist_ok=True)

        # User config
        config_file = config_dir / "user_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
        print(f"[OK] Saved user configuration: {config_file}")

        # AI config (for AI Orchestrator)
        if self.config.get('ai_backend'):
            ai_config_file = config_dir / "ai_config.json"
            ai_config_data = {
                'ollama': self.config['ai_backend'].get('ollama', {}),
                'achilles': self.config['ai_backend'].get('achilles', {}),
                'modes': {
                    'clippy': {
                        'system_prompt': 'You are Clippy, a friendly LightSpeed assistant.',
                        'tone': 'friendly'
                    },
                    'orchestrator': {
                        'system_prompt': 'You are the LightSpeed Orchestrator AI.',
                        'tone': 'professional'
                    }
                }
            }
            with open(ai_config_file, 'w', encoding='utf-8') as f:
                json.dump(ai_config_data, f, indent=2)
            print(f"[OK] Saved AI configuration: {ai_config_file}")

        # Widget layout config
        if self.config.get('widgets'):
            layout_config_file = config_dir / "layout_config.json"
            with open(layout_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config['widgets'], f, indent=2)
            print(f"[OK] Saved widget layout: {layout_config_file}")

        # Library registry
        if self.detected_libraries:
            library_registry_file = config_dir / "library_registry.json"
            with open(library_registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.detected_libraries, f, indent=2)
            print(f"[OK] Saved library registry: {library_registry_file}")

        # Function registry
        if self.detected_functions:
            function_registry_file = config_dir / "function_registry.json"
            with open(function_registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.detected_functions, f, indent=2)
            print(f"[OK] Saved function registry: {function_registry_file}")

    def _show_setup_summary(self):
        """Show setup summary"""

        print("\n" + "=" * 70)
        print("SETUP COMPLETE - LIGHTSPEED v3.0.0")
        print("=" * 70 + "\n")

        # User & Company
        print(f"User:     {self.config['user']['username']} ({self.config['user']['role']})")
        print(f"Company:  {self.config['company']['name']}")
        print(f"Projects: {len(self.config['projects'])}")

        if self.config['projects']:
            for p in self.config['projects']:
                print(f"  - {p['name']} ({p['type']})")

        # AI Backend
        if self.config.get('ai_backend'):
            backend = self.config['ai_backend'].get('backend', 'none')
            if backend == 'ollama':
                model = self.config['ai_backend']['ollama'].get('model', 'unknown')
                mode = self.config['ai_backend'].get('mode', 'clippy')
                print(f"\nAI Backend: Ollama ({model}) in {mode} mode")
            elif backend == 'achilles':
                print(f"\nAI Backend: Achilles (custom AI)")
            else:
                print(f"\nAI Backend: Not configured")

        # Widgets & Layout
        if self.config.get('widgets'):
            widgets_data = self.config['widgets']
            if 'enabled_widgets' in widgets_data:
                enabled_count = sum(1 for v in widgets_data['enabled_widgets'].values() if v)
                layout_type = widgets_data.get('layout_type', 'default')
                grid_cols = widgets_data.get('grid_columns', 3)
                print(f"\nDashboard: {enabled_count} widgets in {grid_cols}-column {layout_type} layout")
            else:
                # Legacy format
                enabled_count = sum(1 for v in widgets_data.values() if v)
                print(f"\nWidgets:   {enabled_count} enabled")

        # OKRs
        if self.config.get('okrs'):
            print(f"OKRs:      {len(self.config['okrs'])} configured")

        # Z-Floors
        if self.config.get('floors'):
            floor_data = self.config['floors']
            total_floors = floor_data.get('total_floors', 0)
            total_components = floor_data.get('total_components', 0)
            print(f"\nZ-Floors:  {total_floors} floors, {total_components} components")
            print(f"           Inside-out initialization (Z-4 -> Z+3)")

        # Detection Summary
        print(f"\nSystem Detection:")
        available_libs = [k for k, v in self.detected_libraries.items() if v.get('available')]
        print(f"  Libraries:  {len(available_libs)} available")

        total_funcs = sum(len(v) for v in self.detected_functions.values())
        print(f"  Functions:  {total_funcs} discovered")

        print("\n" + "=" * 70)
        print("Your LightSpeed platform is ready!")
        print("=" * 70 + "\n")

        print("Launch Options:")
        print("  python StartLightSpeed.py              # Full platform")
        print("  python StartLightSpeed.py --portal N   # N portal")
        print("  python StartLightSpeed.py --portal IT  # IT portal")
        print("  python StartLightSpeed.py --portal 3D  # 3D immersive")
        print("  python StartLightSpeed.py --health     # Health check")

        print("\n" + "=" * 70 + "\n")


class SetupWizardWindow:
    """
    UI-only Setup Wizard (no terminal prompts).

    This wraps the existing SetupWizard persistence format, but gathers inputs via Tk.
    """

    def __init__(self, parent=None, on_complete=None, title: str = "LightSpeed Setup Wizard"):
        try:
            import tkinter as tk
            from tkinter import ttk, messagebox, simpledialog
        except Exception as e:
            raise RuntimeError(f"tkinter is required for SetupWizardWindow: {e}")

        self._tk = tk
        self._ttk = ttk
        self._messagebox = messagebox
        self._simpledialog = simpledialog

        self._root, owner = _safe_tk_parent(parent)
        self._owner = owner
        self._on_complete = on_complete

        self.window = tk.Toplevel(owner) if owner is not None else tk.Toplevel()
        self.window.title(title)
        self.window.geometry("900x650")
        self.window.minsize(840, 600)

        # State
        self._step_index = 0
        self._steps = []

        self.var_username = tk.StringVar(value="nathaniel.bouwer")
        self.var_fullname = tk.StringVar(value="Nathaniel Bouwer")
        self.var_email = tk.StringVar(value="")
        self.var_role = tk.StringVar(value="founder")
        self.var_clearance = tk.IntVar(value=5)

        self.var_company_name = tk.StringVar(value="Romer Industries / EMASSC")
        self.var_industry = tk.StringVar(value="technology")

        self.var_ai_backend = tk.StringVar(value="none")
        self.var_ollama_host = tk.StringVar(value="http://localhost:11434")
        self.var_ollama_model = tk.StringVar(value="llama3.2")
        self.var_ai_mode = tk.StringVar(value="orchestrator")

        self.projects: List[Dict[str, Any]] = [
            {"name": "LightSpeed", "type": "r_and_d", "status": "active", "created": datetime.now().isoformat()}
        ]

        self._build_ui()
        self._show_step(0)

        # Ensure clean shutdown for hidden root
        self.window.protocol("WM_DELETE_WINDOW", self.close)

    def close(self):
        global _ACTIVE_SETUP_WIZARD_WINDOW
        try:
            self.window.destroy()
        finally:
            try:
                if _ACTIVE_SETUP_WIZARD_WINDOW is self:
                    _ACTIVE_SETUP_WIZARD_WINDOW = None
            except Exception:
                _ACTIVE_SETUP_WIZARD_WINDOW = None
            if self._root is not None:
                try:
                    self._root.destroy()
                except Exception:
                    pass

    def _build_ui(self):
        tk = self._tk
        ttk = self._ttk

        # Header
        header = ttk.Frame(self.window, padding=(16, 14))
        header.pack(fill="x")
        ttk.Label(header, text="LightSpeed Setup Wizard", font=("Segoe UI", 16, "bold")).pack(side="left")
        self.step_label = ttk.Label(header, text="", font=("Segoe UI", 10))
        self.step_label.pack(side="right")

        # Content
        self.content = ttk.Frame(self.window, padding=(16, 0))
        self.content.pack(fill="both", expand=True)

        # Footer buttons
        footer = ttk.Frame(self.window, padding=(16, 14))
        footer.pack(fill="x")
        self.btn_back = ttk.Button(footer, text="Back", command=self._back)
        self.btn_back.pack(side="left")
        self.btn_next = ttk.Button(footer, text="Next", command=self._next)
        self.btn_next.pack(side="right")
        self.btn_finish = ttk.Button(footer, text="Finish", command=self._finish)
        self.btn_finish.pack(side="right", padx=(0, 8))

        # Steps (built lazily/rebuildable to avoid Tk widget lifecycle edge cases)
        self._step_builders = [
            self._build_step_profile,
            self._build_step_company_projects,
            self._build_step_ai_and_save,
        ]
        # Build step frames on-demand to avoid "bad window path name" errors when
        # Tk widgets are recreated or the parent window lifecycle changes.
        self._steps = [None for _ in self._step_builders]

    def _clear_content(self):
        # Do NOT destroy step frames: they are reused across navigation.
        for child in self.content.winfo_children():
            try:
                child.pack_forget()
            except Exception:
                # If a child isn't pack-managed, leave it alone rather than destroying.
                pass

    def _ensure_step_frame(self, idx: int):
        """Return a valid step frame, rebuilding it if it was destroyed."""
        idx = max(0, min(idx, len(self._steps) - 1))
        frame = self._steps[idx]
        try:
            if frame is not None and getattr(frame, "winfo_exists", lambda: False)():
                return frame
        except Exception:
            pass

        # Rebuild the step frame (best-effort; avoids hard crashes on Tk widget lifecycle quirks).
        try:
            frame = self._step_builders[idx]()
            self._steps[idx] = frame
            return frame
        except Exception as e:
            raise RuntimeError(f"Setup Wizard step {idx} could not be rebuilt: {e}") from e

    def _show_step(self, idx: int):
        # If the window has already been closed/destroyed, ignore navigation events.
        try:
            if not self.window.winfo_exists():
                return
        except Exception:
            return

        idx = max(0, min(idx, len(self._steps) - 1))
        self._step_index = idx

        try:
            if not self.content.winfo_exists():
                return
        except Exception:
            return

        self._clear_content()
        frame = self._ensure_step_frame(idx)
        try:
            frame.pack(fill="both", expand=True)
        except Exception:
            # Avoid surfacing Tk widget path errors to the user; they can re-open the wizard.
            return

        titles = ["Profile", "Company & Projects", "AI & Save"]
        self.step_label.config(text=f"Step {idx + 1}/{len(self._steps)} — {titles[idx]}")

        self.btn_back.config(state=("disabled" if idx == 0 else "normal"))
        self.btn_next.config(state=("disabled" if idx == len(self._steps) - 1 else "normal"))
        self.btn_finish.config(state=("normal" if idx == len(self._steps) - 1 else "disabled"))

    def _back(self):
        self._show_step(self._step_index - 1)

    def _next(self):
        if not self._validate_step(self._step_index):
            return
        self._show_step(self._step_index + 1)

    def _validate_step(self, idx: int) -> bool:
        msg = self._messagebox
        if idx == 0:
            if not self.var_username.get().strip():
                msg.showerror("Validation", "Username is required.", parent=self.window)
                return False
            return True
        if idx == 1:
            if not self.var_company_name.get().strip():
                msg.showerror("Validation", "Company name is required.", parent=self.window)
                return False
            if not self.projects:
                msg.showerror("Validation", "Add at least one project.", parent=self.window)
                return False
            return True
        return True

    def _build_step_profile(self):
        tk = self._tk
        ttk = self._ttk

        frame = ttk.Frame(self.content)
        ttk.Label(frame, text="User Profile", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(10, 8))

        form = ttk.Frame(frame)
        form.pack(fill="x", pady=(0, 8))

        def row(label, widget, r):
            ttk.Label(form, text=label).grid(row=r, column=0, sticky="w", padx=(0, 10), pady=6)
            widget.grid(row=r, column=1, sticky="ew", pady=6)

        form.columnconfigure(1, weight=1)

        row("Username", ttk.Entry(form, textvariable=self.var_username), 0)
        row("Full name", ttk.Entry(form, textvariable=self.var_fullname), 1)
        row("Email", ttk.Entry(form, textvariable=self.var_email), 2)

        role_combo = ttk.Combobox(form, textvariable=self.var_role, state="readonly",
                                  values=["founder", "admin", "engineer", "analyst", "user"])
        row("Role", role_combo, 3)

        clearance = ttk.Spinbox(form, from_=1, to=5, textvariable=self.var_clearance, width=10)
        row("Clearance", clearance, 4)

        ttk.Label(
            frame,
            text="Setup is UI-only. All configuration is saved into `Z Axis/Z-4_Merovingian/data/db/lightspeed_unified.db` and `config/*.json`.",
            wraplength=820,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))

        return frame

    def _build_step_company_projects(self):
        tk = self._tk
        ttk = self._ttk
        msg = self._messagebox

        frame = ttk.Frame(self.content)
        ttk.Label(frame, text="Company & Projects", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(10, 8))

        company = ttk.LabelFrame(frame, text="Company", padding=10)
        company.pack(fill="x", pady=(0, 10))
        ttk.Label(company, text="Name").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
        name_entry = ttk.Entry(company, textvariable=self.var_company_name)
        name_entry.grid(row=0, column=1, sticky="ew", pady=6)
        company.columnconfigure(1, weight=1)

        ttk.Label(company, text="Industry").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
        industry_combo = ttk.Combobox(
            company,
            textvariable=self.var_industry,
            state="readonly",
            values=["technology", "manufacturing", "services", "healthcare", "education", "finance", "other"],
        )
        industry_combo.grid(row=1, column=1, sticky="w", pady=6)

        projects = ttk.LabelFrame(frame, text="Projects", padding=10)
        projects.pack(fill="both", expand=True)

        self.projects_list = tk.Listbox(projects, height=8)
        self.projects_list.pack(side="left", fill="both", expand=True)

        def refresh_projects():
            self.projects_list.delete(0, "end")
            for p in self.projects:
                self.projects_list.insert("end", f"{p['name']}  [{p.get('type', 'operations')}]")

        def add_project():
            name = self._simpledialog.askstring("Project", "Project name:", parent=self.window)
            if not name:
                return
            ptype = self._simpledialog.askstring(
                "Project", "Project type (r_and_d / operations / analysis / planning):", parent=self.window
            ) or "operations"
            self.projects.append(
                {"name": name.strip(), "type": ptype.strip(), "status": "active", "created": datetime.now().isoformat()}
            )
            refresh_projects()

        def remove_project():
            sel = self.projects_list.curselection()
            if not sel:
                return
            idx = int(sel[0])
            if idx < 0 or idx >= len(self.projects):
                return
            if not msg.askyesno("Remove Project", f"Remove project '{self.projects[idx]['name']}'?", parent=self.window):
                return
            self.projects.pop(idx)
            refresh_projects()

        buttons = ttk.Frame(projects)
        buttons.pack(side="right", fill="y", padx=(10, 0))
        ttk.Button(buttons, text="Add", command=add_project).pack(fill="x", pady=4)
        ttk.Button(buttons, text="Remove", command=remove_project).pack(fill="x", pady=4)
        ttk.Button(buttons, text="Refresh", command=refresh_projects).pack(fill="x", pady=(12, 4))

        refresh_projects()
        return frame

    def _build_step_ai_and_save(self):
        ttk = self._ttk

        frame = ttk.Frame(self.content)
        ttk.Label(frame, text="AI Backend & Save", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(10, 8))

        ai = ttk.LabelFrame(frame, text="AI Backend (optional)", padding=10)
        ai.pack(fill="x", pady=(0, 10))

        ttk.Label(ai, text="Backend").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
        backend_combo = ttk.Combobox(ai, textvariable=self.var_ai_backend, state="readonly",
                                     values=["none", "ollama", "achilles"])
        backend_combo.grid(row=0, column=1, sticky="w", pady=6)

        ttk.Label(ai, text="Mode").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
        mode_combo = ttk.Combobox(ai, textvariable=self.var_ai_mode, state="readonly",
                                  values=["clippy", "orchestrator"])
        mode_combo.grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(ai, text="Ollama host").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(ai, textvariable=self.var_ollama_host).grid(row=2, column=1, sticky="ew", pady=6)
        ai.columnconfigure(1, weight=1)

        ttk.Label(ai, text="Ollama model").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(ai, textvariable=self.var_ollama_model).grid(row=3, column=1, sticky="w", pady=6)

        status = ttk.LabelFrame(frame, text="Status", padding=10)
        status.pack(fill="both", expand=True)
        self.status_text = self._tk.Text(status, height=10, wrap="word")
        self.status_text.pack(fill="both", expand=True)
        self.status_text.insert("end", "Ready to save configuration.\n")
        self.status_text.configure(state="disabled")

        return frame

    def _append_status(self, text: str):
        widget = getattr(self, "status_text", None)
        try:
            if widget is None or not widget.winfo_exists():
                return
            widget.configure(state="normal")
            widget.insert("end", text.rstrip() + "\n")
            widget.see("end")
            widget.configure(state="disabled")
        except Exception:
            return

    def _finish(self):
        if not self._validate_step(self._step_index):
            return

        self._append_status("Collecting system detection...")

        wizard = SetupWizard()
        try:
            # Silent detection (no interactive prompts)
            wizard._detect_libraries()
            wizard._detect_functions()
            wizard._detect_ai_backends()
            wizard._detect_widgets_and_templates()
        except Exception as e:
            self._append_status(f"[WARN] Detection error: {e}")

        # Build config structure compatible with SetupWizard persistence
        user = {
            "username": self.var_username.get().strip(),
            "fullname": self.var_fullname.get().strip(),
            "email": self.var_email.get().strip(),
            "role": self.var_role.get().strip() or "user",
            "clearance": int(self.var_clearance.get() or 1),
        }
        company = {
            "name": self.var_company_name.get().strip(),
            "industry": self.var_industry.get().strip() or "other",
            "established": datetime.now().year,
        }

        ai_backend = {"backend": "none", "ollama": {"enabled": False}, "achilles": {"enabled": False}, "mode": "clippy"}
        backend_choice = (self.var_ai_backend.get() or "none").strip().lower()
        if backend_choice == "ollama":
            ai_backend = {
                "backend": "ollama",
                "ollama": {
                    "enabled": True,
                    "host": (self.var_ollama_host.get() or "http://localhost:11434").strip(),
                    "model": (self.var_ollama_model.get() or "llama3.2").strip(),
                },
                "achilles": {"enabled": False},
                "mode": (self.var_ai_mode.get() or "clippy").strip(),
            }
        elif backend_choice == "achilles":
            ai_backend = {"backend": "achilles", "ollama": {"enabled": False}, "achilles": {"enabled": True}, "mode": "orchestrator"}

        # Floors: minimal enablement list (folder keys)
        enabled_floors: List[str] = []
        z_axis_path = LIGHTSPEED_ROOT / "Z Axis"
        try:
            if z_axis_path.exists():
                # Only enable floor folders that actually have a manifest (prevents legacy/backup dirs from being treated as active floors).
                enabled_floors = sorted(
                    [
                        p.name
                        for p in z_axis_path.iterdir()
                        if p.is_dir()
                        and p.name.startswith("Z")
                        and (p / "_FLOOR_MANIFEST.json").exists()
                    ]
                )
        except Exception:
            enabled_floors = []

        wizard.config = {
            "user": user,
            "company": company,
            "ai_backend": ai_backend,
            "projects": list(self.projects),
            "widgets": {"layout_type": "bento", "grid_columns": 3, "enabled_widgets": {}},
            "okrs": [],
            "floors": {
                "floor_loader_enabled": True,
                "enabled_floors": enabled_floors,
                "total_floors": len(enabled_floors),
                "total_components": 0,
            },
            "detected_libraries": wizard.detected_libraries,
            "detected_functions": wizard.detected_functions,
            "setup_date": datetime.now().isoformat(),
            "version": "3.0.0",
        }

        self._append_status("Saving to database and config files...")

        try:
            wizard._save_to_database()
            wizard._save_config_file()
            self._append_status("[OK] Saved configuration.")
        except Exception as e:
            self._append_status(f"[ERROR] Save failed: {e}")
            self._messagebox.showerror("Setup Wizard", f"Save failed:\n{e}", parent=self.window)
            return

        try:
            if callable(self._on_complete):
                self._on_complete(wizard.config)
        finally:
            self._messagebox.showinfo("Setup Wizard", "Setup complete.", parent=self.window)
            self.close()


def launch_setup_wizard_ui(parent=None, on_complete=None):
    """Launch the UI-only Setup Wizard window (no terminal prompts)."""
    global _ACTIVE_SETUP_WIZARD_WINDOW
    try:
        win = _ACTIVE_SETUP_WIZARD_WINDOW
        if win is not None and getattr(win, "window", None) is not None and win.window.winfo_exists():
            try:
                win.window.lift()
                win.window.focus_force()
            except Exception:
                pass
            return win
    except Exception:
        _ACTIVE_SETUP_WIZARD_WINDOW = None

    win = SetupWizardWindow(parent=parent, on_complete=on_complete)
    _ACTIVE_SETUP_WIZARD_WINDOW = win
    return win


def run_setup_wizard_ui(parent=None) -> Optional[Dict[str, Any]]:
    """
    Launch the UI-only Setup Wizard and block until it closes.

    Intended for CLI entry points that still want an in-window experience.
    """
    result: Dict[str, Any] = {"config": None}

    def _on_complete(config: Dict[str, Any]) -> None:
        result["config"] = config

    win = SetupWizardWindow(parent=parent, on_complete=_on_complete)

    # If we created a hidden root, drive the event loop until the wizard closes.
    root = getattr(win, "_root", None)
    if root is not None:
        try:
            root.mainloop()
        except KeyboardInterrupt:
            try:
                win.close()
            except Exception:
                pass

    return result.get("config")


if __name__ == "__main__":
    config = run_setup_wizard_ui(parent=None)
    sys.exit(0 if config else 1)
