#!/usr/bin/env python
# CODEX NOTE (2026-01-30):
# - This verifier prints the platform version from the repo `VERSION` file for consistency with `N.py` and `__main__.py`.
# - Tests are intended to be low risk; however a small subset intentionally writes **selftest** entries to Z Direct
#   (directed channel inbox + durable registry) to validate Trinity commit gating end-to-end.
"""
LightSpeed - Integration Verification Script
Automated testing of all integrated systems

Verifies:
- All 4 packages properly integrated
- Raphael physics operational
- Spherical UI system ready
- World Server functional
- ACHILLES AI configured
- Database initialized
- All imports working

Author: LightSpeed Team / ACHILLES
Version: dynamic (reads repo VERSION file when available)
"""

import sys
import os
from pathlib import Path
import json
import subprocess

# Add project root to path
# tools/ -> Z-3_Smith/ -> Z Axis/ -> LightSpeed/
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

# `core.*` lives under the Merovingian floor; add it explicitly so this verifier can
# import services/UI consistently when run from the repo root.
MEROVINGIAN_ROOT = PROJECT_ROOT / "Z Axis" / "Z-4_Merovingian"
if MEROVINGIAN_ROOT.exists():
    sys.path.insert(0, str(MEROVINGIAN_ROOT))

try:
    from core.config.paths import (  # type: ignore
        LIGHTSPEED_ROOT,
        MORPHEUS_LIBRARY,
        CONSTRUCT_ROOT,
        TRINITY_ROOT,
        MEROVINGIAN_DATA,
    )
except Exception:
    LIGHTSPEED_ROOT = PROJECT_ROOT
    MORPHEUS_LIBRARY = PROJECT_ROOT / "Z Axis" / "Z-1_Morpheus" / "library"
    CONSTRUCT_ROOT = PROJECT_ROOT / "Z Axis" / "Z0_TheConstruct"
    TRINITY_ROOT = PROJECT_ROOT / "Z Axis" / "Z+3_Trinity"
    MEROVINGIAN_DATA = PROJECT_ROOT / "Z Axis" / "Z-4_Merovingian" / "data"

# `ui.*` lives under Trinity; add it explicitly so we can validate Bento/UI integrations.
try:
    if isinstance(TRINITY_ROOT, Path) and TRINITY_ROOT.exists():
        sys.path.insert(0, str(TRINITY_ROOT))
except Exception:
    pass

# Test results
tests_passed = 0
tests_failed = 0
test_results = []

# Cross-test state (kept small; used for end-to-end approval loop tests).
LAST_ORACLE_VAULT_ID = None
LAST_ORACLE_TRINITY_INBOX_ENV = None


def test(name: str, func):
    """Run a test and track results."""
    global tests_passed, tests_failed
    try:
        result = func()
        tests_passed += 1
        test_results.append(("PASS", name, result))
        print(f"[PASS] {name}: {result}")
        return True
    except Exception as e:
        tests_failed += 1
        test_results.append(("FAIL", name, str(e)))
        print(f"[FAIL] {name}: {e}")
        return False


def _read_version() -> str:
    try:
        v = (Path(LIGHTSPEED_ROOT) / "VERSION").read_text(encoding="utf-8", errors="replace").strip()
        return v if v else "unknown"
    except Exception:
        return "unknown"


LS_VERSION = _read_version()

print("=" * 80)
print(f"LightSpeed Unified Orchestrator v{LS_VERSION} - Integration Verification")
print("=" * 80)
print()

# Test 1: Library Package Integration
def verify_library():
    library_path = Path(MORPHEUS_LIBRARY)
    if not library_path.exists():
        raise FileNotFoundError(f"Morpheus library not found at {library_path}")

    items = list(library_path.iterdir())
    size_mb = sum(f.stat().st_size for f in library_path.rglob('*') if f.is_file()) / 1024 / 1024
    return f"Found {len(items)} top-level items, ~{size_mb:.0f}MB"

test("Library Package", verify_library)

# Test 2: GMAT Integration
def verify_gmat():
    gmat_path = Path(CONSTRUCT_ROOT) / "tools" / "GMAT"
    if not gmat_path.exists():
        raise FileNotFoundError(f"GMAT not found at {gmat_path}")

    items = list(gmat_path.iterdir())
    return f"Found {len(items)} items in GMAT directory"

test("GMAT Integration", verify_gmat)

# Test 3: Tabby Integration
def verify_tabby():
    # Tabby is treated as a third-party vendor tree. It may be present under the
    # active Trinity tools path OR archived under `Z Axis/archive/vendor/`.
    candidates = [
        Path(TRINITY_ROOT) / "tools" / "Tabby",
        Path(PROJECT_ROOT) / "Z Axis" / "archive" / "vendor" / "Tabby",
    ]
    tabby_path = next((p for p in candidates if p.exists()), None)
    if tabby_path is None:
        return "Not installed (optional vendor tool)"

    items = list(tabby_path.iterdir())
    return f"Found {len(items)} items in Tabby directory @ {tabby_path}"

test("Tabby Integration", verify_tabby)

# Test 4: Raphael Physics Integration
def verify_raphael():
    raphael_path = PROJECT_ROOT / "Z Axis" / "Z-4_Merovingian" / "core" / "physics_modules" / "raphael_equations.py"
    if not raphael_path.exists():
        raise FileNotFoundError(f"Raphael equations not found at {raphael_path}")
    return "Raphael equations module present"

test("Raphael Physics Files", verify_raphael)

# Test 5: Raphael Physics Import
def verify_raphael_import():
    from core.physics.raphael import get_raphael_engine, RaphaelPhysicsEngine
    engine = get_raphael_engine()

    if not isinstance(engine, RaphaelPhysicsEngine):
        raise TypeError(f"Expected RaphaelPhysicsEngine, got {type(engine)}")

    return "Engine initialized successfully"

test("Raphael Physics Import", verify_raphael_import)

# Test 6: Spherical UI Import
def verify_spherical_ui():
    from core.ui.spherical_ui import EquirectangularUI, Widget3D
    from core.ui.floor_ui_wrapper import FloorUIWrapper, FloorUIFactory, create_floor_ui

    configs = FloorUIFactory.FLOOR_CONFIGS
    return f"{len(configs)} floor configurations ready"

test("Spherical UI Import", verify_spherical_ui)

# Test 7: World Server Import
def verify_world_server():
    from core.services.world_server import WorldServer, get_world_server

    server = get_world_server()
    if not isinstance(server, WorldServer):
        raise TypeError(f"Expected WorldServer, got {type(server)}")

    return f"{len(server.floors)} floors registered"

test("World Server Import", verify_world_server)

# Test 8: Smart Theming Import
def verify_smart_theme():
    from core.ui.smart_theme import SmartThemeExtractor, get_smart_theme_extractor

    extractor = get_smart_theme_extractor()
    if not isinstance(extractor, SmartThemeExtractor):
        raise TypeError(f"Expected SmartThemeExtractor, got {type(extractor)}")

    return f"Glassy effects enabled (opacity: {extractor.default_opacity})"

