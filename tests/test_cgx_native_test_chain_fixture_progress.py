"""A local test fixture is not a native issuer/peer admission receipt."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "cgx/review/cgx_native_test_chain_fixture_progress_20261123.json"
ORIGINAL = ROOT / "cgx/review/cgx_native_admission_owner_intent_20261123.json"
GATES = ROOT / "cgx/review/unispace_crossspace_gate_register_v0_1.json"


def read(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def test_current_fixture_progress_uses_existing_root_and_source_refs():
    p = read(PROGRESS)
    assert p["schema"] == "CGX-NATIVE-TEST-CHAIN-FIXTURE-PROGRESS/0.1"
    assert p["canonical_root"] == "cgx:root:cognigrex"
    assert p["observation_kind"] == (
        "REMOTE_HOST_COMMAND_OUTPUT_NOT_INDEPENDENT_CRYPTOGRAPHIC_RECEIPT")
    assert len(p["source_refs"]) == 6
    for relative in p["source_refs"].values():
        assert (ROOT / relative).is_file()


def test_two_independent_fixture_suites_are_not_live_admission():
    p = read(PROGRESS)
    stages = {row["id"]: row for row in p["test_stages"]}
    assert set(stages) == {"T0", "T1", "T2", "T3", "T4", "T5", "T6"}
    assert [stages[x]["count_passed"] for x in ("T1", "T2")] == [19, 13]
    assert [stages[x]["count_failed"] for x in ("T1", "T2")] == [0, 0]
    assert p["evidence_boundary"]["test_count_passed_in_local_fixtures"] == 32
    assert p["evidence_boundary"]["test_count_is_native_acceptance"] == 0
    assert all(row["signed_native_receipt"] is False for row in stages.values())
    assert all(stages[x]["state"].startswith("HOLD") for x in ("T3", "T4", "T5", "T6"))


def test_dirty_live_host_and_stale_site_do_not_satisfy_signer():
    p = read(PROGRESS)
    host = p["local_observation"]
    assert host["deployment_mappings"] == 757
    assert host["changed_installed_mappings"] == 61
    assert host["locally_dirty_entries"] == 3
    assert host["checkout_identical_to_latest_github_source"] is False
    assert host["deployment_blockers"] == [
        "REVIEW_BRANCH_NOT_ACCEPTED_MAIN",
        "MAIN_NOT_ALIGNED_WITH_ORIGIN",
        "UNCOMMITTED_OR_UNTRACKED_SOURCE",
        "MANAGED_SERVICES_ACTIVE",
    ]
    assert host["port_8765_http_health_verified"] is False
    assert host["no_restart_or_install_performed"] is True
    assert p["hosted_observation"]["native_admitted"] is False
    assert p["hosted_observation"]["peer_verified"] is False


def test_original_approval_and_all_51_engineering_gates_remain_held():
    progress, original, gates = read(PROGRESS), read(ORIGINAL), read(GATES)
    assert original["record_class"] == (
        "CHAT_RECORDED_OWNER_INTENT_NOT_NATIVE_SIGNED_LEASE")
    assert original["source_state"] == (
        "OWNER_INTENT_PRESERVED_NATIVE_ACTIONS_HELD_UNTIL_WITNESSED")
    assert all(v is False for v in original["native_authority"].values())
    assert gates["source_count"] == len(gates["task_groups"]) == 51
    assert all(x["owner_approval_observed"] is False
               and x["effectful_action_authorised"] is False
               and x["state"] == "OPEN_REVIEW_ONLY"
               for x in gates["task_groups"])
    boundary = progress["evidence_boundary"]
    for condition in ("no_native_db_mutation", "no_signed_owner_lease_verified",
                      "no_independent_peer_qualification",
                      "no_main_merge", "no_public_website_release"):
        assert boundary[condition] is True
    assert progress["next_gate"].startswith("T3_INDEPENDENT_SIGNED_OWNER_ISSUER")
