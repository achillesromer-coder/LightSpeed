import hashlib
import json
import os
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import sync_desktop_source
from sync_desktop_source import (
    CANONICAL_SOURCE_ROOT,
    expand_source_paths,
    load_allowlist,
    main,
    sync_sources,
    validate_relative_path,
)


@pytest.mark.parametrize(
    "relative",
    [
        "Desktop_Hooks/LightSpeed/N.py",
        "Desktop_Hooks/LightSpeed/config/app.json",
        "LightSpeed_Runtime/lightspeed_runtime/store.py",
    ],
)
def test_validate_relative_path_accepts_source_paths(relative):
    assert validate_relative_path(relative)


@pytest.mark.parametrize(
    "relative",
    [
        "Desktop_Hooks/LightSpeed/data/runtime.db",
        "Desktop_Hooks/LightSpeed/ARCHIVE/old.py",
        "Desktop_Hooks/LightSpeed/ai_logs/run.json",
        "Desktop_Hooks/LightSpeed/__pycache__/N.pyc",
        "Desktop_Hooks/LightSpeed/.pytest_cache/state.json",
        "Desktop_Hooks/LightSpeed/node_modules/package/index.js",
        "Desktop_Hooks/LightSpeed/reservoirs/raw.json",
        "Desktop_Hooks/LightSpeed/vault/secret.json",
        "Desktop_Hooks/LightSpeed/venv/Lib/site.py",
        "Desktop_Hooks/LightSpeed/legacy/old.py",
    ],
)
def test_validate_relative_path_rejects_blocked_segments(relative):
    assert not validate_relative_path(relative)


@pytest.mark.parametrize(
    "relative",
    [
        "../outside.py",
        "active/../../outside.py",
        "/absolute/source.py",
        r"C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed\N.py",
        r"\\server\share\source.py",
        "C:drive-relative.py",
        "active/.. /outside.py",
        "active/data./runtime.py",
        "active/NUL.py",
        "active/source.py:stream",
        "",
    ],
)
def test_validate_relative_path_rejects_absolute_and_traversal_paths(relative):
    assert not validate_relative_path(relative)


