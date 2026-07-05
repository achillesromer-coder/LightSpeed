"""
Dependency Tracker
LightSpeed Platform - Morpheus Floor (Z+2)

Tracks dependencies between files, modules, and packages.
Builds dependency graphs for visualization and analysis.

Author: LightSpeed Team / ACHILLES
Date: December 9, 2025
"""

from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import json
import importlib.util
import re
from dataclasses import dataclass, asdict
from datetime import datetime

from ..services import get_db, EventBus


class DependencyTracker:
    """
    Tracks and analyzes code dependencies.

    Features:
    - Build dependency graphs from imports
    - Detect circular dependencies
    - Find dependency chains
    - Calculate module coupling
    - Identify unused imports
    - Generate dependency reports
    """

    def __init__(self):
        self.db = get_db()
        self.event_bus = EventBus()

    def build_dependency_graph(self, project_id: int) -> Dict[str, List[str]]:
        """
        Build complete dependency graph for a project.

        Args:
            project_id: Project ID

        Returns:
            Dict mapping file paths to their dependencies:
            {
                "/path/to/file1.py": ["/path/to/file2.py", "/path/to/file3.py"],
                ...
            }
        """
        graph = defaultdict(list)

        # Get all code analysis records for project
        query = """
            SELECT f.path, ca.imports
            FROM files f
            JOIN code_analysis ca ON f.id = ca.file_id
            WHERE f.project_id = ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (project_id,))
            rows = cursor.fetchall()

        # Build file path to module mapping
        file_map = self._build_file_map(project_id)

        # Process each file's imports
        for file_path, imports_json in rows:
            if not imports_json:
                continue

            imports = json.loads(imports_json)

            for imp in imports:
                module_name = imp.get('module', '')

                # Try to resolve to actual file
                if module_name in file_map:
                    dependency_path = file_map[module_name]
                    if dependency_path != file_path:
                        graph[file_path].append(dependency_path)

        return dict(graph)

    def find_circular_dependencies(self, project_id: int) -> List[List[str]]:
        """
        Find circular dependency chains.

        Args:
            project_id: Project ID

        Returns:
            List of circular dependency chains:
            [
                ["/path/a.py", "/path/b.py", "/path/a.py"],
                ...
            ]
        """
        graph = self.build_dependency_graph(project_id)
        cycles = []

        def dfs(node: str, path: List[str], visited: Set[str]):
            """Depth-first search for cycles."""
            if node in visited:
                # Found cycle
                if node in path:
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:] + [node]
                    # Only add if we haven't seen this cycle before
                    if cycle not in cycles and cycle[::-1] not in cycles:
                        cycles.append(cycle)
                return

            visited.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, path[:], visited.copy())

        # Check from each node
        for node in graph.keys():
            dfs(node, [], set())

        return cycles

    def get_dependency_chain(self, from_file: str, to_file: str, project_id: int) -> Optional[List[str]]:
        """
        Find dependency chain from one file to another.

        Args:
            from_file: Starting file path
            to_file: Target file path
            project_id: Project ID

        Returns:
            Dependency chain if exists, None otherwise:
            ["/path/from.py", "/path/mid.py", "/path/to.py"]
        """
        graph = self.build_dependency_graph(project_id)

        def bfs(start: str, target: str) -> Optional[List[str]]:
            """Breadth-first search for shortest path."""
            if start == target:
                return [start]

            queue = [(start, [start])]
            visited = {start}

            while queue:
                current, path = queue.pop(0)

                for neighbor in graph.get(current, []):
                    if neighbor == target:
                        return path + [neighbor]

                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))

            return None

        return bfs(from_file, to_file)

    def calculate_coupling(self, project_id: int) -> Dict[str, float]:
        """
        Calculate coupling metrics for each file.

        Coupling = (efferent + afferent) / total_files

        Args:
            project_id: Project ID

        Returns:
            Dict mapping file paths to coupling scores:
            {"/path/to/file.py": 0.15, ...}
        """
        graph = self.build_dependency_graph(project_id)

        # Calculate efferent coupling (outgoing dependencies)
        efferent = {file: len(deps) for file, deps in graph.items()}

        # Calculate afferent coupling (incoming dependencies)
        afferent = defaultdict(int)
        for file, deps in graph.items():
            for dep in deps:
                afferent[dep] += 1

        # Calculate total coupling
        all_files = set(graph.keys()) | set(afferent.keys())
        total_files = len(all_files)

        coupling = {}
        for file in all_files:
            e = efferent.get(file, 0)
            a = afferent.get(file, 0)
            coupling[file] = (e + a) / max(total_files, 1)

        return coupling

    def get_most_coupled_files(self, project_id: int, limit: int = 10) -> List[Dict]:
        """
        Get files with highest coupling.

        Args:
            project_id: Project ID
            limit: Number of results to return

        Returns:
            List of files with coupling info
        """
        coupling = self.calculate_coupling(project_id)

        results = [
            {'file_path': file, 'coupling': score}
            for file, score in coupling.items()
        ]

        results.sort(key=lambda x: x['coupling'], reverse=True)

        return results[:limit]

    def get_file_dependencies(self, file_path: str) -> Dict[str, List[str]]:
        """
        Get dependencies for a specific file.

        Returns:
            Dict with 'imports' (modules imported) and 'imported_by' (files that import this)
        """
        query = """
            SELECT ca.imports
            FROM code_analysis ca
            JOIN files f ON ca.file_id = f.id
            WHERE f.path = ?
            ORDER BY ca.analyzed_at DESC
            LIMIT 1
        """

        imports = []
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (file_path,))
            row = cursor.fetchone()

            if row and row[0]:
                imports_data = json.loads(row[0])
                imports = [imp.get('module', '') for imp in imports_data]

        # Find files that import this one (simplified)
        # Full implementation would need reverse index
        imported_by = []

        return {
            'imports': imports,
            'imported_by': imported_by
        }

    def detect_unused_imports(self, file_path: str) -> List[str]:
        """
        Detect potentially unused imports in a file.

        This is a simplified implementation. Full version would parse
        actual code usage, not just definitions.

        Args:
            file_path: Path to Python file

        Returns:
            List of potentially unused import modules
        """
        # Get imports
        query = """
            SELECT ca.imports, ca.functions, ca.classes
            FROM code_analysis ca
            JOIN files f ON ca.file_id = f.id
            WHERE f.path = ?
            ORDER BY ca.analyzed_at DESC
            LIMIT 1
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (file_path,))
            row = cursor.fetchone()

        if not row:
            return []

        imports = json.loads(row[0]) if row[0] else []
        functions = json.loads(row[1]) if row[1] else []
        classes = json.loads(row[2]) if row[2] else []

        # Extract used names from functions and classes
        used_names = set()
        for func in functions:
            # This is simplified - would need to parse function bodies
            used_names.add(func.get('name', ''))

        for cls in classes:
            used_names.add(cls.get('name', ''))
            for base in cls.get('bases', []):
                used_names.add(base)

        # Check which imports might be unused
        unused = []
        for imp in imports:
            module = imp.get('module', '')
            names = imp.get('names', [])

            # If importing specific names, check if used
            if names and '*' not in names:
                all_unused = True
                for name in names:
                    if name in used_names:
                        all_unused = False
                        break

                if all_unused:
                    unused.append(module)

        return unused

    def generate_dependency_report(self, project_id: int) -> Dict:
        """
        Generate comprehensive dependency report.

        Returns:
            Dict with complete dependency analysis:
            {
                "total_files": 150,
                "total_dependencies": 450,
                "circular_dependencies": [...],
                "most_coupled": [...],
                "avg_coupling": 0.15
            }
        """
        graph = self.build_dependency_graph(project_id)
        circular = self.find_circular_dependencies(project_id)
        coupling = self.calculate_coupling(project_id)
        most_coupled = self.get_most_coupled_files(project_id, limit=10)

        total_deps = sum(len(deps) for deps in graph.values())
        avg_coupling = sum(coupling.values()) / max(len(coupling), 1)

        return {
            'total_files': len(graph),
            'total_dependencies': total_deps,
            'avg_dependencies_per_file': total_deps / max(len(graph), 1),
            'circular_dependencies': circular,
            'circular_count': len(circular),
            'most_coupled': most_coupled,
            'avg_coupling': round(avg_coupling, 4)
        }

    def _build_file_map(self, project_id: int) -> Dict[str, str]:
        """
        Build mapping from module names to file paths.

        Returns:
            Dict mapping module names to file paths
        """
        query = """
            SELECT path, name
            FROM files
            WHERE project_id = ? AND extension = '.py'
        """

        file_map = {}

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (project_id,))
            rows = cursor.fetchall()

        for file_path, file_name in rows:
            # Convert file path to module name
            path = Path(file_path)

            # Simple module name = filename without .py
            if file_name.endswith('.py'):
                module_name = file_name[:-3]
                file_map[module_name] = file_path

            # Also map full dotted path
            # This is simplified - full implementation would handle packages correctly

        return file_map


