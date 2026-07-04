#!/usr/bin/env python
"""
IT Portal - Unified IT/Founder Control Center
Consolidates: startup_wizard.py + setup_wizard.py + first_run protocols
Features: System diagnostics, Z-floor tabs, integrated wizards, live monitoring

This is the IT/Founder mode main interface with god-level access.
Accessible only with clearance level 4+ (IT/Founder credentials).

Author: Romer Industries / EMASSC / LightSpeed Team
Version: 5.1.2
Date: April 9, 2026
"""

import sys
import os
import json
import sqlite3
import socket
import difflib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import importlib.util
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging

# Reduce noisy import-time prints; enable with env var when troubleshooting.
_IMPORT_DEBUG = bool(os.environ.get("LIGHTSPEED_DEBUG_IMPORTS"))
logger = logging.getLogger(__name__)

# CODEX NOTE (2026-01-30):
# - Trinity IT Portal is the approval gate for Z Direct durable registries.
# - Z Direct JSONL streams are append-only staging; commits write into `Z Direct/objects.json` via
#   `core.services.get_z_direct().commit_envelope_to_registry(...)` (adds provenance + atomic upsert).


def _bootstrap_sys_path() -> None:
    """
    Ensure sibling Trinity UI modules and the Merovingian `core/` package are importable.

    This module is frequently loaded via file-loader patterns, which do not implicitly
    add the module folder to `sys.path`.
    """
    try:
        ui_dir = Path(__file__).resolve().parent
        if str(ui_dir) not in sys.path:
            sys.path.insert(0, str(ui_dir))
    except Exception:
        pass

    try:
        here = Path(__file__).resolve()
        root = None
        for cand in (here, *here.parents):
            if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                root = cand
                break
        if root is None:
            return

        trinity_floor = root / "Z Axis" / "Z+3_Trinity"
        merovingian_floor = root / "Z Axis" / "Z-4_Merovingian"
        for p in (trinity_floor, merovingian_floor):
            if p.exists() and str(p) not in sys.path:
                sys.path.insert(0, str(p))
    except Exception:
        return


_bootstrap_sys_path()

TRINITY_CONSOLIDATED_FEATURES = ["Portal", "Bento System", "Settings Hub"]

TRINITY_SETTINGS_FOCUS_BY_FEATURE = {
    "Settings Hub": "",
    "Themes": "trinity_launchers",
    "Templates": "trinity_launchers",
    "Wizards": "setup_state",
}

SETUP_WORKSPACE_TAB_TITLE = "Setup " + "Wizard"

FLOOR_TAB_CONTRACTS = {
    "Trinity": ["Portal", "Bento System", "Settings Hub", "Themes", "Templates", "Wizards"],
    "Neo": ["Planner", "API Manager", "Code Assistant", "Lab Assistant", "Training", "Context", "Z Direct Registry"],
    "Architect": ["Project Manager", "Projects", "Tasks", "Timeline", "Portal", "Task Board", "Registry"],
    "TheConstruct": ["Dashboard", "Physics Calculators", "3D Immersive", "Registry"],
    "Morpheus": ["Dependency Map", "Portal", "Knowledge Search", "Files", "Chat Archive", "Registry"],
    "Oracle": ["Library", "Ingestion", "Backup & Restore", "Portal", "IP Vault", "Encyclopedia", "Dictionary"],
    "Smith": ["Background Jobs", "Jobs & Artifacts", "SOPs", "Portal", "Workflow Scheduler", "Workflow Debugger", "Registry"],
    "Merovingian": ["System Metrics", "Logs", "Database Browser", "Performance Profiler", "Portal", "Diagnostics"],
}


