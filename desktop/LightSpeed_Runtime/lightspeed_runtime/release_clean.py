from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from lightspeed_runtime.storage_paths import (
    architect_floor_root,
    datatables_root,
    encyclopedia_root,
    library_root,
    merovingian_root,
    oracle_root,
    trinity_root,
)


DATABASE_TABLES_TO_CLEAR = [
    {"name": "time_entries", "category": "user_runtime", "reason": "Transient time tracking and session evidence."},
    {"name": "tasks", "category": "user_runtime", "reason": "Working task rows from in-progress runs."},
    {"name": "projects", "category": "user_runtime", "reason": "User/project runtime rows after publishing or reset."},
    {"name": "companies", "category": "user_runtime", "reason": "Runtime company rows from workspace setup."},
    {"name": "users", "category": "user_runtime", "reason": "User profile rows during blank-state reset."},
    {"name": "user_preferences", "category": "user_runtime", "reason": "Tailoring and local UI state."},
    {"name": "ai_interactions", "category": "runtime", "reason": "Assistant interaction traces for a clean publish state."},
    {"name": "chat_messages", "category": "runtime", "reason": "Conversation history generated during runs."},
    {"name": "chat_conversations", "category": "runtime", "reason": "Conversation shells and thread summaries."},
    {"name": "doc_task_markers", "category": "runtime", "reason": "Document-linked task markers from ingestion."},
    {"name": "oracle_ingestion_tasks", "category": "runtime", "reason": "Oracle ingestion queue rows from prior runs."},
    {"name": "interfloor_tasks", "category": "runtime", "reason": "Inter-floor handoff queue state."},
    {"name": "simulations", "category": "runtime", "reason": "Simulation rows from prior smoke or lab runs."},
]

LAUNCH_STATE_CLEANUP_KEYS = [
    {"key": "first_run_complete", "reason": "Blank release prep should reopen the startup wizard path."},
    {"key": "show_splash_screen", "reason": "Splash state should be re-evaluated during release prep."},
    {"key": "show_status_bar", "reason": "Status bar visibility is part of launch-state normalization."},
    {"key": "last_launched", "reason": "Last-launch timestamp is transient release evidence."},
]

SETUP_STATE_CLEANUP_KEYS = [
    {"key": "active_floors", "reason": "Floor activation is reshaped during setup-state resets."},
    {"key": "default_floor", "reason": "Default floor selection is part of guided setup."},
    {"key": "workspace_modes", "reason": "Workspace mode selection belongs in setup planning."},
    {"key": "top_level_navigation_modes", "reason": "Navigation modes are normalized before publish."},
    {"key": "z_floor_dropdown_enabled", "reason": "Z-floor dropdown availability is a setup-state control."},
    {"key": "page_settings_pattern", "reason": "Settings routing should be consolidated during setup cleanup."},
]

STALE_RUNTIME_ROW_TABLES = [
    table for table in DATABASE_TABLES_TO_CLEAR if table["name"] in {"projects", "companies", "users", "user_preferences"}
]

GENERATED_CACHE_TEMP_ROOTS = [
    ".pytest_cache",
    "__pycache__",
    "tests/__pycache__",
    "tools/__pycache__",
    "lightspeed_runtime/__pycache__",
    "lightspeed_runtime/achilles/__pycache__",
    "lightspeed_runtime/labs/__pycache__",
    "lightspeed_runtime/publishing/__pycache__",
    "lightspeed_runtime/reservoirs/__pycache__",
    "lightspeed_runtime/shell/__pycache__",
    "Z Axis/Z+3_Trinity/ui/__pycache__",
    "Z Axis/Z+3_Trinity/components/__pycache__",
    "Z Axis/Z+3_Trinity/diagnostics/__pycache__",
    "Z Axis/Z+3_Trinity/wizards/__pycache__",
    "Z Axis/Z-4_Merovingian/core/__pycache__",
    "Z Axis/Z-4_Merovingian/core/services/__pycache__",
    "Z Axis/Z-4_Merovingian/core/config/__pycache__",
    "Z Axis/Z-2_Oracle/tools/__pycache__",
    "Z Axis/Z-1_Morpheus/database/__pycache__",
    "Z Axis/Z-1_Morpheus/database/models/__pycache__",
    "temp",
    "tmp",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    "coverage",
]

