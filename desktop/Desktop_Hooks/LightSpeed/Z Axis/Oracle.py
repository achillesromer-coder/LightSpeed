#!/usr/bin/env python
"""
Oracle (Z-2) - Archive & Data Ingestion Floor
Complete Floor Coordinator with Archives, Data Ingestion, and IP Vault

Oracle is THE primary data archiving and ingestion layer. It holds:
- Data archives and historical records
- Auto-ingestion systems and pipelines
- IP vault and proprietary knowledge
- Encyclopedia and dictionary systems
- Smart Floor Library integration

Variables Held:
- archive_index: Indexed archived data
- ingestion_queues: Active ingestion pipelines
- ip_vault_entries: Proprietary knowledge vault
- encyclopedia_data: Curated knowledge entries
- dictionary_cache: Reference data

Renders:
- Oracle portal (glass UI dashboard)
- Ingestion control center
- IP vault browser
- Encyclopedia/dictionary viewer
- Archive search interface
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Optional, Dict, List, Any
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import json
import hashlib


def _load_symbol(rel_path: str, symbol: str):
    """Load a symbol (class/function) from a file by relative path"""
    root = Path(__file__).resolve().parents[1]
    path = (root / rel_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    mod_name = f"lightspeed_dynamic_{path.stem}_{abs(hash(str(path)))%1_000_000}"
    spec = spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    mod = module_from_spec(spec)
    # Ensure dataclasses/type evaluation can resolve __module__ via sys.modules.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, symbol):
        raise AttributeError(f"{symbol} not found in {path}")
    return getattr(mod, symbol)


# Backwards compatibility
_load_class = _load_symbol


class OracleFloorState:
    """
    State manager for Oracle floor

    This class holds all state variables for archiving and data ingestion
    """

    def __init__(self):
        # Archive state
        self.archive_index: Dict[str, Any] = {}
        self.archived_items: List[Dict[str, Any]] = []
        self.total_archives = 0

        # Ingestion state
        self.ingestion_queues: Dict[str, List[Dict]] = {}
        self.active_ingestions: List[Dict[str, Any]] = []
        self.ingestion_history: List[Dict] = []
        self.auto_ingestion_enabled = True

        # IP Vault state
        self.ip_vault_entries: Dict[str, Any] = {}
        self.vault_locked = True
        self.vault_access_log: List[Dict] = []

        # Encyclopedia/Dictionary state
        self.encyclopedia_entries: Dict[str, str] = {}
        self.dictionary_cache: Dict[str, str] = {}
        self.reference_data: Dict[str, Any] = {}

        # Smart Floor Library state
        self.library_connected = False
        self.library_index: Dict[str, Any] = {}

    def add_archive(self, title: str, data: Any, metadata: Dict):
        """Add an item to the archives"""
        archive_id = f"archive_{self.total_archives}"
        archive = {
            'id': archive_id,
            'title': title,
            'data': data,
            'metadata': metadata
        }
        self.archived_items.append(archive)
        self.archive_index[archive_id] = archive
        self.total_archives += 1

    def queue_ingestion(self, source: str, config: Dict):
        """Queue a data ingestion job"""
        if source not in self.ingestion_queues:
            self.ingestion_queues[source] = []
        self.ingestion_queues[source].append(config)


class OracleUI(ttk.Frame):
    """
    Primary Oracle UI - Archive & Data Ingestion

    Oracle owns all data archiving, auto-ingestion, IP vault, and reference systems.
    It provides comprehensive data management and historical record keeping.
    """

    def __init__(self, parent: tk.Misc, app: Optional[object] = None, *, compact: bool = False, **_ignored):
        super().__init__(parent)
        self.app = app
        self.compact = bool(compact)
        self.state = OracleFloorState()
        self.runtime_bridge = getattr(app, "oracle_morpheus_bridge", None)

        try:
            from core.services import get_db, get_event_bus, get_storage
            self.db = getattr(app, "db", None) or get_db()
            self.event_bus = getattr(app, "event_bus", None) or get_event_bus()
            self.storage = getattr(app, "storage", None) or get_storage()
        except Exception:
            self.db = None
            self.event_bus = None
            self.storage = None

        # Register Bento widgets
        self._register_bento_widgets()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Tabs (lazy builders)
        self._tabs: Dict[str, ttk.Frame] = {}
        self._builders: Dict[str, Any] = {}
        # When compact mode is enabled, leaf tabs live in nested notebooks. These maps
        # let us select tabs reliably from Bento buttons / deep-links.
        self._tab_group: Dict[str, str] = {}  # leaf title -> group title
        self._tab_container: Dict[str, Any] = {}  # leaf title -> ttk.Notebook or None
        self._group_frames: Dict[str, ttk.Frame] = {}  # group title -> top notebook frame

        if self.compact:
            self._build_compact_shell()
        else:
            self._build_full_shell()

    def _build_full_shell(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self._register_tab("Portal", self._build_portal)
        self._register_tab("Ingestion", self._build_ingestion)
        self._register_tab("IP Vault", self._build_ip_vault)
        self._register_tab("Encyclopedia", self._build_encyclopedia)
        self._register_tab("Dictionary", self._build_dictionary)
        self._register_tab("Library", self._build_library)
        self._register_tab("Backup & Restore", self._build_backup_restore)
        self._register_tab("Z Direct Registry", self._build_z_direct_registry)

        self._ensure_built("Portal")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _build_compact_shell(self) -> None:
        """
        Compact embedding for IT Portal:
        - Portal (single surface)
        - Operations (ingestion/vault/library/z-direct/backup)
        - Knowledge (encyclopedia/dictionary)
        """
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        portal_group = ttk.Frame(self.notebook)
        ops_group = ttk.Frame(self.notebook)
        know_group = ttk.Frame(self.notebook)

        self.notebook.add(portal_group, text="Portal")
        self.notebook.add(ops_group, text="Operations")
        self.notebook.add(know_group, text="Knowledge")

        self._group_frames = {
            "Portal": portal_group,
            "Operations": ops_group,
            "Knowledge": know_group,
        }

        # Portal is a single surface (no nested notebook).
        self._tabs["Portal"] = portal_group
        self._builders["Portal"] = self._build_portal
        self._tab_group["Portal"] = "Portal"
        self._tab_container["Portal"] = None

        # Operations notebook (nested)
        ops_nb = ttk.Notebook(ops_group)
        ops_nb.pack(fill="both", expand=True)
        self._register_tab("Ingestion", self._build_ingestion, notebook=ops_nb, group="Operations")
        self._register_tab("IP Vault", self._build_ip_vault, notebook=ops_nb, group="Operations")
        self._register_tab("Library", self._build_library, notebook=ops_nb, group="Operations")
        self._register_tab("Z Direct Registry", self._build_z_direct_registry, notebook=ops_nb, group="Operations")
        self._register_tab("Backup & Restore", self._build_backup_restore, notebook=ops_nb, group="Operations")

        # Knowledge notebook (nested)
        know_nb = ttk.Notebook(know_group)
        know_nb.pack(fill="both", expand=True)
        self._register_tab("Encyclopedia", self._build_encyclopedia, notebook=know_nb, group="Knowledge")
        self._register_tab("Dictionary", self._build_dictionary, notebook=know_nb, group="Knowledge")

        # Lazy-load
        self._ensure_built("Portal")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_group_tab_changed)
        ops_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        know_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _register_tab(self, title: str, builder, *, notebook: Optional[ttk.Notebook] = None, group: str = "Portal"):
        """Register a lazy-loaded tab (supports nested notebooks in compact mode)."""
        nb = notebook or self.notebook
        frame = ttk.Frame(nb)
        nb.add(frame, text=title)
        self._tabs[title] = frame
        self._builders[title] = builder
        self._tab_group[title] = group
        self._tab_container[title] = nb

    def _ensure_built(self, title: str):
        """Ensure tab is built"""
        frame = self._tabs.get(title)
        builder = self._builders.get(title)
        if frame is None or builder is None:
            return
        if getattr(frame, "_built", False):
            return
        builder(frame)
        setattr(frame, "_built", True)

    def _on_tab_changed(self, event):
        """Handle tab change - lazy load content"""
        nb = getattr(event, "widget", None) or self.notebook
        current_tab = nb.select()
        tab_text = nb.tab(current_tab, "text")
        self._ensure_built(tab_text)

    def _on_group_tab_changed(self, event):
        """When switching compact groups, ensure the visible leaf is built."""
        try:
            group = self.notebook.tab(self.notebook.select(), "text")
        except Exception:
            return
        if group == "Portal":
            self._ensure_built("Portal")
            return
        # For nested notebooks, ensure the currently-selected leaf is built.
        try:
            grp_frame = self._group_frames.get(group)
            if grp_frame is None:
                return
            children = [w for w in grp_frame.winfo_children() if isinstance(w, ttk.Notebook)]
            if not children:
                return
            nb = children[0]
            leaf = nb.tab(nb.select(), "text")
            self._ensure_built(leaf)
        except Exception:
            return

    def select_tab(self, title: str) -> None:
        """Select a leaf tab by title, regardless of compact/full shell."""
        if title not in self._tabs:
            return
        if not self.compact:
            try:
                self.notebook.select(self._tabs[title])
            except Exception:
                pass
            self._ensure_built(title)
            return

        group = self._tab_group.get(title) or "Portal"
        try:
            self.notebook.select(self._group_frames[group])
        except Exception:
            pass
        if group == "Portal":
            self._ensure_built("Portal")
            return
        nb = self._tab_container.get(title)
        if nb is not None:
            try:
                nb.select(self._tabs[title])
            except Exception:
                pass
        self._ensure_built(title)

    def _build_portal(self, parent: ttk.Frame):
        """Build portal dashboard tab"""
        try:
            from core.ui.base_portal_glass import mount_smart_ops_strip  # type: ignore

            mount_smart_ops_strip(parent, app=self.app, floor_channel="Z-2", it_portal=self.compact, title="Oracle Ops")
        except Exception:
            pass
        try:
            from lightspeed_runtime.desktop_adapters import build_oracle_population_panel

            panel = build_oracle_population_panel(parent, self.app)
            if panel is not None:
                panel.pack(fill="x", padx=12, pady=(0, 10))
        except Exception:
            pass

        actions = ttk.Frame(parent)
        actions.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Label(
            actions,
            text="Primary Oracle workbench: stay in the portal until you deliberately open a deeper surface.",
            justify="left",
        ).pack(side="left", padx=(0, 12))
        ttk.Button(actions, text="Ingestion Queue", command=lambda: self.select_tab("Ingestion")).pack(side="left")
        ttk.Button(actions, text="Knowledge Library", command=lambda: self.select_tab("Library")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Encyclopedia", command=lambda: self.select_tab("Encyclopedia")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Z Direct", command=lambda: self.select_tab("Z Direct Registry")).pack(side="left", padx=(8, 0))

        try:
            Portal = _load_class("Z Axis/Z-2_Oracle/components/oracle_portal_glass.py", "OraclePortalGlass")
            ui = Portal(parent)
            ui.pack(fill="both", expand=True)
        except Exception as e:
            ttk.Label(parent, text=f"Oracle Portal unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_ingestion(self, parent: ttk.Frame):
        """Build ingestion control tab"""
        ttk.Label(parent, text="Data Ingestion Control", font=("Consolas", 14, "bold")).pack(pady=10)
        ttk.Label(parent, text=f"Auto-Ingestion: {'Enabled' if self.state.auto_ingestion_enabled else 'Disabled'}").pack(pady=5)
        ttk.Label(parent, text=f"Active Ingestions: {len(self.state.active_ingestions)}").pack(pady=5)

        try:
            Panel = _load_class("Z Axis/Z-2_Oracle/components/oracle_ui_panel.py", "OracleUIPanel")
            ttk.Button(
                parent,
                text="Open Oracle UI Panel",
                command=lambda: Panel(parent=self.winfo_toplevel()).open_panel(),
            ).pack(padx=10, pady=10)
        except Exception as e:
            ttk.Label(parent, text=f"Oracle UI Panel unavailable:\n{e}", justify="left").pack(
                padx=16, pady=16
            )

        try:
            from lightspeed_runtime.desktop_adapters import mount_oracle_reservoir_overview

            mount_oracle_reservoir_overview(parent, self.app)
        except Exception:
            pass

    def _build_ip_vault(self, parent: ttk.Frame):
        """Build IP vault tab"""
        ttk.Label(parent, text="IP Vault", font=("Consolas", 14, "bold")).pack(pady=10)
        ttk.Label(parent, text=f"Vault Status: {'Locked' if self.state.vault_locked else 'Unlocked'}").pack(pady=5)
        ttk.Label(parent, text=f"Vault Entries: {len(self.state.ip_vault_entries)}").pack(pady=5)

    def _build_encyclopedia(self, parent: ttk.Frame):
        """Build Encyclopedia tab (Oracle-owned persistent A-Z volumes)."""
        ttk.Label(parent, text="Encyclopedia", font=("Consolas", 14, "bold")).pack(pady=(10, 6))
        ttk.Label(
            parent,
            text="Three-volume knowledge repository (Empirical / Economic / Applied). Entries are stored on disk under Oracle.",
            justify="left",
        ).pack(padx=12, pady=(0, 10), anchor="w")

        # Lazy-load system from component file (not a package import).
        enc = None
        vol_enum = None
        try:
            if not hasattr(self, "_encyclopedia_system"):
                try:
                    EncyclopediaSystem = _load_symbol("Z Axis/Z-2_Oracle/components/encyclopedia_system.py", "EncyclopediaSystem")
                    EncyclopediaVolume = _load_symbol("Z Axis/Z-2_Oracle/components/encyclopedia_system.py", "EncyclopediaVolume")
                    vol_enum = EncyclopediaVolume
                except Exception:
                    EncyclopediaSystem = None
                    vol_enum = None

                logger = None
                try:
                    from core.services import get_oracle_logger  # type: ignore
                    logger = get_oracle_logger()
                except Exception:
                    logger = None

                if EncyclopediaSystem is not None:
                    setattr(self, "_encyclopedia_system", EncyclopediaSystem(db=self.db, logger=logger))
                    setattr(self, "_encyclopedia_volume_enum", vol_enum)
                else:
                    setattr(self, "_encyclopedia_system", None)
                    setattr(self, "_encyclopedia_volume_enum", None)

            enc = getattr(self, "_encyclopedia_system", None)
            vol_enum = getattr(self, "_encyclopedia_volume_enum", None)
        except Exception:
            enc = None
            vol_enum = None

        if enc is None:
            ttk.Label(parent, text="Encyclopedia System unavailable.", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )
            return

        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        controls = ttk.Frame(container)
        controls.pack(fill="x", pady=(0, 8))

        stats_var = tk.StringVar(value="")
        ttk.Label(controls, textvariable=stats_var).pack(side="left")

        ttk.Label(controls, text="Volume:").pack(side="left", padx=(14, 4))
        vol_var = tk.StringVar(value="All")
        vol_values = ["All", "Empirical", "Economic", "Applied"]
        vol_combo = ttk.Combobox(controls, textvariable=vol_var, state="readonly", width=14, values=vol_values)
        vol_combo.pack(side="left", padx=(0, 12))

        ttk.Label(controls, text="Search:").pack(side="left")
        q_var = tk.StringVar(value="")
        ttk.Entry(controls, textvariable=q_var, width=40).pack(side="left", padx=(6, 14), fill="x", expand=True)

        btns = ttk.Frame(controls)
        btns.pack(side="right")

        def _open_folder() -> None:
            try:
                base = getattr(enc, "base_path", None)
                if base:
                    os.startfile(str(base))  # type: ignore[attr-defined]
            except Exception:
                return

        ttk.Button(btns, text="Open Folder", command=_open_folder).pack(side="left", padx=(0, 6))

        # Layout panes: list + details
        panes = ttk.PanedWindow(container, orient="horizontal")
        panes.pack(fill="both", expand=True)

        left = ttk.Frame(panes)
        right = ttk.Frame(panes)
        try:
            panes.add(left, weight=2)
            panes.add(right, weight=3)
        except Exception:
            panes.add(left)
            panes.add(right)

        cols = ("term", "volume", "cat", "updated")
        tree = ttk.Treeview(left, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c.upper())
        tree.column("term", width=280, anchor="w")
        tree.column("volume", width=110, anchor="w")
        tree.column("cat", width=55, anchor="center")
        tree.column("updated", width=160, anchor="w")
        tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(left, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)

        details = scrolledtext.ScrolledText(right, height=18, bg="#1e1e1e", fg="#00FF88", font=("Consolas", 9))
        details.pack(fill="both", expand=True)

        state: Dict[str, Any] = {"rows": []}

        def _sel_volume():
            v = (vol_var.get() or "All").strip()
            if vol_enum is None:
                return None
            try:
                if v == "Empirical":
                    return vol_enum.EMPIRICAL
                if v == "Economic":
                    return vol_enum.ECONOMIC
                if v == "Applied":
                    return vol_enum.APPLIED
            except Exception:
                return None
            return None

        def refresh():
            try:
                tree.delete(*tree.get_children())
            except Exception:
                pass

            try:
                stats = enc.get_statistics()
                stats_var.set(f"Entries: {int(stats.get('total_entries') or 0)}")
            except Exception:
                stats_var.set("")

            q = (q_var.get() or "").strip()
            vol = _sel_volume()

            rows = []
            try:
                if q:
                    rows = enc.search(q, volume=vol)
                else:
                    # No query: show everything, optionally filtered by volume.
                    rows = list(getattr(enc, "entry_index", {}).values())
                    if vol is not None:
                        rows = [e for e in rows if isinstance(e, dict) and e.get("volume") == getattr(vol, "name", None)]
            except Exception:
                rows = []

            view = []
            for e in rows or []:
                if not isinstance(e, dict):
                    continue
                term = str(e.get("term") or "")
                vol_name = str(e.get("volume") or "")
                cat = str(e.get("category_letter") or "")
                updated = str(e.get("updated_at") or e.get("created_at") or "")
                view.append(e)
                try:
                    tree.insert("", tk.END, values=(term, vol_name, cat, updated[:19]))
                except Exception:
                    pass

            state["rows"] = view
            render_details(None)

        def selected_obj():
            try:
                sel = tree.selection()
                if not sel:
                    return None
                idx = tree.index(sel[0])
                rows = state.get("rows") or []
                if 0 <= idx < len(rows):
                    return rows[idx]
            except Exception:
                return None
            return None

        def render_details(obj):
            try:
                details.delete("1.0", tk.END)
                if not obj:
                    details.insert(tk.END, "Select an entry to view details.")
                else:
                    details.insert(tk.END, json.dumps(obj, indent=2, ensure_ascii=False))
            except Exception:
                pass

        def on_select(_evt=None):
            render_details(selected_obj())

        tree.bind("<<TreeviewSelect>>", on_select)
        q_var.trace_add("write", lambda *_: refresh())
        vol_combo.bind("<<ComboboxSelected>>", lambda _e: refresh())

        refresh()

    def _build_dictionary(self, parent: ttk.Frame):
        """Build multilingual dictionary viewer (hardcoded foundation + extensions)."""
        ttk.Label(parent, text="Dictionary", font=("Consolas", 14, "bold")).pack(pady=(10, 6))
        ttk.Label(
            parent,
            text="Hardcoded foundation terms (multilingual) used by Oracle Encyclopedia entries.",
            justify="left",
        ).pack(padx=12, pady=(0, 10), anchor="w")

        enc = getattr(self, "_encyclopedia_system", None)
        if enc is None:
            # Ensure encyclopedia system is initialized (dictionary lives there) without rendering UI.
            try:
                EncyclopediaSystem = _load_symbol("Z Axis/Z-2_Oracle/components/encyclopedia_system.py", "EncyclopediaSystem")
            except Exception:
                EncyclopediaSystem = None

            logger = None
            try:
                from core.services import get_oracle_logger  # type: ignore
                logger = get_oracle_logger()
            except Exception:
                logger = None

            try:
                if EncyclopediaSystem is not None:
                    enc = EncyclopediaSystem(db=self.db, logger=logger)
                    setattr(self, "_encyclopedia_system", enc)
            except Exception:
                enc = None

        if enc is None:
            ttk.Label(parent, text="Dictionary unavailable.", justify="left").pack(fill="both", expand=True, padx=16, pady=16)
            return

        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        controls = ttk.Frame(container)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Label(controls, text="Search:").pack(side="left")
        q_var = tk.StringVar(value="")
        ttk.Entry(controls, textvariable=q_var, width=40).pack(side="left", padx=(6, 14), fill="x", expand=True)

        stats_var = tk.StringVar(value="")
        ttk.Label(controls, textvariable=stats_var).pack(side="right")

        panes = ttk.PanedWindow(container, orient="horizontal")
        panes.pack(fill="both", expand=True)

        left = ttk.Frame(panes)
        right = ttk.Frame(panes)
        try:
            panes.add(left, weight=2)
            panes.add(right, weight=3)
        except Exception:
            panes.add(left)
            panes.add(right)

        cols = ("term", "umbrella", "si_unit")
        tree = ttk.Treeview(left, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c.upper())
        tree.column("term", width=220, anchor="w")
        tree.column("umbrella", width=160, anchor="w")
        tree.column("si_unit", width=80, anchor="center")
        tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(left, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)

        details = scrolledtext.ScrolledText(right, height=18, bg="#1e1e1e", fg="#00FF88", font=("Consolas", 9))
        details.pack(fill="both", expand=True)

        state: Dict[str, Any] = {"rows": []}

        def refresh():
            try:
                tree.delete(*tree.get_children())
            except Exception:
                pass

            d = getattr(enc, "dictionary", {}) or {}
            q = (q_var.get() or "").strip().lower()
            rows = []
            for term, payload in d.items():
                if not isinstance(payload, dict):
                    continue
                if q and q not in str(term).lower() and q not in json.dumps(payload).lower():
                    continue
                umbrella = str(payload.get("umbrella") or "")
                si = str(payload.get("si_unit") or payload.get("symbol") or "")
                rows.append({"term": term, "payload": payload, "umbrella": umbrella, "si": si})

            rows.sort(key=lambda r: str(r.get("term") or "").lower())
            state["rows"] = rows
            stats_var.set(f"Terms: {len(rows)}")

            for r in rows:
                try:
                    tree.insert("", tk.END, values=(r.get("term"), r.get("umbrella"), r.get("si")))
                except Exception:
                    pass

            render_details(None)

        def selected_obj():
            try:
                sel = tree.selection()
                if not sel:
                    return None
                idx = tree.index(sel[0])
                rows = state.get("rows") or []
                if 0 <= idx < len(rows):
                    return rows[idx]
            except Exception:
                return None
            return None

        def render_details(obj):
            try:
                details.delete("1.0", tk.END)
                if not obj:
                    details.insert(tk.END, "Select a term to view details.")
                else:
                    details.insert(tk.END, json.dumps(obj.get("payload") or {}, indent=2, ensure_ascii=False))
            except Exception:
                pass

        tree.bind("<<TreeviewSelect>>", lambda _e: render_details(selected_obj()))
        q_var.trace_add("write", lambda *_: refresh())

        refresh()


    def _oracle_registry_path(self) -> Path:
        """Return the durable registry path for Oracle (committed objects)."""
        try:
            from core.config.paths import ORACLE_ROOT  # type: ignore
            return Path(ORACLE_ROOT) / "Z Direct" / "objects.json"
        except Exception:
            # Floor entrypoint lives under `Z Axis/Oracle.py`.
            return Path(__file__).parent / "Z-2_Oracle" / "Z Direct" / "objects.json"

    def _load_oracle_registry_objects(self) -> list[dict]:
        path = self._oracle_registry_path()
        try:
            if not path.exists():
                return []
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            out = []
            for v in data.values():
                if isinstance(v, dict):
                    out.append(v)
            return out
        return []

    def _build_library(self, parent: ttk.Frame):
        """Readable, menu-like browser for Oracle's durable registry."""
        ttk.Label(parent, text="Library (Oracle Durable Registry)", font=("Consolas", 14, "bold")).pack(pady=(10, 6))
        ttk.Label(
            parent,
            text="Browse committed Oracle objects. For new knowledge, stage proposals to Trinity for review.",
            justify="left",
        ).pack(padx=12, pady=(0, 10), anchor="w")

        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        controls = ttk.Frame(container)
        controls.pack(fill="x", pady=(0, 8))

        ttk.Label(controls, text="Kind:").pack(side="left")
        kind_var = tk.StringVar(value="all")
        kind_combo = ttk.Combobox(
            controls,
            textvariable=kind_var,
            state="readonly",
            width=18,
            values=["all", "vault_file", "knowledge_node", "citation", "learning_module", "workspace", "research_query", "dataset", "experiment_run"],
        )
        kind_combo.pack(side="left", padx=(6, 14))

        ttk.Label(controls, text="Search:").pack(side="left")
        query_var = tk.StringVar(value="")
        ttk.Entry(controls, textvariable=query_var, width=40).pack(side="left", padx=(6, 14), fill="x", expand=True)

        btns = ttk.Frame(controls)
        btns.pack(side="right")

        # Stage knowledge proposal (non-destructive; routes into Trinity inbox/outbox)
        ttk.Button(btns, text="Stage Knowledge Proposal...", command=lambda: self._stage_knowledge_proposal(parent)).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Refresh", command=lambda: refresh()).pack(side="left")

        panes = ttk.PanedWindow(container, orient="horizontal")
        panes.pack(fill="both", expand=True)

        left = ttk.Frame(panes)
        right = ttk.Frame(panes)
        try:
            panes.add(left, weight=2)
            panes.add(right, weight=3)
        except Exception:
            panes.add(left)
            panes.add(right)

        cols = ("kind", "id", "title")
        tree = ttk.Treeview(left, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c.upper())
        tree.column("kind", width=130, anchor="w")
        tree.column("id", width=110, anchor="w")
        tree.column("title", width=520, anchor="w")
        tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(left, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)

        details = scrolledtext.ScrolledText(right, height=18, bg="#1e1e1e", fg="#00FF88", font=("Consolas", 9))
        details.pack(fill="both", expand=True)

        state = {"rows": []}

        def _title_for(obj: dict) -> str:
            k = str(obj.get("kind") or "")
            if k == "vault_file":
                return str(obj.get("source_name") or obj.get("name") or "")
            if k == "knowledge_node":
                return str(obj.get("concept") or "")
            if k == "citation":
                return str(obj.get("note") or "")
            return str(obj.get("title") or obj.get("name") or obj.get("query_text") or "")

        def refresh():
            try:
                tree.delete(*tree.get_children())
            except Exception:
                pass

            rows = self._load_oracle_registry_objects()
            ksel = (kind_var.get() or "all").strip()
            q = (query_var.get() or "").strip().lower()

            view = []
            for obj in rows:
                if not isinstance(obj, dict):
                    continue
                k = str(obj.get("kind") or "")
                if ksel != "all" and k != ksel:
                    continue
                rid = str(obj.get("id") or "")
                title = _title_for(obj)
                hay = f"{k} {rid} {title}".lower()
                if q and q not in hay:
                    continue
                view.append(obj)
                try:
                    tree.insert("", tk.END, values=(k, rid, (title[:160] + "...") if len(title) > 160 else title))
                except Exception:
                    pass

            state["rows"] = view
            render_details(None)

        def selected_obj():
            try:
                sel = tree.selection()
                if not sel:
                    return None
                idx = tree.index(sel[0])
                rows = state.get("rows") or []
                if 0 <= idx < len(rows):
                    return rows[idx]
            except Exception:
                return None
            return None

        def render_details(obj):
            try:
                details.delete("1.0", tk.END)
                if not obj:
                    details.insert(tk.END, "Select an item to view details.")
                else:
                    details.insert(tk.END, json.dumps(obj, indent=2))
            except Exception:
                pass

        def on_select(_evt=None):
            render_details(selected_obj())

        def open_selected(_evt=None):
            obj = selected_obj()
            if not obj:
                return
            # Best-effort file open
            p = obj.get("path") or obj.get("source_path")
            try:
                if isinstance(p, str) and p.strip():
                    fp = Path(p)
                    if fp.exists():
                        os.startfile(str(fp))  # type: ignore[attr-defined]
            except Exception:
                return

        tree.bind("<<TreeviewSelect>>", on_select)
        tree.bind("<Double-Button-1>", open_selected)
        query_var.trace_add("write", lambda *_: refresh())
        kind_combo.bind("<<ComboboxSelected>>", lambda _e: refresh())

        refresh()

    def _stage_knowledge_proposal(self, parent: ttk.Frame) -> None:
        """Pick a file and stage an Oracle knowledge proposal into Trinity for approval."""
        try:
            fp = filedialog.askopenfilename(parent=self.winfo_toplevel(), title="Select file to propose")
        except Exception:
            fp = ""
        if not fp:
            return

        try:
            src = Path(fp)
            if not src.exists():
                messagebox.showwarning("Proposal", f"File not found:\\n{src}", parent=self.winfo_toplevel())
                return
        except Exception:
            return

        sha = ""
        try:
            sha = hashlib.sha256(src.read_bytes()).hexdigest()
        except Exception:
            sha = ""

        vault_file = {
            "kind": "vault_file",
            "id": f"vault_{sha[:16]}" if sha else f"vault_{src.stem}",
            "path": str(src),
            "source_name": src.name,
            "sha256": sha,
            "metadata": {"proposed_by": "oracle.ui"},
        }

        try:
            # Neo owns the objectifier; Oracle calls it to stage proposals.
            Objectifier = _load_class("Z Axis/Z+2_Neo/ai/document_objectifier.py", "DocumentObjectifier")
            obj = Objectifier()
            res = obj.stage_knowledge_proposal_to_trinity(vault_file)
            if not isinstance(res, dict) or not res.get("success"):
                messagebox.showerror("Proposal", str((res or {}).get("error") or "Stage failed"), parent=self.winfo_toplevel())
                return
            messagebox.showinfo(
                "Proposal",
                f"Staged proposal(s): {res.get('staged')}\\nReview in Trinity IT Portal - Z Direct (Channel Z+3).",
                parent=self.winfo_toplevel(),
            )
        except Exception as e:
            messagebox.showerror("Proposal", f"Stage failed:\\n{e}", parent=self.winfo_toplevel())

    def _build_backup_restore(self, parent: ttk.Frame):
        """Backup & Restore is request-only: stage restore requests for Trinity review."""
        ttk.Label(parent, text="Backup & Restore (Request Only)", font=("Consolas", 14, "bold")).pack(pady=(10, 6))
        ttk.Label(
            parent,
            text="Restores are not automatic. Stage a restore request into Trinity for review/approval before any action.",
            justify="left",
        ).pack(padx=12, pady=(0, 10), anchor="w")

        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        top = ttk.Frame(container)
        top.pack(fill="x", pady=(0, 8))

        self._backup_status = tk.StringVar(value="Scanning for backups...")
        ttk.Label(top, textvariable=self._backup_status).pack(side="left")

        ttk.Button(top, text="Refresh", command=lambda: refresh()).pack(side="right")
        ttk.Button(top, text="Stage Restore Request", command=lambda: stage_request()).pack(side="right", padx=(0, 6))

        cols = ("modified", "path")
        tree = ttk.Treeview(container, columns=cols, show="tree headings", height=14)
        tree.heading("#0", text="Backup")
        tree.heading("modified", text="Modified")
        tree.heading("path", text="Path")
        tree.column("#0", width=340, anchor="w")
        tree.column("modified", width=170, anchor="w")
        tree.column("path", width=620, anchor="w")
        tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)

        state = {"rows": []}

        def find_backups() -> list[Path]:
            roots = []
            try:
                roots.append(Path(__file__).parent / "Z-1_Morpheus")
            except Exception:
                pass
            # Best-effort: search within Z Axis for crystallization backups.
            try:
                z_axis = Path(__file__).parent
                roots.append(z_axis)
            except Exception:
                pass

            found = []
            seen = set()
            for r in roots:
                try:
                    if not r.exists():
                        continue
                    for d in r.rglob("_CRYSTALLIZATION_BACKUP_*"):
                        if d.is_dir():
                            key = str(d.resolve())
                            if key not in seen:
                                seen.add(key)
                                found.append(d)
                except Exception:
                    continue
            return sorted(found, key=lambda x: x.name)

        def refresh():
            try:
                tree.delete(*tree.get_children())
            except Exception:
                pass
            rows = []
            backups = find_backups()
            for d in backups:
                try:
                    import datetime as _dt
                    mod_s = _dt.datetime.fromtimestamp(d.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    mod_s = ""
                rows.append({"name": d.name, "path": str(d), "modified": mod_s})
                try:
                    tree.insert("", tk.END, text=d.name, values=(mod_s, str(d)))
                except Exception:
                    pass

            state["rows"] = rows
            try:
                self._backup_status.set(f"Backups found: {len(rows)}")
            except Exception:
                pass

        def selected():
            try:
                sel = tree.selection()
                if not sel:
                    return None
                idx = tree.index(sel[0])
                rows = state.get("rows") or []
                if 0 <= idx < len(rows):
                    return rows[idx]
            except Exception:
                return None
            return None

        def stage_request():
            it = selected()
            if not it:
                messagebox.showwarning("Restore", "Select a backup directory first.", parent=self.winfo_toplevel())
                return

            try:
                from core.services import get_z_direct  # type: ignore
                zd = get_z_direct()
            except Exception as e:
                messagebox.showerror("Restore", f"Z Direct unavailable:\\n{e}", parent=self.winfo_toplevel())
                return

            payload = {
                "kind": "restore_request",
                "id": f"restore_{hash(it.get('path')) & 0xffffffff:08x}",
                "backup_path": it.get("path"),
                "requested_by": "oracle.ui",
                "note": "Request-only. Requires Trinity review before any restore.",
            }

            env = zd.make_envelope(
                kind="object",
                channel="Z-2",
                z_context="Z-2_Oracle",
                source="oracle.restore_request",
                tags=["proposal", "restore", "backup"],
                payload=payload,
            )

            try:
                zd.append_object("Z+3", env)
            except Exception as e:
                messagebox.showerror("Restore", f"Stage failed:\\n{e}", parent=self.winfo_toplevel())
                return

            messagebox.showinfo("Restore", "Restore request staged to Trinity (Z+3).", parent=self.winfo_toplevel())

        refresh()

    def _build_z_direct_registry(self, parent: ttk.Frame):
        """
        Z Direct Registry (Oracle): browse committed objects for interactability.

        Trinity is the approval gate for commits; this view reads the durable registry:
        `Z Axis/Z-2_Oracle/Z Direct/objects.json`.
        """
        ttk.Label(parent, text="Z Direct Registry (Committed)", font=("Consolas", 14, "bold")).pack(pady=10)

        try:
            from core.services import get_z_direct  # type: ignore
            z_direct = get_z_direct()
        except Exception as e:
            ttk.Label(parent, text=f"Z Direct unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )
            return

        # This is the missing interactability surface: committed objects + their schemas should be
        # browseable from a single place, even outside the IT Portal.
        sub = ttk.Notebook(parent)
        sub.pack(fill="both", expand=True, padx=10, pady=10)

        objects_tab = ttk.Frame(sub)
        schemas_tab = ttk.Frame(sub)
        builtin_tab = ttk.Frame(sub)
        sub.add(objects_tab, text="Objects")
        sub.add(schemas_tab, text="Schemas")
        sub.add(builtin_tab, text="Builtin Schemas")

        def _make_split_view(host: ttk.Frame):
            outer = ttk.Frame(host)
            outer.pack(fill="both", expand=True)
            outer.columnconfigure(0, weight=1)
            outer.columnconfigure(1, weight=2)
            outer.rowconfigure(0, weight=1)

            left = ttk.Frame(outer)
            left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
            right = ttk.Frame(outer)
            right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

            listbox = tk.Listbox(left, height=20, font=("Consolas", 10))
            listbox.pack(fill="both", expand=True)

            details = tk.Text(right, wrap="word", font=("Consolas", 10))
            details.pack(fill="both", expand=True)
            return listbox, details

        def _render_into(details_widget: tk.Text, value: Any) -> None:
            try:
                details_widget.delete("1.0", "end")
            except Exception:
                pass
            try:
                details_widget.insert("1.0", json.dumps(value, indent=2, ensure_ascii=True))
            except Exception:
                details_widget.insert("1.0", str(value))

        # ------------------------------
        # Objects tab
        # ------------------------------
        obj_list, obj_details = _make_split_view(objects_tab)
        obj_state: Dict[str, Any] = {"items": []}

        obj_btns = ttk.Frame(objects_tab)
        obj_btns.pack(fill="x", pady=(10, 0))

        def _load_objects() -> None:
            try:
                items = z_direct.read_registry("Z-2", name="objects")
            except Exception:
                items = []

            # This view is for interactable objects. Hide schemas here and prefer vault files when present.
            items = [it for it in (items or []) if isinstance(it, dict) and it.get("kind") != "schema"]
            vaults = [it for it in items if isinstance(it, dict) and it.get("kind") == "vault_file"]
            obj_state["items"] = vaults if vaults else (items or [])

            obj_list.delete(0, "end")
            for it in obj_state["items"]:
                kind = (it.get("kind") or "object") if isinstance(it, dict) else "object"
                oid = (it.get("id") or "") if isinstance(it, dict) else ""
                name = (it.get("name") or it.get("title") or "") if isinstance(it, dict) else ""
                obj_list.insert("end", f"{kind} {oid} {name}".strip())
            _render_into(obj_details, {"count": len(obj_state["items"]), "channel": "Z-2"})

        def _open_object_file() -> None:
            try:
                sel = obj_list.curselection()
                if not sel:
                    messagebox.showwarning("Registry", "Select an item first.", parent=self.winfo_toplevel())
                    return
                it = obj_state["items"][int(sel[0])]
                if not isinstance(it, dict):
                    messagebox.showwarning("Registry", "Invalid item selection.", parent=self.winfo_toplevel())
                    return
                p = it.get("path") or it.get("source_path")
                if not isinstance(p, str) or not p.strip():
                    messagebox.showwarning("Registry", "No file path on this object.", parent=self.winfo_toplevel())
                    return
                fp = Path(p)
                if not fp.exists():
                    messagebox.showwarning("Registry", f"File not found:\n{fp}", parent=self.winfo_toplevel())
                    return
                os.startfile(str(fp))  # type: ignore[attr-defined]
            except Exception as e:
                messagebox.showerror("Registry", f"Open failed:\n{e}", parent=self.winfo_toplevel())

        def _on_object_select(_evt=None) -> None:
            try:
                sel = obj_list.curselection()
                if not sel:
                    return
                it = obj_state["items"][int(sel[0])]
                _render_into(obj_details, it)
            except Exception:
                return

        ttk.Button(obj_btns, text="Refresh", command=_load_objects).pack(side="left")
        ttk.Button(obj_btns, text="Open File", command=_open_object_file).pack(side="left", padx=(8, 0))
        obj_list.bind("<<ListboxSelect>>", _on_object_select)
        _load_objects()

        # ------------------------------
        # Schemas tab
        # ------------------------------
        sch_list, sch_details = _make_split_view(schemas_tab)
        sch_state: Dict[str, Any] = {"items": []}

        sch_btns = ttk.Frame(schemas_tab)
        sch_btns.pack(fill="x", pady=(10, 0))

        def _load_schemas() -> None:
            try:
                items = z_direct.read_registry("Z-2", name="objects")
            except Exception:
                items = []
            schemas = [it for it in (items or []) if isinstance(it, dict) and it.get("kind") == "schema"]
            sch_state["items"] = schemas

            sch_list.delete(0, "end")
            for it in sch_state["items"]:
                sid = (it.get("id") or "") if isinstance(it, dict) else ""
                name = (it.get("name") or "") if isinstance(it, dict) else ""
                sch_list.insert("end", f"schema {sid} {name}".strip())
            _render_into(sch_details, {"count": len(sch_state["items"]), "channel": "Z-2"})

        def _copy_selected_schema() -> None:
            try:
                sel = sch_list.curselection()
                if not sel:
                    messagebox.showwarning("Schemas", "Select a schema first.", parent=self.winfo_toplevel())
                    return
                it = sch_state["items"][int(sel[0])]
                if not isinstance(it, dict):
                    return
                payload = it.get("json_schema") if isinstance(it.get("json_schema"), dict) else None
                if payload is None:
                    payload = it.get("schema") if isinstance(it.get("schema"), dict) else None
                if payload is None:
                    payload = it
                txt = json.dumps(payload, indent=2, ensure_ascii=True)
                top = self.winfo_toplevel()
                top.clipboard_clear()
                top.clipboard_append(txt)
                messagebox.showinfo("Schemas", "Schema JSON copied to clipboard.", parent=top)
            except Exception as e:
                messagebox.showerror("Schemas", f"Copy failed:\n{e}", parent=self.winfo_toplevel())

        def _on_schema_select(_evt=None) -> None:
            try:
                sel = sch_list.curselection()
                if not sel:
                    return
                it = sch_state["items"][int(sel[0])]
                _render_into(sch_details, it)
            except Exception:
                return

        ttk.Button(sch_btns, text="Refresh", command=_load_schemas).pack(side="left")
        ttk.Button(sch_btns, text="Copy Schema JSON", command=_copy_selected_schema).pack(side="left", padx=(8, 0))
        sch_list.bind("<<ListboxSelect>>", _on_schema_select)
        _load_schemas()

        # ------------------------------
        # Builtin schemas tab (read-only)
        # ------------------------------
        bi_list, bi_details = _make_split_view(builtin_tab)
        bi_state: Dict[str, Any] = {"items": []}

        bi_btns = ttk.Frame(builtin_tab)
        bi_btns.pack(fill="x", pady=(10, 0))

        def _load_builtin() -> None:
            try:
                items = z_direct.builtin_schema_payloads() if hasattr(z_direct, "builtin_schema_payloads") else []
            except Exception:
                items = []
            bi_state["items"] = items or []
            bi_list.delete(0, "end")
            for it in bi_state["items"]:
                sid = (it.get("id") or "") if isinstance(it, dict) else ""
                name = (it.get("name") or "") if isinstance(it, dict) else ""
                bi_list.insert("end", f"builtin {sid} {name}".strip())
            _render_into(bi_details, {"count": len(bi_state["items"]), "source": "builtin_schema_payloads"})

        def _copy_builtin() -> None:
            try:
                sel = bi_list.curselection()
                if not sel:
                    messagebox.showwarning("Builtin Schemas", "Select a schema first.", parent=self.winfo_toplevel())
                    return
                it = bi_state["items"][int(sel[0])]
                txt = json.dumps(it, indent=2, ensure_ascii=True)
                top = self.winfo_toplevel()
                top.clipboard_clear()
                top.clipboard_append(txt)
                messagebox.showinfo("Builtin Schemas", "Schema payload copied to clipboard.", parent=top)
            except Exception as e:
                messagebox.showerror("Builtin Schemas", f"Copy failed:\n{e}", parent=self.winfo_toplevel())

        def _on_builtin_select(_evt=None) -> None:
            try:
                sel = bi_list.curselection()
                if not sel:
                    return
                it = bi_state["items"][int(sel[0])]
                _render_into(bi_details, it)
            except Exception:
                return

        ttk.Button(bi_btns, text="Refresh", command=_load_builtin).pack(side="left")
        ttk.Button(bi_btns, text="Copy Payload", command=_copy_builtin).pack(side="left", padx=(8, 0))
        bi_list.bind("<<ListboxSelect>>", _on_builtin_select)
        _load_builtin()

    def _register_bento_widgets(self):
        """Register Oracle widgets with Bento system"""
        try:
            import sys
            trinity_path = Path(__file__).parent / "Z+3_Trinity"
            if str(trinity_path) not in sys.path:
                sys.path.insert(0, str(trinity_path))

            from ui.universal_bento_system import register_floor_widgets, BentoWidget, BentoWidgetType

            widgets = [
                BentoWidget(
                    id="oracle_encyclopedia",
                    title="Encyclopedia",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-2_Oracle",
                    callback=lambda w: self._open_encyclopedia(),
                    config={"icon": "ENC", "description": "Browse encyclopedia"}
                ),
                BentoWidget(
                    id="oracle_dictionary",
                    title="Dictionary",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-2_Oracle",
                    callback=lambda w: self._open_dictionary(),
                    config={"icon": "DICT", "description": "Search dictionary"}
                ),
                BentoWidget(
                    id="oracle_ip_vault",
                    title="IP Vault",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-2_Oracle",
                    callback=lambda w: self._open_ip_vault(),
                    config={"icon": "VAULT", "description": "Access IP vault"}
                )
                ,
                BentoWidget(
                    id="oracle_z_direct",
                    title="Z Direct",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-2_Oracle",
                    callback=lambda w: self.select_tab("Z Direct Registry"),
                    config={"icon": "Z", "description": "Browse committed objects + schemas (read-only)"}
                ),
                BentoWidget(
                    id="oracle_library",
                    title="Library",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-2_Oracle",
                    callback=lambda w: self.select_tab("Library"),
                    config={"icon": "LIB", "description": "Browse durable registry + stage proposals"}
                ),
                BentoWidget(
                    id="oracle_backup_restore",
                    title="Backup & Restore",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-2_Oracle",
                    callback=lambda w: self.select_tab("Backup & Restore"),
                    config={"icon": "BACKUP", "description": "Stage restore requests (approval-gated)"}
                ),
            ]

            register_floor_widgets("Z-2_Oracle", widgets)
            print("[Oracle] Registered Oracle Bento widgets")
        except Exception as e:
            print(f"[Oracle] Could not register Bento widgets: {e}")

    def _open_encyclopedia(self):
        """Open encyclopedia tab"""
        print("[Oracle] Opening Encyclopedia...")
        self.select_tab("Encyclopedia")

    def _open_dictionary(self):
        """Open dictionary tab"""
        print("[Oracle] Opening Dictionary...")
        self.select_tab("Dictionary")

    def _open_ip_vault(self):
        """Open IP vault tab"""
        print("[Oracle] Opening IP Vault...")
        self.select_tab("IP Vault")


def create_gui(*args, **kwargs):
    """
    N.py / IT Portal integration entry point.

    Supported call shapes:
    - create_gui(parent, colors)
    - create_gui(app, parent, colors)
    """
    app = None
    parent = None
    if args and isinstance(args[0], tk.Misc):
        parent = args[0]
    elif len(args) >= 2 and isinstance(args[1], tk.Misc):
        app = args[0]
        parent = args[1]
    if parent is None:
        return None
    compact = bool(kwargs.get("compact") or kwargs.get("it_portal"))
    return OracleUI(parent, app=app, compact=compact)


def build(*args, **kwargs):
    """Alias for legacy floor loaders."""
    return create_gui(*args, **kwargs)


# ---------------------------------------------------------------------------
# Floor boot hook (used by FloorLoader)
# ---------------------------------------------------------------------------

_ORACLE_INITIALIZED = False
ORACLE_RUNTIME: Dict[str, Any] = {}


def initialize(*, components: Optional[Dict[str, Any]] = None, dependencies: Optional[Dict[str, Any]] = None, **_kwargs) -> bool:
    """
    Initialize Oracle floor runtime services.

    This runs during floor bootstrap (no UI) and ensures Oracle's
    background services and integrations are active.

    Args:
        components: Pre-loaded component classes/instances
        dependencies: Shared services (db, event_bus, storage, logger)
        **_kwargs: Additional platform parameters

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    global _ORACLE_INITIALIZED, ORACLE_RUNTIME
    if _ORACLE_INITIALIZED:
        return True
    _ORACLE_INITIALIZED = True

    try:
        # Core services are provided by the Merovingian floor (`Z Axis/Z-4_Merovingian/core`).
        # Use the stable namespace import path (`core.services`) and avoid invalid module names.
        from core.services import get_db, get_event_bus, get_storage, get_logger  # type: ignore

        db = get_db()
        event_bus = get_event_bus()
        storage = get_storage()
        logger = get_logger()
    except Exception as e:
        print(f"[Oracle] Failed to load core services: {e}")
        db = None
        event_bus = None
        storage = None
        logger = None

    ORACLE_RUNTIME["db"] = db
    ORACLE_RUNTIME["event_bus"] = event_bus
    ORACLE_RUNTIME["storage"] = storage
    ORACLE_RUNTIME["logger"] = logger

    # Floor-specific initialization

    # Start file ingestion watcher
    try:
        integrator_cls = None
        if isinstance(components, dict):
            integrator_cls = components.get("oracle_smart_integrator")
        if integrator_cls is None:
            integrator_cls = _load_symbol(
                "Z Axis/Z-2_Oracle/components/oracle_smart_floor_integrator.py",
                "OracleSmartFloorIntegrator",
            )

        integrator = integrator_cls(db=db, event_bus=event_bus, storage=storage, logger=logger)
        ORACLE_RUNTIME["integrator"] = integrator

        # Start watching ingestion queue (disabled for smoke/verify to avoid background threads and DB locks).
        if os.environ.get("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS") != "1":
            start = getattr(integrator, "start_watching", None)
            if callable(start):
                start()

        if logger:
            logger.info("[Oracle] Smart Floor Integrator ready")
    except Exception as e:
        ORACLE_RUNTIME["integrator_error"] = str(e)
        if logger:
            logger.warning(f"[Oracle] Smart integrator unavailable: {e}")


    # Subscribe to relevant events
    if event_bus:
        try:
            event_bus.subscribe("system.health.check", _on_health_check)
        except Exception as e:
            if logger:
                logger.warning(f"[Oracle] Event subscription failed: {e}")

    # Publish floor ready event
    if event_bus:
        try:
            event_bus.publish("oracle.floor.ready", {
                "floor": "Oracle",
                "z_level": -2,
                "capabilities": ['file_ingestion', 'archive_management', 'smart_integration', 'encyclopedia']
            })
        except Exception as e:
            if logger:
                logger.warning(f"[Oracle] Failed to publish ready event: {e}")

    if logger:
        logger.info("[Oracle] Floor initialized successfully")

    return True


def _on_health_check(event):
    """Respond to health check events"""
    event_bus = ORACLE_RUNTIME.get("event_bus")
    if event_bus:
        try:
            event_bus.publish("oracle.health.status", {
                "floor": "Oracle",
                "status": "operational",
                "z_level": -2
            })
        except Exception:
            pass

def main() -> int:
    root = tk.Tk()
    root.title("Oracle (Z-2) - Archive & Ingestion")
    root.geometry("1200x800")
    OracleUI(root).pack(fill="both", expand=True)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
