from __future__ import annotations

import pytest

from lightspeed_runtime.cgx_query_planner import CGXQueryPlanError, compile_query_plan


def test_retail_query_collapses_to_umbrella_plus_native_facets() -> None:
    result = compile_query_plan(
        "Dairy Free Plant Based Snacks",
        facet_schema={
            "dietary": {
                "control": "checkbox",
                "values": {
                    "Vegan": ["plant based", "plant-based", "vegan"],
                    "Dairy Free": ["dairy free", "non dairy"],
                },
            }
        },
        umbrella_terms={"Snacks": ["snacks", "snack"]},
        capability_manifest={
            "capability_id": "retail-search",
            "kind": "retrieval_search",
            "designed_functions": ["umbrella_query", "facets"],
            "accepted_inputs": ["text_query", "checkbox_facets"],
        },
    )
    assert result["umbrella_query"] == "Snacks"
    assert result["applied_facets"] == {"dietary": ["Vegan", "Dairy Free"]}
    assert [item["control"] for item in result["controls_used"]] == ["checkbox", "checkbox"]
    assert result["capability_packet"]["query"] == "Snacks"
    assert result["hydration_stage"] == 0


def test_gmat_route_produces_structured_tool_packet_without_corpus_dump() -> None:
    result = compile_query_plan(
        "simulate selected transfer using current spacecraft and epoch",
        umbrella_terms={"transfer": ["transfer"]},
        capability_manifest={
            "capability_id": "gmat",
            "kind": "gmat",
            "designed_functions": ["trajectory_simulation"],
            "accepted_inputs": ["initial_state", "epoch", "force_model", "maneuvers", "objective"],
        },
        structured_payload={
            "initial_state_ref": "STATE-001",
            "epoch_ref": "EPOCH-001",
            "force_model_ref": "FM-001",
            "objective": "evaluate_transfer",
        },
    )
    assert result["capability_packet"]["mode"] == "structured-tool"
    assert result["capability_packet"]["status"] == "ready"
    assert result["capability_packet"]["query_context"] == "transfer"
    assert "full_corpus" not in str(result["capability_packet"])


def test_unknown_explicit_facet_fails_closed() -> None:
    with pytest.raises(CGXQueryPlanError, match="unknown value"):
        compile_query_plan(
            "Snacks",
            facet_schema={"dietary": {"control": "checkbox", "values": ["Vegan"]}},
            umbrella_terms=["Snacks"],
            structured_constraints={"dietary": "Invented Diet"},
        )
