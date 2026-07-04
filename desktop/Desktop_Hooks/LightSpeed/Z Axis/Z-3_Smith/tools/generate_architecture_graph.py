#!/usr/bin/env python
"""
Generate an architecture graph for the LightSpeed workspace.

Goal: represent the *runtime codebase* as nodes/edges so we can simplify safely:
- file nodes (.py, plus select config/manifest nodes)
- edges for: imports, dynamic file-load hooks, floor manifests, service registry, event bus topics

This script is intentionally conservative:
- It avoids scanning huge archives/datasets/logs.
- It never mutates runtime state; it only reads files and writes graph outputs under `dataindex/`.
"""

from __future__ import annotations

import ast
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for cand in (start, *start.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return start.parent


def _read_text(path: Path) -> str:
    data = path.read_text(encoding="utf-8", errors="replace")
    if data.startswith("\ufeff"):
        data = data[1:]
    return data


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def _iter_python_files(root: Path) -> List[Path]:
    """
    Runtime-code scope: exclude bulk artifacts/archives/logs/toolchains.
    """
    exclude_dir_names = {
        "__pycache__",
        ".pytest_cache",
        ".git",
        "node_modules",
        "dist",
        "build",
        # bulk runtime artifacts/logs
        "ai_logs",
        "operations",
        "w6",
        "data",
        "Data",
    }

    # Prefix exclusions for known huge vendored/toolchain/data trees.
    prefix_excludes = [
        root / "Z Axis" / "archive",
        root / "Z Axis" / "Z-1_Morpheus" / "library",
        root / "Z Axis" / "Z-1_Morpheus" / "organization",
        root / "Z Axis" / "Z-2_Oracle" / "archive",
        root / "Z Axis" / "Z-2_Oracle" / "vault",
        root / "Z Axis" / "Z-2_Oracle" / "Data",
        root / "Z Axis" / "Z0_TheConstruct" / "data",
        root / "Z Axis" / "Z0_TheConstruct" / "tools" / "GMAT",
        root / "Z Axis" / "Z0_TheConstruct" / "tools" / "GMAT_R2025a",
    ]
    prefix_excludes_norm = [str(p.resolve()).replace("\\", "/").lower() for p in prefix_excludes]

    py_files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)
        dp_norm = str(dp.resolve()).replace("\\", "/").lower()
        if any(dp_norm.startswith(pref) for pref in prefix_excludes_norm):
            dirnames[:] = []
            continue

        # prune dirnames in-place
        dirnames[:] = [d for d in dirnames if d not in exclude_dir_names]
        for fn in filenames:
            if fn.endswith(".py"):
                py_files.append(dp / fn)
    return py_files


def _module_name_candidates(path: Path, base: Path) -> List[str]:
    """
    Compute module name candidates for a file under a sys.path root `base`.
    """
    try:
        rel = path.relative_to(base)
    except Exception:
        return []

    parts = list(rel.parts)
    if not parts:
        return []

    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]  # drop .py
    parts = [p for p in parts if p]
    if not parts:
        return []
    return [".".join(parts)]


def _build_module_index(root: Path, py_files: Iterable[Path]) -> Dict[str, str]:
    """
    Build a best-effort module->file index for import resolution.

    The platform mutates sys.path at runtime, so we simulate the common roots:
    - repo root
    - Z Axis
    - each Z-floor directory
    - Z-4_Merovingian (so `core.*` resolves)
    """
    bases: List[Path] = [root, root / "Z Axis"]
    z_axis = root / "Z Axis"
    if z_axis.exists():
        for floor_dir in z_axis.iterdir():
            if floor_dir.is_dir() and floor_dir.name.startswith("Z"):
                bases.append(floor_dir)
        bases.append(z_axis / "Z-4_Merovingian")  # provides `core.*`

    index: Dict[str, str] = {}
    for p in py_files:
        for base in bases:
            for mod in _module_name_candidates(p, base):
                # Do not overwrite an earlier mapping; prefer the first hit to keep stability.
                index.setdefault(mod, _safe_rel(p, root))
    return index


