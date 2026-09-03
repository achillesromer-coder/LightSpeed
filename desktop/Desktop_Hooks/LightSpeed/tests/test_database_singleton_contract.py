from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from core.services import database as database_module


def _install_test_operator_namespace(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, create_database: bool = True
) -> Path:
    operator_root = tmp_path / "operator"
    canonical = operator_root / "Data" / "db" / "lightspeed_unified.db"
    canonical.parent.mkdir(parents=True)
    if create_database:
        sqlite3.connect(canonical).close()
    monkeypatch.setattr(database_module, "CANONICAL_OPERATOR_ROOT", operator_root)
    monkeypatch.setattr(database_module, "CANONICAL_OPERATOR_DATABASE", canonical)
    return canonical


def test_configured_default_database_is_existing_singleton(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    canonical = _install_test_operator_namespace(monkeypatch, tmp_path)
    alias = tmp_path / "canonical-alias.db"
    os.link(canonical, alias)
    monkeypatch.setenv(database_module.CANONICAL_DATABASE_ENV, str(alias))

    resolved, enforced = database_module._default_database_path()

    assert enforced is True
    assert resolved == canonical
    assert os.path.samefile(alias, resolved)


def test_missing_configured_default_database_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_test_operator_namespace(monkeypatch, tmp_path)
    missing = tmp_path / "missing" / "lightspeed_unified.db"
    monkeypatch.setenv(database_module.CANONICAL_DATABASE_ENV, str(missing))

    with pytest.raises(FileNotFoundError, match="does not exist"):
        database_module._default_database_path()

    assert not missing.exists()
    assert not missing.parent.exists()


def test_distinct_existing_configured_database_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    canonical = _install_test_operator_namespace(monkeypatch, tmp_path)
    distinct = tmp_path / "distinct" / "lightspeed_unified.db"
    distinct.parent.mkdir(parents=True)
    sqlite3.connect(distinct).close()
    monkeypatch.setenv(database_module.CANONICAL_DATABASE_ENV, str(distinct))

    with pytest.raises(ValueError, match="same file"):
        database_module._default_database_path()

    assert canonical.exists()
    assert distinct.exists()
    assert not os.path.samefile(canonical, distinct)


def test_missing_windows_canonical_database_fails_before_alias_use(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    canonical = _install_test_operator_namespace(monkeypatch, tmp_path, create_database=False)
    alias_candidate = tmp_path / "other" / "lightspeed_unified.db"
    alias_candidate.parent.mkdir(parents=True)
    sqlite3.connect(alias_candidate).close()
    monkeypatch.setenv(database_module.CANONICAL_DATABASE_ENV, str(alias_candidate))

    with pytest.raises(FileNotFoundError, match="sole canonical database is missing"):
        database_module._default_database_path()

    assert not canonical.exists()


def test_missing_windows_operator_namespace_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    operator_root = tmp_path / "absent-operator"
    canonical = operator_root / "Data" / "db" / "lightspeed_unified.db"
    monkeypatch.setattr(database_module, "CANONICAL_OPERATOR_ROOT", operator_root)
    monkeypatch.setattr(database_module, "CANONICAL_OPERATOR_DATABASE", canonical)
    monkeypatch.delenv(database_module.CANONICAL_DATABASE_ENV, raising=False)

    with pytest.raises(FileNotFoundError, match="operator namespace is unavailable"):
        database_module._default_database_path()

    assert not operator_root.exists()


def test_unconfigured_windows_default_returns_existing_canonical_namespace(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    canonical = _install_test_operator_namespace(monkeypatch, tmp_path)
    monkeypatch.delenv(database_module.CANONICAL_DATABASE_ENV, raising=False)

    resolved, enforced = database_module._default_database_path()

    assert enforced is True
    assert resolved == canonical


def test_explicit_fixture_database_path_remains_isolated(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv(database_module.CANONICAL_DATABASE_ENV, raising=False)
    fixture = tmp_path / "fixture" / "test.db"

    service = database_module.DatabaseService(str(fixture))

    assert service.operator_canonical is False
    assert service.db_path == fixture
    assert fixture.exists()
