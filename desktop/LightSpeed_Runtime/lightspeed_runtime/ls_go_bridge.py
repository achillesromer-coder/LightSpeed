from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from lightspeed_runtime.project_artifact_store import stage_project_artifacts
from lightspeed_runtime.project_pipeline import ProjectPipeline
from lightspeed_runtime.representation_edge import (
    RepresentationEdgeDisabled,
    RepresentationValidationError,
    build_store as build_representation_edge_store,
    default_review_paths as representation_review_paths,
)
from lightspeed_runtime.storage_paths import neo_actions_root

COMMAND_SCHEMA = "lightspeed-go-command-v1"
ALLOWED_FLOORS = {
    "Achilles",
    "Neo",
    "Architect",
    "TheConstruct",
    "Morpheus",
    "Oracle",
    "Smith",
    "Merovingian",
    "Trinity",
}
ALLOWED_PRIORITIES = {"critical", "high", "normal", "low"}
ALLOWED_MODES = {"review", "queue"}
DEFAULT_ALLOWED_ORIGINS = [
    "https://lightspeed-go.nathaniel-b.chatgpt.site",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:4173",
    "http://localhost:5173",
    "http://localhost:4173",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _pid_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_limited_information, False, int(pid)
        )
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _supervisor_status(shell_root: Path) -> dict[str, Any]:
    lock_path = (
        shell_root
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "runtime_exports"
        / "merovingian_supervisor.lock.json"
    )
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        heartbeat = datetime.fromisoformat(str(payload["heartbeat_utc"]).replace("Z", "+00:00"))
        if heartbeat.tzinfo is None:
            heartbeat = heartbeat.replace(tzinfo=timezone.utc)
        age_seconds = max(0.0, (datetime.now(timezone.utc) - heartbeat).total_seconds())
        interval_seconds = max(30, min(int(payload.get("interval_seconds", 60)), 3600))
        stale_after_seconds = max(90, interval_seconds * 2 + 15)
        pid = int(payload.get("pid"))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return {
            "alive": False,
            "reason": f"invalid_or_missing_supervisor_lock:{type(exc).__name__}",
            "lock_path": str(lock_path),
        }

    process_alive = _pid_alive(pid)
    heartbeat_fresh = age_seconds <= stale_after_seconds
    return {
        "alive": process_alive and heartbeat_fresh,
        "pid": pid,
        "process_alive": process_alive,
        "heartbeat_fresh": heartbeat_fresh,
        "heartbeat_utc": heartbeat.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "heartbeat_age_seconds": round(age_seconds, 3),
        "stale_after_seconds": stale_after_seconds,
        "state": payload.get("state"),
        "lock_path": str(lock_path),
        "reason": (
            "live"
            if process_alive and heartbeat_fresh
            else "process_not_running" if not process_alive else "heartbeat_stale"
        ),
    }


def _bounded(value: Any, *, maximum: int, required: bool = False) -> str:
    text = " ".join(str(value or "").split()).strip()[:maximum]
    if required and not text:
        raise HTTPException(status_code=400, detail="Required command field is missing")
    return text


def _allowed_origins() -> list[str]:
    configured = [item.strip() for item in os.environ.get("LIGHTSPEED_GO_ALLOWED_ORIGINS", "").split(",")]
    return [*DEFAULT_ALLOWED_ORIGINS, *[item for item in configured if item]]


def _try_get_services(shell_root: Path):
    merovingian_root = shell_root / "Z Axis" / "Z-4_Merovingian"
    if str(merovingian_root) not in sys.path:
        sys.path.insert(0, str(merovingian_root))
    try:
        from core.services import initialize_services  # type: ignore

        services = initialize_services()
        return services.get("database"), services.get("storage")
    except Exception:
        return None, None


def _queue_path(root: Path) -> Path:
    path = neo_actions_root(root) / "ls_go_command_queue.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_queue(root: Path, limit: int = 30) -> list[dict[str, Any]]:
    path = _queue_path(root)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return list(reversed(rows[-max(1, min(limit, 200)) :]))


def _append_queue(root: Path, payload: dict[str, Any]) -> str:
    path = _queue_path(root)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return str(path)


