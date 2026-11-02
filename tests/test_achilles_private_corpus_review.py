from __future__ import annotations

import importlib.util
import hashlib
import json
import os
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



def test_atomic_json_does_not_follow_preplanted_predictable_tmp_symlink(tmp_path):
    """A prior progress.json.tmp alias must not overwrite an outside sentinel."""
    dest = tmp_path / "progress.json"
    sentinel = tmp_path / "external.txt"
    sentinel.write_text("DO_NOT_CHANGE", encoding="utf-8")
    planted = tmp_path / "progress.json.tmp"
    try:
        planted.symlink_to(sentinel)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable on this filesystem: {exc}")
    mod.atomic_json(dest, {"state": "REVIEW_ONLY"})
    assert sentinel.read_text(encoding="utf-8") == "DO_NOT_CHANGE"
    assert planted.is_symlink()
    assert json.loads(dest.read_text(encoding="utf-8")) == {"state": "REVIEW_ONLY"}
    assert not list(tmp_path.glob(".progress.json.*.tmp"))


def test_atomic_json_replaces_existing_receipt_without_stale_tmp(tmp_path):
    dest = tmp_path / "summary.json"
    dest.write_text('{"state":"OLD"}', encoding="utf-8")
    mod.atomic_json(dest, {"state": "REVIEW_ONLY"})
    assert json.loads(dest.read_text(encoding="utf-8")) == {"state": "REVIEW_ONLY"}
    assert not (tmp_path / "summary.json.tmp").exists()
    assert not list(tmp_path.glob(".summary.json.*.tmp"))


@pytest.mark.parametrize("alias_kind", ["symlink", "hardlink"])
def test_private_loopback_shortcut_never_follows_planted_output_alias(tmp_path, alias_kind):
    """The loopback bearer-token shortcut must not overwrite an outside file."""
    shortcut = tmp_path / "Open Achilles source progress.url"
    sentinel = tmp_path / "outside_sentinel.txt"
    sentinel.write_text("DO_NOT_CHANGE", encoding="utf-8")
    try:
        if alias_kind == "symlink":
            shortcut.symlink_to(sentinel)
        else:
            os.link(sentinel, shortcut)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"{alias_kind} creation unavailable: {exc}")
    expected = "[InternetShortcut]\nURL=http://127.0.0.1:8767/t/TEST_ONLY\n"
    mod.atomic_text(shortcut, expected)
    assert sentinel.read_text(encoding="utf-8") == "DO_NOT_CHANGE"
    assert shortcut.read_text(encoding="utf-8") == expected
    assert not shortcut.is_symlink()
    assert not list(tmp_path.glob(".Open Achilles source progress.url.*.tmp"))


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


@pytest.mark.parametrize("level", ["root", "nested"])
def test_receipt_duplicate_json_keys_fail_before_source_identity_acceptance(tmp_path, level):
    """Even identical/shadowed R0 receipt keys must never be silently discarded."""
    entries = [{"shard": f"conversations-{n:03d}.json",
                "size_bytes": 10, "sha256": "a" * 64} for n in range(12)]
    original = json.dumps({"schema": "CGX-OWNER-GPT-EXPORT-SHARD-RECEIPT/0.1",
                           "shards": entries, "total_bytes": 120})
    if level == "root":
        altered = original.replace('"total_bytes": 120',
                                   '"total_bytes": 120, "total_bytes": 120', 1)
    else:
        altered = original.replace('"size_bytes": 10',
                                   '"size_bytes": 10, "size_bytes": 11', 1)
    assert altered != original
    p = tmp_path / "receipt.json"
    p.write_text(altered, encoding="utf-8")
    with pytest.raises(ValueError, match="SOURCE_RECEIPT_DUPLICATE_KEY_HOLD"):
        mod.qualified_receipt(p)


