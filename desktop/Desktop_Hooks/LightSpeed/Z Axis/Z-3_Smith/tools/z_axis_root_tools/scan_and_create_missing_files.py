#!/usr/bin/env python
"""
Scan Z Axis Structure and Create Missing Files
Systematically maps directory structure and creates missing base files

Author: LightSpeed Team
Version: 0.9.0
Date: January 12, 2026
"""

from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Set
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

# Standard directory structure for each floor
STANDARD_DIRECTORIES = [
    "components",
    "ui",
    "tools",
    "data",
    "config",
    "tests",
    "docs",
    "examples",
    "Z Direct"
]

# Standard files for each floor root
STANDARD_ROOT_FILES = [
    "__init__.py",
    "README.md",
    ".gitignore"
]

# Standard files for components directory
COMPONENT_FILES = [
    "__init__.py"
]

# Floor definitions with expected structure
FLOORS = {
    "Z-4_Merovingian": {
        "name": "Merovingian",
        "z_level": -4,
        "key_components": ["database", "event_bus", "storage", "logger", "performance_monitor", "cache_manager", "websocket_server"]
    },
    "Z-3_Smith": {
        "name": "Smith",
        "z_level": -3,
        "key_components": ["security_scanner", "validator", "integrity_checker"]
    },
    "Z-2_Oracle": {
        "name": "Oracle",
        "z_level": -2,
        "key_components": ["prediction_engine", "archive_manager", "ip_vault"]
    },
    "Z-1_Morpheus": {
        "name": "Morpheus",
        "z_level": -1,
        "key_components": ["knowledge_base", "indexer", "semantic_search"]
    },
    "Z0_TheConstruct": {
        "name": "TheConstruct",
        "z_level": 0,
        "key_components": ["simulation_engine", "3d_renderer", "physics_tools"]
    },
    "Z+1_Architect": {
        "name": "Architect",
        "z_level": 1,
        "key_components": ["task_manager", "project_planner", "okr_tracker"]
    },
    "Z+2_Neo": {
        "name": "Neo",
        "z_level": 2,
        "key_components": ["ai_orchestrator", "cognigrex", "code_assistant", "context_manager"]
    },
    "Z+3_Trinity": {
        "name": "Trinity",
        "z_level": 3,
        "key_components": ["dashboard", "service_manager", "portal_glass", "settings_hub"]
    }
}


class FloorScanner:
    """Scan floor structure and identify missing files"""

    def __init__(self, floor_dir: Path, floor_info: Dict):
        self.floor_dir = floor_dir
        self.floor_info = floor_info
        self.missing_dirs = []
        self.missing_files = []
        self.existing_structure = {}

    def scan(self):
        """Scan floor directory structure"""
        print(f"\n[{self.floor_info['name']}] Scanning Z-Level {self.floor_info['z_level']:+d}")
        print(f"  Location: {self.floor_dir.relative_to(Z_AXIS_ROOT)}")

        # Check standard directories
        for dir_name in STANDARD_DIRECTORIES:
            dir_path = self.floor_dir / dir_name
            if not dir_path.exists():
                self.missing_dirs.append(dir_name)
            else:
                # Scan subdirectory
                self.existing_structure[dir_name] = self._scan_directory(dir_path)

        # Check root files
        for file_name in STANDARD_ROOT_FILES:
            file_path = self.floor_dir / file_name
            if not file_path.exists():
                self.missing_files.append(('root', file_name))

        # Check component __init__.py files
        components_dir = self.floor_dir / "components"
        if components_dir.exists() and not (components_dir / "__init__.py").exists():
            self.missing_files.append(('components', '__init__.py'))

        # Report findings
        self._report()

    def _scan_directory(self, directory: Path) -> Dict:
        """Recursively scan directory"""
        structure = {
            'files': [],
            'subdirs': {}
        }

        try:
            for item in directory.iterdir():
                if item.is_file():
                    structure['files'].append(item.name)
                elif item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_'):
                    structure['subdirs'][item.name] = self._scan_directory(item)
        except PermissionError:
            pass

        return structure

    def _report(self):
        """Report scan results"""
        if self.missing_dirs:
            print(f"  Missing directories ({len(self.missing_dirs)}):")
            for dir_name in self.missing_dirs:
                print(f"    - {dir_name}/")

        if self.missing_files:
            print(f"  Missing files ({len(self.missing_files)}):")
            for location, file_name in self.missing_files:
                print(f"    - {location}/{file_name}")

        if not self.missing_dirs and not self.missing_files:
            print(f"  [OK] All standard directories and files present")


