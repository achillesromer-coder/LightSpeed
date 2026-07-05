#!/usr/bin/env python
"""
Analyze Z-Floor Structure Consistency
Identifies misalignments and ensures uniformity across the Z-Axis system
"""

import os
import json
from pathlib import Path
from collections import defaultdict
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

floors = [
    'Z+3_Trinity', 'Z+2_Neo', 'Z+1_Architect',
    'Z0_TheConstruct', 'Z-1_Morpheus', 'Z-2_Oracle', 'Z-3_Smith', 'Z-4_Merovingian'
]

# Standard directory structure expected on all floors
STANDARD_DIRS = ['components', 'config', 'data', 'docs', 'examples']
OPTIONAL_DIRS = ['tests', 'assets', 'legacy']

def analyze_directory_structure():
    """Analyze directory structure across all floors"""
    print("=" * 80)
    print("Z-FLOOR DIRECTORY STRUCTURE ANALYSIS")
    print("=" * 80)
    print()

    all_dirs = {}
    missing_standard = {}

    for floor in floors:
        floor_path = Z_AXIS_ROOT / floor
        if not floor_path.exists():
            print(f"[ERROR] Floor {floor} does not exist!")
            continue

        # Get all subdirectories (excluding hidden and private)
        subdirs = [d.name for d in floor_path.iterdir()
                  if d.is_dir() and not d.name.startswith(('_', '.'))]
        all_dirs[floor] = sorted(subdirs)

        # Check for missing standard directories
        missing = [d for d in STANDARD_DIRS if d not in subdirs]
        if missing:
            missing_standard[floor] = missing

    # Find all unique directories across floors
    all_unique = set()
    for dirs in all_dirs.values():
        all_unique.update(dirs)

    # Print directory presence matrix
    print("Directory Presence Matrix:")
    print("-" * 80)
    print(f"{'Floor':<20} {'components':<12} {'config':<12} {'data':<12} {'docs':<12} {'examples':<12}")
    print("-" * 80)

    for floor in floors:
        dirs = all_dirs.get(floor, [])
        row = f"{floor:<20} "
        for std_dir in STANDARD_DIRS:
            status = "YES" if std_dir in dirs else "MISSING"
            row += f"{status:<12} "
        print(row)

    print()
    print("=" * 80)

    # Report missing standard directories
    if missing_standard:
        print("\nMISSING STANDARD DIRECTORIES:")
        print("-" * 80)
        for floor, missing in missing_standard.items():
            print(f"{floor}: {', '.join(missing)}")
    else:
        print("\nAll floors have standard directories!")

    print()
    print("=" * 80)

    # Show unique/custom directories per floor
    print("\nUNIQUE/CUSTOM DIRECTORIES PER FLOOR:")
    print("-" * 80)
    for floor in floors:
        dirs = all_dirs.get(floor, [])
        unique = [d for d in dirs if d not in STANDARD_DIRS + OPTIONAL_DIRS]
        if unique:
            print(f"{floor}: {', '.join(unique)}")

    return all_dirs, missing_standard

def analyze_manifest_consistency():
    """Analyze _FLOOR_MANIFEST.json consistency"""
    print()
    print("=" * 80)
    print("FLOOR MANIFEST CONSISTENCY ANALYSIS")
    print("=" * 80)
    print()

    manifests = {}

    for floor in floors:
        manifest_path = Z_AXIS_ROOT / floor / '_FLOOR_MANIFEST.json'
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                manifests[floor] = data

    # Check required fields
    required_fields = ['floor_name', 'z_level', 'version', 'description']

    print(f"{'Floor':<20} {'Name':<15} {'Z-Level':<10} {'Version':<10} {'Services':<10} {'Components':<12}")
    print("-" * 80)

    for floor in floors:
        if floor in manifests:
            m = manifests[floor]
            print(f"{floor:<20} {m.get('floor_name', 'N/A'):<15} {m.get('z_level', 'N/A'):<10} "
                  f"{m.get('version', 'N/A'):<10} {len(m.get('services', [])):<10} "
                  f"{len(m.get('components', [])):<12}")
        else:
            print(f"{floor:<20} {'MISSING MANIFEST':<15}")

    print()
    print("=" * 80)

    # Check for inconsistencies
    print("\nMANIFEST INCONSISTENCIES:")
    print("-" * 80)

    issues = []
    for floor in floors:
        if floor not in manifests:
            issues.append(f"{floor}: Missing _FLOOR_MANIFEST.json")
            continue

        m = manifests[floor]

        # Check required fields
        for field in required_fields:
            if field not in m:
                issues.append(f"{floor}: Missing required field '{field}'")
                continue
            val = m.get(field)
            # Treat numeric 0 as valid (e.g. z_level for Z0_TheConstruct)
            if val is None or (isinstance(val, str) and not val.strip()):
                issues.append(f"{floor}: Missing required field '{field}'")

        # Check version consistency
        if m.get('version') != '1.0.0':
            issues.append(f"{floor}: Version mismatch (expected 1.0.0, got {m.get('version')})")

    if issues:
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("  No inconsistencies found!")

    return manifests

