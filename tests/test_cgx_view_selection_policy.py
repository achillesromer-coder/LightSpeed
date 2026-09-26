from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_cgx_domain_templates.py"
DT = ROOT / "cgx" / "domain_templates"

spec = importlib.util.spec_from_file_location("validate_cgx_domain_templates", SCRIPT)
validator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(validator)


def load_json(name: str):
    return json.loads((DT / name).read_text(encoding="utf-8"))


def failures_for(policy):
    views = load_json("semantic_view_lens_registry.json")
    view_ids = validator.view_ids_from_registry(views)
    return validator.validate_view_selection_policy(policy, view_ids)


def test_current_view_selection_policy_contract_passes():
    assert failures_for(load_json("view_selection_policy.json")) == []


def test_security_and_admission_must_be_first():
    policy = copy.deepcopy(load_json("view_selection_policy.json"))
    policy["inputs_in_priority_order"][0:2] = list(reversed(policy["inputs_in_priority_order"][0:2]))
    assert any("security_and_admission first" in failure for failure in failures_for(policy))


def test_unknown_view_is_rejected():
    policy = copy.deepcopy(load_json("view_selection_policy.json"))
    policy["task_mapping"]["operate"].append("unknown-view")
    assert any("unknown views" in failure for failure in failures_for(policy))


def test_canonical_mutation_is_rejected():
    policy = copy.deepcopy(load_json("view_selection_policy.json"))
    policy["output"]["canonical_mutation"] = True
    assert any("must not mutate canon" in failure for failure in failures_for(policy))


def test_required_security_evidence_root_outputs_are_enforced():
    policy = copy.deepcopy(load_json("view_selection_policy.json"))
    policy["output"]["fields"].remove("evidence_ceiling")
    assert any("output missing fields" in failure for failure in failures_for(policy))


def test_hybridisation_must_keep_one_primary_view_and_same_object_set():
    policy = copy.deepcopy(load_json("view_selection_policy.json"))
    policy["hybridisation_policy"]["max_primary_views"] = 2
    policy["hybridisation_policy"]["combine_if"] = "convenience"
    failures = failures_for(policy)
    assert any("exactly one primary view" in failure for failure in failures)
    assert any("same stable object set" in failure for failure in failures)
