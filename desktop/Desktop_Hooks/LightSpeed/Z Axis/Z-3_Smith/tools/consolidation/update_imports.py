"""
LightSpeed V0.9.5 - Import Path Update Script
Updates all hardcoded paths to use centralized config

This script:
1. Finds all hardcoded paths (./data, ./logs, etc.)
2. Replaces with centralized imports from core.config.paths
3. Updates import statements
4. Preserves file integrity

Author: LightSpeed Team
Version: 0.9.5
Date: January 3, 2026
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Set
import sys

# Root directory
LIGHTSPEED_ROOT = Path(__file__).parent

# Import replacement patterns
# Maps old hardcoded paths → new centralized imports
PATH_REPLACEMENTS = {
    # Data folder
    r"Path\(['\"]\.\/[Dd]ata['\"]?\)": "MEROVINGIAN_DATA",
    r"['\"]\.\/[Dd]ata\/?['\"]": "str(MEROVINGIAN_DATA)",
    r"os\.path\.join\([^,]+,\s*['\"][Dd]ata['\"]": "MEROVINGIAN_DATA",

    # Docs folder
    r"Path\(['\"]\.\/docs['\"]?\)": "MORPHEUS_DOCS",
    r"['\"]\.\/docs\/?['\"]": "str(MORPHEUS_DOCS)",

    # Knowledge folder
    r"Path\(['\"]\.\/knowledge['\"]?\)": "MORPHEUS_KNOWLEDGE",
    r"['\"]\.\/knowledge\/?['\"]": "str(MORPHEUS_KNOWLEDGE)",

    # Library folder
    r"Path\(['\"]\.\/[Ll]ibrary['\"]?\)": "MORPHEUS_LIBRARY",
    r"['\"]\.\/[Ll]ibrary\/?['\"]": "str(MORPHEUS_LIBRARY)",

    # Logs folder
    r"Path\(['\"]\.\/logs['\"]?\)": "SMITH_LOGS",
    r"['\"]\.\/logs\/?['\"]": "str(SMITH_LOGS)",

    # Output folder
    r"Path\(['\"]\.\/[Oo]utput['\"]?\)": "TRINITY_OUTPUT",
    r"['\"]\.\/[Oo]utput\/?['\"]": "str(TRINITY_OUTPUT)",

    # Tools archive
    r"Path\(['\"]\.\/tools_archive['\"]?\)": "ARCHITECT_TOOLS",
    r"['\"]\.\/tools_archive\/?['\"]": "str(ARCHITECT_TOOLS)",

    # Immersive modules
    r"Path\(['\"]\.\/immersive_modules['\"]?\)": "ORACLE_IMMERSIVE",
    r"['\"]\.\/immersive_modules\/?['\"]": "str(ORACLE_IMMERSIVE)",

    # AI logs
    r"Path\(['\"]\.\/ai_logs['\"]?\)": "NEO_AGENT / 'logs'",
    r"['\"]\.\/ai_logs\/?['\"]": "str(NEO_AGENT / 'logs')",
}

# Required imports for each path constant
REQUIRED_IMPORTS = {
    'MEROVINGIAN_DATA': 'from core.config.paths import MEROVINGIAN_DATA',
    'MORPHEUS_DOCS': 'from core.config.paths import MORPHEUS_DOCS',
    'MORPHEUS_KNOWLEDGE': 'from core.config.paths import MORPHEUS_KNOWLEDGE',
    'MORPHEUS_LIBRARY': 'from core.config.paths import MORPHEUS_LIBRARY',
    'SMITH_LOGS': 'from core.config.paths import SMITH_LOGS',
    'TRINITY_OUTPUT': 'from core.config.paths import TRINITY_OUTPUT',
    'ARCHITECT_TOOLS': 'from core.config.paths import ARCHITECT_TOOLS',
    'ORACLE_IMMERSIVE': 'from core.config.paths import ORACLE_IMMERSIVE',
    'NEO_AGENT': 'from core.config.paths import NEO_AGENT',
}

# Files to exclude
EXCLUDE_PATTERNS = [
    '**/.venv/**',
    '**/venv/**',
    '**/__pycache__/**',
    '**/site-packages/**',
    '**/.git/**',
    '**/build/**',
    '**/dist/**',
    '**/node_modules/**',
    # Exclude the config file itself
    '**/core/config/paths.py',
    # Exclude migration scripts
    '**/migrate_to_z_floors.py',
    '**/update_imports.py',
    '**/standardize_versions.py',
]


def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed"""
    # Check exclusions
    for pattern in EXCLUDE_PATTERNS:
        if file_path.match(pattern):
            return False

    # Only process Python files
    return file_path.suffix == '.py'


