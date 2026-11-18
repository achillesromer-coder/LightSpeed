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


def write_nested_review_archive(archive, raw: bytes, *, chunk_bytes: int = 1024) -> str:
    """Place review objects in a caller-owned empty ZIP carrier, not a new store."""
    import zipfile
    if archive.namelist():
        raise CGXCrossAnalysisError("review carrier must be empty")
    root, objects = pack_nested_review_payload(raw, chunk_bytes=chunk_bytes)
    for key, data in sorted(objects.items()):
        info = zipfile.ZipInfo("review/objects/" + key)
        info.compress_type = zipfile.ZIP_STORED
        archive.writestr(info, data)
    return root


def hydrate_nested_review_archive(archive, root: str, prefix: str = "", *,
                                  allowed_prefixes: tuple[str, ...], max_bytes: int):
    """Read selected verified objects from a persisted review carrier.

    No archive extraction, native admission, or independent access authentication.
    The expected root and access scope are supplied by the trusted caller.
    """
    import re
    infos = archive.infolist()
    if not infos or len(infos) > 200000:
        raise CGXCrossAnalysisError("invalid review carrier size")
    index = {}
    for info in infos:
        name = info.filename
        if (not re.fullmatch(r"review/objects/[0-9a-f]{64}", name)
                or name in index or not 0 <= info.file_size <= 4096
                or info.flag_bits & 1):
            raise CGXCrossAnalysisError("invalid or duplicate review carrier member")
        index[name] = info
    def fetch(key):
        info = index.get("review/objects/" + key)
        if info is None:
            raise CGXCrossAnalysisError("missing review object")
        return archive.read(info)
    return hydrate_nested_review_payload(root, fetch, prefix,
                                         allowed_prefixes=allowed_prefixes,
                                         max_bytes=max_bytes)



def pack_achilles_profile_review(source: bytes):
    """Review-only semantic projection of the existing Achilles profile.

    Retain the original byte digest. Section roots index canonical JSON values,
    not original formatting, model weights, native Object_IDs or authority.
    Uses the existing ternary payload graph rather than a new persistent store.
    """
    import hashlib
    import json
    if type(source) is not bytes or not 1 <= len(source) <= 1024 * 1024:
        raise CGXCrossAnalysisError("invalid profile source")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise CGXCrossAnalysisError("duplicate JSON key")
            result[key] = value
        return result
    def canonical(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False).encode("ascii")
    try:
        d = json.loads(source, object_pairs_hook=unique)
        if (not isinstance(d, dict) or len(d) > 64 or
                d.get("identity", {}).get("agent") != "Achilles" or
                d["identity"].get("canonical_semantic_parent") != "cgx:root:cognigrex" or
                d.get("lifecycle", {}).get("native_dbr_admission") is not False or
                d["lifecycle"].get("release_authorized") is not False or
                not isinstance(d.get("dynamic_system_research"), dict)):
            raise CGXCrossAnalysisError("profile identity or review boundary mismatch")
        canonical_profile = canonical(d)
        objects = {}
        sections = {}
        for key, value in sorted(d.items()):
            raw = canonical(value)
            root, parts = pack_nested_review_payload(raw)
            objects.update(parts)
            sections[key] = {"root": root, "sha256": hashlib.sha256(raw).hexdigest(),
                             "bytes": len(raw)}
        descriptor = {
            "schema": "CGX-ACHILLES-SEMANTIC-REVIEW/0.1",
            "agent": "Achilles", "parent": "cgx:root:cognigrex",
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "canonical_profile_sha256": hashlib.sha256(canonical_profile).hexdigest(),
            "sections": sections, "native_admitted": False,
            "model_weights_included": False, "authority_transfer": False,
        }
        return descriptor, hashlib.sha256(canonical(descriptor)).hexdigest(), objects
    except (TypeError, ValueError, AttributeError, KeyError, RecursionError) as exc:
        if isinstance(exc, CGXCrossAnalysisError):
            raise
        raise CGXCrossAnalysisError("invalid Achilles profile") from exc


