from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime import runtime_productization as rp


def _set_root(monkeypatch, tmp_path: Path) -> Path:
    root = tmp_path / "managed"
    monkeypatch.setenv("LIGHTSPEED_RUNTIME_MANAGED_ROOT", str(root))
    return root


def test_status_is_read_only_for_missing_slot(monkeypatch, tmp_path: Path) -> None:
    root = _set_root(monkeypatch, tmp_path)
    status = rp.runtime_productization_status("alpha")
    assert status["slot"] == "alpha"
    assert status["managed_marker"] is False
    assert status["configured"] is False
    assert status["installed"] is False
    assert Path(status["managed_root"]) == root
    assert not root.exists()


def test_write_actions_require_confirmation(monkeypatch, tmp_path: Path) -> None:
    _set_root(monkeypatch, tmp_path)
    for action in ("configure", "install", "update", "rollback"):
        with pytest.raises(rp.RuntimeProductizationError, match="confirmed=true"):
            rp.manage_runtime_productization(action, slot="alpha")


def test_unsafe_slot_is_rejected(monkeypatch, tmp_path: Path) -> None:
    _set_root(monkeypatch, tmp_path)
    with pytest.raises(rp.RuntimeProductizationError, match="slot must match"):
        rp.runtime_productization_status("../escape")


@pytest.mark.parametrize(
    "slot",
    [
        "CON", "con.txt", "PRN", "AUX.cfg", "NUL", "COM1", "com9.log",
        "LPT1", "lpt9.tmp", "alpha.", "alpha..",
    ],
)
def test_windows_reserved_slot_names_fail_closed_without_side_effects(
    monkeypatch, tmp_path: Path, slot: str
) -> None:
    root = _set_root(monkeypatch, tmp_path)
    with pytest.raises(rp.RuntimeProductizationError, match="Windows-reserved"):
        rp.runtime_productization_status(slot)
    assert not root.exists()


@pytest.mark.parametrize("slot", ["alpha", "conductor", "COM10", "alpha.config"])
def test_non_reserved_slot_names_remain_valid(monkeypatch, tmp_path: Path, slot: str) -> None:
    root = _set_root(monkeypatch, tmp_path)
    assert rp.runtime_productization_status(slot)["slot"] == slot
    assert not root.exists()


def test_configure_writes_bounded_marker_and_config(monkeypatch, tmp_path: Path) -> None:
    root = _set_root(monkeypatch, tmp_path)
    result = rp.manage_runtime_productization(
        "configure", slot="alpha", profile="api", confirmed=True
    )
    assert result["status"] == "PASS"
    slot = root / "alpha"
    marker = json.loads((slot / rp.MARKER_NAME).read_text(encoding="utf-8"))
    config = json.loads((slot / rp.CONFIG_NAME).read_text(encoding="utf-8"))
    assert marker["slot"] == "alpha"
    assert marker["authority"] == "digital-runtime-slot-only"
    assert config["profile"] == "api"
    assert config["authority"] == "digital-runtime-config-only"


@pytest.mark.parametrize("profile", ["core", "desktop"])
def test_install_update_and_rollback_use_managed_slot_only(
    monkeypatch, tmp_path: Path, profile: str
) -> None:
    root = _set_root(monkeypatch, tmp_path)
    calls: list[tuple[str, str]] = []

    def fake_installer(paths, *, profile: str, action: str):
        calls.append((action, profile))
        python = paths["venv"] / "Scripts" / "python.exe"
        python.parent.mkdir(parents=True, exist_ok=True)
        python.write_text("probe", encoding="utf-8")
        receipt = paths["receipt_root"] / f"{paths['slot_dir'].name}-{action}-fake.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(
            json.dumps({"schema": "LIGHTSPEED-RUNTIME-INSTALL/0.1"}),
            encoding="utf-8",
        )
        return {
            "installer_receipt": str(receipt),
            "stdout": "PASS",
            "stderr": "",
            "returncode": 0,
        }

    monkeypatch.setattr(rp, "_run_installer_process", fake_installer)

    installed = rp.manage_runtime_productization(
        "install", slot="alpha", profile=profile, confirmed=True
    )
    assert installed["state"]["installed"] is True
    assert calls == [("install", profile)]

    with pytest.raises(rp.RuntimeProductizationError, match="already installed"):
        rp.manage_runtime_productization(
            "install", slot="alpha", profile=profile, confirmed=True
        )

    updated = rp.manage_runtime_productization(
        "update", slot="alpha", profile="dev", confirmed=True
    )
    assert updated["state"]["profile"] == "dev"
    assert calls[-1] == ("update", "dev")

    rolled = rp.manage_runtime_productization(
        "rollback", slot="alpha", confirmed=True
    )
    assert rolled["state"]["installed"] is False
    assert not (root / "alpha").exists()
    assert list((root / "_receipts").glob("alpha-rollback-*.json"))


