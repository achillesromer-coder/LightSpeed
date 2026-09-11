from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_org_module():
    path = REPO_ROOT / "Launcher" / "services" / "org.py"
    spec = importlib.util.spec_from_file_location("launcher_org_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_read_paths_do_not_materialize_company_or_project_scaffolds(tmp_path, monkeypatch):
    org = _load_org_module()
    companies = tmp_path / "companies"
    monkeypatch.setattr(org, "COMPANIES_DIR", companies)

    assert org.list_companies() == []
    assert org.list_projects("romer") == []
    project = org.project_dir("romer", "rfs-emff")

    assert project == companies / "romer" / "projects" / "rfs-emff"
    assert not companies.exists()
    assert not project.exists()


def test_explicit_project_creation_is_minimal_and_idempotent(tmp_path, monkeypatch):
    org = _load_org_module()
    companies = tmp_path / "companies"
    monkeypatch.setattr(org, "COMPANIES_DIR", companies)

    first = org.create_project("romer", "rfs-emff", "RFS & EMFF")
    project = org.project_dir("romer", "rfs-emff")
    first_created = first["created_ts"]

    assert project.is_dir()
    assert (project / "project.json").is_file()
    assert (project / "history.jsonl").is_file()
    assert not (project / "archives").exists()
    assert not (project / "nodes").exists()
    assert first["settings"]["materialization"] == "reference_first"
    assert first["settings"]["canonical_payload_policy"] == "pointer_not_copy"

    second = org.create_project("romer", "rfs-emff", "Changed display name")
    assert second["created_ts"] == first_created
    assert second["name"] == "RFS & EMFF"


def test_legacy_neo_ui_does_not_create_per_message_files() -> None:
    source = (REPO_ROOT / "Launcher" / "Z Axis" / "Neo.py").read_text(encoding="utf-8")

    assert '"ai_logs"' not in source
    assert ".mkdir(" not in source
    assert 'history.jsonl' in source
    assert 'history.open("a"' in source
    assert '.write_text(' not in source