test("Smart Theming Import", verify_smart_theme)

# Test 9: Widget Registry Import
def verify_widget_registry():
    from core.ui.widget_registry import get_widget_registry

    registry = get_widget_registry()
    widgets = registry.get_all_widgets()
    categories = registry.get_all_categories()

    return f"{len(widgets)} widgets in {len(categories)} categories"

test("Widget Registry Import", verify_widget_registry)

# Test 9b: N UI Contracts (UI-first host + Bento overlay)
def verify_n_ui_contracts():
    n_path = PROJECT_ROOT / "N.py"
    if not n_path.exists():
        raise FileNotFoundError(f"N.py not found at {n_path}")

    src = n_path.read_text(encoding="utf-8-sig", errors="replace")
    required = [
        "def show_immersive_world(self, interactive: bool = False):",
        "show_immersive_world(interactive=True)",
        "cognigrex_3d_environment.py",
        "create_2d_frame",
        "_lightspeed_dim",
        "interface_mode = 'portal'",
        "def open_command_palette(",
        "<Control-k>",
        # Host action hooks for the command palette / menu management.
        "def toggle_bento_panel(self) -> None:",
        "def bento_clear_recents(self) -> bool:",
        "def bento_clear_favorites(self) -> bool:",
        "def open_oracle_registry(self):",
        # Data-defined bento widgets can invoke host actions without new code.
        "host_action_args",
    ]
    missing = [r for r in required if r not in src]
    if missing:
        raise AssertionError(f"Missing UI contract markers: {', '.join(missing)}")

    return "UI-first host + embedded Bento overlay markers present"

test("N UI Contracts", verify_n_ui_contracts)

# Test 9d: Bento + Menu contracts (scope/density + persistence helpers + overlay hotkeys)
def verify_bento_menu_contracts():
    bento_path = PROJECT_ROOT / "Z Axis" / "Z+3_Trinity" / "ui" / "universal_bento_system.py"
    if not bento_path.exists():
        raise FileNotFoundError(f"Universal Bento system not found: {bento_path}")
    src = bento_path.read_text(encoding="utf-8-sig", errors="replace")
    required = [
        "bento.scope",
        "bento.density",
        "def clear_recent_widgets",
        "def clear_favorite_widgets",
        "oracle_z_direct",
        "_load_committed_bento_widget_definitions",
    ]
    missing = [r for r in required if r not in src]
    if missing:
        raise AssertionError(f"Missing Bento/menu markers: {', '.join(missing)}")

    engine_path = PROJECT_ROOT / "Z Axis" / "Z0_TheConstruct" / "ui" / "immersive_3d_engine.py"
    if engine_path.exists():
        esrc = engine_path.read_text(encoding="utf-8-sig", errors="replace")
        # Hotkeys + banner are part of the readability/interactability contract.
        for marker in ("Tab", "1-4", "V", "MENU", "Scope:"):
            if marker not in esrc:
                raise AssertionError(f"Missing curved-overlay menu marker: {marker}")

    return "Scope/density + persistence helpers + curved overlay hotkeys present"

test("Bento Menu Contracts", verify_bento_menu_contracts)

# Test 9e: Oracle durable registry schema support (read-only interactability surface)
def verify_oracle_registry_schema_support():
    panel_path = PROJECT_ROOT / "Z Axis" / "Z-2_Oracle" / "components" / "oracle_ui_panel.py"
    if not panel_path.exists():
        raise FileNotFoundError(panel_path)
    src = panel_path.read_text(encoding="utf-8-sig", errors="replace")
    required = [
        "schema",
        "def open_panel(self, initial_tab",
        "def select_tab",
        "if k == \"schema\":",
        "Copied schema JSON to clipboard",
    ]
    missing = [r for r in required if r not in src]
    if missing:
        raise AssertionError(f"Oracle registry schema markers missing: {', '.join(missing)}")
    return "Oracle registry supports schemas + deep-link selection"

test("Oracle Registry Schema Support", verify_oracle_registry_schema_support)

# Test 9f: IT Portal commit preview gate (diff + envelope preview)
def verify_it_portal_commit_preview_contract():
    path = PROJECT_ROOT / "Z Axis" / "Z+3_Trinity" / "ui" / "it_portal.py"
    if not path.exists():
        raise FileNotFoundError(path)
    src = path.read_text(encoding="utf-8-sig", errors="replace")
    required = [
        "_confirm_commit_with_preview",
        "difflib.unified_diff",
        "Commit Preview",
        "Diff vs committed",
    ]
    missing = [r for r in required if r not in src]
    if missing:
        raise AssertionError(f"IT Portal commit preview markers missing: {', '.join(missing)}")
    return "Commit preview + diff gate present"

test("IT Portal Commit Preview", verify_it_portal_commit_preview_contract)

# Test 9c: Context Menu Wiring (static contract checks)
def verify_context_menu_wiring():
    checks = [
        (PROJECT_ROOT / "Z Axis" / "Z+3_Trinity" / "wizards" / "unified_search_system.py", "_on_result_right_click"),
        (PROJECT_ROOT / "Z Axis" / "Z+3_Trinity" / "ui" / "it_portal.py", "UniversalFileContextMenu"),
        (PROJECT_ROOT / "Z Axis" / "Z-2_Oracle" / "components" / "oracle_ui_panel.py", "_on_registry_right_click"),
        (PROJECT_ROOT / "Z Axis" / "Z-2_Oracle" / "immersive_modules" / "immersive_modules" / "project_tree.py", "<Button-3>"),
        (PROJECT_ROOT / "Z Axis" / "Z-2_Oracle" / "immersive_modules" / "immersive_modules" / "document_viewer.py", "<Button-3>"),
    ]
    missing = []
    for path, marker in checks:
        if not path.exists():
            missing.append(f"missing:{path}")
            continue
        src = path.read_text(encoding="utf-8-sig", errors="replace")
        if marker not in src:
            missing.append(f"{path.name}:{marker}")
    if missing:
        raise AssertionError("Context menu wiring missing markers: " + "; ".join(missing))
    return "Unified Search + IT Portal + Oracle registry + immersive viewers have right-click wiring"

test("Context Menu Wiring", verify_context_menu_wiring)

# Test 10: ACHILLES AI Configuration
def verify_achilles_config():
    config_path = PROJECT_ROOT / "config" / "ai_config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"AI config not found at {config_path}")

    with open(config_path, 'r') as f:
        config = json.load(f)

    ollama_enabled = bool(config.get("ollama", {}).get("enabled", False))
    achilles_enabled = bool(config.get("achilles", {}).get("enabled", False))

    if not (ollama_enabled or achilles_enabled):
        raise ValueError("No AI backend enabled (enable 'ollama' and/or 'achilles')")

    mode_keys = list((config.get("modes") or {}).keys())
    return f"Enabled backends: ollama={ollama_enabled}, achilles={achilles_enabled} | modes={mode_keys}"

