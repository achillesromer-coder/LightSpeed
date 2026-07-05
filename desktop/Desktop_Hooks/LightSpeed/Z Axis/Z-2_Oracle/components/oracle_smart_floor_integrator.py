#!/usr/bin/env python
"""
Oracle Smart Floor Integrator
Automatically processes, categorizes, and distributes all files across Z-floors

Architecture:
1. Oracle receives all base files (archive)
2. Smith queues extraction and analysis tasks
3. SmartFloor system distributes objects to appropriate floors
4. Encyclopedia system (3 volumes) maintains empirical knowledge
5. Multilingual dictionary provides foundational data

NOTE (Codex 2026-02-03): Oracle stages Z Direct envelopes only (append-only) and mirrors them to
Trinity's directed inbox/outbox for review; it does not write durable registries (Trinity is the gate).
It also stages a bootstrap `schema` proposal for `vault_file` when missing (so IT can commit it).

Author: Romer Industries / EMASSC
Version: 0.9.5
Date: December 31, 2025
"""

import os
import json
import sqlite3
import hashlib
import mimetypes
import csv
import tempfile
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import re
import importlib.util
import sys

# Core services
try:
    from core.services import (
        get_db,
        get_event_bus,
        get_storage,
        get_oracle_logger,
        get_services_logger,
        get_z_direct,
    )
    HAS_SERVICES = True
except ImportError:
    # Best-effort bootstrap when this module is loaded via file-loader (e.g., from Trinity widgets).
    try:
        def _find_lightspeed_root(start: Path) -> Path:
            start = start.resolve()
            for cand in (start, *start.parents):
                if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                    return cand
            return start.parent

        _LS_ROOT = _find_lightspeed_root(Path(__file__))
        if str(_LS_ROOT) not in sys.path:
            sys.path.insert(0, str(_LS_ROOT))
        _Z_AXIS = _LS_ROOT / "Z Axis"
        if _Z_AXIS.exists() and str(_Z_AXIS) not in sys.path:
            sys.path.insert(0, str(_Z_AXIS))
        _MEROV = _Z_AXIS / "Z-4_Merovingian"
        if _MEROV.exists() and str(_MEROV) not in sys.path:
            sys.path.insert(0, str(_MEROV))

        from core.services import (
            get_db,
            get_event_bus,
            get_storage,
            get_oracle_logger,
            get_services_logger,
            get_z_direct,
        )
        HAS_SERVICES = True
    except Exception:
        HAS_SERVICES = False


