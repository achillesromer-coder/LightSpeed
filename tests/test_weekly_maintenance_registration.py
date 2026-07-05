from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "register_weekly_maintenance.ps1"


def test_registration_uses_canonical_runtime_and_friday_schedule() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert r"C:\LightSpeed_Consolidated\venv\Scripts\python.exe" in source
    assert r"C:\LightSpeed_Consolidated\LightSpeed_Runtime" in source
    assert "-m lightspeed_runtime.maintenance" in source
    assert "--root C:\\LightSpeed_Consolidated\\Desktop_Hooks\\LightSpeed" in source
    assert "-DaysOfWeek Friday" in source
    assert "-At '19:00'" in source


def test_registration_starts_missed_runs_without_waking_the_machine() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "-StartWhenAvailable" in source
    assert "-WakeToRun:$false" in source
    assert "-MultipleInstances IgnoreNew" in source
    assert "SupportsShouldProcess" in source
