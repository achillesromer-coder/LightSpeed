from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from lightspeed_runtime.source_intake import SourceIntakeError
from lightspeed_runtime.source_intake_remote import reconcile_drive_source
from lightspeed_runtime.source_intake_remote import reconcile_drive_batch


def test_reuse_is_byte_verified_and_credential_free(tmp_path):
    p = tmp_path / "source.dat"
    p.write_bytes(b"a,b\n1,2\n")
    result = reconcile_drive_source(metadata={"id": "drive-id", "size": "8", "download_url": "SECRET"},
        downloaded=p.read_bytes(), local_source=p, allowed_roots=[tmp_path], declared_source_name="source.csv")
    assert result["status"] == "EXACT_BYTES_REUSED"
    assert result["intake_payload"]["declared_source_name"] == "source.csv"
    assert "SECRET" not in str(result)
    assert result["provider_revision"] is None
    assert not result["deletion_eligible"] and not result["queue_dispatched"]


@pytest.mark.parametrize("case", ["changed", "size", "identity", "outside", "path_alias"])
def test_unsafe_reconciliation_is_rejected(tmp_path, case):
    p = tmp_path / "source.dat"
    p.write_bytes(b"AB")
    scope = tmp_path / "scope"
    scope.mkdir()
    args = dict(metadata={"id": "drive-id", "size": "2"}, downloaded=b"AB",
                local_source=p, allowed_roots=[tmp_path])
    if case == "changed": args["downloaded"] = b"CD"
    if case == "size": args["metadata"]["size"] = "3"
    if case == "identity": args["metadata"]["id"] = "../drive-id"
    if case == "outside": args["allowed_roots"] = [scope]
    if case == "path_alias": args["declared_source_name"] = "../payload.csv"
    with pytest.raises(SourceIntakeError):
        reconcile_drive_source(**args)
    assert p.read_bytes() == b"AB"


def test_batch_preserves_failure_and_duplicate_without_dispatch(tmp_path):
    p = tmp_path / "source.dat"
    p.write_bytes(b"AB")
    good = {"metadata": {"id": "drive-id", "size": "2"}, "downloaded": b"AB", "local_source": p}
    bad = {**good, "downloaded": b"CD"}
    result = reconcile_drive_batch([good, bad, good], allowed_roots=[tmp_path])
    assert [r["status"] for r in result["results"]] == ["REVIEW_CANDIDATE", "RECONCILIATION_REQUIRED", "DUPLICATE_IN_BATCH"]
    assert not result["queue_dispatched"] and not result["deletion_eligible"]
    assert result["results"][1] == {"index": 1, "status": "RECONCILIATION_REQUIRED"}


@pytest.mark.parametrize("items", [[], [{}] * 17, [{"downloaded": "not bytes"}]])
def test_batch_rejects_unbounded_or_unfetched_input(tmp_path, items):
    with pytest.raises(SourceIntakeError):
        reconcile_drive_batch(items, allowed_roots=[tmp_path])


def test_batch_enforces_total_byte_budget(tmp_path, monkeypatch):
    monkeypatch.setattr("lightspeed_runtime.source_intake_remote.MAX_SOURCE_BYTES", 3)
    with pytest.raises(SourceIntakeError, match="byte budget"):
        reconcile_drive_batch([{"downloaded": b"AB"}, {"downloaded": b"CD"}], allowed_roots=[tmp_path])


def test_batch_records_malformed_metadata_as_failure(tmp_path):
    result = reconcile_drive_batch([{"downloaded": b"AB", "metadata": []}], allowed_roots=[tmp_path])
    assert result["results"] == [{"index": 0, "status": "RECONCILIATION_REQUIRED"}]
