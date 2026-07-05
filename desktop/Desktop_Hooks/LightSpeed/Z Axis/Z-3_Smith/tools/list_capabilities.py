#!/usr/bin/env python
"""
Collect tool capabilities into a catalog (LAS-aligned).

Scans Z-3_Smith/tools for *_capabilities.json and writes
`dataindex/tool_catalog.json` with basic metadata for UI/registry wiring.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict


def find_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
            return candidate
    return start


def load_json(path: Path) -> Dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    root = find_root(Path(__file__).resolve())
    tools_dir = root / "Z Axis" / "Z-3_Smith" / "tools"
    out_path = root / "dataindex" / "tool_catalog.json"

    entries: List[Dict] = []
    for cap_file in tools_dir.glob("*_capabilities.json"):
        data = load_json(cap_file)
        if not data.get("tool_key"):
            continue
        entries.append({
            "tool_key": data.get("tool_key"),
            "tool_name": data.get("tool_name"),
            "description": data.get("description"),
            "default_z_context": data.get("default_z_context"),
            "default_workspace": data.get("default_workspace"),
            "actions": data.get("actions", []),
            "default_output_path": data.get("default_output_path"),
            "ui_category": data.get("ui", {}).get("category"),
            "capabilities_path": str(cap_file.relative_to(root))
        })

    catalog = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "count": len(entries),
        "tools": sorted(entries, key=lambda e: e["tool_key"]),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"[tool_catalog] Wrote {out_path} ({len(entries)} tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