def test_rollback_refuses_unmarked_directory(monkeypatch, tmp_path: Path) -> None:
    root = _set_root(monkeypatch, tmp_path)
    slot = root / "alpha"
    slot.mkdir(parents=True)
    (slot / "keep.txt").write_text("preserve", encoding="utf-8")

    with pytest.raises(rp.RuntimeProductizationError, match="managed marker missing"):
        rp.manage_runtime_productization("rollback", slot="alpha", confirmed=True)

    assert (slot / "keep.txt").read_text(encoding="utf-8") == "preserve"


def test_update_requires_installed_slot(monkeypatch, tmp_path: Path) -> None:
    _set_root(monkeypatch, tmp_path)
    rp.manage_runtime_productization(
        "configure", slot="alpha", profile="core", confirmed=True
    )
    with pytest.raises(rp.RuntimeProductizationError, match="not installed"):
        rp.manage_runtime_productization("update", slot="alpha", confirmed=True)


def test_installer_command_respects_host_execution_policy(monkeypatch, tmp_path: Path) -> None:
    """Mock subprocess only; verify no policy override or actual installer run."""
    from types import SimpleNamespace

    _set_root(monkeypatch, tmp_path)
    fake_script = tmp_path / "installer.ps1"
    fake_script.write_text("# no execution", encoding="utf-8")
    monkeypatch.setattr(rp, "INSTALLER", fake_script)
    observed = []

    def fake_run(command, **kwargs):
        observed.append((command, kwargs))
        return SimpleNamespace(returncode=1, stdout="", stderr="policy denied")

    monkeypatch.setattr(rp.subprocess, "run", fake_run)
    with pytest.raises(rp.RuntimeProductizationError, match="policy denied"):
        rp._run_installer_process(rp._paths("alpha"), profile="core", action="install")

    assert len(observed) == 1
    command, options = observed[0]
    assert command[:2] == ["powershell", "-NoProfile"]
    assert "-ExecutionPolicy" not in command
    assert "Bypass" not in command
    assert command[command.index("-File") + 1] == str(fake_script)
    assert options["check"] is False
    assert options["timeout"] == 900


@pytest.mark.parametrize("action", ["configure", "install"])
@pytest.mark.parametrize("preexisting_file", [False, True])
def test_existing_unmarked_slot_is_never_adopted(
    monkeypatch, tmp_path: Path, action: str, preexisting_file: bool
) -> None:
    root = _set_root(monkeypatch, tmp_path)
    slot = root / "alpha"
    slot.mkdir(parents=True)
    if preexisting_file:
        (slot / "keep.txt").write_text("preserve", encoding="utf-8")

    with pytest.raises(rp.RuntimeProductizationError, match="managed marker missing"):
        rp.manage_runtime_productization(
            action, slot="alpha", profile="core", confirmed=True
        )

    assert slot.is_dir()
    assert not (slot / rp.MARKER_NAME).exists()
    assert not (slot / rp.CONFIG_NAME).exists()
    if preexisting_file:
        assert (slot / "keep.txt").read_text(encoding="utf-8") == "preserve"
    assert not (root / "_receipts").exists()


def test_symlinked_managed_slot_cannot_be_configured_or_rolled_back(
    monkeypatch, tmp_path: Path
) -> None:
    root = _set_root(monkeypatch, tmp_path)
    root.mkdir()
    target = tmp_path / "unrelated"
    target.mkdir()
    (target / "keep.txt").write_text("preserve", encoding="utf-8")
    link = root / "alpha"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation unavailable on this host")

    for action in ("configure", "rollback"):
        with pytest.raises(rp.RuntimeProductizationError, match="symlink"):
            rp.manage_runtime_productization(action, slot="alpha", confirmed=True)

    assert (target / "keep.txt").read_text(encoding="utf-8") == "preserve"
    assert not (target / rp.MARKER_NAME).exists()
    assert not (root / "_receipts").exists()


