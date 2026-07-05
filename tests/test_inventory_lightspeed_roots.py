from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys


TOOLS_ROOT = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from inventory_lightspeed_roots import (  # noqa: E402
    classify_file,
    extract_candidate,
    inventory_roots,
    iter_physical_files,
)


def test_root_classification_preserves_newer_unique_files(tmp_path: Path) -> None:
    result = classify_file(
        path=tmp_path / "N_updated.py",
        canonical_hashes=set(),
        modified_utc="2025-11-14T10:46:19Z",
    )

    assert result.action == "extract_candidate"
    assert result.source_classification == "source"


def test_identical_file_is_not_copied_again(tmp_path: Path) -> None:
    digest = "abc"

    result = classify_file(
        path=tmp_path / "duplicate.md",
        canonical_hashes={digest},
        digest=digest,
    )

    assert result.action == "reference_existing"


def test_runtime_payload_is_inventory_only(tmp_path: Path) -> None:
    result = classify_file(
        path=tmp_path / "models" / "agent.gguf",
        canonical_hashes=set(),
        digest="unique",
    )

    assert result.action == "inventory_only"
    assert result.source_classification == "model"


def test_extract_candidate_preserves_root_and_checksum(tmp_path: Path) -> None:
    source_root = tmp_path / "old"
    source = source_root / "Z Axis" / "Trinity.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('trinity')\n", encoding="utf-8")
    destination_root = tmp_path / "historical"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()

    receipt = extract_candidate(
        source=source,
        source_root=source_root,
        root_label="desktop",
        destination_root=destination_root,
        digest=digest,
    )

    target = destination_root / "desktop" / "Z Axis" / "Trinity.py"
    assert target.read_bytes() == source.read_bytes()
    assert receipt["sha256"] == digest
    assert Path(receipt["destination"]) == target


def test_inventory_does_not_follow_directory_links(tmp_path: Path) -> None:
    root = tmp_path / "root"
    external = tmp_path / "external"
    root.mkdir()
    external.mkdir()
    (root / "kept.py").write_text("kept\n", encoding="utf-8")
    (external / "escaped.py").write_text("escaped\n", encoding="utf-8")
    link = root / "external-link"
    try:
        os.symlink(external, link, target_is_directory=True)
    except OSError:
        return

    relative_paths = {path.relative_to(root).as_posix() for path in iter_physical_files(root)}

    assert relative_paths == {"kept.py"}


def test_inventory_aggregates_runaway_archive_records(tmp_path: Path) -> None:
    historical_root = tmp_path / "historical"
    runaway_root = historical_root / "legacy" / "oracle_ingest_file"
    runaway_root.mkdir(parents=True)
    payloads = [b"one", b"two-two", b"three"]
    for index, payload in enumerate(payloads):
        run = runaway_root / f"run-{index}"
        run.mkdir()
        (run / "manifest.json").write_bytes(payload)

    canonical_root = tmp_path / "canonical"
    canonical_root.mkdir()
    inventory_path = tmp_path / "inventory.jsonl"
    result = inventory_roots(
        roots={"desktop": historical_root},
        canonical_root=canonical_root,
        destination_root=tmp_path / "extracted",
        inventory_path=inventory_path,
        execute_extract=False,
    )

    records = [
        json.loads(line)
        for line in inventory_path.read_text(encoding="utf-8").splitlines()
    ]

    assert result["total_files"] == 3
    assert result["total_bytes"] == sum(map(len, payloads))
    assert len(records) == 1
    assert records[0]["record_type"] == "aggregate"
    assert records[0]["source_classification"] == "archive"
    assert records[0]["count"] == 3
    assert records[0]["bytes"] == sum(map(len, payloads))
    assert len(records[0]["sample_paths"]) == 3
    assert "sha256" not in records[0]
