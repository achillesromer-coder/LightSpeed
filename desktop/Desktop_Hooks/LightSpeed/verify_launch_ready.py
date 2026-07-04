#!/usr/bin/env python
"""
LightSpeed Consolidated - Launch Readiness Verification
========================================================

Comprehensive system verification for production launch.
Checks all Z-Axis floors, services, configurations, and generates
a detailed report of system readiness.

Usage:
    python verify_launch_ready.py              # Full verification
    python verify_launch_ready.py --quick      # Quick check
    python verify_launch_ready.py --fix        # Attempt auto-fixes
    python verify_launch_ready.py --report     # Generate detailed report

Author: LightSpeed Team / ACHILLES
Version: 5.1.2
"""

# CODEX NOTE (2026-02-06, updated 2026-04-03):
# - Reports now write under `Z Axis/Z-4_Merovingian/data/reports/launch_readiness/`.
# - Canonical spec/tracking: `dataindex/02_MASTER_BUILD_SPEC_SHEET.md`.
# - AI log archives are Oracle-owned under `Z Axis/Z-2_Oracle/data/legacy/ai_logs`.

import sys
import os
import json
import time
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
LIGHTSPEED_ROOT = SCRIPT_DIR
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
SPLIT_RUNTIME_ROOT = (LIGHTSPEED_ROOT.parent.parent / "LightSpeed_Runtime").resolve()

# Add paths
sys.path.insert(0, str(LIGHTSPEED_ROOT))
if SPLIT_RUNTIME_ROOT.exists():
    sys.path.insert(0, str(SPLIT_RUNTIME_ROOT))

from lightspeed_runtime.storage_paths import reports_root
from lightspeed_runtime.startup_options import launch_runtime_report

DEFAULT_REPORT_DIR = reports_root(LIGHTSPEED_ROOT) / "launch_readiness"
APP_VERSION = "5.1.2"
SKIP_SCAN_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
    "archive",
    "legacy",
    "legacy_packs",
    "vault",
    "vendor",
    "node_modules",
}


def iter_active_files(root: Path, suffix: str, *, max_depth: int = 6, limit: int = 5000) -> List[Path]:
    """Return active files without traversing archived/vendor reservoirs."""
    files: List[Path] = []
    if not root.exists():
        return files

    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        try:
            depth = len(current.relative_to(root).parts)
        except ValueError:
            depth = 0

        if depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = [
                name for name in dirnames
                if name.lower() not in SKIP_SCAN_DIRS and not name.startswith(".")
            ]

        for filename in filenames:
            if filename.lower().endswith(suffix.lower()):
                files.append(current / filename)
                if len(files) >= limit:
                    return files
    return files

# Canonical floor configuration
CANONICAL_FLOORS = {
    "Z+3_Trinity": {"z_level": 3, "color": "#FF1493", "role": "UI Layer"},
    "Z+2_Neo": {"z_level": 2, "color": "#00FF00", "role": "AI Orchestration"},
    "Z+1_Architect": {"z_level": 1, "color": "#DAA520", "role": "Planning"},
    "Z0_TheConstruct": {"z_level": 0, "color": "#808080", "role": "3D Environment"},
    "Z-1_Morpheus": {"z_level": -1, "color": "#4B0082", "role": "Knowledge Base"},
    "Z-2_Oracle": {"z_level": -2, "color": "#00008B", "role": "IP Vault"},
    "Z-3_Smith": {"z_level": -3, "color": "#006400", "role": "Automation"},
    "Z-4_Merovingian": {"z_level": -4, "color": "#8B0000", "role": "Core Services"},
}


class CheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


@dataclass
class VerificationResult:
    """Result of a single verification check."""
    name: str
    category: str
    status: CheckStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0
    fixable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "fixable": self.fixable,
        }


# ============================================================================
# VERIFICATION FUNCTIONS
# ============================================================================

