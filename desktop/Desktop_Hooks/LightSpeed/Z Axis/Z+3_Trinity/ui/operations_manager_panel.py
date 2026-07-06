"""
Trinity Operations Workspace Manager (read-only scaffold).

Purpose:
- Read `operations/registry/operations_registry.json`
- List workspaces (W1-W7, Achilles, Home, optional GMAT integration slot) with metadata
- Generate copy-ready iframe snippets for Squarespace embeds
- Respect role gating flags (W6 read-only, W7 gated, GMAT read-only)

Note: This is a data-layer helper; UI rendering/wiring should be added in a Trinity panel.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from lightspeed_runtime.bridge_health import default_bridge_health_path, read_bridge_health
except Exception:
    default_bridge_health_path = None  # type: ignore[assignment]
    read_bridge_health = None  # type: ignore[assignment]

try:
    from core.config.paths import OPERATIONS_REGISTRY_PATH  # type: ignore
except Exception:
    _root = Path(__file__).resolve().parents[3]
    _canonical = _root / "Z Axis" / "Z-4_Merovingian" / "data" / "operations" / "registry" / "operations_registry.json"
    _legacy = _root / "operations" / "registry" / "operations_registry.json"
    OPERATIONS_REGISTRY_PATH = _canonical if _canonical.exists() else _legacy

REGISTRY_PATH = Path(OPERATIONS_REGISTRY_PATH)


def _repo_root() -> Path:
    for cand in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return Path(__file__).resolve().parents[3]


def _bridge_workspace() -> Dict[str, Any]:
    root = _repo_root()
    health = {}
    if read_bridge_health is not None:
        try:
            health = read_bridge_health(root)  # type: ignore[misc]
        except Exception:
            health = {}
    data_url = ""
    if default_bridge_health_path is not None:
        try:
            data_url = str(default_bridge_health_path(root))  # type: ignore[misc]
        except Exception:
            data_url = ""
    public = health.get("public_routes") or {}
    squarespace = health.get("squarespace_embed") or {}
    status = health.get("overall_status", "unknown")
    readiness = health.get("readiness_percent", 0)
    return {
        "workspace_id": "LS-BRIDGE-HEALTH",
        "title": "Romer Bridge Health",
        "description": (
            f"Walkthrough bridge status: {status}, {readiness}% readiness, "
            f"{public.get('pass_count', 0)}/{public.get('required_count', 0)} public routes live, "
            f"{squarespace.get('unconfirmed_count', 0)} Squarespace embed routes pending proof."
        ),
        "workspace_url": str(health.get("site_base_url") or "https://romer.industries"),
        "data_url": data_url,
        "widget_type": "bento.status",
        "datasource": "readonly",
        "data_sharing": False,
        "owner_floor": "Trinity",
        "tags": ["bridge", "walkthrough", "romer", "health"],
    }


def load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        payload = {"workspaces": []}
    else:
        with REGISTRY_PATH.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    workspaces = list(payload.get("workspaces", []))
    if not any(ws.get("workspace_id") == "LS-BRIDGE-HEALTH" for ws in workspaces):
        workspaces.insert(0, _bridge_workspace())
    payload["workspaces"] = workspaces
    return payload


def list_workspaces(tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    workspaces = load_registry().get("workspaces", [])
    if tags:
        tags_lower = {t.lower() for t in tags}
        workspaces = [w for w in workspaces if tags_lower & {t.lower() for t in w.get("tags", [])}]
    return workspaces


def get_workspace(workspace_id: str) -> Optional[Dict[str, Any]]:
    for ws in list_workspaces():
        if ws.get("workspace_id") == workspace_id:
            return ws
    return None


def is_readonly(ws: Dict[str, Any]) -> bool:
    """Role gating: W6, W7, and the optional GMAT integration slot are read-only."""
    wid = (ws.get("workspace_id") or "").upper()
    return wid in {"LS-BRIDGE-HEALTH", "LS-W6-ASSETS", "LS-W7-DECENTRALIZED", "LS-OPS-GMAT"}


def render_embed_snippet(ws: Dict[str, Any]) -> str:
    wid = ws.get("workspace_id", "")
    url = ws.get("workspace_url", "")
    widget = ws.get("widget_type", "bento.standard")
    datasource = ws.get("datasource", "readonly")
    sharing = str(ws.get("data_sharing", False)).lower()
    return (
        "<!-- LightSpeed Workspace Embed -->\n"
        f"<div id=\"ls-embed\" data-workspace=\"{wid}\" data-widget=\"{widget}\" "
        f"data-datasource=\"{datasource}\" data-datasharing=\"{sharing}\">\n"
        f"  <iframe src=\"{url}\" title=\"LightSpeed Workspace {wid}\" "
        "loading=\"lazy\" style=\"width:100%;height:720px;border:0;border-radius:12px;\"></iframe>\n"
        "</div>"
    )


def describe_workspace(ws: Dict[str, Any]) -> str:
    return (
        f"{ws.get('workspace_id','')} | {ws.get('title','')} | widget={ws.get('widget_type')} | "
        f"datasource={ws.get('datasource')} | sharing={ws.get('data_sharing')} | owner={ws.get('owner_floor')} "
        f"| readonly={is_readonly(ws)}"
    )


if __name__ == "__main__":
    all_ws = list_workspaces()
    print(f"workspaces: {len(all_ws)}")
    for ws in all_ws:
        print(describe_workspace(ws))
    for ws in all_ws:
        print(f"\n--- {ws.get('workspace_id')} snippet")
        print(render_embed_snippet(ws))
