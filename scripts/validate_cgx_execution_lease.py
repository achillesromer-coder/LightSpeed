#!/usr/bin/env python3
from __future__ import annotations
from datetime import UTC, datetime, timedelta
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_cgx_agent_runtime import validate_lease

def base_lease():
    now=datetime.now(UTC)
    return {
      "lease_id":"fixture:lease:prelaunch",
      "lease_class":"DIGITAL_WRITE",
      "state":"ACTIVE",
      "issued_by":"fixture:root-authority",
      "subject_agent":"Neo",
      "valid_from":(now-timedelta(minutes=5)).isoformat(),
      "valid_until":(now+timedelta(hours=1)).isoformat(),
      "domains":["romer"],
      "execution_depths":["execute","publish"],
      "max_cascade_class":"C3",
      "allowed_floors":["Neo"],
      "scope":{"task_ids":["CGX-LAUNCH-006"],"action_classes":["execute","publish"]},
      "revocable":True,
      "rollback_or_recovery_ref":"fixture:rollback",
      "assurance_receipt_ref":"fixture:assurance",
      "custodial_receipt_ref":"fixture:custodial",
      "risk_acceptance_ref":"fixture:risk",
      "authority_phase":"PRE_LAUNCH",
      "authority_phase_ref":"cgx://internal/governance/root-authority-phase"
    }

def check(lease, execution_depth="execute", action_class="execute", consequential=True, project_id=None, object_id=None, tool_scope=None, configuration_id=None, execution_class="DIGITAL_WRITE"):
    return validate_lease(
      lease,
      agent_id="Neo",
      domain="romer",
      execution_depth=execution_depth,
      cascade_class="C2",
      task_id="CGX-LAUNCH-006",
      project_id=project_id,
      action_class=action_class,
      execution_class=execution_class,
      planned_floors=["Neo"],
      consequential=consequential,
      object_id=object_id,
      tool_scope=tool_scope,
      configuration_id=configuration_id,
    )

