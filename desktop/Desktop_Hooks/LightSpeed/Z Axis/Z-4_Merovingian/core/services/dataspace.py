"""
Dataspace Service - Immutable Job Outputs + Manifests

Implements the V1 canonical rule-set:
- Every action is a Job
- Every job produces a manifest.json
- Artifacts are immutable (new run => new folder)
- Operational events and routes use the shared SQLite authority.

Dataspace root (local): `LightSpeed/w6/data/`
Layout:
  w6/data/<tool_key>/<YYYYMMDD_HHMMSS_jobid>/
    manifest.json
    inputs.json        (optional)
    result.json
    run.log            (optional)
    ...
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from lightspeed_runtime.operational_store import (
    OperationalStore,
    default_operational_db_path,
)

from .logger import get_services_logger

logger = get_services_logger()

# CODEX NOTE (2026-07-05):
# - Z Direct operational streams are stored once in the shared SQLite authority.
# - Registry writes are UI-gated by Trinity (commit actions), but the service here
#   performs format/validation/compatibility and atomic writes.
# - Compatibility: older repos may have `objects.json` / `tasks.json` as `{}` or a
#   dict mapping instead of a list; reads normalize into a list of dict items.

try:
    from core.config.paths import W6_DATA_ROOT  # type: ignore
except Exception:
    W6_DATA_ROOT = Path.cwd() / "w6" / "data"

try:
    from core.config.paths import (  # type: ignore
        TRINITY_ROOT,
        NEO_ROOT,
        ARCHITECT_ROOT,
        CONSTRUCT_ROOT,
        MORPHEUS_ROOT,
        ORACLE_ROOT,
        SMITH_ROOT,
        MEROVINGIAN_ROOT,
        initialize_z_direct_structure,
    )
except Exception:
    TRINITY_ROOT = None
    NEO_ROOT = None
    ARCHITECT_ROOT = None
    CONSTRUCT_ROOT = None
    MORPHEUS_ROOT = None
    ORACLE_ROOT = None
    SMITH_ROOT = None
    MEROVINGIAN_ROOT = None
    initialize_z_direct_structure = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_tool_key(value: str) -> str:
    value = (value or "unknown").strip().lower()
    out = []
    for ch in value:
        if ch.isalnum() or ch in ("-", "_"):
            out.append(ch)
        else:
            out.append("_")
    return "".join(out).strip("_") or "unknown"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _stable_item_digest(item: Dict[str, Any]) -> str:
    """
    Stable digest for a registry item (used for change tracking / de-dup).
    """
    try:
        payload = json.dumps(item, sort_keys=True, ensure_ascii=False).encode("utf-8", errors="replace")
    except Exception:
        payload = str(item).encode("utf-8", errors="replace")
    return sha256_bytes(payload)


@dataclass(frozen=True)
class ArtifactRef:
    path: str
    sha256: str
    size_bytes: int
    kind: str = "artifact"
    media_type: Optional[str] = None
    name: Optional[str] = None


class DataspaceService:
    """
    Creates immutable job run directories and writes the canonical `manifest.json`.
    """

    def __init__(self, dataspace_root: Optional[Path] = None):
        self.root = Path(dataspace_root) if dataspace_root is not None else Path(W6_DATA_ROOT)
        try:
            self.root.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def job_run_dir(self, tool_key: str, job_id: int, when: Optional[datetime] = None) -> Path:
        tool_key = _safe_tool_key(tool_key)
        when = when or datetime.now()
        ts = when.strftime("%Y%m%d_%H%M%S")
        return self.root / tool_key / f"{ts}_{job_id}"

    def build_manifest(
        self,
        *,
        job_id: int,
        tool_key: str,
        z_context: str,
        status: str,
        inputs: Optional[List[Dict[str, Any]]] = None,
        outputs: Optional[List[Dict[str, Any]]] = None,
        config: Optional[Dict[str, Any]] = None,
        timings: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        task_id: Optional[int] = None,
        project_id: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "schema_version": "v1",
            "job": {
                "id": job_id,
                "tool_key": _safe_tool_key(tool_key),
                "status": status,
                "z_context": z_context,
                "task_id": task_id,
                "project_id": project_id,
                "created_at": _utc_now_iso(),
            },
            "inputs": inputs or [],
            "outputs": outputs or [],
            "config": config or {},
            "timings": timings or {},
            "tags": tags or [],
            "extra": extra or {},
        }

    def write_manifest(self, run_dir: Path, manifest: Dict[str, Any]) -> Path:
        path = Path(run_dir) / "manifest.json"
        write_json(path, manifest)
        return path

    def materialize_output_json(
        self,
        run_dir: Path,
        filename: str,
        payload: Any,
        *,
        kind: str = "result",
        name: Optional[str] = None,
    ) -> ArtifactRef:
        out_path = (Path(run_dir) / filename).resolve()
        write_json(out_path, payload)
        sha = sha256_file(out_path)
        size = out_path.stat().st_size if out_path.exists() else 0
        return ArtifactRef(
            path=str(out_path),
            sha256=sha,
            size_bytes=size,
            kind=kind,
            media_type="application/json",
            name=name or filename,
        )


_DATASPACE: Optional[DataspaceService] = None


def get_dataspace() -> DataspaceService:
    global _DATASPACE
    if _DATASPACE is None:
        _DATASPACE = DataspaceService()
    return _DATASPACE


def _floor_roots_for_z_direct() -> Dict[str, Path]:
    """
    Canonical 8-floor stack (Z-4..Z+3) root mapping for Z Direct operations.
    """
    out: Dict[str, Path] = {}
    if isinstance(MEROVINGIAN_ROOT, Path):
        out["Z-4"] = MEROVINGIAN_ROOT
    if isinstance(SMITH_ROOT, Path):
        out["Z-3"] = SMITH_ROOT
    if isinstance(ORACLE_ROOT, Path):
        out["Z-2"] = ORACLE_ROOT
    if isinstance(MORPHEUS_ROOT, Path):
        out["Z-1"] = MORPHEUS_ROOT
    if isinstance(CONSTRUCT_ROOT, Path):
        out["Z0"] = CONSTRUCT_ROOT
    if isinstance(ARCHITECT_ROOT, Path):
        out["Z+1"] = ARCHITECT_ROOT
    if isinstance(NEO_ROOT, Path):
        out["Z+2"] = NEO_ROOT
    if isinstance(TRINITY_ROOT, Path):
        out["Z+3"] = TRINITY_ROOT
    return out


def _ensure_z_direct_scaffold() -> None:
    try:
        if callable(initialize_z_direct_structure):
            initialize_z_direct_structure()
    except Exception:
        pass


class ZDirectService:
    """
    Z Direct interface backed by SQLite operational events and atomic registries.

    Notes:
    - This does not enforce schema beyond the "envelope" helpers here.
    - Trinity UI is expected to be the approval gate for schema/object commits.
    """

    def __init__(
        self,
        *,
        root: Optional[Path] = None,
        floor_roots: Optional[Dict[str, Path]] = None,
    ):
        if floor_roots is None:
            _ensure_z_direct_scaffold()
            self._floor_roots = _floor_roots_for_z_direct()
        else:
            self._floor_roots = {
                str(channel): Path(path)
                for channel, path in floor_roots.items()
            }
        if root is not None:
            self.root = Path(root)
        elif isinstance(MEROVINGIAN_ROOT, Path):
            self.root = MEROVINGIAN_ROOT.parent.parent
        elif self._floor_roots:
            self.root = next(iter(self._floor_roots.values())).parent.parent
        else:
            self.root = Path.cwd()
        self._operational_path = default_operational_db_path(self.root)
        self._store = OperationalStore(self._operational_path)

    def z_direct_root(self, channel: str) -> Path:
        root = self._floor_roots.get(channel)
        if root is None:
            raise KeyError(f"Unknown Z Direct channel: {channel}")
        return (root / "Z Direct").resolve()

    def _jsonl_path(self, channel: str, kind: str) -> Path:
        if kind not in ("events", "objects"):
            raise ValueError(f"Unsupported jsonl kind: {kind}")
        self.z_direct_root(channel)
        return self._operational_path

    def _json_path(self, channel: str, name: str) -> Path:
        if name not in ("objects", "tasks"):
            raise ValueError(f"Unsupported json name: {name}")
        return self.z_direct_root(channel) / f"{name}.json"

    def _ensure_channel_dir(self, floor_channel: str, peer_channel: str) -> Path:
        """
        Return the operational authority without creating channel directories.
        """
        self.z_direct_root(floor_channel)
        self.z_direct_root(peer_channel)
        return self._operational_path

    def channel_inbox_path(self, *, to_channel: str, from_channel: str) -> Path:
        return self._ensure_channel_dir(to_channel, from_channel)

    def channel_outbox_path(self, *, from_channel: str, to_channel: str) -> Path:
        return self._ensure_channel_dir(from_channel, to_channel)

    def append_channel_inbox(self, *, to_channel: str, from_channel: str, payload: Dict[str, Any]) -> Path:
        """Record a directed payload once and index its source-to-target route."""
        return self._record_payload(
            payload,
            source_channel=from_channel,
            target_channel=to_channel,
        )

    def append_channel_outbox(self, *, from_channel: str, to_channel: str, payload: Dict[str, Any]) -> Path:
        """Record a directed payload once and index its source-to-target route."""
        return self._record_payload(
            payload,
            source_channel=from_channel,
            target_channel=to_channel,
        )

    def list_channel_peers(self, channel: str) -> List[str]:
        """
        List peer-channel folders present under `Z Direct/channels/` for the given channel.

        This is best-effort and excludes template/internal folders.
        """
        self.z_direct_root(channel)
        return self._store.peers(channel)

    def tail_channel_inbox(self, *, to_channel: str, from_channel: str, limit: int = 200) -> List[Dict[str, Any]]:
        """Return recent directed payloads received from a floor."""
        return self._decode_rows(
            self._store.routed(
                source=from_channel,
                target=to_channel,
                limit=limit,
            )
        )

    def tail_channel_outbox(self, *, from_channel: str, to_channel: str, limit: int = 200) -> List[Dict[str, Any]]:
        """Return recent directed payloads sent to a floor."""
        return self._decode_rows(
            self._store.routed(
                source=from_channel,
                target=to_channel,
                limit=limit,
            )
        )

    def _normalize_registry_payload(self, data: Any) -> List[Dict[str, Any]]:
        """
        Normalize older/loose registry formats into a stable list[dict] form.

        Supported inputs:
        - list[dict] (canonical)
        - {"items": [...]} (legacy wrapper)
        - { "<id>": {...}, ... } (legacy mapping form)
        - {} or None -> []
        """
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]

        if isinstance(data, dict):
            items = data.get("items")
            if isinstance(items, list):
                return [x for x in items if isinstance(x, dict)]

            out: List[Dict[str, Any]] = []
            for k, v in data.items():
                if isinstance(v, dict):
                    obj = dict(v)
                    # If the mapping key looks like an identity, preserve it.
                    if "id" not in obj and isinstance(k, str) and k.strip():
                        obj["id"] = k.strip()
                    out.append(obj)
            return out

        return []

    def append_event(self, channel: str, payload: Dict[str, Any]) -> Path:
        return self._record_payload(
            payload,
            source_channel=channel,
            forced_kind="event",
        )

    def append_object(self, channel: str, payload: Dict[str, Any]) -> Path:
        return self._record_payload(
            payload,
            source_channel=channel,
            forced_kind="object",
        )

    @staticmethod
    def _payload_digest(payload: Dict[str, Any]) -> str:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _payload_kind(payload: Dict[str, Any], forced_kind: Optional[str]) -> str:
        candidate = forced_kind or payload.get("kind") or "event"
        return str(candidate).strip().lower() or "event"

    def _record_payload(
        self,
        payload: Dict[str, Any],
        *,
        source_channel: Optional[str] = None,
        target_channel: Optional[str] = None,
        forced_kind: Optional[str] = None,
    ) -> Path:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")
        digest = self._payload_digest(payload)
        event_id = f"z-direct:{digest}"
        payload_source = payload.get("channel") or payload.get("source_floor")
        payload_target = payload.get("target_floor")
        source = str(payload_source or source_channel or "").strip() or None
        target = str(payload_target or "").strip() or None
        kind = self._payload_kind(payload, forced_kind)
        self._store.record_event(
            {
                "event_id": event_id,
                "kind": f"z_direct_{kind}",
                "source": source,
                "target": target,
                "status": payload.get("status"),
                "recorded_at": payload.get("created_at") or payload.get("timestamp"),
                "payload": payload,
            }
        )
        if source_channel and target_channel:
            self._store.record_route(
                event_id=event_id,
                source=source_channel,
                target=target_channel,
                recorded_at=str(
                    payload.get("created_at")
                    or payload.get("timestamp")
                    or _utc_now_iso()
                ),
            )
        return self._operational_path

    @staticmethod
    def _decode_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        decoded: List[Dict[str, Any]] = []
        for row in reversed(rows):
            try:
                stored = json.loads(str(row.get("payload_json") or "{}"))
                payload = stored.get("payload")
                if isinstance(payload, dict):
                    decoded.append(payload)
            except Exception:
                continue
        return decoded

    def append_jsonl(self, path: Path, payload: Dict[str, Any]) -> Path:
        """Compatibility adapter for callers that have not moved to typed methods."""
        kind = "object" if Path(path).stem == "objects" else "event"
        return self._record_payload(payload, forced_kind=kind)

    def read_jsonl_tail(self, path: Path, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Read last N JSONL records (best effort; tolerant of partial/invalid lines).
        """
        limit = max(0, int(limit))
        if limit == 0 or not path.exists():
            return []
        lines: List[str] = []
        try:
            with open(path, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                chunk = 8192
                buf = b""
                pos = size
                while pos > 0 and len(lines) <= (limit + 5):
                    read_size = chunk if pos - chunk > 0 else pos
                    pos -= read_size
                    f.seek(pos)
                    buf = f.read(read_size) + buf
                    while b"\n" in buf:
                        idx = buf.rfind(b"\n")
                        line = buf[idx + 1 :]
                        buf = buf[:idx]
                        if line:
                            try:
                                lines.append(line.decode("utf-8", errors="replace"))
                            except Exception:
                                pass
                        if len(lines) >= (limit + 5):
                            break
                if buf and len(lines) < (limit + 5):
                    try:
                        lines.append(buf.decode("utf-8", errors="replace"))
                    except Exception:
                        pass
        except Exception:
            return []

        # `lines` is collected newest-first (we scan backwards from EOF). Select the
        # newest `limit` lines from the *front* of the list, then reverse to return
        # chronological order.
        out: List[Dict[str, Any]] = []
        selected = lines[:limit]
        for raw in reversed(selected):
            raw = (raw or "").strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict):
                    out.append(obj)
            except Exception:
                continue
        return out

    def tail_events(self, channel: str, limit: int = 200) -> List[Dict[str, Any]]:
        self.z_direct_root(channel)
        return self._decode_rows(
            self._store.recent(
                limit=limit,
                kind="z_direct_event",
                source=channel,
            )
        )

    def tail_objects(self, channel: str, limit: int = 200) -> List[Dict[str, Any]]:
        self.z_direct_root(channel)
        return self._decode_rows(
            self._store.recent(
                limit=limit,
                kind="z_direct_object",
                source=channel,
            )
        )

    def read_registry(self, channel: str, *, name: str = "objects") -> List[Dict[str, Any]]:
        """
        Read the floor registry JSON (defaults to `objects.json`).

        This file is intended to hold the latest approved, durable registry entries
        (distinct from the append-only JSONL streams).
        """
        path = self._json_path(channel, name)
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            return self._normalize_registry_payload(data)
        except Exception:
            return []

    def upsert_registry_item(
        self,
        channel: str,
        item: Dict[str, Any],
        *,
        name: str = "objects",
        key_fields: Tuple[str, ...] = ("kind", "id"),
    ) -> Path:
        """
        Upsert a registry item into `<name>.json` (atomic write).

        Default identity is (kind, id) so a single registry can contain both object and schema
        entries without collisions.
        """
        path = self._json_path(channel, name)
        items = self.read_registry(channel, name=name)

        def _key(obj: Dict[str, Any]) -> Tuple[Any, ...]:
            return tuple(obj.get(k) for k in key_fields)

        now = _utc_now_iso()
        new_item = dict(item or {})
        # Preserve existing created_at if present for the same identity.
        existing_created_at: Optional[str] = None
        target_key = _key(new_item)
        for existing in items:
            if isinstance(existing, dict) and _key(existing) == target_key:
                existing_created_at = str(existing.get("created_at") or "") or None
                break

        new_item.setdefault("created_at", existing_created_at or now)
        new_item["updated_at"] = now
        new_item["sha256"] = _stable_item_digest(new_item)

        out: List[Dict[str, Any]] = []
        replaced = False
        for existing in items:
            if not isinstance(existing, dict):
                continue
            if _key(existing) == target_key:
                out.append(new_item)
                replaced = True
            else:
                out.append(existing)
        if not replaced:
            out.append(new_item)

        write_json(path, out)
        return path

    def commit_envelope_to_registry(
        self,
        channel: str,
        env: Dict[str, Any],
        *,
        registry: str = "objects",
        committed_by: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Validate a staged Z Direct envelope and commit its payload into a durable registry.

        Trinity UI should call this instead of directly writing registry files.
        """
        ok, errors = self.validate_envelope(env, for_channel=channel)
        if not ok:
            raise ValueError("Envelope validation failed: " + "; ".join(errors))

        if env.get("kind") != "object":
            raise ValueError("Only object envelopes may be committed to a durable registry")

        payload = env.get("payload") if isinstance(env, dict) else None
        if not isinstance(payload, dict):
            raise ValueError("Envelope payload must be a dict")

        kind = payload.get("kind")
        obj_id = payload.get("id")

        # Accept numeric IDs but normalize to string for a stable registry key.
        if isinstance(obj_id, (int, float)):
            obj_id = str(obj_id)
            payload = dict(payload)
            payload["id"] = obj_id

        # Attach a minimal provenance block (does not mutate the staged JSONL entry).
        committed_at = _utc_now_iso()
        provenance = {
            "envelope_created_at": env.get("created_at"),
            "envelope_channel": env.get("channel"),
            "envelope_kind": env.get("kind"),
            "z_context": env.get("z_context"),
            "source": env.get("source"),
            "job_id": env.get("job_id"),
            "tool_key": env.get("tool_key"),
            "committed_at": committed_at,
            "committed_by": committed_by or {},
        }

        item = dict(payload)
        # Preserve any existing provenance by nesting it.
        if isinstance(item.get("provenance"), dict):
            item["provenance"] = {**item["provenance"], **provenance}
        else:
            item["provenance"] = provenance

        return self.upsert_registry_item(channel, item, name=registry, key_fields=("kind", "id"))

    def make_envelope(
        self,
        *,
        kind: str,
        channel: str,
        payload: Dict[str, Any],
        z_context: str,
        source: str,
        job_id: Optional[int] = None,
        tool_key: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return {
            "schema_version": "z-direct-v1",
            "kind": kind,
            "channel": channel,
            "z_context": z_context,
            "created_at": _utc_now_iso(),
            "source": source,
            "job_id": job_id,
            "tool_key": tool_key,
            "tags": tags or [],
            "payload": payload,
        }

    def validate_envelope(self, env: Any, *, for_channel: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Best-effort validation for a Z Direct envelope.

        This is intentionally lightweight (no jsonschema dependency). It is used
        by Trinity's approval gate to catch obvious problems before writing to a
        durable registry.
        """
        errors: List[str] = []
        if not isinstance(env, dict):
            return False, ["Envelope must be a dict"]

        if env.get("schema_version") != "z-direct-v1":
            errors.append("schema_version must be 'z-direct-v1'")

        env_kind = env.get("kind")
        if env_kind not in ("event", "object"):
            errors.append("kind must be 'event' or 'object'")

        ch = env.get("channel")
        if not isinstance(ch, str) or not ch.strip():
            errors.append("channel is required")

        payload = env.get("payload")
        if not isinstance(payload, dict):
            errors.append("payload must be a dict")
            return False, errors

        # Envelope kind specific checks
        if env_kind == "object":
            pk = payload.get("kind")
            pid = payload.get("id")
            if not isinstance(pk, str) or not pk.strip():
                errors.append("payload.kind is required for object envelopes")
            if pid is None or (isinstance(pid, str) and not pid.strip()):
                errors.append("payload.id is required for object envelopes")
        elif env_kind == "event":
            # Some events use `type`, others are action receipts (commit/reject).
            if not (isinstance(payload.get("type"), str) and str(payload.get("type")).strip()) and not (
                isinstance(payload.get("action"), str) and str(payload.get("action")).strip()
            ):
                errors.append("event payload should include payload.type or payload.action")

        # Payload-kind specific checks (non-fatal for unknown kinds).
        try:
            pkind = payload.get("kind")
            if isinstance(pkind, str):
                # Prefer validating against a committed schema registry for the target channel.
                target = for_channel if isinstance(for_channel, str) and for_channel.strip() else ch
                errors.extend(self._validate_payload_kind(target, pkind, payload))
        except Exception:
            pass

        return (len(errors) == 0), errors

    def _get_committed_schema(self, channel: str, payload_kind: str) -> Optional[Dict[str, Any]]:
        """
        Load a committed schema for `payload_kind` from the target channel registry.

        Convention: schemas are stored in `objects.json` as items with:
          - kind == "schema"
          - id == <payload_kind>
          - json_schema (dict) or schema (dict)
        """
        try:
            if not isinstance(channel, str) or not channel.strip():
                return None
            items = self.read_registry(channel, name="objects")
            for it in items or []:
                if not isinstance(it, dict):
                    continue
                if it.get("kind") != "schema":
                    continue
                if str(it.get("id") or "").strip() != str(payload_kind or "").strip():
                    continue
                js = it.get("json_schema") if isinstance(it.get("json_schema"), dict) else None
                if js is None:
                    js = it.get("schema") if isinstance(it.get("schema"), dict) else None
                if isinstance(js, dict):
                    return js
        except Exception:
            return None
        return None

    def _validate_payload_kind(self, channel: str, pkind: str, payload: Dict[str, Any]) -> List[str]:
        """
        Validate common payload kinds used across the Z axis.

        Unknown kinds are allowed (schema is evolving); this only adds guardrails.
        """
        out: List[str] = []
        k = (pkind or "").strip().lower()
        if not k:
            return out

        # If a committed schema exists, prefer it (so operators can evolve shapes).
        schema = self._get_committed_schema(channel, pkind)
        if isinstance(schema, dict):
            try:
                required = schema.get("required") if isinstance(schema, dict) else None
                if isinstance(required, list):
                    for field in required:
                        if not isinstance(field, str) or not field.strip():
                            continue
                        v = payload.get(field)
                        if v is None or (isinstance(v, str) and not v.strip()):
                            out.append(f"payload.{field} is required for kind={pkind} (schema)")

                props = schema.get("properties") if isinstance(schema, dict) else None
                if isinstance(props, dict):
                    for field, spec in props.items():
                        if not isinstance(field, str) or field not in payload:
                            continue
                        if not isinstance(spec, dict):
                            continue
                        typ = spec.get("type")
                        if not isinstance(typ, str) or not typ.strip():
                            continue
                        val = payload.get(field)
                        if val is None:
                            continue
                        ok = True
                        t = typ.strip().lower()
                        if t == "string":
                            ok = isinstance(val, str)
                        elif t == "integer":
                            ok = isinstance(val, int) and not isinstance(val, bool)
                        elif t == "number":
                            ok = isinstance(val, (int, float)) and not isinstance(val, bool)
                        elif t == "object":
                            ok = isinstance(val, dict)
                        elif t == "array":
                            ok = isinstance(val, list)
                        elif t == "boolean":
                            ok = isinstance(val, bool)
                        if not ok:
                            out.append(f"payload.{field} should be {t} for kind={pkind} (schema)")
            except Exception:
                pass
            return out

        def _req(field: str) -> None:
            v = payload.get(field)
            if v is None or (isinstance(v, str) and not v.strip()):
                out.append(f"payload.{field} is required for kind={pkind}")

        if k == "task":
            _req("id")
            _req("title")
            _req("status")
        elif k == "vault_file":
            _req("id")
            _req("sha256")
            _req("name")
            _req("path")
        elif k == "project":
            _req("id")
            # Accept either name or title.
            if not (payload.get("name") or payload.get("title")):
                out.append("payload.name or payload.title is required for kind=project")
        elif k == "ai_response":
            _req("id")
            _req("type")
        elif k == "simulation_result":
            _req("id")
            _req("sim_type")
        elif k == "bento_widget":
            _req("id")
            _req("title")
            _req("floor")
            _req("widget_type")
        elif k == "action_def":
            _req("id")
            _req("title")
            _req("host_action")
        elif k == "simulation_def":
            _req("id")
            _req("title")
            _req("sim_type")
        elif k == "workflow_def":
            _req("id")
            _req("title")
        elif k == "schema":
            _req("id")
            _req("name")
            # Schema content should exist under one of these keys.
            if not (isinstance(payload.get("json_schema"), dict) or isinstance(payload.get("schema"), dict)):
                out.append("payload.json_schema or payload.schema is required for kind=schema")

        return out

    def builtin_schema_payloads(self) -> List[Dict[str, Any]]:
        """
        Built-in JSON-schema-like payload schemas for common object kinds.

        These are intended as a bootstrap set. Operators can commit them as
        `kind="schema"` objects into a floor registry and then evolve them there.
        """
        def _schema(name: str, required: List[str], properties: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": name,
                "type": "object",
                "additionalProperties": True,
                "required": required,
                "properties": properties,
            }

        return [
            {
                "kind": "schema",
                "id": "task",
                "name": "task",
                "json_schema": _schema(
                    "task",
                    ["kind", "id", "title", "status"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "status": {"type": "string"},
                        "priority": {"type": "integer"},
                        "project_id": {"type": "string"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "vault_file",
                "name": "vault_file",
                "json_schema": _schema(
                    "vault_file",
                    ["kind", "id", "sha256", "name", "path"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "sha256": {"type": "string"},
                        "name": {"type": "string"},
                        "path": {"type": "string"},
                        "source_name": {"type": "string"},
                        "source_path": {"type": "string"},
                        "size_bytes": {"type": "integer"},
                        "mime_type": {"type": "string"},
                        "task_id": {"type": "string"},
                        "job_id": {"type": "string"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "ai_response",
                "name": "ai_response",
                "json_schema": _schema(
                    "ai_response",
                    ["kind", "id", "type"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "type": {"type": "string"},
                        "request": {"type": "object"},
                        "result": {"type": "object"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "simulation_result",
                "name": "simulation_result",
                "json_schema": _schema(
                    "simulation_result",
                    ["kind", "id", "sim_type"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "sim_type": {"type": "string"},
                        "params": {"type": "object"},
                        "result": {"type": "object"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "bento_widget",
                "name": "bento_widget",
                "json_schema": _schema(
                    "bento_widget",
                    ["kind", "id", "title", "floor", "widget_type"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "floor": {"type": "string"},
                        "widget_type": {"type": "string"},
                        "config": {"type": "object"},
                        "enabled": {"type": "boolean"},
                        "tags": {"type": "array"},
                        "metadata": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "action_def",
                "name": "action_def",
                "json_schema": _schema(
                    "action_def",
                    ["kind", "id", "title", "host_action"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "category": {"type": "string"},
                        "host_action": {"type": "string"},
                        "host_action_args": {"type": "object"},
                        "params": {"type": "array"},
                        "safety": {"type": "object"},
                        "enabled": {"type": "boolean"},
                        "tags": {"type": "array"},
                        "metadata": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "simulation_def",
                "name": "simulation_def",
                "json_schema": _schema(
                    "simulation_def",
                    ["kind", "id", "title", "sim_type"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "sim_type": {"type": "string"},
                        "entrypoint": {"type": "object"},
                        "params": {"type": "array"},
                        "output_kind": {"type": "string"},
                        "enabled": {"type": "boolean"},
                        "tags": {"type": "array"},
                        "metadata": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "workflow_def",
                "name": "workflow_def",
                "json_schema": _schema(
                    "workflow_def",
                    ["kind", "id", "title", "steps"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "steps": {"type": "array"},
                        "enabled": {"type": "boolean"},
                        "tags": {"type": "array"},
                        "metadata": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "project",
                "name": "project",
                "json_schema": _schema(
                    "project",
                    ["kind", "id"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                    },
                ),
            },
            # Knowledge + learning primitives (Cognigrex spine).
            {
                "kind": "schema",
                "id": "knowledge_node",
                "name": "knowledge_node",
                "json_schema": _schema(
                    "knowledge_node",
                    ["kind", "id", "concept", "definition"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "concept": {"type": "string"},
                        "definition": {"type": "string"},
                        "domain": {"type": "string"},
                        "related_concepts": {"type": "array"},
                        "sources": {"type": "array"},
                        "confidence": {"type": "number"},
                        "metadata": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "citation",
                "name": "citation",
                "json_schema": _schema(
                    "citation",
                    ["kind", "id", "vault_file_id"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "vault_file_id": {"type": "string"},
                        "note": {"type": "string"},
                        "span": {"type": "object"},
                        "quote_hash": {"type": "string"},
                        "metadata": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "workspace",
                "name": "workspace",
                "json_schema": _schema(
                    "workspace",
                    ["kind", "id", "name"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "domain": {"type": "string"},
                        "purpose": {"type": "string"},
                        "datasets": {"type": "array"},
                        "queries": {"type": "array"},
                        "outputs": {"type": "array"},
                        "metadata": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "research_query",
                "name": "research_query",
                "json_schema": _schema(
                    "research_query",
                    ["kind", "id", "query_text", "domain"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "workspace_id": {"type": "string"},
                        "query_text": {"type": "string"},
                        "domain": {"type": "string"},
                        "context": {"type": "object"},
                        "results": {"type": "array"},
                        "confidence": {"type": "number"},
                        "metadata": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "dataset",
                "name": "dataset",
                "json_schema": _schema(
                    "dataset",
                    ["kind", "id", "name", "path"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "domain": {"type": "string"},
                        "dataset_type": {"type": "string"},
                        "path": {"type": "string"},
                        "description": {"type": "string"},
                        "metadata": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "experiment_run",
                "name": "experiment_run",
                "json_schema": _schema(
                    "experiment_run",
                    ["kind", "id", "title", "status"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "workspace_id": {"type": "string"},
                        "status": {"type": "string"},
                        "inputs": {"type": "object"},
                        "toolchain": {"type": "array"},
                        "outputs": {"type": "array"},
                        "metadata": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
            },
            {
                "kind": "schema",
                "id": "learning_module",
                "name": "learning_module",
                "json_schema": _schema(
                    "learning_module",
                    ["kind", "id", "title"],
                    {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "objectives": {"type": "array"},
                        "prereqs": {"type": "array"},
                        "steps": {"type": "array"},
                        "assessments": {"type": "array"},
                        "metadata": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
            },
        ]


_Z_DIRECT: Optional[ZDirectService] = None


def get_z_direct() -> ZDirectService:
    global _Z_DIRECT
    if _Z_DIRECT is None:
        _Z_DIRECT = ZDirectService()
    return _Z_DIRECT
