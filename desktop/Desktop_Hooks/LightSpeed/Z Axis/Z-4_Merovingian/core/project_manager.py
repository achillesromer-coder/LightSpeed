"""
LightSpeed Project Manager
Comprehensive project and file management system

Features:
- Universal file type support (ANY file type)
- Project environment management (venv, dependencies)
- Drag-and-drop file integration
- Dynamic tool/widget registration
- File conversion and export
- Project templates and scaffolding
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import mimetypes


class FileHandler:
    """Universal file handler for any file type."""

    SUPPORTED_CATEGORIES = {
        'text': ['.txt', '.md', '.rst', '.log'],
        'code': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', '.rb'],
        'web': ['.html', '.htm', '.css', '.scss', '.sass', '.jsx', '.tsx', '.vue'],
        'data': ['.json', '.yaml', '.yml', '.xml', '.csv', '.tsv', '.sql'],
        'document': ['.pdf', '.doc', '.docx', '.odt', '.rtf'],
        'spreadsheet': ['.xls', '.xlsx', '.ods', '.csv'],
        'presentation': ['.ppt', '.pptx', '.odp'],
        'image': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico', '.webp'],
        'audio': ['.mp3', '.wav', '.ogg', '.flac', '.m4a'],
        'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
        'archive': ['.zip', '.tar', '.gz', '.bz2', '.7z', '.rar'],
        'config': ['.ini', '.conf', '.cfg', '.env', '.toml'],
        'notebook': ['.ipynb'],
        'cad': ['.dwg', '.dxf', '.stl', '.obj', '.fbx'],
        'other': []  # Catch-all
    }

    @classmethod
    def get_category(cls, file_path: Path) -> str:
        """Get file category from extension."""
        ext = file_path.suffix.lower()

        for category, extensions in cls.SUPPORTED_CATEGORIES.items():
            if ext in extensions:
                return category

        return 'other'

    @classmethod
    def can_preview(cls, file_path: Path) -> bool:
        """Check if file can be previewed in UI."""
        category = cls.get_category(file_path)
        return category in ['text', 'code', 'web', 'data', 'image']

    @classmethod
    def get_mime_type(cls, file_path: Path) -> str:
        """Get MIME type for file."""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'

    @classmethod
    def read_preview(cls, file_path: Path, max_size: int = 100000) -> Dict[str, Any]:
        """
        Read file for preview.

        Returns:
            Dictionary with preview data
        """
        category = cls.get_category(file_path)

        try:
            file_size = file_path.stat().st_size

            if file_size > max_size:
                return {
                    'success': False,
                    'error': 'File too large for preview',
                    'size': file_size,
                    'max_size': max_size
                }

            if category in ['text', 'code', 'web', 'data', 'config']:
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    return {
                        'success': True,
                        'category': category,
                        'content': content,
                        'lines': len(content.splitlines()),
                        'size': file_size
                    }
                except UnicodeDecodeError:
                    return {
                        'success': False,
                        'error': 'Binary file, cannot preview as text',
                        'category': category
                    }

            elif category == 'image':
                return {
                    'success': True,
                    'category': 'image',
                    'path': str(file_path),
                    'size': file_size,
                    'mime_type': cls.get_mime_type(file_path)
                }

            else:
                return {
                    'success': False,
                    'error': f'Preview not supported for {category}',
                    'category': category,
                    'size': file_size
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'category': category
            }


class ProjectEnvironment:
    """Manages project virtual environments and dependencies."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.venv_path = project_path / ".venv"
        self.requirements_file = project_path / "requirements.txt"

    def has_venv(self) -> bool:
        """Check if project has virtual environment."""
        return self.venv_path.exists() and (self.venv_path / "Scripts" / "python.exe").exists()

    def create_venv(self) -> Dict[str, Any]:
        """Create virtual environment for project."""
        try:
            import venv

            venv.create(self.venv_path, with_pip=True)

            return {
                'success': True,
                'path': str(self.venv_path),
                'message': 'Virtual environment created'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def install_requirements(self) -> Dict[str, Any]:
        """Install requirements from requirements.txt."""
        if not self.requirements_file.exists():
            return {
                'success': False,
                'error': 'No requirements.txt found'
            }

        try:
            import subprocess

            pip_exe = self.venv_path / "Scripts" / "pip.exe"

            if not pip_exe.exists():
                return {
                    'success': False,
                    'error': 'Virtual environment not found'
                }

            result = subprocess.run(
                [str(pip_exe), "install", "-r", str(self.requirements_file)],
                capture_output=True,
                text=True
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_installed_packages(self) -> List[str]:
        """Get list of installed packages in venv."""
        try:
            import subprocess

            pip_exe = self.venv_path / "Scripts" / "pip.exe"

            if not pip_exe.exists():
                return []

            result = subprocess.run(
                [str(pip_exe), "list", "--format=freeze"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            else:
                return []

        except Exception:
            return []


class ToolRegistry:
    """Dynamic tool and widget registration system."""

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.categories: Dict[str, List[str]] = {
            'api': [],
            'widget': [],
            'converter': [],
            'analyzer': [],
            'generator': [],
            'integration': []
        }

    def register_tool(
        self,
        name: str,
        category: str,
        handler: Callable,
        description: str = "",
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a new tool.

        Args:
            name: Tool name
            category: Tool category
            handler: Callable function/class
            description: Tool description
            config: Optional configuration
        """
        self.tools[name] = {
            'category': category,
            'handler': handler,
            'description': description,
            'config': config or {},
            'registered_at': datetime.now().isoformat()
        }

        if category in self.categories:
            self.categories[category].append(name)

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool by name."""
        return self.tools.get(name)

    def get_tools_by_category(self, category: str) -> List[str]:
        """Get all tools in a category."""
        return self.categories.get(category, [])

    def list_tools(self) -> Dict[str, List[str]]:
        """List all registered tools by category."""
        return self.categories.copy()


class ProjectManager:
    """
    Comprehensive project manager.

    Features:
    - Create/manage projects with any file types
    - Virtual environment management
    - File organization and versioning
    - Tool/widget integration
    - Export to multiple formats
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.tool_registry = ToolRegistry()
        self._register_default_tools()

    def _floor_folder_map(self) -> Dict[str, str]:
        """
        Map human floor names to canonical Z-Axis folder names.

        Returns:
            Mapping of floor display name -> Z Axis folder name
        """
        return {
            "Merovingian": "Z-4_Merovingian",
            "Smith": "Z-3_Smith",
            "Oracle": "Z-2_Oracle",
            "Morpheus": "Z-1_Morpheus",
            "TheConstruct": "Z0_TheConstruct",
            "Architect": "Z+1_Architect",
            "Neo": "Z+2_Neo",
            "Trinity": "Z+3_Trinity",
        }

    def _find_lightspeed_root(self) -> Path:
        here = Path(__file__).resolve()
        for cand in (here, *here.parents):
            if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                return cand
        return here.parents[5]

    def _apply_z_direct_templates(self, project_path: Path, *, z_floor_names: List[str], metadata: Dict[str, Any]) -> None:
        """
        Initialize per-project Z-Direct scaffolding.

        Each floor can maintain a floor-owned template library under:
            `Z Axis/<FLOOR>/Z Direct/`

        This function mirrors that structure into the project under:
            `Z-Floors/<FloorName>/z_direct/`

        and records the relationship in project metadata for later tooling.
        """
        lightspeed_root = self._find_lightspeed_root()
        z_axis_root = lightspeed_root / "Z Axis"

        folder_map = self._floor_folder_map()
        initialized: Dict[str, Any] = {}

        for floor_name in z_floor_names:
            floor_folder = folder_map.get(floor_name)
            if not floor_folder:
                continue

            z_direct_root = z_axis_root / floor_folder / "Z Direct"
            if not z_direct_root.exists():
                continue

            dest_root = project_path / "Z-Floors" / floor_name / "z_direct"
            dest_root.mkdir(parents=True, exist_ok=True)

            subfolders: List[str] = []
            for entry in sorted(z_direct_root.iterdir(), key=lambda p: p.name.lower()):
                if entry.is_dir():
                    subfolders.append(entry.name)
                    (dest_root / entry.name).mkdir(parents=True, exist_ok=True)
                elif entry.is_file():
                    # Copy top-level template files if present and not yet created.
                    dest = dest_root / entry.name
                    if not dest.exists():
                        try:
                            shutil.copy2(entry, dest)
                        except Exception:
                            pass

            initialized[floor_name] = {
                "source": str(z_direct_root),
                "destination": str(dest_root),
                "subfolders": subfolders,
            }

        if initialized:
            metadata.setdefault("z_direct", {})
            metadata["z_direct"]["initialized"] = True
            metadata["z_direct"]["floors"] = initialized

    def create_project(
        self,
        name: str,
        project_type: str = "general",
        template: Optional[str] = None,
        z_floors: Optional[List[str]] = None,
        expertise_level: str = "intermediate",
        phases: Optional[List[str]] = None,
        description: Optional[str] = None,
        owner_id: Optional[int] = None,
        company_id: Optional[int] = None,
        floor: Optional[str] = None,
        status: str = "active",
        persist_db: bool = True,
    ) -> Dict[str, Any]:
        """
        Create new project with Z-axis integrated structure.

        Enhanced V1.0.0: Now creates proper Z-axis folder structure with sub-projects,
        expertise levels, project phases, and blank template files for each type.

        Args:
            name: Project name
            project_type: Type (python, web, data, general, physics, documentation)
            template: Optional template name
            z_floors: List of Z-floors this project belongs to (default: all)
            expertise_level: Project expertise level (beginner, intermediate, advanced, expert)
            phases: Project phases (planning, development, testing, deployment, maintenance)

        Returns:
            Project creation result with full Z-axis integration
        """
        project_path = self.base_path / name

        if project_path.exists():
            return {
                'success': False,
                'error': f'Project "{name}" already exists'
            }

        try:
            # Create base structure
            project_path.mkdir(parents=True)

            # V1.0.0 Enhancement: Create Z-axis integrated folders
            # Each Z-floor gets dedicated folder with objects and schema subdirectories
            z_floor_names = z_floors or [
                "Merovingian", "Smith", "Oracle", "Morpheus",
                "TheConstruct", "Architect", "Neo", "Trinity"
            ]

            for floor in z_floor_names:
                floor_path = project_path / "Z-Floors" / floor
                (floor_path / "objects").mkdir(parents=True)
                (floor_path / "schema").mkdir(parents=True)
                (floor_path / "components").mkdir(parents=True)

                # Create README for each floor
                readme = floor_path / "README.md"
                readme.write_text(f"# {floor} Floor - {name}\n\n"
                                f"Project-specific resources for {floor} floor.\n\n"
                                f"- **objects/**: Reusable objects and classes\n"
                                f"- **schema/**: Data schemas and definitions\n"
                                f"- **components/**: Floor-specific components\n",
                                encoding='utf-8')

            # Create expertise-based folder structure
            # Projects become more specific as you go down the tree
            expertise_path = project_path / "expertise" / expertise_level
            expertise_path.mkdir(parents=True)

            # Create phase-based folders
            phase_names = phases or ["planning", "development", "testing", "deployment", "maintenance"]
            for phase in phase_names:
                phase_path = project_path / "phases" / phase
                phase_path.mkdir(parents=True)

                # Create blank template files for each phase
                (phase_path / "notes.md").write_text(f"# {phase.title()} Phase Notes\n\n", encoding='utf-8')
                (phase_path / "checklist.md").write_text(f"# {phase.title()} Checklist\n\n- [ ] Task 1\n", encoding='utf-8')

            # Create common directories with enhanced structure
            (project_path / "src").mkdir()
            (project_path / "data" / "raw").mkdir(parents=True)
            (project_path / "data" / "processed").mkdir(parents=True)
            (project_path / "docs" / "architecture").mkdir(parents=True)
            (project_path / "docs" / "api").mkdir(parents=True)
            (project_path / "tests" / "unit").mkdir(parents=True)
            (project_path / "tests" / "integration").mkdir(parents=True)
            (project_path / "output" / "reports").mkdir(parents=True)
            (project_path / "output" / "exports").mkdir(parents=True)

            # Create sub-projects folder structure
            sub_projects_path = project_path / "sub-projects"
            sub_projects_path.mkdir()
            (sub_projects_path / ".gitkeep").touch()  # Keep empty folder in git

            # Create blank template files for each supported file type
            templates_path = project_path / "templates"
            templates_path.mkdir()

            file_templates = {
                'python': ('main.py', '#!/usr/bin/env python\n"""Main module."""\n\n\ndef main():\n    pass\n\n\nif __name__ == "__main__":\n    main()\n'),
                'javascript': ('index.js', '// Main JavaScript file\n\nconsole.log("Hello from LightSpeed!");\n'),
                'html': ('index.html', '<!DOCTYPE html>\n<html>\n<head>\n    <title>LightSpeed Project</title>\n</head>\n<body>\n    <h1>Hello from LightSpeed!</h1>\n</body>\n</html>\n'),
                'css': ('styles.css', '/* Main stylesheet */\n\nbody {\n    font-family: Arial, sans-serif;\n}\n'),
                'markdown': ('README.md', f'# {name}\n\nProject description here.\n'),
                'json': ('config.json', '{\n  "name": "' + name + '",\n  "version": "0.1.0"\n}\n'),
                'yaml': ('config.yaml', f'name: {name}\nversion: 0.1.0\n'),
                'requirements': ('requirements.txt', '# Python dependencies\n'),
                'gitignore': ('.gitignore', '__pycache__/\n*.pyc\n.venv/\n.env\n'),
            }

            for file_type, (filename, content) in file_templates.items():
                template_file = templates_path / filename
                template_file.write_text(content, encoding='utf-8')

            # Create project metadata with V1.0.0 enhancements
            metadata = {
                'name': name,
                'type': project_type,
                'created': datetime.now().isoformat(),
                'version': '0.1.0',
                'expertise_level': expertise_level,
                'phases': phase_names,
                'z_floors': z_floor_names,
                'tools': [],
                'files': [],
                'sub_projects': [],
                'status': status,
                'tags': [],
                'description': description or f'LightSpeed project: {name}',
            }

            # Initialize Z-Direct templates (floor-owned project scaffolding)
            self._apply_z_direct_templates(project_path, z_floor_names=z_floor_names, metadata=metadata)

            metadata_file = project_path / "project.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            # Apply template if specified
            if template:
                self._apply_template(project_path, template, project_type)

            # Save to database if available. This is optional to support legacy call sites
            # that persist project rows elsewhere (avoid duplicate rows).
            db_saved = False
            db_error_str: Optional[str] = None
            if persist_db:
                try:
                    from core.services.database import get_db
                    db = get_db()

                    # Introspect columns to stay compatible with older schemas.
                    cols = set()
                    try:
                        for row in db.get_table_info("projects"):
                            if isinstance(row, dict):
                                cols.add(row.get("name"))
                            else:
                                cols.add(getattr(row, "name", None))
                    except Exception:
                        cols = set()

                    created_at = datetime.now().isoformat()
                    row = {
                        "name": name,
                        "description": description,
                        "type": project_type,
                        "status": status,
                        "owner_id": owner_id,
                        "company_id": company_id,
                        "floor": floor,
                        "path": str(project_path),
                        "metadata": json.dumps(metadata),
                        "created_at": created_at,
                        "updated_at": created_at,
                    }

                    # Filter to columns that exist (and drop None values).
                    insert_cols = []
                    insert_vals = []
                    for k, v in row.items():
                        if v is None:
                            continue
                        if cols and k not in cols:
                            continue
                        insert_cols.append(k)
                        insert_vals.append(v)

                    if not insert_cols:
                        # Very old schema or introspection failure; fall back to minimal insert.
                        db.execute(
                            "INSERT INTO projects (name, type, path, status, created_at, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                            (name, project_type, str(project_path), status, created_at, json.dumps(metadata)),
                        )
                    else:
                        placeholders = ", ".join(["?"] * len(insert_cols))
                        col_sql = ", ".join(insert_cols)
                        db.execute(
                            f"INSERT INTO projects ({col_sql}) VALUES ({placeholders})",
                            tuple(insert_vals),
                        )
                    db_saved = True
                except Exception as db_error:
                    # Database save failed but project created - non-fatal
                    db_error_str = str(db_error)
                    print(f"Warning: Could not save to database: {db_error}")

            return {
                'success': True,
                'path': str(project_path),
                'metadata': metadata,
                'db_saved': db_saved,
                'db_error': db_error_str,
                'message': f'Project "{name}" created with Z-axis structure',
            }

        except Exception as e:
            # Clean up on failure
            if project_path.exists():
                shutil.rmtree(project_path, ignore_errors=True)

            return {
                'success': False,
                'error': str(e)
            }

    def repair_duplicate_project_rows(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Repair duplicate rows in the `projects` table.

        Historically, multiple UI entrypoints persisted project rows (N.py + ProjectManager),
        which could create duplicate DB records for the same project folder. This helper:
        - finds duplicate `projects.name` groups,
        - selects a keeper row (prefers rows referenced by `tasks.project_id`, then richer data),
        - merges missing fields into the keeper,
        - reassigns any tasks to the keeper,
        - deletes the redundant rows.

        When dry_run=True, returns a report without changing the DB.
        """
        try:
            from core.services.database import get_db
            db = get_db()
        except Exception as e:
            return {"success": False, "error": f"Database unavailable: {e}"}

        def _row_get(r: Any, key: str, default: Any = None) -> Any:
            try:
                if isinstance(r, dict):
                    return r.get(key, default)
                return r[key]  # sqlite3.Row supports mapping access
            except Exception:
                return default

        def _truthy(v: Any) -> bool:
            if v is None:
                return False
            if isinstance(v, str):
                return bool(v.strip())
            return True

        try:
            dup_groups = db.fetchall(
                "SELECT name, COUNT(*) AS c FROM projects GROUP BY name HAVING COUNT(*) > 1 ORDER BY c DESC, name ASC"
            )
        except Exception as e:
            return {"success": False, "error": f"Failed to query duplicates: {e}"}

        actions: List[Dict[str, Any]] = []
        deleted_rows = 0
        updated_rows = 0
        moved_tasks = 0

        for grp in dup_groups or []:
            name = _row_get(grp, "name")
            if not name:
                continue

            rows = db.fetchall(
                "SELECT * FROM projects WHERE name=? ORDER BY COALESCE(updated_at, created_at) DESC, id DESC",
                (name,),
            ) or []
            if len(rows) < 2:
                continue

            ids = [int(_row_get(r, "id", 0) or 0) for r in rows]
            ids = [i for i in ids if i > 0]
            if len(ids) < 2:
                continue

            # Prefer a keeper row that is referenced by tasks.
            task_counts: Dict[int, int] = {}
            for pid in ids:
                try:
                    res = db.fetchone("SELECT COUNT(*) AS c FROM tasks WHERE project_id=?", (pid,))
                    task_counts[pid] = int(_row_get(res, "c", 0) or 0)
                except Exception:
                    task_counts[pid] = 0

            def _data_score(r: Any) -> float:
                rid = int(_row_get(r, "id", 0) or 0)
                score = 0.0
                # Hard preference: referenced rows should survive.
                score += float(task_counts.get(rid, 0)) * 1000.0
                if _truthy(_row_get(r, "path")):
                    score += 50.0
                if _truthy(_row_get(r, "metadata")):
                    score += 25.0
                if _truthy(_row_get(r, "description")):
                    score += 10.0
                if _truthy(_row_get(r, "company_id")):
                    score += 5.0
                if _truthy(_row_get(r, "owner_id")):
                    score += 5.0
                if _truthy(_row_get(r, "floor")):
                    score += 2.0
                return score

            keeper = max(rows, key=_data_score)
            keeper_id = int(_row_get(keeper, "id", 0) or 0)
            if keeper_id <= 0:
                continue

            fields = ["description", "type", "status", "owner_id", "company_id", "floor", "path", "metadata", "created_at", "updated_at"]
            merged: Dict[str, Any] = {k: _row_get(keeper, k) for k in fields}
            for k in fields:
                if _truthy(merged.get(k)):
                    continue
                for cand in rows:
                    v = _row_get(cand, k)
                    if _truthy(v):
                        merged[k] = v
                        break

            updates: Dict[str, Any] = {}
            for k in fields:
                v_new = merged.get(k)
                v_old = _row_get(keeper, k)
                if v_new is None:
                    continue
                # Normalize strings
                if isinstance(v_new, str) and isinstance(v_old, str) and v_new == v_old:
                    continue
                if v_new != v_old and _truthy(v_new):
                    updates[k] = v_new

            delete_ids = [int(_row_get(r, "id", 0) or 0) for r in rows if int(_row_get(r, "id", 0) or 0) != keeper_id]
            delete_ids = [i for i in delete_ids if i > 0]

            # How many tasks would be moved?
            task_moves = {pid: task_counts.get(pid, 0) for pid in delete_ids if task_counts.get(pid, 0)}

            actions.append(
                {
                    "name": name,
                    "keep_id": keeper_id,
                    "delete_ids": delete_ids,
                    "update_keeper": updates,
                    "tasks_to_move": task_moves,
                }
            )

            if dry_run:
                continue

            # Apply keeper updates first.
            if updates:
                try:
                    cols = ", ".join([f"{k}=?" for k in updates.keys()])
                    vals = list(updates.values())
                    # Always refresh updated_at on repair.
                    if "updated_at" not in updates:
                        cols += ", updated_at=?"
                        vals.append(datetime.now().isoformat())
                    vals.append(keeper_id)
                    db.execute(f"UPDATE projects SET {cols} WHERE id=?", tuple(vals))
                    updated_rows += 1
                except Exception as e:
                    print(f"Warning: Failed to update keeper row for {name}: {e}")

            # Re-point tasks, then delete redundant rows.
            for pid in delete_ids:
                try:
                    moved = task_counts.get(pid, 0) or 0
                    if moved:
                        db.execute("UPDATE tasks SET project_id=? WHERE project_id=?", (keeper_id, pid))
                        moved_tasks += int(moved)
                except Exception as e:
                    print(f"Warning: Failed to move tasks from project_id={pid} to {keeper_id}: {e}")
                try:
                    db.execute("DELETE FROM projects WHERE id=?", (pid,))
                    deleted_rows += 1
                except Exception as e:
                    print(f"Warning: Failed to delete duplicate project row id={pid}: {e}")

        return {
            "success": True,
            "dry_run": dry_run,
            "duplicate_groups": len(dup_groups or []),
            "updated_rows": updated_rows,
            "deleted_rows": deleted_rows,
            "moved_tasks": moved_tasks,
            "actions": actions,
        }

    def sync_registry_with_filesystem(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Sync the canonical projects table with the filesystem under `base_path`.

        This repairs cases where:
        - a project folder exists on disk but no DB row exists (e.g. created offline / restored)
        - a DB row exists but the folder is missing on disk (marks status='missing' for visibility)

        When dry_run=True, returns a report without changing the DB.
        """
        try:
            from core.services.database import get_db
            db = get_db()
        except Exception as e:
            return {"success": False, "error": f"Database unavailable: {e}"}

        base = Path(str(getattr(self, "base_path", ""))).resolve()
        if not base.exists():
            return {"success": False, "error": f"Projects root not found: {base}"}

        def _row_get(r: Any, key: str, default: Any = None) -> Any:
            try:
                if isinstance(r, dict):
                    return r.get(key, default)
                return r[key]
            except Exception:
                return default

        fs_dirs: Dict[str, Path] = {}
        try:
            for p in base.iterdir():
                if p.is_dir() and not p.name.startswith("."):
                    fs_dirs[p.name] = p
        except Exception as e:
            return {"success": False, "error": f"Failed to scan filesystem: {e}"}

        db_rows = []
        try:
            db_rows = db.fetchall("SELECT id, name, path, status, metadata, created_at, updated_at FROM projects") or []
        except Exception as e:
            return {"success": False, "error": f"Failed to query projects table: {e}"}

        # Only consider DB rows that belong to this projects root (path under base) or have no path.
        owned: Dict[str, List[Dict[str, Any]]] = {}
        for r in db_rows:
            name = str(_row_get(r, "name", "") or "").strip()
            if not name:
                continue
            path = str(_row_get(r, "path", "") or "").strip()
            if path:
                try:
                    rp = Path(path).resolve()
                    if base not in rp.parents and rp != base:
                        continue
                except Exception:
                    # If path is unparsable, ignore it in sync to avoid corrupting unrelated records.
                    continue
            owned.setdefault(name, []).append(
                {
                    "id": int(_row_get(r, "id", 0) or 0),
                    "name": name,
                    "path": path,
                    "status": _row_get(r, "status"),
                    "metadata": _row_get(r, "metadata"),
                    "created_at": _row_get(r, "created_at"),
                    "updated_at": _row_get(r, "updated_at"),
                }
            )

        fs_names = set(fs_dirs.keys())
        db_names = set(owned.keys())

        missing_in_db = sorted(fs_names - db_names, key=str.lower)
        missing_on_disk = sorted(db_names - fs_names, key=str.lower)

        changes = {"add": [], "mark_missing": []}

        # Insert rows for missing folders.
        for name in missing_in_db:
            proj_dir = fs_dirs.get(name)
            if proj_dir is None:
                continue

            description = None
            ptype = None
            status = "active"
            floor = "Architect"
            metadata = None

            # Use project.json metadata if present.
            try:
                pj = proj_dir / "project.json"
                if pj.exists():
                    data = json.loads(pj.read_text(encoding="utf-8", errors="replace"))
                    if isinstance(data, dict):
                        description = data.get("description") if isinstance(data.get("description"), str) else description
                        ptype = data.get("type") if isinstance(data.get("type"), str) else ptype
                        status = data.get("status") if isinstance(data.get("status"), str) else status
                        metadata = json.dumps(data)
            except Exception:
                pass

            changes["add"].append({"name": name, "path": str(proj_dir), "type": ptype, "status": status})
            if dry_run:
                continue

            created_at = datetime.now().isoformat()
            try:
                db.execute(
                    "INSERT INTO projects (name, description, type, status, floor, path, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, description, ptype, status, floor, str(proj_dir), metadata, created_at, created_at),
                )
            except Exception:
                # Back-compat: older schema may not have all columns
                try:
                    db.execute(
                        "INSERT INTO projects (name, type, path, status, created_at, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                        (name, ptype, str(proj_dir), status, created_at, metadata),
                    )
                except Exception as e:
                    return {"success": False, "error": f"Failed to insert missing project '{name}': {e}"}

        # Mark rows missing on disk.
        for name in missing_on_disk:
            rows = owned.get(name) or []
            if not rows:
                continue
            # Only mark the newest row for the name to avoid touching duplicates; duplicates are handled by repair.
            try:
                row = sorted(rows, key=lambda r: int(r.get("id") or 0), reverse=True)[0]
            except Exception:
                row = rows[0]
            pid = int(row.get("id") or 0)
            if pid <= 0:
                continue
            changes["mark_missing"].append({"id": pid, "name": name})
            if dry_run:
                continue
            try:
                db.execute("UPDATE projects SET status=?, updated_at=? WHERE id=?", ("missing", datetime.now().isoformat(), pid))
            except Exception:
                # Older schemas might not have updated_at/status; ignore.
                pass

        return {
            "success": True,
            "dry_run": dry_run,
            "would_add": len(changes["add"]),
            "would_mark_missing": len(changes["mark_missing"]),
            "added": 0 if dry_run else len(changes["add"]),
            "marked_missing": 0 if dry_run else len(changes["mark_missing"]),
            "changes": changes,
        }

    def add_file_to_project(
        self,
        project_name: str,
        source_file: Path,
        destination_dir: str = "data"
    ) -> Dict[str, Any]:
        """
        Add file to project (supports ANY file type).

        Args:
            project_name: Project name
            source_file: Source file path
            destination_dir: Target directory (data, src, docs, etc.)

        Returns:
            Add operation result
        """
        project_path = self.base_path / project_name

        if not project_path.exists():
            return {
                'success': False,
                'error': f'Project "{project_name}" not found'
            }

        try:
            dest_dir = project_path / destination_dir
            dest_dir.mkdir(parents=True, exist_ok=True)

            dest_file = dest_dir / source_file.name

            # Copy file
            shutil.copy2(source_file, dest_file)

            # Update project metadata
            metadata_file = project_path / "project.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                metadata['files'].append({
                    'name': source_file.name,
                    'path': f"{destination_dir}/{source_file.name}",
                    'category': FileHandler.get_category(source_file),
                    'size': source_file.stat().st_size,
                    'added': datetime.now().isoformat()
                })

                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

            return {
                'success': True,
                'destination': str(dest_file),
                'category': FileHandler.get_category(source_file)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_project_files(
        self,
        project_name: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all files in project, optionally filtered by category.

        Args:
            project_name: Project name
            category: Optional file category filter

        Returns:
            List of file information dictionaries
        """
        project_path = self.base_path / project_name

        if not project_path.exists():
            return []

        files = []

        for file_path in project_path.rglob("*"):
            if file_path.is_file() and file_path.name != "project.json":
                file_category = FileHandler.get_category(file_path)

                if category is None or file_category == category:
                    files.append({
                        'name': file_path.name,
                        'path': str(file_path.relative_to(project_path)),
                        'full_path': str(file_path),
                        'category': file_category,
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })

        return sorted(files, key=lambda x: x['modified'], reverse=True)

    def export_project(
        self,
        project_name: str,
        format: str = "zip",
        include_venv: bool = False
    ) -> Dict[str, Any]:
        """
        Export project to archive.

        Args:
            project_name: Project name
            format: Export format (zip, tar, tar.gz)
            include_venv: Include virtual environment

        Returns:
            Export result with file path
        """
        project_path = self.base_path / project_name

        if not project_path.exists():
            return {
                'success': False,
                'error': f'Project "{project_name}" not found'
            }

        try:
            output_name = f"{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if format == "zip":
                output_file = self.base_path / f"{output_name}.zip"
                shutil.make_archive(
                    str(self.base_path / output_name),
                    'zip',
                    project_path,
                    base_dir="."
                )
            elif format in ["tar", "tar.gz"]:
                output_file = self.base_path / f"{output_name}.tar.gz"
                shutil.make_archive(
                    str(self.base_path / output_name),
                    'gztar',
                    project_path,
                    base_dir="."
                )
            else:
                return {
                    'success': False,
                    'error': f'Unsupported format: {format}'
                }

            return {
                'success': True,
                'output_file': str(output_file),
                'size': output_file.stat().st_size
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _apply_template(self, project_path: Path, template: str, project_type: str) -> None:
        """Apply project template."""
        if project_type == "python":
            # Create Python project structure
            (project_path / "requirements.txt").write_text("# Project dependencies\n")
            (project_path / "README.md").write_text(f"# {project_path.name}\n\nPython project\n")

            # Create sample __init__.py
            (project_path / "src" / "__init__.py").write_text("# Package initialization\n")

        elif project_type == "web":
            # Create web project structure
            (project_path / "src" / "index.html").write_text("<!DOCTYPE html>\n<html>\n<head>\n    <title>Project</title>\n</head>\n<body>\n</body>\n</html>\n")
            (project_path / "src" / "style.css").write_text("/* Styles */\n")
            (project_path / "src" / "script.js").write_text("// JavaScript\n")

        elif project_type == "data":
            # Create data science project structure
            (project_path / "notebooks").mkdir()
            (project_path / "requirements.txt").write_text("pandas\nnumpy\nmatplotlib\nseaborn\njupyter\n")
            (project_path / "README.md").write_text(f"# {project_path.name}\n\nData science project\n")

    def archive_to_oracle(
        self,
        project_name: str,
        oracle_root: Path,
        company: str = "default_company",
        workspace: str = "default_workspace"
    ) -> Dict[str, Any]:
        """
        Archive project files to Oracle IP Vault.

        Args:
            project_name: Project name
            oracle_root: Oracle archives root directory
            company: Company identifier
            workspace: Workspace/project identifier

        Returns:
            Archive operation result
        """
        project_path = self.base_path / project_name

        if not project_path.exists():
            return {
                'success': False,
                'error': f'Project "{project_name}" not found'
            }

        try:
            # Create Oracle archives structure
            archives_dir = oracle_root / company / workspace / "archives" / project_name
            archives_dir.mkdir(parents=True, exist_ok=True)

            # Copy all project files to Oracle
            archived_files = []
            errors = []

            for file_path in project_path.rglob("*"):
                if file_path.is_file() and file_path.name != "project.json":
                    # Skip venv
                    if ".venv" in file_path.parts:
                        continue

                    try:
                        # Preserve directory structure
                        rel_path = file_path.relative_to(project_path)
                        dest_file = archives_dir / rel_path
                        dest_file.parent.mkdir(parents=True, exist_ok=True)

                        # Copy file
                        shutil.copy2(file_path, dest_file)
                        archived_files.append(str(rel_path))

                    except Exception as e:
                        errors.append(f"{file_path.name}: {str(e)}")

            # Create archive manifest
            manifest = {
                'project_name': project_name,
                'archived_at': datetime.now().isoformat(),
                'total_files': len(archived_files),
                'files': archived_files,
                'errors': errors
            }

            manifest_file = archives_dir / "archive_manifest.json"
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)

            return {
                'success': True,
                'archived_files': len(archived_files),
                'archive_path': str(archives_dir),
                'manifest': str(manifest_file),
                'errors': errors
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _register_default_tools(self) -> None:
        """Register default tools."""
        # API integrations
        from core.ai.ai_tools import AITools

        self.tool_registry.register_tool(
            'nullschool',
            'api',
            AITools.get_wind_data,
            'Earth wind and weather data visualization'
        )

        self.tool_registry.register_tool(
            'tree_of_life',
            'api',
            AITools.search_tree_of_life,
            'Biodiversity and taxonomy database'
        )

        self.tool_registry.register_tool(
            'qr_generator',
            'generator',
            AITools.generate_qr_code,
            'QR code generation tool'
        )


# Convenience functions
def create_project_manager(base_path: str | None = None) -> ProjectManager:
    """
    Create a ProjectManager instance.

    V1 canonical:
    - Projects are Architect-owned on disk: `Z Axis/Z+1_Architect/projects`.
    - Avoid defaulting to `./projects` (root clutter + breaks floor ownership).
    """
    if base_path:
        return ProjectManager(Path(base_path))

    try:
        from core.config.paths import PROJECTS_ROOT  # type: ignore
        return ProjectManager(Path(PROJECTS_ROOT))
    except Exception:
        return ProjectManager(Path("projects"))
