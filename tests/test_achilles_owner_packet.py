"""Source-only Achilles owner packet tests. No host, model, credentials or DB."""
from __future__ import annotations
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_achilles_owner_packet.py"
spec = importlib.util.spec_from_file_location("achilles_owner_packet", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def planned(instruction, task_id):
    return {
        "workflow_id": task_id,
        "instruction_sha256": module._hash(instruction),
        "floor_sequence": ["Neo", "Architect", "Morpheus"],
        "proof_required": True,
        "canonical_promotion_authorized": False,
        "public_publish_authorized": False,
    }


def test_identity_preserves_domain_ownership_and_no_self_approval():
    p = module.load_profile()
    assert p["identity"]["principal_domain"] == "emassc"
    assert "Neo owns Romer-Grex" in p["identity"]["domain_ownership"]
    assert p["authority"]["agent_can_self_approve"] is False
    assert p["lifecycle"]["native_dbr_admission"] is False


def test_owner_packet_routes_with_supervisor_and_no_sensitive_raw_payload():
    text = "private instruction: prohibit copying this task body"
    source = "drive-private://secret-file"
    packet = module.prepare_packet(text, "TASK-1", private_source_ids=(source,), planner=planned)
    serialized = json.dumps(packet)
    assert text not in serialized
    assert source not in serialized
    assert module._hash(source) not in serialized
    assert "private_source_id_hashes" not in packet
    assert packet["output_classification"] == "PRIVATE_OWNER_REVIEW_ONLY"
    assert packet["public_projection_authorized"] is False
    assert packet["private_source_set_binding"] == "NOT_INCLUDED_REQUIRES_PRIVATE_REVALIDATION"
    assert packet["authorization"]["private_source_set_approved"] is False
    assert packet["supervisor"]["floor_sequence"] == ["Neo", "Architect", "Morpheus"]
    assert packet["private_source_count"] == 1
    assert packet["authorization"]["effective_tool_permissions"] == []
    assert packet["authorization"]["no_self_approval"] is True
    assert packet["execution_request"]["execute"] is False
    assert packet["runtime_host_readback"] == "NOT_PERFORMED"


def test_idempotency_preserves_same_task_and_deduplicates_references():
    a = module.prepare_packet("same work", "TASK-2", private_source_ids=("a", "b", "a"), planner=planned)
    b = module.prepare_packet("same work", "TASK-2", private_source_ids=("b", "a"), planner=planned)
    c = module.prepare_packet("changed", "TASK-2", private_source_ids=("b", "a"), planner=planned)
    assert a["idempotency_fingerprint"] == b["idempotency_fingerprint"]
    assert a["idempotency_fingerprint"] != c["idempotency_fingerprint"]
    assert a["private_source_count"] == 2
    # Different same-size source sets deliberately share a public-safe fingerprint.
    # This MUST NOT be used as source-set equality or dispatch approval.
    d = module.prepare_packet("same work", "TASK-2", private_source_ids=("c", "d"), planner=planned)
    e = module.prepare_packet("same work", "TASK-2", private_source_ids=("a",), planner=planned)
    assert d["idempotency_fingerprint"] == a["idempotency_fingerprint"]
    assert e["idempotency_fingerprint"] != a["idempotency_fingerprint"]
    assert d["authorization"]["private_source_set_approved"] is False


def test_mutated_profile_fails_closed(tmp_path):
    data = module.load_profile()
    data["authority"]["agent_can_self_approve"] = True
    candidate = tmp_path / "tampered.json"
    candidate.write_text(json.dumps(data), encoding="utf-8")
    try:
        module.load_profile(candidate)
    except module.ProfileHold as error:
        assert "PRIVILEGE_ESCALATION" in str(error)
    else:
        raise AssertionError("Self-approval must remain denied")


def test_foreign_domain_fails_closed(tmp_path):
    data = module.load_profile()
    data["identity"]["principal_domain"] = "romer"
    candidate = tmp_path / "foreign.json"
    candidate.write_text(json.dumps(data), encoding="utf-8")
    try:
        module.load_profile(candidate)
    except module.ProfileHold as error:
        assert "IDENTITY_AUTHORITY" in str(error)
    else:
        raise AssertionError("Authority must not be reassigned silently")


def test_unsafe_supervisor_route_or_release_raises_hold():
    def publish_plan(instruction, task_id):
        result = planned(instruction, task_id)
        result["public_publish_authorized"] = True
        return result
    def bypass_plan(instruction, task_id):
        result = planned(instruction, task_id)
        result["floor_sequence"] = ["Smith"]
        return result
    for provider, reason in ((publish_plan, "SELF_PROMOTION"), (bypass_plan, "SUPERVISOR_ROUTE")):
        try:
            module.prepare_packet("do not run", "TASK-3", planner=provider)
        except module.ProfileHold as error:
            assert reason in str(error)
        else:
            raise AssertionError("Unsafe plan must fail closed")


def test_private_file_cli_output_contains_no_instruction(tmp_path):
    source = tmp_path / "private.txt"
    source.write_text("PRIVATE-DO-NOT-COPY-RAW", encoding="utf-8")
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--instruction-file", str(source), "--task-id", "TASK-4"],
        text=True, capture_output=True, check=False,
    )
    assert done.returncode == 0, done.stderr
    assert "PRIVATE-DO-NOT-COPY-RAW" not in done.stdout
    output = json.loads(done.stdout)
    assert output["authorization"]["owner_decision"] == "PENDING"
    assert output["state"] == "REVIEW_ONLY_NOT_DISPATCHED"


def test_plugin_selector_is_generated_and_profile_is_additive():
    selector = json.loads((ROOT / "plugins/packages/achilles/references/selector.json").read_text())
    source = json.loads((ROOT / "cgx/domain_templates/plugin_selector_registry.json").read_text())
    assert selector["profile"] == source["selectors"]["achilles"]
    assert selector["profile"]["default_domain"] == "emassc"
    assert (ROOT / "cgx/domain_templates/achilles_owner_operator_profile.json").is_file()


def test_unknown_supervisor_floor_and_missing_proof_fail_closed():
    def injected_floor(instruction, task_id):
        result = planned(instruction, task_id)
        result["floor_sequence"] = ["Neo", "UnapprovedTool", "Morpheus"]
        return result
    def proof_disabled(instruction, task_id):
        result = planned(instruction, task_id)
        result["proof_required"] = False
        return result
    def duplicate_gate(instruction, task_id):
        result = planned(instruction, task_id)
        result["floor_sequence"] = ["Neo", "Architect", "Architect", "Morpheus"]
        return result
    for provider, reason in ((injected_floor, "SUPERVISOR_ROUTE"),
                             (proof_disabled, "SUPERVISOR_PROOF"),
                             (duplicate_gate, "SUPERVISOR_ROUTE")):
        try:
            module.prepare_packet("review only", "TASK-NEGATIVE", planner=provider)
        except module.ProfileHold as error:
            assert reason in str(error)
        else:
            raise AssertionError("Supervisor negative case must fail closed")
