#!/usr/bin/env python
"""
LightSpeed Consolidated - Complete Test Suite Runner
====================================================

Runs all test categories and generates a comprehensive report.
Use this script before deployment or major releases.

Usage:
    python tests/run_all_tests.py              # Run all tests
    python tests/run_all_tests.py --quick      # Quick smoke test
    python tests/run_all_tests.py --verbose    # Verbose output
    python tests/run_all_tests.py --report     # Generate HTML report

Author: LightSpeed Team / ACHILLES
Version: 5.1.1
"""

# CODEX NOTE (2026-02-06):
# - This runner executes pytest with `cwd=tests/` to keep tool caches out of repo root.
# - Summary parsing is regex-based to tolerate pytest's decorated output lines.

import sys
import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import subprocess
import re

# Resolve paths
TESTS_DIR = Path(__file__).parent
LIGHTSPEED_ROOT = TESTS_DIR.parent
SPLIT_RUNTIME_ROOT = (LIGHTSPEED_ROOT.parent.parent / "LightSpeed_Runtime").resolve()

# Add to path
sys.path.insert(0, str(LIGHTSPEED_ROOT))
sys.path.insert(0, str(TESTS_DIR))
if SPLIT_RUNTIME_ROOT.exists():
    sys.path.insert(0, str(SPLIT_RUNTIME_ROOT))

from lightspeed_runtime.storage_paths import quality_root


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

TEST_MODULES = {
    "runtime_package": {
        "file": "test_runtime_package.py",
        "description": "Canonical runtime package and export path tests",
        "priority": 1,
    },
    "floors": {
        "file": "test_z_axis_floors.py",
        "description": "Z Axis floor validation",
        "priority": 1,
    },
    "simulations": {
        "file": "test_simulations.py",
        "description": "Physics and simulation tests",
        "priority": 2,
    },
    "scenarios": {
        "file": "test_scenarios.py",
        "description": "Template scenario tests",
        "priority": 3,
    },
    "z_direct": {
        "file": "test_z_direct.py",
        "description": "Z Direct inter-floor communication",
        "priority": 2,
    },
    "health": {
        "file": "test_health.py",
        "description": "System health checks",
        "priority": 1,
    },
}

QUICK_TESTS = ["runtime_package", "health", "floors"]  # Quick smoke test modules


# ============================================================================
# TEST RUNNER
# ============================================================================

class TestResult:
    """Result of a test module run."""

    def __init__(self, module: str, passed: int, failed: int, errors: int,
                 skipped: int, duration: float, output: str = ""):
        self.module = module
        self.passed = passed
        self.failed = failed
        self.errors = errors
        self.skipped = skipped
        self.duration = duration
        self.output = output
        self.total = passed + failed + errors + skipped

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 100.0
        return (self.passed / self.total) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "total": self.total,
            "success_rate": self.success_rate,
            "duration_seconds": self.duration,
        }


def run_pytest_module(module_file: str, verbose: bool = False) -> TestResult:
    """Run a single pytest module and parse results."""
    module_path = TESTS_DIR / module_file
    module_name = module_file.replace(".py", "")

    if not module_path.exists():
        return TestResult(module_name, 0, 0, 1, 0, 0, f"Module not found: {module_file}")

    # Build pytest command
    cmd = [sys.executable, "-m", "pytest", str(module_path)]
    if verbose:
        cmd.append("-v")
    cmd.extend(["--tb=short", "-q"])

    # Run pytest
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(TESTS_DIR)
        )
        output = result.stdout + result.stderr
        returncode = result.returncode
    except subprocess.TimeoutExpired:
        return TestResult(module_name, 0, 0, 1, 0, 300, "Test timeout")
    except Exception as e:
        return TestResult(module_name, 0, 0, 1, 0, 0, str(e))

    duration = time.time() - start_time

    # Parse pytest output for counts.
    # Pytest summary lines are not stable wrt decoration (e.g. "==== 1 failed, 54 passed ===="),
    # so we use regex to extract the final counts reliably.
    passed = failed = errors = skipped = 0
    for line in output.splitlines():
        line = line.strip()
        m = re.search(r"(\d+)\s+passed\b", line)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+)\s+failed\b", line)
        if m:
            failed = int(m.group(1))
        m = re.search(r"(\d+)\s+errors?\b", line)
        if m:
            errors = int(m.group(1))
        m = re.search(r"(\d+)\s+skipped\b", line)
        if m:
            skipped = int(m.group(1))

    # Pytest returncode is the most reliable indicator of pass/fail. Our regex can be
    # fooled by log lines that contain phrases like "1 failed" even when tests pass.
    if returncode == 0:
        failed = 0
        errors = 0

    return TestResult(module_name, passed, failed, errors, skipped, duration, output)


