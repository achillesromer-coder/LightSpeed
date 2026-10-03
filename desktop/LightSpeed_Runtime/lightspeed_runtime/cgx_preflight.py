from __future__ import annotations

"""Typed read-only wrappers for the existing CGX assurance/custodial preflight chain."""

from pathlib import Path
import sys
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from cgx_assurance_route import route as assurance_route  # type: ignore
from cgx_assurance_preflight import assess as assurance_assess  # type: ignore
from resolve_cgx_extensions import resolve as custodial_resolve  # type: ignore
from cgx_custodial_preflight import assess_custodial  # type: ignore


VALID_DOMAINS = {"romer", "eco", "emassc", "lightspeed"}
VALID_EXECUTION_DEPTHS = {"inspect", "propose", "simulate", "execute", "build", "publish"}
VALID_CASCADE_CLASSES = {"C0", "C1", "C2", "C3", "C4"}


class CGXPreflightError(ValueError):
    """Raised when a preflight request is malformed."""


def _normalise_domain(value: str) -> str:
    domain = str(value or "").strip().lower()
    aliases = {"romer-grex": "romer", "eco-grex": "eco", "ls": "lightspeed"}
    domain = aliases.get(domain, domain)
    if domain not in VALID_DOMAINS:
        raise CGXPreflightError(f"unsupported domain: {value!r}")
    return domain


def _normalise_depth(value: str) -> str:
    depth = str(value or "").strip().lower()
    if depth not in VALID_EXECUTION_DEPTHS:
        raise CGXPreflightError(f"unsupported execution depth: {value!r}")
    return depth


def _normalise_cascade(value: str) -> str:
    cascade = str(value or "C0").strip().upper()
    if cascade not in VALID_CASCADE_CLASSES:
        raise CGXPreflightError(f"unsupported cascade class: {value!r}")
    return cascade


def _normalise_tags(tags: Iterable[str] = ()) -> list[str]:
    return sorted({str(item).strip().lower() for item in tags if str(item).strip()})


def build_assurance_preflight(
    domain: str,
    execution_depth: str,
    *,
    cascade_class: str = "C0",
    tags: Iterable[str] = (),
    assessment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    domain = _normalise_domain(domain)
    depth = _normalise_depth(execution_depth)
    cascade = _normalise_cascade(cascade_class)
    tag_list = _normalise_tags(tags)

    resolution = assurance_route(domain, depth, cascade, tag_list)
    decision, reasons = assurance_assess(resolution, assessment)
    return {
        "schema": "CGX-ASSURANCE-PREFLIGHT/0.2",
        "decision": decision,
        "hold_reasons": list(reasons),
        "resolution": resolution,
        "assessment_supplied": assessment is not None,
        "automatic_execution": False,
        "canonical_mutation": False,
        "authority_limit": (
            "Assurance clearance bounds method evidence only. It is not risk acceptance, "
            "legal approval, certification, custodial approval, or execution authority."
        ),
    }


def build_custodial_preflight(
    domain: str,
    execution_depth: str,
    *,
    reasoning_depth: str = "standard",
    cascade_class: str = "C0",
    tags: Iterable[str] = (),
    requested_mode: str | None = None,
    assessment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    domain = _normalise_domain(domain)
    depth = _normalise_depth(execution_depth)
    cascade = _normalise_cascade(cascade_class)
    tag_list = _normalise_tags(tags)

    resolution = custodial_resolve(
        domain,
        depth,
        str(reasoning_depth or "standard"),
        cascade,
        tag_list,
        requested_mode,
    )
    decision, reasons = assess_custodial(resolution, assessment)
    return {
        "schema": "CGX-CUSTODIAL-PREFLIGHT/0.2",
        "decision": decision,
        "hold_reasons": list(reasons),
        "resolution": resolution,
        "assessment_supplied": assessment is not None,
        "source_driven_hard_predicates": list(resolution.get("hard_predicates") or []),
        "automatic_execution": False,
        "canonical_mutation": False,
        "authority_limit": (
            "Custodial preflight may HOLD only under declared gate/safety conditions. "
            "It does not create semantic, moral, ownership, representation, or execution authority."
        ),
    }


def build_consequence_preflight(
    domain: str,
    execution_depth: str,
    *,
    reasoning_depth: str = "standard",
    cascade_class: str = "C0",
    tags: Iterable[str] = (),
    assurance_assessment: dict[str, Any] | None = None,
    custodial_assessment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    domain = _normalise_domain(domain)
    depth = _normalise_depth(execution_depth)
    cascade = _normalise_cascade(cascade_class)
    tag_list = _normalise_tags(tags)

    assurance = build_assurance_preflight(
        domain,
        depth,
        cascade_class=cascade,
        tags=tag_list,
        assessment=assurance_assessment,
    )
    custodial = build_custodial_preflight(
        domain,
        depth,
        reasoning_depth=reasoning_depth,
        cascade_class=cascade,
        tags=tag_list,
        assessment=custodial_assessment,
    )
    holds = [
        *[f"assurance:{item}" for item in assurance["hold_reasons"] if assurance["decision"] == "HOLD"],
        *[f"custodial:{item}" for item in custodial["hold_reasons"] if custodial["decision"] == "HOLD"],
    ]
    consequential = depth in {"execute", "build", "publish"} or cascade in {"C2", "C3", "C4"}
    decision = "HOLD" if holds else (
        "CLEARED_FOR_AUTHORITY_GATE" if consequential else "ALLOW_WITH_RECEIPTS"
    )
    return {
        "schema": "CGX-CONSEQUENCE-PREFLIGHT/0.2",
        "decision": decision,
        "hold_reasons": holds,
        "context": {
            "domain": domain,
            "execution_depth": depth,
            "reasoning_depth": str(reasoning_depth or "standard"),
            "cascade_class": cascade,
            "tags": tag_list,
        },
        "assurance": assurance,
        "custodial": custodial,
        "next_gate": (
            "resolve blocking evidence or predicates"
            if decision == "HOLD"
            else "scoped authority / risk acceptance / execution lease"
        ),
        "automatic_execution": False,
        "canonical_mutation": False,
        "authority_limit": (
            "CLEARED_FOR_AUTHORITY_GATE is not execution permission. It only means the "
            "assurance and custodial preflights found no unresolved blocker for the declared scope."
        ),
    }


__all__ = [
    "CGXPreflightError",
    "build_assurance_preflight",
    "build_custodial_preflight",
    "build_consequence_preflight",
]
