"""Exercise path resolution without importing the desktop UI or starting services."""
import ast
import os
from pathlib import Path
from typing import Optional

import pytest


@pytest.fixture(params=["N.py", "__main__.py"])
def resolve(request, tmp_path, monkeypatch):
    monkeypatch.delenv("LIGHTSPEED_RUNTIME_ROOT", raising=False)
    source = Path(__file__).resolve().parents[1] / "desktop/Desktop_Hooks/LightSpeed" / request.param
    tree = ast.parse(source.read_text(encoding="utf-8-sig"))
    nodes = [n for n in tree.body if (
        isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_CANONICAL_RUNTIME_CANDIDATES" for t in n.targets)
    ) or (isinstance(n, ast.FunctionDef) and n.name == "_resolve_canonical_runtime_root")]
    assert len(nodes) == 2
    app = tmp_path / "Relocated Suite" / "App"
    namespace = {"LIGHTSPEED_ROOT": app, "Path": Path, "Optional": Optional, "os": os}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), namespace)
    return namespace["_resolve_canonical_runtime_root"], app


def package(root):
    (root / "lightspeed_runtime").mkdir(parents=True)
    (root / "lightspeed_runtime/__init__.py").write_text("", encoding="utf-8")
    return root.resolve()


def test_relocated_core_without_installed_paths(resolve):
    find, app = resolve
    expected = package(app.parent / "Core")
    assert find() == expected


def test_configured_absolute_runtime_precedes_core(resolve, monkeypatch, tmp_path):
    find, app = resolve
    package(app.parent / "Core")
    configured = package(tmp_path / "Selected Runtime")
    monkeypatch.setenv("LIGHTSPEED_RUNTIME_ROOT", str(configured))
    assert find() == configured


@pytest.mark.parametrize("configured", ["relative-runtime", "missing-absolute"])
def test_invalid_configured_root_does_not_hide_legacy_runtime(resolve, monkeypatch, tmp_path, configured):
    find, app = resolve
    value = str(tmp_path / "absent") if configured == "missing-absolute" else configured
    monkeypatch.setenv("LIGHTSPEED_RUNTIME_ROOT", value)
    expected = package(app.parent.parent / "LightSpeed_Runtime")
    (app.parent / "Core").mkdir(parents=True)
    assert find() == expected


def test_legacy_embedded_runtime_and_missing_layout(resolve):
    find, app = resolve
    assert find() is None
    expected = package(app / "canonical_runtime")
    assert find() == expected
