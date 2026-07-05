from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def construct_floor_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_construct_runtime_dir() -> Path:
    return construct_floor_root() / "data" / "runtime"


def load_construct_runtime_profile() -> dict[str, Any]:
    path = resolve_construct_runtime_dir() / "construct_runtime_profile.json"
    payload = _read_json(path, fallback=_default_construct_runtime_profile())
    payload.setdefault("profile_id", "construct_runtime_default")
    payload.setdefault("default_surface", "ambient_embed")
    payload["_profile_path"] = str(path)
    return payload


def load_virtual_space_test_matrix() -> dict[str, Any]:
    path = resolve_construct_runtime_dir() / "virtual_space_test_matrix.json"
    payload = _read_json(path, fallback=_default_virtual_space_test_matrix())
    payload.setdefault("profile_id", "construct_runtime_default")
    payload["_profile_path"] = str(path)
    return payload


def _read_json(path: Path, *, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            if isinstance(payload, dict):
                return payload
    except Exception:
        pass
    return dict(fallback)


def _default_construct_runtime_profile() -> dict[str, Any]:
    return {
        "profile_id": "construct_runtime_default",
        "default_surface": "ambient_embed",
        "render_modes": [
            {"mode": "ambient_embed", "target_fps": 33, "boot_default": True},
            {"mode": "tower_overlay", "target_fps": 45, "boot_default": False},
            {"mode": "immersive_full", "target_fps": 60, "manual_only": True},
        ],
        "resource_guards": {
            "max_visible_widgets": 36,
            "max_live_texture_panels": 8,
            "max_background_simulations": 1,
            "max_parallel_render_jobs": 1,
        },
    }


def _default_virtual_space_test_matrix() -> dict[str, Any]:
    return {
        "profile_id": "construct_runtime_default",
        "default_surface": "ambient_embed",
        "virtual_space_tests": {
            "smoke_lanes": [
                {"lane_id": "construct_boot_contract", "surface": "runtime_profile"},
                {"lane_id": "ambient_embed_smoke", "surface": "immersive_3d_engine"},
            ],
            "manual_lanes": [
                {"lane_id": "immersive_full_launch", "surface": "immersive_3d_engine"},
            ],
        },
    }
