import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "cgx" / "domain_templates"


def test_mobile_node_binding_contract_is_single_root_and_bounded():
    contract = json.loads((TEMPLATES / "mobile_node_binding_contract.json").read_text(encoding="utf-8"))
    assert contract["schema"] == "CGX-MOBILE-NODE-BINDING/0.1"
    assert contract["entrypoint"]["semantic_root"] == "cgx://cgx.cgx"
    assert contract["entrypoint"]["surface"] == "mobile"
    assert contract["entrypoint"]["protocol_chain"] == [
        "CGX-MOBILE-BOOTSTRAP/0.1",
        "CGX-DEVICE-HANDSHAKE/0.1",
        "CGX-NODE-EXCHANGE-CONTRACT/0.1",
    ]
    assert contract["capability_policy"]["default"].startswith("deny")
    assert contract["transport"]["content_addressed_transfer"] is True
    assert contract["transport"]["receiver_hash_readback_required"] is True
    assert contract["transport"]["arbitrary_shell_capability"] is False
    assert "no-second-runtime" in contract["invariants"]
    assert "no-authority-by-device" in contract["invariants"]
    assert "no-secrets-in-carrier" in contract["invariants"]


def test_mobile_binding_is_registered_as_shared_parent_contract():
    domains = json.loads((TEMPLATES / "domains.json").read_text(encoding="utf-8"))
    assert "mobile-node-binding" in domains["parent_filespace"]["shared_kernel"]
    assert domains["shared_contracts"]["mobile_node_binding"] == "mobile_node_binding_contract.json"