def main():
    failures=[]
    x=base_lease()
    ok,reasons,_=check(x)
    if ok or "lease-root-authority-receipt-ref-missing" not in reasons:
        failures.append("prelaunch consequential lease did not require root-authority receipt")

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    ok,reasons,_=check(x)
    if not ok:
        failures.append("complete prelaunch consequential lease failed: "+",".join(reasons))

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    ok,reasons,_=check(x,execution_depth="publish",action_class="publish")
    if ok or "lease-release-receipt-ref-missing" not in reasons:
        failures.append("publish lease did not require release receipt")

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    x["release_receipt_ref"]="fixture:release"
    ok,reasons,_=check(x,execution_depth="publish",action_class="publish")
    if not ok:
        failures.append("complete publish lease failed: "+",".join(reasons))

    x=base_lease()
    x["authority_phase"]="DISTRIBUTED_OPERATION"
    x.pop("root_authority_receipt_ref",None)
    ok,reasons,_=check(x)
    if not ok:
        failures.append("distributed-operation lease incorrectly inherited prelaunch root receipt requirement: "+",".join(reasons))

    # Synthetic scope-only regressions: no host call, signature or DBR acceptance.
    scope_negatives = [
        ("scope-absent", None, "lease-scope-invalid"),
        ("scope-not-object", [], "lease-scope-invalid"),
        ("task-allowlist-absent", {"action_classes":["execute"]}, "lease-task-scope-missing"),
        ("task-allowlist-empty", {"task_ids":[], "action_classes":["execute"]}, "lease-task-scope-invalid"),
        ("action-allowlist-absent", {"task_ids":["CGX-LAUNCH-006"]}, "lease-action-class-scope-missing"),
        ("action-allowlist-empty", {"task_ids":["CGX-LAUNCH-006"], "action_classes":[]}, "lease-action-class-scope-invalid"),
        ("task-not-allowed", {"task_ids":["OTHER"], "action_classes":["execute"]}, "lease-task-out-of-scope:CGX-LAUNCH-006"),
        ("action-not-allowed", {"task_ids":["CGX-LAUNCH-006"], "action_classes":["publish"]}, "lease-action-class-out-of-scope:execute"),
    ]
    for label, scope_value, expected_reason in scope_negatives:
        x=base_lease()
        x["root_authority_receipt_ref"]="fixture:root-approval"
        if scope_value is None:
            x.pop("scope",None)
        else:
            x["scope"]=copy.deepcopy(scope_value)
        ok,reasons,_=check(x)
        if ok or expected_reason not in reasons:
            failures.append(label + ": expected " + expected_reason + "; got " + ",".join(reasons))

    # Invalid envelope/identity types must fail closed, even when other
    # lease fields look valid. These are NOT signature-verification tests.
    for bad_envelope in ([], "lease", 42):
        ok,reasons,_=check(bad_envelope)
        if ok or "execution-lease-invalid" not in reasons:
            failures.append("non-object lease envelope accepted: " + repr(bad_envelope))
    malformed_identity = [
        ("lease_id", None, "lease-lease-id-invalid"),
        ("lease_id", "", "lease-lease-id-invalid"),
        ("lease_id", 17, "lease-lease-id-invalid"),
        ("lease_id", "   ", "lease-lease-id-invalid"),
        ("issued_by", None, "lease-issued-by-invalid"),
        ("issued_by", [], "lease-issued-by-invalid"),
        ("issued_by", "   ", "lease-issued-by-invalid"),
        ("subject_agent", None, "lease-subject-agent-invalid"),
        ("subject_agent", {}, "lease-subject-agent-invalid"),
        ("subject_agent", "   ", "lease-subject-agent-invalid"),
    ]
    for field, bad_value, expected_reason in malformed_identity:
        x=base_lease()
        x["root_authority_receipt_ref"]="fixture:root-approval"
        x[field]=copy.deepcopy(bad_value)
        ok,reasons,_=check(x)
        if ok or expected_reason not in reasons:
            failures.append(field + " invalid identity type not rejected: " + ",".join(reasons))

    # Truthy non-string receipt references must not satisfy structural gates.
    # These are source-only typed-reference checks, NOT proof of signature,
    # revocation registry, issuer trust or native DBR admission.
    typed_reference_cases = (
        ("authority_phase_ref", "execute", "lease-authority-phase-ref-missing"),
        ("rollback_or_recovery_ref", "execute", "lease-rollback-or-recovery-ref-missing"),
        ("assurance_receipt_ref", "execute", "lease-assurance-receipt-ref-missing"),
        ("custodial_receipt_ref", "execute", "lease-custodial-receipt-ref-missing"),
        ("risk_acceptance_ref", "execute", "lease-risk-acceptance-ref-missing"),
        ("root_authority_receipt_ref", "execute", "lease-root-authority-receipt-ref-missing"),
        ("release_receipt_ref", "publish", "lease-release-receipt-ref-missing"),
        ("stop_authority_ref", "execute", "lease-stop-authority-missing"),
        ("safe_state_ref", "execute", "lease-safe-state-missing"),
    )
    for field, depth, expected in typed_reference_cases:
        for bad in (17, ["fixture:reference"], "   ", "\x00fixture:reference", "fixture:reference\nforged"):
            x=base_lease()
            x["root_authority_receipt_ref"]="fixture:root-approval"
            x["release_receipt_ref"]="fixture:release"
            x["stop_authority_ref"]="fixture:stop"
            x["safe_state_ref"]="fixture:safe"
            is_external=field in {"stop_authority_ref", "safe_state_ref"}
            if is_external:
                x["lease_class"]="EXTERNAL_ACTION"
            x[field]=copy.deepcopy(bad)
            ok,reasons,_=check(x, execution_depth=depth, action_class=depth,
                               execution_class="EXTERNAL_ACTION" if is_external else "DIGITAL_WRITE")
            if ok or expected not in reasons:
                failures.append(f"typed receipt {field} accepted {bad!r}: {reasons}")

    # Actual CLI negative bindings: malformed truthy references must return 4
    # without supervisor invocation. No signed authority or host is exercised.
    with tempfile.TemporaryDirectory(prefix="cgx-lease-typed-refs-") as temp:
        lease_path=Path(temp)/"synthetic-typed-ref.json"
        for field, depth, bad, expected in (
            ("authority_phase_ref", "inspect", 17, "lease-authority-phase-ref-missing"),
            ("release_receipt_ref", "publish", ["fixture:release"], "lease-release-receipt-ref-missing"),
            ("authority_phase_ref", "inspect", "\x00fixture:phase", "lease-authority-phase-ref-missing"),
            ("release_receipt_ref", "publish", "fixture:release\nforged", "lease-release-receipt-ref-missing"),
        ):
            x=base_lease()
            x["root_authority_receipt_ref"]="fixture:root-approval"
            x["execution_depths"].append("inspect")
            x["scope"]["action_classes"].append("inspect")
            x[field]=bad
            lease_path.write_text(json.dumps(x),encoding="utf-8")
            argv=[sys.executable,str(ROOT/"scripts"/"run_cgx_agent_runtime.py"),
                  "--instruction","synthetic typed reference rejection",
                  "--domain","romer","--execution-depth",depth,
                  "--execution-class","COMPUTE_ONLY","--agent-id","Neo",
                  "--task-id","CGX-LAUNCH-006","--execute",
                  "--execution-lease-json",str(lease_path)]
            result=subprocess.run(argv,capture_output=True,text=True,timeout=15,check=False)
            try:
                receipt=json.loads(result.stdout)
                reasons=receipt["execution_lease"]["reasons"]
            except (ValueError,KeyError,TypeError):
                receipt={}
                reasons=[]
            if (result.returncode!=4 or expected not in reasons
                    or receipt.get("supervisor_receipt") is not None):
                failures.append(f"CLI typed ref {field} did not fail closed: "
                                +repr({"exit":result.returncode,"reasons":reasons,
                                       "supervisor":receipt.get("supervisor_receipt"),
                                       "stderr":result.stderr[:200]}))

    # Typed allowlists reject malformed and mixed-type values, even when the
    # requested legitimate entry is also present. Source-only; not issuer proof.
    malformed_allowlists = [
        ("domains", ["romer", 42], "lease-domains-allowlist-invalid"),
        ("domains", "romer", "lease-domains-allowlist-invalid"),
        ("domains", None, "lease-domains-allowlist-invalid"),
        ("execution_depths", ["execute", None], "lease-execution-depths-allowlist-invalid"),
        ("execution_depths", "execute", "lease-execution-depths-allowlist-invalid"),
        ("allowed_floors", ["Neo", {"unexpected": "claim"}], "lease-allowed-floors-allowlist-invalid"),
        ("allowed_floors", ["Neo", " "], "lease-allowed-floors-allowlist-invalid"),
        ("allowed_floors", {"0": "Neo"}, "lease-allowed-floors-allowlist-invalid"),
    ]
    for field, bad_value, expected_reason in malformed_allowlists:
        x=base_lease()
        x["root_authority_receipt_ref"]="fixture:root-approval"
        x[field]=copy.deepcopy(bad_value)
        ok,reasons,_=check(x)
        if ok or expected_reason not in reasons:
            failures.append(field + " malformed typed allowlist was not rejected: " + ",".join(reasons))

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    ok,reasons,_=check(x,project_id="PROJECT-ONE")
    if ok or "lease-project-scope-missing" not in reasons:
        failures.append("requested project without allowlist was not rejected")
    x["scope"]["project_ids"]=["PROJECT-ONE"]
    ok,reasons,_=check(x,project_id="PROJECT-ONE")
    if not ok:
        failures.append("explicitly scoped project fixture failed: " + ",".join(reasons))

    # Request-bound CCC tool/object/configuration scopes. These checks verify
    # typed structural allowlists, NOT signature, revocation, nonce consumption,
    # host permission, tool installation or signed DBR admission.
    for field, argument, value, label in (
        ("object_ids", "object_id", "cgx://review/object-1", "object"),
        ("tool_scopes", "tool_scope", "ccc:review:science.query", "tool"),
        ("configuration_ids", "configuration_id", "review-config-1", "configuration"),
    ):
        x=base_lease()
        x["root_authority_receipt_ref"]="fixture:root-approval"
        ok,reasons,_=check(x, **{argument:value})
        if ok or f"lease-{label}-scope-missing" not in reasons:
            failures.append(f"{label}: requested scope without explicit allowlist accepted: {reasons}")

        x["scope"][field]=[value]
        ok,reasons,_=check(x, **{argument:value})
        if not ok:
            failures.append(f"{label}: explicit requested scope rejected: {reasons}")

        x["scope"][field]=["other"]
        ok,reasons,_=check(x, **{argument:value})
        if ok or f"lease-{label}-out-of-scope:{value}" not in reasons:
            failures.append(f"{label}: out-of-scope request accepted: {reasons}")

        x["scope"][field]=[value, None]
        ok,reasons,_=check(x, **{argument:value})
        if ok or f"lease-{label}-scope-invalid" not in reasons:
            failures.append(f"{label}: mixed-type allowlist accepted: {reasons}")

        x["scope"][field]=[value]
        ok,reasons,_=check(x)
        if ok or f"lease-scope-requires-{label}" not in reasons:
            failures.append(f"{label}: declared scope without request target accepted: {reasons}")

    # Exercise the real CLI's request-to-validator binding with intentionally
    # mismatched synthetic scopes. The invalid lease exits before model/runtime
    # invocation. This does not authenticate issuer, host, CCC tool or DBR.
    x=base_lease()
    x["execution_depths"].append("inspect")
    x["scope"]["action_classes"].append("inspect")
    x["scope"].update({
        "object_ids":["cgx://review/allowed-object"],
        "tool_scopes":["ccc:review:allowed-tool"],
        "configuration_ids":["review-allowed-config"],
    })
    with tempfile.TemporaryDirectory(prefix="cgx-lease-scope-negative-") as temp:
        lease_path=Path(temp)/"synthetic-lease.json"
        lease_path.write_text(json.dumps(x),encoding="utf-8")
        for label, flag, requested in (
            ("object","--object-id","cgx://review/denied-object"),
            ("tool","--tool-scope","ccc:review:denied-tool"),
            ("configuration","--configuration-id","review-denied-config"),
        ):
            targets={
                "--object-id":"cgx://review/allowed-object",
                "--tool-scope":"ccc:review:allowed-tool",
                "--configuration-id":"review-allowed-config",
            }
            targets[flag]=requested
            argv=[sys.executable,str(ROOT/"scripts"/"run_cgx_agent_runtime.py"),
                  "--instruction","synthetic source-review scope rejection",
                  "--domain","romer","--execution-depth","inspect",
                  "--execution-class","COMPUTE_ONLY","--agent-id","Neo",
                  "--task-id","CGX-LAUNCH-006","--execute",
                  "--execution-lease-json",str(lease_path)]
            for name,value in targets.items():
                argv.extend((name,value))
            result=subprocess.run(argv,capture_output=True,text=True,timeout=15,check=False)
            try:
                receipt=json.loads(result.stdout)
                reasons=receipt["execution_lease"]["reasons"]
            except (ValueError,KeyError,TypeError):
                reasons=[]
            expected=f"lease-{label}-out-of-scope:{requested}"
            if result.returncode!=4 or expected not in reasons:
                failures.append(f"CLI {label} negative failed: code={result.returncode}, reasons={reasons}, stderr={result.stderr[:200]}")

    # CLI omitted targets must not bypass lease-declared scope. The existing
    # fixture declares all three scoped identities, but the command omits
    # target flags. A fail-closed exit must occur before any supervisor call.
    x=base_lease()
    x["execution_depths"].append("inspect")
    x["scope"]["action_classes"].append("inspect")
    x["scope"].update({
        "object_ids":["cgx://review/allowed-object"],
        "tool_scopes":["ccc:review:allowed-tool"],
        "configuration_ids":["review-allowed-config"],
    })
    with tempfile.TemporaryDirectory(prefix="cgx-lease-omitted-targets-") as temp:
        lease_path=Path(temp)/"synthetic-lease.json"
        lease_path.write_text(json.dumps(x),encoding="utf-8")
        argv=[sys.executable,str(ROOT/"scripts"/"run_cgx_agent_runtime.py"),
              "--instruction","synthetic omitted-target scope rejection",
              "--domain","romer","--execution-depth","inspect",
              "--execution-class","COMPUTE_ONLY","--agent-id","Neo",
              "--task-id","CGX-LAUNCH-006","--execute",
              "--execution-lease-json",str(lease_path)]
        result=subprocess.run(argv,capture_output=True,text=True,timeout=15,check=False)
        try:
            receipt=json.loads(result.stdout)
            reasons=receipt["execution_lease"]["reasons"]
        except (ValueError,KeyError,TypeError):
            receipt={}
            reasons=[]
        expected={"lease-scope-requires-object","lease-scope-requires-tool",
                  "lease-scope-requires-configuration"}
        if (result.returncode!=4 or not expected.issubset(set(reasons))
                or receipt.get("supervisor_receipt") is not None):
            failures.append("CLI omitted target scope not fail-closed before supervisor: "
                            +repr({"exit":result.returncode,"reasons":reasons,
                                   "supervisor":receipt.get("supervisor_receipt"),
                                   "stderr":result.stderr[:200]}))

    # T1 temporal/state fail-closed negatives at both validator and actual CLI.
    # These are synthetic structural checks, NOT signature, issuer, revocation
    # registry, durable replay, host or DBR verification.
    now=datetime.now(UTC)
    t1_cases=(
        ("expired", {
            "valid_from":(now-timedelta(hours=2)).isoformat(),
            "valid_until":(now-timedelta(hours=1)).isoformat(),
        }, "lease-outside-validity-window"),
        ("not-yet-valid", {
            "valid_from":(now+timedelta(hours=1)).isoformat(),
            "valid_until":(now+timedelta(hours=2)).isoformat(),
        }, "lease-outside-validity-window"),
        ("inverted-window", {
            "valid_from":(now+timedelta(hours=1)).isoformat(),
            "valid_until":(now-timedelta(hours=1)).isoformat(),
        }, "lease-invalid-time-window"),
        ("naive-expiry", {
            "valid_until":(now+timedelta(hours=1)).replace(tzinfo=None).isoformat(),
        }, "lease-time-invalid"),
        ("revoked-state", {"state":"REVOKED"}, "lease-not-active:REVOKED"),
    )
    with tempfile.TemporaryDirectory(prefix="cgx-t1-lease-negatives-") as temp:
        lease_path=Path(temp)/"synthetic-t1-lease.json"
        for label, changes, expected in t1_cases:
            x=base_lease()
            x["root_authority_receipt_ref"]="fixture:root-approval"
            x["execution_depths"].append("inspect")
            x["scope"]["action_classes"].append("inspect")
            x.update(changes)
            ok,reasons,_=check(x)
            if ok or expected not in reasons:
                failures.append(f"T1 {label}: validator did not reject: {reasons}")
            lease_path.write_text(json.dumps(x),encoding="utf-8")
            argv=[sys.executable,str(ROOT/"scripts"/"run_cgx_agent_runtime.py"),
                  "--instruction","synthetic T1 temporal/state rejection",
                  "--domain","romer","--execution-depth","inspect",
                  "--execution-class","COMPUTE_ONLY","--agent-id","Neo",
                  "--task-id","CGX-LAUNCH-006","--execute",
                  "--execution-lease-json",str(lease_path)]
            result=subprocess.run(argv,capture_output=True,text=True,timeout=15,check=False)
            try:
                receipt=json.loads(result.stdout)
                cli_reasons=receipt["execution_lease"]["reasons"]
            except (ValueError,KeyError,TypeError):
                receipt={}
                cli_reasons=[]
            if (result.returncode!=4 or expected not in cli_reasons
                    or receipt.get("supervisor_receipt") is not None):
                failures.append(f"T1 {label}: CLI failed closed incorrectly: "
                                +repr({"exit":result.returncode,"reasons":cli_reasons,
                                       "supervisor":receipt.get("supervisor_receipt"),
                                       "stderr":result.stderr[:200]}))

    print({"status":"PASS" if not failures else "FAIL","failures":failures})
    return 1 if failures else 0

if __name__=="__main__":
    raise SystemExit(main())
