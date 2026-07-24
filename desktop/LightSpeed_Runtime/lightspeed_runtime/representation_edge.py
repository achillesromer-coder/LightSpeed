from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterable, Mapping

from lightspeed_runtime.operational_store import default_operational_db_path


FEATURE_FLAG = "LIGHTSPEED_REPRESENTATION_EDGE_ENABLED"
MIGRATION_ID = "representation-edge-v1"
SCHEMA_VERSION = "cognigrex-representation-edge-v1"
REVIEW_SCHEMA = "lightspeed-go-representation-review-v1"
DECISION_SCHEMA = "lightspeed-go-representation-decision-v1"
PROMOTION_SCHEMA = "lightspeed-drive-promotion-contract-v1"

TRUE_VALUES = frozenset({"1", "true", "yes", "on", "enabled"})
OBJECT_STATES = frozenset({"candidate", "active", "held", "superseded", "conflict"})
REPRESENTATION_STATES = frozenset(
    {"candidate", "active", "provisional", "held", "superseded", "missing", "conflict", "rejected"}
)
CONFIDENCE_CLASSES = frozenset({"unknown", "low", "moderate", "high", "confirmed"})
RELATIONS = frozenset(
    {
        "derived_from",
        "measured_by",
        "recorded_in",
        "visualizes",
        "parameterizes",
        "simulates",
        "recommends_for",
        "supersedes",
        "digital_twin_of",
        "same_as_candidate",
        "contradicts",
        "corroborates",
        "depends_on",
        "bounded_by",
    }
)
EVIDENCE_REQUIRED_RELATIONS = RELATIONS - {"depends_on", "bounded_by"}
LOCATOR_TYPES = frozenset(
    {
        "drive_file",
        "drive_workbook",
        "drive_workbook_row",
        "git_file",
        "local_receipt",
        "local_project_registry",
        "logical",
        "missing",
    }
)
DECISIONS = frozenset(
    {"approve", "provisional_approve", "hold", "reject", "request_evidence", "supersede"}
)
OWNER_ONLY_DECISIONS = frozenset({"approve", "supersede"})
OWNER_ACTORS = frozenset({"nathaniel", "nathaniel bouwer", "owner"})
ACHILLES_ACTORS = frozenset({"achilles", "nathaniel", "nathaniel bouwer", "owner"})
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
DEFAULT_CONFIDENCE_THRESHOLDS = {
    "low_upper": 0.35,
    "moderate_upper": 0.70,
    "high_upper": 0.95,
}

TABLES = (
    "canonical_objects",
    "object_identifiers",
    "horizons",
    "evidence_bundles",
    "object_representations",
    "representation_edges",
    "representation_review_packets",
    "representation_decisions",
    "drive_promotion_jobs",
)


class RepresentationEdgeDisabled(RuntimeError):
    """Raised when the disabled-by-default representation edge is invoked."""


class RepresentationValidationError(ValueError):
    """Raised when an object, representation, edge, or promotion is unsafe."""


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def content_sha256(value: Any) -> str:
    payload = value if isinstance(value, bytes) else canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def stable_graph_payload(value: Any) -> Any:
    """Remove operational audit timestamps before hashing graph semantics."""
    if isinstance(value, dict):
        return {
            key: stable_graph_payload(item)
            for key, item in value.items()
            if key not in {"created_utc", "updated_utc"}
        }
    if isinstance(value, list):
        return [stable_graph_payload(item) for item in value]
    return value


def feature_enabled(environ: Mapping[str, str] | None = None) -> bool:
    source = os.environ if environ is None else environ
    return str(source.get(FEATURE_FLAG, "")).strip().casefold() in TRUE_VALUES


def classify_confidence(
    value: float | None,
    *,
    thresholds: Mapping[str, float] | None = None,
    confirmed: bool = False,
) -> str:
    if value is None:
        return "unknown"
    numeric = float(value)
    if not 0.0 <= numeric <= 1.0:
        raise RepresentationValidationError("confidence must be between 0 and 1")
    if confirmed:
        return "confirmed"
    rules = {**DEFAULT_CONFIDENCE_THRESHOLDS, **dict(thresholds or {})}
    if numeric < float(rules["low_upper"]):
        return "low"
    if numeric < float(rules["moderate_upper"]):
        return "moderate"
    return "high"


def _json(value: Any) -> str:
    return canonical_json(value if value is not None else {})


