from __future__ import annotations

from pathlib import Path

import pytest

from lightspeed_runtime.publish_snapshot import (
    build_publish_snapshot_plan,
    default_publish_snapshot_destination,
    normalize_destination,
)


def test_publish_snapshot_plan_is_overwrite_only_and_preserves_source(tmp_path: Path) -> None:
    destination = Path("D:/LightSpeed Consolidated/LightSpeed")

    plan = build_publish_snapshot_plan(tmp_path, destination)

    assert plan["overwrite_only"] is True
    assert plan["preserves_source_root"] is True
    assert plan["source_policy"] == "c_root_live"
    assert plan["destination_root"] == str(destination.resolve())
    assert plan["safe_destination"] is True


def test_publish_snapshot_rejects_live_source_overlap(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        normalize_destination(tmp_path, tmp_path)

    with pytest.raises(ValueError):
        normalize_destination(tmp_path, tmp_path / "publish")


def test_publish_snapshot_default_destination_is_canonical_publish_root(tmp_path: Path) -> None:
    destination = default_publish_snapshot_destination(tmp_path)

    assert destination.name == "snapshot"
    assert "publish" in str(destination).lower()
