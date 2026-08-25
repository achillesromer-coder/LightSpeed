from __future__ import annotations

import ast
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
    shell_source = (
        LIGHTSPEED_ROOT
        / "Z Axis"
        / "Z+3_Trinity"
        / "ui"
        / "it_shell.py"
    ).read_text(encoding="utf-8")
    portal_source = (
        LIGHTSPEED_ROOT
        / "Z Axis"
        / "Z+3_Trinity"
        / "ui"
        / "it_portal.py"
    ).read_text(encoding="utf-8")

    assert '"Z Axis/Z+3_Trinity/ui/it_shell.py"' in n_source
    assert 'portal = ITShell(' in n_source
    assert "host_floor = host_floor_name(floor)" in shell_source
    assert "renderer(self.content_host, host_floor)" in shell_source
    assert 'class ITPortal(tk.Frame):' in portal_source
    assert 'class ITPortal(tk.Toplevel):' not in portal_source


def test_n_routes_shell_floors_to_real_canonical_entrypoints():
    n_path = LIGHTSPEED_ROOT / "N.py"
    n_source = n_path.read_text(encoding="utf-8-sig")
    n_module = ast.parse(n_source, filename=str(n_path))
    floor_locations = None
    loader_source = ""
    for node in n_module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "FLOOR_LOCATIONS"
            for target in node.targets
        ):
            floor_locations = ast.literal_eval(node.value)
        if isinstance(node, ast.FunctionDef) and node.name == "_get_z_floor_module":
            loader_source = ast.get_source_segment(n_source, node) or ""

    assert floor_locations is not None
    assert floor_locations["TheConstruct"] == "Z Axis/TheConstruct.py"
    assert floor_locations["Merovingian"] == "Z Axis/Merovingian.py"
    for floor in ("TheConstruct", "Merovingian"):
        entrypoint = LIGHTSPEED_ROOT / floor_locations[floor]
        assert entrypoint.is_file()
        entrypoint_module = ast.parse(
            entrypoint.read_text(encoding="utf-8"),
            filename=str(entrypoint),
        )
        functions = {
            node.name
            for node in entrypoint_module.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert {"create_gui", "build"}.issubset(functions)

    assert 'floor_name == "Merovingian"' not in loader_source


def test_shell_labels_use_the_canonical_version_file():
    n_source = (LIGHTSPEED_ROOT / "N.py").read_text(encoding="utf-8")

    assert (LIGHTSPEED_ROOT / "VERSION").read_text(encoding="utf-8").strip() == "5.1.2"
    assert "LIGHTSPEED_VERSION = _read_lightspeed_version()" in n_source
    assert (
        'self.title(f"LightSpeed Unified Orchestrator v{LIGHTSPEED_VERSION}")'
        in n_source
    )
    assert (
        'description=f"LightSpeed Unified Orchestrator v{LIGHTSPEED_VERSION}"'
        in n_source
    )


def test_project_file_dialog_has_one_pack_only_status_bar():
    n_path = LIGHTSPEED_ROOT / "N.py"
    n_source = n_path.read_text(encoding="utf-8-sig")
    n_module = ast.parse(n_source, filename=str(n_path))
    methods = [
        node
        for node in ast.walk(n_module)
        if isinstance(node, ast.FunctionDef) and node.name == "manage_project_files"
    ]

    assert len(methods) == 1
    method_source = ast.get_source_segment(n_source, methods[0]) or ""
    assert method_source.count("status_bar = tk.Frame") == 1
    assert "progress_bar.pack(" in method_source
    assert "progress_bar.grid(" not in method_source
    assert "progress_bar.grid_remove(" not in method_source