@dataclass
class ParsedFile:
    relpath: str
    imports: List[str]
    dynamic_files: List[str]
    publish_topics: List[str]
    subscribe_topics: List[str]
    parse_error: Optional[str] = None


_DYNAMIC_FILE_PATTERNS = (
    # internal dynamic file-load helpers
    "_load_symbol_from_file",
    "_load_symbol",
    "_load_class_from_file",
    "spec_from_file_location",
)


def _extract_call_str_arg(node: ast.Call, pos: int = 0) -> Optional[str]:
    try:
        if len(node.args) <= pos:
            return None
        arg = node.args[pos]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    except Exception:
        return None
    return None


def _parse_python_file(root: Path, path: Path) -> ParsedFile:
    rel = _safe_rel(path, root)
    try:
        src = _read_text(path)
        tree = ast.parse(src, filename=str(path))
    except Exception as e:
        return ParsedFile(rel, [], [], [], [], parse_error=f"{type(e).__name__}: {str(e)[:160]}")

    imports: List[str] = []
    dynamic_files: List[str] = []
    pub: List[str] = []
    sub: List[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

        # capture dynamic file-load patterns (string literal paths)
        if isinstance(node, ast.Call):
            fn = node.func
            fn_name = None
            if isinstance(fn, ast.Name):
                fn_name = fn.id
            elif isinstance(fn, ast.Attribute):
                fn_name = fn.attr

            if fn_name in _DYNAMIC_FILE_PATTERNS:
                s = _extract_call_str_arg(node, 0)
                if s:
                    dynamic_files.append(s)

            # EventBus publish/subscribe topics (best-effort)
            if fn_name in ("publish", "subscribe"):
                topic = _extract_call_str_arg(node, 0)
                if topic:
                    if fn_name == "publish":
                        pub.append(topic)
                    else:
                        sub.append(topic)

    # normalize a bit
    imports = sorted(set(imports))
    dynamic_files = sorted(set(dynamic_files))
    pub = sorted(set(pub))
    sub = sorted(set(sub))

    return ParsedFile(rel, imports, dynamic_files, pub, sub, parse_error=None)


def _load_floor_manifests(root: Path) -> List[Dict[str, Any]]:
    manifests: List[Dict[str, Any]] = []
    z_axis = root / "Z Axis"
    if not z_axis.exists():
        return manifests
    for floor_dir in sorted(z_axis.iterdir(), key=lambda p: p.name):
        if not floor_dir.is_dir() or not floor_dir.name.startswith("Z"):
            continue
        fp = floor_dir / "_FLOOR_MANIFEST.json"
        if not fp.exists():
            continue
        try:
            payload = json.loads(_read_text(fp))
            payload["_manifest_path"] = _safe_rel(fp, root)
            payload["_floor_dir"] = floor_dir.name
            manifests.append(payload)
        except Exception:
            continue
    return manifests


def _load_service_registry(root: Path) -> Dict[str, Any]:
    path = root / "Z Axis" / "Z0_TheConstruct" / "Config" / "service_registry.json"
    if not path.exists():
        return {}
    try:
        return json.loads(_read_text(path))
    except Exception:
        return {}


def _resolve_rel_file(root: Path, s: str) -> Optional[str]:
    """
    Resolve a discovered string path into a repo-relative path when possible.
    """
    val = (s or "").strip().strip("\"'").replace("\\", "/")
    if not val:
        return None

    # Common case: repository-relative "Z Axis/..." style.
    candidate = (root / val).resolve()
    if candidate.exists():
        return _safe_rel(candidate, root)

    # Sometimes strings are nested like "Z Axis\\Z+3_Trinity\\...".
    if val.lower().startswith("z axis/"):
        candidate = (root / val).resolve()
        if candidate.exists():
            return _safe_rel(candidate, root)

    return None


def build_graph(root: Path) -> Dict[str, Any]:
    py_files = _iter_python_files(root)
    module_index = _build_module_index(root, py_files)

    parsed: List[ParsedFile] = []
    for p in py_files:
        parsed.append(_parse_python_file(root, p))

    # Nodes
    nodes: Dict[str, Dict[str, Any]] = {}

    def add_node(node_id: str, **meta: Any) -> None:
        nodes.setdefault(node_id, {"id": node_id, **meta})

    # File nodes
    for pf in parsed:
        add_node(
            f"file:{pf.relpath}",
            kind="file",
            path=pf.relpath,
            parse_error=pf.parse_error,
        )

    # Topic nodes
    all_topics: Set[str] = set()
    for pf in parsed:
        all_topics.update(pf.publish_topics)
        all_topics.update(pf.subscribe_topics)
    for t in sorted(all_topics):
        add_node(f"topic:{t}", kind="topic", topic=t)

    # Manifest + service registry nodes
    manifests = _load_floor_manifests(root)
    for m in manifests:
        mf_path = m.get("_manifest_path")
        floor_dir = m.get("_floor_dir")
        add_node(f"floor:{floor_dir}", kind="floor", floor_dir=floor_dir, z_level=m.get("z_level"), floor_name=m.get("floor_name"))
        if mf_path:
            add_node(f"manifest:{mf_path}", kind="manifest", path=mf_path)

    registry = _load_service_registry(root)
    if registry:
        add_node("service_registry", kind="service_registry", path=_safe_rel(root / "Z Axis" / "Z0_TheConstruct" / "Config" / "service_registry.json", root))

    # Edges
    edges: List[Dict[str, Any]] = []

    def add_edge(src: str, dst: str, rel: str, **meta: Any) -> None:
        edges.append({"src": src, "dst": dst, "rel": rel, **meta})

    # Import edges (module -> file when resolvable)
    unresolved_imports: Counter[str] = Counter()
    for pf in parsed:
        src = f"file:{pf.relpath}"
        for mod in pf.imports:
            target = module_index.get(mod)
            if target:
                add_edge(src, f"file:{target}", "imports", module=mod)
            else:
                unresolved_imports[mod] += 1

    # Dynamic file-load edges
    for pf in parsed:
        src = f"file:{pf.relpath}"
        for s in pf.dynamic_files:
            resolved = _resolve_rel_file(root, s)
            if resolved:
                add_edge(src, f"file:{resolved}", "loads_file", raw=s)

    # Event bus edges (file -> topic)
    for pf in parsed:
        src = f"file:{pf.relpath}"
        for t in pf.publish_topics:
            add_edge(src, f"topic:{t}", "publishes")
        for t in pf.subscribe_topics:
            add_edge(src, f"topic:{t}", "subscribes")

    # Floor manifest edges
    for m in manifests:
        floor_dir = m.get("_floor_dir")
        floor_node = f"floor:{floor_dir}"
        mf_path = m.get("_manifest_path")
        if mf_path:
            add_edge(floor_node, f"manifest:{mf_path}", "declares")

        for dep in (m.get("dependencies") or []):
            dep = str(dep)
            target = module_index.get(dep)
            if target:
                add_edge(floor_node, f"file:{target}", "depends_on_module", module=dep)
            else:
                add_node(f"module:{dep}", kind="module", module=dep)
                add_edge(floor_node, f"module:{dep}", "depends_on_module", module=dep, resolved=False)

        for comp in (m.get("components") or []):
            comp_id = comp.get("id") or "unknown"
            comp_node = f"component:{floor_dir}:{comp_id}"
            add_node(
                comp_node,
                kind="component",
                floor=floor_dir,
                component_id=comp_id,
                name=comp.get("name"),
                enabled=bool(comp.get("enabled", True)),
                phase=comp.get("phase"),
            )
            add_edge(floor_node, comp_node, "contains")

            source_file = comp.get("source_file") or ""
            if source_file:
                resolved = _resolve_rel_file(root, source_file)
                if resolved:
                    add_edge(comp_node, f"file:{resolved}", "implemented_by", path=resolved)
                else:
                    add_node(f"file_ref:{source_file}", kind="file_ref", raw=source_file)
                    add_edge(comp_node, f"file_ref:{source_file}", "implemented_by", raw=source_file, resolved=False)

            module = comp.get("module") or ""
            if module:
                target = module_index.get(module)
                if target:
                    add_edge(comp_node, f"file:{target}", "uses_module", module=module)
                else:
                    add_node(f"module:{module}", kind="module", module=module)
                    add_edge(comp_node, f"module:{module}", "uses_module", module=module, resolved=False)

    # Service registry edges
    if registry:
        for name, cfg in registry.items():
            entry = cfg if isinstance(cfg, dict) else {}
            enabled = bool(entry.get("enabled", False))
            entry_type = entry.get("type", "unknown")
            mod = entry.get("module")

            node_id = f"service:{name}"
            add_node(node_id, kind="service_entry", name=name, entry_type=entry_type, enabled=enabled)
            add_edge("service_registry", node_id, "contains")
            if mod:
                target = module_index.get(mod)
                if target:
                    add_edge(node_id, f"file:{target}", "loads_module", module=mod)
                else:
                    add_node(f"module:{mod}", kind="module", module=mod)
                    add_edge(node_id, f"module:{mod}", "loads_module", module=mod, resolved=False)

    # Summary
    edge_counts = Counter(e["rel"] for e in edges)
    parse_fail = sum(1 for pf in parsed if pf.parse_error)
    topic_counts = {
        "topics": len(all_topics),
        "publishes": sum(len(pf.publish_topics) for pf in parsed),
        "subscribes": sum(len(pf.subscribe_topics) for pf in parsed),
    }

    return {
        "generated_at": None,
        "root": str(root).replace("\\", "/"),
        "scope": {
            "python_files": len(py_files),
            "parse_failures": parse_fail,
            "excluded": {
                "notes": "This graph excludes bulk archives/datasets/logs/toolchains by design.",
            },
        },
        "stats": {
            "nodes": len(nodes),
            "edges": len(edges),
            "edges_by_type": dict(edge_counts),
            "unresolved_imports_top": unresolved_imports.most_common(50),
            "topics": topic_counts,
        },
        "nodes": list(nodes.values()),
        "edges": edges,
        "module_index_size": len(module_index),
    }


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _write_summary_md(path: Path, graph: Dict[str, Any]) -> None:
    stats = graph.get("stats") or {}
    scope = graph.get("scope") or {}
    lines = []
    lines.append("# LightSpeed Architecture Graph (Runtime Code Scope)")
    lines.append("")
    lines.append(f"**Python files scanned:** {scope.get('python_files')}")
    lines.append(f"**Parse failures:** {scope.get('parse_failures')}")
    lines.append(f"**Nodes:** {stats.get('nodes')}")
    lines.append(f"**Edges:** {stats.get('edges')}")
    lines.append("")
    lines.append("## Edges by Type")
    for k, v in sorted((stats.get("edges_by_type") or {}).items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    lines.append("## Unresolved Imports (Top 50)")
    for mod, count in (stats.get("unresolved_imports_top") or [])[:50]:
        lines.append(f"- `{mod}`: {count}")
    lines.append("")
    topics = stats.get("topics") or {}
    lines.append("## Event Topics")
    lines.append(f"- Topics: {topics.get('topics')}")
    lines.append(f"- Publish sites: {topics.get('publishes')}")
    lines.append(f"- Subscribe sites: {topics.get('subscribes')}")
    lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    root = _find_lightspeed_root(Path(__file__))
    graph = build_graph(root)
    graph["generated_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()

    out_json = root / "dataindex" / "architecture_graph.json"
    out_md = root / "dataindex" / "architecture_graph_summary.md"
    _write_json(out_json, graph)
    _write_summary_md(out_md, graph)
    print(f"[arch] wrote {out_json}")
    print(f"[arch] wrote {out_md}")
    print(f"[arch] nodes={graph['stats']['nodes']} edges={graph['stats']['edges']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