def verify_directory_structure() -> List[VerificationResult]:
    """Verify core directory structure."""
    results = []

    # Required directories
    required_dirs = [
        ("Z Axis", "Z Axis root"),
        ("config", "Configuration"),
        ("Z Axis/Z-2_Oracle/data/legacy/ai_logs", "Oracle AI log archive"),
        ("tests", "Test suite"),
    ]

    for dirname, description in required_dirs:
        start = time.time()
        dirpath = LIGHTSPEED_ROOT / dirname

        if dirpath.exists() and dirpath.is_dir():
            results.append(VerificationResult(
                name=f"dir_{dirname}",
                category="structure",
                status=CheckStatus.PASS,
                message=f"{description} directory exists",
                duration_ms=(time.time() - start) * 1000,
            ))
        else:
            results.append(VerificationResult(
                name=f"dir_{dirname}",
                category="structure",
                status=CheckStatus.FAIL,
                message=f"{description} directory missing",
                fixable=True,
                duration_ms=(time.time() - start) * 1000,
            ))

    return results


def verify_entry_points() -> List[VerificationResult]:
    """Verify main entry points exist."""
    results = []

    entry_points = [
        ("__main__.py", "Unified launcher"),
        ("N.py", "N.py orchestrator"),
        ("LAUNCH_GUI.bat", "Windows launcher"),
    ]

    for filename, description in entry_points:
        start = time.time()
        filepath = LIGHTSPEED_ROOT / filename

        if filepath.exists():
            # Check file size
            size = filepath.stat().st_size
            results.append(VerificationResult(
                name=f"entry_{filename}",
                category="entry_points",
                status=CheckStatus.PASS,
                message=f"{description} exists ({size:,} bytes)",
                details={"size_bytes": size},
                duration_ms=(time.time() - start) * 1000,
            ))
        else:
            results.append(VerificationResult(
                name=f"entry_{filename}",
                category="entry_points",
                status=CheckStatus.FAIL if filename != "LAUNCH_GUI.bat" else CheckStatus.WARN,
                message=f"{description} missing",
                duration_ms=(time.time() - start) * 1000,
            ))

    return results


def verify_launch_runtime() -> List[VerificationResult]:
    """Verify the launcher resolves to a Python runtime with the core LightSpeed modules."""
    start = time.time()
    report = launch_runtime_report(LIGHTSPEED_ROOT)
    selected = report.get("selected") if isinstance(report.get("selected"), dict) else {}
    probe = report.get("probe") if isinstance(report.get("probe"), dict) else {}

    if not selected:
        return [
            VerificationResult(
                name="launch_runtime",
                category="entry_points",
                status=CheckStatus.FAIL,
                message="No preferred launch runtime found (expected Python 3.11 or workspace venv)",
                fixable=True,
                duration_ms=(time.time() - start) * 1000,
            )
        ]

    if report.get("ready"):
        return [
            VerificationResult(
                name="launch_runtime",
                category="entry_points",
                status=CheckStatus.PASS,
                message=(
                    f"Launch runtime ready via {selected.get('label')} "
                    f"({probe.get('version') or 'unknown version'})"
                ),
                details={
                    "runtime_path": selected.get("path"),
                    "runtime_source": selected.get("source"),
                    "version": probe.get("version"),
                },
                duration_ms=(time.time() - start) * 1000,
            )
        ]

    missing_modules = probe.get("missing_modules") if isinstance(probe.get("missing_modules"), list) else []
    message = (
        f"Launch runtime not ready via {selected.get('label')}: "
        f"missing {', '.join(missing_modules) or 'core modules'}"
    )
    return [
        VerificationResult(
            name="launch_runtime",
            category="entry_points",
            status=CheckStatus.FAIL,
            message=message,
            details={
                "runtime_path": selected.get("path"),
                "runtime_source": selected.get("source"),
                "missing_modules": missing_modules,
                "probe_error": probe.get("error"),
            },
            fixable=True,
            duration_ms=(time.time() - start) * 1000,
        )
    ]


def verify_z_axis_floors() -> List[VerificationResult]:
    """Verify all Z-Axis floors."""
    results = []

    for floor_id, config in CANONICAL_FLOORS.items():
        start = time.time()
        floor_path = Z_AXIS_ROOT / floor_id

        if floor_path.exists():
            # Count active Python files without traversing archives/vaults.
            py_files = iter_active_files(floor_path, ".py", max_depth=6)

            # Check for Z Direct
            has_z_direct = (floor_path / "Z Direct").exists()

            results.append(VerificationResult(
                name=f"floor_{floor_id}",
                category="z_axis",
                status=CheckStatus.PASS,
                message=f"{floor_id} ({config['role']}) - {len(py_files)} Python files",
                details={
                    "z_level": config["z_level"],
                    "color": config["color"],
                    "role": config["role"],
                    "python_files": len(py_files),
                    "has_z_direct": has_z_direct,
                },
                duration_ms=(time.time() - start) * 1000,
            ))
        else:
            results.append(VerificationResult(
                name=f"floor_{floor_id}",
                category="z_axis",
                status=CheckStatus.FAIL,
                message=f"{floor_id} directory missing",
                fixable=True,
                duration_ms=(time.time() - start) * 1000,
            ))

    return results


