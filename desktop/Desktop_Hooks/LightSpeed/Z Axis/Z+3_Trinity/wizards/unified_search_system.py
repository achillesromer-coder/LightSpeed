#!/usr/bin/env python
"""
UNIFIED SEARCH SYSTEM - Global Search across all LightSpeed Assets
Provides fast, intelligent search across calculators, datasets, documentation, and more.

Features:
- Fuzzy search with typo tolerance
- Category-based filtering
- Recently accessed items
- AI-powered search suggestions
- Integration with all Z-floors

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 20, 2026
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable, Any
import json
import sqlite3
from datetime import datetime
import difflib

# Setup paths
TRINITY_ROOT = Path(__file__).parent.parent.resolve()
LIGHTSPEED_ROOT = TRINITY_ROOT.parent.parent
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
MORPHEUS_ROOT = Z_AXIS_ROOT / "Z-1_Morpheus"
CONSTRUCT_ROOT = Z_AXIS_ROOT / "Z0_TheConstruct"

# Add to path
sys.path.insert(0, str(LIGHTSPEED_ROOT))
sys.path.insert(0, str(MORPHEUS_ROOT))

# Import database models
try:
    from database.models.calculators import CalculatorModule
    from database.models.datasets import ScientificDataset
    from database.base import get_session, DB_PATH as LEGACY_DB_PATH
    # Only enable if the legacy DB file actually exists; otherwise fall back to file-based indexing.
    try:
        HAS_DATABASE = Path(str(LEGACY_DB_PATH)).exists()
    except Exception:
        HAS_DATABASE = False
except ImportError:
    HAS_DATABASE = False
    print("[WARNING] Database models not available - search will be limited")


class SearchResult:
    """Represents a single search result"""

    def __init__(self,
                 name: str,
                 category: str,
                 description: str,
                 path: str,
                 result_type: str,
                 score: float = 1.0,
                 metadata: Optional[Dict] = None):
        self.name = name
        self.category = category
        self.description = description
        self.path = path
        self.result_type = result_type  # calculator, dataset, documentation, tool
        self.score = score
        self.metadata = metadata or {}

    def __repr__(self):
        return f"<SearchResult({self.name}, {self.result_type}, score={self.score:.2f})>"


class UnifiedSearchSystem:
    """
    Unified search system for all LightSpeed assets.

    Searches across:
    - Calculator modules (49+)
    - Scientific datasets (21+)
    - Documentation files
    - UI components
    - Tools and utilities
    """

    # Search categories
    CATEGORIES = {
        'all': 'All Assets',
        'actions': 'Actions / Commands',
        'calculators': 'Calculator Modules',
        'datasets': 'Scientific Datasets',
        'documentation': 'Documentation',
        'tools': 'Tools & Utilities',
        'ui': 'UI Components',
        'objects': 'Committed Objects (Registry)',
        'vault': 'Oracle Vault (Files)',
        'knowledge': 'Cognigrex Knowledge (Nodes)',
    }

    # Calculator subcategories
    CALC_SUBCATEGORIES = {
        'atomic': 'Atomic Physics',
        'black_hole': 'Black Hole Physics',
        'cosmology': 'Cosmology & Astrophysics',
        'quantum': 'Quantum Mechanics',
        'orbital': 'Orbital Mechanics',
        'raphael': 'Raphael Framework',
        'holographic': 'Holographic Simulations'
    }

    # Dataset categories
    DATASET_CATEGORIES = {
        'planck_cmb': 'Planck CMB',
        'ligo_gw': 'LIGO Gravitational Waves',
        'simulation': 'Simulations',
        'database': 'Databases'
    }

    def __init__(self, *, actions: Optional[List[SearchResult]] = None):
        """Initialize search system"""
        self.session = None
        # Keep DB availability instance-scoped (avoid mutating module globals).
        self.has_database = bool(HAS_DATABASE)
        self.search_index = []
        self.recent_searches = []
        self.recent_results = []
        self._actions = list(actions or [])

        # Initialize database connection
        if self.has_database:
            try:
                self.session = get_session()
                print("[SEARCH] Database connection established")
            except Exception as e:
                print(f"[SEARCH] Failed to connect to database: {e}")
                self.session = None
                self.has_database = False

        # Build search index
        self._build_index()

    def _build_index(self):
        """Build searchable index of all assets"""
        print("[SEARCH] Building search index...")

        # Index calculators
        self._index_calculators()

        # Index datasets
        self._index_datasets()

        # Index documentation
        self._index_documentation()

        # Index Oracle durable registry (vault files + knowledge nodes)
        self._index_oracle_registry()

        # Index Trinity durable registry (schemas + UI/action/workflow definitions)
        self._index_trinity_registry()

        # Index tools
        self._index_tools()

        # Index UI components
        self._index_ui_components()

        # Index command/actions (host-provided)
        self._index_actions()

        print(f"[SEARCH] Index built: {len(self.search_index)} items")

    def _index_trinity_registry(self) -> None:
        """
        Index Trinity Z Direct durable registry objects.

        This is the canonical place for operator-approved definitions that make the UI
        expandable without code changes (schemas, action defs, workflow defs, bento widgets).
        """
        try:
            trinity_objects = (Z_AXIS_ROOT / "Z+3_Trinity" / "Z Direct" / "objects.json").resolve()
            if not trinity_objects.exists():
                return
            data = json.loads(trinity_objects.read_text(encoding="utf-8", errors="replace"))
            if not isinstance(data, list):
                return

            for it in data:
                if not isinstance(it, dict):
                    continue
                k = str(it.get("kind") or "").strip()
                if not k:
                    continue

                # Respect `enabled` when present (default True).
                if it.get("enabled") is False:
                    continue

                obj_id = str(it.get("id") or "").strip()
                title = str(it.get("title") or it.get("name") or obj_id or k).strip()
                desc = str(it.get("description") or "").strip()
                tags = it.get("tags")
                tags_s = ""
                try:
                    if isinstance(tags, list):
                        cleaned = [str(t).strip() for t in tags if str(t).strip()]
                        if cleaned:
                            tags_s = ", ".join(cleaned[:6]) + (", ..." if len(cleaned) > 6 else "")
                    elif isinstance(tags, str) and tags.strip():
                        tags_s = tags.strip()
                except Exception:
                    tags_s = ""

                if k == "schema":
                    self.search_index.append(
                        SearchResult(
                            name=title,
                            category="Z Direct Schema",
                            description=(desc or f"Committed schema (id={obj_id})") + (f" tags={tags_s}" if tags_s else ""),
                            path=str(trinity_objects),
                            result_type="ui",
                            metadata={"kind": "schema", "id": obj_id},
                        )
                    )
                # action_def is indexed as runnable actions in SearchUI (host-aware) to avoid duplicates.
                elif k in ("workflow_def", "simulation_def", "bento_widget"):
                    cat = {
                        "workflow_def": "Tools & Utilities",
                        "simulation_def": "Tools & Utilities",
                        "bento_widget": "UI Components",
                    }.get(k, "Tools & Utilities")
                    self.search_index.append(
                        SearchResult(
                            name=title,
                            category=cat,
                            description=(desc or f"{k} (id={obj_id})") + (f" tags={tags_s}" if tags_s else ""),
                            path=str(trinity_objects),
                            result_type="tool",
                            metadata={"kind": k, "id": obj_id},
                        )
                    )
                else:
                    # Other committed objects (projects, datasets, research queries, etc.) are surfaced
                    # as read-only "object" results; the UI can route these into the Object Catalog.
                    self.search_index.append(
                        SearchResult(
                            name=title,
                            category="Committed Object",
                            description=(desc or f"{k} (id={obj_id})") + (f" tags={tags_s}" if tags_s else ""),
                            path=str(trinity_objects),
                            result_type="object",
                            metadata={"kind": k, "id": obj_id, "registry": "trinity", "tags": tags},
                        )
                    )
        except Exception:
            return

    def _index_actions(self) -> None:
        """Index action/command entries (for command palette use)."""
        for a in list(self._actions or []):
            try:
                if isinstance(a, SearchResult) and (a.result_type == "action"):
                    self.search_index.append(a)
            except Exception:
                continue

    def _index_oracle_registry(self):
        """Index Oracle Z Direct durable registry objects (vault_file + knowledge_node)."""
        try:
            oracle_objects = (Z_AXIS_ROOT / "Z-2_Oracle" / "Z Direct" / "objects.json").resolve()
            if not oracle_objects.exists():
                return
            data = json.loads(oracle_objects.read_text(encoding="utf-8", errors="replace"))
            if not isinstance(data, list):
                return

            added = 0
            for it in data:
                if not isinstance(it, dict):
                    continue
                k = it.get("kind")
                if k == "vault_file":
                    name = str(it.get("source_name") or it.get("name") or it.get("id") or "vault_file")
                    desc = f"Oracle vault file (id={it.get('id')})"
                    path = str(it.get("path") or "")
                    self.search_index.append(
                        SearchResult(
                            name=name,
                            category="oracle",
                            description=desc,
                            path=path,
                            result_type="vault",
                            metadata={
                                "vault_id": it.get("id"),
                                "sha256": it.get("sha256"),
                                "source_path": it.get("source_path"),
                                "mime_type": it.get("mime_type"),
                                "size_bytes": it.get("size_bytes"),
                            },
                        )
                    )
                    added += 1
                elif k == "knowledge_node":
                    name = str(it.get("concept") or it.get("id") or "knowledge_node")
                    desc = str(it.get("definition") or "")
                    # Keep the UI responsive; details pane shows full-ish content already.
                    if len(desc) > 240:
                        desc = desc[:240] + "..."
                    self.search_index.append(
                        SearchResult(
                            name=name,
                            category=str(it.get("domain") or "GENERAL").lower(),
                            description=desc,
                            path=str(it.get("id") or ""),
                            result_type="knowledge",
                            metadata={
                                "knowledge_node_id": it.get("id"),
                                "domain": it.get("domain"),
                                "confidence": it.get("confidence"),
                                "sources": it.get("sources"),
                            },
                        )
                    )
                    added += 1
                elif k == "citation":
                    cid = str(it.get("id") or "").strip()
                    name = str(it.get("note") or cid or "citation")
                    if len(name) > 80:
                        name = name[:80] + "..."
                    vault_id = str(it.get("vault_file_id") or "").strip()
                    desc = f"Citation (id={cid}) vault_file_id={vault_id}" if cid or vault_id else "Citation"
                    self.search_index.append(
                        SearchResult(
                            name=name,
                            category="oracle",
                            description=desc,
                            path=str(cid),
                            result_type="object",
                            metadata={"kind": "citation", "id": cid, "registry": "oracle", "vault_file_id": vault_id},
                        )
                    )
                    added += 1
                elif isinstance(k, str) and k.strip() and str(it.get("id") or "").strip():
                    # Other Oracle committed objects (workspaces/datasets/learning modules/etc.)
                    obj_id = str(it.get("id") or "").strip()
                    title = str(it.get("title") or it.get("name") or obj_id or k).strip()
                    desc = str(it.get("description") or "").strip()
                    if len(desc) > 240:
                        desc = desc[:240] + "..."
                    self.search_index.append(
                        SearchResult(
                            name=title,
                            category="oracle",
                            description=desc or f"{k} (id={obj_id})",
                            path=str(obj_id),
                            result_type="object",
                            metadata={"kind": str(k), "id": obj_id, "registry": "oracle"},
                        )
                    )
                    added += 1

            if added:
                print(f"[SEARCH] Indexed {added} Oracle registry items")
        except Exception as e:
            print(f"[SEARCH] Failed to index Oracle registry: {e}")

    def _index_calculators(self):
        """Index all calculator modules"""
        if self.has_database and self.session:
            try:
                calculators = self.session.query(CalculatorModule).filter_by(status='active').all()

                for calc in calculators:
                    result = SearchResult(
                        name=calc.name,
                        category=calc.category or 'general',
                        description=calc.description or '',
                        path=calc.filepath,
                        result_type='calculator',
                        metadata={
                            'subcategory': calc.subcategory,
                            'floor': calc.floor,
                            'version': calc.version,
                            'usage_count': calc.usage_count,
                            'dataset_requirements': calc.dataset_requirements
                        }
                    )
                self.search_index.append(result)

                print(f"[SEARCH] Indexed {len(calculators)} calculators")
            except Exception as e:
                print(f"[SEARCH] Failed to index calculators: {e}")
                # If DB access is broken, disable it for the remainder of this instance.
                self.has_database = False
                self.session = None

    def _index_datasets(self):
        """Index all scientific datasets"""
        if self.has_database and self.session:
            try:
                datasets = self.session.query(ScientificDataset).all()

                for ds in datasets:
                    result = SearchResult(
                        name=ds.filename,
                        category=ds.category,
                        description=ds.description or '',
                        path=ds.filepath,
                        result_type='dataset',
                        metadata={
                            'format': ds.format,
                            'size_gb': ds.size_gb,
                            'mission': ds.mission,
                            'observation_date': str(ds.observation_date) if ds.observation_date else None,
                            'access_count': ds.access_count
                        }
                    )
                    self.search_index.append(result)

                print(f"[SEARCH] Indexed {len(datasets)} datasets")
            except Exception as e:
                print(f"[SEARCH] Failed to index datasets: {e}")
                self.has_database = False
                self.session = None

    def _index_documentation(self):
        """Index documentation files"""
        # Search for markdown files in ai_logs/reports
        docs_path = LIGHTSPEED_ROOT / "ai_logs" / "reports"

        if docs_path.exists():
            md_files = list(docs_path.rglob("*.md"))

            for md_file in md_files:
                result = SearchResult(
                    name=md_file.stem,
                    category='documentation',
                    description=f"Documentation: {md_file.stem.replace('_', ' ').title()}",
                    path=str(md_file),
                    result_type='documentation',
                    metadata={
                        'file_type': 'markdown',
                        'size_kb': md_file.stat().st_size / 1024
                    }
                )
                self.search_index.append(result)

            print(f"[SEARCH] Indexed {len(md_files)} documentation files")

    def _index_tools(self):
        """Index tools and utilities"""
        # Search for Python tools in each floor
        for floor_dir in Z_AXIS_ROOT.iterdir():
            if floor_dir.is_dir() and floor_dir.name.startswith('Z'):
                tools_dir = floor_dir / "tools"

                if tools_dir.exists():
                    py_files = list(tools_dir.glob("*.py"))

                    for py_file in py_files:
                        if py_file.name.startswith('_'):
                            continue

                        result = SearchResult(
                            name=py_file.stem,
                            category='tools',
                            description=f"Tool: {py_file.stem.replace('_', ' ').title()}",
                            path=str(py_file),
                            result_type='tool',
                            metadata={
                                'floor': floor_dir.name,
                                'file_type': 'python'
                            }
                        )
                        self.search_index.append(result)

    def _index_ui_components(self):
        """Index UI components"""
        # Search Trinity components
        trinity_components = TRINITY_ROOT / "components"

        if trinity_components.exists():
            py_files = list(trinity_components.glob("*.py"))

            for py_file in py_files:
                if py_file.name.startswith('_'):
                    continue

                result = SearchResult(
                    name=py_file.stem,
                    category='ui',
                    description=f"UI Component: {py_file.stem.replace('_', ' ').title()}",
                    path=str(py_file),
                    result_type='ui',
                    metadata={
                        'floor': 'Z+3_Trinity',
                        'file_type': 'python'
                    }
                )
                self.search_index.append(result)

    def search(self,
               query: str,
               category: str = 'all',
               max_results: int = 20,
               fuzzy: bool = True) -> List[SearchResult]:
        """
        Search for assets matching query.

        Args:
            query: Search query string
            category: Filter by category ('all', 'calculators', 'datasets', etc.)
            max_results: Maximum number of results to return
            fuzzy: Enable fuzzy matching for typo tolerance

        Returns:
            List of SearchResult objects sorted by relevance
        """
        query = (query or "").strip()
        if not query:
            # Empty query is treated as browsing/listing (UI can call list_assets explicitly).
            return self.list_assets(category=category, limit=max_results)

        query = query.lower().strip()
        results = []

        # Add to recent searches
        if query not in self.recent_searches:
            self.recent_searches.insert(0, query)
            self.recent_searches = self.recent_searches[:10]  # Keep last 10

        # Filter by category
        search_pool = self.search_index
        if category != 'all':
            allowed = self._category_to_result_types(category)
            if allowed:
                search_pool = [r for r in self.search_index if r.result_type in allowed]

        # Search each item
        for item in search_pool:
            score = self._calculate_relevance(query, item, fuzzy)

            if score > 0:
                item.score = score
                results.append(item)

        # Sort by score (descending)
        results.sort(key=lambda r: r.score, reverse=True)

        # Limit results
        results = results[:max_results]

        # Store recent results
        self.recent_results = results

        return results

    def list_assets(self, category: str = "all", limit: int = 200) -> List[SearchResult]:
        """
        Browse assets without a query.

        This is intentionally simple: it returns a stable, name-sorted slice of the index,
        filtered by the requested category (if any).
        """
        pool = self.search_index
        if category and category != "all":
            allowed = self._category_to_result_types(category)
            if allowed:
                pool = [r for r in self.search_index if r.result_type in allowed]
        pool = sorted(pool, key=lambda r: (r.result_type, (r.name or "").lower()))
        return pool[: max(1, int(limit or 1))]

    def _category_to_result_types(self, category: str) -> Optional[set]:
        """
        Map UI category keys to SearchResult.result_type values.

        The UI historically used pluralized keys (e.g. "calculators") while SearchResult
        uses singular result_type values (e.g. "calculator").
        """
        c = (category or "").strip().lower()
        if not c or c == "all":
            return None

        mapping = {
            "action": {"action"},
            "actions": {"action"},
            "command": {"action"},
            "commands": {"action"},
            "calculator": {"calculator"},
            "calculators": {"calculator"},
            "dataset": {"dataset"},
            "datasets": {"dataset"},
            "documentation": {"documentation"},
            "docs": {"documentation"},
            "tool": {"tool"},
            "tools": {"tool"},
            "ui": {"ui"},
            "object": {"object"},
            "objects": {"object"},
            "vault": {"vault"},
            "knowledge": {"knowledge"},
        }
        return mapping.get(c, {c})

    def _calculate_relevance(self, query: str, item: SearchResult, fuzzy: bool = True) -> float:
        """
        Calculate relevance score for a search item.

        Returns a score from 0 (no match) to 1 (perfect match).
        """
        q = (query or "").strip().lower()
        score = 0.0
        blob = f"{item.name} {item.description} {item.category} {item.path}".lower()
        terms = [t for t in q.split() if t.strip()]

        # Multi-term query: require all tokens to appear somewhere in the blob.
        # This makes the command-palette feel much more "menu-like" (narrowing by words).
        if len(terms) > 1:
            if not all(t in blob for t in terms):
                return 0.0
            # Give a baseline for satisfying all terms, then let single-term boosts refine ordering.
            score += 0.55

        # Exact name match
        if q and q == item.name.lower():
            return 1.0

        # Name contains query (or any term)
        if q and q in item.name.lower():
            score += 0.8
        elif len(terms) > 1:
            if any(t in item.name.lower() for t in terms):
                score += 0.25

        # Description contains query (or any term)
        if q and q in item.description.lower():
            score += 0.5
        elif len(terms) > 1:
            if any(t in item.description.lower() for t in terms):
                score += 0.15

        # Category match
        if q and q in item.category.lower():
            score += 0.4
        elif len(terms) > 1:
            if any(t in item.category.lower() for t in terms):
                score += 0.1

        # Path contains query
        if q and q in item.path.lower():
            score += 0.3
        elif len(terms) > 1:
            if any(t in item.path.lower() for t in terms):
                score += 0.08

        # Fuzzy match on name
        if fuzzy and score == 0 and q:
            fuzzy_score = difflib.SequenceMatcher(None, q, item.name.lower()).ratio()
            if fuzzy_score > 0.7:
                score += fuzzy_score * 0.6

        # Boost based on usage (if available)
        if 'usage_count' in item.metadata:
            usage_boost = min(item.metadata['usage_count'] / 100.0, 0.2)
            score += usage_boost

        if 'access_count' in item.metadata:
            access_boost = min(item.metadata['access_count'] / 50.0, 0.2)
            score += access_boost

        return min(score, 1.0)

    def get_recent_searches(self) -> List[str]:
        """Get recent search queries"""
        return self.recent_searches

    def get_popular_items(self, limit: int = 10) -> List[SearchResult]:
        """Get most popular/accessed items"""
        popular = []

        for item in self.search_index:
            usage = item.metadata.get('usage_count', 0) + item.metadata.get('access_count', 0)
            if usage > 0:
                item.score = usage
                popular.append(item)

        popular.sort(key=lambda r: r.score, reverse=True)
        return popular[:limit]

    def suggest_related(self, result: SearchResult, limit: int = 5) -> List[SearchResult]:
        """Suggest related items based on a result"""
        related = []

        # Find items in same category
        for item in self.search_index:
            if item.name == result.name:
                continue

            # Same category
            if item.category == result.category:
                related.append(item)

            # Dataset linked to calculator
            elif result.result_type == 'calculator' and item.result_type == 'dataset':
                if result.metadata.get('dataset_requirements'):
                    if item.category in result.metadata['dataset_requirements']:
                        related.append(item)

            # Calculator that uses dataset
            elif result.result_type == 'dataset' and item.result_type == 'calculator':
                if item.metadata.get('dataset_requirements'):
                    if result.category in item.metadata['dataset_requirements']:
                        related.append(item)

        return related[:limit]


class SearchUI:
    """
    Search UI component for Trinity.

    Provides a modern, responsive search interface.
    """

    def __init__(
        self,
        parent: tk.Tk,
        *,
        initial_query: str = "",
        initial_category: str = "all",
        host: Any = None,
    ):
        """Initialize search UI"""
        self.parent = parent
        self.host = host
        self._action_handlers: Dict[str, Callable[[], None]] = {}
        actions = []
        try:
            actions, self._action_handlers = self._build_action_entries(host)
        except Exception:
            actions, self._action_handlers = [], {}
        self.search_system = UnifiedSearchSystem(actions=actions)
        self.results = []
        self._oracle_cache = None
        self._initial_query = initial_query or ""
        self._initial_category = (initial_category or "all").strip().lower()
        self._category_name_to_id = {v: k for k, v in UnifiedSearchSystem.CATEGORIES.items()}

        # Create UI
        self._create_ui()

        # Seed initial state (supports "browsing" a category without typing).
        try:
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, self._initial_query)
        except Exception:
            pass
        try:
            cat_id = self._initial_category if self._initial_category in UnifiedSearchSystem.CATEGORIES else "all"
            self.category_display_var.set(UnifiedSearchSystem.CATEGORIES.get(cat_id, UnifiedSearchSystem.CATEGORIES.get("all", "all")))
        except Exception:
            pass
        try:
            self.parent.after(50, self._perform_search)
        except Exception:
            pass

    def _build_action_entries(self, host: Any) -> Tuple[List[SearchResult], Dict[str, Callable[[], None]]]:
        """
        Build action results + handlers for command-palette use.

        These are host-dependent (N.py passes itself as `host`), so the search index stays
        accurate even when the UI is reused elsewhere.
        """
        actions: List[SearchResult] = []
        handlers: Dict[str, Callable[[], None]] = {}

        def _add(action_id: str, name: str, description: str, fn: Callable[[], None]) -> None:
            action_id = str(action_id or "").strip()
            if not action_id:
                return
            handlers[action_id] = fn
            actions.append(
                SearchResult(
                    name=name,
                    category="actions",
                    description=description,
                    path="",
                    result_type="action",
                    metadata={"action_id": action_id},
                )
            )

        if host is None:
            return actions, handlers

        def _call(attr: str, *args, **kwargs) -> Callable[[], None]:
            def _runner() -> None:
                try:
                    fn = getattr(host, attr, None)
                    if callable(fn):
                        fn(*args, **kwargs)
                except Exception:
                    pass
            return _runner

        # Core navigation actions (UI-first).
        _add("go_home", "Go Home / Lobby", "Return to the UI-first lobby.", _call("show_main_menu"))
        _add("open_help", "Help", "Open keyboard shortcuts + help.", _call("show_help"))
        _add(
            "open_world_host",
            "Open World Host (UI-first)",
            "Open the ambient environment host with the 2D Bento menu.",
            _call("show_immersive_world", interactive=False),
        )
        _add(
            "open_world_immersive",
            "Open Immersive (Interactive)",
            "Open immersive mode (explicit) with the curved overlay menu.",
            _call("show_immersive_world", interactive=True),
        )
        _add("toggle_bento_panel", "Toggle Bento Panel", "Show/hide the 2D Bento menu when available.", _call("toggle_bento_panel"))
        _add("focus_bento_search", "Focus Bento Search", "Focus the Bento menu search box (when visible).", _call("focus_bento_search"))
        _add("clear_bento_recents", "Clear Bento Recents", "Clear recent Bento items for the active user.", _call("bento_clear_recents"))
        _add("clear_bento_favorites", "Clear Bento Favorites", "Clear favorited Bento items for the active user.", _call("bento_clear_favorites"))

        # Z-floor shortcuts.
        _add("open_oracle", "Open Oracle", "Knowledge vault + durable registry.", _call("open_z_floor", "Oracle"))
        _add("open_morpheus", "Open Morpheus", "Documentation + learning layer.", _call("open_z_floor", "Morpheus"))
        _add("open_construct", "Open TheConstruct", "Physics lab + simulation environment.", _call("open_z_floor", "TheConstruct"))
        _add("open_trinity", "Open Trinity", "Dashboards + control panels.", _call("open_z_floor", "Trinity"))
        _add("open_architect", "Open Architect", "Planning + projects.", _call("open_z_floor", "Architect"))
        _add("open_neo", "Open Neo", "AI integration + planning.", _call("open_z_floor", "Neo"))
        _add("open_smith", "Open Smith", "Automation + background jobs.", _call("open_z_floor", "Smith"))
        _add("open_merovingian", "Open Merovingian", "Diagnostics + core services.", _call("open_z_floor", "Merovingian"))

        # Floor tool deep-links (single dynamic menu surface).
        _add(
            "open_architect_project_manager",
            "Architect: Project Manager",
            "Open Architect and select Project Manager.",
            _call("open_z_floor_tab", "Architect", "Project Manager"),
        )
        _add(
            "open_oracle_library",
            "Oracle: Library",
            "Open Oracle and select Library.",
            _call("open_z_floor_tab", "Oracle", "Library"),
        )
        _add(
            "open_smith_jobs_artifacts",
            "Smith: Jobs & Artifacts",
            "Open Smith and select Jobs & Artifacts ledger.",
            _call("open_z_floor_tab", "Smith", "Jobs & Artifacts"),
        )
        _add(
            "open_merovingian_logs",
            "Merovingian: Logs",
            "Open Merovingian and select Logs viewer.",
            _call("open_z_floor_tab", "Merovingian", "Logs"),
        )
        _add(
            "open_merovingian_db",
            "Merovingian: Database Browser",
            "Open Merovingian and select Database Browser.",
            _call("open_z_floor_tab", "Merovingian", "Database Browser"),
        )
        _add(
            "open_merovingian_profiler",
            "Merovingian: Performance Profiler",
            "Open Merovingian and select Performance Profiler.",
            _call("open_z_floor_tab", "Merovingian", "Performance Profiler"),
        )
        _add(
            "open_neo_planner",
            "Neo: Planner",
            "Open Neo and select Planner (Plan A/B/C staging).",
            _call("open_z_floor_tab", "Neo", "Planner"),
        )
        _add(
            "open_morpheus_depmap",
            "Morpheus: Dependency Map",
            "Open Morpheus and select Dependency Map.",
            _call("open_z_floor_tab", "Morpheus", "Dependency Map"),
        )
        _add(
            "open_trinity_settings_hub",
            "Trinity: Settings Hub",
            "Open Trinity and select Settings Hub.",
            _call("open_z_floor_tab", "Trinity", "Settings Hub"),
        )

        # IT/Founder-only affordances.
        try:
            user_mode = str(getattr(host, "user_mode", "") or "")
        except Exception:
            user_mode = ""
        if user_mode == "it_founder":
            _add("open_it_portal", "Open IT Portal", "Founder control center (governance + approvals + floor hub).", _call("open_it_portal"))
            _add("open_settings", "Settings", "Open settings manager.", _call("show_settings"))

        # Operator-approved action definitions (data-defined, committed via Z Direct).
        try:
            from core.services import get_z_direct  # type: ignore

            zd = get_z_direct()
            items = zd.read_registry("Z+3", name="objects") or []
        except Exception:
            items = []

        for it in items:
            if not isinstance(it, dict):
                continue
            if it.get("kind") != "action_def":
                continue
            if it.get("enabled") is False:
                continue

            act_id = str(it.get("id") or "").strip()
            if not act_id:
                continue
            title = str(it.get("title") or act_id).strip()
            desc = str(it.get("description") or "").strip() or f"Action definition (id={act_id})"
            host_action = str(it.get("host_action") or "").strip()
            host_args = it.get("host_action_args") if isinstance(it.get("host_action_args"), dict) else {}
            param_specs = it.get("params") if isinstance(it.get("params"), list) else []
            safety = it.get("safety") if isinstance(it.get("safety"), dict) else {}
            needs_confirm = bool(safety.get("requires_confirm", False))

            if not host_action:
                continue
            fn = getattr(host, host_action, None)
            if not callable(fn):
                continue

            action_key = f"action_def:{act_id}"
            if action_key in handlers:
                continue

            def _runner(
                _fn=fn,
                _args=host_args,
                _params=param_specs,
                _needs_confirm=needs_confirm,
                _title=title,
                _desc=desc,
            ) -> None:
                try:
                    if _needs_confirm:
                        ok = messagebox.askyesno("Confirm Action", f"Run action: {_title}?", parent=self.parent)
                        if not ok:
                            return

                    run_kwargs: Dict[str, Any] = {}
                    if isinstance(_args, dict):
                        run_kwargs.update(_args)

                    # If the action definition declares params, collect them with a typed form.
                    if isinstance(_params, list) and _params:
                        try:
                            from core.ui.base_portal_glass import SpecForm  # type: ignore
                        except Exception:
                            SpecForm = None  # type: ignore

                        if SpecForm is None:
                            messagebox.showwarning(
                                "Action Runner",
                                "SpecForm is unavailable; cannot render typed parameter inputs.",
                                parent=self.parent,
                            )
                            return

                        win = tk.Toplevel(self.parent)
                        try:
                            win.title(_title)
                            win.geometry("720x520")
                        except Exception:
                            pass

                        ttk.Label(win, text=_title, font=("Arial", 14, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
                        if _desc:
                            ttk.Label(win, text=_desc, font=("Arial", 9), foreground="gray").pack(
                                anchor="w", padx=12, pady=(0, 10)
                            )

                        form_host = ttk.Frame(win)
                        form_host.pack(fill="both", expand=True, padx=12, pady=(0, 10))

                        form = SpecForm(form_host, _params)
                        form.pack(fill="x", expand=False)

                        btns = ttk.Frame(win)
                        btns.pack(fill="x", padx=12, pady=(0, 12))

                        def _do_run():
                            vals, errs = form.get_values()
                            if errs:
                                messagebox.showerror("Action Runner", "Fix input errors:\n- " + "\n- ".join(errs), parent=win)
                                return
                            try:
                                all_kwargs = dict(run_kwargs)
                                all_kwargs.update(vals)
                                _fn(**all_kwargs) if all_kwargs else _fn()
                            except Exception as e:
                                messagebox.showerror("Action Runner", f"Action failed:\n{e}", parent=win)
                                return
                            try:
                                win.destroy()
                            except Exception:
                                pass

                        ttk.Button(btns, text="Run", command=_do_run).pack(side="left")
                        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="left", padx=(8, 0))
                        return

                    _fn(**run_kwargs) if run_kwargs else _fn()
                except Exception:
                    pass

            _add(action_key, title, desc, _runner)

        return actions, handlers

    def _run_action(self, result: SearchResult, *, close_palette: bool = False) -> None:
        """Execute an action result (best-effort)."""
        action_id = ""
        try:
            action_id = str((result.metadata or {}).get("action_id") or "").strip()
        except Exception:
            action_id = ""
        fn = self._action_handlers.get(action_id)
        if not callable(fn):
            return
        try:
            fn()
        except Exception:
            pass
        if close_palette:
            try:
                self.parent.destroy()
            except Exception:
                pass

    def _create_ui(self):
        """Create search interface"""
        # Main container
        container = ttk.Frame(self.parent)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        title = ttk.Label(container, text="LightSpeed Unified Search",
                         font=('Arial', 18, 'bold'))
        title.pack(pady=(0, 10))

        # Search bar
        search_frame = ttk.Frame(container)
        search_frame.pack(fill=tk.X, pady=10)

        self.search_entry = ttk.Entry(search_frame, font=('Arial', 12))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind('<Return>', lambda e: self._perform_search())
        # Command-palette behavior: focus search input on open.
        try:
            self.parent.after(10, lambda: (self.search_entry.focus_set(), self.search_entry.selection_range(0, tk.END)))
        except Exception:
            pass

        search_btn = ttk.Button(search_frame, text="Search",
                               command=self._perform_search)
        search_btn.pack(side=tk.LEFT, padx=(5, 0))

        # Category filter (combobox is more scalable than radio buttons)
        filter_frame = ttk.Frame(container)
        filter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))

        self.category_display_var = tk.StringVar(value=UnifiedSearchSystem.CATEGORIES.get("all", "all"))
        self.category_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.category_display_var,
            state="readonly",
            values=list(UnifiedSearchSystem.CATEGORIES.values()),
            width=34,
        )
        self.category_combo.pack(side=tk.LEFT)
        try:
            self.category_combo.bind("<<ComboboxSelected>>", lambda _e: self._perform_search())
        except Exception:
            pass

        ttk.Label(filter_frame, text=UnifiedSearchSystem.CATEGORIES.get("all", ""),
                  font=('Arial', 9), foreground='gray').pack(side=tk.LEFT, padx=(10, 0))

        # Results area
        results_frame = ttk.Frame(container)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Results tree
        columns = ('Name', 'Type', 'Category', 'Description')
        self.results_tree = ttk.Treeview(results_frame, columns=columns,
                                         show='headings', height=15)

        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL,
                                 command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        # Bind double-click
        self.results_tree.bind('<Double-Button-1>', self._on_result_select)
        # Right-click should behave like a "real menu": open file/folder actions + cross-floor tools.
        try:
            self.results_tree.bind('<Button-3>', self._on_result_right_click)
        except Exception:
            pass

        # Status bar
        self.status_label = ttk.Label(container, text="Ready",
                                     font=('Arial', 9), foreground='gray')
        self.status_label.pack(pady=(5, 0))

    def _perform_search(self):
        """Execute search"""
        query = (self.search_entry.get() or "").strip()
        cat_name = (self.category_display_var.get() or "").strip()
        category = self._category_name_to_id.get(cat_name, "all")
        # Command-palette affordance: leading ">" means "actions only".
        if query.startswith(">"):
            query = query[1:].lstrip()
            category = "actions"
            try:
                self.category_display_var.set(UnifiedSearchSystem.CATEGORIES.get("actions", "Actions / Commands"))
            except Exception:
                pass

        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Perform search (empty query becomes browse/list)
        self.results = self.search_system.search(query, category=category, max_results=250)

        # Display results
        for result in self.results:
            self.results_tree.insert('', tk.END, values=(
                result.name,
                result.result_type.title(),
                result.category.title(),
                result.description[:60] + '...' if len(result.description) > 60 else result.description
            ))

        # Update status
        if query:
            self.status_label.config(text=f"Found {len(self.results)} results for '{query}'")
        else:
            human = UnifiedSearchSystem.CATEGORIES.get(category, category)
            self.status_label.config(text=f"Listing {len(self.results)} items ({human})")

    def _on_result_select(self, event):
        """Handle result selection"""
        selection = self.results_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        index = self.results_tree.index(item_id)

        if 0 <= index < len(self.results):
            result = self.results[index]
            if result.result_type == "action":
                self._run_action(result, close_palette=True)
                return
            self._show_result_details(result)

    def _on_result_right_click(self, event):
        """Right-click context menu for results (open/copy/details + UniversalFileContextMenu when path-backed)."""
        try:
            iid = self.results_tree.identify_row(event.y)
            if not iid:
                return
            self.results_tree.selection_set(iid)
            index = self.results_tree.index(iid)
        except Exception:
            return

        if not (0 <= index < len(self.results)):
            return
        result = self.results[index]

        # Prefer the universal cross-floor context menu when this result is path-backed.
        p = None
        try:
            p = Path(str(result.path)).expanduser()
            if not p.exists():
                p = None
        except Exception:
            p = None

        if p is not None:
            try:
                from ui.universal_context_menu import UniversalFileContextMenu  # type: ignore

                menu = UniversalFileContextMenu.create(
                    self.results_tree,
                    filepath=(p if p.is_file() else None),
                    folderpath=(p if p.is_dir() else None),
                    show_advanced=True,
                )
                menu.tk_popup(event.x_root, event.y_root)
                menu.grab_release()
                return
            except Exception:
                # Fall back to a minimal Tk menu below.
                pass

        menu = tk.Menu(self.results_tree, tearoff=0)

        def _copy(text: str):
            try:
                self.parent.clipboard_clear()
                self.parent.clipboard_append(text)
            except Exception:
                pass

        if result.result_type == "action":
            menu.add_command(label="Run", command=lambda: self._run_action(result, close_palette=True))
            menu.add_separator()
        menu.add_command(label="Details", command=lambda: self._show_result_details(result))

        rid = ""
        try:
            rid = str(
                result.metadata.get("vault_id")
                or result.metadata.get("knowledge_node_id")
                or result.metadata.get("id")
                or ""
            )
        except Exception:
            rid = ""
        if rid:
            menu.add_command(label="Copy ID", command=lambda: _copy(rid))
        if result.path:
            menu.add_command(label="Copy Path", command=lambda: _copy(str(result.path)))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass

    def _show_result_details(self, result: SearchResult):
        """Show detailed information about a result"""
        # Create detail window
        detail_window = tk.Toplevel(self.parent)
        detail_window.title(f"Details: {result.name}")
        detail_window.geometry("600x400")

        # Content
        container = ttk.Frame(detail_window)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Name
        ttk.Label(container, text=result.name,
                 font=('Arial', 16, 'bold')).pack(anchor='w', pady=(0, 10))

        # Type and category
        ttk.Label(container, text=f"Type: {result.result_type.title()}",
                 font=('Arial', 11)).pack(anchor='w')
        ttk.Label(container, text=f"Category: {result.category.title()}",
                 font=('Arial', 11)).pack(anchor='w', pady=(0, 10))

        # Description
        ttk.Label(container, text="Description:",
                 font=('Arial', 11, 'bold')).pack(anchor='w')
        desc_text = tk.Text(container, height=4, wrap=tk.WORD)
        desc_text.insert('1.0', result.description)
        desc_text.config(state=tk.DISABLED)
        desc_text.pack(fill=tk.X, pady=(0, 10))

        # Path
        ttk.Label(container, text="Path:",
                 font=('Arial', 11, 'bold')).pack(anchor='w')
        ttk.Label(container, text=result.path,
                 font=('Arial', 9), foreground='gray').pack(anchor='w', pady=(0, 10))

        # Actions (open file/folder for anything path-backed; extra affordances for Oracle registry items)
        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(0, 10))

        def _open_path(p: str):
            try:
                if p:
                    os.startfile(p)  # type: ignore[attr-defined]
            except Exception:
                pass

        def _open_folder_for(p: str):
            try:
                if not p:
                    return
                pp = Path(p)
                if pp.is_file():
                    os.startfile(str(pp.parent))  # type: ignore[attr-defined]
                else:
                    os.startfile(str(pp))  # type: ignore[attr-defined]
            except Exception:
                pass

        if result.result_type == "action":
            ttk.Button(
                actions,
                text="Run",
                command=lambda: (self._run_action(result, close_palette=False), detail_window.destroy()),
            ).pack(side=tk.LEFT)

        if result.result_type in ("vault", "calculator", "dataset", "documentation", "tool", "ui"):
            ttk.Button(actions, text="Open", command=lambda: _open_path(result.path)).pack(side=tk.LEFT)
            ttk.Button(actions, text="Open Folder", command=lambda: _open_folder_for(result.path)).pack(side=tk.LEFT, padx=(6, 0))

            if result.result_type == "vault" and result.metadata.get("source_path"):
                ttk.Button(actions, text="Open Source", command=lambda: _open_path(str(result.metadata.get("source_path") or ""))).pack(
                    side=tk.LEFT, padx=(6, 0)
                )

        if result.result_type == "knowledge":
            ttk.Button(actions, text="Browse Sources", command=lambda: self._show_knowledge_sources(result)).pack(side=tk.LEFT)

        if result.result_type == "object":
            # Prefer routing committed objects into the read-only Object Catalog when host wiring exists.
            try:
                host = getattr(self, "host", None)
                fn = getattr(host, "open_object_catalog", None) if host is not None else None
            except Exception:
                fn = None
            if callable(fn):
                obj_kind = str((result.metadata or {}).get("kind") or "all")
                scope = str((result.metadata or {}).get("registry") or "trinity").strip().lower() or "trinity"
                try:
                    ttk.Button(
                        actions,
                        text="Open in Catalog",
                        command=lambda: (fn(scope=scope, kind=obj_kind, query=str((result.metadata or {}).get("id") or "")), detail_window.destroy()),
                    ).pack(side=tk.LEFT)
                except Exception:
                    pass

        # Metadata
        if result.metadata:
            ttk.Label(container, text="Metadata:",
                     font=('Arial', 11, 'bold')).pack(anchor='w')

            meta_text = tk.Text(container, height=6, wrap=tk.WORD)
            for key, value in result.metadata.items():
                if value is not None:
                    meta_text.insert(tk.END, f"{key}: {value}\n")
            meta_text.config(state=tk.DISABLED)
            meta_text.pack(fill=tk.BOTH, expand=True)

        # Close button
        ttk.Button(container, text="Close",
                  command=detail_window.destroy).pack(pady=(10, 0))

    def _show_knowledge_sources(self, result: SearchResult):
        """Show resolved sources for a knowledge node (best-effort)."""
        win = tk.Toplevel(self.parent)
        win.title(f"Sources: {result.name}")
        win.geometry("720x420")

        container = ttk.Frame(win)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        ttk.Label(container, text=f"Knowledge Node: {result.name}", font=("Arial", 12, "bold")).pack(anchor="w")

        sources = result.metadata.get("sources") or []
        if not isinstance(sources, list):
            sources = [sources]

        lst = tk.Listbox(container, height=14)
        lst.pack(fill=tk.BOTH, expand=True, pady=(10, 10))

        resolved = []
        for s in sources:
            vault_id = None
            citation_id = None
            if isinstance(s, dict):
                vault_id = s.get("vault_file_id") or s.get("vault_id")
                citation_id = s.get("citation_id")
            elif isinstance(s, str):
                # Sometimes sources are stored as raw ids/labels.
                if s.isdigit():
                    vault_id = s
            label = f"vault_file_id={vault_id}" if vault_id else str(s)
            if citation_id:
                label += f" citation_id={citation_id}"
            path = self._resolve_oracle_vault_path(str(vault_id)) if vault_id else ""
            if path:
                label += f" -> {path}"
            resolved.append((label, path))
            lst.insert(tk.END, label)

        btns = ttk.Frame(container)
        btns.pack(fill=tk.X)

        def _open_selected():
            try:
                idx = int(lst.curselection()[0])
            except Exception:
                return
            p = resolved[idx][1]
            try:
                if p:
                    os.startfile(p)  # type: ignore[attr-defined]
            except Exception:
                pass

        ttk.Button(btns, text="Open Selected", command=_open_selected).pack(side=tk.LEFT)
        ttk.Button(btns, text="Close", command=win.destroy).pack(side=tk.RIGHT)

    def _resolve_oracle_vault_path(self, vault_id: str) -> str:
        """Resolve Oracle vault_file path from objects.json (cached, best-effort)."""
        vault_id = (vault_id or "").strip()
        if not vault_id:
            return ""

        try:
            if self._oracle_cache is None:
                oracle_objects = (Z_AXIS_ROOT / "Z-2_Oracle" / "Z Direct" / "objects.json").resolve()
                if not oracle_objects.exists():
                    self._oracle_cache = {}
                else:
                    data = json.loads(oracle_objects.read_text(encoding="utf-8", errors="replace"))
                    cache = {}
                    if isinstance(data, list):
                        for it in data:
                            if isinstance(it, dict) and it.get("kind") == "vault_file":
                                cache[str(it.get("id") or "")] = str(it.get("path") or "")
                    self._oracle_cache = cache
            return str((self._oracle_cache or {}).get(vault_id, ""))
        except Exception:
            return ""


def main():
    """Test the search system"""
    root = tk.Tk()
    root.title("LightSpeed Unified Search")
    root.geometry("1000x600")

    search_ui = SearchUI(root)

    root.mainloop()


if __name__ == "__main__":
    main()
