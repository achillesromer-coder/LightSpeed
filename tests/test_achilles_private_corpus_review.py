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
        source.write_text(source.read_text().replace("Owner only", "Owner else"), encoding="utf-8")
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


def test_r1_parsed_snapshot_must_match_verified_bytes(tmp_path, monkeypatch):
    source, entry = sample(tmp_path)
    original = mod.verify_source

    def change_between_verification_and_parse(path, identity):
        verified = original(path, identity)
        # Simulate an external sync replacing the file after its first hash pass.
        path.write_text(path.read_text(encoding="utf-8").replace(
            "Owner only private instruction", "Altered owner private instruction"
        ), encoding="utf-8")
        return verified

    monkeypatch.setattr(mod, "verify_source", change_between_verification_and_parse)
    con = mod.connect(tmp_path / "new_review.sqlite")
    try:
        with pytest.raises(ValueError, match="SOURCE_SNAPSHOT_CHANGED_DURING_READ_HOLD"):
            mod.ingest_shard(con, source, entry)
        assert con.execute("SELECT count(*) FROM shard").fetchone()[0] == 0
        assert con.execute("SELECT count(*) FROM message").fetchone()[0] == 0
    finally:
        con.close()


def test_duplicate_conversation_variant_is_preserved_by_original_shard(tmp_path):
    first, original_identity = sample(tmp_path)
    second = tmp_path / "conversations-010.json"
    original_conv = json.loads(first.read_text(encoding="utf-8"))[0]
    changed = dict(original_conv)
    changed["title"] = "Achilles source metadata update"
    changed["update_time"] = 4.0
    second.write_text(json.dumps([changed]), encoding="utf-8")
    later_identity = {
        "shard": second.name,
        "sha256": hashlib.sha256(second.read_bytes()).hexdigest(),
        "size_bytes": second.stat().st_size,
    }
    con = mod.connect(tmp_path / "new_review.sqlite")
    try:
        mod.ingest_shard(con, first, original_identity)
        mod.ingest_shard(con, second, later_identity)
        variants = con.execute("""
            SELECT shard,conversation_id,title,updated,source_visible_words,metadata_sha256
            FROM conversation_variant WHERE conversation_id='conversation-a'
            ORDER BY shard
        """).fetchall()
        assert len(variants) == 2
        assert {v[0] for v in variants} == {
            first.name, second.name
        }
        assert all(v[4] > 0 and len(v[5]) == 64 for v in variants)
        assert con.execute("SELECT title FROM conversation WHERE id='conversation-a'").fetchone()[0] == "Achilles local review"
        assert con.execute("SELECT count(*) FROM message").fetchone()[0] == 2
        assert con.execute(
            "SELECT count(*) FROM source_issue WHERE kind='CONVERSATION_METADATA_VARIANT'"
        ).fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM shard").fetchone()[0] == 2
    finally:
        con.close()


def test_chunked_reader_handles_shard_larger_than_individual_record_bound(tmp_path):
    records = [{"id": f"conversation-{i}", "title": "private", "mapping": {}}
               for i in range(40)]
    p = tmp_path / "conversations-008.json"
    p.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    receipt = {"shard": p.name, "size_bytes": p.stat().st_size,
               "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    assert receipt["size_bytes"] > 1024
    rows = list(mod.iter_source_conversations(
        p, receipt, max_record_bytes=1024, chunk_bytes=97))
    assert len(rows) == 40
    assert rows[0]["id"] == "conversation-0"
    assert rows[-1]["id"] == "conversation-39"


def test_chunked_reader_rejects_oversized_record(tmp_path):
    p = tmp_path / "conversations-008.json"
    p.write_text(json.dumps([{"id": "one", "padding": "a" * 3000}]),
                 encoding="utf-8")
    receipt = {"shard": p.name, "size_bytes": p.stat().st_size,
               "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    with pytest.raises(ValueError, match="SOURCE_RECORD_EXCEEDS_60MIB_HOLD"):
        list(mod.iter_source_conversations(
            p, receipt, max_record_bytes=512, chunk_bytes=64))


@pytest.mark.parametrize("payload", [
    '[{"id":"a"},]',
    '[{"id":"a"}]{"outside":true}',
    '[{"id":"a"}, {"id":"b"}',
    '[NaN]',
])
def test_chunked_reader_fails_closed_on_bad_json(tmp_path, payload):
    p = tmp_path / "conversations-008.json"
    p.write_text(payload, encoding="utf-8")
    receipt = {"shard": p.name, "size_bytes": p.stat().st_size,
               "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    with pytest.raises(ValueError):
        list(mod.iter_source_conversations(
            p, receipt, max_record_bytes=512, chunk_bytes=64))


def test_chunked_reader_preserves_unicode_variants_and_occurrences(tmp_path):
    p = tmp_path / "conversations-008.json"
    conv = {"id": "one", "title": "private", "mapping": {
        "first": {"message": {"id": "same", "author": {"role": "user"},
                              "content": {"parts": ["🧩 alpha"]}}},
        "second": {"message": {"id": "same", "author": {"role": "user"},
                               "content": {"parts": ["🧩 alpha"]}}},
    }}
    p.write_text(json.dumps([conv, conv], ensure_ascii=False), encoding="utf-8")
    receipt = {"shard": p.name, "size_bytes": p.stat().st_size,
               "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    db = mod.connect(tmp_path / "review.sqlite")
    try:
        assert mod.ingest_shard(db, p, receipt)[0] == 2
        assert db.execute("SELECT count(*) FROM conversation_variant").fetchone()[0] == 2
        assert db.execute("SELECT count(*) FROM occurrence").fetchone()[0] == 2
        assert db.execute("SELECT count(*) FROM message").fetchone()[0] == 1
        assert mod.summary(db)["native_admission"] is False
    finally:
        db.close()


def test_chunked_reader_second_pass_digest_mismatch_rolls_back(tmp_path, monkeypatch):
    source, receipt = sample(tmp_path)
    original = mod.verify_source
    def change_after_hash(path, identity):
        digest = original(path, identity)
        path.write_text(path.read_text().replace("Owner only", "Other words"), encoding="utf-8")
        return digest
    monkeypatch.setattr(mod, "verify_source", change_after_hash)
    db = mod.connect(tmp_path / "review.sqlite")
    try:
        with pytest.raises(ValueError, match="SOURCE_SNAPSHOT_CHANGED_DURING_READ_HOLD"):
            mod.ingest_shard(db, source, receipt)
        assert db.execute("SELECT count(*) FROM shard").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM message").fetchone()[0] == 0
    finally:
        db.close()
