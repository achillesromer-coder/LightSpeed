#!/usr/bin/env python
"""
LightSpeed Library Usage Analysis
Systematically analyzes all Python imports across the platform

Author: LightSpeed Team
Version: 0.9.5
Date: January 12, 2026
"""

import ast
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for cand in (start, *start.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return start.parent


LIGHTSPEED_ROOT = _find_lightspeed_root(Path(__file__))
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"

# Floors to analyze
FLOORS = [
    "Z-4_Merovingian",
    "Z-3_Smith",
    "Z-2_Oracle",
    "Z-1_Morpheus",
    "Z0_TheConstruct",
    "Z+1_Architect",
    "Z+2_Neo",
    "Z+3_Trinity"
]

class ImportAnalyzer(ast.NodeVisitor):
    """AST visitor to extract import statements"""

    def __init__(self):
        self.imports = []
        self.from_imports = []

    def visit_Import(self, node):
        """Handle 'import X' statements"""
        for alias in node.names:
            self.imports.append({
                'module': alias.name,
                'alias': alias.asname,
                'line': node.lineno
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Handle 'from X import Y' statements"""
        module = node.module if node.module else ''
        for alias in node.names:
            self.from_imports.append({
                'module': module,
                'name': alias.name,
                'alias': alias.asname,
                'level': node.level,
                'line': node.lineno
            })
        self.generic_visit(node)


class LibraryScanner:
    """Scan all Python files and analyze library usage"""

    def __init__(self):
        self.stdlib_modules = self._get_stdlib_modules()
        self.all_imports = defaultdict(list)
        self.floor_imports = defaultdict(lambda: defaultdict(list))
        self.file_count = 0
        self.error_files = []

    def _get_stdlib_modules(self) -> Set[str]:
        """Get standard library module names"""
        return {
            'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections',
            'concurrent', 'contextlib', 'copy', 'csv', 'datetime', 'decimal',
            'difflib', 'enum', 'functools', 'glob', 'hashlib', 'heapq',
            'importlib', 'io', 'itertools', 'json', 'logging', 'math',
            'multiprocessing', 'os', 'pathlib', 'pickle', 're', 'shutil',
            'socket', 'sqlite3', 'string', 'struct', 'subprocess', 'sys',
            'tempfile', 'textwrap', 'threading', 'time', 'traceback',
            'typing', 'unittest', 'urllib', 'uuid', 'warnings', 'weakref',
            'xml', 'zipfile', 'gzip', 'tarfile', 'codecs', 'dataclasses',
            'statistics', 'random', 'secrets', 'queue', 'configparser',
            'signal', 'email', 'html', 'http', 'urllib.parse'
        }

    def scan_file(self, file_path: Path, floor_name: str = None) -> Dict:
        """Scan a single Python file for imports"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            analyzer = ImportAnalyzer()
            analyzer.visit(tree)

            imports = {
                'file': str(file_path.relative_to(LIGHTSPEED_ROOT)),
                'floor': floor_name,
                'imports': analyzer.imports,
                'from_imports': analyzer.from_imports,
                'total': len(analyzer.imports) + len(analyzer.from_imports)
            }

            # Categorize imports
            for imp in analyzer.imports:
                module = imp['module'].split('.')[0]
                self.all_imports[module].append({
                    'file': imports['file'],
                    'floor': floor_name,
                    'line': imp['line'],
                    'full_module': imp['module']
                })
                if floor_name:
                    self.floor_imports[floor_name][module].append(imports['file'])

            for imp in analyzer.from_imports:
                module = imp['module'].split('.')[0] if imp['module'] else ''
                if module:
                    self.all_imports[module].append({
                        'file': imports['file'],
                        'floor': floor_name,
                        'line': imp['line'],
                        'full_module': imp['module'],
                        'imported': imp['name']
                    })
                    if floor_name:
                        self.floor_imports[floor_name][module].append(imports['file'])

            self.file_count += 1
            return imports

        except SyntaxError as e:
            self.error_files.append({
                'file': str(file_path.relative_to(LIGHTSPEED_ROOT)),
                'error': f"SyntaxError: {e}"
            })
            return None
        except Exception as e:
            self.error_files.append({
                'file': str(file_path.relative_to(LIGHTSPEED_ROOT)),
                'error': f"{type(e).__name__}: {e}"
            })
            return None

    def scan_floor(self, floor_name: str) -> List[Dict]:
        """Scan all Python files in a floor"""
        floor_dir = Z_AXIS_ROOT / floor_name
        results = []

        if not floor_dir.exists():
            print(f"[WARN] Floor not found: {floor_name}")
            return results

        # Find all Python files (excluding venv/env/site-packages)
        for py_file in floor_dir.rglob("*.py"):
            # Skip virtual environments and cache
            if any(part in str(py_file) for part in ['env', '.venv', 'site-packages', '__pycache__']):
                continue

            result = self.scan_file(py_file, floor_name)
            if result:
                results.append(result)

        return results

    def categorize_libraries(self) -> Dict:
        """Categorize all libraries into stdlib, third-party, and local"""
        categories = {
            'stdlib': defaultdict(int),
            'third_party': defaultdict(int),
            'local': defaultdict(int),
            'unknown': defaultdict(int)
        }

        for module, usages in self.all_imports.items():
            count = len(usages)

            if module in self.stdlib_modules:
                categories['stdlib'][module] = count
            elif module.startswith('.') or not module:
                categories['local'][module] = count
            elif module in ['PyQt6', 'PyQt5', 'PySide6', 'flask', 'fastapi',
                           'requests', 'numpy', 'pandas', 'matplotlib', 'scipy',
                           'sklearn', 'tensorflow', 'torch', 'ollama', 'openai']:
                categories['third_party'][module] = count
            else:
                # Check if it's a local module
                if module in ['Merovingian', 'Smith', 'Oracle', 'Morpheus',
                             'TheConstruct', 'Architect', 'Neo', 'Trinity']:
                    categories['local'][module] = count
                else:
                    categories['unknown'][module] = count

        return categories

    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        categories = self.categorize_libraries()

        # Top 20 most used libraries
        top_libraries = sorted(
            self.all_imports.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:20]

        # Libraries by floor
        floor_summary = {}
        for floor, imports in self.floor_imports.items():
            floor_summary[floor] = {
                'total_libraries': len(imports),
                'top_5': sorted(
                    imports.items(),
                    key=lambda x: len(set(x[1])),
                    reverse=True
                )[:5]
            }

        report = {
            'summary': {
                'files_scanned': self.file_count,
                'total_unique_libraries': len(self.all_imports),
                'stdlib_count': len(categories['stdlib']),
                'third_party_count': len(categories['third_party']),
                'local_count': len(categories['local']),
                'unknown_count': len(categories['unknown']),
                'errors': len(self.error_files)
            },
            'categories': {
                'stdlib': dict(sorted(categories['stdlib'].items(),
                                     key=lambda x: x[1], reverse=True)),
                'third_party': dict(sorted(categories['third_party'].items(),
                                          key=lambda x: x[1], reverse=True)),
                'local': dict(sorted(categories['local'].items(),
                                    key=lambda x: x[1], reverse=True)),
                'unknown': dict(sorted(categories['unknown'].items(),
                                      key=lambda x: x[1], reverse=True))
            },
            'top_20_libraries': [
                {
                    'library': lib,
                    'usage_count': len(usages),
                    'files': len(set(u['file'] for u in usages)),
                    'floors': len(set(u['floor'] for u in usages if u['floor']))
                }
                for lib, usages in top_libraries
            ],
            'floor_summary': floor_summary,
            'errors': self.error_files
        }

        return report


def main():
    """Main execution"""
    print("=" * 80)
    print("LightSpeed Library Usage Analysis")
    print("=" * 80)

    scanner = LibraryScanner()

    # Scan all floors
    print("\nScanning Z-Axis floors...")
    for floor in FLOORS:
        print(f"  [{floor}] Scanning...")
        results = scanner.scan_floor(floor)
        print(f"    Files scanned: {len(results)}")

    # Scan root Z Axis files
    print("\n  [Root Files] Scanning...")
    root_files = ['N.py', 'Merovingian.py', 'Smith.py', 'Oracle.py', 'Morpheus.py',
                  'TheConstruct.py', 'Architect.py', 'Neo.py', 'Trinity.py']
    for filename in root_files:
        file_path = LIGHTSPEED_ROOT / filename
        if file_path.exists():
            scanner.scan_file(file_path, 'Root')

    # Generate report
    print("\n" + "=" * 80)
    print("Generating Analysis Report")
    print("=" * 80)

    report = scanner.generate_report()

    # Save report
    output_file = (
        Z_AXIS_ROOT
        / "Z-1_Morpheus"
        / "documentation"
        / "_ZAxisRoot_Archive"
        / "LIBRARY_USAGE_ANALYSIS.json"
    )
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\n[OK] Report saved: {output_file.name}")

    # Print summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Files Scanned: {report['summary']['files_scanned']}")
    print(f"Total Unique Libraries: {report['summary']['total_unique_libraries']}")
    print(f"  - Standard Library: {report['summary']['stdlib_count']}")
    print(f"  - Third-Party: {report['summary']['third_party_count']}")
    print(f"  - Local Modules: {report['summary']['local_count']}")
    print(f"  - Unknown: {report['summary']['unknown_count']}")
    print(f"Errors: {report['summary']['errors']}")

    print("\nTop 10 Most Used Libraries:")
    for i, lib in enumerate(report['top_20_libraries'][:10], 1):
        print(f"  {i:2d}. {lib['library']:20s} - {lib['usage_count']:4d} usages across {lib['files']:3d} files")

    if report['summary']['errors'] > 0:
        print(f"\n[WARN] {report['summary']['errors']} files had parsing errors")
        print("  See LIBRARY_USAGE_ANALYSIS.json for details")

    return report


if __name__ == "__main__":
    report = main()
