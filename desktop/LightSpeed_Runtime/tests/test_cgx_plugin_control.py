from __future__ import annotations

import json
from pathlib import Path
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.cgx_plugin_control import (
    CGXInterfaceError,
    Intent,
    build_context_envelope,
    current_recovery,
    decide_minimum_sufficient_work,
    normalize_selector_name,
    resolve_selector,
)


def _domains() -> dict:
    return {
        "domains": {
            "romer": {"file": "Romer.cgx", "principal_agent": "Neo"},
            "eco": {"file": "Eco.cgx", "principal_agent": "Athene"},
            "emassc": {"file": "EMASSC.cgx", "principal_agent": "Achilles"},
        },
        "generation_policy": {
            "current_recovery_state": "S92",
            "current_recovery_sha256": "a" * 64,
            "current_recovery_content_root": "content",
            "current_recovery_dbr_root": "dbr",
            "current_recovery_topology": "topology",
            "recovery_promotion_evidence": {"canonical_verifier": "PASS"},
        },
    }


def _registry() -> dict:
    return {
        "selectors": {
            "neo": {
                "kind": "agent",
                "agent": "Neo",
                "default_domain": "romer",
            },
            "romer-grex": {
                "kind": "domain",
                "domain": "romer",
                "principal_agent": "Neo",
            },
            "cognigrex": {
                "kind": "system",
                "system": "Cognigrex.cgx",
            },
            "lightspeed": {
                "kind": "system",
                "system": "LS.cgx",
                "parent_domain": "emassc",
            },
        }
    }


def test_selector_normalisation_and_domain_resolution():
    assert normalize_selector_name("@Römer-Grex") == "romer-grex"
    resolved = resolve_selector("@Römer-Grex", registry=_registry(), domains=_domains())
    assert resolved["domain"] == "romer"
    assert resolved["principal_agent"] == "Neo"


def test_current_recovery_requires_verifier_pass():
    assert current_recovery(_domains())["state_id"] == "S92"
    bad = _domains()
    bad["generation_policy"]["recovery_promotion_evidence"]["canonical_verifier"] = "FAIL"
    try:
        current_recovery(bad)
    except CGXInterfaceError:
        pass
    else:
        raise AssertionError("expected fail-closed recovery resolution")


def test_exact_existing_result_is_reused():
    intent = Intent("test", "Mark V", ("geometry=v3",), proof_standard="secondary")
    decision = decide_minimum_sufficient_work(
        intent,
        [
            {
                "receipt_id": "R1",
                "status": "PASS",
                "current": True,
                "subject": "Mark V",
                "operation": "test",
                "constraints": ["geometry=v3", "temperature=nominal"],
                "proof_standard": "secondary",
            }
        ],
    )
    assert decision.strategy == "reuse_existing"
    assert decision.reused_receipts == ("R1",)


def test_compatible_prior_results_can_reconcile_only_when_explicitly_authorized():
    intent = Intent("estimate", "load")
    decision = decide_minimum_sufficient_work(
        intent,
        [
            {
                "receipt_id": "A",
                "status": "PASS",
                "subject": "load",
                "compatibility_group": "same-model",
                "reconciliation_authorized": True,
                "derivation_rule": "linear interpolation within validated range",
            },
            {
                "receipt_id": "B",
                "status": "PASS",
                "subject": "load",
                "compatibility_group": "same-model",
                "reconciliation_authorized": True,
                "derivation_rule": "linear interpolation within validated range",
            },
        ],
    )
    assert decision.strategy == "reconcile_existing"
    assert set(decision.reused_receipts) == {"A", "B"}


def test_missing_discriminant_is_preferred_to_new_mass_sweep():
    intent = Intent("test", "RFS oscillator")
    decision = decide_minimum_sufficient_work(
        intent,
        [
            {
                "receipt_id": "old",
                "status": "PASS",
                "subject": "RFS oscillator",
                "unresolved_discriminants": ["coil-gap-at-80C"],
            }
        ],
    )
    assert decision.strategy == "execute_missing_only"
    assert decision.unresolved_discriminants == ("coil-gap-at-80C",)


def test_context_envelope_preserves_existing_authority_and_local_first_policy():
    envelope = build_context_envelope(
        "Neo",
        {
            "operation": "analyse",
            "subject": "Mark V",
            "constraints": ["current geometry"],
            "requested_outputs": ["receipt"],
        },
        registry=_registry(),
        domains=_domains(),
    )
    assert envelope["schema_version"] == "cgx-context-envelope-v1"
    assert envelope["selector"]["agent"] == "Neo"
    assert envelope["recovery"]["state_id"] == "S92"
    assert envelope["authority"]["canonical_release_gate"] == "Achilles"
    assert envelope["work_policy"]["reasoning_route"] == "local_first"
    assert envelope["work_policy"]["strategy"] == "bounded_new_execution"


def test_capability_shortcalls_resolve_real_runtime_and_explicit_gaps():
    from lightspeed_runtime.cgx_capability_registry import resolve_shortcall

    sweep = resolve_shortcall("Raphael", "/sweep")
    assert sweep["route_id"] == "science.rfs_emff_sweep"
    assert sweep["route"]["state"] == "available"
    assert sweep["route"]["handler"].endswith(":execute_sweep")

    habitat = resolve_shortcall("Eco-Grex", "habitat")
    assert habitat["route_id"] == "eco.assess"
    assert habitat["route"]["state"] == "assisted"


def test_all_nine_selectors_have_extension_and_capability_shortcalls():
    from lightspeed_runtime.cgx_capability_registry import (
        list_shortcalls,
        load_selector_shortcalls,
    )

    selectors = load_selector_shortcalls()["selectors"]
    assert len(selectors) == 9
    for selector in selectors:
        calls = list_shortcalls(selector)
        assert calls["extend"] == "extensions.tool"
        assert calls["capabilities"] == "interface.capabilities"
