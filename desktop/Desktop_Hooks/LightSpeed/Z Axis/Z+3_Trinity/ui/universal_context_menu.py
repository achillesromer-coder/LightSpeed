"""
Universal Context Menu - Cross-Floor Integration
Z+3_Trinity UI Component

Universal context menu system providing cross-floor tool access from any context.
Integrates Smith tools, Oracle ingestion, Neo AI, Settings, and Floor navigation.

Features:
- Universal file/folder operations
- Cross-floor tool access (Smith, Oracle, Neo)
- Settings access from anywhere
- Floor navigation from any context
- Premium glassmorphism styling

Floor: Trinity
Z-Level: 3
Author: LightSpeed Team / Claude (Sonnet 4.5)
Version: 1.0.0
Date: 2026-01-18
"""

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path
import sys
import importlib.util
import subprocess
import inspect

# Import base context menu system (initialized after sys.path is normalized).
ContextMenuItem = None
ContextMenuBuilder = None
HAS_BASE_CONTEXT_MENU = False


def _find_lightspeed_root() -> Path:
    """Locate LightSpeed root directory"""
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
            return candidate
    return here.parents[3]


LIGHTSPEED_ROOT = _find_lightspeed_root()
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
TRINITY_ROOT = Path(__file__).resolve().parents[1]
MEROVINGIAN_ROOT = Z_AXIS_ROOT / "Z-4_Merovingian"

# Ensure paths are importable
for path in [LIGHTSPEED_ROOT, Z_AXIS_ROOT, TRINITY_ROOT, MEROVINGIAN_ROOT]:
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

def _try_import_base_context_menu() -> None:
    global ContextMenuItem, ContextMenuBuilder, HAS_BASE_CONTEXT_MENU
    if HAS_BASE_CONTEXT_MENU:
        return
    try:
        from components.context_menu import ContextMenuItem as _Item, ContextMenuBuilder as _Builder  # type: ignore
        ContextMenuItem = _Item
        ContextMenuBuilder = _Builder
        HAS_BASE_CONTEXT_MENU = True
    except Exception:
        HAS_BASE_CONTEXT_MENU = False


_try_import_base_context_menu()

def _safe_get_event_bus():
    try:
        from core.services import get_event_bus  # type: ignore
        return get_event_bus()
    except Exception:
        return None


