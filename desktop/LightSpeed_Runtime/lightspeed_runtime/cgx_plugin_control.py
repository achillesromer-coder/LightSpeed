from __future__ import annotations

"""CGX plugin/interface control helpers for the existing LightSpeed runtime.

This module is deliberately not a server or second runtime. It resolves thin
human/plugin selectors into current CGX state and chooses the minimum sufficient
work strategy before the existing Cognigrex supervisor / LS GO paths are used.
"""

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "cgx-context-envelope-v1"
STRATEGIES = {
    "reuse_existing",
    "reconcile_existing",
    "execute_missing_only",
    "bounded_new_execution",
    "blocked",
}
DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parents[3]
    / "cgx"
    / "domain_templates"
    / "plugin_selector_registry.json"
)
DEFAULT_DOMAINS_PATH = (
    Path(__file__).resolve().parents[3]
    / "cgx"
    / "domain_templates"
    / "domains.json"
)


class CGXInterfaceError(RuntimeError):
    """Raised when current CGX state cannot safely resolve an interface request."""


@dataclass(frozen=True)
class Intent:
    operation: str
    subject: str
    constraints: tuple[str, ...] = ()
    requested_outputs: tuple[str, ...] = ()
    proof_standard: str | None = None

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "Intent":
        operation = str(payload.get("operation") or "").strip()
        subject = str(payload.get("subject") or "").strip()
        if not operation or not subject:
            raise CGXInterfaceError("intent requires non-empty operation and subject")
        constraints = tuple(
            str(item).strip()
            for item in payload.get("constraints") or ()
            if str(item).strip()
        )
        outputs = tuple(
            str(item).strip()
            for item in payload.get("requested_outputs") or ()
            if str(item).strip()
        )
        proof = payload.get("proof_standard")
        return cls(
            operation=operation,
            subject=subject,
            constraints=constraints,
            requested_outputs=outputs,
            proof_standard=str(proof).strip() if proof else None,
        )


