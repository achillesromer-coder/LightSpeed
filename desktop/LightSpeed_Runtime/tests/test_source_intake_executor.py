import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from lightspeed_runtime.source_intake import SourceIntakeError
from lightspeed_runtime.source_intake_executor import execute_source_intake, readback_source_intake


def test_intake_preserves_native_bytes_and_exposes_derived_output(tmp_path):
    source = tmp_path / "source.csv"
    raw = b'component,value\r\nA,12\r\n'
    source.write_bytes(raw)
    payload = {"source_path": str(source), "source_sha256": hashlib.sha256(raw).hexdigest()}
    receipt = execute_source_intake(payload, command_id="test-intake", shell_root=tmp_path / "App", allowed_roots=[tmp_path])
    assert source.read_bytes() == raw
    assert receipt["canonical_mutation"] is False
    assert receipt["semantic_acceptance"] == "requires_independent_review"
    assert Path(receipt["artifacts"][0]["path"]).read_bytes() == raw
    for artifact in receipt["artifacts"]:
        assert hashlib.sha256(Path(artifact["path"]).read_bytes()).hexdigest() == artifact["sha256"]
    envelope = json.loads(Path(receipt["artifacts"][1]["path"]).read_text())
    assert envelope["projections"][0]["rows"][1] == ["A", "12"]
    assert readback_source_intake(payload, command_id="test-intake", shell_root=tmp_path / "App",
                                  allowed_roots=[tmp_path]) == receipt
    with pytest.raises(SourceIntakeError, match="already exist"):
        execute_source_intake(payload, command_id="test-intake", shell_root=tmp_path / "App", allowed_roots=[tmp_path])


