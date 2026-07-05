#!/usr/bin/env python
"""
Generate embed snippets from operations/registry/operations_registry.json
into operations/registry/embed_snippets.md.

Intended use:
- Run after editing the registry to refresh copy-ready iframe snippets for Squarespace.
- Non-destructive; creates/overwrites embed_snippets.md only.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
try:
    from core.config.paths import OPERATIONS_ROOT, OPERATIONS_REGISTRY_PATH  # type: ignore
except Exception:
    _ops_canonical = ROOT / "Z Axis" / "Z-4_Merovingian" / "data" / "operations"
    _ops_legacy = ROOT / "operations"
    OPERATIONS_ROOT = _ops_canonical if (_ops_canonical / "registry" / "operations_registry.json").exists() else _ops_legacy
    OPERATIONS_REGISTRY_PATH = Path(OPERATIONS_ROOT) / "registry" / "operations_registry.json"

REGISTRY_PATH = Path(OPERATIONS_REGISTRY_PATH)
EMBEDS_PATH = Path(OPERATIONS_ROOT) / "registry" / "embed_snippets.md"


def load_registry():
    if not REGISTRY_PATH.exists():
        return {"workspaces": []}
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def render_snippet(ws: dict) -> str:
    wid = ws.get("workspace_id", "")
    title = ws.get("title", wid)
    url = ws.get("workspace_url", "")
    widget = ws.get("widget_type", "bento.standard")
    datasource = ws.get("datasource", "readonly")
    sharing = str(ws.get("data_sharing", False)).lower()
    return (
        f"## {wid} — {title}\n\n"
        "`````\n"
        "<!-- LightSpeed Workspace Embed -->\n"
        f"<div id=\"ls-embed\" data-workspace=\"{wid}\" data-widget=\"{widget}\" "
        f"data-datasource=\"{datasource}\" data-datasharing=\"{sharing}\">\n"
        f"  <iframe src=\"{url}\" title=\"LightSpeed Workspace {wid}\" "
        "loading=\"lazy\" style=\"width:100%;height:720px;border:0;border-radius:12px;\"></iframe>\n"
        "</div>\n"
        "`````\n"
    )


def main() -> int:
    reg = load_registry()
    snippets = [render_snippet(ws) for ws in reg.get("workspaces", [])]
    EMBEDS_PATH.write_text("\n".join(snippets), encoding="utf-8")
    print(f"[embeds] Wrote {EMBEDS_PATH} ({len(snippets)} snippets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