def create_app(root: Path | str) -> FastAPI:
    shell_root = Path(root).resolve()
    db, storage = _try_get_services(shell_root)
    project_pipeline = ProjectPipeline(shell_root)
    representation_edge = build_representation_edge_store(shell_root)
    representation_edge_error: str | None = None
    if representation_edge.enabled:
        review_queue, decisions, outbox = representation_review_paths(shell_root)
        try:
            representation_edge.seed_proof_graphs(
                review_queue_path=review_queue,
                decision_path=decisions,
                local_outbox=outbox,
            )
        except Exception as exc:
            representation_edge_error = f"{type(exc).__name__}: {exc}"
    app = FastAPI(
        title="LightSpeed GO Desktop Bridge",
        description="Local-only, Achilles-governed command, project and review bridge for LS GO.",
        version="1.2.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
        max_age=600,
    )

    @app.get("/api/v1/status")
    async def status():
        registry = project_pipeline.refresh(force=False, queue_changes=True)
        health = registry.get("health") or {}
        health_details = health.get("details") or {}
        supervisor = _supervisor_status(shell_root)
        merovingian_healthy = health.get("status") == "pass" and bool(supervisor.get("alive"))
        core_services_healthy = bool(db) and bool(storage) and merovingian_healthy
        return JSONResponse(
            {
                "ok": core_services_healthy,
                "time_utc": utc_now_iso(),
                "bridge": "ls-go",
                "root": str(shell_root),
                "services": {
                    "db": bool(db),
                    "storage": bool(storage),
                    "merovingian": merovingian_healthy,
                },
                "merovingian": {
                    "status": "pass" if merovingian_healthy else "unavailable",
                    "receipt": str(project_pipeline.health_path),
                    "supervisor": supervisor,
                    "project_summary": registry.get("summary") or {},
                    "cleanup_summary": registry.get("cleanup_summary") or {},
                    "drive_writeback": health_details.get("drive_writeback"),
                    "root_resolution": health_details.get("root_resolution"),
                },
                "resources": health_details.get("resource_guard") or {},
                "agent_floors": health_details.get("agent_floors") or {},
                "queue_path": str(_queue_path(shell_root)),
                "review_queue_path": str(project_pipeline.review_queue_path),
                "representation_edge": {
                    **representation_edge.status(),
                    "error": representation_edge_error,
                },
                "execution_boundary": "local queue, immutable named artifacts, receipts and review only; no public direct execution",
            }
        )

    @app.get("/api/v1/tasks")
    async def list_tasks(limit: int = 30):
        if db:
            try:
                rows = db.execute_query(
                    "SELECT id, title, description, project_id, status, priority, created_at, updated_at, metadata_json "
                    "FROM tasks ORDER BY id DESC LIMIT ?",
                    (max(1, min(int(limit), 200)),),
                )
                return JSONResponse({"tasks": rows})
            except Exception:
                pass
        queue_rows = _read_queue(shell_root, limit=limit)
        tasks = [
            {
                "id": row.get("command_id"),
                "title": row.get("title"),
                "description": row.get("instruction"),
                "status": row.get("state", "queued"),
                "priority": row.get("priority", "normal"),
                "created_at": row.get("accepted_utc"),
            }
            for row in queue_rows
        ]
        return JSONResponse({"tasks": tasks})

    @app.get("/api/v1/projects")
    async def list_projects():
        registry = project_pipeline.refresh(force=False, queue_changes=True)
        return JSONResponse(
            {
                "projects": registry.get("projects") or [],
                "summary": registry.get("summary") or {},
                "duplicate_names": registry.get("duplicate_names") or [],
                "cleanup_summary": registry.get("cleanup_summary") or {},
            }
        )

    @app.get("/api/v1/reviews")
    async def list_reviews(limit: int = 50):
        return JSONResponse(
            {"reviews": project_pipeline.list_reviews(limit=max(1, min(int(limit), 200)))}
        )

    @app.post("/api/v1/reviews/{review_id}/decision")
    async def decide_review(review_id: str, body: dict[str, Any]):
        decision = _bounded(body.get("decision"), maximum=16, required=True).lower()
        note = _bounded(body.get("note"), maximum=1000)
        try:
            receipt = project_pipeline.decide_review(review_id, decision, note)
        except KeyError:
            raise HTTPException(status_code=404, detail="Review item not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return JSONResponse({"accepted": True, "receipt": receipt})

    def require_representation_edge():
        if not representation_edge.enabled:
            raise HTTPException(
                status_code=404,
                detail="Canonical representation edge is disabled by feature flag.",
            )
        if representation_edge_error:
            raise HTTPException(status_code=503, detail=representation_edge_error)
        try:
            state = representation_edge.status()
        except RepresentationEdgeDisabled as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        if not state.get("migration_applied"):
            raise HTTPException(status_code=503, detail="Representation-edge migration is unavailable.")
        return representation_edge

    @app.get("/api/v1/representation-edge/status")
    async def representation_edge_status():
        return JSONResponse(
            {
                **representation_edge.status(),
                "error": representation_edge_error,
                "drive_write_executed": False,
            }
        )

    @app.get("/api/v1/representation-graphs")
    async def list_representation_graphs():
        edge = require_representation_edge()
        return JSONResponse({"graphs": edge.list_graphs()})

    @app.get("/api/v1/representation-graphs/{object_id:path}")
    async def get_representation_graph(object_id: str):
        edge = require_representation_edge()
        try:
            graph = edge.graph(_bounded(object_id, maximum=160, required=True))
        except KeyError:
            raise HTTPException(status_code=404, detail="Canonical object candidate not found")
        return JSONResponse({"graph": graph})

    @app.get("/api/v1/representation-reviews")
    async def list_representation_reviews():
        edge = require_representation_edge()
        return JSONResponse({"reviews": edge.list_reviews()})

    @app.post("/api/v1/representation-reviews/{review_id}/decision")
    async def decide_representation_review(review_id: str, body: dict[str, Any]):
        edge = require_representation_edge()
        decision = _bounded(body.get("decision"), maximum=32, required=True)
        actor = _bounded(body.get("actor"), maximum=80, required=True)
        scope = _bounded(body.get("scope") or "identity", maximum=16, required=True)
        note = _bounded(body.get("note"), maximum=1000)
        raw_edge_ids = body.get("edge_ids") or []
        if not isinstance(raw_edge_ids, list):
            raise HTTPException(status_code=400, detail="edge_ids must be a bounded list")
        edge_ids = [_bounded(value, maximum=160, required=True) for value in raw_edge_ids[:100]]
        _, decision_path, outbox = representation_review_paths(shell_root)
        try:
            receipt = edge.record_decision(
                review_id=_bounded(review_id, maximum=96, required=True),
                decision=decision,
                actor=actor,
                scope=scope,
                note=note,
                edge_ids=edge_ids,
                decision_path=decision_path,
                local_outbox=outbox,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Representation review not found")
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except RepresentationValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return JSONResponse({"accepted": True, "receipt": receipt})

    @app.get("/api/v1/representation-promotions")
    async def list_representation_promotions():
        edge = require_representation_edge()
        return JSONResponse(
            {
                "promotions": edge.list_promotions(),
                "drive_write_executed": False,
                "readback_required": True,
            }
        )

    @app.post("/api/v1/projects/{project_id}/receipts")
    async def accept_project_receipt(project_id: str, body: dict[str, Any]):
        bounded_project_id = _bounded(project_id, maximum=96, required=True)
        summary = _bounded(body.get("summary"), maximum=4000, required=True)
        raw_paths = body.get("artifact_paths") or []
        if not isinstance(raw_paths, list):
            raise HTTPException(status_code=400, detail="artifact_paths must be a list")
        artifact_paths = [_bounded(value, maximum=1000) for value in raw_paths]
        try:
            artifact_manifest = stage_project_artifacts(
                project_pipeline,
                project_id=bounded_project_id,
                artifact_paths=artifact_paths,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Registered project not found")
        except (ValueError, FileNotFoundError, FileExistsError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        copied_paths = [
            str(item.get("destination_path"))
            for item in artifact_manifest.get("copied") or []
            if item.get("destination_path")
        ]
        review_artifacts = [str(artifact_manifest["manifest_path"]), *copied_paths]
        staging_summary = (
            f"{summary} Immutable artifact staging: "
            f"{artifact_manifest.get('copied_count', 0)} copied, "
            f"{artifact_manifest.get('skipped_count', 0)} skipped; "
            f"mode={artifact_manifest.get('drive_writeback_mode')}."
        )
        packet = project_pipeline.queue_project_work_receipt(
            project_id=bounded_project_id,
            summary=staging_summary,
            artifact_paths=review_artifacts,
        )
        return JSONResponse(
            {
                "accepted": True,
                "review": packet,
                "artifact_manifest": artifact_manifest,
            }
        )

    @app.post("/api/v1/ls-go/commands")
    async def accept_command(body: dict[str, Any]):
        if body.get("schema_version") != COMMAND_SCHEMA:
            raise HTTPException(status_code=400, detail="Unsupported command schema")

        command_id = _bounded(body.get("command_id"), maximum=96, required=True)
        instruction = _bounded(body.get("instruction"), maximum=4000, required=True)
        title = _bounded(body.get("title") or instruction, maximum=160, required=True)
        target_floor = _bounded(body.get("target_floor"), maximum=40, required=True)
        priority = _bounded(body.get("priority") or "normal", maximum=16)
        execution_mode = _bounded(body.get("execution_mode") or "review", maximum=16)

        if target_floor not in ALLOWED_FLOORS:
            raise HTTPException(status_code=400, detail="Unsupported target floor")
        if priority not in ALLOWED_PRIORITIES:
            raise HTTPException(status_code=400, detail="Unsupported priority")
        if execution_mode not in ALLOWED_MODES:
            raise HTTPException(status_code=400, detail="Unsupported execution mode")
        if body.get("oversight_floor") != "Achilles":
            raise HTTPException(status_code=400, detail="Achilles oversight is required")
        if body.get("proof_required") is not True or body.get("public_safe") is not True:
            raise HTTPException(status_code=400, detail="Proof and public-safe gates are required")

        accepted = {
            "schema_version": COMMAND_SCHEMA,
            "command_id": command_id,
            "accepted_utc": utc_now_iso(),
            "source": "LS GO",
            "title": title,
            "instruction": instruction,
            "target_floor": target_floor,
            "oversight_floor": "Achilles",
            "priority": priority,
            "execution_mode": execution_mode,
            "state": "review" if execution_mode == "review" else "queued",
            "proof_required": True,
            "public_safe": True,
        }
        artifact_ref = _append_queue(shell_root, accepted)

        task_id: Optional[int] = None
        job: Optional[dict[str, Any]] = None
        if db:
            try:
                now = accepted["accepted_utc"]
                metadata_json = json.dumps(
                    {
                        "schema_version": COMMAND_SCHEMA,
                        "command_id": command_id,
                        "source": "LS GO",
                        "target_floor": target_floor,
                        "oversight_floor": "Achilles",
                        "execution_mode": execution_mode,
                        "proof_required": True,
                        "public_safe": True,
                        "artifact_ref": artifact_ref,
                    },
                    ensure_ascii=False,
                )
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO tasks (title, description, project_id, status, priority, created_at, updated_at, metadata_json) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (title, instruction, "LS-GO", accepted["state"], priority, now, now, metadata_json),
                    )
                    task_id = int(cursor.lastrowid)
                created = db.create_job_v1(
                    job_type="ls_go_command",
                    tool_key="ls_go_command",
                    z_context=target_floor,
                    params={
                        "command_id": command_id,
                        "instruction": instruction,
                        "execution_mode": execution_mode,
                        "oversight_floor": "Achilles",
                    },
                    task_id=task_id,
                    project_id="LS-GO",
                    tags=["ls-go", "achilles", target_floor.lower()],
                    inputs=[{"kind": "command_envelope", "path": artifact_ref}],
                )
                job = created if isinstance(created, dict) else {"result": created}
            except Exception as exc:
                accepted["db_detail"] = f"Queue persisted; database handoff unavailable: {type(exc).__name__}"

        return JSONResponse(
            {
                "accepted": True,
                "command_id": command_id,
                "task_id": task_id,
                "job": job,
                "state": accepted["state"],
                "artifact_ref": artifact_ref,
                "detail": accepted.get("db_detail", "Command persisted and routed to the Desktop task/job lane."),
            }
        )

    return app


def start_server(root: Path | str, host: str = "127.0.0.1", port: int = 8765) -> None:
    uvicorn.run(create_app(root), host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server(Path(os.environ.get("LIGHTSPEED_ROOT", Path.cwd())))
