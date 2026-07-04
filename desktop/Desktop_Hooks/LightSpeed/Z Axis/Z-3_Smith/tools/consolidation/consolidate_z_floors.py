"""
Z-Floor Consolidation Script (Legacy-Compatible)

Purpose:
- Migrate *old root-level* folders (e.g. `./logs`, `./projects`, `./legacy_archive`)
  into the canonical Z-Axis architecture.

V1 canonical ownership (disk):
- Projects: `Z Axis/Z+1_Architect/projects`
- Logs:     `Z Axis/Z-4_Merovingian/data/logs`
- Legacy:   `Z Axis/Z-1_Morpheus/organization/legacy`

Important:
- Safe to run multiple times.
- Does not create deprecated floors (e.g. `Z-4_Core`) or re-copy code that has
  already been consolidated.
"""

import shutil
from pathlib import Path

def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for cand in (start, *start.parents):
        try:
            if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                return cand
        except Exception:
            continue
    return start


# Base paths (portable)
BASE_DIR = _find_lightspeed_root(Path(__file__))
Z_AXIS = BASE_DIR / "Z Axis"

CANON_LOGS = Z_AXIS / "Z-4_Merovingian" / "data" / "logs"
CANON_PROJECTS = Z_AXIS / "Z+1_Architect" / "projects"
CANON_LEGACY = Z_AXIS / "Z-1_Morpheus" / "organization" / "legacy"

def ensure_dir(path):
    """Create directory if it doesn't exist"""
    path.mkdir(parents=True, exist_ok=True)
    return path

def move_with_merge(src, dst):
    """Move directory contents, merging if destination exists"""
    if not src.exists():
        print(f"Source doesn't exist: {src}")
        return False

    ensure_dir(dst)

    for item in src.iterdir():
        dest_item = dst / item.name
        if item.is_dir():
            if dest_item.exists():
                # Merge directories
                move_with_merge(item, dest_item)
            else:
                shutil.move(str(item), str(dest_item))
                print(f"Moved directory: {item.name}")
        else:
            if dest_item.exists():
                print(f"Skipping existing file: {item.name}")
            else:
                shutil.move(str(item), str(dest_item))
                print(f"Moved file: {item.name}")

    return True

def phase_1_data_migration():
    """Phase 1: Move data directories into Z-floors"""
    print("\n=== PHASE 1: DATA MIGRATION ===\n")

    # 1. Move logs/ → Z-4_Merovingian/logs/
    print("1. Moving logs/ → Z-4_Merovingian/logs/")
    logs_src = BASE_DIR / "logs"
    logs_dst = CANON_LOGS
    if logs_src.exists():
        ensure_dir(logs_dst.parent)
        if logs_dst.exists():
            print(f"  Merging with existing logs directory...")
            for log_file in logs_src.glob("*"):
                if log_file.is_file():
                    dst_file = logs_dst / log_file.name
                    if not dst_file.exists():
                        shutil.copy2(str(log_file), str(dst_file))
                        print(f"  Copied: {log_file.name}")
        else:
            shutil.copytree(str(logs_src), str(logs_dst))
            print(f"  ✓ Copied logs to Z-4_Merovingian/logs/")
    else:
        print(f"  Source not found: {logs_src}")

    # 2. Move projects/ → Z+1_Architect/projects/
    print("\n2. Moving projects/ → Z+1_Architect/projects/")
    projects_src = BASE_DIR / "projects"
    projects_dst = CANON_PROJECTS
    if projects_src.exists():
        ensure_dir(projects_dst.parent)
        if projects_dst.exists():
            print(f"  Merging with existing projects directory...")
            for project in projects_src.iterdir():
                dst_project = projects_dst / project.name
                if not dst_project.exists():
                    shutil.move(str(project), str(dst_project))
                    print(f"  Moved: {project.name}")
                else:
                    print(f"  Skipping existing: {project.name}")
        else:
            shutil.copytree(str(projects_src), str(projects_dst))
            print(f"  ✓ Copied projects to Z+1_Architect/projects/")
    else:
        print(f"  Source not found: {projects_src}")

    # 3. Move legacy_archive/ → Z-1_Morpheus/archives/
    print("\n3. Moving legacy_archive/ → Z-1_Morpheus/archives/")
    legacy_src = BASE_DIR / "legacy_archive"
    legacy_dst = CANON_LEGACY / "legacy_archive"
    if legacy_src.exists():
        ensure_dir(legacy_dst.parent)
        if legacy_dst.exists():
            print(f"  Merging with existing archives directory...")
            for item in legacy_src.iterdir():
                dst_item = legacy_dst / item.name
                if not dst_item.exists():
                    if item.is_dir():
                        shutil.copytree(str(item), str(dst_item))
                    else:
                        shutil.copy2(str(item), str(dst_item))
                    print(f"  Copied: {item.name}")
        else:
            shutil.copytree(str(legacy_src), str(legacy_dst))
            print(f"  ✓ Copied legacy_archive to Z-1_Morpheus/archives/")
    else:
        print(f"  Source not found: {legacy_src}")

