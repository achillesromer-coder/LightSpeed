from __future__ import annotations

import hashlib
import re
from typing import Any


class CGXQueryPlanError(RuntimeError):
    """Raised when a facet-first query plan cannot be built safely."""


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def _phrase_present(text: str, phrase: str) -> bool:
    phrase = _norm(phrase)
    if not phrase:
        return False
    return f" {phrase} " in f" {text} "


def _remove_phrase(text: str, phrase: str) -> str:
    phrase = _norm(phrase)
    if not phrase:
        return text
    return re.sub(rf"(?<!\w){re.escape(phrase)}(?!\w)", " ", text).strip()


def _canonical_alias_map(values: Any) -> dict[str, list[str]]:
    if isinstance(values, list):
        return {str(value): [str(value)] for value in values if str(value).strip()}
    if not isinstance(values, dict):
        raise CGXQueryPlanError("facet values must be a list or canonical->aliases mapping")
    result: dict[str, list[str]] = {}
    for canonical, aliases in values.items():
        if not isinstance(canonical, str) or not canonical.strip():
            raise CGXQueryPlanError("facet canonical value is invalid")
        if isinstance(aliases, str):
            aliases = [aliases]
        if not isinstance(aliases, list):
            raise CGXQueryPlanError(f"aliases for {canonical} must be a list")
        result[canonical] = [canonical, *[str(alias) for alias in aliases if str(alias).strip()]]
    return result


def _umbrella_alias_map(umbrella_terms: Any) -> dict[str, list[str]]:
    if isinstance(umbrella_terms, list):
        return {str(value): [str(value)] for value in umbrella_terms if str(value).strip()}
    if isinstance(umbrella_terms, dict):
        return _canonical_alias_map(umbrella_terms)
    raise CGXQueryPlanError("umbrella_terms must be a list or canonical->aliases mapping")


def compile_query_plan(
    raw_query: str,
    *,
    facet_schema: dict[str, dict] | None = None,
    umbrella_terms: list[str] | dict[str, list[str]] | None = None,
    capability_manifest: dict | None = None,
    structured_constraints: dict[str, list[str] | str] | None = None,
    structured_payload: dict | None = None,
) -> dict:
    """Compile natural-language intent into a minimal query + structured controls.

    The planner is deliberately deterministic. An LLM may propose facet candidates
    or umbrella vocabularies, but this function only applies values that are
    present in the supplied schema or explicit structured constraints.
    """

    if not isinstance(raw_query, str) or not raw_query.strip():
        raise CGXQueryPlanError("raw_query must be non-empty text")

    raw_query = raw_query.strip()
    normalized = _norm(raw_query)
    residual = normalized
    applied_facets: dict[str, list[str]] = {}
    controls_used: list[dict[str, str]] = []
    matched_phrases: list[str] = []
    schema = facet_schema or {}

    for facet_name, config in schema.items():
        if not isinstance(config, dict):
            raise CGXQueryPlanError(f"facet {facet_name} must be an object")
        control = str(config.get("control") or "checkbox")
        aliases = _canonical_alias_map(config.get("values") or [])
        chosen: list[str] = []
        for canonical, phrases in aliases.items():
            matched = sorted(
                {phrase for phrase in phrases if _phrase_present(normalized, phrase)},
                key=lambda item: len(_norm(item)),
                reverse=True,
            )
            if matched:
                chosen.append(canonical)
                matched_phrases.extend(matched)
        if chosen:
            applied_facets[facet_name] = chosen
            for value in chosen:
                controls_used.append({"facet": facet_name, "value": value, "control": control})

    explicit = structured_constraints or {}
    for facet_name, requested in explicit.items():
        if facet_name not in schema:
            raise CGXQueryPlanError(f"structured constraint references unknown facet: {facet_name}")
        aliases = _canonical_alias_map(schema[facet_name].get("values") or [])
        values = [requested] if isinstance(requested, str) else list(requested)
        for value in values:
            if value not in aliases:
                raise CGXQueryPlanError(f"unknown value for {facet_name}: {value}")
            applied_facets.setdefault(facet_name, [])
            if value not in applied_facets[facet_name]:
                applied_facets[facet_name].append(value)
                controls_used.append(
                    {
                        "facet": facet_name,
                        "value": value,
                        "control": str(schema[facet_name].get("control") or "checkbox"),
                    }
                )

    umbrella_query = ""
    umbrella_matches: list[tuple[int, str, str]] = []
    if umbrella_terms:
        for canonical, phrases in _umbrella_alias_map(umbrella_terms).items():
            for phrase in phrases:
                if _phrase_present(normalized, phrase):
                    umbrella_matches.append((len(_norm(phrase)), canonical, phrase))
    if umbrella_matches:
        _, umbrella_query, umbrella_phrase = sorted(umbrella_matches, reverse=True)[0]
        matched_phrases.append(umbrella_phrase)

    for phrase in sorted(set(matched_phrases), key=lambda item: len(_norm(item)), reverse=True):
        residual = _remove_phrase(residual, phrase)
    residual = re.sub(r"\s+", " ", residual).strip()

    executable_query = umbrella_query or residual or raw_query
    unresolved_constraints = [residual] if umbrella_query and residual else []

    manifest = capability_manifest if isinstance(capability_manifest, dict) else {}
    capability_id = str(manifest.get("capability_id") or "unspecified")
    kind = str(manifest.get("kind") or "retrieval_search")
    designed = [str(item) for item in (manifest.get("designed_functions") or [])]
    accepted_inputs = [str(item) for item in (manifest.get("accepted_inputs") or [])]

    if kind in {"formal_solver", "simulation", "mpl", "gmat"}:
        packet = {
            "mode": "structured-tool",
            "query_context": executable_query,
            "facets": applied_facets,
            "structured_payload": dict(structured_payload or {}),
            "status": "ready" if structured_payload else "needs_structured_payload",
        }
    elif kind == "llm_semantic":
        packet = {
            "mode": "semantic",
            "umbrella_query": executable_query,
            "facets": applied_facets,
            "unresolved_constraints": unresolved_constraints,
            "structured_payload": dict(structured_payload or {}),
        }
    else:
        packet = {
            "mode": "retrieval",
            "query": executable_query,
            "facets": applied_facets,
            "controls": controls_used,
        }

    intent_hash = hashlib.sha256(raw_query.encode("utf-8")).hexdigest()
    return {
        "raw_query": raw_query,
        "intent_hash": intent_hash,
        "umbrella_query": executable_query,
        "applied_facets": applied_facets,
        "controls_used": controls_used,
        "residual_text": residual,
        "unresolved_constraints": unresolved_constraints,
        "capability_route": {
            "capability_id": capability_id,
            "kind": kind,
            "designed_functions": designed,
            "accepted_inputs": accepted_inputs,
        },
        "capability_packet": packet,
        "hydration_stage": 0,
        "sufficiency_state": "UNTESTED",
        "rehydration_triggers": [
            "zero_results",
            "result_set_too_broad_for_task",
            "required_constraint_unresolved",
            "tool_rejects_packet",
            "conflicting_evidence_requires_source_expansion",
            "requested_precision_exceeds_current_packet",
        ],
        "lineage": {
            "normalisation": "FFQP/0.1",
            "hydration": "PQH/0.1",
            "routing": "CNR/0.1",
            "raw_intent_preserved": True,
            "canonical_mutation": False,
        },
    }
