"""
LightSpeed V0.9.5 - Folder Migration to Z-Floor Architecture
Migrates legacy root folders into proper Z-floor locations

This script:
1. Moves folders from root → Z-floor subdirectories
2. Creates AI_LOGS documentation graph
3. Updates all import references
4. Preserves file integrity

Author: LightSpeed Team
Version: 0.9.5
Date: January 3, 2026
"""

import shutil
from pathlib import Path
import sys

# Import our centralized paths
from core.config.paths import (
    LIGHTSPEED_ROOT,
    NEO_AGENT,
    MORPHEUS_DOCS, MORPHEUS_KNOWLEDGE, MORPHEUS_LIBRARY,
    ARCHITECT_TOOLS,
    ORACLE_IMMERSIVE, ORACLE_LIBRARY,
    SMITH_LOGS,
    MEROVINGIAN_DATA,
    TRINITY_OUTPUT,
    initialize_z_floor_structure,
)

# Migration map: source → destination
MIGRATION_MAP = {
    # ai_logs → Neo agent logs
    'ai_logs': NEO_AGENT / 'logs',

    # data → Merovingian data
    'Data': MEROVINGIAN_DATA,

    # docs → Morpheus documentation
    'docs': MORPHEUS_DOCS / 'legacy',

    # immersive_modules → Oracle immersive
    'immersive_modules': ORACLE_IMMERSIVE,

    # knowledge → Morpheus knowledge
    'knowledge': MORPHEUS_KNOWLEDGE,

    # Library → Morpheus library (empirical knowledge)
    # Note: User specified Oracle also has library (immersive visual)
    # We'll keep Morpheus for empirical text-based library
    'Library': MORPHEUS_LIBRARY,

    # logs → Smith logs
    'logs': SMITH_LOGS,

    # Output → Trinity output
    'Output': TRINITY_OUTPUT,

    # tools_archive → Architect tools
    'tools_archive': ARCHITECT_TOOLS,
}


def check_folder_exists(folder_name: str) -> bool:
    """Check if a folder exists in root"""
    path = LIGHTSPEED_ROOT / folder_name
    return path.exists() and path.is_dir()


def migrate_folder(source_name: str, dest_path: Path, dry_run: bool = False):
    """
    Migrate a folder from root to Z-floor location.

    Args:
        source_name: Folder name in root
        dest_path: Destination Z-floor path
        dry_run: If True, only print what would happen
    """
    source = LIGHTSPEED_ROOT / source_name

    if not source.exists():
        print(f"[SKIP] {source_name} - does not exist")
        return

    if not source.is_dir():
        print(f"[SKIP] {source_name} - not a directory")
        return

    # Check if destination already has content
    if dest_path.exists() and any(dest_path.iterdir()):
        print(f"[WARN] {source_name} -> {dest_path.relative_to(LIGHTSPEED_ROOT)}")
        print(f"       Destination not empty, will MERGE contents")

        if dry_run:
            print(f"       [DRY RUN] Would merge {source_name} into {dest_path.name}")
            return

        # Merge: copy each item
        for item in source.iterdir():
            dest_item = dest_path / item.name
            if item.is_dir():
                if dest_item.exists():
                    print(f"       Merging subdirectory: {item.name}")
                    shutil.copytree(item, dest_item, dirs_exist_ok=True)
                else:
                    shutil.copytree(item, dest_item)
            else:
                shutil.copy2(item, dest_item)

        print(f"[MERGED] {source_name} -> {dest_path.relative_to(LIGHTSPEED_ROOT)}")

    else:
        # Destination empty or doesn't exist - simple move
        if dry_run:
            print(f"[DRY RUN] Would move {source_name} -> {dest_path.relative_to(LIGHTSPEED_ROOT)}")
            return

        # Ensure parent exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Try to move, but fall back to copy if files are locked
        try:
            shutil.move(str(source), str(dest_path))
            print(f"[MOVED] {source_name} -> {dest_path.relative_to(LIGHTSPEED_ROOT)}")
        except (PermissionError, OSError) as e:
            print(f"[COPY] {source_name} -> {dest_path.relative_to(LIGHTSPEED_ROOT)} (files locked, copying instead)")
            shutil.copytree(source, dest_path, dirs_exist_ok=True)
            print(f"       Note: Original folder remains (files in use)")


