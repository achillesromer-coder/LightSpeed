"""
LightSpeed - Centralized Path Configuration
Single source of truth for all filesystem paths.

This eliminates hardcoded paths like './data/', './logs/' scattered throughout the codebase.
All modules should import from here to remain consistent after folder migrations.

Canonical Z-Floor Architecture (current platform runtime):
- Z+3 (Trinity): UI layer & immersive portal
- Z+2 (Neo): AI integration & Cognigrex
- Z+1 (Architect): planning, tools, design
- Z0 (TheConstruct): physics simulations, render engine
- Z-1 (Morpheus): knowledge & code analysis
- Z-2 (Oracle): archive, document/IP vault, smart ingestion
- Z-3 (Smith): background tasks, workflow automation
- Z-4 (Merovingian): diagnostics, telemetry, system health

Note: historical/legacy folder variants may still exist in `Z Axis/`.
This module prefers the canonical folders when present and falls back to legacy
folders to keep older tools importable.

Author: LightSpeed Team / ACHILLES
Version: 5.1.2
Date: April 9, 2026
"""

from __future__ import annotations

from pathlib import Path
import os
import sys

def _find_lightspeed_root(start: Path) -> Path:
    """
    Resolve the LightSpeed root directory robustly.

    Folder layout is actively being migrated into Z floors, so this must not
    rely on fixed `parents[N]` offsets.
    """
    start = start.resolve()
    for candidate in (start, *start.parents):
        try:
            if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
                return candidate
        except Exception:
            continue

    for path_str in sys.path:
        try:
            candidate = Path(path_str).resolve()
            if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
                return candidate
        except Exception:
            continue

    # Last resort: current working directory
    try:
        cwd = Path.cwd().resolve()
        if (cwd / "N.py").exists() and (cwd / "Z Axis").exists():
            return cwd
    except Exception:
        pass

    return start.parent


# Root directory (single source of truth)
LIGHTSPEED_ROOT = _find_lightspeed_root(Path(__file__))

# ============================================================================
# Z-FLOOR STRUCTURE
# ============================================================================

Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"

# ============================================================================
# WORKSPACES / DATA (Operations W1-W6)
# ============================================================================

# Local workspace roots (legacy web-first /operations/w1..w6 model).
WORKSPACES_ROOT = LIGHTSPEED_ROOT
W6_ROOT = WORKSPACES_ROOT / "w6"
W6_DATA_ROOT = W6_ROOT / "data"

# Legacy generated-state aliases. These are reassigned to floor-owned roots
# after canonical floor roots are resolved below.
GENERATED_DATA_ROOT = LIGHTSPEED_ROOT / "data" / "generated"
GENERATED_INGESTION_ROOT = GENERATED_DATA_ROOT / "ingestion"
GENERATED_RUNTIME_EXPORTS = GENERATED_DATA_ROOT / "runtime_exports"
GENERATED_PUBLISH = GENERATED_DATA_ROOT / "publish"
GENERATED_LOGS = GENERATED_DATA_ROOT / "logs"

def _pick_dir(*candidates: Path) -> Path:
    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate
        except Exception:
            continue
    return candidates[0]


# Canonical floor roots (prefer canonical, fall back to legacy variants)
TRINITY_ROOT = _pick_dir(Z_AXIS_ROOT / "Z+3_Trinity", Z_AXIS_ROOT / "Z-4_Trinity")
NEO_ROOT = _pick_dir(Z_AXIS_ROOT / "Z+2_Neo", Z_AXIS_ROOT / "Z+3_Neo")
ARCHITECT_ROOT = _pick_dir(Z_AXIS_ROOT / "Z+1_Architect", Z_AXIS_ROOT / "Z-1_Architect")
CONSTRUCT_ROOT = _pick_dir(Z_AXIS_ROOT / "Z0_TheConstruct")
MORPHEUS_ROOT = _pick_dir(Z_AXIS_ROOT / "Z-1_Morpheus", Z_AXIS_ROOT / "Z+2_Morpheus", Z_AXIS_ROOT / "Z+3_Morpheus")
ORACLE_ROOT = _pick_dir(Z_AXIS_ROOT / "Z-2_Oracle", Z_AXIS_ROOT / "Z-1_Oracle")
SMITH_ROOT = _pick_dir(Z_AXIS_ROOT / "Z-3_Smith", Z_AXIS_ROOT / "Z-2_Smith")
MEROVINGIAN_ROOT = _pick_dir(Z_AXIS_ROOT / "Z-4_Merovingian", Z_AXIS_ROOT / "Z-3_Merovingian")


