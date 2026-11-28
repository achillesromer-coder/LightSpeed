"""Guard the one-root overdue UOS release plan against accidental promotion."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "cgx/review/unispace_primary_product_launch_recovery_20261123.json"
GATES = ROOT / "cgx/review/unispace_crossspace_gate_register_v0_1.json"


def load():
    return json.loads(PLAN.read_text("utf-8"))


def validate(p):
    assert p["schema"] == "CGX-UNISPACE-PRIMARY-PRODUCT-LAUNCH-RECOVERY/0.1"
    assert p["root"] == "cgx:root:cognigrex"
    assert p["scope"] == "SOURCE_LINKED_EXECUTION_SPEC_NOT_RUNTIME_INSTALL_OR_RELEASE_APPROVAL"
    assert p["deadline"]["reported_delay_days"] == 9
    assert p["deadline"]["exact_original_deadline_independently_verified"] is False
    assert p["source_observations"]["canonical_pr"] == 228
    assert p["source_observations"]["merged_convergence_prs"] == [232, 230, 229]
    assert p["source_observations"]["currently_open_distinct_prs"] == [205, 236]
    assert p["source_observations"]["open_gate_group_count"] == 51
    assert p["source_observations"]["hosted_status"] == "HOSTED_AUTHENTICATED_NATIVE_HELD_PEER_UNVERIFIED"
    assert p["source_observations"]["native_bridge"].endswith("LOCAL_OBSERVATION")
    reference = json.loads((ROOT / "UniSpace/product.json").read_text("utf-8"))
    assert reference["runtime_activated"] is False
    assert reference["complete_product_acceptance"] is False
    assert p["source_observations"]["existing_public_reference"]["manifest"] == "UniSpace/product.json"
    assert set(p["architecture"]["canonical_facets"]) == {
        "file_space", "data_space", "social_space", "print_space", "intelligence_space"
    }
    assert len(p["architecture"]["ui_selectors"]) == 7
    assert p["architecture"]["non_mintable_sentinel"] == "T174"
    assert p["architecture"]["separate_roots_created"] is False
    assert p["architecture"]["separate_schedulers_created"] is False
    gates = json.loads(GATES.read_text("utf-8"))
    assert gates["canonical_root"] == p["root"]
    assert gates["source_count"] == 51
    assert all(x["state"] == "OPEN_REVIEW_ONLY" for x in gates["task_groups"])
    assert all(x["effectful_action_authorised"] is False for x in gates["task_groups"])
    facets = p["facets"]
    assert len(facets) == 5
    assert {x["id"] for x in facets} == set(p["architecture"]["canonical_facets"])
    for x in facets:
        assert (x["owner_lane"] in (
            "CGX Achilles Römer", "CGX Neo LightSpeed", "CGX Athene Eco",
            "CGX Cognigrex Family", "CGX UniSpace Product"))
        assert len(x["acceptance"]) >= 3
        assert not x["status"].startswith("PRODUCTION_ACCEPTED")
    assert p["ui_and_support"]["ProfileSpace"]["not_a_new_db"] is True
    assert p["ui_and_support"]["SystemSpace"]["not_a_new_db"] is True
    assert p["ui_and_support"]["LOAD_and_CCC"]["not_another_root"] is True
    assert p["ui_and_support"]["Site"]["public_site_verified"] is False
    batches = p["batch_execution"]
    order = [x["id"] for x in batches]
    assert order == [f"B{x:02}" for x in range(8)]
    assert len(order) == len(set(order))
    for i, task in enumerate(batches):
        assert all(dep in order[:i] for dep in task["depends_on"])
        assert task["lane"] in {facet["owner_lane"] for facet in facets}
        assert task["gate"]
    assert batches[3]["class"] == "NATIVE_HOLD_UNTIL_PROOF"
    assert batches[4]["class"] == "LIVE_MUTATION_HOLD"
    assert batches[5]["class"] == "OFFCHAIN_DRY_RUN_ONLY"
    assert batches[6]["class"] == "EXTERNAL_PUBLISH_HOLD"
    assert batches[6]["depends_on"] == ["B00", "B02"]
    assert "B05" not in batches[6]["depends_on"]  # Preview does not require native/on-chain mint.
    tiers = p["release_tiers"]
    assert [x["id"] for x in tiers] == ["R0", "R1", "R2", "R3"]
    assert tiers[-1]["now"].startswith("BLOCKED")
    assert p["mint_sequence"][-1].startswith("ONCHAIN_MINT_ONLY")
    assert p["outreach"]["internal_planning_targets_not_forecasts"]["public_communications_without_approval"] == 0
    assert p["outreach"]["initial_allowed_phase"] == "INTERNAL_NONCONFIDENTIAL_PREPARATION"
    assert len(p["outreach"]["channels"]) >= 3
    assert all(v is False for v in p["invariants"].values())


def test_release_manifest_stays_source_linked_and_no_mint():
    validate(load())


def test_cannot_rewrite_gate_counts_or_claim_public_release():
    p = load()
    p["source_observations"]["open_gate_group_count"] = 0
    with pytest.raises(AssertionError):
        validate(p)
    p = load()
    p["invariants"]["public_launch_finished"] = True
    with pytest.raises(AssertionError):
        validate(p)


def test_separate_root_and_mint_overclaims_rejected():
    for field, value in [
        ("root", "cgx:root:second"),
        ("scope", "NATIVE_PRODUCTION_ACCEPTED"),
    ]:
        p = load()
        p[field] = value
        with pytest.raises(AssertionError):
            validate(p)
    p = load()
    p["invariants"]["onchain_mint_finished"] = True
    with pytest.raises(AssertionError):
        validate(p)


def test_batch_dependencies_must_not_skip_prior_prerequisites():
    p = load()
    p["batch_execution"][3]["depends_on"] = ["B07"]
    with pytest.raises(AssertionError):
        validate(p)


def test_socialspace_is_optin_not_a_public_contact_harvester():
    p = load()
    s = next(x for x in p["facets"] if x["id"] == "social_space")
    assert "explicit_two_principal_opt_in" in s["integration"]
    assert "AI_free_or_no_AI_contact_enforced_server_side" in s["integration"]
    assert s["release"] == "OPTIONAL_LATER_THAN_PRIMARY"


def test_reference_carrier_does_not_satisfy_native_product():
    p = load()
    assert "NATIVE_MINTED" in p["primary_release_definition"]["must_not_claim_early"]
    assert p["source_observations"]["existing_public_reference"]["state"] == "S91_REFERENCE_PRE_ALPHA"
    assert p["release_tiers"][0]["scope"] == "REFERENCE_ASSET_NOT_FUNCTIONAL_UOS"