test("ACHILLES AI Config", verify_achilles_config)

# Test 11: Triangle Renderer with Raphael
def verify_triangle_renderer():
    from core.rendering.triangle_renderer import TriangleRenderer

    # Check if HAS_RAPHAEL is available
    import core.rendering.triangle_renderer as tr_module
    has_raphael = getattr(tr_module, 'HAS_RAPHAEL', False)

    return f"Raphael integration: {'Available' if has_raphael else 'Not available'}"

test("Triangle Renderer", verify_triangle_renderer)

# Test 12: Database Path
def verify_database():
    db_path = Path(MEROVINGIAN_DATA) / "db" / "lightspeed_unified.db"

    if db_path.exists():
        size_kb = db_path.stat().st_size / 1024
        return f"Database exists ({size_kb:.1f}KB) @ {db_path}"
    else:
        return f"Database not initialized (expected at {db_path})"

test("Database Path", verify_database)

# Test 13: Core UI Exports
def verify_core_ui_exports():
    from core.ui import (
        EquirectangularUI,
        Widget3D,
        FloorUIWrapper,
        FloorUIFactory,
        create_floor_ui,
        SmartThemeExtractor,
        get_smart_theme_extractor,
        create_theme_from_image
    )

    return "All V1.0.0 exports available"

test("Core UI Exports", verify_core_ui_exports)

# Test 14: Floor Manifests
def verify_floor_manifests():
    floor_ids = ["Z-4", "Z-3", "Z-2", "Z-1", "Z+0", "Z+1", "Z+2", "Z+3"]
    floor_dirs = {
        "Z-4": "Z-4_Merovingian",
        "Z-3": "Z-3_Smith",
        "Z-2": "Z-2_Oracle",
        "Z-1": "Z-1_Morpheus",
        "Z+0": "Z0_TheConstruct",
        "Z+1": "Z+1_Architect",
        "Z+2": "Z+2_Neo",
        "Z+3": "Z+3_Trinity"
    }

    found_manifests = 0
    for floor_id, floor_dir in floor_dirs.items():
        manifest_path = PROJECT_ROOT / "Z Axis" / floor_dir / "_FLOOR_MANIFEST.json"
        if manifest_path.exists():
            found_manifests += 1

    return f"{found_manifests}/8 floor manifests found"

test("Floor Manifests", verify_floor_manifests)

# Test 14B: Module version is quiet (no eager imports / banners)
def verify_module_version_quiet():
    # `python -m LightSpeed` requires running from the parent of the repo root.
    cmd = [sys.executable, "-m", "LightSpeed", "--version"]
    cp = subprocess.run(
        cmd,
        cwd=str(Path(PROJECT_ROOT).parent),
        capture_output=True,
        text=True,
    )
    if cp.returncode != 0:
        raise RuntimeError(f"Non-zero exit ({cp.returncode}): {cp.stderr.strip()}")
    out = (cp.stdout or "").strip()
    if "LightSpeed Unified Launcher v" not in out:
        raise AssertionError(f"Unexpected output: {out[:200]}")
    # Guard against regressions where `__main__.py` eagerly imports heavy modules.
    noisy_markers = ["Registered template:", "LIGHTSPEED PLATFORM", "Z-AXIS ARCHITECTURE:"]
    if any(m in out for m in noisy_markers):
        raise AssertionError(f"Output not quiet (contains markers): {out[:200]}")
    return out.splitlines()[0]

test("Module Version Quiet", verify_module_version_quiet)

# Test 15: Documentation Files
def verify_documentation():
    docs = [
        "README.md",
        "Z Axis/Z-1_Morpheus/documentation/QUICK_START.md",
        "Z Axis/Z-1_Morpheus/documentation/QUICK_REFERENCE.md",
        "Z Axis/Z-1_Morpheus/documentation/INDEX.md",
        "Z Axis/Z-1_Morpheus/documentation/ACHILLES_CODEX.md",
    ]

    found = sum(1 for doc in docs if (PROJECT_ROOT / doc).exists())
    return f"{found}/{len(docs)} documentation files present"

test("Documentation Files", verify_documentation)

# Test 16: Initialization Scripts
def verify_init_scripts():
    scripts = [
        "Z Axis/Z+3_Trinity/wizards/cognigrex_setup_wizard.py",
        "Z Axis/Z+3_Trinity/components/cognigrex_login.py",
        "LAUNCH_GUI.bat"
    ]

    found = sum(1 for script in scripts if (PROJECT_ROOT / script).exists())
    return f"{found}/{len(scripts)} initialization scripts present"

test("Initialization Scripts", verify_init_scripts)

# Test 17: Wavefunction Calculation Test
def verify_wavefunction_calc():
    from core.physics.raphael import get_raphael_engine

    engine = get_raphael_engine()

    # Test wavefunction calculation
    result = engine.wavefunction.calculate_reflection(
        sphere1_center=(0, 0, 0),
        sphere1_radius=1.0,
        sphere2_center=(2, 0, 0),
        sphere2_radius=0.5,
        wavelength=550.0  # Green light
    )

    if result.reflection_coefficient < 0 or result.reflection_coefficient > 1:
        raise ValueError(f"Invalid reflection coefficient: {result.reflection_coefficient}")

    return f"Reflection coefficient: {result.reflection_coefficient:.3f}"

test("Wavefunction Calculation", verify_wavefunction_calc)

# Test 18: Light Reflectivity Test
def verify_light_reflectivity():
    from core.physics.raphael import get_raphael_engine

    engine = get_raphael_engine()

    # Test wavelength to RGB conversion
    rgb = engine.light.wavelength_to_rgb(550.0)  # Green

    if not all(0 <= c <= 255 for c in rgb):
        raise ValueError(f"Invalid RGB values: {rgb}")

    return f"550nm -> RGB{rgb}"

test("Light Reflectivity", verify_light_reflectivity)

# Test 19: Floor UI Factory Configs
def verify_floor_configs():
    from core.ui.floor_ui_wrapper import FloorUIFactory

    expected_floors = ["Z-4", "Z-3", "Z-2", "Z-1", "Z+0", "Z+1", "Z+2", "Z+3"]
    configs = FloorUIFactory.FLOOR_CONFIGS

    missing = [f for f in expected_floors if f not in configs]
    if missing:
        raise ValueError(f"Missing floor configs: {missing}")

    return f"All 8 floor configs present"

test("Floor UI Configs", verify_floor_configs)

# Test 20: World Server Port Allocation
def verify_port_allocation():
    from core.services.world_server import WorldServer

    expected_ports = {
        "Z-4": 8004,
        "Z-3": 8003,
        "Z-2": 8002,
        "Z-1": 8001,
        "Z+0": 8000,
        "Z+1": 8010,
        "Z+2": 8020,
        "Z+3": 8030,
    }

    actual_ports = WorldServer.FLOOR_PORTS

    if actual_ports != expected_ports:
        raise ValueError("Port allocation mismatch")

    return f"All 8 ports correctly allocated (8000-8030)"

