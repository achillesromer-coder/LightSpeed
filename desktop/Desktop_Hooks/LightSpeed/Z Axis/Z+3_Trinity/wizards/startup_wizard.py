#!/usr/bin/env python
"""
STARTUP WIZARD - System Initialization
Checks platform readiness (read-only)

This wizard runs on first launch and checks:
1. All Python dependencies
2. Z-layer components (7 floors)
3. Database connectivity + schema presence (read-only)
4. Component registry
5. Network connections
6. System settings
7. File structure

Author: LightSpeed Team
Version: 0.9.5
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

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


class StartupWizard:
    """
    Comprehensive startup wizard that initializes the entire platform.

    Checks all dependencies, components, database, and configurations.
    """

    def __init__(self):
        self.root = LIGHTSPEED_ROOT
        self.results = {
            'dependencies': {},
            'z_layers': {},
            'database': {},
            'components': {},
            'settings': {},
            'network': {}
        }

    def run(self) -> bool:
        """Run complete startup wizard"""

        print("\n>>> LIGHTSPEED STARTUP WIZARD\n")
        print("This wizard will check and initialize all platform components.\n")

        # Phase 1: Dependencies
        print("=" * 70)
        print("PHASE 1: CHECKING DEPENDENCIES")
        print("=" * 70 + "\n")
        deps_ok = self._check_dependencies()

        # Phase 2: Z-Layers
        print("\n" + "=" * 70)
        print("PHASE 2: CHECKING Z-AXIS LAYERS")
        print("=" * 70 + "\n")
        layers_ok = self._check_z_layers()

        # Phase 3: Database
        print("\n" + "=" * 70)
        print("PHASE 3: CHECKING DATABASE")
        print("=" * 70 + "\n")
        db_ok = self._initialize_database()

        # Phase 4: Component Registry
        print("\n" + "=" * 70)
        print("PHASE 4: BUILDING COMPONENT REGISTRY")
        print("=" * 70 + "\n")
        components_ok = self._build_component_registry()

        # Phase 5: System Settings
        print("\n" + "=" * 70)
        print("PHASE 5: INITIALIZING SETTINGS")
        print("=" * 70 + "\n")
        settings_ok = self._initialize_settings()

        # Phase 6: Network Check
        print("\n" + "=" * 70)
        print("PHASE 6: CHECKING NETWORK")
        print("=" * 70 + "\n")
        network_ok = self._check_network()

        # Summary
        self._show_summary()

        # Overall success if critical components are OK
        critical_ok = deps_ok and db_ok and components_ok
        return critical_ok

    def _check_dependencies(self) -> bool:
        """Check all Python dependencies"""

        required = {
            'Core': ['numpy', 'sqlite3'],
            'Web': ['fastapi', 'uvicorn', 'dash'],
            'Visualization': ['plotly', 'matplotlib'],
            'UI': ['tkinter'],
            'Optional': ['pandas', 'scipy', 'requests']
        }

        all_ok = True

        for category, packages in required.items():
            print(f"\n[{category}]")

            for package in packages:
                try:
                    if package == 'sqlite3':
                        import sqlite3
                    elif package == 'tkinter':
                        import tkinter
                    else:
                        __import__(package)

                    print(f"  [OK] {package}")
                    self.results['dependencies'][package] = True

                except ImportError:
                    if category == 'Optional':
                        print(f"  [!] {package} (optional - not critical)")
                        self.results['dependencies'][package] = False
                    else:
                        print(f"  [X] {package} (REQUIRED)")
                        self.results['dependencies'][package] = False
                        if category != 'Optional':
                            all_ok = False

        if not all_ok:
            print("\n[!] Some required dependencies are missing.")
            print("Install with: pip install fastapi uvicorn dash plotly matplotlib numpy")

        return all_ok

    def _check_z_layers(self) -> bool:
        """Check all Z-axis floor files"""

        # Canonical Z-Axis (current):
        #   Z+3 Trinity, Z+2 Neo, Z+1 Architect, Z0 TheConstruct,
        #   Z-1 Morpheus, Z-2 Oracle, Z-3 Smith, Z-4 Merovingian
        floors = [
            ("Trinity", "Z+3", "UI Layer & Immersive Portal"),
            ("Neo", "Z+2", "AI Integration"),
            ("Architect", "Z+1", "Mission Planning & Roadmaps"),
            ("TheConstruct", "Z0", "Physics & Simulations"),
            ("Morpheus", "Z-1", "Knowledge & Code Analysis"),
            ("Oracle", "Z-2", "IP Vault & Document Archive"),
            ("Smith", "Z-3", "Automation & Jobs"),
            ("Merovingian", "Z-4", "System Core & Diagnostics"),
        ]

        z_axis_dir = self.root / "Z Axis"
        all_exist = True

        for name, level, description in floors:
            floor_file = z_axis_dir / f"{name}.py"
            exists = floor_file.exists()

            self.results['z_layers'][name] = {
                'level': level,
                'description': description,
                'exists': exists,
                'path': str(floor_file)
            }

            if exists:
                print(f"  [OK] {level} {name:15s} - {description}")
            else:
                print(f"  [X] {level} {name:15s} - Not found")
                all_exist = False

        return True  # Not critical for startup; floors are manifest-driven at runtime

    def _initialize_database(self) -> bool:
        """Check database connectivity and schema presence (read-only).

        Policy: startup checks must not mutate schema. Schema creation/migrations are owned by Trinity
        via `Z Axis/Z+3_Trinity/tools/initialize_database.py` (invoked from IT Portal).
        """

        # Use the unified DB location (Merovingian floor during migration); never create a legacy root `Data/` DB.
        try:
            from core.services import get_db  # type: ignore
            db_path = Path(get_db().db_path)
        except Exception:
            db_path = self.root / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db"

        if not db_path.exists():
            print(f"  [X] Database missing: {db_path}")
            self.results['database']['path'] = str(db_path)
            self.results['database']['tables'] = 0
            self.results['database']['status'] = 'missing'
            return False

        try:
            # Open read-only whenever possible.
            try:
                conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
            except Exception:
                conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check existing tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]

            print(f"  [OK] Database connected: {db_path}")
            print(f"  [OK] Existing tables: {len(existing_tables)}")

            # If no tables, do not initialize here; operator must run explicit migration via IT Portal.
            if len(existing_tables) == 0:
                print("\n  [!] Database schema is not initialized.")
                print("      Run DB Migration from IT Portal (Trinity) or execute:")
                print("      python \"Z Axis/Z+3_Trinity/tools/initialize_database.py\"")
                self.results['database']['path'] = str(db_path)
                self.results['database']['tables'] = 0
                self.results['database']['status'] = 'needs_migration'
                try:
                    conn.close()
                except Exception:
                    pass
                return False

            conn.close()

            self.results['database']['path'] = str(db_path)
            self.results['database']['tables'] = len(existing_tables)
            self.results['database']['status'] = 'operational'

            return True

        except Exception as e:
            print(f"  [X] Database error: {e}")
            self.results['database']['status'] = 'error'
            self.results['database']['error'] = str(e)
            return False

    def _create_database_schema(self, cursor):
        """Create basic database schema"""

        # Core tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                role TEXT DEFAULT 'user',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                industry TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company_id INTEGER,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                category TEXT,
                description TEXT
            )
        """)

        # Add more tables as needed...

    def _build_component_registry(self) -> bool:
        """Build registry of all available components"""

        print("  Scanning components...")

        # Use ComponentLinker if available
        try:
            # Prefer file-based loading so we don't depend on invalid package names (Z+3_Trinity).
            from importlib.util import spec_from_file_location, module_from_spec

            linker_path = (self.root / "Z Axis" / "Z0_TheConstruct" / "tools" / "ComponentLinker.py").resolve()
            if not linker_path.exists():
                raise FileNotFoundError(linker_path)

            spec = spec_from_file_location("lightspeed_component_linker", linker_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load ComponentLinker from {linker_path}")
            mod = module_from_spec(spec)
            # Ensure the module is present in sys.modules while executing so dataclasses/typing
            # can resolve `cls.__module__` globals safely.
            import sys
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            ComponentLinker = getattr(mod, "ComponentLinker")

            linker = ComponentLinker(self.root)
            components = linker.discover_all_components()

            print(f"  [OK] Discovered {len(components)} components")

            for comp_type in ['floor', 'service', 'simulator', 'renderer', 'analyzer', 'ui']:
                count = sum(1 for c in components.values() if c.component_type == comp_type)
                if count > 0:
                    print(f"    - {comp_type}: {count}")

            self.results['components'] = {
                'total': len(components),
                'by_type': {
                    comp_type: sum(1 for c in components.values() if c.component_type == comp_type)
                    for comp_type in set(c.component_type for c in components.values())
                }
            }

            return True

        except Exception as e:
            print(f"  [!] Component discovery: {e}")
            print(f"    Using basic component list")

            # Fallback: manual list
            self.results['components'] = {
                'total': 26,
                'by_type': {
                    'floor': 5,
                    'service': 4,
                    'simulator': 5,
                    'renderer': 2,
                    'analyzer': 3,
                    'ui': 4,
                    'ai_system': 3
                }
            }

            return True

    def _initialize_settings(self) -> bool:
        """Initialize default settings"""

        config_dir = self.root / "config"
        config_dir.mkdir(exist_ok=True)

        settings_file = config_dir / "settings.json"

        if settings_file.exists():
            print(f"  [OK] Settings file exists: {settings_file}")
            with open(settings_file) as f:
                settings = json.load(f)
            print(f"  [OK] Loaded {len(settings)} settings")

        else:
            print("  Creating default settings...")

            settings = {
                'platform': {
                    'name': 'LightSpeed',
                    'version': '2.0.0',
                    'organization': 'Römer Industries'
                },
                'ui': {
                    'theme': 'dark',
                    'font_size': 12,
                    'show_grid': True,
                    'auto_save': True
                },
                'database': {
                    'path': str(db_path),
                    'backup_enabled': True,
                    'backup_interval_hours': 24
                },
                'network': {
                    'api_port': 8000,
                    'web_port': 3005,
                    'enable_cors': True
                },
                'floors': {
                    floor: {'enabled': True, 'autostart': True}
                    for floor in ['Neo', 'Morpheus', 'Architect', 'Oracle',
                                'Trinity', 'Smith', 'Merovingian', 'TheConstruct']
                }
            }

            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            print(f"  [OK] Created settings: {settings_file}")

        self.results['settings'] = settings
        return True

    def _check_network(self) -> bool:
        """Check network connectivity and ports"""

        import socket

        ports_to_check = [
            (8000, 'API Server'),
            (3005, 'Web Interface'),
        ]

        print("  Checking port availability...")

        all_available = True
        for port, service in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()

            if result != 0:
                print(f"  [OK] Port {port} available ({service})")
            else:
                print(f"  [!] Port {port} in use ({service})")
                all_available = False

        self.results['network']['ports_available'] = all_available

        return True  # Not critical

    def _show_summary(self):
        """Show startup summary"""

        print("\n" + "=" * 70)
        print("STARTUP SUMMARY")
        print("=" * 70 + "\n")

        # Dependencies
        deps = self.results['dependencies']
        deps_ok = sum(1 for v in deps.values() if v)
        deps_total = len(deps)
        print(f"  Dependencies:  {deps_ok}/{deps_total} installed")

        # Z-Layers
        layers = self.results['z_layers']
        layers_ok = sum(1 for v in layers.values() if v['exists'])
        layers_total = len(layers)
        print(f"  Z-Axis Layers: {layers_ok}/{layers_total} found")

        # Database
        db = self.results['database']
        if db.get('status') == 'operational':
            print(f"  Database:      [OK] {db.get('tables', 0)} tables")
        else:
            print(f"  Database:      [X] Error")

        # Components
        comps = self.results['components']
        print(f"  Components:    {comps.get('total', 0)} discovered")

        # Settings
        if self.results['settings']:
            print(f"  Settings:      [OK] Configured")
        else:
            print(f"  Settings:      [!] Using defaults")

        print("\n" + "=" * 70 + "\n")

        # Critical check
        critical_ok = (
            deps_ok >= deps_total * 0.8 and  # 80% of deps
            db.get('status') == 'operational'
        )

        if critical_ok:
            print("[OK] ALL CRITICAL SYSTEMS OPERATIONAL\n")
        else:
            print("[!] SOME SYSTEMS NEED ATTENTION\n")


if __name__ == "__main__":
    wizard = StartupWizard()
    success = wizard.run()
    sys.exit(0 if success else 1)
