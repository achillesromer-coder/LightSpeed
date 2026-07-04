#!/usr/bin/env python
"""
Generate a minimal, floor-centric data index for the LightSpeed workspace.

Outputs:
- `LightSpeed/dataindex/z_axis_index.json` (floor manifests + key paths)
- `LightSpeed/dataindex/depmap.json` (dependency graph: floors + services + files/modules)

Adds: merge operations registry depmap fragment if present at operations/registry/depmap_export.json.
"""

from __future__ import annotations

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict

def find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in (start, *start.parents):
        if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
            return candidate
    return start.parent

def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        try:
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            return {}

def main() -> int:
    root = find_lightspeed_root(Path(__file__))
    z_axis = root / "Z Axis"
    out_path = root / "dataindex" / "z_axis_index.json"
    depmap_path = root / "dataindex" / "depmap.json"
    tool_catalog_path = root / "dataindex" / "tool_catalog.json"

    floor_dirs_all = [p for p in z_axis.iterdir() if p.is_dir() and p.name.startswith("Z")]

    # Non-destructive legacy handling: keep the folder on disk, but exclude it from
    # active indexing/depmap so "canonical" tooling stays aligned with the 8-floor stack.
    legacy_floor_dirs = [
        fd for fd in floor_dirs_all
        if fd.name == "Z+4_FirstRun" or (fd / "_FLOOR_MANIFEST.legacy.json").exists()
    ]
    floor_dirs = [fd for fd in floor_dirs_all if fd not in legacy_floor_dirs]

    floors = []
    for fd in floor_dirs:
        manifest = fd / "_FLOOR_MANIFEST.json"
        if manifest.exists():
            floors.append(read_json(manifest))
        else:
            floors.append({
                "id": fd.name.lower(),
                "path": str(fd),
                "missing_manifest": True,
            })

    legacy_floors = []
    for fd in legacy_floor_dirs:
        legacy_floors.append({
            "id": fd.name.lower(),
            "path": str(fd),
            "legacy": True,
            "reason": "consolidated into Trinity (Z+3)",
            "legacy_manifest": str(fd / "_FLOOR_MANIFEST.legacy.json") if (fd / "_FLOOR_MANIFEST.legacy.json").exists() else None,
        })

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "z_axis": str(z_axis),
        "expected_root_minimal": {
            "folders": ["__pycache__", "ai_logs", "config", "Z Axis", "dataindex"],
            "files": ["__main__.py", "N.py", "LAUNCH_GUI.bat", "README.md"],
        },
        "floors": floors,
        "legacy_floors": legacy_floors,
    }

    # Generate tool catalog (capabilities) if available
    catalog_script = root / "Z Axis" / "Z-3_Smith" / "tools" / "list_capabilities.py"
    if catalog_script.exists():
        try:
            subprocess.run(["python", str(catalog_script)], check=True)
            if tool_catalog_path.exists():
                payload["tool_catalog"] = {
                    "path": str(tool_catalog_path),
                    "count": len(read_json(tool_catalog_path).get("tools", []))
                }
        except Exception as exc:
            payload["tool_catalog_error"] = str(exc)

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[dataindex] Wrote {out_path}")
    print(f"[dataindex] Floors indexed: {len(floors)}")
    if legacy_floors:
        print(f"[dataindex] Legacy floors excluded: {len(legacy_floors)}")

    # Dependency map (requires `core.*` imports, so ensure floor roots are importable)
    try:
        sys.path.insert(0, str(root))
        sys.path.insert(0, str(z_axis))
        for fd in floor_dirs:
            sys.path.insert(0, str(fd))

        from core.analysis.dependencies import PlatformDependencyMapper  # type: ignore

        graph = PlatformDependencyMapper(root).build()

        # Merge operations registry fragment if present
        fragment_path = root / "operations" / "registry" / "depmap_export.json"
        if fragment_path.exists():
            fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
            frag_nodes = fragment.get("nodes", [])
            frag_edges = fragment.get("edges", [])
            graph_nodes = graph.get("nodes", []) or []
            graph_edges = graph.get("edges", []) or []
            graph_nodes.extend(frag_nodes)
            graph_edges.extend(frag_edges)
            graph["nodes"] = graph_nodes
            graph["edges"] = graph_edges
            print(f"[dataindex] Merged operations registry fragment: +{len(frag_nodes)} nodes, +{len(frag_edges)} edges")

        depmap_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
        issues = (graph.get("stats") or {}).get("issues") or {}
        print(f"[dataindex] Wrote {depmap_path}")
        print(f"[dataindex] Depmap issues: {issues}")
    except Exception as e:
        print(f"[dataindex] WARNING: depmap generation failed: {e}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
