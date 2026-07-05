#!/usr/bin/env python
"""
Dependency Manager - Centralized Requirements Management
LightSpeed Type I Civilization Platform

Smart floor-aware dependency management:
- Auto-discovers requirements from all Z-Axis floors
- Aggregates into master requirements file
- Maintains floor-specific requirement files
- Detects new dependencies and updates Construct master
- Prevents duplicate dependencies
- Validates version compatibility
- Generates installation commands

Architecture:
- TheConstruct hosts the master requirements
- Each floor can have optional requirements.txt
- Setup/install flows live under Trinity (Z+3) for this consolidated build
- NEO orchestrates updates via smart floor functions

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

import re
import argparse
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import sys

# Find LightSpeed root
LIGHTSPEED_ROOT = Path(__file__).resolve()
for candidate in (LIGHTSPEED_ROOT, *LIGHTSPEED_ROOT.parents):
    if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
        LIGHTSPEED_ROOT = candidate
        break

Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
CONSTRUCT_ROOT = Z_AXIS_ROOT / "Z0_TheConstruct"
REQUIREMENTS_DIR = CONSTRUCT_ROOT / "requirements"


@dataclass
class Dependency:
    """Single package dependency"""
    package: str
    version_spec: str
    source_floor: str
    is_core: bool = False
    is_optional: bool = False
    notes: Optional[str] = None

    def to_requirement_line(self) -> str:
        """Convert to requirements.txt format"""
        line = f"{self.package}{self.version_spec}"
        if self.notes:
            line += f"  # {self.notes}"
        return line

    @classmethod
    def from_line(cls, line: str, source_floor: str) -> Optional['Dependency']:
        """Parse from requirements.txt line"""
        # Remove comments
        if '#' in line:
            parts = line.split('#', 1)
            line = parts[0].strip()
            notes = parts[1].strip()
        else:
            notes = None

        line = line.strip()
        if not line or line.startswith('#'):
            return None

        # Parse package and version
        match = re.match(r'^([a-zA-Z0-9_-]+)(.*?)$', line)
        if not match:
            return None

        package = match.group(1).lower()
        version_spec = match.group(2)

        return cls(
            package=package,
            version_spec=version_spec,
            source_floor=source_floor,
            notes=notes
        )


class DependencyManager:
    """
    Centralized dependency management system

    Responsibilities:
    - Discover floor requirements
    - Aggregate dependencies
    - Detect conflicts
    - Generate master requirements
    - Update on new floor additions
    """

    # Standard library modules (don't need pip install)
    STDLIB_MODULES = {
        'tkinter', 'sqlite3', 'json', 'pathlib', 'datetime', 'time',
        'threading', 'asyncio', 'collections', 'dataclasses', 'enum',
        'typing', 'functools', 'itertools', 'contextlib', 'logging',
        'os', 'sys', 're', 'io', 'shutil', 'subprocess', 'urllib',
        'http', 'email', 'xml', 'html', 'csv', 'pickle', 'hashlib',
        'secrets', 'random', 'math', 'statistics', 'decimal', 'fractions'
    }

    # Core dependencies required by all installations
    CORE_PACKAGES = {
        'pillow', 'matplotlib', 'numpy', 'pandas', 'psutil',
        'fastapi', 'uvicorn', 'pydantic', 'websockets',
        'pytest', 'pytest-asyncio'
    }

    # Floor definitions
    FLOORS = [
        ('Z+3_Trinity', 'Trinity Coordination'),
        ('Z+3_Trinity', 'Trinity Dashboard'),
        ('Z+2_Neo', 'Neo AI Orchestration'),
        ('Z+1_Architect', 'Architect Task Management'),
        ('Z0_TheConstruct', 'TheConstruct Simulations'),
        ('Z-1_Morpheus', 'Morpheus Knowledge'),
        ('Z-2_Oracle', 'Oracle Predictions'),
        ('Z-3_Smith', 'Smith Security'),
        ('Z-4_Merovingian', 'Merovingian Core Services')
    ]

    def __init__(self):
        self.dependencies: Dict[str, Dependency] = {}
        self.floor_dependencies: Dict[str, List[Dependency]] = defaultdict(list)
        self.conflicts: List[Tuple[str, Dependency, Dependency]] = []

    def discover_floor_requirements(self, floor_path: Path, floor_name: str) -> List[Dependency]:
        """
        Discover requirements for a specific floor

        Searches in order:
        1. floor_path/requirements.txt
        2. floor_path/requirements/requirements.txt
        3. Returns empty if none found
        """
        search_paths = [
            floor_path / "requirements.txt",
            floor_path / "requirements" / "requirements.txt"
        ]

        for req_file in search_paths:
            if req_file.exists():
                print(f"  Found requirements: {req_file.relative_to(LIGHTSPEED_ROOT)}")
                return self._parse_requirements_file(req_file, floor_name)

        return []

    def _parse_requirements_file(self, file_path: Path, floor_name: str) -> List[Dependency]:
        """Parse requirements.txt file"""
        dependencies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    dep = Dependency.from_line(line, floor_name)
                    if dep:
                        # Mark as core if in core packages
                        dep.is_core = dep.package in self.CORE_PACKAGES
                        dependencies.append(dep)
        except Exception as e:
            print(f"  Warning: Error parsing {file_path}: {e}")

        return dependencies

    def scan_all_floors(self):
        """Scan all Z-Axis floors for requirements"""
        print("Scanning Z-Axis floors for dependencies...")
        print("=" * 70)

        for floor_dir, floor_desc in self.FLOORS:
            floor_path = Z_AXIS_ROOT / floor_dir

            if not floor_path.exists():
                print(f"[SKIP] {floor_dir}: Directory not found")
                continue

            print(f"\n[SCAN] {floor_dir} - {floor_desc}")

            deps = self.discover_floor_requirements(floor_path, floor_dir)

            if deps:
                self.floor_dependencies[floor_dir] = deps
                print(f"  Discovered {len(deps)} dependencies")

                for dep in deps:
                    self._add_dependency(dep)
            else:
                print(f"  No requirements.txt found (using core dependencies)")

        print(f"\n{'=' * 70}")
        print(f"Total unique dependencies: {len(self.dependencies)}")
        print(f"Floors with dependencies: {len(self.floor_dependencies)}")

    def _add_dependency(self, dep: Dependency):
        """Add dependency and check for conflicts"""
        if dep.package in self.STDLIB_MODULES:
            print(f"  Note: {dep.package} is stdlib, skipping")
            return

        existing = self.dependencies.get(dep.package)

        if existing:
            # Check version conflict
            if existing.version_spec != dep.version_spec:
                self.conflicts.append((dep.package, existing, dep))
                print(f"  Conflict: {dep.package} version mismatch")
                print(f"    {existing.source_floor}: {existing.version_spec}")
                print(f"    {dep.source_floor}: {dep.version_spec}")

                # Use more restrictive version
                if self._is_more_restrictive(dep.version_spec, existing.version_spec):
                    self.dependencies[dep.package] = dep
            # else: same version, no action needed
        else:
            self.dependencies[dep.package] = dep

    def _is_more_restrictive(self, ver1: str, ver2: str) -> bool:
        """Determine which version spec is more restrictive"""
        # Simple heuristic: more specific is more restrictive
        if not ver1:
            return False
        if not ver2:
            return True

        # If one has == and other has >=, prefer ==
        if '==' in ver1 and '>=' in ver2:
            return True
        if '==' in ver2 and '>=' in ver1:
            return False

        # Otherwise, prefer newer version
        return ver1 > ver2

    def generate_master_requirements(self) -> str:
        """Generate master requirements.txt content"""
        lines = []

        lines.append("# LightSpeed Platform - Master Requirements")
        lines.append("# Auto-generated by dependency_manager.py")
        lines.append(f"# Total floors scanned: {len(self.FLOORS)}")
        lines.append(f"# Total unique dependencies: {len(self.dependencies)}")
        lines.append("# Version: 1.2.0")
        lines.append("")

        # Core dependencies
        lines.append("# " + "=" * 68)
        lines.append("# CORE DEPENDENCIES (Required for all installations)")
        lines.append("# " + "=" * 68)
        lines.append("")

        core_deps = [d for d in self.dependencies.values() if d.is_core]
        for dep in sorted(core_deps, key=lambda d: d.package):
            lines.append(dep.to_requirement_line())

        lines.append("")

        # Floor-specific dependencies
        lines.append("# " + "=" * 68)
        lines.append("# FLOOR-SPECIFIC DEPENDENCIES")
        lines.append("# " + "=" * 68)
        lines.append("")

        non_core_deps = [d for d in self.dependencies.values() if not d.is_core]

        # Group by floor
        for floor_dir, floor_desc in self.FLOORS:
            floor_deps = [d for d in non_core_deps if d.source_floor == floor_dir]

            if floor_deps:
                lines.append(f"# --- {floor_dir} - {floor_desc} ---")
                for dep in sorted(floor_deps, key=lambda d: d.package):
                    lines.append(dep.to_requirement_line())
                lines.append("")

        # Conflicts section
        if self.conflicts:
            lines.append("# " + "=" * 68)
            lines.append("# VERSION CONFLICTS DETECTED")
            lines.append("# " + "=" * 68)
            lines.append("")

            for package, dep1, dep2 in self.conflicts:
                lines.append(f"# Conflict: {package}")
                lines.append(f"#   {dep1.source_floor}: {dep1.version_spec}")
                lines.append(f"#   {dep2.source_floor}: {dep2.version_spec}")
                lines.append(f"#   Resolution: Using {self.dependencies[package].version_spec}")
                lines.append("")

        return '\n'.join(lines)

    def generate_core_requirements(self) -> str:
        """Generate minimal core requirements"""
        lines = []

        lines.append("# LightSpeed Platform - Core Dependencies Only")
        lines.append("# Minimal installation for basic functionality")
        lines.append("# Version: 1.2.0")
        lines.append("")

        core_deps = [d for d in self.dependencies.values() if d.is_core]
        for dep in sorted(core_deps, key=lambda d: d.package):
            lines.append(dep.to_requirement_line())

        return '\n'.join(lines)

    def generate_floor_requirements(self, floor_dir: str) -> str:
        """Generate requirements for specific floor"""
        lines = []

        floor_desc = next((desc for d, desc in self.FLOORS if d == floor_dir), floor_dir)

        lines.append(f"# {floor_desc} - Requirements")
        lines.append(f"# Floor: {floor_dir}")
        lines.append("# Version: 1.2.0")
        lines.append("")
        lines.append("# Core dependencies (required)")
        lines.append("-r requirements_core.txt")
        lines.append("")

        # Floor-specific
        floor_deps = self.floor_dependencies.get(floor_dir, [])
        non_core = [d for d in floor_deps if not d.is_core]

        if non_core:
            lines.append(f"# {floor_desc} specific dependencies")
            for dep in sorted(non_core, key=lambda d: d.package):
                lines.append(dep.to_requirement_line())
        else:
            lines.append("# No additional dependencies required")

        return '\n'.join(lines)

    def save_all_requirements(self):
        """Save all generated requirement files"""
        print("\nGenerating requirement files...")
        print("=" * 70)

        # Ensure directory exists
        REQUIREMENTS_DIR.mkdir(parents=True, exist_ok=True)

        # Master requirements
        master_file = REQUIREMENTS_DIR / "requirements_master.txt"
        master_content = self.generate_master_requirements()
        master_file.write_text(master_content, encoding='utf-8')
        print(f"[SAVED] {master_file.relative_to(LIGHTSPEED_ROOT)}")

        # Core requirements
        core_file = REQUIREMENTS_DIR / "requirements_core.txt"
        core_content = self.generate_core_requirements()
        core_file.write_text(core_content, encoding='utf-8')
        print(f"[SAVED] {core_file.relative_to(LIGHTSPEED_ROOT)}")

        # Floor-specific requirements
        for floor_dir, _ in self.FLOORS:
            if floor_dir in self.floor_dependencies:
                floor_file = REQUIREMENTS_DIR / f"requirements_{floor_dir.lower()}.txt"
                floor_content = self.generate_floor_requirements(floor_dir)
                floor_file.write_text(floor_content, encoding='utf-8')
                print(f"[SAVED] {floor_file.relative_to(LIGHTSPEED_ROOT)}")

        print(f"{'=' * 70}")
        print(f"All requirement files saved to: {REQUIREMENTS_DIR.relative_to(LIGHTSPEED_ROOT)}")

    def create_base_templates(self):
        """Create base template requirements for floors without them"""
        print("\nCreating base templates for floors...")
        print("=" * 70)

        for floor_dir, floor_desc in self.FLOORS:
            floor_path = Z_AXIS_ROOT / floor_dir

            if not floor_path.exists():
                continue

            req_file = floor_path / "requirements.txt"

            if not req_file.exists():
                template = f"""# {floor_desc} - Requirements
