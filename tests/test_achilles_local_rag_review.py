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
        rag.infer_local(evidence, "Review", "../models/other")