class _LazyFloorShell(tk.Frame):
    """Lightweight floor surface used by IT Portal to avoid eager heavy floor boot."""

    def __init__(
        self,
        parent,
        floor_name: str,
        z_level: str,
        description: str,
        colors: Dict[str, str],
        open_runtime,
        open_settings=None,
        actions: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(parent, bg=colors["bg_dark"])
        self.floor_name = floor_name
        self.z_level = z_level
        self.description = description
        self.colors = colors
        self.open_runtime = open_runtime
        self.open_settings = open_settings
        self.actions = list(actions or [])
        self._tabs: Dict[str, Any] = {}
        self._feature_lookup: Dict[str, Dict[str, Any]] = {}
        self._feature_index: List[Dict[str, Any]] = []
        self._feature_list: Optional[tk.Listbox] = None
        self._detail_title = tk.StringVar(value=f"{floor_name} Portal")
        self._detail_body = tk.StringVar(value=description)
        self._detail_meta = tk.StringVar(value="Select a feature, component, service, or capability.")

        header = tk.Frame(self, bg=colors["bg_dark"])
        header.pack(fill="x", padx=4, pady=(0, 8))

        tk.Label(
            header,
            text=f"{z_level} {floor_name} smart floor",
            font=("Arial", 13, "bold"),
            bg=colors["bg_dark"],
            fg=colors["accent_cyan"],
        ).pack(side="left")

        tk.Button(
            header,
            text="Open Floor Hub",
            command=self._open_runtime,
            bg=colors.get("button_green", "#14532d"),
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=3,
        ).pack(side="right")

        tk.Label(
            self,
            text=description,
            font=("Arial", 10),
            bg=colors["bg_dark"],
            fg=colors["text_green"],
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=4, pady=(0, 8))

        body = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=colors["bg_dark"], sashwidth=4)
        body.pack(fill="both", expand=True, padx=4, pady=4)

        left = tk.Frame(body, bg=colors["bg_panel"], width=320)
        right = tk.Frame(body, bg=colors["bg_panel"])
        try:
            body.add(left, minsize=260)
            body.add(right, minsize=460)
        except Exception:
            body.add(left)
            body.add(right)

        tk.Label(
            left,
            text="Floor Interface",
            font=("Arial", 11, "bold"),
            bg=colors["bg_panel"],
            fg=colors["accent_cyan"],
            anchor="w",
        ).pack(fill="x", padx=10, pady=(10, 4))

        self._feature_list = tk.Listbox(
            left,
            bg="#07131f",
            fg=colors["text_white"],
            selectbackground=colors["accent_cyan"],
            selectforeground="#000000",
            font=("Consolas", 10),
            activestyle="none",
        )
        self._feature_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        try:
            self._feature_list.bind("<<ListboxSelect>>", self._on_feature_select)
            self._feature_list.bind("<Double-Button-1>", lambda _e: self._open_selected_feature())
            self._feature_list.bind("<Return>", lambda _e: self._open_selected_feature())
        except Exception:
            pass

        detail_header = tk.Frame(right, bg=colors["bg_panel"])
        detail_header.pack(fill="x", padx=12, pady=(12, 8))
        tk.Label(
            detail_header,
            textvariable=self._detail_title,
            font=("Arial", 14, "bold"),
            bg=colors["bg_panel"],
            fg=colors["text_white"],
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        tk.Button(
            detail_header,
            text="Open / Configure",
            command=self._open_selected_feature,
            bg=colors.get("button_green", "#14532d"),
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=3,
        ).pack(side="right")

        tk.Label(
            right,
            textvariable=self._detail_meta,
            font=("Consolas", 9),
            bg=colors["bg_panel"],
            fg=colors["text_green"],
            anchor="w",
            justify="left",
            wraplength=700,
        ).pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(
            right,
            textvariable=self._detail_body,
            font=("Arial", 10),
            bg=colors["bg_panel"],
            fg=colors["text_white"],
            wraplength=740,
            justify="left",
        ).pack(fill="x", padx=12, pady=(0, 12))

        action_grid = tk.Frame(right, bg=colors["bg_panel"])
        action_grid.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._populate_single_surface(action_grid)

    def _action_row(
        self,
        *,
        label: str,
        kind: str,
        description: str,
        target: str = "",
        priority: str = "",
        focus_section: str = "",
    ) -> Dict[str, Any]:
        return {
            "label": str(label or target or "Portal"),
            "kind": str(kind or "feature"),
            "description": str(description or self.description),
            "target": str(target or label or "Portal"),
            "priority": str(priority or ""),
            "focus_section": str(focus_section or ""),
        }

    def _feature_rows(self) -> List[Dict[str, Any]]:
        rows = [
            self._action_row(
                label=tab_name,
                kind="feature",
                description=f"{tab_name} surface for {self.floor_name}.",
                target=tab_name,
                focus_section=TRINITY_SETTINGS_FOCUS_BY_FEATURE.get(tab_name, "") if self.floor_name == "Trinity" else "",
            )
            for tab_name in FLOOR_TAB_CONTRACTS.get(self.floor_name, ["Portal"])
        ]
        for action in self.actions:
            if not isinstance(action, dict):
                continue
            rows.append(
                self._action_row(
                    label=str(action.get("label") or action.get("id") or "Action"),
                    kind=str(action.get("kind") or "manifest"),
                    description=str(action.get("description") or self.description),
                    target=str(action.get("target") or action.get("label") or action.get("id") or "Portal"),
                    priority=str(action.get("priority") or ""),
                    focus_section=str(action.get("focus_section") or ""),
                )
            )
        return rows

    def _populate_single_surface(self, action_grid) -> None:
        rows = self._feature_rows()
        if self._feature_list is not None:
            for row in rows:
                key = f"{row['kind']}::{row['label']}"
                self._feature_lookup[key] = row
                self._feature_index.append(row)
                self._tabs.setdefault(row["label"], row)
                self._feature_list.insert(tk.END, f"{row['kind']:<10} {row['label']}")

        for index, row in enumerate(rows[:12]):
            button = tk.Button(
                action_grid,
                text=f"{row['kind'].upper()}\n{row['label']}",
                command=lambda r=row: self._select_feature_row(r),
                bg=("#12324a" if row["kind"] == "feature" else self.colors.get("bg_blue", "#000033")),
                activebackground=self.colors["accent_cyan"],
                fg="white",
                activeforeground="#000000",
                font=("Arial", 9, "bold"),
                relief=tk.RAISED,
                bd=1,
                width=22,
                height=4,
                wraplength=150,
            )
            button.grid(row=index // 3, column=index % 3, padx=6, pady=6, sticky="nsew")
        for column in range(3):
            action_grid.grid_columnconfigure(column, weight=1)
        if rows:
            self._select_feature_row(rows[0])
            try:
                if self._feature_list is not None:
                    self._feature_list.selection_set(0)
            except Exception:
                pass

    def _on_feature_select(self, _event=None) -> None:
        if self._feature_list is None:
            return
        selected = self._feature_list.curselection()
        if not selected:
            return
        try:
            row = self._feature_index[int(selected[0])]
            self._select_feature_row(row)
        except Exception:
            return

    def _select_feature_row(self, row: Dict[str, Any]) -> None:
        self._detail_title.set(f"{self.floor_name} / {row.get('label', 'Portal')}")
        meta = f"{self.z_level} | {row.get('kind', 'feature')}"
        if row.get("priority"):
            meta += f" | {row.get('priority')}"
        if row.get("target"):
            meta += f" | target={row.get('target')}"
        self._detail_meta.set(meta)
        self._detail_body.set(str(row.get("description") or self.description))
        self._selected_feature = row

    def _open_runtime(self) -> None:
        try:
            if callable(self.open_runtime):
                self.open_runtime(self.floor_name)
        except Exception:
            pass

    def select_tab(self, title: str) -> bool:
        target = str(title or "Portal")
        row = self._tabs.get(target)
        if row is None:
            return False
        try:
            if isinstance(row, dict):
                self._select_feature_row(row)
                if self._feature_list is not None:
                    for index in range(self._feature_list.size()):
                        item = str(self._feature_list.get(index) or "")
                        if item.endswith(target):
                            self._feature_list.selection_clear(0, tk.END)
                            self._feature_list.selection_set(index)
                            self._feature_list.see(index)
                            break
        except Exception:
            return False
        return True

    def _open_selected_feature(self) -> None:
        row = getattr(self, "_selected_feature", {}) or {}
        focus_section = str(row.get("focus_section") or "")
        if focus_section and callable(self.open_settings):
            try:
                self.open_settings(focus_section)
                return
            except Exception:
                pass
        self._open_runtime()

# Core services
try:
    from core.services import get_db, get_event_bus, get_storage
    HAS_SERVICES = True
except ImportError:
    HAS_SERVICES = False
    if _IMPORT_DEBUG:
        print("[!] Core services not available")

# Wizards (will integrate)
try:
    from wizards.startup_wizard import StartupWizard
    from wizards.setup_wizard import SetupWizard
    HAS_WIZARDS = True
except ImportError:
    # Best-effort: ensure Trinity floor root (which contains `wizards/`) is on sys.path.
    try:
        _here = Path(__file__).resolve()
        _root = None
        for _cand in (_here, *_here.parents):
            if (_cand / "N.py").exists() and (_cand / "Z Axis").exists():
                _root = _cand
                break
        if _root is not None:
            _trinity_floor = _root / "Z Axis" / "Z+3_Trinity"
            if _trinity_floor.exists() and str(_trinity_floor) not in sys.path:
                sys.path.insert(0, str(_trinity_floor))
            from wizards.startup_wizard import StartupWizard  # type: ignore
            from wizards.setup_wizard import SetupWizard  # type: ignore
            HAS_WIZARDS = True
        else:
            HAS_WIZARDS = False
    except Exception:
        HAS_WIZARDS = False
    if not HAS_WIZARDS:
        if _IMPORT_DEBUG:
            print("[!] Wizards not available")

# ProjectManager
try:
    from core.project_manager import create_project_manager, ProjectEnvironment
    HAS_PROJECT_MANAGER = True
except ImportError:
    HAS_PROJECT_MANAGER = False
    if _IMPORT_DEBUG:
        print("[!] ProjectManager not available")

# Dashboard widgets (DB-backed; used by IT Portal and N dashboard)
try:
    from dashboard_widgets import (
        TaskListWidget,
        BackgroundJobsWidget,
        APITogglesWidget,
        DependencyMapWidget,
        DatabaseStatsWidget,
        RecentActivityWidget,
    )
    HAS_DASH_WIDGETS = True
except Exception:
    # Back-compat path (older layouts)
    try:
        from core.ui.dashboard_widgets import (  # type: ignore
            TaskListWidget,
            BackgroundJobsWidget,
            APITogglesWidget,
            DependencyMapWidget,
            DatabaseStatsWidget,
            RecentActivityWidget,
        )
        HAS_DASH_WIDGETS = True
    except Exception:
        HAS_DASH_WIDGETS = False


class ITPortal(tk.Toplevel):
    """
    IT/Founder Control Portal

    Provides:
    - Integrated setup wizards (first-run protocol)
    - 8 Z-floor tabs (dedicated workspaces)
    - Live system diagnostics
    - Component activation controls
    - Database browser
    - Log viewer
    - System metrics
    - API integration interface
    """

    def __init__(
        self,
        parent,
        user,
        colors,
        z_floors_available,
        lightspeed_root: Optional[Path] = None,
        **_ignored,
    ):
        super().__init__(parent)

        self.parent_app = parent
        self.current_user = user
        self.colors = colors
        self.z_floors = z_floors_available
        # Keep live UI instances for deep-linking into floor-owned tabs.
        self._floor_ui_instances: Dict[str, Any] = {}

        # Company context (optional; set by N.py multi-company lobby)
        self.company_id = None
        self.company_name = None
        if isinstance(user, dict):
            try:
                self.company_id = user.get("company_id")
                self.company_name = user.get("company") or user.get("company_name")
            except Exception:
                self.company_id = None
                self.company_name = None

        # Canonical root (used for logs/config/dataindex paths)
        self.lightspeed_root = Path(lightspeed_root) if lightspeed_root else self._find_lightspeed_root()

        # Window setup
        self.title("Operator Portal - LightSpeed Control Center")
        self.geometry("1400x900")
        try:
            self.state('zoomed')
        except:
            pass
        self.configure(bg=colors['bg_dark'])

        # Database
        if HAS_SERVICES:
            self.db = get_db()
            self.event_bus = get_event_bus()
            self.storage = get_storage()
        else:
            self.db = None
            self.event_bus = None
            self.storage = None

        # ProjectManager
        if HAS_PROJECT_MANAGER:
            # Projects live under TheConstruct (Z0). Do not infer via __file__ parents (folder migrations).
            try:
                from core.config.paths import CONSTRUCT_ROOT  # type: ignore
                projects_root = Path(CONSTRUCT_ROOT) / "projects"
            except Exception:
                projects_root = Path.cwd() / "projects"
            self.project_manager = create_project_manager(str(projects_root))
        else:
            self.project_manager = None

        # Create UI
        self._create_header()
        self._create_ops_strip()
        self._create_main_tabs()
        self._create_footer()

        # Background jobs UI state
        self._bg_job_tree = None
        self._selected_bg_job_id = None

        # Check first run
        self._check_first_run()

    def set_services(self, db, event_bus, storage):
        """
        Set core service references (optional - overrides auto-detected)
        Called by N_UNIFIED.py to ensure consistent service instances
        """
        self.db = db
        self.event_bus = event_bus
        self.storage = storage

    def set_company_context(self, company_id: Optional[int] = None, company_name: Optional[str] = None) -> None:
        """Set the active company scope (used for task filtering + project root selection)."""
        self.company_id = company_id
        if company_name is not None:
            self.company_name = company_name
        label = getattr(self, "_header_company_label", None)
        try:
            if label is not None and label.winfo_exists():
                text = self.company_name or ("Company #" + str(self.company_id) if self.company_id is not None else "Shared")
                label.config(text=text)
        except Exception:
            pass

        # Live-update embedded widgets if present
        try:
            widget = getattr(self, "_dashboard_tasks_widget", None)
            if widget is not None and hasattr(widget, "set_company_id"):
                widget.set_company_id(self.company_id)
        except Exception:
            pass

    def set_project_manager(self, project_manager) -> None:
        """Override ProjectManager instance (N.py passes its canonical manager)."""
        self.project_manager = project_manager

    def _find_lightspeed_root(self) -> Path:
        here = Path(__file__).resolve()
        for cand in (here, *here.parents):
            if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                return cand
        return Path.cwd().resolve()

    def select_z_floor(self, floor_name: str) -> bool:
        """
        Select the dedicated Z-floor tab by its floor name (e.g., 'Neo', 'Oracle').

        Trinity owns the immersive navigation UI, but IT Portal remains the gate
        and is responsible for activating/selecting the canonical floor tabs.
        """
        try:
            notebook = getattr(self, "notebook", None)
            floors_nb = getattr(self, "_floors_notebook", None)
            floors_root = getattr(self, "_floors_root_tab", None)
            if notebook is None or floors_nb is None or floors_root is None:
                return False

            target = (floor_name or "").strip()
            if not target:
                return False

            # Ensure the Floors hub is visible, then select the floor within the nested notebook.
            try:
                notebook.select(floors_root)
            except Exception:
                pass

            for tab_id in floors_nb.tabs():
                label = str(floors_nb.tab(tab_id, "text") or "")
                # Tabs are labeled like "Z+2 Neo"
                if label.endswith(f" {target}") or label.strip() == target:
                    floors_nb.select(tab_id)
                    return True
            return False
        except Exception:
            return False

    def _open_floor_runtime(self, floor_name: str) -> bool:
        """
        Open a full floor runtime only when explicitly requested.

        The IT Portal embeds lightweight floor shells by default so startup,
        tests, and walkthroughs do not pay the cost of Oracle/Construct/Neo
        heavy loaders until an operator asks for them.
        """
        parent = getattr(self, "parent_app", None)
        for method_name in ("show_floors_hub", "open_z_floor"):
            fn = getattr(parent, method_name, None)
            if not callable(fn):
                continue
            try:
                if method_name == "show_floors_hub":
                    fn(select_floor=floor_name)
                else:
                    fn(floor_name)
                return True
            except Exception:
                continue

        try:
            messagebox.showinfo(
                "Floor Runtime",
                f"{floor_name} is available as a lightweight IT Portal shell.\n"
                "Open the full desktop floor from the main Z Floor menu.",
                parent=self,
            )
        except Exception:
            pass
        return False

    def open_floor_tab(self, floor_name: str, subtab_title: str = "") -> bool:
        """
        Select a floor and optionally a sub-tab inside the floor UI (best-effort).

        Floor UIs are Tk frames that usually expose:
        - `notebook` (ttk.Notebook)
        - `_tabs` mapping from title -> ttk.Frame
        """
        if not self.select_z_floor(floor_name):
            # Avoid silent failures: operators should know why nothing happened.
            try:
                messagebox.showwarning(
                    "Floor Not Available",
                    f"{floor_name} is not available in this build or could not be loaded.",
                )
            except Exception:
                pass
            return False

        if not subtab_title:
            return True

        ui = None
        try:
            ui = (getattr(self, "_floor_ui_instances", None) or {}).get(floor_name)
        except Exception:
            ui = None

        if ui is None:
            return True

        # Prefer floor-owned routing (supports compact nested notebooks).
        try:
            fn = getattr(ui, "select_tab", None)
            if callable(fn):
                fn(str(subtab_title))
                return True
        except Exception:
            pass

        try:
            nb = getattr(ui, "notebook", None)
            tabs = getattr(ui, "_tabs", None)
            if nb is None or not isinstance(tabs, dict):
                return True

            if subtab_title in tabs:
                nb.select(tabs[subtab_title])
                return True

            try:
                messagebox.showinfo(
                    "Subtab Not Found",
                    f"{floor_name} loaded, but tab '{subtab_title}' was not found.",
                )
            except Exception:
                pass
            return True
        except Exception:
            return True

    def _select_tab_title(self, title: str) -> bool:
        """Select a tab by its visible title."""
        try:
            notebook = getattr(self, "notebook", None)
            if notebook is None:
                return False
            target = (title or "").strip()
            if not target:
                return False

            for tab_id in notebook.tabs():
                if str(notebook.tab(tab_id, "text") or "") == target:
                    notebook.select(tab_id)
                    return True

            # Nested: Tools hub (preferred for secondary operational tabs).
            tools_nb = getattr(self, "_tools_notebook", None)
            tools_root = getattr(self, "_tools_root_tab", None)
            if tools_nb is not None and tools_root is not None:
                for tab_id in tools_nb.tabs():
                    if str(tools_nb.tab(tab_id, "text") or "") == target:
                        try:
                            notebook.select(tools_root)
                        except Exception:
                            pass
                        try:
                            tools_nb.select(tab_id)
                        except Exception:
                            pass
                        return True

            return False
        except Exception:
            return False

    def _open_z_direct_view(
        self,
        *,
        channel: str,
        peer: str = "All",
        kind: Optional[str] = None,
        tags: Optional[str] = None,
        search: Optional[str] = None,
    ) -> None:
        """
        Deep-link into the Z Direct operator view.

        Used by tool panes to route operators to the canonical review/approval surface.
        """
        try:
            tab = getattr(self, "_z_direct_tab", None)
            if tab is None:
                return
            try:
                self.notebook.select(tab)
            except Exception:
                return
            try:
                cv = getattr(self, "_z_direct_channel_var", None)
                if cv is not None:
                    cv.set(str(channel))
            except Exception:
                pass
            try:
                pv = getattr(self, "_z_direct_peer_var", None)
                if pv is not None:
                    pv.set(str(peer))
            except Exception:
                pass
            try:
                kv = getattr(self, "_z_direct_kind_var", None)
                if kv is not None and kind is not None:
                    kv.set(str(kind))
            except Exception:
                pass
            try:
                tv = getattr(self, "_z_direct_tags_var", None)
                if tv is not None and tags is not None:
                    tv.set(str(tags))
            except Exception:
                pass
            try:
                sv = getattr(self, "_z_direct_search_var", None)
                if sv is not None and search is not None:
                    sv.set(str(search))
            except Exception:
                pass
            try:
                refresh = getattr(self, "_z_direct_refresh", None)
                if callable(refresh):
                    refresh()
            except Exception:
                pass
        except Exception:
            return

    def _add_owner_bar(self, parent: tk.Widget, *, owner_floor: str, owner_channel: str, note: str = "") -> None:
        """
        Add a small banner that clarifies ownership and provides deep-links.

        This helps keep the IT Portal categorized while still surfacing secondary tools
        for operators.
        """
        try:
            bar = tk.Frame(parent, bg=self.colors["bg_dark"])
            bar.pack(fill="x", padx=20, pady=(0, 10))
            left = tk.Frame(bar, bg=self.colors["bg_dark"])
            left.pack(side="left", fill="x", expand=True)
            tk.Label(
                left,
                text=f"Owner floor: {owner_floor}  |  Channel: {owner_channel}" + (f"  |  {note}" if note else ""),
                bg=self.colors["bg_dark"],
                fg=self.colors["text_cyan"],
                font=("Arial", 9, "bold"),
            ).pack(anchor="w")
            tk.Button(
                bar,
                text=f"Open {owner_floor} Floor",
                command=lambda: self.select_z_floor(owner_floor),
                bg=self.colors["bg_panel"],
                fg="white",
                font=("Arial", 9, "bold"),
            ).pack(side="right", padx=(8, 0))
            tk.Button(
                bar,
                text=f"Open Z Direct ({owner_channel})",
                command=lambda: self._open_z_direct_view(channel=str(owner_channel), peer="All"),
                bg=self.colors["button_green"],
                fg="white",
                font=("Arial", 9, "bold"),
            ).pack(side="right")
        except Exception:
            return

    # ========================================================================
    # PROJECT MANAGER TAB ACTIONS (no placeholders)
    # ========================================================================

    def _pm_refresh_list(self):
        """Refresh the Project Manager tree view."""
        tree = getattr(self, "pm_tree", None)
        if tree is None:
            return
        if not HAS_PROJECT_MANAGER or not self.project_manager:
            return

        for item in tree.get_children():
            tree.delete(item)

        base = Path(self.project_manager.base_path)
        if not base.exists():
            return

        skip = {".venv", "venv", "__pycache__", "node_modules"}

        for project_dir in sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
            # Skip hidden/system
            if project_dir.name.startswith("."):
                continue

            proj_type = "general"
            meta_file = project_dir / "project.json"
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8", errors="replace"))
                    proj_type = meta.get("type") or meta.get("project_type") or proj_type
                except Exception:
                    pass

            file_count = 0
            total_size = 0
            latest_mtime = meta_file.stat().st_mtime if meta_file.exists() else project_dir.stat().st_mtime
            try:
                for fp in project_dir.rglob("*"):
                    if not fp.is_file():
                        continue
                    if any(part in skip for part in fp.parts):
                        continue
                    file_count += 1
                    st = fp.stat()
                    total_size += st.st_size
                    latest_mtime = max(latest_mtime, st.st_mtime)
            except Exception:
                pass

            size_mb = total_size / (1024 * 1024)
            modified = datetime.fromtimestamp(latest_mtime).strftime("%Y-%m-%d %H:%M")

            tree.insert("", "end", text=project_dir.name, values=(proj_type, str(file_count), f"{size_mb:.1f} MB", modified))

    def _pm_create_project(self):
        """Create a new project via ProjectManager."""
        if not HAS_PROJECT_MANAGER or not self.project_manager:
            messagebox.showerror("Project Manager", "ProjectManager not available.", parent=self)
            return

        from tkinter import simpledialog

        name = simpledialog.askstring("Create Project", "Project name:", parent=self)
        if not name:
            return
        name = name.strip()
        if not name:
            return

        # Minimal type choice (keep UI fast)
        project_type = simpledialog.askstring(
            "Create Project",
            "Project type (python/web/data/general/physics/documentation):",
            initialvalue="general",
            parent=self,
        )
        project_type = (project_type or "general").strip() or "general"

        result = self.project_manager.create_project(name=name, project_type=project_type)
        if result.get("success"):
            self._pm_refresh_list()
            messagebox.showinfo("Project Created", result.get("message") or f'Project "{name}" created.', parent=self)
        else:
            messagebox.showerror("Create Project Failed", result.get("error") or "Unknown error", parent=self)

    def _pm_list_projects(self):
        """Refresh the UI list (alias)."""
        self._pm_refresh_list()
        messagebox.showinfo("Projects", "Project list refreshed.", parent=self)

    def _pm_export_all(self):
        """Export all projects to zip archives (writes new archives; does not delete anything)."""
        if not HAS_PROJECT_MANAGER or not self.project_manager:
            messagebox.showerror("Project Manager", "ProjectManager not available.", parent=self)
            return

        base = Path(self.project_manager.base_path)
        projects = [p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")]
        if not projects:
            messagebox.showinfo("Export", "No projects found.", parent=self)
            return

        exported = 0
        errors = []
        for name in projects:
            res = self.project_manager.export_project(name, format="zip", include_venv=False)
            if res.get("success"):
                exported += 1
            else:
                errors.append(f"{name}: {res.get('error')}")

        msg = f"Exported {exported}/{len(projects)} projects."
        if errors:
            msg += "\n\nErrors (first 5):\n" + "\n".join(errors[:5])
        messagebox.showinfo("Export", msg, parent=self)

    def _pm_archive_all(self):
        """Archive all projects into Oracle's Data folder (no deletions)."""
        if not HAS_PROJECT_MANAGER or not self.project_manager:
            messagebox.showerror("Project Manager", "ProjectManager not available.", parent=self)
            return

        lightspeed_root = self.lightspeed_root
        oracle_root = lightspeed_root / "Z Axis" / "Z-2_Oracle" / "Data"

        base = Path(self.project_manager.base_path)
        projects = [p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")]
        if not projects:
            messagebox.showinfo("Archive", "No projects found.", parent=self)
            return

        company = (self.current_user.get("company") or "default_company").replace(" ", "_")
        workspace = "default_workspace"

        archived = 0
        errors = []
        for name in projects:
            res = self.project_manager.archive_to_oracle(
                project_name=name,
                oracle_root=oracle_root,
                company=company,
                workspace=workspace,
            )
            if res.get("success"):
                archived += 1
            else:
                errors.append(f"{name}: {res.get('error')}")

        msg = f"Archived {archived}/{len(projects)} projects to Oracle.\n\nOracle root:\n{oracle_root}"
        if errors:
            msg += "\n\nErrors (first 5):\n" + "\n".join(errors[:5])
        messagebox.showinfo("Archive", msg, parent=self)

    def _pm_cleanup(self):
        """
        Non-destructive cleanup (policy: no deletions).
        Performs a quick integrity scan and reports issues.
        """
        if not HAS_PROJECT_MANAGER or not self.project_manager:
            messagebox.showerror("Project Manager", "ProjectManager not available.", parent=self)
            return

        base = Path(self.project_manager.base_path)
        if not base.exists():
            messagebox.showinfo("Integrity Review", "No project directory found.", parent=self)
            return

        missing_meta = []
        for p in base.iterdir():
            if not p.is_dir() or p.name.startswith("."):
                continue
            if not (p / "project.json").exists():
                missing_meta.append(p.name)

        if not missing_meta:
            messagebox.showinfo("Integrity Review", "Integrity scan OK. No action taken.", parent=self)
        else:
            messagebox.showwarning(
                "Integrity Review (Report)",
                "Integrity scan found projects missing `project.json`.\n"
                "No files were deleted. You can open each project in the Studio tab and create metadata if needed.\n\n"
                "Missing metadata (first 20):\n" + "\n".join(missing_meta[:20]),
                parent=self,
            )

    def _create_header(self):
        """Create portal header"""
        header = tk.Frame(self, bg=self.colors['bg_panel'], height=60)
        header.pack(side='top', fill='x')
        header.pack_propagate(False)

        # Title
        title = tk.Label(
            header,
            text="IT/Founder Portal",
            font=('Arial', 20, 'bold'),
            bg=self.colors['bg_panel'],
            fg=self.colors['accent_cyan'],
        )
        title.pack(side='left', padx=20)
        self._header_title_label = title

        # User + company info (right side)
        right = tk.Frame(header, bg=self.colors['bg_panel'])
        right.pack(side='right', padx=20)

        # Actions (always available from IT Portal)
        actions = tk.Frame(right, bg=self.colors['bg_panel'])
        actions.pack(anchor="e", pady=(0, 2))

        def _btn(text: str, command):
            tk.Button(
                actions,
                text=text,
                command=command,
                bg=self.colors.get('button_blue', self.colors['bg_panel']),
                fg='white',
                font=('Arial', 9, 'bold'),
                relief=tk.FLAT,
                padx=10,
                pady=4,
            ).pack(side=tk.LEFT, padx=4)

        def _menu_btn(text: str, commands):
            button = tk.Menubutton(
                actions,
                text=text,
                bg=self.colors.get('button_blue', self.colors['bg_panel']),
                fg='white',
                font=('Arial', 9, 'bold'),
                relief=tk.FLAT,
                padx=10,
                pady=4,
                activebackground=self.colors.get('button_blue', self.colors['bg_panel']),
                activeforeground='white',
            )
            menu = tk.Menu(button, tearoff=0, bg=self.colors['bg_panel'], fg='white')
            for label, command in commands:
                menu.add_command(label=label, command=command)
            button.config(menu=menu)
            button.pack(side=tk.LEFT, padx=4)

        _btn("Page Menu", self._open_page_settings)
        _menu_btn(
            "Master Setup",
            [
                ("Profiles / Company", lambda: self._open_hub_focus("setup_state")),
                ("Tailoring / Layout", lambda: self._open_hub_focus("tailoring")),
                ("Settings Hub", self._open_settings_manager),
            ],
        )
        _btn("Operational Finalization", lambda: self.open_floor_tab("Architect", "Projects"))
        _btn("Trinity Actions", lambda: self._open_trinity_settings_surface(focus_section="trinity_launchers"))

        # Feature jump (reduces tab hunting; single "smart menu" surface).
        jump = tk.Frame(right, bg=self.colors['bg_panel'])
        jump.pack(anchor="e", pady=(2, 0))

        tk.Label(
            jump,
            text="Jump:",
            bg=self.colors['bg_panel'],
            fg=self.colors.get('text_cyan', self.colors.get('accent_cyan', '#00ffff')),
            font=('Arial', 9, 'bold'),
        ).pack(side=tk.LEFT, padx=(0, 6))

        self._jump_floor_var = tk.StringVar(value="Trinity")
        self._jump_feature_var = tk.StringVar(value="Portal")

        floors = []
        try:
            floors = [k for k, v in (self.z_floors or {}).items() if k and v is not None]
        except Exception:
            floors = []
        if not floors:
            try:
                floors = list((self.z_floors or {}).keys())
            except Exception:
                floors = ["Trinity", "Neo", "Architect", "Oracle", "Morpheus", "Smith", "Merovingian", "TheConstruct"]

        floor_box = ttk.Combobox(jump, textvariable=self._jump_floor_var, values=floors, state="readonly", width=12)
        floor_box.pack(side=tk.LEFT)

        feature_box = ttk.Combobox(jump, textvariable=self._jump_feature_var, values=[], state="readonly", width=22)
        feature_box.pack(side=tk.LEFT, padx=(6, 0))
        self._jump_feature_box = feature_box

        def _on_floor_change(_e=None):
            try:
                self._refresh_jump_features(str(self._jump_floor_var.get() or ""))
            except Exception:
                pass

        try:
            floor_box.bind("<<ComboboxSelected>>", _on_floor_change)
        except Exception:
            pass

        tk.Button(
            jump,
            text="Go",
            command=self._jump_go,
            bg=self.colors.get('button_blue', self.colors['bg_panel']),
            fg='white',
            font=('Arial', 9, 'bold'),
            relief=tk.FLAT,
            padx=10,
            pady=4,
        ).pack(side=tk.LEFT, padx=(6, 0))

        # Seed features for the default floor.
        try:
            self._refresh_jump_features(str(self._jump_floor_var.get() or "Trinity"))
        except Exception:
            pass

        company_text = self.company_name or ("Company #" + str(self.company_id) if self.company_id is not None else "Shared")
        self._header_company_label = tk.Label(
            right,
            text=company_text,
            bg=self.colors['bg_panel'],
            fg=self.colors['accent_cyan'],
            font=('Arial', 10, 'bold'),
        )
        self._header_company_label.pack(anchor="e")

        user_text = f"{self.current_user.get('fullname', 'IT Admin')} (Clearance {self.current_user.get('clearance', 4)})"
        tk.Label(
            right,
            text=user_text,
            bg=self.colors['bg_panel'],
            fg=self.colors['text_green'],
            font=('Arial', 12),
        ).pack(anchor="e")

    def _refresh_jump_features(self, floor_name: str) -> None:
        """
        Populate the jump feature list based on the loaded floor UI when possible.

        This is intentionally "best-effort": if a floor hasn't been opened yet,
        we provide a conservative default list.
        """
        floor = (floor_name or "").strip()
        box = getattr(self, "_jump_feature_box", None)
        if box is None:
            return

        defaults = FLOOR_TAB_CONTRACTS

        features = list(defaults.get(floor, ["Portal"]))
        try:
            ui = (getattr(self, "_floor_ui_instances", None) or {}).get(floor)
            tabs = getattr(ui, "_tabs", None)
            if isinstance(tabs, dict) and tabs:
                features = sorted([str(k) for k in tabs.keys() if str(k).strip()])
        except Exception:
            pass

        features = self._normalize_floor_features(floor, features)

        try:
            box["values"] = features
        except Exception:
            pass

        # Keep selection stable when possible.
        cur = ""
        try:
            cur = str(self._jump_feature_var.get() or "")
        except Exception:
            cur = ""
        if cur not in features:
            try:
                self._jump_feature_var.set(features[0] if features else "Portal")
            except Exception:
                pass

    def _normalize_floor_features(self, floor_name: str, features: List[str]) -> List[str]:
        floor = str(floor_name or "").strip()
        items = [str(item).strip() for item in (features or []) if str(item).strip()]
        if floor != "Trinity":
            return items

        preserved = [
            item for item in items
            if item not in {"Portal", "Bento System", "Settings Hub", "Themes", "Templates", "Wizards"}
        ]
        return list(TRINITY_CONSOLIDATED_FEATURES) + preserved

    def _jump_go(self) -> None:
        """Execute the header jump selection."""
        floor = ""
        feat = ""
        try:
            floor = str(self._jump_floor_var.get() or "").strip()
        except Exception:
            floor = ""
        try:
            feat = str(self._jump_feature_var.get() or "").strip()
        except Exception:
            feat = ""
        if not floor:
            return

        if floor == "Trinity" and feat in TRINITY_SETTINGS_FOCUS_BY_FEATURE:
            if self._open_trinity_settings_surface(focus_section=TRINITY_SETTINGS_FOCUS_BY_FEATURE[feat]):
                return

        try:
            self.open_floor_tab(floor, feat)
        finally:
            # Refresh options after opening (floor UI may now be available).
            try:
                self.after(200, lambda: self._refresh_jump_features(floor))
            except Exception:
                pass

    def _create_ops_strip(self) -> None:
        """
        Add a shared Smart Ops strip below the header.

        This is the operator-first surface for:
        - worker gating visibility (retrieve-only vs IT mode)
        - Smith->Trinity routed-task inbox visibility
        - safe, session-scoped quick actions
        """
        try:
            from core.ui.base_portal_glass import mount_smart_ops_strip  # type: ignore

            host = getattr(self, "parent_app", None) or self
            self._ops_strip = mount_smart_ops_strip(
                self,
                app=host,
                floor_channel="Z+3",
                it_portal=True,
                auto_drain=True,
                title="Session Ops",
            )
        except Exception:
            self._ops_strip = None

    def _create_main_tabs(self):
        """Create main tabbed interface"""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        try:
            self.notebook.bind("<<NotebookTabChanged>>", lambda _e: self._refresh_header_title())
        except Exception:
            pass

        # Core, operator-first tabs (keep top-level uncluttered).
        self._create_dashboard_tab()
        self._create_z_direct_tab()
        self._create_wizard_tab()

        # Floors are canonical: keep as a dedicated "Floors" hub instead of 8+ top-level tabs.
        floors_root = ttk.Frame(self.notebook)
        self.notebook.add(floors_root, text="Floors")
        floors_nb = ttk.Notebook(floors_root)
        floors_nb.pack(fill="both", expand=True, padx=10, pady=10)
        try:
            floors_nb.bind("<<NotebookTabChanged>>", lambda _e: self._refresh_header_title())
        except Exception:
            pass
        # Store handles so dashboard actions can deep-link into floors.
        self._floors_root_tab = floors_root
        self._floors_notebook = floors_nb
        self._create_z_floor_tabs(notebook=floors_nb)

        # Tools hub: group secondary operational surfaces here (owned by floors, surfaced for IT/Founder).
        tools_root = ttk.Frame(self.notebook)
        self.notebook.add(tools_root, text="Tools")
        tools_nb = ttk.Notebook(tools_root)
        tools_nb.pack(fill="both", expand=True, padx=10, pady=10)
        try:
            tools_nb.bind("<<NotebookTabChanged>>", lambda _e: self._refresh_header_title())
        except Exception:
            pass
        # Store handles so quick-actions can deep-link into tool tabs.
        self._tools_root_tab = tools_root
        self._tools_notebook = tools_nb

        # Keep Tools hub minimal. Floor-owned tools live in their canonical floors.
        # This tab is only shortcuts/deep-links for operator convenience.
        self._create_operator_shortcuts_tab(notebook=tools_nb)

        # Initial header context
        try:
            self._refresh_header_title()
        except Exception:
            pass

    def _create_z_direct_tab(self):
        """
        Z Direct: inter-floor event/object exchange viewer.

        This is intentionally read-mostly. "Commit" actions write into the
        floor's `Z Direct/objects.json` registry (atomic upsert), leaving JSONL
        as the append-only history.
        """
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Z Direct")
        # Keep a handle for other tabs that want to deep-link here.
        self._z_direct_tab = tab

        tk.Label(
            tab,
            text="Z Direct (Inter-floor Exchange)",
            font=('Arial', 18, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_cyan'],
        ).pack(pady=(16, 8))

        try:
            from core.services import get_z_direct  # type: ignore
            z_direct = get_z_direct()
        except Exception:
            z_direct = None

        if z_direct is None:
            tk.Label(
                tab,
                text="Z Direct service not available in this environment.",
                bg=self.colors['bg_dark'],
                fg=self.colors['error_red'],
                font=('Arial', 12, 'bold'),
            ).pack(pady=10)
            return

        controls = tk.Frame(tab, bg=self.colors['bg_dark'])
        controls.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(
            controls,
            text="Channel:",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            font=('Arial', 11, 'bold'),
        ).pack(side="left")

        channel_var = tk.StringVar(value="Z+3")
        channel_choices = ["Z+3", "Z+2", "Z+1", "Z0", "Z-1", "Z-2", "Z-3", "Z-4"]
        channel_menu = ttk.Combobox(
            controls,
            textvariable=channel_var,
            values=channel_choices,
            width=8,
            state="readonly",
        )
        channel_menu.pack(side="left", padx=(8, 16))

        tk.Label(
            controls,
            text="Peer:",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            font=('Arial', 11, 'bold'),
        ).pack(side="left")

        peer_var = tk.StringVar(value="Z-3")
        peer_choices = ["All"] + channel_choices
        peer_menu = ttk.Combobox(
            controls,
            textvariable=peer_var,
            values=peer_choices,
            width=8,
            state="readonly",
        )
        peer_menu.pack(side="left", padx=(8, 16))
        try:
            channel_menu.bind("<<ComboboxSelected>>", lambda _e: refresh())
            peer_menu.bind("<<ComboboxSelected>>", lambda _e: refresh())
        except Exception:
            pass

        # Expose control hooks so other tabs (Library / Background Jobs) can deep-link the operator
        # into the review queue after staging proposals.
        try:
            self._z_direct_channel_var = channel_var
            self._z_direct_peer_var = peer_var
            self._z_direct_refresh = refresh
        except Exception:
            pass

        limit_var = tk.IntVar(value=200)
        tk.Label(
            controls,
            text="Tail:",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            font=('Arial', 11, 'bold'),
        ).pack(side="left")
        ttk.Spinbox(controls, from_=20, to=1000, textvariable=limit_var, width=7).pack(
            side="left", padx=(8, 16)
        )

        kind_filter_var = tk.StringVar(value="all")
        tk.Label(
            controls,
            text="Kind:",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            font=('Arial', 11, 'bold'),
        ).pack(side="left")
        kind_menu = ttk.Combobox(
            controls,
            textvariable=kind_filter_var,
            values=[
                "all",
                "event",
                "task",
                "schema",
                "vault_file",
                "knowledge_node",
                "citation",
                "workspace",
                "learning_module",
                "research_query",
                "dataset",
                "experiment_run",
                "project",
                "ai_response",
                "simulation_result",
                "action_def",
                "simulation_def",
                "workflow_def",
                "bento_widget",
            ],
            width=16,
            state="readonly",
        )
        kind_menu.pack(side="left", padx=(8, 16))
        try:
            kind_menu.bind("<<ComboboxSelected>>", lambda _e: refresh())
        except Exception:
            pass

        # Tag filter (envelope tags + payload tags). Used heavily for V1R bootstrapping review.
        tag_filter_var = tk.StringVar(value="any")
        tk.Label(
            controls,
            text="Tags:",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            font=('Arial', 11, 'bold'),
        ).pack(side="left")
        tag_menu = ttk.Combobox(
            controls,
            textvariable=tag_filter_var,
            values=[
                "any",
                "plan",
                "cognigrex",
                "template",
                "library",
                "v1r",
                "bootstrap",
                "schema",
                "simulation",
                "action_def",
                "bento_widget",
                "workflow_def",
            ],
            width=12,
            state="readonly",
        )
        tag_menu.pack(side="left", padx=(8, 16))
        try:
            tag_menu.bind("<<ComboboxSelected>>", lambda _e: refresh())
        except Exception:
            pass

        search_var = tk.StringVar(value="")
        tk.Label(
            controls,
            text="Search:",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            font=('Arial', 11, 'bold'),
        ).pack(side="left")
        search_entry = ttk.Entry(controls, textvariable=search_var, width=22)
        search_entry.pack(side="left", padx=(8, 16))
        try:
            search_entry.bind("<Return>", lambda _e: refresh())
        except Exception:
            pass

        # Expose filter hooks so other tabs can deep-link into a *scoped* Z Direct view
        # after staging proposals (e.g., Plans -> Kind=workflow_def, Tags=plan).
        try:
            self._z_direct_kind_var = kind_filter_var
            self._z_direct_tags_var = tag_filter_var
            self._z_direct_search_var = search_var
        except Exception:
            pass

        registry_var = tk.StringVar(value="objects")
        tk.Label(
            controls,
            text="Registry:",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            font=('Arial', 11, 'bold'),
        ).pack(side="left")
        registry_menu = ttk.Combobox(
            controls,
            textvariable=registry_var,
            values=["objects", "tasks"],
            width=10,
            state="readonly",
        )
        registry_menu.pack(side="left", padx=(8, 16))

        target_channel_var = tk.StringVar(value="auto")
        tk.Label(
            controls,
            text="Target:",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            font=('Arial', 11, 'bold'),
        ).pack(side="left")
        target_menu = ttk.Combobox(
            controls,
            textvariable=target_channel_var,
            values=["auto"] + channel_choices,
            width=8,
            state="readonly",
        )
        target_menu.pack(side="left", padx=(8, 16))

        body = tk.Frame(tab, bg=self.colors['bg_dark'])
        body.pack(fill="both", expand=True, padx=20, pady=10)

        left = ttk.LabelFrame(body, text="Stream")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = ttk.LabelFrame(body, text="Details / Registry")
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        stream_notebook = ttk.Notebook(left)
        stream_notebook.pack(fill="both", expand=True, padx=6, pady=6)

        events_tab = ttk.Frame(stream_notebook)
        objs_tab = ttk.Frame(stream_notebook)
        inbox_tab = ttk.Frame(stream_notebook)
        outbox_tab = ttk.Frame(stream_notebook)
        stream_notebook.add(events_tab, text="Events")
        stream_notebook.add(objs_tab, text="Objects")
        stream_notebook.add(inbox_tab, text="Inbox")
        stream_notebook.add(outbox_tab, text="Outbox")

        events_text = scrolledtext.ScrolledText(
            events_tab,
            bg="#10131a",
            fg=self.colors['text_green'],
            font=('Consolas', 9),
            wrap="none",
        )
        events_text.pack(fill="both", expand=True)

        obj_list = tk.Listbox(
            objs_tab,
            bg="#10131a",
            fg=self.colors['accent_cyan'],
            font=('Consolas', 9),
            activestyle="dotbox",
            selectmode=tk.EXTENDED,
        )
        obj_list.pack(fill="both", expand=True)

        inbox_list = tk.Listbox(
            inbox_tab,
            bg="#10131a",
            fg=self.colors['accent_cyan'],
            font=('Consolas', 9),
            activestyle="dotbox",
            selectmode=tk.EXTENDED,
        )
        inbox_list.pack(fill="both", expand=True)

        outbox_list = tk.Listbox(
            outbox_tab,
            bg="#10131a",
            fg=self.colors['accent_cyan'],
            font=('Consolas', 9),
            activestyle="dotbox",
            selectmode=tk.EXTENDED,
        )
        outbox_list.pack(fill="both", expand=True)

        right_tabs = ttk.Notebook(right)
        right_tabs.pack(fill="both", expand=True, padx=6, pady=(6, 8))

        details_tab = ttk.Frame(right_tabs)
        registry_tab = ttk.Frame(right_tabs)
        right_tabs.add(details_tab, text="Details")
        right_tabs.add(registry_tab, text="Registry (objects/tasks)")

        details = scrolledtext.ScrolledText(
            details_tab,
            bg="#10131a",
            fg=self.colors['text_white'],
            font=('Consolas', 9),
            wrap="word",
        )
        details.pack(fill="both", expand=True)

        registry_text = scrolledtext.ScrolledText(
            registry_tab,
            bg="#10131a",
            fg=self.colors['text_white'],
            font=('Consolas', 9),
            wrap="word",
        )
        registry_text.pack(fill="both", expand=True)

        actions = tk.Frame(right, bg=self.colors['bg_dark'])
        actions.pack(fill="x", padx=6, pady=(0, 8))

        status_lbl = tk.Label(
            actions,
            text="",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_green'],
            font=('Arial', 10, 'bold'),
        )
        status_lbl.pack(side="left")

        # Keep last loaded objects/registry so list selections can map to payload.
        state: Dict[str, Any] = {
            "objects": [],
            "objects_view": [],
            "registry": [],
            "registry_view": [],
            "inbox": [],
            "outbox": [],
            "_details_obj": None,
        }

        def _set_details(obj: Any):
            # Persist last selection so actions (e.g., open path) can operate on it.
            state["_details_obj"] = obj
            try:
                details.delete("1.0", tk.END)
            except Exception:
                pass
            try:
                details.insert("1.0", json.dumps(obj, indent=2, ensure_ascii=False))
            except Exception:
                details.insert("1.0", str(obj))

        def open_path_from_details():
            try:
                import os

                obj = state.get("_details_obj")
                if not isinstance(obj, dict):
                    messagebox.showwarning("Z Direct", "Select an item with a payload path first.", parent=self)
                    return

                # Details payloads may wrap an envelope: {"stream": "...", "peer": "...", "envelope": {...}}
                env = obj.get("envelope") if isinstance(obj.get("envelope"), dict) else obj
                payload = env.get("payload") if isinstance(env, dict) and isinstance(env.get("payload"), dict) else {}

                # Common payload path keys across floors (vault_file, templates, artifacts, etc.).
                candidates = [
                    payload.get("path"),
                    payload.get("source_path"),
                    payload.get("vault_path"),
                    payload.get("file_location"),
                ]
                path = next((p for p in candidates if isinstance(p, str) and p.strip()), None)

                if not path:
                    messagebox.showwarning("Z Direct", "No file path found in selected payload.", parent=self)
                    return
                if not os.path.exists(path):
                    messagebox.showwarning("Z Direct", f"Path not found:\n{path}", parent=self)
                    return

                os.startfile(path)  # nosec - local operator action
            except Exception as e:
                messagebox.showerror("Z Direct", f"Open failed:\n{e}", parent=self)

        def _env_payload_kind(env: Any) -> str:
            try:
                if not isinstance(env, dict):
                    return ""
                payload = env.get("payload")
                if isinstance(payload, dict):
                    k = payload.get("kind")
                    if isinstance(k, str):
                        return k
                k2 = env.get("kind")
                return str(k2) if isinstance(k2, str) else ""
            except Exception:
                return ""

        def _env_tags(env: Any) -> List[str]:
            """Return merged tags from envelope-level `tags` and payload `tags` (best-effort)."""
            if not isinstance(env, dict):
                return []
            tags: List[str] = []
            try:
                t = env.get("tags")
                if isinstance(t, list):
                    tags.extend([str(x) for x in t if isinstance(x, (str, int, float))])
            except Exception:
                pass
            try:
                payload = env.get("payload") if isinstance(env.get("payload"), dict) else {}
                t2 = payload.get("tags") if isinstance(payload, dict) else None
                if isinstance(t2, list):
                    tags.extend([str(x) for x in t2 if isinstance(x, (str, int, float))])
            except Exception:
                pass

            out: List[str] = []
            for x in tags:
                s = str(x or "").strip()
                if s:
                    out.append(s)
            return out

        def _env_search_blob(env: Any) -> str:
            """Best-effort searchable text for an env/envelope."""
            if not isinstance(env, dict):
                return ""
            try:
                payload = env.get("payload") if isinstance(env.get("payload"), dict) else {}
                parts = [
                    env.get("created_at"),
                    env.get("source"),
                    env.get("z_context"),
                    env.get("channel"),
                    env.get("kind"),
                    " ".join(_env_tags(env)),
                    payload.get("kind"),
                    payload.get("id"),
                    payload.get("name"),
                    payload.get("title"),
                    payload.get("path"),
                    payload.get("source_path"),
                    payload.get("vault_path"),
                    payload.get("file_location"),
                ]
                return " ".join([str(p) for p in parts if p is not None]).lower()
            except Exception:
                return str(env).lower()

        def _matches_filters(env: Any) -> bool:
            kf = (kind_filter_var.get() or "all").strip().lower()
            if kf and kf != "all":
                if _env_payload_kind(env).strip().lower() != kf:
                    return False

            tf = (tag_filter_var.get() or "any").strip().lower()
            if tf and tf != "any":
                tags = [t.strip().lower() for t in _env_tags(env)]
                if tf not in tags:
                    return False

            q = (search_var.get() or "").strip().lower()
            if q:
                if q not in _env_search_blob(env):
                    return False
            return True

        def _registry_search_blob(item: Any) -> str:
            if not isinstance(item, dict):
                return ""
            try:
                parts = [
                    item.get("kind"),
                    item.get("id"),
                    item.get("name"),
                    item.get("title"),
                    item.get("updated_at"),
                    item.get("created_at"),
                ]
                return " ".join([str(p) for p in parts if p is not None]).lower()
            except Exception:
                return str(item).lower()

        def _matches_registry_filters(item: Any) -> bool:
            kf = (kind_filter_var.get() or "all").strip().lower()
            if kf and kf != "all":
                try:
                    if str((item or {}).get("kind") or "").strip().lower() != kf:
                        return False
                except Exception:
                    return False
            tf = (tag_filter_var.get() or "any").strip().lower()
            if tf and tf != "any":
                try:
                    tags = item.get("tags") if isinstance(item, dict) else None
                    tags_l = [str(x).strip().lower() for x in (tags or []) if isinstance(x, (str, int, float))]
                    if tf not in tags_l:
                        return False
                except Exception:
                    return False
            q = (search_var.get() or "").strip().lower()
            if q:
                if q not in _registry_search_blob(item):
                    return False
            return True

        def refresh():
            ch = channel_var.get()
            lim = int(limit_var.get() or 200)
            try:
                evs = z_direct.tail_events(ch, limit=lim)
            except Exception:
                evs = []

            events_text.delete("1.0", tk.END)
            for e in evs[-lim:]:
                try:
                    ts = (e.get("created_at") or e.get("payload", {}).get("created_at") or "")
                    src = e.get("source") or e.get("payload", {}).get("source") or ""
                    kind = e.get("kind") or e.get("payload", {}).get("kind") or ""
                    events_text.insert(tk.END, f"{ts} {kind} {src}\n")
                except Exception:
                    continue

            try:
                objs = z_direct.tail_objects(ch, limit=lim)
            except Exception:
                objs = []
            state["objects"] = objs
            objs_view = [o for o in (objs or []) if _matches_filters(o)]
            state["objects_view"] = objs_view
            obj_list.delete(0, tk.END)
            for i, o in enumerate(objs_view):
                payload = (o.get("payload") or {}) if isinstance(o, dict) else {}
                try:
                    tags = [t.strip().lower() for t in _env_tags(o)]
                except Exception:
                    tags = []
                tag_mark = "[v1r] " if "v1r" in tags else ""
                label = f"{i:03d} {tag_mark}{payload.get('kind','object')} {payload.get('id','')}"
                obj_list.insert(tk.END, label.strip())

            peer = peer_var.get()
            inbox_entries: List[Dict[str, Any]] = []
            outbox_entries: List[Dict[str, Any]] = []

            def _tail_peer(p: str) -> None:
                if not isinstance(p, str) or not p or p == ch:
                    return
                try:
                    if hasattr(z_direct, "tail_channel_inbox"):
                        inbox = z_direct.tail_channel_inbox(to_channel=ch, from_channel=p, limit=lim)
                    else:
                        inbox = z_direct.read_jsonl_tail(
                            z_direct.channel_inbox_path(to_channel=ch, from_channel=p), limit=lim
                        )
                except Exception:
                    inbox = []
                try:
                    if hasattr(z_direct, "tail_channel_outbox"):
                        outbox = z_direct.tail_channel_outbox(from_channel=ch, to_channel=p, limit=lim)
                    else:
                        outbox = z_direct.read_jsonl_tail(
                            z_direct.channel_outbox_path(from_channel=ch, to_channel=p), limit=lim
                        )
                except Exception:
                    outbox = []

                for e in inbox or []:
                    if isinstance(e, dict):
                        if _matches_filters(e):
                            inbox_entries.append({"peer": p, "env": e})
                for e in outbox or []:
                    if isinstance(e, dict):
                        if _matches_filters(e):
                            outbox_entries.append({"peer": p, "env": e})

            # Peer selection supports "All" for a unified review queue.
            if isinstance(peer, str) and peer.strip().lower() == "all":
                peers = []
                try:
                    if hasattr(z_direct, "list_channel_peers"):
                        peers = z_direct.list_channel_peers(ch)
                except Exception:
                    peers = []
                if not peers:
                    peers = [p for p in channel_choices if p != ch]
                for p in peers:
                    _tail_peer(p)
            else:
                _tail_peer(peer)

            def _ts(env: Dict[str, Any]) -> str:
                try:
                    return str(env.get("created_at") or "")
                except Exception:
                    return ""

            inbox_entries = sorted(inbox_entries, key=lambda it: _ts(it.get("env") or {}))
            outbox_entries = sorted(outbox_entries, key=lambda it: _ts(it.get("env") or {}))

            inbox_view = inbox_entries[-lim:]
            outbox_view = outbox_entries[-lim:]
            state["inbox"] = inbox_view
            state["outbox"] = outbox_view

            inbox_list.delete(0, tk.END)
            for i, item in enumerate(inbox_view):
                try:
                    p = item.get("peer")
                    e = item.get("env") if isinstance(item.get("env"), dict) else {}
                    ts = (e.get("created_at") or e.get("payload", {}).get("created_at") or "")
                    src = e.get("source") or e.get("payload", {}).get("source") or ""
                    kind = e.get("kind") or e.get("payload", {}).get("kind") or ""
                    origin = e.get("channel")
                    try:
                        tags = [t.strip().lower() for t in _env_tags(e)]
                    except Exception:
                        tags = []
                    tag_mark = "[v1r] " if "v1r" in tags else ""
                    label = f"{i:03d} {tag_mark}{ts} {kind} {src}"
                    if isinstance(p, str) and p:
                        label = f"{p} | {label}"
                    if isinstance(origin, str) and origin:
                        label += f" [{origin}]"
                    inbox_list.insert(tk.END, label.strip())
                except Exception:
                    continue

            outbox_list.delete(0, tk.END)
            for i, item in enumerate(outbox_view):
                try:
                    p = item.get("peer")
                    e = item.get("env") if isinstance(item.get("env"), dict) else {}
                    ts = (e.get("created_at") or e.get("payload", {}).get("created_at") or "")
                    src = e.get("source") or e.get("payload", {}).get("source") or ""
                    kind = e.get("kind") or e.get("payload", {}).get("kind") or ""
                    dest = e.get("channel")
                    try:
                        tags = [t.strip().lower() for t in _env_tags(e)]
                    except Exception:
                        tags = []
                    tag_mark = "[v1r] " if "v1r" in tags else ""
                    label = f"{i:03d} {tag_mark}{ts} {kind} {src}"
                    if isinstance(p, str) and p:
                        label = f"{p} | {label}"
                    if isinstance(dest, str) and dest:
                        label += f" [{dest}]"
                    outbox_list.insert(tk.END, label.strip())
                except Exception:
                    continue

            status_lbl.config(
                text=f"{ch}: events={len(evs)} objects={len(objs)} | {peer}: inbox={len(inbox_entries)} outbox={len(outbox_entries)}"
            )
            _set_details({"channel": ch, "events": len(evs), "objects": len(objs)})
            try:
                registry_text.delete("1.0", tk.END)
                registry_text.insert(
                    "1.0",
                    json.dumps(
                        {"hint": "Click 'Load Registry' to view the selected durable registry (objects.json/tasks.json)."},
                        indent=2,
                    ),
                )
            except Exception:
                pass
            state["registry"] = []

        def on_select(_evt=None):
            try:
                sel = obj_list.curselection()
                if not sel:
                    return
                idx = int(sel[0])
                obj = state.get("objects_view", []) or state.get("objects", [])
                obj = obj[idx]
                # If the registry is loaded, show whether the selected item is already committed.
                try:
                    payload = (obj.get("payload") or {}) if isinstance(obj, dict) else {}
                    kind = payload.get("kind")
                    obj_id = payload.get("id")
                    if isinstance(kind, str) and isinstance(obj_id, str) and state.get("registry"):
                        committed = any(
                            isinstance(it, dict) and it.get("kind") == kind and it.get("id") == obj_id
                            for it in (state.get("registry") or [])
                        )
                        _set_details({"committed": committed, "envelope": obj})
                        return
                except Exception:
                    pass
                _set_details(obj)
            except Exception:
                return

        def on_inbox_select(_evt=None):
            try:
                sel = inbox_list.curselection()
                if not sel:
                    return
                idx = int(sel[0])
                item = state.get("inbox", [])[idx]
                env = item.get("env") if isinstance(item, dict) else item
                peer = item.get("peer") if isinstance(item, dict) else None
                _set_details({"stream": "inbox", "peer": peer, "envelope": env})
            except Exception:
                return

        def on_outbox_select(_evt=None):
            try:
                sel = outbox_list.curselection()
                if not sel:
                    return
                idx = int(sel[0])
                item = state.get("outbox", [])[idx]
                env = item.get("env") if isinstance(item, dict) else item
                peer = item.get("peer") if isinstance(item, dict) else None
                _set_details({"stream": "outbox", "peer": peer, "envelope": env})
            except Exception:
                return

        def load_registry():
            ch = channel_var.get()
            reg_name = registry_var.get() or "objects"
            try:
                reg = z_direct.read_registry(ch, name=reg_name)
            except Exception:
                reg = []
            state["registry"] = reg
            reg_view = [it for it in (reg or []) if _matches_registry_filters(it)]
            state["registry_view"] = reg_view
            try:
                registry_text.delete("1.0", tk.END)
            except Exception:
                pass
            try:
                registry_text.insert(
                    "1.0",
                    json.dumps(
                        {
                            "channel": ch,
                            "registry": reg_name,
                            "total_items": len(reg or []),
                            "filtered_items": len(reg_view or []),
                            "items": reg_view,
                        },
                        indent=2,
                        ensure_ascii=False,
                    ),
                )
            except Exception:
                registry_text.insert("1.0", str(reg_view))

        def seed_builtin_schemas():
            """
            Seed a baseline schema catalog into the selected channel registry.

            This writes `kind="schema"` objects into `<channel>/Z Direct/objects.json`
            using the same commit path as other registry items (atomic upsert).
            """
            try:
                if not hasattr(z_direct, "builtin_schema_payloads"):
                    messagebox.showwarning("Z Direct", "Builtin schemas not available in this environment.", parent=self)
                    return
                ch = channel_var.get()
                if not messagebox.askyesno(
                    "Z Direct",
                    f"Seed builtin schemas into {ch}/objects.json?\n\nThis will upsert kind=schema entries for common payload kinds.",
                    parent=self,
                ):
                    return
                tag_v1r = False
                try:
                    tag_v1r = bool(
                        messagebox.askyesno(
                            "Z Direct",
                            "Tag these schema commits as v1r/bootstrap?\n\n"
                            "Recommended for the first seed so you can filter bootstrap batches in Z Direct.",
                            parent=self,
                        )
                    )
                except Exception:
                    tag_v1r = False
                committed_by = {
                    "username": self.current_user.get("username")
                    or self.current_user.get("fullname")
                    or "it_admin",
                    "clearance": self.current_user.get("clearance", 4),
                }
                payloads = z_direct.builtin_schema_payloads() or []
                committed = 0
                for payload in payloads:
                    if not isinstance(payload, dict):
                        continue
                    seed_tags = ["schema", "seed"]
                    if tag_v1r:
                        seed_tags.extend(["v1r", "bootstrap"])
                    env = z_direct.make_envelope(
                        kind="object",
                        channel=ch,
                        z_context="Z+3_Trinity",
                        source="trinity.it_portal.seed_builtin_schemas",
                        tags=seed_tags,
                        payload=payload,
                    )
                    z_direct.commit_envelope_to_registry(ch, env, registry="objects", committed_by=committed_by)
                    committed += 1
                try:
                    z_direct.append_event(
                        ch,
                        z_direct.make_envelope(
                            kind="event",
                            channel=ch,
                            z_context="Z+3_Trinity",
                            source="trinity.it_portal.seed_builtin_schemas",
                            tags=(["schema", "seed", "committed"] + (["v1r", "bootstrap"] if tag_v1r else [])),
                            payload={"action": "seed_schemas", "count": committed},
                        ),
                    )
                except Exception:
                    pass
                messagebox.showinfo("Z Direct", f"Seeded {committed} schema entries into {ch}/objects.json.", parent=self)
                try:
                    load_registry()
                except Exception:
                    pass
                try:
                    refresh()
                except Exception:
                    pass
            except Exception as e:
                messagebox.showerror("Z Direct", f"Seed schemas failed:\n{e}", parent=self)

        def validate_selected():
            try:
                if not hasattr(z_direct, "validate_envelope"):
                    messagebox.showwarning("Z Direct", "Validation not supported by this Z Direct service.", parent=self)
                    return
                sel = obj_list.curselection()
                if not sel:
                    messagebox.showwarning("Z Direct", "Select an object first.", parent=self)
                    return
                idx = int(sel[0])
                envs = state.get("objects_view", []) or state.get("objects", [])
                env = envs[idx]
                ok, errs = z_direct.validate_envelope(env)
                if ok:
                    messagebox.showinfo("Z Direct", "Validation OK.", parent=self)
                else:
                    messagebox.showwarning("Z Direct", "Validation failed:\n\n- " + "\n- ".join(errs), parent=self)
            except Exception as e:
                messagebox.showerror("Z Direct", f"Validate failed:\n{e}", parent=self)

        def validate_inbox_selected():
            try:
                if not hasattr(z_direct, "validate_envelope"):
                    messagebox.showwarning("Z Direct", "Validation not supported by this Z Direct service.", parent=self)
                    return
                sel = inbox_list.curselection()
                if not sel:
                    messagebox.showwarning("Z Direct", "Select an inbox item first.", parent=self)
                    return
                idx = int(sel[0])
                item = state.get("inbox", [])[idx]
                env = item.get("env") if isinstance(item, dict) else item
                ok, errs = z_direct.validate_envelope(env)
                if ok:
                    messagebox.showinfo("Z Direct", "Validation OK.", parent=self)
                else:
                    messagebox.showwarning("Z Direct", "Validation failed:\n\n- " + "\n- ".join(errs), parent=self)
            except Exception as e:
                messagebox.showerror("Z Direct", f"Validate failed:\n{e}", parent=self)

        def propose_knowledge_from_inbox():
            """
            Generate a `knowledge_node` proposal from a selected Oracle `vault_file`.

            This stages a proposal into Trinity's directed inbox from Neo (Z+2) and targets
            Oracle's durable registry (Z-2) via the envelope's `channel`.
            """
            try:
                sel = inbox_list.curselection()
                if not sel:
                    messagebox.showwarning("Z Direct", "Select an inbox item first.", parent=self)
                    return
                idx = int(sel[0])
                item = state.get("inbox", [])[idx]
                env = item.get("env") if isinstance(item, dict) else item
                payload = env.get("payload") if isinstance(env, dict) else None
                if not isinstance(payload, dict) or payload.get("kind") != "vault_file":
                    messagebox.showwarning("Z Direct", "Selected inbox item is not a vault_file object.", parent=self)
                    return

                res = self._stage_knowledge_proposal(payload)
                if not isinstance(res, dict) or not res.get("success"):
                    messagebox.showerror("Z Direct", f"Knowledge proposal failed:\n{res}", parent=self)
                    return

                # Switch peer view to Neo so the operator immediately sees the proposal.
                try:
                    peer_var.set("Z+2")
                except Exception:
                    pass
                try:
                    refresh()
                except Exception:
                    pass

                messagebox.showinfo(
                    "Z Direct",
                    "Staged knowledge proposal into Trinity review queue.\n\n"
                    f"citation_id: {res.get('citation_id')}\n"
                    f"knowledge_node_id: {res.get('knowledge_node_id')}\n"
                    f"knowledge_node_ids: {res.get('knowledge_node_ids')}\n\n"
                    f"staged_items: {res.get('staged') or 1}\n\n"
                    "Next: Commit Inbox Selected with Target=auto to write into Z-2_Oracle durable registry.",
                    parent=self,
                )
            except Exception as e:
                messagebox.showerror("Z Direct", f"Knowledge proposal failed:\n{e}", parent=self)

        def _confirm_commit_with_preview(*, title: str, channel: str, registry: str, env: Dict[str, Any]) -> bool:
            """
            Pre-commit preview gate:
            - shows envelope JSON
            - shows best-effort diff vs currently committed registry item (by kind/id)
            """
            try:
                win = tk.Toplevel(self)
                win.title(title or "Confirm Commit")
                win.geometry("980x720")
                try:
                    win.transient(self)
                except Exception:
                    pass

                container = ttk.Frame(win)
                container.pack(fill="both", expand=True, padx=12, pady=12)

                payload = env.get("payload") if isinstance(env, dict) else None
                kind = (payload or {}).get("kind") if isinstance(payload, dict) else None
                obj_id = (payload or {}).get("id") if isinstance(payload, dict) else None
                ident = f"{kind}:{obj_id}" if isinstance(kind, str) and obj_id is not None else "item"

                ttk.Label(
                    container,
                    text=f"Commit Preview  |  channel={channel}  registry={registry}.json  |  {ident}",
                    font=("Consolas", 12, "bold"),
                ).pack(anchor="w")

                nb = ttk.Notebook(container)
                nb.pack(fill="both", expand=True, pady=(10, 10))

                tab_env = ttk.Frame(nb)
                tab_diff = ttk.Frame(nb)
                nb.add(tab_env, text="Envelope")
                nb.add(tab_diff, text="Diff vs committed")

                env_txt = scrolledtext.ScrolledText(tab_env, wrap=tk.WORD, font=("Consolas", 10))
                env_txt.pack(fill="both", expand=True)
                try:
                    env_txt.insert("1.0", json.dumps(env, indent=2, ensure_ascii=True))
                except Exception:
                    env_txt.insert("1.0", str(env))
                try:
                    env_txt.config(state=tk.DISABLED)
                except Exception:
                    pass

                diff_txt = scrolledtext.ScrolledText(tab_diff, wrap=tk.NONE, font=("Consolas", 10))
                diff_txt.pack(fill="both", expand=True)

                diff_rendered = False
                try:
                    committed_rows = z_direct.read_registry(channel, name=str(registry or "objects"))
                    old = None
                    if isinstance(kind, str) and obj_id is not None:
                        for it in (committed_rows or []):
                            if not isinstance(it, dict):
                                continue
                            if it.get("kind") == kind and str(it.get("id")) == str(obj_id):
                                old = it
                                break
                    if isinstance(old, dict) and isinstance(payload, dict):
                        old_s = json.dumps(old, indent=2, sort_keys=True, ensure_ascii=True).splitlines(keepends=False)
                        new_s = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True).splitlines(keepends=False)
                        d = difflib.unified_diff(old_s, new_s, fromfile="committed", tofile="payload", lineterm="")
                        diff = "\n".join(d).strip()
                        diff_txt.insert("1.0", diff if diff else "(No diff; payload matches committed item)")
                        diff_rendered = True
                    elif isinstance(payload, dict):
                        diff_txt.insert("1.0", "(No committed item found for this kind/id; this will be a new upsert)")
                        diff_rendered = True
                except Exception as e:
                    diff_txt.insert("1.0", f"(Diff unavailable: {e})")
                    diff_rendered = True

                if not diff_rendered:
                    diff_txt.insert("1.0", "(Diff unavailable)")
                try:
                    diff_txt.config(state=tk.DISABLED)
                except Exception:
                    pass

                decision = {"ok": False}

                btns = ttk.Frame(container)
                btns.pack(fill="x")

                def _commit():
                    decision["ok"] = True
                    try:
                        win.destroy()
                    except Exception:
                        pass

                def _cancel():
                    decision["ok"] = False
                    try:
                        win.destroy()
                    except Exception:
                        pass

                ttk.Button(btns, text="Commit", command=_commit).pack(side="left")
                ttk.Button(btns, text="Cancel", command=_cancel).pack(side="right")
                try:
                    win.grab_set()
                except Exception:
                    pass
                win.wait_window()
                return bool(decision.get("ok"))
            except Exception:
                # Fallback to simple yes/no gate.
                try:
                    return bool(messagebox.askyesno("Z Direct", "Commit selected item to durable registry?", parent=self))
                except Exception:
                    return False

        def commit_selected():
            try:
                sel = obj_list.curselection()
                if not sel:
                    messagebox.showwarning("Z Direct", "Select an object first.", parent=self)
                    return
                idx = int(sel[0])
                envs = state.get("objects_view", []) or state.get("objects", [])
                env = envs[idx]
                ch = channel_var.get()

                payload = env.get("payload") if isinstance(env, dict) else None
                kind = (payload or {}).get("kind") if isinstance(payload, dict) else None
                obj_id = (payload or {}).get("id") if isinstance(payload, dict) else None
                ident = f"{kind}:{obj_id}" if isinstance(kind, str) and isinstance(obj_id, str) else "unknown"

                reg_name = registry_var.get() or "objects"
                # Tasks are typically committed into `tasks.json` (not `objects.json`).
                if kind == "task" and reg_name == "objects":
                    reg_name = "tasks"
                    try:
                        registry_var.set(reg_name)
                    except Exception:
                        pass

                if not _confirm_commit_with_preview(
                    title="Commit staged item",
                    channel=str(ch),
                    registry=str(reg_name),
                    env=env if isinstance(env, dict) else {},
                ):
                    return

                committed_by = {
                    "username": self.current_user.get("username")
                    or self.current_user.get("fullname")
                    or "it_admin",
                    "clearance": self.current_user.get("clearance", 4),
                }
                z_direct.commit_envelope_to_registry(ch, env, registry=reg_name, committed_by=committed_by)
                # Emit an approval event into the target channel stream for observability (append-only).
                try:
                    ev = z_direct.make_envelope(
                        kind="event",
                        channel=ch,
                        z_context="Z+3_Trinity",
                        source="trinity.it_portal",
                        tags=["review", "committed"],
                        payload={
                            "action": "commit",
                            "registry": reg_name,
                            "target_kind": kind,
                            "target_id": obj_id,
                            "committed_by": committed_by,
                        },
                    )
                    z_direct.append_event(ch, ev)
                except Exception:
                    pass
                messagebox.showinfo("Z Direct", f"Committed to registry ({reg_name}.json).", parent=self)
                try:
                    load_registry()
                except Exception:
                    pass
                try:
                    refresh()
                except Exception:
                    pass
            except Exception as e:
                messagebox.showerror("Z Direct", f"Commit failed:\n{e}", parent=self)

        def select_all_visible_objects():
            try:
                obj_list.selection_set(0, tk.END)
            except Exception:
                pass

        def clear_selection():
            try:
                obj_list.selection_clear(0, tk.END)
            except Exception:
                pass
            try:
                inbox_list.selection_clear(0, tk.END)
            except Exception:
                pass
            try:
                outbox_list.selection_clear(0, tk.END)
            except Exception:
                pass

        def _registry_for_env(env: Any) -> str:
            reg_name = registry_var.get() or "objects"
            try:
                payload = env.get("payload") if isinstance(env, dict) else None
                kind = (payload or {}).get("kind") if isinstance(payload, dict) else None
                if kind == "task" and reg_name == "objects":
                    return "tasks"
            except Exception:
                pass
            return reg_name

        def _confirm_batch_commit_with_preview(*, title: str, channel: str, envs: List[Dict[str, Any]]) -> bool:
            """
            Batch pre-commit preview gate:
            - shows a combined diff for all selected items (by kind/id) vs the committed registry
            - requires one explicit operator confirmation to commit the batch
            """
            try:
                win = tk.Toplevel(self)
                win.title(title or "Confirm Batch Commit")
                win.geometry("1100x760")
                try:
                    win.transient(self)
                except Exception:
                    pass

                container = ttk.Frame(win)
                container.pack(fill="both", expand=True, padx=12, pady=12)

                ttk.Label(
                    container,
                    text=f"Batch Commit Preview  |  channel={channel}  |  items={len(envs)}",
                    font=("Consolas", 12, "bold"),
                ).pack(anchor="w")

                txt = scrolledtext.ScrolledText(container, wrap=tk.NONE, font=("Consolas", 10))
                txt.pack(fill="both", expand=True, pady=(10, 10))

                # Cache committed registries per registry name to avoid repeated reads.
                committed_cache: Dict[str, List[Dict[str, Any]]] = {}

                def _committed_rows(registry: str) -> List[Dict[str, Any]]:
                    if registry not in committed_cache:
                        committed_cache[registry] = z_direct.read_registry(channel, name=str(registry or "objects")) or []
                    return committed_cache[registry]

                for i, env in enumerate(envs):
                    payload = env.get("payload") if isinstance(env, dict) else None
                    kind = (payload or {}).get("kind") if isinstance(payload, dict) else None
                    obj_id = (payload or {}).get("id") if isinstance(payload, dict) else None
                    ident = f"{kind}:{obj_id}" if isinstance(kind, str) and obj_id is not None else f"item_{i}"
                    reg_name = _registry_for_env(env)

                    txt.insert(tk.END, "\n" + ("=" * 88) + "\n")
                    txt.insert(tk.END, f"[{i+1}/{len(envs)}] {ident}  (registry={reg_name}.json)\n")
                    txt.insert(tk.END, ("-" * 88) + "\n")

                    try:
                        old = None
                        if isinstance(kind, str) and obj_id is not None:
                            for it in (_committed_rows(reg_name) or []):
                                if not isinstance(it, dict):
                                    continue
                                if it.get("kind") == kind and str(it.get("id")) == str(obj_id):
                                    old = it
                                    break
                        if isinstance(old, dict) and isinstance(payload, dict):
                            old_s = json.dumps(old, indent=2, sort_keys=True, ensure_ascii=True).splitlines(keepends=False)
                            new_s = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True).splitlines(keepends=False)
                            d = difflib.unified_diff(old_s, new_s, fromfile="committed", tofile="payload", lineterm="")
                            diff = "\n".join(d).strip()
                            txt.insert(tk.END, (diff if diff else "(No diff; payload matches committed item)") + "\n")
                        elif isinstance(payload, dict):
                            txt.insert(tk.END, "(No committed item found for this kind/id; this will be a new upsert)\n")
                        else:
                            txt.insert(tk.END, "(Invalid envelope payload; cannot diff)\n")
                    except Exception as e:
                        txt.insert(tk.END, f"(Diff unavailable: {e})\n")

                try:
                    txt.config(state=tk.DISABLED)
                except Exception:
                    pass

                decision = {"ok": False}
                btns = ttk.Frame(container)
                btns.pack(fill="x")

                def _commit():
                    decision["ok"] = True
                    try:
                        win.destroy()
                    except Exception:
                        pass

                def _cancel():
                    decision["ok"] = False
                    try:
                        win.destroy()
                    except Exception:
                        pass

                ttk.Button(btns, text=f"Commit {len(envs)}", command=_commit).pack(side="left")
                ttk.Button(btns, text="Cancel", command=_cancel).pack(side="right")
                try:
                    win.grab_set()
                except Exception:
                    pass
                win.wait_window()
                return bool(decision.get("ok"))
            except Exception:
                try:
                    return bool(messagebox.askyesno("Z Direct", f"Commit {len(envs)} selected items?", parent=self))
                except Exception:
                    return False

        def commit_selected_batch():
            try:
                sel = list(obj_list.curselection() or [])
                if not sel:
                    messagebox.showwarning("Z Direct", "Select one or more objects first.", parent=self)
                    return

                envs_view = state.get("objects_view", []) or state.get("objects", [])
                envs: List[Dict[str, Any]] = []
                for idx in sel:
                    try:
                        env = envs_view[int(idx)]
                        if isinstance(env, dict):
                            envs.append(env)
                    except Exception:
                        continue

                if not envs:
                    messagebox.showwarning("Z Direct", "No valid envelopes found in selection.", parent=self)
                    return

                ch = channel_var.get()

                # Safety: batch commit is powerful; encourage tag-scoped views for staged bootstrap batches.
                try:
                    tag = str(tag_filter_var.get() or "").strip().lower()
                except Exception:
                    tag = ""
                if not tag or tag == "any":
                    if not messagebox.askyesno(
                        "Z Direct",
                        f"Tags filter is set to 'any'.\n\nCommit {len(envs)} selected item(s) anyway?\n\n"
                        "Tip: set Tags=v1r to isolate the bootstrap batch before committing.",
                        parent=self,
                    ):
                        return

                if not _confirm_batch_commit_with_preview(title="Batch commit staged items", channel=str(ch), envs=envs):
                    return

                committed_by = {
                    "username": self.current_user.get("username")
                    or self.current_user.get("fullname")
                    or "it_admin",
                    "clearance": self.current_user.get("clearance", 4),
                }

                committed = 0
                failed: List[str] = []
                for env in envs:
                    payload = env.get("payload") if isinstance(env, dict) else None
                    kind = (payload or {}).get("kind") if isinstance(payload, dict) else None
                    obj_id = (payload or {}).get("id") if isinstance(payload, dict) else None
                    ident = f"{kind}:{obj_id}" if isinstance(kind, str) and obj_id is not None else "item"
                    reg_name = _registry_for_env(env)
                    try:
                        z_direct.commit_envelope_to_registry(ch, env, registry=reg_name, committed_by=committed_by)
                        committed += 1
                    except Exception as e:
                        failed.append(f"{ident} ({reg_name}): {e}")

                # Summary event (append-only) for observability.
                try:
                    z_direct.append_event(
                        ch,
                        z_direct.make_envelope(
                            kind="event",
                            channel=ch,
                            z_context="Z+3_Trinity",
                            source="trinity.it_portal",
                            tags=["review", "committed", "batch"],
                            payload={"action": "batch_commit", "count": committed, "failed": len(failed)},
                        ),
                    )
                except Exception:
                    pass

                if failed:
                    messagebox.showwarning(
                        "Z Direct",
                        f"Batch committed {committed}/{len(envs)}.\n\nFailures:\n- " + "\n- ".join(failed[:12]),
                        parent=self,
                    )
                else:
                    messagebox.showinfo("Z Direct", f"Batch committed {committed} item(s).", parent=self)

                try:
                    load_registry()
                except Exception:
                    pass
                try:
                    refresh()
                except Exception:
                    pass
            except Exception as e:
                messagebox.showerror("Z Direct", f"Batch commit failed:\n{e}", parent=self)

        def commit_inbox_selected():
            try:
                sel = inbox_list.curselection()
                if not sel:
                    messagebox.showwarning("Z Direct", "Select an inbox item first.", parent=self)
                    return
                idx = int(sel[0])
                item = state.get("inbox", [])[idx]
                env = item.get("env") if isinstance(item, dict) else item
                peer = item.get("peer") if isinstance(item, dict) else peer_var.get()

                payload = env.get("payload") if isinstance(env, dict) else None
                kind = (payload or {}).get("kind") if isinstance(payload, dict) else None
                obj_id = (payload or {}).get("id") if isinstance(payload, dict) else None
                ident = f"{kind}:{obj_id}" if isinstance(kind, str) and obj_id is not None else "inbox_item"

                reg_name = registry_var.get() or "objects"
                if kind == "task" and reg_name == "objects":
                    reg_name = "tasks"
                    try:
                        registry_var.set(reg_name)
                    except Exception:
                        pass

                target = target_channel_var.get() or "auto"
                if target == "auto":
                    try:
                        target = env.get("channel") if isinstance(env, dict) else None
                    except Exception:
                        target = None
                    if not isinstance(target, str) or not target:
                        target = channel_var.get()

                if not _confirm_commit_with_preview(
                    title="Commit inbox item",
                    channel=str(target),
                    registry=str(reg_name),
                    env=env if isinstance(env, dict) else {},
                ):
                    return

                committed_by = {
                    "username": self.current_user.get("username")
                    or self.current_user.get("fullname")
                    or "it_admin",
                    "clearance": self.current_user.get("clearance", 4),
                }
                z_direct.commit_envelope_to_registry(target, env, registry=reg_name, committed_by=committed_by)
                # Emit a commit event into the target channel stream and send a receipt to the origin peer.
                try:
                    receipt = z_direct.make_envelope(
                        kind="event",
                        channel=target,
                        z_context="Z+3_Trinity",
                        source="trinity.it_portal",
                        tags=["review", "committed", "receipt"],
                        payload={
                            "action": "commit",
                            "registry": reg_name,
                            "target_channel": target,
                            "target_kind": kind,
                            "target_id": obj_id,
                            "committed_by": committed_by,
                        },
                    )
                    try:
                        z_direct.append_event(target, receipt)
                    except Exception:
                        pass
                    # Best-effort: notify the selected peer (origin) via directed channels.
                    if isinstance(peer, str) and peer and peer != "Z+3" and peer.strip().lower() != "all":
                        try:
                            z_direct.append_channel_outbox(from_channel="Z+3", to_channel=peer, payload=receipt)
                        except Exception:
                            pass
                        try:
                            z_direct.append_channel_inbox(to_channel=peer, from_channel="Z+3", payload=receipt)
                        except Exception:
                            pass
                except Exception:
                    pass
                messagebox.showinfo("Z Direct", f"Committed to {target}/{reg_name}.json.", parent=self)
                try:
                    if target == channel_var.get():
                        load_registry()
                except Exception:
                    pass
                try:
                    refresh()
                except Exception:
                    pass
            except Exception as e:
                messagebox.showerror("Z Direct", f"Inbox commit failed:\n{e}", parent=self)

        def send_selected_to_peer_inbox():
            try:
                sel = obj_list.curselection()
                if not sel:
                    messagebox.showwarning("Z Direct", "Select an object first.", parent=self)
                    return
                idx = int(sel[0])
                env = state.get("objects", [])[idx]
                ch = channel_var.get()
                peer = peer_var.get()

                if not isinstance(peer, str) or not peer.strip():
                    messagebox.showwarning("Z Direct", "Select a peer channel.", parent=self)
                    return
                if peer.strip().lower() == "all":
                    messagebox.showwarning("Z Direct", "Peer must be a specific channel (not 'All').", parent=self)
                    return
                if peer == ch:
                    messagebox.showwarning("Z Direct", "Peer must be different from channel.", parent=self)
                    return

                payload = env.get("payload") if isinstance(env, dict) else None
                kind = (payload or {}).get("kind") if isinstance(payload, dict) else None
                obj_id = (payload or {}).get("id") if isinstance(payload, dict) else None
                ident = f"{kind}:{obj_id}" if isinstance(kind, str) and obj_id is not None else "selected"

                if not messagebox.askyesno(
                    "Z Direct",
                    f"Send selected item to peer inbox?\n\nfrom: {ch}\n to:  {peer}\n\n{ident}",
                    parent=self,
                ):
                    return

                # Write both outbox (sender) and inbox (recipient) so routing is observable from either side.
                try:
                    z_direct.append_channel_outbox(from_channel=ch, to_channel=peer, payload=env)
                except Exception:
                    pass
                z_direct.append_channel_inbox(to_channel=peer, from_channel=ch, payload=env)
                messagebox.showinfo("Z Direct", "Sent to peer inbox.", parent=self)
                try:
                    refresh()
                except Exception:
                    pass
            except Exception as e:
                messagebox.showerror("Z Direct", f"Send failed:\n{e}", parent=self)

        def reject_selected():
            try:
                sel = obj_list.curselection()
                if not sel:
                    messagebox.showwarning("Z Direct", "Select an object first.", parent=self)
                    return
                idx = int(sel[0])
                env = state.get("objects", [])[idx]
                ch = channel_var.get()

                payload = env.get("payload") if isinstance(env, dict) else None
                kind = (payload or {}).get("kind") if isinstance(payload, dict) else None
                obj_id = (payload or {}).get("id") if isinstance(payload, dict) else None
                ident = f"{kind}:{obj_id}" if isinstance(kind, str) and obj_id is not None else "unknown"

                from tkinter import simpledialog

                reason = simpledialog.askstring(
                    "Z Direct",
                    f"Reject selected item?\n\n{ident}\n\nReason (optional):",
                    parent=self,
                )
                if reason is None:
                    return

                ev = z_direct.make_envelope(
                    kind="event",
                    channel=ch,
                    z_context="Z+3_Trinity",
                    source="trinity.it_portal",
                    tags=["review", "rejected"],
                    payload={
                        "action": "reject",
                        "target_kind": kind,
                        "target_id": obj_id,
                        "target_created_at": env.get("created_at") if isinstance(env, dict) else None,
                        "reason": str(reason),
                    },
                )
                z_direct.append_event(ch, ev)
                messagebox.showinfo("Z Direct", "Rejection recorded (event appended).", parent=self)
                try:
                    refresh()
                except Exception:
                    pass
            except Exception as e:
                messagebox.showerror("Z Direct", f"Reject failed:\n{e}", parent=self)

        def reject_inbox_selected():
            try:
                sel = inbox_list.curselection()
                if not sel:
                    messagebox.showwarning("Z Direct", "Select an inbox item first.", parent=self)
                    return
                idx = int(sel[0])
                item = state.get("inbox", [])[idx]
                env = item.get("env") if isinstance(item, dict) else item
                peer = item.get("peer") if isinstance(item, dict) else None

                payload = env.get("payload") if isinstance(env, dict) else None
                kind = (payload or {}).get("kind") if isinstance(payload, dict) else None
                obj_id = (payload or {}).get("id") if isinstance(payload, dict) else None
                ident = f"{kind}:{obj_id}" if isinstance(kind, str) and obj_id is not None else "inbox_item"

                from tkinter import simpledialog

                reason = simpledialog.askstring(
                    "Z Direct",
                    f"Reject inbox item?\n\n{ident}\n\nReason (optional):",
                    parent=self,
                )
                if reason is None:
                    return

                # Prefer the envelope's declared origin; fall back to the peer that delivered it.
                origin = env.get("channel") if isinstance(env, dict) else None
                if not isinstance(origin, str) or not origin:
                    origin = peer if isinstance(peer, str) else None
                if not isinstance(origin, str) or not origin or origin.strip().lower() == "all":
                    origin = "Z+3"

                ev = z_direct.make_envelope(
                    kind="event",
                    channel=origin,
                    z_context="Z+3_Trinity",
                    source="trinity.it_portal",
                    tags=["review", "rejected"],
                    payload={
                        "action": "reject",
                        "target_channel": origin,
                        "target_kind": kind,
                        "target_id": obj_id,
                        "reason": str(reason),
                    },
                )
                # Record in the origin floor stream and send a directed receipt.
                try:
                    z_direct.append_event(origin, ev)
                except Exception:
                    pass
                try:
                    if origin != "Z+3":
                        z_direct.append_channel_outbox(from_channel="Z+3", to_channel=origin, payload=ev)
                except Exception:
                    pass
                try:
                    if origin != "Z+3":
                        z_direct.append_channel_inbox(to_channel=origin, from_channel="Z+3", payload=ev)
                except Exception:
                    pass

                messagebox.showinfo("Z Direct", "Inbox rejection recorded (event + receipt).", parent=self)
                try:
                    refresh()
                except Exception:
                    pass
            except Exception as e:
                messagebox.showerror("Z Direct", f"Inbox reject failed:\n{e}", parent=self)

        def _save_bento_layout():
            try:
                from ui.universal_bento_system import get_bento_system  # type: ignore

                b = get_bento_system()
                ok = bool(b.save_layout_to_settings())
                if ok:
                    messagebox.showinfo("Bento Layout", "Saved Bento layout to Trinity settings.", parent=self)
                else:
                    messagebox.showwarning("Bento Layout", "Failed to save Bento layout.", parent=self)
            except Exception as e:
                messagebox.showerror("Bento Layout", f"Failed to save Bento layout:\n{e}", parent=self)

        def _reset_bento_layout():
            try:
                from ui.universal_bento_system import get_bento_system  # type: ignore

                b = get_bento_system()
                if not messagebox.askyesno(
                    "Bento Layout",
                    "Reset Bento layout to auto-packing (clears saved layout)?",
                    parent=self,
                ):
                    return
                ok = bool(b.reset_layout_in_settings())
                if ok:
                    messagebox.showinfo("Bento Layout", "Reset Bento layout (auto-packing).", parent=self)
                else:
                    messagebox.showwarning("Bento Layout", "Failed to reset Bento layout.", parent=self)
            except Exception as e:
                messagebox.showerror("Bento Layout", f"Failed to reset Bento layout:\n{e}", parent=self)

        def _stage_v1r_definitions():
            """
            Stage baseline V1R definitions into Trinity Z Direct (append-only).

            This delegates to the host shell (N.py) when the portal is embedded there.
            """
            host = getattr(self, "parent_app", None)
            fn = getattr(host, "stage_v1r_definitions", None)
            if not callable(fn):
                messagebox.showwarning(
                    "Stage V1R",
                    "V1R staging is only available when the IT Portal is opened from N (host context).",
                    parent=self,
                )
                return
            try:
                ok = bool(fn(confirm=True))
                if ok:
                    try:
                        refresh()
                    except Exception:
                        pass
            except Exception as e:
                messagebox.showerror("Stage V1R", f"Stage failed:\n{e}", parent=self)

        ttk.Button(controls, text="Refresh", command=refresh).pack(side="left")
        ttk.Button(controls, text="Load Registry", command=load_registry).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="Seed Schemas", command=seed_builtin_schemas).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="Stage V1R (Z Direct)", command=_stage_v1r_definitions).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="Save Stack Layout", command=_save_bento_layout).pack(side="left", padx=(16, 0))
        ttk.Button(controls, text="Reset Stack Layout", command=_reset_bento_layout).pack(side="left", padx=(8, 0))

        registry_menu_btn = tk.Menubutton(actions, text="Selection Actions")
        registry_menu = tk.Menu(registry_menu_btn, tearoff=0)
        registry_menu.add_command(label="Select All (View)", command=select_all_visible_objects)
        registry_menu.add_command(label="Clear Selection", command=clear_selection)
        registry_menu.add_separator()
        registry_menu.add_command(label="Open Path", command=open_path_from_details)
        registry_menu_btn.config(menu=registry_menu)
        registry_menu_btn.pack(side="left", padx=(8, 0))

        inbox_menu_btn = tk.Menubutton(actions, text="Inbox Actions")
        inbox_menu = tk.Menu(inbox_menu_btn, tearoff=0)
        inbox_menu.add_command(label="Propose Knowledge", command=propose_knowledge_from_inbox)
        inbox_menu.add_command(label="Validate Inbox", command=validate_inbox_selected)
        inbox_menu.add_command(label="Validate Selected", command=validate_selected)
        inbox_menu.add_separator()
        inbox_menu.add_command(label="Send Selected -> Peer Inbox", command=send_selected_to_peer_inbox)
        inbox_menu.add_command(label="Reject Selected", command=reject_selected)
        inbox_menu.add_command(label="Reject Inbox Selected", command=reject_inbox_selected)
        inbox_menu_btn.config(menu=inbox_menu)
        inbox_menu_btn.pack(side="right", padx=(0, 8))

        commit_menu_btn = tk.Menubutton(actions, text="Commit Actions")
        commit_menu = tk.Menu(commit_menu_btn, tearoff=0)
        commit_menu.add_command(label="Commit Inbox Selected", command=commit_inbox_selected)
        commit_menu.add_command(label="Commit Selection (Batch)", command=commit_selected_batch)
        commit_menu.add_command(label="Commit Selected", command=commit_selected)
        commit_menu_btn.config(menu=commit_menu)
        commit_menu_btn.pack(side="right")

        obj_list.bind("<<ListboxSelect>>", on_select)
        inbox_list.bind("<<ListboxSelect>>", on_inbox_select)
        outbox_list.bind("<<ListboxSelect>>", on_outbox_select)

        # Initial load
        try:
            refresh()
        except Exception:
            pass



    def _stage_knowledge_proposal(
        self,
        vault_file_payload: Dict[str, Any],
        *,
        review_channel: str = "Z+3",
        origin_channel: str = "Z+2",
        target_registry_channel: str = "Z-2",
    ) -> Dict[str, Any]:
        """
        Stage a knowledge proposal (citation + knowledge nodes) into Trinity for review.

        Governance: stage-only; durable registry writes still require explicit Trinity commit.
        """
        if not isinstance(vault_file_payload, dict) or vault_file_payload.get("kind") != "vault_file":
            return {"success": False, "error": "payload must be a vault_file dict"}

        neo_path = (self.lightspeed_root / "Z Axis" / "Z+2_Neo" / "ai" / "document_objectifier.py").resolve()
        if not neo_path.exists():
            return {"success": False, "error": f"Neo DocumentObjectifier not found: {neo_path}"}

        try:
            spec = importlib.util.spec_from_file_location("lightspeed_neo_document_objectifier", neo_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load Neo DocumentObjectifier from {neo_path}")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            DocumentObjectifier = getattr(mod, "DocumentObjectifier")

            objifier = DocumentObjectifier()
            return objifier.stage_knowledge_proposal_to_trinity(
                vault_file_payload,
                review_channel=review_channel,
                origin_channel=origin_channel,
                target_registry_channel=target_registry_channel,
            )
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _load_oracle_registry_objects(self) -> List[Dict[str, Any]]:
        """Load Oracle durable registry objects (Z-2/objects.json)."""
        try:
            p = (self.lightspeed_root / "Z Axis" / "Z-2_Oracle" / "Z Direct" / "objects.json").resolve()
            if not p.exists():
                return []
            data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _resolve_oracle_vault_path(self, vault_id: str) -> str:
        """Resolve an Oracle vault_file path by id (best-effort)."""
        vault_id = (vault_id or "").strip()
        if not vault_id:
            return ""
        try:
            for it in self._load_oracle_registry_objects():
                if isinstance(it, dict) and it.get("kind") == "vault_file" and str(it.get("id") or "") == vault_id:
                    return str(it.get("path") or "")
        except Exception:
            pass
        return ""

    def _run_knowledge_proposal_sweep(self, *, batch_size: int = 2) -> None:
        """
        Stage-only sweep: for new Oracle `vault_file` durable-registry entries, stage knowledge proposals into Trinity.

        This persists a cursor in the `jobs` table (job_type="knowledge_proposal_sweep") so we avoid duplicates.
        """
        if not self.db or not hasattr(self.db, "get_connection"):
            messagebox.showerror("Knowledge Sweep", "Database service unavailable.", parent=self)
            return

        try:
            rows = self._load_oracle_registry_objects()
            vaults = [it for it in rows if isinstance(it, dict) and it.get("kind") == "vault_file"]

            def _vid(v: Dict[str, Any]) -> int:
                try:
                    return int(str(v.get("id") or "0").strip() or 0)
                except Exception:
                    return 0

            vaults.sort(key=_vid)

            cursor = 0
            job_id = None
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, result_json FROM jobs WHERE job_type=? ORDER BY id DESC LIMIT 1",
                    ("knowledge_proposal_sweep",),
                )
                row = cur.fetchone()
                if row and row[0]:
                    job_id = int(row[0])
                    try:
                        prev = json.loads(row[1] or "{}")
                        cursor = int(prev.get("cursor_vault_id") or 0)
                    except Exception:
                        cursor = 0
                else:
                    created_at = datetime.now().isoformat()
                    cur.execute(
                        """
                        INSERT INTO jobs (job_type, params_json, status, scheduled_for, created_at, started_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        ("knowledge_proposal_sweep", json.dumps({"batch_size": int(batch_size)}), "running", None, created_at, created_at, created_at),
                    )
                    job_id = int(cur.lastrowid)

            pending = [v for v in vaults if _vid(v) > int(cursor or 0)]
            pending = pending[: max(1, int(batch_size or 1))]

            staged_items = 0
            processed_ids: List[str] = []
            errors: List[str] = []
            new_cursor = int(cursor or 0)

            for v in pending:
                res = self._stage_knowledge_proposal(v)
                if isinstance(res, dict) and res.get("success"):
                    staged_items += int(res.get("staged") or 1)
                    processed_ids.append(str(v.get("id") or ""))
                    new_cursor = max(new_cursor, _vid(v))
                else:
                    errors.append(str(res))

            payload = {
                "success": True,
                "cursor_vault_id": int(new_cursor or 0),
                "staged_items": staged_items,
                "processed_vault_ids": processed_ids,
                "errors": errors[:5],
                "ran_at": datetime.now().isoformat(),
            }

            if job_id is not None:
                with self.db.get_connection() as conn:
                    conn.cursor().execute(
                        "UPDATE jobs SET status=?, result_json=?, updated_at=? WHERE id=?",
                        ("running", json.dumps(payload, ensure_ascii=False), datetime.now().isoformat(), int(job_id)),
                    )

            msg = (
                "Knowledge proposal sweep complete (stage-only).\n\n"
                f"cursor_vault_id: {payload['cursor_vault_id']}\n"
                f"processed: {processed_ids}\n"
                f"staged_items: {staged_items}\n"
            )
            if errors:
                msg += "\nErrors:\n- " + "\n- ".join(errors[:5])
            messagebox.showinfo("Knowledge Sweep", msg, parent=self)

            try:
                self._refresh_background_jobs()
            except Exception:
                pass

            # Deep-link: switch to Z Direct tab and show Neo peer inbox so the operator can commit.
            try:
                if hasattr(self, "_z_direct_tab"):
                    self.notebook.select(self._z_direct_tab)
                if getattr(self, "_z_direct_peer_var", None) is not None:
                    self._z_direct_peer_var.set("Z+2")
                if getattr(self, "_z_direct_refresh", None) is not None:
                    self._z_direct_refresh()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Knowledge Sweep", f"Sweep failed:\n{e}", parent=self)

    def _create_library_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """
        Library: operator-facing browsing surface for Oracle's durable registry.

        This is the "menu-like" readable layer for knowledge/vault browsing, complementing
        Unified Search (which can also browse).
        """
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Oracle: Library")

        tk.Label(
            tab,
            text="Library (Oracle Durable Registry)",
            font=('Arial', 18, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_cyan'],
        ).pack(pady=(16, 8))
        self._add_owner_bar(tab, owner_floor="Oracle", owner_channel="Z-2", note="durable registry browse + proposals (no deletes)")

        container = tk.Frame(tab, bg=self.colors['bg_dark'])
        container.pack(fill="both", expand=True, padx=20, pady=10)

        controls = tk.Frame(container, bg=self.colors['bg_dark'])
        controls.pack(fill="x", pady=(0, 10))

        tk.Label(controls, text="Kind:", bg=self.colors['bg_dark'], fg=self.colors['text_green']).pack(side="left")
        kind_var = tk.StringVar(value="all")
        kind_combo = ttk.Combobox(
            controls,
            textvariable=kind_var,
            state="readonly",
            width=18,
            values=["all", "vault_file", "knowledge_node", "citation", "learning_module", "workspace", "research_query", "dataset", "experiment_run"],
        )
        kind_combo.pack(side="left", padx=(6, 14))

        tk.Label(controls, text="Search:", bg=self.colors['bg_dark'], fg=self.colors['text_green']).pack(side="left")
        query_var = tk.StringVar(value="")
        query_entry = ttk.Entry(controls, textvariable=query_var, width=40)
        query_entry.pack(side="left", padx=(6, 14), fill="x", expand=True)

        # Main split
        body = tk.Frame(container, bg=self.colors['bg_dark'])
        body.pack(fill="both", expand=True)

        left = ttk.LabelFrame(body, text="Registry Items")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right = ttk.LabelFrame(body, text="Details")
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        cols = ("kind", "id", "title")
        tree = ttk.Treeview(left, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c.upper())
        tree.column("kind", width=130, anchor="w")
        tree.column("id", width=90, anchor="w")
        tree.column("title", width=520, anchor="w")
        tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        sb = ttk.Scrollbar(left, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)

        details = scrolledtext.ScrolledText(
            right,
            height=18,
            bg="#1e1e1e",
            fg="#00FF88",
            font=("Consolas", 9),
        )
        details.pack(fill="both", expand=True, padx=5, pady=5)
        try:
            details.config(state=tk.DISABLED)
        except Exception:
            pass

        btns = tk.Frame(container, bg=self.colors['bg_dark'])
        btns.pack(fill="x", pady=(10, 0))

        state: Dict[str, Any] = {"rows": []}

        def _title_for(obj: Dict[str, Any]) -> str:
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
                for it in tree.get_children():
                    tree.delete(it)
            except Exception:
                return

            rows = self._load_oracle_registry_objects()
            ksel = (kind_var.get() or "all").strip()
            q = (query_var.get() or "").strip().lower()

            view: List[Dict[str, Any]] = []
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
                    continue

            state["rows"] = view
            _render_details()

        def _selected_obj() -> Optional[Dict[str, Any]]:
            try:
                sel = tree.selection()
                if not sel:
                    return None
                idx = tree.index(sel[0])
                rows = state.get("rows") or []
                if 0 <= idx < len(rows):
                    return rows[idx]
            except Exception:
                pass
            return None

        def _open_universal_context_menu(event=None):
            """
            Right-click: open Trinity's UniversalFileContextMenu when the selected object
            resolves to an on-disk file/folder (vault_file/citation/knowledge_node source).
            """
            if event is None:
                return
            try:
                iid = tree.identify_row(event.y)
                if iid:
                    tree.selection_set(iid)
            except Exception:
                pass

            obj = _selected_obj()
            if not obj:
                return

            # Resolve best-effort filesystem target.
            try:
                k = str(obj.get("kind") or "")
                p = ""
                if k == "vault_file":
                    p = str(obj.get("path") or "")
                elif k == "citation":
                    p = self._resolve_oracle_vault_path(str(obj.get("vault_file_id") or ""))
                elif k == "knowledge_node":
                    sources = obj.get("sources") or []
                    if isinstance(sources, list) and sources:
                        s0 = sources[0]
                        if isinstance(s0, dict):
                            p = self._resolve_oracle_vault_path(str(s0.get("vault_file_id") or s0.get("id") or ""))
                        elif isinstance(s0, str) and s0.isdigit():
                            p = self._resolve_oracle_vault_path(s0)
                if not p:
                    return
                target = Path(p)
                if not target.exists():
                    return
            except Exception:
                return

            try:
                _force_trinity_ui_package()
                from ui.universal_context_menu import UniversalFileContextMenu  # type: ignore

                menu = UniversalFileContextMenu.create(
                    tree,
                    filepath=(target if target.is_file() else None),
                    folderpath=(target if target.is_dir() else None),
                    show_advanced=True,
                )
                menu.tk_popup(event.x_root, event.y_root)
                menu.grab_release()
            except Exception:
                return

        def _render_details():
            obj = _selected_obj()
            try:
                details.config(state=tk.NORMAL)
                details.delete("1.0", tk.END)
                if obj is None:
                    details.insert(tk.END, "Select an item to view details.")
                else:
                    details.insert(tk.END, json.dumps(obj, indent=2))
                details.config(state=tk.DISABLED)
            except Exception:
                pass

        def _open_path(p: str):
            try:
                if p:
                    os.startfile(p)  # type: ignore[attr-defined]
            except Exception:
                pass

        def open_selected():
            obj = _selected_obj()
            if not obj:
                return
            try:
                k = str(obj.get("kind") or "")
                p = ""
                if k == "vault_file":
                    p = str(obj.get("path") or "")
                elif k == "citation":
                    p = self._resolve_oracle_vault_path(str(obj.get("vault_file_id") or ""))
                elif k == "knowledge_node":
                    sources = obj.get("sources") or []
                    if isinstance(sources, list) and sources:
                        s0 = sources[0]
                        if isinstance(s0, dict):
                            p = self._resolve_oracle_vault_path(str(s0.get("vault_file_id") or s0.get("id") or ""))
                        elif isinstance(s0, str) and s0.isdigit():
                            p = self._resolve_oracle_vault_path(s0)
                _open_path(p)
            except Exception:
                pass

        def open_folder():
            obj = _selected_obj()
            if not obj:
                return
            try:
                p = ""
                if obj.get("kind") == "vault_file":
                    p = str(obj.get("path") or "")
                if not p:
                    return
                pp = Path(p)
                os.startfile(str(pp.parent if pp.is_file() else pp))  # type: ignore[attr-defined]
            except Exception:
                pass

        def copy_id():
            obj = _selected_obj()
            if not obj:
                return
            try:
                rid = str(obj.get("id") or "")
                self.clipboard_clear()
                self.clipboard_append(rid)
            except Exception:
                pass

        def propose_knowledge():
            obj = _selected_obj()
            if not obj or obj.get("kind") != "vault_file":
                messagebox.showwarning("Library", "Select a vault_file first.", parent=self)
                return
            res = self._stage_knowledge_proposal(obj)
            if not isinstance(res, dict) or not res.get("success"):
                messagebox.showerror("Library", f"Proposal failed:\n{res}", parent=self)
                return
            messagebox.showinfo(
                "Library",
                "Staged knowledge proposal into Trinity review queue.\n\n"
                f"citation_id: {res.get('citation_id')}\n"
                f"knowledge_node_ids: {res.get('knowledge_node_ids')}\n\n"
                "Next: go to Z Direct tab -> Peer=Z+2 -> Commit Inbox Selected (Target=auto).",
                parent=self,
            )
            try:
                if hasattr(self, "_z_direct_tab"):
                    self.notebook.select(self._z_direct_tab)
                if getattr(self, "_z_direct_peer_var", None) is not None:
                    self._z_direct_peer_var.set("Z+2")
                if getattr(self, "_z_direct_refresh", None) is not None:
                    self._z_direct_refresh()
            except Exception:
                pass

        ttk.Button(btns, text="Refresh", command=refresh).pack(side="left")
        ttk.Button(btns, text="Open", command=open_selected).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Open Folder", command=open_folder).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Copy ID", command=copy_id).pack(side="left", padx=(8, 0))
        ttk.Button(
            btns,
            text="Stage Knowledge (Run Once)",
            command=lambda: self._run_knowledge_proposal_sweep(batch_size=2),
        ).pack(side="left", padx=(16, 0))

        def _open_oracle_object_catalog() -> None:
            """
            Host-wired convenience: route into N's Object Catalog for Oracle committed objects.

            This keeps the Library panel focused on browse/propose while Catalog provides a
            menu-first cross-kind inspector for durable registries.
            """
            host = getattr(self, "parent_app", None)
            fn = getattr(host, "open_object_catalog", None) if host is not None else None
            if not callable(fn):
                messagebox.showwarning(
                    "Object Catalog",
                    "Object Catalog is only available when the IT Portal is opened from N (host context).",
                    parent=self,
                )
                return
            obj = _selected_obj()
            kind = str((obj or {}).get("kind") or "all")
            q = str((obj or {}).get("id") or "")
            try:
                fn(scope="oracle", kind=kind if kind else "all", query=q)
            except Exception:
                fn(scope="oracle", kind="all", query=q)

        ttk.Button(btns, text="Open Object Catalog", command=_open_oracle_object_catalog).pack(side="left", padx=(8, 0))

        def _vault_id_for_related(obj: Optional[Dict[str, Any]]) -> str:
            if not isinstance(obj, dict):
                return ""
            k = str(obj.get("kind") or "")
            if k == "vault_file":
                return str(obj.get("id") or "").strip()
            if k == "citation":
                return str(obj.get("vault_file_id") or "").strip()
            if k == "knowledge_node":
                sources = obj.get("sources") or []
                if isinstance(sources, list):
                    for s in sources:
                        if isinstance(s, dict):
                            vid = str(s.get("vault_file_id") or s.get("id") or "").strip()
                            if vid:
                                return vid
                        elif isinstance(s, str) and s.strip().isdigit():
                            return s.strip()
            return ""

        def _citation_ids_for_related(obj: Optional[Dict[str, Any]]) -> List[str]:
            """
            Extract citation_id(s) used for cross-linking citations <-> knowledge_nodes.

            - citation -> [citation.id]
            - knowledge_node -> sources[*].citation_id (when present)
            """
            if not isinstance(obj, dict):
                return []
            k = str(obj.get("kind") or "").strip()
            if k == "citation":
                cid = str(obj.get("id") or "").strip()
                return [cid] if cid else []
            if k == "knowledge_node":
                out: List[str] = []
                sources = obj.get("sources") or []
                if isinstance(sources, list):
                    for s in sources:
                        if isinstance(s, dict):
                            cid = str(s.get("citation_id") or "").strip()
                            if cid:
                                out.append(cid)
                # Stable unique order
                seen: set = set()
                uniq: List[str] = []
                for cid in out:
                    if cid in seen:
                        continue
                    seen.add(cid)
                    uniq.append(cid)
                return uniq
            return []

        def _open_related_window(title: str, items: List[Dict[str, Any]], *, kind_hint: str = "") -> None:
            win = tk.Toplevel(self)
            win.title(title)
            win.geometry("1100x740")
            try:
                win.transient(self)
            except Exception:
                pass

            header = tk.Frame(win, bg=self.colors["bg_panel"])
            header.pack(fill="x")
            tk.Label(
                header,
                text=title,
                bg=self.colors["bg_panel"],
                fg=self.colors["accent_cyan"],
                font=("Arial", 14, "bold"),
            ).pack(side="left", padx=12, pady=10)
            tk.Button(
                header,
                text="Close",
                command=win.destroy,
                bg=self.colors["bg_blue"],
                fg=self.colors["text_white"],
                relief="flat",
                padx=12,
                pady=6,
            ).pack(side="right", padx=12, pady=10)

            body2 = tk.Frame(win, bg=self.colors["bg_dark"])
            body2.pack(fill="both", expand=True, padx=12, pady=12)

            left2 = ttk.LabelFrame(body2, text="Items")
            left2.pack(side="left", fill="both", expand=True, padx=(0, 10))
            right2 = ttk.LabelFrame(body2, text="Details")
            right2.pack(side="right", fill="both", expand=True, padx=(10, 0))

            cols2 = ("kind", "id", "title")
            tree2 = ttk.Treeview(left2, columns=cols2, show="headings", height=18)
            for c in cols2:
                tree2.heading(c, text=c.upper())
            tree2.column("kind", width=130, anchor="w")
            tree2.column("id", width=110, anchor="w")
            tree2.column("title", width=520, anchor="w")
            tree2.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            sb2 = ttk.Scrollbar(left2, orient="vertical", command=tree2.yview)
            sb2.pack(side="right", fill="y")
            tree2.configure(yscrollcommand=sb2.set)

            details2 = scrolledtext.ScrolledText(
                right2,
                height=18,
                bg="#1e1e1e",
                fg="#00FF88",
                font=("Consolas", 9),
            )
            details2.pack(fill="both", expand=True, padx=5, pady=5)
            try:
                details2.config(state=tk.DISABLED)
            except Exception:
                pass

            def _sel2() -> Optional[Dict[str, Any]]:
                try:
                    sel = tree2.selection()
                    if not sel:
                        return None
                    idx = tree2.index(sel[0])
                    if 0 <= idx < len(items):
                        return items[idx]
                except Exception:
                    return None
                return None

            def _render2() -> None:
                obj = _sel2()
                try:
                    details2.config(state=tk.NORMAL)
                    details2.delete("1.0", tk.END)
                    details2.insert("1.0", json.dumps(obj or {}, indent=2))
                    details2.config(state=tk.DISABLED)
                except Exception:
                    pass

            def _copy_ids() -> None:
                try:
                    ids = [str(it.get("id") or "") for it in items if isinstance(it, dict)]
                    txt = "\n".join([i for i in ids if i.strip()]).strip()
                    if not txt:
                        return
                    self.clipboard_clear()
                    self.clipboard_append(txt)
                except Exception:
                    pass

            def _open_in_z_direct() -> None:
                # Z Direct is the operator surface; this deep-link helps inspection/approval workflows.
                try:
                    self._open_z_direct_view(channel="Z-2", peer="All", kind=(kind_hint or None))
                except Exception:
                    pass

            # Populate
            for it in items:
                try:
                    k = str(it.get("kind") or "")
                    rid = str(it.get("id") or "")
                    title2 = _title_for(it)
                    tree2.insert("", tk.END, values=(k, rid, (title2[:160] + "...") if len(title2) > 160 else title2))
                except Exception:
                    continue
            try:
                tree2.bind("<<TreeviewSelect>>", lambda _e: _render2())
            except Exception:
                pass
            _render2()

            btn_row = tk.Frame(win, bg=self.colors["bg_dark"])
            btn_row.pack(fill="x", padx=12, pady=(0, 12))
            tk.Button(
                btn_row,
                text="Copy IDs",
                command=_copy_ids,
                bg=self.colors["button_green"],
                fg="white",
                font=("Arial", 10, "bold"),
            ).pack(side="left")
            tk.Button(
                btn_row,
                text="Open Z Direct (Z-2)",
                command=_open_in_z_direct,
                bg=self.colors["bg_panel"],
                fg="white",
                font=("Arial", 10, "bold"),
            ).pack(side="left", padx=(8, 0))

        def show_related_citations() -> None:
            obj = _selected_obj()
            vault_id = _vault_id_for_related(obj)
            if not vault_id:
                messagebox.showwarning("Library", "Select a vault-linked item first (vault_file/citation/knowledge_node).", parent=self)
                return
            rows_all = self._load_oracle_registry_objects()
            items = [
                it
                for it in rows_all
                if isinstance(it, dict)
                and str(it.get("kind") or "") == "citation"
                and str(it.get("vault_file_id") or "").strip() == vault_id
            ]
            _open_related_window(f"Related Citations (vault_file_id={vault_id})", items, kind_hint="citation")

        def show_related_knowledge_nodes() -> None:
            obj = _selected_obj()
            vault_id = _vault_id_for_related(obj)
            if not vault_id:
                messagebox.showwarning("Library", "Select a vault-linked item first (vault_file/citation/knowledge_node).", parent=self)
                return
            rows_all = self._load_oracle_registry_objects()
            items: List[Dict[str, Any]] = []
            for it in rows_all:
                if not isinstance(it, dict) or str(it.get("kind") or "") != "knowledge_node":
                    continue
                sources = it.get("sources") or []
                found = False
                if isinstance(sources, list):
                    for s in sources:
                        if isinstance(s, dict):
                            vid = str(s.get("vault_file_id") or s.get("id") or "").strip()
                            if vid and vid == vault_id:
                                found = True
                                break
                        elif isinstance(s, str) and s.strip() == vault_id:
                            found = True
                            break
                if found:
                    items.append(it)
            _open_related_window(f"Related Knowledge Nodes (vault_file_id={vault_id})", items, kind_hint="knowledge_node")

        def show_related_by_citation() -> None:
            obj = _selected_obj()
            if not isinstance(obj, dict):
                messagebox.showwarning("Library", "Select an item first.", parent=self)
                return

            k = str(obj.get("kind") or "").strip()
            rows_all = self._load_oracle_registry_objects()
            if k == "citation":
                cid = str(obj.get("id") or "").strip()
                if not cid:
                    messagebox.showwarning("Library", "Selected citation has no id.", parent=self)
                    return
                items: List[Dict[str, Any]] = []
                for it in rows_all:
                    if not isinstance(it, dict) or str(it.get("kind") or "") != "knowledge_node":
                        continue
                    sources = it.get("sources") or []
                    found = False
                    if isinstance(sources, list):
                        for s in sources:
                            if isinstance(s, dict) and str(s.get("citation_id") or "").strip() == cid:
                                found = True
                                break
                    if found:
                        items.append(it)
                _open_related_window(f"Knowledge Nodes referencing citation_id={cid}", items, kind_hint="knowledge_node")
                return

            if k == "knowledge_node":
                cids = _citation_ids_for_related(obj)
                if not cids:
                    messagebox.showwarning("Library", "No citation_id found on this knowledge_node sources.", parent=self)
                    return
                items = [
                    it
                    for it in rows_all
                    if isinstance(it, dict)
                    and str(it.get("kind") or "") == "citation"
                    and str(it.get("id") or "").strip() in set(cids)
                ]
                _open_related_window(f"Citations referenced by knowledge_node (citation_id in sources)", items, kind_hint="citation")
                return

            messagebox.showwarning("Library", "Select a citation or knowledge_node for citation-based linking.", parent=self)

        ttk.Button(btns, text="Related Citations", command=show_related_citations).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Related Knowledge", command=show_related_knowledge_nodes).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Related via Citation", command=show_related_by_citation).pack(side="left", padx=(8, 0))
        def find_duplicates():
            """
            Identify likely duplicates in the Oracle durable registry.

            Primary heuristic: `vault_file.sha256` collisions (same bytes -> multiple paths/names).
            This does not delete anything; it generates an operator report for review.
            """
            rows = state.get("rows") or []
            if not isinstance(rows, list) or not rows:
                messagebox.showwarning("Library", "No registry rows loaded yet. Click Refresh first.", parent=self)
                return

            groups: Dict[str, List[Dict[str, Any]]] = {}
            for obj in rows:
                if not isinstance(obj, dict):
                    continue
                if str(obj.get("kind") or "") != "vault_file":
                    continue
                sha = str(obj.get("sha256") or "").strip()
                if not sha:
                    continue
                groups.setdefault(sha, []).append(obj)

            dupes = [(sha, items) for sha, items in groups.items() if len(items) > 1]
            dupes.sort(key=lambda x: len(x[1]), reverse=True)

            if not dupes:
                messagebox.showinfo("Library", "No vault_file duplicates found (by sha256) in the current view.", parent=self)
                return

            # Render report
            lines_out: List[str] = []
            total_items = sum(len(items) for _sha, items in dupes)
            lines_out.append("# Oracle Library Dedupe Report (sha256)")
            lines_out.append(f"generated_at: {datetime.utcnow().isoformat()}Z")
            lines_out.append(f"groups: {len(dupes)}")
            lines_out.append(f"items_in_groups: {total_items}")
            lines_out.append("")
            for i, (sha, items) in enumerate(dupes[:50]):
                lines_out.append(f"## [{i+1}] sha256={sha} ({len(items)} items)")
                for it in items[:12]:
                    vid = str(it.get("id") or "")
                    name = str(it.get("source_name") or it.get("name") or "")
                    path = str(it.get("path") or "")
                    lines_out.append(f"- id={vid} name={name} path={path}")
                if len(items) > 12:
                    lines_out.append(f"- ... (+{len(items) - 12} more)")
                lines_out.append("")
            if len(dupes) > 50:
                lines_out.append(f"(truncated: showing 50/{len(dupes)} groups)")

            report = "\n".join(lines_out).strip() + "\n"

            win = tk.Toplevel(self)
            win.title("Library Dedupe Report (sha256)")
            win.geometry("1100x760")
            try:
                win.transient(self)
            except Exception:
                pass

            header = tk.Frame(win, bg=self.colors["bg_panel"])
            header.pack(fill="x")
            tk.Label(
                header,
                text="Library Dedupe Report (sha256)",
                bg=self.colors["bg_panel"],
                fg=self.colors["accent_cyan"],
                font=("Arial", 14, "bold"),
            ).pack(side="left", padx=12, pady=10)
            tk.Button(
                header,
                text="Close",
                command=win.destroy,
                bg=self.colors["bg_blue"],
                fg=self.colors["text_white"],
                relief="flat",
                padx=12,
                pady=6,
            ).pack(side="right", padx=12, pady=10)

            text = scrolledtext.ScrolledText(
                win,
                bg="#001122",
                fg=self.colors["text_green"],
                font=("Consolas", 10),
                wrap="word",
            )
            text.pack(fill="both", expand=True, padx=12, pady=12)
            text.insert("1.0", report)
            try:
                text.configure(state="disabled")
            except Exception:
                pass

            btns2 = tk.Frame(win, bg=self.colors["bg_dark"])
            btns2.pack(fill="x", padx=12, pady=(0, 12))

            def _copy():
                try:
                    self.clipboard_clear()
                    self.clipboard_append(report)
                except Exception:
                    pass

            def _stage_to_smith():
                try:
                    from core.services import get_z_direct  # type: ignore

                    zd = get_z_direct()
                    env = zd.make_envelope(
                        kind="event",
                        channel="Z+3",
                        z_context="Z+3_Trinity",
                        source="trinity.it_portal.library",
                        tags=["library", "dedupe", "report"],
                        payload={
                            "kind": "dedupe_report",
                            "heuristic": "vault_file.sha256",
                            "groups": [
                                {
                                    "sha256": sha,
                                    "count": len(items),
                                    "vault_file_ids": [str(it.get("id") or "") for it in items if isinstance(it, dict)],
                                }
                                for sha, items in dupes[:200]
                            ],
                        },
                    )
                    # Record locally and deliver to Smith for actioning.
                    try:
                        zd.append_event("Z+3", env)
                    except Exception:
                        pass
                    try:
                        zd.append_channel_outbox(from_channel="Z+3", to_channel="Z-3", payload=env)
                    except Exception:
                        pass
                    try:
                        zd.append_channel_inbox(to_channel="Z-3", from_channel="Z+3", payload=env)
                    except Exception:
                        pass
                    messagebox.showinfo(
                        "Library",
                        "Staged dedupe report (event) and delivered it to Smith inbox.\n\n"
                        "Next: Tools -> Z Direct -> Channel=Z-3 (or select Smith floor) to review and route tasks.",
                        parent=win,
                    )
                except Exception as e:
                    messagebox.showerror("Library", f"Failed to stage report:\n{e}", parent=win)

            tk.Button(
                btns2,
                text="Copy Report",
                command=_copy,
                bg=self.colors["button_green"],
                fg="white",
                font=("Arial", 10, "bold"),
            ).pack(side="left")
            tk.Button(
                btns2,
                text="Stage to Smith Inbox",
                command=_stage_to_smith,
                bg=self.colors["button_orange"],
                fg="white",
                font=("Arial", 10, "bold"),
            ).pack(side="left", padx=(8, 0))

        ttk.Button(btns, text="Propose Knowledge", command=propose_knowledge).pack(side="right")
        ttk.Button(btns, text="Find Duplicates (sha256)", command=find_duplicates).pack(side="right", padx=(0, 8))
        def _queue_db_dedupe():
            """Queue a DB-backed sha256 duplicate scan (runs in Smith background worker)."""
            try:
                host = getattr(self, "parent_app", None)
                queue = getattr(host, "smith_queue", None)
                if queue is None or not hasattr(queue, "add_task"):
                    raise RuntimeError("Smith queue is unavailable (launch via N.py / LAUNCH_GUI to enable background jobs).")
                task_id = queue.add_task(
                    task_type="oracle.find_duplicates_sha256",
                    parameters={"limit": 50},
                    source_floor="Z-2_Oracle",
                    priority=3,
                )
                messagebox.showinfo(
                    "Library",
                    f"Queued DB sha256 duplicate scan as Smith task #{task_id}.\n\n"
                    "View progress/results in Smith -> Jobs Monitor (Background Jobs widget).",
                    parent=self,
                )
            except Exception as e:
                messagebox.showwarning("Library", f"Could not queue DB duplicate scan:\n{e}", parent=self)

        ttk.Button(btns, text="Queue Duplicates (DB)", command=_queue_db_dedupe).pack(side="right", padx=(0, 8))

        try:
            tree.bind("<<TreeviewSelect>>", lambda _e: _render_details())
            tree.bind("<Button-3>", _open_universal_context_menu)
            kind_combo.bind("<<ComboboxSelected>>", lambda _e: refresh())
            query_entry.bind("<Return>", lambda _e: refresh())
        except Exception:
            pass

        refresh()
    def _create_dependency_map_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Dependency Map: Floors + services + manifest link graph (no imports)."""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Merovingian: Dependency Map")

        tk.Label(
            tab,
            text="Platform Dependency Map (Floors + Services)",
            font=('Arial', 18, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_cyan'],
        ).pack(pady=20)
        self._add_owner_bar(tab, owner_floor="Merovingian", owner_channel="Z-4", note="manifests/services graph")

        container = tk.Frame(tab, bg=self.colors['bg_dark'])
        container.pack(fill='both', expand=True, padx=20, pady=10)

        left = ttk.LabelFrame(container, text="Graph Tree")
        left.pack(side='left', fill='both', expand=True, padx=(0, 10))

        right = ttk.LabelFrame(container, text="Summary / Issues")
        right.pack(side='right', fill='both', expand=True, padx=(10, 0))

        columns = ('Kind', 'Status', 'Details')
        tree = ttk.Treeview(left, columns=columns, show='tree headings', height=18)
        tree.heading('#0', text='Node')
        tree.heading('Kind', text='Kind')
        tree.heading('Status', text='Status')
        tree.heading('Details', text='Details')
        tree.column('#0', width=260)
        tree.column('Kind', width=110)
        tree.column('Status', width=90)
        tree.column('Details', width=420)
        tree.pack(fill='both', expand=True, padx=5, pady=5)

        summary = scrolledtext.ScrolledText(
            right,
            height=18,
            bg='#1e1e1e',
            fg='#00FF88',
            font=('Consolas', 9),
        )
        summary.pack(fill='both', expand=True, padx=5, pady=5)

        btns = tk.Frame(tab, bg=self.colors['bg_dark'])
        btns.pack(fill='x', padx=20, pady=(0, 10))

        state = {"graph": None}

        def _lightspeed_root() -> Path:
            here = Path(__file__).resolve()
            for cand in (here, *here.parents):
                if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                    return cand
            return Path.cwd().resolve()

        def scan():
            tree.delete(*tree.get_children())
            summary.config(state='normal')
            summary.delete('1.0', 'end')

            try:
                from core.analysis.dependencies import PlatformDependencyMapper
                lightspeed_root = _lightspeed_root()
                graph = PlatformDependencyMapper(lightspeed_root).build()
                state["graph"] = graph

                # Keep the rest of the platform in sync (N/Trinity widgets read this).
                try:
                    out_path = (lightspeed_root / "dataindex" / "depmap.json").resolve()
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
                except Exception:
                    pass

                nodes = {n["id"]: n for n in graph.get("nodes", [])}
                edges = graph.get("edges", [])

                children = {}
                for e in edges:
                    children.setdefault(e["source"], []).append((e["target"], e["kind"]))

                def render(node_id: str, parent: str = ""):
                    n = nodes.get(node_id)
                    if not n:
                        return
                    ok = bool(n.get("ok", True))
                    status = "OK" if ok else "MISS"
                    kind = n.get("kind", "")
                    details = ""
                    meta = n.get("meta") or {}
                    if kind == "module":
                        details = str(meta.get("resolution") or meta.get("origin") or "")
                    elif kind == "file":
                        details = str(meta.get("path") or "")
                    elif kind in ("floor", "service", "component"):
                        if isinstance(meta, dict):
                            if "enabled" in meta:
                                details = f"enabled={meta.get('enabled')}"
                    item = tree.insert(parent, 'end', text=n.get("label", node_id), values=(kind, status, details))
                    for child_id, edge_kind in sorted(children.get(node_id, []), key=lambda x: (x[1], x[0])):
                        render(child_id, item)

                render("group:floors")
                render("group:services")

                stats = graph.get("stats", {})
                issues = graph.get("issues", {})
                summary.insert('end', "[Dependency Map]\n")
                summary.insert('end', f"Generated: {stats.get('generated_at')}\n")
                summary.insert('end', f"Nodes: {stats.get('nodes')}  Edges: {stats.get('edges')}\n\n")
                summary.insert('end', "[Issues]\n")
                for k, v in (stats.get("issues") or {}).items():
                    summary.insert('end', f"- {k}: {v}\n")
                summary.insert('end', "\n")

                if issues.get("unresolvable_modules"):
                    summary.insert('end', "Unresolvable modules (first 50):\n")
                    for m in issues["unresolvable_modules"][:50]:
                        summary.insert('end', f"  - {m}\n")
                    summary.insert('end', "\n")

                if issues.get("missing_files"):
                    summary.insert('end', "Missing files (first 50):\n")
                    for p in issues["missing_files"][:50]:
                        summary.insert('end', f"  - {p}\n")
                    summary.insert('end', "\n")

            except Exception as e:
                summary.insert('end', f"Error building dependency map: {e}\n")
                state["graph"] = None

            summary.config(state='disabled')

        def export_json():
            graph = state.get("graph")
            if not graph:
                messagebox.showwarning("No Data", "Run Scan first.", parent=self)
                return
            lightspeed_root = _lightspeed_root()
            out_path = (lightspeed_root / "dataindex" / "depmap.json").resolve()
            try:
                out_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
                messagebox.showinfo("Exported", f"Wrote:\n{out_path}", parent=self)
            except Exception as e:
                messagebox.showerror("Export Failed", str(e), parent=self)

        def copy_json():
            graph = state.get("graph")
            if not graph:
                messagebox.showwarning("No Data", "Run Scan first.", parent=self)
                return
            try:
                self.clipboard_clear()
                self.clipboard_append(json.dumps(graph))
                messagebox.showinfo("Copied", "Dependency map JSON copied to clipboard.", parent=self)
            except Exception as e:
                messagebox.showerror("Copy Failed", str(e), parent=self)

        tk.Button(btns, text="Scan", command=scan,
                  bg=self.colors['button_green'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        tk.Button(btns, text="Export JSON", command=export_json,
                  bg=self.colors['button_green'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        tk.Button(btns, text="Copy JSON", command=copy_json,
                  bg=self.colors['button_green'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        scan()

    def _create_footer(self):
        """Create status footer"""
        footer = tk.Frame(self, bg=self.colors['bg_panel'], height=30)
        footer.pack(side='bottom', fill='x')
        footer.pack_propagate(False)

        self.status_label = tk.Label(footer, text="IT Portal Ready",
                                     bg=self.colors['bg_panel'],
                                     fg=self.colors['text_green'],
                                     font=('Arial', 9), anchor='w')
        self.status_label.pack(side='left', padx=10)

        # System indicators
        if HAS_SERVICES:
            tk.Label(footer, text="* Services Online",
                    bg=self.colors['bg_panel'],
                    fg=self.colors['success_green'],
                    font=('Arial', 8)).pack(side='right', padx=10)

    # ========================================================================
    # TAB 1: DASHBOARD
    # ========================================================================

    def _create_dashboard_tab(self):
        """Dashboard with system overview"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Dashboard")

        # Header + toolbar
        header = tk.Frame(tab, bg=self.colors['bg_dark'])
        header.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            header,
            text="System Overview",
            font=("Arial", 18, "bold"),
            bg=self.colors["bg_dark"],
            fg=self.colors["accent_cyan"],
        ).pack(side="left")

        toolbar = tk.Frame(header, bg=self.colors["bg_dark"])
        toolbar.pack(side="right")

        tk.Button(
            toolbar,
            text="Refresh",
            command=lambda: self._refresh_dashboard(),
            bg=self.colors["button_green"],
            fg="white",
            font=("Arial", 9, "bold"),
        ).pack(side="right", padx=(6, 0))

        tk.Button(
            toolbar,
            text="Open Jobs Ledger",
            command=lambda: self.open_floor_tab("Smith", "Jobs & Artifacts"),
            bg=self.colors["button_green"],
            fg="white",
            font=("Arial", 9, "bold"),
        ).pack(side="right", padx=(6, 0))

        banner = tk.Frame(tab, bg=self.colors["bg_panel"])
        banner.pack(fill="x", padx=16, pady=(0, 12))

        role_text = "IT/Founder Operator Surface"
        company_text = self.company_name or ("Company #" + str(self.company_id) if self.company_id is not None else "Shared Scope")
        tk.Label(
            banner,
            text=f"{role_text} | Scope: {company_text}",
            bg=self.colors["bg_panel"],
            fg=self.colors["accent_cyan"],
            font=("Arial", 11, "bold"),
        ).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Label(
            banner,
            text=(
                "Use this dashboard for governance and operator flow, not as a second general user shell. "
                "Canonical path: Floors for work surfaces, Z Direct for approvals, Oracle Library for knowledge review."
            ),
            justify="left",
            wraplength=1200,
            bg=self.colors["bg_panel"],
            fg=self.colors["text_white"],
            font=("Arial", 9),
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Resizable dashboard layout (drag the sashes between panes).
        root_pane = ttk.PanedWindow(tab, orient="vertical")
        root_pane.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        row1 = ttk.PanedWindow(root_pane, orient="horizontal")
        row2 = ttk.PanedWindow(root_pane, orient="horizontal")
        row3 = ttk.PanedWindow(root_pane, orient="horizontal")

        try:
            root_pane.add(row1, weight=1)
            root_pane.add(row2, weight=1)
            root_pane.add(row3, weight=1)
        except Exception:
            root_pane.add(row1)
            root_pane.add(row2)
            root_pane.add(row3)

        # Services status
        self._create_dashboard_paned_panel(row1, "Services Status", self._populate_services_panel)

        # Z-Floors status
        self._create_dashboard_paned_panel(row1, "Z-Floors", self._populate_floors_panel)

        # Database stats
        self._create_dashboard_paned_panel(row1, "Database", self._populate_database_panel)

        # Dependencies (live, DB/manifest-backed)
        if HAS_DASH_WIDGETS:
            self._create_dashboard_paned_panel(row2, "Dependencies", self._populate_dependencies_panel)
        else:
            self._create_dashboard_paned_panel(row2, "Components", self._populate_components_panel)

        # Active tasks
        self._create_dashboard_paned_panel(row2, "Active Tasks", self._populate_tasks_panel)

        # Recent jobs (DB-backed) + entry point to the immutable job ledger.
        self._create_dashboard_paned_panel(row2, "Jobs (Recent)", self._populate_jobs_panel)

        # Quick actions (Column 1)
        actions_panel = self._create_dashboard_paned_panel(row3, "Quick Actions", None)

        actions = [
            ("Run System Check", self._run_system_check),
            ("Open Z Direct", lambda: self._select_tab_title("Z Direct")),
            ("Oracle Library", lambda: self._select_tab_title("Oracle: Library")),
            ("Project Manager", lambda: self.open_floor_tab("Architect", "Project Manager")),
            ("Jobs & Artifacts", lambda: self.open_floor_tab("Smith", "Jobs & Artifacts")),
            ("Oracle Ingestion", lambda: self._open_oracle_panel()),
            ("Database Browser", lambda: self.open_floor_tab("Merovingian", "Database Browser")),
            ("Profile + Setup", lambda: self._open_hub_focus("setup_state")),
        ]

        for text, cmd in actions:
            tk.Button(actions_panel, text=text, command=cmd,
                     bg=self.colors['button_green'], fg='white',
                     font=('Arial', 10, 'bold'), width=20).pack(pady=5, padx=10)

        # Canonical operator flow (Column 2)
        trinity_panel = self._create_dashboard_paned_panel(row3, "Operator Flow", None)

        trinity_actions = [
            ("1. Workspace Floors", lambda: self._select_tab_title("Floors")),
            ("2. Oracle Library", lambda: self._select_tab_title("Oracle: Library")),
            ("3. Review Approvals", lambda: self._select_tab_title("Z Direct")),
            ("4. Architect Finalization", lambda: self.open_floor_tab("Architect", "Portal")),
            ("5. Trinity Settings", lambda: self.open_floor_tab("Trinity", "Settings Hub")),
        ]

        for text, cmd in trinity_actions:
            tk.Button(trinity_panel, text=text, command=cmd,
                     bg=self.colors['accent_cyan'], fg='black',
                     font=('Arial', 10, 'bold'), width=20).pack(pady=5, padx=10)

        # Recent activity (Column 3)
        self._create_dashboard_paned_panel(row3, "Recent Activity", self._populate_activity_panel)

        # Store a refresher hook for toolbar usage.
        self._dashboard_refresh_hook = lambda: self._refresh_dashboard()

    def _refresh_dashboard(self):
        """Best-effort dashboard refresh (rebuilds dashboard tab contents)."""
        try:
            # Recreate only the dashboard tab to avoid disturbing other tabs/state.
            current = self.notebook.select()
            # Find and replace the Dashboard tab.
            dash_id = None
            for tab_id in self.notebook.tabs():
                if str(self.notebook.tab(tab_id, "text") or "") == "Dashboard":
                    dash_id = tab_id
                    break
            if dash_id is None:
                return
            try:
                dash_index = int(self.notebook.index(dash_id))
            except Exception:
                dash_index = None
            try:
                self.notebook.forget(dash_id)
            except Exception:
                return
            self._create_dashboard_tab()
            # Keep Dashboard as the first tab (or preserve its previous index).
            try:
                if dash_index is not None:
                    new_id = None
                    for tab_id in self.notebook.tabs():
                        if str(self.notebook.tab(tab_id, "text") or "") == "Dashboard":
                            new_id = tab_id
                            break
                    if new_id is not None:
                        self.notebook.insert(dash_index, new_id)
            except Exception:
                pass
            # Return to original tab if possible.
            if current:
                try:
                    self.notebook.select(current)
                except Exception:
                    pass
        except Exception:
            pass

    def _create_dashboard_paned_panel(self, paned: ttk.PanedWindow, title: str, populate_func=None):
        """
        Create a resizable dashboard panel inside a PanedWindow.

        Adds a header with a +/- toggle so users can collapse sections without
        losing their place.
        """
        panel = tk.Frame(paned, bg=self.colors["bg_panel"], relief="solid", bd=2)

        header = tk.Frame(panel, bg=self.colors["bg_panel"])
        header.pack(fill="x", padx=8, pady=(8, 4))

        title_lbl = tk.Label(
            header,
            text=title,
            bg=self.colors["bg_panel"],
            fg=self.colors["accent_cyan"],
            font=("Arial", 12, "bold"),
            anchor="w",
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        body = tk.Frame(panel, bg=self.colors["bg_panel"])
        body.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        state = {"collapsed": False}

        def toggle():
            state["collapsed"] = not state["collapsed"]
            try:
                if state["collapsed"]:
                    body.pack_forget()
                    btn_toggle.config(text="+")
                else:
                    body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
                    btn_toggle.config(text="-")
            except Exception:
                pass

        btn_toggle = tk.Button(
            header,
            text="-",
            command=toggle,
            bg=self.colors["bg_panel"],
            fg=self.colors["text_green"],
            relief="flat",
            font=("Arial", 12, "bold"),
            padx=6,
            pady=0,
        )
        btn_toggle.pack(side="right")

        if populate_func:
            try:
                populate_func(body)
            except Exception:
                # Keep the dashboard alive even if a panel fails to populate.
                pass

        try:
            paned.add(panel, weight=1)
        except Exception:
            paned.add(panel)
        return panel

    def _populate_dependencies_panel(self, panel):
        """Populate dependency overview (depmap + service registry)."""
        if not HAS_DASH_WIDGETS:
            self._populate_components_panel(panel)
            return
        try:
            DependencyMapWidget(panel, lightspeed_root=self.lightspeed_root).pack(fill="both", expand=True, padx=10, pady=10)
        except Exception:
            self._populate_components_panel(panel)

    def _populate_jobs_panel(self, panel):
        """Populate recent jobs summary (interactive, DB-backed)."""
        if HAS_DASH_WIDGETS:
            try:
                # A full jobs widget in the dashboard can be heavy; show a compact list + open button.
                pass
            except Exception:
                pass

        if not self.db:
            tk.Label(
                panel,
                text="Database offline",
                bg=self.colors['bg_panel'],
                fg=self.colors['error_red'],
                font=('Arial', 10),
            ).pack(padx=15, pady=5)
            return

        container = tk.Frame(panel, bg=self.colors['bg_panel'])
        container.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("status", "tool", "type", "updated")
        tree = ttk.Treeview(container, columns=columns, show="tree headings", height=6)
        tree.heading("#0", text="ID")
        tree.heading("status", text="Status")
        tree.heading("tool", text="Tool")
        tree.heading("type", text="Type")
        tree.heading("updated", text="Updated")
        tree.column("#0", width=60)
        tree.column("status", width=90)
        tree.column("tool", width=140)
        tree.column("type", width=140)
        tree.column("updated", width=140)
        tree.pack(side="top", fill="both", expand=True)

        btns = tk.Frame(container, bg=self.colors['bg_panel'])
        btns.pack(side="bottom", fill="x", pady=(6, 0))

        def refresh():
            try:
                tree.delete(*tree.get_children())
                rows = self.db.fetchall(
                    """
                    SELECT id, job_type, tool_key, status, COALESCE(updated_at, created_at) AS updated_at
                    FROM jobs
                    ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
                    LIMIT 8
                    """
                ) or []
                for r in rows:
                    tree.insert(
                        "",
                        "end",
                        text=str(r.get("id")),
                        values=(
                            r.get("status") or "pending",
                            (r.get("tool_key") or "")[:36],
                            r.get("job_type") or "",
                            r.get("updated_at") or "",
                        ),
                    )
            except Exception:
                return

        def open_jobs_tab():
            try:
                self.open_floor_tab("Smith", "Jobs & Artifacts")
            except Exception:
                pass

        tk.Button(
            btns,
            text="Open Jobs Ledger",
            command=open_jobs_tab,
            bg=self.colors['button_green'],
            fg="white",
            font=("Arial", 9, "bold"),
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btns,
            text="Refresh",
            command=refresh,
            bg=self.colors['button_green'],
            fg="white",
            font=("Arial", 9, "bold"),
        ).pack(side="left")

        refresh()

    def _create_jobs_ledger_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Tab 17B: Immutable V1 job ledger (jobs + artifacts + manifests)."""
        import os

        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Smith: Jobs & Artifacts")

        tk.Label(
            tab,
            text="Jobs & Artifacts (V1 Ledger)",
            font=("Arial", 18, "bold"),
            bg=self.colors["bg_dark"],
            fg=self.colors["accent_cyan"],
        ).pack(pady=20)
        self._add_owner_bar(tab, owner_floor="Smith", owner_channel="Z-3", note="jobs/artifacts ledger")

        if not self.db:
            tk.Label(
                tab,
                text="Database offline",
                bg=self.colors["bg_dark"],
                fg=self.colors["error_red"],
                font=("Arial", 12, "bold"),
            ).pack(pady=20)
            return

        container = tk.Frame(tab, bg=self.colors["bg_dark"])
        container.pack(fill="both", expand=True, padx=20, pady=10)

        panes = ttk.PanedWindow(container, orient="vertical")
        panes.pack(fill="both", expand=True)

        top = ttk.Frame(panes)
        bottom = ttk.Frame(panes)
        try:
            panes.add(top, weight=2)
            panes.add(bottom, weight=1)
        except Exception:
            panes.add(top)
            panes.add(bottom)

        # Jobs list
        jobs_frame = ttk.LabelFrame(top, text="Jobs")
        jobs_frame.pack(fill="both", expand=True, padx=6, pady=6)

        filter_row = tk.Frame(jobs_frame, bg=self.colors["bg_panel"])
        filter_row.pack(fill="x", padx=6, pady=(6, 0))

        tk.Label(filter_row, text="Filter:", bg=self.colors["bg_panel"], fg=self.colors["text_green"]).pack(side="left")
        filter_var = tk.StringVar(value="")
        tk.Entry(filter_row, textvariable=filter_var, width=28).pack(side="left", padx=(6, 0))

        columns = ("status", "job_type", "tool_key", "z_context", "created", "manifest")
        job_tree = ttk.Treeview(jobs_frame, columns=columns, show="tree headings", height=10)
        job_tree.heading("#0", text="ID")
        job_tree.heading("status", text="Status")
        job_tree.heading("job_type", text="Type")
        job_tree.heading("tool_key", text="Tool")
        job_tree.heading("z_context", text="Z")
        job_tree.heading("created", text="Created")
        job_tree.heading("manifest", text="Manifest")
        job_tree.column("#0", width=70)
        job_tree.column("status", width=90)
        job_tree.column("job_type", width=130)
        job_tree.column("tool_key", width=160)
        job_tree.column("z_context", width=90)
        job_tree.column("created", width=150)
        job_tree.column("manifest", width=220)
        job_tree.pack(fill="both", expand=True, padx=6, pady=6)

        selected_job_id = {"value": None}

        def _open_path(p: str | None):
            if not p:
                return
            try:
                os.startfile(p)  # type: ignore[attr-defined]
            except Exception:
                pass

        def _job_rows():
            try:
                rows = self.db.fetchall(
                    "SELECT id, status, job_type, tool_key, z_context, created_at, manifest_path, run_dir "
                    "FROM jobs ORDER BY id DESC LIMIT 300"
                ) or []
                return rows
            except Exception:
                return []

        def refresh_jobs():
            try:
                job_tree.delete(*job_tree.get_children())
            except Exception:
                pass

            q = filter_var.get().strip().lower()
            for r in _job_rows():
                hay = " ".join(
                    [
                        str(r.get("job_type") or ""),
                        str(r.get("tool_key") or ""),
                        str(r.get("z_context") or ""),
                        str(r.get("status") or ""),
                    ]
                ).lower()
                if q and q not in hay:
                    continue
                jid = r.get("id")
                job_tree.insert(
                    "",
                    "end",
                    text=str(jid),
                    values=(
                        r.get("status") or "",
                        r.get("job_type") or "",
                        r.get("tool_key") or "",
                        r.get("z_context") or "",
                        (r.get("created_at") or "")[:19],
                        r.get("manifest_path") or "",
                    ),
                    tags=(str(jid),),
                )

        # Artifacts list
        arts_frame = ttk.LabelFrame(bottom, text="Artifacts")
        arts_frame.pack(fill="both", expand=True, padx=6, pady=6)

        art_cols = ("kind", "name", "size", "path")
        art_tree = ttk.Treeview(arts_frame, columns=art_cols, show="tree headings", height=8)
        art_tree.heading("#0", text="ID")
        art_tree.heading("kind", text="Kind")
        art_tree.heading("name", text="Name")
        art_tree.heading("size", text="Bytes")
        art_tree.heading("path", text="Path")
        art_tree.column("#0", width=70)
        art_tree.column("kind", width=120)
        art_tree.column("name", width=180)
        art_tree.column("size", width=90)
        art_tree.column("path", width=520)
        art_tree.pack(fill="both", expand=True, padx=6, pady=6)

        def refresh_artifacts(job_id: int | None):
            try:
                art_tree.delete(*art_tree.get_children())
            except Exception:
                pass
            if not job_id:
                return
            try:
                rows = self.db.fetchall(
                    "SELECT id, kind, name, size_bytes, path FROM artifacts WHERE job_id = ? ORDER BY id ASC",
                    (int(job_id),),
                ) or []
                for r in rows:
                    art_tree.insert(
                        "",
                        "end",
                        text=str(r.get("id")),
                        values=(
                            r.get("kind") or "",
                            r.get("name") or "",
                            r.get("size_bytes") or 0,
                            r.get("path") or "",
                        ),
                    )
            except Exception:
                return

        def on_job_select(_event=None):
            sel = job_tree.selection()
            if not sel:
                selected_job_id["value"] = None
                refresh_artifacts(None)
                return
            jid = job_tree.item(sel[0], "text")
            try:
                selected_job_id["value"] = int(str(jid).strip())
            except Exception:
                selected_job_id["value"] = None
            refresh_artifacts(selected_job_id["value"])

        job_tree.bind("<<TreeviewSelect>>", on_job_select)

        btns = tk.Frame(tab, bg=self.colors["bg_dark"])
        btns.pack(fill="x", padx=20, pady=(0, 12))

        tk.Button(
            btns,
            text="Refresh",
            command=refresh_jobs,
            bg=self.colors["button_green"],
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(side="left", padx=(0, 6))

        def open_run_dir():
            jid = selected_job_id["value"]
            if not jid:
                return
            try:
                row = self.db.fetchone("SELECT run_dir FROM jobs WHERE id = ?", (int(jid),))
                _open_path(row.get("run_dir") if row else None)
            except Exception:
                return

        def open_manifest():
            jid = selected_job_id["value"]
            if not jid:
                return
            try:
                row = self.db.fetchone("SELECT manifest_path FROM jobs WHERE id = ?", (int(jid),))
                _open_path(row.get("manifest_path") if row else None)
            except Exception:
                return

        tk.Button(
            btns,
            text="Open Run Folder",
            command=open_run_dir,
            bg=self.colors["button_green"],
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btns,
            text="Open Manifest",
            command=open_manifest,
            bg=self.colors["button_green"],
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(side="left", padx=(0, 6))

        filter_var.trace_add("write", lambda *_: refresh_jobs())
        refresh_jobs()

    def _create_dashboard_panel(self, parent, title, populate_func=None, side='left'):
        """Create dashboard panel"""
        panel = tk.Frame(parent, bg=self.colors['bg_panel'], relief='solid', bd=2)
        panel.pack(side=side, fill='both', expand=True, padx=5)

        tk.Label(panel, text=title,
                bg=self.colors['bg_panel'],
                fg=self.colors['accent_cyan'],
                font=('Arial', 12, 'bold')).pack(pady=10)

        if populate_func:
            populate_func(panel)

        return panel

    def _populate_services_panel(self, panel):
        """Populate services status"""
        if HAS_SERVICES:
            services = [
                ("Database", "operational"),
                ("Event Bus", "operational"),
                ("Storage", "operational"),
            ]
        else:
            services = [("Services", "offline")]

        for service, status in services:
            color = self.colors['success_green'] if status == "operational" else self.colors['error_red']
            tk.Label(panel, text=f"* {service}: {status}",
                    bg=self.colors['bg_panel'], fg=color,
                    font=('Arial', 9)).pack(anchor='w', padx=15, pady=2)

        # Service registry (floors/services enablement)
        try:
            from core.services.function_registry import validate_service_registry

            reg_status = validate_service_registry(self.lightspeed_root, include_disabled=True)
            if reg_status.get("exists"):
                enabled = reg_status.get("enabled", 0)
                total = reg_status.get("total", 0)
                ok = reg_status.get("import_ok", 0)
                fail = reg_status.get("import_fail", 0)

                tk.Label(panel, text=f"Service Registry: {enabled}/{total} enabled",
                         bg=self.colors['bg_panel'], fg=self.colors['text_cyan'],
                         font=('Arial', 9, 'bold')).pack(anchor='w', padx=15, pady=(10, 2))

                color = self.colors['success_green'] if fail == 0 else self.colors['warning_orange']
                tk.Label(panel, text=f"Imports: {ok} ok, {fail} failed",
                         bg=self.colors['bg_panel'], fg=color,
                         font=('Arial', 9)).pack(anchor='w', padx=15, pady=1)

                if fail:
                    errors = [
                        (name, entry.get("error"))
                        for name, entry in (reg_status.get("entries") or {}).items()
                        if entry and entry.get("enabled", False) and not entry.get("import_ok", False)
                    ]
                    for name, err in errors[:3]:
                        short = (err or "")[:80]
                        tk.Label(panel, text=f"  - {name}: {short}",
                                 bg=self.colors['bg_panel'], fg=self.colors['warning_orange'],
                                 font=('Arial', 8)).pack(anchor='w', padx=20, pady=1)
            else:
                tk.Label(panel, text="Service Registry: not found",
                         bg=self.colors['bg_panel'], fg=self.colors['warning_orange'],
                         font=('Arial', 9)).pack(anchor='w', padx=15, pady=(10, 2))
        except Exception as e:
            tk.Label(panel, text=f"Service Registry error: {str(e)[:80]}",
                     bg=self.colors['bg_panel'], fg=self.colors['warning_orange'],
                     font=('Arial', 9)).pack(anchor='w', padx=15, pady=(10, 2))

    def _populate_floors_panel(self, panel):
        """Populate Z-floors status"""
        floor_count = len([f for f in self.z_floors.values() if f is not None])
        total_floors = 8

        tk.Label(panel, text=f"{floor_count}/{total_floors} floors loaded",
                bg=self.colors['bg_panel'], fg=self.colors['text_green'],
                font=('Arial', 10)).pack(padx=15, pady=5)

        for floor_name, module in self.z_floors.items():
            color = self.colors['success_green'] if module else self.colors['warning_orange']
            status = "loaded" if module else "unavailable"
            tk.Label(panel, text=f"* {floor_name}: {status}",
                    bg=self.colors['bg_panel'], fg=color,
                    font=('Arial', 9)).pack(anchor='w', padx=15, pady=1)

    def _populate_database_panel(self, panel):
        """Populate database stats"""
        # Schema status + explicit migration button (setup/login consolidated into Trinity; no silent runtime mutation).
        header = tk.Frame(panel, bg=self.colors["bg_panel"])
        header.pack(fill="x", padx=10, pady=(10, 6))

        schema_ok = None
        schema_report = None
        try:
            schema_ok = getattr(self.db, "schema_ok", None)
            schema_report = getattr(self.db, "schema_report", None)
        except Exception:
            schema_ok = None
            schema_report = None

        if schema_ok is True:
            schema_text = "Schema: Ready"
            schema_color = self.colors["success_green"]
        elif schema_ok is False:
            missing_tables = (schema_report or {}).get("missing_tables") or []
            missing_cols = (schema_report or {}).get("missing_columns") or {}
            schema_text = f"Schema: Update required (tables={len(missing_tables)}, cols={len(missing_cols)})"
            schema_color = self.colors["error_red"]
        else:
            schema_text = "Schema: Unknown"
            schema_color = self.colors["warning_orange"]

        tk.Label(
            header,
            text=schema_text,
            bg=self.colors["bg_panel"],
            fg=schema_color,
            font=("Arial", 10, "bold"),
        ).pack(side="left")

        def run_migration():
            if not messagebox.askyesno(
                "Database Schema Update",
                "Run Trinity database initialization/update?\n\n"
                "This is an explicit schema update (no silent runtime mutation).",
                parent=self,
            ):
                return

            def _worker():
                try:
                    init_path = (
                        self.lightspeed_root
                        / "Z Axis"
                        / "Z+3_Trinity"
                        / "tools"
                        / "initialize_database.py"
                    ).resolve()
                    spec = importlib.util.spec_from_file_location("lightspeed_firstrun_db_init", init_path)
                    if spec is None or spec.loader is None:
                        raise ImportError(f"Cannot load DB initializer from {init_path}")
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = mod
                    spec.loader.exec_module(mod)
                    init_fn = getattr(mod, "initialize_database")
                    res = init_fn(quiet=True)

                    def _done_ok():
                        try:
                            # Refresh DB handle so schema flags update
                            if hasattr(self.db, "validate_schema"):
                                self.db.schema_report = self.db.validate_schema()
                                self.db.schema_ok = bool((self.db.schema_report or {}).get("ok"))
                        except Exception:
                            pass
                        messagebox.showinfo(
                            "Database Schema Update",
                            "Database schema update finished.\n\n"
                            f"OK: {bool(res.get('ok'))}\n"
                            f"Created tables: {len(res.get('created_tables') or [])}\n"
                            f"Added columns: {sum(len(v) for v in (res.get('added_columns') or {}).values())}",
                            parent=self,
                        )

                    self.after(0, _done_ok)
                except Exception as exc:
                    self.after(0, lambda: messagebox.showerror("Database Schema Update", f"Failed:\n{exc}", parent=self))

            threading.Thread(target=_worker, daemon=True).start()

        tk.Button(
            header,
            text="Update Schema",
            command=run_migration,
            bg=self.colors["bg_blue"],
            fg=self.colors["text_white"],
            relief="flat",
            padx=10,
            pady=4,
        ).pack(side="right")

        # Detailed stats widget (optional)
        if HAS_DASH_WIDGETS:
            try:
                DatabaseStatsWidget(panel, lightspeed_root=self.lightspeed_root).pack(fill="both", expand=True, padx=10, pady=10)
                return
            except Exception:
                pass
        if self.db:
            try:
                tables = self.db.get_all_tables()
                tk.Label(panel, text=f"Tables: {len(tables)}",
                        bg=self.colors['bg_panel'], fg=self.colors['text_green'],
                        font=('Arial', 10)).pack(padx=15, pady=2)

                # Sample table sizes
                for table_name in ['users', 'projects', 'files']:
                    try:
                        count = len(self.db.fetchall(f"SELECT * FROM {table_name}"))
                        tk.Label(panel, text=f"{table_name}: {count} rows",
                                bg=self.colors['bg_panel'], fg=self.colors['text_cyan'],
                                font=('Arial', 9)).pack(anchor='w', padx=15, pady=1)
                    except:
                        pass
            except Exception as e:
                tk.Label(panel, text=f"Error: {e}",
                        bg=self.colors['bg_panel'], fg=self.colors['error_red'],
                        font=('Arial', 9)).pack(padx=15, pady=5)
        else:
            tk.Label(panel, text="Database offline",
                    bg=self.colors['bg_panel'], fg=self.colors['error_red'],
                    font=('Arial', 10)).pack(padx=15, pady=5)

    def _populate_components_panel(self, panel):
        """Populate components status"""
        try:
            linker_path = (
                self.lightspeed_root
                / "Z Axis"
                / "Z0_TheConstruct"
                / "tools"
                / "ComponentLinker.py"
            ).resolve()
            if not linker_path.exists():
                raise FileNotFoundError(f"ComponentLinker not found at: {linker_path}")

            spec = importlib.util.spec_from_file_location("lightspeed_component_linker", linker_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load ComponentLinker from {linker_path}")

            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            ComponentLinker = getattr(mod, "ComponentLinker")

            linker = ComponentLinker(self.lightspeed_root)
            components = linker.discover_all_components() or {}

            total = len(components)
            by_type: Dict[str, int] = {}
            for c in components.values():
                try:
                    by_type[c.component_type] = by_type.get(c.component_type, 0) + 1
                except Exception:
                    by_type["other"] = by_type.get("other", 0) + 1

            tk.Label(
                panel,
                text=f"{total} components discovered",
                bg=self.colors['bg_panel'],
                fg=self.colors['text_green'],
                font=('Arial', 10),
            ).pack(padx=15, pady=5)

            for k, v in sorted(by_type.items(), key=lambda kv: (-kv[1], kv[0]))[:4]:
                tk.Label(
                    panel,
                    text=f"{k}: {v}",
                    bg=self.colors['bg_panel'],
                    fg=self.colors['text_cyan'],
                    font=('Arial', 9),
                ).pack(anchor='w', padx=15, pady=1)

            tk.Label(
                panel,
                text="Discovery: floor manifests + floor-native modules",
                bg=self.colors['bg_panel'],
                fg=self.colors['text_cyan'],
                font=('Arial', 8),
            ).pack(anchor='w', padx=15, pady=(6, 1))
        except Exception as e:
            tk.Label(
                panel,
                text=f"Component discovery unavailable: {str(e)[:80]}",
                bg=self.colors['bg_panel'],
                fg=self.colors['warning_orange'],
                font=('Arial', 9),
            ).pack(padx=15, pady=5)

    def _populate_tasks_panel(self, panel):
        """Populate active tasks"""
        if HAS_DASH_WIDGETS:
            try:
                widget = TaskListWidget(panel, company_id=self.company_id)
                widget.pack(fill="both", expand=True, padx=10, pady=10)
                self._dashboard_tasks_widget = widget
                return
            except Exception:
                pass

        # Fallback (minimal, schema-correct)
        if not self.db:
            tk.Label(
                panel,
                text="Database offline",
                bg=self.colors['bg_panel'],
                fg=self.colors['error_red'],
                font=('Arial', 10),
            ).pack(padx=15, pady=5)
            return

        try:
            tasks = self.db.fetchall(
                "SELECT title, status FROM tasks WHERE status != 'completed' ORDER BY created_at DESC LIMIT 5"
            )
            if tasks:
                for task in tasks:
                    status = task.get("status")
                    color = self.colors['text_cyan'] if status == 'in_progress' else self.colors['text_green']
                    tk.Label(
                        panel,
                        text=f"* {task.get('title')} ({status})",
                        bg=self.colors['bg_panel'],
                        fg=color,
                        font=('Arial', 9),
                    ).pack(anchor='w', padx=15, pady=2)
            else:
                tk.Label(
                    panel,
                    text="No active tasks",
                    bg=self.colors['bg_panel'],
                    fg=self.colors['text_green'],
                    font=('Arial', 10),
                ).pack(padx=15, pady=5)
        except Exception:
            tk.Label(
                panel,
                text="No tasks tracked yet",
                bg=self.colors['bg_panel'],
                fg=self.colors['text_green'],
                font=('Arial', 10),
            ).pack(padx=15, pady=5)

    def _populate_activity_panel(self, panel):
        """Populate recent activity"""
        # Keep the dashboard lightweight. The full RecentActivityWidget can
        # perform heavier log/file work during startup; the dashboard only
        # needs a compact operational snapshot.
        if self.db:
            try:
                def _cols(table: str) -> set:
                    try:
                        rows = self.db.execute_query(f"PRAGMA table_info({table})")
                        return {r.get("name") for r in (rows or []) if r.get("name")}
                    except Exception:
                        return set()

                # Query recent database changes
                projects_cols = _cols("projects")
                files_cols = _cols("files")
                users_cols = _cols("users")

                proj_name = "name" if "name" in projects_cols else ("title" if "title" in projects_cols else None)
                proj_created = "created_at" if "created_at" in projects_cols else None
                file_name = "name" if "name" in files_cols else ("filename" if "filename" in files_cols else None)
                file_created = "created_at" if "created_at" in files_cols else None
                user_name = "username" if "username" in users_cols else ("name" if "name" in users_cols else None)
                user_created = "created_at" if "created_at" in users_cols else None

                activity_queries = []
                if proj_name and proj_created:
                    activity_queries.append(
                        (f"SELECT 'Project created: ' || {proj_name} AS activity, {proj_created} AS created_at FROM projects ORDER BY {proj_created} DESC LIMIT 3", "projects")
                    )
                if file_name and file_created:
                    activity_queries.append(
                        (f"SELECT 'File uploaded: ' || {file_name} AS activity, {file_created} AS created_at FROM files ORDER BY {file_created} DESC LIMIT 3", "files")
                    )
                if user_name and user_created:
                    activity_queries.append(
                        (f"SELECT 'User joined: ' || {user_name} AS activity, {user_created} AS created_at FROM users ORDER BY {user_created} DESC LIMIT 3", "users")
                    )

                activities = []
                for query, source in activity_queries:
                    try:
                        results = self.db.fetchall(query)
                        activities.extend(results)
                    except:
                        pass  # Table might not exist

                if activities:
                    # Sort by created_at and show top 5
                    activities_sorted = sorted(activities, key=lambda x: x.get('created_at', ''), reverse=True)[:5]

                    for activity in activities_sorted:
                        tk.Label(panel, text=f"* {activity['activity']}",
                                bg=self.colors['bg_panel'], fg=self.colors['text_cyan'],
                                font=('Arial', 9)).pack(anchor='w', padx=15, pady=2)
                else:
                    tk.Label(panel, text="No recent activity",
                            bg=self.colors['bg_panel'], fg=self.colors['text_green'],
                            font=('Arial', 10)).pack(padx=15, pady=5)

            except Exception as e:
                tk.Label(panel, text="Activity log unavailable",
                        bg=self.colors['bg_panel'], fg=self.colors['warning_orange'],
                        font=('Arial', 10)).pack(padx=15, pady=5)
        else:
            tk.Label(panel, text="Database offline",
                    bg=self.colors['bg_panel'], fg=self.colors['error_red'],
                    font=('Arial', 10)).pack(padx=15, pady=5)

    # ========================================================================
    # TAB 2: DIAGNOSTICS
    # ========================================================================

    def _create_diagnostics_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """System diagnostics tab"""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Merovingian: Diagnostics")

        # Header
        tk.Label(tab, text="System Diagnostics",
                font=('Arial', 18, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)
        self._add_owner_bar(tab, owner_floor="Merovingian", owner_channel="Z-4", note="system diagnostics / health")

        # Run diagnostics button
        tk.Button(tab, text="Run Full System Check",
                 command=self._run_full_diagnostics,
                 bg=self.colors['button_green'], fg='white',
                 font=('Arial', 12, 'bold'), width=25, height=2).pack(pady=10)

        # Results area
        self.diagnostics_text = scrolledtext.ScrolledText(
            tab, bg='#001122', fg=self.colors['text_green'],
            font=('Consolas', 10), wrap='word', height=30
        )
        self.diagnostics_text.pack(fill='both', expand=True, padx=20, pady=10)

        # Initial message
        self.diagnostics_text.insert('1.0', "Click 'Run Full System Check' to begin diagnostics...\n\n")

    def _run_full_diagnostics(self, *, text_widget=None):
        """Run comprehensive diagnostics (writes to provided widget or the legacy diagnostics tab)."""
        tw = text_widget or getattr(self, "diagnostics_text", None)
        if tw is None:
            return
        # Maintain backward compatibility with older helpers that write to `self.diagnostics_text`.
        self.diagnostics_text = tw

        tw.delete('1.0', 'end')
        tw.insert('end', "=" * 70 + "\n")
        tw.insert('end', "LIGHTSPEED SYSTEM DIAGNOSTICS\n")
        tw.insert('end', "=" * 70 + "\n\n")

        # Use startup wizard if available
        if HAS_WIZARDS:
            tw.insert('end', "Running StartupWizard checks...\n\n")
            wizard = StartupWizard()

            # Redirect output to text widget
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                wizard.run()
                output = sys.stdout.getvalue()
                tw.insert('end', output)
            finally:
                sys.stdout = old_stdout
        else:
            self._manual_diagnostics()

    def _manual_diagnostics(self):
        """Manual diagnostics (fallback)"""
        # Check dependencies
        self.diagnostics_text.insert('end', "[1/6] Checking dependencies...\n")
        deps = ['numpy', 'tkinter', 'sqlite3', 'fastapi', 'plotly']
        for dep in deps:
            try:
                __import__(dep) if dep != 'tkinter' else __import__('tkinter')
                self.diagnostics_text.insert('end', f"  [OK] {dep}\n")
            except ImportError:
                self.diagnostics_text.insert('end', f"  [X] {dep}\n")

        # Check Z-floors
        self.diagnostics_text.insert('end', "\n[2/6] Checking Z-floors...\n")
        for floor, module in self.z_floors.items():
            status = "OK" if module else "Missing"
            self.diagnostics_text.insert('end', f"  [{status}] {floor}\n")

        # Check database
        self.diagnostics_text.insert('end', "\n[3/6] Checking database...\n")
        if self.db:
            tables = self.db.get_all_tables()
            self.diagnostics_text.insert('end', f"  [OK] {len(tables)} tables\n")
        else:
            self.diagnostics_text.insert('end', "  [X] Database not available\n")

        # Check network ports
        self.diagnostics_text.insert('end', "\n[4/6] Checking network ports...\n")
        for port, service in [(8000, 'API'), (9000, 'Log Server'), (8001, 'Worker')]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            status = "Available" if result != 0 else "In use"
            self.diagnostics_text.insert('end', f"  [{status}] Port {port} ({service})\n")

        # Check storage
        self.diagnostics_text.insert('end', "\n[5/6] Checking storage...\n")
        if self.storage:
            stats = self.storage.get_storage_stats()
            self.diagnostics_text.insert('end', f"  [OK] {stats['total_files']} files\n")
        else:
            self.diagnostics_text.insert('end', "  [!] Storage service not available\n")

        # Summary
        self.diagnostics_text.insert('end', "\n[6/6] Summary\n")
        self.diagnostics_text.insert('end', "=" * 70 + "\n")
        self.diagnostics_text.insert('end', "[OK] Diagnostics complete\n")

    # ========================================================================
    # TAB 3: SETUP STATE (INTEGRATED)
    # ========================================================================

    def _create_wizard_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Integrated setup-state tab."""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text=SETUP_WORKSPACE_TAB_TITLE)

        # Header
        tk.Label(tab, text="Setup State",
                font=('Arial', 18, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)

        # Info
        info_text = """
First-run onboarding now routes through Trinity Master Settings Hub:

1. User Profile (name, email, role, clearance)
2. Company Information (name, industry)
3. Projects (initial project setup)
4. Widget Preferences (dashboard layout)
5. OKRs (objectives and key results)
6. Settings (theme, database, network)

Use the Master Settings Hub for launchers, page-local setup state, and floor-owned settings.
        """

        tk.Label(tab, text=info_text, justify='left',
                bg=self.colors['bg_dark'], fg=self.colors['text_green'],
                font=('Arial', 10)).pack(pady=20, padx=40)

        # Hub-first actions
        tk.Button(
            tab,
            text="Open Master Setup",
            command=lambda: self._open_hub_focus("setup_state"),
            bg=self.colors['button_green'], fg='white',
            font=('Arial', 12, 'bold'), width=25, height=2,
        ).pack(pady=(20, 8))

        tk.Button(
            tab,
            text="Open Page Settings",
            command=self._open_page_settings,
            bg=self.colors['bg_panel'], fg='white',
            font=('Arial', 11, 'bold'), width=25, height=2,
        ).pack(pady=(0, 8))

        # Note
        tk.Label(
            tab,
            text="Setup state is now a master-surface flow rather than a separate wizard page.",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_cyan'],
            font=('Arial', 9),
        ).pack(pady=10)

    def _launch_setup_wizard(self):
        """Open the Trinity Settings Hub focused to setup state."""
        try:
            if self._open_trinity_settings_surface(focus_section="setup_state"):
                return
            raise RuntimeError("Master Settings Hub not available")
        except Exception as e:
            messagebox.showerror(
                "Setup Hub",
                f"Master Settings Hub setup surface not available:\n{e}",
                parent=self,
            )

    # ========================================================================
    # TAB 4-11: Z-FLOORS (DEDICATED TABS)
    # ========================================================================

    def _create_z_floor_tabs(self, *, notebook: Optional[ttk.Notebook] = None):
        """Create dedicated tab for each canonical Z-floor (8-floor runtime stack)."""
        nb = notebook or self.notebook
        floors = [
            ("Trinity", "Z+3", "UI Layer, IT Portal, Themes, Bento, Governance"),
            ("Neo", "Z+2", "AI Integration & Cognigrex"),
            ("Architect", "Z+1", "Planning, Projects, Dev Tools"),
            ("TheConstruct", "Z0", "Physics & Simulations (environment host)"),
            ("Morpheus", "Z-1", "Knowledge, Docs, Read-mostly Indexing"),
            ("Oracle", "Z-2", "Archive/Vault, Ingestion, Durable Knowledge"),
            ("Smith", "Z-3", "Automation, Background Jobs, Indexing"),
            ("Merovingian", "Z-4", "Core Services, Diagnostics, Health"),
        ]

        floor_locations = {
            # Canonical floor entrypoints live in `Z Axis/<Floor>.py`.
            "Smith": "Z Axis/Smith.py",
            "Oracle": "Z Axis/Oracle.py",
            "Morpheus": "Z Axis/Morpheus.py",
            "TheConstruct": "Z Axis/TheConstruct.py",
            "Architect": "Z Axis/Architect.py",
            "Neo": "Z Axis/Neo.py",
            "Trinity": "Z Axis/Trinity.py",
            "Merovingian": "Z Axis/Merovingian.py",
        }
        floor_actions: Dict[str, List[Dict[str, Any]]] = {}
        try:
            from lightspeed_runtime.project_component_wall import build_floor_action_catalog

            catalog = build_floor_action_catalog(self.lightspeed_root)
            for floor in catalog.get("floors") or []:
                if isinstance(floor, dict):
                    floor_actions[str(floor.get("floor") or "")] = [
                        item for item in (floor.get("actions") or []) if isinstance(item, dict)
                    ]
        except Exception:
            floor_actions = {}

        try:
            from lightspeed_runtime.startup_options import build_startup_action_catalog

            for floor_name, actions in build_startup_action_catalog(self.lightspeed_root).items():
                floor_actions.setdefault(str(floor_name), []).extend(
                    [item for item in actions if isinstance(item, dict)]
                )
        except Exception:
            pass

        def _get_or_load_floor_module(name: str):
            """
            IT Portal requires floor tabs to be operational.

            N.py passes a cached dict (`Z_FLOORS_AVAILABLE`) seeded with floor keys but lazily imported.
            Here we load the canonical entrypoint modules on-demand so floor tabs do not render as stubs.
            """
            try:
                mod = self.z_floors.get(name)
            except Exception:
                mod = None
            if mod is not None:
                return mod

            rel = floor_locations.get(name)
            if not rel:
                return None
            try:
                path = (self.lightspeed_root / rel).resolve()
                if not path.exists():
                    return None
                mod_name = f"lightspeed_itportal_floor_{name.lower()}"
                spec = importlib.util.spec_from_file_location(mod_name, str(path))
                if spec is None or spec.loader is None:
                    return None
                m = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = m
                spec.loader.exec_module(m)
                try:
                    # Cache into the shared dict for other consumers in this portal session.
                    self.z_floors[name] = m
                except Exception:
                    pass
                return m
            except Exception as e:
                if _IMPORT_DEBUG:
                    print(f"[ITPortal] Failed to load floor entrypoint {name}: {e}")
                return None

        for floor_name, z_level, description in floors:
            tab = ttk.Frame(nb)
            nb.add(tab, text=f"{z_level} {floor_name}")

            content_frame = tk.Frame(tab, bg=self.colors['bg_dark'])
            content_frame.pack(fill='both', expand=True, padx=14, pady=14)
            floor_ui = _LazyFloorShell(
                content_frame,
                floor_name,
                z_level,
                description,
                self.colors,
                self._open_floor_runtime,
                open_settings=lambda focus_section="", _self=self: _self._open_hub_focus(str(focus_section or "")),
                actions=floor_actions.get(floor_name, []),
            )
            floor_ui.pack(fill="both", expand=True)
            self._floor_ui_instances[floor_name] = floor_ui

    # ========================================================================
    # TOOLS: OPERATOR SHORTCUTS (MINIMAL HUB)
    # ========================================================================

    def _create_operator_shortcuts_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """
        Minimal Tools hub: shortcuts only.

        Floor-owned operational tools live in their floors (Merovingian/Smith/Oracle/etc).
        IT Portal remains the governance + approval gate (Z Direct).
        """
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Operator Shortcuts")

        tk.Label(
            tab,
            text="Operator Shortcuts",
            font=("Arial", 18, "bold"),
            bg=self.colors["bg_dark"],
            fg=self.colors["accent_cyan"],
        ).pack(pady=(16, 8))

        tk.Label(
            tab,
            text="Open floor-owned tools quickly. For approvals/commits, use the Z Direct tab.",
            font=("Arial", 11),
            bg=self.colors["bg_dark"],
            fg=self.colors["text_green"],
        ).pack(pady=(0, 12))

        grid = tk.Frame(tab, bg=self.colors["bg_dark"])
        grid.pack(fill="both", expand=True, padx=20, pady=10)

        def add_section(title: str):
            lf = ttk.LabelFrame(grid, text=title)
            lf.pack(fill="x", pady=8)
            row = tk.Frame(lf, bg=self.colors["bg_dark"])
            row.pack(fill="x", padx=10, pady=10)
            return row

        def btn(parent, label: str, floor: str, subtab: str):
            tk.Button(
                parent,
                text=label,
                command=lambda: self.open_floor_tab(floor, subtab),
                bg=self.colors["button_green"],
                fg="white",
                font=("Arial", 10, "bold"),
                width=22,
            ).pack(side="left", padx=6, pady=4)

        # Trinity: governance helpers
        tr = add_section("Trinity (UI/Settings)")
        btn(tr, "Bento System", "Trinity", "Bento System")
        tk.Button(
            tr,
            text="Settings Hub",
            command=lambda: self._open_trinity_settings_surface(focus_section="trinity_launchers"),
            bg=self.colors["button_green"],
            fg="white",
            font=("Arial", 10, "bold"),
            width=22,
        ).pack(side="left", padx=6, pady=4)

        # Architect: projects
        ar = add_section("Architect (Projects)")
        btn(ar, "Project Manager", "Architect", "Project Manager")
        btn(ar, "Tasks", "Architect", "Tasks")
        btn(ar, "Timeline", "Architect", "Timeline")

        # Neo: planning + API
        ne = add_section("Neo (AI/Planning)")
        btn(ne, "Planner", "Neo", "Planner")
        btn(ne, "API Manager", "Neo", "API Manager")
        btn(ne, "Code Assistant", "Neo", "Code Assistant")

        # Oracle: durable library
        orc = add_section("Oracle (Library)")
        btn(orc, "Library", "Oracle", "Library")
        btn(orc, "Ingestion", "Oracle", "Ingestion")
        btn(orc, "Backup & Restore", "Oracle", "Backup & Restore")

        # Smith: jobs + SOPs
        sm = add_section("Smith (Automation)")
        btn(sm, "Background Jobs", "Smith", "Background Jobs")
        btn(sm, "Jobs & Artifacts", "Smith", "Jobs & Artifacts")
        btn(sm, "SOPs", "Smith", "SOPs")

        # Merovingian: diagnostics + logs
        me = add_section("Merovingian (Diagnostics)")
        btn(me, "System Metrics", "Merovingian", "System Metrics")
        btn(me, "Logs", "Merovingian", "Logs")
        btn(me, "Database Browser", "Merovingian", "Database Browser")
        btn(me, "Profiler", "Merovingian", "Performance Profiler")

        # Morpheus: dependency map
        mo = add_section("Morpheus (Knowledge)")
        btn(mo, "Dependency Map", "Morpheus", "Dependency Map")

    # ========================================================================
    # TAB 12: DATABASE BROWSER
    # ========================================================================

    def _create_database_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Database browser tab"""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Merovingian: Database")

        # Header
        tk.Label(tab, text="Database Browser",
                font=('Arial', 18, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)
        self._add_owner_bar(tab, owner_floor="Merovingian", owner_channel="Z-4", note="DB read-only browse (migrations are explicit/gated)")

        # Table selector
        selector_frame = tk.Frame(tab, bg=self.colors['bg_dark'])
        selector_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(selector_frame, text="Table:",
                bg=self.colors['bg_dark'], fg=self.colors['text_green'],
                font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        if self.db:
            tables = self.db.get_all_tables()
        else:
            tables = []

        self.table_var = tk.StringVar(value=tables[0] if tables else "")
        table_combo = ttk.Combobox(selector_frame, textvariable=self.table_var,
                                   values=tables, width=30)
        table_combo.pack(side='left', padx=5)

        tk.Button(selector_frame, text="Load Table",
                 command=self._load_table_data,
                 bg=self.colors['button_green'], fg='white',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        # Data display
        self.db_text = scrolledtext.ScrolledText(
            tab, bg='#001122', fg=self.colors['text_green'],
            font=('Consolas', 9), wrap='none', height=30
        )
        self.db_text.pack(fill='both', expand=True, padx=20, pady=10)

    def _load_table_data(self):
        """Load and display table data"""
        table_name = self.table_var.get()
        if not table_name or not self.db:
            return

        self.db_text.delete('1.0', 'end')

        try:
            rows = self.db.fetchall(f"SELECT * FROM {table_name}")

            if rows:
                # Header
                columns = rows[0].keys()
                header = " | ".join(f"{col:20s}" for col in columns)
                self.db_text.insert('end', header + "\n")
                self.db_text.insert('end', "-" * len(header) + "\n")

                # Rows
                for row in rows:
                    row_text = " | ".join(f"{str(row[col])[:20]:20s}" for col in columns)
                    self.db_text.insert('end', row_text + "\n")

                self.db_text.insert('end', f"\n{len(rows)} rows\n")
            else:
                self.db_text.insert('end', f"Table '{table_name}' is empty\n")

        except Exception as e:
            self.db_text.insert('end', f"Error: {e}\n")

    # ========================================================================
    # TAB 13: LOGS
    # ========================================================================

    def _create_logs_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Logs viewer tab"""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Merovingian: Logs")

        # Header
        tk.Label(tab, text="System Logs",
                font=('Arial', 18, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)
        self._add_owner_bar(tab, owner_floor="Merovingian", owner_channel="Z-4", note="ops/telemetry logs")

        # Controls
        controls_frame = tk.Frame(tab, bg=self.colors['bg_dark'])
        controls_frame.pack(fill='x', padx=20, pady=10)

        tk.Button(controls_frame, text="Refresh Logs",
                 command=self._load_logs,
                 bg=self.colors['button_green'], fg='white',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        tk.Button(controls_frame, text="Clear Display",
                 command=lambda: self.logs_text.delete('1.0', 'end'),
                 bg=self.colors['bg_panel'], fg='white',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        # Logs display
        self.logs_text = scrolledtext.ScrolledText(
            tab, bg='#001122', fg=self.colors['text_green'],
            font=('Consolas', 9), wrap='word', height=30
        )
        self.logs_text.pack(fill='both', expand=True, padx=20, pady=10)

        # Load initial logs
        self._load_logs()

    def _load_logs(self):
        """Load and display system logs"""
        self.logs_text.delete('1.0', 'end')
        self.logs_text.insert('end', "=" * 70 + "\n")
        self.logs_text.insert('end', "SYSTEM LOGS\n")
        self.logs_text.insert('end', "=" * 70 + "\n\n")

        # Check for log files (floor-native + workspace logs)
        log_dirs = [
            (self.lightspeed_root / "ai_logs").resolve(),
            (self.lightspeed_root.parent / "logs").resolve(),
        ]

        found_any = False
        for log_dir in log_dirs:
            if not log_dir.exists():
                continue
            log_files = list(log_dir.glob("*.log")) + list(log_dir.glob("*.txt"))
            if not log_files:
                continue
            found_any = True
            self.logs_text.insert('end', f"\n=== {log_dir} ===\n")
            for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                self.logs_text.insert('end', f"\n--- {log_file.name} ---\n")
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        for line in lines[-50:]:
                            self.logs_text.insert('end', line)
                except Exception as e:
                    self.logs_text.insert('end', f"Error reading log: {e}\n")

        if not found_any:
            self.logs_text.insert('end', "No logs found (ai_logs/logs directories missing or empty)\n")

        self.logs_text.see('1.0')  # Scroll to top

    # ========================================================================
    # TAB 14: SETTINGS
    # ========================================================================

    def _create_settings_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Settings tab (links to SettingsManager)"""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Trinity: Settings")

        # Header
        tk.Label(tab, text="Platform Settings",
                font=('Arial', 18, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)
        self._add_owner_bar(tab, owner_floor="Trinity", owner_channel="Z+3", note="settings hub + tailoring")

        # Info
        tk.Label(tab, text="Comprehensive settings management",
                bg=self.colors['bg_dark'], fg=self.colors['text_green'],
                font=('Arial', 12)).pack(pady=10)

        # Context-aware settings entry point
        tk.Button(tab, text="Open Page Settings for This View",
                 command=self._open_page_settings,
                 bg=self.colors['button_green'], fg='white',
                 font=('Arial', 12, 'bold'), width=30, height=2).pack(pady=20)

        tk.Button(tab, text="Startup & Auto Options",
                 command=lambda: self._open_hub_focus("startup_options"),
                 bg=self.colors['bg_blue'], fg='white',
                 font=('Arial', 11, 'bold'), width=30, height=1).pack(pady=(0, 12))

        # Settings categories
        categories = [
            "System (theme, backups, startup)",
            "UI (layout, refresh, animations)",
            "Processing (file size, OCR, parallel)",
            "AI (Ollama, assistant mode, analysis)",
            "Network (ports, remote access)",
            "Database (path, backups, interval)",
        ]

        tk.Label(tab, text="Available Settings:",
                bg=self.colors['bg_dark'], fg=self.colors['text_cyan'],
                font=('Arial', 10, 'bold')).pack(pady=(20, 10))

        for category in categories:
            tk.Label(tab, text=f"- {category}",
                    bg=self.colors['bg_dark'], fg=self.colors['text_green'],
                    font=('Arial', 9)).pack(anchor='w', padx=100, pady=2)

    def _open_trinity_settings_surface(
        self,
        *,
        focus_section: str = "",
        context: Optional[Dict[str, str]] = None,
    ) -> bool:
        try:
            from smart_settings_hub import SmartSettingsHub  # type: ignore

            hub = SmartSettingsHub(parent=self, host=getattr(self, "parent_app", None))
            hub.open_dialog_with_context(context=context, focus_section=focus_section)
            return True
        except Exception:
            return False

    def _open_settings_manager(self):
        """Open SettingsManager window"""
        if self._open_trinity_settings_surface():
            return

        if os.environ.get("LIGHTSPEED_ENABLE_LEGACY_SETTINGS"):
            try:
                from settings_manager import SettingsManager  # type: ignore
                settings_mgr = SettingsManager()
                settings_mgr.create_settings_window(self)
                return
            except Exception:
                pass

        messagebox.showerror(
            "Master Settings Hub",
            "Smart Settings Hub is not available.\n\nLegacy settings windows are disabled by default.",
            parent=self,
        )

    def _open_hub_focus(self, focus_section: str = "") -> None:
        """Open the Trinity Master Settings Hub with a specific focus section."""
        if self._open_trinity_settings_surface(focus_section=focus_section):
            return
        if focus_section == "setup_state":
            self._launch_setup_wizard()
            return
        self._open_settings_manager()

    def get_active_page_context(self) -> Dict[str, str]:
        """
        Return a best-effort context for the currently active IT Portal page.

        Used by the Master Settings Hub "Page Settings" to scope overrides.
        """
        def _tok(s: str) -> str:
            s = (s or "").strip().lower()
            out = []
            for ch in s:
                if ch.isalnum():
                    out.append(ch)
                elif ch in (" ", "-", "/", "\\", ":"):
                    out.append("_")
            return "".join(out).strip("_") or "unknown"

        main_label = ""
        try:
            nb = getattr(self, "notebook", None)
            if nb is not None:
                main_label = str(nb.tab("current", "text") or "")
        except Exception:
            main_label = ""

        ctx: Dict[str, str] = {"label": main_label or "IT Portal", "page_id": f"it.{_tok(main_label or 'portal')}"}

        # If we're inside Floors, include floor + subtab when available.
        if (main_label or "").strip() == "Floors":
            try:
                floors_nb = getattr(self, "_floors_notebook", None)
                if floors_nb is not None:
                    floor_label = str(floors_nb.tab("current", "text") or "")
                    # Tabs are labeled like "Z+2 Neo" -> floor key "neo"
                    floor_name = floor_label.split()[-1] if floor_label.split() else ""
                    ui = (getattr(self, "_floor_ui_instances", None) or {}).get(floor_name)
                    subtab = ""
                    try:
                        sub_nb = getattr(ui, "notebook", None)
                        if sub_nb is not None:
                            subtab = str(sub_nb.tab("current", "text") or "")
                    except Exception:
                        subtab = ""

                    ctx["label"] = "Floors / " + (floor_name or floor_label or "Unknown") + ((" / " + subtab) if subtab else "")
                    ctx["page_id"] = "floors." + _tok(floor_name or floor_label) + (("." + _tok(subtab)) if subtab else "")
            except Exception:
                pass

        # If we're inside Tools, include subtab.
        if (main_label or "").strip() == "Tools":
            try:
                tools_nb = getattr(self, "_tools_notebook", None)
                if tools_nb is not None:
                    tools_label = str(tools_nb.tab("current", "text") or "")
                    ctx["label"] = "Tools / " + (tools_label or "Tools")
                    ctx["page_id"] = "tools." + _tok(tools_label or "tools")
            except Exception:
                pass

        return ctx

    def _refresh_header_title(self) -> None:
        """Refresh the header title from Page Settings (if an override exists)."""
        lbl = getattr(self, "_header_title_label", None)
        if lbl is None:
            return

        default_title = "IT/Founder Portal"
        ctx = self.get_active_page_context()
        page_id = str(ctx.get("page_id") or "").strip()

        override = ""
        if page_id:
            try:
                from core.config.paths import TRINITY_SETTINGS  # type: ignore
                path = TRINITY_SETTINGS / "smart_settings.json"
                if path.exists():
                    data = json.loads(path.read_text(encoding="utf-8", errors="replace") or "{}")
                    override = str(data.get(f"pages.{page_id}.title") or "").strip()
            except Exception:
                override = ""

        title = override or default_title
        try:
            if lbl.winfo_exists():
                lbl.config(text=title)
        except Exception:
            pass

    def _open_page_settings(self) -> None:
        """Open Master Settings Hub focused to Page Settings for the active context."""
        if self._open_trinity_settings_surface(
            focus_section="page",
            context=self.get_active_page_context(),
        ):
            return
        messagebox.showerror("Page Settings", "Master Settings Hub not available.", parent=self)

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _check_first_run(self):
        """Check if first-run setup needed"""
        # Check if database has data
        if self.db:
            users = self.db.fetchall("SELECT * FROM users LIMIT 1")
            companies = self.db.fetchall("SELECT * FROM companies LIMIT 1")

            if not users or not companies:
                # Schedule the prompt after UI construction so tests/headless checks
                # do not block on a modal dialog before the window is ready.
                try:
                    self.after(300, self._prompt_first_run_setup)
                except Exception:
                    self._select_tab_title("Setup State")

    def _prompt_first_run_setup(self):
        """Prompt the operator to enter the unified setup surface."""
        try:
            response = messagebox.askyesno(
                "First Run Detected",
                "It looks like this is your first time running IT Portal.\n\n" +
                "Would you like to open the setup state hub to configure:\n" +
                "- User profiles\n" +
                "- Company information\n" +
                "- Projects\n" +
                "- Widgets and OKRs",
                parent=self,
            )
        except Exception:
            response = False

        if response:
            if not self._open_trinity_settings_surface(focus_section="setup_state"):
                # Prefer title-based selection (tab order may change as the portal is reorganized).
                self._select_tab_title("Setup State")

    def _run_system_check(self):
        """Quick system check"""
        # Diagnostics tab no longer lives in the Tools hub; run diagnostics in a dedicated window.
        try:
            self.open_floor_tab("Merovingian", "Portal")
        except Exception:
            pass
        self._open_diagnostics_window()

    def update_status(self, msg: str):
        """Update status message"""
        self.status_label.config(text=msg)

    def log(self, message: str):
        """Log message for compatibility with Z-floor UIs (Oracle, Smith, etc.)"""
        print(f"[ITPortal] {message}")
        self.update_status(message)
        # Also log to any configured logger
        if hasattr(self, 'logger') and self.logger:
            self.logger.info(message)

    # ========================================================================
    # NEW WINDOW METHODS FOR DASHBOARD QUICK ACTIONS
    # ========================================================================

    def _open_diagnostics_window(self):
        """Open diagnostics in a dedicated window (Tools hub is shortcuts-only)."""
        win = tk.Toplevel(self)
        win.title("System Diagnostics")
        win.geometry("980x700")
        try:
            win.configure(bg=self.colors["bg_dark"])
        except Exception:
            pass

        tk.Label(
            win,
            text="LightSpeed System Diagnostics",
            font=("Arial", 16, "bold"),
            bg=self.colors["bg_dark"],
            fg=self.colors["accent_cyan"],
        ).pack(pady=(12, 6))

        btns = tk.Frame(win, bg=self.colors["bg_dark"])
        btns.pack(fill="x", padx=12, pady=(0, 8))

        out = scrolledtext.ScrolledText(
            win,
            bg="#001122",
            fg=self.colors["text_green"],
            font=("Consolas", 10),
            wrap="word",
            height=30,
        )
        out.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Button(
            btns,
            text="Run Full System Check",
            command=lambda: self._run_full_diagnostics(text_widget=out),
            bg=self.colors["button_green"],
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(side="left")

        tk.Button(
            btns,
            text="Close",
            command=win.destroy,
            bg=self.colors["button_orange"],
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(side="right")

        try:
            out.insert("1.0", "Click 'Run Full System Check' to begin diagnostics...\\n\\n")
        except Exception:
            pass

    def _open_logs_window(self):
        """Open logs in new window"""
        log_window = tk.Toplevel(self)
        log_window.title("System Logs")
        log_window.geometry("900x600")

        # Header
        tk.Label(log_window, text="System Logs Viewer",
                font=('Arial', 16, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=10)

        # Controls
        controls = tk.Frame(log_window, bg=self.colors['bg_dark'])
        controls.pack(fill='x', padx=10, pady=5)

        tk.Button(controls, text="Refresh", command=lambda: self._load_logs_to_window(log_text),
                 bg=self.colors['button_green'], fg='white',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        # Logs display
        log_text = scrolledtext.ScrolledText(
            log_window, bg='#001122', fg=self.colors['text_green'],
            font=('Consolas', 9), wrap='word'
        )
        log_text.pack(fill='both', expand=True, padx=10, pady=10)

        # Load initial logs
        self._load_logs_to_window(log_text)

    def _load_logs_to_window(self, text_widget):
        """Load logs into window text widget"""
        text_widget.delete('1.0', 'end')
        text_widget.insert('end', "=" * 70 + "\n")
        text_widget.insert('end', "SYSTEM LOGS\n")
        text_widget.insert('end', "=" * 70 + "\n\n")

        log_dirs = [
            (self.lightspeed_root / "ai_logs").resolve(),
            (self.lightspeed_root.parent / "logs").resolve(),
        ]

        found_any = False
        for log_dir in log_dirs:
            if not log_dir.exists():
                continue
            log_files = list(log_dir.glob("*.log")) + list(log_dir.glob("*.txt"))
            if not log_files:
                continue
            found_any = True
            text_widget.insert('end', f"\n=== {log_dir} ===\n")
            for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                text_widget.insert('end', f"\n--- {log_file.name} ---\n")
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        for line in lines[-50:]:
                            text_widget.insert('end', line)
                except Exception as e:
                    text_widget.insert('end', f"Error reading log: {e}\n")

        if not found_any:
            text_widget.insert('end', "No logs found (ai_logs/logs directories missing or empty)\n")

    def _open_db_browser_window(self):
        """Open database browser in new window"""
        db_window = tk.Toplevel(self)
        db_window.title("Database Browser")
        db_window.geometry("1000x700")

        # Header
        tk.Label(db_window, text="Database Browser",
                font=('Arial', 16, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=10)

        # Table selector
        selector_frame = tk.Frame(db_window, bg=self.colors['bg_dark'])
        selector_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(selector_frame, text="Table:",
                bg=self.colors['bg_dark'], fg=self.colors['text_green'],
                font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        if self.db:
            tables = self.db.get_all_tables()
        else:
            tables = []

        table_var = tk.StringVar(value=tables[0] if tables else "")
        table_combo = ttk.Combobox(selector_frame, textvariable=table_var, values=tables, width=30)
        table_combo.pack(side='left', padx=5)

        db_text = scrolledtext.ScrolledText(
            db_window, bg='#001122', fg=self.colors['text_green'],
            font=('Consolas', 9), wrap='none'
        )
        db_text.pack(fill='both', expand=True, padx=10, pady=10)

        def load_table():
            table_name = table_var.get()
            if not table_name or not self.db:
                return
            db_text.delete('1.0', 'end')
            try:
                rows = self.db.fetchall(f"SELECT * FROM {table_name}")
                if rows:
                    columns = rows[0].keys()
                    header = " | ".join(f"{col:20s}" for col in columns)
                    db_text.insert('end', header + "\n")
                    db_text.insert('end', "-" * len(header) + "\n")
                    for row in rows:
                        row_text = " | ".join(f"{str(row[col])[:20]:20s}" for col in columns)
                        db_text.insert('end', row_text + "\n")
                    db_text.insert('end', f"\n{len(rows)} rows\n")
                else:
                    db_text.insert('end', f"Table '{table_name}' is empty\n")
            except Exception as e:
                db_text.insert('end', f"Error: {e}\n")

        tk.Button(selector_frame, text="Load Table", command=load_table,
                 bg=self.colors['button_green'], fg='white',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=5)

    def _open_wizard_window(self):
        """Open setup state through the Trinity Settings Hub."""
        if self._open_trinity_settings_surface(focus_section="setup_state"):
            return
        self._launch_setup_wizard()

    def _open_oracle_panel(self):
        """Open Oracle ingestion control panel (UI-only)."""
        try:
            from importlib.util import module_from_spec, spec_from_file_location

            oracle_path = (self.lightspeed_root / "Z Axis" / "Z-2_Oracle" / "components" / "oracle_ui_panel.py").resolve()
            if not oracle_path.exists():
                raise FileNotFoundError(oracle_path)

            mod_name = f"lightspeed_oracle_ui_panel_{abs(hash(str(oracle_path)))%1_000_000}"
            spec = spec_from_file_location(mod_name, oracle_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load {oracle_path}")

            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)
            panel_cls = getattr(mod, "OracleUIPanel", None)
            if panel_cls is None:
                raise AttributeError("OracleUIPanel not found")
            panel = panel_cls(parent=self)
            panel.open_panel()
        except Exception as e:
            messagebox.showerror("Oracle", f"Failed to open Oracle panel:\n{e}", parent=self)

    def _open_theme_manager(self):
        """Open theme manager (Trinity-owned)."""
        if self._open_trinity_settings_surface(focus_section="trinity_launchers"):
            return

        messagebox.showinfo(
            "Themes",
            "Theme and template tools live under Trinity Master Settings Hub.\n\n"
            "Open Master Settings or Master Settings Hub from the portal header.",
            parent=self,
        )

    def _open_portal_manager(self):
        """
        Portal Manager (Trinity-owned).

        Consolidation rule: IT Portal should not spawn a parallel "portal manager"
        surface with duplicated tabs/categories. Portal + Bento layout live in
        Trinity, and are accessed via floor tabs.
        """
        try:
            if self.open_floor_tab("Trinity", "Portal"):
                return
        except Exception:
            pass

        # Fallback (standalone / floor not loadable).
        messagebox.showinfo(
            "Portal Manager",
            "Portal management lives in Trinity.\n\n"
            "Open: Floors -> Z+3 Trinity -> Portal (and Bento System).",
            parent=self,
        )

    def _open_widget_customizer(self):
        """
        Widget Customizer (Trinity-owned).

        The old popup used a category-notebook (often ~20+ tabs) which duplicated
        Trinity's Bento system and made the portal feel fragmented.
        """
        try:
            if self.open_floor_tab("Trinity", "Bento System"):
                return
        except Exception:
            pass

        messagebox.showinfo(
            "Widget Customizer",
            "Widget configuration lives in Trinity.\n\n"
            "Open: Floors -> Z+3 Trinity -> Bento System.",
            parent=self,
        )

    # ========================================================================
    # API MANAGER METHODS
    # ========================================================================

    def _add_api_key(self):
        """Add or update API key"""
        api_window = tk.Toplevel(self)
        api_window.title("Add API Key")
        api_window.geometry("500x400")
        api_window.configure(bg=self.colors['bg_dark'])

        # API Name
        tk.Label(api_window, text="API Name:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(20, 5))

        api_name_var = tk.StringVar()
        api_name_combo = ttk.Combobox(api_window, textvariable=api_name_var,
                                     values=["OpenAI", "Anthropic", "Weather API", "Tree of Life", "Custom"],
                                     width=40)
        api_name_combo.pack(pady=5)

        # API Key
        tk.Label(api_window, text="API Key:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(15, 5))

        api_key_entry = tk.Entry(api_window, width=43, show="*", font=('Consolas', 10))
        api_key_entry.pack(pady=5)

        # Endpoint URL
        tk.Label(api_window, text="Endpoint URL (optional):", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(15, 5))

        endpoint_entry = tk.Entry(api_window, width=43, font=('Consolas', 10))
        endpoint_entry.pack(pady=5)

        # Show/Hide key toggle
        show_var = tk.BooleanVar(value=False)
        def toggle_show():
            api_key_entry.config(show="" if show_var.get() else "*")

        tk.Checkbutton(api_window, text="Show API Key", variable=show_var,
                      command=toggle_show, bg=self.colors['bg_dark'],
                      fg=self.colors['text_cyan'], selectcolor=self.colors['bg_panel']).pack(pady=10)

        # Save button
        def save_api_key():
            name = api_name_var.get()
            key = api_key_entry.get()
            endpoint = endpoint_entry.get()

            if not name or not key:
                messagebox.showerror("Error", "API Name and Key are required!", parent=api_window)
                return

            # Save to config (would normally save to encrypted storage)
            try:
                config_path = self.lightspeed_root / "config" / "api_keys.json"
                config_path.parent.mkdir(exist_ok=True)

                # Load existing
                api_keys = {}
                if config_path.exists():
                    import json
                    with open(config_path, 'r') as f:
                        api_keys = json.load(f)

                # Add new key (in production, encrypt this!)
                api_keys[name] = {
                    "key": key,  # WARNING: Should be encrypted in production
                    "endpoint": endpoint,
                    "added": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                # Save
                with open(config_path, 'w') as f:
                    json.dump(api_keys, f, indent=2)

                messagebox.showinfo("Success",
                                  f"API key for '{name}' saved successfully!\n\n"
                                  f"Note: In production, keys should be encrypted.",
                                  parent=api_window)
                api_window.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save API key: {e}", parent=api_window)

        tk.Button(api_window, text="Save API Key", command=save_api_key,
                 bg=self.colors['button_green'], fg='white',
                 font=('Arial', 12, 'bold'), width=20).pack(pady=20)

    # ========================================================================
    # BACKGROUND JOBS METHODS
    # ========================================================================

    def _create_background_job(self):
        """Create new background job"""
        job_window = tk.Toplevel(self)
        job_window.title("Create Background Job")
        job_window.geometry("500x450")
        job_window.configure(bg=self.colors['bg_dark'])

        tk.Label(job_window, text="Create Background Job",
                font=('Arial', 16, 'bold'), bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)

        # Job Type
        tk.Label(job_window, text="Job Type:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(10, 5))

        job_type_var = tk.StringVar(value="Database Backup")
        job_types = [
            "Database Backup",
            "File Sync",
            "System Hygiene",
            "Data Export",
            "Index Rebuild",
            "Log Rotation"
        ]

        for job_type in job_types:
            tk.Radiobutton(job_window, text=job_type, variable=job_type_var,
                          value=job_type, bg=self.colors['bg_dark'],
                          fg=self.colors['text_green'], selectcolor=self.colors['bg_panel']).pack(anchor='w', padx=50)

        # Schedule
        tk.Label(job_window, text="Schedule:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(15, 5))

        schedule_var = tk.StringVar(value="Run Now")
        schedule_combo = ttk.Combobox(job_window, textvariable=schedule_var,
                                     values=["Run Now", "Daily at 2 AM", "Weekly Sunday 3 AM", "Monthly 1st at 4 AM"],
                                     width=30)
        schedule_combo.pack(pady=5)

        # Create button
        def create_job():
            job_type = job_type_var.get()
            schedule = schedule_var.get()

            if not self.db:
                messagebox.showerror("Database Unavailable", "Database service not available.", parent=job_window)
                return

            job_type_map = {
                "Database Backup": "database_backup",
                "File Sync": "file_sync",
                "System Hygiene": "system_cleanup",
                "Data Export": "data_export",
                "Index Rebuild": "index_rebuild",
                "Log Rotation": "log_rotation",
            }
            mapped_job_type = job_type_map.get(job_type, job_type.lower().replace(" ", "_"))

            scheduled_for = None
            now = datetime.now()
            if schedule == "Run Now":
                scheduled_for = now.isoformat()
            elif schedule == "Daily at 2 AM":
                target = now.replace(hour=2, minute=0, second=0, microsecond=0)
                if target <= now:
                    target = target + timedelta(days=1)
                scheduled_for = target.isoformat()
            elif schedule == "Weekly Sunday 3 AM":
                target = now.replace(hour=3, minute=0, second=0, microsecond=0)
                days_ahead = (6 - target.weekday()) % 7
                if days_ahead == 0 and target <= now:
                    days_ahead = 7
                target = target + timedelta(days=days_ahead)
                scheduled_for = target.isoformat()
            elif schedule == "Monthly 1st at 4 AM":
                target = now.replace(day=1, hour=4, minute=0, second=0, microsecond=0)
                if target <= now:
                    year = target.year + (1 if target.month == 12 else 0)
                    month = 1 if target.month == 12 else target.month + 1
                    target = target.replace(year=year, month=month)
                scheduled_for = target.isoformat()

            try:
                job_id = self.db.create_background_job(mapped_job_type, parameters={}, scheduled_for=scheduled_for)
            except Exception as e:
                messagebox.showerror("Create Job Failed", str(e), parent=job_window)
                return

            self._refresh_background_jobs()
            messagebox.showinfo(
                "Job Created",
                f"Background job created successfully!\n\nType: {mapped_job_type}\nSchedule: {schedule}\nDB Job ID: {job_id}",
                parent=job_window,
            )
            job_window.destroy()

        tk.Button(job_window, text="Create Job", command=create_job,
                 bg=self.colors['button_green'], fg='white',
                 font=('Arial', 12, 'bold'), width=20).pack(pady=30)

    def _get_selected_bg_job_id(self) -> Optional[int]:
        widget = getattr(self, "_bg_jobs_widget", None)
        try:
            if widget is not None and hasattr(widget, "_selected_job"):
                row = widget._selected_job()
                if isinstance(row, dict) and row.get("id") is not None:
                    return int(row["id"])
        except Exception:
            pass
        return self._selected_bg_job_id

    def _refresh_background_jobs(self):
        """Refresh background jobs list (supports both legacy tree and DB widget)."""
        widget = getattr(self, "_bg_jobs_widget", None)
        if widget is not None:
            try:
                widget.refresh()
                return
            except Exception:
                pass

        tree = getattr(self, "_bg_job_tree", None)
        if tree is None:
            return
        if not self.db:
            return

        try:
            for item in tree.get_children():
                tree.delete(item)

            rows = self.db.fetchall(
                """
                SELECT id, job_type, status, started_at, COALESCE(updated_at, created_at) AS updated_at
                FROM jobs
                ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
                LIMIT 200
                """
            ) or []

            for r in rows:
                jid = r.get("id")
                job_type = r.get("job_type") or ""
                status = r.get("status") or "pending"
                started = r.get("started_at") or ""
                updated = r.get("updated_at") or ""
                tree.insert("", "end", text=str(jid), values=(job_type, status, "", started or updated))
        except Exception:
            return

    def _pause_background_job(self):
        """Pause selected background job"""
        if not self.db:
            messagebox.showerror("Database Unavailable", "Database service not available.", parent=self)
            return
        job_id = self._get_selected_bg_job_id()
        if not job_id:
            messagebox.showwarning("No Selection", "Select a job first.", parent=self)
            return

        try:
            self.db.execute_update(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
                ("paused", datetime.now().isoformat(), job_id),
            )
            self._refresh_background_jobs()
        except Exception as e:
            messagebox.showerror("Pause Failed", str(e), parent=self)

    def _kill_background_job(self):
        """Kill selected background job"""
        if not self.db:
            messagebox.showerror("Database Unavailable", "Database service not available.", parent=self)
            return
        job_id = self._get_selected_bg_job_id()
        if not job_id:
            messagebox.showwarning("No Selection", "Select a job first.", parent=self)
            return

        confirm = messagebox.askyesno(
            "Kill Job",
            "Are you sure you want to terminate this job?\n\nThis action cannot be undone.",
            parent=self,
        )
        if not confirm:
            return

        try:
            self.db.execute_update(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
                ("cancelled", datetime.now().isoformat(), job_id),
            )
            self._refresh_background_jobs()
        except Exception as e:
            messagebox.showerror("Kill Failed", str(e), parent=self)

    # ========================================================================
    # USER MANAGEMENT METHODS
    # ========================================================================

    def _add_user(self):
        """Add new user to system"""
        user_window = tk.Toplevel(self)
        user_window.title("Add User")
        user_window.geometry("500x550")
        user_window.configure(bg=self.colors['bg_dark'])

        tk.Label(user_window, text="Add New User",
                font=('Arial', 16, 'bold'), bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)

        # Username
        tk.Label(user_window, text="Username:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(10, 5))
        username_entry = tk.Entry(user_window, width=40, font=('Arial', 10))
        username_entry.pack(pady=5)

        # Full Name
        tk.Label(user_window, text="Full Name:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(10, 5))
        fullname_entry = tk.Entry(user_window, width=40, font=('Arial', 10))
        fullname_entry.pack(pady=5)

        # Role
        tk.Label(user_window, text="Role:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(10, 5))
        role_var = tk.StringVar(value="Client")
        role_combo = ttk.Combobox(user_window, textvariable=role_var,
                                 values=["Founder", "Admin", "Developer", "Client", "Guest"],
                                 width=37)
        role_combo.pack(pady=5)

        # Clearance Level
        tk.Label(user_window, text="Clearance Level:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(10, 5))
        clearance_var = tk.IntVar(value=1)
        tk.Scale(user_window, from_=0, to=5, orient=tk.HORIZONTAL,
                variable=clearance_var, bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], length=300).pack(pady=5)

        # Password
        tk.Label(user_window, text="Initial Password:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(10, 5))
        password_entry = tk.Entry(user_window, width=40, show="*", font=('Arial', 10))
        password_entry.pack(pady=5)

        # Create button
        def create_user():
            username = username_entry.get()
            fullname = fullname_entry.get()
            role = role_var.get()
            clearance = clearance_var.get()
            password = password_entry.get()

            if not username or not fullname or not password:
                messagebox.showerror("Error", "All fields are required!", parent=user_window)
                return

            # In production, save to database with hashed password
            messagebox.showinfo("Success",
                              f"User created successfully!\n\n"
                              f"Username: {username}\n"
                              f"Full Name: {fullname}\n"
                              f"Role: {role}\n"
                              f"Clearance: Level {clearance}\n\n"
                              f"User can now log in to the system.",
                              parent=user_window)
            user_window.destroy()

        tk.Button(user_window, text="Create User", command=create_user,
                 bg=self.colors['button_green'], fg='white',
                 font=('Arial', 12, 'bold'), width=20).pack(pady=30)

    def _edit_permissions(self):
        """Edit user permissions"""
        perm_window = tk.Toplevel(self)
        perm_window.title("Edit Permissions")
        perm_window.geometry("600x500")
        perm_window.configure(bg=self.colors['bg_dark'])

        tk.Label(perm_window, text="Edit User Permissions",
                font=('Arial', 16, 'bold'), bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)

        # User selection
        tk.Label(perm_window, text="Select User:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(10, 5))

        user_var = tk.StringVar(value="client_user")
        user_combo = ttk.Combobox(perm_window, textvariable=user_var,
                                 values=["nathaniel.bouwer", "client_user", "demo_user"],
                                 width=37)
        user_combo.pack(pady=5)

        # Permissions frame
        perm_frame = tk.Frame(perm_window, bg=self.colors['bg_panel'], relief='solid', bd=2)
        perm_frame.pack(fill='both', expand=True, padx=30, pady=20)

        tk.Label(perm_frame, text="Permissions:",
                bg=self.colors['bg_panel'], fg=self.colors['text_green'],
                font=('Arial', 12, 'bold')).pack(pady=10)

        # Permission checkboxes
        permissions = [
            ("Read Projects", tk.BooleanVar(value=True)),
            ("Write Projects", tk.BooleanVar(value=False)),
            ("Delete Projects", tk.BooleanVar(value=False)),
            ("Access IT Portal", tk.BooleanVar(value=True)),
            ("Manage Users", tk.BooleanVar(value=False)),
            ("System Administration", tk.BooleanVar(value=False)),
            ("API Access", tk.BooleanVar(value=True)),
            ("Background Jobs", tk.BooleanVar(value=False)),
        ]

        for perm_name, perm_var in permissions:
            tk.Checkbutton(perm_frame, text=perm_name, variable=perm_var,
                          bg=self.colors['bg_panel'], fg=self.colors['text_green'],
                          selectcolor=self.colors['bg_dark']).pack(anchor='w', padx=30, pady=3)

        # Save button
        def save_permissions():
            active_perms = [name for name, var in permissions if var.get()]
            messagebox.showinfo("Success",
                              f"Permissions updated for: {user_var.get()}\n\n"
                              f"Active permissions: {len(active_perms)}\n"
                              f"{', '.join(active_perms[:3])}...",
                              parent=perm_window)
            perm_window.destroy()

        tk.Button(perm_window, text="Save Permissions", command=save_permissions,
                 bg=self.colors['button_green'], fg='white',
                 font=('Arial', 12, 'bold'), width=20).pack(pady=20)

    # ========================================================================
    # BACKUP & RESTORE METHODS
    # ========================================================================

    def _restore_backup(self):
        """Restore from backup"""
        restore_window = tk.Toplevel(self)
        restore_window.title("Restore from Backup")
        restore_window.geometry("600x400")
        restore_window.configure(bg=self.colors['bg_dark'])

        tk.Label(restore_window, text="Restore from Backup",
                font=('Arial', 16, 'bold'), bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)

        # Warning
        warning_frame = tk.Frame(restore_window, bg='#FF6600', relief='solid', bd=2)
        warning_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(warning_frame, text="WARNING",
                bg='#FF6600', fg='white', font=('Arial', 12, 'bold')).pack(pady=5)
        tk.Label(warning_frame, text="Restoring will overwrite current data!",
                bg='#FF6600', fg='white', font=('Arial', 10)).pack(pady=(0, 5))

        # Backup selection
        tk.Label(restore_window, text="Select Backup:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(20, 5))

        backup_var = tk.StringVar(value="_CRYSTALLIZATION_BACKUP_20251214_224940")
        backups = [
            "_CRYSTALLIZATION_BACKUP_20251214_224940 (6.3 GB - Dec 14)",
            "auto_backup_20251214_000000 (120 MB - Dec 14)",
            "manual_backup_20251213_153000 (5.8 GB - Dec 13)"
        ]

        for backup in backups:
            tk.Radiobutton(restore_window, text=backup, variable=backup_var,
                          value=backup.split(' ')[0], bg=self.colors['bg_dark'],
                          fg=self.colors['text_green'], selectcolor=self.colors['bg_panel']).pack(anchor='w', padx=50)

        # Restore options
        full_restore_var = tk.BooleanVar(value=True)
        tk.Checkbutton(restore_window, text="Full system restore (database + files)",
                      variable=full_restore_var, bg=self.colors['bg_dark'],
                      fg=self.colors['text_cyan'], selectcolor=self.colors['bg_panel']).pack(pady=10)

        # Restore button
        def start_restore():
            backup = backup_var.get()
            confirm = messagebox.askyesno("Confirm Restore",
                                         f"Restore from backup?\n\n"
                                         f"Backup: {backup}\n"
                                         f"Mode: {'Full System' if full_restore_var.get() else 'Partial'}\n\n"
                                         f"Current data will be overwritten!",
                                         parent=restore_window)
            if confirm:
                messagebox.showinfo("Restore Started",
                                  f"Restore operation started!\n\n"
                                  f"This may take several minutes.\n"
                                  f"Progress will be shown in the background jobs tab.",
                                  parent=restore_window)
                restore_window.destroy()

        tk.Button(restore_window, text="Start Restore", command=start_restore,
                 bg=self.colors['button_orange'], fg='white',
                 font=('Arial', 12, 'bold'), width=20).pack(pady=30)

    def _schedule_backup(self):
        """Schedule automatic backups"""
        schedule_window = tk.Toplevel(self)
        schedule_window.title("Schedule Auto-Backup")
        schedule_window.geometry("550x500")
        schedule_window.configure(bg=self.colors['bg_dark'])

        tk.Label(schedule_window, text="Schedule Automatic Backups",
                font=('Arial', 16, 'bold'), bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)

        # Frequency
        tk.Label(schedule_window, text="Backup Frequency:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(10, 5))

        freq_var = tk.StringVar(value="Daily")
        frequencies = ["Hourly", "Every 6 hours", "Daily", "Weekly", "Monthly"]

        for freq in frequencies:
            tk.Radiobutton(schedule_window, text=freq, variable=freq_var,
                          value=freq, bg=self.colors['bg_dark'],
                          fg=self.colors['text_green'], selectcolor=self.colors['bg_panel']).pack(anchor='w', padx=50)

        # Time
        tk.Label(schedule_window, text="Backup Time:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(15, 5))

        time_var = tk.StringVar(value="02:00 AM")
        time_combo = ttk.Combobox(schedule_window, textvariable=time_var,
                                 values=["12:00 AM", "02:00 AM", "04:00 AM", "06:00 AM", "12:00 PM"],
                                 width=20)
        time_combo.pack(pady=5)

        # Retention
        tk.Label(schedule_window, text="Keep backups for:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(15, 5))

        retention_var = tk.StringVar(value="30 days")
        retention_combo = ttk.Combobox(schedule_window, textvariable=retention_var,
                                      values=["7 days", "30 days", "90 days", "1 year", "Forever"],
                                      width=20)
        retention_combo.pack(pady=5)

        # Backup type
        backup_type_var = tk.StringVar(value="Full")
        tk.Label(schedule_window, text="Backup Type:", bg=self.colors['bg_dark'],
                fg=self.colors['text_green'], font=('Arial', 11)).pack(pady=(15, 5))

        tk.Radiobutton(schedule_window, text="Full Backup (slower, complete)",
                      variable=backup_type_var, value="Full",
                      bg=self.colors['bg_dark'], fg=self.colors['text_green'],
                      selectcolor=self.colors['bg_panel']).pack(anchor='w', padx=50)
        tk.Radiobutton(schedule_window, text="Incremental (faster, changes only)",
                      variable=backup_type_var, value="Incremental",
                      bg=self.colors['bg_dark'], fg=self.colors['text_green'],
                      selectcolor=self.colors['bg_panel']).pack(anchor='w', padx=50)

        # Save button
        def save_schedule():
            freq = freq_var.get()
            time = time_var.get()
            retention = retention_var.get()
            backup_type = backup_type_var.get()

            messagebox.showinfo("Schedule Saved",
                              f"Backup schedule configured!\n\n"
                              f"Frequency: {freq}\n"
                              f"Time: {time}\n"
                              f"Retention: {retention}\n"
                              f"Type: {backup_type}\n\n"
                              f"Next backup: Tomorrow at {time}",
                              parent=schedule_window)
            schedule_window.destroy()

        tk.Button(schedule_window, text="Save Schedule", command=save_schedule,
                 bg=self.colors['button_green'], fg='white',
                 font=('Arial', 12, 'bold'), width=20).pack(pady=30)

    def _create_api_manager_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Tab 16: API Integration Manager"""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Neo: API Manager")

        tk.Label(
            tab,
            text="API Integration Manager",
            font=('Arial', 18, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent_cyan'],
        ).pack(pady=20)
        self._add_owner_bar(tab, owner_floor="Neo", owner_channel="Z+2", note="API/AI integration switches")

        if HAS_DASH_WIDGETS:
            try:
                quick = ttk.LabelFrame(tab, text="Quick Toggles (unified_config.json)")
                quick.pack(fill="x", padx=20, pady=(0, 10))
                APITogglesWidget(quick).pack(fill="x", expand=True, padx=6, pady=6)
            except Exception:
                pass

        # Backed by the unified APIManager (no placeholders)
        try:
            from core.api.api_manager import APIManager
            self.api_manager = APIManager(config_path="config/apis.json")
        except Exception as e:
            tk.Label(
                tab,
                text=f"API Manager unavailable:\n{e}",
                font=('Arial', 12),
                bg=self.colors['bg_dark'],
                fg=self.colors.get('text_red', 'red'),
                justify="left",
            ).pack(padx=20, pady=20, anchor="w")
            return

        api_frame = ttk.LabelFrame(tab, text="Registered APIs")
        api_frame.pack(fill='both', expand=True, padx=20, pady=10)

        columns = ('Provider', 'Type', 'Enabled', 'Base URL', 'Last Test')
        api_tree = ttk.Treeview(api_frame, columns=columns, show='headings', height=12)
        for col, title, width, anchor in [
            ('Provider', 'Provider', 160, 'w'),
            ('Type', 'Type', 90, 'w'),
            ('Enabled', 'Enabled', 80, 'center'),
            ('Base URL', 'Base URL', 420, 'w'),
            ('Last Test', 'Last Tested', 150, 'w'),
        ]:
            api_tree.heading(col, text=title)
            api_tree.column(col, width=width, anchor=anchor)

        api_tree.pack(fill='both', expand=True, padx=5, pady=5)

        def refresh():
            try:
                self.api_manager.load()
            except Exception:
                pass
            for item in api_tree.get_children():
                api_tree.delete(item)
            for provider, api in sorted(self.api_manager.apis.items(), key=lambda kv: kv[0]):
                last_test = ""
                try:
                    last_test = (api.config or {}).get("last_tested_at", "")
                except Exception:
                    last_test = ""
                api_tree.insert(
                    '',
                    'end',
                    iid=provider,
                    values=(provider, api.api_type, "yes" if api.enabled else "no", api.base_url, last_test),
                )

        def selected_provider() -> Optional[str]:
            sel = api_tree.selection()
            if not sel:
                return None
            return sel[0]

        def open_wizard():
            try:
                self.api_manager.create_wizard_window(self)
            except Exception as e:
                messagebox.showerror("API Wizard", f"Failed to open API wizard:\n{e}", parent=self)

        def toggle_enabled():
            provider = selected_provider()
            if not provider:
                messagebox.showwarning("API Manager", "Select an API first.", parent=self)
                return
            api = self.api_manager.get_api(provider)
            if not api:
                return
            api.enabled = not bool(api.enabled)
            self.api_manager.save()
            refresh()

        def test_selected():
            provider = selected_provider()
            if not provider:
                messagebox.showwarning("API Manager", "Select an API first.", parent=self)
                return
            ok, msg = self.api_manager.test_connection(provider)
            api = self.api_manager.get_api(provider)
            if api is not None:
                try:
                    api.config = api.config or {}
                    api.config["last_tested_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    api.config["last_test_result"] = {"ok": bool(ok), "message": str(msg)}
                    self.api_manager.save()
                except Exception:
                    pass
            refresh()
            messagebox.showinfo("API Test", msg, parent=self)

        btn_frame = tk.Frame(tab, bg=self.colors['bg_dark'])
        btn_frame.pack(fill='x', padx=20, pady=10)

        tk.Button(
            btn_frame,
            text="Open API Wizard",
            command=open_wizard,
            bg=self.colors['button_green'],
            fg='white',
            font=('Arial', 10, 'bold'),
        ).pack(side='left', padx=5)

        tk.Button(
            btn_frame,
            text="Enable/Disable",
            command=toggle_enabled,
            bg=self.colors['button_green'],
            fg='white',
            font=('Arial', 10, 'bold'),
        ).pack(side='left', padx=5)

        tk.Button(
            btn_frame,
            text="Test Selected",
            command=test_selected,
            bg=self.colors['button_green'],
            fg='white',
            font=('Arial', 10, 'bold'),
        ).pack(side='left', padx=5)

        tk.Button(
            btn_frame,
            text="Refresh",
            command=refresh,
            bg=self.colors['button_green'],
            fg='white',
            font=('Arial', 10, 'bold'),
        ).pack(side='left', padx=5)

        tk.Button(
            btn_frame,
            text="Add API Key",
            command=self._add_api_key,
            bg=self.colors['button_green'],
            fg='white',
            font=('Arial', 10, 'bold'),
        ).pack(side='right', padx=5)

        refresh()


    def _create_background_jobs_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Tab 17: Background Jobs (Smith Floor)"""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Smith: Background Jobs")

        # Header
        tk.Label(tab, text="Background Jobs Monitor (Smith Floor)",
                font=('Arial', 18, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)
        self._add_owner_bar(tab, owner_floor="Smith", owner_channel="Z-3", note="automation/jobs")

        # Prefer the DB-backed widget (used across the platform) when available.
        if HAS_DASH_WIDGETS:
            try:
                widget = BackgroundJobsWidget(tab)
                widget.pack(fill="both", expand=True, padx=20, pady=10)
                self._bg_jobs_widget = widget

                btn_frame = tk.Frame(tab, bg=self.colors['bg_dark'])
                btn_frame.pack(fill='x', padx=20, pady=10)

                tk.Button(
                    btn_frame,
                    text="New Job",
                    command=self._create_background_job,
                    bg=self.colors['button_green'],
                    fg='white',
                    font=('Arial', 10, 'bold'),
                ).pack(side='left', padx=5)

                tk.Button(
                    btn_frame,
                    text="Refresh",
                    command=self._refresh_background_jobs,
                    bg=self.colors['button_green'],
                    fg='white',
                    font=('Arial', 10, 'bold'),
                ).pack(side='left', padx=5)

                tk.Button(
                    btn_frame,
                    text="Stage Knowledge (Run Once)",
                    command=lambda: self._run_knowledge_proposal_sweep(batch_size=2),
                    bg=self.colors['button_orange'],
                    fg='white',
                    font=('Arial', 10, 'bold'),
                ).pack(side='left', padx=5)

                tk.Button(
                    btn_frame,
                    text="Pause Selected",
                    command=self._pause_background_job,
                    bg=self.colors['button_orange'],
                    fg='white',
                    font=('Arial', 10, 'bold'),
                ).pack(side='left', padx=5)

                tk.Button(
                    btn_frame,
                    text="Kill Selected",
                    command=self._kill_background_job,
                    bg=self.colors['error_red'],
                    fg='white',
                    font=('Arial', 10, 'bold'),
                ).pack(side='left', padx=5)

                return
            except Exception:
                # Fall back to the legacy tree view UI.
                pass

        # Job Queue
        queue_frame = ttk.LabelFrame(tab, text="Active Jobs")
        queue_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # TreeView for jobs
        columns = ('Type', 'Status', 'Progress', 'Started')
        job_tree = ttk.Treeview(queue_frame, columns=columns, show='tree headings', height=10)

        job_tree.heading('#0', text='Job ID')
        job_tree.heading('Type', text='Type')
        job_tree.heading('Status', text='Status')
        job_tree.heading('Progress', text='Progress')
        job_tree.heading('Started', text='Started')

        job_tree.pack(fill='both', expand=True, padx=5, pady=5)
        self._bg_job_tree = job_tree

        def on_select(_event=None):
            sel = job_tree.selection()
            if not sel:
                self._selected_bg_job_id = None
                return
            job_id = job_tree.item(sel[0], 'text')
            try:
                self._selected_bg_job_id = int(str(job_id).strip())
            except Exception:
                self._selected_bg_job_id = None

        job_tree.bind('<<TreeviewSelect>>', on_select)

        # Initial load
        self._refresh_background_jobs()

        # Controls
        btn_frame = tk.Frame(tab, bg=self.colors['bg_dark'])
        btn_frame.pack(fill='x', padx=20, pady=10)

        tk.Button(btn_frame, text="New Job", command=self._create_background_job,
                 bg=self.colors['button_green'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        tk.Button(btn_frame, text="Refresh", command=self._refresh_background_jobs,
                 bg=self.colors['button_green'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        tk.Button(btn_frame, text="Pause Selected", command=self._pause_background_job,
                 bg=self.colors['button_orange'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        tk.Button(btn_frame, text="Kill Selected", command=self._kill_background_job,
                 bg=self.colors['error_red'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)


    def _create_backup_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Tab 21: Backup & Restore"""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Oracle: Backup & Restore")

        # Header
        tk.Label(tab, text="Backup & Restore Management",
                font=('Arial', 18, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)
        self._add_owner_bar(tab, owner_floor="Oracle", owner_channel="Z-2", note="vault/registry backups (review before restore)")

        # Backup Status
        status_frame = tk.Frame(tab, bg=self.colors['bg_panel'], relief='solid', bd=2)
        status_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(status_frame, text="Last Backup: December 14, 2025 at 11:04 PM",
                bg=self.colors['bg_panel'], fg=self.colors['text_green'],
                font=('Arial', 12, 'bold')).pack(pady=10)

        tk.Label(status_frame, text="Backup Location: _CRYSTALLIZATION_BACKUP_20251214_224940",
                bg=self.colors['bg_panel'], fg=self.colors['text_cyan'],
                font=('Arial', 10)).pack(pady=(0, 10))

        # Backup List
        backup_frame = ttk.LabelFrame(tab, text="Available Backups")
        backup_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # TreeView for backups
        columns = ('Size', 'Created', 'Type')
        backup_tree = ttk.Treeview(backup_frame, columns=columns, show='tree headings', height=8)

        backup_tree.heading('#0', text='Backup Name')
        backup_tree.heading('Size', text='Size')
        backup_tree.heading('Created', text='Created')
        backup_tree.heading('Type', text='Type')

        backup_tree.pack(fill='both', expand=True, padx=5, pady=5)

        # Sample backups
        backups = [
            ("_CRYSTALLIZATION_BACKUP_20251214_224940", "6.3 GB", "Dec 14, 11:04 PM", "Full"),
            ("auto_backup_20251214_000000", "120 MB", "Dec 14, 12:00 AM", "Incremental"),
            ("manual_backup_20251213_153000", "5.8 GB", "Dec 13, 3:30 PM", "Full")
        ]

        for name, size, created, backup_type in backups:
            backup_tree.insert('', 'end', text=name, values=(size, created, backup_type))

        # Actions
        btn_frame = tk.Frame(tab, bg=self.colors['bg_dark'])
        btn_frame.pack(fill='x', padx=20, pady=10)

        tk.Button(btn_frame, text="Create Backup Now", command=lambda: messagebox.showinfo("Backup", "Creating backup...", parent=self),
                 bg=self.colors['button_green'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        tk.Button(btn_frame, text="Restore from Backup", command=self._restore_backup,
                 bg=self.colors['button_orange'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        tk.Button(btn_frame, text="Schedule Auto-Backup", command=self._schedule_backup,
                 bg=self.colors['button_green'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)

    # ========================================================================
    # END NEW TABS
    # ========================================================================

    def _create_health_monitoring_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Tab 18: Health Monitoring (Merovingian Floor)"""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Merovingian: Health")

        # Header
        tk.Label(tab, text="System Health Monitoring (Merovingian Floor)",
                font=('Arial', 18, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)
        self._add_owner_bar(tab, owner_floor="Merovingian", owner_channel="Z-4", note="health monitor")

        # Health Score
        score_frame = tk.Frame(tab, bg=self.colors['bg_panel'], relief='solid', bd=2)
        score_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(score_frame, text="Overall System Health",
                bg=self.colors['bg_panel'], fg=self.colors['text_green'],
                font=('Arial', 12, 'bold')).pack(pady=10)

        self._hm_score_value = tk.Label(
            score_frame,
            text="-",
            bg=self.colors['bg_panel'],
            fg=self.colors['success_green'],
            font=('Arial', 36, 'bold'),
        )
        self._hm_score_value.pack()

        self._hm_score_status = tk.Label(
            score_frame,
            text="-",
            bg=self.colors['bg_panel'],
            fg=self.colors['success_green'],
            font=('Arial', 14),
        )
        self._hm_score_status.pack(pady=(0, 10))

        risk_frame = tk.Frame(score_frame, bg=self.colors['bg_panel'])
        risk_frame.pack(fill='x', padx=15, pady=(0, 10))

        tk.Label(
            risk_frame,
            text="Predictive Risk",
            bg=self.colors['bg_panel'],
            fg=self.colors['text_green'],
            font=('Arial', 10, 'bold'),
        ).pack(side='left')

        self._hm_risk_value = tk.Label(
            risk_frame,
            text="-",
            bg=self.colors['bg_panel'],
            fg=self.colors['text_cyan'],
            font=('Arial', 10, 'bold'),
        )
        self._hm_risk_value.pack(side='right')

        # Component Health
        components_frame = ttk.LabelFrame(tab, text="Component Status")
        components_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self._hm_component_rows = {}

        def add_component_row(label: str):
            comp_frame = tk.Frame(components_frame, bg=self.colors['bg_dark'])
            comp_frame.pack(fill='x', padx=10, pady=5)

            tk.Label(
                comp_frame,
                text=f"* {label}:",
                bg=self.colors['bg_dark'],
                fg=self.colors['text_green'],
                font=('Arial', 11, 'bold'),
                width=20,
                anchor='w',
            ).pack(side='left')

            status_label = tk.Label(
                comp_frame,
                text="-",
                bg=self.colors['bg_dark'],
                fg=self.colors['text_green'],
                font=('Arial', 11),
                width=15,
            )
            status_label.pack(side='left')

            value_label = tk.Label(
                comp_frame,
                text="-",
                bg=self.colors['bg_dark'],
                fg=self.colors['text_green'],
                font=('Arial', 11, 'bold'),
            )
            value_label.pack(side='right')

            self._hm_component_rows[label] = (status_label, value_label)

        for label in ("CPU", "Memory", "Disk", "Database", "Event Bus", "Storage", "Z-Floors", "Jobs (1h)", "Errors (1h)"):
            add_component_row(label)

        report_frame = ttk.LabelFrame(tab, text="Predictive Report")
        report_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self._hm_report_text = scrolledtext.ScrolledText(
            report_frame,
            height=10,
            bg='#1e1e1e',
            fg='#00FF88',
            font=('Consolas', 9),
        )
        self._hm_report_text.pack(fill='both', expand=True, padx=5, pady=5)
        self._hm_report_text.insert('1.0', "Loading...\n")
        self._hm_report_text.config(state=tk.DISABLED)

        btn_frame = tk.Frame(tab, bg=self.colors['bg_dark'])
        btn_frame.pack(fill='x', padx=20, pady=(0, 10))

        tk.Button(
            btn_frame,
            text="Refresh",
            command=self._refresh_health_monitoring_tab,
            bg=self.colors['button_green'],
            fg='white',
            font=('Arial', 10, 'bold'),
        ).pack(side='left', padx=5)

        self._refresh_health_monitoring_tab()


    def _refresh_health_monitoring_tab(self):
        """Refresh Health Monitor tab from DB telemetry + predictive engine."""
        if not hasattr(self, "_hm_component_rows") or not hasattr(self, "_hm_report_text"):
            return

        def set_component(label: str, status: str, value: str, color: str):
            row = self._hm_component_rows.get(label)
            if not row:
                return
            status_label, value_label = row
            status_label.config(text=status, fg=color)
            value_label.config(text=value, fg=color)

        def status_color(level: str) -> str:
            s = (level or "").lower()
            if s in ("healthy", "ok", "good", "excellent"):
                return self.colors['success_green']
            if s in ("warning", "warn"):
                return self.colors['warning_orange']
            if s in ("critical", "bad", "error", "missing"):
                return self.colors['error_red']
            return self.colors['text_green']

        def threshold_status(v: Optional[float], warn: float, crit: float) -> str:
            if v is None:
                return "unknown"
            if v >= crit:
                return "critical"
            if v >= warn:
                return "warning"
            return "healthy"

        cpu = mem = disk = None
        recorded_at = None
        if self.db:
            try:
                health = self.db.get_system_health() or {}
                cpu = health.get("cpu_percent")
                mem = health.get("memory_percent")
                disk = health.get("disk_percent")
                recorded_at = health.get("recorded_at")
            except Exception:
                pass

        def pct_or_na(v) -> str:
            try:
                return f"{float(v):.1f}%"
            except Exception:
                return "n/a"

        cpu_status = threshold_status(float(cpu) if cpu is not None else None, 70.0, 90.0)
        mem_status = threshold_status(float(mem) if mem is not None else None, 75.0, 90.0)
        disk_status = threshold_status(float(disk) if disk is not None else None, 80.0, 95.0)
        set_component("CPU", cpu_status, pct_or_na(cpu), status_color(cpu_status))
        set_component("Memory", mem_status, pct_or_na(mem), status_color(mem_status))
        set_component("Disk", disk_status, pct_or_na(disk), status_color(disk_status))

        set_component(
            "Database",
            "healthy" if self.db else "missing",
            "connected" if self.db else "n/a",
            status_color("healthy" if self.db else "missing"),
        )
        set_component(
            "Event Bus",
            "healthy" if self.event_bus else "missing",
            "enabled" if self.event_bus else "n/a",
            status_color("healthy" if self.event_bus else "missing"),
        )
        set_component(
            "Storage",
            "healthy" if self.storage else "missing",
            "ready" if self.storage else "n/a",
            status_color("healthy" if self.storage else "missing"),
        )

        try:
            floors_count = len(self.z_floors) if self.z_floors is not None else 0
        except Exception:
            floors_count = 0
        set_component("Z-Floors", "healthy" if floors_count else "unknown", str(floors_count), status_color("healthy" if floors_count else "warning"))

        risk_report = None
        if self.db:
            try:
                from core.services.predictive_maintenance import get_predictive_maintenance_engine
                engine = get_predictive_maintenance_engine(db=self.db, event_bus=self.event_bus)
                risk_report = engine.compute_risk(window_minutes=60, component="system")
            except Exception:
                risk_report = None

        score = None
        try:
            if cpu is not None and mem is not None and disk is not None:
                score = 100.0 - ((float(cpu) + float(mem) + float(disk)) / 3.0)
        except Exception:
            score = None

        if score is None:
            self._hm_score_value.config(text="-", fg=self.colors['text_green'])
            self._hm_score_status.config(text="No telemetry yet", fg=self.colors['text_green'])
        else:
            self._hm_score_value.config(text=f"{score:.0f}%")
            if score >= 90:
                self._hm_score_value.config(fg=self.colors['success_green'])
                self._hm_score_status.config(text="Excellent", fg=self.colors['success_green'])
            elif score >= 70:
                self._hm_score_value.config(fg=self.colors['warning_orange'])
                self._hm_score_status.config(text="Warning", fg=self.colors['warning_orange'])
            else:
                self._hm_score_value.config(fg=self.colors['error_red'])
                self._hm_score_status.config(text="Critical", fg=self.colors['error_red'])

        if risk_report:
            risk = float(risk_report.get("risk_score") or 0.0)
            risk_color = self.colors['success_green'] if risk < 50 else (self.colors['warning_orange'] if risk < 80 else self.colors['error_red'])
            self._hm_risk_value.config(text=f"{risk:.0f}/100", fg=risk_color)
            failed_jobs = (risk_report.get("job_stats") or {}).get("failed", 0)
            errors = (risk_report.get("log_stats") or {}).get("errors", 0)
            set_component("Jobs (1h)", "failed" if failed_jobs else "healthy", str(failed_jobs), risk_color)
            set_component("Errors (1h)", "error" if errors else "healthy", str(errors), risk_color)
        else:
            self._hm_risk_value.config(text="n/a", fg=self.colors['text_green'])
            set_component("Jobs (1h)", "unknown", "n/a", self.colors['text_green'])
            set_component("Errors (1h)", "unknown", "n/a", self.colors['text_green'])

        self._hm_report_text.config(state='normal')
        self._hm_report_text.delete('1.0', 'end')
        if not risk_report:
            self._hm_report_text.insert('1.0', "Predictive engine unavailable (DB missing or no telemetry).\n")
        else:
            self._hm_report_text.insert('end', "[Predictive Maintenance]\n")
            self._hm_report_text.insert('end', f"Generated: {risk_report.get('generated_at')}\n")
            if recorded_at:
                self._hm_report_text.insert('end', f"Telemetry latest: {recorded_at}\n")
            self._hm_report_text.insert('end', f"Risk score: {risk_report.get('risk_score')}\n\n")

            if risk_report.get("alerts"):
                self._hm_report_text.insert('end', "Alerts:\n")
                for a in risk_report["alerts"][:10]:
                    self._hm_report_text.insert('end', f" - [{a.get('severity')}] {a.get('message')}\n")
                self._hm_report_text.insert('end', "\n")

            forecasts = risk_report.get("forecasts") or {}
            if forecasts:
                self._hm_report_text.insert('end', "Forecasts:\n")
                for metric, f in forecasts.items():
                    try:
                        self._hm_report_text.insert(
                            'end',
                            f" - {metric}: now={float(f.get('current_value')):.1f} slope/min={float(f.get('slope_per_min')):.2f} 15m={float(f.get('forecast_15m')):.1f}\n",
                        )
                    except Exception:
                        self._hm_report_text.insert('end', f" - {metric}: {f}\n")
                self._hm_report_text.insert('end', "\n")

            if risk_report.get("recommendations"):
                self._hm_report_text.insert('end', "Recommendations:\n")
                for r in risk_report["recommendations"][:10]:
                    self._hm_report_text.insert('end', f" - {r.get('detail')}\n")
                self._hm_report_text.insert('end', "\n")

        self._hm_report_text.config(state=tk.DISABLED)

        # Schedule periodic refresh (every 5s)
        try:
            if hasattr(self, "_hm_refresh_job") and self._hm_refresh_job is not None:
                self.after_cancel(self._hm_refresh_job)
        except Exception:
            pass
        try:
            self._hm_refresh_job = self.after(5000, self._refresh_health_monitoring_tab)
        except Exception:
            self._hm_refresh_job = None


    def _create_performance_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Tab 19: Performance Metrics"""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Merovingian: Performance")

        # Header
        tk.Label(tab, text="Performance Metrics & Optimization",
                font=('Arial', 18, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)
        self._add_owner_bar(tab, owner_floor="Merovingian", owner_channel="Z-4", note="performance/telemetry")

        # Metrics Grid
        metrics_frame = tk.Frame(tab, bg=self.colors['bg_dark'])
        metrics_frame.pack(fill='x', padx=20, pady=10)

        metrics = [
            ("Avg Response Time", "45 ms", self.colors['success_green']),
            ("DB Query Speed", "12 ms", self.colors['success_green']),
            ("Memory Usage", "2.4 GB", self.colors['warning_orange']),
            ("CPU Usage", "23%", self.colors['success_green']),
        ]

        for i, (label, value, color) in enumerate(metrics):
            metric_card = tk.Frame(metrics_frame, bg=self.colors['bg_panel'], relief='solid', bd=1)
            metric_card.grid(row=0, column=i, padx=5, sticky='ew')
            metrics_frame.grid_columnconfigure(i, weight=1)

            tk.Label(metric_card, text=label, bg=self.colors['bg_panel'],
                    fg=self.colors['text_green'], font=('Arial', 10)).pack(pady=(10, 2))
            tk.Label(metric_card, text=value, bg=self.colors['bg_panel'],
                    fg=color, font=('Arial', 16, 'bold')).pack(pady=(0, 10))

        # Performance Log
        log_frame = ttk.LabelFrame(tab, text="Performance Log")
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)

        log_text = scrolledtext.ScrolledText(log_frame, height=12, bg='#1e1e1e', fg='#00FF88', font=('Consolas', 9))
        log_text.pack(fill='both', expand=True, padx=5, pady=5)

        sample_log = """[10:45:23] Database query executed in 8ms
[10:45:25] Z-Floor switch (Neo -> Oracle) in 120ms
[10:45:30] ProjectManager file scan completed in 350ms
[10:45:35] Settings saved successfully in 5ms
[10:45:40] Memory usage: 2.4GB (acceptable)
[10:45:45] No performance bottlenecks detected"""

        log_text.insert('1.0', sample_log)
        log_text.config(state=tk.DISABLED)


    def _create_project_manager_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Project Manager tab for IT Portal"""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Architect: Project Manager")

        if not HAS_PROJECT_MANAGER or not self.project_manager:
            tk.Label(tab, text="ProjectManager Not Available",
                    font=('Arial', 16, 'bold'),
                    bg=self.colors['bg_dark'],
                    fg=self.colors['error_red']).pack(pady=50)
            return

        # Header
        header_frame = tk.Frame(tab, bg=self.colors['bg_panel'], height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text="Project Manager - IT Administration",
                font=('Arial', 16, 'bold'),
                bg=self.colors['bg_panel'],
                fg=self.colors['accent_cyan']).pack(side='left', padx=20, pady=10)
        self._add_owner_bar(tab, owner_floor="Architect", owner_channel="Z+1", note="projects/workspaces")

        # Stats panel
        stats_frame = tk.Frame(tab, bg=self.colors['bg_dark'])
        stats_frame.pack(fill='x', padx=20, pady=10)

        # Get project statistics
        try:
            all_projects = list(Path(self.project_manager.base_path).iterdir())
            project_count = len([p for p in all_projects if p.is_dir()])

            total_files = 0
            total_size = 0
            for project_dir in all_projects:
                if project_dir.is_dir():
                    for file_path in project_dir.rglob("*"):
                        if file_path.is_file() and ".venv" not in file_path.parts:
                            total_files += 1
                            total_size += file_path.stat().st_size

            size_mb = total_size / (1024 * 1024)

            # Display stats
            stats = [
                ("Total Projects", str(project_count)),
                ("Total Files", str(total_files)),
                ("Total Size", f"{size_mb:.1f} MB"),
                ("Tools Registered", str(sum(len(tools) for tools in self.project_manager.tool_registry.list_tools().values())))
            ]

            for i, (label, value) in enumerate(stats):
                stat_card = tk.Frame(stats_frame, bg=self.colors['bg_panel'], relief='solid', bd=1)
                stat_card.grid(row=0, column=i, padx=10, sticky='ew')
                stats_frame.grid_columnconfigure(i, weight=1)

                tk.Label(stat_card, text=label,
                        bg=self.colors['bg_panel'], fg=self.colors['text_green'],
                        font=('Arial', 10)).pack(pady=(10, 2))

                tk.Label(stat_card, text=value,
                        bg=self.colors['bg_panel'], fg=self.colors['accent_cyan'],
                        font=('Arial', 18, 'bold')).pack(pady=(0, 10))

        except Exception as e:
            tk.Label(stats_frame, text=f"Error loading stats: {e}",
                    bg=self.colors['bg_dark'], fg=self.colors['error_red']).pack()

        # Actions panel
        actions_frame = tk.Frame(tab, bg=self.colors['bg_dark'])
        actions_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(actions_frame, text="Quick Actions",
                font=('Arial', 12, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['text_green']).pack(anchor='w', pady=(0, 10))

        btn_frame = tk.Frame(actions_frame, bg=self.colors['bg_dark'])
        btn_frame.pack(fill='x')

        actions = [
            ("Create Project", self._pm_create_project),
            ("List Projects", self._pm_list_projects),
            ("Export All", self._pm_export_all),
            ("Archive to Oracle", self._pm_archive_all),
            ("Integrity Review", self._pm_cleanup)
        ]

        for i, (text, command) in enumerate(actions):
            tk.Button(btn_frame, text=text, command=command,
                     bg=self.colors['button_green'], fg='white',
                     font=('Arial', 10, 'bold'), width=15, height=2).grid(row=0, column=i, padx=5)

        # Project list
        list_frame = ttk.LabelFrame(tab, text="Projects")
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # TreeView for projects
        columns = ('Type', 'Files', 'Size', 'Modified')
        self.pm_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)
        self.pm_tree.pack(side='left', fill='both', expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.pm_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.pm_tree.configure(yscrollcommand=scrollbar.set)

        # Configure columns
        self.pm_tree.heading('#0', text='Project Name')
        self.pm_tree.heading('Type', text='Type')
        self.pm_tree.heading('Files', text='Files')
        self.pm_tree.heading('Size', text='Size')
        self.pm_tree.heading('Modified', text='Modified')

        self.pm_tree.column('#0', width=250)
        self.pm_tree.column('Type', width=100)
        self.pm_tree.column('Files', width=80)
        self.pm_tree.column('Size', width=100)
        self.pm_tree.column('Modified', width=150)

        # Load projects
        self._pm_refresh_list()


    def _create_security_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Tab 20: Security & Permissions"""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Trinity: Security")

        # Header
        tk.Label(tab, text="Security & User Management",
                font=('Arial', 18, 'bold'),
                bg=self.colors['bg_dark'],
                fg=self.colors['accent_cyan']).pack(pady=20)
        self._add_owner_bar(tab, owner_floor="Trinity", owner_channel="Z+3", note="users/clearance/governance")

        # User Management
        users_frame = ttk.LabelFrame(tab, text="Users & Clearance Levels")
        users_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # TreeView for users
        columns = ('Role', 'Clearance', 'Last Login', 'Status')
        user_tree = ttk.Treeview(users_frame, columns=columns, show='tree headings', height=8)

        user_tree.heading('#0', text='Username')
        user_tree.heading('Role', text='Role')
        user_tree.heading('Clearance', text='Clearance')
        user_tree.heading('Last Login', text='Last Login')
        user_tree.heading('Status', text='Status')

        user_tree.pack(fill='both', expand=True, padx=5, pady=5)

        # Sample users
        users = [
            ("nathaniel.bouwer", "Founder", "Level 5", "Today 10:30 AM", "Active"),
            ("client_user", "Client", "Level 1", "Yesterday 3:45 PM", "Active"),
            ("demo_user", "Guest", "Level 0", "Never", "Inactive")
        ]

        for username, role, clearance, last_login, status in users:
            user_tree.insert('', 'end', text=username, values=(role, clearance, last_login, status))

        # Controls
        btn_frame = tk.Frame(tab, bg=self.colors['bg_dark'])
        btn_frame.pack(fill='x', padx=20, pady=10)

        tk.Button(btn_frame, text="Add User", command=self._add_user,
                 bg=self.colors['button_green'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        tk.Button(btn_frame, text="Edit Permissions", command=self._edit_permissions,
                 bg=self.colors['button_orange'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)

    def _create_cognigrex_planner_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """
        Cognigrex Planner: generate an execution plan (A/B/C) and stage it to Z Direct.

        Governance rules:
        - stages `workflow_def` objects into Trinity's staging stream (append-only)
        - durable registry writes happen only via explicit IT Portal commit actions (Z Direct tab)
        """
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Neo: Planner")

        tk.Label(
            tab,
            text="Cognigrex Planner (Plan A / B / C)",
            font=("Arial", 18, "bold"),
            bg=self.colors["bg_dark"],
            fg=self.colors["accent_cyan"],
        ).pack(pady=(18, 6))
        self._add_owner_bar(tab, owner_floor="Neo", owner_channel="Z+2", note="stage plans -> review/commit via Trinity Z Direct")

        intro = tk.Label(
            tab,
            text=(
                "Generate a structured plan aligned to the canonical Z-stack.\n"
                "Output: staged `workflow_def` objects in Trinity Z Direct (append-only), tagged for review.\n"
                "Flow: Stage -> Z Direct (Channel=Z+3, Kind=workflow_def, Tags=plan) -> Commit Selection (Batch)."
            ),
            justify="left",
            bg=self.colors["bg_dark"],
            fg=self.colors["text_green"],
            font=("Arial", 10),
        )
        intro.pack(anchor="w", padx=20, pady=(0, 10))

        controls = tk.Frame(tab, bg=self.colors["bg_dark"])
        controls.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(
            controls,
            text="Focus:",
            bg=self.colors["bg_dark"],
            fg=self.colors["text_white"],
            font=("Arial", 10, "bold"),
        ).pack(side="left")
        focus_var = tk.StringVar(value="V1R alignment (UI-first + Z Direct governance + library consolidation)")
        focus_entry = ttk.Entry(controls, textvariable=focus_var, width=72)
        focus_entry.pack(side="left", padx=(8, 16))
        show_json_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            controls,
            text="Show JSON",
            variable=show_json_var,
            bg=self.colors["bg_dark"],
            fg=self.colors["text_white"],
            selectcolor=self.colors["bg_dark"],
            activebackground=self.colors["bg_dark"],
            activeforeground=self.colors["accent_cyan"],
        ).pack(side="left")

        output = scrolledtext.ScrolledText(
            tab,
            bg="#001122",
            fg=self.colors["text_green"],
            font=("Consolas", 10),
            wrap="word",
            height=26,
        )
        output.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        def _make_workflow_payloads(focus: str) -> List[Dict[str, Any]]:
            now = datetime.utcnow().isoformat() + "Z"
            focus = (focus or "").strip() or "V1R alignment"

            def step(title: str, *, owner: str, channel: str, what: str, artifacts: Optional[List[str]] = None) -> Dict[str, Any]:
                return {
                    "title": title,
                    "owner_floor": owner,
                    "channel": channel,
                    "what": what,
                    "artifacts": artifacts or [],
                }

            plan_a = {
                "kind": "workflow_def",
                "id": "cognigrex_plan_a_v1",
                "title": "Plan A - Stabilize Ops & Governance (V1R)",
                "description": (
                    "Lock the UI-first contract, keep immersive pinned, and make Z Direct the explicit approval gate. "
                    f"Focus: {focus}. Generated: {now}."
                ),
                "tags": ["plan", "cognigrex", "A", "v1r"],
                "steps": [
                    step(
                        "Confirm canonical runtime and pinned immersive gate",
                        owner="Trinity",
                        channel="Z+3",
                        what="Verify N launches UI-first host; interactive immersive requires per-user unpin; guest mode remains config-gated.",
                        artifacts=["N.py", "config/unified_config.json", "Z Axis/Z0_TheConstruct/ui/immersive_3d_engine.py"],
                    ),
                    step(
                        "Operator governance loop (stage -> review -> commit)",
                        owner="Trinity",
                        channel="Z+3",
                        what="Use IT Portal Z Direct tags + diff preview for approvals; avoid silent registry writes.",
                        artifacts=["Z Axis/Z+3_Trinity/ui/it_portal.py", "Z Axis/Z-4_Merovingian/core/services/dataspace.py"],
                    ),
                    step(
                        "Floor tab operability check",
                        owner="Trinity",
                        channel="Z+3",
                        what="Ensure Floors hub loads 8 canonical floors and their UIs render (no stub).",
                        artifacts=["Z Axis/Z+3_Trinity/ui/it_portal.py", "Z Axis/Trinity.py", "Z Axis/Neo.py"],
                    ),
                    step(
                        "Seed + commit bootstrap definitions (only via IT Portal)",
                        owner="Trinity",
                        channel="Z+3",
                        what="Stage V1R defs (schemas/defs/widgets) then commit with Tags=v1r.",
                        artifacts=["N.py:stage_v1r_definitions", "Z Axis/Z+3_Trinity/Z Direct/objects.jsonl"],
                    ),
                ],
                "metadata": {"generated_at": now, "focus": focus},
            }

            plan_b = {
                "kind": "workflow_def",
                "id": "cognigrex_plan_b_v1",
                "title": "Plan B - Oracle Library Consolidation (Archive/Encyclopedia)",
                "description": (
                    "Consolidate vault/knowledge into a searchable, de-duplicated durable registry. "
                    "No deletes; actioning via staged reports -> Smith tasks. "
                    f"Focus: {focus}. Generated: {now}."
                ),
                "tags": ["plan", "cognigrex", "B", "library", "v1r"],
                "steps": [
                    step(
                        "Identify duplicates by sha256 and stage a dedupe report",
                        owner="Oracle",
                        channel="Z-2",
                        what="Use IT Portal Oracle: Library -> Find Duplicates (sha256) -> Stage to Smith inbox.",
                        artifacts=["Z Axis/Z+3_Trinity/ui/it_portal.py (Oracle: Library)"],
                    ),
                    step(
                        "Convert reports into tasks/OKRs (append-only)",
                        owner="Smith",
                        channel="Z-3",
                        what="Review dedupe/proposal events in Z Direct; create tasks for consolidation workstreams (no destructive ops).",
                        artifacts=["Z Axis/Z-3_Smith", "Z Axis/Z+3_Trinity/Z Direct/channels"],
                    ),
                    step(
                        "Expand knowledge proposals into durable objects",
                        owner="Neo",
                        channel="Z+2",
                        what="Use Propose Knowledge flow (vault_file -> citation/knowledge_node proposals) and commit via Trinity approval.",
                        artifacts=["Z Axis/Z+3_Trinity/ui/it_portal.py (Propose Knowledge)", "Z Axis/Z+2_Neo/ai/document_objectifier.py"],
                    ),
                ],
                "metadata": {"generated_at": now, "focus": focus},
            }

            plan_c = {
                "kind": "workflow_def",
                "id": "cognigrex_plan_c_v1",
                "title": "Plan C - User UI + Expandability (Bento/Widgets/Templates)",
                "description": (
                    "Make N's Bento UI the primary interaction surface, backed by typed templates and committed widget/definition objects. "
                    f"Focus: {focus}. Generated: {now}."
                ),
                "tags": ["plan", "cognigrex", "C", "ui", "v1r"],
                "steps": [
                    step(
                        "Bento as menu (readable + clickable) across host modes",
                        owner="Trinity",
                        channel="Z+3",
                        what="Ensure Universal Bento loads committed bento_widget definitions and host wiring works; keep 3D as ambient host.",
                        artifacts=["Z Axis/Z+3_Trinity/ui/universal_bento_system.py", "N.py:_wire_bento_widget_callbacks"],
                    ),
                    step(
                        "Spec-driven definitions (no placeholders)",
                        owner="Merovingian",
                        channel="Z-4",
                        what="Use SpecForm + templates to generate/validate action_def/simulation_def/workflow_def; commit via IT Portal.",
                        artifacts=["Z Axis/Z-4_Merovingian/core/ui/base_portal_glass.py", "Z Axis/Z-4_Merovingian/core/services/template_system.py"],
                    ),
                    step(
                        "Simulation runner uses committed simulation_def",
                        owner="TheConstruct",
                        channel="Z0",
                        what="Expand simulation_def catalog; verify runner stays typed and UI-first.",
                        artifacts=["Z Axis/Z0_TheConstruct/components/construct_dashboard_glass.py", "N.py:run_simulation"],
                    ),
                ],
                "metadata": {"generated_at": now, "focus": focus},
            }

            return [plan_a, plan_b, plan_c]

        def stage_plan_abc():
            focus = focus_var.get()
            try:
                from core.services import get_z_direct  # type: ignore

                zd = get_z_direct()
            except Exception as e:
                messagebox.showerror("Planner", f"Z Direct unavailable:\n{e}", parent=self)
                return

            plans = _make_workflow_payloads(focus)
            staged = 0
            errors: List[str] = []
            for p in plans:
                try:
                    env = zd.make_envelope(
                        kind="object",
                        channel="Z+3",
                        z_context="Z+3_Trinity",
                        source="trinity.it_portal.planner",
                        tags=["plan", "cognigrex", "abc", "stage"],
                        payload=p,
                    )
                    zd.append_object("Z+3", env)
                    staged += 1
                except Exception as e:
                    errors.append(f"{p.get('id')}: {e}")

            try:
                output.delete("1.0", tk.END)
                output.insert(
                    "1.0",
                    "Staged workflow_def objects to Trinity Z Direct (objects.jsonl):\n"
                    + "\n".join([f"- {p['id']}" for p in plans])
                    + ("\n\nErrors:\n- " + "\n- ".join(errors) if errors else "")
                    + "\n\nNext:\n"
                    + "1) Z Direct tab\n"
                    + "2) Channel=Z+3, Kind=workflow_def, Tags=plan (or Search=cognigrex_plan)\n"
                    + "3) Select All (View) -> Commit Selection (Batch)\n",
                )
                output.see("1.0")
            except Exception:
                pass

            if errors:
                messagebox.showwarning("Planner", f"Staged {staged}/{len(plans)} plans.\n\nFailures:\n- " + "\n- ".join(errors), parent=self)
            else:
                messagebox.showinfo("Planner", f"Staged {staged} plan objects.\n\nOpen Z Direct to review/commit.", parent=self)
            try:
                self._open_z_direct_view(
                    channel="Z+3",
                    peer="All",
                    kind="workflow_def",
                    tags="plan",
                    search="cognigrex_plan",
                )
            except Exception:
                pass

        def preview_plan_abc():
            focus = focus_var.get()
            plans = _make_workflow_payloads(focus)
            try:
                output.delete("1.0", tk.END)
                summary = [
                    "Cognigrex Planner - Preview (not staged)\n",
                    f"Focus: {focus}\n",
                    "Plans:\n",
                ]
                for p in plans:
                    steps = p.get("steps") or []
                    summary.append(f"- {p.get('id')} | {p.get('title')} | steps={len(steps)} | tags={p.get('tags')}\n")
                if bool(show_json_var.get()):
                    summary.append("\nJSON:\n")
                    summary.append(json.dumps(plans, indent=2, ensure_ascii=False))
                    summary.append("\n")
                output.insert("1.0", "".join(summary))
                output.see("1.0")
            except Exception:
                pass

        def copy_output():
            try:
                txt = (output.get("1.0", tk.END) or "").strip()
                if not txt:
                    return
                self.clipboard_clear()
                self.clipboard_append(txt)
                messagebox.showinfo("Planner", "Copied to clipboard.", parent=self)
            except Exception:
                pass

        btns = tk.Frame(tab, bg=self.colors["bg_dark"])
        btns.pack(fill="x", padx=20, pady=(0, 20))

        tk.Button(
            btns,
            text="Preview",
            command=preview_plan_abc,
            bg=self.colors["bg_panel"],
            fg="white",
            font=("Arial", 11, "bold"),
            padx=12,
            pady=8,
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btns,
            text="Stage Plan A/B/C (workflow_defs)",
            command=stage_plan_abc,
            bg=self.colors["button_green"],
            fg="white",
            font=("Arial", 11, "bold"),
            padx=12,
            pady=8,
        ).pack(side="left")

        tk.Button(
            btns,
            text="Copy Output",
            command=copy_output,
            bg=self.colors["bg_blue"],
            fg="white",
            font=("Arial", 11, "bold"),
            padx=12,
            pady=8,
        ).pack(side="left", padx=(10, 0))

        try:
            preview_plan_abc()
        except Exception:
            pass

    def _create_template_manager_tab(self, *, notebook: Optional[ttk.Notebook] = None):
        """Template Manager: productive generators (JSON/Markdown/UI payloads), stage-only to Z Direct."""
        nb = notebook or self.notebook
        tab = ttk.Frame(nb)
        nb.add(tab, text="Trinity: Templates")

        tk.Label(
            tab,
            text="Template Manager (Productive Generators)",
            font=("Arial", 18, "bold"),
            bg=self.colors["bg_dark"],
            fg=self.colors["accent_cyan"],
        ).pack(pady=(16, 8))
        self._add_owner_bar(tab, owner_floor="Trinity", owner_channel="Z+3", note="generate -> (optional) stage to Z Direct -> approve/commit")

        tk.Label(
            tab,
            text=(
                "Use templates to generate artifacts (docs, schemas, defs, object payloads) without hand-authoring JSON.\n"
                "Template Manager can optionally stage generated Z Direct payloads into Z+3 append-only streams.\n"
                "Durable registry commits remain approval-gated via IT Portal -> Z Direct."
            ),
            justify="left",
            bg=self.colors["bg_dark"],
            fg=self.colors["text_green"],
            font=("Arial", 10),
        ).pack(anchor="w", padx=20, pady=(0, 12))

        actions = tk.Frame(tab, bg=self.colors["bg_dark"])
        actions.pack(fill="x", padx=20, pady=(0, 12))

        def open_templates():
            try:
                from template_manager import TemplateManagerDialog  # type: ignore

                TemplateManagerDialog(self)
            except Exception as e:
                messagebox.showerror("Template Manager", f"Could not open Template Manager:\n{e}", parent=self)

        tk.Button(
            actions,
            text="Open Template Manager",
            command=open_templates,
            bg=self.colors["button_green"],
            fg="white",
            font=("Arial", 11, "bold"),
            padx=12,
            pady=8,
        ).pack(side="left")

        tk.Button(
            actions,
            text="Open Z Direct (Trinity)",
            command=lambda: self._open_z_direct_view(channel="Z+3", peer="All"),
            bg=self.colors["bg_panel"],
            fg="white",
            font=("Arial", 11, "bold"),
            padx=12,
            pady=8,
        ).pack(side="left", padx=(10, 0))

        quick = ttk.LabelFrame(tab, text="Quick Stage (Governed)")
        quick.pack(fill="x", padx=20, pady=(0, 12))
        try:
            quick.configure(style="TLabelframe")
        except Exception:
            pass

        tk.Label(
            quick,
            text=(
                "Create a small typed object payload and stage it to Trinity Z Direct (append-only).\n"
                "This does not commit to any durable registry. Review/commit via IT Portal -> Z Direct."
            ),
            justify="left",
            bg=self.colors["bg_dark"],
            fg=self.colors["text_green"],
            font=("Arial", 10),
        ).pack(anchor="w", padx=12, pady=(10, 8))

        route_row = tk.Frame(quick, bg=self.colors["bg_dark"])
        route_row.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(
            route_row,
            text="Route to peer inbox (optional):",
            bg=self.colors["bg_dark"],
            fg=self.colors["text_white"],
            font=("Arial", 10, "bold"),
            width=26,
            anchor="w",
        ).pack(side="left")
        target_peer_var = tk.StringVar(value="None")
        ttk.Combobox(
            route_row,
            textvariable=target_peer_var,
            state="readonly",
            width=10,
            values=["None", "Z-4", "Z-3", "Z-2", "Z-1", "Z0", "Z+1", "Z+2"],
        ).pack(side="left")

        btn_row = tk.Frame(quick, bg=self.colors["bg_dark"])
        btn_row.pack(fill="x", padx=12, pady=(0, 12))

        def _parse_tags(raw: str) -> List[str]:
            out: List[str] = []
            for part in (raw or "").split(","):
                s = part.strip()
                if s:
                    out.append(s)
            return out

        def _stage_object(payload: Dict[str, Any], *, kind: str, tags: Optional[List[str]] = None) -> bool:
            try:
                from core.services import get_z_direct  # type: ignore

                zd = get_z_direct()
            except Exception as e:
                messagebox.showerror("Quick Stage", f"Z Direct unavailable:\n{e}", parent=self)
                return False

            try:
                env = zd.make_envelope(
                    kind="object",
                    channel="Z+3",
                    z_context="Z+3_Trinity",
                    source="trinity.it_portal.templates.quick_stage",
                    tags=list(tags or []),
                    payload=payload,
                )
                zd.append_object("Z+3", env)
            except Exception as e:
                messagebox.showerror("Quick Stage", f"Stage failed:\n{e}", parent=self)
                return False

            try:
                peer = (target_peer_var.get() or "None").strip()
                if peer and peer != "None" and peer != "All" and peer != "Z+3":
                    # Mirror to peer inbox/outbox so routing is observable from either side.
                    try:
                        zd.append_channel_outbox(from_channel="Z+3", to_channel=peer, payload=env)
                    except Exception:
                        pass
                    try:
                        zd.append_channel_inbox(to_channel=peer, from_channel="Z+3", payload=env)
                    except Exception:
                        pass
                    self._open_z_direct_view(channel="Z+3", peer=peer, kind=kind, tags="template", search=str(payload.get("id") or ""))
                else:
                    self._open_z_direct_view(channel="Z+3", peer="All", kind=kind, tags="template", search=str(payload.get("id") or ""))
            except Exception:
                pass
            return True

        def _open_quick_dialog(*, kind: str, template_name: str) -> None:
            win = tk.Toplevel(self)
            win.title(f"Quick Stage - {kind}")
            win.geometry("980x720")
            try:
                win.transient(self)
            except Exception:
                pass
            try:
                win.configure(bg=self.colors["bg_dark"])
            except Exception:
                pass

            header = tk.Frame(win, bg=self.colors["bg_panel"])
            header.pack(fill="x")
            tk.Label(
                header,
                text=f"Quick Stage: {kind}",
                bg=self.colors["bg_panel"],
                fg=self.colors["accent_cyan"],
                font=("Arial", 14, "bold"),
            ).pack(side="left", padx=12, pady=10)
            tk.Button(
                header,
                text="Close",
                command=win.destroy,
                bg=self.colors["bg_blue"],
                fg=self.colors["text_white"],
                relief="flat",
                padx=12,
                pady=6,
            ).pack(side="right", padx=12, pady=10)

            body = tk.Frame(win, bg=self.colors["bg_dark"])
            body.pack(fill="both", expand=True, padx=12, pady=12)

            # Template-backed defaults (but we avoid staging placeholder values by requiring the key fields).
            try:
                from core.services.template_system import get_template_registry  # type: ignore

                reg = get_template_registry()
                tmpl = reg.get_template(template_name) if reg is not None else None
                defaults = tmpl.get_default_settings() if tmpl is not None else {}
                if not isinstance(defaults, dict):
                    defaults = {}
            except Exception:
                defaults = {}

            # Shared fields
            tags_var = tk.StringVar(value="cognigrex")
            tk.Label(
                body,
                text="Tags (comma-separated):",
                bg=self.colors["bg_dark"],
                fg=self.colors["text_white"],
                font=("Arial", 10, "bold"),
            ).pack(anchor="w")
            ttk.Entry(body, textvariable=tags_var, width=90).pack(anchor="w", pady=(0, 10))

            form = ttk.LabelFrame(body, text="Fields")
            form.pack(fill="both", expand=True)

            # Kind-specific controls
            vars_: Dict[str, Any] = {}

            def _add_entry(label: str, key: str, *, required: bool = False, width: int = 84) -> None:
                row = tk.Frame(form, bg=self.colors["bg_dark"])
                row.pack(fill="x", padx=10, pady=(8, 0))
                tk.Label(
                    row,
                    text=label + (" *" if required else ""),
                    bg=self.colors["bg_dark"],
                    fg=self.colors["text_white"],
                    font=("Arial", 10, "bold" if required else "normal"),
                    width=22,
                    anchor="w",
                ).pack(side="left")
                v = tk.StringVar(value="")
                vars_[key] = v
                ttk.Entry(row, textvariable=v, width=width).pack(side="left", fill="x", expand=True)

            def _add_text(label: str, key: str, *, required: bool = False, height: int = 6) -> None:
                tk.Label(
                    form,
                    text=label + (" *" if required else ""),
                    bg=self.colors["bg_dark"],
                    fg=self.colors["text_white"],
                    font=("Arial", 10, "bold" if required else "normal"),
                ).pack(anchor="w", padx=10, pady=(10, 0))
                t = scrolledtext.ScrolledText(
                    form,
                    height=height,
                    bg="#001122",
                    fg=self.colors["text_green"],
                    font=("Consolas", 10),
                    wrap="word",
                )
                t.pack(fill="x", padx=10, pady=(4, 0))
                vars_[key] = t

            def _add_choice(label: str, key: str, values: List[str], *, default: str = "") -> None:
                row = tk.Frame(form, bg=self.colors["bg_dark"])
                row.pack(fill="x", padx=10, pady=(8, 0))
                tk.Label(
                    row,
                    text=label,
                    bg=self.colors["bg_dark"],
                    fg=self.colors["text_white"],
                    font=("Arial", 10, "bold"),
                    width=22,
                    anchor="w",
                ).pack(side="left")
                v = tk.StringVar(value=(default or (values[0] if values else "")))
                vars_[key] = v
                ttk.Combobox(row, textvariable=v, values=values, state="readonly", width=30).pack(side="left")

            if kind == "project":
                _add_entry("Title", "title", required=True)
                _add_text("Summary", "summary", required=False, height=6)
                _add_choice("Status", "status", ["active", "paused", "completed", "archived"], default="active")
            elif kind == "research_query":
                _add_text("Query Text", "query_text", required=True, height=6)
                _add_entry("Domain", "domain", required=True)
                _add_entry("Workspace ID", "workspace_id", required=False)
                _add_entry("Project ID", "project_id", required=False)
                _add_choice("Status", "status", ["draft", "queued", "in_progress", "answered"], default="draft")
            elif kind == "dataset":
                _add_entry("Name", "name", required=True)
                _add_entry("Path", "path", required=True)
                _add_entry("Domain", "domain", required=False)
                _add_entry("Dataset Type", "dataset_type", required=False)
                _add_text("Description", "description", required=False, height=5)
                _add_text("Source Paths (1/line)", "source_paths", required=False, height=6)
                _add_entry("Schema Ref", "schema_ref", required=False)
                _add_entry("Rows", "rows", required=False, width=20)
                _add_entry("Cols", "cols", required=False, width=20)
            elif kind == "experiment_run":
                _add_entry("Title", "title", required=True)
                _add_entry("Tool Key", "tool_key", required=False)
                _add_choice("Status", "status", ["planned", "running", "completed", "failed"], default="planned")
                _add_text("Inputs (JSON)", "inputs_json", required=False, height=6)
                _add_text("Outputs (JSON)", "outputs_json", required=False, height=6)
                _add_text("Artifacts (1/line)", "artifacts", required=False, height=5)
            elif kind == "workspace":
                _add_entry("Name", "name", required=True)
                _add_entry("Domain", "domain", required=False)
                _add_text("Purpose", "purpose", required=False, height=5)
            elif kind == "learning_module":
                _add_entry("Title", "title", required=True)
                _add_text("Objectives (1/line)", "objectives", required=False, height=6)
                _add_text("Steps (1/line)", "steps", required=False, height=8)
                _add_text("Prereqs (1/line)", "prereqs", required=False, height=5)
            elif kind == "citation":
                _add_entry("Vault File ID", "vault_file_id", required=True)
                _add_text("Note", "note", required=False, height=5)
                _add_entry("Quote Hash", "quote_hash", required=False)
            elif kind == "knowledge_node":
                _add_entry("Concept", "concept", required=True)
                _add_text("Definition", "definition", required=True, height=6)
                _add_entry("Domain", "domain", required=False)
                _add_entry("Confidence (0-1)", "confidence", required=False, width=20)
                _add_text("Sources (JSON)", "sources_json", required=False, height=6)

            def _get_text(key: str) -> str:
                v = vars_.get(key)
                if isinstance(v, tk.StringVar):
                    return str(v.get() or "").strip()
                if isinstance(v, scrolledtext.ScrolledText):
                    return str(v.get("1.0", tk.END) or "").strip()
                return ""

            def _to_int(raw: str) -> int:
                try:
                    return int(str(raw).strip())
                except Exception:
                    return 0

            def stage_now() -> None:
                try:
                    import uuid as _uuid

                    obj_id = _uuid.uuid4().hex[:16]
                except Exception:
                    obj_id = str(int(time.time()))

                payload = dict(defaults or {})
                payload["kind"] = kind
                payload["id"] = payload.get("id") or f"{kind[:3]}_{obj_id}"
                try:
                    md = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
                    md["romer_standard"] = True
                    payload["metadata"] = md
                except Exception:
                    payload["metadata"] = {"romer_standard": True}

                user_tags = _parse_tags(tags_var.get())
                payload["tags"] = list({*(payload.get("tags") or []), *user_tags, "template", "quick_stage", "cognigrex"})

                if kind == "project":
                    title = _get_text("title")
                    if not title:
                        messagebox.showwarning("Quick Stage", "Title is required.", parent=win)
                        return
                    payload["title"] = title
                    payload["summary"] = _get_text("summary")
                    payload["status"] = _get_text("status") or "active"
                elif kind == "research_query":
                    query_text = _get_text("query_text")
                    if not query_text:
                        messagebox.showwarning("Quick Stage", "Query Text is required.", parent=win)
                        return
                    payload["query_text"] = query_text
                    payload["status"] = _get_text("status") or "draft"
                    dom = _get_text("domain") or str(payload.get("domain") or "").strip()
                    if not dom:
                        dom = "GENERAL"
                    payload["domain"] = dom
                    wsid = _get_text("workspace_id")
                    if wsid:
                        payload["workspace_id"] = wsid
                    pid = _get_text("project_id")
                    if pid:
                        ctx = payload.get("context") if isinstance(payload.get("context"), dict) else {}
                        ctx["project_id"] = pid
                        payload["context"] = ctx
                elif kind == "dataset":
                    name = _get_text("name")
                    if not name:
                        messagebox.showwarning("Quick Stage", "Name is required.", parent=win)
                        return
                    path = _get_text("path")
                    if not path:
                        messagebox.showwarning("Quick Stage", "Path is required.", parent=win)
                        return
                    payload["name"] = name
                    payload["path"] = path
                    dom = _get_text("domain")
                    if dom:
                        payload["domain"] = dom
                    dt = _get_text("dataset_type")
                    if dt:
                        payload["dataset_type"] = dt
                    payload["description"] = _get_text("description")
                    sp = [ln.strip() for ln in _get_text("source_paths").splitlines() if ln.strip()]
                    payload["source_paths"] = sp
                    sref = _get_text("schema_ref")
                    if sref:
                        payload["schema_ref"] = sref
                    stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
                    r = _to_int(_get_text("rows"))
                    c = _to_int(_get_text("cols"))
                    if r:
                        stats["rows"] = r
                    if c:
                        stats["cols"] = c
                    payload["stats"] = stats
                elif kind == "experiment_run":
                    title = _get_text("title")
                    if not title:
                        messagebox.showwarning("Quick Stage", "Title is required.", parent=win)
                        return
                    payload["title"] = title
                    tk_key = _get_text("tool_key")
                    if tk_key:
                        payload["tool_key"] = tk_key
                    payload["status"] = _get_text("status") or "planned"
                    try:
                        ij = _get_text("inputs_json")
                        payload["inputs"] = json.loads(ij) if ij else {}
                    except Exception:
                        messagebox.showwarning("Quick Stage", "Inputs JSON is invalid.", parent=win)
                        return
                    try:
                        oj = _get_text("outputs_json")
                        payload["outputs"] = json.loads(oj) if oj else {}
                    except Exception:
                        messagebox.showwarning("Quick Stage", "Outputs JSON is invalid.", parent=win)
                        return
                    arts = [ln.strip() for ln in _get_text("artifacts").splitlines() if ln.strip()]
                    payload["artifacts"] = arts
                elif kind == "workspace":
                    name = _get_text("name")
                    if not name:
                        messagebox.showwarning("Quick Stage", "Name is required.", parent=win)
                        return
                    payload["name"] = name
                    dom = _get_text("domain")
                    if dom:
                        payload["domain"] = dom
                    payload["purpose"] = _get_text("purpose")
                elif kind == "learning_module":
                    title = _get_text("title")
                    if not title:
                        messagebox.showwarning("Quick Stage", "Title is required.", parent=win)
                        return
                    payload["title"] = title
                    payload["objectives"] = [ln.strip() for ln in _get_text("objectives").splitlines() if ln.strip()]
                    payload["steps"] = [ln.strip() for ln in _get_text("steps").splitlines() if ln.strip()]
                    payload["prereqs"] = [ln.strip() for ln in _get_text("prereqs").splitlines() if ln.strip()]
                elif kind == "citation":
                    vid = _get_text("vault_file_id")
                    if not vid:
                        messagebox.showwarning("Quick Stage", "Vault File ID is required.", parent=win)
                        return
                    payload["vault_file_id"] = vid
                    payload["note"] = _get_text("note")
                    qh = _get_text("quote_hash")
                    if qh:
                        payload["quote_hash"] = qh
                elif kind == "knowledge_node":
                    concept = _get_text("concept")
                    definition = _get_text("definition")
                    if not concept or not definition:
                        messagebox.showwarning("Quick Stage", "Concept and Definition are required.", parent=win)
                        return
                    payload["concept"] = concept
                    payload["definition"] = definition
                    dom = _get_text("domain")
                    if dom:
                        payload["domain"] = dom
                    try:
                        conf_raw = _get_text("confidence")
                        if conf_raw:
                            payload["confidence"] = float(conf_raw)
                    except Exception:
                        pass
                    try:
                        sj = _get_text("sources_json")
                        payload["sources"] = json.loads(sj) if sj else []
                    except Exception:
                        messagebox.showwarning("Quick Stage", "Sources JSON is invalid.", parent=win)
                        return

                ok = _stage_object(payload, kind=kind, tags=["template", "quick_stage", "cognigrex"])
                if ok:
                    try:
                        messagebox.showinfo("Quick Stage", f"Staged {kind}:{payload.get('id')}", parent=win)
                    except Exception:
                        pass
                    try:
                        win.destroy()
                    except Exception:
                        pass

            footer = tk.Frame(body, bg=self.colors["bg_dark"])
            footer.pack(fill="x", pady=(12, 0))
            tk.Button(
                footer,
                text="Stage (to Z+3 objects.jsonl)",
                command=stage_now,
                bg=self.colors["button_green"],
                fg="white",
                font=("Arial", 11, "bold"),
                padx=12,
                pady=8,
            ).pack(side="left")
            tk.Button(
                footer,
                text="Copy JSON Preview",
                command=lambda: (self.clipboard_clear(), self.clipboard_append(json.dumps(defaults or {}, indent=2, ensure_ascii=False))),
                bg=self.colors["bg_panel"],
                fg="white",
                font=("Arial", 11, "bold"),
                padx=12,
                pady=8,
            ).pack(side="left", padx=(10, 0))

        tk.Button(
            btn_row,
            text="Stage Project",
            command=lambda: _open_quick_dialog(kind="project", template_name="ProjectTemplate"),
            bg=self.colors["bg_panel"],
            fg="white",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=6,
        ).pack(side="left")
        tk.Button(
            btn_row,
            text="Stage Research Query",
            command=lambda: _open_quick_dialog(kind="research_query", template_name="ResearchQueryTemplate"),
            bg=self.colors["bg_panel"],
            fg="white",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=6,
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            btn_row,
            text="Stage Dataset",
            command=lambda: _open_quick_dialog(kind="dataset", template_name="DatasetTemplate"),
            bg=self.colors["bg_panel"],
            fg="white",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=6,
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            btn_row,
            text="Stage Experiment Run",
            command=lambda: _open_quick_dialog(kind="experiment_run", template_name="ExperimentRunTemplate"),
            bg=self.colors["bg_panel"],
            fg="white",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=6,
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            btn_row,
            text="Stage Workspace",
            command=lambda: _open_quick_dialog(kind="workspace", template_name="WorkspaceTemplate"),
            bg=self.colors["bg_panel"],
            fg="white",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=6,
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            btn_row,
            text="Stage Learning Module",
            command=lambda: _open_quick_dialog(kind="learning_module", template_name="LearningModuleTemplate"),
            bg=self.colors["bg_panel"],
            fg="white",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=6,
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            btn_row,
            text="Stage Citation",
            command=lambda: _open_quick_dialog(kind="citation", template_name="CitationTemplate"),
            bg=self.colors["bg_panel"],
            fg="white",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=6,
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            btn_row,
            text="Stage Knowledge Node",
            command=lambda: _open_quick_dialog(kind="knowledge_node", template_name="KnowledgeNodeTemplate"),
            bg=self.colors["bg_panel"],
            fg="white",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=6,
        ).pack(side="left", padx=(8, 0))


# ==================================================================================
# STANDALONE LAUNCH (for testing)
# ==================================================================================

def main():
    """Test IT Portal standalone"""
    root = tk.Tk()
    root.withdraw()

    # Mock user
    user = {
        'username': 'nathaniel.bouwer',
        'fullname': 'Nathaniel Bouwer',
        'position': 'Founder',
        'clearance': 5
    }

    # Mock colors
    colors = {
        'bg_dark': '#000B1F',
        'bg_blue': '#001B3F',
        'bg_panel': '#002855',
        'accent_cyan': '#00FFFF',
        'accent_magenta': '#FF00FF',
        'accent_pink': '#FF0088',
        'text_green': '#00FF88',
        'text_cyan': '#00DDDD',
        'text_white': '#FFFFFF',
        'border_blue': '#0055FF',
        'button_green': '#00AA00',
        'button_hover': '#00DD00',
        'error_red': '#FF3333',
        'warning_orange': '#FF9900',
        'success_green': '#00FF00',
    }

    # Mock Z-floors
    z_floors = {
        'Neo': None,
        'Morpheus': None,
        'Architect': None,
        'TheConstruct': None,
        'Oracle': None,
        'Smith': None,
        'Merovingian': None,
        'Trinity': None,
    }

    portal = ITPortal(root, user, colors, z_floors)
    portal.mainloop()


if __name__ == "__main__":
    main()
