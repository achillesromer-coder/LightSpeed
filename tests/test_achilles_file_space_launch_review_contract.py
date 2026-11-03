"""FileSpace-first unminted launch gating, no side effects."""
import json
from pathlib import Path

CONTRACT=Path(__file__).resolve().parents[1]/"cgx"/"domain_templates"/"achilles_file_space_launch_review_contract.json"


def load():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_single_existing_canonical_parent():
    c=load()
    assert c["canonical_parent"]=="cgx:root:cognigrex"
    assert c["state"]=="REVIEW_ONLY_UNMINTED"
    assert c["canonical_objects_minted"]==0


def test_file_space_is_first():
    phases=load()["phase_order"]
    assert [(p["ordinal"],p["id"]) for p in phases]==[
        (1,"file_space"),(2,"unispace_file_space_control"),(3,"data_space"),(4,"print_space")]


def test_data_and_print_cannot_skip_file_space():
    p={x["id"]:x for x in load()["phase_order"]}
    assert p["data_space"]["state"]=="NOT_ACTIVATED"
    assert "file_space:LANDED_AND_ACCEPTED" in p["data_space"]["dependency"]
    assert "data_space:TESTED" in p["print_space"]["dependency"]


def test_no_stage_self_mints():
    for phase in load()["phase_order"]:
        assert phase["may_self_mint"] is False


def test_romer_4d_printing_is_not_unispace_product():
    c=load()
    specialist=c["separate_specialist_domains"]["romer_grex_4d_printing"]
    assert specialist["owner"]=="Romer.cgx"
    assert specialist["state"]=="SPECIALIST_RESEARCH_ISOLATED"
    assert "NOT a UniSpace product" in specialist["relation_to_print_space"]


def test_semantic_shorthand_needs_roundtrip_not_mere_shapes():
    x=load()["shorthand_contract"]
    assert x["state"]=="CANDIDATE_ONLY"
    required=set(x["required"])
    assert {"dimension","units","transform law","roundtrip or explicitly quantified loss",
            "canonical source identity","rights and signer chain"} <= required


def test_no_training_grant_or_automatic_promotion():
    c=load()
    assert c["model_and_training"]["weights_finetuned"] is False
    assert c["model_and_training"]["training_data_approval"]=="NOT_YET_QUALIFIED"
    assert "native DBR mint" in c["mutation_policy"]["forbidden_without_independent_authority"]
    assert c["receipts"]["signed_issuer"] is False
    assert c["receipts"]["lease_verified"] is False


def test_existing_owner_lanes_not_reparented():
    roles=load()["owner_roles"]
    assert roles["achilles"]["principal_domain"]=="emassc"
    assert roles["neo"]["principal_domain"]=="romer"
    assert roles["athene"]["principal_domain"]=="eco"
    assert roles["achilles"]["self_approval"] is False
