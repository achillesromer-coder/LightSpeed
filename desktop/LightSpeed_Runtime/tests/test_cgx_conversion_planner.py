from __future__ import annotations

import pytest

from lightspeed_runtime.cgx_conversion_planner import CGXConversionPlanError, compile_conversion_plan


TYPE_REGISTRY = {
    "schema": "CGX-FILE-TYPE-CONVERSION-REGISTRY/0.1",
    "types": [
        {
            "id": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "extensions": ["xlsx"],
            "r1": "OOXML workbook/sheet/cell/table structure",
            "adapter": "xlsx-ooxml-stdlib-v0.1",
        },
        {
            "id": "model/step",
            "extensions": ["step", "stp"],
            "r1": None,
            "status": "specialist-adapter-required",
        },
    ],
}

CONTRACT = {
    "schema": "CGX-FILE-CONVERSION-CONTRACT/0.1",
}

FIRST_FILES = {
    "schema": "CGX-FIRST-FILE-CONVERSION-REGISTRY/0.1",
    "mappings": [
        {
            "mapping_id": "FF-MARK3-XLSX-001",
            "domain": "romer",
            "source_sha256": "a" * 64,
            "semantic_target": "/romer/mark-iii",
            "evidence_ceiling": "source-bounded semantics only",
        }
    ],
}


def test_registered_xlsx_uses_r0_r1_r2_and_preserves_authority() -> None:
    plan = compile_conversion_plan(
        file_name="Mark_III_Digital_Twin_v0_1.xlsx",
        source_sha256="a" * 64,
        source_ref="gdrive:mark3",
        domain="romer",
        requested_outputs=["mark3.graph"],
        type_registry=TYPE_REGISTRY,
        conversion_contract=CONTRACT,
        first_file_registry=FIRST_FILES,
    )
    assert [x["class"] for x in plan["stages"]] == [
        "R0_EXACT",
        "R1_SEMANTIC_REVERSIBLE",
        "R2_RECONSTRUCTED",
        "R3_GENERATIVE",
    ]
    assert plan["registered_mapping"]["mapping_id"] == "FF-MARK3-XLSX-001"
    assert plan["source"]["native_authority_preserved"] is True
    assert plan["canonical_mutation"] is False
    assert plan["authority_transfer"] is False


def test_unknown_specialist_type_stays_reference_only_and_frontiered() -> None:
    plan = compile_conversion_plan(
        file_name="MarkIII.step",
        source_sha256="b" * 64,
        source_ref="gdrive:cad",
        type_registry=TYPE_REGISTRY,
        conversion_contract=CONTRACT,
        first_file_registry=FIRST_FILES,
    )
    assert plan["semantic_state"] == "reference_only"
    assert [x["class"] for x in plan["stages"]] == ["R0_EXACT"]
    assert plan["frontier"][0]["reason"] == "SEMANTIC_ADAPTER_REQUIRED"


def test_target_without_registered_mapping_does_not_invent_r2() -> None:
    plan = compile_conversion_plan(
        file_name="unknown.xlsx",
        source_sha256="c" * 64,
        source_ref="gdrive:other",
        semantic_target="/romer/new-object",
        type_registry=TYPE_REGISTRY,
        conversion_contract=CONTRACT,
        first_file_registry=FIRST_FILES,
    )
    r2 = [x for x in plan["stages"] if x["class"] == "R2_RECONSTRUCTED"][0]
    assert r2["state"] == "HOLD_MAPPING_REQUIRED"
    assert any(x["reason"] == "SEMANTIC_MAPPING_REQUIRED" for x in plan["frontier"])


def test_invalid_hash_fails_closed() -> None:
    with pytest.raises(CGXConversionPlanError, match="SHA-256"):
        compile_conversion_plan(
            file_name="x.xlsx",
            source_sha256="not-a-hash",
            source_ref="gdrive:x",
            type_registry=TYPE_REGISTRY,
            conversion_contract=CONTRACT,
            first_file_registry=FIRST_FILES,
        )
