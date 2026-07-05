from __future__ import annotations

from lightspeed_runtime.local_floor_runner import (
    build_ollama_request,
    normalize_floor_response,
    normalize_receipt_file,
)


def test_floor_request_releases_model_memory_after_each_bounded_run() -> None:
    request = build_ollama_request(
        {
            "policy": {"receipt_prompt_overrides": {"num_predict": 128}},
            "shell_root": "C:\\LightSpeed_Consolidated\\Desktop_Hooks\\LightSpeed",
        },
        {
            "floor": "Neo",
            "order": 1,
            "ollama_connection": {"model": "qwen3:8b"},
            "training_context": {},
            "assimilation_draw": {},
        },
    )

    assert request["stream"] is False
    assert request["think"] is False
    assert request["keep_alive"] == 0
    assert request["options"]["num_predict"] == 128
    assert "Approved receipt route:" in request["prompt"]
    assert "Z+2_Neo" in request["prompt"]
    assert "Do not invent or suggest an alternate path" in request["prompt"]
    assert "Keep the entire response under 90 words" in request["prompt"]
    assert "Do not use Markdown fences" in request["prompt"]


def test_plain_text_floor_response_is_normalized_to_the_receipt_contract() -> None:
    route = (
        "C:\\LightSpeed_Consolidated\\Desktop_Hooks\\LightSpeed\\Z Axis\\"
        "Z+2_Neo\\data\\temp_shells\\outputs\\local_floor_runner_receipt_Morpheus_latest.json"
    )
    normalized = normalize_floor_response(
        f"Floor 6 reviewed overlap candidates. Safe artifact route: {route}. No blocker.",
        expected_route=route,
    )

    assert normalized["floor_summary"] == "Floor 6 reviewed overlap candidates."
    assert normalized["safe_artifact_route"] == route
    assert normalized["blocker"] is None
    assert normalized["route_verified"] is True
    assert normalized["source_format"] == "normalized_text"


def test_existing_receipt_can_be_normalized_without_recalling_the_model(tmp_path) -> None:
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(
        (
            '{"response":{"response":"Summary. Safe artifact route: '
            + str(receipt_path).replace("\\", "\\\\")
            + '. No blocker."}}'
        ),
        encoding="utf-8",
    )

    receipt = normalize_receipt_file(receipt_path)

    assert receipt["response_contract"]["route_verified"] is True
    assert receipt["response_contract"]["source_format"] == "normalized_text"