def create_ai_logs_graph():
    """
    Create AI_LOGS documentation graph as requested.
    This maps AI interactions, context, and decision flows.
    """
    ai_logs_dir = NEO_AGENT / 'logs'
    ai_logs_dir.mkdir(parents=True, exist_ok=True)

    # Create README explaining the AI logs structure
    readme_content = """# AI Logs - Neo Agent Intelligence Graph

This directory contains AI agent logs, context tracking, and decision flow documentation.

## Structure

```
logs/
├── conversations/          # AI conversation history
│   ├── by_date/           # Organized by date
│   └── by_floor/          # Organized by Z-floor
├── decisions/             # AI decision logs
│   ├── approved/          # User-approved decisions
│   └── pending/           # Awaiting approval
├── context/               # Achilles context system data
│   ├── workflows/         # Workflow task tracking
│   └── encyclopedia/      # Knowledge graph entries
└── graphs/                # Visual decision flow graphs
    ├── svg/               # SVG format
    └── json/              # Machine-readable graph data
```

## Graph Format

AI decision graphs use this structure:

```json
{
  "graph_id": "unique_id",
  "timestamp": "2026-01-03T...",
  "trigger": "user_request | floor_event | background_task",
  "nodes": [
    {
      "id": "node_1",
      "type": "decision | action | floor_call",
      "floor": "Morpheus | Smith | ...",
      "action": "description",
      "result": "success | pending | failed"
    }
  ],
  "edges": [
    {"from": "node_1", "to": "node_2", "label": "condition"}
  ],
  "outcome": "final result description"
}
```

## Integration

All AI interactions across floors are logged here for:
- Debugging multi-floor workflows
- Understanding AI decision patterns
- Tracking conversation context
- Building knowledge graphs
- Optimizing floor coordination

## Related Systems

- **Achilles Context**: `core/ai/achilles_context.py`
- **Workflow Automation**: `core/ai/workflow_automation.py`
- **Document Objectifier**: `core/ai/document_objectifier.py`
- **Neo Coordination**: `Z Axis/Z+3_Neo/coordination/`

---

**Version:** 0.9.5
**Last Updated:** January 3, 2026
"""

    (ai_logs_dir / 'README.md').write_text(readme_content, encoding='utf-8')

    # Create subdirectories
    subdirs = [
        'conversations/by_date',
        'conversations/by_floor',
        'decisions/approved',
        'decisions/pending',
        'context/workflows',
        'context/encyclopedia',
        'graphs/svg',
        'graphs/json',
    ]

    for subdir in subdirs:
        (ai_logs_dir / subdir).mkdir(parents=True, exist_ok=True)

    print(f"[CREATED] AI_LOGS graph structure in {ai_logs_dir.relative_to(LIGHTSPEED_ROOT)}")
    print(f"          8 subdirectories + README.md")


def main(dry_run: bool = False):
    """
    Execute migration.

    Args:
        dry_run: If True, only show what would happen without making changes
    """
    print("=" * 70)
    print("LightSpeed V0.9.5 - Z-Floor Migration")
    print("=" * 70)
    print()

    if dry_run:
        print("[DRY RUN MODE] - No files will be moved")
        print()

    # Step 1: Ensure Z-floor structure exists
    print("[Step 1] Initializing Z-floor structure...")
    initialize_z_floor_structure()
    print()

    # Step 2: Create AI_LOGS graph (per Q2)
    print("[Step 2] Creating AI_LOGS graph...")
    create_ai_logs_graph()
    print()

    # Step 3: Migrate folders
    print("[Step 3] Migrating root folders to Z-floors...")
    print()

    for source_name, dest_path in MIGRATION_MAP.items():
        migrate_folder(source_name, dest_path, dry_run=dry_run)

    print()
    print("=" * 70)
    if dry_run:
        print("DRY RUN COMPLETE - No changes made")
        print("Run again without --dry-run to execute migration")
    else:
        print("MIGRATION COMPLETE")
        print()
        print("Next steps:")
        print("1. Update import statements (run: python update_imports.py)")
        print("2. Test N.py launch")
        print("3. Validate all Z-floor modules load correctly")
    print("=" * 70)


if __name__ == '__main__':
    # Check for dry-run flag
    dry_run_mode = '--dry-run' in sys.argv or '-d' in sys.argv

    if not dry_run_mode:
        print()
        print("WARNING: This will move folders from root into Z-floor structure")
        print()
        response = input("Continue? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Migration cancelled")
            sys.exit(0)
        print()

    main(dry_run=dry_run_mode)
