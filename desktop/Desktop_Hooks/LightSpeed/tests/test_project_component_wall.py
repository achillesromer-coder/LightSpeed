from __future__ import annotations

from pathlib import Path

from lightspeed_runtime.project_component_wall import (
    DEFAULT_SMART_WIDGETS,
    add_file_tile,
    add_folder_tile,
    add_smart_widget_tile,
    add_static_icon_tile,
    artifact_action_groups,
    build_floor_action_catalog,
    build_wall_state,
    create_z_direct_handoff,
    ensure_project_wall,
    read_artifact_preview,
    preview_drawer_descriptor,
    provenance_proof_tags,
    action_schema_for_tile_kind,
    search_project_wall_items,
    table_editing_contract,
    resolve_project_root,
    resolve_child_folder_target,
    preview_renderer_descriptor,
    smart_widget_descriptor,
    tile_path_segments,
    tile_belongs_to_folder,
    tile_size_hint,
    unique_destination_path,
    write_artifact_text,
)


def test_project_wall_bootstraps_default_component_sets(tmp_path: Path) -> None:
    project = {"name": "Demo Project"}
    project_root = resolve_project_root(tmp_path, project, projects_root=tmp_path / "projects")

    payload = ensure_project_wall(project_root, project, create=True)
    state = build_wall_state(project_root, project)

    assert payload["project_name"] == "Demo Project"
    assert (project_root / "project_wall.json").exists()
    assert {item["label"] for item in state["component_sets"]} >= {
        "Documents",
        "Tables",
        "Smart Widgets",
        "Z Direct Staging",
    }
    assert {tile["kind"] for tile in state["tiles"]} >= {"folder", "smart_widget"}
    smart_widget_floors = {tile["floor"] for tile in state["tiles"] if tile["kind"] == "smart_widget"}
    assert smart_widget_floors >= {"TheConstruct", "Oracle", "Morpheus", "Smith", "Merovingian"}
    assert len(DEFAULT_SMART_WIDGETS) == 8


def test_project_wall_smart_widgets_are_contract_backed_floor_descriptors(tmp_path: Path) -> None:
    project = {"name": "Smart Widget Project"}
    project_root = tmp_path / "Smart Widget Project"
    state = ensure_project_wall(project_root, project, create=True)
    construct_tile = next(
        tile
        for tile in state["tiles"]
        if tile.get("kind") == "smart_widget" and tile.get("floor") == "TheConstruct"
    )

    descriptor = smart_widget_descriptor(construct_tile)
    preview = read_artifact_preview(project_root, construct_tile)
    renderer = preview_renderer_descriptor(project_root, construct_tile)
    groups = artifact_action_groups(project_root, construct_tile)

    assert "heliocentric_grid" in construct_tile["contract_widgets"]
    assert any(check["id"] == "construct_gmat_batch" for check in construct_tile["fidelity_checks"])
    assert descriptor["export"]["supported"] is True
    assert preview["preview_mode"] == "smart_widget"
    assert preview["status"] == "ok"
    assert preview["smart_widget"]["floor"] == "TheConstruct"
    assert preview["drawer_descriptor"]["renderer"]["route"] == "smart_floor_widget"
    assert renderer["route"] == "smart_floor_widget"
    assert renderer["rerun"]["supported"] is True
    assert any(action["id"] == "open_floor_widget" for action in groups["open"])
    assert any(action["id"] == "export_widget_contract" for action in groups["export"])
    assert not any(action["id"] == "open_external" for action in groups.get("open", []))