test("World Server Ports", verify_port_allocation)

# Test 21: Z Direct (directed channels + durable registry commit gate)
def verify_z_direct():
    try:
        from core.services import get_z_direct  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Z Direct service import failed: {e}")

    zd = get_z_direct()

    # Ensure tail reads do not error (even if empty).
    _ = zd.tail_events("Z-3", limit=5)
    _ = zd.tail_objects("Z-3", limit=5)

    # Directed channel: write an event into Trinity inbox from Smith.
    env = zd.make_envelope(
        kind="event",
        channel="Z-3",
        z_context="Z-3_Smith",
        source="verify_integration",
        tags=["selftest", "z-direct"],
        payload={"action": "selftest_channel", "ok": True},
    )
    inbox_path = zd.append_channel_inbox(to_channel="Z+3", from_channel="Z-3", payload=env)
    # Peer discovery is used by Trinity's "Peer=All" inbox aggregation.
    peers = []
    try:
        if hasattr(zd, "list_channel_peers"):
            peers = zd.list_channel_peers("Z+3")
    except Exception:
        peers = []
    if peers and "Z-3" not in peers:
        raise RuntimeError(f"list_channel_peers(Z+3) missing Z-3 (got {peers})")

    # Commit gate: commit a staged object envelope into Trinity's durable registry.
    obj_env = zd.make_envelope(
        kind="object",
        channel="Z-3",
        z_context="Z-3_Smith",
        source="verify_integration",
        tags=["selftest", "z-direct"],
        payload={
            "kind": "selftest",
            "id": "verify_integration",
            "message": "Z Direct commit gate self-test",
        },
    )
    reg_path = zd.commit_envelope_to_registry(
        "Z+3",
        obj_env,
        registry="objects",
        committed_by={"username": "verify_integration.py", "clearance": 5},
    )

    # Also validate the `tasks.json` durable registry path (Trinity UI supports committing tasks).
    task_env = zd.make_envelope(
        kind="object",
        channel="Z-3",
        z_context="Z-3_Smith",
        source="verify_integration",
        tags=["selftest", "z-direct", "task"],
        payload={
            "kind": "task",
            "id": "verify_integration_task",
            "title": "Z Direct tasks registry self-test",
            "status": "pending",
        },
    )
    tasks_path = zd.commit_envelope_to_registry(
        "Z+3",
        task_env,
        registry="tasks",
        committed_by={"username": "verify_integration.py", "clearance": 5},
    )

    reg = zd.read_registry("Z+3", name="objects")
    if not isinstance(reg, list):
        raise RuntimeError("Registry did not normalize into a list")

    tasks_reg = zd.read_registry("Z+3", name="tasks")
    if not isinstance(tasks_reg, list):
        raise RuntimeError("Tasks registry did not normalize into a list")
    if not any(isinstance(it, dict) and it.get("kind") == "task" and it.get("id") == "verify_integration_task" for it in tasks_reg):
        raise RuntimeError("Tasks registry did not include verify_integration_task")

    peer_hint = f" | peers={len(peers)}" if peers else ""
    return f"Channel inbox: {inbox_path.name}{peer_hint} | objects={reg_path.name} ({len(reg)} items) | tasks={tasks_path.name} ({len(tasks_reg)} items)"

test("Z Direct (channels/registry)", verify_z_direct)

def verify_z_direct_builtin_schemas():
    from core.services import get_z_direct  # type: ignore

    zd = get_z_direct()
    if not hasattr(zd, "builtin_schema_payloads"):
        raise RuntimeError("Z Direct missing builtin_schema_payloads()")
    payloads = zd.builtin_schema_payloads()
    if not isinstance(payloads, list) or len(payloads) < 3:
        raise RuntimeError("Unexpected builtin schema payloads (expected list with >=3 items)")
    # Spot-check shape
    first = payloads[0] if payloads else None
    if not (isinstance(first, dict) and first.get("kind") == "schema" and first.get("id")):
        raise RuntimeError("Builtin schema payload shape invalid")
    ids = {str(p.get("id")) for p in payloads if isinstance(p, dict) and p.get("id")}
    for needed in ("simulation_result", "bento_widget", "action_def", "simulation_def", "workflow_def"):
        if needed not in ids:
            raise RuntimeError(f"Missing expected builtin schema: {needed}")
    return f"{len(payloads)} builtin schema payloads available"

test("Z Direct (builtin schemas)", verify_z_direct_builtin_schemas)

def verify_bento_loads_committed_bento_widgets():
    """
    End-to-end: commit a bento_widget definition then ensure UniversalBentoSystem loads it.

    This encodes the "extend UI via data, then wire via host_action" contract.
    """
    from core.services import get_z_direct  # type: ignore
    from ui.universal_bento_system import UniversalBentoSystem  # type: ignore

    zd = get_z_direct()
    committed_by = {"username": "verify_integration.py", "clearance": 5}

    payload = {
        "kind": "bento_widget",
        "id": "verify_bento_widget",
        "title": "Verify Bento Widget",
        "floor": "Z+3_Trinity",
        "widget_type": "BUTTON",
        "config": {"icon": "TEST", "host_action": "toggle_bento_panel", "host_action_args": {}},
        "enabled": True,
        "metadata": {"selftest": True},
    }

    env = zd.make_envelope(
        kind="object",
        channel="Z-3",
        z_context="Z-3_Smith",
        source="verify_integration",
        tags=["selftest", "bento_widget"],
        payload=payload,
    )
    zd.commit_envelope_to_registry("Z+3", env, registry="objects", committed_by=committed_by)

    b = UniversalBentoSystem()
    widgets = b.get_all_widgets() or []
    if not any(isinstance(w, object) and getattr(w, "id", None) == "verify_bento_widget" for w in widgets):
        raise RuntimeError("UniversalBentoSystem did not load committed bento_widget definition")

    # Cleanup: disable the test widget so it doesn't appear in normal operator menus.
    try:
        payload2 = dict(payload)
        payload2["enabled"] = False
        env2 = zd.make_envelope(
            kind="object",
            channel="Z-3",
            z_context="Z-3_Smith",
            source="verify_integration",
            tags=["selftest", "bento_widget", "cleanup"],
            payload=payload2,
        )
        zd.commit_envelope_to_registry("Z+3", env2, registry="objects", committed_by=committed_by)
    except Exception:
        pass

    return "Committed bento_widget loaded into UniversalBentoSystem"

test("Bento (load committed bento_widget)", verify_bento_loads_committed_bento_widgets)

