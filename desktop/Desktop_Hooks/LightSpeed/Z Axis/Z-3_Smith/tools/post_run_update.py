#!/usr/bin/env python
"""
Post-run update helper:
- Append a run_ref (manifest path) to a scenario in the canonical scenario catalog.
- Optionally regenerate dataindex/depmap.

Usage:
    python post_run_update.py --scenario_id SCEN-003B --manifest w6/data/gmat_run/.../manifest.json --update_index
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "Z Axis" / "Z-4_Merovingian" / "data" / "operations" / "registry" / "scenario_catalog.json"
GEN_INDEX = ROOT / "Z Axis" / "Z-3_Smith" / "tools" / "generate_dataindex.py"


def append_run_ref(scenario_id: str, run_ref: str) -> bool:
    if not CATALOG.exists():
        raise FileNotFoundError(f"Catalog not found: {CATALOG}")
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
    parser.add_argument("--scenario_id", required=True, help="Scenario ID to update")
    parser.add_argument("--manifest", required=True, help="Relative or absolute path to manifest.json")
    parser.add_argument("--update_index", action="store_true", help="Run generate_dataindex.py after updating")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = (ROOT / manifest_path).resolve()
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    # Store run_ref relative to repo root for catalog
    try:
        run_ref = str(manifest_path.relative_to(ROOT))
    except Exception:
        run_ref = str(manifest_path)

    changed = append_run_ref(args.scenario_id, run_ref)
    if changed:
        print(f"Appended run_ref to {args.scenario_id}: {run_ref}")
        if args.update_index and GEN_INDEX.exists():
            subprocess.run(["python", str(GEN_INDEX)], check=True)
        return 0
    else:
        print("No change (scenario not found or run_ref already present)")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