@pytest.mark.parametrize("source_parts,target_parts", [
    (("raw",), ("raw", "private_output")),
    (("private_output", "raw"), ("private_output",)),
])
def test_preflight_rejects_source_output_ancestor_overlap(tmp_path, source_parts, target_parts):
    """Both nesting directions are unsafe even before an SQLite DB exists."""
    source_root = tmp_path.joinpath(*source_parts)
    target = tmp_path.joinpath(*target_parts)
    source_root.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    receipt = tmp_path / "shard_receipt.json"
    receipt.write_text("{}", encoding="utf-8")
    args = type("A", (), {"shards_dir": source_root, "receipt": receipt,
                          "private_dir": target, "preflight_only": True,
                          "serve": False, "max_shards": 0, "port": 8767})
    with pytest.raises(ValueError, match="SOURCE_OR_OUTPUT_PATH_HOLD"):
        mod.run(args)
    assert not (target / "semantic_review.sqlite").exists()


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


@pytest.mark.parametrize("payload", [
    '[{"id":"a","title":"first","title":"second","mapping":{}}]',
    '[{"id":"a","mapping":{"node":{"message":{"id":"m1"}},"node":{"message":{"id":"m2"}}}}]',
    '[{"id":"a","mapping":{"node":{"parent":"p1","parent":"p2"}}}]',
])
def test_chunked_reader_rejects_duplicate_object_keys(tmp_path, payload):
    """Source key collisions must not silently discard original R0 values."""
    p = tmp_path / "conversations-011.json"
    p.write_text(payload, encoding="utf-8")
    receipt = {"shard": p.name, "size_bytes": p.stat().st_size,
               "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    with pytest.raises(ValueError, match="SOURCE_DUPLICATE_JSON_KEY_HOLD"):
        list(mod.iter_source_conversations(
            p, receipt, max_record_bytes=1024, chunk_bytes=17))


def test_chunked_reader_allows_equal_values_under_distinct_keys(tmp_path):
    p = tmp_path / "conversations-011.json"
    p.write_text('[{"id":"a","title":"same","description":"same","mapping":{}}]',
                 encoding="utf-8")
    receipt = {"shard": p.name, "size_bytes": p.stat().st_size,
               "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    rows = list(mod.iter_source_conversations(
        p, receipt, max_record_bytes=1024, chunk_bytes=17))
    assert len(rows) == 1
    assert rows[0]["title"] == rows[0]["description"] == "same"