def verify_z_direct_committed_schema_validation():
    from core.services import get_z_direct  # type: ignore

    zd = get_z_direct()
    schema_kind = "verify_integration_demo_kind"
    committed_by = {"username": "verify_integration.py", "clearance": 5}

    # Commit a custom schema into Trinity's durable registry.
    schema_env = zd.make_envelope(
        kind="object",
        channel="Z-3",
        z_context="Z-3_Smith",
        source="verify_integration",
        tags=["selftest", "schema"],
        payload={
            "kind": "schema",
            "id": schema_kind,
            "name": schema_kind,
            "json_schema": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": schema_kind,
                "type": "object",
                "additionalProperties": True,
                "required": ["kind", "id", "foo"],
                "properties": {"kind": {"type": "string"}, "id": {"type": "string"}, "foo": {"type": "string"}},
            },
        },
    )
    zd.commit_envelope_to_registry("Z+3", schema_env, registry="objects", committed_by=committed_by)

    # Validate that the commit gate enforces the committed schema.
    bad_env = zd.make_envelope(
        kind="object",
        channel="Z-3",
        z_context="Z-3_Smith",
        source="verify_integration",
        tags=["selftest", "schema-guard"],
        payload={"kind": schema_kind, "id": "demo1"},
    )
    failed = False
    try:
        zd.commit_envelope_to_registry("Z+3", bad_env, registry="objects", committed_by=committed_by)
    except Exception:
        failed = True
    if not failed:
        raise RuntimeError("Expected schema validation to reject missing required field foo")

    good_env = zd.make_envelope(
        kind="object",
        channel="Z-3",
        z_context="Z-3_Smith",
        source="verify_integration",
        tags=["selftest", "schema-guard"],
        payload={"kind": schema_kind, "id": "demo1", "foo": "bar"},
    )
    zd.commit_envelope_to_registry("Z+3", good_env, registry="objects", committed_by=committed_by)
    return f"Committed schema enforced required fields for kind={schema_kind}"

test("Z Direct (committed schema validation)", verify_z_direct_committed_schema_validation)