def test_symlinked_managed_root_cannot_be_configured_or_rolled_back(
    monkeypatch, tmp_path: Path
) -> None:
    root = _set_root(monkeypatch, tmp_path)
    target = tmp_path / "unrelated-root"
    target.mkdir()
    (target / "keep.txt").write_text("preserve", encoding="utf-8")
    try:
        root.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation unavailable on this host")

    for action in ("configure", "rollback"):
        with pytest.raises(rp.RuntimeProductizationError, match="managed root.*reparse"):
            rp.manage_runtime_productization(action, slot="alpha", confirmed=True)
    assert (target / "keep.txt").read_text(encoding="utf-8") == "preserve"
    assert not (target / "alpha").exists()
    assert not (target / "_receipts").exists()


@pytest.mark.parametrize("redirected", ["root", "slot"])
def test_windows_reparse_attribute_is_fail_closed_without_writes(
    monkeypatch, tmp_path: Path, redirected: str
) -> None:
    from types import SimpleNamespace

    root = _set_root(monkeypatch, tmp_path)
    slot = root / "alpha"
    slot.mkdir(parents=True)
    target = root if redirected == "root" else slot
    original_lstat = Path.lstat

    def simulated_windows_lstat(self):
        if self == target:
            return SimpleNamespace(st_file_attributes=0x400)
        return original_lstat(self)

    monkeypatch.setattr(Path, "lstat", simulated_windows_lstat)
    with pytest.raises(rp.RuntimeProductizationError, match="reparse point"):
        rp.runtime_productization_status("alpha")
    with pytest.raises(rp.RuntimeProductizationError, match="reparse point"):
        rp.manage_runtime_productization("configure", slot="alpha", confirmed=True)
    assert not (slot / rp.MARKER_NAME).exists()
    assert not (root / "_receipts").exists()

@pytest.mark.parametrize("redirected", ["receipts", "venv", "scripts"])
def test_nested_managed_directory_symlinks_fail_closed(
    monkeypatch, tmp_path: Path, redirected: str
) -> None:
    root = _set_root(monkeypatch, tmp_path)
    slot = root / "alpha"
    slot.mkdir(parents=True)
    outside = tmp_path / "unrelated"
    outside.mkdir()
    (outside / "keep.txt").write_text("preserve", encoding="utf-8")
    if redirected == "receipts":
        link = root / "_receipts"
    elif redirected == "venv":
        link = slot / "venv"
    else:
        (slot / "venv").mkdir()
        link = slot / "venv" / "Scripts"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation unavailable on this host")
    for action in ("status", "configure"):
        with pytest.raises(rp.RuntimeProductizationError, match="reparse point"):
            rp.manage_runtime_productization(
                action, slot="alpha", confirmed=(action == "configure")
            )
    assert (outside / "keep.txt").read_text(encoding="utf-8") == "preserve"
    assert not (slot / rp.MARKER_NAME).exists()
    assert not (slot / rp.CONFIG_NAME).exists()


@pytest.mark.parametrize("redirected", ["receipts", "venv", "scripts"])
def test_nested_windows_reparse_attributes_fail_closed(
    monkeypatch, tmp_path: Path, redirected: str
) -> None:
    from types import SimpleNamespace

    root = _set_root(monkeypatch, tmp_path)
    slot = root / "alpha"
    (slot / "venv" / "Scripts").mkdir(parents=True)
    target = {
        "receipts": root / "_receipts",
        "venv": slot / "venv",
        "scripts": slot / "venv" / "Scripts",
    }[redirected]
    if redirected == "receipts":
        target.mkdir()
    original_lstat = Path.lstat

    def simulated_windows_lstat(self):
        if self == target:
            return SimpleNamespace(st_file_attributes=0x400)
        return original_lstat(self)

    monkeypatch.setattr(Path, "lstat", simulated_windows_lstat)
    with pytest.raises(rp.RuntimeProductizationError, match="reparse point"):
        rp.runtime_productization_status("alpha")
    with pytest.raises(rp.RuntimeProductizationError, match="reparse point"):
        rp.manage_runtime_productization("configure", slot="alpha", confirmed=True)
    assert not (slot / rp.MARKER_NAME).exists()
    assert not (root / "_receipts" / "alpha-configure.json").exists()


