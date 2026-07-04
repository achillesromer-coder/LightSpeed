#!/usr/bin/env python
"""
Append a run_ref to operations/registry/scenario_catalog.json for a given scenario_id.

Usage:
    python append_run_ref.py --scenario_id SCEN-003B --run_ref w6/data/gmat_run/.../manifest.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PREFERRED = ROOT / "Z Axis" / "Z-4_Merovingian" / "data" / "operations" / "registry" / "scenario_catalog.json"
LEGACY = ROOT / "operations" / "registry" / "scenario_catalog.json"
CATALOG = PREFERRED if PREFERRED.exists() else LEGACY


def append_ref(scenario_id: str, run_ref: str) -> bool:
    if not CATALOG.exists():
        return False
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    changed = False
    for s in data.get("scenarios", []):
        if s.get("scenario_id") == scenario_id:
            refs = s.get("run_refs") or []
            if run_ref not in refs:
                refs.append(run_ref)
                s["run_refs"] = refs
                changed = True
            break
    if changed:
        CATALOG.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario_id", required=True)
    parser.add_argument("--run_ref", required=True)
    args = parser.parse_args()

    if append_ref(args.scenario_id, args.run_ref):
        print(f"Appended run_ref to {args.scenario_id}: {args.run_ref}")
        return 0
    else:
        print("No change (scenario not found or run_ref already present)")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