@dataclass(frozen=True)
class WorkDecision:
    strategy: str
    why: tuple[str, ...]
    reused_receipts: tuple[str, ...] = ()
    unresolved_discriminants: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "why": list(self.why),
            "reused_receipts": list(self.reused_receipts),
            "unresolved_discriminants": list(self.unresolved_discriminants),
        }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CGXInterfaceError(f"required CGX file missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CGXInterfaceError(f"invalid CGX JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise CGXInterfaceError(f"CGX JSON root must be an object: {path}")
    return payload


def load_selector_registry(path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    payload = _read_json(path)
    selectors = payload.get("selectors")
    if not isinstance(selectors, dict) or not selectors:
        raise CGXInterfaceError("selector registry contains no selectors")
    return payload


def load_domains(path: Path = DEFAULT_DOMAINS_PATH) -> dict[str, Any]:
    payload = _read_json(path)
    if not isinstance(payload.get("domains"), dict):
        raise CGXInterfaceError("domains registry is missing domains")
    return payload


def normalize_selector_name(name: str) -> str:
    return (
        name.strip()
        .casefold()
        .replace("ö", "o")
        .replace("_", "-")
        .replace(" ", "-")
        .lstrip("@")
    )


def resolve_selector(
    name: str,
    *,
    registry: dict[str, Any] | None = None,
    domains: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry or load_selector_registry()
    domains = domains or load_domains()
    key = normalize_selector_name(name)
    aliases = {
        "romergrex": "romer-grex",
        "roemer-grex": "romer-grex",
        "roemergrex": "romer-grex",
        "ecogrex": "eco-grex",
        "light-speed": "lightspeed",
        "ls": "lightspeed",
        "cgx": "cognigrex",
    }
    key = aliases.get(key, key)
    selector = (registry.get("selectors") or {}).get(key)
    if not isinstance(selector, dict):
        raise CGXInterfaceError(f"unknown CGX selector: {name}")

    resolved = {"name": key, **selector}
    domain_key = resolved.get("domain") or resolved.get("default_domain")
    if domain_key:
        domain = (domains.get("domains") or {}).get(domain_key)
        if not isinstance(domain, dict):
            raise CGXInterfaceError(f"selector domain is unavailable: {domain_key}")
        resolved["domain_profile"] = domain
        resolved.setdefault("principal_agent", domain.get("principal_agent"))
    return resolved


def current_recovery(domains: dict[str, Any] | None = None) -> dict[str, Any]:
    domains = domains or load_domains()
    policy = domains.get("generation_policy") or {}
    state = str(policy.get("current_recovery_state") or "").strip()
    sha256 = str(policy.get("current_recovery_sha256") or "").strip()
    evidence = policy.get("recovery_promotion_evidence") or {}
    verifier = "PASS" if evidence.get("canonical_verifier") == "PASS" else "UNKNOWN"
    if not state or len(sha256) != 64:
        raise CGXInterfaceError("current accepted Recovery state is unresolved")
    if verifier != "PASS":
        raise CGXInterfaceError(
            f"current Recovery {state} has no canonical verifier PASS"
        )
    return {
        "state_id": state,
        "sha256": sha256,
        "content_root": policy.get("current_recovery_content_root"),
        "dbr_root": policy.get("current_recovery_dbr_root"),
        "topology": policy.get("current_recovery_topology"),
        "verification": verifier,
    }


def _receipt_id(row: dict[str, Any]) -> str | None:
    value = row.get("receipt_id") or row.get("result_id") or row.get("id")
    return str(value) if value else None


def _setish(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value}
    if isinstance(value, Iterable):
        return {str(item) for item in value}
    return {str(value)}


def _covers_intent(row: dict[str, Any], intent: Intent) -> bool:
    """Return True only for an explicit, complete reusable result.

    Absence of operation metadata is not treated as wildcard coverage. Partial
    results that advertise unresolved discriminants must flow to reconciliation
    or missing-only execution rather than short-circuiting as exact reuse.
    """
    if str(row.get("status") or "").upper() not in {"PASS", "VALID", "COMPLETE"}:
        return False
    subject = str(row.get("subject") or "").casefold()
    if subject != intent.subject.casefold():
        return False
    unresolved = _setish(
        row.get("unresolved_discriminants") or row.get("missing")
    )
    if unresolved:
        return False
    operations = {
        item.casefold()
        for item in _setish(row.get("operations") or row.get("operation"))
    }
    if not operations or intent.operation.casefold() not in operations:
        return False
    covered = {item.casefold() for item in _setish(row.get("constraints"))}
    required = {item.casefold() for item in intent.constraints}
    if not required.issubset(covered):
        return False
    if intent.proof_standard:
        proof = str(row.get("proof_standard") or "")
        if proof.casefold() != intent.proof_standard.casefold():
            return False
    return bool(row.get("current", True))


def decide_minimum_sufficient_work(
    intent: Intent,
    evidence: Iterable[dict[str, Any]] = (),
) -> WorkDecision:
    """Choose reuse/reconciliation/missing-only/new-work without executing it.

    Reconciliation is allowed only when evidence explicitly advertises
    compatibility and a valid derivation rule. This function never assumes
    interpolation merely because two results exist.
    """
    rows = [row for row in evidence if isinstance(row, dict)]

    exact = [row for row in rows if _covers_intent(row, intent)]
    if exact:
        ids = tuple(filter(None, (_receipt_id(row) for row in exact)))
        return WorkDecision(
            "reuse_existing",
            ("A current valid result already covers the requested intent.",),
            reused_receipts=ids,
        )

    reconcilable = [
        row
        for row in rows
        if str(row.get("subject") or "").casefold() == intent.subject.casefold()
        and row.get("reconciliation_authorized") is True
        and bool(row.get("derivation_rule"))
        and str(row.get("status") or "").upper() in {"PASS", "VALID", "COMPLETE"}
    ]
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in reconcilable:
        key = str(row.get("compatibility_group") or "").strip()
        if key:
            groups.setdefault(key, []).append(row)
    for group, compatible in groups.items():
        if len(compatible) >= 2:
            ids = tuple(filter(None, (_receipt_id(row) for row in compatible)))
            return WorkDecision(
                "reconcile_existing",
                (
                    f"Compatible prior results in group {group} explicitly permit derivation.",
                    "Use the declared derivation rule and uncertainty treatment before new execution.",
                ),
                reused_receipts=ids,
            )

    missing: list[str] = []
    for row in rows:
        if str(row.get("subject") or "").casefold() != intent.subject.casefold():
            continue
        unresolved = row.get("unresolved_discriminants") or row.get("missing")
        for item in _setish(unresolved):
            if item and item not in missing:
                missing.append(item)
    if missing:
        return WorkDecision(
            "execute_missing_only",
            (
                "Existing evidence is relevant but explicitly identifies unresolved discriminants.",
                "Execute only the smallest work needed to resolve those discriminants.",
            ),
            unresolved_discriminants=tuple(missing),
        )

    return WorkDecision(
        "bounded_new_execution",
        (
            "No current exact result or explicitly valid reconciliation route was found.",
            "Bound any new execution to the decision need and current execution lease.",
        ),
    )


def build_context_envelope(
    selector_name: str,
    intent_payload: dict[str, Any],
    *,
    evidence: Iterable[dict[str, Any]] = (),
    registry: dict[str, Any] | None = None,
    domains: dict[str, Any] | None = None,
    reasoning_route: str = "local_first",
    return_mode: str = "receipt",
    allow_heavy: bool = False,
) -> dict[str, Any]:
    domains = domains or load_domains()
    selector = resolve_selector(selector_name, registry=registry, domains=domains)
    recovery = current_recovery(domains)
    intent = Intent.from_mapping(intent_payload)
    decision = decide_minimum_sufficient_work(intent, evidence)

    principal = selector.get("agent") or selector.get("principal_agent")
    if selector.get("kind") == "system" and selector.get("system") == "Cognigrex.cgx":
        principal = principal or "Neo"

    target_surfaces = ["Cognigrex.cgx"]
    if selector.get("kind") == "domain":
        target_surfaces.append(str(selector.get("domain_profile", {}).get("file")))
    if selector.get("name") == "lightspeed":
        target_surfaces.extend(["LS.cgx", "LightSpeed Desktop", "LS GO"])

    return {
        "schema_version": SCHEMA_VERSION,
        "selector": {
            "name": selector["name"],
            "kind": selector.get("kind"),
            "agent": selector.get("agent"),
            "domain": selector.get("domain") or selector.get("default_domain"),
            "system": selector.get("system"),
        },
        "recovery": recovery,
        "authority": {
            "operational_head": "Neo",
            "canonical_release_gate": "Achilles",
            "principal_agent": principal,
            "restrictions": [
                "no automatic semantic truth from runtime receipts",
                "no canonical promotion without resolved gate",
                "no parallel runtime or authority creation",
            ],
        },
        "intent": asdict(intent),
        "work_policy": {
            **decision.to_dict(),
            "reasoning_route": reasoning_route,
            "return_mode": return_mode,
            "allow_heavy": bool(allow_heavy),
        },
        "execution": {
            "target_surfaces": target_surfaces,
            "skills": ["cgx-handshake", "cgx-minimum-sufficient-work"],
            "capabilities": [],
            "required_gates": ["current-recovery-verifier", "resolved-execution-lease"],
        },
    }


__all__ = [
    "CGXInterfaceError",
    "Intent",
    "WorkDecision",
    "build_context_envelope",
    "current_recovery",
    "decide_minimum_sufficient_work",
    "load_domains",
    "load_selector_registry",
    "normalize_selector_name",
    "resolve_selector",
]
