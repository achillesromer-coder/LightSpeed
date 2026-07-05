# Launcher/services/org.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

APP_ROOT = Path(__file__).resolve().parents[1]      # .../Launcher
DATA_DIR = APP_ROOT.parent / "data"                 # .../data
COMPANIES_DIR = DATA_DIR / "companies"
COMPANIES_DIR.mkdir(parents=True, exist_ok=True)


def _company_dir(company: str) -> Path:
    d = COMPANIES_DIR / company
    (d / "projects").mkdir(parents=True, exist_ok=True)
    return d


def list_companies() -> List[str]:
    return sorted([p.name for p in COMPANIES_DIR.glob("*") if p.is_dir()])


def create_company(slug: str, title: Optional[str] = None) -> Path:
    d = _company_dir(slug)
    # seed minimal company.json if missing
    cj = d / "company.json"
    if not cj.exists():
        cj.write_text(json.dumps({"slug": slug, "title": title or slug}, indent=2), encoding="utf-8")
    # seed users.json if missing
    uj = d / "users.json"
    if not uj.exists():
        uj.write_text(json.dumps({"users": []}, indent=2), encoding="utf-8")
    return d


def list_projects(company: str) -> List[Dict[str, Any]]:
    d = _company_dir(company) / "projects"
    out = []
    for pj in sorted(d.glob("*/project.json")):
        data = json.loads(pj.read_text(encoding="utf-8"))
        out.append(data)
    return out


def create_project(company: str, project_id: str, name: Optional[str] = None) -> Dict[str, Any]:
    d = _company_dir(company) / "projects" / project_id
    (d / "archives").mkdir(parents=True, exist_ok=True)
    (d / "nodes").mkdir(parents=True, exist_ok=True)
    proj = {
        "id": project_id,
        "company": company,
        "name": name or project_id,
        "created_ts": __import__("time").time(),
        "owners": [],
        "tags": [],
        "settings": {},
    }
    (d / "project.json").write_text(json.dumps(proj, indent=2), encoding="utf-8")
    # Seed audit log
    (d / "history.jsonl").write_text("", encoding="utf-8")
    return proj


def project_dir(company: str, project_id: str) -> Path:
    return _company_dir(company) / "projects" / project_id
