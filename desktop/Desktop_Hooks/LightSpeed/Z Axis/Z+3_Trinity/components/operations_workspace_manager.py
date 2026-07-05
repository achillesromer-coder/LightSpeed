"""
Operations Workspace Manager Panel (Trinity)

Read-only panel to browse /operations registry entries, filter workspaces, and copy
Squarespace embed snippets. Uses registry helpers in `ui/operations_manager_panel.py`.

Features:
- List all workspaces (home, project pages, Achilles, vendor integration slots) from registry
- Filter by tag and search (id/title/description)
- Copy iframe embed snippet to clipboard
- Open workspace URL in default browser
- Role gating indicators (read-only for protected/vendor integrations)
"""
from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Any, Dict, List, Optional
import webbrowser
from datetime import datetime

try:
    from ..ui import operations_manager_panel as ops_helper
except ImportError:
    # Fallback for direct execution
    import sys

    CURRENT = Path(__file__).resolve()
    sys.path.append(str(CURRENT.parents[1] / "ui"))
    import operations_manager_panel as ops_helper  # type: ignore

try:
    from lightspeed_runtime.storage_paths import operations_root as _smart_operations_root
except Exception:
    def _smart_operations_root(root: Path) -> Path:
        return root / "Z Axis" / "Z-3_Smith" / "data" / "operations"


