from __future__ import annotations

import json
from pathlib import Path

import pytest

from lightspeed_runtime.background_application import (
    BACKGROUND_SCOPES,
    build_background_application_plan,
    build_background_scope_plan,
    read_background_application_plan,
    write_background_application_plan,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_background_plan_projects_all_supported_scopes(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "config" / "settings.json",
        {
            "background.mode": "futuristic_gamelike",
            "background.input_type": "uploaded_picture",
            "background.gradient": "#111,#222",
            "background.image_path": "wallpaper.png",
            "background.environment_reference": "render_ref.glb",
            "background.scope": "floor",
        },
    )
    _write_json(
        tmp_path / "config" / "premium_theme_config.json",
        {
            "editable_backgrounds": {
                "base_themes": {"minimal": "a", "balanced": "b", "futuristic_gamelike": "c"},
                "inputs": ["solid_color", "multi_stop_gradient", "uploaded_picture", "uploaded_environment_reference"],
            }
        },
    )

    plan = build_background_application_plan(tmp_path)

    assert plan["background_settings"]["mode"] == "futuristic_gamelike"
    assert plan["scope"] == "floor"
    assert [item["scope"] for item in plan["surface_plans"]] == list(BACKGROUND_SCOPES)
    assert any(item["active"] is True for item in plan["surface_plans"])
    assert plan["surface_plans"][2]["preview"]["image_path"] == "wallpaper.png"


def test_background_scope_validation_and_subplan(tmp_path: Path) -> None:
    _write_json(tmp_path / "config" / "settings.json", {"background.scope": "project"})
    _write_json(tmp_path / "config" / "premium_theme_config.json", {})

    project_plan = build_background_scope_plan(tmp_path, "project")

    assert project_plan["scope"] == "project"
    assert project_plan["surface"] == "Project"
    assert "project wall" in project_plan["summary"].lower()

    with pytest.raises(ValueError):
        build_background_scope_plan(tmp_path, "unsupported")


def test_background_plan_round_trips_to_json(tmp_path: Path) -> None:
    _write_json(tmp_path / "config" / "settings.json", {"background.scope": "workspace"})
    _write_json(tmp_path / "config" / "premium_theme_config.json", {})
    out = tmp_path / "background_application.json"

    payload = write_background_application_plan(tmp_path, out)
    stored = read_background_application_plan(tmp_path, out)

    assert out.exists()
    assert stored["scope"] == "workspace"
    assert payload["path"] == str(out)