# Floor: {floor_dir}
#
# Add floor-specific dependencies here.
# Core dependencies are automatically included from TheConstruct.
#
# Format: package>=version
# Example: scipy>=1.11.0
#
# Run dependency sync to update master:
# python Z0_TheConstruct/tools/dependency_manager.py --sync

# Floor-specific dependencies (add below)
"""
                req_file.write_text(template, encoding='utf-8')
                print(f"[CREATED] {req_file.relative_to(LIGHTSPEED_ROOT)}")

        print(f"{'=' * 70}")

    def print_summary(self):
        """Print summary statistics"""
        print("\nDependency Management Summary")
        print("=" * 70)

        print(f"\nFloors scanned: {len(self.FLOORS)}")
        print(f"Floors with dependencies: {len(self.floor_dependencies)}")
        print(f"Total unique packages: {len(self.dependencies)}")
        print(f"Core packages: {len([d for d in self.dependencies.values() if d.is_core])}")
        print(f"Floor-specific packages: {len([d for d in self.dependencies.values() if not d.is_core])}")

        if self.conflicts:
            print(f"\nVersion conflicts: {len(self.conflicts)}")
            for package, _, _ in self.conflicts:
                print(f"  - {package}")
        else:
            print("\nNo version conflicts detected")

        print("\nInstallation commands:")
        print(f"  Full install:    pip install -r {REQUIREMENTS_DIR.relative_to(LIGHTSPEED_ROOT)}/requirements_master.txt")
        print(f"  Core only:       pip install -r {REQUIREMENTS_DIR.relative_to(LIGHTSPEED_ROOT)}/requirements_core.txt")
        print(f"  Specific floor:  pip install -r {REQUIREMENTS_DIR.relative_to(LIGHTSPEED_ROOT)}/requirements_[floor].txt")

        print("=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LightSpeed Dependency Manager - Smart Floor-Aware Package Management"
    )

    parser.add_argument(
        '--sync',
        action='store_true',
        help='Scan all floors and update master requirements'
    )

    parser.add_argument(
        '--create-templates',
        action='store_true',
        help='Create base requirement templates for floors without them'
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Check for conflicts without updating files'
    )

    args = parser.parse_args()

    # Create manager
    manager = DependencyManager()

    if args.create_templates:
        manager.create_base_templates()
        return

    # Scan floors
    manager.scan_all_floors()

    if args.check:
        # Just show summary
        manager.print_summary()
    else:
        # Save files (default with --sync or no args)
        manager.save_all_requirements()
        manager.print_summary()


if __name__ == "__main__":
    main()
