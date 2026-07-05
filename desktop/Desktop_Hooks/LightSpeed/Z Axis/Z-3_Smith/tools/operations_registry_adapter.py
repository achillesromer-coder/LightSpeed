"""
Operations Registry Adapter (Smith)

Loads the Operations registry and converts it into a depmap-style nodes/edges
fragment that can be merged into the platform dependency map.

V1 note: the Operations registry is floor-native (Merovingian-owned) but remains
compatible with historical root layouts.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from core.config.paths import OPERATIONS_ROOT, OPERATIONS_REGISTRY_PATH  # type: ignore
except Exception:
    _root = Path(__file__).resolve().parents[3]
    _ops_canonical = _root / "Z Axis" / "Z-4_Merovingian" / "data" / "operations"
    _ops_legacy = _root / "operations"
    OPERATIONS_ROOT = _ops_canonical if (_ops_canonical / "registry" / "operations_registry.json").exists() else _ops_legacy
    OPERATIONS_REGISTRY_PATH = Path(OPERATIONS_ROOT) / "registry" / "operations_registry.json"

REGISTRY_PATH = Path(OPERATIONS_REGISTRY_PATH)
EXPORT_PATH = Path(OPERATIONS_ROOT) / "registry" / "depmap_export.json"

def load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"workspaces": []}
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def registry_to_depmap() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    data = load_registry()
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    for ws in data.get("workspaces", []):
        ws_id = ws.get("workspace_id") or ""
        title = ws.get("title") or ws_id
        node_id = f"workspace:{ws_id}" if ws_id else None
        if not node_id:
            continue
        nodes.append({
            "id": node_id,
            "kind": "workspace",
            "label": title,
            "ok": True,
            "meta": {
                "widget_type": ws.get("widget_type"),
                "datasource": ws.get("datasource"),
                "data_sharing": ws.get("data_sharing"),
                "owner_floor": ws.get("owner_floor"),
                "tags": ws.get("tags", []),
            },
        })
        for ref in ws.get("external_refs", []) or []:
            edges.append({
                "source": node_id,
                "target": f"url:{ref}",
                "kind": "references"
            })
    return nodes, edges

def export_depmap_fragment() -> Path:
    """Write nodes/edges to a depmap fragment for later merge."""
    nodes, edges = registry_to_depmap()
    payload = {"nodes": nodes, "edges": edges, "source": "operations_registry"}
    EXPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return EXPORT_PATH

def describe_registry() -> str:
    data = load_registry()
    return f"workspaces={len(data.get('workspaces', []))}"

if __name__ == "__main__":
    nodes, edges = registry_to_depmap()
    print(describe_registry())
    print("nodes", len(nodes), "edges", len(edges))
    path = export_depmap_fragment()
    print(f"exported fragment -> {path}")
