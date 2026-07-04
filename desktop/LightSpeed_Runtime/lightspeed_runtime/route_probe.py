from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from lightspeed_runtime.storage_paths import catalog_root
from lightspeed_runtime.web_integration import build_romer_web_integration, read_romer_web_integration


Fetcher = Callable[[str, float], dict]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_route_probe_report_path(root: Path) -> Path:
    return catalog_root(root) / "website" / "route_probe_report.json"


def _extract_title(content: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", content, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def probe_url(url: str, timeout: float = 8.0) -> dict:
    request = Request(url, headers={"User-Agent": "LightSpeed-Route-Probe/0.10"})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(16384)
            text = raw.decode("utf-8", errors="replace")
            return {
                "actual_status": int(getattr(response, "status", 0) or 0),
                "probe_status": "http_ok",
                "content_type": response.headers.get("Content-Type", ""),
                "title": _extract_title(text),
                "bytes_sampled": len(raw),
                "error": "",
            }
    except HTTPError as exc:
        return {
            "actual_status": int(exc.code),
            "probe_status": "http_error",
            "content_type": exc.headers.get("Content-Type", "") if exc.headers else "",
            "title": "",
            "bytes_sampled": 0,
            "error": str(exc),
        }
    except (URLError, OSError, TimeoutError) as exc:
        return {
            "actual_status": None,
            "probe_status": "connection_error",
            "content_type": "",
            "title": "",
            "bytes_sampled": 0,
            "error": str(exc),
        }


def _default_routes(root: Path) -> list[dict]:
    integration = read_romer_web_integration(root) or build_romer_web_integration(root)
    return list(integration.get("website_routes", []))


def build_route_probe_report(
    root: Path,
    *,
    routes: list[dict] | None = None,
    timeout: float = 8.0,
    fetcher: Fetcher | None = None,
) -> dict:
    root = Path(root)
    selected_routes = routes if routes is not None else _default_routes(root)
    fetch = fetcher or probe_url
    results = []
    for route in selected_routes:
        url = str(route.get("url") or "")
        observed = fetch(url, timeout) if url else {"actual_status": None, "probe_status": "missing_url", "error": "missing url"}
        expected_status = str(route.get("observed_status") or "unknown")
        is_public_required = expected_status == "public_200"
        ok = observed.get("actual_status") == 200 if is_public_required else observed.get("actual_status") == 200
        results.append(
            {
                "route": route.get("route"),
                "url": url,
                "owner_floor": route.get("owner_floor"),
                "workspace": route.get("workspace"),
                "expected_status": expected_status,
                "actual_status": observed.get("actual_status"),
                "probe_status": observed.get("probe_status"),
                "ok": bool(ok),
                "title": observed.get("title") or route.get("title") or "",
                "content_type": observed.get("content_type") or "",
                "error": observed.get("error") or "",
            }
        )

    public_results = [item for item in results if item["expected_status"] == "public_200"]
    data_results = [item for item in results if item["expected_status"] != "public_200"]
    public_ok = sum(1 for item in public_results if item["ok"])
    data_ok = sum(1 for item in data_results if item["ok"])
    failures = [item for item in results if not item["ok"]]
    status = "pass" if not failures else "public_pass_data_warnings" if public_ok == len(public_results) else "route_failures"

    return {
        "generated_at": utc_now_iso(),
        "owner_floor": "Oracle",
        "report_path": str(default_route_probe_report_path(root)),
        "status": status,
        "route_count": len(results),
        "public_route_count": len(public_results),
        "public_route_ok_count": public_ok,
        "data_route_count": len(data_results),
        "data_route_ok_count": data_ok,
        "failure_count": len(failures),
        "failures": [
            {
                "route": item.get("route"),
                "actual_status": item.get("actual_status"),
                "probe_status": item.get("probe_status"),
                "error": item.get("error"),
            }
            for item in failures
        ],
        "results": results,
        "policy": "Public routes must return HTTP 200 before walkthrough. Data routes may warn during walkthrough but need payloads or explicit maintenance stubs before V0.10.0 packaging.",
    }


def read_route_probe_report(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_route_probe_report_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_route_probe_report(
    root: Path,
    output_path: Path | None = None,
    *,
    timeout: float = 8.0,
    routes: list[dict] | None = None,
    fetcher: Fetcher | None = None,
) -> dict:
    destination = output_path or default_route_probe_report_path(root)
    payload = build_route_probe_report(root, routes=routes, timeout=timeout, fetcher=fetcher)
    payload["report_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
