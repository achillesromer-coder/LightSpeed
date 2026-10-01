from __future__ import annotations

import hashlib
import re
from pathlib import PurePath
from typing import Any, Mapping


class CGXConversionPlanError(ValueError):
    """Raised when a file-conversion plan cannot be built without guessing."""


_HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CGXConversionPlanError(f"{field} must be non-empty text")
    return value.strip()


def _load_registry(value: Mapping[str, Any] | None, field: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise CGXConversionPlanError(f"{field} must be an object")
    return dict(value)


def _extension(file_name: str) -> str:
    suffix = PurePath(file_name).suffix.lower().lstrip(".")
    return suffix


def _match_type(file_name: str, media_type: str | None, registry: dict[str, Any]) -> dict[str, Any] | None:
    explicit = (media_type or "").strip().lower()
    ext = _extension(file_name)
    for item in registry.get("types", []):
        if not isinstance(item, Mapping):
            continue
        if explicit and str(item.get("id") or "").lower() == explicit:
            return dict(item)
        extensions = {str(x).lower().lstrip(".") for x in item.get("extensions", [])}
        if ext and ext in extensions:
            return dict(item)
    return None


def _match_first_file(
    *,
    source_sha256: str,
    domain: str | None,
    first_file_registry: dict[str, Any],
) -> dict[str, Any] | None:
    matches = []
    for item in first_file_registry.get("mappings", []):
        if not isinstance(item, Mapping):
            continue
        if str(item.get("source_sha256") or "").lower() != source_sha256.lower():
            continue
        if domain and str(item.get("domain") or "") != domain:
            continue
        matches.append(dict(item))
    if len(matches) > 1 and not domain:
        # A source may intentionally feed multiple domains (for example EMASSC -> LS).
        # Do not silently choose one semantic owner.
        return None
    return matches[0] if matches else None


def compile_conversion_plan(
    *,
    file_name: str,
    source_sha256: str,
    source_ref: str,
    media_type: str | None = None,
    domain: str | None = None,
    semantic_target: str | None = None,
    requested_outputs: list[str] | None = None,
    type_registry: Mapping[str, Any] | None = None,
    conversion_contract: Mapping[str, Any] | None = None,
    first_file_registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a read-only source->semantic->representation conversion plan.

    The plan never mutates canon or infers missing source values. R0 exact-source
    preservation is always the first stage. R1/R2 are enabled only by registered
    capabilities/mappings; R3 is representation-only.
    """
    file_name = _nonempty(file_name, "file_name")
    source_ref = _nonempty(source_ref, "source_ref")
    source_sha256 = _nonempty(source_sha256, "source_sha256").lower()
    if not _HEX64.match(source_sha256):
        raise CGXConversionPlanError("source_sha256 must be a 64-character hexadecimal SHA-256")

    types = _load_registry(type_registry, "type_registry")
    contract = _load_registry(conversion_contract, "conversion_contract")
    first_files = _load_registry(first_file_registry, "first_file_registry")

    if contract and contract.get("schema") != "CGX-FILE-CONVERSION-CONTRACT/0.1":
        raise CGXConversionPlanError("unsupported conversion contract schema")
    if types and types.get("schema") != "CGX-FILE-TYPE-CONVERSION-REGISTRY/0.1":
        raise CGXConversionPlanError("unsupported file-type registry schema")
    if first_files and first_files.get("schema") != "CGX-FIRST-FILE-CONVERSION-REGISTRY/0.1":
        raise CGXConversionPlanError("unsupported first-file registry schema")

    type_profile = _match_type(file_name, media_type, types)
    mapping = _match_first_file(
        source_sha256=source_sha256,
        domain=domain,
        first_file_registry=first_files,
    )

    resolved_media_type = (
        str(type_profile.get("id"))
        if type_profile
        else ((media_type or "").strip() or "application/octet-stream")
    )
    stages: list[dict[str, Any]] = [
        {
            "class": "R0_EXACT",
            "state": "READY",
            "action": "retain/reference exact native source identity and bytes",
            "authority": "source/provider",
        }
    ]
    frontier: list[dict[str, str]] = []
    loss_map: list[dict[str, str]] = []

    r1_supported = bool(type_profile and type_profile.get("r1"))
    if r1_supported:
        stages.append(
            {
                "class": "R1_SEMANTIC_REVERSIBLE",
                "state": "READY",
                "action": str(type_profile.get("r1")),
                "adapter": type_profile.get("adapter") or type_profile.get("handler"),
                "scope": "declared extracted structure only",
            }
        )
    else:
        frontier.append(
            {
                "reason": "SEMANTIC_ADAPTER_REQUIRED",
                "detail": f"No registered R1 semantic adapter for {resolved_media_type}",
            }
        )

    target = semantic_target or (mapping.get("semantic_target") if mapping else None)
    if mapping:
        stages.append(
            {
                "class": "R2_RECONSTRUCTED",
                "state": "READY",
                "action": "apply registered source-bounded semantic mapping",
                "mapping_id": mapping.get("mapping_id"),
                "semantic_target": target,
                "evidence_ceiling": mapping.get("evidence_ceiling"),
            }
        )
        loss_map.append(
            {
                "class": "R2_RECONSTRUCTED",
                "loss": "semantic reconstruction is not byte-reversible",
            }
        )
    elif target and r1_supported:
        stages.append(
            {
                "class": "R2_RECONSTRUCTED",
                "state": "HOLD_MAPPING_REQUIRED",
                "semantic_target": target,
                "action": "semantic target supplied but no admitted mapping is registered",
            }
        )
        frontier.append(
            {
                "reason": "SEMANTIC_MAPPING_REQUIRED",
                "detail": "R2 cannot be inferred from file structure alone",
            }
        )

    outputs = [str(x).strip() for x in (requested_outputs or []) if str(x).strip()]
    if outputs:
        stages.append(
            {
                "class": "R3_GENERATIVE",
                "state": "READY_AFTER_RESOLVE",
                "outputs": outputs,
                "action": "render resolved semantic state into requested representation(s)",
                "canonical_authority": False,
            }
        )
        loss_map.append(
            {
                "class": "R3_GENERATIVE",
                "loss": "representation/layout/generation cannot reconstruct source authority",
            }
        )

    if mapping and domain and mapping.get("domain") != domain:
        raise CGXConversionPlanError("registered first-file mapping domain does not match requested domain")

    intent = {
        "file_name": file_name,
        "source_sha256": source_sha256,
        "source_ref": source_ref,
        "media_type": resolved_media_type,
        "domain": domain,
        "semantic_target": target,
        "requested_outputs": outputs,
    }
    plan_hash = hashlib.sha256(
        repr(sorted(intent.items(), key=lambda item: item[0])).encode("utf-8")
    ).hexdigest()

    semantic_state = "reference_only"
    if mapping:
        semantic_state = "mapping_ready"
    elif r1_supported:
        semantic_state = "structure_ready"

    return {
        "schema": "CGX-CONVERSION-PLAN/0.1",
        "plan_sha256": plan_hash,
        "source": {
            "file_name": file_name,
            "source_ref": source_ref,
            "sha256": source_sha256,
            "media_type": resolved_media_type,
            "native_authority_preserved": True,
        },
        "type_profile": type_profile,
        "registered_mapping": mapping,
        "semantic_state": semantic_state,
        "stages": stages,
        "loss_map": loss_map,
        "frontier": frontier,
        "canonical_mutation": False,
        "execution_performed": False,
        "authority_transfer": False,
        "round_trip_scope": "R1 declared extracted structure only" if r1_supported else None,
    }