def _loaded(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _append_jsonl_once(path: Path, payload: dict[str, Any], identity_field: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    identity = str(payload.get(identity_field) or "")
    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and str(row.get(identity_field) or "") == identity:
                return False
    with path.open("a", encoding="utf-8") as stream:
        stream.write(canonical_json(payload) + "\n")
    return True


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def default_review_paths(shell_root: Path) -> tuple[Path, Path, Path]:
    runtime_exports = (
        Path(shell_root)
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "runtime_exports"
    )
    return (
        runtime_exports / "go_review_queue.jsonl",
        runtime_exports / "go_review_decisions.jsonl",
        runtime_exports / "drive_outbox",
    )


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS representation_schema_migrations (
    migration_id TEXT PRIMARY KEY,
    applied_utc TEXT NOT NULL,
    schema_sha256 TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS canonical_objects (
    object_id TEXT PRIMARY KEY,
    object_type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    authority TEXT NOT NULL,
    identity_confidence_numeric REAL NOT NULL
        CHECK(identity_confidence_numeric >= 0.0 AND identity_confidence_numeric <= 1.0),
    identity_confidence_class TEXT NOT NULL
        CHECK(identity_confidence_class IN ('unknown','low','moderate','high','confirmed')),
    state TEXT NOT NULL
        CHECK(state IN ('candidate','active','held','superseded','conflict')),
    created_utc TEXT NOT NULL,
    updated_utc TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS object_identifiers (
    identifier_id TEXT PRIMARY KEY,
    object_id TEXT NOT NULL,
    namespace TEXT NOT NULL COLLATE NOCASE,
    identifier_value TEXT NOT NULL COLLATE NOCASE,
    identifier_type TEXT NOT NULL
        CHECK(identifier_type IN (
            'internal','empirical_authority','usi','mission_unit','display_name',
            'alias','historical','classification'
        )),
    authority TEXT NOT NULL,
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK(is_primary IN (0,1)),
    state TEXT NOT NULL,
    valid_from_utc TEXT,
    valid_to_utc TEXT,
    FOREIGN KEY(object_id) REFERENCES canonical_objects(object_id) ON DELETE CASCADE,
    UNIQUE(namespace, identifier_value)
);
CREATE INDEX IF NOT EXISTS idx_object_identifiers_object
    ON object_identifiers(object_id, is_primary, namespace);

CREATE TABLE IF NOT EXISTS horizons (
    horizon_id TEXT PRIMARY KEY,
    parent_horizon_id TEXT,
    name TEXT NOT NULL,
    horizon_type TEXT NOT NULL,
    objective TEXT NOT NULL,
    assumptions_json TEXT NOT NULL,
    constraints_json TEXT NOT NULL,
    accepted_inputs_json TEXT NOT NULL,
    input_set_sha256 TEXT NOT NULL,
    sensitivity_summary_json TEXT NOT NULL,
    state TEXT NOT NULL,
    valid_from_utc TEXT,
    valid_to_utc TEXT,
    created_utc TEXT NOT NULL,
    updated_utc TEXT NOT NULL,
    FOREIGN KEY(parent_horizon_id) REFERENCES horizons(horizon_id)
);

CREATE TABLE IF NOT EXISTS evidence_bundles (
    evidence_bundle_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    state TEXT NOT NULL,
    evidence_items_json TEXT NOT NULL,
    independence_group_count INTEGER NOT NULL DEFAULT 0,
    duplicate_reference_count INTEGER NOT NULL DEFAULT 0,
    source_weight_summary_json TEXT NOT NULL,
    confidence_effect REAL NOT NULL DEFAULT 0.0,
    claim_boundary TEXT NOT NULL,
    created_utc TEXT NOT NULL,
    updated_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS object_representations (
    representation_id TEXT PRIMARY KEY,
    object_id TEXT NOT NULL,
    representation_type TEXT NOT NULL,
    locator_type TEXT NOT NULL,
    locator_json TEXT NOT NULL,
    content_sha256 TEXT,
    schema_id TEXT,
    source_authority TEXT NOT NULL,
    confidence_numeric REAL NOT NULL
        CHECK(confidence_numeric >= 0.0 AND confidence_numeric <= 1.0),
    confidence_class TEXT NOT NULL
        CHECK(confidence_class IN ('unknown','low','moderate','high','confirmed')),
    evidence_class TEXT NOT NULL,
    valid_from_utc TEXT,
    valid_to_utc TEXT,
    horizon_id TEXT,
    state TEXT NOT NULL
        CHECK(state IN (
            'candidate','active','provisional','held','superseded',
            'missing','conflict','rejected'
        )),
    claim_boundary TEXT NOT NULL,
    created_utc TEXT NOT NULL,
    updated_utc TEXT NOT NULL,
    FOREIGN KEY(object_id) REFERENCES canonical_objects(object_id) ON DELETE CASCADE,
    FOREIGN KEY(horizon_id) REFERENCES horizons(horizon_id)
);
CREATE INDEX IF NOT EXISTS idx_representations_object
    ON object_representations(object_id, representation_type, state);

CREATE TABLE IF NOT EXISTS representation_edges (
    edge_id TEXT PRIMARY KEY,
    from_representation_id TEXT NOT NULL,
    to_representation_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    evidence_bundle_id TEXT,
    confidence_numeric REAL NOT NULL
        CHECK(confidence_numeric >= 0.0 AND confidence_numeric <= 1.0),
    confidence_class TEXT NOT NULL
        CHECK(confidence_class IN ('unknown','low','moderate','high','confirmed')),
    claim_boundary TEXT NOT NULL,
    created_by_floor TEXT NOT NULL,
    review_state TEXT NOT NULL,
    owner_decision_id TEXT,
    created_utc TEXT NOT NULL,
    updated_utc TEXT NOT NULL,
    FOREIGN KEY(from_representation_id)
        REFERENCES object_representations(representation_id) ON DELETE CASCADE,
    FOREIGN KEY(to_representation_id)
        REFERENCES object_representations(representation_id) ON DELETE CASCADE,
    FOREIGN KEY(evidence_bundle_id)
        REFERENCES evidence_bundles(evidence_bundle_id)
);
CREATE INDEX IF NOT EXISTS idx_representation_edges_from
    ON representation_edges(from_representation_id, relation);
CREATE INDEX IF NOT EXISTS idx_representation_edges_to
    ON representation_edges(to_representation_id, relation);

CREATE TABLE IF NOT EXISTS representation_review_packets (
    review_id TEXT PRIMARY KEY,
    object_id TEXT NOT NULL,
    graph_sha256 TEXT NOT NULL,
    state TEXT NOT NULL,
    review_stage TEXT NOT NULL,
    allowed_decisions_json TEXT NOT NULL,
    packet_json TEXT NOT NULL,
    created_utc TEXT NOT NULL,
    updated_utc TEXT NOT NULL,
    FOREIGN KEY(object_id) REFERENCES canonical_objects(object_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS representation_decisions (
    decision_id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL,
    graph_sha256 TEXT NOT NULL,
    scope TEXT NOT NULL,
    decision TEXT NOT NULL,
    actor TEXT NOT NULL,
    edge_ids_json TEXT NOT NULL,
    note TEXT NOT NULL,
    applies_external_write INTEGER NOT NULL DEFAULT 0 CHECK(applies_external_write IN (0,1)),
    created_utc TEXT NOT NULL,
    FOREIGN KEY(review_id) REFERENCES representation_review_packets(review_id)
);

CREATE TABLE IF NOT EXISTS drive_promotion_jobs (
    promotion_id TEXT PRIMARY KEY,
    object_id TEXT NOT NULL,
    review_id TEXT NOT NULL,
    state TEXT NOT NULL,
    expected_parent TEXT,
    expected_metadata_json TEXT NOT NULL,
    graph_sha256 TEXT NOT NULL,
    decision_id TEXT,
    drive_object_id TEXT,
    drive_revision_id TEXT,
    immutable_file_sha256 TEXT,
    normalized_content_sha256 TEXT,
    readback_json TEXT NOT NULL DEFAULT '{}',
    created_utc TEXT NOT NULL,
    updated_utc TEXT NOT NULL,
    FOREIGN KEY(object_id) REFERENCES canonical_objects(object_id),
    FOREIGN KEY(review_id) REFERENCES representation_review_packets(review_id)
);
"""


ROLLBACK_SQL = """
DROP TABLE IF EXISTS drive_promotion_jobs;
DROP TABLE IF EXISTS representation_decisions;
DROP TABLE IF EXISTS representation_review_packets;
DROP TABLE IF EXISTS representation_edges;
DROP TABLE IF EXISTS object_representations;
DROP TABLE IF EXISTS evidence_bundles;
DROP TABLE IF EXISTS horizons;
DROP TABLE IF EXISTS object_identifiers;
DROP TABLE IF EXISTS canonical_objects;
DELETE FROM representation_schema_migrations WHERE migration_id = 'representation-edge-v1';
"""


class RepresentationEdgeStore:
    """Feature-gated relationship graph inside the one LightSpeed SQLite database."""

    def __init__(self, database_path: Path, *, enabled: bool | None = None):
        self.database_path = Path(database_path)
        self.enabled = feature_enabled() if enabled is None else bool(enabled)

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise RepresentationEdgeDisabled(
                f"{FEATURE_FLAG}=1 is required; the representation edge is disabled by default"
            )

    def _connect(self) -> sqlite3.Connection:
        self._require_enabled()
        if not self.database_path.is_file():
            raise FileNotFoundError(
                f"Existing unified SQLite database is required: {self.database_path}"
            )
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def status(self) -> dict[str, Any]:
        if not self.enabled:
            return {
                "enabled": False,
                "feature_flag": FEATURE_FLAG,
                "database_path": str(self.database_path),
                "database_exists": self.database_path.is_file(),
                "migration_applied": False,
            }
        if not self.database_path.is_file():
            return {
                "enabled": True,
                "feature_flag": FEATURE_FLAG,
                "database_path": str(self.database_path),
                "database_exists": False,
                "migration_applied": False,
            }
        with self._connect() as connection:
            migration_table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='representation_schema_migrations'"
            ).fetchone()
            applied = False
            if migration_table:
                applied = connection.execute(
                    "SELECT 1 FROM representation_schema_migrations WHERE migration_id=?",
                    (MIGRATION_ID,),
                ).fetchone() is not None
            counts = {}
            if applied:
                for table in TABLES:
                    counts[table] = int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        return {
            "enabled": True,
            "feature_flag": FEATURE_FLAG,
            "database_path": str(self.database_path),
            "database_exists": True,
            "migration_applied": applied,
            "counts": counts,
        }

    def apply_migration(self) -> dict[str, Any]:
        self._require_enabled()
        schema_hash = content_sha256(MIGRATION_SQL)
        with self._connect() as connection:
            connection.executescript("BEGIN IMMEDIATE;\n" + MIGRATION_SQL)
            decision_columns = {
                str(row["name"])
                for row in connection.execute(
                    "PRAGMA table_info(representation_decisions)"
                ).fetchall()
            }
            if "graph_sha256" not in decision_columns:
                connection.execute(
                    "ALTER TABLE representation_decisions ADD COLUMN graph_sha256 TEXT"
                )
            connection.execute(
                """
                INSERT INTO representation_schema_migrations (
                    migration_id, applied_utc, schema_sha256
                ) VALUES (?, ?, ?)
                ON CONFLICT(migration_id) DO UPDATE SET schema_sha256=excluded.schema_sha256
                """,
                (MIGRATION_ID, utc_now_iso(), schema_hash),
            )
        return {"migration_id": MIGRATION_ID, "schema_sha256": schema_hash, "applied": True}

    def rollback_migration(self) -> dict[str, Any]:
        self._require_enabled()
        with self._connect() as connection:
            connection.executescript("BEGIN IMMEDIATE;\n" + ROLLBACK_SQL)
        return {
            "migration_id": MIGRATION_ID,
            "rolled_back": True,
            "retained_receipt_history": True,
            "retained_external_receipt_history": True,
        }

    def _upsert_object(self, value: dict[str, Any]) -> None:
        confidence = float(value["identity_confidence_numeric"])
        confidence_class = str(value["identity_confidence_class"])
        state = str(value["state"])
        if not 0.0 <= confidence <= 1.0:
            raise RepresentationValidationError("identity confidence must be between 0 and 1")
        if confidence_class not in CONFIDENCE_CLASSES:
            raise RepresentationValidationError("unsupported identity confidence class")
        if state not in OBJECT_STATES:
            raise RepresentationValidationError("unsupported object state")
        stamp = utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO canonical_objects (
                    object_id, object_type, canonical_name, display_name, description,
                    authority, identity_confidence_numeric, identity_confidence_class,
                    state, created_utc, updated_utc, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(object_id) DO UPDATE SET
                    object_type=excluded.object_type,
                    canonical_name=excluded.canonical_name,
                    display_name=excluded.display_name,
                    description=excluded.description,
                    authority=excluded.authority,
                    identity_confidence_numeric=excluded.identity_confidence_numeric,
                    identity_confidence_class=excluded.identity_confidence_class,
                    state=excluded.state,
                    updated_utc=excluded.updated_utc,
                    metadata_json=excluded.metadata_json
                """,
                (
                    value["object_id"],
                    value["object_type"],
                    value["canonical_name"],
                    value.get("display_name") or value["canonical_name"],
                    value.get("description") or "",
                    value["authority"],
                    confidence,
                    confidence_class,
                    state,
                    value.get("created_utc") or stamp,
                    stamp,
                    _json(value.get("metadata")),
                ),
            )

    def _collision_review(
        self,
        *,
        object_id: str,
        namespace: str,
        identifier_value: str,
        existing_object_id: str,
    ) -> str:
        review_id = (
            "LSGO-REVIEW-"
            + hashlib.sha256(
                f"identifier-collision|{namespace.casefold()}|{identifier_value.casefold()}".encode("utf-8")
            ).hexdigest()[:16].upper()
        )
        stamp = utc_now_iso()
        packet = {
            "schema_version": REVIEW_SCHEMA,
            "review_id": review_id,
            "event_type": "identifier_collision",
            "object_id": object_id,
            "existing_object_id": existing_object_id,
            "namespace": namespace,
            "identifier_value": identifier_value,
            "state": "conflict",
            "allowed_decisions": sorted(DECISIONS),
            "automatic_merge": False,
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO representation_review_packets (
                    review_id, object_id, graph_sha256, state, review_stage,
                    allowed_decisions_json, packet_json, created_utc, updated_utc
                ) VALUES (?, ?, ?, 'conflict', 'identity', ?, ?, ?, ?)
                """,
                (
                    review_id,
                    object_id,
                    content_sha256(packet),
                    _json(sorted(DECISIONS)),
                    _json(packet),
                    stamp,
                    stamp,
                ),
            )
        return review_id

    def add_identifier(self, value: dict[str, Any]) -> dict[str, Any]:
        stamp = utc_now_iso()
        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT object_id, identifier_id
                FROM object_identifiers
                WHERE namespace=? AND identifier_value=?
                """,
                (value["namespace"], value["identifier_value"]),
            ).fetchone()
            if existing and str(existing["object_id"]) != str(value["object_id"]):
                review_id = self._collision_review(
                    object_id=str(value["object_id"]),
                    namespace=str(value["namespace"]),
                    identifier_value=str(value["identifier_value"]),
                    existing_object_id=str(existing["object_id"]),
                )
                return {"inserted": False, "collision": True, "review_id": review_id}
            connection.execute(
                """
                INSERT INTO object_identifiers (
                    identifier_id, object_id, namespace, identifier_value,
                    identifier_type, authority, is_primary, state,
                    valid_from_utc, valid_to_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(identifier_id) DO UPDATE SET
                    authority=excluded.authority,
                    is_primary=excluded.is_primary,
                    state=excluded.state,
                    valid_from_utc=excluded.valid_from_utc,
                    valid_to_utc=excluded.valid_to_utc
                """,
                (
                    value["identifier_id"],
                    value["object_id"],
                    value["namespace"],
                    value["identifier_value"],
                    value["identifier_type"],
                    value["authority"],
                    int(bool(value.get("is_primary"))),
                    value.get("state") or "active",
                    value.get("valid_from_utc") or stamp,
                    value.get("valid_to_utc"),
                ),
            )
        return {"inserted": not bool(existing), "collision": False}

    def _upsert_horizon(self, value: dict[str, Any]) -> None:
        input_hash = str(value["input_set_sha256"]).casefold()
        self._validate_sha256(input_hash, required=True)
        stamp = utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO horizons (
                    horizon_id, parent_horizon_id, name, horizon_type, objective,
                    assumptions_json, constraints_json, accepted_inputs_json,
                    input_set_sha256, sensitivity_summary_json, state,
                    valid_from_utc, valid_to_utc, created_utc, updated_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(horizon_id) DO UPDATE SET
                    parent_horizon_id=excluded.parent_horizon_id,
                    name=excluded.name,
                    horizon_type=excluded.horizon_type,
                    objective=excluded.objective,
                    assumptions_json=excluded.assumptions_json,
                    constraints_json=excluded.constraints_json,
                    accepted_inputs_json=excluded.accepted_inputs_json,
                    input_set_sha256=excluded.input_set_sha256,
                    sensitivity_summary_json=excluded.sensitivity_summary_json,
                    state=excluded.state,
                    valid_to_utc=excluded.valid_to_utc,
                    updated_utc=excluded.updated_utc
                """,
                (
                    value["horizon_id"],
                    value.get("parent_horizon_id"),
                    value["name"],
                    value["horizon_type"],
                    value["objective"],
                    _json(value.get("assumptions")),
                    _json(value.get("constraints")),
                    _json(value.get("accepted_inputs")),
                    input_hash,
                    _json(value.get("sensitivity_summary")),
                    value.get("state") or "candidate",
                    value.get("valid_from_utc") or stamp,
                    value.get("valid_to_utc"),
                    value.get("created_utc") or stamp,
                    stamp,
                ),
            )

    @staticmethod
    def evidence_confidence_effect(
        evidence_items: Iterable[dict[str, Any]],
        *,
        independent_increment: float = 0.05,
    ) -> dict[str, Any]:
        independent_groups: set[str] = set()
        duplicates = 0
        outliers = 0
        for item in evidence_items:
            if bool(item.get("duplicate")):
                duplicates += 1
                continue
            if bool(item.get("outlier")):
                outliers += 1
            if str(item.get("independence_status") or "") != "independent":
                continue
            fingerprint = str(item.get("underlying_source_fingerprint") or "").strip()
            if fingerprint:
                independent_groups.add(fingerprint)
        increase = max(0, len(independent_groups) - 1) * max(0.0, float(independent_increment))
        return {
            "independence_group_count": len(independent_groups),
            "duplicate_reference_count": duplicates,
            "outlier_count": outliers,
            "confidence_effect": min(increase, 1.0),
        }

    def _upsert_evidence_bundle(self, value: dict[str, Any]) -> None:
        items = list(value.get("evidence_items") or [])
        calculated = self.evidence_confidence_effect(
            items,
            independent_increment=float(value.get("independent_increment") or 0.05),
        )
        stamp = utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO evidence_bundles (
                    evidence_bundle_id, title, state, evidence_items_json,
                    independence_group_count, duplicate_reference_count,
                    source_weight_summary_json, confidence_effect, claim_boundary,
                    created_utc, updated_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(evidence_bundle_id) DO UPDATE SET
                    title=excluded.title,
                    state=excluded.state,
                    evidence_items_json=excluded.evidence_items_json,
                    independence_group_count=excluded.independence_group_count,
                    duplicate_reference_count=excluded.duplicate_reference_count,
                    source_weight_summary_json=excluded.source_weight_summary_json,
                    confidence_effect=excluded.confidence_effect,
                    claim_boundary=excluded.claim_boundary,
                    updated_utc=excluded.updated_utc
                """,
                (
                    value["evidence_bundle_id"],
                    value["title"],
                    value.get("state") or "candidate",
                    _json(items),
                    int(value.get("independence_group_count", calculated["independence_group_count"])),
                    int(value.get("duplicate_reference_count", calculated["duplicate_reference_count"])),
                    _json(value.get("source_weight_summary") or calculated),
                    float(value.get("confidence_effect", calculated["confidence_effect"])),
                    value.get("claim_boundary") or "",
                    value.get("created_utc") or stamp,
                    stamp,
                ),
            )

    @staticmethod
    def _validate_sha256(value: str | None, *, required: bool = False) -> None:
        if not value and not required:
            return
        if not value or not SHA256_PATTERN.fullmatch(str(value)):
            raise RepresentationValidationError("content hash must be a complete SHA-256")

    @staticmethod
    def _validate_locator(
        *,
        representation_type: str,
        locator_type: str,
        locator: dict[str, Any],
        state: str,
        content_hash: str | None,
        claim_boundary: str,
    ) -> None:
        if locator_type not in LOCATOR_TYPES:
            raise RepresentationValidationError(f"unsupported locator type: {locator_type}")
        if locator_type == "drive_workbook_row":
            if not locator.get("drive_file_id") or not locator.get("sheet_name"):
                raise RepresentationValidationError("workbook row requires Drive file ID and sheet")
            if not locator.get("stable_key"):
                if state != "missing" or locator.get("missing_state") != "awaiting_stable_workbook_key":
                    raise RepresentationValidationError(
                        "workbook row without stable key must remain missing/awaiting_stable_workbook_key"
                    )
            if locator.get("current_row_number") and not (
                locator.get("stable_key") or locator.get("content_key")
            ):
                raise RepresentationValidationError("current row number alone is not identity")
        if representation_type in {"visual", "mesh"} and state != "missing":
            illustrative = locator.get("evidence_class") == "illustrative_only"
            if illustrative and (not content_hash or not claim_boundary):
                raise RepresentationValidationError(
                    "illustrative visual requires input hash and explicit claim boundary"
                )
        if representation_type == "recommendation" and not locator.get("next_highest_value_question"):
            raise RepresentationValidationError("recommendation requires next highest-value question")

    def _upsert_representation(self, value: dict[str, Any]) -> None:
        state = str(value["state"])
        confidence_class = str(value["confidence_class"])
        confidence = float(value["confidence_numeric"])
        locator = dict(value.get("locator") or {})
        locator_type = str(value["locator_type"])
        content_hash = (
            str(value["content_sha256"]).casefold() if value.get("content_sha256") else None
        )
        claim_boundary = str(value.get("claim_boundary") or "")
        representation_type = str(value["representation_type"])
        if state not in REPRESENTATION_STATES:
            raise RepresentationValidationError("unsupported representation state")
        if confidence_class not in CONFIDENCE_CLASSES or not 0.0 <= confidence <= 1.0:
            raise RepresentationValidationError("invalid representation confidence")
        self._validate_sha256(content_hash)
        if representation_type == "recommendation" and not value.get("horizon_id"):
            raise RepresentationValidationError("recommendation requires a horizon")
        if (
            state == "active"
            and "held" in str(value.get("evidence_class") or "").casefold()
        ):
            raise RepresentationValidationError("held evidence cannot become an active claim")
        if (
            representation_type in {"equation", "model"}
            and str(value.get("evidence_class") or "").casefold() == "empirical_capability"
        ):
            raise RepresentationValidationError(
                "mathematics cannot promote empirical capability confidence by itself"
            )
        self._validate_locator(
            representation_type=representation_type,
            locator_type=locator_type,
            locator=locator,
            state=state,
            content_hash=content_hash,
            claim_boundary=claim_boundary,
        )
        stamp = utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO object_representations (
                    representation_id, object_id, representation_type, locator_type,
                    locator_json, content_sha256, schema_id, source_authority,
                    confidence_numeric, confidence_class, evidence_class,
                    valid_from_utc, valid_to_utc, horizon_id, state,
                    claim_boundary, created_utc, updated_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(representation_id) DO UPDATE SET
                    object_id=excluded.object_id,
                    representation_type=excluded.representation_type,
                    locator_type=excluded.locator_type,
                    locator_json=excluded.locator_json,
                    content_sha256=excluded.content_sha256,
                    schema_id=excluded.schema_id,
                    source_authority=excluded.source_authority,
                    confidence_numeric=excluded.confidence_numeric,
                    confidence_class=excluded.confidence_class,
                    evidence_class=excluded.evidence_class,
                    valid_to_utc=excluded.valid_to_utc,
                    horizon_id=excluded.horizon_id,
                    state=excluded.state,
                    claim_boundary=excluded.claim_boundary,
                    updated_utc=excluded.updated_utc
                """,
                (
                    value["representation_id"],
                    value["object_id"],
                    representation_type,
                    locator_type,
                    _json(locator),
                    content_hash,
                    value.get("schema_id"),
                    value.get("source_authority") or "unknown",
                    confidence,
                    confidence_class,
                    value.get("evidence_class") or "unclassified",
                    value.get("valid_from_utc") or stamp,
                    value.get("valid_to_utc"),
                    value.get("horizon_id"),
                    state,
                    claim_boundary,
                    value.get("created_utc") or stamp,
                    stamp,
                ),
            )

    def _upsert_edge(self, value: dict[str, Any]) -> None:
        relation = str(value["relation"])
        evidence_bundle_id = value.get("evidence_bundle_id")
        if relation not in RELATIONS:
            raise RepresentationValidationError(f"unsupported relation: {relation}")
        if relation in EVIDENCE_REQUIRED_RELATIONS and not evidence_bundle_id:
            raise RepresentationValidationError(f"{relation} requires an evidence bundle")
        if value["from_representation_id"] == value["to_representation_id"]:
            raise RepresentationValidationError("self-referential representation edge is invalid")
        confidence = float(value["confidence_numeric"])
        confidence_class = str(value["confidence_class"])
        if not 0.0 <= confidence <= 1.0 or confidence_class not in CONFIDENCE_CLASSES:
            raise RepresentationValidationError("invalid edge confidence")
        stamp = utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO representation_edges (
                    edge_id, from_representation_id, to_representation_id, relation,
                    evidence_bundle_id, confidence_numeric, confidence_class,
                    claim_boundary, created_by_floor, review_state,
                    owner_decision_id, created_utc, updated_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(edge_id) DO UPDATE SET
                    evidence_bundle_id=excluded.evidence_bundle_id,
                    confidence_numeric=excluded.confidence_numeric,
                    confidence_class=excluded.confidence_class,
                    claim_boundary=excluded.claim_boundary,
                    review_state=excluded.review_state,
                    owner_decision_id=excluded.owner_decision_id,
                    updated_utc=excluded.updated_utc
                """,
                (
                    value["edge_id"],
                    value["from_representation_id"],
                    value["to_representation_id"],
                    relation,
                    evidence_bundle_id,
                    confidence,
                    confidence_class,
                    value.get("claim_boundary") or "",
                    value.get("created_by_floor") or "Neo",
                    value.get("review_state") or "pending",
                    value.get("owner_decision_id"),
                    value.get("created_utc") or stamp,
                    stamp,
                ),
            )

    def seed_proof_graphs(
        self,
        *,
        review_queue_path: Path,
        decision_path: Path,
        local_outbox: Path,
    ) -> dict[str, Any]:
        self.apply_migration()
        proofs = _proof_definitions()
        for proof in proofs:
            for value in proof["objects"]:
                self._upsert_object(value)
            for value in proof["identifiers"]:
                result = self.add_identifier(value)
                if result.get("collision"):
                    raise RepresentationValidationError(
                        f"identifier collision while seeding {value['identifier_id']}: {result['review_id']}"
                    )
            for value in proof.get("horizons") or []:
                self._upsert_horizon(value)
            for value in proof.get("evidence_bundles") or []:
                self._upsert_evidence_bundle(value)
            for value in proof["representations"]:
                self._upsert_representation(value)
            for value in proof["edges"]:
                self._upsert_edge(value)

        packets = []
        promotions = []
        for object_id in ("ASPHA.0001", "engineering-twin:rfs-emff-sandbox", "de-sporte-05d89c2a"):
            packet = self._prepare_review_packet(
                object_id=object_id,
                review_queue_path=review_queue_path,
                local_outbox=local_outbox,
            )
            packets.append(packet)
            promotions.append(
                self._prepare_drive_promotion(
                    object_id=object_id,
                    review_id=packet["review_id"],
                    local_outbox=local_outbox,
                )
            )
        return {
            "schema_version": SCHEMA_VERSION,
            "objects": [value["object_id"] for proof in proofs for value in proof["objects"]],
            "graphs": [
                "ASPHA.0001",
                "engineering-twin:rfs-emff-sandbox",
                "de-sporte-05d89c2a",
            ],
            "review_packet_ids": [packet["review_id"] for packet in packets],
            "review_queue_path": str(review_queue_path),
            "decision_path": str(decision_path),
            "local_outbox": str(local_outbox),
            "promotions": promotions,
            "drive_write_executed": False,
        }

    def list_graphs(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT object_id
                FROM canonical_objects
                WHERE object_id IN (
                    'ASPHA.0001',
                    'engineering-twin:rfs-emff-sandbox',
                    'de-sporte-05d89c2a'
                )
                ORDER BY object_id
                """
            ).fetchall()
        return [self.graph(str(row["object_id"])) for row in rows]

    def propose_horizon(
        self,
        *,
        parent_horizon_id: str,
        accepted_inputs: dict[str, Any],
        material_change: bool,
        changed_engines: Iterable[str] = (),
        resource_state: str = "normal",
    ) -> dict[str, Any]:
        input_hash = content_sha256(accepted_inputs)
        engines = sorted({str(value).strip() for value in changed_engines if str(value).strip()})
        if not material_change:
            return {
                "horizon_id": parent_horizon_id,
                "state": "enrichment_only",
                "input_set_sha256": input_hash,
                "rerun_required": False,
                "affected_engines": [],
                "prior_rationale_preserved": True,
            }
        candidate_id = (
            f"{parent_horizon_id}:candidate:"
            + hashlib.sha256(input_hash.encode("utf-8")).hexdigest()[:12]
        )
        held = resource_state.casefold() in {"warning", "critical", "hold"}
        return {
            "horizon_id": candidate_id,
            "parent_horizon_id": parent_horizon_id,
            "state": "resource_held" if held else "candidate",
            "input_set_sha256": input_hash,
            "rerun_required": bool(engines),
            "rerun_authorized": bool(engines) and not held,
            "affected_engines": engines,
            "prior_rationale_preserved": True,
            "prior_rationale_label": "rational under the earlier accepted horizon",
        }

    @staticmethod
    def validate_controlled_unpack_manifest(
        entries: Iterable[dict[str, Any]],
        *,
        max_files: int = 5_000,
        max_total_bytes: int = 1_073_741_824,
    ) -> dict[str, Any]:
        rows = list(entries)
        if len(rows) > max_files:
            raise RepresentationValidationError("controlled unpack file-count limit exceeded")
        total = 0
        blocked: list[str] = []
        for row in rows:
            relative = str(row.get("path") or "").replace("\\", "/")
            size = int(row.get("size_bytes") or 0)
            if (
                not relative
                or relative.startswith("/")
                or re.match(r"^[A-Za-z]:", relative)
                or ".." in Path(relative).parts
            ):
                raise RepresentationValidationError("controlled unpack path traversal rejected")
            if size < 0:
                raise RepresentationValidationError("controlled unpack size is invalid")
            total += size
            lowered = relative.casefold()
            if (
                lowered.startswith(".env")
                or lowered.endswith((".pem", ".key", ".p12", ".pfx"))
                or "credential" in lowered
                or "token" in lowered
                or "id_rsa" in lowered
            ):
                blocked.append(relative)
        if total > max_total_bytes:
            raise RepresentationValidationError("controlled unpack size limit exceeded")
        if blocked:
            raise RepresentationValidationError(
                "controlled unpack secret scan rejected: " + ", ".join(blocked[:5])
            )
        return {
            "file_count": len(rows),
            "total_bytes": total,
            "path_traversal_safe": True,
            "secret_scan": "pass",
            "source_mutated": False,
        }

    @staticmethod
    def _public_locator(row: dict[str, Any]) -> dict[str, Any]:
        locator = _loaded(row.get("locator_json"), {})
        locator_type = str(row.get("locator_type") or "")
        if locator_type in {"local_receipt", "local_project_registry"}:
            return {
                "locator_type": locator_type,
                "label": locator.get("label") or locator.get("receipt_id") or "private local evidence",
                "sensitive": True,
                "path_exposed": False,
            }
        safe_keys = {
            "drive_file_id",
            "drive_revision_id",
            "normalized_content_sha256",
            "sheet_name",
            "stable_key",
            "content_key",
            "current_row_number",
            "current_cell_range",
            "missing_state",
            "reason",
            "last_search",
            "next_evidence_action",
            "assigned_floor",
            "dependency_effect",
            "repository",
            "commit_sha",
            "path",
            "target_id",
            "schema_id",
            "evidence_class",
            "input_set_sha256",
            "objective",
            "next_highest_value_question",
            "classifications",
        }
        return {
            "locator_type": locator_type,
            **{key: value for key, value in locator.items() if key in safe_keys},
        }

    def graph(self, object_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            object_row = connection.execute(
                "SELECT * FROM canonical_objects WHERE object_id=?", (object_id,)
            ).fetchone()
            if object_row is None:
                raise KeyError(object_id)
            identifiers = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT identifier_id, namespace, identifier_value, identifier_type,
                           authority, is_primary, state
                    FROM object_identifiers WHERE object_id=?
                    ORDER BY is_primary DESC, namespace, identifier_value
                    """,
                    (object_id,),
                ).fetchall()
            ]
            representations = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT * FROM object_representations
                    WHERE object_id=?
                    ORDER BY representation_type, representation_id
                    """,
                    (object_id,),
                ).fetchall()
            ]
            representation_ids = [row["representation_id"] for row in representations]
            edges: list[dict[str, Any]] = []
            if representation_ids:
                placeholders = ",".join("?" for _ in representation_ids)
                edges = [
                    dict(row)
                    for row in connection.execute(
                        f"""
                        SELECT * FROM representation_edges
                        WHERE from_representation_id IN ({placeholders})
                           OR to_representation_id IN ({placeholders})
                        ORDER BY edge_id
                        """,
                        (*representation_ids, *representation_ids),
                    ).fetchall()
                ]
            horizon_ids = sorted(
                {str(row["horizon_id"]) for row in representations if row.get("horizon_id")}
            )
            horizons: list[dict[str, Any]] = []
            for horizon_id in horizon_ids:
                row = connection.execute(
                    "SELECT * FROM horizons WHERE horizon_id=?", (horizon_id,)
                ).fetchone()
                if row:
                    horizons.append(dict(row))
            review = connection.execute(
                """
                SELECT review_id, state, review_stage, graph_sha256
                FROM representation_review_packets
                WHERE object_id=? ORDER BY created_utc DESC LIMIT 1
                """,
                (object_id,),
            ).fetchone()
            decisions: list[dict[str, Any]] = []
            if review:
                decisions = [
                    dict(row)
                    for row in connection.execute(
                        """
                        SELECT decision_id, scope, decision, actor, edge_ids_json, note,
                               applies_external_write, created_utc
                        FROM representation_decisions WHERE review_id=?
                        ORDER BY created_utc
                        """,
                        (review["review_id"],),
                    ).fetchall()
                ]

        object_value = dict(object_row)
        object_value["metadata"] = _loaded(object_value.pop("metadata_json"), {})
        for row in representations:
            row["locator"] = self._public_locator(row)
            row.pop("locator_json", None)
        for row in horizons:
            row["assumptions"] = _loaded(row.pop("assumptions_json"), {})
            row["constraints"] = _loaded(row.pop("constraints_json"), {})
            row["accepted_inputs"] = _loaded(row.pop("accepted_inputs_json"), {})
            row["sensitivity_summary"] = _loaded(row.pop("sensitivity_summary_json"), {})
        for row in decisions:
            row["edge_ids"] = _loaded(row.pop("edge_ids_json"), [])

        missing = [
            {
                "representation_id": row["representation_id"],
                "type": row["representation_type"],
                **row["locator"],
                "claim_boundary": row["claim_boundary"],
            }
            for row in representations
            if row["state"] == "missing"
        ]
        conflicts = [
            {
                "edge_id": row["edge_id"],
                "from": row["from_representation_id"],
                "to": row["to_representation_id"],
                "claim_boundary": row["claim_boundary"],
            }
            for row in edges
            if row["relation"] == "contradicts" or row["review_state"] == "conflict"
        ]
        return {
            "schema_version": SCHEMA_VERSION,
            "object": object_value,
            "identifiers": identifiers,
            "representations": representations,
            "edges": edges,
            "missing": missing,
            "conflicts": conflicts,
            "horizons": horizons,
            "review": dict(review) if review else None,
            "decisions": decisions,
            "canonical_state": (
                "canonical_drive_readback_complete"
                if object_value["state"] == "active"
                else "local_candidate_pending_owner_and_drive_readback"
            ),
        }

    def _prepare_review_packet(
        self,
        *,
        object_id: str,
        review_queue_path: Path,
        local_outbox: Path,
    ) -> dict[str, Any]:
        graph = self.graph(object_id)
        graph_for_hash = {
            key: graph[key]
            for key in (
                "schema_version",
                "object",
                "identifiers",
                "representations",
                "edges",
                "missing",
                "conflicts",
                "horizons",
            )
        }
        graph_hash = content_sha256(stable_graph_payload(graph_for_hash))
        review_id = (
            "LSGO-REVIEW-"
            + hashlib.sha256(f"{SCHEMA_VERSION}|{object_id}".encode("utf-8")).hexdigest()[:16].upper()
        )
        stamp = utc_now_iso()
        next_question = next(
            (
                row["locator"].get("next_highest_value_question")
                for row in graph["representations"]
                if row["representation_type"] == "recommendation"
            ),
            "",
        )
        packet = {
            "schema_version": REVIEW_SCHEMA,
            "review_id": review_id,
            "created_utc": stamp,
            "source": "LightSpeed Desktop / canonical representation edge",
            "target": "LS GO",
            "oversight_floor": "Achilles",
            "routing_floor": "Neo",
            "owner": "Nathaniel Bouwer",
            "event_type": "canonical_representation_graph",
            "object_id": object_id,
            "title": f"Review canonical representation graph: {graph['object']['display_name']}",
            "summary": (
                f"Identity first; then {len(graph['edges'])} edges. "
                f"{len(graph['missing'])} missing links and {len(graph['conflicts'])} conflicts retained."
            ),
            "graph_sha256": graph_hash,
            "state": "pending_identity_review",
            "review_stage": "identity",
            "allowed_decisions": sorted(DECISIONS),
            "owner_only_decisions": sorted(OWNER_ONLY_DECISIONS),
            "claim_boundary": [
                row["claim_boundary"]
                for row in graph["representations"]
                if row.get("claim_boundary")
            ],
            "next_highest_value_question": next_question,
            "proposed_drive_destination": "approved canonical object-graph folder; exact parent pending review",
            "drive_writeback_mode": "local_outbox_pending_drive_sync",
            "drive_write_executed": False,
            "rollback": f"rollback migration {MIGRATION_ID}; retain review history",
            "proof_required": True,
            "public_safe": object_id != "de-sporte-05d89c2a",
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO representation_review_packets (
                    review_id, object_id, graph_sha256, state, review_stage,
                    allowed_decisions_json, packet_json, created_utc, updated_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(review_id) DO UPDATE SET
                    state=CASE
                        WHEN representation_review_packets.graph_sha256=excluded.graph_sha256
                        THEN representation_review_packets.state
                        ELSE 'pending_identity_review'
                    END,
                    review_stage=CASE
                        WHEN representation_review_packets.graph_sha256=excluded.graph_sha256
                        THEN representation_review_packets.review_stage
                        ELSE 'identity'
                    END,
                    graph_sha256=excluded.graph_sha256,
                    allowed_decisions_json=excluded.allowed_decisions_json,
                    packet_json=excluded.packet_json,
                    updated_utc=excluded.updated_utc
                """,
                (
                    review_id,
                    object_id,
                    graph_hash,
                    packet["state"],
                    packet["review_stage"],
                    _json(packet["allowed_decisions"]),
                    _json(packet),
                    stamp,
                    stamp,
                ),
            )
        _append_jsonl_once(review_queue_path, packet, "review_id")
        _write_json(local_outbox / f"{review_id}.json", packet)
        return packet

    def list_reviews(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT packet_json, state, review_stage, graph_sha256
                FROM representation_review_packets
                ORDER BY created_utc
                """
            ).fetchall()
        result = []
        for row in rows:
            packet = _loaded(row["packet_json"], {})
            packet.update(
                {
                    "state": row["state"],
                    "review_stage": row["review_stage"],
                    "graph_sha256": row["graph_sha256"],
                }
            )
            result.append(packet)
        return result

    def list_promotions(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT promotion_id, object_id, review_id, state, expected_parent,
                       expected_metadata_json, graph_sha256, decision_id,
                       drive_object_id, drive_revision_id, immutable_file_sha256,
                       normalized_content_sha256, readback_json, created_utc, updated_utc
                FROM drive_promotion_jobs
                ORDER BY object_id
                """
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            value = dict(row)
            value["expected_metadata"] = _loaded(value.pop("expected_metadata_json"), {})
            value["readback"] = _loaded(value.pop("readback_json"), {})
            value["drive_write_executed"] = False
            value["canonical"] = value["state"] == "canonical_drive_readback_complete"
            result.append(value)
        return result

    def record_decision(
        self,
        *,
        review_id: str,
        decision: str,
        actor: str,
        scope: str,
        note: str,
        edge_ids: Iterable[str],
        decision_path: Path,
        local_outbox: Path,
    ) -> dict[str, Any]:
        decision = decision.strip().casefold()
        actor_key = actor.strip().casefold()
        scope = scope.strip().casefold()
        if decision not in DECISIONS:
            raise RepresentationValidationError("unsupported review decision")
        if scope not in {"identity", "edges"}:
            raise RepresentationValidationError("decision scope must be identity or edges")
        if decision in OWNER_ONLY_DECISIONS and actor_key not in OWNER_ACTORS:
            raise PermissionError("final approval and supersession require Nathaniel")
        if actor_key not in ACHILLES_ACTORS:
            raise PermissionError("Nathaniel or Achilles review authority is required")
        edge_ids = sorted({str(value).strip() for value in edge_ids if str(value).strip()})
        with self._connect() as connection:
            review = connection.execute(
                "SELECT * FROM representation_review_packets WHERE review_id=?",
                (review_id,),
            ).fetchone()
            if review is None:
                raise KeyError(review_id)
            if scope == "edges":
                identity = connection.execute(
                    """
                    SELECT 1 FROM representation_decisions
                    WHERE review_id=? AND scope='identity'
                      AND decision IN ('approve','provisional_approve')
                      AND graph_sha256=?
                    LIMIT 1
                    """,
                    (review_id, review["graph_sha256"]),
                ).fetchone()
                if identity is None:
                    raise RepresentationValidationError("identity review must precede edge review")
                if not edge_ids:
                    raise RepresentationValidationError("edge review requires bounded edge IDs")
                placeholders = ",".join("?" for _ in edge_ids)
                known = connection.execute(
                    f"SELECT COUNT(*) FROM representation_edges WHERE edge_id IN ({placeholders})",
                    edge_ids,
                ).fetchone()[0]
                if int(known) != len(edge_ids):
                    raise RepresentationValidationError("edge decision contains unknown edge ID")
            stamp = utc_now_iso()
            seed = canonical_json(
                {
                    "review_id": review_id,
                    "decision": decision,
                    "actor": actor,
                    "scope": scope,
                    "edge_ids": edge_ids,
                    "created_utc": stamp,
                }
            )
            decision_id = "LSGO-DECISION-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16].upper()
            receipt = {
                "schema_version": DECISION_SCHEMA,
                "decision_id": decision_id,
                "review_id": review_id,
                "graph_sha256": review["graph_sha256"],
                "scope": scope,
                "decision": decision,
                "actor": actor,
                "edge_ids": edge_ids,
                "note": " ".join(note.split())[:1000],
                "created_utc": stamp,
                "applies_external_write": False,
                "drive_write_executed": False,
                "canonical_state": "pending_drive_promotion_and_exact_readback",
            }
            connection.execute(
                """
                INSERT INTO representation_decisions (
                    decision_id, review_id, graph_sha256, scope, decision, actor, edge_ids_json,
                    note, applies_external_write, created_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    decision_id,
                    review_id,
                    review["graph_sha256"],
                    scope,
                    decision,
                    actor,
                    _json(edge_ids),
                    receipt["note"],
                    stamp,
                ),
            )
            next_state = {
                "approve": "approved_pending_drive_readback",
                "provisional_approve": "provisional_pending_drive_readback",
                "hold": "held",
                "reject": "rejected",
                "request_evidence": "evidence_requested",
                "supersede": "supersession_pending_drive_readback",
            }[decision]
            review_stage = "edges" if scope == "identity" and decision in {
                "approve",
                "provisional_approve",
            } else scope
            connection.execute(
                """
                UPDATE representation_review_packets
                SET state=?, review_stage=?, updated_utc=?
                WHERE review_id=?
                """,
                (next_state, review_stage, stamp, review_id),
            )
            if scope == "edges":
                placeholders = ",".join("?" for _ in edge_ids)
                edge_state = "approved" if decision in {"approve", "provisional_approve"} else decision
                connection.execute(
                    f"""
                    UPDATE representation_edges
                    SET review_state=?, owner_decision_id=?, updated_utc=?
                    WHERE edge_id IN ({placeholders})
                    """,
                    (edge_state, decision_id, stamp, *edge_ids),
                )
        _append_jsonl_once(decision_path, receipt, "decision_id")
        _write_json(local_outbox / f"{review_id}_{decision_id}.json", receipt)
        return receipt

    def _prepare_drive_promotion(
        self,
        *,
        object_id: str,
        review_id: str,
        local_outbox: Path,
    ) -> dict[str, Any]:
        with self._connect() as connection:
            review = connection.execute(
                """
                SELECT graph_sha256 FROM representation_review_packets
                WHERE review_id=? AND object_id=?
                """,
                (review_id, object_id),
            ).fetchone()
        if review is None:
            raise RepresentationValidationError(
                "review packet is required before Drive promotion preparation"
            )
        graph_hash = str(review["graph_sha256"])
        promotion_id = (
            "DRIVE-PROMOTION-"
            + hashlib.sha256(f"{object_id}|{review_id}".encode("utf-8")).hexdigest()[:16].upper()
        )
        stamp = utc_now_iso()
        personal = object_id == "de-sporte-05d89c2a"
        state = (
            "held_personal_private_no_business_promotion"
            if personal
            else "local_outbox_pending_drive_sync"
        )
        contract = {
            "schema_version": PROMOTION_SCHEMA,
            "promotion_id": promotion_id,
            "object_id": object_id,
            "review_id": review_id,
            "state": state,
            "graph_sha256": graph_hash,
            "expected_parent": None,
            "expected_metadata": {
                "schema_version": SCHEMA_VERSION,
                "object_id": object_id,
                "review_id": review_id,
                "public_safe": not personal,
            },
            "required_readback": [
                "drive_object_id",
                "drive_revision_id_or_immutable_file_sha256",
                "canonical_normalized_content_sha256_where_applicable",
                "expected_parent",
                "expected_metadata",
                "matching_object_id",
                "matching_decision_receipt",
                "no_source_mutation",
                "no_secret_or_private_data_violation",
            ],
            "drive_write_executed": False,
            "drive_readback_complete": False,
            "automatic_promotion": False,
            "created_utc": stamp,
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO drive_promotion_jobs (
                    promotion_id, object_id, review_id, state, expected_parent,
                    expected_metadata_json, graph_sha256, decision_id,
                    drive_object_id, drive_revision_id, immutable_file_sha256,
                    normalized_content_sha256, readback_json, created_utc, updated_utc
                ) VALUES (?, ?, ?, ?, NULL, ?, ?, NULL, NULL, NULL, NULL, NULL, '{}', ?, ?)
                ON CONFLICT(promotion_id) DO UPDATE SET
                    state=CASE
                        WHEN drive_promotion_jobs.graph_sha256=excluded.graph_sha256
                        THEN drive_promotion_jobs.state
                        ELSE excluded.state
                    END,
                    expected_parent=CASE
                        WHEN drive_promotion_jobs.graph_sha256=excluded.graph_sha256
                        THEN drive_promotion_jobs.expected_parent
                        ELSE NULL
                    END,
                    decision_id=CASE
                        WHEN drive_promotion_jobs.graph_sha256=excluded.graph_sha256
                        THEN drive_promotion_jobs.decision_id
                        ELSE NULL
                    END,
                    expected_metadata_json=excluded.expected_metadata_json,
                    graph_sha256=excluded.graph_sha256,
                    updated_utc=excluded.updated_utc
                """,
                (
                    promotion_id,
                    object_id,
                    review_id,
                    state,
                    _json(contract["expected_metadata"]),
                    graph_hash,
                    stamp,
                    stamp,
                ),
            )
        _write_json(local_outbox / f"{promotion_id}.json", contract)
        return contract

    def confirm_drive_readback(self, promotion_id: str, readback: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as connection:
            promotion = connection.execute(
                "SELECT object_id, expected_parent FROM drive_promotion_jobs WHERE promotion_id=?",
                (promotion_id,),
            ).fetchone()
        if promotion is None:
            raise KeyError(promotion_id)
        if str(promotion["object_id"]) == "de-sporte-05d89c2a":
            raise RepresentationValidationError(
                "personal/private De Sporte cannot promote to business or Drive canon"
            )
        required = {
            "drive_object_id",
            "expected_parent",
            "metadata",
            "object_id",
            "decision_id",
            "graph_sha256",
        }
        missing = sorted(key for key in required if not readback.get(key))
        if readback.get("no_source_mutation") is not True:
            missing.append("no_source_mutation=true")
        if readback.get("no_secret_or_private_data_violation") is not True:
            missing.append("no_secret_or_private_data_violation=true")
        if not (
            readback.get("drive_revision_id")
            or SHA256_PATTERN.fullmatch(str(readback.get("immutable_file_sha256") or ""))
        ):
            missing.append("drive_revision_id_or_immutable_file_sha256")
        if missing:
            raise RepresentationValidationError(
                "canonical state rejected without exact Drive readback: " + ", ".join(missing)
            )
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM drive_promotion_jobs WHERE promotion_id=?",
                (promotion_id,),
            ).fetchone()
            if row is None:
                raise KeyError(promotion_id)
            if not row["expected_parent"]:
                raise RepresentationValidationError(
                    "exact approved Drive parent must be staged before readback"
                )
            if str(readback["expected_parent"]) != str(row["expected_parent"]):
                raise RepresentationValidationError("Drive readback parent does not match promotion")
            if str(readback["object_id"]) != str(row["object_id"]):
                raise RepresentationValidationError("Drive readback object ID does not match graph")
            if str(readback["graph_sha256"]).casefold() != str(row["graph_sha256"]).casefold():
                raise RepresentationValidationError("Drive readback graph hash does not match promotion")
            expected_metadata = _loaded(row["expected_metadata_json"], {})
            if readback["metadata"] != expected_metadata:
                raise RepresentationValidationError("Drive readback metadata does not match promotion")
            normalized_hash = readback.get("normalized_content_sha256")
            if normalized_hash and not SHA256_PATTERN.fullmatch(str(normalized_hash)):
                raise RepresentationValidationError(
                    "normalized content hash must be SHA-256 when supplied"
                )
            native_workbook_requires_hash = connection.execute(
                """
                SELECT 1 FROM object_representations
                WHERE object_id=? AND locator_type='drive_workbook'
                  AND state IN ('active','provisional','held')
                LIMIT 1
                """,
                (row["object_id"],),
            ).fetchone()
            if native_workbook_requires_hash and not SHA256_PATTERN.fullmatch(
                str(normalized_hash or "")
            ):
                raise RepresentationValidationError(
                    "canonical normalized workbook content hash is required"
                )
            decision = connection.execute(
                """
                SELECT decision_id FROM representation_decisions
                WHERE decision_id=? AND review_id=?
                  AND decision='approve' AND graph_sha256=?
                """,
                (readback["decision_id"], row["review_id"], row["graph_sha256"]),
            ).fetchone()
            if decision is None:
                raise RepresentationValidationError(
                    "matching owner-approved decision receipt is required"
                )
            if row["decision_id"] and str(row["decision_id"]) != str(readback["decision_id"]):
                raise RepresentationValidationError(
                    "Drive readback decision does not match the staged transfer target"
                )
            stamp = utc_now_iso()
            connection.execute(
                """
                UPDATE drive_promotion_jobs
                SET state='canonical_drive_readback_complete',
                    decision_id=?, drive_object_id=?, drive_revision_id=?,
                    immutable_file_sha256=?, normalized_content_sha256=?,
                    expected_parent=?, readback_json=?, updated_utc=?
                WHERE promotion_id=?
                """,
                (
                    readback["decision_id"],
                    readback["drive_object_id"],
                    readback.get("drive_revision_id"),
                    readback.get("immutable_file_sha256"),
                    readback.get("normalized_content_sha256"),
                    readback["expected_parent"],
                    _json(readback),
                    stamp,
                    promotion_id,
                ),
            )
            connection.execute(
                "UPDATE canonical_objects SET state='active', updated_utc=? WHERE object_id=?",
                (stamp, row["object_id"]),
            )
        return {"promotion_id": promotion_id, "canonical": True, "readback": readback}

    def stage_promotion_target(
        self,
        *,
        promotion_id: str,
        expected_parent: str,
        decision_id: str,
    ) -> dict[str, Any]:
        """Bind a reviewed promotion to one exact Drive parent without writing Drive."""
        parent = " ".join(str(expected_parent).split())[:300]
        if not parent:
            raise RepresentationValidationError("exact Drive parent is required")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT review_id, object_id FROM drive_promotion_jobs WHERE promotion_id=?",
                (promotion_id,),
            ).fetchone()
            if row is None:
                raise KeyError(promotion_id)
            if str(row["object_id"]) == "de-sporte-05d89c2a":
                raise RepresentationValidationError(
                    "personal/private De Sporte cannot promote to business or Drive canon"
                )
            decision = connection.execute(
                """
                SELECT 1 FROM representation_decisions
                WHERE decision_id=? AND review_id=? AND decision='approve'
                  AND graph_sha256=(
                      SELECT graph_sha256 FROM drive_promotion_jobs WHERE promotion_id=?
                  )
                """,
                (decision_id, row["review_id"], promotion_id),
            ).fetchone()
            if decision is None:
                raise RepresentationValidationError(
                    "owner-approved identity decision is required before target staging"
                )
            stamp = utc_now_iso()
            connection.execute(
                """
                UPDATE drive_promotion_jobs
                SET expected_parent=?, decision_id=?,
                    state='approved_target_pending_drive_write', updated_utc=?
                WHERE promotion_id=?
                """,
                (parent, decision_id, stamp, promotion_id),
            )
        return {
            "promotion_id": promotion_id,
            "expected_parent": parent,
            "decision_id": decision_id,
            "state": "approved_target_pending_drive_write",
            "drive_write_executed": False,
        }


def _proof_definitions() -> list[dict[str, Any]]:
    evidence_baseline = "2026-07-24 accepted local/Drive evidence baseline"
    apophis_claim = (
        "Catalogue and trajectory evidence do not establish launch feasibility, route, delta-v, "
        "mining feasibility, extraction performance, operational safety, target priority, or mission approval."
    )
    rfs_claim = (
        "Evidence classification does not approve RFS/EMFF capability, performance, extraction, "
        "efficiency, safety, feasibility, simulation output, workbook mutation, or scientific promotion."
    )
    de_sporte_claim = (
        "Registration and process health do not authorize personal content ingestion or promotion "
        "into workplace, Drive, public, health, legal, or financial canon."
    )
    apophis_horizon_inputs = {
        "object": "ASPHA.0001",
        "posture": "tag_and_track_if_required_fleet_exceeds_current_capacity",
        "launch_options": [3, 5, 7],
        "cumulative_unit_states": [6, 8, 10],
        "mine_first_assumption": False,
    }
    rfs_horizon_inputs = {
        "object": "engineering-twin:rfs-emff-sandbox",
        "minimum_sequence": [
            "apparatus_definition",
            "instrumentation_sensor_schema",
            "reproducible_control_dataset",
            "material_sample_matrix",
            "mathematical_baseline",
        ],
        "simulation_authorized": False,
    }
    de_sporte_horizon_inputs = {
        "object": "de-sporte-05d89c2a",
        "classification": "personal_private",
        "business_promotion": False,
        "content_ingestion": False,
    }

    apophis = {
        "objects": [
            {
                "object_id": "ASPHA.0001",
                "object_type": "asteroid",
                "canonical_name": "ASPHA.0001",
                "display_name": "Apophis",
                "description": "Candidate Römer identity for asteroid 99942 Apophis.",
                "authority": "Nathaniel primary-name gate; JPL empirical identity",
                "identity_confidence_numeric": 0.98,
                "identity_confidence_class": "high",
                "state": "candidate",
                "metadata": {
                    "classification_shorthand": "Aten / Stony / Potentially Hazardous Asteroid / sequence 0001",
                    "classification_is_empirical_claim": False,
                },
            }
        ],
        "identifiers": [
            {
                "identifier_id": "identifier:ASPHA.0001:romer",
                "object_id": "ASPHA.0001",
                "namespace": "romer",
                "identifier_value": "ASPHA.0001",
                "identifier_type": "internal",
                "authority": "Nathaniel",
                "is_primary": True,
            },
            {
                "identifier_id": "identifier:ASPHA.0001:jpl",
                "object_id": "ASPHA.0001",
                "namespace": "jpl",
                "identifier_value": "99942",
                "identifier_type": "empirical_authority",
                "authority": "JPL",
            },
            {
                "identifier_id": "identifier:ASPHA.0001:display",
                "object_id": "ASPHA.0001",
                "namespace": "human_name",
                "identifier_value": "Apophis",
                "identifier_type": "display_name",
                "authority": "IAU/JPL",
            },
            {
                "identifier_id": "identifier:ASPHA.0001:designation",
                "object_id": "ASPHA.0001",
                "namespace": "provisional_designation",
                "identifier_value": "2004 MN4",
                "identifier_type": "alias",
                "authority": "MPC/JPL",
            },
        ],
        "horizons": [
            {
                "horizon_id": "horizon:apophis:tag-track:v1",
                "name": "Apophis first bounded posture",
                "horizon_type": "mission_candidate",
                "objective": "Select a bounded posture without assuming mine-first feasibility.",
                "assumptions": apophis_horizon_inputs,
                "constraints": {
                    "current_capacity_unproven": True,
                    "mission_simulation_missing": True,
                    "resource_guard_required": True,
                },
                "accepted_inputs": apophis_horizon_inputs,
                "input_set_sha256": content_sha256(apophis_horizon_inputs),
                "sensitivity_summary": {
                    "status": "not_run",
                    "required": ["fleet capacity", "duration", "route", "timing", "uncertainty"],
                },
                "state": "candidate",
            }
        ],
        "evidence_bundles": [
            {
                "evidence_bundle_id": "evidence:apophis:jpl-workbook:v1",
                "title": "Apophis JPL and workbook locator evidence",
                "state": "provisional",
                "evidence_items": [
                    {
                        "source_representation_id": "rep:apophis:jpl-horizons",
                        "authors": ["NASA/JPL"],
                        "publication_or_observation_date": "2026-07-23",
                        "authority": "JPL Horizons",
                        "underlying_source_fingerprint": "jpl-horizons-99942-solution-220",
                        "independence_status": "independent",
                        "novelty_relevance": "empirical source locator",
                        "domain_expertise_relevance": "authoritative",
                        "corroboration_relevance": "identity and state series",
                        "outlier": False,
                        "duplicate": False,
                        "review_state": "candidate",
                    },
                    {
                        "source_representation_id": "rep:apophis:raw-workbook-row",
                        "authors": ["Römer workbook maintainers"],
                        "publication_or_observation_date": "2026-03-05",
                        "authority": "Drive workbook",
                        "underlying_source_fingerprint": "ssodnet-apophis-secondary",
                        "independence_status": "shared_lineage",
                        "novelty_relevance": "operational classification input",
                        "domain_expertise_relevance": "unreviewed",
                        "corroboration_relevance": "candidate only",
                        "outlier": False,
                        "duplicate": False,
                        "review_state": "awaiting_stable_workbook_key",
                    },
                ],
                "claim_boundary": apophis_claim,
            }
        ],
        "representations": [
            {
                "representation_id": "rep:apophis:jpl-horizons",
                "object_id": "ASPHA.0001",
                "representation_type": "empirical_source",
                "locator_type": "git_file",
                "locator": {
                    "repository": "achillesromer-coder/Data",
                    "commit_sha": "e2e242b3884dd14241b33dca730e07a297c3da85",
                    "path": "data/jpl/horizons/latest/apophis.json",
                    "target_id": "99942",
                    "schema_id": "jpl-horizons-capture",
                },
                "content_sha256": "628ada4017163212f2a4754cbcf6b0ebeac5af943abbfa998e38a7aace1b4bb8",
                "schema_id": "jpl-horizons-capture",
                "source_authority": "NASA/JPL Horizons",
                "confidence_numeric": 0.98,
                "confidence_class": "high",
                "evidence_class": "empirical_authority",
                "state": "active",
                "claim_boundary": apophis_claim,
            },
            {
                "representation_id": "rep:apophis:operating-workbook",
                "object_id": "ASPHA.0001",
                "representation_type": "workbook",
                "locator_type": "drive_workbook",
                "locator": {
                    "drive_file_id": "1Uy04F5gtf2mXf9tDmAyIvNrsCn1kn4Csa2oc-skSZxY",
                    "drive_revision_id": None,
                    "normalized_content_sha256": None,
                    "schema_id": "type1-asteroid-operating-workbook",
                },
                "content_sha256": None,
                "schema_id": "type1-asteroid-operating-workbook",
                "source_authority": "Drive canonical workbook",
                "confidence_numeric": 0.8,
                "confidence_class": "high",
                "evidence_class": "canonical_locator_pending_revision_hash",
                "state": "provisional",
                "claim_boundary": "Workbook is read-only; no stable Apophis row key or normalized hash is proven.",
            },
            {
                "representation_id": "rep:apophis:raw-workbook-row",
                "object_id": "ASPHA.0001",
                "representation_type": "workbook_row",
                "locator_type": "drive_workbook_row",
                "locator": {
                    "drive_file_id": "1Lqeqcxmhatc2sdCeRYUHtWx3D-MnVYnW",
                    "drive_revision_id": None,
                    "sheet_name": "4_Asteroid_Master",
                    "stable_key": None,
                    "content_key": "Object_ID=Apophis",
                    "current_row_number": 2,
                    "current_cell_range": "A2:N2",
                    "missing_state": "awaiting_stable_workbook_key",
                    "reason": "Object_ID contains a name but has not been proven as a permanent logical key.",
                    "last_search": evidence_baseline,
                    "next_evidence_action": "Owner/workbook steward approves a permanent row key without mutating this pass.",
                    "assigned_floor": "Oracle",
                    "dependency_effect": "Workbook edge cannot be approved or promoted.",
                },
                "content_sha256": None,
                "schema_id": "asteroid-strategic-mapping-base-row",
                "source_authority": "Drive raw workbook / SsODNet lineage",
                "confidence_numeric": 0.5,
                "confidence_class": "moderate",
                "evidence_class": "content_locator_only",
                "state": "missing",
                "claim_boundary": apophis_claim,
            },
            {
                "representation_id": "rep:apophis:mesh",
                "object_id": "ASPHA.0001",
                "representation_type": "mesh",
                "locator_type": "missing",
                "locator": {
                    "missing_state": "searched_not_found",
                    "reason": "No identity-proven Apophis mesh was linked; filename resemblance is insufficient.",
                    "last_search": evidence_baseline,
                    "next_evidence_action": "Locate a source-established shape model or create hashed illustrative geometry.",
                    "assigned_floor": "Oracle",
                    "dependency_effect": "No measured shape or mesh visualization claim.",
                },
                "content_sha256": None,
                "schema_id": None,
                "source_authority": "none",
                "confidence_numeric": 0.0,
                "confidence_class": "unknown",
                "evidence_class": "missing",
                "state": "missing",
                "claim_boundary": "No measured Apophis shape is represented.",
            },
            {
                "representation_id": "rep:apophis:mission-simulation",
                "object_id": "ASPHA.0001",
                "representation_type": "simulation_output",
                "locator_type": "missing",
                "locator": {
                    "missing_state": "awaiting_approved_task_and_inputs",
                    "reason": "No bounded mission/fuel/extraction simulation is authorised or available.",
                    "last_search": evidence_baseline,
                    "next_evidence_action": "Approve bounded inputs only after capacity and route requirements are known.",
                    "assigned_floor": "TheConstruct",
                    "dependency_effect": "Mission recommendation remains provisional.",
                },
                "content_sha256": None,
                "schema_id": None,
                "source_authority": "none",
                "confidence_numeric": 0.0,
                "confidence_class": "unknown",
                "evidence_class": "missing",
                "horizon_id": "horizon:apophis:tag-track:v1",
                "state": "missing",
                "claim_boundary": apophis_claim,
            },
            {
                "representation_id": "rep:apophis:recommendation",
                "object_id": "ASPHA.0001",
                "representation_type": "recommendation",
                "locator_type": "logical",
                "locator": {
                    "objective": "Select tag-and-track if estimated required fleet exceeds current capacity.",
                    "input_set_sha256": content_sha256(apophis_horizon_inputs),
                    "next_highest_value_question": (
                        "What measured fleet, duration, extraction-capacity, route, and uncertainty inputs "
                        "are sufficient to compare tag-and-track with mine-first?"
                    ),
                },
                "content_sha256": content_sha256(
                    {"recommendation": "tag_and_track", "inputs": apophis_horizon_inputs}
                ),
                "schema_id": "horizon-bound-recommendation-v1",
                "source_authority": "Architect/Neo candidate",
                "confidence_numeric": 0.25,
                "confidence_class": "low",
                "evidence_class": "horizon_bound_candidate",
                "horizon_id": "horizon:apophis:tag-track:v1",
                "state": "provisional",
                "claim_boundary": apophis_claim,
            },
        ],
        "edges": [
            {
                "edge_id": "edge:apophis:jpl-recorded-workbook",
                "from_representation_id": "rep:apophis:jpl-horizons",
                "to_representation_id": "rep:apophis:raw-workbook-row",
                "relation": "recorded_in",
                "evidence_bundle_id": "evidence:apophis:jpl-workbook:v1",
                "confidence_numeric": 0.5,
                "confidence_class": "moderate",
                "claim_boundary": "Held until stable workbook row identity and lineage are approved.",
                "created_by_floor": "Oracle",
                "review_state": "held",
            },
            {
                "edge_id": "edge:apophis:recommendation-depends-jpl",
                "from_representation_id": "rep:apophis:recommendation",
                "to_representation_id": "rep:apophis:jpl-horizons",
                "relation": "depends_on",
                "evidence_bundle_id": None,
                "confidence_numeric": 0.4,
                "confidence_class": "moderate",
                "claim_boundary": apophis_claim,
                "created_by_floor": "Architect",
                "review_state": "pending",
            },
        ],
    }

    rfs = {
        "objects": [
            {
                "object_id": "engineering-twin:rfs-emff-sandbox",
                "object_type": "engineering_twin",
                "canonical_name": "RFS/EMFF sandbox",
                "display_name": "RFS/EMFF evidence sandbox",
                "description": "Held engineering-twin container for evidence and experimental intake.",
                "authority": "Nathaniel / Achilles evidence gate",
                "identity_confidence_numeric": 0.9,
                "identity_confidence_class": "high",
                "state": "candidate",
                "metadata": {"empirical_capability_approved": False},
            },
            {
                "object_id": "engineering-system:rfs",
                "object_type": "engineering_system",
                "canonical_name": "RFS",
                "display_name": "RFS",
                "description": "Candidate RFS engineering system identity; capability remains unproven.",
                "authority": "Nathaniel / Achilles evidence gate",
                "identity_confidence_numeric": 0.75,
                "identity_confidence_class": "moderate",
                "state": "held",
                "metadata": {"parent_sandbox": "engineering-twin:rfs-emff-sandbox"},
            },
            {
                "object_id": "engineering-system:emff",
                "object_type": "engineering_system",
                "canonical_name": "EMFF",
                "display_name": "EMFF",
                "description": "Candidate EMFF engineering system identity; capability remains unproven.",
                "authority": "Nathaniel / Achilles evidence gate",
                "identity_confidence_numeric": 0.75,
                "identity_confidence_class": "moderate",
                "state": "held",
                "metadata": {"parent_sandbox": "engineering-twin:rfs-emff-sandbox"},
            },
        ],
        "identifiers": [
            {
                "identifier_id": "identifier:rfs-emff-sandbox",
                "object_id": "engineering-twin:rfs-emff-sandbox",
                "namespace": "engineering_twin",
                "identifier_value": "rfs-emff-sandbox",
                "identifier_type": "internal",
                "authority": "Nathaniel",
                "is_primary": True,
            },
            {
                "identifier_id": "identifier:rfs",
                "object_id": "engineering-system:rfs",
                "namespace": "engineering_system",
                "identifier_value": "rfs",
                "identifier_type": "internal",
                "authority": "Nathaniel",
                "is_primary": True,
            },
            {
                "identifier_id": "identifier:emff",
                "object_id": "engineering-system:emff",
                "namespace": "engineering_system",
                "identifier_value": "emff",
                "identifier_type": "internal",
                "authority": "Nathaniel",
                "is_primary": True,
            },
        ],
        "horizons": [
            {
                "horizon_id": "horizon:rfs-emff:first-evidence",
                "name": "RFS/EMFF first reproducible evidence horizon",
                "horizon_type": "experimental_candidate",
                "objective": "Obtain reproducible apparatus, controls, raw data, and material provenance.",
                "assumptions": rfs_horizon_inputs,
                "constraints": {
                    "no_capability_promotion": True,
                    "workbook_read_only": True,
                    "archive_controlled_unpack_only": True,
                },
                "accepted_inputs": rfs_horizon_inputs,
                "input_set_sha256": content_sha256(rfs_horizon_inputs),
                "sensitivity_summary": {"status": "awaiting_empirical_inputs"},
                "state": "candidate",
            }
        ],
        "evidence_bundles": [
            {
                "evidence_bundle_id": "evidence:rfs-emff:classification:v1",
                "title": "RFS/EMFF retained-source classification",
                "state": "approved_local_pending_drive_readback",
                "evidence_items": [
                    {
                        "source_representation_id": "rep:rfs-emff:classification-receipt",
                        "authors": ["RFS/EMFF evidence corpus"],
                        "publication_or_observation_date": None,
                        "authority": "local owner decision",
                        "underlying_source_fingerprint": "classified-retained-source-set",
                        "independence_status": "unassessed",
                        "novelty_relevance": "classification only",
                        "domain_expertise_relevance": "unassessed",
                        "corroboration_relevance": "none",
                        "outlier": False,
                        "duplicate": False,
                        "review_state": "approved_local_pending_drive_readback",
                    }
                ],
                "independence_group_count": 0,
                "duplicate_reference_count": 148,
                "source_weight_summary": {
                    "retained_classified_sources": 27,
                    "duplicate_references_held": 148,
                    "empirical_confidence_increase": 0.0,
                },
                "confidence_effect": 0.0,
                "claim_boundary": rfs_claim,
            }
        ],
        "representations": [
            {
                "representation_id": "rep:rfs-emff:sandbox-state",
                "object_id": "engineering-twin:rfs-emff-sandbox",
                "representation_type": "operational_state",
                "locator_type": "logical",
                "locator": {"schema_id": "rfs-emff-sandbox-state-v1"},
                "content_sha256": content_sha256({"state": "held", "capability": "unproven"}),
                "schema_id": "rfs-emff-sandbox-state-v1",
                "source_authority": "Achilles",
                "confidence_numeric": 0.9,
                "confidence_class": "high",
                "evidence_class": "governance_state",
                "state": "held",
                "claim_boundary": rfs_claim,
            },
            {
                "representation_id": "rep:rfs:system-state",
                "object_id": "engineering-system:rfs",
                "representation_type": "operational_state",
                "locator_type": "logical",
                "locator": {"schema_id": "engineering-system-candidate-v1"},
                "content_sha256": content_sha256({"system": "RFS", "state": "held"}),
                "schema_id": "engineering-system-candidate-v1",
                "source_authority": "Achilles",
                "confidence_numeric": 0.7,
                "confidence_class": "moderate",
                "evidence_class": "identity_candidate",
                "state": "held",
                "claim_boundary": rfs_claim,
            },
            {
                "representation_id": "rep:emff:system-state",
                "object_id": "engineering-system:emff",
                "representation_type": "operational_state",
                "locator_type": "logical",
                "locator": {"schema_id": "engineering-system-candidate-v1"},
                "content_sha256": content_sha256({"system": "EMFF", "state": "held"}),
                "schema_id": "engineering-system-candidate-v1",
                "source_authority": "Achilles",
                "confidence_numeric": 0.7,
                "confidence_class": "moderate",
                "evidence_class": "identity_candidate",
                "state": "held",
                "claim_boundary": rfs_claim,
            },
            {
                "representation_id": "rep:rfs-emff:classification-receipt",
                "object_id": "engineering-twin:rfs-emff-sandbox",
                "representation_type": "receipt",
                "locator_type": "local_receipt",
                "locator": {
                    "receipt_id": "LSGO-REVIEW-59D998FCAA1D8503",
                    "label": "owner evidence-classification decision",
                },
                "content_sha256": content_sha256(
                    {
                        "review_id": "LSGO-REVIEW-59D998FCAA1D8503",
                        "approved": "classification_only",
                        "retained": 27,
                        "duplicate_hold": 148,
                    }
                ),
                "schema_id": "lightspeed-go-review-decision-v1",
                "source_authority": "Nathaniel / Achilles GO gate",
                "confidence_numeric": 1.0,
                "confidence_class": "confirmed",
                "evidence_class": "approved_local_pending_drive_readback",
                "state": "provisional",
                "claim_boundary": rfs_claim,
            },
            {
                "representation_id": "rep:rfs-emff:workbook",
                "object_id": "engineering-twin:rfs-emff-sandbox",
                "representation_type": "workbook",
                "locator_type": "logical",
                "locator": {"schema_id": "rfs-emff-evidence-workbook"},
                "content_sha256": "1cc3f421ed128186b1ab018f7af8eda27bc30572b21bc8b8a1d2bada91c9a58f",
                "schema_id": "rfs-emff-evidence-workbook",
                "source_authority": "local exact-file evidence",
                "confidence_numeric": 0.8,
                "confidence_class": "high",
                "evidence_class": "exact_file_identity_not_claim_approval",
                "state": "held",
                "claim_boundary": rfs_claim,
            },
            {
                "representation_id": "rep:rfs-emff:archive",
                "object_id": "engineering-twin:rfs-emff-sandbox",
                "representation_type": "archive",
                "locator_type": "logical",
                "locator": {
                    "schema_id": "rfs-emff-held-archive",
                    "missing_state": "held_pending_controlled_unpack",
                },
                "content_sha256": "4d55d645faca3db3bafb9ce79f09faf51ae235644255ce6e4e30adab369224ba",
                "schema_id": "rfs-emff-held-archive",
                "source_authority": "local exact-file evidence",
                "confidence_numeric": 0.8,
                "confidence_class": "high",
                "evidence_class": "held_pending_controlled_unpack",
                "state": "held",
                "claim_boundary": rfs_claim,
            },
            *[
                {
                    "representation_id": f"rep:rfs-emff:missing:{key}",
                    "object_id": "engineering-twin:rfs-emff-sandbox",
                    "representation_type": rep_type,
                    "locator_type": "missing",
                    "locator": {
                        "missing_state": missing_state,
                        "reason": reason,
                        "last_search": evidence_baseline,
                        "next_evidence_action": next_action,
                        "assigned_floor": floor,
                        "dependency_effect": "Empirical capability and scientific promotion remain held.",
                    },
                    "content_sha256": None,
                    "schema_id": None,
                    "source_authority": "none",
                    "confidence_numeric": 0.0,
                    "confidence_class": "unknown",
                    "evidence_class": "missing",
                    "horizon_id": "horizon:rfs-emff:first-evidence",
                    "state": "missing",
                    "claim_boundary": rfs_claim,
                }
                for key, rep_type, missing_state, reason, next_action, floor in [
                    (
                        "apparatus",
                        "artifact",
                        "awaiting_physical_experiment",
                        "No accepted apparatus definition or physical provenance.",
                        "Document apparatus geometry, provenance, controls, and calibration.",
                        "TheConstruct",
                    ),
                    (
                        "instrumentation",
                        "model",
                        "insufficient_evidence",
                        "No accepted instrumentation and sensor schema.",
                        "Define calibrated sensors, sampling, uncertainty, and negative/zero controls.",
                        "TheConstruct",
                    ),
                    (
                        "control-dataset",
                        "empirical_source",
                        "awaiting_physical_experiment",
                        "No reproducible raw control dataset with at least two repeat runs.",
                        "Capture bounded raw data with repeat runs and immutable provenance.",
                        "Oracle",
                    ),
                    (
                        "material-matrix",
                        "artifact",
                        "awaiting_physical_experiment",
                        "No accepted material sample matrix or sample provenance.",
                        "Define samples, composition, custody, and measurement uncertainty.",
                        "Oracle",
                    ),
                    (
                        "mathematical-baseline",
                        "equation",
                        "awaiting_independent_corroboration",
                        "Existing mathematics has not been promoted as an empirical capability baseline.",
                        "Review bounded model assumptions without raising physical capability confidence.",
                        "Morpheus",
                    ),
                ]
            ],
            {
                "representation_id": "rep:rfs-emff:recommendation",
                "object_id": "engineering-twin:rfs-emff-sandbox",
                "representation_type": "recommendation",
                "locator_type": "logical",
                "locator": {
                    "objective": "Obtain a reproducible instrumented dataset and apparatus definition.",
                    "input_set_sha256": content_sha256(rfs_horizon_inputs),
                    "next_highest_value_question": (
                        "What minimum apparatus, calibrated sensor schema, controls, repeat-run data, "
                        "and material provenance will support the first empirical candidate?"
                    ),
                },
                "content_sha256": content_sha256(
                    {"recommendation": "obtain_reproducible_evidence", "inputs": rfs_horizon_inputs}
                ),
                "schema_id": "horizon-bound-recommendation-v1",
                "source_authority": "Achilles evidence gate",
                "confidence_numeric": 0.9,
                "confidence_class": "high",
                "evidence_class": "governance_recommendation_not_capability_claim",
                "horizon_id": "horizon:rfs-emff:first-evidence",
                "state": "provisional",
                "claim_boundary": rfs_claim,
            },
        ],
        "edges": [
            {
                "edge_id": "edge:rfs:depends-sandbox",
                "from_representation_id": "rep:rfs:system-state",
                "to_representation_id": "rep:rfs-emff:sandbox-state",
                "relation": "depends_on",
                "evidence_bundle_id": None,
                "confidence_numeric": 0.9,
                "confidence_class": "high",
                "claim_boundary": "Container relationship only; no capability inference.",
                "created_by_floor": "Architect",
                "review_state": "pending",
            },
            {
                "edge_id": "edge:emff:depends-sandbox",
                "from_representation_id": "rep:emff:system-state",
                "to_representation_id": "rep:rfs-emff:sandbox-state",
                "relation": "depends_on",
                "evidence_bundle_id": None,
                "confidence_numeric": 0.9,
                "confidence_class": "high",
                "claim_boundary": "Container relationship only; no capability inference.",
                "created_by_floor": "Architect",
                "review_state": "pending",
            },
            {
                "edge_id": "edge:rfs-emff:receipt-corroborates-workbook",
                "from_representation_id": "rep:rfs-emff:classification-receipt",
                "to_representation_id": "rep:rfs-emff:workbook",
                "relation": "corroborates",
                "evidence_bundle_id": "evidence:rfs-emff:classification:v1",
                "confidence_numeric": 0.7,
                "confidence_class": "moderate",
                "claim_boundary": rfs_claim,
                "created_by_floor": "Morpheus",
                "review_state": "approved_local_pending_drive_readback",
            },
            {
                "edge_id": "edge:rfs-emff:recommendation-depends-dataset",
                "from_representation_id": "rep:rfs-emff:recommendation",
                "to_representation_id": "rep:rfs-emff:missing:control-dataset",
                "relation": "depends_on",
                "evidence_bundle_id": None,
                "confidence_numeric": 0.95,
                "confidence_class": "high",
                "claim_boundary": rfs_claim,
                "created_by_floor": "Achilles",
                "review_state": "pending",
            },
        ],
    }

    de_sporte = {
        "objects": [
            {
                "object_id": "de-sporte-05d89c2a",
                "object_type": "operational_project",
                "canonical_name": "De Sporte",
                "display_name": "De Sporte",
                "description": (
                    "Personal/private persistence, rest, continuity, and persona-development environment "
                    "for Cognigrex members."
                ),
                "authority": "Nathaniel personal/private classification",
                "identity_confidence_numeric": 1.0,
                "identity_confidence_class": "confirmed",
                "state": "candidate",
                "metadata": {
                    "business_project": False,
                    "content_file_count_observed": 20525,
                    "content_assimilated": False,
                    "public_safe": False,
                },
            }
        ],
        "identifiers": [
            {
                "identifier_id": "identifier:de-sporte:internal",
                "object_id": "de-sporte-05d89c2a",
                "namespace": "operational_project",
                "identifier_value": "de-sporte-05d89c2a",
                "identifier_type": "internal",
                "authority": "LightSpeed project registry",
                "is_primary": True,
            },
            {
                "identifier_id": "identifier:de-sporte:display",
                "object_id": "de-sporte-05d89c2a",
                "namespace": "display_name",
                "identifier_value": "De Sporte",
                "identifier_type": "display_name",
                "authority": "Nathaniel",
            },
            *[
                {
                    "identifier_id": f"identifier:de-sporte:class:{classification}",
                    "object_id": "de-sporte-05d89c2a",
                    "namespace": "classification",
                    "identifier_value": classification,
                    "identifier_type": "classification",
                    "authority": "Nathaniel",
                }
                for classification in (
                    "personal_private",
                    "operational_local",
                    "agent_persona",
                    "agent_rest_environment",
                    "sensitive",
                    "noncanonical_business",
                    "nonpublic",
                )
            ],
        ],
        "horizons": [
            {
                "horizon_id": "horizon:de-sporte:private-operations",
                "name": "De Sporte private operations",
                "horizon_type": "personal_operating_period",
                "objective": "Maintain private continuity without workplace or public data bleed.",
                "assumptions": de_sporte_horizon_inputs,
                "constraints": {
                    "metadata_only": True,
                    "no_automatic_drive_write": True,
                    "no_personal_to_business_promotion": True,
                },
                "accepted_inputs": de_sporte_horizon_inputs,
                "input_set_sha256": content_sha256(de_sporte_horizon_inputs),
                "sensitivity_summary": {"status": "technically_unnecessary"},
                "state": "candidate",
            }
        ],
        "evidence_bundles": [
            {
                "evidence_bundle_id": "evidence:de-sporte:registry-health:v1",
                "title": "De Sporte registry and bounded operational receipts",
                "state": "provisional",
                "evidence_items": [
                    {
                        "source_representation_id": "rep:de-sporte:registry",
                        "authors": ["Merovingian"],
                        "publication_or_observation_date": "2026-07-24",
                        "authority": "LightSpeed project registry",
                        "underlying_source_fingerprint": "de-sporte-registry-05d89c2a",
                        "independence_status": "operational",
                        "novelty_relevance": "identity and availability only",
                        "domain_expertise_relevance": "runtime health",
                        "corroboration_relevance": "none",
                        "outlier": False,
                        "duplicate": False,
                        "review_state": "approved_registry_sync_only",
                    }
                ],
                "claim_boundary": de_sporte_claim,
            }
        ],
        "representations": [
            {
                "representation_id": "rep:de-sporte:registry",
                "object_id": "de-sporte-05d89c2a",
                "representation_type": "operational_state",
                "locator_type": "local_project_registry",
                "locator": {
                    "label": "De Sporte external project registration",
                    "classifications": [
                        "personal_private",
                        "operational_local",
                        "sensitive",
                        "nonpublic",
                    ],
                },
                "content_sha256": "db1b703c78b29d26c60dc541d16c30b1d606c29af6ceb8fd68c54aea3e0ebe21",
                "schema_id": "lightspeed-project-registry-v1",
                "source_authority": "Merovingian",
                "confidence_numeric": 1.0,
                "confidence_class": "confirmed",
                "evidence_class": "metadata_only",
                "state": "active",
                "claim_boundary": de_sporte_claim,
            },
            {
                "representation_id": "rep:de-sporte:health-receipt",
                "object_id": "de-sporte-05d89c2a",
                "representation_type": "receipt",
                "locator_type": "local_receipt",
                "locator": {
                    "receipt_id": "merovingian_soft_launch_receipt",
                    "label": "bounded local process and storage health receipt",
                },
                "content_sha256": "6610149100625a74f2bcd537f79c4923684895fe8a946815f45f395652431a05",
                "schema_id": "lightspeed-merovingian-soft-launch-v1",
                "source_authority": "Merovingian",
                "confidence_numeric": 0.9,
                "confidence_class": "high",
                "evidence_class": "operational_health_only",
                "state": "active",
                "claim_boundary": de_sporte_claim,
            },
            {
                "representation_id": "rep:de-sporte:workbook",
                "object_id": "de-sporte-05d89c2a",
                "representation_type": "workbook",
                "locator_type": "missing",
                "locator": {
                    "missing_state": "technically_unnecessary",
                    "reason": "No workbook is required for the initial private operational identity.",
                    "last_search": evidence_baseline,
                    "next_evidence_action": "None unless Nathaniel nominates an exact private-safe workbook.",
                    "assigned_floor": "Achilles",
                    "dependency_effect": "No operational block.",
                },
                "content_sha256": None,
                "schema_id": None,
                "source_authority": "none",
                "confidence_numeric": 0.0,
                "confidence_class": "unknown",
                "evidence_class": "missing_not_required",
                "state": "missing",
                "claim_boundary": de_sporte_claim,
            },
            {
                "representation_id": "rep:de-sporte:packaged-executable",
                "object_id": "de-sporte-05d89c2a",
                "representation_type": "artifact",
                "locator_type": "missing",
                "locator": {
                    "missing_state": "awaiting_exact_artifact_receipt",
                    "reason": "Runtime visibility does not identify an immutable packaged executable artifact.",
                    "last_search": evidence_baseline,
                    "next_evidence_action": "Attach an owner-approved executable hash and build receipt only.",
                    "assigned_floor": "Smith",
                    "dependency_effect": "Executable provenance remains provisional.",
                },
                "content_sha256": None,
                "schema_id": None,
                "source_authority": "none",
                "confidence_numeric": 0.0,
                "confidence_class": "unknown",
                "evidence_class": "missing",
                "state": "missing",
                "claim_boundary": de_sporte_claim,
            },
            {
                "representation_id": "rep:de-sporte:recommendation",
                "object_id": "de-sporte-05d89c2a",
                "representation_type": "recommendation",
                "locator_type": "logical",
                "locator": {
                    "objective": "Keep De Sporte personal/private and metadata-only in LightSpeed.",
                    "input_set_sha256": content_sha256(de_sporte_horizon_inputs),
                    "next_highest_value_question": (
                        "Which exact owner-approved operational receipt, if any, should be retained "
                        "without ingesting personal project content?"
                    ),
                },
                "content_sha256": content_sha256(
                    {"recommendation": "remain_personal_private", "inputs": de_sporte_horizon_inputs}
                ),
                "schema_id": "horizon-bound-recommendation-v1",
                "source_authority": "Nathaniel / Achilles",
                "confidence_numeric": 1.0,
                "confidence_class": "confirmed",
                "evidence_class": "privacy_boundary",
                "horizon_id": "horizon:de-sporte:private-operations",
                "state": "provisional",
                "claim_boundary": de_sporte_claim,
            },
        ],
        "edges": [
            {
                "edge_id": "edge:de-sporte:health-corroborates-registry",
                "from_representation_id": "rep:de-sporte:health-receipt",
                "to_representation_id": "rep:de-sporte:registry",
                "relation": "corroborates",
                "evidence_bundle_id": "evidence:de-sporte:registry-health:v1",
                "confidence_numeric": 0.8,
                "confidence_class": "high",
                "claim_boundary": de_sporte_claim,
                "created_by_floor": "Merovingian",
                "review_state": "pending",
            },
            {
                "edge_id": "edge:de-sporte:recommendation-depends-registry",
                "from_representation_id": "rep:de-sporte:recommendation",
                "to_representation_id": "rep:de-sporte:registry",
                "relation": "depends_on",
                "evidence_bundle_id": None,
                "confidence_numeric": 1.0,
                "confidence_class": "confirmed",
                "claim_boundary": de_sporte_claim,
                "created_by_floor": "Achilles",
                "review_state": "pending",
            },
        ],
    }
    return [apophis, rfs, de_sporte]


def build_store(shell_root: Path, *, enabled: bool | None = None) -> RepresentationEdgeStore:
    return RepresentationEdgeStore(default_operational_db_path(shell_root), enabled=enabled)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage the feature-gated representation-edge slice.")
    parser.add_argument("--root", type=Path, required=True, help="Canonical LightSpeed Desktop shell root.")
    parser.add_argument("--apply", action="store_true", help="Apply the reversible migration.")
    parser.add_argument("--seed", action="store_true", help="Seed three bounded proof graphs and review packets.")
    parser.add_argument("--rollback", action="store_true", help="Drop only representation-edge tables.")
    parser.add_argument("--status", action="store_true", help="Report feature and migration state.")
    args = parser.parse_args(argv)
    store = build_store(args.root)
    review_queue, decisions, outbox = default_review_paths(args.root)
    result: dict[str, Any] = {"feature_flag": FEATURE_FLAG}
    if args.rollback:
        result["rollback"] = store.rollback_migration()
    else:
        if args.apply or args.seed:
            result["migration"] = store.apply_migration()
        if args.seed:
            result["seed"] = store.seed_proof_graphs(
                review_queue_path=review_queue,
                decision_path=decisions,
                local_outbox=outbox,
            )
    if args.status or not (args.apply or args.seed or args.rollback):
        result["status"] = store.status()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