# Z+2: Neo - Internal AI Agent
NEO_AGENT = NEO_ROOT / "agent"
NEO_CONTEXT = NEO_ROOT / "context"
NEO_COORDINATION = NEO_ROOT / "coordination"

# Morpheus - Encyclopedia, Library, Documentation
MORPHEUS_ENCYCLOPEDIA = MORPHEUS_ROOT / "encyclopedia"
MORPHEUS_LIBRARY = MORPHEUS_ROOT / "library"  # Empirical knowledge (true knowns)
MORPHEUS_DOCS = MORPHEUS_ROOT / "documentation"
MORPHEUS_KNOWLEDGE = MORPHEUS_ROOT / "knowledge"

# Architect - Planning, Tools, Design
ARCHITECT_TOOLS = ARCHITECT_ROOT / "tools_archive"
ARCHITECT_PLANNING = ARCHITECT_ROOT / "planning"
ARCHITECT_PROJECTS = ARCHITECT_ROOT / "projects"
ARCHITECT_CONFIG = ARCHITECT_ROOT / "config"
ARCHITECT_RUNTIME_CONFIG = ARCHITECT_CONFIG / "runtime"
ARCHITECT_AI_CONFIG = ARCHITECT_CONFIG / "ai_config.json"
ARCHITECT_INTERMEDIARY_TARGETS = ARCHITECT_RUNTIME_CONFIG / "intermediary_targets.json"

# TheConstruct - Physics, Simulations, Render Engine
CONSTRUCT_PHYSICS = CONSTRUCT_ROOT / "physics"
CONSTRUCT_SIMULATIONS = CONSTRUCT_ROOT / "simulations"
CONSTRUCT_RENDER = CONSTRUCT_ROOT / "render_engine"

# Oracle - Archive, Immersive Library
ORACLE_ARCHIVE = ORACLE_ROOT / "archive"
ORACLE_LIBRARY = ORACLE_ROOT / "library"  # Immersive visual library
ORACLE_CONFIG = ORACLE_ROOT / "config"
ORACLE_RUNTIME_CONFIG = ORACLE_CONFIG / "runtime"
ORACLE_RUNTIME_RESERVOIRS = ORACLE_RUNTIME_CONFIG / "runtime_reservoirs.json"
ORACLE_IMMERSIVE = _pick_dir(
    ORACLE_ROOT / "immersive_modules",
    ORACLE_ROOT / "legacy" / "Z-1_Oracle" / "immersive_modules",
)

# Smith - Background Tasks, Neo Integration, Smart Floor Management
SMITH_LOGS = SMITH_ROOT / "logs"
SMITH_TASKS = SMITH_ROOT / "tasks"
SMITH_NEO_INTEGRATION = SMITH_ROOT / "neo_integration"
SMITH_SMART_FLOOR = SMITH_ROOT / "smart_floor_management"

# Merovingian - Business Intelligence, Optimization, Profiles
MEROVINGIAN_DATA = MEROVINGIAN_ROOT / "data"
MEROVINGIAN_PROFILES = MEROVINGIAN_ROOT / "profiles"  # Non-empirical user data
MEROVINGIAN_OPTIMIZATION = MEROVINGIAN_ROOT / "optimization"
MEROVINGIAN_ANALYTICS = MEROVINGIAN_ROOT / "analytics"