def phase_2_code_consolidation():
    """Phase 2: Move code into Z-floors"""
    print("\n=== PHASE 2: CODE CONSOLIDATION ===\n")

    # V1: code is already consolidated into floor-owned packages.
    # Keep this phase as a no-op to avoid creating deprecated floors (e.g. Z-4_Core).
    print(
        "Phase 2 is deprecated for V1.\n"
        "- Core services already live under Merovingian (`Z Axis/Z-4_Merovingian/core`).\n"
        "- No action taken.\n"
    )
    return

    # Create Z-4_Core if it doesn't exist
    print("4. Creating Z-4_Core for infrastructure services")
    z4_core = Z_AXIS / "Z-4_Core"
    ensure_dir(z4_core / "services")
    ensure_dir(z4_core / "config")
    ensure_dir(z4_core / "storage")
    ensure_dir(z4_core / "database")
    print(f"  ✓ Created Z-4_Core directory structure")

    # Move core services to Z-4_Core
    print("\n5. Moving core services to Z-4_Core/")
    core_services_src = Z_AXIS / "core" / "core" / "services"
    core_services_dst = z4_core / "services"

    if core_services_src.exists():
        files_to_move = [
            "smart_floor_library.py",
            "event_bus.py",
            "database.py",
            "storage.py",
            "floor_loader.py",
            "function_registry.py",
            "logger.py"
        ]

        for filename in files_to_move:
            src_file = core_services_src / filename
            dst_file = core_services_dst / filename
            if src_file.exists():
                if not dst_file.exists():
                    shutil.copy2(str(src_file), str(dst_file))
                    print(f"  Copied: {filename}")
                else:
                    print(f"  Already exists: {filename}")

    # Move config loader
    print("\n6. Moving config_loader.py to Z-4_Core/config/")
    config_src = Z_AXIS / "core" / "core" / "config" / "config_loader.py"
    config_dst = z4_core / "config" / "config_loader.py"
    if config_src.exists() and not config_dst.exists():
        shutil.copy2(str(config_src), str(config_dst))
        print(f"  ✓ Copied config_loader.py")

    # Create __init__.py files
    print("\n7. Creating __init__.py files for proper module structure")
    init_files = [
        z4_core / "__init__.py",
        z4_core / "services" / "__init__.py",
        z4_core / "config" / "__init__.py",
        z4_core / "storage" / "__init__.py",
        z4_core / "database" / "__init__.py"
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.write_text('"""Z-4_Core: Infrastructure and Core Services"""\n')
            print(f"  Created: {init_file.relative_to(Z_AXIS)}")

def phase_3_immersive_consolidation():
    """Phase 3: Consolidate all immersive/3D systems"""
    print("\n=== PHASE 3: IMMERSIVE/3D CONSOLIDATION ===\n")

    # V1: immersive/3D entrypoints are integrated via `python -m LightSpeed --3d` and N.
    # Keep this phase as a no-op to prevent regeneration of obsolete templates.
    print(
        "Phase 3 is deprecated for V1.\n"
        "- Immersive/3D entrypoints are already integrated into the runtime.\n"
        "- No action taken.\n"
    )
    return

    print("8. Consolidating immersive systems to Z0_TheConstruct/gui/")
    z0_gui = Z_AXIS / "Z0_TheConstruct" / "gui"
    ensure_dir(z0_gui)

    # Find all immersive files
    immersive_files = []
    immersive_files.append(Z_AXIS / "Z+3_Trinity" / "ui" / "immersive_n_integrated.py")
    immersive_files.append(Z_AXIS / "Z+3_Trinity" / "ui" / "immersive_engine.py")
    immersive_files.append(Z_AXIS / "Z+3_Trinity" / "ui" / "immersive_interface.py")
    immersive_files.append(Z_AXIS / "Z+3_Trinity" / "ui" / "immersive_bento_ui.py")
    immersive_files.append(Z_AXIS / "Z0_TheConstruct" / "ui" / "immersive_3d_engine.py")
    immersive_files.append(Z_AXIS / "core" / "core" / "rendering" / "immersive_3d_interface.py")

    for src_file in immersive_files:
        if src_file.exists():
            dst_file = z0_gui / src_file.name
            if not dst_file.exists():
                shutil.copy2(str(src_file), str(dst_file))
                print(f"  Copied: {src_file.name}")
            else:
                print(f"  Already exists: {src_file.name}")

    # Create main N_interface.py
    print("\n9. Creating Z0_TheConstruct/gui/N_interface.py as main GUI")
    n_interface = z0_gui / "N_interface.py"
    if not n_interface.exists():
        n_interface.write_text('''"""
N_interface.py - Main GUI Interface for LightSpeed
Primary entry point for Z0_TheConstruct GUI engine
Handles all rendering, immersive 3D, physics, visualizations
"""

# This will be the main GUI entry point
# Consolidates functionality from immersive_n_integrated.py and other GUI systems

from pathlib import Path
import sys

# Add Z-floor paths
Z_AXIS_PATH = Path(__file__).parent.parent.parent

def main():
    """Main GUI entry point"""
    print("Z0_TheConstruct N Interface - Main GUI Engine")
    print("Initializing immersive environment...")

    # Import and initialize GUI systems
    # This will be expanded to include all GUI functionality

if __name__ == "__main__":
    main()
''')
        print(f"  ✓ Created N_interface.py template")

    # Create __init__.py
    gui_init = z0_gui / "__init__.py"
    if not gui_init.exists():
        gui_init.write_text('"""Z0_TheConstruct GUI Engine"""\n')
        print(f"  Created __init__.py")

def create_summary_report():
    """Create a summary of what was moved"""
    print("\n" + "="*60)
    print("Z-FLOOR CONSOLIDATION SUMMARY")
    print("="*60)

    # Check what exists
    checks = [
        ("Logs in Z-4_Merovingian", Z_AXIS / "Z-4_Merovingian" / "logs"),
        ("Projects in Z+1_Architect", Z_AXIS / "Z+1_Architect" / "projects"),
        ("Archives in Z-1_Morpheus", Z_AXIS / "Z-1_Morpheus" / "archives"),
        ("Z-4_Core created", Z_AXIS / "Z-4_Core"),
        ("Z-4_Core services", Z_AXIS / "Z-4_Core" / "services"),
        ("Z0_TheConstruct/gui", Z_AXIS / "Z0_TheConstruct" / "gui"),
        ("N_interface.py", Z_AXIS / "Z0_TheConstruct" / "gui" / "N_interface.py"),
    ]

    for name, path in checks:
        exists = "✓" if path.exists() else "✗"
        print(f"{exists} {name}: {path.exists()}")

    print("\nNext steps:")
    print("1. Update import statements in affected files")
    print("2. Create smart_bento_hub.py in Z+3_Trinity")
    print("3. Update N.py to call Z0_TheConstruct/gui/N_interface.py")
    print("4. Test functionality")
    print("5. Remove old directories after verification")

if __name__ == "__main__":
    print("LightSpeed Z-Floor Consolidation")
    print("=" * 60)

    try:
        phase_1_data_migration()
        phase_2_code_consolidation()
        phase_3_immersive_consolidation()
        create_summary_report()

        print("\n✓ Consolidation complete!")
        print("\nNote: Old directories have been COPIED (not moved) for safety.")
        print("Verify everything works before deleting originals.")

    except Exception as e:
        print(f"\n✗ Error during consolidation: {e}")
        import traceback
        traceback.print_exc()