DUPLICATE_SURFACE_AUDIT_DESCRIPTORS = [
    {"surface": "settings", "entrypoint": "Settings Hub", "status": "primary", "action": "retain", "reason": "Canonical settings entrypoint."},
    {"surface": "settings", "entrypoint": "Legacy Theme Manager", "status": "duplicate", "action": "cull_later", "reason": "Theme controls now route through Trinity settings."},
    {"surface": "wizard", "entrypoint": "Startup Wizard", "status": "primary", "action": "retain", "reason": "Launch/setup guidance remains canonical."},
    {"surface": "wizard", "entrypoint": "Legacy Setup Wizard", "status": "duplicate", "action": "cull_later", "reason": "Setup flows should converge on one guided surface."},
    {"surface": "popup", "entrypoint": "Floating Popup Panel", "status": "duplicate", "action": "cull_later", "reason": "Inline panels are preferred over heavy popups."},
    {"surface": "popup", "entrypoint": "Context Drawer", "status": "primary", "action": "retain", "reason": "Compact contextual drawers remain useful."},
]

POST_FINAL_PASS_RELOCATION_TARGETS = [
    {
        "id": "oracle_ai_logs",
        "source": "Z Axis/Z-2_Oracle/data/legacy/ai_logs",
        "destination": "AI Logs",
        "action": "move_to_outer_archive",
        "reason": "AI logs are useful build evidence, but they are not part of the blank packaged application.",
    },
    {
        "id": "launch_readiness_reports",
        "source": "Z Axis/Z-4_Merovingian/data/reports/launch_readiness",
        "destination": "Packaging Reports/launch_readiness",
        "action": "move_to_outer_archive",
        "reason": "Readiness reports should stay reviewable outside the packaged app after final proofing.",
    },
]

POST_FINAL_PASS_PACKAGE_EXCLUSIONS = [
    {
        "id": "test_caches",
        "patterns": [".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache"],
        "action": "delete_or_exclude",
        "reason": "Generated caches should never ship in the release package.",
    },
    {
        "id": "runtime_user_rows",
        "patterns": ["projects", "companies", "users", "user_preferences"],
        "action": "blank_state_reset",
        "reason": "Packaged release should open as a blank application without prior user/project data.",
    },
]


