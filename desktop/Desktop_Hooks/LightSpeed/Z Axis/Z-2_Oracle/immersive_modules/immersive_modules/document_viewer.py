"""Document Viewer (Immersive Module)

Implements the optional `DocumentViewer` referenced by `LightSpeed/N_UNIFIED.py`.
Provides a simple, universal preview surface for common file types.

- Text/code/data: in-app preview
- Images: preview if Pillow is available
- PDFs/other: open externally (fallback)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Dict, Any, List

import tkinter as tk
from tkinter import ttk, filedialog
import importlib.util

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except Exception:
    HAS_PIL = False

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
    return here.parents[4]


def _load_universal_context_menu():
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


class DocumentViewer:
    def __init__(self, parent: tk.Widget, colors: Dict[str, str], db=None):
        self.parent = parent
        self.colors = colors
        self.db = db

        self.frame = tk.Frame(parent, bg=colors.get('bg_dark', '#0b1020'))
        self.current_path: Optional[Path] = None

        self._image_ref = None

    def create_viewer(self) -> tk.Frame:
        toolbar = tk.Frame(self.frame, bg=self.colors.get('bg_panel', '#102040'))
        toolbar.pack(side='top', fill='x', padx=10, pady=10)

        tk.Label(
            toolbar,
            text='Document Viewer',
            bg=self.colors.get('bg_panel', '#102040'),
            fg=self.colors.get('accent_cyan', '#00ffff'),
            font=('Arial', 16, 'bold')
        ).pack(side='left')

        tk.Button(
            toolbar,
            text='Open File',
            command=self._pick_file,
            bg=self.colors.get('accent_magenta', '#ff00ff'),
            fg='white',
            padx=12,
            pady=6
        ).pack(side='right', padx=6)

        tk.Button(
            toolbar,
            text='Open Object Library',
            command=self._open_object_library,
            bg=self.colors.get('border_blue', '#0055ff'),
            fg='white',
            padx=12,
            pady=6
        ).pack(side='right', padx=6)

        body = tk.Frame(self.frame, bg=self.colors.get('bg_dark', '#0b1020'))
        body.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        left = tk.Frame(body, bg=self.colors.get('bg_panel', '#102040'))
        left.pack(side='left', fill='y', padx=(0, 10))

        tk.Label(
            left,
            text='Quick Docs',
            bg=self.colors.get('bg_panel', '#102040'),
            fg=self.colors.get('text_cyan', '#00ddff'),
            font=('Arial', 11, 'bold')
        ).pack(anchor='w', padx=10, pady=(10, 6))

        self.docs_list = tk.Listbox(
            left,
            width=35,
            bg=self.colors.get('bg_dark', '#0b1020'),
            fg=self.colors.get('text_white', '#ffffff'),
            highlightthickness=0,
            selectbackground=self.colors.get('accent_pink', '#ff0088')
        )
        self.docs_list.pack(fill='y', expand=True, padx=10, pady=(0, 10))
        self.docs_list.bind('<<ListboxSelect>>', self._on_select_doc)
        self.docs_list.bind('<Button-3>', self._on_docs_right_click)

        self._populate_quick_docs()

        right = tk.Frame(body, bg=self.colors.get('bg_dark', '#0b1020'))
        right.pack(side='right', fill='both', expand=True)

        self.path_var = tk.StringVar(value='(no file open)')
        tk.Label(
            right,
            textvariable=self.path_var,
            bg=self.colors.get('bg_dark', '#0b1020'),
            fg=self.colors.get('text_light', '#98989d'),
            anchor='w'
        ).pack(fill='x', pady=(0, 6))

        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill='both', expand=True)

        self.preview_frame = tk.Frame(self.notebook, bg=self.colors.get('bg_dark', '#0b1020'))
        self.info_frame = tk.Frame(self.notebook, bg=self.colors.get('bg_dark', '#0b1020'))
        self.notebook.add(self.preview_frame, text='Preview')
        self.notebook.add(self.info_frame, text='Info')

        self.text = tk.Text(
            self.preview_frame,
            bg=self.colors.get('bg_dark', '#0b1020'),
            fg=self.colors.get('text_white', '#ffffff'),
            insertbackground=self.colors.get('accent_cyan', '#00ffff'),
            wrap='none'
        )
        self.text.pack(fill='both', expand=True)

        self.image_label = tk.Label(
            self.preview_frame,
            bg=self.colors.get('bg_dark', '#0b1020'),
            fg=self.colors.get('text_white', '#ffffff')
        )

        self.info_text = tk.Text(
            self.info_frame,
            bg=self.colors.get('bg_dark', '#0b1020'),
            fg=self.colors.get('text_white', '#ffffff'),
            insertbackground=self.colors.get('accent_cyan', '#00ffff'),
            wrap='word',
            height=10
        )
        self.info_text.pack(fill='both', expand=True)
        self.info_text.config(state='disabled')

        return self.frame

    def _populate_quick_docs(self) -> None:
        self.docs_list.delete(0, 'end')
        ls_root = Path(__file__).resolve().parents[1]
        for name in sorted(p.name for p in ls_root.iterdir() if p.is_file() and p.suffix.lower() in {'.md', '.txt', '.json'}):
            self.docs_list.insert('end', name)

    def _on_select_doc(self, _event=None) -> None:
        sel = self.docs_list.curselection()
        if not sel:
            return
        name = self.docs_list.get(sel[0])
        ls_root = Path(__file__).resolve().parents[1]
        path = ls_root / name
        if path.exists():
            self.open_file(path)

    def _on_docs_right_click(self, event=None) -> None:
        if event is None:
            return
        try:
            idx = self.docs_list.nearest(event.y)
            if idx is None:
                return
            self.docs_list.selection_clear(0, 'end')
            self.docs_list.selection_set(idx)
        except Exception:
            return

        try:
            name = self.docs_list.get(idx)
        except Exception:
            return

        ls_root = Path(__file__).resolve().parents[1]
        p = ls_root / name
        if not p.exists():
            return

        mod = _load_universal_context_menu()
        if not mod:
            return
        try:
            UniversalFileContextMenu = getattr(mod, "UniversalFileContextMenu", None)
            if UniversalFileContextMenu is None:
                return
            menu = UniversalFileContextMenu.create(
                self.docs_list,
                filepath=p,
                folderpath=None,
                show_advanced=True,
            )
            menu.tk_popup(event.x_root, event.y_root)
            menu.grab_release()
        except Exception:
            return

    def _pick_file(self) -> None:
        path = filedialog.askopenfilename(title='Open file')
        if path:
            self.open_file(Path(path))

    def _open_object_library(self) -> None:
        ls_root = Path(__file__).resolve().parents[1]
        p = ls_root / 'knowledge' / 'reference' / 'OBJECT_LIBRARY.json'
        if p.exists():
            self.open_file(p)
        else:
            self._set_info({'error': f'Not found: {p}'})

    def open_file(self, path: Path) -> None:
        self.current_path = path
        self.path_var.set(str(path))

        # Reset preview widgets
        self.image_label.pack_forget()
        self.text.pack(fill='both', expand=True)
        self.text.delete('1.0', 'end')
        self._image_ref = None

        info: Dict[str, Any] = {
            'path': str(path),
            'exists': path.exists(),
            'size': path.stat().st_size if path.exists() else None,
            'suffix': path.suffix.lower(),
        }

        # Prefer FileHandler preview if available
        if FileHandler is not None and path.exists():
            preview = FileHandler.read_preview(path)
            info['preview'] = {k: v for k, v in preview.items() if k != 'content'}
            if preview.get('success') and 'content' in preview:
                self.text.insert('end', preview['content'])
                self._set_info(info)
                return
            if preview.get('success') and preview.get('category') == 'image':
                self._preview_image(path)
                self._set_info(info)
                return

        # Fallback: open externally for PDFs/unknown
        if path.suffix.lower() == '.pdf':
            self.text.insert('end', 'PDF preview is not built-in. Opening externally...\n')
            self._open_external(path)
            self._set_info(info)
            return

        # Fallback: naive text read
        try:
            text = path.read_text(encoding='utf-8', errors='ignore')
            self.text.insert('end', text)
        except Exception as e:
            self.text.insert('end', f'Cannot preview file: {e}\n')
            self._open_external(path)

        self._set_info(info)

    def _preview_image(self, path: Path) -> None:
        if not HAS_PIL:
            self.text.insert('end', 'Image preview requires Pillow (PIL).\n')
            return
        try:
            img = Image.open(path)
            img.thumbnail((1100, 700))
            self._image_ref = ImageTk.PhotoImage(img)
            self.text.pack_forget()
            self.image_label.config(image=self._image_ref, text='')
            self.image_label.pack(fill='both', expand=True)
        except Exception as e:
            self.text.insert('end', f'Image preview failed: {e}\n')

    def _open_external(self, path: Path) -> None:
        try:
            os.startfile(str(path))  # Windows
        except Exception:
            pass

    def _set_info(self, info: Dict[str, Any]) -> None:
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', 'end')
        self.info_text.insert('end', json_pretty(info))
        self.info_text.config(state='disabled')


def json_pretty(data: Any) -> str:
    import json
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return str(data)