def verify_core_services() -> List[VerificationResult]:
    """Verify Z-4 Merovingian core services."""
    results = []

    merovingian = Z_AXIS_ROOT / "Z-4_Merovingian"
    services_path = merovingian / "core" / "services"

    required_services = [
        ("event_bus.py", "Event Bus"),
        ("settings_hub.py", "Settings Hub"),
        ("database.py", "Database Service"),
        ("storage.py", "Storage Service"),
        ("cache_manager.py", "Cache Manager"),
        ("logger.py", "Logger Service"),
    ]

    for filename, description in required_services:
        start = time.time()
        filepath = services_path / filename

        if filepath.exists():
            size = filepath.stat().st_size
            results.append(VerificationResult(
                name=f"service_{filename}",
                category="services",
                status=CheckStatus.PASS,
                message=f"{description} ({size:,} bytes)",
                details={"size_bytes": size},
                duration_ms=(time.time() - start) * 1000,
            ))
        else:
            results.append(VerificationResult(
                name=f"service_{filename}",
                category="services",
                status=CheckStatus.FAIL,
                message=f"{description} missing",
                duration_ms=(time.time() - start) * 1000,
            ))

    return results


def verify_configuration() -> List[VerificationResult]:
    """Verify configuration files."""
    results = []

    config_files = [
        ("config/lightspeed_config.json", "Main config"),
        ("config/settings.json", "Runtime settings"),
        ("config/z_direct_template.json", "Z Direct template"),
        ("config/user_config.json", "User config"),
    ]

    for filepath, description in config_files:
        start = time.time()
        full_path = LIGHTSPEED_ROOT / filepath

        if full_path.exists():
            try:
                with open(full_path) as f:
                    config = json.load(f)

                results.append(VerificationResult(
                    name=f"config_{Path(filepath).stem}",
                    category="configuration",
                    status=CheckStatus.PASS,
                    message=f"{description} valid JSON",
                    details={"keys": list(config.keys()) if isinstance(config, dict) else "array"},
                    duration_ms=(time.time() - start) * 1000,
                ))
            except json.JSONDecodeError as e:
                results.append(VerificationResult(
                    name=f"config_{Path(filepath).stem}",
                    category="configuration",
                    status=CheckStatus.FAIL,
                    message=f"{description} invalid JSON: {e}",
                    fixable=True,
                    duration_ms=(time.time() - start) * 1000,
                ))
        else:
            results.append(VerificationResult(
                name=f"config_{Path(filepath).stem}",
                category="configuration",
                status=CheckStatus.WARN,
                message=f"{description} not found",
                duration_ms=(time.time() - start) * 1000,
            ))

    return results


def verify_physics_engine() -> List[VerificationResult]:
    """Verify Raphael physics engine."""
    results = []

    raphael_path = Z_AXIS_ROOT / "Z-4_Merovingian" / "core" / "physics" / "raphael"
    start = time.time()

    if raphael_path.exists():
        # Count simulation files without traversing generated caches.
        py_files = iter_active_files(raphael_path, ".py", max_depth=8)

        # Check for key components
        has_equations = (raphael_path / "raphael_equations.py").exists()
        has_simulations = (raphael_path / "Simulations").exists()
        has_phenomena = (raphael_path / "natural_phenonema").exists()

        results.append(VerificationResult(
            name="physics_raphael",
            category="physics",
            status=CheckStatus.PASS,
            message=f"Raphael engine found ({len(py_files)} Python files)",
            details={
                "python_files": len(py_files),
                "has_equations": has_equations,
                "has_simulations": has_simulations,
                "has_phenomena": has_phenomena,
            },
            duration_ms=(time.time() - start) * 1000,
        ))
    else:
        results.append(VerificationResult(
            name="physics_raphael",
            category="physics",
            status=CheckStatus.WARN,
            message="Raphael physics engine not found",
            duration_ms=(time.time() - start) * 1000,
        ))

    return results


