from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import lightspeed_runtime.startup_options as startup_options
from lightspeed_runtime.startup_options import (
    build_startup_action_catalog,
    canonical_database_path,
    launch_runtime_candidates,
    probe_launch_python,
    read_launch_control_profile,
    read_startup_options,
    startup_setting_defaults,
    write_startup_option_values,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _create_directory_alias(alias: Path, backing: Path) -> None:
    try:
        alias.symlink_to(backing, target_is_directory=True)
        return
    except OSError:
        if os.name != "nt":
            raise
    completed = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(alias), str(backing)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        pytest.skip(f"directory alias unavailable: {completed.stderr or completed.stdout}")


def test_operator_namespace_survives_backing_alias(tmp_path: Path, monkeypatch) -> None:
    backing = tmp_path / "physical_backing" / "LightSpeed"
    alias = tmp_path / "operator" / "App"
    backing.mkdir(parents=True)
    alias.parent.mkdir(parents=True)
    _create_directory_alias(alias, backing)
    monkeypatch.setattr(startup_options, "CANONICAL_OPERATOR_ROOT", alias)

    _write_json(backing / "config" / "settings.json", {"show_splash_screen": True})
    _write_json(backing / "config" / "lightspeed_config.json", {"floors": {}})
    _write_json(backing / "config" / "unified_config.json", {"z_floors": {}})

    startup = read_startup_options(backing)
    launch = read_launch_control_profile(backing)

    assert Path(startup["root"]) == alias.absolute()
    assert Path(launch["root"]) == alias.absolute()
    assert all(Path(path).is_relative_to(alias.absolute()) for path in startup["source_files"].values())
    assert all(Path(path).is_relative_to(alias.absolute()) for path in launch["source_files"].values())

    assert write_startup_option_values(backing, {"startup.show_splash_screen": False}) is True
    assert json.loads((backing / "config" / "settings.json").read_text(encoding="utf-8"))[
        "show_splash_screen"
    ] is False


def test_database_path_ignores_core_and_cwd_and_fails_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    canonical = tmp_path / "operator_data" / "db" / "lightspeed_unified.db"
    core_candidate = tmp_path / "Core" / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db"
    canonical.parent.mkdir(parents=True)
    canonical.write_bytes(b"canonical")
    core_candidate.parent.mkdir(parents=True)
    core_candidate.write_bytes(b"noncanonical")
    monkeypatch.setattr(startup_options, "CANONICAL_DATABASE_PATH", canonical)
    monkeypatch.chdir(core_candidate.parent)

    assert canonical_database_path(core_candidate) == canonical.absolute()

    canonical.unlink()
    with pytest.raises(RuntimeError, match="canonical LightSpeed database is unavailable"):
        canonical_database_path(core_candidate)


def test_startup_options_normalize_existing_configs(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "config" / "settings.json",
        {
            "active_floors": ["Trinity", "Neo"],
            "show_splash_screen": True,
            "z_floor_dropdown_enabled": True,
            "ollama_auto_start": False,
            "web_server_auto_start": False,
            "db_auto_backup": True,
            "db_vacuum_on_startup": False,
            "max_concurrent_jobs": 4,
        },
    )
    _write_json(
        tmp_path / "config" / "lightspeed_config.json",
        {"floors": {"Trinity": {"enabled": True, "autostart": True, "port": 3005}}},
    )
    _write_json(
        tmp_path / "config" / "unified_config.json",
        {
            "z_floors": {
                "Z+3_Trinity": {
                    "theme": "dashboard_control",
                    "description": "Operator portal and settings.",
                }
            },
            "navigation_model": {"holospace_entry_policy": "Construct-only"},
        },
    )

    profile = read_startup_options(tmp_path)

    assert profile["floors"]["Trinity"]["canonical_id"] == "Z+3_Trinity"
    assert profile["floors"]["Trinity"]["autostart"] is True
    assert profile["global_options"]["holospace_entry_policy"] == "Construct-only"


def test_startup_actions_are_manifest_compatible(tmp_path: Path) -> None:
    _write_json(tmp_path / "config" / "settings.json", {"active_floors": ["Trinity"]})
    _write_json(tmp_path / "config" / "lightspeed_config.json", {"floors": {}})
    _write_json(tmp_path / "config" / "unified_config.json", {"z_floors": {}})

    catalog = build_startup_action_catalog(tmp_path)

    assert "Trinity" in catalog
    assert any(action["label"] == "Startup & Auto Options" for action in catalog["Trinity"])
    assert all("focus_section" in action for action in catalog["Trinity"])


def test_startup_option_write_updates_settings_json(tmp_path: Path) -> None:
    settings = tmp_path / "config" / "settings.json"
    _write_json(settings, {"show_splash_screen": True, "max_concurrent_jobs": 4})

    changed = write_startup_option_values(
        tmp_path,
        {
            "startup.show_splash_screen": False,
            "startup.max_concurrent_jobs": 7,
        },
    )
    payload = json.loads(settings.read_text(encoding="utf-8"))

    assert changed is True
    assert payload["show_splash_screen"] is False
    assert payload["max_concurrent_jobs"] == 7
    assert startup_setting_defaults(tmp_path)["startup.max_concurrent_jobs"] == 7


def test_launch_control_profile_prefers_resident_boot_and_defers_manual_heavy(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "config" / "settings.json",
        {
            "active_floors": ["Trinity", "Neo", "Smith", "Oracle", "TheConstruct"],
            "show_splash_screen": True,
            "max_concurrent_jobs": 4,
        },
    )
    _write_json(
        tmp_path / "config" / "lightspeed_config.json",
        {
            "floors": {
                "Trinity": {"enabled": True, "autostart": True},
                "Neo": {"enabled": True, "autostart": True},
                "Smith": {"enabled": True, "autostart": True},
                "Oracle": {"enabled": True, "autostart": True},
                "TheConstruct": {"enabled": True, "autostart": True},
            }
        },
    )
    _write_json(tmp_path / "config" / "unified_config.json", {"z_floors": {}})
    _write_json(tmp_path / "config" / "workspace_lanes.json", {"primary_surface": "Trinity", "interface_mode": "single_surface_bento_shell"})
    _write_json(tmp_path / "config" / "host_runtime_policy.json", {"runtime_limits": {"interactive_session_mode": "chrome_headroom_compact_shell"}})
    _write_json(tmp_path / "config" / "launch_control.json", {"gate": "CL-2 STAGING", "state": "local_launch_enablement"})
    _write_json(
        tmp_path / "Z Axis" / "Z-3_Smith" / "data" / "staging" / "floor_stage_population.json",
        {
            "boot_lane_order": ["Merovingian", "Trinity", "Neo", "Smith", "Oracle", "TheConstruct"],
            "resident_floors": ["Trinity", "Neo", "Smith"],
            "staged_floors": ["Oracle"],
            "manual_heavy_floors": ["TheConstruct"],
        },
    )

    profile = read_launch_control_profile(tmp_path)

    assert profile["profile_id"] == "resident_bounded_launch"
    assert profile["workspace_primary_surface"] == "Trinity"
    assert profile["launch_gate"] == "CL-2 STAGING"
    assert profile["boot_floors"] == ["Trinity", "Neo", "Smith"]
    assert profile["deferred_floors"] == ["Oracle"]
    assert profile["manual_heavy_floors"] == ["TheConstruct"]


def test_launch_runtime_candidates_prefer_workspace_venv_then_python311(
    tmp_path: Path,
    monkeypatch,
) -> None:
    lightspeed_root = tmp_path / "Desktop_Hooks" / "LightSpeed"
    lightspeed_root.mkdir(parents=True)

    local_app_data = tmp_path / "LocalAppData"
    python311 = local_app_data / "Programs" / "Python" / "Python311" / "python.exe"
    python311.parent.mkdir(parents=True, exist_ok=True)
    python311.write_text("", encoding="utf-8")

    workspace_venv = tmp_path / "venv" / "Scripts" / "python.exe"
    workspace_venv.parent.mkdir(parents=True, exist_ok=True)
    workspace_venv.write_text("", encoding="utf-8")

    monkeypatch.delenv("LIGHTSPEED_PYTHON", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))

    candidates = launch_runtime_candidates(lightspeed_root)

    assert [candidate["label"] for candidate in candidates] == ["workspace_venv", "python311"]
    assert candidates[0]["exists"] is True
    assert candidates[1]["exists"] is True


def test_launch_runtime_probe_allows_cold_import_headroom(
    tmp_path: Path,
    monkeypatch,
) -> None:
    python_path = tmp_path / "python.exe"
    python_path.write_text("", encoding="utf-8")
    observed: dict[str, int] = {}

    def fake_run(*args, timeout: int, **kwargs):
        observed["timeout"] = timeout
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "version": "3.11.9",
                    "missing_modules": [],
                    "module_results": {"json": "ok"},
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(startup_options.subprocess, "run", fake_run)

    result = probe_launch_python(python_path, modules=["json"])

    assert result["ok"] is True
    assert observed["timeout"] == 60