def test_repeated_conversation_source_visible_occurrence_ledger(tmp_path):
    """Repeated node IDs in one shard retain every visible source occurrence."""
    source, entry = sample(tmp_path)
    first = json.loads(source.read_text(encoding="utf-8"))[0]
    second = json.loads(json.dumps(first))
    second["title"] = "Second source occurrence, not an identity merge"
    second["mapping"]["u-node"]["message"]["id"] = "u-variant"
    second["mapping"]["u-node"]["message"]["create_time"] = 9.0
    source.write_text(json.dumps([first, second]), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    db = mod.connect(tmp_path / "new_private_review.sqlite")
    try:
        assert mod.ingest_shard(db, source, entry)[0] == 2
        rows = db.execute("""
            SELECT conversation_index,node_ordinal,node_id,message_id,created
            FROM source_visible_occurrence
            ORDER BY conversation_index,node_ordinal
        """).fetchall()
        assert len(rows) == 4
        assert [row[0] for row in rows] == [0, 0, 1, 1]
        assert [row[2] for row in rows] == ["u-node", "a-node", "u-node", "a-node"]
        assert rows[0][3] == "u-1" and rows[2][3] == "u-variant"
        assert rows[0][4] == 1.0 and rows[2][4] == 9.0
        assert db.execute("SELECT count(*) FROM occurrence").fetchone()[0] == 2
        assert db.execute("SELECT count(*) FROM conversation_variant").fetchone()[0] == 2
        assert db.execute("SELECT count(*) FROM message").fetchone()[0] == 3
        assert mod.summary(db)["native_admission"] is False
    finally:
        db.close()


def test_source_prompt_ancestry_preserves_repeated_response_branch_variants(tmp_path):
    """Same response ID/text may have distinct source-local prompt ancestry."""
    source, _ = sample(tmp_path)
    first = json.loads(source.read_text(encoding="utf-8"))[0]
    second = json.loads(json.dumps(first))
    second["mapping"]["u-node"]["message"]["id"] = "u-second"
    second["mapping"]["a-node"]["message"]["create_time"] = 3.0
    source.write_text(json.dumps([first, second]), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    db = mod.connect(tmp_path / "private_ancestry.sqlite")
    try:
        assert mod.ingest_shard(db, source, entry)[0] == 2
        ancestry = db.execute("""
            SELECT conversation_index,response_node_id,response_message_id,
                   prompt_node_id,prompt_message_id,ancestor_hops,source_parent_node
            FROM source_prompt_response_occurrence
            ORDER BY conversation_index
        """).fetchall()
        assert ancestry == [
            (0, "a-node", "a-1", "u-node", "u-1", 1, "u-node"),
            (1, "a-node", "a-1", "u-node", "u-second", 1, "u-node"),
        ]
        assert db.execute(
            "SELECT prompt_id FROM prompt_response WHERE response_id='a-1'"
        ).fetchone()[0] == "u-1"  # legacy first-seen projection only
        assert db.execute("SELECT sha256 FROM shard").fetchone()[0] == entry["sha256"]
        assert mod.summary(db)["native_admission"] is False
    finally:
        db.close()


def test_source_prompt_ancestry_excludes_hidden_user_source(tmp_path):
    source, _ = sample(tmp_path)
    original = json.loads(source.read_text(encoding="utf-8"))
    original[0]["mapping"]["u-node"]["message"]["metadata"] = {"channel": "analysis"}
    source.write_text(json.dumps(original), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    db = mod.connect(tmp_path / "hidden_ancestry.sqlite")
    try:
        assert mod.ingest_shard(db, source, entry)[0] == 1
        assert db.execute(
            "SELECT count(*) FROM source_prompt_response_occurrence"
        ).fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM prompt_response").fetchone()[0] == 0
        assert mod.summary(db)["native_admission"] is False
    finally:
        db.close()


def test_reused_message_id_metadata_variant_is_flagged_before_r2(tmp_path):
    """Same text and ID do not certify equal source time, parent or channel."""
    source, _ = sample(tmp_path)
    first = json.loads(source.read_text(encoding="utf-8"))[0]
    second = json.loads(json.dumps(first))
    second["mapping"]["u-node"]["message"]["create_time"] = 9.0
    second["mapping"]["u-node"]["message"]["metadata"] = {"channel": "final"}
    second["mapping"]["u-node"]["parent"] = "unresolved-external-parent"
    source.write_text(json.dumps([first, second]), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    db = mod.connect(tmp_path / "new_private_review.sqlite")
    try:
        assert mod.ingest_shard(db, source, entry)[0] == 2
        rows = db.execute("""
            SELECT conversation_index,message_id,created,channel,parent_node
            FROM source_visible_occurrence
            WHERE node_id='u-node' ORDER BY conversation_index
        """).fetchall()
        assert rows == [
            (0, "u-1", 1.0, "", None),
            (1, "u-1", 9.0, "final", "unresolved-external-parent"),
        ]
        assert db.execute(
            "SELECT count(*) FROM source_issue "
            "WHERE kind='MESSAGE_ID_METADATA_VARIANT' AND source_id='u-1'"
        ).fetchone()[0] == 1
        assert db.execute("SELECT created FROM message WHERE id='u-1'").fetchone()[0] == 1.0
        assert mod.summary(db)["native_admission"] is False
    finally:
        db.close()


@pytest.mark.parametrize("numeric", ["1e999", "-1e999", "1.0e10000"])
def test_streaming_rejects_nonfinite_json_number_without_partial_commit(tmp_path, numeric):
    """Valid JSON exponent syntax must not become infinite R1 time metadata."""
    source = tmp_path / "conversations-011.json"
    source.write_text('[{"id":"c","create_time":' + numeric +
                      ',"mapping":{"n":{"message":{"id":"m","author":{"role":"user"},' +
                      '"content":{"parts":["source only"]}}}}}]', encoding="utf-8")
    entry = {"shard": source.name, "size_bytes": source.stat().st_size,
             "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    with pytest.raises(ValueError, match="SOURCE_NONFINITE_JSON_NUMBER_HOLD"):
        list(mod.iter_source_conversations(source, entry, chunk_bytes=7))
    con = mod.connect(tmp_path / "review.sqlite")
    try:
        with pytest.raises(ValueError, match="SOURCE_NONFINITE_JSON_NUMBER_HOLD"):
            mod.ingest_shard(con, source, entry)
        assert con.execute("SELECT count(*) FROM shard").fetchone()[0] == 0
        assert con.execute("SELECT count(*) FROM message").fetchone()[0] == 0
        assert mod.summary(con)["native_admission"] is False
    finally:
        con.close()


@pytest.mark.parametrize("numeric", ["1e-999", "-1e-999", "1e-324"])
def test_streaming_rejects_nonzero_json_decimal_underflow(tmp_path, numeric):
    """Nonzero source numbers must not silently become zero in R1 metadata."""
    source = tmp_path / "conversations-011.json"
    source.write_text('[{"id":"c","create_time":' + numeric +
                      ',"mapping":{"n":{"message":{"id":"m","author":{"role":"user"},' +
                      '"content":{"parts":["synthetic review"]}}}}}]', encoding="utf-8")
    entry = {"shard": source.name, "size_bytes": source.stat().st_size,
             "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    with pytest.raises(ValueError, match="SOURCE_FLOAT_UNDERFLOW_HOLD"):
        list(mod.iter_source_conversations(source, entry, chunk_bytes=7))
    con = mod.connect(tmp_path / "review.sqlite")
    try:
        with pytest.raises(ValueError, match="SOURCE_FLOAT_UNDERFLOW_HOLD"):
            mod.ingest_shard(con, source, entry)
        assert con.execute("SELECT count(*) FROM shard").fetchone()[0] == 0
        assert con.execute("SELECT count(*) FROM message").fetchone()[0] == 0
        assert mod.summary(con)["native_admission"] is False
    finally:
        con.close()


@pytest.mark.parametrize("numeric", ["0e-999", "-0.0"])
def test_streaming_allows_exact_zero_json_decimals(tmp_path, numeric):
    source = tmp_path / "conversations-011.json"
    source.write_text('[{"id":"c","create_time":' + numeric +
                      ',"mapping":{}}]', encoding="utf-8")
    entry = {"shard": source.name, "size_bytes": source.stat().st_size,
             "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    assert len(list(mod.iter_source_conversations(source, entry, chunk_bytes=7))) == 1


@pytest.mark.parametrize("through_parent", [False, True])
def test_private_output_symlink_or_parent_junction_alias_fails_before_db_write(tmp_path, through_parent):
    """A private-output alias cannot redirect R1 SQLite outside approved ACL."""
    raw = tmp_path / "raw"
    raw.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "private_alias"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Directory symlinks unavailable: {exc}")
    target = link
    if through_parent:
        (outside / "review").mkdir()
        target = link / "review"
    receipt = tmp_path / "receipt.json"
    entries = [{"shard": f"conversations-{n:03d}.json",
                "size_bytes": 10, "sha256": "a" * 64} for n in range(12)]
    receipt.write_text(json.dumps({
        "schema": "CGX-OWNER-GPT-EXPORT-SHARD-RECEIPT/0.1",
        "shards": entries, "total_bytes": 120
    }), encoding="utf-8")
    args = type("A", (), {
        "shards_dir": raw, "receipt": receipt, "private_dir": target,
        "preflight_only": False, "serve": False, "max_shards": 0, "port": 8767
    })
    with pytest.raises(ValueError, match="PRIVATE_DIRECTORY_REPARSE_HOLD"):
        mod.run(args)
    assert not (outside / "semantic_review.sqlite").exists()
    assert not (outside / "review" / "semantic_review.sqlite").exists()


@pytest.mark.parametrize("suffix", ["", "-wal", "-shm", "-journal"])
def test_private_sqlite_alias_and_sidecar_rejected_before_open(tmp_path, suffix):
    """Planted DB and SQLite sidecar symlinks must not escape private ACL."""
    db = tmp_path / "private_review.sqlite"
    sentinel = tmp_path / "outside_sentinel.bin"
    sentinel.write_bytes(b"DO_NOT_MODIFY")
    alias = Path(str(db) + suffix)
    try:
        alias.symlink_to(sentinel)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"File symlinks unavailable: {exc}")
    with pytest.raises(ValueError, match="PRIVATE_SQLITE_TARGET_ALIAS_HOLD"):
        mod.connect(db)
    assert sentinel.read_bytes() == b"DO_NOT_MODIFY"
    if suffix:
        assert not db.exists()


def test_private_sqlite_hardlink_alias_rejected_before_open(tmp_path):
    """A hardlinked existing DB must not mutate another source file."""
    db = tmp_path / "private_review.sqlite"
    sentinel = tmp_path / "outside_sentinel.bin"
    sentinel.write_bytes(b"DO_NOT_MODIFY")
    try:
        os.link(sentinel, db)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Hardlinks unavailable: {exc}")
    with pytest.raises(ValueError, match="PRIVATE_SQLITE_TARGET_ALIAS_HOLD"):
        mod.connect(db)
    assert sentinel.read_bytes() == b"DO_NOT_MODIFY"


@pytest.mark.parametrize("which", ["source", "receipt", "source_parent", "receipt_parent"])
def test_private_r0_source_or_receipt_reparse_alias_fails_closed(tmp_path, which):
    """Do not resolve away an unapproved source/receipt directory alias."""
    original = tmp_path / "original"
    original.mkdir()
    (original / "raw").mkdir()
    entries = [{"shard": f"conversations-{n:03d}.json",
                "size_bytes": 10, "sha256": "a" * 64} for n in range(12)]
    (original / "receipt.json").write_text(json.dumps({
        "schema": "CGX-OWNER-GPT-EXPORT-SHARD-RECEIPT/0.1",
        "shards": entries, "total_bytes": 120
    }), encoding="utf-8")
    alias = tmp_path / "alias"
    if which in ("source", "receipt"):
        destination = original / ("raw" if which == "source" else "receipt.json")
        try:
            alias.symlink_to(destination, target_is_directory=which == "source")
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"Symlinks unavailable: {exc}")
        source = alias if which == "source" else original / "raw"
        receipt = alias if which == "receipt" else original / "receipt.json"
    else:
        try:
            alias.symlink_to(original, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"Directory symlinks unavailable: {exc}")
        source = alias / "raw" if which == "source_parent" else original / "raw"
        receipt = alias / "receipt.json" if which == "receipt_parent" else original / "receipt.json"
    target = tmp_path / "approved_private"
    target.mkdir()
    args = type("A", (), {
        "shards_dir": source, "receipt": receipt, "private_dir": target,
        "preflight_only": True, "serve": False, "max_shards": 0, "port": 8767
    })
    with pytest.raises(ValueError, match="SOURCE_INPUT_REPARSE_HOLD"):
        mod.run(args)
    assert not (target / "semantic_review.sqlite").exists()
    assert (original / "receipt.json").is_file()


def test_conflicting_message_id_never_leaks_source_identifier(tmp_path):
    """A source-controlled message ID must not escape into error/progress logs."""
    source, _ = sample(tmp_path)
    first = json.loads(source.read_text(encoding="utf-8"))[0]
    second = json.loads(json.dumps(first))
    synthetic_private_id = "SYNTHETIC_PRIVATE_IDENTIFIER_DO_NOT_LOG"
    first["mapping"]["u-node"]["message"]["id"] = synthetic_private_id
    second["id"] = "conversation-conflict"
    second["mapping"]["u-node"]["message"]["id"] = synthetic_private_id
    second["mapping"]["u-node"]["message"]["content"]["parts"] = [
        "Deliberately conflicting synthetic source text"
    ]
    source.write_text(json.dumps([first, second]), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    con = mod.connect(tmp_path / "review.sqlite")
    try:
        with pytest.raises(ValueError) as caught:
            mod.ingest_shard(con, source, entry)
        assert str(caught.value) == "CONFLICTING_MESSAGE_ID_HOLD"
        assert synthetic_private_id not in str(caught.value)
        assert con.execute("SELECT count(*) FROM shard").fetchone()[0] == 0
        assert con.execute("SELECT count(*) FROM message").fetchone()[0] == 0
        assert mod.summary(con)["native_admission"] is False
    finally:
        con.close()

@pytest.mark.parametrize("kind,bad_id", [
    ("conversation", 7),
    ("conversation", True),
    ("conversation", 0),
    ("conversation", False),
    ("conversation", ""),
    ("message", 7),
    ("message", True),
    ("message", 7.0),
    ("message", 0),
    ("message", False),
    ("message", ""),
    ("message", None),
])
def test_r0_identifier_types_do_not_coerce_into_existing_string_ids(tmp_path, kind, bad_id):
    """A numeric/boolean source ID is not equivalent to its text rendering."""
    source, entry = sample(tmp_path)
    conv = json.loads(source.read_text(encoding="utf-8"))[0]
    if kind == "conversation":
        conv["conversation_id"] = bad_id
    else:
        conv["mapping"]["u-node"]["message"]["id"] = bad_id
    source.write_text(json.dumps([conv]), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    con = mod.connect(tmp_path / "typed_id_review.sqlite")
    try:
        with pytest.raises(ValueError, match=(
            "SOURCE_CONVERSATION_ID_HOLD" if kind == "conversation"
            else "SOURCE_MESSAGE_ID_HOLD"
        )):
            mod.ingest_shard(con, source, entry)
        assert con.execute("SELECT count(*) FROM shard").fetchone()[0] == 0
        assert con.execute("SELECT count(*) FROM message").fetchone()[0] == 0
        assert con.execute("SELECT count(*) FROM conversation_variant").fetchone()[0] == 0
        assert mod.summary(con)["native_admission"] is False
    finally:
        con.close()


@pytest.mark.parametrize("bad_parent", [0, False, 7, [], {}, ""])
def test_source_parent_pointer_rejects_nonstring_without_commit(tmp_path, bad_parent):
    """R0 parent references cannot silently become a false typed R1 edge."""
    source, _ = sample(tmp_path)
    conv = json.loads(source.read_text(encoding="utf-8"))[0]
    conv["mapping"]["a-node"]["parent"] = bad_parent
    source.write_text(json.dumps([conv]), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    con = mod.connect(tmp_path / "typed_parent.sqlite")
    try:
        with pytest.raises(ValueError, match="SOURCE_PARENT_NODE_ID_HOLD"):
            mod.ingest_shard(con, source, entry)
        assert con.execute("SELECT count(*) FROM shard").fetchone()[0] == 0
        assert con.execute("SELECT count(*) FROM message").fetchone()[0] == 0
        assert con.execute("SELECT count(*) FROM prompt_response").fetchone()[0] == 0
        assert mod.summary(con)["native_admission"] is False
    finally:
        con.close()


@pytest.mark.parametrize("bad_parent", [0, False, []])
def test_source_hidden_intermediate_parent_pointer_fails_closed(tmp_path, bad_parent):
    """A filtered analysis node may be traversed but cannot launder a bad ID."""
    source, _ = sample(tmp_path)
    conv = json.loads(source.read_text(encoding="utf-8"))[0]
    conv["mapping"]["a-node"]["parent"] = "hidden-node"
    conv["mapping"]["hidden-node"]["parent"] = bad_parent
    source.write_text(json.dumps([conv]), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    con = mod.connect(tmp_path / "hidden_parent.sqlite")
    try:
        with pytest.raises(ValueError, match="SOURCE_PARENT_NODE_ID_HOLD"):
            mod.ingest_shard(con, source, entry)
        assert con.execute("SELECT count(*) FROM shard").fetchone()[0] == 0
        assert con.execute("SELECT count(*) FROM prompt_response").fetchone()[0] == 0
    finally:
        con.close()


@pytest.mark.parametrize("bad_id", [0, False, 7, None])
def test_source_hidden_user_ancestor_id_is_not_string_coerced(tmp_path, bad_id):
    """Even a filtered user is rejected at the earliest visible-node ID gate."""
    source, _ = sample(tmp_path)
    conv = json.loads(source.read_text(encoding="utf-8"))[0]
    conv["mapping"]["u-node"]["message"]["metadata"] = {"channel": "analysis"}
    conv["mapping"]["u-node"]["message"]["id"] = bad_id
    source.write_text(json.dumps([conv]), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    con = mod.connect(tmp_path / "hidden_user.sqlite")
    try:
        with pytest.raises(ValueError, match="SOURCE_MESSAGE_ID_HOLD"):
            mod.ingest_shard(con, source, entry)
        assert con.execute("SELECT count(*) FROM shard").fetchone()[0] == 0
        assert con.execute("SELECT count(*) FROM prompt_response").fetchone()[0] == 0
    finally:
        con.close()


def test_source_filtered_user_ancestor_cannot_become_prompt_link(tmp_path):
    """An excluded user channel is not a visible prompt-response source."""
    source, _ = sample(tmp_path)
    conv = json.loads(source.read_text(encoding="utf-8"))[0]
    conv["mapping"]["u-node"]["message"]["metadata"] = {"channel": "analysis"}
    source.write_text(json.dumps([conv]), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    con = mod.connect(tmp_path / "filtered_user.sqlite")
    try:
        assert mod.ingest_shard(con, source, entry)[0] == 1
        assert mod.summary(con)["unique_messages"] == 1
        assert mod.summary(con)["prompt_response_links"] == 0
        assert con.execute(
            "SELECT count(*) FROM source_issue WHERE kind='UNRESOLVED_USER_PARENT'"
        ).fetchone()[0] == 1
        assert mod.summary(con)["native_admission"] is False
    finally:
        con.close()


def test_source_omitted_ancestor_id_preserves_original_node_key_fallback(tmp_path):
    """A missing ID differs from an explicitly invalid ID."""
    source, _ = sample(tmp_path)
    conv = json.loads(source.read_text(encoding="utf-8"))[0]
    del conv["mapping"]["u-node"]["message"]["id"]
    source.write_text(json.dumps([conv]), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    con = mod.connect(tmp_path / "omitted_ancestor.sqlite")
    try:
        assert mod.ingest_shard(con, source, entry)[0] == 1
        assert con.execute(
            "SELECT prompt_id FROM prompt_response WHERE response_id='a-1'"
        ).fetchone() == ("u-node",)
        assert mod.summary(con)["native_admission"] is False
    finally:
        con.close()

@pytest.mark.parametrize("field,bad_value,reason", [
    ("title", 0, "SOURCE_CONVERSATION_TITLE_TYPE_HOLD"),
    ("title", False, "SOURCE_CONVERSATION_TITLE_TYPE_HOLD"),
    ("title", ["alias"], "SOURCE_CONVERSATION_TITLE_TYPE_HOLD"),
    ("create_time", "1.0", "SOURCE_TIMESTAMP_TYPE_OR_PRECISION_HOLD"),
    ("create_time", True, "SOURCE_TIMESTAMP_TYPE_OR_PRECISION_HOLD"),
    ("update_time", [], "SOURCE_TIMESTAMP_TYPE_OR_PRECISION_HOLD"),
    ("create_time", 2**53, "SOURCE_TIMESTAMP_TYPE_OR_PRECISION_HOLD"),
    ("create_time", 10**400, "SOURCE_TIMESTAMP_TYPE_OR_PRECISION_HOLD"),
    ("message_create_time", "2.0", "SOURCE_TIMESTAMP_TYPE_OR_PRECISION_HOLD"),
    ("message_create_time", False, "SOURCE_TIMESTAMP_TYPE_OR_PRECISION_HOLD"),
    ("message_create_time", 2**53, "SOURCE_TIMESTAMP_TYPE_OR_PRECISION_HOLD"),
])
def test_source_metadata_types_reject_lossy_sqlite_coercion(tmp_path, field, bad_value, reason):
    """R1 must not silently conflate distinct R0 title/time JSON types."""
    source, _ = sample(tmp_path)
    conv = json.loads(source.read_text(encoding="utf-8"))[0]
    if field == "message_create_time":
        conv["mapping"]["a-node"]["message"]["create_time"] = bad_value
    else:
        conv[field] = bad_value
    source.write_text(json.dumps([conv]), encoding="utf-8")
    entry = {"shard": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "size_bytes": source.stat().st_size}
    con = mod.connect(tmp_path / "typed_metadata.sqlite")
    try:
        with pytest.raises(ValueError, match=reason):
            mod.ingest_shard(con, source, entry)
        for table in ("shard", "conversation", "conversation_variant",
                      "message", "source_visible_occurrence",
                      "source_prompt_response_occurrence"):
            assert con.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0
        assert mod.summary(con)["native_admission"] is False
    finally:
        con.close()

