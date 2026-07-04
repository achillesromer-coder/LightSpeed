from __future__ import annotations

from pathlib import Path


LIGHTSPEED_ROOT = Path(__file__).resolve().parents[1]


def test_launcher_targets_single_package_entrypoint():
    launcher = (
        LIGHTSPEED_ROOT.parent.parent
        / "Desktop_Hooks"
        / "LightSpeed"
        / "launcher_exe.py"
    ).read_text(encoding="utf-8")
    entrypoint = (LIGHTSPEED_ROOT / "__main__.py").read_text(encoding="utf-8")

    assert 'entrypoint = shell_root / "__main__.py"' in launcher
    assert 'N_ENTRYPOINT = LIGHTSPEED_ROOT / "N.py"' in entrypoint
    assert "_analysis_remote" not in entrypoint


def test_trinity_shell_is_embedded_and_readiness_checks_real_surface():
    n_source = (LIGHTSPEED_ROOT / "N.py").read_text(encoding="utf-8")
    portal_source = (
        LIGHTSPEED_ROOT
        / "Z Axis"
        / "Z+3_Trinity"
        / "ui"
        / "it_portal.py"
    ).read_text(encoding="utf-8")

    assert '"Z Axis/Z+3_Trinity/ui/it_shell.py"' in n_source
    assert 'portal = ITShell(' in n_source
    assert 'class ITPortal(tk.Frame):' in portal_source
    assert 'class ITPortal(tk.Toplevel):' not in portal_source
