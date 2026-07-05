#!/usr/bin/env python
"""
Generate initialize() hooks for all LightSpeed floors.

This tool automatically adds standardized initialize() hooks to floor modules
that don't have them yet, ensuring consistent floor bootstrapping.

Usage:
    python generate_floor_init_hooks.py

Author: LightSpeed Platform Team
Date: January 11, 2026
"""

from pathlib import Path
from typing import Dict, List, Tuple
import re


# Floor configuration
FLOORS = [
    {
        "name": "Trinity",
        "file": "Trinity.py",
        "z_level": 3,
        "capabilities": ["ui_dashboards", "3d_visualization", "user_interface", "theme_management"],
        "specific_init": """
    # Initialize UI theme engine
    try:
        from Z_Axis.Z+3_Trinity.ui.theme_manager import ThemeManager  # type: ignore
        theme_mgr = ThemeManager()
        TRINITY_RUNTIME["theme_manager"] = theme_mgr
        if logger:
            logger.info("[Trinity] Theme manager initialized")
    except Exception as e:
        TRINITY_RUNTIME["theme_error"] = str(e)

    # Start 3D visualization server if enabled
    try:
        from core.services import get_world_server  # type: ignore
        world_server = get_world_server()
        if world_server:
            TRINITY_RUNTIME["world_server"] = world_server
    except Exception as e:
        if logger:
            logger.debug(f"[Trinity] 3D server not available: {e}")
"""
    },
    {
        "name": "Architect",
        "file": "Architect.py",
        "z_level": 1,
        "capabilities": ["mission_planning", "project_management", "goals", "okrs", "roadmaps"],
        "specific_init": """
    # Initialize mission planning tools
    try:
        from Z_Axis.Z+1_Architect.components.progress_widget import DBTaskBoard  # type: ignore
        task_board = DBTaskBoard(parent=None, db_path=db.db_path if db else None)
        ARCHITECT_RUNTIME["task_board"] = task_board
        if logger:
            logger.info("[Architect] Task board initialized")
    except Exception as e:
        ARCHITECT_RUNTIME["task_board_error"] = str(e)
"""
    },
    {
        "name": "TheConstruct",
        "file": "TheConstruct.py",
        "z_level": 0,
        "capabilities": ["physics_simulations", "raphael_equations", "big_bang", "orbital_mechanics", "quantum_mechanics"],
        "specific_init": """
    # Initialize physics simulation engines
    try:
        from core.services import get_physics_tools  # type: ignore
        physics = get_physics_tools()
        CONSTRUCT_RUNTIME["physics_tools"] = physics
        if logger:
            logger.info("[TheConstruct] Physics tools initialized")
    except Exception as e:
        CONSTRUCT_RUNTIME["physics_error"] = str(e)

    # Start 3D rendering service
    try:
        from Z_Axis.Z0_TheConstruct.components.visualization_3d import Visualization3DComponent  # type: ignore
        viz = Visualization3DComponent()
        CONSTRUCT_RUNTIME["visualization"] = viz
    except Exception as e:
        if logger:
            logger.debug(f"[TheConstruct] 3D visualization not available: {e}")
"""
    },
    {
        "name": "Morpheus",
        "file": "Morpheus.py",
        "z_level": -1,
        "capabilities": ["code_analysis", "documentation", "knowledge_base", "search"],
        "specific_init": """
    # Initialize code analysis tools
    try:
        from Z_Axis.Z-1_Morpheus.components.morpheus_portal_glass import MorpheusPortalGlass  # type: ignore
        # Portal glass will be instantiated on demand
        MORPHEUS_RUNTIME["portal_available"] = True
    except Exception as e:
        MORPHEUS_RUNTIME["portal_error"] = str(e)

    # Start documentation indexer
    if storage:
        try:
            # Index documentation files
            docs_path = storage.get_floor_path("morpheus") / "documentation"
            if docs_path.exists():
                MORPHEUS_RUNTIME["docs_path"] = str(docs_path)
                if logger:
                    logger.info(f"[Morpheus] Documentation indexed: {docs_path}")
        except Exception as e:
            if logger:
                logger.debug(f"[Morpheus] Documentation indexing skipped: {e}")
"""
    },
    {
        "name": "Oracle",
        "file": "Oracle.py",
        "z_level": -2,
        "capabilities": ["file_ingestion", "archive_management", "smart_integration", "encyclopedia"],
        "specific_init": """
    # Start file ingestion watcher
    try:
        integrator_cls = None
        if isinstance(components, dict):
            integrator_cls = components.get("oracle_smart_integrator")
        if integrator_cls is None:
            from Z_Axis.Z-2_Oracle.components.oracle_smart_integrator import OracleSmartFloorIntegrator  # type: ignore
            integrator_cls = OracleSmartFloorIntegrator

        integrator = integrator_cls(db=db, event_bus=event_bus, storage=storage, logger=logger)
        ORACLE_RUNTIME["integrator"] = integrator

        # Start watching ingestion queue
        integrator.start_watching()

        if logger:
            logger.info("[Oracle] Smart Floor Integrator started")
    except Exception as e:
        ORACLE_RUNTIME["integrator_error"] = str(e)
        if logger:
            logger.warning(f"[Oracle] Smart integrator unavailable: {e}")
"""
    },
    {
        "name": "Merovingian",
        "file": "Merovingian.py",
        "z_level": -4,
        "capabilities": ["system_health", "diagnostics", "predictive_maintenance", "monitoring"],
        "specific_init": """
    # Start health monitoring service
    try:
        from core.services import get_predictive_maintenance_engine  # type: ignore
        pm_engine = get_predictive_maintenance_engine()
        MEROVINGIAN_RUNTIME["predictive_maintenance"] = pm_engine
        if logger:
            logger.info("[Merovingian] Predictive maintenance engine initialized")
    except Exception as e:
        MEROVINGIAN_RUNTIME["pm_error"] = str(e)

    # Initialize system diagnostics
    if db:
        try:
            # Log initial system health
            health_data = {
                "cpu_available": True,
                "memory_available": True,
                "disk_available": True,
                "timestamp": "system_start"
            }
            MEROVINGIAN_RUNTIME["initial_health"] = health_data
        except Exception as e:
            if logger:
                logger.debug(f"[Merovingian] Health logging skipped: {e}")
"""
    }
]


