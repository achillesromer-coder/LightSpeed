"""
Romer Industries Connector (Neo Floor)

Purpose:
- Provide a single, reusable integration layer between LightSpeed and the
  romer.industries web workspaces (operations, W1–W6, Achilles).

Constraints:
- romer.industries appears to be Squarespace password-protected (401 without
  WWW-Authenticate). We do NOT hardcode secrets. Authentication is supported
  via user-supplied cookie header (recommended) and/or future unlock flows.

Environment variables (optional):
- ROMER_COOKIE: raw Cookie header value after unlocking the site in a browser
                (e.g., "SS_MID=...; ss_cvr=...; ...").
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import json
import os
import time

import requests


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


@dataclass(frozen=True)
class RomerAuth:
    """
    Authentication material for romer.industries.

    For Squarespace password pages, cookie-based auth is the most reliable
    approach for programmatic fetches.
    """

    cookie_header: Optional[str] = None

    @staticmethod
    def from_env() -> "RomerAuth":
        cookie = os.environ.get("ROMER_COOKIE") or None
        if cookie:
            cookie = cookie.strip() or None
        return RomerAuth(cookie_header=cookie)

    def headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "User-Agent": "LightSpeed/1.0 (+Neo Romer Connector)",
            "Accept": "*/*",
        }
        if self.cookie_header:
            headers["Cookie"] = self.cookie_header
        return headers


class RomerIndustriesConnector:
    def __init__(self, base_url: str = "https://romer.industries", cache_dir: Optional[Path] = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        try:
            from core.config.paths import MEROVINGIAN_DATA  # type: ignore
            default_cache = Path(MEROVINGIAN_DATA) / "romer_sync"
        except Exception:
            default_cache = Path.cwd() / "Z Axis" / "Z-4_Merovingian" / "data" / "romer_sync"

        self.cache_dir = (cache_dir or default_cache).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "raw").mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "reports").mkdir(parents=True, exist_ok=True)

    def url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def fetch(self, path: str, auth: Optional[RomerAuth] = None, timeout_s: int = 30) -> Tuple[int, str, bytes]:
        auth = auth or RomerAuth.from_env()
        u = self.url(path)
        r = self.session.get(u, headers=auth.headers(), timeout=timeout_s)
        ctype = r.headers.get("content-type") or ""
        return r.status_code, ctype, r.content

    def default_targets(self) -> Dict[str, str]:
        """
        Canonical Romer endpoints referenced in project docs / UI snippets.
        These may be password-protected.
        """
        return {
            "operations": "/operations",
            "lightspeedhome": "/lightspeedhome",
            "achilles_page": "/achilles",
            "achilles_data_root": "/data/achilles",
            "data_directory": "/data/directory",
            "w1_data": "/w1/data",
            "w2_data": "/w2/data",
            "w3_data": "/w3/data",
            "w4_data": "/w4/data",
            "w5_data": "/w5/data",
            "w6_data": "/w6/data",
        }

    def sync_targets(self, targets: Optional[Dict[str, str]] = None, auth: Optional[RomerAuth] = None) -> Dict[str, Any]:
        """
        Fetch a set of targets and write raw payloads + a JSON report to cache_dir.
        """
        auth = auth or RomerAuth.from_env()
        targets = targets or self.default_targets()

        report: Dict[str, Any] = {
            "ts": _now_iso(),
            "base_url": self.base_url,
            "targets": {},
        }

        for name, path in targets.items():
            try:
                status, ctype, body = self.fetch(path, auth=auth)
                out_path = self.cache_dir / "raw" / f"{name}.bin"
                out_path.write_bytes(body)
                report["targets"][name] = {
                    "path": path,
                    "url": self.url(path),
                    "status": status,
                    "content_type": ctype,
                    "bytes": len(body),
                    "saved_as": str(out_path),
                }
            except Exception as e:
                report["targets"][name] = {
                    "path": path,
                    "url": self.url(path),
                    "error": str(e),
                }

        rep_path = self.cache_dir / "reports" / f"sync_{int(time.time())}.json"
        rep_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
