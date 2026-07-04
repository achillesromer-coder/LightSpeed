#!/usr/bin/env python
"""
Cross-Floor Alignment Analyzer
Ensures uniformity across the Z-Axis system with minimal reinstating
Uses Z-floor functions and calls according to architecture

Author: LightSpeed Team
Version: 1.0.0
Date: 2026-01-13
"""

import os
import json
import re
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

# Floor definitions
FLOORS = [
    ('Z+3_Trinity', 3, 'Trinity'),
    ('Z+2_Neo', 2, 'Neo'),
    ('Z+1_Architect', 1, 'Architect'),
    ('Z0_TheConstruct', 0, 'TheConstruct'),
    ('Z-1_Morpheus', -1, 'Morpheus'),
    ('Z-2_Oracle', -2, 'Oracle'),
    ('Z-3_Smith', -3, 'Smith'),
    ('Z-4_Merovingian', -4, 'Merovingian'),
]

class CrossFloorAnalyzer:
    """Analyze cross-floor alignments and misalignments"""

    def __init__(self):
        self.floor_data = {}
        self.misalignments = []
        self.inter_floor_calls = defaultdict(list)

    def analyze_all(self):
        """Run all analyses"""
        print("=" * 80)
        print("CROSS-FLOOR ALIGNMENT ANALYZER")
        print("=" * 80)
        print()

        self.analyze_z_direct_structure()
        self.analyze_inter_floor_imports()
        self.analyze_component_interfaces()
        self.analyze_service_availability()
        self.generate_alignment_plan()

    def analyze_z_direct_structure(self):
        """Analyze Z Direct communication structure"""
        print("1. Z DIRECT COMMUNICATION STRUCTURE")
        print("-" * 80)

        for floor_dir, z_level, floor_name in FLOORS:
            z_direct_path = Z_AXIS_ROOT / floor_dir / "Z Direct"
            if z_direct_path.exists():
                files = list(z_direct_path.glob("*.*"))
                dirs = [d for d in z_direct_path.iterdir() if d.is_dir()]

                # Check for standard Z Direct files
                expected_files = [
                    'communication_log.txt',
                    'data_objects.json',
                    'events.jsonl',
                    'floor_config.json',
                    'inter_floor_events.json',
                    'performance_metrics.json',
                    'status.html'
                ]

                missing = []
                for expected in expected_files:
                    if not (z_direct_path / expected).exists():
                        missing.append(expected)

                if missing:
                    print(f"{floor_name}: MISSING {len(missing)} files - {', '.join(missing[:3])}")
                    self.misalignments.append({
                        'floor': floor_name,
                        'type': 'z_direct_files',
                        'issue': f'Missing files: {", ".join(missing)}',
                        'severity': 'medium'
                    })
                else:
                    print(f"{floor_name}: OK - All standard files present")

                # Check for cross-floor communication directories
                expected_dirs = [f'Z{z_level:+d}' if z_level != 0 else 'Z0']
                for other_floor_dir, other_z, other_name in FLOORS:
                    if other_floor_dir != floor_dir:
                        dir_name = f'Z{other_z:+d}' if other_z != 0 else 'Z0'
                        expected_dirs.append(dir_name)

            else:
                print(f"{floor_name}: MISSING Z Direct directory!")
                self.misalignments.append({
                    'floor': floor_name,
                    'type': 'z_direct_missing',
                    'issue': 'No Z Direct directory',
                    'severity': 'high'
                })

        print()

    def analyze_inter_floor_imports(self):
        """Analyze inter-floor imports and dependencies"""
        print("2. INTER-FLOOR IMPORTS ANALYSIS")
        print("-" * 80)

        import_pattern = re.compile(r'from\s+(Z[\+\-]?\d+_\w+|Z Axis[\\/]Z[\+\-]?\d+_\w+)[\.\s]')
        direct_import_pattern = re.compile(r'import\s+(Z[\+\-]?\d+_\w+)')

        for floor_dir, z_level, floor_name in FLOORS:
            floor_path = Z_AXIS_ROOT / floor_dir
            py_files = list(floor_path.rglob('*.py'))

            imports_found = defaultdict(int)

            for py_file in py_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                        # Find imports
                        for match in import_pattern.finditer(content):
                            imported = match.group(1)
                            imports_found[imported] += 1

                        for match in direct_import_pattern.finditer(content):
                            imported = match.group(1)
                            imports_found[imported] += 1

                except Exception:
                    continue

            if imports_found:
                print(f"\n{floor_name} imports from other floors:")
                for imported, count in sorted(imports_found.items(), key=lambda x: x[1], reverse=True):
                    print(f"  - {imported}: {count} times")
                    self.inter_floor_calls[floor_name].append(imported)
            else:
                print(f"{floor_name}: No direct inter-floor imports (using Z Direct)")

        print()

    def analyze_component_interfaces(self):
        """Analyze component interface consistency"""
        print("3. COMPONENT INTERFACE CONSISTENCY")
        print("-" * 80)

        component_methods = {}

        for floor_dir, z_level, floor_name in FLOORS:
            components_dir = Z_AXIS_ROOT / floor_dir / 'components'
            if not components_dir.exists():
                continue

            # Find CoreComponent files
            core_component_files = list(components_dir.glob(f'{floor_name}CoreComponent.py'))

            if core_component_files:
                core_file = core_component_files[0]
                try:
                    with open(core_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                        # Find public methods
                        method_pattern = re.compile(r'def\s+([a-z_][a-z0-9_]*)\s*\(')
                        methods = [m.group(1) for m in method_pattern.finditer(content)
                                  if not m.group(1).startswith('_')]

                        component_methods[floor_name] = set(methods)
                        print(f"{floor_name}: {len(methods)} public methods in CoreComponent")

                except Exception as e:
                    print(f"{floor_name}: Error reading CoreComponent - {e}")
            else:
                print(f"{floor_name}: No CoreComponent found")

        # Find common methods
        if component_methods:
            all_methods = set.union(*component_methods.values())
            common_methods = set.intersection(*component_methods.values())

            print(f"\nCommon methods across all floors: {len(common_methods)}")
            if common_methods:
                print(f"  {', '.join(sorted(list(common_methods))[:10])}")

        print()

    def analyze_service_availability(self):
        """Analyze service availability and registration"""
        print("4. SERVICE AVAILABILITY ANALYSIS")
        print("-" * 80)

        for floor_dir, z_level, floor_name in FLOORS:
            manifest_path = Z_AXIS_ROOT / floor_dir / '_FLOOR_MANIFEST.json'

            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    services = data.get('services', [])
                    components = data.get('components', [])
                    capabilities = data.get('capabilities', [])

                    print(f"{floor_name}:")
                    print(f"  Services: {len(services)}")
                    print(f"  Components: {len(components)}")
                    print(f"  Capabilities: {len(capabilities)}")

                    # Check if services are properly registered
                    if len(services) == 0 and len(components) > 0:
                        self.misalignments.append({
                            'floor': floor_name,
                            'type': 'service_registration',
                            'issue': 'Has components but no registered services',
                            'severity': 'low'
                        })

            else:
                print(f"{floor_name}: No manifest found")

        print()

    def generate_alignment_plan(self):
        """Generate comprehensive alignment plan"""
        print("5. ALIGNMENT PLAN")
        print("=" * 80)
        print()

        if not self.misalignments:
            print("All floors are properly aligned!")
            return

        # Group by severity
        high = [m for m in self.misalignments if m['severity'] == 'high']
        medium = [m for m in self.misalignments if m['severity'] == 'medium']
        low = [m for m in self.misalignments if m['severity'] == 'low']

        if high:
            print("HIGH PRIORITY ISSUES:")
            print("-" * 80)
            for i, issue in enumerate(high, 1):
                print(f"{i}. [{issue['floor']}] {issue['issue']}")
                print(f"   Type: {issue['type']}")
                self._suggest_fix(issue)
            print()

        if medium:
            print("MEDIUM PRIORITY ISSUES:")
            print("-" * 80)
            for i, issue in enumerate(medium, 1):
                print(f"{i}. [{issue['floor']}] {issue['issue']}")
                print(f"   Type: {issue['type']}")
                self._suggest_fix(issue)
            print()

        if low:
            print("LOW PRIORITY ISSUES:")
            print("-" * 80)
            for i, issue in enumerate(low, 1):
                print(f"{i}. [{issue['floor']}] {issue['issue']}")
            print()

    def _suggest_fix(self, issue):
        """Suggest fix for an issue"""
        if issue['type'] == 'z_direct_missing':
            print(f"   Fix: Run create_z_direct_files.py to create Z Direct structure")
        elif issue['type'] == 'z_direct_files':
            print(f"   Fix: Populate missing files from Merovingian template")
        elif issue['type'] == 'service_registration':
            print(f"   Fix: Register services in _FLOOR_MANIFEST.json")

    def generate_inter_floor_map(self):
        """Generate inter-floor communication map"""
        print()
        print("6. INTER-FLOOR COMMUNICATION MAP")
        print("=" * 80)
        print()

        if not self.inter_floor_calls:
            print("All floors use Z Direct for communication (recommended)")
            return

        print("Direct import dependencies (should migrate to Z Direct):")
        print("-" * 80)

        for floor, imports in self.inter_floor_calls.items():
            if imports:
                print(f"\n{floor} ->")
                for imp in set(imports):
                    print(f"  +-- {imp}")

    def check_standard_compliance(self):
        """Check compliance with LightSpeed floor standards"""
        print()
        print("7. STANDARD COMPLIANCE CHECK")
        print("=" * 80)
        print()

        standards = {
            'has_manifest': True,
            'has_init': True,
            'has_components_dir': True,
            'has_z_direct': True,
            'has_config': True,
            'has_data': True,
            'has_docs': True,
            'has_examples': True
        }

        compliance_scores = {}

        for floor_dir, z_level, floor_name in FLOORS:
            floor_path = Z_AXIS_ROOT / floor_dir
            score = 0
            total = len(standards)

            if (floor_path / '_FLOOR_MANIFEST.json').exists():
                score += 1
            if (floor_path / '__init__.py').exists():
                score += 1
            if (floor_path / 'components').exists():
                score += 1
            if (floor_path / 'Z Direct').exists():
                score += 1
            if (floor_path / 'config').exists():
                score += 1
            if (floor_path / 'data').exists():
                score += 1
            if (floor_path / 'docs').exists():
                score += 1
            if (floor_path / 'examples').exists():
                score += 1

            compliance_scores[floor_name] = (score, total)
            percentage = (score / total) * 100

            status = "EXCELLENT" if percentage == 100 else "GOOD" if percentage >= 87.5 else "NEEDS WORK"
            print(f"{floor_name}: {score}/{total} ({percentage:.1f}%) - {status}")

        print()

        # Overall compliance
        total_score = sum(s for s, t in compliance_scores.values())
        total_possible = sum(t for s, t in compliance_scores.values())
        overall = (total_score / total_possible) * 100

        print(f"OVERALL Z-AXIS COMPLIANCE: {overall:.1f}%")

        if overall >= 95:
            print("Status: EXCELLENT - System is well-aligned")
        elif overall >= 85:
            print("Status: GOOD - Minor alignment issues")
        else:
            print("Status: NEEDS ATTENTION - Significant alignment work needed")

        print()

def main():
    analyzer = CrossFloorAnalyzer()
    analyzer.analyze_all()
    analyzer.generate_inter_floor_map()
    analyzer.check_standard_compliance()

    print("=" * 80)
    print(f"ANALYSIS COMPLETE - {len(analyzer.misalignments)} misalignments found")
    print("=" * 80)
    print()

if __name__ == '__main__':
    main()
