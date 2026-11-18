from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/cgx_living_consolidation_review.py"


def load_module():
    name = "cgx_living_consolidation_review_test"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fixture_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True,
                   capture_output=True)
    files = {
        "pkg/__init__.py": b"",
        "physics/raphael/geometry.py": b"",
        "spare/empty.dat": b"",
        "pkg/actual.py": b"meaningful",
    }
    for rel, data in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    subprocess.run(["git", "-C", str(repo), "add", "."],
                   check=True, capture_output=True)
    return repo


def test_one_source_and_no_deletions(tmp_path):
    module = load_module()
    repo = fixture_repo(tmp_path)
    carriers = tmp_path / "carrier"
    carriers.mkdir()
    (carriers / "LS.cgx").write_bytes(b"same")
    (carriers / "LightSpeed.cgx").write_bytes(b"same")
    (carriers / "Romer.cgx").write_bytes(b"other")
    before = {x.relative_to(repo).as_posix(): x.read_bytes()
              for x in repo.rglob("*") if x.is_file() and ".git" not in x.parts}
    result = module.build_living_consolidation_review(repo, carriers)
    assert result["schema"] == "CGX-LIVING-CONSOLIDATION-REVIEW/0.1"
    assert result["tracked_source_count"] == 4
    assert result["tracked_zero_byte_count"] == 3
    assert result["retained_zero_by_kind"] == {
        "RETAIN_PYTHON_PACKAGE_MARKER": 1,
        "RETAIN_UNVERIFIED_RESEARCH_SCAFFOLD": 1,
        "RETAIN_UNRESOLVED_ZERO_BYTE_ASSET": 1,
    }
    assert result["unique_carrier_hash_count"] == 2
    assert result["collapsed_display_aliases"] == 1
    assert len(result["one_card_per_unique_content"]) == 2
    assert not result["file_deletion_performed"]
    assert not result["source_modification_performed"]
    assert result["safe_delete_candidates"] == []
    assert all(not row["deletion_eligible"] for row in result["retained_zero_byte_source"])
    after = {x.relative_to(repo).as_posix(): x.read_bytes()
             for x in repo.rglob("*") if x.is_file() and ".git" not in x.parts}
    assert before == after
    assert result == module.build_living_consolidation_review(repo, carriers)


def test_empty_cgx_carrier_is_held_not_erased(tmp_path):
    module = load_module()
    repo = fixture_repo(tmp_path)
    carriers = tmp_path / "carrier"
    carriers.mkdir()
    empty = carriers / "UNVERIFIED.cgx"
    empty.write_bytes(b"")
    result = module.build_living_consolidation_review(repo, carriers)
    assert result["zero_byte_carrier_holds"] == ["UNVERIFIED.cgx"]
    assert empty.exists()
    assert result["safe_delete_candidates"] == []
    assert not result["native_mint_performed"]


def test_git_scope_failure_denies_review(tmp_path):
    import pytest
    module = load_module()
    root = tmp_path / "not-a-repo"
    root.mkdir()
    with pytest.raises(ValueError, match="tracked Git scope unavailable"):
        module.build_living_consolidation_review(root, tmp_path)