def test_project_wall_adds_folder_file_icon_and_widget_tiles(tmp_path: Path) -> None:
    project = {"name": "Tile Project"}
    project_root = tmp_path / "Tile Project"
    ensure_project_wall(project_root, project, create=True)

    folder_tile = add_folder_tile(project_root, "Run Notes", parent_folder="component_sets/Documents")
    file_tile = add_file_tile(
        project_root,
        "results.csv",
        target="component_sets/Tables/results.csv",
        folder="component_sets/Tables",
    )
    icon_tile = add_static_icon_tile(project_root, "Brief", target="component_sets/Static Icons/brief.md")
    widget_tile = add_smart_widget_tile(
        project_root,
        "Neo next actions",
        floor="Neo",
        target="Planner",
        purpose="Prepare project next actions.",
    )

    state = build_wall_state(project_root, project)
    ids = {tile["id"] for tile in state["tiles"]}

    assert folder_tile["id"] in ids
    assert file_tile["id"] in ids
    assert icon_tile["id"] in ids
    assert widget_tile["id"] in ids
    assert (project_root / "component_sets" / "Documents" / "Run Notes").is_dir()


def test_project_wall_preserves_duplicate_import_targets(tmp_path: Path) -> None:
    target = tmp_path / "component_sets" / "Documents" / "brief.md"
    target.parent.mkdir(parents=True)
    target.write_text("first", encoding="utf-8")

    duplicate = unique_destination_path(target)

    assert duplicate.name == "brief (2).md"
    assert duplicate.parent == target.parent


def test_project_wall_previews_edits_and_handoffs_artifacts(tmp_path: Path) -> None:
    project_root = tmp_path / "Preview Project"
    ensure_project_wall(project_root, {"name": "Preview Project"}, create=True)
    artifact = project_root / "component_sets" / "Documents" / "note.md"
    artifact.write_text("# Start\n\nline one", encoding="utf-8")
    tile = add_file_tile(
        project_root,
        "note.md",
        target="component_sets/Documents/note.md",
        folder="component_sets/Documents",
    )

    preview = read_artifact_preview(project_root, tile)
    assert preview["editable"] is True
    assert "# Start" in preview["content"]

    update = write_artifact_text(project_root, tile, "# Updated")
    assert update["relative_path"] == "component_sets/Documents/note.md"
    assert artifact.read_text(encoding="utf-8") == "# Updated"

    handoff = create_z_direct_handoff(
        project_root,
        tile,
        target_floor="Morpheus",
        action="review_artifact",
        note="Proof the note.",
    )
    assert Path(handoff["path"]).exists()
    assert handoff["payload"]["target_floor"] == "Morpheus"
    assert handoff["relative_path"].startswith("component_sets/Z Direct Staging/")


def test_project_wall_scopes_tiles_and_models_media_actions(tmp_path: Path) -> None:
    project_root = tmp_path / "Media Project"
    ensure_project_wall(project_root, {"name": "Media Project"}, create=True)
    image = project_root / "component_sets" / "Documents" / "scan.png"
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    tile = add_file_tile(
        project_root,
        "scan.png",
        target="component_sets/Documents/scan.png",
        folder="component_sets/Documents",
    )

    preview = read_artifact_preview(project_root, tile)
    groups = artifact_action_groups(project_root, tile)

    assert tile_belongs_to_folder(tile, "component_sets/Documents") is True
    assert tile_belongs_to_folder(tile, "component_sets/Simulations") is False
    assert preview["preview_mode"] == "image"
    assert preview["editable"] is False
    assert any(action["id"] == "preview_image" for action in groups["inspect"])
    assert any(action["id"] == "open_external" for action in groups["open"])