# Test 22: Directed review queue smoke (Architect -> Trinity inbox)
def verify_architect_directed_review_queue():
    import importlib.util
    from datetime import datetime, timezone

    try:
        from core.services import get_z_direct  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Z Direct service import failed: {e}")

    zd = get_z_direct()

    arch_path = PROJECT_ROOT / "Z Axis" / "Z+1_Architect" / "Architect.py"
    if not arch_path.exists():
        raise RuntimeError(f"Architect.py not found: {arch_path}")

    spec = importlib.util.spec_from_file_location("ls_floor_architect", str(arch_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to create module spec for Architect.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore

    started = datetime.now(timezone.utc)
    task_id = mod.create_task(  # type: ignore
        "verify_integration_directed_task",
        project_id=None,
        description="Directed review queue self-test",
        priority=0,
        status="pending",
    )

    # Verify the staged envelope is mirrored into Trinity's directed inbox (and sender outbox).
    inbox = zd.tail_channel_inbox(to_channel="Z+3", from_channel="Z+1", limit=200)
    outbox = zd.tail_channel_outbox(from_channel="Z+1", to_channel="Z+3", limit=200)

    def _matches(env: dict) -> bool:
        if not isinstance(env, dict):
            return False
        payload = env.get("payload") if isinstance(env.get("payload"), dict) else {}
        if payload.get("kind") != "task":
            return False
        env_id = payload.get("id")
        if str(env_id) != str(task_id):
            return False
        # Prefer confirming this is a fresh item.
        try:
            created_at = env.get("created_at")
            if isinstance(created_at, str) and created_at:
                ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if ts < started:
                    return False
        except Exception:
            pass
        return True

    if not any(_matches(e) for e in inbox or []):
        raise RuntimeError("Did not find Architect task envelope mirrored into Trinity inbox")
    if not any(_matches(e) for e in outbox or []):
        raise RuntimeError("Did not find Architect task envelope written to Z+1 outbox")

    return f"task:{task_id} mirrored (Z+1 -> Z+3)"


test("Architect -> Trinity (directed review queue)", verify_architect_directed_review_queue)


# Test 23: Directed review queue smoke (TheConstruct -> Trinity inbox)
def verify_construct_directed_review_queue():
    import importlib.util
    from datetime import datetime, timezone

    try:
        from core.services import get_z_direct  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Z Direct service import failed: {e}")

    zd = get_z_direct()

    c_path = PROJECT_ROOT / "Z Axis" / "Z0_TheConstruct" / "TheConstruct.py"
    if not c_path.exists():
        raise RuntimeError(f"TheConstruct.py not found: {c_path}")

    spec = importlib.util.spec_from_file_location("ls_floor_construct", str(c_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to create module spec for TheConstruct.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore

    # TheConstruct's entrypoint may not always have full core-service imports available
    # in isolation; inject Z Direct explicitly so staging/mirroring can still be exercised.
    try:
        mod.initialize(dependencies={"z_direct": zd}, enable_immersive=False)  # type: ignore
    except Exception:
        pass

    started = datetime.now(timezone.utc)
    _ = mod.run_simulation("raphael", protons=1, neutrons=1, electrons=1)  # type: ignore

    inbox = zd.tail_channel_inbox(to_channel="Z+3", from_channel="Z0", limit=200)
    outbox = zd.tail_channel_outbox(from_channel="Z0", to_channel="Z+3", limit=200)

    def _matches(env: dict) -> bool:
        if not isinstance(env, dict):
            return False
        payload = env.get("payload") if isinstance(env.get("payload"), dict) else {}
        if payload.get("kind") != "simulation_result":
            return False
        # Prefer confirming this is a fresh item.
        try:
            created_at = env.get("created_at")
            if isinstance(created_at, str) and created_at:
                ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if ts < started:
                    return False
        except Exception:
            pass
        return True

    if not any(_matches(e) for e in inbox or []):
        raise RuntimeError("Did not find Construct simulation_result mirrored into Trinity inbox")
    if not any(_matches(e) for e in outbox or []):
        raise RuntimeError("Did not find Construct simulation_result written to Z0 outbox")

    return "simulation_result mirrored (Z0 -> Z+3)"


test("TheConstruct -> Trinity (directed review queue)", verify_construct_directed_review_queue)


# Test 24: Template System (Romer palette defaults)
def verify_template_system():
    try:
        from core.services.template_system import get_template_registry  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Template system import failed: {e}")

    reg = get_template_registry()
    theme = reg.get_template("ThemeTemplate")
    if theme is None:
        raise RuntimeError("ThemeTemplate not registered")

    out = theme.render({"name": "verify_integration"})
    if not isinstance(out, dict):
        raise RuntimeError("ThemeTemplate.render did not return a dict")

    colors = out.get("colors") if isinstance(out, dict) else None
    if not isinstance(colors, dict):
        raise RuntimeError("ThemeTemplate colors missing")

    primary = colors.get("primary")
    if not isinstance(primary, str) or not primary.strip():
        raise RuntimeError("ThemeTemplate primary color missing")

    # Data templates we expect to exist for expansion workflows.
    for tname in (
        "VaultFileTemplate",
        "ResearchQueryTemplate",
        "DatasetTemplate",
        "ExperimentRunTemplate",
        "ProjectTemplate",
        "SimulationResultTemplate",
        "BentoWidgetDefinitionTemplate",
        "ZDirectSchemaTemplate",
        "ActionDefinitionTemplate",
        "SimulationDefinitionTemplate",
        "WorkflowDefinitionTemplate",
    ):
        tmpl = reg.get_template(tname)
        if tmpl is None:
            raise RuntimeError(f"{tname} not registered")
        defaults = tmpl.get_default_settings()
        if not isinstance(defaults, dict):
            raise RuntimeError(f"{tname}.get_default_settings did not return a dict")
        if not bool(getattr(tmpl, "validate", lambda _d: False)(defaults)):
            raise RuntimeError(f"{tname} defaults did not validate")

    return f"ThemeTemplate primary={primary} | data_templates=ok"

test("Template System (Romer defaults)", verify_template_system)

def verify_spec_form_available():
    """Spec-driven form renderer exists for typed menu controls (no placeholders)."""
    try:
        from core.ui.base_portal_glass import SpecForm  # type: ignore
    except Exception as e:
        raise RuntimeError(f"SpecForm import failed: {e}")
    if SpecForm is None:
        raise RuntimeError("SpecForm is None")
    return "SpecForm available"

test("SpecForm (typed param UI)", verify_spec_form_available)


# Test 25: Bento config load (grid geometry + span sizing)
def verify_bento():
    try:
        from ui.universal_bento_system import get_bento_system  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Bento system import failed: {e}")

    b = get_bento_system()
    cols = int(getattr(b, "grid_cols", 0) or 0)
    rows = int(getattr(b, "grid_rows", 0) or 0)
    radius = float(getattr(b, "radius", 0.0) or 0.0)
    if cols <= 0 or rows <= 0 or radius <= 0:
        raise RuntimeError(f"Invalid bento geometry cols={cols} rows={rows} radius={radius}")

    # Span sizing (a few core widgets declare spans in config)
    widgets = b.get_all_widgets()
    dash = next((w for w in widgets if getattr(w, "id", None) == "trinity_dashboard"), None)
    if dash is None:
        raise RuntimeError("Expected widget trinity_dashboard not found")

    layout = b.layout_for_widgets(widgets)
    pos = b.get_widget_position_3d_for(dash, 0, layout=layout)
    sc = int(pos.get("span_cols", 1) or 1)
    sr = int(pos.get("span_rows", 1) or 1)
    if sc < 2 or sr < 2:
        raise RuntimeError(f"Expected trinity_dashboard to be a multi-cell panel, got span={sc}x{sr}")

    width_m = float(pos.get("width_m", 0.0) or 0.0)
    height_m = float(pos.get("height_m", 0.0) or 0.0)
    base_w = float(getattr(b, "cell_width", 0.0) or 0.0)
    base_h = float(getattr(b, "cell_height", 0.0) or 0.0)
    if width_m < base_w * 2.0 or height_m < base_h * 2.0:
        raise RuntimeError("Span sizing did not scale 3D panel dimensions as expected")

    return f"grid={cols}x{rows} radius_m={radius:.2f} | dash_span={sc}x{sr} size_m={width_m:.2f}x{height_m:.2f}"

test("Bento System (config geometry)", verify_bento)


# Test 26: Bento per-user layout persistence (DB-backed user_preferences.widget_layout)
def verify_bento_user_persistence():
    try:
        import sqlite3
        import ui.universal_bento_system as ub  # type: ignore
        from ui.universal_bento_system import get_bento_system  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Bento system import failed: {e}")

    b = get_bento_system()
    setter = getattr(b, "set_user_context", None)
    if not callable(setter):
        raise RuntimeError("UniversalBentoSystem.set_user_context not available")

    user_id = "verify_bento_user"
    setter(user_id)

    widgets = b.get_all_widgets() or []
    if not widgets:
        raise RuntimeError("No Bento widgets registered")

    # Create a packed layout and persist it to the DB via user preferences.
    layout = b.layout_for_widgets(widgets, prefer_saved=False)
    sanitizer = getattr(b, "_sanitize_layout", None)
    if callable(sanitizer):
        layout = sanitizer(layout)

    ok_save = False
    try:
        ok_save = bool(getattr(b, "_persist_layout_to_user_preferences")(layout))
    except Exception:
        ok_save = False
    if not ok_save:
        raise RuntimeError("Failed to persist Bento layout to user_preferences")

    # Confirm DB row exists and widget_layout has content.
    db_path = PROJECT_ROOT / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db"
    if not db_path.exists():
        raise RuntimeError(f"DB not found at {db_path}")

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT widget_layout FROM user_preferences WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row or row[0] is None or len(str(row[0])) < 10:
        raise RuntimeError("user_preferences.widget_layout not written")

    # Force reload: clear singleton and re-load, then ensure saved_layout populated.
    ub._bento_system = None
    b2 = ub.get_bento_system()
    setter2 = getattr(b2, "set_user_context", None)
    if callable(setter2):
        setter2(user_id)
    loaded = getattr(b2, "saved_layout", None) or {}
    if not isinstance(loaded, dict) or len(loaded) < 5:
        raise RuntimeError("Reloaded Bento saved_layout is empty/unexpected")

    return f"rows={len(loaded)} db_bytes={len(str(row[0]))}"


test("Bento Persistence (per-user)", verify_bento_user_persistence)


# Test 24: Oracle staging to Z Direct (no durable auto-commit)
def verify_oracle_z_direct_staging():
    oracle_root = PROJECT_ROOT / "Z Axis" / "Z-2_Oracle"
    if not oracle_root.exists():
        raise FileNotFoundError(f"Oracle floor not found at {oracle_root}")

    # `components.*` lives under the Oracle floor.
    sys.path.insert(0, str(oracle_root))

    from components.oracle_smart_floor_integrator import OracleSmartFloorIntegrator  # type: ignore

    z_direct_dir = oracle_root / "Z Direct"
    objects_jsonl = z_direct_dir / "objects.jsonl"
    events_jsonl = z_direct_dir / "events.jsonl"
    objects_registry = z_direct_dir / "objects.json"
    oracle_outbox = z_direct_dir / "channels" / "Z+3" / "outbox.jsonl"

    trinity_root = PROJECT_ROOT / "Z Axis" / "Z+3_Trinity"
    trinity_inbox = trinity_root / "Z Direct" / "channels" / "Z-2" / "inbox.jsonl"

    before_obj = objects_jsonl.read_text(encoding="utf-8", errors="replace").count("\n") if objects_jsonl.exists() else 0
    before_ev = events_jsonl.read_text(encoding="utf-8", errors="replace").count("\n") if events_jsonl.exists() else 0
    before_reg = objects_registry.read_text(encoding="utf-8", errors="replace") if objects_registry.exists() else ""
    before_out = oracle_outbox.read_text(encoding="utf-8", errors="replace").count("\n") if oracle_outbox.exists() else 0
    before_in = trinity_inbox.read_text(encoding="utf-8", errors="replace").count("\n") if trinity_inbox.exists() else 0

    import tempfile
    import uuid

    temp_path = Path(tempfile.gettempdir()) / f"lightspeed_oracle_stage_{uuid.uuid4().hex}.txt"
    temp_path.write_text(f"oracle staging selftest {uuid.uuid4().hex}\n", encoding="utf-8")

    integrator = OracleSmartFloorIntegrator()
    res = integrator.ingest_file(str(temp_path), metadata={"source": "verify_integration.py"})
    if not isinstance(res, dict) or not res.get("success"):
        raise RuntimeError(f"Oracle ingest_file failed: {res}")

    after_obj = objects_jsonl.read_text(encoding="utf-8", errors="replace").count("\n") if objects_jsonl.exists() else 0
    after_ev = events_jsonl.read_text(encoding="utf-8", errors="replace").count("\n") if events_jsonl.exists() else 0
    after_reg = objects_registry.read_text(encoding="utf-8", errors="replace") if objects_registry.exists() else ""
    after_out = oracle_outbox.read_text(encoding="utf-8", errors="replace").count("\n") if oracle_outbox.exists() else 0
    after_in = trinity_inbox.read_text(encoding="utf-8", errors="replace").count("\n") if trinity_inbox.exists() else 0

    if after_obj <= before_obj:
        raise RuntimeError("Oracle did not append to Z Direct objects.jsonl (expected staging envelope)")
    if after_ev <= before_ev:
        raise RuntimeError("Oracle did not append to Z Direct events.jsonl (expected staging event)")
    if after_reg != before_reg:
        raise RuntimeError("Oracle modified durable Z Direct registry (objects.json); expected Trinity-gated commits only")
    if after_out <= before_out:
        raise RuntimeError("Oracle did not append directed outbox to Trinity (channels/Z+3/outbox.jsonl)")
    if after_in <= before_in:
        raise RuntimeError("Oracle did not append directed inbox line in Trinity (channels/Z-2/inbox.jsonl)")

    # Capture the latest Trinity inbox env for a follow-up end-to-end approval commit.
    global LAST_ORACLE_VAULT_ID, LAST_ORACLE_TRINITY_INBOX_ENV
    try:
        import time
        from core.services import get_z_direct  # type: ignore

        zd = get_z_direct()
        vault_id = res.get("vault_id")
        vault_id = str(vault_id) if vault_id is not None else ""

        picked = None
        for _attempt in range(6):
            inbox_tail = zd.tail_channel_inbox(to_channel="Z+3", from_channel="Z-2", limit=200)
            for env in reversed(inbox_tail or []):
                try:
                    payload = env.get("payload") if isinstance(env, dict) else None
                    if isinstance(payload, dict) and payload.get("kind") == "vault_file" and str(payload.get("id")) == vault_id:
                        picked = env
                        break
                except Exception:
                    continue
            if picked is not None:
                break
            time.sleep(0.1)

        if picked is None:
            raise RuntimeError("Failed to capture the matching Trinity inbox envelope for the ingested vault_file")

        LAST_ORACLE_VAULT_ID = vault_id
        LAST_ORACLE_TRINITY_INBOX_ENV = picked
    except Exception as e:
        raise RuntimeError(f"Oracle staging could not capture Trinity inbox env: {e}")

    return (
        f"staged +{after_obj - before_obj} objects, +{after_ev - before_ev} events | "
        f"directed +{after_out - before_out} outbox, +{after_in - before_in} inbox | "
        f"durable_registry_unchanged"
    )


test("Oracle Z Direct staging (no auto-commit)", verify_oracle_z_direct_staging)

# Test 25: Approval loop (Trinity inbox -> commit back to Oracle durable registry)
def verify_trinity_approval_oracle_commit():
    global LAST_ORACLE_VAULT_ID, LAST_ORACLE_TRINITY_INBOX_ENV
    if not LAST_ORACLE_TRINITY_INBOX_ENV:
        raise RuntimeError("Missing captured Trinity inbox env from Oracle staging test")

    try:
        from core.services import get_z_direct  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Z Direct service import failed: {e}")

    zd = get_z_direct()
    env = LAST_ORACLE_TRINITY_INBOX_ENV
    vault_id = str(LAST_ORACLE_VAULT_ID or "")

    zd.commit_envelope_to_registry(
        "Z-2",
        env,
        registry="objects",
        committed_by={"username": "verify_integration.py", "clearance": 5, "via": "approval_loop"},
    )

    reg = zd.read_registry("Z-2", name="objects")
    if not any(isinstance(it, dict) and it.get("kind") == "vault_file" and str(it.get("id")) == vault_id for it in (reg or [])):
        raise RuntimeError("Oracle durable registry did not include committed vault_file from Trinity inbox")

    return f"committed vault_file:{vault_id} into Z-2/objects.json"


test("Approval loop (Trinity inbox -> Oracle registry)", verify_trinity_approval_oracle_commit)

def verify_oracle_registry_supports_citation_and_knowledge_node():
    """
    End-to-end (governed) support for non-vault Oracle objects.

    We stage deterministic `citation` and `knowledge_node` envelopes into Trinity's directed inbox
    (as if from Neo), then commit them back into Oracle's durable registry. IDs are stable so the
    registry does not balloon across repeated verifier runs.
    """
    global LAST_ORACLE_VAULT_ID
    vault_id = str(LAST_ORACLE_VAULT_ID or "").strip()
    if not vault_id:
        raise RuntimeError("Missing LAST_ORACLE_VAULT_ID from Oracle approval test")

    try:
        from core.services import get_z_direct  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Z Direct service import failed: {e}")

    zd = get_z_direct()
    reg = zd.read_registry("Z-2", name="objects") or []
    vault = None
    for it in reg:
        if isinstance(it, dict) and it.get("kind") == "vault_file" and str(it.get("id") or "") == vault_id:
            vault = it
            break
    if not isinstance(vault, dict):
        raise RuntimeError("Could not resolve committed vault_file payload from Oracle registry")

    cit_id = "verify_integration_citation"
    kn_id = "verify_integration_knowledge_node"

    citation = {
        "kind": "citation",
        "id": cit_id,
        "vault_file_id": vault_id,
        "note": "Integration verifier citation (deterministic id)",
        "span": {"start": 0, "end": 1},
        "quote_hash": "",
        "metadata": {"proposed_by": "verify_integration.py", "romer_standard": True},
    }

    knowledge_node = {
        "kind": "knowledge_node",
        "id": kn_id,
        "concept": "Integration Verifier Concept",
        "definition": "Smoke-test knowledge_node commit into Oracle durable registry.",
        "domain": "GENERAL",
        "related_concepts": [],
        "sources": [
            {
                "vault_file_id": vault_id,
                "citation_id": cit_id,
                "sha256": vault.get("sha256"),
                "name": vault.get("source_name") or vault.get("name"),
                "path": vault.get("path"),
            }
        ],
        "confidence": 0.9,
        "metadata": {"proposed_by": "verify_integration.py", "romer_standard": True},
    }

    origin = "Z+2"
    review = "Z+3"
    target = "Z-2"

    cit_env = zd.make_envelope(
        kind="object",
        channel=target,
        z_context="Z+2_Neo",
        source="verify_integration.py",
        tags=["proposal", "citation", "cognigrex"],
        payload=citation,
    )
    kn_env = zd.make_envelope(
        kind="object",
        channel=target,
        z_context="Z+2_Neo",
        source="verify_integration.py",
        tags=["proposal", "knowledge", "cognigrex"],
        payload=knowledge_node,
    )

    # Stage into Trinity directed channels (observable governance surface).
    try:
        zd.append_channel_outbox(from_channel=origin, to_channel=review, payload=cit_env)
    except Exception:
        pass
    try:
        zd.append_channel_inbox(to_channel=review, from_channel=origin, payload=cit_env)
    except Exception:
        pass
    try:
        zd.append_channel_outbox(from_channel=origin, to_channel=review, payload=kn_env)
    except Exception:
        pass
    try:
        zd.append_channel_inbox(to_channel=review, from_channel=origin, payload=kn_env)
    except Exception:
        pass

    # Commit to Oracle durable registry (upsert; deterministic ids).
    committed_by = {"username": "verify_integration.py", "clearance": 5, "via": "approval_loop"}
    zd.commit_envelope_to_registry(target, cit_env, registry="objects", committed_by=committed_by)
    zd.commit_envelope_to_registry(target, kn_env, registry="objects", committed_by=committed_by)

    reg2 = zd.read_registry("Z-2", name="objects") or []
    if not any(isinstance(it, dict) and it.get("kind") == "citation" and str(it.get("id") or "") == cit_id for it in reg2):
        raise RuntimeError("Oracle registry did not include committed citation")
    if not any(isinstance(it, dict) and it.get("kind") == "knowledge_node" and str(it.get("id") or "") == kn_id for it in reg2):
        raise RuntimeError("Oracle registry did not include committed knowledge_node")

    return f"committed citation:{cit_id} + knowledge_node:{kn_id} into Z-2/objects.json"


test("Approval loop (Trinity inbox -> Oracle registry) [citation/knowledge]", verify_oracle_registry_supports_citation_and_knowledge_node)


# Test 26: Smith doc-marker -> task staging -> Trinity inbox -> commit back to Smith durable tasks registry
def verify_smith_task_approval_loop():
    import importlib.util
    import tempfile
    import uuid
    import time

    tool_path = PROJECT_ROOT / "Z Axis" / "Z-3_Smith" / "tools" / "scan_docs_to_tasks.py"
    if not tool_path.exists():
        raise FileNotFoundError(f"Smith scan tool not found at {tool_path}")

    spec = importlib.util.spec_from_file_location("lightspeed_dyn_scan_docs_to_tasks", tool_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load Smith scan tool module spec")
    mod = importlib.util.module_from_spec(spec)
    # Dataclasses/type evaluation expects the module to be registered.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    scan_docs_to_db = getattr(mod, "scan_docs_to_db", None)
    emit_summary = getattr(mod, "_emit_z_direct_summary", None)
    if not callable(scan_docs_to_db) or not callable(emit_summary):
        raise RuntimeError("Smith scan tool missing scan_docs_to_db/_emit_z_direct_summary")

    # Create a unique temp doc so markers always insert and a task is created.
    marker_id = uuid.uuid4().hex
    temp_doc = Path(tempfile.gettempdir()) / f"lightspeed_smith_task_{marker_id}.md"
    temp_doc.write_text(
        "\n".join(
            [
                f"# Smith selftest {marker_id}",
                "",
                f"TODO: verify_integration approval loop {marker_id}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Use the platform DB (Merovingian-owned).
    db_path = PROJECT_ROOT / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db"

    res = scan_docs_to_db(
        db_path=Path(db_path),
        scan_root=Path(temp_doc),
        include_exts=[".md"],
        exclude_dirs=["__pycache__", ".git"],
        create_tasks=True,
        backfill_company_ids=False,
    )
    if not getattr(res, "tasks_created", 0):
        raise RuntimeError("Expected Smith scan to create at least one task")
    created = list(getattr(res, "created_task_payloads", []) or [])
    if not created:
        raise RuntimeError("Expected Smith scan to stage created_task_payloads")

    # Publish to Z Direct (including Trinity directed inbox).
    emit_summary(Path(PROJECT_ROOT), scan_root=Path(temp_doc), res=res)

    try:
        from core.services import get_z_direct  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Z Direct service import failed: {e}")
    zd = get_z_direct()

    task_id = str((created[0] or {}).get("id") or "")
    if not task_id:
        raise RuntimeError("Missing created task id")

    # Directed inbox can be noisy (other floors may be staging in parallel); search a larger tail
    # and retry briefly to avoid flakes on slower disks.
    picked = None
    for _ in range(6):
        inbox_tail = zd.tail_channel_inbox(to_channel="Z+3", from_channel="Z-3", limit=2000)
        for env in reversed(inbox_tail or []):
            try:
                payload = env.get("payload") if isinstance(env, dict) else None
                if isinstance(payload, dict) and payload.get("kind") == "task" and str(payload.get("id")) == task_id:
                    picked = env
                    break
            except Exception:
                continue
        if picked is not None:
            break
        time.sleep(0.25)
    if picked is None:
        raise RuntimeError("Did not find staged Smith task in Trinity inbox")

    # Commit back into Smith's durable tasks registry.
    zd.commit_envelope_to_registry(
        "Z-3",
        picked,
        registry="tasks",
        committed_by={"username": "verify_integration.py", "clearance": 5, "via": "approval_loop"},
    )
    reg = zd.read_registry("Z-3", name="tasks")
    if not any(isinstance(it, dict) and it.get("kind") == "task" and str(it.get("id")) == task_id for it in (reg or [])):
        raise RuntimeError("Smith durable tasks registry did not include committed task from Trinity inbox")

    return f"task:{task_id} staged->Trinity->committed to Z-3/tasks.json"


test("Approval loop (Trinity inbox -> Smith tasks)", verify_smith_task_approval_loop)

# Summary
print()
print("=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)
print()
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Success Rate: {tests_passed / (tests_passed + tests_failed) * 100:.1f}%")
print()

if tests_failed == 0:
    print("[SUCCESS] ALL TESTS PASSED - Platform is fully operational!")
    print()
    print(f"LightSpeed Unified Orchestrator v{LS_VERSION} is ready for deployment.")
    print()
    print("Next steps:")
    print("1. Run: LAUNCH_GUI.bat  (Windows)")
    print("2. Or run: python N.py --gui")
    print("3. (Optional) Verify again: python \"Z Axis/Z-3_Smith/tools/verify_integration.py\"")
else:
    print("[WARNING] SOME TESTS FAILED - Review errors above")
    print()
    print("Failed tests:")
    for status, name, result in test_results:
        if status == "FAIL":
            print(f"  - {name}: {result}")

print()
print("=" * 80)

# Exit code
sys.exit(0 if tests_failed == 0 else 1)
