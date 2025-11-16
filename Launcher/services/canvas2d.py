# Launcher/services/canvas2d.py
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Literal

from .org import project_dir

NodeType = Literal["Task", "Asset", "Doc", "API", "Portal", "Custom"]
TaskStatus = Literal["Todo", "In Progress", "Review", "Done"]

@dataclass
class Node:
    id: str
    title: str
    type: NodeType
    floor: int                   # Z index
    x: int                       # snapped px
    y: int
    body: str = ""
    status: Optional[TaskStatus] = None
    urgency: Optional[str] = None     # "none|low|med|high|date:YYYY-MM-DD"
    created_ts: float = 0.0
    updated_ts: float = 0.0
    meta: Dict[str, Any] = None

@dataclass
class Edge:
    id: str
    src: str
    dst: str
    label: str = ""
    created_ts: float = 0.0

class GraphStore:
    """
    JSONL backed node/edge store per project. Enforces guardrails and snap grid.
    """
    def __init__(self, company: str, project_id: str, snap_px: int = 24,
                 max_nodes_per_floor: int = 500, max_edges: int = 1000):
        self.company = company
        self.project_id = project_id
        self.root = project_dir(company, project_id)
        self.nodes_dir = self.root / "nodes"
        self.edges_dir = self.root / "nodes"  # stored together for simplicity
        self.nodes_dir.mkdir(parents=True, exist_ok=True)
        self.snap = max(8, min(128, int(snap_px)))
        self.max_nodes_per_floor = int(max_nodes_per_floor)
        self.max_edges = int(max_edges)
        self._cache_nodes: Dict[str, Node] = {}
        self._cache_edges: Dict[str, Edge] = {}
        self._load_all()

    # ---------- CRUD ----------
    def create_node(self, title: str, ntype: NodeType, floor: int, x: int, y: int,
                    status: Optional[TaskStatus] = None, body: str = "", urgency: Optional[str] = None,
                    meta: Optional[Dict[str, Any]] = None) -> Node:
        self._enforce_limits(floor)
        n = Node(
            id=str(uuid.uuid4()),
            title=title.strip(),
            type=ntype,
            floor=int(floor),
            x=self._snap(x), y=self._snap(y),
            body=body or "",
            status=status, urgency=urgency,
            created_ts=time.time(), updated_ts=time.time(),
            meta=meta or {},
        )
        self._write_node(n)
        self._cache_nodes[n.id] = n
        return n

    def update_node_pos(self, node_id: str, x: int, y: int) -> Node:
        n = self._get_node(node_id)
        n.x = self._snap(x); n.y = self._snap(y); n.updated_ts = time.time()
        self._write_node(n); return n

    def update_node(self, node_id: str, **fields) -> Node:
        n = self._get_node(node_id)
        for k, v in fields.items():
            if hasattr(n, k):
                setattr(n, k, v)
        n.updated_ts = time.time()
        self._write_node(n); return n

    def delete_node(self, node_id: str) -> None:
        p = self.nodes_dir / f"{node_id}.json"
        if p.exists():
            p.unlink()
        self._cache_nodes.pop(node_id, None)
        # remove attached edges
        for e in list(self._cache_edges.values()):
            if e.src == node_id or e.dst == node_id:
                self.delete_edge(e.id)

    def list_nodes(self, floor: Optional[int] = None) -> List[Node]:
        vals = list(self._cache_nodes.values())
        if floor is not None:
            vals = [n for n in vals if n.floor == int(floor)]
        return sorted(vals, key=lambda n: (n.floor, n.y, n.x, n.title.lower()))

    def create_edge(self, src: str, dst: str, label: str = "") -> Edge:
        if len(self._cache_edges) >= self.max_edges:
            raise ValueError("edge limit reached")
        if src == dst:
            raise ValueError("self edge not allowed")
        e = Edge(id=str(uuid.uuid4()), src=src, dst=dst, label=label, created_ts=time.time())
        self._write_edge(e); self._cache_edges[e.id] = e
        return e

    def delete_edge(self, edge_id: str) -> None:
        p = self.edges_dir / f"edge_{edge_id}.json"
        if p.exists():
            p.unlink()
        self._cache_edges.pop(edge_id, None)

    def list_edges(self) -> List[Edge]:
        return list(self._cache_edges.values())

    # ---------- internals ----------
    def _enforce_limits(self, floor: int) -> None:
        count = sum(1 for n in self._cache_nodes.values() if n.floor == int(floor))
        if count >= self.max_nodes_per_floor:
            raise ValueError(f"node limit reached for floor {floor}")

    def _snap(self, v: int) -> int:
        s = self.snap
        return int(round(v / s) * s)

    def _get_node(self, node_id: str) -> Node:
        n = self._cache_nodes.get(node_id)
        if not n:
            p = self.nodes_dir / f"{node_id}.json"
            if not p.exists():
                raise KeyError(node_id)
            n = Node(**json.loads(p.read_text(encoding="utf-8")))
            self._cache_nodes[node_id] = n
        return n

    def _write_node(self, n: Node) -> None:
        (self.nodes_dir / f"{n.id}.json").write_text(json.dumps(asdict(n), indent=2), encoding="utf-8")

    def _write_edge(self, e: Edge) -> None:
        (self.edges_dir / f"edge_{e.id}.json").write_text(json.dumps(asdict(e), indent=2), encoding="utf-8")

    def _load_all(self) -> None:
        for p in self.nodes_dir.glob("*.json"):
            try:
                n = Node(**json.loads(p.read_text(encoding="utf-8")))
                self._cache_nodes[n.id] = n
            except Exception:
                continue
        for p in self.edges_dir.glob("edge_*.json"):
            try:
                e = Edge(**json.loads(p.read_text(encoding="utf-8")))
                self._cache_edges[e.id] = e
            except Exception:
                continue
