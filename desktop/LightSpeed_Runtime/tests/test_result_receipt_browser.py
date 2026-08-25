from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime import ls_go_bridge, result_receipt_browser


def _results_root(shell: Path) -> Path:
    return shell / "Z Axis" / "Z+2_Neo" / "data" / "actions" / "results"


def _write_receipt(root: Path, result_id: str, **overrides) -> tuple[Path, dict]:
    payload = {
        "schema_version": "lightspeed-go-local-result-v1",
        "result_id": result_id,
        "command_id": result_id.replace("RESULT", "TASK", 1),
        "task_id": 490,
        "job_id": 490026,
        "status": "completed",
        "action_type": "rfs_emff_sweep",
        "target_floor": "TheConstruct",
        "created_utc": "2026-08-24T19:22:34+10:00",
        "completed_utc": "2026-08-24T19:22:35+10:00",
        "public_safe": True,
        "proof_required": True,
        "public_publish_authorized": False,
        "drive_write_executed": False,
        "receipt_path": r"D:\LightSpeed\App\private\receipt.json",
        "shell_root": r"D:\LightSpeed\App",
        "summary": "Bounded local result.",
        "workflow": {"private_path": r"D:\LightSpeed\private"},
    }
    payload.update(overrides)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{result_id}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path, payload


def _snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.iterdir()
        if path.is_file()
    }


def test_result_receipt_index_is_path_free_bounded_and_read_only(tmp_path):
    root = _results_root(tmp_path)
    newest, _ = _write_receipt(root, "LSGO-RESULT-NEW")
    _write_receipt(
        root,
        "LSGO-RESULT-HELD",
        status="held",
        completed_utc="2026-08-23T10:00:00Z",
        public_safe=None,
        proof_required=None,
    )
    before = _snapshot(root)

    response = result_receipt_browser.list_result_receipts(tmp_path, limit=1)

    assert response["schema_version"] == "lightspeed-local-results-index-v1"
    assert response["state"] == "available"
    assert [item["result_id"] for item in response["results"]] == ["LSGO-RESULT-NEW"]
    assert response["summary"] == {
        "visible_result_count": 1,
        "invalid_file_count": 0,
        "scanned_file_count": 2,
        "limit": 1,
        "truncated": True,
        "status_counts": {"completed": 1, "held": 1},
    }
    record = response["results"][0]
    assert record["sha256"] == hashlib.sha256(newest.read_bytes()).hexdigest()
    assert record["public_safe_state"] == "true"
    assert record["proof_required_state"] == "true"
    serialized = json.dumps(response)
    assert "receipt_path" not in serialized
    assert "shell_root" not in serialized
    assert "workflow" not in serialized
    assert "private_path" not in serialized
    assert "Bounded local result" not in serialized
    assert str(root) not in serialized
    assert _snapshot(root) == before


def test_result_receipt_index_excludes_invalid_oversized_and_reparse_files(
    tmp_path, monkeypatch
):
    root = _results_root(tmp_path)
    _write_receipt(root, "LSGO-RESULT-VALID")
    malformed = root / "LSGO-RESULT-MALFORMED.json"
    malformed.write_text("{not-json", encoding="utf-8")
    mismatch = root / "LSGO-RESULT-MISMATCH.json"
    mismatch.write_text(
        json.dumps(
            {
                "schema_version": "lightspeed-go-local-result-v1",
                "result_id": "LSGO-RESULT-DIFFERENT",
            }
        ),
        encoding="utf-8",
    )
    oversized = root / "LSGO-RESULT-OVERSIZED.json"
    oversized.write_bytes(b" " * (result_receipt_browser.MAX_RECEIPT_BYTES + 1))
    reparse, _ = _write_receipt(root, "LSGO-RESULT-REPARSE")
    original_reparse_check = result_receipt_browser._is_reparse_point
    monkeypatch.setattr(
        result_receipt_browser,
        "_is_reparse_point",
        lambda path: path == reparse or original_reparse_check(path),
    )

    response = result_receipt_browser.list_result_receipts(tmp_path)

    assert [item["result_id"] for item in response["results"]] == ["LSGO-RESULT-VALID"]
    assert response["summary"]["invalid_file_count"] == 4
    assert response["summary"]["scanned_file_count"] == 5