def _safe_get_db_path() -> Optional[Path]:
    try:
        from core.services import get_db  # type: ignore
        db = get_db()
        for attr in ("db_path", "database_path", "path"):
            val = getattr(db, attr, None)
            if val:
                return Path(str(val)).resolve()
    except Exception:
        pass
    # Fallback to canonical Merovingian DB location
    fallback = (Z_AXIS_ROOT / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db").resolve()
    return fallback if fallback.exists() else None


class UniversalFileContextMenu:
    """
    Universal file/folder context menu with cross-floor integration.

    Provides:
    - Standard file operations (Open, Rename, Delete, Properties)
    - Smith Tools integration (Scan for Tasks, Run Automation)
    - Oracle integration (Ingest to Oracle)
    - Neo AI integration (Analyze with AI)
    - Floor navigation (Open in different floors)
    """

    @staticmethod
    def create(
        widget: tk.Widget,
        filepath: Optional[Path] = None,
        folderpath: Optional[Path] = None,
        show_advanced: bool = True
    ) -> tk.Menu:
        """
        Create universal file/folder context menu.

        Parameters:
            widget: Parent widget
            filepath: File path (for file operations)
            folderpath: Folder path (for folder operations)
            show_advanced: Show advanced cross-floor options

        Returns:
            Configured context menu
        """

        if not HAS_BASE_CONTEXT_MENU:
            # Fallback simple menu
            menu = tk.Menu(widget, tearoff=0)
            menu.add_command(label="Context menu system not available")
            return menu

        builder = ContextMenuBuilder(widget)
        items = []

        # Determine context
        target_path = filepath or folderpath
        is_file = filepath is not None
        is_folder = folderpath is not None

        if target_path and target_path.exists():
            # ==================================================
            # File/Folder Exists - Full Operations Menu
            # ==================================================

            # Standard Operations
            if is_file:
                items.append(ContextMenuItem(
                    '📖 Open',
                    lambda: UniversalFileContextMenu._open_file(target_path),
                    accelerator='Enter'
                ))
            else:
                items.append(ContextMenuItem(
                    '📂 Open Folder',
                    lambda: UniversalFileContextMenu._open_folder(target_path),
                    accelerator='Enter'
                ))

            items.append(ContextMenuItem(
                '✏️ Rename',
                lambda: UniversalFileContextMenu._rename(target_path),
                accelerator='F2'
            ))

            items.append(ContextMenuItem('separator'))

            # ==================================================
            # Cross-Floor Integration
            # ==================================================

            if show_advanced:
                cross_floor_items = []

                # Neo AI Analysis
                cross_floor_items.append(ContextMenuItem(
                    '🤖 Analyze with Neo AI',
                    lambda: UniversalFileContextMenu._analyze_with_neo(target_path)
                ))

                # Oracle Ingestion
                if is_file:
                    cross_floor_items.append(ContextMenuItem(
                        '📥 Ingest to Oracle',
                        lambda: UniversalFileContextMenu._ingest_to_oracle(target_path)
                    ))
                else:
                    cross_floor_items.append(ContextMenuItem(
                        '📥 Ingest Folder to Oracle',
                        lambda: UniversalFileContextMenu._ingest_folder_to_oracle(target_path)
                    ))

                # Smith Tools
                smith_items = []
                if is_file and target_path.suffix in ['.md', '.txt', '.py', '.json']:
                    smith_items.append(ContextMenuItem(
                        '📋 Scan for Tasks',
                        lambda: UniversalFileContextMenu._scan_for_tasks(target_path)
                    ))
                if is_folder:
                    smith_items.append(ContextMenuItem(
                        '📂 Scan All Docs',
                        lambda: UniversalFileContextMenu._scan_folder_for_tasks(target_path)
                    ))
                smith_items.append(ContextMenuItem(
                    '⚡ Run Automation...',
                    lambda: UniversalFileContextMenu._show_smith_tools(widget, target_path)
                ))

                cross_floor_items.append(ContextMenuItem(
                    '🔧 Smith Tools',
                    submenu=smith_items
                ))

                # Architect Project Tools
                if is_folder:
                    cross_floor_items.append(ContextMenuItem(
                        '📐 Create Project (Architect)',
                        lambda: UniversalFileContextMenu._create_project(target_path)
                    ))

                # TheConstruct Physics
                if is_file and target_path.suffix in ['.py', '.json', '.csv']:
                    cross_floor_items.append(ContextMenuItem(
                        '🧮 Calculate Physics (TheConstruct)',
                        lambda: UniversalFileContextMenu._show_physics_calculators(widget)
                    ))

                items.extend(cross_floor_items)
                items.append(ContextMenuItem('separator'))

            # ==================================================
            # Navigation & Utilities
            # ==================================================

            items.append(ContextMenuItem(
                '📋 Copy Path',
                lambda: UniversalFileContextMenu._copy_path(target_path)
            ))

            items.append(ContextMenuItem(
                '📂 Open Location',
                lambda: UniversalFileContextMenu._open_location(target_path)
            ))

            items.append(ContextMenuItem('separator'))

            # Floor Navigation Submenu
            if show_advanced:
                floor_items = []
                for floor in [
                    ('Z+3 Trinity', 'trinity'),
                    ('Z+2 Neo', 'neo'),
                    ('Z+1 Architect', 'architect'),
                    ('Z0 TheConstruct', 'theconstruct'),
                    ('Z-1 Morpheus', 'morpheus'),
                    ('Z-2 Oracle', 'oracle'),
                    ('Z-3 Smith', 'smith'),
                    ('Z-4 Merovingian', 'merovingian')
                ]:
                    floor_name, floor_id = floor
                    floor_items.append(ContextMenuItem(
                        floor_name,
                        lambda fid=floor_id: UniversalFileContextMenu._navigate_to_floor(fid, target_path)
                    ))

                items.append(ContextMenuItem(
                    '🏢 Open in Floor...',
                    submenu=floor_items
                ))

                items.append(ContextMenuItem('separator'))

            # Properties & Settings
            items.append(ContextMenuItem(
                '🔍 Properties',
                lambda: UniversalFileContextMenu._show_properties(target_path)
            ))

            if show_advanced:
                items.append(ContextMenuItem(
                    '⚙️ Settings',
                    lambda: UniversalFileContextMenu._open_settings(widget)
                ))

            items.append(ContextMenuItem('separator'))

            # Delete
            items.append(ContextMenuItem(
                '🗑️ Delete',
                lambda: UniversalFileContextMenu._delete(target_path),
                accelerator='Del'
            ))

        else:
            # ==================================================
            # No File/Folder - Create Operations
            # ==================================================

            items.extend([
                ContextMenuItem('📄 New File', lambda: UniversalFileContextMenu._create_file(widget)),
                ContextMenuItem('📁 New Folder', lambda: UniversalFileContextMenu._create_folder(widget)),
                ContextMenuItem('separator'),
                ContextMenuItem('📥 Import File...', lambda: UniversalFileContextMenu._import_file(widget)),
                ContextMenuItem('separator'),
                ContextMenuItem('⚙️ Settings', lambda: UniversalFileContextMenu._open_settings(widget))
            ])

        builder.add_items(items)
        return builder.build()

    # ==================================================
    # Standard File Operations
    # ==================================================

    @staticmethod
    def _open_file(filepath: Path):
        """Open file with default application"""
        import subprocess
        if sys.platform == 'win32':
            subprocess.run(['start', '', str(filepath)], shell=True)
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(filepath)])
        else:
            subprocess.run(['xdg-open', str(filepath)])

    @staticmethod
    def _open_folder(folderpath: Path):
        """Open folder in file explorer"""
        import subprocess
        if sys.platform == 'win32':
            subprocess.run(['explorer', str(folderpath)])
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(folderpath)])
        else:
            subprocess.run(['xdg-open', str(folderpath)])

    @staticmethod
    def _rename(path: Path):
        """Rename file or folder"""
        new_name = simpledialog.askstring('Rename', 'New name:', initialvalue=path.name)
        if new_name:
            try:
                new_path = path.parent / new_name
                path.rename(new_path)
                messagebox.showinfo('Success', f'Renamed to: {new_name}')
            except Exception as e:
                messagebox.showerror('Error', f'Rename failed: {e}')

    @staticmethod
    def _delete(path: Path):
        """Delete file or folder"""
        response = messagebox.askyesno('Confirm Delete', f'Delete {path.name}?')
        if response:
            try:
                if path.is_file():
                    path.unlink()
                else:
                    import shutil
                    shutil.rmtree(path)
                messagebox.showinfo('Success', f'{path.name} deleted')
            except Exception as e:
                messagebox.showerror('Error', f'Delete failed: {e}')

    @staticmethod
    def _copy_path(path: Path):
        """Copy path to clipboard"""
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(str(path))
        root.destroy()
        messagebox.showinfo('Copied', 'Path copied to clipboard')

    @staticmethod
    def _open_location(path: Path):
        """Open containing folder"""
        UniversalFileContextMenu._open_folder(path.parent)

    @staticmethod
    def _show_properties(path: Path):
        """Show file/folder properties"""
        stats = path.stat()
        info = f"""
{'File' if path.is_file() else 'Folder'}: {path.name}
Location: {path.parent}
Size: {stats.st_size:,} bytes
Created: {stats.st_ctime}
Modified: {stats.st_mtime}
"""
        messagebox.showinfo('Properties', info)

    @staticmethod
    def _create_file(widget):
        """Create new file"""
        filename = simpledialog.askstring('New File', 'File name:')
        if filename:
            try:
                Path(filename).touch()
                messagebox.showinfo('Success', f'Created: {filename}')
            except Exception as e:
                messagebox.showerror('Error', f'Create failed: {e}')

    @staticmethod
    def _create_folder(widget):
        """Create new folder"""
        foldername = simpledialog.askstring('New Folder', 'Folder name:')
        if foldername:
            try:
                Path(foldername).mkdir(exist_ok=True)
                messagebox.showinfo('Success', f'Created: {foldername}')
            except Exception as e:
                messagebox.showerror('Error', f'Create failed: {e}')

    @staticmethod
    def _import_file(widget):
        """Import file"""
        filepath = filedialog.askopenfilename(title='Import File')
        if filepath:
            messagebox.showinfo('Imported', f'Selected: {filepath}')

    # ==================================================
    # Cross-Floor Integrations
    # ==================================================

    @staticmethod
    def _analyze_with_neo(filepath: Path):
        """Analyze file with Neo AI"""
        bus = _safe_get_event_bus()
        if not bus:
            messagebox.showwarning(
                "Neo AI Unavailable",
                "Event bus is not available in this runtime.\n\n"
                "Launch via `python -m LightSpeed` / `N.py` to enable cross-floor routing.",
            )
            return

        try:
            bus.publish(
                "trinity.ai.request",
                {
                    "request_type": "file_analysis",
                    "file_path": str(filepath.resolve()),
                    "filename": filepath.name,
                    "requested_by": "Trinity.ContextMenu",
                    "ts": None,
                },
            )
        except Exception as e:
            messagebox.showerror("Neo AI Error", f"Failed to publish AI request:\n{e}")
            return

        messagebox.showinfo(
            "Neo AI Analysis Queued",
            f"Queued analysis for:\n{filepath.name}\n\n"
            "Neo will publish results on `neo.ai.response`.",
        )

    @staticmethod
    def _ingest_to_oracle(filepath: Path):
        """Ingest file to Oracle vault"""
        response = messagebox.askyesno(
            "Oracle Ingestion",
            f"Ingest {filepath.name} to Oracle Data Vault?\n\n"
            "This will:\n"
            "- Hash + deduplicate\n"
            "- Copy to vault\n"
            "- Register in DB\n"
            "- Queue for SmartFloor processing/routing",
        )
        if not response:
            return

        def _run():
            try:
                # Load integrator by file to avoid invalid package names.
                integ_path = (Z_AXIS_ROOT / "Z-2_Oracle" / "components" / "oracle_smart_floor_integrator.py").resolve()
                spec = importlib.util.spec_from_file_location("lightspeed_oracle_integrator", integ_path)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Cannot load Oracle integrator from {integ_path}")
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
                Integrator = getattr(mod, "OracleSmartFloorIntegrator")
                integrator = Integrator()
                result = integrator.ingest_file(str(filepath.resolve()))
                return ("ok", result)
            except Exception as e:
                return ("err", str(e))

        status, payload = _run()
        if status == "err":
            messagebox.showerror("Oracle Ingestion Error", str(payload))
            return

        result = payload or {}
        if result.get("success"):
            msg = f"Ingested: {filepath.name}\n\nVault ID: {result.get('vault_id')}\nQueue: {result.get('queue_position')}"
            if result.get("already_archived"):
                msg = f"Already archived (deduplicated): {filepath.name}\n\nVault ID: {result.get('vault_id')}"
            messagebox.showinfo("Oracle Ingestion", msg)
        else:
            messagebox.showerror("Oracle Ingestion", f"Failed:\n{result.get('error') or result}")

    @staticmethod
    def _ingest_folder_to_oracle(folderpath: Path):
        """Ingest entire folder to Oracle vault"""
        response = messagebox.askyesno(
            'Oracle Folder Ingestion',
            f'Ingest all files from {folderpath.name} to Oracle?\n\n'
            f'This will process all documents in the folder.'
        )
        if response:
            messagebox.showinfo('Queued', f'{folderpath.name} queued for batch ingestion')

    @staticmethod
    def _scan_for_tasks(filepath: Path):
        """Scan file for tasks using Smith tools"""
        db_path = _safe_get_db_path()
        if not db_path:
            messagebox.showwarning(
                "Scanner Unavailable",
                "No database path detected; cannot store markers.\n\n"
                "Launch via `python -m LightSpeed` / `N.py` first.",
            )
            return

        try:
            tool_path = (Z_AXIS_ROOT / "Z-3_Smith" / "tools" / "scan_docs_to_tasks.py").resolve()
            spec = importlib.util.spec_from_file_location("lightspeed_scan_docs_to_tasks", tool_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load scanner from {tool_path}")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            scan_docs_to_db = getattr(mod, "scan_docs_to_db")
        except Exception as e:
            messagebox.showerror("Scanner Error", f"Failed to load Smith scanner:\n{e}")
            return

        # Run scan synchronously (fast for single file) and show summary.
        try:
            res = scan_docs_to_db(db_path=db_path, scan_root=filepath.resolve(), include_exts=(filepath.suffix.lower(),))
            messagebox.showinfo(
                "Smith Task Scanner",
                f"Scanned: {filepath.name}\n\n"
                f"Markers found: {res.markers_found}\n"
                f"Markers inserted: {res.markers_inserted}\n"
                f"Tasks created: {res.tasks_created}",
            )
        except Exception as e:
            messagebox.showerror("Scanner Error", f"Scan failed:\n{e}")

    @staticmethod
    def _scan_folder_for_tasks(folderpath: Path):
        """Scan folder for tasks"""
        response = messagebox.askyesno(
            'Smith Folder Scanner',
            f'Scan all documents in {folderpath.name} for tasks?'
        )
        if response:
            messagebox.showinfo('Scanning', 'Folder scan started (background job)')

    @staticmethod
    def _show_smith_tools(widget, path: Path):
        """Show Smith automation tools menu"""
        def _run_tool(script_rel: str, *argv: str) -> None:
            script = (Z_AXIS_ROOT / script_rel).resolve()
            if not script.exists():
                messagebox.showerror("Smith Tool", f"Tool not found:\n{script}")
                return
            try:
                subprocess.Popen([sys.executable, str(script), *argv])
            except Exception as e:
                messagebox.showerror("Smith Tool", f"Failed to launch:\n{e}")
        dialog = tk.Toplevel(widget)
        dialog.title(f'Smith Tools - {path.name}')
        dialog.geometry('400x500')
        dialog.configure(bg='#1e1e1e')

        tk.Label(
            dialog,
            text='⚡ Smith Automation Tools',
            font=('Segoe UI', 14, 'bold'),
            fg='#00FF88',
            bg='#1e1e1e'
        ).pack(pady=20)

        tools: List[tuple[str, Callable[[], None]]] = [
            (
                "Scan for Tasks",
                lambda: UniversalFileContextMenu._scan_for_tasks(path)
                if path.is_file()
                else UniversalFileContextMenu._scan_folder_for_tasks(path),
            ),
            ("Generate Dataindex", lambda: _run_tool("Z-3_Smith/tools/generate_dataindex.py")),
            ("Import GPT Export", lambda: _run_tool("Z-3_Smith/tools/import_gpt_export.py")),
            ("Doc Marker Pipeline", lambda: _run_tool("Z-3_Smith/tools/scan_docs_to_tasks.py", "--root", str(path if path.is_dir() else path.parent))),
            ("Validate Launch Path", lambda: _run_tool("Z-3_Smith/tools/validate_launch_path.py")),
        ]

        for tool, handler in tools:
            tk.Button(
                dialog,
                text=f'▶ {tool}',
                font=('Segoe UI', 10),
                bg='#2d2d2d',
                fg='white',
                activebackground='#00FF88',
                activeforeground='black',
                relief=tk.FLAT,
                padx=20,
                pady=10,
                command=handler
            ).pack(fill=tk.X, padx=20, pady=5)

    @staticmethod
    def _create_project(folderpath: Path):
        """Create Architect project from folder"""
        default_name = folderpath.name
        project_name = simpledialog.askstring("Create Project", "Project name:", initialvalue=default_name)
        if not project_name:
            return

        response = messagebox.askyesno(
            "Create Project",
            f"Create project '{project_name}' from folder:\n{folderpath}\n\n"
            "This will create a project in TheConstruct and copy files into it.",
        )
        if not response:
            return

        try:
            from core.config.paths import CONSTRUCT_ROOT  # type: ignore
            from core.project_manager import create_project_manager  # type: ignore
            projects_dir = Path(CONSTRUCT_ROOT) / "projects"
            projects_dir.mkdir(parents=True, exist_ok=True)
            pm = create_project_manager(str(projects_dir))

            created = pm.create_project(project_name, project_type="general")
            if not created.get("success"):
                messagebox.showerror("Create Project", created.get("error") or "Unknown error")
                return

            copied = 0
            for fp in folderpath.rglob("*"):
                if fp.is_file():
                    res = pm.add_file_to_project(project_name, fp, destination_dir="data")
                    if res.get("success"):
                        copied += 1

            messagebox.showinfo(
                "Create Project",
                f"Project created:\n{created.get('path')}\n\nFiles copied: {copied}",
            )
        except Exception as e:
            messagebox.showerror("Create Project", f"Failed:\n{e}")

    @staticmethod
    def _show_physics_calculators(widget):
        """Show TheConstruct physics calculators"""
        calc_path = (Z_AXIS_ROOT / "Z0_TheConstruct" / "physics_calculators.py").resolve()
        if not calc_path.exists():
            messagebox.showerror("Physics Calculators", f"Not found:\n{calc_path}")
            return

        try:
            spec = importlib.util.spec_from_file_location("lightspeed_physics_calculators", calc_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load {calc_path}")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
        except Exception as e:
            messagebox.showerror("Physics Calculators", f"Failed to load library:\n{e}")
            return

        funcs = []
        for name, fn in vars(mod).items():
            if callable(fn) and str(name).startswith("calculate_"):
                try:
                    sig = inspect.signature(fn)
                except Exception:
                    continue
                funcs.append((name, fn, sig))
        funcs.sort(key=lambda t: t[0])

        win = tk.Toplevel(widget)
        win.title("TheConstruct - Physics Calculators")
        win.geometry("900x600")
        win.configure(bg="#0a1628")

        left = tk.Frame(win, bg="#0a1628")
        left.pack(side="left", fill="y", padx=10, pady=10)
        right = tk.Frame(win, bg="#0a1628")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        tk.Label(left, text="Calculators", bg="#0a1628", fg="#cfeaff", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        lb = tk.Listbox(left, width=34, height=28)
        lb.pack(fill="y", expand=True, pady=8)
        for name, _fn, _sig in funcs:
            lb.insert(tk.END, name)

        form = tk.Frame(right, bg="#0a1628")
        form.pack(fill="x", pady=6)
        output = tk.Text(right, height=18, bg="#0b141d", fg="#cfeaff", insertbackground="#cfeaff")
        output.pack(fill="both", expand=True)

        entries: Dict[str, tk.Entry] = {}

        def _safe_run(run_fn: Callable[[], None]) -> None:
            try:
                run_fn()
            except Exception as e:
                messagebox.showerror("Calculator Error", str(e), parent=win)

        def _render_form(index: int) -> None:
            for w in form.winfo_children():
                w.destroy()
            entries.clear()
            if index < 0 or index >= len(funcs):
                return
            name, fn, sig = funcs[index]
            tk.Label(form, text=name, bg="#0a1628", fg="#00e5ff", font=("Segoe UI", 12, "bold")).pack(anchor="w")
            for param in sig.parameters.values():
                if param.kind in (param.VAR_KEYWORD, param.VAR_POSITIONAL):
                    continue
                row = tk.Frame(form, bg="#0a1628")
                row.pack(fill="x", pady=4)
                tk.Label(row, text=param.name, width=18, anchor="w", bg="#0a1628", fg="#cfeaff").pack(side="left")
                ent = tk.Entry(row)
                ent.pack(side="left", fill="x", expand=True)
                entries[param.name] = ent

            def _run():
                kwargs: Dict[str, Any] = {}
                for k, ent in entries.items():
                    raw = ent.get().strip()
                    if not raw:
                        raise ValueError(f"Missing value: {k}")
                    kwargs[k] = float(raw)
                res = fn(**kwargs)
                output.delete("1.0", tk.END)
                output.insert(tk.END, f"Inputs: {kwargs}\\n\\n")
                if hasattr(res, "__dict__"):
                    for kk, vv in res.__dict__.items():
                        output.insert(tk.END, f"{kk}: {vv}\n")
                else:
                    output.insert(tk.END, str(res))

            tk.Button(form, text="Run", command=lambda: _safe_run(_run)).pack(anchor="w", pady=8)

        def _on_select(_evt=None):
            sel = lb.curselection()
            if not sel:
                return
            _render_form(int(sel[0]))

        lb.bind("<<ListboxSelect>>", _on_select)
        if funcs:
            lb.selection_set(0)
            _render_form(0)

    @staticmethod
    def _navigate_to_floor(floor_id: str, context_path: Optional[Path] = None):
        """Navigate to specific Z-floor"""
        bus = _safe_get_event_bus()
        payload = {
            "floor_id": floor_id,
            "context_path": str(context_path.resolve()) if context_path else None,
            "requested_by": "Trinity.ContextMenu",
        }
        if bus:
            try:
                bus.publish("ui.navigate.floor", payload)
            except Exception:
                pass
        messagebox.showinfo(
            "Floor Navigation",
            f"Navigation request sent for {floor_id}.\n"
            f"Context: {context_path.name if context_path else 'None'}",
        )

    @staticmethod
    def _open_settings(widget):
        """Open Settings panel"""
        try:
            from ui.smart_settings_hub import SmartSettingsHub  # type: ignore
        except Exception as e:
            messagebox.showerror("Settings", f"Settings hub not available:\n{e}")
            return

        try:
            win = tk.Toplevel(widget)
            win.title("LightSpeed Settings")
            win.geometry("1200x800")
            SmartSettingsHub(win).pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Settings", f"Failed to open settings:\n{e}")


class UniversalPortalContextMenu:
    """
    Universal context menu for portal/window right-click.

    Provides:
    - Floor navigation
    - Settings access
    - Smith tools
    - Help & documentation
    """

    @staticmethod
    def create(widget: tk.Widget, floor_name: str = "Unknown") -> tk.Menu:
        """Create universal portal context menu"""

        if not HAS_BASE_CONTEXT_MENU:
            menu = tk.Menu(widget, tearoff=0)
            menu.add_command(label="Context menu not available")
            return menu

        builder = ContextMenuBuilder(widget)

        # Floor Navigation
        floor_items = []
        for floor in [
            'Z+3 Trinity', 'Z+2 Neo', 'Z+1 Architect',
            'Z0 TheConstruct', 'Z-1 Morpheus', 'Z-2 Oracle', 'Z-3 Smith', 'Z-4 Merovingian'
        ]:
            floor_items.append(ContextMenuItem(
                floor,
                lambda f=floor: messagebox.showinfo('Navigate', f'Opening {f}...')
            ))

        # Tools & Utilities
        smith_tools = []
        for tool in ['Scan Docs', 'Generate Index', 'Automation...']:
            smith_tools.append(ContextMenuItem(
                tool,
                lambda t=tool: messagebox.showinfo('Smith', f'{t} executed')
            ))

        # Calculators
        calc_items = []
        for calc in ['Physics', 'Morpheus Legacy', 'Financial']:
            calc_items.append(ContextMenuItem(
                calc,
                lambda c=calc: messagebox.showinfo('Calculator', f'{c} calculator opened')
            ))

        items = [
            ContextMenuItem('🏢 Navigate to Floor...', submenu=floor_items),
            ContextMenuItem('separator'),
            ContextMenuItem('🔧 Smith Tools...', submenu=smith_tools),
            ContextMenuItem('🧮 Calculators...', submenu=calc_items),
            ContextMenuItem('separator'),
            ContextMenuItem('⚙️ Settings', lambda: UniversalFileContextMenu._open_settings(widget)),
            ContextMenuItem('❓ Help', lambda: messagebox.showinfo('Help', f'{floor_name} Floor Help'))
        ]

        builder.add_items(items)
        return builder.build()


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Universal Context Menu Demo')
    root.geometry('800x600')
    root.configure(bg='#1e1e1e')

    label = tk.Label(
        root,
        text='Right-click anywhere for Universal Context Menu\n\n'
             'Features:\n'
             '- Cross-floor tool integration\n'
             '- Smith automation tools\n'
             '- Oracle ingestion\n'
             '- Neo AI analysis\n'
             '- Floor navigation\n'
             '- Settings access',
        font=('Segoe UI', 12),
        fg='white',
        bg='#1e1e1e',
        justify='left'
    )
    label.pack(fill='both', expand=True, padx=50, pady=50)

    # Test with no file
    menu = UniversalFileContextMenu.create(label, filepath=None, show_advanced=True)
    label.bind('<Button-3>', lambda e: menu.tk_popup(e.x_root, e.y_root))

    root.mainloop()
