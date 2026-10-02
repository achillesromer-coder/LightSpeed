from __future__ import annotations

"""Bounded cross-analysis planning facade for Cognigrex/LightSpeed.

This module composes existing context, query, capability, minimum-work and
preflight logic. It plans work; it does not silently execute tests, sweeps,
external writes, or canonical promotion.
"""

from typing import Any, Iterable

from lightspeed_runtime.cgx_capability_registry import capability_summary
from lightspeed_runtime.cgx_plugin_control import build_context_envelope
from lightspeed_runtime.cgx_preflight import build_consequence_preflight
from lightspeed_runtime.cgx_query_planner import compile_query_plan


class CGXCrossAnalysisError(ValueError):
    """Raised when a cross-analysis request is malformed."""


def _default_intent(question: str) -> dict[str, Any]:
    return {
        "operation": "cross-analyse",
        "subject": question,
        "constraints": [],
        "requested_outputs": ["cross-analysis-plan", "receipt"],
    }


def _domain_from_context(envelope: dict[str, Any], override: str | None) -> str | None:
    if override:
        return str(override).strip().lower()
    selector = envelope.get("selector") or {}
    domain = selector.get("domain")
    if domain:
        return str(domain)
    if selector.get("name") == "lightspeed":
        return "lightspeed"
    return None


def _recommended_routes(strategy: str) -> list[dict[str, Any]]:
    if strategy == "reuse_existing":
        return [
            {"route_id": "receipts.list", "reason": "retrieve the covering current receipt"},
        ]
    if strategy == "reconcile_existing":
        return [
            {"route_id": "receipts.open", "reason": "read declared compatible receipts"},
            {"route_id": "cgx.minimum_work", "reason": "verify derivation remains admissible"},
        ]
    if strategy == "execute_missing_only":
        return [
            {"route_id": "science.query", "reason": "resolve existing structured evidence first"},
            {"route_id": "tests.plan", "reason": "compile only unresolved discriminants"},
            {"route_id": "local.supervise", "reason": "execute bounded local work only when needed"},
        ]
    if strategy == "bounded_new_execution":
        return [
            {"route_id": "science.query", "reason": "query current evidence before new computation"},
            {"route_id": "tests.plan", "reason": "build the smallest dependency-safe test cascade"},
            {"route_id": "local.supervise", "reason": "route bounded local reasoning/compute"},
        ]
    return []


def build_cross_analysis_plan(
    selector: str,
    question: str,
    *,
    intent_payload: dict[str, Any] | None = None,
    evidence: Iterable[dict[str, Any]] = (),
    facet_schema: dict[str, dict] | None = None,
    umbrella_terms: list[str] | dict[str, list[str]] | None = None,
    structured_constraints: dict[str, list[str] | str] | None = None,
    structured_payload: dict[str, Any] | None = None,
    domain_override: str | None = None,
    execution_depth: str = "inspect",
    reasoning_depth: str = "standard",
    cascade_class: str = "C0",
    tags: Iterable[str] = (),
    assurance_assessment: dict[str, Any] | None = None,
    custodial_assessment: dict[str, Any] | None = None,
    allow_heavy: bool = False,
) -> dict[str, Any]:
    question = str(question or "").strip()
    if not question:
        raise CGXCrossAnalysisError("question must be non-empty")

    envelope = build_context_envelope(
        selector,
        intent_payload or _default_intent(question),
        evidence=evidence,
        reasoning_route="local_first",
        return_mode="receipt",
        allow_heavy=allow_heavy,
    )
    query_plan = compile_query_plan(
        question,
        facet_schema=facet_schema,
        umbrella_terms=umbrella_terms,
        structured_constraints=structured_constraints,
        structured_payload=structured_payload,
    )
    capabilities = capability_summary(selector)
    domain = _domain_from_context(envelope, domain_override)
    if domain is None:
        preflight: dict[str, Any] = {
            "state": "domain_required",
            "reason": (
                "Selector has no single default semantic domain. Supply domain_override "
                "before consequential simulation/build/publish work."
            ),
        }
    else:
        preflight = build_consequence_preflight(
            domain,
            execution_depth,
            reasoning_depth=reasoning_depth,
            cascade_class=cascade_class,
            tags=tags,
            assurance_assessment=assurance_assessment,
            custodial_assessment=custodial_assessment,
        )

    strategy = str((envelope.get("work_policy") or {}).get("strategy") or "blocked")
    return {
        "schema": "CGX-CROSS-ANALYSIS-PLAN/0.1",
        "selector": envelope.get("selector"),
        "question": question,
        "context_envelope": envelope,
        "query_plan": query_plan,
        "capability_summary": capabilities,
        "preflight": preflight,
        "minimum_work_strategy": strategy,
        "recommended_routes": _recommended_routes(strategy),
        "execution_policy": {
            "automatic_execution": False,
            "allow_heavy": bool(allow_heavy),
            "reuse_before_execution": True,
            "missing_only_before_new_sweep": True,
            "external_writes": False,
            "canonical_mutation": False,
        },
        "authority_limit": (
            "This facade plans cross-analysis and identifies bounded routes. It does not "
            "promote runtime/model output to semantic truth or grant execution/release authority."
        ),
    }


__all__ = ["CGXCrossAnalysisError", "build_cross_analysis_plan"]