SMOKE_TEST_COMMANDS = [
    {
        "order": 1,
        "name": "Compile",
        "command": 'python -m py_compile "N.py" "lightspeed_runtime\\release_clean.py" "lightspeed_runtime\\project_component_wall.py" "Z Axis\\Z+3_Trinity\\ui\\smart_settings_hub.py"',
        "purpose": "Catch syntax errors before broader test execution.",
    },
    {
        "order": 2,
        "name": "Targeted Tests",
        "command": "python -m pytest tests\\test_release_clean.py -q",
        "purpose": "Validate release-clean guards and summaries in isolation.",
    },
    {
        "order": 3,
        "name": "Full Tests",
        "command": "python -m pytest tests -q",
        "purpose": "Verify the whole application after the cleanup pass.",
    },
    {
        "order": 4,
        "name": "Launch Readiness",
        "command": "python verify_launch_ready.py",
        "purpose": "Confirm entry points, floors, services, config, and AI logs.",
    },
    {
        "order": 5,
        "name": "Diagnostics",
        "command": (
            "python -c \"from pathlib import Path; import importlib.util; "
            "p=(Path.cwd() / 'Z Axis' / 'Z+3_Trinity' / 'diagnostics' / 'complete_diagnostic_system.py').resolve(); "
            "s=importlib.util.spec_from_file_location('diag', p); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
            "d=m.SystemDiagnostics(); r=d.run_all_diagnostics(); print(len(r))\""
        ),
        "purpose": "Run the diagnostic suite and inspect aggregate status.",
    },
    {
        "order": 6,
        "name": "Blank-State Verification",
        "command": 'python -c "import sqlite3; from pathlib import Path; root=Path.cwd(); db=root / \'Z Axis\' / \'Z-4_Merovingian\' / \'data\' / \'db\' / \'lightspeed_unified.db\'; conn=sqlite3.connect(db); cur=conn.cursor(); tables=[\'time_entries\',\'tasks\',\'projects\',\'companies\',\'users\',\'user_preferences\',\'ai_interactions\',\'chat_messages\',\'chat_conversations\',\'doc_task_markers\',\'oracle_ingestion_tasks\',\'interfloor_tasks\',\'simulations\']; print({t:(cur.execute(\'select count(*) from sqlite_master where type=\\\'table\\\' and name=?\', (t,)).fetchone()[0]) for t in tables}); conn.close()"',
        "purpose": "Confirm blank-state targets exist and can be cleared safely after a publish reset.",
    },
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_root(root: Path) -> Path:
    return Path(root).resolve()


def is_within_root(root: Path, candidate: Path) -> bool:
    root = normalize_root(root)
    candidate = Path(candidate).resolve()
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_within_root(root: Path, candidate: Path) -> Path:
    root = normalize_root(root)
    candidate = Path(candidate).resolve()
    if not is_within_root(root, candidate):
        raise ValueError(f"Path is outside LightSpeed root: {candidate}")
    return candidate


def project_workspace_root(root: Path) -> Path:
    return architect_floor_root(normalize_root(root)) / "projects"


def project_workspace_entries(root: Path) -> List[Path]:
    workspace = project_workspace_root(root)
    if not workspace.exists():
        return []
    entries = []
    for item in sorted(workspace.iterdir(), key=lambda path: path.name.lower()):
        if item.name == ".gitkeep":
            continue
        entries.append(item)
    return entries


def launch_setup_cleanup_plan(root: Path) -> Dict[str, Any]:
    root = normalize_root(root)
    return {
        "generated_at": utc_now_iso(),
        "root": str(root),
        "dry_run_only": True,
        "launch_state": {
            "scope": "blank_release_prep",
            "keys": list(LAUNCH_STATE_CLEANUP_KEYS),
            "summary": "Reset launch-facing state for a clean first-run and startup pass.",
        },
        "setup_state": {
            "scope": "guided_setup_prep",
            "keys": list(SETUP_STATE_CLEANUP_KEYS),
            "summary": "Normalize setup-facing state before a release or publish handoff.",
        },
    }


def stale_runtime_row_cleanup_plan(root: Path) -> Dict[str, Any]:
    root = normalize_root(root)
    return {
        "generated_at": utc_now_iso(),
        "root": str(root),
        "dry_run_only": True,
        "trigger": "after_proof_runs",
        "target_tables": list(STALE_RUNTIME_ROW_TABLES),
        "summary": "Plan for stale user, project, company, and preference runtime rows after proof cycles.",
    }


def generated_cache_temp_cleanup_plan(root: Path) -> Dict[str, Any]:
    root = normalize_root(root)
    candidates: List[Dict[str, Any]] = []
    for rel_path in GENERATED_CACHE_TEMP_ROOTS:
        candidate = resolve_within_root(root, root / rel_path)
        candidates.append(
            {
                "path": str(candidate),
                "exists": candidate.exists(),
                "within_root": True,
                "dry_run_only": True,
            }
        )
    return {
        "generated_at": utc_now_iso(),
        "root": str(root),
        "dry_run_only": True,
        "validation_cycle": "post_validation",
        "candidate_count": len(candidates),
        "candidates": candidates,
        "summary": "Path-guarded cache and temp cleanup candidates for post-validation cycles.",
    }


def duplicate_surface_audit_descriptors(root: Path) -> List[Dict[str, Any]]:
    root = normalize_root(root)
    descriptors = []
    for descriptor in DUPLICATE_SURFACE_AUDIT_DESCRIPTORS:
        item = dict(descriptor)
        item["root"] = str(root)
        descriptors.append(item)
    return descriptors


def post_final_pass_relocation_plan(root: Path) -> Dict[str, Any]:
    """Return the post-final-pass move/exclusion plan without mutating files."""
    root = normalize_root(root)
    outer_root = root.parent
    relocations: List[Dict[str, Any]] = []
    for target in POST_FINAL_PASS_RELOCATION_TARGETS:
        source = resolve_within_root(root, root / target["source"])
        destination = outer_root / target["destination"]
        relocations.append(
            {
                **target,
                "source_path": str(source),
                "source_exists": source.exists(),
                "destination_path": str(destination),
                "destination_inside_package": is_within_root(root, destination),
                "ready": source.exists() and not is_within_root(root, destination),
            }
        )
    return {
        "generated_at": utc_now_iso(),
        "root": str(root),
        "outer_root": str(outer_root),
        "dry_run_only": True,
        "trigger": "after_complete_final_pass_before_v0_10_0_package",
        "relocations": relocations,
        "package_exclusions": list(POST_FINAL_PASS_PACKAGE_EXCLUSIONS),
        "rule": "Do not move logs or reports until the complete final pass is done and readiness/diagnostics are clean.",
    }


def cache_cleanup_roots(root: Path) -> List[Path]:
    root = normalize_root(root)
    candidates = [
        root / ".pytest_cache",
        root / "__pycache__",
        root / "tests" / "__pycache__",
        root / "tools" / "__pycache__",
        root / "lightspeed_runtime" / "__pycache__",
        root / "lightspeed_runtime" / "achilles" / "__pycache__",
        root / "lightspeed_runtime" / "labs" / "__pycache__",
        root / "lightspeed_runtime" / "publishing" / "__pycache__",
        root / "lightspeed_runtime" / "reservoirs" / "__pycache__",
        root / "lightspeed_runtime" / "shell" / "__pycache__",
        root / "Z Axis" / "Z+3_Trinity" / "ui" / "__pycache__",
        root / "Z Axis" / "Z+3_Trinity" / "components" / "__pycache__",
        root / "Z Axis" / "Z+3_Trinity" / "diagnostics" / "__pycache__",
        root / "Z Axis" / "Z+3_Trinity" / "wizards" / "__pycache__",
        root / "Z Axis" / "Z-4_Merovingian" / "core" / "__pycache__",
        root / "Z Axis" / "Z-4_Merovingian" / "core" / "services" / "__pycache__",
        root / "Z Axis" / "Z-4_Merovingian" / "core" / "config" / "__pycache__",
        root / "Z Axis" / "Z-2_Oracle" / "tools" / "__pycache__",
        root / "Z Axis" / "Z-1_Morpheus" / "database" / "__pycache__",
        root / "Z Axis" / "Z-1_Morpheus" / "database" / "models" / "__pycache__",
    ]
    return [resolve_within_root(root, candidate) for candidate in candidates]


def protected_release_paths(root: Path) -> List[Path]:
    root = normalize_root(root)
    protected = [
        root / "N.py",
        root / "verify_launch_ready.py",
        root / "lightspeed_runtime",
        root / "Z Axis",
        root / "config",
        root / "dataindex",
        oracle_root(root),
        library_root(root),
        encyclopedia_root(root),
        datatables_root(root),
        trinity_root(root),
        merovingian_root(root),
    ]
    return [resolve_within_root(root, path) for path in protected]


def blank_state_verification_command(root: Path) -> str:
    root = normalize_root(root)
    db_path = merovingian_root(root) / "db" / "lightspeed_unified.db"
    tables = [
        "time_entries",
        "tasks",
        "projects",
        "companies",
        "users",
        "user_preferences",
        "ai_interactions",
        "chat_messages",
        "chat_conversations",
        "doc_task_markers",
        "oracle_ingestion_tasks",
        "interfloor_tasks",
        "simulations",
    ]
    table_list = ",".join(repr(name) for name in tables)
    return (
        "python -c \"import sqlite3; from pathlib import Path; "
        f"db=Path(r'{db_path}'); "
        f"tables=[{table_list}]; "
        "conn=sqlite3.connect(db); cur=conn.cursor(); counts={}; "
        "[counts.__setitem__(t, cur.execute(f'SELECT COUNT(*) FROM \\\"{t}\\\"').fetchone()[0]) for t in tables if cur.execute('SELECT name FROM sqlite_master WHERE type=\\'table\\' AND name=?', (t,)).fetchone()]; "
        "print(counts); conn.close()\""
    )


def release_cleanup_table_plan(root: Path) -> Dict[str, Any]:
    root = normalize_root(root)
    return {
        "generated_at": utc_now_iso(),
        "root": str(root),
        "database": {
            "path": str(merovingian_root(root) / "db" / "lightspeed_unified.db"),
            "tables": list(DATABASE_TABLES_TO_CLEAR),
        },
        "preserved_paths": [str(path) for path in protected_release_paths(root)],
        "project_workspace": {
            "path": str(project_workspace_root(root)),
            "purpose": "Project workspaces are cleared only at publish/reset time after extraction and handoff.",
        },
        "cache_roots": [str(path) for path in cache_cleanup_roots(root)],
    }


def dry_run_cleanup_summary(root: Path) -> Dict[str, Any]:
    root = normalize_root(root)
    workspace = project_workspace_root(root)
    project_entries = project_workspace_entries(root)
    caches = cache_cleanup_roots(root)
    summary = {
        "generated_at": utc_now_iso(),
        "root": str(root),
        "launch_setup_cleanup": launch_setup_cleanup_plan(root),
        "stale_runtime_rows": stale_runtime_row_cleanup_plan(root),
        "database": {
            "path": str(merovingian_root(root) / "db" / "lightspeed_unified.db"),
            "table_count": len(DATABASE_TABLES_TO_CLEAR),
            "tables": list(DATABASE_TABLES_TO_CLEAR),
        },
        "project_workspace": {
            "path": str(workspace),
            "exists": workspace.exists(),
            "entry_count": len(project_entries),
            "entries": [str(entry) for entry in project_entries],
        },
        "cache_cleanup": {
            "candidate_count": len(caches),
            "candidates": [
                {"path": str(path), "exists": path.exists()} for path in caches
            ],
        },
        "generated_cache_temp_cleanup": generated_cache_temp_cleanup_plan(root),
        "post_final_pass_relocation": post_final_pass_relocation_plan(root),
        "duplicate_surface_audit": duplicate_surface_audit_descriptors(root),
        "protected_paths": [str(path) for path in protected_release_paths(root)],
    }
    return summary


def build_smoke_checklist(root: Path) -> List[Dict[str, Any]]:
    root = normalize_root(root)
    checklist = []
    for item in SMOKE_TEST_COMMANDS:
        step = dict(item)
        step["root"] = str(root)
        checklist.append(step)
    checklist[-1]["command"] = blank_state_verification_command(root)
    return checklist