class FloorBuilder:
    """Create missing directories and files"""

    def __init__(self, floor_dir: Path, floor_info: Dict):
        self.floor_dir = floor_dir
        self.floor_info = floor_info

    def create_missing_structure(self, missing_dirs: List[str], missing_files: List[tuple]):
        """Create all missing directories and files"""
        created_count = 0

        # Create directories
        for dir_name in missing_dirs:
            dir_path = self.floor_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"    [CREATED] {dir_name}/")
            created_count += 1

            # Create __init__.py in each new directory
            if dir_name not in ['data', 'config', 'docs', 'examples', 'Z Direct']:
                init_file = dir_path / "__init__.py"
                self._create_init_file(init_file, dir_name)
                created_count += 1

        # Create files
        for location, file_name in missing_files:
            if location == 'root':
                file_path = self.floor_dir / file_name
            else:
                file_path = self.floor_dir / location / file_name

            if file_name == '__init__.py':
                self._create_init_file(file_path, location)
            elif file_name == 'README.md':
                self._create_readme(file_path)
            elif file_name == '.gitignore':
                self._create_gitignore(file_path)

            print(f"    [CREATED] {location}/{file_name}")
            created_count += 1

        return created_count

    def _create_init_file(self, file_path: Path, package_name: str):
        """Create __init__.py file"""
        content = f'''"""
{self.floor_info['name']} Floor - {package_name.title()} Package

Part of the LightSpeed Type I Civilization Platform
Z-Level: {self.floor_info['z_level']:+d}

This package contains {package_name} functionality for the {self.floor_info['name']} floor.

Author: LightSpeed Team
Version: 0.9.0
Date: {datetime.now().strftime('%Y-%m-%d')}
"""

__version__ = "0.9.0"
__floor__ = "{self.floor_info['name']}"
__z_level__ = {self.floor_info['z_level']}

# Package exports will be added here as components are developed
__all__ = []
'''

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_readme(self, file_path: Path):
        """Create README.md file"""
        content = f'''# {self.floor_info['name']} Floor

**Z-Level:** {self.floor_info['z_level']:+d}
**Version:** 0.9.0
**Status:** Operational

---

## Overview

The {self.floor_info['name']} floor is part of the LightSpeed Type I Civilization Platform's Z-Axis architecture.

## Key Components

'''

        for component in self.floor_info['key_components']:
            content += f"- **{component}** - Component functionality\n"

        content += f'''
## Directory Structure

```
{self.floor_dir.name}/
├── {self.floor_info['name']}.py          # Main floor entry point
├── __init__.py              # Package initialization
├── README.md                # This file
├── components/              # Core components
├── ui/                      # User interface elements
├── tools/                   # Utility tools
├── data/                    # Data files
├── config/                  # Configuration files
├── tests/                   # Unit tests
├── docs/                    # Documentation
├── examples/                # Usage examples
└── Z Direct/                # Inter-floor communication
```

## Usage

```python
from {self.floor_dir.name} import initialize

# Initialize the floor
success = initialize()

if success:
    print("{self.floor_info['name']} floor initialized successfully")
```

## Dependencies

See `floor_manifest.json` in the Z Direct folder for complete dependency information.

## Contributing

When adding new components:
1. Create component file in `components/`
2. Add to `__init__.py` exports
3. Update this README
4. Add tests in `tests/`
5. Document in `docs/`

---

**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
**Maintainer:** LightSpeed Team
'''

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_gitignore(self, file_path: Path):
        """Create .gitignore file"""
        content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Data
data/*
!data/.gitkeep

# Cache
cache/
*.cache

# Temporary
temp/
tmp/
*.tmp

# Config (if sensitive)
config/secrets.json
config/credentials.json

# Testing
.pytest_cache/
.coverage
htmlcov/

# Z Direct (runtime data)
Z Direct/*.json
!Z Direct/floor_manifest.json
Z Direct/*.txt
'''

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)


def main():
    """Main execution"""
    print("=" * 70)
    print("LightSpeed Z-Axis Structure Scan and File Creation")
    print("=" * 70)

    total_missing_dirs = 0
    total_missing_files = 0
    total_created = 0

    # Scan all floors
    scanners = {}
    for floor_dir_name, floor_info in FLOORS.items():
        floor_dir = Z_AXIS_ROOT / floor_dir_name

        if not floor_dir.exists():
            print(f"\n[ERROR] Floor directory not found: {floor_dir_name}")
            continue

        scanner = FloorScanner(floor_dir, floor_info)
        scanner.scan()
        scanners[floor_dir_name] = scanner

        total_missing_dirs += len(scanner.missing_dirs)
        total_missing_files += len(scanner.missing_files)

    # Summary
    print("\n" + "=" * 70)
    print("Scan Summary")
    print("=" * 70)
    print(f"Floors scanned: {len(FLOORS)}")
    print(f"Missing directories: {total_missing_dirs}")
    print(f"Missing files: {total_missing_files}")

    if total_missing_dirs == 0 and total_missing_files == 0:
        print("\n[OK] All floors have complete standard structure!")
        return

    # Ask to create missing items
    print("\n" + "=" * 70)
    print("Creating Missing Structure")
    print("=" * 70)

    for floor_dir_name, scanner in scanners.items():
        if scanner.missing_dirs or scanner.missing_files:
            print(f"\n[{scanner.floor_info['name']}] Creating missing items...")
            floor_dir = Z_AXIS_ROOT / floor_dir_name
            builder = FloorBuilder(floor_dir, scanner.floor_info)
            created = builder.create_missing_structure(scanner.missing_dirs, scanner.missing_files)
            total_created += created

    print("\n" + "=" * 70)
    print("[SUCCESS] Structure Creation Complete")
    print("=" * 70)
    print(f"Total items created: {total_created}")
    print(f"  Directories: {total_missing_dirs}")
    print(f"  Files: {total_missing_files}")


if __name__ == "__main__":
    main()