def test_missing_result_receipt_root_returns_empty_without_creating_it(tmp_path):
    root = _results_root(tmp_path)

    response = result_receipt_browser.list_result_receipts(tmp_path)

    assert response["state"] == "empty"
    assert response["results"] == []
    assert not root.exists()


def test_open_result_receipt_returns_exact_owner_payload_without_mutation(tmp_path):
    root = _results_root(tmp_path)
    path, payload = _write_receipt(root, "LSGO-RESULT-OPEN")
    before = _snapshot(root)

    opened = result_receipt_browser.open_result_receipt(
        tmp_path,
        result_id="LSGO-RESULT-OPEN",
    )

    assert opened["schema_version"] == "lightspeed-local-result-open-v1"
    assert opened["state"] == "opened_read_only"
    assert opened["result"] == payload
    assert opened["identity"]["result_id"] == "LSGO-RESULT-OPEN"
    assert opened["identity"]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert "path" not in opened["identity"]
    assert opened["source_mutated"] is False
    assert _snapshot(root) == before


@pytest.mark.parametrize(
    "result_id",
    ["../outside", r"C:\outside", "nested/receipt", "bad:id", ""],
)
def test_open_result_receipt_rejects_non_identifier_paths(tmp_path, result_id):
    with pytest.raises(result_receipt_browser.ResultReceiptIdRejected):
        result_receipt_browser.open_result_receipt(tmp_path, result_id=result_id)


def test_result_receipt_bridge_exposes_auth_state_and_fails_closed(tmp_path, monkeypatch):
    root = _results_root(tmp_path)
    _, payload = _write_receipt(root, "LSGO-RESULT-BRIDGE")
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    monkeypatch.delenv(ls_go_bridge.OWNER_CONFIRMATION_ENV, raising=False)
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    status_without_auth = client.get("/api/v1/status")
    listing = client.get("/api/v1/results")
    unauthenticated = client.get("/api/v1/results/LSGO-RESULT-BRIDGE")

    assert status_without_auth.status_code == 200
    assert status_without_auth.json()["auth"] == {
        "configured": False,
        "mode": "owner_confirmation_header",
    }
    assert listing.status_code == 200
    assert listing.json()["results"][0]["result_id"] == "LSGO-RESULT-BRIDGE"
    assert "receipt_path" not in json.dumps(listing.json())
    assert unauthenticated.status_code == 403
    assert "not configured" in unauthenticated.json()["detail"]

    monkeypatch.setenv(ls_go_bridge.OWNER_CONFIRMATION_ENV, "owner-test-token")
    wrong = client.get(
        "/api/v1/results/LSGO-RESULT-BRIDGE",
        headers={"X-LightSpeed-Owner-Confirmation": "wrong"},
    )
    opened = client.get(
        "/api/v1/results/LSGO-RESULT-BRIDGE",
        headers={"X-LightSpeed-Owner-Confirmation": "owner-test-token"},
    )
    invalid = client.get(
        "/api/v1/results/bad:id",
        headers={"X-LightSpeed-Owner-Confirmation": "owner-test-token"},
    )
    missing = client.get(
        "/api/v1/results/LSGO-RESULT-MISSING",
        headers={"X-LightSpeed-Owner-Confirmation": "owner-test-token"},
    )

    assert wrong.status_code == 403
    assert opened.status_code == 200
    assert opened.json()["result"] == payload
    assert opened.json()["source_mutated"] is False
    assert invalid.status_code == 400
    assert missing.status_code == 404
    assert client.get("/api/v1/status").json()["auth"]["configured"] is True
