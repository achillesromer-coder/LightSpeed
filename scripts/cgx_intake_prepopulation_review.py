#!/usr/bin/env python3
"""Project existing private intake evidence into the ONE CGX review structure.

This is a deterministic, aggregate-only projection, not an alternate LOAD index.
It cannot ingest content, qualify rights, delete sources, sign or mint.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

SCHEMA = "CGX-MANUAL-INTAKE-PREPOPULATION-REVIEW/0.1"
CANONICAL_PARENT = "cgx:root:cognigrex"
PROFILES = {
    "achilles_owner_operator_profile.json": "Achilles",
    "eco_semantic_library.json": "Eco",
    "emassc_lightspeed_semantic_library.json": "EMASSC_LightSpeed",
    "romer_semantic_library.json": "Romer",
    "semantic_view_lens_registry.json": "UniSpace",
    "reasoning_profiles.json": "Cognigrex",
    "depth_profiles.json": "Cognigrex",
    "founder_semantic_delta_2026-10-02_romer.json": "Romer",
    "founder_semantic_delta_2026-10-07_printable_solid_state.json": "Romer",
    "mark3_interface_semantic_correction_2026-10-05.json": "Romer",
}
ROUTE_ROOTS = {
    "Achilles": "Achilles", "Raphael": "Raphael", "EMASSC": "EMASSC_LightSpeed",
    "LightSpeed": "EMASSC_LightSpeed", "Romer Projected": "Romer",
    "UniSpace_Living_Review_20261103": "UniSpace",
    "UniSpace_20261103_Review_Kit": "UniSpace",
}
sha = lambda b: hashlib.sha256(b).hexdigest()


def project(receipt: dict, receipt_bytes: bytes, repo: Path) -> dict:
    if receipt.get("schema") != "CGX-INTAKE-EQUIVALENCE-REVIEW/0.1":
        raise ValueError("SOURCE_SCHEMA_HOLD")
    if any(receipt.get(k) is not False for k in ("native_mint_authorized", "canonical_write")):
        raise ValueError("NATIVE_OR_CANONICAL_AUTHORITY_HOLD")
    if any(receipt.get(k) != 0 for k in ("sources_changed", "sources_deleted")):
        raise ValueError("SOURCE_MUTATION_HOLD")
    groups = receipt.get("duplicate_groups")
    if not isinstance(groups, list) or receipt.get("verified_groups") != len(groups):
        raise ValueError("DUPLICATE_PROOF_COVERAGE_HOLD")
    for group in groups:
        if group.get("byte_equivalence_verified") is not True or not isinstance(group.get("sources"), list):
            raise ValueError("UNVERIFIED_DUPLICATE_HOLD")
    dispositions = receipt.get("source_dispositions")
    if not isinstance(dispositions, dict):
        raise ValueError("SOURCE_DISPOSITION_SCHEMA_HOLD")
    stages, roots, routes, triage = Counter(), Counter(), Counter(), Counter()
    for encoded, count in dispositions.items():
        if not isinstance(count, int) or count < 0:
            raise ValueError("SOURCE_RECORD_COUNT_INVALID")
        row = json.loads(encoded)
        stage = row.get("disposition")
        rel = row.get("relative")
        if not isinstance(stage, str) or not isinstance(rel, str) or not rel:
            raise ValueError("SOURCE_RECORD_INVALID")
        if row.get("native_admission") is not False or row.get("executable_authority") is not False:
            raise ValueError("SOURCE_RECORD_AUTHORITY_HOLD")
        root = rel.replace("\\", "/").split("/")[0]
        stages[stage] += count
        roots[root] += count
        routes[ROUTE_ROOTS.get(root, "UNASSIGNED_REQUIRES_SOURCE_QUALIFICATION")] += count
        # Classify source *provenance*, never meaning/rights/semantic equivalence.
        parts = rel.replace("\\", "/").split("/")
        segment = (parts[3] if root == "Codex" and len(parts) > 3 else "").casefold()
        if root == "Codex" and segment in {"outputs", "tmp", ".tmp", "logs"}:
            triage["CODEX_GENERATED_OR_TRANSIENT_REVIEW"] += count
        elif root == "Codex":
            triage["CODEX_OTHER_PROVENANCE_REVIEW"] += count
        elif root in ROUTE_ROOTS:
            triage["NAMED_FAMILY_ROOT_REVIEW"] += count
        else:
            triage["UNCLASSIFIED_ROOT_REVIEW"] += count
    core = repo / "plugins" / "source" / "core-skills"
    distributed = repo / "plugins" / "packages"
    canonical = {p.parent.name: sha(p.read_bytes()) for p in core.glob("*/SKILL.md")}
    if not canonical:
        raise ValueError("CANONICAL_SKILLS_MISSING")
    package_counts, drift = Counter(), []
    for f in sorted(distributed.glob("*/skills/*/SKILL.md")):
        family = f.relative_to(distributed).parts[0]
        package_counts[family] += 1
        if canonical.get(f.parent.name) != sha(f.read_bytes()):
            drift.append(f"{family}/{f.parent.name}")
    # Never collapse deployed copies into accidental runtime deletions.
    profiles = []
    base = repo / "cgx" / "domain_templates"
    for filename, family in sorted(PROFILES.items()):
        f = base / filename
        if f.is_file():
            profiles.append({"profile_file": filename, "family": family,
                             "source_sha256": sha(f.read_bytes()),
                             "status": "SOURCE_TEMPLATE_CANDIDATE_NOT_QUALIFIED"})
    return {
        "schema": SCHEMA, "canonical_parent": CANONICAL_PARENT,
        "sole_load_resolver": "LOAD.cgx",
        "source_receipt_sha256": sha(receipt_bytes),
        "source_head_reported": receipt.get("source_head"),
        "intake": {"records_reviewed": sum(stages.values()),
                   "dispositions": dict(sorted(stages.items())),
                   "root_count": len(roots),
                   "provenance_triage": dict(sorted(triage.items())),
                   "triage_policy": "PATH_ANCESTRY_ONLY_NOT_SEMANTIC_IDENTITY_OR_DELETION_PROOF",
                   "route_candidates": dict(sorted(routes.items())),
                   "route_policy": "EXACT_ROOT_ONLY_NO_CONTENT_INFERENCE"},
        "duplicates": {"verified_groups": len(groups),
                       "source_references_in_groups": sum(len(g["sources"]) for g in groups),
                       "hashes_redacted": True,
                       "deletion_eligible": 0,
                       "rule": "BYTE_EQUIVALENCE_IS_NOT_SOURCE_RIGHTS_OR_SUCCESSOR_ADMISSION"},
        "skills": {"canonical_core_count": len(canonical),
                   "canonical_core_sha256": dict(sorted(canonical.items())),
                   "distributed_count": sum(package_counts.values()),
                   "packages_by_family": dict(sorted(package_counts.items())),
                   "drifted_distributed_skills": sorted(drift),
                   "policy": "PACKAGE_COPIES_ARE_DISTRIBUTION_ARTIFACTS_NOT_NEW_CGX_TYPES"},
        "semantic_profiles": profiles,
        "states": {"r0_review": "PARTIAL_SOURCE_REVIEW_ONLY", "r1": "CANDIDATE_ONLY",
                   "r2": "NOT_INFERRED", "r3": "UNQUALIFIED",
                   "native_mint": "HOLD", "independent_dbr": "HOLD",
                   "public_release": "HOLD", "automatic_deletion": False,
                   "automatic_source_move": False,
                   "credential_or_lease_grant": False},
        "usage": "Read-only projection for existing owner lanes; never a new database, resolver or mint registry",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    source = a.receipt.read_bytes()
    projected = project(json.loads(source), source, a.repo)
    data = (json.dumps(projected, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    if a.check:
        if not a.output.is_file() or a.output.read_bytes().replace(b"\r\n", b"\n") != data:
            raise SystemExit("PREPOPULATION_REVIEW_DRIFT_HOLD")
    elif a.write:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open("xb") as f:
            f.write(data)
    print(json.dumps({"schema": SCHEMA, "records": projected["intake"]["records_reviewed"],
      "verified_duplicate_groups": projected["duplicates"]["verified_groups"],
      "distributed_skills": projected["skills"]["distributed_count"],
      "canonical_skills": projected["skills"]["canonical_core_count"],
      "candidate_profiles": len(projected["semantic_profiles"]),
      "drifted_skills": len(projected["skills"]["drifted_distributed_skills"]),
      "native_mints": 0, "source_deletions": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