def test_redirected_ancestor_of_managed_root_is_rejected(
    monkeypatch, tmp_path: Path
) -> None:
    outside = tmp_path / "unrelated"
    outside.mkdir()
    (outside / "keep.txt").write_text("preserve", encoding="utf-8")
    alias = tmp_path / "redirected-parent"
    try:
        alias.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation unavailable on this host")
    monkeypatch.setenv("LIGHTSPEED_RUNTIME_MANAGED_ROOT", str(alias / "managed"))
    for action in ("status", "configure"):
        with pytest.raises(rp.RuntimeProductizationError, match="managed root ancestor.*reparse"):
            rp.manage_runtime_productization(
                action, slot="alpha", confirmed=(action == "configure")
            )
    assert (outside / "keep.txt").read_text(encoding="utf-8") == "preserve"
    assert not (outside / "managed").exists()


def test_windows_reparse_ancestor_of_managed_root_is_rejected(
    monkeypatch, tmp_path: Path
) -> None:
    from types import SimpleNamespace

    root = _set_root(monkeypatch, tmp_path)
    original_lstat = Path.lstat

    def simulated_windows_lstat(self):
        if self == root.parent:
            return SimpleNamespace(st_file_attributes=0x400)
        return original_lstat(self)

    monkeypatch.setattr(Path, "lstat", simulated_windows_lstat)
    with pytest.raises(rp.RuntimeProductizationError, match="managed root ancestor.*reparse"):
        rp.runtime_productization_status("alpha")
    assert not root.exists()


@pytest.mark.parametrize("root_kind", ["relative", "absolute-parent-traversal"])
def test_nonabsolute_or_parent_traversal_managed_root_is_rejected(
    monkeypatch, tmp_path: Path, root_kind: str
) -> None:
    managed_root = (
        "relative-managed"
        if root_kind == "relative"
        else str(tmp_path / "segment" / ".." / "managed")
    )
    monkeypatch.setenv("LIGHTSPEED_RUNTIME_MANAGED_ROOT", managed_root)
    with pytest.raises(rp.RuntimeProductizationError, match="absolute path without parent traversal"):
        rp.runtime_productization_status("alpha")
    assert not (tmp_path / "managed").exists()
@pytest.mark.parametrize(
    "ownership",
    ["missing", "valid", "wrong_schema", "wrong_slot", "non_object", "invalid_json"],
)
def test_status_requires_valid_managed_ownership_not_just_python_file(
    monkeypatch, tmp_path: Path, ownership: str
) -> None:
    root = _set_root(monkeypatch, tmp_path)
    slot_dir = root / "alpha"
    python_path = slot_dir / "venv" / "Scripts" / "python.exe"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("not an executable; status fixture only", encoding="utf-8")
    marker_path = slot_dir / rp.MARKER_NAME
    marker = {
        "schema": "LIGHTSPEED-MANAGED-RUNTIME-MARKER/0.1",
        "slot": "alpha",
        "profile": "core",
        "authority": "digital-runtime-slot-only",
    }
    if ownership == "wrong_schema":
        marker["schema"] = "UNTRUSTED-MARKER/0.1"
    elif ownership == "wrong_slot":
        marker["slot"] = "other"
    if ownership == "non_object":
        marker_path.write_text("[]", encoding="utf-8")
    elif ownership == "invalid_json":
        marker_path.write_text("{invalid-json", encoding="utf-8")
    elif ownership != "missing":
        marker_path.write_text(json.dumps(marker), encoding="utf-8")

    marker_bytes_before = marker_path.read_bytes() if marker_path.exists() else None
    status = rp.runtime_productization_status("alpha")
    assert status["installed"] is (ownership == "valid")
    assert status["managed_marker"] is (
        ownership in ("valid", "wrong_schema", "wrong_slot")
    )
    assert status["authority"] == "status-only"
    assert status["profile"] == ("core" if ownership == "valid" else None)
    assert marker_path.exists() is (ownership != "missing")
    if marker_bytes_before is not None:
        assert marker_path.read_bytes() == marker_bytes_before
    assert python_path.read_text(encoding="utf-8") == (
        "not an executable; status fixture only"
    )
    assert not (root / "_receipts").exists()


