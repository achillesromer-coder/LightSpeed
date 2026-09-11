# Launcher/services/org.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

APP_ROOT = Path(__file__).resolve().parents[1]      # .../Launcher
DATA_DIR = APP_ROOT.parent / "data"                 # .../data
COMPANIES_DIR = DATA_DIR / "companies"


def _company_dir(company: str) -> Path:
    """Return the company path without materialising local state.

    Canonical/source reads must remain side-effect free.  Directory creation is
    reserved for explicit create/update operations so startup, listing and agent
    discovery cannot manufacture duplicate project/fileset scaffolds.
    """
    return COMPANIES_DIR / company


def _ensure_company_dir(company: str) -> Path:
    d = _company_dir(company)
    (d / "projects").mkdir(parents=True, exist_ok=True)
    return d


def list_companies() -> List[str]:
    if not COMPANIES_DIR.is_dir():
        return []
    return sorted([p.name for p in COMPANIES_DIR.iterdir() if p.is_dir()])


def create_company(slug: str, title: Optional[str] = None) -> Path:
    d = _ensure_company_dir(slug)
    # Seed only canonical local identity metadata when it is genuinely absent.
    cj = d / "company.json"
    if not cj.exists():
        cj.write_text(json.dumps({"slug": slug, "title": title or slug}, indent=2), encoding="utf-8")
    uj = d / "users.json"
    if not uj.exists():
        uj.write_text(json.dumps({"users": []}, indent=2), encoding="utf-8")
    return d


def list_projects(company: str) -> List[Dict[str, Any]]:
    d = _company_dir(company) / "projects"
    if not d.is_dir():
        return []
    out = []
    for pj in sorted(d.glob("*/project.json")):
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            out.append(data)
    return out


def create_project(company: str, project_id: str, name: Optional[str] = None) -> Dict[str, Any]:
    """Explicitly materialise the minimal writable local project record.

    Project/source payloads remain referenced through their canonical Drive/Git
    identities and are not cloned into per-agent or per-axis trees by this helper.
    """
    d = _ensure_company_dir(company) / "projects" / project_id
    d.mkdir(parents=True, exist_ok=True)
    proj_path = d / "project.json"
    if proj_path.is_file():
        try:
            existing = json.loads(proj_path.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                return existing
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass

    proj = {
        "id": project_id,
        "company": company,
        "name": name or project_id,
        "created_ts": __import__("time").time(),
        "owners": [],
        "tags": [],
        "settings": {
            "materialization": "reference_first",
            "canonical_payload_policy": "pointer_not_copy",
        },
    }
    proj_path.write_text(json.dumps(proj, indent=2), encoding="utf-8")
    # A single append-only project history is created only for explicit projects.
    history = d / "history.jsonl"
    if not history.exists():
        history.write_text("", encoding="utf-8")
    return proj


def project_dir(company: str, project_id: str) -> Path:
    """Return the local working path without creating it."""
    return _company_dir(company) / "projects" / project_id
