#!/usr/bin/env python
"""
COMPLETE DIAGNOSTIC SYSTEM
Comprehensive health checks, Z-stack validation, and system diagnostics

Features:
- Z-stack architectural validation
- Floor alignment verification
- Component health checks
- Database integrity tests
- Asset discovery validation
- Performance monitoring
- Automated repair suggestions
- Real-time dashboard

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 20, 2026
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import json
import tkinter as tk
from tkinter import ttk
import threading

# Setup paths
TRINITY_ROOT = Path(__file__).parent.parent.resolve()
LIGHTSPEED_ROOT = TRINITY_ROOT.parent.parent
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
ORACLE_ROOT = Z_AXIS_ROOT / "Z-2_Oracle"
MEROVINGIAN_ROOT = Z_AXIS_ROOT / "Z-4_Merovingian"
CANONICAL_AI_LOGS = ORACLE_ROOT / "data" / "legacy" / "ai_logs"
CANONICAL_DB_DIR = MEROVINGIAN_ROOT / "data" / "db"

sys.path.insert(0, str(LIGHTSPEED_ROOT))
sys.path.insert(0, str(TRINITY_ROOT))


class DiagnosticResult:
    """Single diagnostic test result"""

    def __init__(self, name: str, category: str, status: str, message: str, details: Dict = None):
        self.name = name
        self.category = category  # system, database, z-stack, assets, performance
        self.status = status  # pass, warn, fail
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"<DiagnosticResult({self.name}, {self.status})>"


class ZStackValidator:
    """
    Validates Z-stack architectural alignment
    """

    EXPECTED_FLOORS = [
        {'id': 'Z+3_Trinity', 'z_level': 3, 'purpose': 'UI & Dashboard'},
        {'id': 'Z+2_Neo', 'z_level': 2, 'purpose': 'AI Integration'},
        {'id': 'Z+1_Architect', 'z_level': 1, 'purpose': 'Project Planning'},
        {'id': 'Z0_TheConstruct', 'z_level': 0, 'purpose': 'Calculators & Simulations'},
        {'id': 'Z-1_Morpheus', 'z_level': -1, 'purpose': 'Knowledge & Database'},
        {'id': 'Z-2_Oracle', 'z_level': -2, 'purpose': 'Smart Floor Core'},
        {'id': 'Z-3_Smith', 'z_level': -3, 'purpose': 'Task Orchestration'},
        {'id': 'Z-4_Merovingian', 'z_level': -4, 'purpose': 'Data Persistence'}
    ]

    REQUIRED_FILES_PER_FLOOR = [
        '_FLOOR_MANIFEST.json',
        '__init__.py'
    ]

    SKIP_DIRS = {
        ".git",
        ".pytest_cache",
        "__pycache__",
        "archive",
        "legacy",
        "legacy_packs",
        "vault",
    }

    def __init__(self):
        self.results = []

    def _iter_active_files(self, root: Path, suffix: str) -> List[Path]:
        """Walk active floor code/data without descending into heavy archives."""
        matches: List[Path] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d.lower() not in self.SKIP_DIRS and not d.startswith(".")]
            base = Path(dirpath)
            for filename in filenames:
                if filename.lower().endswith(suffix.lower()):
                    matches.append(base / filename)
        return matches

    def validate_all(self) -> List[DiagnosticResult]:
        """Run all Z-stack validations"""
        self.results = []

        # Check floor structure
        self._check_floor_structure()

        # Check floor manifests
        self._check_floor_manifests()

        # Check inter-floor communication
        self._check_interfloor_communication()

        # Check misplaced components
        self._check_misplaced_components()

        return self.results

    def _check_floor_structure(self):
        """Validate floor directory structure"""
        for floor in self.EXPECTED_FLOORS:
            floor_path = Z_AXIS_ROOT / floor['id']

            if floor_path.exists() and floor_path.is_dir():
                self.results.append(DiagnosticResult(
                    name=f"Floor Structure: {floor['id']}",
                    category='z-stack',
                    status='pass',
                    message=f"{floor['id']} directory exists",
                    details={'path': str(floor_path), 'purpose': floor['purpose']}
                ))
            else:
                self.results.append(DiagnosticResult(
                    name=f"Floor Structure: {floor['id']}",
                    category='z-stack',
                    status='fail',
                    message=f"{floor['id']} directory missing",
                    details={'expected_path': str(floor_path)}
                ))

    def _check_floor_manifests(self):
        """Check for required manifest files"""
        for floor in self.EXPECTED_FLOORS:
            floor_path = Z_AXIS_ROOT / floor['id']
            manifest_path = floor_path / '_FLOOR_MANIFEST.json'

            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)

                    # Validate manifest structure
                    required_keys = ['floor_name', 'floor_id', 'z_level', 'version']
                    missing_keys = [k for k in required_keys if k not in manifest]

                    if missing_keys:
                        self.results.append(DiagnosticResult(
                            name=f"Manifest: {floor['id']}",
                            category='z-stack',
                            status='warn',
                            message=f"Manifest missing keys: {', '.join(missing_keys)}",
                            details={'path': str(manifest_path)}
                        ))
                    else:
                        self.results.append(DiagnosticResult(
                            name=f"Manifest: {floor['id']}",
                            category='z-stack',
                            status='pass',
                            message=f"Manifest valid",
                            details={'version': manifest.get('version')}
                        ))

                except Exception as e:
                    self.results.append(DiagnosticResult(
                        name=f"Manifest: {floor['id']}",
                        category='z-stack',
                        status='fail',
                        message=f"Manifest parse error: {e}",
                        details={'path': str(manifest_path)}
                    ))
            else:
                self.results.append(DiagnosticResult(
                    name=f"Manifest: {floor['id']}",
                    category='z-stack',
                    status='fail',
                    message=f"Manifest file missing",
                    details={'expected_path': str(manifest_path)}
                ))

    def _check_interfloor_communication(self):
        """Check Z Direct communication paths"""
        for floor in self.EXPECTED_FLOORS:
            floor_path = Z_AXIS_ROOT / floor['id']
            zdirect_path = floor_path / "Z Direct"

            if zdirect_path.exists():
                # Check for communication files
                comm_log = zdirect_path / "communication_log.txt"
                events_json = zdirect_path / "inter_floor_events.json"

                if comm_log.exists() or events_json.exists():
                    self.results.append(DiagnosticResult(
                        name=f"Inter-floor Comm: {floor['id']}",
                        category='z-stack',
                        status='pass',
                        message=f"Communication files present",
                        details={'path': str(zdirect_path)}
                    ))
                else:
                    self.results.append(DiagnosticResult(
                        name=f"Inter-floor Comm: {floor['id']}",
                        category='z-stack',
                        status='warn',
                        message=f"Z Direct exists but no comm files",
                        details={'path': str(zdirect_path)}
                    ))
            else:
                self.results.append(DiagnosticResult(
                    name=f"Inter-floor Comm: {floor['id']}",
                    category='z-stack',
                    status='warn',
                    message=f"Z Direct directory missing",
                    details={'expected_path': str(zdirect_path)}
                ))

    def _check_misplaced_components(self):
        """Identify components in wrong floors"""
        # Check for active database files outside Merovingian, the canonical
        # persistence/audit floor. Archived legacy packs are ignored.
        for floor in self.EXPECTED_FLOORS:
            if floor['id'] == 'Z-4_Merovingian':
                continue

            floor_path = Z_AXIS_ROOT / floor['id']
            if not floor_path.exists():
                continue

            # Look for database files
            db_files = self._iter_active_files(floor_path, ".db")
            if db_files:
                self.results.append(DiagnosticResult(
                    name=f"Misplaced DB: {floor['id']}",
                    category='z-stack',
                    status='warn',
                    message=f"Database files found in {floor['id']} (should be in Z-4_Merovingian)",
                    details={'files': [str(f) for f in db_files]}
                ))

        # Check for calculator modules outside Z0_TheConstruct. The diagnostic
        # ignores support services, SQLAlchemy models, and archived vault files
        # so UI launchers and persistence code are not misclassified.
        for floor in self.EXPECTED_FLOORS:
            if floor['id'] == 'Z0_TheConstruct':
                continue

            floor_path = Z_AXIS_ROOT / floor['id']
            if not floor_path.exists():
                continue

            # Look for calculator-like files
            calc_keywords = ['calculator']
            py_files = self._iter_active_files(floor_path, ".py")
            misplaced_calcs = [
                f for f in py_files
                if any(kw in f.stem.lower() for kw in calc_keywords)
                and not any(part.lower() in {"archive", "legacy", "legacy_packs", "__pycache__", "database"} for part in f.parts)
            ]

            if misplaced_calcs:
                self.results.append(DiagnosticResult(
                    name=f"Misplaced Calculators: {floor['id']}",
                    category='z-stack',
                    status='warn',
                    message=f"Calculator-like files in {floor['id']} (should be in Z0_TheConstruct)",
                    details={'files': [f.name for f in misplaced_calcs[:5]]}
                ))


class SystemDiagnostics:
    """
    Complete system diagnostics
    """

    def __init__(self):
        self.results = []
        self.z_stack_validator = ZStackValidator()

    def run_all_diagnostics(self) -> List[DiagnosticResult]:
        """Run complete diagnostic suite"""
        self.results = []

        print("=" * 70)
        print("LIGHTSPEED COMPLETE DIAGNOSTIC SYSTEM")
        print("=" * 70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 1. System checks
        print("[1/7] Running system checks...")
        self._check_python_version()
        self._check_dependencies()
        self._check_directory_structure()

        # 2. Z-stack validation
        print("[2/7] Validating Z-stack architecture...")
        z_results = self.z_stack_validator.validate_all()
        self.results.extend(z_results)

        # 3. Database checks
        print("[3/7] Checking database...")
        self._check_database()

        # 4. Asset checks
        print("[4/7] Validating assets...")
        self._check_assets()

        # 5. UI/Portal checks
        print("[5/7] Checking UI components...")
        self._check_ui_components()

        # 6. Integration checks
        print("[6/7] Checking integrations...")
        self._check_integrations()

        # 7. Performance checks
        print("[7/7] Running performance checks...")
        self._check_performance()

        print("\n" + "=" * 70)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 70)

        return self.results

    def _check_python_version(self):
        """Check Python version"""
        version = sys.version_info

        if version.major == 3 and version.minor >= 11:
            self.results.append(DiagnosticResult(
                name="Python Version",
                category='system',
                status='pass',
                message=f"Python {version.major}.{version.minor}.{version.micro}",
                details={'version': f"{version.major}.{version.minor}.{version.micro}"}
            ))
        else:
            self.results.append(DiagnosticResult(
                name="Python Version",
                category='system',
                status='warn',
                message=f"Python {version.major}.{version.minor} (recommended 3.11+)",
                details={'version': f"{version.major}.{version.minor}.{version.micro}"}
            ))

    def _check_dependencies(self):
        """Check critical dependencies"""
        dependencies = {
            'tkinter': 'UI framework',
            'sqlite3': 'Database',
            'json': 'Configuration',
            'pathlib': 'File operations'
        }

        for module, purpose in dependencies.items():
            try:
                __import__(module)
                self.results.append(DiagnosticResult(
                    name=f"Dependency: {module}",
                    category='system',
                    status='pass',
                    message=f"{module} available",
                    details={'purpose': purpose}
                ))
            except ImportError:
                self.results.append(DiagnosticResult(
                    name=f"Dependency: {module}",
                    category='system',
                    status='fail',
                    message=f"{module} not found",
                    details={'purpose': purpose}
                ))

    def _check_directory_structure(self):
        """Check core directory structure"""
        critical_dirs = [
            ('LightSpeed Root', LIGHTSPEED_ROOT),
            ('Z Axis', Z_AXIS_ROOT),
            ('Trinity', TRINITY_ROOT),
            ('Database', CANONICAL_DB_DIR),
            ('AI Logs', CANONICAL_AI_LOGS)
        ]

        for name, path in critical_dirs:
            if path.exists():
                self.results.append(DiagnosticResult(
                    name=f"Directory: {name}",
                    category='system',
                    status='pass',
                    message=f"{name} directory exists",
                    details={'path': str(path)}
                ))
            else:
                self.results.append(DiagnosticResult(
                    name=f"Directory: {name}",
                    category='system',
                    status='fail',
                    message=f"{name} directory missing",
                    details={'expected_path': str(path)}
                ))

    def _check_database(self):
        """Check database connectivity and integrity"""
        try:
            sys.path.insert(0, str(Z_AXIS_ROOT / "Z-1_Morpheus"))
            from database.base import get_session, init_db
            import database.models  # noqa: F401 - ensure all SQLAlchemy models are registered
            from database.models.calculators import CalculatorModule
            from database.models.datasets import ScientificDataset

            init_db()
            session = get_session()

            # Check calculator count
            calc_count = session.query(CalculatorModule).count()
            self.results.append(DiagnosticResult(
                name="Database: Calculators",
                category='database',
                status='pass',
                message=f"{calc_count} calculators registered",
                details={'count': calc_count}
            ))

            # Check dataset count
            ds_count = session.query(ScientificDataset).count()
            self.results.append(DiagnosticResult(
                name="Database: Datasets",
                category='database',
                status='pass',
                message=f"{ds_count} datasets registered",
                details={'count': ds_count}
            ))

        except Exception as e:
            self.results.append(DiagnosticResult(
                name="Database Connection",
                category='database',
                status='fail',
                message=f"Database error: {str(e)}",
                details={'error': str(e)}
            ))

    def _check_assets(self):
        """Check asset management system"""
        try:
            sys.path.insert(0, str(Z_AXIS_ROOT / "Z-2_Oracle"))
            from tools.asset_management_system import AssetManagementSystem

            ams = AssetManagementSystem()
            stats = ams.get_statistics()

            self.results.append(DiagnosticResult(
                name="Asset Manager",
                category='assets',
                status='pass',
                message=f"Asset manager initialized",
                details={
                    'total_assets': stats['total_assets'],
                    'by_type': stats['by_type']
                }
            ))

        except Exception as e:
            self.results.append(DiagnosticResult(
                name="Asset Manager",
                category='assets',
                status='fail',
                message=f"Asset manager error: {str(e)}",
                details={'error': str(e)}
            ))

    def _check_ui_components(self):
        """Check UI component availability"""
        legacy_root = LIGHTSPEED_ROOT / 'Z Axis' / 'archive' / 'legacy_packs' / 'legacy_trinity_ui'

        ui_components = [
            ('IT Portal', TRINITY_ROOT / 'ui' / 'it_portal.py', None),
            # These enhanced/experimental modules are now archived to keep the runtime surface area minimal.
            ('IT Portal Enhanced', TRINITY_ROOT / 'ui' / 'it_portal_enhanced.py', legacy_root / 'it_portal_enhanced.py'),
            ('Placeable Workspace', TRINITY_ROOT / 'ui' / 'placeable_workspace_enhanced.py', legacy_root / 'placeable_workspace_enhanced.py'),
            ('OASIS Aesthetic', LIGHTSPEED_ROOT / 'config' / 'premium_theme_config.json', None),
        ]

        for name, primary, archived in ui_components:
            path = primary
            archived_used = False
            if not path.exists() and archived is not None and archived.exists():
                path = archived
                archived_used = True

            if path.exists():
                self.results.append(DiagnosticResult(
                    name=f"UI: {name}",
                    category='ui',
                    status='pass',
                    message=f"{name} available" + (" (archived)" if archived_used else ""),
                    details={'path': str(path), 'archived': archived_used}
                ))
            else:
                self.results.append(DiagnosticResult(
                    name=f"UI: {name}",
                    category='ui',
                    status='warn',
                    message=f"{name} not found",
                    details={'expected_path': str(primary), 'archived_path': str(archived) if archived is not None else None}
                ))

    def _check_integrations(self):
        """Check system integrations"""
        integration_files = [
            ('Unified Launcher', [
                LIGHTSPEED_ROOT / 'unified_lightspeed_launcher.py',
                LIGHTSPEED_ROOT / '__main__.py',
                LIGHTSPEED_ROOT / 'LAUNCH_GUI.bat',
            ]),
            ('Search System', [
                TRINITY_ROOT / 'wizards' / 'unified_search_system.py',
            ]),
            ('Integration Guide', [
                TRINITY_ROOT / 'ui' / 'it_portal_integration_guide.py',
                LIGHTSPEED_ROOT / 'README.md',
                LIGHTSPEED_ROOT / 'dataindex',
            ])
        ]

        for name, paths in integration_files:
            existing = next((path for path in paths if path.exists()), None)
            if existing is not None:
                self.results.append(DiagnosticResult(
                    name=f"Integration: {name}",
                    category='integration',
                    status='pass',
                    message=f"{name} available",
                    details={'path': str(existing)}
                ))
            else:
                self.results.append(DiagnosticResult(
                    name=f"Integration: {name}",
                    category='integration',
                    status='warn',
                    message=f"{name} not found",
                    details={'expected_paths': [str(path) for path in paths]}
                ))

    def _check_performance(self):
        """Check system performance metrics"""
        import time

        # Measure import time
        start = time.time()
        try:
            import tkinter as tk
            elapsed = time.time() - start

            if elapsed < 0.1:
                status = 'pass'
            elif elapsed < 0.5:
                status = 'warn'
            else:
                status = 'fail'

            self.results.append(DiagnosticResult(
                name="Performance: Import Speed",
                category='performance',
                status=status,
                message=f"Tkinter import: {elapsed:.3f}s",
                details={'time_seconds': elapsed}
            ))
        except Exception as e:
            self.results.append(DiagnosticResult(
                name="Performance: Import Speed",
                category='performance',
                status='fail',
                message=f"Import test failed: {e}",
                details={'error': str(e)}
            ))

    def generate_report(self) -> str:
        """Generate text report"""
        if not self.results:
            return "No diagnostic results available"

        # Count by status
        passed = len([r for r in self.results if r.status == 'pass'])
        warned = len([r for r in self.results if r.status == 'warn'])
        failed = len([r for r in self.results if r.status == 'fail'])

        report = []
        report.append("=" * 70)
        report.append("LIGHTSPEED DIAGNOSTIC REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Tests: {len(self.results)}")
        report.append(f"Passed: {passed} | Warnings: {warned} | Failed: {failed}")
        report.append("")

        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        for category, results in sorted(categories.items()):
            report.append("")
            report.append(f"{category.upper()} CHECKS")
            report.append("-" * 70)

            for result in results:
                status_icon = {
                    'pass': '✓',
                    'warn': '⚠',
                    'fail': '✗'
                }.get(result.status, '?')

                report.append(f"{status_icon} {result.name}: {result.message}")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)

    def export_json(self, filepath: Path = None) -> str:
        """Export results to JSON"""
        if not filepath:
            filepath = CANONICAL_AI_LOGS / f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'passed': len([r for r in self.results if r.status == 'pass']),
            'warned': len([r for r in self.results if r.status == 'warn']),
            'failed': len([r for r in self.results if r.status == 'fail']),
            'results': [
                {
                    'name': r.name,
                    'category': r.category,
                    'status': r.status,
                    'message': r.message,
                    'details': r.details,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        return str(filepath)


class DiagnosticDashboard(tk.Tk):
    """
    Real-time diagnostic dashboard
    """

    def __init__(self):
        super().__init__()

        self.title("LightSpeed Diagnostic Dashboard")
        self.geometry("1200x800")

        # Apply OASIS theme if available
        try:
            from ui.oasis_aesthetic_system import apply_oasis_theme, OASISColors
            apply_oasis_theme(self)
            self.colors = OASISColors
            self.has_oasis = True
        except:
            self.config(bg='#0A1628')
            self.has_oasis = False

        # Diagnostic system
        self.diagnostics = SystemDiagnostics()
        self.results = []

        # Create UI
        self._create_ui()

        # Run diagnostics
        self.after(100, self._run_diagnostics_async)

    def _create_ui(self):
        """Create dashboard UI"""
        # Title
        title = tk.Label(
            self,
            text="🔧 LIGHTSPEED DIAGNOSTIC DASHBOARD",
            font=('Orbitron', 20, 'bold'),
            fg='#00F5FF',
            bg='#0A1628'
        )
        title.pack(pady=20)

        # Status summary
        self.summary_frame = tk.Frame(self, bg='#001D3D')
        self.summary_frame.pack(fill=tk.X, padx=20, pady=10)

        self.summary_labels = {}
        for status in ['Total', 'Passed', 'Warnings', 'Failed']:
            label = tk.Label(
                self.summary_frame,
                text=f"{status}: 0",
                font=('Segoe UI', 12, 'bold'),
                fg='#FFFFFF',
                bg='#001D3D'
            )
            label.pack(side=tk.LEFT, padx=20)
            self.summary_labels[status] = label

        # Results tree
        tree_frame = tk.Frame(self, bg='#0A1628')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ('Category', 'Test', 'Status', 'Message')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=25)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Buttons
        button_frame = tk.Frame(self, bg='#0A1628')
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Button(
            button_frame,
            text="Refresh",
            font=('Segoe UI', 11, 'bold'),
            bg='#00F5FF',
            fg='#000814',
            command=self._run_diagnostics_async
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="Export Report",
            font=('Segoe UI', 11, 'bold'),
            bg='#FF006E',
            fg='#FFFFFF',
            command=self._export_report
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="Close",
            font=('Segoe UI', 11, 'bold'),
            bg='#64748B',
            fg='#FFFFFF',
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _run_diagnostics_async(self):
        """Run diagnostics in background thread"""
        def run():
            self.results = self.diagnostics.run_all_diagnostics()
            self.after(0, self._update_display)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _update_display(self):
        """Update display with results"""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Count statuses
        passed = len([r for r in self.results if r.status == 'pass'])
        warned = len([r for r in self.results if r.status == 'warn'])
        failed = len([r for r in self.results if r.status == 'fail'])

        # Update summary
        self.summary_labels['Total'].config(text=f"Total: {len(self.results)}")
        self.summary_labels['Passed'].config(text=f"Passed: {passed}", fg='#00FF41')
        self.summary_labels['Warnings'].config(text=f"Warnings: {warned}", fg='#FFB627')
        self.summary_labels['Failed'].config(text=f"Failed: {failed}", fg='#FF006E')

        # Populate tree
        for result in self.results:
            status_icon = {
                'pass': '✓',
                'warn': '⚠',
                'fail': '✗'
            }.get(result.status, '?')

            self.tree.insert('', tk.END, values=(
                result.category.upper(),
                result.name,
                status_icon,
                result.message
            ))

    def _export_report(self):
        """Export diagnostic report"""
        report_path = self.diagnostics.export_json()
        tk.messagebox.showinfo(
            "Export Complete",
            f"Diagnostic report exported to:\n{report_path}"
        )


def main():
    """Run diagnostic dashboard"""
    dashboard = DiagnosticDashboard()
    dashboard.mainloop()


if __name__ == "__main__":
    main()
