#!/usr/bin/env python3
"""Read-only, fail-closed review of cross-space UniSpace handoff dependencies.

This module is NOT a second CGX resolver, scheduler, native DBR, or release
controller. It checks the supplied 51-task source-review projection and the
existing cgx_unispace_facet_mesh output. It never promotes status or dispatches.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "CGX-UNISPACE-CROSSSPACE-GATE-REGISTRY/0.1"
RECEIPT_SCHEMA = "CGX-UNISPACE-CROSSSPACE-SOURCE-REVIEW/0.1"
ROOT = "cgx:root:cognigrex"
MESH_SCHEMA = "CGX-UNISPACE-SINGLE-ROOT-FACET-MESH/0.1"
REGISTRY = Path("cgx/review/unispace_crossspace_gate_register_v0_1.json")
EXPECTED_SHA256 = "748c18632d6e2ce0a685da5498d83ed585cfc1f5af8b1658eec2128db82403a1"
CHECKPOINT_SHA256 = "634695accc767f7a25e41e10335cc8b7a6c7f988cbaf4b024e700c92e1d522fa"
SPACES = {
    "PrintSpace": (16, "print_space"),
    "FileSpace": (6, "file_space"),
    "DataSpace": (6, "data_space"),
    "SocialSpace": (6, "social_space"),
    "IntelligenceSpace": (6, "intelligence_space"),
    "UniSpace": (7, None),
    "ArchiveAndLegacy": (4, None),
}
EXPECTED_IDS = (
    [f"SW-{i:02d}" for i in range(1, 8)] +
    [f"NATIVE-{i:02d}" for i in range(1, 5)] +
    [f"PHYS-{i:02d}" for i in range(1, 6)] +
    [f"FS-{i:02d}" for i in range(1, 7)] +
    [f"DS-{i:02d}" for i in range(1, 7)] +
    [f"SS-{i:02d}" for i in range(1, 7)] +
    [f"IM-{i:02d}" for i in range(1, 7)] +
    [f"US-{i:02d}" for i in range(1, 8)] +
    [f"AR-{i:02d}" for i in range(1, 5)]
)
TOP_KEYS = frozenset({
    "schema", "canonical_root", "facet_mesh_schema", "checkpoint_sha256",
    "observation", "source_count", "source_verified_printspace_count",
    "proposed_crossspace_count", "source_pr_heads",
    "source_heads_are_currently_authenticated", "authority", "task_groups",
    "dependency_provenance", "archive_candidates_unchanged", "schedules_changed", "status",
})
TASK_KEYS = frozenset({
    "id", "space", "label", "provenance", "state",
    "proposed_dependencies", "source_facet", "closure_gate",
    "owner_approval_observed", "effectful_action_authorised",
})
AUTH_KEYS = frozenset({
    "owner_acceptance", "public_release", "native_dbr_write", "native_hydration",
    "mint", "machine_control", "archive_delete", "new_root", "new_scheduler",
    "file_space_product_phase_active",
})
REF_RE = re.compile(r"[a-f0-9]{40}\Z")
MAX_BYTES = 64000


class CrossSpaceHold(ValueError):
    """The source-review inputs failed an invariant; no state mutation allowed."""


def _hold_if(cond: bool, reason: str) -> None:
    if cond:
        raise CrossSpaceHold(reason)


def validate_registry(obj: object) -> dict:
    """Validate logical invariants, not live native authority or provenance."""
    _hold_if(not isinstance(obj, dict) or set(obj) != TOP_KEYS,
             "registry schema fields or authority extras changed")
    _hold_if(obj["schema"] != SCHEMA or obj["canonical_root"] != ROOT or
             obj["facet_mesh_schema"] != MESH_SCHEMA or
             obj["checkpoint_sha256"] != CHECKPOINT_SHA256,
             "wrong original parent or checkpoint")
    _hold_if(obj["status"] != "SOURCE_REVIEW_HANDOFF_OPEN_NO_NATIVE_ADMISSION" or
             obj["dependency_provenance"] != "PROPOSED_SEQUENCE_NOT_INDEPENDENTLY_VERIFIED" or
             obj["source_heads_are_currently_authenticated"] is not False or
             obj["schedules_changed"] is not False,
             "source-only authority boundary changed")
    _hold_if(not isinstance(obj["authority"], dict) or
             set(obj["authority"]) != AUTH_KEYS or
             any(x is not False for x in obj["authority"].values()),
             "privileged action or product phase was promoted")
    heads = obj["source_pr_heads"]
    _hold_if(not isinstance(heads, dict) or
             set(heads) != {"205", "228", "229", "230", "232", "236"} or
             any(not isinstance(v, str) or not REF_RE.fullmatch(v)
                 for v in heads.values()),
             "source branch-head observations missing/invalid")
    _hold_if(type(obj["source_count"]) is not int or obj["source_count"] != 51 or
             obj["source_verified_printspace_count"] != 16 or
             obj["proposed_crossspace_count"] != 35 or
             obj["archive_candidates_unchanged"] != 3,
             "handoff task or archive count changed")
    tasks = obj["task_groups"]
    _hold_if(not isinstance(tasks, list) or len(tasks) != 51,
             "missing or extra handoff task groups")
    ids: dict[str, dict] = {}
    for i, task in enumerate(tasks):
        _hold_if(not isinstance(task, dict) or set(task) != TASK_KEYS,
                 "task schema changed, new authority or private field introduced")
        task_id = task["id"]
        _hold_if(task_id != EXPECTED_IDS[i] or task_id in ids,
                 "noncanonical, duplicated or reordered task ID")
        ids[task_id] = task
        space = task["space"]
        _hold_if(space not in SPACES or task["source_facet"] != SPACES[space][1],
                 "task points outside one canonical facet")
        provenance = ("OPEN_SOURCE_VERIFIED" if space == "PrintSpace"
                      else "PROPOSED_NEEDS_CURRENT_SOURCE_RECONCILIATION")
        _hold_if(task["provenance"] != provenance or
                 task["state"] != "OPEN_REVIEW_ONLY" or
                 task["closure_gate"] != "INDEPENDENT_SOURCE_AND_OWNER_EVIDENCE_REQUIRED" or
                 task["owner_approval_observed"] is not False or
                 task["effectful_action_authorised"] is not False or
                 not isinstance(task["label"], str) or
                 not 8 <= len(task["label"]) <= 180,
                 "unproven task was promoted or edited outside review")
        edges = task["proposed_dependencies"]
        _hold_if(not isinstance(edges, list) or len(edges) > 8 or
                 len(edges) != len(set(edges)) or
                 any(not isinstance(x, str) or x == task_id for x in edges),
                 "invalid dependency set")
    _hold_if(Counter(t["space"] for t in tasks) !=
             Counter({name: spec[0] for name, spec in SPACES.items()}),
             "missing canonical space tasks")
    visited, visiting = set(), set()
    def check(task_id: str) -> None:
        if task_id in visited:
            return
        _hold_if(task_id in visiting, "dependency cycle")
        _hold_if(task_id not in ids, "dependency escapes canonical handoff")
        visiting.add(task_id)
        for dep in ids[task_id]["proposed_dependencies"]:
            check(dep)
        visiting.remove(task_id)
        visited.add(task_id)
    for task_id in EXPECTED_IDS:
        check(task_id)
    return obj


def validate_source_mesh(document: object) -> dict:
    """Consume existing UniSpace facet mesh, never create a parallel one."""
    _hold_if(not isinstance(document, dict), "missing existing facet mesh")
    mesh = document.get("mesh", document)
    _hold_if(not isinstance(mesh, dict) or mesh.get("schema") != MESH_SCHEMA or
             mesh.get("canonical_root_id") != ROOT or
             mesh.get("state") != "SOURCE_CONTRACT_MESH_OBSERVED" or
             mesh.get("facet_count") != 5 or
             mesh.get("unique_contract_count") != 12 or
             mesh.get("unique_service_count") != 7,
             "existing root/facet source contract not observed")
    for name in ("new_root_created", "new_database_created", "model_weights_modified",
                 "native_execution_authorized", "mint_or_network_authorized",
                 "source_hydration_performed"):
        _hold_if(mesh.get(name) is not False, "facet mesh claims effectful action: " + name)
    facets = mesh.get("facets")
    _hold_if(not isinstance(facets, list) or len(facets) != 5 or
             {f.get("id") for f in facets if isinstance(f, dict)} !=
             {spec[1] for spec in SPACES.values() if spec[1]},
             "facet identity set incomplete")
    for facet in facets:
        _hold_if(facet.get("state") != "SOURCE_CONTRACTS_PRESENT" or
                 facet.get("execution_authorized") is not False or
                 facet.get("independent_native_admission") is not False,
                 "source facet was held or promoted")
    return mesh


def source_review(registry: dict, registry_sha256: str,
                  mesh_document: dict | None = None) -> dict:
    reg = validate_registry(registry)
    reviewed = validate_source_mesh(mesh_document) if mesh_document is not None else None
    tasks = reg["task_groups"]
    allowed_roots = [x["id"] for x in tasks if not x["proposed_dependencies"]]
    return {
        "schema": RECEIPT_SCHEMA, "state": "SOURCE_REVIEW_ONLY_51_TASKS_OPEN",
        "canonical_root": ROOT, "task_count": len(tasks),
        "source_verified_printspace_open": 16, "proposed_crossspace_open": 35,
        "group_counts": dict(sorted(Counter(x["space"] for x in tasks).items())),
        "source_register_sha256": registry_sha256,
        "source_mesh_observed": reviewed is not None,
        "source_contracts_present_not_native": reviewed is not None,
        "source_heads_verified_current": False,
        "proposed_independent_review_roots": allowed_roots,
        "all_task_groups_closed": False,
        "owner_acceptance_observed": False,
        "next_product_phase_authorised": False,
        "native_admitted": False,
        "archive_delete_authorised": False,
        "new_scheduler_created": False,
        "new_root_created": False,
        "side_effects_performed": False,
    }


def validate_current_contract(repo: Path, registry: dict) -> dict:
    """Read current and historical source contracts; never grant execution authority."""
    paths = (
        "cgx/domain_templates/unispace_objectspace_current_contract.json",
        "cgx/manufacturing/printspace_product_handoff_v0_1.json",
        "cgx/manufacturing/printspace_pre_dbr_archive_register_v0_1.json",
        REGISTRY.as_posix(),
    )
    def read(relative: str) -> tuple[dict, str]:
        path = repo / relative
        _hold_if(path.is_symlink() or not path.is_file() or path.stat().st_size > 262144,
                 "current contract source unavailable or unsafe")
        raw = path.read_bytes()
        _hold_if(relative == REGISTRY.as_posix() and hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256,
                 "historical cross-space registry bytes changed")
        obj = json.loads(raw)
        _hold_if(not isinstance(obj, dict), "current contract source must be an object")
        # Git blob identity only, not a signature or rights proof.
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        return obj, blob

    contract, contract_blob = read(paths[0])
    handoff, handoff_blob = read(paths[1])
    archive, archive_blob = read(paths[2])
    recorded, registry_blob = read(paths[3])
    _hold_if(recorded != validate_registry(registry), "registry readback mismatch")
    try:
        policy = contract["executionPolicy"]
        compat = policy["historicalReviewCompatibility"]
        historic = compat["historicalReviewRef"]
        science = contract["crossGrex"]["scientificAdmission"]
        gate = science["gateRegister"]
        physical = science["physicalQualification"]
        ids = [row["id"] for row in handoff["open_workstreams"] if row["category"] == "physical"]
        expected = [row["id"] for row in registry["task_groups"] if row["space"] == "PrintSpace" and row["id"].startswith("PHYS-")]
        _hold_if(contract["parent"] != ROOT or contract["product"] != "UniSpace" or
                 science["existingRoot"] != ROOT, "current product/root mismatch")
        _hold_if((policy["normalRdcRemainingFloorPct"], policy["emergencyRdcRemainingFloorPct"]) != (21, 20) or
                 compat["effectivePolicyRef"] != "#/executionPolicy" or
                 compat["preserveHistoricalBytes"] is not True or
                 compat["requireFreshQuota"] is not True or compat["unknownQuota"] != "HOLD" or
                 compat["normalEmergencySeparation"] is not True or
                 compat["nativeEnforcementVerified"] is not False, "current execution policy mismatch")
        _hold_if(historic["register"] != paths[1] or historic["archiveRegister"] != paths[2] or
                 historic["registerBlob"] != handoff_blob or historic["archiveRegisterBlob"] != archive_blob or
                 handoff_blob != "060ec29e90913dc593f2498c3319d3725ca07792" or
                 archive_blob != "20e2a5267feb4199ce274ed0fca1d50fbb368c24" or
                 historic["pr"] != 236 or not REF_RE.fullmatch(historic["commit"]),
                 "historical evidence blob mismatch")
        _hold_if((historic["normalRdcRemainingFloorPct"], historic["emergencyRdcRemainingFloorPct"]) != (25, 24) or
                 (handoff["automation_mode"]["remote_desktop_normal_reserve_pct"],
                  handoff["automation_mode"]["remote_desktop_emergency_floor_pct"]) != (25, 24) or
                 (archive["invariant_policy"]["protected_remote_desktop_reserve_pct"],
                  archive["invariant_policy"]["emergency_remote_desktop_floor_pct"]) != (25, 24),
                 "historical reserve evidence changed")
        _hold_if(gate["path"] != paths[3] or gate["blob"] != registry_blob or
                 gate["printspaceGateIds"] != expected or ids != expected or len(ids) != 5,
                 "physical gate crosswalk mismatch")
        _hold_if(science["classification"] != {"visualPreset": "VISUAL_PRESET_ONLY", "synthetic": "simulated",
                 "deduction": "inferred", "hypothesis": "inferred", "fiction": "fictional", "measurement": "empirical"} or
                 science["codec"]["t173"] != "CANDIDATE_REVERSIBLE_CODEC_NOT_PHYSICS_PROOF" or
                 science["codec"]["t174"] != "RESERVED_NONMINTABLE" or
                 science["codec"]["binaryFallback"] is not True, "scientific classification drift")
        _hold_if(any(physical[k] is not True for k in (
                 "meshPassIsNotMachineAuthority", "simulationPassIsNotMeasurement", "visualPresetIsNotMeteorology",
                 "materialDirectionRequiresIndependentCoupons", "environmentalScaleTransferRequiresIndependentEvidence")) or
                 physical["physicalActuationAuthorised"] is not False or science["nativeAdmission"] is not False or
                 science["gateClosureClaimed"] is not False or science["sourceOccurrenceAclRequired"] is not True or
                 not isinstance(contract["release"], dict) or set(contract["release"]) != {
                     "sourceRightsVerified", "issuerAuthenticated", "signedDBR", "independentTwoNodeReadback",
                     "publicBundlePrivacyApproved", "ownerPublicLaunchApproved", "nativeMint", "siteDeployment"} or
                 any(v is not False for v in contract["release"].values()), "scientific or release authority escalated")
    except (KeyError, TypeError, AttributeError) as exc:
        raise CrossSpaceHold("current contract fields missing or malformed") from exc
    return {"state": "CURRENT_CONTRACT_SOURCE_CROSSCHECK_ONLY", "contract_git_blob": contract_blob,
            "historical_handoff_git_blob": handoff_blob, "historical_archive_git_blob": archive_blob,
            "physical_gate_ids": expected, "current_rdc_floors": [21, 20], "historical_rdc_floors": [25, 24],
            "native_admitted": False, "physical_actuation_authorised": False, "dispatch_performed": False}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--mesh-json", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--check-current-contract", action="store_true")
    args = p.parse_args()
    file = args.repo / REGISTRY
    try:
        _hold_if(file.is_symlink() or not file.is_file() or file.stat().st_size > MAX_BYTES,
                 "registry unavailable or unsafe")
        raw = file.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        _hold_if(sha != EXPECTED_SHA256, "registry bytes drifted from reviewed SHA256")
        registry = json.loads(raw)
        mesh = None
        if args.mesh_json is not None:
            _hold_if(args.mesh_json.is_symlink() or args.mesh_json.stat().st_size > MAX_BYTES,
                     "mesh JSON unavailable or unsafe")
            mesh = json.loads(args.mesh_json.read_bytes())
        out = source_review(registry, sha, mesh)
        if args.check_current_contract:
            out["current_contract_crosscheck"] = validate_current_contract(args.repo, registry)
    except (OSError, json.JSONDecodeError, CrossSpaceHold, RecursionError) as e:
        print(json.dumps({"schema": RECEIPT_SCHEMA, "state": "HOLD",
                          "hold_code": type(e).__name__,
                          "native_admitted": False,
                          "archive_delete_authorised": False,
                          "side_effects_performed": False}, sort_keys=True))
        return 2
    payload = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