def test_intake_recovery_rejects_changed_bundle_without_overwriting_it(tmp_path):
    source = tmp_path / "source.csv"
    source.write_bytes(b"a,b\n1,2\n")
    payload = {"source_path": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    receipt = execute_source_intake(payload, command_id="test-intake", shell_root=tmp_path / "App",
                                    allowed_roots=[tmp_path])
    artifact = Path(receipt["artifacts"][1]["path"])
    tampered = b"x" * artifact.stat().st_size
    artifact.write_bytes(tampered)
    with pytest.raises(SourceIntakeError, match="artifact .* mismatch"):
        readback_source_intake(payload, command_id="test-intake", shell_root=tmp_path / "App",
                               allowed_roots=[tmp_path])
    assert artifact.read_bytes() == tampered


def test_intake_recovery_checks_envelope_digest_independently_of_artifact_manifest(tmp_path):
    source = tmp_path / "source.csv"
    source.write_bytes(b"a,b\n1,2\n")
    payload = {"source_path": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    receipt = execute_source_intake(payload, command_id="test-intake", shell_root=tmp_path / "App",
                                    allowed_roots=[tmp_path])
    envelope_path = Path(receipt["artifacts"][1]["path"])
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    envelope["warnings"].append("fabricated")
    envelope_path.write_text(json.dumps(envelope), encoding="utf-8")
    receipt["artifacts"][1]["bytes"] = envelope_path.stat().st_size
    receipt["artifacts"][1]["sha256"] = hashlib.sha256(envelope_path.read_bytes()).hexdigest()
    Path(receipt["receipt_path"]).write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(SourceIntakeError, match="envelope lineage mismatch"):
        readback_source_intake(payload, command_id="test-intake", shell_root=tmp_path / "App",
                               allowed_roots=[tmp_path])


@pytest.mark.parametrize("reason", ["outside", "hash"])
def test_intake_rejects_unbound_source_before_creating_output(tmp_path, reason):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    source = (tmp_path if reason == "outside" else allowed) / "sample.txt"
    source.write_bytes(b"source evidence")
    payload = {"source_path": str(source), "source_sha256": "0" * 64}
    with pytest.raises(SourceIntakeError, match="outside|hash"):
        execute_source_intake(payload, command_id="test-intake", shell_root=tmp_path / "App", allowed_roots=[allowed])
    assert not (tmp_path / "App").exists()


def test_archive_expansion_budget_is_checked_before_parsing(tmp_path, monkeypatch):
    import io
    import zipfile
    from lightspeed_runtime import source_intake_executor as executor
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("large.txt", b"x" * 4096)
    source = tmp_path / "source.zip"
    source.write_bytes(data.getvalue())
    monkeypatch.setattr(executor, "MAX_SOURCE_BYTES", 1024)
    with pytest.raises(SourceIntakeError, match="archive exceeds"):
        execute_source_intake({"source_path": str(source), "source_sha256": hashlib.sha256(data.getvalue()).hexdigest()},
                              command_id="test-archive", shell_root=tmp_path / "App", allowed_roots=[tmp_path])


def test_filespace_candidate_is_private_source_bound_and_unpromoted(tmp_path):
    source = tmp_path / "source.csv"
    source.write_bytes(b"a,b\n1,2\n")
    payload = {"source_path": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    receipt = execute_source_intake(payload, command_id="candidate", shell_root=tmp_path / "App", allowed_roots=[tmp_path])
    assert receipt["schema"] == "lightspeed-source-intake-receipt-v2"
    candidate = json.loads(Path(receipt["artifacts"][2]["path"]).read_text())
    assert candidate["identity"]["source_sha256"] == payload["source_sha256"]
    assert candidate["identity"]["object_id"] is None
    assert candidate["security"]["visibility"] == "PRIVATE"
    assert candidate["custody"]["source_owner_verified"] is False
    assert candidate["canonical_promotion_authorized"] is False
    assert candidate["public_publish_authorized"] is False
    assert candidate["layers"]["R1_admission"] == "REQUIRES_SEPARATE_CONVERSION_PLAN"
    assert readback_source_intake(payload, command_id="candidate", shell_root=tmp_path / "App", allowed_roots=[tmp_path]) == receipt


@pytest.mark.parametrize("tamper", ["missing", "hash", "identity", "public", "promotion"])
def test_filespace_recovery_rejects_tampering_even_with_rehashed_manifest(tmp_path, tamper):
    source = tmp_path / "source.md"
    source.write_bytes(b"# Evidence\n")
    payload = {"source_path": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    receipt = execute_source_intake(payload, command_id="candidate", shell_root=tmp_path / "App", allowed_roots=[tmp_path])
    item = receipt["artifacts"][2]
    path = Path(item["path"])
    candidate = json.loads(path.read_text())
    if tamper == "missing":
        path.unlink()
    elif tamper == "hash":
        path.write_text("{}")
    else:
        if tamper == "identity":
            candidate["identity"]["object_id"] = "unapproved-object"
        elif tamper == "public":
            candidate["security"]["visibility"] = "PUBLIC_SAFE"
        else:
            candidate["canonical_promotion_authorized"] = True
        path.write_text(json.dumps(candidate))
        item["bytes"] = path.stat().st_size
        item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        Path(receipt["receipt_path"]).write_text(json.dumps(receipt))
    with pytest.raises(SourceIntakeError, match="artifact|candidate lineage"):
        readback_source_intake(payload, command_id="candidate", shell_root=tmp_path / "App", allowed_roots=[tmp_path])


def test_legacy_two_artifact_bundle_readback_does_not_backfill(tmp_path):
    source = tmp_path / "source.txt"
    source.write_bytes(b"historical source")
    payload = {"source_path": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    receipt = execute_source_intake(payload, command_id="legacy", shell_root=tmp_path / "App", allowed_roots=[tmp_path])
    Path(receipt["artifacts"].pop()["path"]).unlink()
    receipt["schema"] = "lightspeed-source-intake-receipt-v1"
    Path(receipt["receipt_path"]).write_text(json.dumps(receipt))
    before = {p.name: p.read_bytes() for p in Path(receipt["receipt_path"]).parent.iterdir()}
    assert readback_source_intake(payload, command_id="legacy", shell_root=tmp_path / "App", allowed_roots=[tmp_path]) == receipt
    assert {p.name: p.read_bytes() for p in Path(receipt["receipt_path"]).parent.iterdir()} == before
