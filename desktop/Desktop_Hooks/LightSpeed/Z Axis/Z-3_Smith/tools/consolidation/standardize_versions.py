"""
LightSpeed V0.9.5 - Version Standardization Script
Updates all version strings to 0.9.5 across the codebase

Author: LightSpeed Team
Version: 0.9.5
Date: January 3, 2026
"""

import re
from pathlib import Path
from typing import List, Tuple

# Target version
TARGET_VERSION = "0.9.5"

# Root directory
LIGHTSPEED_ROOT = Path(__file__).parent

# Patterns to match version strings
VERSION_PATTERNS = [
    # Python docstrings
    (r'Version:\s*\d+\.\d+\.\d+', f'Version: {TARGET_VERSION}'),
    (r'version\s*=\s*["\'][\d\.]+["\']', f'version = "{TARGET_VERSION}"'),
    (r'__version__\s*=\s*["\'][\d\.]+["\']', f'__version__ = "{TARGET_VERSION}"'),

    # Comments
    (r'#\s*Version:\s*\d+\.\d+\.\d+', f'# Version: {TARGET_VERSION}'),
    (r'#\s*v\d+\.\d+\.\d+', f'# v{TARGET_VERSION}'),

    # Markdown
    (r'\*\*Version:\*\*\s*\d+\.\d+\.\d+', f'**Version:** {TARGET_VERSION}'),
    (r'Version\s+\d+\.\d+\.\d+', f'Version {TARGET_VERSION}'),

    # Specific patterns (don't match library versions like numpy 1.11.2)
    (r'LightSpeed\s+V?\d+\.\d+\.\d+', f'LightSpeed V{TARGET_VERSION}'),
]

# Files to exclude (contain library version numbers, not LightSpeed versions)
EXCLUDE_PATTERNS = [
    '**/node_modules/**',
    '**/.venv/**',
    '**/venv/**',
    '**/__pycache__/**',
    '**/site-packages/**',
    '**/.git/**',
    '**/build/**',
    '**/dist/**',
]


def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed"""
    # Check exclusions
    for pattern in EXCLUDE_PATTERNS:
        if file_path.match(pattern):
            return False

    # Only process specific file types
    return file_path.suffix in {'.py', '.md', '.txt', '.json', '.yaml', '.yml'}


def update_versions_in_file(file_path: Path, dry_run: bool = False) -> Tuple[bool, int]:
    """
    Update version strings in a file.

    Returns:
        (changed, count) - whether file was changed and number of replacements
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        total_replacements = 0

        # Apply each pattern
        for pattern, replacement in VERSION_PATTERNS:
            content, count = re.subn(pattern, replacement, content)
            total_replacements += count

        # Check if anything changed
        if content != original_content and total_replacements > 0:
            if not dry_run:
                file_path.write_text(content, encoding='utf-8')
            return True, total_replacements

        return False, 0

    except Exception as e:
        print(f"[ERROR] {file_path}: {e}")
        return False, 0


def main(dry_run: bool = False):
    """Execute version standardization"""
    print("=" * 70)
    print(f"LightSpeed Version Standardization -> {TARGET_VERSION}")
    print("=" * 70)
    print()

    if dry_run:
        print("[DRY RUN MODE] - No files will be modified")
        print()

    files_changed = 0
    total_replacements = 0
    files_processed = 0

    # Process all files
    for file_path in LIGHTSPEED_ROOT.rglob('*'):
        if not file_path.is_file():
            continue

        if not should_process_file(file_path):
            continue

        files_processed += 1
        changed, count = update_versions_in_file(file_path, dry_run=dry_run)

        if changed:
            files_changed += 1
            total_replacements += count
            rel_path = file_path.relative_to(LIGHTSPEED_ROOT)
            if dry_run:
                print(f"[WOULD UPDATE] {rel_path} ({count} replacements)")
            else:
                print(f"[UPDATED] {rel_path} ({count} replacements)")

    print()
    print("=" * 70)
    print(f"Files processed: {files_processed}")
    print(f"Files changed: {files_changed}")
    print(f"Total replacements: {total_replacements}")

    if dry_run:
        print()
        print("DRY RUN COMPLETE - No changes made")
        print(f"Run without --dry-run to update to version {TARGET_VERSION}")
    else:
        print()
        print(f"All versions standardized to {TARGET_VERSION}")

    print("=" * 70)


if __name__ == '__main__':
    import sys
    dry_run_mode = '--dry-run' in sys.argv or '-d' in sys.argv
    main(dry_run=dry_run_mode)