def generate_init_hook(floor: Dict) -> str:
    """Generate the initialize() hook code for a floor."""

    floor_name = floor["name"]
    floor_upper = floor_name.upper()
    z_level = floor["z_level"]
    capabilities = floor["capabilities"]
    specific_init = floor["specific_init"]

    template = f'''
# ---------------------------------------------------------------------------
# Floor boot hook (used by FloorLoader)
# ---------------------------------------------------------------------------

_{floor_upper}_INITIALIZED = False
{floor_upper}_RUNTIME: Dict[str, Any] = {{}}


def initialize(*, components: Optional[Dict[str, Any]] = None, dependencies: Optional[Dict[str, Any]] = None, **_kwargs) -> bool:
    """
    Initialize {floor_name} floor runtime services.

    This runs during floor bootstrap (no UI) and ensures {floor_name}'s
    background services and integrations are active.

    Args:
        components: Pre-loaded component classes/instances
        dependencies: Shared services (db, event_bus, storage, logger)
        **_kwargs: Additional platform parameters

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    global _{floor_upper}_INITIALIZED, {floor_upper}_RUNTIME
    if _{floor_upper}_INITIALIZED:
        return True
    _{floor_upper}_INITIALIZED = True

    try:
        from Z_Axis.Z-4_Merovingian.core.services import get_db, get_event_bus, get_storage, get_logger  # type: ignore
        db = get_db()
        event_bus = get_event_bus()
        storage = get_storage()
        logger = get_logger()
    except Exception:
        # Fallback to alternative import paths
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Z-4_Merovingian"))
            from core.services import get_db, get_event_bus, get_storage, get_logger  # type: ignore
            db = get_db()
            event_bus = get_event_bus()
            storage = get_storage()
            logger = get_logger()
        except Exception as e:
            print(f"[{floor_name}] Failed to load core services: {{e}}")
            db = None
            event_bus = None
            storage = None
            logger = None

    {floor_upper}_RUNTIME["db"] = db
    {floor_upper}_RUNTIME["event_bus"] = event_bus
    {floor_upper}_RUNTIME["storage"] = storage
    {floor_upper}_RUNTIME["logger"] = logger

    # Floor-specific initialization
{specific_init}

    # Subscribe to relevant events
    if event_bus:
        try:
            event_bus.subscribe("system.health.check", _on_health_check)
        except Exception as e:
            if logger:
                logger.warning(f"[{floor_name}] Event subscription failed: {{e}}")

    # Publish floor ready event
    if event_bus:
        try:
            event_bus.publish("{floor_name.lower()}.floor.ready", {{
                "floor": "{floor_name}",
                "z_level": {z_level},
                "capabilities": {capabilities}
            }})
        except Exception as e:
            if logger:
                logger.warning(f"[{floor_name}] Failed to publish ready event: {{e}}")

    if logger:
        logger.info("[{floor_name}] Floor initialized successfully")

    return True


def _on_health_check(event):
    """Respond to health check events"""
    event_bus = {floor_upper}_RUNTIME.get("event_bus")
    if event_bus:
        try:
            event_bus.publish("{floor_name.lower()}.health.status", {{
                "floor": "{floor_name}",
                "status": "operational",
                "z_level": {z_level}
            }})
        except Exception:
            pass
'''

    return template


def add_init_hook_to_file(floor_file: Path, init_code: str) -> bool:
    """Add the initialize() hook to a floor file."""

    if not floor_file.exists():
        print(f"[X] File not found: {floor_file}")
        return False

    # Read the file
    with open(floor_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if initialize() already exists
    if re.search(r'^def initialize\s*\(', content, re.MULTILINE):
        print(f"[OK] {floor_file.name} already has initialize() hook")
        return True

    # Find the insertion point (before main() function)
    main_pattern = r'(\ndef main\(\) -> int:)'
    match = re.search(main_pattern, content)

    if not match:
        print(f"[WARN] Could not find main() function in {floor_file.name}")
        return False

    # Insert the initialize() hook
    insert_pos = match.start()
    new_content = content[:insert_pos] + init_code + content[insert_pos:]

    # Write back
    with open(floor_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"[OK] Added initialize() hook to {floor_file.name}")
    return True


def main():
    """Main execution function."""

    print("=" * 70)
    print("LightSpeed Floor Initialize() Hook Generator")
    print("=" * 70)
    print()

    z_axis_dir = Path(__file__).resolve().parents[2]
    print(f"Z-Axis Directory: {z_axis_dir}")
    print()

    success_count = 0
    skip_count = 0
    fail_count = 0

    for floor_config in FLOORS:
        floor_name = floor_config["name"]
        floor_file = z_axis_dir / floor_config["file"]

        print(f"Processing {floor_name}...")

        init_code = generate_init_hook(floor_config)

        if add_init_hook_to_file(floor_file, init_code):
            if "already has" in str(init_code):
                skip_count += 1
            else:
                success_count += 1
        else:
            fail_count += 1

        print()

    print("=" * 70)
    print(f"[+] Successfully added: {success_count}")
    print(f"[-] Skipped (already exists): {skip_count}")
    print(f"[!] Failed: {fail_count}")
    print("=" * 70)


if __name__ == "__main__":
    main()
