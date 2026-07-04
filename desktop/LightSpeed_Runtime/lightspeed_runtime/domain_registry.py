from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainDefinition:
    name: str
    summary: str
    responsibilities: list[str]


@dataclass(frozen=True)
class SourceTypeDefinition:
    source_type: str
    label: str
    summary: str
    operator_usage: str


CANONICAL_DOMAINS: dict[str, DomainDefinition] = {
    "operator_home": DomainDefinition(
        name="operator_home",
        summary="Agent home/work environment, source-truth policy, model budgets, and consolidation control.",
        responsibilities=[
            "environment governance",
            "source-truth registry",
            "model assignments",
            "consolidation queue",
            "overlap analysis",
        ],
    ),
    "shell": DomainDefinition(
        name="shell",
        summary="Desktop app shell, workspace state, approvals, and floor navigation.",
        responsibilities=[
            "workspace navigation",
            "session state",
            "approvals",
            "operator-facing shell controls",
        ],
    ),
    "achilles": DomainDefinition(
        name="achilles",
        summary="Primary operator persona and bounded orchestration layer.",
        responsibilities=[
            "intent interpretation",
            "retrieval",
            "action proposal",
            "approval-gated execution",
            "publishable summaries",
        ],
    ),
    "reservoirs": DomainDefinition(
        name="reservoirs",
        summary="External source registration, indexing, manifests, provenance, and previews.",
        responsibilities=[
            "source registration",
            "classification",
            "asset indexing",
            "manifest handling",
            "knowledge provenance",
        ],
    ),
    "labs": DomainDefinition(
        name="labs",
        summary="Calculators, GMAT/scenario execution, and physics/simulation contracts.",
        responsibilities=[
            "scenario runs",
            "calculator jobs",
            "GMAT bundle generation",
            "dataset attachment",
            "run metrics",
        ],
    ),
    "publishing": DomainDefinition(
        name="publishing",
        summary="Curated exports for website/dataspace consumption.",
        responsibilities=[
            "workspace publish manifests",
            "artifact linking",
            "status snapshots",
            "dataspace handoff",
        ],
    ),
}


FLOOR_RUNTIME_MAPPING: dict[str, str] = {
    "Trinity": "shell",
    "Neo": "achilles",
    "Architect": "shell",
    "TheConstruct": "labs",
    "Morpheus": "reservoirs",
    "Oracle": "reservoirs",
    "Smith": "shell",
    "Merovingian": "publishing",
}


SOURCE_TYPE_DEFINITIONS: dict[str, SourceTypeDefinition] = {
    "doctrine_export": SourceTypeDefinition(
        source_type="doctrine_export",
        label="Doctrine Export",
        summary="Proofed planning, direction, and operational doctrine exported from notebooks or knowledge tools.",
        operator_usage="Use as high-priority guidance when forming briefs, knowns, and publishable summaries.",
    ),
    "calculator_library": SourceTypeDefinition(
        source_type="calculator_library",
        label="Calculator Library",
        summary="Reusable analytical calculators, scripts, and reference tooling that support engineering or mission planning.",
        operator_usage="Use as reference tooling for lab runs, scenario inputs, and validation support.",
    ),
    "physics_archive": SourceTypeDefinition(
        source_type="physics_archive",
        label="Physics Archive",
        summary="Legacy or deep-reference technical material retained for equation, physics, and method backtracking.",
        operator_usage="Use as archival support for refinement, validation, and recovery of historical technical context.",
    ),
    "drive_business_layer": SourceTypeDefinition(
        source_type="drive_business_layer",
        label="Drive Business Layer",
        summary="Business-case and operational source layer curated in Drive and held as a gated truth surface.",
        operator_usage="Use only after source-status and claim gates are satisfied; do not treat raw sheets as implementation-ready.",
    ),
    "repo_control_layer": SourceTypeDefinition(
        source_type="repo_control_layer",
        label="Repo Control Layer",
        summary="Control registry for claims, source status, dossiers, and Codex-safe handoff state.",
        operator_usage="Use as the coordination and approval layer that determines what may enter desktop implementation.",
    ),
    "desktop_runtime_layer": SourceTypeDefinition(
        source_type="desktop_runtime_layer",
        label="Desktop Runtime Layer",
        summary="Local executable contract surface that consumes approved control records and curates internal state.",
        operator_usage="Use as the active integration lane for LightSpeed and related desktop operators.",
    ),
    "public_dossier_output": SourceTypeDefinition(
        source_type="public_dossier_output",
        label="Public Dossier Output",
        summary="Reviewed submission and presentation output prepared for external consumption.",
        operator_usage="Use only after proofing, approval, and packaging gates have passed.",
    ),
    "device_operations_lane": SourceTypeDefinition(
        source_type="device_operations_lane",
        label="Device Operations Lane",
        summary="Future Achilles, GO, and dash handoff lane for reviewed tasks and results.",
        operator_usage="Use as a later-stage operations channel, not as a primary truth source.",
    ),
    "web_publish_shell": SourceTypeDefinition(
        source_type="web_publish_shell",
        label="Web Publish Shell",
        summary="Final gated web shell for public-facing publication surfaces.",
        operator_usage="Use only for gated publication outputs after desktop proof, repo sync, and approval.",
    ),
}


def get_domain_definition(name: str) -> DomainDefinition:
    return CANONICAL_DOMAINS[name]


def get_source_type_definition(source_type: str) -> SourceTypeDefinition | None:
    return SOURCE_TYPE_DEFINITIONS.get(source_type)