# Canonical generated state is floor-owned. The root `data/generated` tree is a
# legacy compatibility shell only and must not be recreated by active services.
GENERATED_DATA_ROOT = MEROVINGIAN_DATA
GENERATED_INGESTION_ROOT = ORACLE_ROOT / "data" / "ingestion"
GENERATED_RUNTIME_EXPORTS = MEROVINGIAN_DATA / "runtime_exports"
GENERATED_PUBLISH = ARCHITECT_ROOT / "data" / "publish"
GENERATED_LOGS = MEROVINGIAN_DATA / "logs"

# Operations (web-first workspace mirrors)
#
# Canonical V1 direction: keep operational registries and workspace scaffolds floor-native,
# owned by Merovingian (governance + controlled external edges).
#
# Compatibility: older layouts placed `operations/` at the LightSpeed root. We only fall back
# to the root location if the canonical registry does not exist (e.g. during migration or if
# a partial move left an empty/locked placeholder folder at the root).
_ops_root_legacy = LIGHTSPEED_ROOT / "operations"
_ops_root_canonical = MEROVINGIAN_DATA / "operations"
_ops_registry_canonical = _ops_root_canonical / "registry" / "operations_registry.json"

OPERATIONS_ROOT = _ops_root_canonical if _ops_registry_canonical.exists() else _ops_root_legacy
OPERATIONS_REGISTRY_PATH = OPERATIONS_ROOT / "registry" / "operations_registry.json"

# Trinity - Settings, Portal Config, Themes, UI, Environment Rendering
TRINITY_SETTINGS = TRINITY_ROOT / "settings"
TRINITY_THEMES = TRINITY_ROOT / "themes"
TRINITY_PORTAL_CONFIG = TRINITY_ROOT / "portal_config"
TRINITY_UI_CONFIG = TRINITY_ROOT / "ui_config"
TRINITY_ENVIRONMENT = TRINITY_ROOT / "environment_rendering"
TRINITY_OUTPUT = TRINITY_ROOT / "output"

# ============================================================================
# LEGACY PATH MAPPINGS (for backward compatibility during migration)
# ============================================================================

