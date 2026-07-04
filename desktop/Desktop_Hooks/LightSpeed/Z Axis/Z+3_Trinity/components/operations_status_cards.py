"""
Operations Status Cards (Trinity)

Lightweight status widgets for vendor integrations and local Ops assets.
Shows title, URL, data URL (if any), gating flags, and quick-open buttons.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from lightspeed_runtime.bridge_health import (
        build_bridge_health,
        default_bridge_health_path,
        read_bridge_health,
    )
except Exception:
    build_bridge_health = None  # type: ignore[assignment]
    default_bridge_health_path = None  # type: ignore[assignment]
    read_bridge_health = None  # type: ignore[assignment]

try:
    from core.config.paths import OPERATIONS_ROOT  # type: ignore
except Exception:
    _root = Path(__file__).resolve().parents[3]
    _canonical = _root / "Z Axis" / "Z-4_Merovingian" / "data" / "operations"
    _legacy = _root / "operations"
    OPERATIONS_ROOT = _canonical if (_canonical / "registry" / "operations_registry.json").exists() else _legacy

try:
    from ..ui import operations_manager_panel as ops_helper
except ImportError:
    import sys

    CURRENT = Path(__file__).resolve()
    sys.path.append(str(CURRENT.parents[1] / "ui"))
    import operations_manager_panel as ops_helper  # type: ignore


def _repo_root() -> Path:
    """Best-effort resolve the LightSpeed repo root (where N.py lives)."""
    here = Path(__file__).resolve()
    for cand in (here, *here.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return here.parents[3]


def _bridge_health_payload() -> Dict[str, Any]:
    root = _repo_root()
    if read_bridge_health is not None:
        try:
            cached = read_bridge_health(root)  # type: ignore[misc]
            if cached:
                return cached
        except Exception:
            pass
    if build_bridge_health is not None:
        try:
            return build_bridge_health(root)  # type: ignore[misc]
        except Exception:
            return {}
    return {}


def _describe_workspace(workspace_id: str, ws: Optional[Dict[str, Any]]) -> str:
    """
    Provide an accurate description without relying on placeholder/stub modules.

    Goal: "press a button -> expected result" even when a vendor tool is not installed.
    """
    if workspace_id == "LS-BRIDGE-HEALTH":
        health = _bridge_health_payload()
        if health:
            status = health.get("overall_status", "unknown")
            percent = health.get("readiness_percent", 0)
            public = health.get("public_routes") or {}
            return (
                f"Romer bridge {status}: {percent}% readiness, "
                f"{public.get('pass_count', 0)}/{public.get('required_count', 0)} public routes live."
            )
        return "Romer bridge health contract not generated yet. Run finalization reports or refresh the bridge."

    base_desc = ""
    if isinstance(ws, dict):
        base_desc = str(ws.get("description") or "").strip()

    root = _repo_root()
    if workspace_id == "LS-OPS-GMAT":
        gmat_dir = root / "Z Axis" / "Z0_TheConstruct" / "tools" / "GMAT"
        if gmat_dir.exists():
            return base_desc or "GMAT tools detected locally. Use Open workspace to view the integration surface."
        return base_desc or (
            "GMAT tools are not present locally. This entry is an integration slot; install/attach GMAT when needed."
        )

    if workspace_id == "LS-W6-ASSETS":
        local_path = Path(OPERATIONS_ROOT) / "w6_asset_library" / "data"
        file_count = sum(1 for p in local_path.rglob("*") if p.is_file()) if local_path.exists() else 0
        if local_path.exists():
            return base_desc or f"Local asset library available ({file_count} file(s) discovered)."
        return base_desc or "Local asset library not found on this machine."

    return base_desc or "Operations workspace."


TARGET_IDS = ["LS-BRIDGE-HEALTH", "LS-OPS-GMAT", "LS-W6-ASSETS"]


class OperationsStatusCards(ttk.Frame):
    """Two-card panel for GMAT integration status and the local asset library."""

    def __init__(self, parent: tk.Widget, registry: Optional[List[Dict[str, Any]]] = None, theme=None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.registry = registry or ops_helper.list_workspaces()
        self.cards: Dict[str, ttk.Frame] = {}
        self._build_ui()

    def _workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        if workspace_id == "LS-BRIDGE-HEALTH":
            health = _bridge_health_payload()
            contract_path = ""
            if default_bridge_health_path is not None:
                try:
                    contract_path = str(default_bridge_health_path(_repo_root()))  # type: ignore[misc]
                except Exception:
                    contract_path = ""
            return {
                "workspace_id": workspace_id,
                "title": "Romer Bridge Health",
                "description": _describe_workspace(workspace_id, None),
                "workspace_url": str((health or {}).get("site_base_url") or "https://romer.industries"),
                "data_url": contract_path,
                "widget_type": "bento.status",
                "datasource": "readonly",
                "data_sharing": False,
                "owner_floor": "Trinity",
            }
        for ws in self.registry:
            if ws.get("workspace_id") == workspace_id:
                return ws
        return None

    def _build_ui(self) -> None:
        for wid in TARGET_IDS:
            card = ttk.Labelframe(self, text=wid)
            card.pack(fill="x", padx=8, pady=6)
            self.cards[wid] = card
            self._render_card(card, wid)

    def _render_card(self, card: ttk.Labelframe, workspace_id: str) -> None:
        ws = self._workspace(workspace_id)
        title = ws.get("title", "Missing in registry") if ws else "Missing in registry"
        url = ws.get("workspace_url") if ws else ""
        data_url = ws.get("data_url") if ws else ""
        readonly = True if workspace_id == "LS-BRIDGE-HEALTH" else (ops_helper.is_readonly(ws) if ws else True)
        desc = _describe_workspace(workspace_id, ws)

        ttk.Label(card, text=title).pack(anchor="w", padx=6, pady=(4, 2))
        ttk.Label(card, text=desc, wraplength=640, foreground="#555").pack(anchor="w", padx=6, pady=(0, 4))

        meta = ttk.Frame(card)
        meta.pack(fill="x", padx=6, pady=2)
        ttk.Label(meta, text=f"URL: {url or 'n/a'}").pack(anchor="w")
        ttk.Label(meta, text=f"Data: {data_url or 'n/a'}").pack(anchor="w")
        ttk.Label(meta, text=f"Read-only: {'yes' if readonly else 'no'}").pack(anchor="w")

        if workspace_id == "LS-BRIDGE-HEALTH":
            health = _bridge_health_payload()
            public = health.get("public_routes") or {}
            data = health.get("dataspace_routes") or {}
            drive = health.get("drive_sources") or {}
            sheets = health.get("spreadsheet_feeds") or {}
            ttk.Label(meta, text=f"Public routes: {public.get('pass_count', 0)}/{public.get('required_count', 0)} live").pack(anchor="w")
            ttk.Label(meta, text=f"Dataspace endpoints pending: {data.get('pending_count', 0)}").pack(anchor="w")
            ttk.Label(meta, text=f"Drive: {drive.get('accessible_count', 0)}/{drive.get('count', 0)} accessible").pack(anchor="w")
            ttk.Label(meta, text=f"Sheets: {sheets.get('accessible_count', 0)}/{sheets.get('count', 0)} accessible").pack(anchor="w")

        if workspace_id == "LS-W6-ASSETS":
            local_path = Path(OPERATIONS_ROOT) / "w6_asset_library" / "data"
            file_count = sum(1 for p in local_path.rglob("*") if p.is_file()) if local_path.exists() else 0
            ttk.Label(meta, text=f"Local assets: {file_count} file(s) in the asset library").pack(anchor="w")

        btns = ttk.Frame(card)
        btns.pack(fill="x", padx=6, pady=4)

        ttk.Button(btns, text="Open workspace", command=lambda u=url: self._open(u)).pack(side="left")
        ttk.Button(btns, text="Open data", command=lambda u=data_url: self._open(u)).pack(side="left", padx=(8, 0))

    @staticmethod
    def _open(url: Optional[str]) -> None:
        if not url:
            messagebox.showinfo("Open link", "No URL available for this entry.")
            return
        target = str(url)
        try:
            path = Path(target)
            if path.exists():
                webbrowser.open(path.resolve().as_uri())
                return
        except Exception:
            pass
        webbrowser.open(target)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Operations Status Cards")
    panel = OperationsStatusCards(root)
    panel.pack(fill="both", expand=True)
    root.mainloop()