def test_status_valid_marker_without_python_file_is_not_installed(
    monkeypatch, tmp_path: Path
) -> None:
    root = _set_root(monkeypatch, tmp_path)
    slot = root / "alpha"
    slot.mkdir(parents=True)
    marker = {
        "schema": "LIGHTSPEED-MANAGED-RUNTIME-MARKER/0.1",
        "slot": "alpha",
        "profile": "core",
        "authority": "digital-runtime-slot-only",
    }
    (slot / rp.MARKER_NAME).write_text(json.dumps(marker), encoding="utf-8")
    status = rp.runtime_productization_status("alpha")
    assert status["managed_marker"] is True
    assert status["installed"] is False
    assert not (slot / "venv").exists()


def test_status_executable_directory_does_not_count_as_installed(
    monkeypatch, tmp_path: Path
) -> None:
    root = _set_root(monkeypatch, tmp_path)
    slot = root / "alpha"
    python_path = slot / "venv" / "Scripts" / "python.exe"
    python_path.mkdir(parents=True)
    marker = {
        "schema": "LIGHTSPEED-MANAGED-RUNTIME-MARKER/0.1",
        "slot": "alpha",
        "profile": "core",
        "authority": "digital-runtime-slot-only",
    }
    (slot / rp.MARKER_NAME).write_text(json.dumps(marker), encoding="utf-8")
    status = rp.runtime_productization_status("alpha")
    assert status["managed_marker"] is True
    assert status["installed"] is False
@pytest.mark.parametrize("leaf", ["marker", "config", "python"])
def test_redirected_managed_leaf_files_fail_closed(
    monkeypatch, tmp_path: Path, leaf: str
) -> None:
    root = _set_root(monkeypatch, tmp_path)
    slot = root / "alpha"
    targets = {
        "marker": slot / rp.MARKER_NAME,
        "config": slot / rp.CONFIG_NAME,
        "python": slot / "venv" / "Scripts" / "python.exe",
    }
    link = targets[leaf]
    link.parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "unrelated-leaf.json"
    outside.write_text('{"keep": "unchanged"}', encoding="utf-8")
    try:
        link.symlink_to(outside, target_is_directory=False)
    except (OSError, NotImplementedError):
        pytest.skip("file symlink creation unavailable on this host")

    for action in ("status", "configure"):
        with pytest.raises(rp.RuntimeProductizationError, match="reparse point"):
            rp.manage_runtime_productization(
                action, slot="alpha", confirmed=(action == "configure")
            )
    assert outside.read_text(encoding="utf-8") == '{"keep": "unchanged"}'
    assert link.is_symlink()
    assert not (root / "_receipts").exists()


@pytest.mark.parametrize("leaf", ["marker", "config", "python"])
def test_windows_reparse_leaf_files_fail_closed(
    monkeypatch, tmp_path: Path, leaf: str
) -> None:
    from types import SimpleNamespace

    root = _set_root(monkeypatch, tmp_path)
    slot = root / "alpha"
    targets = {
        "marker": slot / rp.MARKER_NAME,
        "config": slot / rp.CONFIG_NAME,
        "python": slot / "venv" / "Scripts" / "python.exe",
    }
    target = targets[leaf]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("preserve", encoding="utf-8")
    original_lstat = Path.lstat

    def simulated_windows_lstat(self):
        if self == target:
            return SimpleNamespace(st_file_attributes=0x400)
        return original_lstat(self)

    monkeypatch.setattr(Path, "lstat", simulated_windows_lstat)
    for action in ("status", "configure"):
        with pytest.raises(rp.RuntimeProductizationError, match="reparse point"):
            rp.manage_runtime_productization(
                action, slot="alpha", confirmed=(action == "configure")
            )
    assert target.read_text(encoding="utf-8") == "preserve"
    assert not (root / "_receipts").exists()

