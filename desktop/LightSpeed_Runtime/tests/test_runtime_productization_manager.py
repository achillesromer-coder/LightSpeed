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


def test_install_update_and_rollback_use_managed_slot_only(
    monkeypatch, tmp_path: Path
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
        "install", slot="alpha", profile="core", confirmed=True
    )
    assert installed["state"]["installed"] is True
    assert calls == [("install", "core")]

    with pytest.raises(rp.RuntimeProductizationError, match="already installed"):
        rp.manage_runtime_productization(
            "install", slot="alpha", profile="core", confirmed=True
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
