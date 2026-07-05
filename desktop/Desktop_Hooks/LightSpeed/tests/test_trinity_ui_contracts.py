from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRINITY_ROOT = ROOT / "Z Axis" / "Z+3_Trinity"

IT_PORTAL = TRINITY_ROOT / "ui" / "it_portal.py"
SMART_SETTINGS_HUB = TRINITY_ROOT / "ui" / "smart_settings_hub.py"
TEMPLATE_MANAGER = TRINITY_ROOT / "ui" / "template_manager.py"
TRINITY_PORTAL_GLASS = TRINITY_ROOT / "components" / "trinity_portal_glass.py"
COGNIGREX_LOGIN = TRINITY_ROOT / "components" / "cognigrex_login.py"
SMART_BENTO_HUB = TRINITY_ROOT / "smart_bento_hub.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _parse(path: Path) -> ast.Module:
    return ast.parse(_read(path), filename=str(path))


def _literal_assignment(module: ast.Module, name: str):
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                return ast.literal_eval(node.value)
    raise AssertionError(f"Assignment not found: {name}")


def test_modified_trinity_files_parse() -> None:
    for path in (
        IT_PORTAL,
        SMART_SETTINGS_HUB,
        TEMPLATE_MANAGER,
        TRINITY_PORTAL_GLASS,
        COGNIGREX_LOGIN,
        SMART_BENTO_HUB,
    ):
        _parse(path)


def test_it_portal_collapses_trinity_feature_launchers() -> None:
    module = _parse(IT_PORTAL)
    features = _literal_assignment(module, "TRINITY_CONSOLIDATED_FEATURES")
    focus_map = _literal_assignment(module, "TRINITY_SETTINGS_FOCUS_BY_FEATURE")
    source = _read(IT_PORTAL)

    assert features == ["Portal", "Bento System", "Settings Hub"]
    assert focus_map["Themes"] == "trinity_launchers"
    assert focus_map["Templates"] == "trinity_launchers"
    assert focus_map["Wizards"] == "setup_state"
    assert '_menu_btn(' in source
    assert '"Profile + Setup"' in source
    assert '_btn("Settings Hub"' not in source
    assert '_btn("Trinity Actions"' in source
    assert '_btn("Themes"' not in source
    assert 'text="Setup State"' in source
    assert 'text="Setup Wizard"' not in source
    assert 'text="Launch Setup Wizard"' not in source
    assert 'self._open_trinity_settings_surface(focus_section="setup_state")' in source
    assert 'self._select_tab_title("Setup State")' in source


def test_smart_settings_hub_integrates_setup_and_surface_sections() -> None:
    module = _parse(SMART_SETTINGS_HUB)
    tabs = _literal_assignment(module, "SETTINGS_HUB_TAB_INDEX")
    aliases = _literal_assignment(module, "SETTINGS_HUB_FOCUS_ALIASES")
    source = _read(SMART_SETTINGS_HUB)

    assert tabs["setup_state"] == 2
    assert tabs["trinity_launchers"] == 2
    assert tabs["backgrounds"] == 1
    assert aliases["profile"] == "setup_state"
    assert aliases["account"] == "setup_state"
    assert aliases["themes"] == "trinity_launchers"
    assert aliases["templates"] == "trinity_launchers"
    assert aliases["wizards"] == "setup_state"
    assert aliases["startup"] == "startup_options"
    assert aliases["background"] == "backgrounds"
    assert tabs["startup_options"] == 2
    assert "tk.Menubutton" in source
    assert '"Profile + Setup"' in source
    assert '"Startup & Auto Options"' in source
    assert '"Background Builder"' in source
    assert '"Trinity Tools"' in source
    assert '"Profiles + Company"' in source
    assert '"Tailoring + Layout"' in source
    assert 'text="Run Setup Wizard"' not in source
    assert 'text="Enhanced Startup Wizard"' not in source
    assert 'text="Open Theme Designer"' not in source
    assert 'text="Open Template Manager"' not in source
    assert 'def _create_action_menu' in source
    assert 'self._focus_section_in_hub("setup_state")' in source


def test_template_manager_uses_single_generate_mode_control() -> None:
    module = _parse(TEMPLATE_MANAGER)
    options = _literal_assignment(module, "GENERATION_MODE_OPTIONS")
    source = _read(TEMPLATE_MANAGER)

    assert options == [
        ("Use current customizations", "template"),
        ("Reset to defaults before generate", "defaults"),
    ]
    assert 'text="Generate Output"' in source
    assert 'text="Create Blank"' not in source
    assert 'text="From Template"' not in source


def test_trinity_portal_glass_routes_settings_actions_through_hub() -> None:
    module = _parse(TRINITY_PORTAL_GLASS)
    context = _literal_assignment(module, "TRINITY_PORTAL_GLASS_SETTINGS_CONTEXT")
    source = _read(TRINITY_PORTAL_GLASS)

    assert context["page_id"] == "trinity.portal_glass.settings"
    assert context["label"] == "Trinity Portal Glass / Settings"
    assert 'text="Open Smart Settings Hub"' not in source
    assert 'text="Portal Settings"' in source
    assert 'text="Settings Content"' not in source
    assert 'text="Page Settings"' in source
    assert 'text="Trinity Tools"' in source
    assert 'text="Profile + Setup"' in source
    assert 'text="Theme + Templates"' not in source
    assert 'text="Setup Tools"' not in source
    assert 'label="Theme + Templates"' in source
    assert 'label="Profile + Setup"' in source
    assert 'open_dialog_with_context(context=context, focus_section=focus_section)' in source


def test_cognigrex_login_routes_profile_setup_through_settings_hub() -> None:
    module = _parse(COGNIGREX_LOGIN)
    context = _literal_assignment(module, "COGNIGREX_LOGIN_SETTINGS_CONTEXT")
    source = _read(COGNIGREX_LOGIN)

    assert context["page_id"] == "trinity.cognigrex_login"
    assert context["label"] == "Cognigrex Login / Profile + Setup"
    assert 'text="Run Setup Wizard"' not in source
    assert 'text="Profile + Setup"' in source
    assert '"Profiles + Company"' in source
    assert '"Tailoring + Layout"' in source
    assert 'self._open_setup_hub("setup_state")' in source
    assert 'self._open_setup_hub("tailoring")' in source
    assert 'hub.open_dialog_with_context(' in source
    assert 'self._launch_legacy_setup_wizard()' in source


def test_smart_bento_hub_uses_compact_settings_launchers() -> None:
    module = _parse(SMART_BENTO_HUB)
    context = _literal_assignment(module, "SMART_BENTO_SETTINGS_CONTEXT")
    source = _read(SMART_BENTO_HUB)

    assert context["page_id"] == "trinity.smart_bento_hub"
    assert context["label"] == "Smart Bento Hub / Profile + Setup"
    assert 'text="Profile + Setup"' in source
    assert 'text="Trinity Tools"' in source
    assert '"Profiles + Company"' in source
    assert '"Tailoring + Layout"' in source
    assert '"Theme + Templates"' in source
    assert 'self._open_settings_hub("setup_state")' in source
    assert 'self._open_settings_hub("tailoring")' in source
    assert 'self._open_settings_hub("trinity_launchers")' in source
