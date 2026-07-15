from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List


FLOOR_CANONICAL_IDS = {
    "Trinity": "Z+3_Trinity",
    "Neo": "Z+2_Neo",
    "Architect": "Z+1_Architect",
    "TheConstruct": "Z0_TheConstruct",
    "Morpheus": "Z-1_Morpheus",
    "Oracle": "Z-2_Oracle",
    "Smith": "Z-3_Smith",
    "Merovingian": "Z-4_Merovingian",
}


FLOOR_ORDER = [
    "Trinity",
    "Neo",
    "Architect",
    "TheConstruct",
    "Morpheus",
    "Oracle",
    "Smith",
    "Merovingian",
]


STARTUP_SETTINGS_MAP = {
    "startup.show_splash_screen": ("show_splash_screen", bool),
    "startup.z_floor_dropdown_enabled": ("z_floor_dropdown_enabled", bool),
    "startup.ollama_auto_start": ("ollama_auto_start", bool),
    "startup.web_server_auto_start": ("web_server_auto_start", bool),
    "startup.db_auto_backup": ("db_auto_backup", bool),
    "startup.db_vacuum_on_startup": ("db_vacuum_on_startup", bool),
    "startup.max_concurrent_jobs": ("max_concurrent_jobs", int),
}


LAUNCH_CORE_MODULES = [
    "numpy",
    "psutil",
    "pandas",
    "PIL",
    "tkinter",
]


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(payload, dict):
                return payload
    except Exception:
        pass
    return {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _bool_text(value: Any) -> str:
    return "on" if bool(value) else "off"


def _config_paths(root: Path) -> Dict[str, Path]:
    config_root = root / "config"
    return {
        "settings": config_root / "settings.json",
        "lightspeed": config_root / "lightspeed_config.json",
        "unified": config_root / "unified_config.json",
        "host_runtime_policy": config_root / "host_runtime_policy.json",
        "workspace_lanes": config_root / "workspace_lanes.json",
        "launch_control": config_root / "launch_control.json",
        "floor_stage_population": root / "Z Axis" / "Z-3_Smith" / "data" / "staging" / "floor_stage_population.json",
    }


def _workspace_root(root: Path) -> Path:
    root = Path(root).resolve()
    if (root / "Desktop_Hooks").exists() and (root / "LightSpeed_Runtime").exists():
        return root
    if root.name == "LightSpeed" and root.parent.name == "Desktop_Hooks":
        return root.parent.parent
    if root.name == "LightSpeed_Runtime" and root.parent.name == "LightSpeed_Consolidated":
        return root.parent
    return root


def launch_runtime_candidates(root: Path) -> List[Dict[str, Any]]:
    """Return ordered Python runtimes that are acceptable for LightSpeed launch."""
    workspace_root = _workspace_root(Path(root))
    local_app_data = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))

    raw_candidates = [
        ("env_override", os.environ.get("LIGHTSPEED_PYTHON", "").strip(), "LIGHTSPEED_PYTHON"),
        (
            "workspace_venv",
            str(workspace_root / "venv" / "Scripts" / "python.exe"),
            "workspace_venv",
        ),
        (
            "python311",
            str(local_app_data / "Programs" / "Python" / "Python311" / "python.exe"),
            "LOCALAPPDATA/Python311",
        ),
    ]

    seen: set[str] = set()
    candidates: List[Dict[str, Any]] = []
    for label, raw_path, source in raw_candidates:
        if not raw_path:
            continue
        path = Path(raw_path).expanduser()
        normalized = str(path).lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        candidates.append(
            {
                "label": label,
                "path": str(path),
                "source": source,
                "exists": path.exists(),
            }
        )
    return candidates