# ============================================================================
# PLATFORM DEPENDENCY MAPPING (manifests + service registry)
# ============================================================================


@dataclass(frozen=True)
class DependencyNode:
    id: str
    kind: str  # floor|component|service|module|file|group
    label: str
    ok: bool = True
    meta: Dict[str, object] = None

    def to_dict(self) -> Dict[str, object]:
        d = asdict(self)
        if d.get("meta") is None:
            d["meta"] = {}
        return d


@dataclass(frozen=True)
class DependencyEdge:
    source: str
    target: str
    kind: str  # contains|depends_on|implements

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


class PlatformDependencyMapper:
    """
    Builds a cross-floor dependency map using:
    - `Z Axis/*/_FLOOR_MANIFEST.json` (floor/component deps + source files)
    - `Z Axis/Z0_TheConstruct/Config/service_registry.json` (services + modules)

    This is intentionally "safe": it uses `importlib.util.find_spec()` and file existence checks,
    not imports, to avoid side effects during mapping.
    """

    def __init__(self, lightspeed_root: Path):
        self.root = Path(lightspeed_root).resolve()
        self.z_axis_dir = self.root / "Z Axis"
        self.service_registry_path = self.z_axis_dir / "Z0_TheConstruct" / "Config" / "service_registry.json"

    def build(self) -> Dict[str, object]:
        nodes: Dict[str, DependencyNode] = {}
        edges: List[DependencyEdge] = []
        issues = {
            "missing_files": [],
            "unresolvable_modules": [],
            "invalid_module_names": [],
            "missing_manifests": [],
        }

        def add_node(node: DependencyNode) -> None:
            existing = nodes.get(node.id)
            if existing is None:
                nodes[node.id] = node
                return
            if existing.ok and not node.ok:
                nodes[node.id] = node

        def add_edge(source: str, target: str, kind: str) -> None:
            edges.append(DependencyEdge(source=source, target=target, kind=kind))

        _module_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")

        def is_valid_module_name(module: str) -> bool:
            if not module or not isinstance(module, str):
                return False
            return bool(_module_re.match(module))

        def resolve_module(module: str, record_issue: bool = True) -> Dict[str, object]:
            if not module:
                return {"ok": False, "resolution": "missing"}
            if not is_valid_module_name(module):
                if record_issue:
                    issues["invalid_module_names"].append(module)
                # Many manifests use non-importable module strings but include `source_file`.
                return {"ok": False, "resolution": "invalid"}
            try:
                spec = importlib.util.find_spec(module)
                if spec is not None:
                    return {"ok": True, "resolution": "python", "origin": spec.origin or ""}
            except Exception:
                pass

            # Try resolving a floor runner module by file path (`Z Axis/<module>.py`)
            floor_runner = self.z_axis_dir / f"{module}.py"
            if floor_runner.exists():
                return {"ok": True, "resolution": "file", "path": str(floor_runner)}

            if record_issue:
                issues["unresolvable_modules"].append(module)
            return {"ok": False, "resolution": "missing"}

        # Groups
        add_node(DependencyNode(id="group:floors", kind="group", label="Floors"))
        add_node(DependencyNode(id="group:services", kind="group", label="Services"))

        # Floor manifests
        if self.z_axis_dir.exists():
            floor_dirs = [
                d for d in self.z_axis_dir.iterdir()
                if d.is_dir() and d.name.startswith("Z") and (d / "_FLOOR_MANIFEST.json").exists()
            ]
        else:
            floor_dirs = []

        if not floor_dirs:
            issues["missing_manifests"].append(str(self.z_axis_dir))

        for floor_dir in floor_dirs:
            manifest_path = floor_dir / "_FLOOR_MANIFEST.json"
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            floor_key = floor_dir.name
            floor_label = manifest.get("floor_name") or floor_key
            floor_node_id = f"floor:{floor_key}"
            add_node(DependencyNode(id=floor_node_id, kind="floor", label=f"{floor_label} ({floor_key})", meta={
                "floor_name": floor_label,
                "folder": floor_key,
                "z_level": manifest.get("z_level"),
            }))
            add_edge("group:floors", floor_node_id, "contains")

            for dep in (manifest.get("dependencies") or []):
                dep_node_id = f"module:{dep}"
                resolution = resolve_module(dep, record_issue=True)
                add_node(DependencyNode(
                    id=dep_node_id,
                    kind="module",
                    label=dep,
                    ok=bool(resolution.get("ok")),
                    meta=resolution,
                ))
                add_edge(floor_node_id, dep_node_id, "depends_on")

            for comp in (manifest.get("components") or []):
                comp_id = comp.get("id") or "unknown"
                comp_node_id = f"component:{floor_key}:{comp_id}"
                add_node(DependencyNode(
                    id=comp_node_id,
                    kind="component",
                    label=comp.get("name") or comp_id,
                    ok=bool(comp.get("enabled", True)),
                    meta={
                        "floor": floor_key,
                        "component_id": comp_id,
                        "enabled": bool(comp.get("enabled", True)),
                    },
                ))
                add_edge(floor_node_id, comp_node_id, "contains")

                source_file = comp.get("source_file") or ""
                if source_file:
                    candidate = (self.root / source_file).resolve()
                    file_ok = candidate.exists()
                    if not file_ok:
                        issues["missing_files"].append(str(candidate))
                    file_node_id = f"file:{source_file}"
                    add_node(DependencyNode(
                        id=file_node_id,
                        kind="file",
                        label=str(source_file),
                        ok=file_ok,
                        meta={"path": str(candidate)},
                    ))
                    add_edge(comp_node_id, file_node_id, "implements")

                module = comp.get("module") or ""
                if module:
                    mod_node_id = f"module:{module}"
                    resolution = resolve_module(module, record_issue=not bool(source_file))
                    # If a component has a source_file, treat the module string as a label; FloorLoader can load by file.
                    ok = bool(resolution.get("ok")) or bool(source_file)
                    if (not resolution.get("ok")) and source_file:
                        resolution = {**resolution, "resolution": "file_manifest_fallback", "ok": True}
                    add_node(DependencyNode(
                        id=mod_node_id,
                        kind="module",
                        label=module,
                        ok=ok,
                        meta=resolution,
                    ))
                    add_edge(comp_node_id, mod_node_id, "depends_on")

        # Service registry
        if self.service_registry_path.exists():
            try:
                registry = json.loads(self.service_registry_path.read_text(encoding="utf-8"))
            except Exception:
                registry = {}
        else:
            registry = {}

        for service_id, entry in registry.items():
            service_node_id = f"service:{service_id}"
            enabled = bool(entry.get("enabled", True))
            module = entry.get("module") or ""
            add_node(DependencyNode(
                id=service_node_id,
                kind="service",
                label=service_id,
                ok=enabled,
                meta={
                    "type": entry.get("type"),
                    "enabled": enabled,
                    "module": module,
                },
            ))
            add_edge("group:services", service_node_id, "contains")

            if module:
                mod_node_id = f"module:{module}"
                resolution = resolve_module(module, record_issue=True)
                add_node(DependencyNode(
                    id=mod_node_id,
                    kind="module",
                    label=module,
                    ok=bool(resolution.get("ok")),
                    meta=resolution,
                ))
                add_edge(service_node_id, mod_node_id, "depends_on")

        stats = {
            "generated_at": datetime.now().isoformat(),
            "nodes": len(nodes),
            "edges": len(edges),
            "issues": {k: len(v) for k, v in issues.items()},
        }

        return {
            "stats": stats,
            "nodes": [n.to_dict() for n in nodes.values()],
            "edges": [e.to_dict() for e in edges],
            "issues": issues,
        }