def test_project_wall_renderer_descriptors_cover_major_artifact_modes(tmp_path: Path) -> None:
    project_root = tmp_path / "Renderer Project"
    ensure_project_wall(project_root, {"name": "Renderer Project"}, create=True)
    cases = {
        "pdf": project_root / "component_sets" / "Documents" / "brief.pdf",
        "image": project_root / "component_sets" / "Documents" / "chart.png",
        "map": project_root / "component_sets" / "Documents" / "zones.geojson",
        "spreadsheet": project_root / "component_sets" / "Tables" / "metrics.xlsx",
        "dataset": project_root / "component_sets" / "Tables" / "library.sqlite",
        "simulation": project_root / "component_sets" / "Simulations" / "run.gmat",
        "ephemeris": project_root / "component_sets" / "Simulations" / "trajectory.eph",
    }

    for suffix, path in cases.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("content", encoding="utf-8")
        tile = {
            "kind": "file",
            "label": path.name,
            "target": str(path.relative_to(project_root)).replace("\\", "/"),
            "folder": str(path.parent.relative_to(project_root)).replace("\\", "/"),
        }
        descriptor = preview_renderer_descriptor(project_root, tile)

        assert descriptor["preview_mode"] in {"pdf", "image", "map", "spreadsheet", "dataset", "simulation"}
        assert descriptor["route"]
        assert descriptor["display_hint"]
        assert isinstance(descriptor["actions"], list)
        assert "supported" in descriptor["export"]
        assert "supported" in descriptor["rerun"]
        assert descriptor["metadata_fields"]
        if suffix == "simulation":
            assert descriptor["rerun"]["supported"] is True
            assert "gmat" in descriptor["rerun"]["formats"]
        if suffix == "ephemeris":
            assert descriptor["artifact_subtype"] == "ephemeris"
            assert descriptor["rerun"]["supported"] is True
            assert "eph" in descriptor["export"]["formats"]


def test_project_wall_table_editing_contract_and_drawer_descriptor(tmp_path: Path) -> None:
    project_root = tmp_path / "Table Project"
    ensure_project_wall(project_root, {"name": "Table Project"}, create=True)
    table = project_root / "component_sets" / "Tables" / "metrics.csv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text("name,value\nalpha,1\nbeta,2", encoding="utf-8")
    tile = add_file_tile(
        project_root,
        "metrics.csv",
        target="component_sets/Tables/metrics.csv",
        folder="component_sets/Tables",
    )
    preview = read_artifact_preview(project_root, tile)
    contract = table_editing_contract(project_root, tile, preview)
    drawer = preview_drawer_descriptor(project_root, tile, preview)

    assert contract["columns"] == ["name", "value"]
    assert len(contract["editable_cells"]) == 2
    assert contract["save_target_policy"]["allowed"] is True
    assert contract["route"] == "table_editor"
    assert drawer["mode"] == "table"
    assert drawer["renderer"]["renderer_id"] in {"table", "text"}
    assert drawer["actions"]["required_groups"] == ["inspect", "open", "handoff", "copy"]
    assert any(chip["kind"] == "mode" for chip in drawer["metadata_chips"])
    assert any(chip["kind"] == "density" for chip in drawer["metadata_chips"])


def test_project_wall_provenance_tags_and_action_schema(tmp_path: Path) -> None:
    project_root = tmp_path / "Provenance Project"
    ensure_project_wall(project_root, {"name": "Provenance Project"}, create=True)
    artifact = project_root / "component_sets" / "Documents" / "source.md"
    artifact.write_text("content", encoding="utf-8")
    tile = add_file_tile(
        project_root,
        "source.md",
        target="component_sets/Documents/source.md",
        folder="component_sets/Documents",
    )
    tile["provenance"] = "Oracle"
    tile["proof_state"] = "Morpheus reviewed"
    preview = read_artifact_preview(project_root, tile)
    tags = provenance_proof_tags(tile, preview)
    schema = action_schema_for_tile_kind(tile, preview["action_groups"])

    assert any(tag["kind"] == "provenance" for tag in tags)
    assert any(tag["kind"] == "proof" for tag in tags)
    assert schema["required_groups"] == ["inspect", "open", "handoff", "copy"]
    assert schema["has_unavailable"] in {True, False}
    assert set(schema["groups"]) >= {"inspect", "open", "handoff", "copy"}


