from __future__ import annotations

"""Bounded cross-analysis planning facade for Cognigrex/LightSpeed.

This module composes existing context, query, capability, minimum-work and
preflight logic. It plans work; it does not silently execute tests, sweeps,
external writes, or canonical promotion.
"""

from typing import Any, Iterable

from lightspeed_runtime.cgx_capability_registry import capability_summary
from lightspeed_runtime.cgx_plugin_control import build_context_envelope
from lightspeed_runtime.cgx_object_context import CGXObjectContextError, resolve_object_context
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

    object_context = None
    object_query = str((intent_payload or {}).get("subject") or "").strip()
    if object_query:
        try:
            object_context = resolve_object_context(object_query, domain=domain)
        except CGXObjectContextError:
            object_context = None

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
        "object_context": object_context,
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


def source_hybridisation_candidates(sources: dict[str, bytes]) -> dict[str, Any]:
    """Bounded static reuse discovery; never imports or executes source modules.

    Byte identity permits payload storage reuse only. Function syntax is a
    candidate relation, not behavioural equivalence, scientific validation,
    rights clearance, or permission to replace a role-specific implementation.
    """
    import ast
    import hashlib
    from collections import defaultdict

    if not isinstance(sources, dict) or not sources or len(sources) > 256:
        raise CGXCrossAnalysisError("invalid source collection")
    if any(not isinstance(k, str) or not k or not isinstance(v, bytes)
           for k, v in sources.items()):
        raise CGXCrossAnalysisError("invalid source identity or bytes")
    if sum(map(len, sources.values())) > 5 * 1024 * 1024:
        raise CGXCrossAnalysisError("source budget exceeded")
    payloads = defaultdict(list)
    definitions = defaultdict(lambda: defaultdict(list))
    unresolved = []
    for source_id, raw in sorted(sources.items()):
        digest = hashlib.sha256(raw).hexdigest()
        payloads[digest].append(source_id)
        try:
            tree = ast.parse(raw)
        except (SyntaxError, ValueError, RecursionError):
            unresolved.append(source_id)
            continue
        for position, node in enumerate(tree.body):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fingerprint = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
            definitions[node.name][fingerprint].append(
                {"source_id": source_id, "source_sha256": digest, "body_position": position}
            )
    return {
        "schema": "CGX-SOURCE-HYBRIDISATION-REVIEW/0.1",
        "source_count": len(sources),
        "distinct_payload_count": len(payloads),
        "exact_payload_groups": [
            {"sha256": h, "occurrences": ids}
            for h, ids in sorted(payloads.items()) if len(ids) > 1
        ],
        "function_candidates": [
            {"name": name, "syntax_variants": [
                {"syntax_sha256": h, "occurrences": refs}
                for h, refs in sorted(variants.items())],
             "requires": ["dependency_binding", "units_and_frame_if_applicable",
                          "behavioural_tests", "rights_and_role_scope"]}
            for name, variants in sorted(definitions.items())
            if sum(map(len, variants.values())) > 1
        ],
        "unparsed_sources": unresolved,
        "semantic_equivalence_proven": False,
        "native_admitted": False,
        "execution_performed": False,
    }
