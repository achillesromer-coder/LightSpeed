from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "project_cgx_source.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_cli_with_plan_admits_registered_csv_r1(tmp_path):
    source = tmp_path / "sample.csv"
    source.write_text("id,value\nA,1\n", encoding="utf-8")
    output = tmp_path / "bundle.json"

    result = _run(
        str(source),
        "--with-plan",
        "--domain",
        "romer",
        "--output",
        str(output),
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["status"] == "PASS"
    assert summary["admission_state"] == "R1_ADMITTED"

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == "CGX-FIRST-FILE-CONFORMANCE-BUNDLE/0.1"
    receipt = payload["receipt"]
    assert receipt["schema"] == "CGX-FIRST-FILE-CONFORMANCE-RECEIPT/0.1"
    assert receipt["native_source_authority_preserved"] is True
    assert receipt["canonical_mutation"] is False
    assert receipt["execution_performed"] is False
    assert receipt["conversion_classes_admitted"] == [
        "R0_EXACT",
        "R1_SEMANTIC_REVERSIBLE",
    ]


def test_cli_with_plan_keeps_gated_dwg_at_r0_reference(tmp_path):
    source = tmp_path / "drawing.dwg"
    source.write_bytes(b"opaque-dwg")
    output = tmp_path / "bundle.json"

    result = _run(str(source), "--with-plan", "--output", str(output))

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["receipt"]["admission_state"] == "R0_REFERENCE_ONLY"
    assert payload["receipt"]["conversion_classes_admitted"] == ["R0_EXACT"]
    assert payload["conversion_plan"]["semantic_state"] == "reference_only"
    assert any(
        item["reason"] == "SEMANTIC_ADAPTER_REQUIRED"
        for item in payload["conversion_plan"]["frontier"]
    )


def test_cli_semantic_target_without_mapping_stays_frontier(tmp_path):
    source = tmp_path / "config.toml"
    source.write_text("[system]\nmode='test'\n", encoding="utf-8")
    output = tmp_path / "bundle.json"

    result = _run(
        str(source),
        "--with-plan",
        "--domain",
        "romer",
        "--semantic-target",
        "cgx:romer:unregistered-target",
        "--output",
        str(output),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    plan = payload["conversion_plan"]
    assert plan["semantic_state"] == "structure_ready"
    assert any(
        stage["class"] == "R2_RECONSTRUCTED"
        and stage["state"] == "HOLD_MAPPING_REQUIRED"
        for stage in plan["stages"]
    )
    assert any(
        item["reason"] == "SEMANTIC_MAPPING_REQUIRED"
        for item in plan["frontier"]
    )
    assert payload["receipt"]["canonical_mutation"] is False


def test_cli_default_mode_remains_backward_compatible(tmp_path):
    source = tmp_path / "note.txt"
    source.write_text("hello\n", encoding="utf-8")

    result = _run(str(source))

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "CGX-SOURCE-ENVELOPE/0.1"
    assert "conversion_plan" not in payload
