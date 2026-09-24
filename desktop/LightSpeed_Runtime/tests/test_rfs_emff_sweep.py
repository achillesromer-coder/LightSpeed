from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import pytest


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.rfs_emff_sweep import (  # noqa: E402
    MAX_CASES,
    ReplayConflict,
    REQUEST_SCHEMA,
    SweepValidationError,
    execute_sweep,
    run_sweep,
    validate_request,
    validate_sweep_request,
)


def request_packet() -> dict:
    return {
        "schema_version": REQUEST_SCHEMA,
        "project_ref": "RFS-EMFF screening",
        "source_refs": ["local:project-overview:sha256-pending-review"],
        "base_case": {
            "rfs": {
                "frequency_hz": 10.0,
                "displacement_amplitude_m": 0.001,
                "particle_diameter_m": 0.001,
                "particle_density_kg_m3": 7800.0,
            },
            "emff": {
                "coil_turns": 100.0,
                "coil_length_m": 0.2,
                "coil_diameter_m": 0.05,
                "current_a": 1.0,
                "relative_permeability": 1.0,
                "particle_susceptibility": 0.001,
                "particle_diameter_m": 0.001,
                "particle_density_kg_m3": 7800.0,
                "field_gradient_t_per_m": 0.1,
            },
            "medium": {
                "dynamic_viscosity_pa_s": 0.001,
                "density_kg_m3": 1000.0,
            },
        },
        "axes": [
            {"path": "rfs.frequency_hz", "values": [10.0, 20.0]},
            {"path": "emff.current_a", "values": [1.0, 2.0]},
        ],
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_bounded_sweep_emits_six_immutable_derived_outputs(tmp_path: Path) -> None:
    result = run_sweep(
        request_packet(),
        command_id="LSGO-RFS-EMFF-001",
        output_root=tmp_path,
    )

    assert result["status"] == "completed"
    assert result["idempotent_replay"] is False
    assert result["row_count"] == 4
    run_dir = Path(result["run_dir"])
    assert run_dir.parent == tmp_path
    assert {path.name for path in run_dir.iterdir()} == {
        "results.json",
        "results.csv",
        "screening_sweep.png",
        "METHODS.md",
        "APPENDIX.md",
        "manifest.json",
    }
    assert (run_dir / "screening_sweep.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    payload = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    first = payload["rows"][0]
    expected_acceleration = (2.0 * math.pi * 10.0) ** 2 * 0.001
    assert first["calculations"]["rfs"]["acceleration_peak_m_s2"] == pytest.approx(
        expected_acceleration
    )
    assert payload["evidence_class"] == "derived_screening"
    assert payload["comparison_status"] == "comparison_blocked"
    assert not any(payload["claim_controls"].values())

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["canonical_role"] == "derived"
    assert manifest["validation_state"] == "comparison_blocked"
    assert manifest["review_required"] is True
    assert manifest["automatic_workbook_write"] is False
    assert manifest["automatic_dataset_catalog_write"] is False
    assert manifest["drive_write_executed"] is False
    assert manifest["public_publish_authorized"] is False
    assert manifest["dataset_catalog_candidate"]["automatic_registration"] is False
    assert {item["name"] for item in manifest["artifacts"]} == {
        "results.json",
        "results.csv",
        "screening_sweep.png",
        "METHODS.md",
        "APPENDIX.md",
    }
    for artifact in manifest["artifacts"]:
        path = run_dir / artifact["name"]
        assert artifact["size_bytes"] == path.stat().st_size
        assert artifact["sha256"] == sha256(path)
    assert result["manifest_sha256"] == sha256(run_dir / "manifest.json")

    with (run_dir / "results.csv").open(encoding="utf-8", newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    assert len(csv_rows) == 4
    assert [float(row["rfs_frequency_hz"]) for row in csv_rows] == [10.0, 10.0, 20.0, 20.0]
    assert [float(row["emff_current_a"]) for row in csv_rows] == [1.0, 2.0, 1.0, 2.0]


def test_replay_validates_hashes_without_touching_artifacts(tmp_path: Path) -> None:
    first = run_sweep(request_packet(), command_id="LSGO-RFS-EMFF-REPLAY", output_root=tmp_path)
    run_dir = Path(first["run_dir"])
    before = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in run_dir.iterdir()
    }

    replay = run_sweep(
        request_packet(),
        command_id="LSGO-RFS-EMFF-REPLAY",
        output_root=tmp_path,
    )

    assert replay["idempotent_replay"] is True
    assert replay["manifest_sha256"] == first["manifest_sha256"]
    after = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in run_dir.iterdir()
    }
    assert after == before


def test_replay_rejects_payload_change_or_artifact_tamper(tmp_path: Path) -> None:
    first = run_sweep(request_packet(), command_id="LSGO-RFS-EMFF-CONFLICT", output_root=tmp_path)
    changed = request_packet()
    changed["axes"][0]["values"] = [30.0]
    with pytest.raises(ReplayConflict, match="different sweep content"):
        run_sweep(changed, command_id="LSGO-RFS-EMFF-CONFLICT", output_root=tmp_path)

    result_path = Path(first["run_dir"]) / "results.csv"
    result_path.write_bytes(result_path.read_bytes() + b"tampered\n")
    with pytest.raises(ReplayConflict, match="hash mismatch"):
        run_sweep(request_packet(), command_id="LSGO-RFS-EMFF-CONFLICT", output_root=tmp_path)


def test_request_rejects_unbounded_or_non_screening_inputs() -> None:
    too_many = request_packet()
    too_many["axes"] = [
        {"path": "rfs.frequency_hz", "values": list(range(17))},
        {"path": "emff.current_a", "values": list(range(16))},
    ]
    with pytest.raises(SweepValidationError, match=str(MAX_CASES)):
        validate_request(too_many)

    empirical_claim = request_packet()
    empirical_claim["empirical_evidence"] = {"instrumented": True}
    with pytest.raises(SweepValidationError, match="unsupported fields"):
        validate_request(empirical_claim)

    nonfinite = request_packet()
    nonfinite["axes"][0]["values"] = [float("nan")]
    with pytest.raises(SweepValidationError, match="finite JSON values"):
        validate_request(nonfinite)

    ambiguous_gradient = request_packet()
    ambiguous_gradient["base_case"]["emff"]["grad_b2_t2_per_m"] = 0.01
    with pytest.raises(SweepValidationError, match="not both"):
        validate_request(ambiguous_gradient)


def test_axis_can_supply_a_missing_required_scalar(tmp_path: Path) -> None:
    packet = request_packet()
    del packet["base_case"]["rfs"]["frequency_hz"]

    normalized = validate_request(packet)
    result = run_sweep(normalized, command_id="LSGO-RFS-EMFF-AXIS", output_root=tmp_path)

    assert result["row_count"] == 4


def test_command_id_is_collision_safe_for_windows_path_characters(tmp_path: Path) -> None:
    colon = run_sweep(request_packet(), command_id="RFS:EMFF", output_root=tmp_path)
    underscore = run_sweep(request_packet(), command_id="RFS_EMFF", output_root=tmp_path)

    assert colon["run_dir"] != underscore["run_dir"]
    assert Path(colon["run_dir"]).parent == tmp_path
    assert Path(underscore["run_dir"]).parent == tmp_path


def test_consumer_compatible_exports_remain_bounded_to_construct_lab(tmp_path: Path) -> None:
    assert validate_sweep_request(request_packet()) == validate_request(request_packet())

    result = execute_sweep(
        request_packet(),
        task_id=489,
        job_id=490025,
        shell_root=tmp_path,
        allow_heavy=False,
        command_id="LSGO-RFS-EMFF-INTEGRATION",
    )

    assert Path(result["run_dir"]).is_relative_to(
        tmp_path / "Z Axis" / "Z0_TheConstruct" / "data" / "labs" / "rfs_emff" / "runs"
    )
    assert result["task_id"] == "489"
    assert result["job_id"] == 490025
    assert result["allow_heavy"] is False
    with pytest.raises(SweepValidationError, match="does not permit heavy"):
        execute_sweep(
            request_packet(),
            task_id=489,
            job_id=490025,
            shell_root=tmp_path,
            allow_heavy=True,
        )
