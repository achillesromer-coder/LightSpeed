from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "tools/cgx_review_bytecode_cleanup.py"


def module():
    spec = importlib.util.spec_from_file_location("cgx_review_bytecode_cleanup_test", SOURCE)
    assert spec is not None and spec.loader is not None
    instance = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = instance
    spec.loader.exec_module(instance)
    return instance


def git(repo: Path, *args: str):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                            check=True, text=True)
    return result.stdout.strip()


def fixture_repo(tmp_path: Path):
    root = tmp_path / "CGX_Mobile_Review"
    root.mkdir()
    git(root, "init", "-b", "review/cgx-living-consolidation-20261118")
    git(root, "config", "user.name", "CGX Cleanup Test")
    git(root, "config", "user.email", "test@example.invalid")
    (root / ".gitignore").write_text("__pycache__/\n*.pyc\n*.pyo\nnode_modules/\n", encoding="utf-8")
    (root / "source.py").write_text("source = 'preserve'\n", encoding="utf-8")
    git(root, "add", ".gitignore", "source.py")
    git(root, "commit", "-m", "fixture")
    cache = root / "tools/__pycache__"
    cache.mkdir(parents=True)
    (cache / "module.cpython-311.pyc").write_bytes(b"disposable-compiled-bytecode")
    return root, cache


def test_dry_run_read_only_with_finite_allowlist(tmp_path):
    api = module()
    root, cache = fixture_repo(tmp_path)
    report = api.scan(root)
    assert report["candidate_count"] == 1
    assert report["candidate_bytes"] == len(b"disposable-compiled-bytecode")
    assert report["candidates"][0]["path"] == "tools/__pycache__/module.cpython-311.pyc"
    assert report["mint_authorized"] is False
    assert report["source_or_carrier_deletion_authorized"] is False
    assert (cache / "module.cpython-311.pyc").exists()
    assert git(root, "status", "--porcelain") == ""


def test_archived_destructive_delete_is_bounded_and_exactly_recoverable(tmp_path):
    api = module()
    root, cache = fixture_repo(tmp_path)
    before = (cache / "module.cpython-311.pyc").read_bytes()
    with pytest.raises(api.CleanupHold, match="confirmation"):
        api.execute(root, tmp_path / "recovery", confirm="ALL_Y")
    assert (cache / "module.cpython-311.pyc").exists()
    receipt = api.execute(root, tmp_path / "recovery", confirm=api.CONFIRM)
    assert receipt["state"] == "VERIFIED_BYTECODE_PURGED"
    assert receipt["deleted_files"] == 1
    assert receipt["deleted_bytes"] == len(before)
    assert receipt["held_files"] == []
    assert receipt["source_git_clean_after"]
    assert not cache.exists()
    assert (root / "source.py").read_text(encoding="utf-8") == "source = 'preserve'\n"
    assert git(root, "status", "--porcelain") == ""
    assert Path(receipt["archive"]).exists()
    assert Path(receipt["archive"]).with_suffix(".receipt.json").exists()
    with zipfile.ZipFile(receipt["archive"]) as archive:
        assert archive.read("cache/tools/__pycache__/module.cpython-311.pyc") == before
        manifest = json.loads(archive.read("MANIFEST.json"))
        assert manifest["scan_sha256"] == receipt["scan_sha256"]
    assert api.scan(root)["candidate_count"] == 0


def test_non_bytecode_cache_file_holds_all_deletion(tmp_path):
    api = module()
    root, cache = fixture_repo(tmp_path)
    (cache / "unexpected.txt").write_text("do not delete", encoding="utf-8")
    with pytest.raises(api.CleanupHold, match="non-bytecode"):
        api.scan(root)
    assert (cache / "module.cpython-311.pyc").exists()


def test_dirty_wrong_branch_or_wrong_root_blocks_delete(tmp_path):
    api = module()
    root, cache = fixture_repo(tmp_path)
    (root / "source.py").write_text("changed", encoding="utf-8")
    with pytest.raises(api.CleanupHold, match="unclean"):
        api.scan(root)
    git(root, "restore", "--", "source.py")
    git(root, "switch", "-c", "other-review-branch")
    with pytest.raises(api.CleanupHold, match="branch"):
        api.scan(root)
    with pytest.raises(api.CleanupHold, match="isolated review worktree"):
        api.scan(tmp_path)


def test_tracked_pyc_cannot_be_removed(tmp_path):
    api = module()
    root, cache = fixture_repo(tmp_path)
    git(root, "add", "-f", "tools/__pycache__/module.cpython-311.pyc")
    git(root, "commit", "-m", "fixture tracked bytecode")
    with pytest.raises(api.CleanupHold, match="tracked"):
        api.scan(root)
    assert (cache / "module.cpython-311.pyc").exists()


def test_no_node_modules_or_runtime_cleaned(tmp_path):
    api = module()
    root, cache = fixture_repo(tmp_path)
    other = root / "apps/lightspeed-go/node_modules/.vite"
    other.mkdir(parents=True)
    (other / "compiled.js").write_bytes(b"keep")
    report = api.scan(root)
    assert all("node_modules" not in item["path"] for item in report["candidates"])
    assert report["candidate_count"] == 1
    assert (other / "compiled.js").exists()
