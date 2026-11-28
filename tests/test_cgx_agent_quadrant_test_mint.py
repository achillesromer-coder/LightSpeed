"""Bounded nine-selector CGX test mint: no real agents, peers, wallets, or DB."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.cgx_agent_quadrant_test_mint import (
    AUTHORITY, BOUNDARIES, QUADRANTS, ROOT, SCHEMA, QuadrantTestHold,
    canonical, digest, expected_files, make_batch, publish, validate_quadrants,
)

ROOT_DIR=Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def payload():
    return make_batch(ROOT_DIR,run_id="TEST-QUADRANT-9")


def test_uses_original_canonical_nine_source_profiles(payload):
    assert payload["manifest"]["schema"]==SCHEMA
    assert payload["manifest"]["root"]==ROOT
    assert payload["manifest"]["count"]==9
    assert set(x["selector"] for x in payload["records"])==set(QUADRANTS)
    assert {x["identity_kind"] for x in payload["records"]}=={
        "EXISTING_PRINCIPAL_AGENT","EXISTING_SELECTOR_ONLY"}
    assert all(len(x["source_plugin_sha256"])==64 for x in payload["records"])
    assert len({x["object_id"] for x in payload["records"]})==9
    assert all(x["object_id"].startswith("cgx:test-mint:") for x in payload["records"])


def test_geometric_quadrants_have_strict_nonoverlapping_coordinates():
    validate_quadrants()
    assert {v[0] for v in QUADRANTS.values()}==set(BOUNDARIES)
    assert len({(v[1],v[2]) for v in QUADRANTS.values()})==9


def test_simulations_are_real_deterministic_source_calculations(payload):
    for row in payload["records"]:
        work=row["simulation"]["work_result"]
        assert row["simulation"]["executed"] is True
        assert work["source_proof"]==row["source_plugin_sha256"]
        assert row["simulation"]["work_result_sha256"]==digest(work)
        assert row["record_sha256"]==digest({k:v for k,v in row.items() if k!="record_sha256"})
    assert payload["manifest"]["batch_sha256"]==digest(
        {k:v for k,v in payload["manifest"].items() if k!="batch_sha256"})


def test_no_claim_of_model_agent_activation_native_crypto_or_chain(payload):
    assert all(v is False for v in AUTHORITY.values())
    assert payload["manifest"]["native_agents_launched"]==0
    assert payload["manifest"]["model_calls"]==0
    assert payload["manifest"]["native_dbr_receipts"]==0
    assert payload["manifest"]["onchain_transactions"]==0
    assert payload["manifest"]["actual_os_network_isolation_proven"] is False
    assert payload["manifest"]["actual_signer_or_peer_verified"] is False
    assert payload["manifest"]["native_activation_after_test"].startswith("HELD_")
    assert all(all(value is False for value in r["authority"].values()) for r in payload["records"])


def test_limited_test_budgets_do_not_pretend_os_enforcement(payload):
    for r in payload["records"]:
        assert r["lease"]["max_concurrent_model_jobs"]==0
        assert r["lease"]["max_effectful_jobs"]==0
        assert r["lease"]["cpu_threads_budget"]==1
        assert r["lease"]["budgets_are_declarations_not_os_enforcement"] is True
        assert r["promotable_without_independent_review"] is False


def test_mint_writes_only_ten_bounded_fixture_files_and_readbacks(payload,tmp_path):
    out=tmp_path/"isolated"
    a=publish(payload,out)
    assert a["status"]=="PASS_ISOLATED_SOURCE_TEST_MINT"
    assert a["source_records"]==9 and a["quadrants"]==4
    assert a["newly_created"] is True
    assert a["signed_native_mint"] is False
    assert len(list(out.rglob("*.json")))==10
    assert json.loads((out/"manifest.json").read_text())["root"]==ROOT
    assert a["manifest_sha256"]==__import__("hashlib").sha256(
        expected_files(payload)["manifest.json"]).hexdigest()


def test_exact_rerun_is_idempotent_and_verify_only_does_not_write(payload,tmp_path):
    out=tmp_path/"isolated"
    first=publish(payload,out)
    before={p.relative_to(out).as_posix():p.stat().st_mtime_ns
            for p in out.rglob("*.json")}
    again=publish(payload,out)
    verified=publish(payload,out,verify_only=True)
    after={p.relative_to(out).as_posix():p.stat().st_mtime_ns
           for p in out.rglob("*.json")}
    assert first["manifest_sha256"]==again["manifest_sha256"]==verified["manifest_sha256"]
    assert again["newly_created"] is False
    assert verified["newly_created"] is False
    assert before==after


def test_missing_fixture_held_in_verify_mode(payload,tmp_path):
    with pytest.raises(QuadrantTestHold,match="absent"):
        publish(payload,tmp_path/"no-such-fixture",verify_only=True)


def test_modified_source_mint_fixture_is_detected(payload,tmp_path):
    out=tmp_path/"isolated"
    publish(payload,out)
    target=out/"agents"/"neo.json"
    target.write_text('{"state":"NATIVE_MINTED"}\n')
    with pytest.raises(QuadrantTestHold):
        publish(payload,out,verify_only=True)


def test_unrelated_existing_directory_is_not_overwritten(payload,tmp_path):
    out=tmp_path/"isolated"
    out.mkdir()
    (out/"private.txt").write_text("keep unchanged")
    with pytest.raises(QuadrantTestHold):
        publish(payload,out)
    assert (out/"private.txt").read_text()=="keep unchanged"


@pytest.mark.parametrize("bad",["","../evil","a b","a"*65,"foo\\bar"])
def test_run_id_out_of_scope_is_denied(bad):
    with pytest.raises(QuadrantTestHold,match="Run_ID"):
        make_batch(ROOT_DIR,run_id=bad)


def test_duplicate_cell_or_wrong_quadrant_is_refused(monkeypatch):
    monkeypatch.setitem(QUADRANTS,"neo",("QII",1,1))
    with pytest.raises(QuadrantTestHold):
        validate_quadrants()


def test_refuses_missing_or_out_of_scope_output_parent(payload,tmp_path):
    with pytest.raises(QuadrantTestHold):
        publish(payload,tmp_path/"no-parent"/"isolated")


def test_fixture_bytes_are_canonical_and_bounded(payload):
    encoded=expected_files(payload)
    assert len(encoded)==10
    assert sum(map(len,encoded.values()))<1000000
    assert encoded["manifest.json"]==canonical(payload["manifest"])+b"\n"