def verify_database() -> List[VerificationResult]:
    """Verify database availability."""
    results = []
    start = time.time()

    # Check config for database path
    config_path = LIGHTSPEED_ROOT / "config" / "lightspeed_config.json"

    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)

        db_path = config.get("database", {}).get("path", "")
        if db_path:
            full_db_path = LIGHTSPEED_ROOT / db_path

            if full_db_path.exists():
                # Try to connect
                try:
                    conn = sqlite3.connect(str(full_db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    conn.close()

                    results.append(VerificationResult(
                        name="database_connection",
                        category="database",
                        status=CheckStatus.PASS,
                        message=f"Database connected ({len(tables)} tables)",
                        details={"tables": [t[0] for t in tables]},
                        duration_ms=(time.time() - start) * 1000,
                    ))
                except Exception as e:
                    results.append(VerificationResult(
                        name="database_connection",
                        category="database",
                        status=CheckStatus.FAIL,
                        message=f"Database connection failed: {e}",
                        duration_ms=(time.time() - start) * 1000,
                    ))
            else:
                results.append(VerificationResult(
                    name="database_connection",
                    category="database",
                    status=CheckStatus.WARN,
                    message=f"Database file not found: {db_path}",
                    duration_ms=(time.time() - start) * 1000,
                ))
    else:
        results.append(VerificationResult(
            name="database_connection",
            category="database",
            status=CheckStatus.SKIP,
            message="Config not found - database path unknown",
            duration_ms=(time.time() - start) * 1000,
        ))

    return results


def verify_tests() -> List[VerificationResult]:
    """Verify test suite exists."""
    results = []

    tests_dir = LIGHTSPEED_ROOT / "tests"
    start = time.time()

    if tests_dir.exists():
        test_files = list(tests_dir.glob("test_*.py"))

        results.append(VerificationResult(
            name="test_suite",
            category="tests",
            status=CheckStatus.PASS if len(test_files) > 0 else CheckStatus.WARN,
            message=f"Test suite found ({len(test_files)} test files)",
            details={"test_files": [f.name for f in test_files]},
            duration_ms=(time.time() - start) * 1000,
        ))
    else:
        results.append(VerificationResult(
            name="test_suite",
            category="tests",
            status=CheckStatus.WARN,
            message="Test directory not found",
            fixable=True,
            duration_ms=(time.time() - start) * 1000,
        ))

    return results


def verify_ai_logs() -> List[VerificationResult]:
    """Verify AI logs and documentation."""
    results = []

    ai_logs = LIGHTSPEED_ROOT / "Z Axis" / "Z-2_Oracle" / "data" / "legacy" / "ai_logs"
    start = time.time()

    if ai_logs.exists():
        md_files = iter_active_files(ai_logs, ".md", max_depth=4)
        json_files = iter_active_files(ai_logs, ".json", max_depth=4)

        # Check for key documentation
        key_docs = ["FINAL_HANDOFF.md", "MASTER_INDEX.md", "QUICK_START.md"]
        found_docs = [d for d in key_docs if (ai_logs / d).exists()]

        results.append(VerificationResult(
            name="ai_logs",
            category="documentation",
            status=CheckStatus.PASS,
            message=f"AI logs found ({len(md_files)} markdown, {len(json_files)} JSON)",
            details={
                "markdown_files": len(md_files),
                "json_files": len(json_files),
                "key_docs_found": found_docs,
            },
            duration_ms=(time.time() - start) * 1000,
        ))
    else:
        results.append(VerificationResult(
            name="ai_logs",
            category="documentation",
            status=CheckStatus.WARN,
            message="AI logs directory not found",
            duration_ms=(time.time() - start) * 1000,
        ))

    return results


# ============================================================================
# MAIN VERIFICATION
# ============================================================================

def run_verification(quick: bool = False) -> Dict[str, Any]:
    """Run all verification checks."""
    all_results: List[VerificationResult] = []

    print("=" * 70)
    print("LIGHTSPEED CONSOLIDATED - LAUNCH READINESS VERIFICATION")
    print("=" * 70)
    print(f"Version: {APP_VERSION}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 70)

    # Run verification checks
    checks = [
        ("Directory Structure", verify_directory_structure),
        ("Entry Points", verify_entry_points),
        ("Launch Runtime", verify_launch_runtime),
        ("Z-Axis Floors", verify_z_axis_floors),
        ("Core Services", verify_core_services),
        ("Configuration", verify_configuration),
        ("Physics Engine", verify_physics_engine),
        ("Database", verify_database),
        ("Test Suite", verify_tests),
        ("AI Logs", verify_ai_logs),
    ]

    if quick:
        checks = checks[:5]  # Include launch runtime in the fast path

    for category_name, check_func in checks:
        print(f"\n[CHECKING] {category_name}...")
        results = check_func()
        all_results.extend(results)

        # Summary for this category
        passed = sum(1 for r in results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in results if r.status == CheckStatus.FAIL)
        warned = sum(1 for r in results if r.status == CheckStatus.WARN)

        status_icon = "[OK]" if failed == 0 else "[!!]"
        print(f"  {status_icon} {passed} passed, {failed} failed, {warned} warnings")

    # Overall summary
    total = len(all_results)
    total_passed = sum(1 for r in all_results if r.status == CheckStatus.PASS)
    total_failed = sum(1 for r in all_results if r.status == CheckStatus.FAIL)
    total_warned = sum(1 for r in all_results if r.status == CheckStatus.WARN)
    total_skipped = sum(1 for r in all_results if r.status == CheckStatus.SKIP)

    pass_rate = (total_passed / total * 100) if total > 0 else 0

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"Total Checks: {total}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Warnings: {total_warned}")
    print(f"Skipped: {total_skipped}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print("=" * 70)

    # Determine launch readiness
    if total_failed == 0:
        print("\n[SUCCESS] SYSTEM IS LAUNCH READY!")
        launch_ready = True
        if total_warned > 0:
            print("Note: Some warnings present - review recommended before production.")
    else:
        print(f"\n[WARNING] {total_failed} CRITICAL ISSUES FOUND")
        print("System is NOT ready for launch. Please fix issues before deployment.")
        launch_ready = False

        # List failures
        print("\nCritical Issues:")
        for r in all_results:
            if r.status == CheckStatus.FAIL:
                print(f"  - {r.name}: {r.message}")

    return {
        "timestamp": datetime.now().isoformat(),
        "version": APP_VERSION,
        "launch_ready": launch_ready,
        "summary": {
            "total": total,
            "passed": total_passed,
            "failed": total_failed,
            "warnings": total_warned,
            "skipped": total_skipped,
            "pass_rate": pass_rate,
        },
        "results": [r.to_dict() for r in all_results],
    }


def generate_report(report_data: Dict[str, Any], output_path: Path) -> None:
    """Generate detailed verification report."""
    # Save JSON
    json_path = output_path.with_suffix(".json")
    with open(json_path, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"\nJSON report saved: {json_path}")

    # Generate markdown
    md_content = f"""# LightSpeed Launch Readiness Report

**Generated:** {report_data['timestamp']}
**Version:** {report_data['version']}
**Status:** {'LAUNCH READY' if report_data['launch_ready'] else 'NOT READY'}

## Summary

| Metric | Value |
|--------|-------|
| Total Checks | {report_data['summary']['total']} |
| Passed | {report_data['summary']['passed']} |
| Failed | {report_data['summary']['failed']} |
| Warnings | {report_data['summary']['warnings']} |
| Skipped | {report_data['summary']['skipped']} |
| **Pass Rate** | **{report_data['summary']['pass_rate']:.1f}%** |

## Detailed Results

"""
    # Group by category
    by_category = {}
    for result in report_data['results']:
        cat = result['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(result)

    for category, results in by_category.items():
        md_content += f"### {category.replace('_', ' ').title()}\n\n"
        for r in results:
            icon = {"pass": "✅", "fail": "❌", "warn": "⚠️", "skip": "⏭️"}[r['status']]
            md_content += f"- {icon} **{r['name']}**: {r['message']}\n"
        md_content += "\n"

    md_path = output_path.with_suffix(".md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Markdown report saved: {md_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="LightSpeed Launch Readiness Verification")
    parser.add_argument("--quick", action="store_true", help="Quick verification only")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    parser.add_argument("--fix", action="store_true", help="Attempt to auto-fix issues")

    args = parser.parse_args()

    # Run verification
    report_data = run_verification(quick=args.quick)

    # Generate report if requested
    if args.report:
        # Keep the repo root clean; launch-readiness reports live under Merovingian reports.
        try:
            DEFAULT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        report_path = DEFAULT_REPORT_DIR / f"launch_readiness_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        generate_report(report_data, report_path)

    # Exit code
    if report_data['launch_ready']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
