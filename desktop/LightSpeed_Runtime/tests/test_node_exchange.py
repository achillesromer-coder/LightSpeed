from __future__ import annotations

from pathlib import Path
import json

import pytest

from lightspeed_runtime.node_exchange import (
    NodeExchangeError,
    build_compute_request,
    build_exchange_status,
    build_transfer_envelope,
    execute_local_compute,
    execute_local_transfer,
    load_node_root_registry,
    resolve_node_root,
)


def test_node_root_registry_resolves_only_registered_access(tmp_path: Path) -> None:
    read_root = tmp_path / "read"
    write_root = tmp_path / "write"
    read_root.mkdir()
    write_root.mkdir()
    registry_path = tmp_path / "node_roots.json"
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": "cgx-node-root-registry-v1",
                "node_id": "bouwerbase",
                "roots": [
                    {
                        "root_id": "read-root",
                        "path": str(read_root),
                        "access": "read",
                        "kind": "source",
                    },
                    {
                        "root_id": "write-root",
                        "path": str(write_root),
                        "access": "read_write",
                        "kind": "staging",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    registry = load_node_root_registry(registry_path)

    assert resolve_node_root(
        registry,
        node_id="bouwerbase",
        root_id="write-root",
        require_write=True,
    ) == write_root.resolve()
    with pytest.raises(NodeExchangeError, match="not write-enabled"):
        resolve_node_root(
            registry,
            node_id="bouwerbase",
            root_id="read-root",
            require_write=True,
        )
    with pytest.raises(NodeExchangeError, match="does not belong"):
        resolve_node_root(
            registry,
            node_id="other-node",
            root_id="write-root",
        )


def test_transfer_round_trip_and_reuse(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    source = source_root / "payload.txt"
    source.write_text("CGX node exchange test\n", encoding="utf-8")

    envelope = build_transfer_envelope(
        source,
        source_node_id="node-a",
        target_node_id="node-b",
        source_root_id="source",
        target_root_id="target",
    )
    receipt = execute_local_transfer(
        envelope,
        target_root=target_root,
        allowed_source_roots=[source_root],
        allowed_target_roots=[target_root],
        lease_validation={
            "valid": True,
            "lease_id": "LEASE-WRITE",
            "lease_class": "DIGITAL_WRITE",
        },
    )
    assert receipt["state"] == "verified"
    assert receipt["exact_readback"] is True
    assert receipt["source_sha256"] == receipt["received_sha256"]
    assert receipt["authority_transfer"] is False

    reused = execute_local_transfer(
        envelope,
        target_root=target_root,
        allowed_source_roots=[source_root],
        allowed_target_roots=[target_root],
        lease_validation={
            "valid": True,
            "lease_id": "LEASE-WRITE",
            "lease_class": "DIGITAL_WRITE",
        },
    )
    assert reused["reused_existing_payload"] is True


def test_transfer_rejects_source_outside_allowlist(tmp_path: Path) -> None:
    source = tmp_path / "outside.txt"
    source.write_text("outside", encoding="utf-8")
    approved_source = tmp_path / "approved"
    target_root = tmp_path / "target"
    approved_source.mkdir()
    target_root.mkdir()
    envelope = build_transfer_envelope(
        source,
        source_node_id="node-a",
        target_node_id="node-b",
        source_root_id="source",
        target_root_id="target",
    )
    with pytest.raises(NodeExchangeError, match="outside approved roots"):
        execute_local_transfer(
            envelope,
            target_root=target_root,
            allowed_source_roots=[approved_source],
            allowed_target_roots=[target_root],
            lease_validation={
                "valid": True,
                "lease_id": "LEASE-WRITE",
                "lease_class": "DIGITAL_WRITE",
            },
        )


def test_transfer_requires_digital_write_class(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    source = source_root / "payload.txt"
    source.write_text("lease boundary", encoding="utf-8")
    envelope = build_transfer_envelope(
        source,
        source_node_id="node-a",
        target_node_id="node-a",
        source_root_id="source",
        target_root_id="target",
    )
    with pytest.raises(NodeExchangeError, match="does not permit digital transfer"):
        execute_local_transfer(
            envelope,
            target_root=target_root,
            allowed_source_roots=[source_root],
            allowed_target_roots=[target_root],
            lease_validation={
                "valid": True,
                "lease_id": "LEASE-COMPUTE",
                "lease_class": "COMPUTE_ONLY",
            },
        )


def test_compute_uses_verified_inputs_and_matching_lease() -> None:
    transfer_receipt = {
        "transfer_id": "NXFER-1",
        "state": "verified",
        "source_sha256": "a" * 64,
        "received_sha256": "a" * 64,
        "size_bytes": 10,
        "exact_readback": True,
    }
    request = build_compute_request(
        "Check the transferred payload and return a bounded result.",
        task_id="T1",
        run_id="R1",
        target_node_id="bouwerbase",
        capability_id="cognigrex-supervised-workflow",
        lease_ref="LEASE-1",
        input_receipts=[transfer_receipt],
    )

    calls: list[dict[str, object]] = []
    def fake_runner(instruction: str, **kwargs):
        calls.append({"instruction": instruction, **kwargs})
        return {
            "status": "complete",
            "complete_workflow": True,
            "workflow_id": "wf-1",
            "receipt_path": "receipt.json",
        }

    receipt = execute_local_compute(
        request,
        local_node_id="bouwerbase",
        lease_validation={
            "valid": True,
            "lease_id": "LEASE-1",
            "lease_class": "COMPUTE_ONLY",
        },
        runner=fake_runner,
    )
    assert receipt["status"] == "complete"
    assert receipt["authority_transfer"] is False
    assert receipt["raw_instruction_persisted_in_receipt"] is False
    assert calls and calls[0]["allow_heavy"] is False

    with pytest.raises(NodeExchangeError, match="lease_ref"):
        execute_local_compute(
            request,
            local_node_id="bouwerbase",
            lease_validation={
                "valid": True,
                "lease_id": "LEASE-OTHER",
                "lease_class": "COMPUTE_ONLY",
            },
            runner=fake_runner,
        )
def test_compute_rejects_unverified_transfer_input() -> None:
    request = build_compute_request(
        "Do bounded compute.",
        task_id="T2",
        run_id="R2",
        target_node_id="bouwerbase",
        capability_id="cognigrex-supervised-workflow",
        lease_ref="LEASE-2",
        input_receipts=[
            {
                "transfer_id": "NXFER-2",
                "state": "staged",
                "source_sha256": "b" * 64,
                "received_sha256": None,
                "size_bytes": 4,
                "exact_readback": False,
            }
        ],
    )
    with pytest.raises(NodeExchangeError, match="verified target readback"):
        execute_local_compute(
            request,
            local_node_id="bouwerbase",
            lease_validation={
                "valid": True,
                "lease_id": "LEASE-2",
                "lease_class": "COMPUTE_ONLY",
            },
            runner=lambda *_args, **_kwargs: {},
        )


def test_status_does_not_treat_carrier_as_peer_compute() -> None:
    status = build_exchange_status(
        local_node_id="bouwerbase",
        local_compute_ready=True,
        verified_carriers=["E-volume"],
        peer_nodes=[],
    )
    assert status["compute"]["local_ready"] is True
    assert status["transport"]["verified_carriers"] == ["E-volume"]
    assert status["transport"]["peer_transport_verified"] is False
    assert status["compute"]["peer_compute_verified"] is False
