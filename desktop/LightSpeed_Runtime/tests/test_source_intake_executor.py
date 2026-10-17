import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from lightspeed_runtime.source_intake import SourceIntakeError
from lightspeed_runtime.source_intake_executor import execute_source_intake, verify_source_intake_readback
from lightspeed_runtime.storage_paths import neo_actions_root


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
    with pytest.raises(SourceIntakeError, match="already exist"):
        execute_source_intake(payload, command_id="test-intake", shell_root=tmp_path / "App", allowed_roots=[tmp_path])


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


def test_intake_stops_when_claim_is_revoked_during_source_read(tmp_path):
    source = tmp_path / "source.bin"
    raw = b"x" * (2 * 1024 * 1024)
    source.write_bytes(raw)
    checks = 0

    def check_active():
        nonlocal checks
        checks += 1
        if checks == 3:
            raise RuntimeError("claim revoked")

    with pytest.raises(RuntimeError, match="claim revoked"):
        execute_source_intake(
            {"source_path": str(source), "source_sha256": hashlib.sha256(raw).hexdigest()},
            command_id="cancelled-intake", shell_root=tmp_path / "App",
            allowed_roots=[tmp_path], check_active=check_active,
        )
    assert source.read_bytes() == raw
    assert not (tmp_path / "App").exists()


def test_intake_does_not_publish_when_claim_is_revoked_during_write(tmp_path):
    source = tmp_path / "source.txt"
    raw = b"evidence\n" * 240000
    source.write_bytes(raw)
    checks = 0

    def check_active():
        nonlocal checks
        checks += 1
        # Permit source read, envelope generation, and the first output chunk.
        if checks == 9:
            raise RuntimeError("claim revoked")

    command_id = "cancelled-during-write"
    shell = tmp_path / "App"
    with pytest.raises(RuntimeError, match="claim revoked"):
        execute_source_intake(
            {"source_path": str(source), "source_sha256": hashlib.sha256(raw).hexdigest()},
            command_id=command_id, shell_root=shell,
            allowed_roots=[tmp_path], check_active=check_active,
        )
    destination = neo_actions_root(shell) / "intake" / hashlib.sha256(command_id.encode()).hexdigest()
    assert not destination.exists()
    assert source.read_bytes() == raw


def test_frontier_intake_records_deterministic_prepublish_use(tmp_path):
    source = tmp_path / "source.txt"
    raw = b"bounded original\n"
    source.write_bytes(raw)
    receipt = execute_source_intake(
        {"source_path": str(source), "source_sha256": hashlib.sha256(raw).hexdigest()},
        command_id="metered-intake", shell_root=tmp_path / "App",
        allowed_roots=[tmp_path], frontier_budget={
            "max_elapsed_s": 10, "max_tokens": 1,
            "max_tool_calls": 1, "max_retries": 0, "max_cost_usd": 1,
        },
    )
    usage = receipt["frontier_usage"]
    assert 0 <= usage["prepublish_elapsed_ms"] < 10_000
    assert {key: usage[key] for key in ("tokens", "tool_calls", "retries", "cost_usd")} == {
        "tokens": 0, "tool_calls": 1, "retries": 0, "cost_usd": 0,
    }
    assert usage["wall_clock_enforcement"] == "cooperative_checkpoints_before_publish"
    assert source.read_bytes() == raw
    assert json.loads(Path(receipt["receipt_path"]).read_text())["frontier_usage"] == usage


def test_frontier_intake_elapsed_ceiling_blocks_publication_after_extraction(tmp_path, monkeypatch):
    from lightspeed_runtime import source_intake_executor as executor
    source = tmp_path / "source.txt"
    raw = b"original evidence\n"
    source.write_bytes(raw)
    now = [0]
    original_build = executor.build_source_envelope

    def elapsed_build(**kwargs):
        result = original_build(**kwargs)
        now[0] = 1_000_000_000
        return result

    monkeypatch.setattr(executor.time, "monotonic_ns", lambda: now[0])
    monkeypatch.setattr(executor, "build_source_envelope", elapsed_build)
    command_id = "elapsed-intake"
    shell = tmp_path / "App"
    with pytest.raises(SourceIntakeError, match="wall-clock ceiling"):
        execute_source_intake(
            {"source_path": str(source), "source_sha256": hashlib.sha256(raw).hexdigest()},
            command_id=command_id, shell_root=shell, allowed_roots=[tmp_path],
            frontier_budget={"max_elapsed_s": 1, "max_tokens": 1,
                             "max_tool_calls": 1, "max_retries": 0},
        )
    destination = neo_actions_root(shell) / "intake" / hashlib.sha256(command_id.encode()).hexdigest()
    assert not destination.exists()
    assert source.read_bytes() == raw


@pytest.mark.parametrize("tamper", ["native_bytes", "envelope_bytes", "receipt_bytes", "receipt_claim"])
def test_published_intake_detects_postpublish_tampering(tmp_path, tamper):
    """Terminal completion is conditional on immutable exact-byte readback, not a cached success."""
    source = tmp_path / "original-source.csv"
    raw = b"part,dimension_mm\\nA,12\\n"
    source.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    command_id = "signed-intake-verification"
    shell = tmp_path / "App"
    receipt = execute_source_intake(
        {"source_path": str(source), "source_sha256": digest},
        command_id=command_id, shell_root=shell, allowed_roots=[tmp_path],
    )
    verify_source_intake_readback(
        receipt, command_id=command_id, shell_root=shell, source_sha256=digest,
    )
    original = json.loads(json.dumps(receipt))
    if tamper == "native_bytes":
        target = Path(receipt["artifacts"][0]["path"])
        data = target.read_bytes()
        target.write_bytes(b"X" + data[1:])
    elif tamper == "envelope_bytes":
        target = Path(receipt["artifacts"][1]["path"])
        data = target.read_bytes()
        target.write_bytes(b"X" + data[1:])
    elif tamper == "receipt_bytes":
        target = Path(receipt["receipt_path"])
        stored = json.loads(target.read_text(encoding="utf-8"))
        stored["canonical_mutation"] = True
        target.write_text(json.dumps(stored), encoding="utf-8")
    else:
        receipt["artifacts"][0]["bytes"] += 1
    with pytest.raises(SourceIntakeError, match="artifact|receipt|identity|hash"):
        verify_source_intake_readback(
            receipt, command_id=command_id, shell_root=shell, source_sha256=digest,
        )
    assert source.read_bytes() == raw
    assert original["canonical_mutation"] is False
    assert original["semantic_acceptance"] == "requires_independent_review"


def test_generic_intake_holds_multimember_cgx_carrier_for_specialist(tmp_path):
    """A large .cgx ZIP carrier cannot silently bypass the generic 256-member gate."""
    import zipfile

    original = tmp_path / "archived-carrier.cgx"
    with zipfile.ZipFile(original, "w", compression=zipfile.ZIP_STORED) as archive:
        for index in range(257):
            archive.writestr(f"cgx/fixtures/object-{index:03d}.json", "{}")
    raw = original.read_bytes()
    with pytest.raises(SourceIntakeError, match="archive exceeds bounded extraction budget"):
        execute_source_intake(
            {"source_path": str(original), "source_sha256": hashlib.sha256(raw).hexdigest()},
            command_id="hold-large-cgx-carrier", shell_root=tmp_path / "App",
            allowed_roots=[tmp_path],
        )
    assert original.read_bytes() == raw
    assert not (tmp_path / "App").exists()
