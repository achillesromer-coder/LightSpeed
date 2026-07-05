# Launcher/services/pipelines.py
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from .org import project_dir

Hook = Callable[[Dict[str, Any]], None]

class Publisher:
    """
    Content promotion orchestrator. Writes a publish manifest under:
    <project>/releases/<timestamp>/manifest.json
    """
    def __init__(self, company: str, project_id: str):
        self.company = company
        self.project_id = project_id
        self.root = project_dir(company, project_id)
        self.rel_dir = self.root / "releases"
        self.rel_dir.mkdir(parents=True, exist_ok=True)
        self._hooks: List[Hook] = []

    def add_hook(self, hook: Hook) -> None:
        self._hooks.append(hook)

    def _sha256_file(self, p: Path) -> str:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _collect_assets(self) -> List[Dict[str, Any]]:
        out = []
        arch = self.root / "archives"
        for p in arch.rglob("*"):
            if p.is_file():
                out.append({
                    "path": p.relative_to(self.root).as_posix(),
                    "sha256": self._sha256_file(p),
                    "size": p.stat().st_size,
                })
        return out

    def publish(self, author_id: str, notes: str = "", channel: str = "live") -> Path:
        ts = int(time.time())
        rel = self.rel_dir / str(ts)
        rel.mkdir(parents=True, exist_ok=True)

        manifest = {
            "company": self.company,
            "project_id": self.project_id,
            "ts": ts,
            "author_id": author_id,
            "channel": channel,
            "notes": notes,
            "assets": self._collect_assets(),
        }
        man_path = rel / "manifest.json"
        man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        for hook in list(self._hooks):
            try:
                hook(manifest)
            except Exception:
                pass
        return man_path


# Example hooks you can register in N.py on boot:

def hook_notarise_ip(manifest: Dict[str, Any]) -> None:
    """
    Placeholder for IP notarisation (e.g., hash to a registry or blockchain).
    Right now we just write a 'notarised.json' echo with a deterministic hash.
    """
    payload = {
        "manifest_ts": manifest["ts"],
        "project": manifest["project_id"],
        "company": manifest["company"],
        "digest_sha256": sha256_json(manifest),
        "registry": "local-stub",              # ___ replace with real registry later
    }
    root = project_dir(manifest["company"], manifest["project_id"])
    (root / "releases" / str(manifest["ts"]) / "notarised.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def hook_webhook(manifest: Dict[str, Any]) -> None:
    """
    Placeholder for outbound webhook.
    For now, writes 'webhook.json' under the release folder.
    """
    root = project_dir(manifest["company"], manifest["project_id"])
    (root / "releases" / str(manifest["ts"]) / "webhook.json").write_text(
        json.dumps({"event": "published", "manifest_ts": manifest["ts"]}, indent=2), encoding="utf-8"
    )


def sha256_json(obj: Dict[str, Any]) -> str:
    h = hashlib.sha256(json.dumps(obj, sort_keys=True).encode("utf-8")).hexdigest()
    return h
