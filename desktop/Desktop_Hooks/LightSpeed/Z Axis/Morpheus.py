#!/usr/bin/env python
"""
Morpheus (Z-1) - Knowledge Base & Code Analysis Floor
Complete Floor Coordinator with Knowledge Search, Documentation, and Code Analysis

Morpheus is THE primary knowledge management layer. It holds:
- Knowledge base and documentation
- Code analysis and understanding
- File management and editing
- Search and retrieval systems
- Documentation generation

Variables Held:
- knowledge_index: Indexed knowledge entries
- search_history: Recent searches and results
- analyzed_code: Code analysis results
- documentation_cache: Generated docs
- file_metadata: Tracked file information

Renders:
- Knowledge portal (glass UI dashboard)
- File manager (drag-drop interface)
- Rich text editor
- Knowledge search interface
- Code analysis viewer
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Optional, Dict, List, Any
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


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


class MorpheusFloorState:
    """
    State manager for Morpheus floor

    This class holds all state variables for knowledge management and code analysis
    """

    def __init__(self):
        # Knowledge base state
        self.knowledge_index: Dict[str, Any] = {}
        self.knowledge_entries: List[Dict[str, Any]] = []
        self.total_entries = 0

        # Search state
        self.search_history: List[Dict[str, Any]] = []
        self.last_search_query: Optional[str] = None
        self.search_results: List[Dict] = []

        # Code analysis state
        self.analyzed_files: Dict[str, Dict] = {}
        self.code_insights: List[Dict[str, Any]] = []
        self.analysis_cache: Dict[str, Any] = {}

        # Documentation state
        self.documentation_cache: Dict[str, str] = {}
        self.generated_docs: List[Dict] = []
        self.doc_templates: List[str] = []

        # File management state
        self.tracked_files: List[str] = []
        self.file_metadata: Dict[str, Dict] = {}
        self.recently_opened: List[str] = []

        # Editor state
        self.active_document: Optional[str] = None
        self.unsaved_changes = False

    def add_knowledge_entry(self, title: str, content: str, tags: List[str]):
        """Add an entry to the knowledge base"""
        entry = {
            'title': title,
            'content': content,
            'tags': tags,
            'id': f"entry_{self.total_entries}"
        }
        self.knowledge_entries.append(entry)
        self.knowledge_index[entry['id']] = entry
        self.total_entries += 1

    def search(self, query: str) -> List[Dict]:
        """Search the knowledge base"""
        self.last_search_query = query
        results = [e for e in self.knowledge_entries if query.lower() in e['title'].lower() or query.lower() in e['content'].lower()]
        self.search_history.append({'query': query, 'results_count': len(results)})
        self.search_results = results
        return results


class MorpheusUI(ttk.Frame):
    """
    Primary Morpheus UI - Knowledge Base & Code Analysis

    Morpheus owns all knowledge management, code analysis, file management, and documentation.
    It provides comprehensive search and understanding capabilities.
    """

    def __init__(self, parent: tk.Misc, app: Optional[object] = None, *, compact: bool = False, **_ignored):
        super().__init__(parent)
        self.app = app
        self.compact = bool(compact)
        self.state = MorpheusFloorState()
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

        # Tabs
        self._tabs: Dict[str, ttk.Frame] = {}
        self._builders: Dict[str, Any] = {}
        self._tab_group: Dict[str, str] = {}
        self._tab_container: Dict[str, Any] = {}
        self._group_frames: Dict[str, ttk.Frame] = {}

        if self.compact:
            self._build_compact_shell()
        else:
            self._build_full_shell()

    def _build_full_shell(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self._register_tab("Portal", self._build_portal)
        self._register_tab("Knowledge Search", self._build_knowledge_search)
        self._register_tab("Files", self._build_files)
        self._register_tab("Editor", self._build_editor)
        self._register_tab("Code Analysis", self._build_code_analysis)
        self._register_tab("Dependency Map", self._build_dependency_map)
        self._register_tab("Z Direct Registry", self._build_z_direct_registry)

        self._ensure_built("Portal")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _build_compact_shell(self) -> None:
        """
        Compact embedding for IT Portal:
        - Portal (single surface)
        - Knowledge (search/files/editor)
        - Tools (code analysis/deps)
        - Registry (Z Direct)
        """
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        portal_group = ttk.Frame(self.notebook)
        knowledge_group = ttk.Frame(self.notebook)
        tools_group = ttk.Frame(self.notebook)
        reg_group = ttk.Frame(self.notebook)

        self.notebook.add(portal_group, text="Portal")
        self.notebook.add(knowledge_group, text="Knowledge")
        self.notebook.add(tools_group, text="Tools")
        self.notebook.add(reg_group, text="Registry")

        self._group_frames = {
            "Portal": portal_group,
            "Knowledge": knowledge_group,
            "Tools": tools_group,
            "Registry": reg_group,
        }

        self._tabs["Portal"] = portal_group
        self._builders["Portal"] = self._build_portal
        self._tab_group["Portal"] = "Portal"
        self._tab_container["Portal"] = None

        know_nb = ttk.Notebook(knowledge_group)
        know_nb.pack(fill="both", expand=True)
        self._register_tab("Knowledge Search", self._build_knowledge_search, notebook=know_nb, group="Knowledge")
        self._register_tab("Files", self._build_files, notebook=know_nb, group="Knowledge")
        self._register_tab("Editor", self._build_editor, notebook=know_nb, group="Knowledge")

        tools_nb = ttk.Notebook(tools_group)
        tools_nb.pack(fill="both", expand=True)
        self._register_tab("Code Analysis", self._build_code_analysis, notebook=tools_nb, group="Tools")
        self._register_tab("Dependency Map", self._build_dependency_map, notebook=tools_nb, group="Tools")

        reg_nb = ttk.Notebook(reg_group)
        reg_nb.pack(fill="both", expand=True)
        self._register_tab("Z Direct Registry", self._build_z_direct_registry, notebook=reg_nb, group="Registry")

        self._ensure_built("Portal")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_group_tab_changed)
        know_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        tools_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        reg_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

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

    def _on_group_tab_changed(self, _event):
        """When switching compact groups, ensure the visible leaf is built."""
        try:
            group = self.notebook.tab(self.notebook.select(), "text")
        except Exception:
            return
        if group == "Portal":
            self._ensure_built("Portal")
            return
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

            mount_smart_ops_strip(parent, app=self.app, floor_channel="Z-1", it_portal=self.compact, title="Morpheus Ops")
        except Exception:
            pass
        try:
            from lightspeed_runtime.desktop_adapters import build_morpheus_review_panel

            panel = build_morpheus_review_panel(parent, self.app)
            if panel is not None:
                panel.pack(fill="x", padx=12, pady=(0, 10))
        except Exception:
            pass

        actions = ttk.Frame(parent)
        actions.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Label(
            actions,
            text="Primary Morpheus workbench: review here first, then expand only the surface you need.",
            justify="left",
        ).pack(side="left", padx=(0, 12))
        ttk.Button(actions, text="Review Search", command=lambda: self.select_tab("Knowledge Search")).pack(side="left")
        ttk.Button(actions, text="Files", command=lambda: self.select_tab("Files")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Editor", command=lambda: self.select_tab("Editor")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Code Analysis", command=lambda: self.select_tab("Code Analysis")).pack(side="left", padx=(8, 0))

        try:
            Portal = _load_class("Z Axis/Z-1_Morpheus/components/morpheus_portal_glass.py", "MorpheusPortalGlass")
            ui = Portal(parent)
            ui.pack(fill="both", expand=True)
        except Exception as e:
            ttk.Label(parent, text=f"Morpheus Portal unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_knowledge_search(self, parent: ttk.Frame):
        """Build knowledge search tab"""
        try:
            from lightspeed_runtime.desktop_adapters import mount_morpheus_runtime_search

            if mount_morpheus_runtime_search(parent, self.app):
                return
        except Exception:
            pass

        ttk.Label(parent, text="Knowledge Search", font=("Consolas", 14, "bold")).pack(pady=10)
        ttk.Label(parent, text=f"Total Entries: {self.state.total_entries}").pack(pady=5)
        ttk.Label(parent, text=f"Last Search: {self.state.last_search_query or 'None'}").pack(pady=5)

    def _build_files(self, parent: ttk.Frame):
        """Build files tab"""
        try:
            FileMgr = _load_class("Z Axis/Z-1_Morpheus/components/drag_drop_interface.py", "DragDropFileManager")
            ui = FileMgr(parent)
            ui.pack(fill="both", expand=True)
        except Exception as e:
            ttk.Label(parent, text=f"File Manager unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_editor(self, parent: ttk.Frame):
        """Build editor tab"""
        try:
            Editor = _load_class("Z Axis/Z-1_Morpheus/components/rich_text_editor.py", "RichTextEditor")
            ui = Editor(parent)
            ui.pack(fill="both", expand=True)
            self.state.active_document = "Untitled"
        except Exception as e:
            ttk.Label(parent, text=f"Rich Text Editor unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_code_analysis(self, parent: ttk.Frame):
        """Build code analysis tab"""
        ttk.Label(parent, text="Code Analysis", font=("Consolas", 14, "bold")).pack(pady=10)
        ttk.Label(parent, text=f"Analyzed Files: {len(self.state.analyzed_files)}").pack(pady=5)
        ttk.Label(parent, text=f"Code Insights: {len(self.state.code_insights)}").pack(pady=5)

    def _build_dependency_map(self, parent: ttk.Frame):
        """
        Dependency map + service overview (read-only).

        Morpheus owns "understanding" surfaces; generation is handled by Smith tooling.
        """
        header = ttk.Frame(parent)
        header.pack(fill="x", padx=10, pady=(10, 6))
        ttk.Label(header, text="Dependency Map (depmap.json)", font=("Consolas", 14, "bold")).pack(side="left")

        def _open_depmap():
            try:
                p = (Path(__file__).resolve().parents[1] / "dataindex" / "depmap.json").resolve()
                if p.exists():
                    os.startfile(str(p))  # type: ignore[attr-defined]
            except Exception:
                return

        ttk.Button(header, text="Open depmap.json", command=_open_depmap).pack(side="right")

        try:
            Widget = _load_class("Z Axis/Z+3_Trinity/ui/dashboard_widgets.py", "DependencyMapWidget")
            ui = Widget(parent, lightspeed_root=Path(__file__).resolve().parents[1])
            ui.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        except Exception as e:
            ttk.Label(parent, text=f"Dependency widget unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_z_direct_registry(self, parent: ttk.Frame):
        """
        Z Direct Registry (Morpheus): browse committed knowledge objects for interactability.

        Trinity is the approval gate for commits; this view reads the durable registry:
        `Z Axis/Z-1_Morpheus/Z Direct/objects.json`.
        """
        ttk.Label(parent, text="Z Direct Registry (Committed Objects)", font=("Consolas", 14, "bold")).pack(pady=10)

        try:
            from core.services import get_z_direct  # type: ignore
            z_direct = get_z_direct()
        except Exception as e:
            ttk.Label(parent, text=f"Z Direct unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )
            return

        outer = ttk.Frame(parent)
        outer.pack(fill="both", expand=True, padx=10, pady=10)
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

        btns = ttk.Frame(parent)
        btns.pack(fill="x", padx=10, pady=(0, 10))

        state: Dict[str, Any] = {"items": []}

        def _render_details(item: Any) -> None:
            try:
                details.delete("1.0", "end")
            except Exception:
                pass
            try:
                details.insert("1.0", json.dumps(item, indent=2, ensure_ascii=True))
            except Exception:
                details.insert("1.0", str(item))

        def _load() -> None:
            try:
                items = z_direct.read_registry("Z-1", name="objects")
            except Exception:
                items = []
            state["items"] = items or []
            listbox.delete(0, "end")
            for it in state["items"]:
                if not isinstance(it, dict):
                    listbox.insert("end", str(it))
                    continue
                kind = it.get("kind") or "object"
                oid = it.get("id") or ""
                title = it.get("title") or it.get("name") or ""
                listbox.insert("end", f"{kind} {oid} {title}".strip())
            _render_details({"count": len(state["items"]), "channel": "Z-1"})

        def _open_selected() -> None:
            try:
                sel = listbox.curselection()
                if not sel:
                    messagebox.showwarning("Registry", "Select an item first.", parent=self.winfo_toplevel())
                    return
                it = state["items"][int(sel[0])]
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

        def _on_select(_evt=None) -> None:
            try:
                sel = listbox.curselection()
                if not sel:
                    return
                it = state["items"][int(sel[0])]
                _render_details(it)
            except Exception:
                return

        ttk.Button(btns, text="Refresh", command=_load).pack(side="left")
        ttk.Button(btns, text="Open File", command=_open_selected).pack(side="left", padx=(8, 0))

        listbox.bind("<<ListboxSelect>>", _on_select)
        _load()

    def _register_bento_widgets(self):
        """Register Morpheus widgets with Bento system"""
        try:
            import sys
            trinity_path = Path(__file__).parent / "Z+3_Trinity"
            if str(trinity_path) not in sys.path:
                sys.path.insert(0, str(trinity_path))

            from ui.universal_bento_system import register_floor_widgets, BentoWidget, BentoWidgetType

            widgets = [
                BentoWidget(
                    id="morpheus_knowledge_search",
                    title="Knowledge Search",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-1_Morpheus",
                    callback=lambda w: self._open_knowledge_search(),
                    config={"icon": "🔍", "description": "Search knowledge base"}
                ),
                BentoWidget(
                    id="morpheus_documentation",
                    title="Documentation",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-1_Morpheus",
                    callback=lambda w: self._open_documentation(),
                    config={"icon": "📚", "description": "View documentation"}
                ),
                BentoWidget(
                    id="morpheus_code_analysis",
                    title="Code Analysis",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-1_Morpheus",
                    callback=lambda w: self._open_code_analysis(),
                    config={"icon": "🔬", "description": "Analyze code"}
                )
            ]

            register_floor_widgets("Z-1_Morpheus", widgets)
            print("[Morpheus] Registered Morpheus Bento widgets")
        except Exception as e:
            print(f"[Morpheus] Could not register Bento widgets: {e}")

    def _open_knowledge_search(self):
        """Open knowledge search tab"""
        print("[Morpheus] Opening Knowledge Search...")
        self.select_tab("Knowledge Search")

    def _open_documentation(self):
        """Open documentation tab"""
        print("[Morpheus] Opening Documentation...")
        self.select_tab("Portal")

    def _open_code_analysis(self):
        """Open code analysis tab"""
        print("[Morpheus] Opening Code Analysis...")
        self.select_tab("Code Analysis")


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
    return MorpheusUI(parent, app=app, compact=compact)


def build(*args, **kwargs):
    """Alias for legacy floor loaders."""
    return create_gui(*args, **kwargs)


# ---------------------------------------------------------------------------
# Floor boot hook (used by FloorLoader)
# ---------------------------------------------------------------------------

_MORPHEUS_INITIALIZED = False
MORPHEUS_RUNTIME: Dict[str, Any] = {}


def initialize(*, components: Optional[Dict[str, Any]] = None, dependencies: Optional[Dict[str, Any]] = None, **_kwargs) -> bool:
    """
    Initialize Morpheus floor runtime services.

    This runs during floor bootstrap (no UI) and ensures Morpheus's
    background services and integrations are active.

    Args:
        components: Pre-loaded component classes/instances
        dependencies: Shared services (db, event_bus, storage, logger)
        **_kwargs: Additional platform parameters

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    global _MORPHEUS_INITIALIZED, MORPHEUS_RUNTIME
    if _MORPHEUS_INITIALIZED:
        return True
    _MORPHEUS_INITIALIZED = True

    try:
        # Core services are provided by the Merovingian floor (`Z Axis/Z-4_Merovingian/core`).
        # Use the stable namespace import path (`core.services`) and avoid invalid module names
        # such as `Z-4_Merovingian`.
        from core.services import get_db, get_event_bus, get_storage, get_logger  # type: ignore

        db = get_db()
        event_bus = get_event_bus()
        storage = get_storage()
        logger = get_logger()
    except Exception as e:
        print(f"[Morpheus] Failed to load core services: {e}")
        db = None
        event_bus = None
        storage = None
        logger = None

    MORPHEUS_RUNTIME["db"] = db
    MORPHEUS_RUNTIME["event_bus"] = event_bus
    MORPHEUS_RUNTIME["storage"] = storage
    MORPHEUS_RUNTIME["logger"] = logger

    # Floor-specific initialization

    # Initialize code analysis tools
    try:
        _load_symbol("Z Axis/Z-1_Morpheus/components/morpheus_portal_glass.py", "MorpheusPortalGlass")
        MORPHEUS_RUNTIME["portal_available"] = True
    except Exception as e:
        MORPHEUS_RUNTIME["portal_error"] = str(e)

    # Start documentation indexer
    if storage:
        try:
            # Index documentation files
            docs_path = storage.get_floor_path("morpheus") / "documentation"
            if docs_path.exists():
                MORPHEUS_RUNTIME["docs_path"] = str(docs_path)
                if logger:
                    logger.info(f"[Morpheus] Documentation indexed: {docs_path}")
        except Exception as e:
            if logger:
                logger.debug(f"[Morpheus] Documentation indexing skipped: {e}")


    # Subscribe to relevant events
    if event_bus:
        try:
            event_bus.subscribe("system.health.check", _on_health_check)
        except Exception as e:
            if logger:
                logger.warning(f"[Morpheus] Event subscription failed: {e}")

    # Publish floor ready event
    if event_bus:
        try:
            event_bus.publish("morpheus.floor.ready", {
                "floor": "Morpheus",
                "z_level": -1,
                "capabilities": ['code_analysis', 'documentation', 'knowledge_base', 'search']
            })
        except Exception as e:
            if logger:
                logger.warning(f"[Morpheus] Failed to publish ready event: {e}")

    if logger:
        logger.info("[Morpheus] Floor initialized successfully")

    return True


def _on_health_check(event):
    """Respond to health check events"""
    event_bus = MORPHEUS_RUNTIME.get("event_bus")
    if event_bus:
        try:
            event_bus.publish("morpheus.health.status", {
                "floor": "Morpheus",
                "status": "operational",
                "z_level": -1
            })
        except Exception:
            pass

def main() -> int:
    root = tk.Tk()
    root.title("Morpheus (Z-1) - Knowledge")
    root.geometry("1200x800")
    MorpheusUI(root).pack(fill="both", expand=True)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