class OracleSmartFloorIntegrator:
    """
    Oracle Smart Floor Integrator

    Manages automatic file ingestion, analysis, and Z-floor distribution.
    Coordinates with Smith for task queuing and priority management.
    """

    def __init__(
        self,
        oracle_vault_path: str = None,
        *,
        db=None,
        event_bus=None,
        storage=None,
        z_direct=None,
        **_ignored,
    ):
        """Initialize Oracle Smart Floor Integrator (dependency-injection friendly)."""
        if HAS_SERVICES:
            try:
                self.logger = get_oracle_logger()
            except Exception:
                self.logger = get_services_logger()
        else:
            self.logger = None
        # Prefer injected services (from N.py / FloorLoader) but keep standalone behavior.
        self.db = db if db is not None else (get_db() if HAS_SERVICES else None)
        self.event_bus = event_bus if event_bus is not None else (get_event_bus() if HAS_SERVICES else None)
        self.storage = storage if storage is not None else (get_storage() if HAS_SERVICES else None)
        self.z_direct = z_direct if z_direct is not None else (get_z_direct() if HAS_SERVICES else None)
        self._encyclopedia = None
        self._encyclopedia_volume_enum = None
        # Avoid repeated Z Direct schema proposal staging within a single process.
        self._schema_proposals_staged = set()

        # Oracle vault (archive root)
        if oracle_vault_path:
            self.vault_path = Path(oracle_vault_path)
        else:
            try:
                from core.config.paths import ORACLE_ARCHIVE  # type: ignore
                self.vault_path = Path(ORACLE_ARCHIVE) / "vault"
            except Exception:
                # Fallback: keep it relative to the Oracle floor
                self.vault_path = Path(__file__).resolve().parent.parent / "archive" / "vault"

        self.vault_path.mkdir(parents=True, exist_ok=True)

        # Ingestion queue
        self.ingestion_queue = []
        self.processing_status = {}

        # Z-floor routing table
        self.floor_routing = {
            # Setup/onboarding was consolidated into Trinity (Z+3).
            'Z+3_Trinity': ['wizard', 'setup', 'onboarding', 'ui', 'theme', 'visualization', 'frontend'],
            'Z+2_Neo': ['ai', 'ml', 'ollama', 'gpt', 'training'],
            'Z+1_Architect': ['task', 'plan', 'mission', 'goal', 'timeline'],
            'Z0_TheConstruct': ['physics', 'simulation', 'raphael', 'orbital', 'quantum', '3d'],
            'Z-1_Morpheus': ['knowledge', 'documentation', 'learning', 'analysis', 'code'],
            'Z-2_Oracle': ['archive', 'ip', 'vault', 'document', 'legal'],
            'Z-3_Smith': ['automation', 'workflow', 'job', 'schedule', 'sop'],
            'Z-4_Merovingian': ['system', 'health', 'diagnostics', 'monitoring', 'database']
        }

        if self.logger:
            self.logger.info("[OracleSmartFloor] Oracle Smart Floor Integrator initialized")

        # Best-effort: ensure Oracle-produced object kinds have an explicit schema proposal staged
        # for Trinity review. Do not auto-commit here; Trinity is the approval gate.
        try:
            self._ensure_schema_proposal_staged("vault_file")
        except Exception:
            pass

    def _get_z_direct_service(self):
        """Return a Z Direct service instance if available, otherwise None."""
        if self.z_direct is not None:
            return self.z_direct
        if HAS_SERVICES:
            try:
                return get_z_direct()
            except Exception:
                return None
        return None

    def _ensure_schema_proposal_staged(self, payload_kind: str) -> None:
        """
        Stage a schema proposal envelope for `payload_kind` into Z-2 streams (and Trinity inbox)
        if it is neither committed nor already staged.
        """
        payload_kind = str(payload_kind or "").strip()
        if not payload_kind:
            return
        if payload_kind in self._schema_proposals_staged:
            return

        zd = self._get_z_direct_service()
        if zd is None:
            return

        channel = "Z-2"
        z_context = "Z-2_Oracle"

        # 1) If the schema is already committed, do nothing.
        try:
            committed = zd.read_registry(channel, name="objects")
            for item in committed or []:
                if isinstance(item, dict) and item.get("kind") == "schema" and str(item.get("id")) == payload_kind:
                    self._schema_proposals_staged.add(payload_kind)
                    return
        except Exception:
            pass

        # 2) If it was already staged recently (tail scan), do nothing.
        try:
            for env in zd.tail_objects(channel, limit=1500) or []:
                if not isinstance(env, dict) or env.get("kind") != "object":
                    continue
                payload = env.get("payload")
                if not isinstance(payload, dict):
                    continue
                if payload.get("kind") == "schema" and str(payload.get("id")) == payload_kind:
                    self._schema_proposals_staged.add(payload_kind)
                    return
        except Exception:
            pass

        # 3) Build a schema object from Z Direct builtins (bootstrap set).
        schema_obj = None
        try:
            for obj in zd.builtin_schema_payloads() or []:
                if isinstance(obj, dict) and obj.get("kind") == "schema" and str(obj.get("id")) == payload_kind:
                    schema_obj = dict(obj)
                    break
        except Exception:
            schema_obj = None

        if not isinstance(schema_obj, dict):
            return

        env = zd.make_envelope(
            kind="object",
            channel=channel,
            z_context=z_context,
            source="oracle.schema_proposal",
            tool_key="oracle.schema_proposal",
            tags=["oracle", "schema_proposal"],
            payload=schema_obj,
        )

        try:
            zd.append_object(channel, env)
        except Exception:
            return

        # Mirror to Trinity review queue (best-effort).
        try:
            zd.append_channel_outbox(from_channel=channel, to_channel="Z+3", payload=env)
        except Exception:
            pass
        try:
            zd.append_channel_inbox(to_channel="Z+3", from_channel=channel, payload=env)
        except Exception:
            pass

        # Observability event (best-effort).
        try:
            ev = zd.make_envelope(
                kind="event",
                channel=channel,
                z_context=z_context,
                source="oracle.schema_proposal",
                tool_key="oracle.schema_proposal",
                tags=["oracle", "schema_proposal"],
                payload={
                    "action": "stage_schema_proposal",
                    "payload_kind": payload_kind,
                },
            )
            zd.append_event(channel, ev)
        except Exception:
            pass

        self._schema_proposals_staged.add(payload_kind)

    def ingest_file(self, file_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ingest file into Oracle vault and queue for processing

        Parameters:
            file_path: Path to file to ingest
            metadata: Optional metadata about the file

        Returns:
            Ingestion result with vault_id and queue_position
        """
        try:
            source_path = Path(file_path)

            if not source_path.exists():
                return {'success': False, 'error': 'File not found'}

            # Calculate checksum
            checksum = self._calculate_checksum(source_path)
            job_id: Optional[int] = None
            job_run_dir: Optional[str] = None
            if self.db and hasattr(self.db, "create_job_v1"):
                try:
                    job = self.db.create_job_v1(
                        job_type="ingest",
                        tool_key="oracle.ingest_file",
                        z_context="Z-2_Oracle",
                        status="running",
                        params={
                            "source_path": str(source_path.resolve()),
                            "source_name": source_path.name,
                            "source_ext": source_path.suffix,
                        },
                        inputs=[
                            {
                                "kind": "source_file",
                                "path": str(source_path.resolve()),
                                "sha256": checksum,
                                "name": source_path.name,
                            }
                        ],
                    )
                    job_id = int(job.get("job_id"))
                    job_run_dir = job.get("run_dir")
                except Exception:
                    job_id = None
                    job_run_dir = None

            # Check if already archived
            if self.db:
                existing = self.db.execute_query(
                    "SELECT id FROM files WHERE hash_sha256 = ?",
                    (checksum,)
                )
                if existing:
                    # Best-effort: publish a Z Direct event so Trinity/Morpheus can observe dedupe decisions.
                    try:
                        if HAS_SERVICES:
                            zd = get_z_direct()
                            env = zd.make_envelope(
                                kind="event",
                                channel="Z-2",
                                z_context="Z-2_Oracle",
                                source="oracle.ingest_file",
                                job_id=job_id,
                                tool_key="oracle.ingest_file",
                                tags=["oracle", "dedupe"],
                                payload={
                                    "already_archived": True,
                                    "vault_id": int(existing[0].get("id")),
                                    "source_name": source_path.name,
                                    "source_path": str(source_path.resolve()),
                                    "sha256": checksum,
                                },
                            )
                            zd.append_event("Z-2", env)
                    except Exception:
                        pass
                    if job_id and hasattr(self.db, "finalize_job_v1"):
                        try:
                            self.db.finalize_job_v1(
                                job_id=job_id,
                                status="success",
                                z_context="Z-2_Oracle",
                                outputs=[],
                                result={
                                    "already_archived": True,
                                    "vault_id": existing[0]["id"],
                                    "message": "File already in vault (deduplicated)",
                                },
                            )
                        except Exception:
                            pass
                    return {
                        'success': True,
                        'already_archived': True,
                        'vault_id': existing[0]['id'],
                        'message': 'File already in vault (deduplicated)'
                    }

            # Copy to vault
            vault_filename = f"{checksum[:16]}_{source_path.name}"
            vault_file_path = self.vault_path / vault_filename

            import shutil
            shutil.copy2(source_path, vault_file_path)

            # Register in database
            file_metadata = metadata or {}
            file_metadata.update({
                'original_path': str(source_path),
                'original_name': source_path.name,
                'vault_path': str(vault_file_path),
                'checksum': checksum,
                'size_bytes': source_path.stat().st_size,
                'mime_type': mimetypes.guess_type(source_path)[0],
                'ingestion_time': datetime.now().isoformat()
            })

            if self.db:
                try:
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """INSERT INTO files (path, name, extension, size_bytes, hash_sha256,
                               status, metadata_json) VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
                            (str(vault_file_path), source_path.name, source_path.suffix,
                             source_path.stat().st_size, checksum, json.dumps(file_metadata))
                        )
                        vault_id = cursor.lastrowid
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"[OracleSmartFloor] DB insert failed; using in-memory IDs: {e}")
                    vault_id = None
            else:
                vault_id = None

            if vault_id is None:
                vault_id = len(self.ingestion_queue) + 1

            # Queue for processing
            task_id = self._queue_extraction_task(vault_id, file_metadata)

            # Register job + artifact (V1 ledger/manifest) when available.
            if job_id and hasattr(self.db, "register_artifact_v1") and hasattr(self.db, "finalize_job_v1"):
                try:
                    media_type = mimetypes.guess_type(source_path)[0]
                    self.db.register_artifact_v1(
                        job_id=job_id,
                        z_context="Z-2_Oracle",
                        kind="vault_file",
                        path=str(vault_file_path),
                        sha256=checksum,
                        size_bytes=int(source_path.stat().st_size),
                        name=vault_filename,
                        media_type=media_type,
                        metadata={
                            "vault_id": int(vault_id),
                            "task_id": int(task_id) if task_id is not None else None,
                            "job_run_dir": job_run_dir,
                        },
                    )
                    self.db.finalize_job_v1(
                        job_id=job_id,
                        status="success",
                        z_context="Z-2_Oracle",
                        outputs=[
                            {
                                "kind": "vault_file",
                                "path": str(vault_file_path),
                                "sha256": checksum,
                                "name": vault_filename,
                                "media_type": media_type,
                            }
                        ],
                        result={
                            "vault_id": int(vault_id),
                            "task_id": int(task_id) if task_id is not None else None,
                            "vault_path": str(vault_file_path),
                        },
                    )
                except Exception:
                    pass

            # Best-effort: stage a Z Direct object envelope for the vault item.
            # NOTE: Do not auto-commit to durable registries here; Trinity is the approval gate.
            try:
                if HAS_SERVICES:
                    zd = get_z_direct()
                    obj = {
                        "kind": "vault_file",
                        "id": str(vault_id),
                        "sha256": checksum,
                        "name": vault_filename,
                        "path": str(vault_file_path),
                        "source_name": source_path.name,
                        "source_path": str(source_path.resolve()),
                        "size_bytes": int(source_path.stat().st_size),
                        "mime_type": mimetypes.guess_type(source_path)[0],
                        "task_id": int(task_id) if task_id is not None else None,
                        "job_id": int(job_id) if job_id is not None else None,
                    }
                    env = zd.make_envelope(
                        kind="object",
                        channel="Z-2",
                        z_context="Z-2_Oracle",
                        source="oracle.ingest_file",
                        job_id=job_id,
                        tool_key="oracle.ingest_file",
                        tags=["oracle", "vault"],
                        payload=obj,
                    )
                    zd.append_object("Z-2", env)
                    # Also push into Trinity's directed inbox for approval workflows (best-effort).
                    # This keeps the "review queue" centralized without scanning other floors.
                    try:
                        zd.append_channel_outbox(from_channel="Z-2", to_channel="Z+3", payload=env)
                    except Exception:
                        pass
                    try:
                        zd.append_channel_inbox(to_channel="Z+3", from_channel="Z-2", payload=env)
                    except Exception:
                        pass
                    try:
                        ev = zd.make_envelope(
                            kind="event",
                            channel="Z-2",
                            z_context="Z-2_Oracle",
                            source="oracle.ingest_file",
                            job_id=job_id,
                            tool_key="oracle.ingest_file",
                            tags=["oracle", "vault"],
                            payload={
                                "action": "ingest_file",
                                "vault_id": str(vault_id),
                                "name": vault_filename,
                                "sha256": checksum,
                                "task_id": int(task_id) if task_id is not None else None,
                            },
                        )
                        zd.append_event("Z-2", ev)
                    except Exception:
                        pass
            except Exception:
                pass

            if self.logger:
                self.logger.info(f"[OracleSmartFloor] Ingested: {source_path.name} -> {vault_id}")

            return {
                'success': True,
                'vault_id': vault_id,
                'task_id': task_id,
                'message': f'File ingested to Oracle vault'
            }

        except Exception as e:
            try:
                if "job_id" in locals() and job_id and self.db and hasattr(self.db, "finalize_job_v1"):
                    self.db.finalize_job_v1(
                        job_id=job_id,
                        status="failed",
                        z_context="Z-2_Oracle",
                        error=str(e),
                    )
            except Exception:
                pass
            if self.logger:
                self.logger.error(f"[OracleSmartFloor] Ingestion failed: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _queue_extraction_task(self, vault_id: int, file_metadata: Dict[str, Any]) -> int:
        """
        Queue file extraction task with Smith automation layer

        Parameters:
            vault_id: Vault file ID
            file_metadata: File metadata

        Returns:
            Task ID
        """
        priority = self._calculate_priority(file_metadata)
        task = {
            'type': 'file_extraction',
            'vault_id': vault_id,
            'file_metadata': file_metadata,
            'priority': priority,
            'dependencies': [],
            'created_at': datetime.now().isoformat(),
            'status': 'queued'
        }

        task_id = None
        if self.db:
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """INSERT INTO oracle_ingestion_tasks
                           (vault_id, task_type, file_metadata_json, priority, status, created_at)
                           VALUES (?, ?, ?, ?, 'queued', ?)""",
                        (vault_id, task['type'], json.dumps(file_metadata), priority, task['created_at'])
                    )
                    task_id = cursor.lastrowid
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"[OracleSmartFloor] Failed persisting ingestion task; using in-memory queue: {e}")

        if task_id is None:
            self.ingestion_queue.append(task)
            task_id = len(self.ingestion_queue)

        task['task_id'] = task_id

        # Emit event to Smith
        if self.event_bus:
            self.event_bus.publish('oracle.file_ingested', task)

        if self.logger:
            self.logger.info(f"[OracleSmartFloor] Queued extraction task for vault_id={vault_id}")

        return task_id

    def ingest_url(
        self,
        url: str,
        metadata: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
        *,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        cookies_path: Optional[str] = None,
        allow_non_2xx: bool = False,
    ) -> Dict[str, Any]:
        """
        Download a remote resource and ingest it into the Oracle vault.

        This is the concrete hook for `https://romer.industries/data` (and any other endpoint):
        the URL is downloaded to a local temp file and then processed through `ingest_file()`,
        so it can be routed/objectified into other Z-floors.
        """
        url = (url or "").strip()
        if not url:
            return {"status": "error", "message": "URL is required"}

        try:
            import requests
        except Exception as e:
            return {"status": "error", "message": f"requests is required for URL ingestion: {e}"}

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {"status": "error", "message": f"Invalid URL: {url}"}

        inferred_name = Path(parsed.path).name or "download.bin"
        safe_name = (filename or "").strip() or inferred_name

        tmp_dir = Path(tempfile.gettempdir()) / "lightspeed_oracle_downloads"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        local_path = tmp_dir / safe_name

        def _load_netscape_cookies(path: str, *, host: str) -> Dict[str, str]:
            """
            Load a minimal cookie dict from a Netscape cookies.txt file.

            Supports entries of the form:
              domain  flag  path  secure  expiration  name  value

            Only cookies matching the target host are returned.
            """
            out: Dict[str, str] = {}
            try:
                fp = Path(path).expanduser().resolve()
                if not fp.exists():
                    return out
                host_l = (host or "").strip().lower()
                for raw in fp.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = (raw or "").strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) < 7:
                        continue
                    domain, _flag, _pth, _secure, _exp, name, value = parts[:7]
                    dom = (domain or "").strip().lstrip(".").lower()
                    if not dom or not host_l:
                        continue
                    if host_l == dom or host_l.endswith("." + dom):
                        if name and value:
                            out[str(name)] = str(value)
            except Exception:
                return out
            return out

        try:
            if self.logger:
                self.logger.info(f"[OracleSmartFloor] Downloading URL: {url}")

            req_headers = dict(headers or {})
            # Some endpoints (Squarespace / data pages) behave better with a deterministic UA.
            req_headers.setdefault("User-Agent", "LightSpeedOracle/0.9 (+https://romer.industries)")

            jar: Dict[str, str] = {}
            try:
                if cookies_path:
                    jar.update(_load_netscape_cookies(cookies_path, host=str(parsed.netloc)))
            except Exception:
                pass
            try:
                if cookies:
                    jar.update({str(k): str(v) for k, v in (cookies or {}).items()})
            except Exception:
                pass

            resp = requests.get(url, timeout=30, stream=True, headers=req_headers, cookies=jar or None)
            if not allow_non_2xx:
                resp.raise_for_status()

            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)

            meta = dict(metadata or {})
            meta.update({
                "source": "url",
                "source_url": url,
                "downloaded_at": datetime.now().isoformat(),
                "content_type": resp.headers.get("content-type", ""),
                "http_status": int(getattr(resp, "status_code", 0) or 0),
            })

            task_id = self.ingest_file(str(local_path), metadata=meta)
            return {"status": "ok", "task_id": task_id, "path": str(local_path)}
        except Exception as e:
            return {"status": "error", "message": f"URL ingestion failed: {e}"}

    def ingest_directory(
        self,
        directory_path: str,
        *,
        recursive: bool = True,
        include_extensions: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_files: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Ingest a directory of files into the Oracle vault.

        This is intended for "inbox" style batch ingestion (md/txt exports, drop folders, etc.).

        Args:
            directory_path: Folder to scan.
            recursive: Recurse into subfolders.
            include_extensions: Optional extension allowlist (e.g. ['.md', '.txt']).
            exclude_dirs: Folder names to skip (case-insensitive).
            metadata: Base metadata merged into each file's metadata.
            max_files: Optional cap for safety.

        Returns:
            Summary dict with per-file outcomes.
        """
        root = Path(directory_path).resolve()
        if not root.exists() or not root.is_dir():
            return {"success": False, "error": f"Directory not found: {root}"}

        allow = None
        if include_extensions:
            allow = {str(e).lower() if str(e).startswith(".") else f".{str(e).lower()}" for e in include_extensions}

        exclude = {str(d).strip().lower() for d in (exclude_dirs or []) if str(d).strip()}
        if not exclude:
            exclude = {
                ".git",
                "__pycache__",
                ".venv",
                "venv",
                "node_modules",
                # Never re-ingest the vault itself; inbox lives under archive/.
                "vault",
            }

        base_meta = dict(metadata or {})
        base_meta.setdefault("ingest_source", "directory")
        base_meta.setdefault("ingest_root", str(root))

        ingested = 0
        deduped = 0
        failed = 0
        results: List[Dict[str, Any]] = []

        def iter_files() -> List[Path]:
            if recursive:
                candidates = list(root.rglob("*"))
            else:
                candidates = list(root.glob("*"))
            files = []
            for p in candidates:
                if not p.is_file():
                    continue
                try:
                    parts = [x.lower() for x in p.parts]
                    if any(x in exclude for x in parts):
                        continue
                except Exception:
                    pass
                if allow is not None and p.suffix.lower() not in allow:
                    continue
                files.append(p)
            return sorted(files, key=lambda p: p.name.lower())

        files = iter_files()
        if max_files is not None:
            files = files[: max(0, int(max_files))]

        for idx, file_path in enumerate(files, start=1):
            per_file_meta = dict(base_meta)
            per_file_meta.update(
                {
                    "ingest_relpath": str(file_path.relative_to(root)),
                    "ingest_index": idx,
                }
            )

            try:
                r = self.ingest_file(str(file_path), metadata=per_file_meta)
                if r.get("success") and r.get("already_archived"):
                    deduped += 1
                elif r.get("success"):
                    ingested += 1
                else:
                    failed += 1
                results.append(
                    {
                        "path": str(file_path),
                        "success": bool(r.get("success")),
                        "already_archived": bool(r.get("already_archived")),
                        "vault_id": r.get("vault_id"),
                        "task_id": r.get("task_id"),
                        "error": r.get("error"),
                    }
                )
            except Exception as e:
                failed += 1
                results.append({"path": str(file_path), "success": False, "error": str(e)})

        summary = {
            "success": True,
            "directory": str(root),
            "files_total": len(files),
            "files_ingested": ingested,
            "files_deduped": deduped,
            "files_failed": failed,
            "results": results,
        }

        try:
            if self.event_bus:
                self.event_bus.publish("oracle.directory_ingested", summary)
        except Exception:
            pass

        return summary

    def _calculate_priority(self, file_metadata: Dict[str, Any]) -> int:
        """
        Calculate task priority based on file metadata

        Priority levels:
        1 = Critical (IP documents, patents, legal)
        2 = High (research, papers, core documentation)
        3 = Medium (code, scripts, data)
        4 = Low (media, assets, misc)
        5 = Deferred (archives, backups, logs)
        """
        mime_type = file_metadata.get('mime_type', '')
        extension = file_metadata.get('original_name', '').split('.')[-1].lower()
        name = file_metadata.get('original_name', '').lower()

        # Critical: IP and legal documents
        if any(keyword in name for keyword in ['patent', 'trademark', 'ip_', 'legal', 'contract']):
            return 1

        # High: Research and documentation
        if extension in ['pdf', 'tex', 'docx'] or 'research' in name or 'paper' in name:
            return 2

        # Medium: Code and data
        if extension in ['py', 'js', 'cpp', 'java', 'sql', 'json', 'csv', 'xlsx']:
            return 3

        # Low: Media
        if extension in ['png', 'jpg', 'mp4', 'svg', 'wav']:
            return 4

        # Deferred: Archives and logs
        if extension in ['zip', 'tar', 'gz', 'log', 'bak']:
            return 5

        return 3  # Default: Medium

    def process_extraction_task(self, task_id: int) -> Dict[str, Any]:
        """
        Process extraction task: analyze file and distribute to Z-floors

        Parameters:
            task_id: Task ID from queue

        Returns:
            Processing result
        """
        task = None
        vault_id = None
        file_metadata = None

        if self.db:
            rows = self.db.execute_query(
                "SELECT * FROM oracle_ingestion_tasks WHERE id = ?",
                (task_id,)
            )
            if not rows:
                return {'success': False, 'error': 'Task not found'}

            task_row = rows[0]
            vault_id = task_row.get('vault_id')
            file_metadata = json.loads(task_row.get('file_metadata_json') or "{}")
            task = {
                'task_id': task_id,
                'type': task_row.get('task_type'),
                'vault_id': vault_id,
                'file_metadata': file_metadata,
                'priority': task_row.get('priority', 3),
                'created_at': task_row.get('created_at'),
                'status': task_row.get('status'),
            }

            try:
                self.db.execute_update(
                    "UPDATE oracle_ingestion_tasks SET status = 'in_progress', started_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), task_id)
                )
            except Exception:
                pass
        else:
            if task_id <= 0 or task_id > len(self.ingestion_queue):
                return {'success': False, 'error': 'Invalid task ID'}
            task = self.ingestion_queue[task_id - 1]
            vault_id = task['vault_id']
            file_metadata = task['file_metadata']

        try:
            # Extract file contents based on type
            extracted_data = self._extract_file_contents(file_metadata)

            # Route to appropriate Z-floors
            routing_results = self._route_to_floors(vault_id, extracted_data, file_metadata)

            # Update Encyclopedia if empirical data found
            encyclopedia_updates = self._update_encyclopedia(extracted_data, file_metadata)

            # Mark task complete
            task['status'] = 'completed'
            task['completed_at'] = datetime.now().isoformat()
            task['routing_results'] = routing_results
            task['encyclopedia_updates'] = encyclopedia_updates

            if self.db:
                try:
                    self.db.execute_update(
                        """UPDATE oracle_ingestion_tasks
                           SET status='completed', completed_at=?, routing_results_json=?,
                               encyclopedia_updates=?, error=NULL
                           WHERE id=?""",
                        (
                            task['completed_at'],
                            json.dumps(routing_results),
                            int(encyclopedia_updates),
                            task_id,
                        )
                    )
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"[OracleSmartFloor] Failed updating task status: {e}")

                try:
                    self.db.execute_update(
                        "UPDATE files SET status='analyzed', analyzed_at=? WHERE id=?",
                        (task['completed_at'], vault_id)
                    )
                except Exception:
                    pass

            if self.logger:
                self.logger.info(f"[OracleSmartFloor] Completed extraction task {task_id}")

            return {
                'success': True,
                'task_id': task_id,
                'vault_id': vault_id,
                'floors_updated': routing_results,
                'encyclopedia_entries': encyclopedia_updates
            }

        except Exception as e:
            task['status'] = 'failed'
            task['error'] = str(e)
            if self.logger:
                self.logger.error(f"[OracleSmartFloor] Extraction failed: {e}")

            if self.db:
                try:
                    self.db.execute_update(
                        "UPDATE oracle_ingestion_tasks SET status='failed', completed_at=?, error=? WHERE id=?",
                        (datetime.now().isoformat(), str(e), task_id)
                    )
                except Exception:
                    pass
            return {'success': False, 'error': str(e)}

    def _extract_file_contents(self, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract contents and metadata from file

        Parameters:
            file_metadata: File metadata

        Returns:
            Extracted data dictionary
        """
        vault_path = Path(file_metadata['vault_path'])
        extension = vault_path.suffix.lower()

        extracted = {
            'text_content': None,
            'data_objects': [],
            'parameters': {},
            'functions': [],
            'classes': [],
            'keywords': [],
            'empirical_data': []
        }

        try:
            # Text files: extract content
            if extension in ['.txt', '.md', '.rst']:
                extracted['text_content'] = vault_path.read_text(encoding='utf-8', errors='ignore')
                extracted['keywords'] = self._extract_keywords(extracted['text_content'])
                extracted['empirical_data'] = self._extract_empirical_data(extracted['text_content'])

            # Python files: AST analysis
            elif extension == '.py':
                content = vault_path.read_text(encoding='utf-8', errors='ignore')
                extracted['text_content'] = content
                extracted['functions'] = self._extract_python_functions(content)
                extracted['classes'] = self._extract_python_classes(content)
                extracted['parameters'] = self._extract_python_params(content)

            # JSON/CSV: data objects
            elif extension in ['.json', '.csv']:
                extracted['data_objects'] = self._extract_data_objects(vault_path)

            # PDF: text extraction (basic)
            elif extension == '.pdf':
                extracted['keywords'] = ['pdf', 'document']
                try:
                    from PyPDF2 import PdfReader  # type: ignore
                    reader = PdfReader(str(vault_path))
                    pages_text = []
                    for page in reader.pages[:10]:
                        pages_text.append(page.extract_text() or "")
                    extracted['text_content'] = "\n".join(pages_text).strip() or None
                    if extracted['text_content']:
                        extracted['keywords'] = self._extract_keywords(extracted['text_content'])
                        extracted['empirical_data'] = self._extract_empirical_data(extracted['text_content'])
                except Exception as e:
                    if self.logger:
                        self.logger.info(f"[OracleSmartFloor] PDF text extraction unavailable: {e}")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"[OracleSmartFloor] Content extraction warning: {e}")

        return extracted

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text content"""
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', text)  # CamelCase
        words += re.findall(r'\b[a-z_]{3,}\b', text)  # snake_case
        return list(set(words[:50]))  # Top 50 unique keywords

    def _extract_empirical_data(self, text: str) -> List[Dict[str, Any]]:
        """Extract empirical data (numbers, units, equations) from text"""
        empirical = []

        # Extract numerical values with units
        pattern = r'(\d+\.?\d*)\s*(kg|m|s|N|J|W|Hz|Pa|K|mol|cd|A|V)'
        matches = re.findall(pattern, text)
        for value, unit in matches:
            empirical.append({
                'type': 'measurement',
                'value': float(value),
                'unit': unit,
                'context': 'extracted_from_text'
            })

        return empirical

    def _extract_python_functions(self, code: str) -> List[str]:
        """Extract function names from Python code"""
        pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        return re.findall(pattern, code)

    def _extract_python_classes(self, code: str) -> List[str]:
        """Extract class names from Python code"""
        pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[(:,]'
        return re.findall(pattern, code)

    def _extract_python_params(self, code: str) -> Dict[str, Any]:
        """Extract parameters and constants from Python code"""
        params = {}

        # Extract constants (UPPER_CASE = value)
        pattern = r'([A-Z_]+)\s*=\s*([0-9.]+)'
        matches = re.findall(pattern, code)
        for name, value in matches:
            try:
                params[name] = float(value)
            except:
                params[name] = value

        return params

    def _extract_data_objects(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract data objects from JSON/CSV files"""
        extension = file_path.suffix.lower()

        if extension == '.json':
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data[:100]  # Limit to first 100 objects
                    elif isinstance(data, dict):
                        return [data]
            except:
                return []

        elif extension == '.csv':
            try:
                with open(file_path, newline='', encoding='utf-8', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    out = []
                    for idx, row in enumerate(reader):
                        out.append(dict(row))
                        if idx >= 99:
                            break
                    return out
            except Exception:
                return []

        return []

    def _route_to_floors(self, vault_id: int, extracted_data: Dict[str, Any],
                        file_metadata: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Route extracted data to appropriate Z-floors

        Parameters:
            vault_id: Vault file ID
            extracted_data: Extracted content
            file_metadata: File metadata

        Returns:
            Dictionary of floor -> objects routed
        """
        routing: Dict[str, List[str]] = {}

        def _publish_route(floor: str, matches: List[str]) -> None:
            if not self.event_bus:
                return
            payload = {
                "target_floor": floor,
                "vault_id": vault_id,
                "file_metadata": file_metadata,
                "extracted_data": extracted_data,
                "matched_keywords": matches,
            }
            try:
                # Canonical routing event for wildcard subscribers (e.g. Smith automation).
                self.event_bus.publish("oracle.route", payload)
            except Exception:
                pass
            try:
                # Legacy per-floor topic for backward compatibility.
                self.event_bus.publish(f"oracle.route_{floor.lower()}", payload)
            except Exception:
                pass

        # Analyze keywords to determine target floors
        all_keywords = extracted_data.get('keywords', [])
        all_keywords += file_metadata.get('original_name', '').lower().split('_')

        for floor, floor_keywords in self.floor_routing.items():
            matches = []
            for keyword in all_keywords:
                if any(fk in keyword.lower() for fk in floor_keywords):
                    matches.append(keyword)

            if matches:
                routing[floor] = matches
                _publish_route(floor, matches)

        # Always route to Morpheus (Knowledge Base) for indexing (and publish, so it isn't silent).
        if "Z-1_Morpheus" not in routing:
            routing["Z-1_Morpheus"] = ["knowledge_base_index"]
            _publish_route("Z-1_Morpheus", routing["Z-1_Morpheus"])

        # Fallback routing rules (keyword-based routing can miss most files):
        # - If the file contains code structure, send to Neo for objectification.
        # - If the file contains tabular objects, send to Architect for planning/data views.
        try:
            has_code = bool(extracted_data.get("functions") or extracted_data.get("classes") or extracted_data.get("parameters"))
        except Exception:
            has_code = False
        if has_code and "Z+2_Neo" not in routing:
            routing["Z+2_Neo"] = ["code_objectification"]
            _publish_route("Z+2_Neo", routing["Z+2_Neo"])

        try:
            has_data_objects = bool(extracted_data.get("data_objects"))
        except Exception:
            has_data_objects = False
        if has_data_objects and "Z+1_Architect" not in routing:
            routing["Z+1_Architect"] = ["data_objectification"]
            _publish_route("Z+1_Architect", routing["Z+1_Architect"])

        return routing

    def _load_encyclopedia(self):
        """Lazy-load EncyclopediaSystem from the local component file."""
        if self._encyclopedia is not None:
            return self._encyclopedia

        try:
            module_path = Path(__file__).with_name("encyclopedia_system.py")
            spec = importlib.util.spec_from_file_location("oracle_encyclopedia_system", module_path)
            if spec is None or spec.loader is None:
                self._encyclopedia = None
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            self._encyclopedia_volume_enum = getattr(module, "EncyclopediaVolume", None)
            self._encyclopedia = module.EncyclopediaSystem(db=self.db, logger=self.logger)
            return self._encyclopedia
        except Exception as e:
            if self.logger:
                self.logger.warning(f"[OracleSmartFloor] Encyclopedia unavailable: {e}")
            self._encyclopedia = None
            return None

    def _update_encyclopedia(self, extracted_data: Dict[str, Any], file_metadata: Dict[str, Any]) -> int:
        """
        Update Encyclopedia system with extracted empirical data

        Parameters:
            extracted_data: Extracted content

        Returns:
            Number of encyclopedia entries created
        """
        encyclopedia = self._load_encyclopedia()
        if encyclopedia is None:
            return 0

        created = 0
        original_name = file_metadata.get("original_name") or "unknown_source"

        volume_enum = self._encyclopedia_volume_enum
        if volume_enum is None:
            return 0

        volume = volume_enum.EMPIRICAL
        origin_path = file_metadata.get("original_path") or ""

        # Prefer constants extracted from code (UPPER_CASE assignments).
        params = extracted_data.get("parameters") or {}
        for name, value in list(params.items())[:50]:
            if not isinstance(value, (int, float)):
                continue
            try:
                encyclopedia.add_entry(
                    term=str(name),
                    volume=volume,
                    definition=f"Constant extracted from {original_name}",
                    data_object={"value": value, "source_file": original_name},
                    references=[origin_path] if origin_path else [],
                    metadata={"origin": "oracle_smart_floor_integrator"},
                )
                created += 1
            except Exception:
                continue

        # Also add dictionary foundation terms that appear in text (bounded).
        text = (extracted_data.get("text_content") or "").lower()
        if text:
            matches = []
            for term in getattr(encyclopedia, "dictionary", {}).keys():
                if term in text:
                    matches.append(term)
                if len(matches) >= 10:
                    break
            for term in matches:
                try:
                    encyclopedia.add_entry(
                        term=term,
                        volume=volume,
                        definition=getattr(encyclopedia, "dictionary", {}).get(term, {}).get("definition", ""),
                        data_object=getattr(encyclopedia, "dictionary", {}).get(term, {}),
                        references=[origin_path] if origin_path else [],
                        metadata={"origin": "oracle_smart_floor_integrator"},
                    )
                    created += 1
                except Exception:
                    continue

        if created and self.logger:
            self.logger.info(f"[OracleSmartFloor] Encyclopedia updated: {created} entry(ies)")

        return created

    def process_pending_tasks(self, max_tasks: int = 5) -> List[Dict[str, Any]]:
        """Process pending Oracle ingestion tasks (DB-backed when available)."""
        results: List[Dict[str, Any]] = []
        if max_tasks <= 0:
            return results

        if self.db:
            rows = self.db.execute_query(
                "SELECT id FROM oracle_ingestion_tasks WHERE status IN ('queued', 'pending') ORDER BY created_at ASC LIMIT ?",
                (int(max_tasks),)
            )
            for row in rows:
                results.append(self.process_extraction_task(int(row["id"])))
            return results

        # In-memory fallback
        for idx, task in enumerate(self.ingestion_queue):
            if task.get("status") == "queued":
                results.append(self.process_extraction_task(idx + 1))
                if len(results) >= max_tasks:
                    break
        return results

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        if self.db:
            try:
                rows = self.db.execute_query(
                    "SELECT status, COUNT(*) as c FROM oracle_ingestion_tasks GROUP BY status"
                )
                counts = {r["status"]: int(r["c"]) for r in rows}
                total = sum(counts.values())
                return {
                    "total_tasks": total,
                    "completed": counts.get("completed", 0),
                    "pending": counts.get("queued", 0) + counts.get("pending", 0),
                    "failed": counts.get("failed", 0),
                    "counts": counts,
                }
            except Exception:
                pass

        total = len(self.ingestion_queue)
        completed = sum(1 for task in self.ingestion_queue if task['status'] == 'completed')
        pending = sum(1 for task in self.ingestion_queue if task['status'] == 'queued')
        failed = sum(1 for task in self.ingestion_queue if task['status'] == 'failed')

        return {
            'total_tasks': total,
            'completed': completed,
            'pending': pending,
            'failed': failed,
            'queue': self.ingestion_queue
        }


# Standalone test
if __name__ == '__main__':
    integrator = OracleSmartFloorIntegrator()
    print("[OracleSmartFloor] Oracle Smart Floor Integrator ready")
    print(f"Vault path: {integrator.vault_path}")
    print(f"Floor routing configured for {len(integrator.floor_routing)} Z-floors")
