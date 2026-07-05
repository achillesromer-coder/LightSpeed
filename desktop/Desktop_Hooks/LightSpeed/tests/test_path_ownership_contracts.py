from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from lightspeed_runtime.ai_settings import load_ai_settings, runtime_ai_config_path
from lightspeed_runtime.assimilation import assimilate_external_roots
from lightspeed_runtime.runtime import LightSpeedRuntime
from lightspeed_runtime.storage_paths import (
    canonical_ai_settings_path,
    canonical_execution_queue_path,
    canonical_intermediary_targets_path,
    canonical_runtime_config_path,
    publish_root,
    publish_snapshot_root,
    resolve_ai_settings_path,
    resolve_intermediary_targets_path,
    resolve_runtime_config_path,
    snapshot_export_root,
    runtime_exports_root,
)


def test_runtime_compatibility_paths_are_floor_owned() -> None:
    root = Path("C:/tmp/LightSpeed")

    assert canonical_runtime_config_path(root) == (
        root / "Z Axis" / "Z-2_Oracle" / "config" / "runtime" / "runtime_reservoirs.json"
    )
    assert canonical_intermediary_targets_path(root) == (
        root / "Z Axis" / "Z+1_Architect" / "config" / "runtime" / "intermediary_targets.json"
    )
    assert canonical_ai_settings_path(root) == (
        root / "Z Axis" / "Z+1_Architect" / "config" / "ai_config.json"
    )
    assert runtime_exports_root(root) == root / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports"
    assert publish_root(root) == root / "Z Axis" / "Z+1_Architect" / "data" / "publish"
    assert publish_snapshot_root(root) == root / "Z Axis" / "Z+1_Architect" / "data" / "publish" / "snapshot"
    assert snapshot_export_root(root) == root / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports" / "snapshot"

    legacy_root_config = root / "config"
    for path in (
        canonical_runtime_config_path(root),
        canonical_intermediary_targets_path(root),
        canonical_ai_settings_path(root),
    ):
        assert "Z Axis" in str(path)
        assert not str(path).startswith(str(legacy_root_config))


def test_runtime_reads_legacy_root_config_as_fallback(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    legacy_runtime_dir = root / "config" / "runtime"
    legacy_runtime_dir.mkdir(parents=True, exist_ok=True)
    legacy_runtime_path = legacy_runtime_dir / "runtime_reservoirs.json"
    legacy_runtime_path.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "legacy_reservoir",
                        "root_path": "C:/legacy/reservoir",
                        "source_type": "dataset",
                        "classification": "reference",
                        "floor_owner": "Oracle",
                        "source_label": "Legacy Reservoir",
                        "definition": "Legacy reservoir definition",
                        "operator_notes": "Legacy notes",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    legacy_intermediary_targets_path = legacy_runtime_dir / "intermediary_targets.json"
    legacy_intermediary_targets_path.write_text(
        json.dumps({"website_bridge": {"label": "Legacy Bridge"}}),
        encoding="utf-8",
    )
    legacy_ai_settings_path = root / "config" / "ai_config.json"
    legacy_ai_settings_path.write_text(
        json.dumps(
            {
                "ollama": {"enabled": True, "model": "llama3.2"},
                "achilles": {"enabled": False},
            }
        ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)

    assert runtime.config_path == canonical_runtime_config_path(root)
    assert resolve_runtime_config_path(root) == legacy_runtime_path
    assert runtime.load_config()["sources"][0]["source_id"] == "legacy_reservoir"
    assert resolve_intermediary_targets_path(root) == legacy_intermediary_targets_path
    assert runtime.load_intermediary_targets()["website_bridge"]["label"] == "Legacy Bridge"
    assert runtime.load_intermediary_targets()["website_bridge"]["owner_floor"] == "Smith"
    assert canonical_execution_queue_path(root) == root / "Z Axis" / "Z+1_Architect" / "data" / "finalization" / "execution_queues.json"
    assert resolve_ai_settings_path(root) == legacy_ai_settings_path
    assert load_ai_settings(root)["achilles"]["enabled"] is False


def test_save_ai_settings_writes_to_architect_owned_config(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime = LightSpeedRuntime(root=root)

    saved = runtime.save_ai_settings(
        {
            "active_backend": "ollama_local",
            "active_profile": "low_lag_local",
            "achilles": {"approval_gated": False},
        }
    )

    assert saved == canonical_ai_settings_path(root)
    assert saved == runtime_ai_config_path(root)
    assert saved.exists()
    assert not (root / "config" / "ai_config.json").exists()

    payload = json.loads(saved.read_text(encoding="utf-8"))
    assert payload["achilles"]["approval_gated"] is False


def test_assimilation_rewrites_runtime_config_into_oracle_owned_root(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    legacy_runtime_dir = root / "config" / "runtime"
    legacy_runtime_dir.mkdir(parents=True, exist_ok=True)
    legacy_path = legacy_runtime_dir / "runtime_reservoirs.json"
    legacy_path.write_text(json.dumps({"sources": []}), encoding="utf-8")

    payload = assimilate_external_roots(root)
    canonical_path = canonical_runtime_config_path(root)

    assert payload["config_path"] == str(canonical_path)
    assert canonical_path.exists()
    assert legacy_path.exists()

    written = json.loads(canonical_path.read_text(encoding="utf-8"))
    source_ids = {item["source_id"] for item in written["sources"]}
    assert "library_reference_general" in source_ids


def test_merovingian_core_paths_publish_runtime_owner_contracts() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "Z Axis" / "Z-4_Merovingian" / "core" / "config" / "paths.py"
    spec = importlib.util.spec_from_file_location("lightspeed_core_paths_runtime_contracts", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.ORACLE_RUNTIME_RESERVOIRS == module.ORACLE_RUNTIME_CONFIG / "runtime_reservoirs.json"
    assert module.ARCHITECT_INTERMEDIARY_TARGETS == module.ARCHITECT_RUNTIME_CONFIG / "intermediary_targets.json"
    assert module.ARCHITECT_AI_CONFIG == module.ARCHITECT_CONFIG / "ai_config.json"
    assert str(module.ORACLE_RUNTIME_RESERVOIRS).startswith(str(module.ORACLE_ROOT))
    assert str(module.ARCHITECT_INTERMEDIARY_TARGETS).startswith(str(module.ARCHITECT_ROOT))
    assert str(module.ARCHITECT_AI_CONFIG).startswith(str(module.ARCHITECT_ROOT))