# These map old hardcoded paths to new Z-floor locations
LEGACY_PATHS = {
    './data': MEROVINGIAN_DATA,
    './Data': MEROVINGIAN_DATA,
    'data/': MEROVINGIAN_DATA,

    './docs': MORPHEUS_DOCS,
    './docs/': MORPHEUS_DOCS,
    'docs/': MORPHEUS_DOCS,

    './immersive_modules': ORACLE_IMMERSIVE,
    'immersive_modules/': ORACLE_IMMERSIVE,

    './knowledge': MORPHEUS_KNOWLEDGE,
    'knowledge/': MORPHEUS_KNOWLEDGE,

    './Library': MORPHEUS_LIBRARY,
    './library': MORPHEUS_LIBRARY,
    'Library/': MORPHEUS_LIBRARY,

    './logs': SMITH_LOGS,
    './logs/': SMITH_LOGS,
    'logs/': SMITH_LOGS,

    './Output': TRINITY_OUTPUT,
    './output': TRINITY_OUTPUT,
    'Output/': TRINITY_OUTPUT,

    './tools_archive': ARCHITECT_TOOLS,
    'tools_archive/': ARCHITECT_TOOLS,

    './ai_logs': NEO_AGENT / 'logs',
    'ai_logs/': NEO_AGENT / 'logs',
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def resolve_path(path_str: str) -> Path:
    """
    Resolve a path string, handling legacy paths.

    Args:
        path_str: Path string (can be legacy like './data' or new Z-floor path)

    Returns:
        Resolved Path object
    """
    # Check if it's a legacy path
    for legacy, new_path in LEGACY_PATHS.items():
        if path_str.startswith(legacy):
            # Replace legacy prefix with new path
            remainder = path_str[len(legacy):].lstrip('/')
            return new_path / remainder if remainder else new_path

    # Not a legacy path, resolve normally
    path = Path(path_str)
    if path.is_absolute():
        return path
    else:
        return LIGHTSPEED_ROOT / path


def ensure_path(path: Path) -> Path:
    """
    Ensure a path exists, creating directories if needed.

    Args:
        path: Path to ensure exists

    Returns:
        The path (for chaining)
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def migrate_legacy_path(old_path: str) -> Path:
    """
    Get the new Z-floor location for a legacy path.

    Args:
        old_path: Old path string (e.g., './data/')

    Returns:
        New Z-floor Path object
    """
    return LEGACY_PATHS.get(old_path, resolve_path(old_path))


# ============================================================================
# COMMON PATHS (frequently used across modules)
# ============================================================================

# Core package paths (physical location may move; keep these stable for callers)
CORE_ROOT = Path(__file__).resolve().parents[1]
CORE_CONFIG = CORE_ROOT / "config"
CORE_SERVICES = CORE_ROOT / "services"
CORE_UI = CORE_ROOT / "ui"
CORE_AI = CORE_ROOT / "ai"

# N.py main entry point
N_PY = LIGHTSPEED_ROOT / "N.py"

# Wizards
WIZARDS_ROOT = LIGHTSPEED_ROOT / "wizards"

# Project directories (stored in Architect floor)
PROJECTS_ROOT = ARCHITECT_PROJECTS
PROJECTS_TEST = ARCHITECT_ROOT / "projects_test"

# Virtual environments
VENV_ROOT = LIGHTSPEED_ROOT / ".venv"
VENV_ALT = LIGHTSPEED_ROOT / "venv"

# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_z_floor_structure():
    """
    Create all Z-floor directories if they don't exist.
    Called during first run or migration.
    """
    z_floor_paths = [
        # Neo (Z+3)
        NEO_ROOT, NEO_AGENT, NEO_CONTEXT, NEO_COORDINATION,

        # Morpheus (Z+2)
        MORPHEUS_ROOT, MORPHEUS_ENCYCLOPEDIA, MORPHEUS_LIBRARY,
        MORPHEUS_DOCS, MORPHEUS_KNOWLEDGE,

        # Architect (Z+1)
        ARCHITECT_ROOT, ARCHITECT_TOOLS, ARCHITECT_PLANNING, ARCHITECT_PROJECTS,
        ARCHITECT_CONFIG, ARCHITECT_RUNTIME_CONFIG,

        # TheConstruct (Z0)
        CONSTRUCT_ROOT, CONSTRUCT_PHYSICS, CONSTRUCT_SIMULATIONS, CONSTRUCT_RENDER,

        # Oracle (Z-1)
        ORACLE_ROOT, ORACLE_ARCHIVE, ORACLE_LIBRARY, ORACLE_CONFIG, ORACLE_RUNTIME_CONFIG, ORACLE_IMMERSIVE,

        # Smith (Z-2)
        SMITH_ROOT, SMITH_LOGS, SMITH_TASKS, SMITH_NEO_INTEGRATION, SMITH_SMART_FLOOR,

        # Merovingian (Z-3)
        MEROVINGIAN_ROOT, MEROVINGIAN_DATA, MEROVINGIAN_PROFILES,
        MEROVINGIAN_OPTIMIZATION, MEROVINGIAN_ANALYTICS,

        # Trinity (Z-4)
        TRINITY_ROOT, TRINITY_SETTINGS, TRINITY_THEMES, TRINITY_PORTAL_CONFIG,
        TRINITY_UI_CONFIG, TRINITY_ENVIRONMENT, TRINITY_OUTPUT,

        # Canonical generated state
        GENERATED_DATA_ROOT, GENERATED_INGESTION_ROOT, GENERATED_RUNTIME_EXPORTS,
        GENERATED_PUBLISH, GENERATED_LOGS,
    ]

    for path in z_floor_paths:
        ensure_path(path)

    # Also ensure the Z Direct inter-floor exchange scaffolds exist for each floor.
    try:
        initialize_z_direct_structure()
    except Exception:
        # Z Direct is non-critical for boot; failures should not block startup.
        pass

    print(f"[Paths] Z-floor structure initialized: {len(z_floor_paths)} directories")


def initialize_z_direct_structure() -> None:
    """
    Ensure each floor has durable registries and a manifest.

    Operational events and routed messages live in the shared Merovingian-owned
    SQLite store. Startup must not recreate legacy JSONL streams or empty
    channel/template files.
    """

    floors: list[tuple[Path, str, int, str]] = [
        (TRINITY_ROOT, "Trinity", 3, "Z+3_Trinity"),
        (NEO_ROOT, "Neo", 2, "Z+2_Neo"),
        (ARCHITECT_ROOT, "Architect", 1, "Z+1_Architect"),
        (CONSTRUCT_ROOT, "TheConstruct", 0, "Z0_TheConstruct"),
        (MORPHEUS_ROOT, "Morpheus", -1, "Z-1_Morpheus"),
        (ORACLE_ROOT, "Oracle", -2, "Z-2_Oracle"),
        (SMITH_ROOT, "Smith", -3, "Z-3_Smith"),
        (MEROVINGIAN_ROOT, "Merovingian", -4, "Z-4_Merovingian"),
    ]

    # Channels: N + all floors by Z-level (stable names, independent of folder naming quirks).
    #
    # V1 policy:
    # - Do NOT eagerly create per-channel subfolders (it generates a large amount of duplicated
    #   empty templates across floors and projects).
    # - Channels are declared in `floor_manifest.json` and are created on-demand by floor tooling.
    channels = ["N", "Z+3", "Z+2", "Z+1", "Z0", "Z-1", "Z-2", "Z-3", "Z-4"]

    root_files: list[tuple[str, str]] = [
        ("objects.json", "[]\n"),
        ("tasks.json", "[]\n"),
    ]
    legacy_empty_placeholders = (
        "objects.jsonl",
        "events.jsonl",
        "notes.md",
        "attachments.txt",
        "view.html",
    )

    for floor_root, floor_name, z_level, floor_code in floors:
        z_direct = floor_root / "Z Direct"
        ensure_path(z_direct)

        for rel_name in legacy_empty_placeholders:
            placeholder = z_direct / rel_name
            try:
                if placeholder.is_file() and placeholder.stat().st_size == 0:
                    placeholder.unlink()
            except OSError:
                pass

        # Root files (data sinks)
        for rel_name, content in root_files:
            fp = z_direct / rel_name
            if not fp.exists():
                try:
                    fp.write_text(content, encoding="utf-8")
                except Exception:
                    pass

        # Root README + manifest are templates with minimal useful content.
        readme = z_direct / "README.md"
        readme_content = (
            f"# {floor_code} - Z Direct\n\n"
            f"**Floor:** {floor_name}\n"
            f"**Z Level:** {z_level:+d}\n\n"
            "This folder is the floor-native inter-floor exchange area.\n\n"
            "## Files\n"
            "- `objects.json`: approved durable object registry\n"
            "- `tasks.json`: approved durable task registry\n"
            "- `floor_manifest.json`: floor and channel contract\n\n"
            "## Channels\n"
            "Operational events and directed routes are stored once in the\n"
            "Merovingian-owned SQLite operational authority.\n"
        )
        try:
            current = readme.read_text(encoding="utf-8") if readme.exists() else None
            if current != readme_content:
                readme.write_text(readme_content, encoding="utf-8")
        except OSError:
            pass

        floor_manifest = z_direct / "floor_manifest.json"
        if not floor_manifest.exists():
            try:
                manifest_path = (floor_root / "_FLOOR_MANIFEST.json")
                payload = {
                    "schema_version": "1.0",
                    "floor_code": floor_code,
                    "floor_name": floor_name,
                    "z_level": z_level,
                    "created_at": None,
                    "canonical_floor_manifest": str(manifest_path) if manifest_path.exists() else None,
                    "channels": channels,
                }
                import json

                floor_manifest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            except Exception:
                pass

        # Channel directory (created once) + template hint.
        channels_root = z_direct / "channels"
        ensure_path(channels_root)

        channels_readme = channels_root / "README.md"
        channels_readme_content = (
            "# Z Direct Channels\n\n"
            "This directory is retained for compatibility and reviewed attachments.\n\n"
            "Do not create inbox/outbox JSONL streams. Directed exchange is indexed\n"
            "once in the Merovingian-owned SQLite operational authority.\n\n"
            "Where `<CHANNEL>` is one of:\n"
            f"{', '.join(channels)}\n"
        )
        try:
            current = (
                channels_readme.read_text(encoding="utf-8")
                if channels_readme.exists()
                else None
            )
            if current != channels_readme_content:
                channels_readme.write_text(channels_readme_content, encoding="utf-8")
        except OSError:
            pass

        template_hint = channels_root / "_channel_template"
        if template_hint.is_dir():
            try:
                for rel_name in ("inbox.jsonl", "outbox.jsonl"):
                    placeholder = template_hint / rel_name
                    if placeholder.is_file() and placeholder.stat().st_size == 0:
                        placeholder.unlink()
                template_hint.rmdir()
            except OSError:
                pass


# Export all paths
__all__ = [
    # Root
    'LIGHTSPEED_ROOT',
    'Z_AXIS_ROOT',

    # Z-Floors
    'NEO_ROOT', 'NEO_AGENT', 'NEO_CONTEXT', 'NEO_COORDINATION',
    'MORPHEUS_ROOT', 'MORPHEUS_ENCYCLOPEDIA', 'MORPHEUS_LIBRARY', 'MORPHEUS_DOCS', 'MORPHEUS_KNOWLEDGE',
    'ARCHITECT_ROOT', 'ARCHITECT_TOOLS', 'ARCHITECT_PLANNING', 'ARCHITECT_PROJECTS',
    'ARCHITECT_CONFIG', 'ARCHITECT_RUNTIME_CONFIG', 'ARCHITECT_AI_CONFIG', 'ARCHITECT_INTERMEDIARY_TARGETS',
    'CONSTRUCT_ROOT', 'CONSTRUCT_PHYSICS', 'CONSTRUCT_SIMULATIONS', 'CONSTRUCT_RENDER',
    'ORACLE_ROOT', 'ORACLE_ARCHIVE', 'ORACLE_LIBRARY', 'ORACLE_CONFIG', 'ORACLE_RUNTIME_CONFIG',
    'ORACLE_RUNTIME_RESERVOIRS', 'ORACLE_IMMERSIVE',
    'SMITH_ROOT', 'SMITH_LOGS', 'SMITH_TASKS', 'SMITH_NEO_INTEGRATION', 'SMITH_SMART_FLOOR',
    'MEROVINGIAN_ROOT', 'MEROVINGIAN_DATA', 'MEROVINGIAN_PROFILES', 'MEROVINGIAN_OPTIMIZATION', 'MEROVINGIAN_ANALYTICS',
    'TRINITY_ROOT', 'TRINITY_SETTINGS', 'TRINITY_THEMES', 'TRINITY_PORTAL_CONFIG', 'TRINITY_UI_CONFIG', 'TRINITY_ENVIRONMENT', 'TRINITY_OUTPUT',

    # Core
    'CORE_ROOT', 'CORE_CONFIG', 'CORE_SERVICES', 'CORE_UI', 'CORE_AI',

    # Generated state
    'GENERATED_DATA_ROOT', 'GENERATED_INGESTION_ROOT', 'GENERATED_RUNTIME_EXPORTS', 'GENERATED_PUBLISH', 'GENERATED_LOGS',

    # Common
    'N_PY', 'WIZARDS_ROOT', 'PROJECTS_ROOT', 'PROJECTS_TEST', 'VENV_ROOT',

    # Utilities
    'resolve_path', 'ensure_path', 'migrate_legacy_path', 'initialize_z_floor_structure',

    # Legacy mappings
    'LEGACY_PATHS',
]
