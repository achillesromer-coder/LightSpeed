# Launcher/services/indexer.py
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Iterable, List, Tuple, Optional

from .org import project_dir

WORD = re.compile(r"[A-Za-z0-9_]{2,}")

@dataclass
class DocRef:
    doc_id: str       # stable path-like id
    title: str
    kind: str         # "asset" | "node" | "note"
    path: str         # absolute or project-relative path


class ProjectIndexer:
    """
    Tiny TF-IDF index over a project's archives & nodes.
    Stores index in project_dir/.index/index.json (safe to delete/rebuild).
    """
    def __init__(self, company: str, project_id: str):
        self.company = company
        self.project_id = project_id
        self.root = project_dir(company, project_id)
        self.idx_dir = self.root / ".index"
        self.idx_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.idx_dir / "index.json"

        # in-memory structures
        self.docs: Dict[str, DocRef] = {}
        self.df: Counter[str] = Counter()     # document frequency
        self.tf: Dict[str, Counter[str]] = {} # term frequencies per doc

    # ---------- public ----------
    def build(self) -> None:
        self.docs.clear(); self.df.clear(); self.tf.clear()
        for ref, text in self._walk_sources():
            tokens = self._tokenize(text)
            tf = Counter(tokens)
            self.docs[ref.doc_id] = ref
            self.tf[ref.doc_id] = tf
            for t in tf.keys():
                self.df[t] += 1
        self._persist()

    def update_asset(self, abs_path: Path) -> None:
        """Index/update a single asset file."""
        rel = abs_path.relative_to(self.root).as_posix()
        doc_id = f"asset:{rel}"
        title = abs_path.name
        text = self._extract_text(abs_path)
        self._upsert_doc(DocRef(doc_id, title, "asset", rel), text)

    def update_node(self, node_id: str, payload: Dict[str, Any]) -> None:
        doc_id = f"node:{node_id}"
        title = payload.get("title") or node_id
        body = payload.get("body") or ""
        text = f"{title}\n{body}"
        self._upsert_doc(DocRef(doc_id, title, "node", f"nodes/{node_id}.json"), text)

    def search(self, query: str, k: int = 20) -> List[Tuple[float, DocRef]]:
        if not query.strip():
            return []
        q = [t for t in self._tokenize(query) if t]
        if not q:
            return []
        N = max(1, len(self.docs))
        scores: Dict[str, float] = defaultdict(float)
        for term in q:
            df = self.df.get(term, 0)
            if df == 0:
                continue
            idf = math.log(N / df)
            for doc_id, tf in self.tf.items():
                tf_t = tf.get(term, 0)
                if tf_t:
                    scores[doc_id] += (1 + math.log(tf_t)) * idf
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
        return [(float(score), self.docs[doc_id]) for doc_id, score in ranked]

    # ---------- internals ----------
    def _walk_sources(self) -> Iterable[Tuple[DocRef, str]]:
        # archives
        for p in (self.root / "archives").rglob("*"):
            if p.is_file():
                yield DocRef(f"asset:{p.relative_to(self.root).as_posix()}", p.name, "asset",
                             p.relative_to(self.root).as_posix()), self._extract_text(p)
        # nodes (canvas)
        nodes_dir = self.root / "nodes"
        if nodes_dir.exists():
            for n in nodes_dir.glob("*.json"):
                try:
                    data = json.loads(n.read_text(encoding="utf-8"))
                except Exception:
                    continue
                title = data.get("title") or n.stem
                body = data.get("body") or ""
                yield DocRef(f"node:{n.stem}", title, "node", f"nodes/{n.name}"), f"{title}\n{body}"

    def _upsert_doc(self, ref: DocRef, text: str) -> None:
        tokens = self._tokenize(text)
        tf = Counter(tokens)
        # remove old df counts if present
        if ref.doc_id in self.tf:
            for t in self.tf[ref.doc_id].keys():
                self.df[t] -= 1
                if self.df[t] <= 0:
                    self.df.pop(t, None)
        self.docs[ref.doc_id] = ref
        self.tf[ref.doc_id] = tf
        for t in tf.keys():
            self.df[t] += 1
        self._persist()

    def _persist(self) -> None:
        blob = {
            "docs": {k: asdict_like(v) for k, v in self.docs.items()},
            "df": dict(self.df),
            "tf": {k: dict(v) for k, v in self.tf.items()},
        }
        self.db_path.write_text(json.dumps(blob), encoding="utf-8")

    def load(self) -> bool:
        if not self.db_path.exists():
            return False
        try:
            blob = json.loads(self.db_path.read_text(encoding="utf-8"))
            self.docs = {k: DocRef(**v) for k, v in blob.get("docs", {}).items()}
            self.df = Counter(blob.get("df", {}))
            self.tf = {k: Counter(v) for k, v in blob.get("tf", {}).items()}
            return True
        except Exception:
            return False

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [m.group(0).lower() for m in WORD.finditer(text or "")]

    @staticmethod
    def _extract_text(path: Path) -> str:
        # Safe, dependency-light text extraction
        try:
            if path.suffix.lower() in (".txt", ".md", ".py", ".csv", ".log"):
                return path.read_text(encoding="utf-8", errors="ignore")
            if path.suffix.lower() in (".json",):
                return json.dumps(json.loads(path.read_text(encoding="utf-8", errors="ignore")), ensure_ascii=False)
            if path.suffix.lower() in (".yaml", ".yml"):
                # naive: keep as plain text
                return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass
        return f"{path.name}"


def asdict_like(dr: DocRef) -> Dict[str, Any]:
    return {"doc_id": dr.doc_id, "title": dr.title, "kind": dr.kind, "path": dr.path}
