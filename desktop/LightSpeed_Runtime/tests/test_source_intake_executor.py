import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from lightspeed_runtime.source_intake import SourceIntakeError
from lightspeed_runtime.source_intake_executor import execute_source_intake


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
