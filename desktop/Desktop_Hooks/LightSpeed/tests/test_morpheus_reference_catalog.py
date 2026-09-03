from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "Z Axis"
    / "Z-1_Morpheus"
    / "components"
    / "drag_drop_interface.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("morpheus_reference_catalog", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_removal_never_mutates_source_file(tmp_path):
    module = _load_module()
    source_file = tmp_path / "evidence.txt"
    source_file.write_text("empirical evidence stays intact", encoding="utf-8")

    primary = module.FileCategory("Primary")
    duplicate = module.FileCategory("Duplicate")
    primary.add_file(str(source_file))
    duplicate.add_file(str(source_file))

    removed = module.remove_catalog_references(
        {"Primary": primary, "Duplicate": duplicate},
        [str(source_file)],
    )

    assert removed == [str(source_file)]
    assert primary.files == []
    assert duplicate.files == []
    assert source_file.read_text(encoding="utf-8") == "empirical evidence stays intact"


def test_launch_controls_are_truthful_and_recursive_intake_is_disabled():
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert 'text="Remove Reference"' in source
    assert 'text="Folder Intake (held)"' in source
    assert "state=tk.DISABLED" in source
    assert "source files stay unchanged" in source
    assert ".rglob(" not in source
    assert "_delete_selected" not in source
    assert "_edit_category" not in source
    assert "_undo" not in source
    assert "_redo" not in source