class OperationsWorkspaceManager:
    """Tkinter panel for the Operations workspace registry."""

    def __init__(self, parent: tk.Widget, registry_path: Optional[Path] = None, theme=None) -> None:
        self.parent = parent
        self.registry_path = registry_path
        self.theme = theme

        self.workspaces: List[Dict[str, Any]] = []
        self.tags: List[str] = []

        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="both", expand=True)

        self._build_header()
        self._build_table()
        self._build_details()

        self._oracle_integrator = None

        self._load_registry()
        self._refresh_table()

    # UI construction
    def _build_header(self) -> None:
        header = ttk.Frame(self.frame)
        header.pack(fill="x", padx=8, pady=6)

        ttk.Label(header, text="Workspace Manager").pack(side="left")

        ttk.Label(header, text="Search:").pack(side="left", padx=(12, 4))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(header, textvariable=self.search_var, width=28)
        search_entry.pack(side="left")
        search_entry.bind("<KeyRelease>", lambda _e: self._refresh_table())

        ttk.Label(header, text="Tag:").pack(side="left", padx=(12, 4))
        self.tag_var = tk.StringVar(value="All")
        self.tag_combo = ttk.Combobox(header, textvariable=self.tag_var, width=18, state="readonly")
        self.tag_combo.pack(side="left")
        self.tag_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_table())

        ttk.Button(header, text="Refresh", command=self._load_registry).pack(side="right")

    def _build_table(self) -> None:
        table_frame = ttk.Frame(self.frame)
        table_frame.pack(fill="both", expand=True, padx=8, pady=4)

        columns = ("id", "title", "widget", "datasource", "sharing", "readonly")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        for col, text, width in [
            ("id", "Workspace", 140),
            ("title", "Title", 200),
            ("widget", "Widget", 110),
            ("datasource", "Datasource", 110),
            ("sharing", "Sharing", 80),
            ("readonly", "Read-only", 80),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    def _build_details(self) -> None:
        detail = ttk.Frame(self.frame)
        detail.pack(fill="x", padx=8, pady=(4, 8))

        self.status_var = tk.StringVar(value="Select a workspace to view details.")
        ttk.Label(detail, textvariable=self.status_var).pack(anchor="w", pady=(0, 4))

        self.detail_text = tk.Text(detail, height=6, wrap="word")
        self.detail_text.configure(state="disabled")
        self.detail_text.pack(fill="x")

        controls = ttk.Frame(detail)
        controls.pack(fill="x", pady=6)

        ttk.Label(controls, text="Widget:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.widget_var = tk.StringVar()
        self.widget_combo = ttk.Combobox(controls, textvariable=self.widget_var, width=18, state="readonly")
        self.widget_combo["values"] = ["bento.standard", "bento.info", "bento.mini"]
        self.widget_combo.grid(row=0, column=1, sticky="w")

        ttk.Label(controls, text="Datasource:").grid(row=0, column=2, sticky="w", padx=(12, 6))
        self.datasource_var = tk.StringVar()
        self.datasource_combo = ttk.Combobox(controls, textvariable=self.datasource_var, width=12, state="readonly")
        self.datasource_combo["values"] = ["readwrite", "readonly", "none"]
        self.datasource_combo.grid(row=0, column=3, sticky="w")

        self.datashare_var = tk.BooleanVar()
        self.datashare_check = ttk.Checkbutton(controls, text="Data sharing", variable=self.datashare_var)
        self.datashare_check.grid(row=0, column=4, sticky="w", padx=(12, 0))

        btns = ttk.Frame(detail)
        btns.pack(fill="x", pady=6)
        self.save_btn = ttk.Button(btns, text="Save registry entry", command=self._save_changes)
        self.save_btn.pack(side="left")
        ttk.Button(btns, text="Copy embed snippet", command=self._copy_snippet).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Open workspace URL", command=self._open_link).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Open data URL", command=self._open_data_link).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Snapshot -> Oracle", command=self._snapshot_to_oracle).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Support message", command=self._support_message).pack(side="left", padx=(8, 0))

    # Data loading and filtering
    def _read_registry(self) -> Dict[str, Any]:
        if self.registry_path and self.registry_path.exists():
            try:
                return json.loads(self.registry_path.read_text(encoding="utf-8"))
            except Exception:
                return {"workspaces": []}
        return ops_helper.load_registry()

    def _load_registry(self) -> None:
        registry = self._read_registry()
        self.workspaces = registry.get("workspaces", [])
        self.tags = sorted({tag for ws in self.workspaces for tag in ws.get("tags", [])})
        self.tag_combo["values"] = ["All"] + self.tags
        self.tag_combo.set(self.tag_var.get() if self.tag_var.get() in self.tag_combo["values"] else "All")
        self._refresh_table()

    def _filtered(self) -> List[Dict[str, Any]]:
        query = self.search_var.get().strip().lower()
        tag_filter = self.tag_var.get()

        def matches(ws: Dict[str, Any]) -> bool:
            hay = " ".join([
                ws.get("workspace_id", ""),
                ws.get("title", ""),
                ws.get("description", ""),
            ]).lower()
            tag_ok = tag_filter in (None, "", "All") or tag_filter in ws.get("tags", [])
            text_ok = (query in hay) if query else True
            return text_ok and tag_ok

        return [ws for ws in self.workspaces if matches(ws)]

    def _refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for ws in self._filtered():
            readonly = ops_helper.is_readonly(ws)
            self.tree.insert(
                "",
                "end",
                iid=ws.get("workspace_id"),
                values=(
                    ws.get("workspace_id", ""),
                    ws.get("title", ""),
                    ws.get("widget_type", ""),
                    ws.get("datasource", ""),
                    str(ws.get("data_sharing", False)).lower(),
                    "yes" if readonly else "no",
                ),
            )
        self.status_var.set(f"{len(self._filtered())} workspaces loaded.")
        self._render_detail(None)

    def _workspace_by_id(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        for ws in self.workspaces:
            if ws.get("workspace_id") == workspace_id:
                return ws
        return None

    # Event handlers
    def _on_select(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            self._render_detail(None)
            return
        ws_id = selection[0]
        ws = self._workspace_by_id(ws_id) or ops_helper.get_workspace(ws_id)
        self._render_detail(ws)

    def _render_detail(self, ws: Optional[Dict[str, Any]]) -> None:
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)

        if not ws:
            self.detail_text.insert("1.0", "No workspace selected.")
            self.detail_text.configure(state="disabled")
            return

        readonly = ops_helper.is_readonly(ws)
        lines = [
            f"Workspace: {ws.get('workspace_id','')}",
            f"Title: {ws.get('title','')}",
            f"Description: {ws.get('description','')}",
            f"URL: {ws.get('workspace_url','')}",
            f"Widget: {ws.get('widget_type','')} | Datasource: {ws.get('datasource','')}",
            f"Data sharing: {ws.get('data_sharing', False)}",
            f"Owner floor: {ws.get('owner_floor','')}",
            f"Tags: {', '.join(ws.get('tags', []))}",
            f"Read-only: {'yes' if readonly else 'no'}",
        ]
        if readonly:
            lines.append("Note: This workspace is read-only for protected or vendor-managed integrations.")

        self.detail_text.insert("1.0", "\n".join(lines))
        self.detail_text.configure(state="disabled")
        self.status_var.set(f"{ws.get('workspace_id','')} ready. Copy snippet or open URL.")

        # Controls reflect selection
        self.widget_var.set(ws.get("widget_type", ""))
        self.datasource_var.set(ws.get("datasource", ""))
        self.datashare_var.set(bool(ws.get("data_sharing", False)))
        state = "disabled" if readonly else "readonly"
        self.widget_combo.configure(state=state)
        self.datasource_combo.configure(state=state)
        self.datashare_check.state(["disabled"] if readonly else ["!disabled"])
        self.save_btn.state(["disabled"] if readonly else ["!disabled"])

    def _copy_snippet(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Copy snippet", "Select a workspace first.")
            return
        ws = self._workspace_by_id(selection[0]) or ops_helper.get_workspace(selection[0])
        if not ws:
            messagebox.showinfo("Copy snippet", "Workspace not found in registry.")
            return
        snippet = ops_helper.render_embed_snippet(ws)
        self.parent.clipboard_clear()
        self.parent.clipboard_append(snippet)
        self.status_var.set(f"Copied embed snippet for {ws.get('workspace_id')}.")

    def _open_link(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Open workspace", "Select a workspace first.")
            return
        ws = self._workspace_by_id(selection[0]) or ops_helper.get_workspace(selection[0])
        if not ws:
            messagebox.showinfo("Open workspace", "Workspace not found in registry.")
            return
        url = ws.get("workspace_url")
        if not url:
            messagebox.showinfo("Open workspace", "Workspace URL is missing.")
            return
        webbrowser.open(url)
        self.status_var.set(f"Opened {ws.get('workspace_id')} in browser.")

    def _open_data_link(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Open data", "Select a workspace first.")
            return
        ws = self._workspace_by_id(selection[0]) or ops_helper.get_workspace(selection[0])
        if not ws:
            messagebox.showinfo("Open data", "Workspace not found in registry.")
            return
        url = ws.get("data_url")
        if not url:
            messagebox.showinfo("Open data", "Data URL is missing for this workspace.")
            return
        webbrowser.open(url)
        self.status_var.set(f"Opened data URL for {ws.get('workspace_id')}.")

    def _default_romer_cookies_path(self) -> Optional[str]:
        """
        Best-effort find an operator-provided cookies.txt (Netscape format).

        This enables Oracle URL ingestion to access Squarespace-secured /wN/data endpoints.
        """
        try:
            # Operator override
            import os

            override = (os.environ.get("LIGHTSPEED_ROMER_COOKIES_PATH") or "").strip()
            if override:
                p = Path(override).expanduser()
                if p.exists():
                    return str(p)
        except Exception:
            pass

        root = Path(__file__).resolve()
        for cand in (root.parents[3] / "ai_logs" / "cookies.txt", root.parents[3] / "ai_logs" / "cookies.txt"):
            try:
                if cand.exists():
                    return str(cand)
            except Exception:
                continue
        return None

    def _get_oracle_integrator(self):
        if self._oracle_integrator is not None:
            return self._oracle_integrator

        try:
            from core.services import get_db, get_event_bus, get_storage, get_z_direct, get_oracle_logger  # type: ignore

            db = get_db()
            eb = get_event_bus()
            st = get_storage()
            zd = get_z_direct()
            logger = get_oracle_logger()
        except Exception:
            db = None
            eb = None
            st = None
            zd = None
            logger = None

        try:
            # Avoid import-package pitfalls; load from file path.
            module_path = Path(__file__).resolve().parents[3] / "Z Axis" / "Z-2_Oracle" / "components" / "oracle_smart_floor_integrator.py"
            from importlib.util import spec_from_file_location, module_from_spec

            spec = spec_from_file_location("lightspeed_oracle_integrator_ops_ws", module_path)
            if spec is None or spec.loader is None:
                return None
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)
            cls = getattr(mod, "OracleSmartFloorIntegrator", None)
            if cls is None:
                return None
            self._oracle_integrator = cls(db=db, event_bus=eb, storage=st, z_direct=zd, logger=logger)
            return self._oracle_integrator
        except Exception:
            self._oracle_integrator = None
            return None

    def _snapshot_to_oracle(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Snapshot", "Select a workspace first.")
            return
        ws = self._workspace_by_id(selection[0]) or ops_helper.get_workspace(selection[0])
        if not ws:
            messagebox.showinfo("Snapshot", "Workspace not found in registry.")
            return

        oracle = self._get_oracle_integrator()
        if oracle is None or not hasattr(oracle, "ingest_url"):
            messagebox.showerror("Snapshot", "Oracle URL ingestion is unavailable in this build.")
            return

        wid = ws.get("workspace_id", "unknown")
        title = ws.get("title", "")
        urls = []
        if ws.get("workspace_url"):
            urls.append(("workspace", ws.get("workspace_url")))
        if ws.get("data_url"):
            urls.append(("data", ws.get("data_url")))
        if not urls:
            messagebox.showinfo("Snapshot", "No URLs found on this registry entry.")
            return

        cookies_path = self._default_romer_cookies_path()
        meta_base = {
            "ops_workspace_id": wid,
            "ops_title": title,
            "ops_source": "romer.industries",
            "tags": ["ops", "romer", "snapshot", wid],
        }

        results = []
        for kind, url in urls:
            try:
                res = oracle.ingest_url(
                    str(url),
                    metadata={**meta_base, "ops_url_kind": kind},
                    filename=f"{wid.lower()}_{kind}.html",
                    cookies_path=cookies_path,
                    # For secured endpoints, keep a snapshot even if not authorized (will be a "Secure" page).
                    allow_non_2xx=(kind == "data"),
                )
                results.append((kind, res))
            except Exception as e:
                results.append((kind, {"status": "error", "message": str(e)}))

        ok = sum(1 for _k, r in results if isinstance(r, dict) and r.get("status") == "ok")
        self.status_var.set(f"Snapshot queued for {wid}: {ok}/{len(results)} ok (Oracle).")
        try:
            detail = "\n".join([f"- {k}: {r.get('status')} {r.get('message','')}" for k, r in results if isinstance(r, dict)])
            messagebox.showinfo("Snapshot -> Oracle", f"{wid} queued.\n\n{detail}")
        except Exception:
            pass

    def _support_message(self) -> None:
        """
        Prepare a support/intake message for the selected workspace.

        This is intentionally non-destructive: it copies the message to clipboard and
        opens the Contact page for manual submission (no website changes required).
        """
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Support", "Select a workspace first.")
            return
        ws = self._workspace_by_id(selection[0]) or ops_helper.get_workspace(selection[0])
        if not ws:
            messagebox.showinfo("Support", "Workspace not found in registry.")
            return

        wid = ws.get("workspace_id", "unknown")
        lines = [
            f"LightSpeed Ops Intake: {wid}",
            "",
            f"Workspace: {ws.get('title','')}",
            f"Workspace URL: {ws.get('workspace_url','')}",
            f"Data URL: {ws.get('data_url','')}",
            f"Tags: {', '.join(ws.get('tags', []))}",
            "",
            "Request:",
            "- (Describe the task / issue / upload request here)",
            "",
            "Attachments:",
            "- (If large files: mention they are staged in LightSpeed Oracle and can be referenced by vault_id / Z Direct envelope)",
        ]
        msg = "\n".join(lines)
        try:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(msg)
        except Exception:
            pass

        try:
            webbrowser.open("https://romer.industries/contact-us")
        except Exception:
            pass

        self.status_var.set(f"Support message copied for {wid} (clipboard). Contact page opened.")

    # Persistence helpers
    def _write_registry(self) -> None:
        registry_path = self.registry_path or ops_helper.REGISTRY_PATH
        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "version": "0.1",
            "workspaces": self.workspaces,
        }
        registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _log_change(self, ws_id: str, before: Dict[str, Any], after: Dict[str, Any]) -> None:
        log_path = (self.registry_path or ops_helper.REGISTRY_PATH).parent / "registry_edits.log"
        changed = {
            k: {"before": before.get(k), "after": after.get(k)}
            for k in ["widget_type", "datasource", "data_sharing"]
            if before.get(k) != after.get(k)
        }
        if not changed:
            return
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "workspace_id": ws_id,
            "changed": changed,
        }
        existing = []
        if log_path.exists():
            try:
                existing = json.loads(log_path.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    existing = []
            except Exception:
                existing = []
        existing.append(entry)
        log_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    def _save_changes(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Save", "Select a workspace first.")
            return
        ws = self._workspace_by_id(selection[0]) or ops_helper.get_workspace(selection[0])
        if not ws:
            messagebox.showinfo("Save", "Workspace not found in registry.")
            return
        if ops_helper.is_readonly(ws):
            messagebox.showinfo("Save", "This workspace is read-only.")
            return

        before = dict(ws)
        ws["widget_type"] = self.widget_var.get()
        ws["datasource"] = self.datasource_var.get()
        ws["data_sharing"] = bool(self.datashare_var.get())
        ws["last_updated"] = datetime.utcnow().date().isoformat()

        for i, item in enumerate(self.workspaces):
            if item.get("workspace_id") == ws.get("workspace_id"):
                self.workspaces[i] = ws
                break

        self._write_registry()
        self._log_change(ws.get("workspace_id", ""), before, ws)
        self._write_job_manifest(ws)
        self.status_var.set(f"Saved {ws.get('workspace_id')} (registry updated). Run embed generator if needed.")
        self._refresh_table()

    def _write_job_manifest(self, ws: Dict[str, Any]) -> None:
        """Emit a lightweight job manifest for audit (Smith-ready)."""
        root = (self.registry_path or ops_helper.REGISTRY_PATH).parents[2]
        job_time = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        job_id = f"registry_edit_{ws.get('workspace_id','unknown')}_{job_time}"
        job_dir = _smart_operations_root(root) / "registry_edits" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "job_id": job_id,
            "job_type": "registry_edit",
            "workspace_id": ws.get("workspace_id"),
            "z_context": "Trinity",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "inputs": {
                "registry_path": str(self.registry_path or ops_helper.REGISTRY_PATH)
            },
            "outputs": {
                "registry_snapshot": str(job_dir / "operations_registry.json"),
                "registry_edits_log": str((self.registry_path or ops_helper.REGISTRY_PATH).parent / "registry_edits.log")
            },
            "metadata": {
                "widget_type": ws.get("widget_type"),
                "datasource": ws.get("datasource"),
                "data_sharing": ws.get("data_sharing"),
                "last_updated": ws.get("last_updated")
            },
            "smith": {
                "queue_hint": str(_smart_operations_root(root) / "registry_edits" / "queue.json"),
                "next_steps": [
                    "generate_operations_embeds.py",
                    "generate_dataindex.py"
                ]
            },
            "tags": ["operations", "registry", "workspace_manager"],
        }

        # Copy current registry snapshot
        try:
            registry_text = (self.registry_path or ops_helper.REGISTRY_PATH).read_text(encoding="utf-8")
            (job_dir / "operations_registry.json").write_text(registry_text, encoding="utf-8")
        except Exception:
            pass

        (job_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # Queue for Smith consumption
        self._queue_smith_job(job_dir, manifest)

    def _queue_smith_job(self, job_dir: Path, manifest: Dict[str, Any]) -> None:
        queue_path = job_dir.parent / "queue.json"
        entry = {
            "job_id": manifest.get("job_id"),
            "manifest": str(job_dir / "manifest.json"),
            "created_at": manifest.get("created_at"),
            "workspace_id": manifest.get("workspace_id"),
            "status": "queued",
            "actions": manifest.get("smith", {}).get("next_steps", []),
        }
        existing = []
        if queue_path.exists():
            try:
                existing = json.loads(queue_path.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    existing = []
            except Exception:
                existing = []
        existing.append(entry)
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        queue_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Operations Workspace Manager")
    app = OperationsWorkspaceManager(root)
    root.mainloop()
