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
        "LightSpeed_Runtime/lightspeed_runtime/reservoirs",
        "LightSpeed_Runtime/lightspeed_runtime/reservoirs/registry.py",
    ],
)
def test_validate_relative_path_accepts_source_paths(relative):
    assert validate_relative_path(relative)


@pytest.mark.parametrize(
    "relative",
    [
        "Desktop_Hooks/LightSpeed/data/runtime.db",
        "Desktop_Hooks/LightSpeed/Z Axis/Z+1_Architect/projects/romer/task.json",
        "Desktop_Hooks/LightSpeed/Z Axis/Z-3_Smith/queues/pending.json",
        "Desktop_Hooks/LightSpeed/Z Axis/Z-2_Oracle/Z Direct/objects.json",
        "Desktop_Hooks/LightSpeed/Z Axis/Z-4_Merovingian/logs/runtime.json",
        "Desktop_Hooks/LightSpeed/Z Axis/Z+2_Neo/outputs/result.json",
        "Desktop_Hooks/LightSpeed/Z Axis/Z0_TheConstruct/tools/GMAT/api.py",
        "Desktop_Hooks/LightSpeed/Z Axis/Z-1_Morpheus/documentation/build.md",
        "Desktop_Hooks/LightSpeed/ARCHIVE/old.py",
        "Desktop_Hooks/LightSpeed/documentation/archives/old.md",
        "Desktop_Hooks/LightSpeed/ai_logs/run.json",
        "Desktop_Hooks/LightSpeed/__pycache__/N.pyc",
        "Desktop_Hooks/LightSpeed/.pytest_cache/state.json",
        "Desktop_Hooks/LightSpeed/node_modules/package/index.js",
        "Desktop_Hooks/LightSpeed/reservoirs/raw.json",
        "LightSpeed_Runtime/lightspeed_runtime/reservoirs/raw.json",
        "LightSpeed_Runtime/lightspeed_runtime/reservoirs/weights/model.gguf",
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


def test_expand_source_paths_excludes_denied_state_and_secret_names(tmp_path):
    source = tmp_path / "source"
    config = source / "config"
    runtime = config / "runtime"
    runtime.mkdir(parents=True)
    for name in [
        "stable_contract.json",
        "cognigrex_setup_state.json",
        "client_secret.json",
        "oauth_credentials.json",
        "access_token.json",
        "sync_receipt.json",
        "generated_runtime_state.json",
        "personal_settings.json",
        "user_config.json",
    ]:
        (config / name).write_text("{}\n", encoding="utf-8")
    (runtime / "session.json").write_text("{}\n", encoding="utf-8")

    expanded = expand_source_paths(
        source,
        ["config"],
        [".json"],
        deny_patterns=[
            "**/*secret*",
            "**/*credential*",
            "**/*token*",
            "**/*receipt*",
            "**/*personal*",
            "**/*setup_state*",
            "**/*state*.json",
            "**/runtime/**",
            "**/user_config.json",
        ],
    )

    assert expanded == ["config/stable_contract.json"]


def test_expand_source_paths_applies_globstar_denies_at_source_root(tmp_path):
    source = tmp_path / "source"
    runtime = source / "runtime"
    runtime.mkdir(parents=True)
    (source / "client_secret.json").write_text("{}\n", encoding="utf-8")
    (runtime / "session.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="denied source path"):
        expand_source_paths(
            source,
            ["client_secret.json"],
            [".json"],
            deny_patterns=["**/*secret*"],
        )

    assert (
        expand_source_paths(
            source,
            ["runtime"],
            [".json"],
            deny_patterns=["**/runtime/**"],
        )
        == []
    )


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


def test_sync_rejects_staged_bytes_that_do_not_match_source_digest(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "N.py").write_text("print('canonical')\n", encoding="utf-8")

    def corrupt_copy(_source_handle, target_handle):
        target_handle.write(b"print('corrupt')\n")

    monkeypatch.setattr(sync_desktop_source.shutil, "copyfileobj", corrupt_copy)

    with pytest.raises(ValueError, match="staged source changed during copy"):
        sync_sources(source, target, ["N.py"])

    assert not (target / "N.py").exists()


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


def test_sync_prunes_only_unapproved_files_inside_managed_roots(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    approved_source = source / "Desktop_Hooks" / "LightSpeed" / "N.py"
    stale = target / "Desktop_Hooks" / "LightSpeed" / "stale.json"
    repository_file = target / "README.md"
    approved_source.parent.mkdir(parents=True)
    stale.parent.mkdir(parents=True)
    approved_source.write_text("print('approved')\n", encoding="utf-8")
    stale.write_text("{}\n", encoding="utf-8")
    repository_file.write_text("keep\n", encoding="utf-8")

    result = sync_sources(
        source,
        target,
        ["Desktop_Hooks/LightSpeed/N.py"],
        extensions=[".py"],
        prune_roots=["Desktop_Hooks", "LightSpeed_Runtime"],
    )

    assert result["pruned"] == 1
    assert not stale.exists()
    assert repository_file.exists()
    assert (target / "Desktop_Hooks" / "LightSpeed" / "N.py").exists()


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


def test_source_and_manifest_are_replaced_atomically_inside_target(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "N.py").write_text("print('atomic')\n", encoding="utf-8")
    real_replace = os.replace
    replacements = []
    before_replace_calls = []

    def recording_replace(source_path, destination_path):
        replacements.append((Path(source_path), Path(destination_path)))
        real_replace(source_path, destination_path)

    def before_replace(temporary_path, destination_path):
        assert temporary_path.is_file()
        before_replace_calls.append((temporary_path, destination_path))

    monkeypatch.setattr(sync_desktop_source.os, "replace", recording_replace)

    sync_sources(
        source,
        target,
        ["N.py"],
        extensions=[".py"],
        before_replace=before_replace,
    )

    manifest_path = target / "source-manifest.json"
    assert [destination for _, destination in replacements] == [
        target / "N.py",
        manifest_path,
    ]
    assert before_replace_calls == replacements
    assert len({temporary for temporary, _ in replacements}) == 2
    for temporary_path, destination_path in replacements:
        assert temporary_path.parent == destination_path.parent
        assert not temporary_path.exists()
    assert not list(target.rglob("*.tmp"))


def test_source_copy_rechecks_parent_reparse_after_temp_write(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    outside = tmp_path / "outside"
    source_file = source / "safe" / "N.py"
    target_parent = target / "safe"
    source_file.parent.mkdir(parents=True)
    target_parent.mkdir(parents=True)
    outside.mkdir()
    source_file.write_text("print('race guarded')\n", encoding="utf-8")
    injected_reparse_points = set()
    real_is_reparse = sync_desktop_source._is_reparse_point

    def fake_is_reparse(path):
        return Path(path) in injected_reparse_points or real_is_reparse(path)

    def before_replace(temporary_path, destination_path):
        if destination_path == target_parent / "N.py":
            assert temporary_path.read_bytes() == source_file.read_bytes()
            injected_reparse_points.add(target_parent)

    monkeypatch.setattr(sync_desktop_source, "_is_reparse_point", fake_is_reparse)

    with pytest.raises(ValueError, match="reparse point"):
        sync_sources(
            source,
            target,
            ["safe/N.py"],
            extensions=[".py"],
            before_replace=before_replace,
        )

    assert not (target_parent / "N.py").exists()
    assert not list(target_parent.glob("*.tmp"))
    assert not list(outside.iterdir())


def test_destination_validation_is_last_check_before_replace(tmp_path, monkeypatch):
    target = tmp_path / "target"
    destination = target / "N.py"
    target.mkdir()
    injected_reparse_points = set()
    temporary_validation_calls = 0
    real_is_reparse = sync_desktop_source._is_reparse_point
    real_validate_temporary_file = sync_desktop_source._validate_temporary_file

    def fake_is_reparse(path):
        return Path(path) in injected_reparse_points or real_is_reparse(path)

    def inject_reparse_after_temporary_validation(temporary_path, expected_guard):
        nonlocal temporary_validation_calls
        real_validate_temporary_file(temporary_path, expected_guard)
        temporary_validation_calls += 1
        if temporary_validation_calls == 2:
            injected_reparse_points.add(destination)

    monkeypatch.setattr(sync_desktop_source, "_is_reparse_point", fake_is_reparse)
    monkeypatch.setattr(
        sync_desktop_source,
        "_validate_temporary_file",
        inject_reparse_after_temporary_validation,
    )

    with pytest.raises(ValueError, match="reparse point"):
        sync_desktop_source._atomic_replace_from_writer(
            target,
            destination,
            lambda handle: handle.write(b"race guarded\n"),
            before_replace=lambda _temporary, _destination: None,
        )

    assert temporary_validation_calls == 2
    assert not destination.exists()
    assert not list(target.glob("*.tmp"))


def test_manifest_rechecks_target_reparse_after_temp_write(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    outside = tmp_path / "outside"
    source.mkdir()
    outside.mkdir()
    (source / "N.py").write_text("print('manifest guarded')\n", encoding="utf-8")
    manifest_path = target / "source-manifest.json"
    injected_reparse_points = set()
    real_is_reparse = sync_desktop_source._is_reparse_point

    def fake_is_reparse(path):
        return Path(path) in injected_reparse_points or real_is_reparse(path)

    def before_replace(temporary_path, destination_path):
        if destination_path == manifest_path:
            assert temporary_path.is_file()
            injected_reparse_points.add(manifest_path)

    monkeypatch.setattr(sync_desktop_source, "_is_reparse_point", fake_is_reparse)

    with pytest.raises(ValueError, match="reparse point"):
        sync_sources(
            source,
            target,
            ["N.py"],
            extensions=[".py"],
            before_replace=before_replace,
        )

    assert (target / "N.py").is_file()
    assert not manifest_path.exists()
    assert not list(target.glob("*.tmp"))
    assert not list(outside.iterdir())


def test_cli_has_fixed_canonical_source_and_dry_run_and_sync_modes(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "canonical-source"
    target = tmp_path / "git-output"
    allowlist_path = tmp_path / "allowlist.json"
    source.mkdir()
    (source / "N.py").write_text("print('cli')\n", encoding="utf-8")
    allowlist_path.write_text(
        json.dumps(
            {
                "roots": ["N.py"],
                "extensions": [".py"],
                "deny_patterns": ["**/*secret*"],
            }
        ),
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
            "Desktop_Hooks/LightSpeed/config/backend_frontend_build_contract.json",
            "Desktop_Hooks/LightSpeed/config/archives_policy.yaml",
            "Desktop_Hooks/LightSpeed/config/deployment_topology.json",
        "Desktop_Hooks/LightSpeed/config/floor_environment_realization_contract.json",
        "Desktop_Hooks/LightSpeed/config/function_registry.json",
        "Desktop_Hooks/LightSpeed/config/host_runtime_policy.json",
        "Desktop_Hooks/LightSpeed/config/input_staging_matrix.json",
        "Desktop_Hooks/LightSpeed/config/premium_theme_config.json",
        "Desktop_Hooks/LightSpeed/config/resource_closure_contract.json",
            "Desktop_Hooks/LightSpeed/config/workspace_lanes.json",
            "Desktop_Hooks/LightSpeed/tests",
            "Desktop_Hooks/LightSpeed/dataindex",
            "Desktop_Hooks/LightSpeed/Z Axis",
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
    assert allowlist["deny_patterns"] == [
        "**/*secret*",
        "**/*credential*",
        "**/*token*",
        "**/*receipt*",
        "**/*personal*",
        "**/*setup_state*",
        "**/*state*.json",
        "**/*_runtime.json",
        "**/runtime/**",
        "**/settings.json",
        "**/user_config.json",
        "**/unified_config.json",
        "**/ai_config.json",
        "**/apis.json",
        "**/lightspeed_config.json",
        "**/*launch_queue*.json",
        "**/*presence_roster*.json",
        "**/*inventory*.json",
        "**/*population*.json",
    ]