def test_project_wall_search_filter_spans_wall_model(tmp_path: Path) -> None:
    project_root = tmp_path / "Search Project"
    ensure_project_wall(project_root, {"name": "Search Project"}, create=True)
    add_file_tile(
        project_root,
        "orbit.csv",
        target="component_sets/Tables/orbit.csv",
        folder="component_sets/Tables",
    )
    add_smart_widget_tile(
        project_root,
        "Neo Route",
        floor="Neo",
        target="Planner",
        purpose="Route tasks for Neo.",
    )
    add_folder_tile(project_root, "Preview Notes", parent_folder="component_sets/Documents")
    state = build_wall_state(project_root, {"name": "Search Project"})
    result = search_project_wall_items(project_root, state, "neo")

    assert result["query"] == "neo"
    assert any(tile.get("floor") == "Neo" for tile in result["tiles"])
    assert any("Preview Notes" not in str(tile.get("label")) for tile in result["tiles"])
    assert result["count"] >= 1


def test_project_wall_breadcrumbs_safe_child_resolution_and_size_hints(tmp_path: Path) -> None:
    project_root = tmp_path / "Breadcrumb Project"
    ensure_project_wall(project_root, {"name": "Breadcrumb Project"}, create=True)
    folder_tile = add_folder_tile(project_root, "Research", parent_folder="component_sets/Documents")
    text_tile = add_file_tile(
        project_root,
        "notes.md",
        target="component_sets/Documents/Research/notes.md",
        folder="component_sets/Documents/Research",
    )

    text_preview = read_artifact_preview(project_root, text_tile)
    folder_preview = read_artifact_preview(project_root, folder_tile)
    child = resolve_child_folder_target(project_root, folder_tile, "Drafts")

    assert [segment["label"] for segment in tile_path_segments(project_root, text_tile)] == [
        "project",
        "component_sets",
        "Documents",
        "Research",
        "notes.md",
    ]
    assert [segment["path"] for segment in tile_path_segments(project_root, folder_tile)][-1].endswith("Research")
    assert child == project_root / "component_sets" / "Documents" / "Research" / "Drafts"
    assert text_preview["tile_size_hint"] == "medium"
    assert folder_preview["tile_size_hint"] == "wide"
    assert tile_size_hint({"kind": "static_icon"}, "metadata") == "small"
    assert tile_size_hint({"kind": "file"}, "image") == "large"


def test_project_wall_action_groups_cover_folder_drilldown_and_missing_targets(tmp_path: Path) -> None:
    project_root = tmp_path / "Action Project"
    ensure_project_wall(project_root, {"name": "Action Project"}, create=True)
    folder_tile = add_folder_tile(project_root, "Deliverables", parent_folder="component_sets/Documents")
    missing_file_tile = add_file_tile(
        project_root,
        "ghost.md",
        target="component_sets/Documents/ghost.md",
        folder="component_sets/Documents",
    )
    (project_root / "component_sets" / "Documents" / "ghost.md").unlink(missing_ok=True)
    unattached_icon = add_static_icon_tile(project_root, "Loose Pin")
    groups_folder = artifact_action_groups(project_root, folder_tile)
    groups_missing = artifact_action_groups(project_root, missing_file_tile)
    groups_unattached = artifact_action_groups(project_root, unattached_icon)

    assert any(action["id"] == "open_folder" for action in groups_folder["drilldown"])
    assert any(action["id"] == "replace_target" for action in groups_missing["attach"])
    assert any(action["id"] == "attach_file" for action in groups_unattached["attach"])


def test_project_wall_builds_manifest_backed_floor_action_catalog(tmp_path: Path) -> None:
    manifest = tmp_path / "Z Axis" / "Z+2_Neo" / "_FLOOR_MANIFEST.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        """
{
  "floor_name": "Neo",
  "z_level": 2,
  "description": "Operator floor",
  "components": [
    {"id": "ai_context", "name": "AI Context", "description": "Context builder", "enabled": true, "priority": "high"}
  ],
  "services": [
    {"name": "NeoCoreService", "description": "Core service", "status": "active"}
  ],
  "capabilities": ["operator_brief"]
}
""".strip(),
        encoding="utf-8",
    )

    catalog = build_floor_action_catalog(tmp_path)

    assert catalog["floor_count"] == 1
    assert catalog["action_count"] == 3
    actions = catalog["floors"][0]["actions"]
    assert {item["kind"] for item in actions} == {"component", "service", "capability"}
