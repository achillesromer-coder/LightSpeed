from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "migrate_first_file_semantics_to_s92.py"
SPEC = importlib.util.spec_from_file_location("first_file_migration", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
migration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(migration)


def make_zip(path: Path, names: list[str]) -> None:
    with zipfile.ZipFile(path, "w") as z:
        for name in names:
            z.writestr(name, b"{}")


def test_semantic_delta_allows_only_bounded_semantic_source_and_proof_paths(tmp_path):
    base = tmp_path / "base.cgx"
    intake = tmp_path / "intake.cgx"
    make_zip(base, ["cgx/bootstrap.json"])
    make_zip(
        intake,
        [
            "cgx/bootstrap.json",
            "graph/cells/cell_a.json",
            "graph/objects/object_a.json",
            "graph/relations/rel_a.json",
            "proof/intake/proof.json",
            "sources/intake/source.json",
            "semantic/intake_index.json",
            "events/S3.json",
            "store/blobs/aa/hash",
        ],
    )
    allowed, ignored = migration.semantic_delta_paths(base, intake)
    assert "graph/cells/cell_a.json" in allowed
    assert "semantic/intake_index.json" in allowed
    assert "events/S3.json" in ignored
    assert "store/blobs/aa/hash" in ignored


def test_semantic_delta_rejects_unexpected_control_or_payload_path(tmp_path):
    base = tmp_path / "base.cgx"
    intake = tmp_path / "intake.cgx"
    make_zip(base, ["cgx/bootstrap.json"])
    make_zip(intake, ["cgx/bootstrap.json", "payload/Q0/unbounded.bin"])
    with pytest.raises(migration.FirstFileMigrationError, match="unexpected"):
        migration.semantic_delta_paths(base, intake)