def test_expand_source_paths_uses_approved_extensions_and_skips_blocked_trees(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    active = source / "active"
    active.mkdir(parents=True)
    (active / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (active / "settings.JSON").write_text("{}\n", encoding="utf-8")
    (active / "binary.exe").write_bytes(b"not source")
    (active / "data").mkdir()
    (active / "data" / "runtime.py").write_text("blocked\n", encoding="utf-8")
    reparse = active / "linked"
    reparse.mkdir()
    (reparse / "outside.py").write_text("do not follow\n", encoding="utf-8")

    real_is_reparse = sync_desktop_source._is_reparse_point

    def fake_is_reparse(path):
        return Path(path) == reparse or real_is_reparse(path)

    monkeypatch.setattr(sync_desktop_source, "_is_reparse_point", fake_is_reparse)

    assert expand_source_paths(source, ["active"], [".py", ".json"]) == [
        "active/main.py",
        "active/settings.JSON",
    ]


def test_expand_source_paths_rejects_unapproved_explicit_file(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "payload.zip").write_bytes(b"archive")

    with pytest.raises(ValueError, match="approved extension"):
        expand_source_paths(source, ["payload.zip"], [".py"])


def test_sync_uses_hashes_and_sizes_and_does_not_copy_unchanged_files(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    source_file = source / "N.py"
    source_file.write_text("print('ok')\n", encoding="utf-8")

    first = sync_sources(source, target, ["N.py"], extensions=[".py"])
    target_mtime = (target / "N.py").stat().st_mtime_ns
    second = sync_sources(source, target, ["N.py"], extensions=[".py"])

    manifest = json.loads((target / "source-manifest.json").read_text(encoding="utf-8"))
    assert first["copied"] == 1
    assert first["unchanged"] == 0
    assert second["copied"] == 0
    assert second["unchanged"] == 1
    assert (target / "N.py").stat().st_mtime_ns == target_mtime
    assert manifest == {
        "schema_version": 1,
        "records": [
                {
                    "path": "N.py",
                    "sha256": hashlib.sha256(source_file.read_bytes()).hexdigest(),
                    "bytes": source_file.stat().st_size,
                }
        ],
    }


def test_dry_run_reports_changes_without_writing_target_or_manifest(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "N.py").write_text("print('dry run')\n", encoding="utf-8")

    result = sync_sources(
        source,
        target,
        ["N.py"],
        extensions=[".py"],
        dry_run=True,
    )

    assert result["mode"] == "dry-run"
    assert result["copied"] == 1
    assert not target.exists()


def test_sync_rejects_reparse_component_in_target_before_copy(tmp_path, monkeypatch):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source_file = source / "safe" / "N.py"
    target_component = target / "safe"
    source_file.parent.mkdir(parents=True)
    target_component.mkdir(parents=True)
    source_file.write_text("print('contained')\n", encoding="utf-8")
    real_is_reparse = sync_desktop_source._is_reparse_point

    def fake_is_reparse(path):
        return Path(path) == target_component or real_is_reparse(path)

    monkeypatch.setattr(sync_desktop_source, "_is_reparse_point", fake_is_reparse)

    with pytest.raises(ValueError, match="reparse point"):
        sync_sources(source, target, ["safe/N.py"], extensions=[".py"])

    assert not (target_component / "N.py").exists()


def test_manifest_is_replaced_atomically_inside_target(tmp_path, monkeypatch):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "N.py").write_text("print('atomic')\n", encoding="utf-8")
    real_replace = os.replace
    replacements = []

    def recording_replace(source_path, destination_path):
        replacements.append((Path(source_path), Path(destination_path)))
        real_replace(source_path, destination_path)

    monkeypatch.setattr(sync_desktop_source.os, "replace", recording_replace)

    sync_sources(source, target, ["N.py"], extensions=[".py"])

    manifest_path = target / "source-manifest.json"
    assert len(replacements) == 1
    temporary_path, destination_path = replacements[0]
    assert temporary_path.parent == target
    assert destination_path == manifest_path
    assert not temporary_path.exists()
    assert not list(target.glob("*.tmp"))


def test_cli_has_fixed_canonical_source_and_dry_run_and_sync_modes(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "canonical-source"
    target = tmp_path / "git-output"
    allowlist_path = tmp_path / "allowlist.json"
    source.mkdir()
    (source / "N.py").write_text("print('cli')\n", encoding="utf-8")
    allowlist_path.write_text(
        json.dumps({"roots": ["N.py"], "extensions": [".py"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(sync_desktop_source, "CANONICAL_SOURCE_ROOT", source)

    assert str(CANONICAL_SOURCE_ROOT) == r"C:\LightSpeed_Consolidated"
    assert (
        main(
            [
                "--allowlist",
                str(allowlist_path),
                "--target-root",
                str(target),
                "--dry-run",
            ]
        )
        == 0
    )
    dry_run_output = json.loads(capsys.readouterr().out)
    assert dry_run_output["mode"] == "dry-run"
    assert not target.exists()

    assert (
        main(
            [
                "--allowlist",
                str(allowlist_path),
                "--target-root",
                str(target),
                "--sync",
            ]
        )
        == 0
    )
    sync_output = json.loads(capsys.readouterr().out)
    assert sync_output["mode"] == "sync"
    assert (target / "N.py").is_file()
    assert (target / "source-manifest.json").is_file()


def test_repository_allowlist_names_only_active_source_roots_and_extensions():
    allowlist = load_allowlist(REPO_ROOT / "tools" / "source_allowlist.json")

    assert allowlist["roots"] == [
        "Desktop_Hooks/LightSpeed/N.py",
        "Desktop_Hooks/LightSpeed/__main__.py",
        "Desktop_Hooks/LightSpeed/launcher_exe.py",
        "Desktop_Hooks/LightSpeed/verify_launch_ready.py",
        "Desktop_Hooks/LightSpeed/config",
        "Desktop_Hooks/LightSpeed/tests",
        "Desktop_Hooks/LightSpeed/dataindex",
        "LightSpeed_Runtime/lightspeed_runtime",
    ]
    assert allowlist["extensions"] == [
        ".py",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".md",
        ".ini",
        ".cfg",
    ]
