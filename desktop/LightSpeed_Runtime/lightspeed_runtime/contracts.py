from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import uuid

try:
    from pydantic import BaseModel, ConfigDict, Field, ValidationError
except Exception:  # pragma: no cover - optional dependency
    BaseModel = None
    ConfigDict = None
    Field = None

    class ValidationError(Exception):
        pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def deterministic_id(prefix: str, *parts: str) -> str:
    joined = "::".join(str(part or "").strip().lower() for part in parts)
    digest = hashlib.sha1(joined.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


CANONICAL_DATASET_ROLES = {
    "raw",
    "reference",
    "curated",
    "derived",
    "simulation_input",
    "publish_output",
}


CANONICAL_ENTITY_KINDS = {
    "workspace",
    "project",
    "dataset",
    "table",
    "document",
    "run",
    "action",
    "artifact",
    "approval",
    "agent",
    "floor",
    "knowledge_theme",
    "source",
}


ACTION_RISK_LEVELS = {
    "publish_manifest": "publish",
    "website_publish_sync": "publish",
    "publish_snapshot": "publish",
    "package_export": "write",
    "build_heliocentric_zoning": "execute",
    "simulation_run": "execute",
    "gmat_batch": "execute",
    "knowledge_refresh": "curate",
    "proofing_review": "curate",
    "operator_brief": "read",
}


def classify_action_risk(action_type: str) -> str:
    return ACTION_RISK_LEVELS.get(str(action_type or "").strip(), "read")


def build_handoff_context(
    *,
    source_floor: str,
    target_floor: str,
    rationale: str = "",
    artifact_refs: list[dict] | None = None,
    execution_mode: str = "tool_first",
) -> dict:
    return {
        "source_floor": source_floor,
        "target_floor": target_floor,
        "rationale": rationale or "Carry current context into the target floor without losing operator intent.",
        "artifact_refs": artifact_refs or [],
        "execution_mode": execution_mode,
    }


def normalize_dataset_role(role: str | None, *, fallback: str = "reference") -> str:
    value = (role or "").strip().lower()
    if value in CANONICAL_DATASET_ROLES:
        return value
    return fallback if fallback in CANONICAL_DATASET_ROLES else "reference"


class TrustedDocumentList(list):
    def __int__(self) -> int:
        return len(self)


@dataclass
class ReservoirManifest:
    source_id: str
    root_path: str
    source_type: str
    classification: str
    configured_root_path: str = ""
    root_resolution: str = "configured"
    floor_owner: str = ""
    source_label: str = ""
    definition: str = ""
    operator_notes: str = ""
    workspace_tags: list[str] = field(default_factory=list)
    project_tags: list[str] = field(default_factory=list)
    trusted_documents: list[str] = field(default_factory=list)
    extractors: list[str] = field(default_factory=list)
    index_status: str = "unindexed"
    last_scan_at: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AssetRecord:
    asset_id: str
    source_id: str
    relative_path: str
    media_type: str
    title: str
    summary: str
    canonical_rank: str
    provenance: dict
    related_projects: list[str] = field(default_factory=list)
    related_workspaces: list[str] = field(default_factory=list)
    preview_ref: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EntityRecord:
    entity_id: str
    entity_kind: str
    title: str
    owner_floor: str
    lifecycle_state: str
    validation_state: str
    provenance: dict
    status: str = "active"
    path_ref: str | None = None
    source_refs: list[str] = field(default_factory=list)
    related_entities: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DatasetManifest:
    dataset_id: str
    title: str
    source_id: str
    owner_floor: str
    role: str
    lifecycle_state: str
    validation_state: str
    absolute_path: str
    relative_path: str
    file_format: str
    media_type: str
    size_bytes: int
    hash_sha256: str
    schema_version: str = "1.0"
    unit_system: str = "mixed"
    uncertainty_summary: str = "not_assessed"
    confidence_score: float = 0.5
    scientific_role: str = "general"
    provenance: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    related_entities: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.role = normalize_dataset_role(self.role)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AchillesActionEnvelope:
    action_id: str
    actor: str
    workspace: str
    target_scope: str
    action_type: str
    inputs: dict
    requires_approval: bool = True
    approval_state: str = "pending"
    result_ref: str | None = None
    audit_ref: str | None = None
    validation_state: str = "validated"
    manager_agent: str = "Achilles"
    trace_id: str | None = None
    risk_level: str = "read"
    execution_mode: str = "tool_first"
    handoff_context: dict = field(default_factory=dict)

    def approve(self, audit_ref: str | None = None) -> None:
        self.approval_state = "approved"
        if audit_ref:
            self.audit_ref = audit_ref

    def reject(self, audit_ref: str | None = None) -> None:
        self.approval_state = "rejected"
        if audit_ref:
            self.audit_ref = audit_ref

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WorkspacePublishManifest:
    workspace_id: str
    project_id: str
    published_at: str
    status: str
    summary_blocks: list[dict]
    artifacts: list[dict]
    visualizations: list[dict]
    latest_runs: list[dict]
    links: list[dict]
    visibility: str
    validation_state: str = "pending"
    validation_summary: str = ""
    owner_floor: str = "Architect"
    control_floor: str = "Architect"
    source_root: str = ""
    source_root_kind: str = "canonical_c_root"
    destination_root: str = ""
    destination_kind: str = "snapshot"
    destination_root_kind: str = "snapshot_output"
    overwrite_existing: bool = True
    snapshot_contract_version: str = "2026.04.finalization"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LabRunContract:
    run_id: str
    lab_type: str
    scenario_id: str
    dataset_refs: list[str]
    parameter_set: dict
    engine: str
    outputs: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    status: str = "queued"
    published: bool = False
    uncertainty_summary: str = "not_assessed"
    confidence_score: float = 0.5

    def mark_running(self) -> None:
        self.status = "running"

    def mark_completed(self, metrics: dict | None = None) -> None:
        self.status = "completed"
        if metrics:
            self.metrics = metrics

    def to_dict(self) -> dict:
        return asdict(self)


if BaseModel is not None:
    class DatasetManifestModel(BaseModel):
        model_config = ConfigDict(extra="allow")

        dataset_id: str
        title: str
        source_id: str
        owner_floor: str
        role: str
        lifecycle_state: str
        validation_state: str
        absolute_path: str
        relative_path: str
        file_format: str
        media_type: str
        size_bytes: int
        hash_sha256: str
        schema_version: str = "1.0"
        unit_system: str = "mixed"
        uncertainty_summary: str = "not_assessed"
        confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
        scientific_role: str = "general"
        provenance: dict = Field(default_factory=dict)
        tags: list[str] = Field(default_factory=list)
        related_entities: list[str] = Field(default_factory=list)

    class AchillesActionEnvelopeModel(BaseModel):
        model_config = ConfigDict(extra="allow")

        action_id: str
        actor: str
        workspace: str
        target_scope: str
        action_type: str
        inputs: dict
        requires_approval: bool = True
        approval_state: str = "pending"
        result_ref: str | None = None
        audit_ref: str | None = None
        validation_state: str = "validated"
        manager_agent: str = "Achilles"
        trace_id: str | None = None
        risk_level: str = "read"
        execution_mode: str = "tool_first"
        handoff_context: dict = Field(default_factory=dict)

    class WorkspacePublishManifestModel(BaseModel):
        model_config = ConfigDict(extra="allow")

        workspace_id: str
        project_id: str
        published_at: str
        status: str
        summary_blocks: list[dict]
        artifacts: list[dict]
        visualizations: list[dict]
        latest_runs: list[dict]
        links: list[dict]
        visibility: str
        validation_state: str = "pending"
        validation_summary: str = ""

    class LabRunContractModel(BaseModel):
        model_config = ConfigDict(extra="allow")

        run_id: str
        lab_type: str
        scenario_id: str
        dataset_refs: list[str]
        parameter_set: dict
        engine: str
        outputs: list[dict] = Field(default_factory=list)
        metrics: dict = Field(default_factory=dict)
        status: str = "queued"
        published: bool = False
        uncertainty_summary: str = "not_assessed"
        confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
else:
    DatasetManifestModel = None
    AchillesActionEnvelopeModel = None
    WorkspacePublishManifestModel = None
    LabRunContractModel = None


def validate_contract_payload(contract_kind: str, payload: dict) -> dict:
    model_map = {
        "dataset_manifest": DatasetManifestModel,
        "action_envelope": AchillesActionEnvelopeModel,
        "publish_manifest": WorkspacePublishManifestModel,
        "lab_run": LabRunContractModel,
    }
    model = model_map.get(contract_kind)
    if model is None:
        return {
            "contract_kind": contract_kind,
            "engine": "python_fallback",
            "valid": isinstance(payload, dict),
            "errors": [] if isinstance(payload, dict) else ["payload_not_dict"],
            "validated_payload": dict(payload) if isinstance(payload, dict) else {},
        }
    try:
        validated = model.model_validate(payload)
        return {
            "contract_kind": contract_kind,
            "engine": "pydantic",
            "valid": True,
            "errors": [],
            "validated_payload": validated.model_dump(),
        }
    except ValidationError as exc:
        return {
            "contract_kind": contract_kind,
            "engine": "pydantic",
            "valid": False,
            "errors": [str(exc)],
            "validated_payload": dict(payload),
        }