def find_hardcoded_paths(content: str) -> List[str]:
    """Find all hardcoded path patterns in content"""
    found = []
    for pattern in PATH_REPLACEMENTS.keys():
        matches = re.findall(pattern, content)
        found.extend(matches)
    return found


def update_imports_in_file(file_path: Path, dry_run: bool = False) -> Tuple[bool, int, Set[str]]:
    """
    Update hardcoded paths in a file.

    Returns:
        (changed, replacement_count, required_imports)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        total_replacements = 0
        imports_needed = set()

        # Apply each pattern
        for pattern, replacement in PATH_REPLACEMENTS.items():
            if re.search(pattern, content):
                content, count = re.subn(pattern, replacement, content)
                total_replacements += count

                # Track which imports we need
                for const_name in REQUIRED_IMPORTS.keys():
                    if const_name in replacement:
                        imports_needed.add(const_name)

        # Add required imports if any replacements were made
        if total_replacements > 0 and imports_needed:
            # Check if file already has imports from core.config.paths
            has_config_import = 'from core.config.paths import' in content or 'from core.config import' in content

            if not has_config_import:
                # Find where to insert imports (after existing imports)
                lines = content.split('\n')
                insert_pos = 0

                # Find last import line
                for i, line in enumerate(lines):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        insert_pos = i + 1
                    elif line.strip() and not line.strip().startswith('#'):
                        # First non-import, non-comment line
                        if insert_pos > 0:
                            break

                # Build import statement
                import_names = sorted(imports_needed)
                if len(import_names) == 1:
                    import_stmt = REQUIRED_IMPORTS[import_names[0]]
                else:
                    import_stmt = f"from core.config.paths import {', '.join(import_names)}"

                # Insert import
                lines.insert(insert_pos, import_stmt)
                content = '\n'.join(lines)

        # Check if anything changed
        if content != original_content:
            if not dry_run:
                file_path.write_text(content, encoding='utf-8')
            return True, total_replacements, imports_needed

        return False, 0, set()

    except Exception as e:
        print(f"[ERROR] {file_path}: {e}")
        return False, 0, set()


def main(dry_run: bool = False):
    """Execute import updates"""
    print("=" * 70)
    print("LightSpeed V0.9.5 - Import Path Update")
    print("=" * 70)
    print()

    if dry_run:
        print("[DRY RUN MODE] - No files will be modified")
        print()

    files_changed = 0
    total_replacements = 0
    files_processed = 0

    # First pass: find all files with hardcoded paths
    print("[Phase 1] Scanning for hardcoded paths...")
    print()

    files_to_update = []
    for file_path in LIGHTSPEED_ROOT.rglob('*.py'):
        if not should_process_file(file_path):
            continue

        files_processed += 1
        try:
            content = file_path.read_text(encoding='utf-8')
            hardcoded = find_hardcoded_paths(content)
            if hardcoded:
                files_to_update.append((file_path, hardcoded))
        except:
            pass

    print(f"Found {len(files_to_update)} files with hardcoded paths")
    print(f"Processed {files_processed} Python files")
    print()

    # Second pass: update files
    print("[Phase 2] Updating imports...")
    print()

    for file_path, _ in files_to_update:
        changed, count, imports = update_imports_in_file(file_path, dry_run=dry_run)

        if changed:
            files_changed += 1
            total_replacements += count
            rel_path = file_path.relative_to(LIGHTSPEED_ROOT)

            if dry_run:
                print(f"[WOULD UPDATE] {rel_path}")
                print(f"               {count} path replacements")
                if imports:
                    print(f"               Imports needed: {', '.join(sorted(imports))}")
            else:
                print(f"[UPDATED] {rel_path}")
                print(f"          {count} path replacements")
                if imports:
                    print(f"          Added imports: {', '.join(sorted(imports))}")

    print()
    print("=" * 70)
    print(f"Files scanned: {files_processed}")
    print(f"Files with hardcoded paths: {len(files_to_update)}")
    print(f"Files updated: {files_changed}")
    print(f"Total replacements: {total_replacements}")

    if dry_run:
        print()
        print("DRY RUN COMPLETE - No changes made")
        print("Run without --dry-run to update imports")
    else:
        print()
        print("Import updates complete!")
        print()
        print("Next steps:")
        print("1. Test imports: python -c 'import N'")
        print("2. Run N.py: python N.py")
        print("3. Verify all floors load correctly")

    print("=" * 70)


if __name__ == '__main__':
    dry_run_mode = '--dry-run' in sys.argv or '-d' in sys.argv

    if not dry_run_mode:
        print()
        print("This will update hardcoded paths to use centralized config")
        print()
        response = input("Continue? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Update cancelled")
            sys.exit(0)
        print()

    main(dry_run=dry_run_mode)
