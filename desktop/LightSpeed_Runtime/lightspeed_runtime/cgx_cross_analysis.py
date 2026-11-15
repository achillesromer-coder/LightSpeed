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


__all__ = ["CGXCrossAnalysisError", "build_cross_analysis_plan",
           "source_hybridisation_candidates", "mandelbrot_grid_candidate",
           "fractal_grid_review_receipt"]


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



def mandelbrot_grid_candidate(width: int, height: int, zoom: float,
                             max_iter: int) -> dict[str, Any]:
    """Bounded shared Raphael/LightSpeed numerical primitive, review-stage only.

    Preserves the legacy pre-update escape check, including zero for no escape
    observed within the iteration window. This is not a membership proof,
    physical simulation, geometric catalogue admission, or native CGX mint.
    """
    if (type(width) is not int or type(height) is not int or
            type(max_iter) is not int or not 1 <= width <= 128 or
            not 1 <= height <= 128 or not 1 <= max_iter <= 256 or
            width * height * max_iter > 1_000_000):
        raise CGXCrossAnalysisError("invalid grid or iteration budget")
    if type(zoom) not in (int, float) or not 1e-6 <= zoom <= 1e6:
        raise CGXCrossAnalysisError("invalid zoom")
    import numpy as np
    xs = np.linspace(-2.0, 2.0, width) / zoom
    ys = np.linspace(-2.0, 2.0, height) / zoom
    grid = []
    for x in xs:
        row = []
        for y in ys:
            state = 0j
            c = complex(x, y)
            escape = 0
            for step in range(max_iter):
                if abs(state) > 2.0:
                    escape = step
                    break
                state = state * state + c
            row.append(escape)
        grid.append(row)
    return {
        "schema": "CGX-RAPHAEL-ESCAPE-GRID-REVIEW/0.1",
        "basis": "dimensionless_complex_plane",
        "axes": ["real", "imaginary"],
        "parameters": {"width": width, "height": height, "zoom": zoom,
                       "max_iter": max_iter},
        "zero_semantics": "escape_not_observed_before_iteration_limit",
        "grid": grid,
        "native_admitted": False,
        "physical_claim": False,
    }


def fractal_grid_review_receipt(width: int, height: int, zoom: float,
                                max_iter: int, *, include_grid: bool = False) -> dict[str, Any]:
    """Shared numerical review route: compact descriptor plus optional payload.

    The checksum is not an Object_ID, DBR, stored blob or execution authority.
    Compact output still computes the grid locally; no compression or remote
    hydration performance is implied.
    """
    import hashlib
    import json
    if type(include_grid) is not bool:
        raise CGXCrossAnalysisError("invalid payload selection")
    result = mandelbrot_grid_candidate(width, height, zoom, max_iter)
    import numpy as np
    grid = result.pop("grid")
    result["parameters"]["zoom"] = float(zoom)
    payload = json.dumps(grid, separators=(",", ":"), allow_nan=False).encode("ascii")
    result.update({
        "schema": "CGX-FRACTAL-GRID-REVIEW-RECEIPT/0.1",
        "route_id": "science.fractal_grid",
        "algorithm": "raphael-legacy-pre-update-escape/1",
        "numpy_version": np.__version__,
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "payload_bytes": len(payload),
        "point_count": width * height,
        "iteration_budget": width * height * max_iter,
        "payload_persisted": False,
        "native_admitted": False,
        "authority_transfer": False,
    })
    receipt_bytes = json.dumps(result, sort_keys=True, separators=(",", ":"),
                               allow_nan=False).encode("ascii")
    result["review_sha256"] = hashlib.sha256(receipt_bytes).hexdigest()
    result["payload_included"] = include_grid
    if include_grid:
        result["grid"] = grid
    return result



