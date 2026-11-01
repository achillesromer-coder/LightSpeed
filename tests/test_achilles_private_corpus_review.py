from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "achilles_private_corpus_review.py"
spec = importlib.util.spec_from_file_location("achilles_private_corpus_review", PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def sample(tmp_path: Path):
    mapping = {
        "u-node": {"message": {
            "id": "u-1", "author": {"role": "user"},
            "content": {"content_type": "text", "parts": ["Owner only private instruction"]},
            "create_time": 1.0,
        }, "parent": None},
        "a-node": {"message": {
            "id": "a-1", "author": {"role": "assistant"},
            "content": {"content_type": "text", "parts": ["Bounded source review, not release"]},
            "create_time": 2.0,
        }, "parent": "u-node"},
        "hidden-node": {"message": {
            "id": "hidden", "author": {"role": "assistant"},
            "metadata": {"channel": "analysis"},
            "content": {"parts": ["HIDDEN_DO_NOT_INDEX"]},
        }, "parent": "u-node"},
        "system-node": {"message": {
            "id": "sys-1", "author": {"role": "system"},
            "content": {"parts": ["INTERNAL_SYSTEM_INSTRUCTION"]},
        }, "parent": None},
    }
    source = tmp_path / "conversations-011.json"
    source.write_text(json.dumps([{
        "id": "conversation-a", "title": "Achilles local review",
        "mapping": mapping, "create_time": 1.0, "update_time": 2.0
    }]), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    return source, entry


def test_private_r1_honours_user_assistant_roles_and_branch_parent(tmp_path):
    source, entry = sample(tmp_path)
    con = mod.connect(tmp_path / "review.sqlite")
    try:
        assert mod.ingest_shard(con, source, entry)[0] == 1
        result = mod.summary(con)
        assert result["shards"] == 1
        assert result["unique_messages"] == 2
        assert result["prompt_response_links"] == 1
        assert result["model_weights_modified"] is False
        assert result["native_admission"] is False
        assert con.execute("SELECT count(*) FROM message_fts WHERE content MATCH 'HIDDEN_DO_NOT_INDEX'").fetchone()[0] == 0
        assert mod.ingest_shard(con, source, entry)[0] == -1
    finally:
        con.close()


def test_file_hash_and_symlink_boundaries_fail_closed(tmp_path):
    source, entry = sample(tmp_path)
    mod.verify_source(source, entry)
    changed = dict(entry, sha256="a" * 64)
    with pytest.raises(ValueError, match="SOURCE_SHA256_MISMATCH"):
        mod.verify_source(source, changed)
    entry_wrong_length = dict(entry, size_bytes=entry["size_bytes"] + 1)
    with pytest.raises(ValueError, match="SOURCE_FILE_IDENTITY_HOLD"):
        mod.verify_source(source, entry_wrong_length)


def test_payload_tamper_fails_without_overwriting_committed_state(tmp_path):
    source, entry = sample(tmp_path)
    con = mod.connect(tmp_path / "review.sqlite")
    try:
        mod.ingest_shard(con, source, entry)
        source.write_text(source.read_text().replace("Owner only", "Changed text"), encoding="utf-8")
        with pytest.raises(ValueError, match="SOURCE_SHA256_MISMATCH"):
            mod.ingest_shard(con, source, entry)
        assert mod.summary(con)["shards"] == 1
        assert mod.summary(con)["unique_messages"] == 2
    finally:
        con.close()


def test_receipt_needs_twelve_distinct_size_hash_bound_sources(tmp_path):
    entries = [{"shard": f"conversations-{n:03d}.json",
                "size_bytes": 10, "sha256": "a" * 64} for n in range(12)]
    p = tmp_path / "receipt.json"
    p.write_text(json.dumps({"schema": "CGX-OWNER-GPT-EXPORT-SHARD-RECEIPT/0.1",
                             "shards": entries, "total_bytes": 120}), encoding="utf-8")
    assert len(mod.qualified_receipt(p)) == 12
    entries[7]["shard"] = "../escape.json"
    p.write_text(json.dumps({"schema": "CGX-OWNER-GPT-EXPORT-SHARD-RECEIPT/0.1",
                             "shards": entries, "total_bytes": 120}), encoding="utf-8")
    with pytest.raises(ValueError, match="SOURCE_IDENTITY_HOLD"):
        mod.qualified_receipt(p)


def test_preflight_does_not_create_database(tmp_path):
    source_root = tmp_path / "raw"
    source_root.mkdir()
    target = tmp_path / "private"
    target.mkdir()
    entries = [{"shard": f"conversations-{n:03d}.json",
                "size_bytes": 10, "sha256": "a" * 64} for n in range(12)]
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"schema": "CGX-OWNER-GPT-EXPORT-SHARD-RECEIPT/0.1",
                                   "shards": entries, "total_bytes": 120}))
    parser_args = type("A", (), {"shards_dir": source_root, "receipt": receipt,
                                 "private_dir": target, "preflight_only": True,
                                 "serve": False, "max_shards": 0, "port": 8767})
    assert mod.run(parser_args) == 0
    assert not (target / "semantic_review.sqlite").exists()