def analyze_init_files():
    """Analyze __init__.py consistency"""
    print()
    print("=" * 80)
    print("__init__.py FILE ANALYSIS")
    print("=" * 80)
    print()

    print(f"{'Floor':<20} {'__init__.py':<15} {'Size (bytes)':<15}")
    print("-" * 80)

    for floor in floors:
        init_path = Z_AXIS_ROOT / floor / '__init__.py'
        if init_path.exists():
            size = init_path.stat().st_size
            print(f"{floor:<20} {'YES':<15} {size:<15}")
        else:
            print(f"{floor:<20} {'MISSING':<15} {'N/A':<15}")

def analyze_component_structure():
    """Analyze components directory structure"""
    print()
    print("=" * 80)
    print("COMPONENTS DIRECTORY ANALYSIS")
    print("=" * 80)
    print()

    for floor in floors:
        components_dir = Z_AXIS_ROOT / floor / 'components'
        if components_dir.exists():
            files = list(components_dir.glob('*.py'))
            print(f"{floor}: {len(files)} Python files in components/")
            if files:
                for f in files[:5]:  # Show first 5
                    print(f"  - {f.name}")
                if len(files) > 5:
                    print(f"  ... and {len(files) - 5} more")
        else:
            print(f"{floor}: [MISSING] components/ directory")
        print()

def generate_alignment_report():
    """Generate comprehensive alignment report"""
    print()
    print("=" * 80)
    print("CROSS-FLOOR ALIGNMENT RECOMMENDATIONS")
    print("=" * 80)
    print()

    recommendations = []

    # Check for missing directories
    for floor in floors:
        floor_path = Z_AXIS_ROOT / floor
        if not floor_path.exists():
            continue

        for std_dir in STANDARD_DIRS:
            dir_path = floor_path / std_dir
            if not dir_path.exists():
                recommendations.append({
                    'floor': floor,
                    'action': f'Create missing {std_dir}/ directory',
                    'priority': 'HIGH',
                    'command': f'mkdir "{floor_path / std_dir}"'
                })

    # Check for __init__.py
    for floor in floors:
        init_path = Z_AXIS_ROOT / floor / '__init__.py'
        if not init_path.exists():
            recommendations.append({
                'floor': floor,
                'action': 'Create __init__.py',
                'priority': 'HIGH',
                'command': f'touch "{init_path}"'
            })

    # Group by priority
    high_priority = [r for r in recommendations if r['priority'] == 'HIGH']
    medium_priority = [r for r in recommendations if r['priority'] == 'MEDIUM']

    if high_priority:
        print("HIGH PRIORITY:")
        print("-" * 80)
        for i, rec in enumerate(high_priority, 1):
            print(f"{i}. [{rec['floor']}] {rec['action']}")
            print(f"   Command: {rec['command']}")
            print()

    if medium_priority:
        print("MEDIUM PRIORITY:")
        print("-" * 80)
        for i, rec in enumerate(medium_priority, 1):
            print(f"{i}. [{rec['floor']}] {rec['action']}")
            print(f"   Command: {rec['command']}")
            print()

    if not recommendations:
        print("All floors are properly aligned!")

    return recommendations

if __name__ == '__main__':
    # Run all analyses
    all_dirs, missing_standard = analyze_directory_structure()
    manifests = analyze_manifest_consistency()
    analyze_init_files()
    analyze_component_structure()
    recommendations = generate_alignment_report()

    print()
    print("=" * 80)
    print(f"ANALYSIS COMPLETE - {len(recommendations)} recommendations generated")
    print("=" * 80)
