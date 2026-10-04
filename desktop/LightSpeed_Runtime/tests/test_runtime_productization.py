from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "desktop" / "LightSpeed_Runtime"
TOOLS = ROOT / "tools"


def _active_lines(name: str) -> list[str]:
    return [
        line.strip()
        for line in (RUNTIME / name).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _assert_pinned(lines: list[str]) -> None:
    for line in lines:
        if line.startswith("-r "):
            continue
        assert re.fullmatch(r"[A-Za-z0-9_.-]+==[A-Za-z0-9_.+-]+", line), line


def test_requirement_profiles_are_pinned_and_composable() -> None:
    core = _active_lines("requirements-core.txt")
    api = _active_lines("requirements-api.txt")
    data = _active_lines("requirements-data.txt")

    validation = _active_lines("requirements-validation.txt")
    dev = _active_lines("requirements-dev.txt")

    for lines in (core, api, data, validation, dev):
        _assert_pinned(lines)

    assert core == ["pydantic==2.12.4"]
    assert api[0] == "-r requirements-core.txt"
    assert {"fastapi==0.121.2", "uvicorn==0.38.0"} <= set(api)
    assert data[0] == "-r requirements-core.txt"
    assert {
        "duckdb==1.5.1",
        "pandas==2.3.3",
        "openpyxl==3.1.5",
        "PyPDF2==3.0.1",
    } <= set(data)
    assert validation == ["-r requirements-data.txt", "pandera==0.33.1"]
    assert dev[:2] == ["-r requirements-api.txt", "-r requirements-validation.txt"]
    assert dev[-1] == "pytest==9.0.1"
    assert all("FreeCAD" not in line for lines in (core, api, data, validation, dev) for line in lines)


def test_installer_declares_workspace_and_external_host_boundaries() -> None:
    installer = (TOOLS / "install_lightspeed_runtime.ps1").read_text(encoding="utf-8")

    for profile in ("core", "api", "data", "validation", "dev"):
        assert profile in installer

    assert "lightspeed_workspace.pth" in installer
    assert "[System.Text.UTF8Encoding]::new($false)" in installer
    assert "Set-Content -LiteralPath $PthPath -Encoding UTF8" not in installer
    assert "from lightspeed_runtime.cgx_preflight import build_assurance_preflight" in installer
    assert 'freecad = "external-host-capability-not-pip-managed"' in installer
    assert 'schema = "LIGHTSPEED-RUNTIME-INSTALL/0.1"' in installer
    assert '$ScriptsRoot = Join-Path $RepoRoot "scripts"' in installer
    assert '[string]$PythonCommand = ""' in installer
    assert '$PythonVersion -ne "3.11"' in installer
    assert "digital-runtime-install-receipt-only" in installer


def test_cgx_preflight_retains_repo_script_contract() -> None:
    source = (RUNTIME / "lightspeed_runtime" / "cgx_preflight.py").read_text(encoding="utf-8")

    assert 'REPO_ROOT = Path(__file__).resolve().parents[3]' in source
    assert 'SCRIPTS_ROOT = REPO_ROOT / "scripts"' in source
    assert "sys.path.insert(0, str(SCRIPTS_ROOT))" in source
    assert "from cgx_assurance_preflight import assess as assurance_assess" in source
    assert "from resolve_cgx_extensions import resolve as custodial_resolve" in source


def test_optional_capability_imports_remain_fail_soft() -> None:
    analytics = (RUNTIME / "lightspeed_runtime" / "analytics_validation.py").read_text(encoding="utf-8")
    scientific = (RUNTIME / "lightspeed_runtime" / "scientific_query.py").read_text(encoding="utf-8")
    ui = (RUNTIME / "lightspeed_runtime" / "ui_experience.py").read_text(encoding="utf-8")

    assert "import pandas as pd" in analytics
    assert "import pandera as pa" in analytics
    assert "except Exception" in analytics
    assert "import duckdb" in scientific
    assert "import pandas as pd" in scientific
    assert scientific.count("except Exception") >= 2
    assert "from PyPDF2 import PdfReader" in ui
    assert "except Exception" in ui

def test_hosted_clean_install_workflow_uses_real_installer() -> None:
    workflow = (
        ROOT / ".github" / "workflows" / "runtime-productization-validation.yml"
    ).read_text(encoding="utf-8")

    assert "runs-on: windows-latest" in workflow
    assert 'python-version: "3.11"' in workflow
    assert "install_lightspeed_runtime.ps1 -Profile dev -PythonCommand python" in workflow
    assert "pip check" in workflow
    assert "test_runtime_productization.py" in workflow
    assert "validate_cgx_capability_facades_local.py" in workflow
    assert "lightspeed-runtime-install-receipt" in workflow
    assert "contents: read" in workflow