def hydrate_achilles_profile_section(descriptor, expected_sha256, section, fetch, *,
                                     allowed_sections, max_bytes):
    """Caller must authenticate the expected descriptor and section scope."""
    import hashlib
    import json
    try:
        raw = json.dumps(descriptor, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("ascii")
        if hashlib.sha256(raw).hexdigest() != expected_sha256:
            raise CGXCrossAnalysisError("descriptor hash mismatch")
        if (descriptor.get("schema") != "CGX-ACHILLES-SEMANTIC-REVIEW/0.1" or
                descriptor.get("agent") != "Achilles" or
                descriptor.get("parent") != "cgx:root:cognigrex" or
                descriptor.get("native_admitted") is not False or
                descriptor.get("authority_transfer") is not False or
                descriptor.get("model_weights_included") is not False):
            raise CGXCrossAnalysisError("invalid review descriptor")
        if not isinstance(allowed_sections, (tuple, frozenset)) or section not in allowed_sections:
            raise PermissionError("section scope denied")
        item = descriptor["sections"][section]
        payload, stats = hydrate_nested_review_payload(item["root"], fetch,
                                allowed_prefixes=("",), max_bytes=max_bytes)
        if len(payload) != item["bytes"] or hashlib.sha256(payload).hexdigest() != item["sha256"]:
            raise CGXCrossAnalysisError("section payload mismatch")
        return json.loads(payload), stats
    except (KeyError, TypeError, ValueError, AttributeError, RecursionError) as exc:
        if isinstance(exc, CGXCrossAnalysisError):
            raise
        raise CGXCrossAnalysisError("invalid section descriptor") from exc



def resolve_achilles_review_context(descriptor, expected_sha256, sections, fetch, *,
                                    allowed_sections, max_bytes):
    """Resolve a bounded, source-bound context with shared object reads.

    A receipt identifies verified input values, not a learned fact, a model
    result, permission, or native DBR. The caller authenticates the expected
    descriptor and the scope. No persistent store or execution is introduced.
    """
    import hashlib
    import json

    def canonical(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False).encode("ascii")

    if (type(max_bytes) is not int or not 1 <= max_bytes <= 32 * 1024 * 1024
            or not isinstance(sections, (tuple, list)) or not 1 <= len(sections) <= 64
            or not all(isinstance(k, str) and k for k in sections)
            or len(set(sections)) != len(sections)
            or not isinstance(allowed_sections, (tuple, frozenset))
            or not all(isinstance(k, str) and k for k in allowed_sections)):
        raise CGXCrossAnalysisError("invalid context selection or budget")
    if not set(sections).issubset(allowed_sections):
        raise PermissionError("context scope denied")
    try:
        if hashlib.sha256(canonical(descriptor)).hexdigest() != expected_sha256:
            raise CGXCrossAnalysisError("descriptor hash mismatch")
        if not all(k in descriptor["sections"] for k in sections):
            raise CGXCrossAnalysisError("unknown context section")
    except (TypeError, ValueError, KeyError, AttributeError, RecursionError) as exc:
        if isinstance(exc, CGXCrossAnalysisError):
            raise
        raise CGXCrossAnalysisError("invalid context descriptor") from exc

    cache = {}
    spent = 0
    references = 0

    def shared_fetch(key):
        nonlocal spent, references
        references += 1
        if key not in cache:
            raw = fetch(key)
            if type(raw) is not bytes or len(raw) > max_bytes - spent:
                raise CGXCrossAnalysisError("aggregate fetch budget exceeded")
            if hashlib.sha256(raw).hexdigest() != key:
                raise CGXCrossAnalysisError("context object hash mismatch")
            cache[key] = raw
            spent += len(raw)
        return cache[key]

    values = {}
    evidence = {}
    for name in sorted(sections):
        value, stats = hydrate_achilles_profile_section(
            descriptor, expected_sha256, name, shared_fetch,
            allowed_sections=allowed_sections, max_bytes=max_bytes)
        values[name] = value
        entry = descriptor["sections"][name]
        evidence[name] = {"root": entry["root"], "payload_sha256": entry["sha256"],
                          "payload_bytes": stats["expanded_bytes"]}
    value_hash = hashlib.sha256(canonical(values)).hexdigest()
    complete = set(values) == set(descriptor["sections"])
    if complete and value_hash != descriptor["canonical_profile_sha256"]:
        raise CGXCrossAnalysisError("complete semantic reconstruction mismatch")
    receipt = {
        "schema": "CGX-ACHILLES-REVIEW-CONTEXT/0.1",
        "descriptor_sha256": expected_sha256,
        "source_sha256": descriptor["source_sha256"],
        "sections": evidence, "context_sha256": value_hash,
        "complete_profile": complete, "evidence_class": "VERIFIED_REVIEW_INPUT",
        "native_admitted": False, "reasoning_evaluated": False,
        "authority_transfer": False,
    }
    receipt["review_sha256"] = hashlib.sha256(canonical(receipt)).hexdigest()
    return values, receipt, {"fetched_bytes": spent, "fetched_objects": len(cache),
                             "object_references": references,
                             "reused_reads": references - len(cache)}



def resolve_achilles_revision_context(descriptor, expected_sha256, sections, fetch, *,
                                     allowed_sections, max_bytes, prior_values,
                                     prior_receipt, expected_prior_review_sha256):
    """Reuse verified permitted semantic sections across profile revisions.

    Prior receipts and current descriptor identities must be authenticated by
    the caller. No permission, source authority or model learning is inherited.
    The existing aggregate budget includes both cached and externally read
    object bytes; external read savings are counted separately.
    """
    import hashlib
    import json

    def canonical(x):
        return json.dumps(x, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False).encode("ascii")

    def bounded_canonical(value):
        # Bound preprocessing separately from hydrated object accounting.
        cap = 8 * 1024 * 1024
        stack = [(value, 0)]
        seen = 0
        estimate = 0
        while stack:
            item, depth = stack.pop()
            seen += 1
            if depth > 64 or seen + len(stack) > 100000:
                raise CGXCrossAnalysisError("prior context shape budget")
            kind = type(item)
            if kind is str:
                estimate += 2 + 12 * len(item)
            elif kind is int:
                if item.bit_length() > 4096:
                    raise CGXCrossAnalysisError("prior context integer budget")
                estimate += 2 + item.bit_length()
            elif kind in (float, bool, type(None)):
                estimate += 32
            elif kind in (list, dict):
                count = len(item) * (2 if kind is dict else 1)
                if seen + len(stack) + count > 100000:
                    raise CGXCrossAnalysisError("prior context node budget")
                estimate += 2 + count
                if kind is dict:
                    for key, child in item.items():
                        if type(key) is not str:
                            raise CGXCrossAnalysisError("prior context key type")
                        stack.extend(((key, depth+1), (child, depth+1)))
                else:
                    stack.extend((child, depth+1) for child in item)
            else:
                raise CGXCrossAnalysisError("prior context JSON type")
            if estimate > cap:
                raise CGXCrossAnalysisError("prior context byte budget")
        raw = canonical(value)
        if len(raw) > cap:
            raise CGXCrossAnalysisError("prior context byte budget")
        return raw

    if (not isinstance(sections, (list, tuple)) or not 1 <= len(sections) <= 64
            or not all(isinstance(k, str) for k in sections)
            or len(set(sections)) != len(sections)
            or not isinstance(allowed_sections, (tuple, frozenset))
            or type(max_bytes) is not int or not 1 <= max_bytes <= 32 * 1024 * 1024):
        raise CGXCrossAnalysisError("invalid revision context")
    if not set(sections).issubset(allowed_sections):
        raise PermissionError("revision context scope denied")
    try:
        if hashlib.sha256(bounded_canonical(descriptor)).hexdigest() != expected_sha256:
            raise CGXCrossAnalysisError("descriptor hash mismatch")
        if not all(k in descriptor["sections"] for k in sections):
            raise CGXCrossAnalysisError("unknown revision section")
        bounded_canonical(prior_receipt)
        if type(prior_receipt) is not dict:
            raise CGXCrossAnalysisError("invalid prior receipt type")
        proof = dict(prior_receipt)
        claimed = proof.pop("review_sha256")
        if (claimed != expected_prior_review_sha256
                or hashlib.sha256(bounded_canonical(proof)).hexdigest() != claimed
                or proof.get("schema") != "CGX-ACHILLES-REVIEW-CONTEXT/0.1"
                or proof.get("native_admitted") is not False
                or proof.get("authority_transfer") is not False
                or proof.get("reasoning_evaluated") is not False
                or proof.get("evidence_class") != "VERIFIED_REVIEW_INPUT"
                or not isinstance(prior_values, dict)
                or set(prior_values) != set(proof["sections"])
                or hashlib.sha256(bounded_canonical(prior_values)).hexdigest() != proof["context_sha256"]):
            raise CGXCrossAnalysisError("prior context verification failed")

        cached = {}
        reused = []
        scratch_reserved = 0
        for name in sorted(sections):
            old = proof["sections"].get(name)
            new = descriptor["sections"][name]
            if old is None or (old["root"], old["payload_sha256"], old["payload_bytes"]) != (
                    new["root"], new["sha256"], new["bytes"]):
                continue
            raw = bounded_canonical(prior_values[name])
            if len(raw) != new["bytes"] or hashlib.sha256(raw).hexdigest() != new["sha256"]:
                raise CGXCrossAnalysisError("prior section payload mismatch")
            # Conservative encoded scratch estimate; no warm repack if over budget.
            leaves = max(1, (len(raw)+1023)//1024)
            estimate = len(raw) + 96 * leaves
            while leaves > 1:
                leaves = (leaves+2)//3
                estimate += 256 * leaves
            if estimate > max_bytes - scratch_reserved:
                continue
            scratch_reserved += estimate
            root, parts = pack_nested_review_payload(raw)
            if root != new["root"]:
                raise CGXCrossAnalysisError("prior section root mismatch")
            cached.update(parts)
            reused.append(name)
    except (TypeError, ValueError, KeyError, AttributeError, RecursionError) as exc:
        if isinstance(exc, CGXCrossAnalysisError):
            raise
        raise CGXCrossAnalysisError("invalid revision evidence") from exc

    external_bytes = external_objects = 0
    def revision_fetch(key):
        nonlocal external_bytes, external_objects
        if key in cached:
            return cached[key]
        raw = fetch(key)
        if type(raw) is not bytes:
            raise CGXCrossAnalysisError("invalid external object")
        external_bytes += len(raw)
        external_objects += 1
        return raw

    values, receipt, stats = resolve_achilles_review_context(
        descriptor, expected_sha256, sections, revision_fetch,
        allowed_sections=allowed_sections, max_bytes=max_bytes)
    transition = {
        "schema": "CGX-ACHILLES-REVIEW-REVISION/0.1",
        "prior_review_sha256": claimed,
        "current_review_sha256": receipt["review_sha256"],
        "reused_sections": reused,
        "resolved_sections": sorted(set(sections) - set(reused)),
        "native_admitted": False, "authority_transfer": False,
        "reasoning_evaluated": False,
    }
    transition["review_sha256"] = hashlib.sha256(canonical(transition)).hexdigest()
    return values, receipt, transition, dict(stats, external_bytes=external_bytes,
                                             external_objects=external_objects)



def resolve_review_occurrence(occurrence, expected_sha256, fetch, authorise, *,
                              prefix="", max_bytes):
    """Resolve exact occurrence scope; shared payload is not shared permission.

    Caller authenticates the expected hash and supplies current authorisation.
    Fetch receives occurrence ID and object hash. No global cache or new
    authority is created. Rechecks cannot undo a previous provider read.
    """
    import hashlib
    import json
    import re
    keys = {"occurrence_id","source_revision","root","scope_revision","allowed_prefixes"}
    if (type(occurrence) is not dict or set(occurrence) != keys or
            any(type(occurrence[k]) is not str or not 1 <= len(occurrence[k]) <= 256
                for k in ("occurrence_id","source_revision","scope_revision")) or
            type(occurrence["root"]) is not str or
            not re.fullmatch(r"[0-9a-f]{64}",occurrence["root"]) or
            type(occurrence["allowed_prefixes"]) is not list or
            not 1 <= len(occurrence["allowed_prefixes"]) <= 64 or
            any(type(p) is not str or len(p)>16 or any(c not in "012" for c in p)
                for p in occurrence["allowed_prefixes"])):
        raise CGXCrossAnalysisError("invalid occurrence")
    oid,revision,scope,root=(occurrence[k] for k in
        ("occurrence_id","source_revision","scope_revision","root"))
    prefixes=tuple(occurrence["allowed_prefixes"])
    snap=dict(occurrence_id=oid,source_revision=revision,scope_revision=scope,
              root=root,allowed_prefixes=list(prefixes))
    encoded=json.dumps(snap,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")
    if hashlib.sha256(encoded).hexdigest()!=expected_sha256:
        raise CGXCrossAnalysisError("occurrence hash mismatch")
    if type(prefix) is not str or not any(prefix.startswith(k) for k in prefixes):
        raise PermissionError("occurrence prefix denied")
    def check():
        if authorise(oid,revision,scope,prefix) is not True:
            raise PermissionError("occurrence permission denied or revoked")
    def scoped_fetch(key):
        check()
        result=fetch(oid,key)
        check()
        return result
    check()
    raw,stats=hydrate_nested_review_payload(root,scoped_fetch,prefix,
                                        allowed_prefixes=prefixes,max_bytes=max_bytes)
    check()
    return raw,dict(stats,occurrence_sha256=expected_sha256,
                    native_admitted=False,authority_transfer=False)



def resolve_provider_review_occurrence(occurrence, expected_sha256, provider_read, authorise, *,
                                       task_id, prefix="", max_bytes):
    """Bind each object read to its occurrence, source revision and task.

    Provider_read is an existing trusted adapter, not an arbitrary tool call.
    The caller must authenticate the provider and its current scope. An echoed
    envelope is not independent authentication or proof of atomic revocation.
    """
    import re
    if type(task_id) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}",task_id):
        raise CGXCrossAnalysisError("invalid occurrence task")
    if type(max_bytes) is not int or not 1<=max_bytes<=32*1024*1024:
        raise CGXCrossAnalysisError("invalid occurrence budget")
    if type(occurrence) is not dict:
        raise CGXCrossAnalysisError("invalid occurrence")
    # Snapshot the supplied identity; the existing resolver validates its hash.
    try:
        identity = {k:occurrence[k] for k in ("occurrence_id","source_revision","scope_revision")}
    except KeyError as exc:
        raise CGXCrossAnalysisError("missing occurrence identity") from exc
    spent=0
    def gate(oid,revision,scope,subtree):
        return authorise(task_id,oid,revision,scope,subtree) is True
    def fetch(oid,key):
        nonlocal spent
        if oid!=identity["occurrence_id"]:
            raise CGXCrossAnalysisError("provider occurrence mismatch")
        limit=min(4096,max_bytes-spent)
        if limit<=0:
            raise CGXCrossAnalysisError("provider read budget exhausted")
        request={**identity,"task_id":task_id,"prefix":prefix,"object_sha256":key,"max_bytes":limit}
        response=provider_read(dict(request))
        if type(response) is not dict or set(response)!=set(request)|{"payload"}:
            raise CGXCrossAnalysisError("invalid provider response")
        if any(type(response[k]) is not type(v) or response[k]!=v for k,v in request.items()):
            raise CGXCrossAnalysisError("provider response binding mismatch")
        raw=response["payload"]
        if type(raw) is not bytes or len(raw)>limit:
            raise CGXCrossAnalysisError("provider response byte budget")
        spent+=len(raw)
        return raw
    raw,stats=resolve_review_occurrence(occurrence,expected_sha256,fetch,gate,
                                      prefix=prefix,max_bytes=max_bytes)
    return raw,dict(stats,task_id=task_id,provider_bytes=spent,
                    provider_authentication_performed=False)



def write_review_collection(archive, payloads, *, task_id, source_revision):
    """One caller-owned review carrier, multiple named roots, shared object bytes.

    Names are evidence occurrence IDs, not file paths or authority. The
    returned descriptor must be anchored independently; no native DBR.
    """
    import hashlib,json,re,zipfile
    def token(v):return type(v) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}",v)
    if not token(task_id) or not token(source_revision) or type(payloads) is not dict or not 1<=len(payloads)<=512:
        raise CGXCrossAnalysisError("invalid collection identity")
    if any(not token(k) or type(v) is not bytes for k,v in payloads.items()) or sum(map(len,payloads.values()))>5*1024*1024:
        raise CGXCrossAnalysisError("invalid collection payloads")
    if archive.namelist():raise CGXCrossAnalysisError("review carrier must be empty")
    entries={};objects={}
    for k,raw in sorted(payloads.items()):
        root,parts=pack_nested_review_payload(raw)
        entries[k]={"root":root,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
        objects.update(parts)
    for key,data in sorted(objects.items()):
        info=zipfile.ZipInfo("review/objects/"+key)
        info.compress_type=zipfile.ZIP_STORED
        archive.writestr(info,data)
    descriptor={"schema":"CGX-REVIEW-COLLECTION/0.1","task_id":task_id,
        "source_revision":source_revision,"entries":entries,"native_admitted":False,"authority_transfer":False}
    h=hashlib.sha256(json.dumps(descriptor,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")).hexdigest()
    return descriptor,h


def hydrate_review_collection(archive, descriptor, expected_sha256, *,
                              task_id, source_revision, scope_revision, selected, max_bytes, authorise):
    """Exact named occurrence reads with cumulative logical fetch budget.

    Caller authenticates the descriptor and live scope. No cross-occurrence
    permissions or native authority inferred from deduplicated payload bytes.
    """
    import hashlib,json,re
    def token(v):return type(v) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}",v)
    def stamp(v):return type(v) is str and re.fullmatch(r"[a-f0-9]{64}",v)
    if (not all(token(v) for v in (task_id,source_revision,scope_revision))
            or not stamp(expected_sha256) or type(max_bytes) is not int or not 1<=max_bytes<=32*1024*1024
            or type(selected) is not list or not 1<=len(selected)<=64 or any(not token(k) for k in selected)
            or len(set(selected))!=len(selected)):
        raise CGXCrossAnalysisError("invalid collection request")
    if (type(descriptor) is not dict or set(descriptor)!={"schema","task_id","source_revision","entries","native_admitted","authority_transfer"}
            or descriptor["schema"]!="CGX-REVIEW-COLLECTION/0.1" or descriptor["task_id"]!=task_id
            or descriptor["source_revision"]!=source_revision or descriptor["native_admitted"] is not False
            or descriptor["authority_transfer"] is not False or type(descriptor["entries"]) is not dict
            or not 1<=len(descriptor["entries"])<=512):
        raise CGXCrossAnalysisError("collection binding mismatch")
    entries={}
    for k,v in descriptor["entries"].items():
        if (not token(k) or type(v) is not dict or set(v)!={"root","sha256","bytes"}
                or not stamp(v["root"]) or not stamp(v["sha256"]) or type(v["bytes"]) is not int
                or not 0<=v["bytes"]<=5*1024*1024):
            raise CGXCrossAnalysisError("invalid collection entry")
        entries[k]=dict(v)
    snap={**descriptor,"entries":entries}
    if (sum(v["bytes"] for v in entries.values())>5*1024*1024
            or hashlib.sha256(json.dumps(snap,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")).hexdigest()!=expected_sha256):
        raise CGXCrossAnalysisError("collection descriptor mismatch")
    if any(k not in entries for k in selected):raise CGXCrossAnalysisError("unknown collection occurrence")
    def check(k):
        if authorise(task_id,k,source_revision,scope_revision,expected_sha256) is not True:
            raise PermissionError("collection occurrence denied or revoked")
    for k in selected:check(k)
    if sum(entries[k]["bytes"] for k in selected)>max_bytes:
        raise CGXCrossAnalysisError("collection payload budget")
    resolved={};spent=0;objects_read=0
    for k in sorted(selected):
        check(k);e=entries[k]
        if max_bytes<=spent:raise CGXCrossAnalysisError("collection fetch budget")
        raw,stats=hydrate_nested_review_archive(archive,e["root"],allowed_prefixes=("",),max_bytes=max_bytes-spent)
        if len(raw)!=e["bytes"] or hashlib.sha256(raw).hexdigest()!=e["sha256"]:
            raise CGXCrossAnalysisError("collection payload mismatch")
        spent+=stats["fetched_bytes"];objects_read+=stats["fetched_objects"]
        check(k);resolved[k]=raw
    for k in selected:check(k)
    return resolved,{"descriptor_sha256":expected_sha256,"task_id":task_id,
        "scope_revision":scope_revision,"selected":sorted(selected),"logical_fetched_bytes":spent,
        "logical_fetched_objects":objects_read,"expanded_bytes":sum(map(len,resolved.values())),
        "provider_authentication_performed":False,"native_admitted":False,"authority_transfer":False}



def _atlas_review_snapshot(raw, expected_sha256):
    """Parse bounded exact atlas bytes; preserve occurrence identity and field text."""
    import hashlib,json,re
    if (type(raw) is not bytes or not 1<=len(raw)<=5*1024*1024
            or type(expected_sha256) is not str or not re.fullmatch(r"[a-f0-9]{64}",expected_sha256)
            or hashlib.sha256(raw).hexdigest()!=expected_sha256):
        raise CGXCrossAnalysisError("atlas source revision mismatch")
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d:raise CGXCrossAnalysisError("duplicate atlas JSON key")
            d[k]=v
        return d
    try:doc=json.loads(raw,object_pairs_hook=unique)
    except (ValueError,RecursionError,UnicodeError) as exc:
        raise CGXCrossAnalysisError("invalid atlas source") from exc
    if type(doc) is not dict:raise CGXCrossAnalysisError("invalid atlas document")
    headers=doc.get("headers");rows=doc.get("records")
    required={"ID","Domain","Family","Component Archetype","Baseline Geometry",
        "Geometric Parameters","Typical Material Stack","Primary Physics",
        "Baseline Model / Equation","Ports / Interfaces","Current Manufacturing Route",
        "Current CGX Build Class","Acceptance Tests","Failure Modes","Evidence State","Source Authority Class"}
    if (type(headers) is not list or not 16<=len(headers)<=64
            or any(type(k) is not str or not 1<=len(k)<=128 for k in headers)
            or len(set(headers))!=len(headers) or not required.issubset(headers)
            or type(rows) is not list or not 1<=len(rows)<=2048
            or type(doc.get("record_count")) is not int or doc["record_count"]!=len(rows)):
        raise CGXCrossAnalysisError("atlas structure mismatch")
    def encode(d):return json.dumps(d,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")
    values={}; references={};groups={}
    for row in rows:
        if (type(row) is not dict or set(row)!=set(headers)
                or any(type(v) is not str or len(v)>16384 for v in row.values())
                or any(not row[k].strip() for k in required)
                or not re.fullmatch(r"CGA-[A-Z0-9-]{1,64}",row["ID"])):
            raise CGXCrossAnalysisError("invalid atlas occurrence")
        rid=row["ID"]
        if rid in values:raise CGXCrossAnalysisError("duplicate atlas occurrence")
        body=encode(row)
        semantic=hashlib.sha256(encode({k:v for k,v in row.items() if k!="ID"})).hexdigest()
        root,_=pack_nested_review_payload(body)
        references[rid]={"row_sha256":hashlib.sha256(body).hexdigest(),"row_ternary_root":root,
            "row_bytes":len(body),"semantic_sha256":semantic,"domain":row["Domain"],
            "family":row["Family"],"evidence_state":row["Evidence State"],
            "build_class":row["Current CGX Build Class"]}
        groups.setdefault(semantic,[]).append(rid)
        values[rid]=body
    # Exact equality of non-ID metadata is only an alias review candidate.
    # No occurrence is discarded or given another occurrence's permission.
    aliases=[sorted(v) for v in groups.values() if len(v)>1]
    index={"schema":"CGX-ATLAS-REVIEW-WORKSET/0.1","source_sha256":expected_sha256,
        "record_count":len(values),"unique_metadata_count":len(groups),
        "references":dict(sorted(references.items())),"exact_metadata_alias_candidates":sorted(aliases),
        "implementation_units_completed":0,"physical_instances_qualified":0,
        "execution_authorized":False,"native_admitted":False}
    return {**index,"workset_sha256":hashlib.sha256(encode(index)).hexdigest()},values


def atlas_review_workset(raw, *, expected_sha256):
    """Index every existing atlas occurrence; no synthetic implementation IDs."""
    return _atlas_review_snapshot(raw,expected_sha256)[0]


def hydrate_atlas_review_rows(raw, *, expected_sha256, expected_workset_sha256,
                               selected, task_id, scope_revision, max_bytes, authorise):
    """Exact canonical row review, with distinct occurrence permission checks."""
    import re,hashlib
    token=lambda v:type(v) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}",v)
    if (not token(task_id) or not token(scope_revision)
            or type(expected_workset_sha256) is not str or not re.fullmatch(r"[a-f0-9]{64}",expected_workset_sha256)
            or type(selected) is not list or not 1<=len(selected)<=64
            or any(type(k) is not str or not re.fullmatch(r"CGA-[A-Z0-9-]{1,64}",k) for k in selected)
            or len(set(selected))!=len(selected) or type(max_bytes) is not int
            or not 1<=max_bytes<=1024*1024):
        raise CGXCrossAnalysisError("invalid atlas review request")
    def check(k):
        if authorise(task_id,k,expected_sha256,scope_revision,expected_workset_sha256) is not True:
            raise PermissionError("atlas occurrence denied or revoked")
    for k in selected:check(k)
    index,values=_atlas_review_snapshot(raw,expected_sha256)
    if index["workset_sha256"]!=expected_workset_sha256 or any(k not in values for k in selected):
        raise CGXCrossAnalysisError("atlas workset binding mismatch")
    if sum(len(values[k]) for k in selected)>max_bytes:
        raise CGXCrossAnalysisError("atlas row budget")
    out={}
    for k in sorted(selected):
        check(k)
        b=values[k];ref=index["references"][k]
        root,objects=pack_nested_review_payload(b)
        inverse,_=hydrate_nested_review_payload(root,objects.__getitem__,allowed_prefixes=("",),max_bytes=1024*1024)
        if inverse!=b or hashlib.sha256(b).hexdigest()!=ref["row_sha256"] or root!=ref["row_ternary_root"]:
            raise CGXCrossAnalysisError("atlas row inverse mismatch")
        out[k]=inverse
        check(k)
    for k in selected:check(k)
    return out,{"task_id":task_id,"scope_revision":scope_revision,
        "source_sha256":expected_sha256,"workset_sha256":expected_workset_sha256,
        "selected":sorted(selected),"expanded_bytes":sum(map(len,out.values())),
        "provider_authentication_performed":False,"native_admitted":False,
        "execution_authorized":False,"physical_instances_qualified":0}

def write_atlas_review_collection(archive, raw, *, expected_sha256,
                                  expected_workset_sha256, task_id):
    """Build the existing collection format from exact atlas occurrences.

    The caller must independently anchor the returned descriptor digest.
    No new registry, native promotion or physical qualification is produced.
    """
    index, values = _atlas_review_snapshot(raw, expected_sha256)
    if index["workset_sha256"] != expected_workset_sha256:
        raise CGXCrossAnalysisError("atlas workset binding mismatch")
    descriptor, digest = write_review_collection(
        archive, values, task_id=task_id, source_revision=expected_sha256)
    for k, v in descriptor["entries"].items():
        ref = index["references"][k]
        if (v["root"], v["sha256"], v["bytes"]) != (
                ref["row_ternary_root"], ref["row_sha256"], ref["row_bytes"]):
            raise CGXCrossAnalysisError("atlas collection row mismatch")
    return descriptor, digest