def probe_launch_python(
    python_path: Path,
    *,
    modules: List[str] | None = None,
    timeout_seconds: int = 60,
) -> Dict[str, Any]:
    """Probe a Python executable for the core modules LightSpeed needs to launch."""
    python_path = Path(python_path).resolve()
    module_list = list(modules or LAUNCH_CORE_MODULES)
    if not python_path.exists():
        return {
            "ok": False,
            "path": str(python_path),
            "version": "",
            "missing_modules": module_list,
            "module_results": {},
            "error": "python executable not found",
        }

    script = "\n".join(
        [
            "import importlib",
            "import json",
            "import sys",
            f"mods = {module_list!r}",
            "results = {}",
            "missing = []",
            "for name in mods:",
            "    try:",
            "        importlib.import_module(name)",
            "        results[name] = 'ok'",
            "    except Exception as exc:",
            "        results[name] = str(exc)",
            "        missing.append(name)",
            "payload = {",
            "    'executable': sys.executable,",
            "    'version': '.'.join(str(part) for part in sys.version_info[:3]),",
            "    'missing_modules': missing,",
            "    'module_results': results,",
            "}",
            "print(json.dumps(payload))",
        ]
    )

    try:
        completed = subprocess.run(
            [str(python_path), "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except Exception as exc:
        return {
            "ok": False,
            "path": str(python_path),
            "version": "",
            "missing_modules": module_list,
            "module_results": {},
            "error": str(exc),
        }

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    try:
        payload = json.loads(stdout) if stdout else {}
    except Exception:
        payload = {}

    missing_modules = payload.get("missing_modules")
    if not isinstance(missing_modules, list):
        missing_modules = list(module_list)

    module_results = payload.get("module_results")
    if not isinstance(module_results, dict):
        module_results = {}

    version = payload.get("version")
    if not isinstance(version, str):
        version = ""

    return {
        "ok": completed.returncode == 0 and not missing_modules,
        "path": str(python_path),
        "version": version,
        "missing_modules": missing_modules,
        "module_results": module_results,
        "error": stderr if completed.returncode != 0 else "",
    }


def launch_runtime_report(root: Path) -> Dict[str, Any]:
    """Return the preferred runtime candidate plus a lightweight readiness probe."""
    candidates = launch_runtime_candidates(root)
    selected = next((candidate for candidate in candidates if candidate.get("exists")), None)
    probe = probe_launch_python(Path(selected["path"])) if selected else None
    return {
        "candidates": candidates,
        "selected": selected,
        "probe": probe,
        "ready": bool(probe and probe.get("ok")),
    }


def startup_setting_defaults(root: Path) -> Dict[str, Any]:
    """Return UI-setting defaults mirrored from canonical startup settings."""
    profile = read_startup_options(root)
    global_options = profile.get("global_options") if isinstance(profile.get("global_options"), dict) else {}
    return {
        "startup.show_splash_screen": bool(global_options.get("show_splash_screen", True)),
        "startup.z_floor_dropdown_enabled": bool(global_options.get("z_floor_dropdown_enabled", True)),
        "startup.ollama_auto_start": bool(global_options.get("ollama_auto_start", False)),
        "startup.web_server_auto_start": bool(global_options.get("web_server_auto_start", False)),
        "startup.db_auto_backup": bool(global_options.get("db_auto_backup", True)),
        "startup.db_vacuum_on_startup": bool(global_options.get("db_vacuum_on_startup", False)),
        "startup.max_concurrent_jobs": int(global_options.get("max_concurrent_jobs", 4) or 4),
    }


def write_startup_option_values(root: Path, values: Dict[str, Any]) -> bool:
    """
    Persist supported startup options to config/settings.json.

    Floor autostart policy remains read-only here because floor runtime launches
    also depend on manifests and host availability; those are surfaced as a
    profile summary rather than edited blindly.
    """
    root = Path(root).resolve()
    settings_path = _config_paths(root)["settings"]
    settings = _read_json(settings_path)
    changed = False

    for ui_key, (settings_key, caster) in STARTUP_SETTINGS_MAP.items():
        if ui_key not in values:
            continue
        raw_value = values.get(ui_key)
        try:
            value = caster(raw_value)
        except Exception:
            value = raw_value
        if settings.get(settings_key) != value:
            settings[settings_key] = value
            changed = True

    if changed:
        _write_json(settings_path, settings)
    return changed


def read_startup_options(root: Path) -> Dict[str, Any]:
    """
    Return one normalized startup/autostart profile from the existing config set.

    This adapter is intentionally read-only. It keeps the UI from inventing a
    fourth startup source while still surfacing the current values consistently
    across Trinity, Smith, Merovingian, and the floor shells.
    """
    root = Path(root).resolve()
    paths = _config_paths(root)
    settings = _read_json(paths["settings"])
    lightspeed = _read_json(paths["lightspeed"])
    unified = _read_json(paths["unified"])

    lightspeed_floors = lightspeed.get("floors") if isinstance(lightspeed.get("floors"), dict) else {}
    unified_floors = unified.get("z_floors") if isinstance(unified.get("z_floors"), dict) else {}
    active_floors = settings.get("active_floors") if isinstance(settings.get("active_floors"), list) else []

    floors: Dict[str, Dict[str, Any]] = {}
    for floor_name in FLOOR_ORDER:
        canonical_id = FLOOR_CANONICAL_IDS[floor_name]
        runtime_cfg = lightspeed_floors.get(floor_name) if isinstance(lightspeed_floors.get(floor_name), dict) else {}
        floor_cfg = unified_floors.get(canonical_id) if isinstance(unified_floors.get(canonical_id), dict) else {}
        enabled = bool(runtime_cfg.get("enabled", floor_name in active_floors or canonical_id in active_floors))
        floors[floor_name] = {
            "floor": floor_name,
            "canonical_id": canonical_id,
            "enabled": enabled,
            "autostart": bool(runtime_cfg.get("autostart", enabled)),
            "port": runtime_cfg.get("port", ""),
            "responsibility": str(runtime_cfg.get("responsibility") or floor_cfg.get("theme") or ""),
            "description": str(floor_cfg.get("description") or ""),
        }

    global_options = {
        "first_run_complete": bool(settings.get("first_run_complete", False)),
        "show_splash_screen": bool(settings.get("show_splash_screen", True)),
        "z_floor_dropdown_enabled": bool(settings.get("z_floor_dropdown_enabled", True)),
        "ollama_auto_start": bool(settings.get("ollama_auto_start", False)),
        "web_server_auto_start": bool(settings.get("web_server_auto_start", False)),
        "db_auto_backup": bool(settings.get("db_auto_backup", True)),
        "db_vacuum_on_startup": bool(settings.get("db_vacuum_on_startup", False)),
        "max_concurrent_jobs": int(settings.get("max_concurrent_jobs", 4) or 4),
        "holospace_entry_policy": str(
            ((unified.get("navigation_model") or {}) if isinstance(unified.get("navigation_model"), dict) else {}).get(
                "holospace_entry_policy",
                "Construct-owned opt-in context",
            )
        ),
    }

    return {
        "root": str(root),
        "source_files": {name: str(path) for name, path in paths.items()},
        "global_options": global_options,
        "floors": floors,
    }


def read_launch_control_profile(root: Path) -> Dict[str, Any]:
    """
    Merge startup toggles with floor population policy into one bounded launch profile.

    Default intent:
    - boot only resident floors on launch
    - leave staged floors deferred
    - require explicit activation for manual-heavy floors
    """
    root = Path(root).resolve()
    paths = _config_paths(root)
    startup = read_startup_options(root)
    stage_population = _read_json(paths["floor_stage_population"])
    workspace_lanes = _read_json(paths["workspace_lanes"])
    host_runtime_policy = _read_json(paths["host_runtime_policy"])
    launch_control = _read_json(paths["launch_control"])

    floors = startup.get("floors") if isinstance(startup.get("floors"), dict) else {}
    enabled_floors = [
        floor_name
        for floor_name, payload in floors.items()
        if isinstance(payload, dict) and payload.get("enabled")
    ]

    boot_lane_order = [
        str(item)
        for item in (stage_population.get("boot_lane_order") or [])
        if str(item) in FLOOR_ORDER
    ]
    resident_floors = [
        str(item)
        for item in (stage_population.get("resident_floors") or [])
        if str(item) in FLOOR_ORDER
    ]
    staged_floors = [
        str(item)
        for item in (stage_population.get("staged_floors") or [])
        if str(item) in FLOOR_ORDER
    ]
    manual_heavy_floors = [
        str(item)
        for item in (stage_population.get("manual_heavy_floors") or [])
        if str(item) in FLOOR_ORDER
    ]

    if not resident_floors:
        resident_floors = [
            floor_name
            for floor_name in FLOOR_ORDER
            if floor_name in enabled_floors and bool((floors.get(floor_name) or {}).get("autostart"))
        ]

    ordered_resident = [floor for floor in boot_lane_order if floor in resident_floors]
    ordered_resident.extend(floor for floor in resident_floors if floor not in ordered_resident)

    ordered_staged = [floor for floor in boot_lane_order if floor in staged_floors]
    ordered_staged.extend(floor for floor in staged_floors if floor not in ordered_staged)

    return {
        "profile_id": "resident_bounded_launch",
        "root": str(root),
        "source_files": {name: str(path) for name, path in paths.items()},
        "workspace_primary_surface": workspace_lanes.get("primary_surface"),
        "interface_mode": workspace_lanes.get("interface_mode"),
        "launch_gate": launch_control.get("gate"),
        "launch_state": launch_control.get("state"),
        "host_session_mode": (
            (host_runtime_policy.get("runtime_limits") or {}).get("interactive_session_mode")
            if isinstance(host_runtime_policy.get("runtime_limits"), dict)
            else None
        ),
        "enabled_floors": enabled_floors,
        "boot_lane_order": boot_lane_order,
        "resident_floors": resident_floors,
        "staged_floors": staged_floors,
        "manual_heavy_floors": manual_heavy_floors,
        "boot_floors": ordered_resident,
        "deferred_floors": ordered_staged,
        "global_options": startup.get("global_options") or {},
        "floors": floors,
    }


def build_startup_action_catalog(root: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Build manifest-compatible floor actions for startup/autostart visibility."""
    profile = read_startup_options(root)
    floors = profile.get("floors") if isinstance(profile.get("floors"), dict) else {}
    global_options = profile.get("global_options") if isinstance(profile.get("global_options"), dict) else {}
    catalog: Dict[str, List[Dict[str, Any]]] = {}

    for floor_name, floor in floors.items():
        if not isinstance(floor, dict):
            continue
        catalog.setdefault(floor_name, []).append(
            {
                "id": f"{floor_name.lower()}_startup_policy",
                "label": "Startup Policy",
                "kind": "startup",
                "target": "startup_options",
                "priority": "runtime",
                "focus_section": "startup_options",
                "description": (
                    f"Enabled {_bool_text(floor.get('enabled'))}; autostart {_bool_text(floor.get('autostart'))}; "
                    f"port {floor.get('port') or 'n/a'}; responsibility {floor.get('responsibility') or 'floor-owned'}."
                ),
            }
        )

    catalog.setdefault("Trinity", []).append(
        {
            "id": "trinity_startup_options",
            "label": "Startup & Auto Options",
            "kind": "settings",
            "target": "startup_options",
            "priority": "startup",
            "focus_section": "startup_options",
            "description": (
                f"Splash {_bool_text(global_options.get('show_splash_screen'))}; "
                f"Z floor dropdown {_bool_text(global_options.get('z_floor_dropdown_enabled'))}; "
                f"web auto-start {_bool_text(global_options.get('web_server_auto_start'))}; "
                f"Ollama auto-start {_bool_text(global_options.get('ollama_auto_start'))}."
            ),
        }
    )
    catalog.setdefault("Smith", []).append(
        {
            "id": "smith_auto_execution_budget",
            "label": "Auto Execution Budget",
            "kind": "automation",
            "target": "startup_options",
            "priority": "runtime",
            "focus_section": "startup_options",
            "description": (
                f"Max concurrent jobs: {global_options.get('max_concurrent_jobs', 4)}. "
                "Smith owns background routing; Trinity owns the visible settings surface."
            ),
        }
    )
    catalog.setdefault("Merovingian", []).append(
        {
            "id": "merovingian_startup_health",
            "label": "Startup Health Policy",
            "kind": "audit",
            "target": "startup_options",
            "priority": "startup",
            "focus_section": "startup_options",
            "description": (
                f"DB auto-backup {_bool_text(global_options.get('db_auto_backup'))}; "
                f"vacuum on startup {_bool_text(global_options.get('db_vacuum_on_startup'))}; "
                "diagnostic evidence remains Merovingian-owned."
            ),
        }
    )
    return catalog


def startup_summary_lines(root: Path) -> List[str]:
    """Human-readable startup profile for compact settings surfaces."""
    profile = read_startup_options(root)
    global_options = profile.get("global_options") if isinstance(profile.get("global_options"), dict) else {}
    floors = profile.get("floors") if isinstance(profile.get("floors"), dict) else {}
    autostart_count = sum(1 for floor in floors.values() if isinstance(floor, dict) and floor.get("autostart"))
    enabled_count = sum(1 for floor in floors.values() if isinstance(floor, dict) and floor.get("enabled"))
    return [
        f"Floors enabled: {enabled_count}/{len(FLOOR_ORDER)}",
        f"Floor runtimes marked autostart: {autostart_count}/{len(FLOOR_ORDER)}",
        f"Splash screen: {_bool_text(global_options.get('show_splash_screen'))}",
        f"Z floor dropdown: {_bool_text(global_options.get('z_floor_dropdown_enabled'))}",
        f"Ollama auto-start: {_bool_text(global_options.get('ollama_auto_start'))}",
        f"Web server auto-start: {_bool_text(global_options.get('web_server_auto_start'))}",
        f"DB auto-backup: {_bool_text(global_options.get('db_auto_backup'))}",
        f"Vacuum on startup: {_bool_text(global_options.get('db_vacuum_on_startup'))}",
        f"Max concurrent jobs: {global_options.get('max_concurrent_jobs', 4)}",
        f"Holospace entry: {global_options.get('holospace_entry_policy')}",
    ]
