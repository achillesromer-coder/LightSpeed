"""
Module Restoration Script
Restore missing core modules from backup archive to main codebase
"""

import shutil
from pathlib import Path

# Define paths
BACKUP_ROOT = Path(r"C:\Users\acc\Desktop\LightSpeed Consolidated\LightSpeed\Z Axis\Z-1_Morpheus\_CRYSTALLIZATION_BACKUP_20251214_224940\core")
MAIN_CORE = Path(r"C:\Users\acc\Desktop\LightSpeed Consolidated\LightSpeed\core")

# Modules to restore
MODULES_TO_RESTORE = {
    "analysis": ["__init__.py", "ast_analyzer.py", "indexer.py", "dependencies.py"],
    "cognigrex": "*",  # Copy all files
    "simulations": "*",
    "physics_modules": "*",
}

# Individual files to restore in existing directories
FILES_TO_RESTORE = {
    "rendering": ["hybrid_renderer.py", "sphere_primitive.py"],
}

def restore_module(module_name, files):
    """Restore a complete module directory"""
    backup_dir = BACKUP_ROOT / module_name
    target_dir = MAIN_CORE / module_name

    if not backup_dir.exists():
        print(f"[ERROR] Backup not found: {backup_dir}")
        return False

    # Create target directory
    target_dir.mkdir(exist_ok=True)
    print(f"[DIR] Created/verified: {target_dir}")

    # Copy files
    if files == "*":
        # Copy all Python files
        for file in backup_dir.glob("*.py"):
            target_file = target_dir / file.name
            shutil.copy2(file, target_file)
            print(f"  [OK] Copied: {file.name}")
    else:
        # Copy specific files
        for filename in files:
            source_file = backup_dir / filename
            target_file = target_dir / filename
            if source_file.exists():
                shutil.copy2(source_file, target_file)
                print(f"  [OK] Copied: {filename}")
            else:
                print(f"  [WARN] Not found: {filename}")

    return True

def restore_files(dir_name, files):
    """Restore individual files to existing directory"""
    backup_dir = BACKUP_ROOT / dir_name
    target_dir = MAIN_CORE / dir_name

    if not backup_dir.exists():
        print(f"[ERROR] Backup directory not found: {backup_dir}")
        return False

    if not target_dir.exists():
        print(f"[ERROR] Target directory doesn't exist: {target_dir}")
        return False

    for filename in files:
        source_file = backup_dir / filename
        target_file = target_dir / filename
        if source_file.exists():
            shutil.copy2(source_file, target_file)
            print(f"  [OK] Copied: {dir_name}/{filename}")
        else:
            print(f"  [WARN] Not found: {dir_name}/{filename}")

    return True

def main():
    print("=" * 60)
    print("LIGHTSPEED MODULE RESTORATION")
    print("=" * 60)
    print()

    # Restore complete modules
    print("[*] Restoring complete modules...")
    print()
    for module, files in MODULES_TO_RESTORE.items():
        print(f"Module: {module}")
        restore_module(module, files)
        print()

    # Restore individual files
    print("[*] Restoring individual files...")
    print()
    for dir_name, files in FILES_TO_RESTORE.items():
        print(f"Directory: {dir_name}")
        restore_files(dir_name, files)
        print()

    print("=" * 60)
    print("[OK] MODULE RESTORATION COMPLETE")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Test imports: python -c 'import core.analysis'")
    print("2. Fix service registry paths")
    print("3. Enable operational services")

if __name__ == "__main__":
    main()
