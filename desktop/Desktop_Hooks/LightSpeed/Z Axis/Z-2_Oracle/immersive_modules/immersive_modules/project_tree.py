"""Project Tree Viewer (Immersive Module)

Implements the optional `ProjectTreeViewer` referenced by `LightSpeed/N_UNIFIED.py`.
Shows a tree for `LightSpeed/projects` and allows quick file preview.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any

import tkinter as tk
from tkinter import ttk
import importlib.util

try:
    from core.project_manager import FileHandler
except Exception:
    FileHandler = None


_UCM_MODULE = None


def _find_lightspeed_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
            return candidate
    # Best-effort fallback (repo layout is stable in this workspace).
    return here.parents[4]


def _load_universal_context_menu():
    """
    Lazy-load Trinity's universal context menu by file path.

    We avoid importing `ui.*` directly here because immersive modules may be used
    standalone (outside N.py's sys.path normalization).
    """
    global _UCM_MODULE
    if _UCM_MODULE is not None:
        return _UCM_MODULE

    try:
        root = _find_lightspeed_root()
        ucm_path = (root / "Z Axis" / "Z+3_Trinity" / "ui" / "universal_context_menu.py").resolve()
        if not ucm_path.exists():
            _UCM_MODULE = False
            return None
        spec = importlib.util.spec_from_file_location("lightspeed_universal_context_menu", str(ucm_path))
        if spec is None or spec.loader is None:
            _UCM_MODULE = False
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _UCM_MODULE = mod
        return mod
    except Exception:
        _UCM_MODULE = False
        return None


class ProjectTreeViewer:
    def __init__(self, parent: tk.Widget, colors: Dict[str, str], db=None):
        self.parent = parent
        self.colors = colors
        self.db = db

        self.frame = tk.Frame(parent, bg=colors.get('bg_dark', '#0b1020'))
        self.preview_text: Optional[tk.Text] = None
        self.tree: Optional[ttk.Treeview] = None

    def create_tree_view(self) -> tk.Frame:
        header = tk.Frame(self.frame, bg=self.colors.get('bg_panel', '#102040'))
        header.pack(side='top', fill='x', padx=10, pady=10)

        tk.Label(
            header,
            text='Project Tree',
            bg=self.colors.get('bg_panel', '#102040'),
            fg=self.colors.get('accent_cyan', '#00ffff'),
            font=('Arial', 16, 'bold')
        ).pack(side='left')

        body = tk.Frame(self.frame, bg=self.colors.get('bg_dark', '#0b1020'))
        body.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        left = tk.Frame(body, bg=self.colors.get('bg_panel', '#102040'))
        left.pack(side='left', fill='both', expand=False)

        right = tk.Frame(body, bg=self.colors.get('bg_dark', '#0b1020'))
        right.pack(side='right', fill='both', expand=True, padx=(10, 0))

        self.tree = ttk.Treeview(left)
        ysb = ttk.Scrollbar(left, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=ysb.set)

        self.tree.pack(side='left', fill='both', expand=True)
        ysb.pack(side='right', fill='y')

        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', self._on_open)
        self.tree.bind('<Button-3>', self._on_right_click)

        self.preview_text = tk.Text(
            right,
            bg=self.colors.get('bg_dark', '#0b1020'),
            fg=self.colors.get('text_white', '#ffffff'),
            insertbackground=self.colors.get('accent_cyan', '#00ffff'),
            wrap='none'
        )
        self.preview_text.pack(fill='both', expand=True)

        self._populate_tree()

        return self.frame

    def _populate_tree(self) -> None:
        assert self.tree is not None
        self.tree.delete(*self.tree.get_children())

        ls_root = Path(__file__).resolve().parents[1]
        roots = [ls_root / 'projects', ls_root / 'Z Axis']

        for root in roots:
            if not root.exists():
                continue
            root_id = self.tree.insert('', 'end', text=str(root.relative_to(ls_root)).replace('\\', '/'), values=(str(root), 'dir'))
            self._add_children(root_id, root, depth=3)

    def _add_children(self, parent_id, path: Path, depth: int) -> None:
        if depth <= 0:
            return
        assert self.tree is not None
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception:
            return
        for e in entries:
            kind = 'dir' if e.is_dir() else 'file'
            node_id = self.tree.insert(parent_id, 'end', text=e.name, values=(str(e), kind))
            if e.is_dir():
                self._add_children(node_id, e, depth=depth-1)

    def _selected_path(self) -> Optional[Path]:
        assert self.tree is not None
        sel = self.tree.selection()
        if not sel:
            return None
        values = self.tree.item(sel[0], 'values')
        if not values:
            return None
        return Path(values[0])

    def _on_right_click(self, event) -> None:
        if self.tree is None:
            return
        try:
            item_id = self.tree.identify_row(event.y)
            if item_id:
                self.tree.selection_set(item_id)
        except Exception:
            item_id = None

        p = self._selected_path()
        if not p:
            return

        mod = _load_universal_context_menu()
        if not mod:
            return

        try:
            UniversalFileContextMenu = getattr(mod, "UniversalFileContextMenu", None)
            if UniversalFileContextMenu is None:
                return
            menu = UniversalFileContextMenu.create(
                self.tree,
                filepath=(p if p.is_file() else None),
                folderpath=(p if p.is_dir() else None),
                show_advanced=True,
            )
            menu.tk_popup(event.x_root, event.y_root)
            menu.grab_release()
        except Exception:
            return

    def _on_select(self, _event=None) -> None:
        p = self._selected_path()
        if not p or p.is_dir():
            return
        self._preview(p)

    def _on_open(self, _event=None) -> None:
        p = self._selected_path()
        if not p or p.is_dir():
            return
        try:
            import os
            os.startfile(str(p))
        except Exception:
            pass

    def _preview(self, path: Path) -> None:
        if self.preview_text is None:
            return
        self.preview_text.delete('1.0', 'end')

        if FileHandler is not None:
            preview = FileHandler.read_preview(path)
            if preview.get('success') and 'content' in preview:
                self.preview_text.insert('end', preview['content'])
                return
            self.preview_text.insert('end', f"Preview not available: {preview.get('error', 'unknown')}\n")
            return

        try:
            self.preview_text.insert('end', path.read_text(encoding='utf-8', errors='ignore'))
        except Exception as e:
            self.preview_text.insert('end', f"Cannot preview: {e}\n")
