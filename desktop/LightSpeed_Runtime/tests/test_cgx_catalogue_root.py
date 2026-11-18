from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lightspeed_runtime.cgx_catalogue_root import resolve_cgx_catalogue_root


def test_source_layout_uses_one_authoritative_repo(tmp_path):
    module = tmp_path / "repo" / "desktop" / "LightSpeed_Runtime" / "lightspeed_runtime" / "cgx_capability_registry.py"
    module.parent.mkdir(parents=True)
    for rel in ("cgx/domain_templates/plugin_capability_routes.json",
                "plugins/source/selector_shortcalls.json"):
        p = tmp_path / "repo" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}", encoding="utf-8")
    assert resolve_cgx_catalogue_root(module) == tmp_path / "repo"


def test_installed_layout_uses_snapshot_not_drive_root(tmp_path):
    module = tmp_path / "Core" / "lightspeed_runtime" / "cgx_capability_registry.py"
    module.parent.mkdir(parents=True)
    for rel in ("cgx/domain_templates/plugin_capability_routes.json",
                "plugins/source/selector_shortcalls.json"):
        p = tmp_path / "Core" / "cgx_catalogue" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}", encoding="utf-8")
    assert resolve_cgx_catalogue_root(module) == tmp_path / "Core" / "cgx_catalogue"


def test_missing_installed_snapshot_never_falls_back_to_drive_root(tmp_path):
    module = tmp_path / "Core" / "lightspeed_runtime" / "cgx_capability_registry.py"
    module.parent.mkdir(parents=True)
    assert resolve_cgx_catalogue_root(module) == tmp_path / "Core" / "cgx_catalogue"
