from __future__ import annotations

from pathlib import Path
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.consolidation_registry import (
    CONSOLIDATION_RECORDS,
    build_consolidation_register,
    write_consolidation_register,
)


def test_consolidation_records_cover_current_major_build_attempts() -> None:
    areas = {record.area for record in CONSOLIDATION_RECORDS}

    assert "Project Bento wall and smart widgets" in areas
    assert "Smart-floor visual, chart, 3D map, and simulation contracts" in areas
    assert "Oracle ingestion, dictionary, datatables, and Morpheus proofing" in areas
    assert "Z Direct handoff, Smith receipts, and dependency approvals" in areas
    assert "Release clean, publish snapshot, D-root packaging, and file culls" in areas
    assert all(record.final_runtime_files for record in CONSOLIDATION_RECORDS)
    assert all(record.packaging_gate for record in CONSOLIDATION_RECORDS)


def test_consolidation_register_validates_canonical_files_in_active_root() -> None:
    register = build_consolidation_register(RUNTIME_ROOT)

    assert register["record_count"] == len(CONSOLIDATION_RECORDS)
    assert register["canonical_complete_count"] == register["record_count"]
    assert register["missing_canonical"] == []
    project_wall = next(record for record in register["records"] if record["area"] == "Project Bento wall and smart widgets")
    assert project_wall["canonical_complete"] is True
    assert any(item["path"] == "lightspeed_runtime/project_component_wall.py" for item in project_wall["runtime_status"])


def test_write_consolidation_register_outputs_json_and_report(tmp_path: Path) -> None:
    runtime = tmp_path / "lightspeed_runtime"
    dataindex = tmp_path / "dataindex"
    trinity_ui = tmp_path / "Z Axis" / "Z+3_Trinity" / "data" / "ui"
    architect_finalization = tmp_path / "Z Axis" / "Z+1_Architect" / "data" / "finalization"
    merovingian_reports = tmp_path / "Z Axis" / "Z-4_Merovingian" / "data" / "reports" / "launch_readiness"
    diagnostics = tmp_path / "Z Axis" / "Z+3_Trinity" / "diagnostics"

    for directory in (runtime, dataindex, trinity_ui, architect_finalization, merovingian_reports, diagnostics):
        directory.mkdir(parents=True, exist_ok=True)

    for record in CONSOLIDATION_RECORDS:
        for rel_path in record.final_runtime_files:
            path = tmp_path / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if rel_path.endswith("launch_readiness"):
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.write_text("stub", encoding="utf-8")
        for rel_path in record.final_data_outputs:
            path = tmp_path / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if rel_path.endswith("launch_readiness"):
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.write_text("stub", encoding="utf-8")

    payload = write_consolidation_register(tmp_path)

    assert Path(payload["json_path"]).exists()
    assert Path(payload["report_path"]).exists()
    assert payload["canonical_complete_count"] == payload["record_count"]
    report = Path(payload["report_path"]).read_text(encoding="utf-8")
    assert "Akin Files And Final Owners" in report
    assert "Project Bento wall and smart widgets" in report
