#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DT = ROOT / "cgx" / "domain_templates"
RUNTIME_DEFAULT = ROOT / "runtime" / "python"

def load(name: str):
    return json.loads((DT / name).read_text(encoding="utf-8"))

def save_json(root: Path, rel: str, obj) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser(description="Build a verified PRE_CANONICAL CGP-IES descendant from exact S91 Recovery. This tool never promotes Recovery.")
    ap.add_argument("--master", required=True, type=Path, help="Exact S91 Recovery .cgx carrier")
    ap.add_argument("--out", required=True, type=Path, help="Output candidate .cgx path; must not overwrite --master")
    ap.add_argument("--runtime-python", type=Path, default=RUNTIME_DEFAULT)
    args = ap.parse_args()

    manifest = load("cgp_ies_parent_extension_manifest.json")
    seed = manifest["seed"]
    if args.master.resolve() == args.out.resolve():
        raise SystemExit("FAIL: candidate output may not overwrite Recovery input")
    actual = sha256_file(args.master)
    if actual != seed["sha256"]:
        raise SystemExit(f"FAIL: Recovery seed SHA-256 mismatch: {actual}")

    sys.path.insert(0, str(args.runtime_python.resolve()))
    import cgx_kernel as kernel

    ws = kernel.open_workspace(args.master)
    try:
        before = kernel.verify(ws.root)
        if not before.get("ok"):
            raise SystemExit("FAIL: seed verifier: " + ";".join(before.get("errors", [])))
        boot = kernel.load_json(ws.root, "cgx/bootstrap.json", {})
        dbr = kernel.load_json(ws.root, "cgx/dbr.json", {})
        if (
            boot.get("state_id") != seed["state_id"]
            or boot.get("content_root") != seed["content_root"]
            or boot.get("topology_snapshot_hash") != seed["topology"]
            or dbr.get("dbr_root") != seed["dbr_root"]
        ):
            raise SystemExit("FAIL: Recovery identity/root mismatch")

        target_root = manifest["target_root"]
        install = manifest["install"]

        def op():
            for dest, source in install.items():
                save_json(ws.root, f"{target_root}/{dest}", load(source))
            save_json(ws.root, f"{target_root}/candidate_state.json", {
                "schema": "CGX-CGP-IES-CANDIDATE-STATE/0.1",
                "policy_state": "PRE_CANONICAL",
                "source_branch_required_for_review": "cgp-ies-functional-handoff-20260930",
                "seed_state": seed["state_id"],
                "seed_sha256": seed["sha256"],
                "canonical_promotion": "REQUIRES_EXPLICIT_OWNER_GOVERNANCE_CONFIRMATION",
                "authority_transfer": False
            })

        state = kernel.mutate(
            ws.root,
            "cgp_ies_extension_candidate_install",
            "Install parent-owned CGP-IES PRE_CANONICAL extension candidate",
            op,
            {
                "extension_id": "cgp-ies",
                "seed_state": seed["state_id"],
                "seed_sha256": seed["sha256"],
                "policy_state": "PRE_CANONICAL",
                "authority_transfer": False,
                "promotion": "NOT_PERFORMED"
            }
        )
        check = kernel.verify(ws.root)
        if not check.get("ok"):
            raise SystemExit("FAIL: post-mutation verifier: " + ";".join(check.get("errors", [])))

        args.out.parent.mkdir(parents=True, exist_ok=True)
        kernel.write_carrier(ws.root, args.out)
    finally:
        ws.close()

    packed_sha = sha256_file(args.out)
    reopened = kernel.open_workspace(args.out)
    try:
        reopen_check = kernel.verify(reopened.root)
        rb = kernel.load_json(reopened.root, "cgx/bootstrap.json", {})
        rd = kernel.load_json(reopened.root, "cgx/dbr.json", {})
        candidate = kernel.load_json(reopened.root, "extensions/cgp-ies/candidate_state.json", {})
    finally:
        reopened.close()
    if not reopen_check.get("ok"):
        raise SystemExit("FAIL: packed reopen verifier")

    receipt = {
        "schema": "CGX-CGP-IES-PARENT-CANDIDATE-RECEIPT/0.1",
        "seed": seed,
        "output": str(args.out),
        "packed_sha256": packed_sha,
        "object_id": rb.get("object_id"),
        "state_id": rb.get("state_id"),
        "content_root": rb.get("content_root"),
        "dbr_root": rd.get("dbr_root"),
        "topology_snapshot_hash": rb.get("topology_snapshot_hash"),
        "commit_verified": state.get("commit_verified"),
        "verify": "PASS",
        "packed_reopen_verify": "PASS",
        "policy_state": candidate.get("policy_state"),
        "promotion": "NOT_PERFORMED",
        "next_gate": "Review/confirm owner values; independently audit this exact candidate; only then consider promotion to a new Recovery authority."
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
