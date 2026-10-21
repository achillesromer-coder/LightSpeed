import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DT = ROOT / "cgx" / "domain_templates"


def load(name):
    return json.loads((DT / name).read_text(encoding="utf-8"))


def test_intersol_profile_is_bound_from_current_domains():
    domains = load("domains.json")
    assert domains["shared_contracts"]["intersol_site_community_profile"] == "intersol_site_community_profile_contract.json"


def test_intersol_profile_preserves_planning_and_authority_boundaries():
    d = load("intersol_site_community_profile_contract.json")
    assert d["schema"] == "CGX-INTERSOL-SITE-COMMUNITY-PROFILE/0.1"
    assert d["authority"]["semantic_owner"] == "Type 1 Romer Cognigrex"
    assert d["reference_site"]["status"] == "reference-model-only"
    boundaries = " ".join(d["evidence_boundaries"]).lower()
    assert "not land or approval authority" in boundaries
    assert "not regulatory/qra proof" in boundaries
    assert "not current employment terms" in boundaries
    assert "not implemented" in boundaries


def test_spatial_geometry_keeps_radius_and_corridor_distinct():
    d = load("intersol_site_community_profile_contract.json")
    spatial = d["spatial_policy"]
    assert spatial["exclusion_radius_m"] == 10000
    assert spatial["managed_eco_corridor_width_m"] == 1000
    assert spatial["outer_planning_radius_m"] == 11000
    assert spatial["outer_planning_radius_m"] == spatial["exclusion_radius_m"] + spatial["managed_eco_corridor_width_m"]
    assert "not an exclusion radius" in " ".join(spatial["invariants"])


def test_personal_sai_profile_is_opt_in_and_secret_free():
    d = load("intersol_site_community_profile_contract.json")
    p = d["personal_sai_profile"]
    assert p["universal_avatar"]["sync_default"] == "off"
    assert "explicit opt-in" in p["universal_avatar"]["sync_scope"]
    rules = " ".join(p["privacy_security"]).lower()
    assert "credentials/tokens/private keys stay outside portable .cgx" in rules
    assert "does not imply permission to publish or write back" in rules


def test_community_contribution_is_optional_and_not_unpaid_upkeep():
    d = load("intersol_site_community_profile_contract.json")
    c = d["workforce_community"]["community_contribution"]
    assert c["participation"] == "optional/recommended"
    assert c["no_penalty_for_nonparticipation"] is True
    assert "no unpaid compulsory upkeep" in c["credit_model"]["rule"]