def run_all_tests(modules: List[str] = None, verbose: bool = False) -> Dict[str, Any]:
    """Run all specified test modules."""
    if modules is None:
        modules = list(TEST_MODULES.keys())

    results = []
    total_passed = total_failed = total_errors = total_skipped = 0
    total_duration = 0

    print("=" * 70)
    print("LIGHTSPEED CONSOLIDATED - TEST SUITE")
    print("=" * 70)
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"Modules to run: {len(modules)}")
    print("-" * 70)

    # Sort by priority
    sorted_modules = sorted(
        [(m, TEST_MODULES[m]) for m in modules if m in TEST_MODULES],
        key=lambda x: x[1]["priority"]
    )

    for module_name, module_config in sorted_modules:
        print(f"\n[RUNNING] {module_name}: {module_config['description']}")

        result = run_pytest_module(module_config["file"], verbose)
        results.append(result)

        total_passed += result.passed
        total_failed += result.failed
        total_errors += result.errors
        total_skipped += result.skipped
        total_duration += result.duration

        # Status indicator
        if result.failed == 0 and result.errors == 0:
            status = "[PASS]"
        elif result.errors > 0:
            status = "[ERROR]"
        else:
            status = "[FAIL]"

        print(f"  {status} Passed: {result.passed}, Failed: {result.failed}, "
              f"Errors: {result.errors}, Skipped: {result.skipped} ({result.duration:.2f}s)")

        if verbose and result.output:
            print(f"\n{result.output}")

    # Summary
    total_tests = total_passed + total_failed + total_errors + total_skipped
    overall_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Errors: {total_errors}")
    print(f"Skipped: {total_skipped}")
    print(f"Success Rate: {overall_rate:.1f}%")
    print(f"Total Duration: {total_duration:.2f}s")
    print("=" * 70)

    # Overall status
    if total_failed == 0 and total_errors == 0:
        print("\n[SUCCESS] ALL TESTS PASSED")
        print("System is ready for launch!")
    else:
        print("\n[WARNING] SOME TESTS FAILED")
        print("Please review failures before deployment.")

    return {
        "timestamp": datetime.now().isoformat(),
        "modules_run": len(results),
        "total_tests": total_tests,
        "passed": total_passed,
        "failed": total_failed,
        "errors": total_errors,
        "skipped": total_skipped,
        "success_rate": overall_rate,
        "duration_seconds": total_duration,
        "results": [r.to_dict() for r in results],
    }


def generate_html_report(report_data: Dict[str, Any], output_path: Path) -> None:
    """Generate an HTML report from test results."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>LightSpeed Test Report - {report_data['timestamp']}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #0a0e1a; color: #e0e6f0; }}
        h1 {{ color: #00d4ff; }}
        .summary {{ background: #141927; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .pass {{ color: #00ff00; }}
        .fail {{ color: #ff4444; }}
        .warn {{ color: #ffaa00; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #1e2738; padding: 12px; text-align: left; }}
        th {{ background: #1e2738; color: #00d4ff; }}
        tr:nth-child(even) {{ background: #141927; }}
        .progress-bar {{ background: #1e2738; height: 20px; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ background: linear-gradient(90deg, #00d4ff, #00ff00); height: 100%; }}
    </style>
</head>
<body>
    <h1>LightSpeed Consolidated - Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Timestamp:</strong> {report_data['timestamp']}</p>
        <p><strong>Modules Run:</strong> {report_data['modules_run']}</p>
        <p><strong>Total Tests:</strong> {report_data['total_tests']}</p>
        <p><strong>Passed:</strong> <span class="pass">{report_data['passed']}</span></p>
        <p><strong>Failed:</strong> <span class="fail">{report_data['failed']}</span></p>
        <p><strong>Errors:</strong> <span class="fail">{report_data['errors']}</span></p>
        <p><strong>Skipped:</strong> <span class="warn">{report_data['skipped']}</span></p>
        <p><strong>Duration:</strong> {report_data['duration_seconds']:.2f} seconds</p>
        <h3>Success Rate: <span class="{'pass' if report_data['success_rate'] >= 80 else 'fail'}">{report_data['success_rate']:.1f}%</span></h3>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {report_data['success_rate']}%;"></div>
        </div>
    </div>

    <h2>Module Results</h2>
    <table>
        <tr>
            <th>Module</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Errors</th>
            <th>Skipped</th>
            <th>Total</th>
            <th>Success Rate</th>
            <th>Duration</th>
        </tr>
"""

    for result in report_data['results']:
        rate_class = 'pass' if result['success_rate'] >= 80 else 'fail'
        html += f"""
        <tr>
            <td>{result['module']}</td>
            <td class="pass">{result['passed']}</td>
            <td class="fail">{result['failed']}</td>
            <td class="fail">{result['errors']}</td>
            <td class="warn">{result['skipped']}</td>
            <td>{result['total']}</td>
            <td class="{rate_class}">{result['success_rate']:.1f}%</td>
            <td>{result['duration_seconds']:.2f}s</td>
        </tr>
"""

    html += """
    </table>

    <p style="margin-top: 40px; color: #666;">
        Generated by LightSpeed Test Suite v5.1.1 - ACHILLES
    </p>
</body>
</html>
"""

    output_path.write_text(html)
    print(f"\nHTML report saved to: {output_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="LightSpeed Test Suite Runner")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke tests only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--module", "-m", type=str, help="Run specific module")

    args = parser.parse_args()

    # Determine modules to run
    if args.module:
        modules = [args.module]
    elif args.quick:
        modules = QUICK_TESTS
    else:
        modules = list(TEST_MODULES.keys())

    # Run tests
    report_data = run_all_tests(modules, args.verbose)

    # Generate report if requested
    if args.report:
        report_path = TESTS_DIR / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        generate_html_report(report_data, report_path)

    # Save JSON report
    json_report_path = quality_root(LIGHTSPEED_ROOT) / "latest_test_results.json"
    json_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"JSON results saved to: {json_report_path}")

    # Exit code based on results
    if report_data['failed'] > 0 or report_data['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
