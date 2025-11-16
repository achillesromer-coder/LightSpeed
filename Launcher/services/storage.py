from __future__ import annotations
import json, hashlib
from pathlib import Path
from dataclasses import asdict, is_dataclass
from typing import Any, Optional

class Storage:
    """Simple JSON store with content-hash versioning."""
    def __init__(self, root: Path):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)

    def _p(self, *parts) -> Path:
        p = self.root.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def load_json(self, rel: str, default: Any) -> Any:
        p = self._p(rel)
        if not p.exists(): return default
        return json.loads(p.read_text(encoding="utf-8"))

    def save_json(self, rel: str, obj: Any) -> str:
        if is_dataclass(obj): obj = asdict(obj)
        blob = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
        sha = hashlib.sha256(blob).hexdigest()[:12]
        p = self._p(rel)
        p.write_text(json.dumps(obj, indent=2), encoding="utf-8")
        # write sidecar version
        p.with_suffix(p.suffix + ".ver").write_text(sha, encoding="utf-8")
        return sha

    def content_hash(self, rel: str) -> Optional[str]:
        p = self._p(rel).with_suffix(self._p(rel).suffix + ".ver")
        return p.read_text(encoding="utf-8").strip() if p.exists() else None
