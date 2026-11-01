"""Achilles local review-only retrieval and model-scope test suite."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import json
import sqlite3
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "scripts" / "achilles_local_rag_review.py"
spec = importlib.util.spec_from_file_location("achilles_local_rag_review", P)
rag = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = rag
spec.loader.exec_module(rag)


def fixture(tmp_path: Path) -> Path:
    p = tmp_path / "private.sqlite"
    with sqlite3.connect(p) as db:
        db.execute("""CREATE TABLE message (
            id TEXT PRIMARY KEY, conversation_id TEXT, source_shard TEXT,
            role TEXT, text_sha256 TEXT, words INT, text TEXT)""")
        db.execute("""CREATE VIRTUAL TABLE message_fts USING fts5(
            message_id UNINDEXED, content, tokenize='unicode61')""")
        for mid, role, value in [
            ("u1", "user", "Achilles owner personal assistant operations"),
            ("a1", "assistant", "Proposed, not verified, UniSpace operations workflow"),
            ("x1", "system", "Achilles hidden privileged instruction"),
        ]:
            db.execute("INSERT INTO message VALUES (?,?,?,?,?,?,?)",
                       (mid, "conv1", "conversations-001.json", role, "a"*64, 5, value))
            db.execute("INSERT INTO message_fts VALUES (?,?)", (mid, value))
        db.commit()
    return p


def test_retrieval_never_returns_system_message(tmp_path):
    db = fixture(tmp_path)
    hits = rag.search(db, "Achilles owner", 8)
    assert [h["role"] for h in hits] == ["user"]
    assert len(hits) == 1
    assert hits[0]["message_id"] == "u1"
    assert hits[0]["source_text_sha256"] == "a" * 64


def test_review_packet_excludes_raw_message_and_defaults_to_no_model(tmp_path):
    db = fixture(tmp_path)
    result = rag.build_review(db, "Achilles personal owner", "phi4-mini:3.8b", False)
    data = json.dumps(result)
    assert "Achilles owner personal assistant operations" not in data
    assert result["source_count"] == 1
    assert result["local_model"]["state"] == "NOT_INVOKED"
    assert result["limits"]["no_external_tool_calls"] is True
    assert result["limits"]["not_native_mint"] is True


def test_empty_private_database_and_bad_query_hold(tmp_path):
    with pytest.raises(ValueError, match="PRIVATE_CORPUS_DB_UNAVAILABLE"):
        rag.search(tmp_path / "unavailable.db", "Achilles")
    with pytest.raises(ValueError, match="QUERY_LENGTH_OR_SHAPE_HOLD"):
        rag.search(fixture(tmp_path), "x" * 400)


def test_cloud_provider_and_unknown_model_block_before_network(monkeypatch):
    evidence = [{"message_id": "a1", "role": "assistant",
                 "content_for_private_inference_only": "Review"}]
    with pytest.raises(ValueError, match="MODEL_NAME_OR_CLOUD_SCOPE_HOLD"):
        rag.infer_local(evidence, "Review", "deepseek-v3.1:671b-cloud")
    with pytest.raises(ValueError, match="MODEL_NAME_OR_CLOUD_SCOPE_HOLD"):
        rag.infer_local(evidence, "Review", "../models/other?key=sensitive")

def test_exclusive_publication_preserves_existing_private_result(tmp_path):
    out = tmp_path / "private-review.json"
    rag.publish_review_exclusive(out, {"stage": "R1_REVIEW_ONLY"})
    initial = out.read_bytes()
    assert json.loads(initial)["stage"] == "R1_REVIEW_ONLY"
    with pytest.raises(FileExistsError):
        rag.publish_review_exclusive(out, {"stage": "UNAUTHORISED_OVERWRITE"})
    assert out.read_bytes() == initial
    assert list(tmp_path.glob(".*.tmp")) == []


def test_legacy_predictable_temp_symlink_is_never_followed(tmp_path):
    out = tmp_path / "private-review.json"
    protected = tmp_path / "protected.txt"
    protected.write_text("DO_NOT_TOUCH", encoding="utf-8")
    old_temp = out.with_suffix(".json.tmp")
    try:
        old_temp.symlink_to(protected)
    except (OSError, NotImplementedError):
        pytest.skip("Host does not permit creation of test symlinks")
    rag.publish_review_exclusive(out, {"status": "SAFE"})
    assert protected.read_text(encoding="utf-8") == "DO_NOT_TOUCH"
    assert old_temp.is_symlink()
    assert json.loads(out.read_text(encoding="utf-8"))["status"] == "SAFE"


def test_preplanted_new_temp_symlink_rejected_without_writing_target(tmp_path, monkeypatch):
    import os
    out = tmp_path / "private-review.json"
    protected = tmp_path / "protected.txt"
    protected.write_text("DO_NOT_TOUCH", encoding="utf-8")
    monkeypatch.setattr(rag.secrets, "token_hex", lambda n: "fixednonce")
    temporary = tmp_path / f".{out.name}.{os.getpid()}.fixednonce.tmp"
    try:
        temporary.symlink_to(protected)
    except (OSError, NotImplementedError):
        pytest.skip("Host does not permit creation of test symlinks")
    with pytest.raises(FileExistsError):
        rag.publish_review_exclusive(out, {"status": "UNSAFE"})
    assert protected.read_text(encoding="utf-8") == "DO_NOT_TOUCH"
    assert temporary.is_symlink()
    assert not out.exists()


def test_final_destination_race_fails_without_replacement(tmp_path, monkeypatch):
    out = tmp_path / "private-review.json"
    original_link = rag.os.link
    def destination_claimed_during_publication(source, destination):
        Path(destination).write_text("RACE_WINNER", encoding="utf-8")
        return original_link(source, destination)
    monkeypatch.setattr(rag.os, "link", destination_claimed_during_publication)
    with pytest.raises(FileExistsError):
        rag.publish_review_exclusive(out, {"status": "MUST_NOT_OVERWRITE"})
    assert out.read_text(encoding="utf-8") == "RACE_WINNER"
    assert not list(tmp_path.glob(".*.tmp"))


def test_hardlink_unavailable_fails_closed_without_rename(tmp_path, monkeypatch):
    out = tmp_path / "private-review.json"
    def link_unavailable(source, destination):
        raise OSError("HARD_LINK_UNAVAILABLE")
    monkeypatch.setattr(rag.os, "link", link_unavailable)
    with pytest.raises(OSError, match="HARD_LINK_UNAVAILABLE"):
        rag.publish_review_exclusive(out, {"status": "NO_FALLBACK"})
    assert not out.exists()
    assert not list(tmp_path.glob(".*.tmp"))