def pack_nested_review_payload(raw: bytes, *, chunk_bytes: int = 1024) -> tuple[str, dict[str, bytes]]:
    """Ternary, content-addressed review DAG over arbitrary bytes.

    Zero is an address digit here, not a minted T173 facet. Nodes are
    deterministic transport metadata, not qualified physical geometry.
    """
    import hashlib
    import json
    if type(raw) is not bytes or len(raw) > 5 * 1024 * 1024:
        raise CGXCrossAnalysisError("invalid payload or size")
    if type(chunk_bytes) is not int or not 64 <= chunk_bytes <= 4096:
        raise CGXCrossAnalysisError("invalid chunk size")
    objects = {}
    def store(value):
        key = hashlib.sha256(value).hexdigest()
        objects[key] = value
        return key
    def node(value):
        return store(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii"))
    chunks = [raw[i:i+chunk_bytes] for i in range(0,len(raw),chunk_bytes)] or [b""]
    roots = [node({"kind":"leaf","blob":store(part)}) for part in chunks]
    while len(roots)>1:
        roots = [node({"kind":"branch","children":roots[i:i+3]}) for i in range(0,len(roots),3)]
    return roots[0], objects


def hydrate_nested_review_payload(root: str, fetch, prefix: str = "", *,
                                  allowed_prefixes: tuple[str, ...], max_bytes: int) -> tuple[bytes, dict[str, int]]:
    """Resolve a subtree by verified hash without fetching unrelated branches.

    The root and allowed prefixes must come from the caller's trusted scope;
    this function does not authenticate them. Budget covers fetched node/blob bytes.
    """
    import hashlib
    import json
    import re
    def valid_key(k):
        return isinstance(k,str) and re.fullmatch(r"[0-9a-f]{64}",k) is not None
    def valid_path(p):
        return isinstance(p,str) and len(p)<=16 and all(c in "012" for c in p)
    if not valid_key(root) or not valid_path(prefix):
        raise CGXCrossAnalysisError("invalid root or ternary address")
    if (not isinstance(allowed_prefixes,tuple) or not all(valid_path(p) for p in allowed_prefixes)
            or not any(prefix.startswith(p) for p in allowed_prefixes)):
        raise PermissionError("subtree scope denied")
    if type(max_bytes) is not int or not 1<=max_bytes<=32*1024*1024:
        raise CGXCrossAnalysisError("invalid fetch budget")
    cache = {}
    spent = 0
    visits = 0
    def read(key):
        nonlocal spent
        if not valid_key(key):
            raise CGXCrossAnalysisError("invalid child hash")
        if key not in cache:
            raw = fetch(key)
            if type(raw) is not bytes or len(raw)>max_bytes-spent:
                raise CGXCrossAnalysisError("fetch budget or payload type")
            if hashlib.sha256(raw).hexdigest()!=key:
                raise CGXCrossAnalysisError("object hash mismatch")
            spent += len(raw)
            cache[key] = raw
        return cache[key]
    def get_node(key):
        raw=read(key)
        if len(raw)>512:
            raise CGXCrossAnalysisError("invalid node size")
        try:
            n=json.loads(raw)
        except (ValueError,UnicodeError) as exc:
            raise CGXCrossAnalysisError("invalid node") from exc
        if not isinstance(n,dict):
            raise CGXCrossAnalysisError("invalid node")
        if set(n)=={"kind","blob"} and n["kind"]=="leaf" and valid_key(n["blob"]):
            return n
        if (set(n)=={"kind","children"} and n["kind"]=="branch" and
                isinstance(n["children"],list) and 1<=len(n["children"])<=3 and
                all(valid_key(k) for k in n["children"])):
            return n
        raise CGXCrossAnalysisError("invalid node shape")
    key=root
    for digit in prefix:
        n=get_node(key); i=int(digit)
        if n["kind"]!="branch" or i>=len(n["children"]):
            raise CGXCrossAnalysisError("address not present")
        key=n["children"][i]
    output=bytearray()
    def walk(k,depth):
        nonlocal visits
        visits+=1
        if depth>16 or visits>200000:
            raise CGXCrossAnalysisError("expansion limit")
        n=get_node(k)
        if n["kind"]=="leaf":
            raw=read(n["blob"])
            if len(raw)>4096 or len(output)+len(raw)>5*1024*1024:
                raise CGXCrossAnalysisError("expanded payload limit")
            output.extend(raw)
        else:
            for child in n["children"]:
                walk(child,depth+1)
    walk(key,len(prefix))
    return bytes(output), {"fetched_bytes":spent,"fetched_objects":len(cache),
                           "expanded_bytes":len(output)}
