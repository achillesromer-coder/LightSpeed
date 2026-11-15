"""Source-only Achilles owner packet tests. No host, model, credentials or DB."""
from __future__ import annotations
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_achilles_owner_packet.py"
spec = importlib.util.spec_from_file_location("achilles_owner_packet", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def planned(instruction, task_id):
    return {
        "workflow_id": f"cognigrex-{task_id}-{module._hash(instruction)[:12]}",
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



def test_missing_or_unbound_supervisor_instruction_digest_fails_closed():
    # Review packets cannot inherit proof from a planner that omits the
    # source instruction binding, even when its route and proof flag look safe.
    for invalid_digest in (None, "", "0" * 64):
        def unbound_plan(instruction, task_id):
            result = planned(instruction, task_id)
            result["instruction_sha256"] = invalid_digest
            return result
        with pytest.raises(module.ProfileHold, match="SUPERVISOR_INSTRUCTION_BINDING_HOLD"):
            module.prepare_packet("private review only", "TASK-DIGEST-NEG", planner=unbound_plan)


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


@pytest.mark.parametrize("section,bad", [
    ("identity", []), ("identity", "foreign"),
    ("authority", [1]), ("authority", True),
    ("lifecycle", ["promoted"]), ("lifecycle", "released"),
])
def test_profile_section_shape_and_hold_register_fail_closed(tmp_path, section, bad):
    profile = module.load_profile()
    profile[section] = bad
    candidate = tmp_path / "untrusted-profile.json"
    candidate.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(module.ProfileHold, match="ACHILLES_PROFILE_SECTION_SHAPE_HOLD"):
        module.load_profile(candidate)


@pytest.mark.parametrize("issues", [
    [], [40, 154, 158, 161], [40, 154, 158, 161, True],
    "40,154,158,161,209", None,
])
def test_missing_or_malformed_standing_hold_register_is_rejected(tmp_path, issues):
    profile = module.load_profile()
    profile["open_issues"] = issues
    candidate = tmp_path / "untrusted-profile.json"
    candidate.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(module.ProfileHold, match="ACHILLES_PROFILE_HOLD_REGISTER_HOLD"):
        module.load_profile(candidate)


@pytest.mark.parametrize("name", [None, [], ""])
def test_invalid_owner_profile_name_is_rejected(tmp_path, name):
    profile = module.load_profile()
    profile["identity"]["proposed_profile_name"] = name
    candidate = tmp_path / "untrusted-profile.json"
    candidate.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(module.ProfileHold, match="ACHILLES_PROFILE_NAME_HOLD"):
        module.load_profile(candidate)


@pytest.mark.parametrize("section,key,value", [
    ("authority", "automatic_rights_grants", True),
    ("lifecycle", "stage", "NATIVE_ADMITTED"),
    ("lifecycle", "evidence_ceiling", "HOST_VERIFIED"),
    ("lifecycle", "active_host_installation", "VERIFIED"),
])
def test_review_profile_lifecycle_and_rights_escalation_fail_closed(tmp_path, section, key, value):
    # A source-only profile cannot silently claim higher authority than its
    # explicit review envelope, even when other no-self-approval flags remain.
    profile = module.load_profile()
    profile[section][key] = value
    candidate = tmp_path / "untrusted-profile.json"
    candidate.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(module.ProfileHold, match="ACHILLES_PRIVILEGE_ESCALATION_HOLD"):
        module.load_profile(candidate)

def test_priority_suffix_task_binding_not_inherited():
    def swapped(instruction, task_id):
        return planned(instruction, "ACHILLES-UNISPACE-DELIVERY-REVIEW-001b")
    with pytest.raises(module.ProfileHold, match="TASK_BINDING_HOLD"):
        module.prepare_packet("same work", "ACHILLES-UNISPACE-DELIVERY-REVIEW-001a", planner=swapped)
    a=module.prepare_packet("same work", "ACHILLES-UNISPACE-DELIVERY-REVIEW-001a", planner=planned)
    b=module.prepare_packet("same work", "ACHILLES-UNISPACE-DELIVERY-REVIEW-001b", planner=planned)
    assert a["idempotency_fingerprint"]!=b["idempotency_fingerprint"]
    assert not a["execution_request"]["execute"] and not b["execution_request"]["execute"]

def test_owner_packet_composition_and_scoped_skill_review():
    from copy import deepcopy
    from lightspeed_runtime.cgx_capability_registry import capability_interop_review, CapabilityRegistryError
    view=capability_interop_review("Achilles")
    keys=("skill:cgx-capability-router","skill:cgx-handshake","role:achilles")
    task="ACHILLES-UNISPACE-DELIVERY-REVIEW-001a"
    def prepare(refs=keys, stamp=view["view_sha256"]):
        return module.prepare_packet("private instruction",task,planner=planned,
            skill_references=refs,expected_skill_view_sha256=stamp)
    packet=prepare()
    assert packet==prepare(keys[::-1])
    assert packet["idempotency_fingerprint"]!=prepare(keys[:1])["idempotency_fingerprint"]
    assert packet["idempotency_fingerprint"]!=module.prepare_packet("private instruction",task,planner=planned)["idempotency_fingerprint"]
    assert "private instruction" not in json.dumps(packet)
    assert not packet["skill_review"]["raw_skill_payload_persisted"]
    stamp=packet["skill_review"]["composition"]["composition_sha256"]
    def auth(t,k,s,h):return t==task and k==keys[0] and s=="fixture-scope" and h==stamp
    def read(p=packet,selected=None,scope="fixture-scope",t=task):
        return module.hydrate_packet_skill_review(p,expected_task_id=t,
            expected_composition_sha256=stamp,selected_skills=selected or [keys[0]],
            scope_revision=scope,max_bytes=100000,authorise=auth)
    raw,receipt=read()
    assert list(raw)==[keys[0]]
    assert receipt["payload_bytes"]==len(raw[keys[0]]) and not receipt["execution_authorized"]
    assert raw[keys[0]].decode("utf-8") not in json.dumps(packet)
    with pytest.raises(PermissionError):read(selected=[keys[1]])
    with pytest.raises(PermissionError):read(scope="revoked")
    with pytest.raises(module.ProfileHold):read(t=task+"b")
    bad=deepcopy(packet);bad["authorization"]["lease_verified"]=True
    with pytest.raises(module.ProfileHold):read(bad)
    bad=deepcopy(packet);bad["skill_review"]["composition"]["authority_transfer"]=True
    with pytest.raises(CapabilityRegistryError):read(bad)
    with pytest.raises(module.ProfileHold):prepare(stamp="0"*64)
    with pytest.raises(module.ProfileHold):prepare(("role:smith",))



def test_paired_fidelity_trial_predeclared_and_fail_closed():
    from lightspeed_runtime.cgx_capability_registry import capability_interop_review
    v=capability_interop_review("Achilles")
    plan=module.prepare_skill_fidelity_trial("review-001a",expected_view_sha256=v["view_sha256"],
        model="qwen3:8b",sparse_skills=["skill:cgx-capability-router","skill:cgx-handshake"])
    stamp=plan["trial_sha256"]
    prompts=module.build_skill_trial_prompts(plan,expected_trial_sha256=stamp,scope_revision="fixture",
                                           authorise=lambda *a:True)
    assert len(prompts)==16
    assert all("expected" not in p for p in prompts)
    expected={c["case_id"]:c["expected"] for c in plan["cases"]}
    obs=[dict(case_id=p["case_id"],arm=p["arm"],model=plan["model"],settings=plan["settings"],
        prompt_sha256=p["prompt_sha256"],result=expected[p["case_id"]],
        prompt_tokens=100 if p["arm"]=="sparse" else 500,output_tokens=12,latency_ms=100) for p in prompts]
    commitment=module.skill_trial_prompt_commitment(plan,prompts)
    def score(rows):return module.score_skill_fidelity_trial(plan,expected_trial_sha256=stamp,prompts=prompts,observations=rows,expected_prompt_commitment=commitment)
    with pytest.raises(module.ProfileHold):
        module.score_skill_fidelity_trial(plan,expected_trial_sha256=stamp,prompts=prompts[::-1],
            observations=obs,expected_prompt_commitment=commitment)
    receipt=score(obs)
    assert receipt["candidate_thresholds_met"] and not receipt["live_reasoning_fidelity_verified"]
    with pytest.raises(module.ProfileHold):score(obs[:-1])
    with pytest.raises(module.ProfileHold):score([dict(obs[0],model="other")]+obs[1:])
    with pytest.raises(module.ProfileHold):score([dict(obs[0],prompt_sha256="0"*64)]+obs[1:])
    bad=[dict(o,result={"decision":"review_only","code":"allowed"}) if o["case_id"]=="stale-access" else o for o in obs]
    assert not score(bad)["candidate_thresholds_met"]
    assert score(bad)["counts"]["sparse"]["unsafe_false_allow"]==1
    with pytest.raises(PermissionError):
        module.build_skill_trial_prompts(plan,expected_trial_sha256=stamp,scope_revision="fixture",authorise=lambda *a:False)


def test_common_inference_preflight_never_grants_execution():
    def gate(**overrides):
        return module.assess_common_inference_admission(**dict(dict(resident_active=True,common_gate_verified=False,
            active_session_count=0,available_gib=13.53,reserve_gib=6.4,model_working_set_gib=4.9),**overrides))
    assert gate()["state"]=="HOLD"
    assert "RAM_RESERVE_HOLD" in gate(available_gib=8)["holds"]
    assert "ACTIVE_INFERENCE_SESSION" in gate(active_session_count=1)["holds"]
    assert gate(common_gate_verified=True)["state"]=="PREFLIGHT_ONLY_GATE_ACQUISITION_REQUIRED"
    assert not gate(common_gate_verified=True)["execution_authorized"]
    with pytest.raises(module.ProfileHold):gate(active_session_count=True)



def test_trial_adapter_requires_common_gate_and_serial_exact_binding(tmp_path):
    from lightspeed_runtime.cgx_capability_registry import capability_interop_review
    from lightspeed_runtime.local_floor_runner import CommonInferenceSession,LocalFloorRunnerError
    v=capability_interop_review("Achilles")
    plan=module.prepare_skill_fidelity_trial("review-001a",expected_view_sha256=v["view_sha256"],
        model="qwen3:8b",sparse_skills=["skill:cgx-capability-router","skill:cgx-handshake"])
    stamp=plan["trial_sha256"]
    prompts=module.build_skill_trial_prompts(plan,expected_trial_sha256=stamp,scope_revision="fixture",
        authorise=lambda *a:True)
    commitment=module.skill_trial_prompt_commitment(plan,prompts)
    expected={c["case_id"]:c["expected"] for c in plan["cases"]}
    path=tmp_path/"shared.lock";calls=[];state={"allowed":True}
    def gate(task="review-001a"):
        return CommonInferenceSession(path,task_id=task,scope_revision="fixture",
            authorise=lambda *a:state["allowed"],resources_ready=lambda:True)
    def adapter(q):
        assert path.is_file() and "expected" not in q
        calls.append((q["case_id"],q["arm"]))
        return {k:q[k] for k in ("case_id","arm","model","settings","prompt_sha256")} | {
            "result":expected[q["case_id"]],"prompt_tokens":100 if q["arm"]=="sparse" else 500,
            "output_tokens":10,"latency_ms":100}
    def run(g,inv=adapter):
        return module.run_skill_trial_with_adapter(plan,expected_trial_sha256=stamp,prompts=prompts,
           expected_prompt_commitment=commitment,common_session=g,invoke=inv)
    with pytest.raises(module.ProfileHold):run(gate("wrong"))
    state["allowed"]=False
    with pytest.raises(LocalFloorRunnerError):run(gate())
    assert not calls and not path.exists()
    state["allowed"]=True
    assert run(gate())["candidate_thresholds_met"] and len(calls)==16 and not path.exists()
    def revoke(q):
        result=adapter(q);state["allowed"]=False;return result
    with pytest.raises(LocalFloorRunnerError):run(gate(),revoke)
    assert len(calls)==17 and not path.exists()
    state["allowed"]=True
    def lost(q):raise TimeoutError("fixture lost response")
    with pytest.raises(TimeoutError):run(gate(),lost)
    assert json.loads(path.read_text(encoding="utf-8"))["state"]=="RECOVERY_HOLD_SERVER_OUTCOME_UNCERTAIN"
    with pytest.raises(LocalFloorRunnerError):run(gate())