@pytest.mark.parametrize(
    "variant",
    [
        "valid", "wrong_schema", "wrong_slot", "wrong_authority",
        "unsupported_profile", "nonstring_profile", "malformed", "non_object",
    ],
)
def test_status_quarantines_untrusted_slot_config_without_modifying_it(
    monkeypatch, tmp_path: Path, variant: str
) -> None:
    root = _set_root(monkeypatch, tmp_path)
    slot = root / "alpha"
    python_path = slot / "venv" / "Scripts" / "python.exe"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("fixture-only", encoding="utf-8")
    marker = {
        "schema": "LIGHTSPEED-MANAGED-RUNTIME-MARKER/0.1",
        "slot": "alpha",
        "profile": "core",
        "authority": "digital-runtime-slot-only",
    }
    (slot / rp.MARKER_NAME).write_text(json.dumps(marker), encoding="utf-8")
    config = {
        "schema": "LIGHTSPEED-RUNTIME-SLOT-CONFIG/0.1",
        "slot": "alpha",
        "profile": "api",
        "authority": "digital-runtime-config-only",
    }
    if variant == "wrong_schema":
        config["schema"] = "FOREIGN-CONFIG/0.1"
    elif variant == "wrong_slot":
        config["slot"] = "beta"
    elif variant == "wrong_authority":
        config["authority"] = "untrusted"
    elif variant == "unsupported_profile":
        config["profile"] = "arbitrary-program"
    elif variant == "nonstring_profile":
        config["profile"] = ["api"]
    config_path = slot / rp.CONFIG_NAME
    if variant == "malformed":
        config_path.write_text("{broken", encoding="utf-8")
    elif variant == "non_object":
        config_path.write_text("[]", encoding="utf-8")
    else:
        config_path.write_text(json.dumps(config), encoding="utf-8")

    original = config_path.read_bytes()
    status = rp.runtime_productization_status("alpha")
    assert status["configured"] is (variant == "valid")
    assert status["profile"] == ("api" if variant == "valid" else "core")
    assert status["installed"] is True
    assert status["authority"] == "status-only"
    assert config_path.read_bytes() == original
    assert python_path.read_text(encoding="utf-8") == "fixture-only"
    assert not (root / "_receipts").exists()


@pytest.mark.parametrize(
    "variant",
    ["wrong_authority", "missing_authority", "invalid_profile", "missing_profile", "nonstring_profile"],
)
def test_invalid_marker_authority_or_profile_never_authorizes_mutation(
    monkeypatch, tmp_path: Path, variant: str
) -> None:
    root = _set_root(monkeypatch, tmp_path)
    slot = root / "alpha"
    python_path = slot / "venv" / "Scripts" / "python.exe"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("fixture-only; never execute", encoding="utf-8")
    protected = slot / "preserve.txt"
    protected.write_text("unrelated bytes", encoding="utf-8")
    marker_path = slot / rp.MARKER_NAME
    marker = {
        "schema": "LIGHTSPEED-MANAGED-RUNTIME-MARKER/0.1",
        "slot": "alpha",
        "authority": "digital-runtime-slot-only",
        "profile": "core",
    }
    if variant == "wrong_authority":
        marker["authority"] = "host-root-authority"
    elif variant == "missing_authority":
        del marker["authority"]
    elif variant == "invalid_profile":
        marker["profile"] = "arbitrary-executable"
    elif variant == "missing_profile":
        del marker["profile"]
    elif variant == "nonstring_profile":
        marker["profile"] = ["core"]
    marker_path.write_text(json.dumps(marker), encoding="utf-8")
    marker_bytes = marker_path.read_bytes()

    status = rp.runtime_productization_status("alpha")
    assert status["installed"] is False
    assert status["authority"] == "status-only"
    for action in ("configure", "update", "rollback"):
        with pytest.raises(rp.RuntimeProductizationError, match="managed marker"):
            rp.manage_runtime_productization(
                action, slot="alpha", profile="core", confirmed=True
            )
    assert marker_path.read_bytes() == marker_bytes
    assert protected.read_text(encoding="utf-8") == "unrelated bytes"
    assert python_path.read_text(encoding="utf-8") == "fixture-only; never execute"
    assert not (root / "_receipts").exists()
