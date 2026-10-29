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


@pytest.mark.parametrize("managed_root", ["relative-managed", "segment/../managed"])
def test_nonabsolute_or_parent_traversal_managed_root_is_rejected(
    monkeypatch, managed_root: str
) -> None:
    monkeypatch.setenv("LIGHTSPEED_RUNTIME_MANAGED_ROOT", managed_root)
    with pytest.raises(rp.RuntimeProductizationError, match="absolute path without parent traversal"):
        rp.runtime_productization_status("alpha")
