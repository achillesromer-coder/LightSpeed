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


def load_json(name):
    return json.loads((DT / name).read_text(encoding="utf-8"))


def failures_for(policy):
    views = load_json("semantic_view_lens_registry.json")
    return validator.validate_view_selection_policy(policy, validator.view_ids_from_registry(views))


def test_current_view_selection_policy_contract_passes():
    assert failures_for(load_json("view_selection_policy.json")) == []


def test_security_and_admission_must_be_first():
    policy = copy.deepcopy(load_json("view_selection_policy.json"))
    policy["inputs_in_priority_order"][0:2] = list(reversed(policy["inputs_in_priority_order"][0:2]))
    assert any("security_and_admission first" in x for x in failures_for(policy))


def test_unknown_view_and_canonical_mutation_are_rejected():
    policy = copy.deepcopy(load_json("view_selection_policy.json"))
    policy["task_mapping"]["operate"].append("unknown-view")
    policy["output"]["canonical_mutation"] = True
    failures = failures_for(policy)
    assert any("unknown views" in x for x in failures)
    assert any("must not mutate canon" in x for x in failures)
