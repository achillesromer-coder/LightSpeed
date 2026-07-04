#!/usr/bin/env python
"""
Smith Task Queue & Priority System
Manages all system tasks, prioritizes based on dependencies and floor needs

Smith is the automation controller that:
1. Receives tasks from all Z-floors
2. Prioritizes based on dependencies and urgency
3. Executes tasks in optimal order
4. Monitors completion and handles failures
5. Coordinates with Oracle for file processing

Author: Romer Industries / EMASSC
Version: 5.1.0
Date: January 30, 2026
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum
import heapq
import threading
import time
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import sys
import os

# CODEX NOTE (2026-01-30):
# - Background workers (Oracle ingestion auto-worker) are disabled in smoke/verify runs via
#   `LIGHTSPEED_DISABLE_BACKGROUND_WORKERS=1` to avoid side effects and SQLite lock contention.
# - Smith remains the automation layer; Trinity remains the approval gate for durable Z Direct registries.


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    DEFERRED = 5


class TaskStatus(Enum):
    """Task status states"""
    QUEUED = 'queued'
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    BLOCKED = 'blocked'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class SmithTaskQueue:
    """
    Smith Task Queue & Priority System

    Manages system-wide task execution with intelligent prioritization
    """

    def __init__(self, db=None, event_bus=None, logger=None):
        """Initialize Smith Task Queue"""
        self.db = db
        self.event_bus = event_bus
        self.logger = logger

        # Priority queue (min-heap by priority)
        self.task_heap = []
        self.tasks = {}  # task_id -> task dict
        self.task_counter = 0

        # Floor task quotas (prevents any floor from monopolizing Smith)
        self.floor_quotas = {
            'Z+3_Trinity': 10,
            'Z+2_Neo': 15,
            'Z+1_Architect': 10,
            'Z0_TheConstruct': 20,
            'Z-1_Morpheus': 15,
            'Z-2_Oracle': 25,  # Higher quota for archive processing
            'Z-3_Smith': 10,
            'Z-4_Merovingian': 15
        }

        # Current floor usage
        self.floor_usage = {floor: 0 for floor in self.floor_quotas}

        # Task execution history
        self.execution_history = []

        # Task execution (handlers + background worker)
        # Smith is the automation layer: tasks are defined by type + params and executed
        # by registered handlers. This keeps the UI responsive and centralizes long-running work.
        self.task_handlers: Dict[str, Any] = {}  # task_type -> callable(task, progress_cb) -> result
        self._worker_thread: Optional[threading.Thread] = None
        self._worker_stop = threading.Event()
        self._cancelled: set[int] = set()

        if self.logger:
            self.logger.info("[SmithQueue] Smith Task Queue initialized")

        # Auto-run Oracle ingestion processing in the background so Oracle->Smith remains "hands-off".
        # This is intentionally best-effort: if the integrator cannot be loaded, Smith still runs.
        self._oracle_ingestion_worker = None
        self._knowledge_proposal_worker = None
        disable_workers = os.environ.get("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS") == "1"
        if not disable_workers:
            try:
                self._oracle_ingestion_worker = _OracleIngestionAutoWorker(
                    db=self.db,
                    event_bus=self.event_bus,
                    logger=self.logger,
                )
                self._oracle_ingestion_worker.start()
            except Exception:
                self._oracle_ingestion_worker = None

            # Optional: stage-only knowledge proposals from newly committed Oracle vault files.
            # This is OFF by default because it can create many review items.
            if os.environ.get("LIGHTSPEED_ENABLE_KNOWLEDGE_AUTOPROPOSAL") == "1":
                try:
                    worker_cls = globals().get("_KnowledgeProposalAutoWorker")
                    if worker_cls is not None:
                        self._knowledge_proposal_worker = worker_cls(  # type: ignore[call-arg]
                            db=self.db,
                            event_bus=self.event_bus,
                            logger=self.logger,
                        )
                        self._knowledge_proposal_worker.start()
                except Exception:
                    self._knowledge_proposal_worker = None

    def register_handler(self, task_type: str, handler) -> None:
        """
        Register a callable that executes a task type.

        Handler signature: handler(task: Dict[str,Any], progress: Callable[[Dict[str,Any]], None]) -> Any
        """
        if not task_type:
            return
        self.task_handlers[str(task_type)] = handler

    def start_worker(self) -> bool:
        """
        Start Smith's generic task executor loop (drains the in-memory queue).

        This is disabled in smoke/verify and test runs via `LIGHTSPEED_DISABLE_BACKGROUND_WORKERS=1`.
        """
        if os.environ.get("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS") == "1":
            return False
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return True

        self._worker_stop.clear()

        def _loop() -> None:
            while not self._worker_stop.is_set():
                task = None
                try:
                    task = self.get_next_task()
                except Exception:
                    task = None

                if not task:
                    time.sleep(0.25)
                    continue

                task_id = int(task.get("task_id") or 0)
                if task_id and task_id in self._cancelled:
                    try:
                        self.complete_task(task_id, error="Cancelled")
                    except Exception:
                        pass
                    continue

                def _progress(payload: Dict[str, Any]) -> None:
                    # Store progress in job metadata for UI visibility (Smith portal widget reads jobs table).
                    try:
                        db_job_id = task.get("db_job_id")
                        if db_job_id:
                            meta = {
                                "task_id": task_id,
                                "source_floor": task.get("source_floor"),
                                "task_type": task.get("task_type"),
                                "progress": payload or {},
                            }
                            self._update_job_row(int(db_job_id), metadata_json=json.dumps(meta))
                    except Exception:
                        pass
                    try:
                        if self.event_bus:
                            self.event_bus.publish("smith.task_progress", {"task_id": task_id, "progress": payload or {}})
                    except Exception:
                        pass

                handler = self.task_handlers.get(str(task.get("task_type") or ""))
                if not callable(handler):
                    try:
                        self.complete_task(task_id, error=f"No handler registered for '{task.get('task_type')}'")
                    except Exception:
                        pass
                    continue

                try:
                    res = handler(task, _progress)
                    self.complete_task(task_id, result=res)
                except Exception as e:
                    self.complete_task(task_id, error=str(e))

        self._worker_thread = threading.Thread(target=_loop, daemon=True)
        try:
            self._worker_thread.start()
            if self.logger:
                self.logger.info("[SmithQueue] Generic task worker started")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"[SmithQueue] Failed starting worker: {e}")
            return False

    def stop_worker(self) -> None:
        self._worker_stop.set()

    # ---------------------------------------------------------------------
    # Oracle ingestion worker controls (IT portal enables these explicitly)
    # ---------------------------------------------------------------------

    def has_oracle_ingestion_worker(self) -> bool:
        """Return True if the Oracle ingestion auto-worker is active in this process."""
        return self._oracle_ingestion_worker is not None

    def ensure_oracle_ingestion_worker_started(self) -> bool:
        """
        Ensure the Oracle ingestion auto-worker exists and is started.

        This allows N.py to start in "retrieve-only" mode (workers disabled) and later
        enable automation when an IT/Founder opens the Trinity IT Portal.
        """
        if os.environ.get("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS") == "1":
            return False
        if self._oracle_ingestion_worker is not None:
            return True
        try:
            self._oracle_ingestion_worker = _OracleIngestionAutoWorker(
                db=self.db,
                event_bus=self.event_bus,
                logger=self.logger,
            )
            self._oracle_ingestion_worker.start()
            return True
        except Exception:
            self._oracle_ingestion_worker = None
            return False

    def run_oracle_ingestion_cycle_once(self) -> Dict[str, Any]:
        """
        Run a single Oracle ingestion drain cycle (small batch).

        Intended for operator-triggered runs from Neo Lab Assistant / IT Portal.
        """
        if os.environ.get("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS") == "1":
            return {"success": False, "error": "workers_disabled"}
        if not self.ensure_oracle_ingestion_worker_started():
            return {"success": False, "error": "oracle_worker_unavailable"}
        try:
            return self._oracle_ingestion_worker.run_once()  # type: ignore[union-attr]
        except Exception as e:
            return {"success": False, "error": str(e)}

    def cancel_task(self, task_id: int) -> bool:
        """
        Best-effort cancellation for queued tasks.

        - If not started yet: marks as cancelled and removes from heaps on next dequeue.
        - If running: flags cancellation; handler must cooperate (progress callbacks can check).
        """
        try:
            task_id = int(task_id)
        except Exception:
            return False
        if task_id <= 0:
            return False
        self._cancelled.add(task_id)
        task = self.tasks.get(task_id)
        if isinstance(task, dict):
            task["status"] = TaskStatus.CANCELLED.value
            if task.get("db_job_id"):
                self._update_job_row(int(task["db_job_id"]), status=task["status"], error="Cancelled")
        try:
            if self.event_bus:
                self.event_bus.publish("smith.task_cancelled", {"task_id": task_id})
        except Exception:
            pass
        return True

    def _ensure_floor_quota(self, floor_id: str) -> None:
        if floor_id not in self.floor_quotas:
            self.floor_quotas[floor_id] = 5
        if floor_id not in self.floor_usage:
            self.floor_usage[floor_id] = 0

    def _insert_job_row(self, task: Dict[str, Any]) -> Optional[int]:
        if not self.db or not hasattr(self.db, "get_connection"):
            return None

        metadata = {
            'task_id': task.get('task_id'),
            'source_floor': task.get('source_floor'),
            'priority': task.get('priority'),
            'dependencies': task.get('dependencies') or [],
        }

        created_at = task.get('created_at') or datetime.now().isoformat()
        params_json = json.dumps(task.get('parameters') or {})
        status = task.get('status') or TaskStatus.PENDING.value

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """
                        INSERT INTO jobs (job_type, params_json, status, scheduled_for, created_at, metadata_json)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            task.get('task_type'),
                            params_json,
                            status,
                            None,
                            created_at,
                            json.dumps(metadata),
                        ),
                    )
                except Exception:
                    cursor.execute(
                        """
                        INSERT INTO jobs (job_type, params_json, status, scheduled_for, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (task.get('task_type'), params_json, status, None, created_at),
                    )
                return cursor.lastrowid
        except Exception as e:
            if self.logger:
                self.logger.error(f"[SmithQueue] DB insert failed: {e}")
            return None

    def _update_job_row(self, db_job_id: int, **fields: Any) -> None:
        if not self.db or not hasattr(self.db, "get_connection"):
            return
        if not db_job_id:
            return

        known = {}
        for key in ("status", "started_at", "completed_at", "result_json", "metadata_json", "error", "updated_at"):
            if key in fields:
                known[key] = fields[key]

        if not known:
            return

        known["updated_at"] = known.get("updated_at") or datetime.now().isoformat()

        columns = []
        params = []
        for k, v in known.items():
            columns.append(f"{k} = ?")
            params.append(v)
        params.append(db_job_id)
        query = f"UPDATE jobs SET {', '.join(columns)} WHERE id = ?"

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
        except Exception as e:
            if self.logger:
                self.logger.error(f"[SmithQueue] DB update failed: {e}")

    def add_task(self, task_type: str, parameters: Dict[str, Any],
                source_floor: str, priority: int = 3,
                dependencies: List[int] = None) -> int:
        """
        Add task to queue

        Parameters:
            task_type: Type of task
            parameters: Task parameters
            source_floor: Originating Z-floor
            priority: Priority level (1=critical, 5=deferred)
            dependencies: List of task_ids that must complete first

        Returns:
            Task ID
        """
        self.task_counter += 1
        task_id = self.task_counter

        self._ensure_floor_quota(source_floor)

        task = {
            'task_id': task_id,
            'task_type': task_type,
            'parameters': parameters,
            'source_floor': source_floor,
            'priority': priority,
            'dependencies': dependencies or [],
            'status': TaskStatus.QUEUED.value,
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None,
            'retry_count': 0
        }

        task['db_job_id'] = None
        self.tasks[task_id] = task

        # Add to heap if no dependencies
        if not task['dependencies']:
            heapq.heappush(self.task_heap, (priority, task_id))
            task['status'] = TaskStatus.PENDING.value
        else:
            task['status'] = TaskStatus.BLOCKED.value

        # Persist to database (best-effort)
        db_job_id = self._insert_job_row(task)
        task['db_job_id'] = db_job_id

        # Emit event
        if self.event_bus:
            self.event_bus.publish('smith.task_added', task)

        if self.logger:
            self.logger.info(f"[SmithQueue] Added task {task_id}: {task_type} (P{priority})")

        return task_id

    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """
        Get next task to execute (highest priority, respecting quotas)

        Returns:
            Task dict or None if queue empty
        """
        if not self.task_heap:
            return None

        # Find next task that doesn't exceed floor quota
        temp_removed = []
        next_task = None

        while self.task_heap:
            priority, task_id = heapq.heappop(self.task_heap)
            task = self.tasks[task_id]
            floor = task['source_floor']
            self._ensure_floor_quota(floor)

            # Check floor quota
            if self.floor_usage[floor] < self.floor_quotas[floor]:
                next_task = task
                next_task['status'] = TaskStatus.IN_PROGRESS.value
                next_task['started_at'] = datetime.now().isoformat()
                self.floor_usage[floor] += 1
                if next_task.get('db_job_id'):
                    self._update_job_row(
                        next_task['db_job_id'],
                        status=next_task['status'],
                        started_at=next_task['started_at'],
                    )
                break
            else:
                # Quota exceeded, try next task
                temp_removed.append((priority, task_id))

        # Re-add tasks that couldn't execute
        for item in temp_removed:
            heapq.heappush(self.task_heap, item)

        return next_task

    def complete_task(self, task_id: int, result: Any = None, error: str = None):
        """
        Mark task as completed

        Parameters:
            task_id: Task ID
            result: Task result (if successful)
            error: Error message (if failed)
        """
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        task['completed_at'] = datetime.now().isoformat()

        if error:
            task['status'] = TaskStatus.FAILED.value
            task['error'] = error

            # Retry logic
            if task['retry_count'] < 3:
                task['retry_count'] += 1
                task['status'] = TaskStatus.PENDING.value
                heapq.heappush(self.task_heap, (task['priority'], task_id))
                if self.logger:
                    self.logger.warning(f"[SmithQueue] Task {task_id} failed, retry {task['retry_count']}/3")
        else:
            task['status'] = TaskStatus.COMPLETED.value
            task['result'] = result

        # Release floor quota
        floor = task['source_floor']
        self.floor_usage[floor] = max(0, self.floor_usage[floor] - 1)

        # Check for unblocked tasks
        self._check_unblocked_tasks(task_id)

        # Update database
        if task.get('db_job_id'):
            self._update_job_row(
                task['db_job_id'],
                status=task['status'],
                completed_at=task['completed_at'],
                result_json=json.dumps(result) if result is not None else None,
                error=error,
            )

        # Emit event
        if self.event_bus:
            self.event_bus.publish('smith.task_completed', task)

        # Add to history
        self.execution_history.append({
            'task_id': task_id,
            'task_type': task['task_type'],
            'completed_at': task['completed_at'],
            'duration_seconds': self._calculate_duration(task),
            'status': task['status']
        })

        if self.logger:
            self.logger.info(f"[SmithQueue] Completed task {task_id}: {task['task_type']}")

    def _check_unblocked_tasks(self, completed_task_id: int):
        """Check if any blocked tasks can now be unblocked"""
        for task_id, task in self.tasks.items():
            if task['status'] == TaskStatus.BLOCKED.value:
                # Check if all dependencies completed
                all_deps_completed = all(
                    self.tasks[dep_id]['status'] == TaskStatus.COMPLETED.value
                    for dep_id in task['dependencies']
                    if dep_id in self.tasks
                )

                if all_deps_completed:
                    task['status'] = TaskStatus.PENDING.value
                    heapq.heappush(self.task_heap, (task['priority'], task_id))
                    if self.logger:
                        self.logger.info(f"[SmithQueue] Unblocked task {task_id}")

    def _calculate_duration(self, task: Dict[str, Any]) -> float:
        """Calculate task duration in seconds"""
        if not task['started_at'] or not task['completed_at']:
            return 0.0

        start = datetime.fromisoformat(task['started_at'])
        end = datetime.fromisoformat(task['completed_at'])
        return (end - start).total_seconds()

    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status summary"""
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(
                1 for task in self.tasks.values()
                if task['status'] == status.value
            )

        floor_stats = {}
        for floor in self.floor_quotas:
            floor_stats[floor] = {
                'quota': self.floor_quotas[floor],
                'usage': self.floor_usage[floor],
                'available': self.floor_quotas[floor] - self.floor_usage[floor]
            }

        return {
            'total_tasks': len(self.tasks),
            'queue_size': len(self.task_heap),
            'status_counts': status_counts,
            'floor_stats': floor_stats,
            'history_size': len(self.execution_history)
        }

    def get_floor_tasks(self, floor: str) -> List[Dict[str, Any]]:
        """Get all tasks for specific floor"""
        return [
            task for task in self.tasks.values()
            if task['source_floor'] == floor
        ]

    def prioritize_test_execution(self, test_file_path: str,
                                  dependencies_completed: bool = True) -> int:
        """
        Smart test execution prioritization

        Tests are held until all dependency files are processed
        and objects are committed to their respective floors.

        Parameters:
            test_file_path: Path to test file
            dependencies_completed: Whether all dependency data is ready

        Returns:
            Task ID (or 0 if held)
        """
        if not dependencies_completed:
            # Hold test in pending queue
            if self.logger:
                self.logger.info(f"[SmithQueue] Test held: {test_file_path} (dependencies pending)")
            return 0

        # All dependencies ready, execute test
        task_id = self.add_task(
            task_type='execute_test',
            parameters={'test_file': test_file_path},
            source_floor='Z0_TheConstruct',
            priority=TaskPriority.HIGH.value
        )

        if self.logger:
            self.logger.info(f"[SmithQueue] Test queued: {test_file_path} (task_id={task_id})")

        return task_id

    def process_oracle_extraction(self, vault_id: int, priority: int = 2) -> int:
        """
        Queue Oracle file extraction task

        Parameters:
            vault_id: Oracle vault file ID
            priority: Task priority

        Returns:
            Task ID
        """
        return self.add_task(
            task_type='oracle_extraction',
            parameters={'vault_id': vault_id},
            source_floor='Z-2_Oracle',
            priority=priority
        )

    def cleanup_unused_files(self, scan_paths: List[str]) -> int:
        """
        Queue cleanup task for unused/unlinked files

        Parameters:
            scan_paths: Paths to scan for orphaned files

        Returns:
            Task ID
        """
        return self.add_task(
            task_type='cleanup_unused',
            parameters={'scan_paths': scan_paths},
            source_floor='Z-3_Smith',
            priority=TaskPriority.LOW.value
        )

    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get task execution metrics"""
        if not self.execution_history:
            return {'message': 'No execution history'}

        total_completed = len(self.execution_history)
        total_duration = sum(h['duration_seconds'] for h in self.execution_history)
        avg_duration = total_duration / total_completed if total_completed > 0 else 0

        task_type_counts = {}
        for h in self.execution_history:
            task_type = h['task_type']
            task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1

        return {
            'total_completed': total_completed,
            'total_duration_seconds': total_duration,
            'average_duration_seconds': avg_duration,
            'task_types': task_type_counts
        }


class _OracleIngestionAutoWorker:
    """
    Background worker that drains Oracle's DB-backed ingestion queue.

    - Watches `oracle_ingestion_tasks` (queued/pending)
    - Runs `OracleSmartFloorIntegrator.process_pending_tasks()` in cycles
    - Publishes lightweight status updates into the `jobs` table for visibility
    """

    _singleton_lock = threading.Lock()
    _singleton_started = False

    def __init__(self, *, db=None, event_bus=None, logger=None):
        self.db = db
        self.event_bus = event_bus
        self.logger = logger

        self.tick_seconds = 1.0
        self.batch_size = 3

        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._job_id: Optional[int] = None
        self._oracle = None
        self._last_dir_ingest_digest: Optional[str] = None
        # Aggregate Oracle route events so we can stage a small number of high-signal
        # tasks instead of flooding Trinity with one task per file.
        self._route_buffer: Dict[str, Dict[str, Any]] = {}
        self._route_last_flush: Dict[str, float] = {}
        self._route_min_flush_seconds = 8.0
        self._route_max_samples = 50

        # Wake faster when Oracle ingests a file.
        try:
            if self.event_bus is not None:
                self.event_bus.subscribe("oracle.file_ingested", lambda _evt: self._wake.set())
                self.event_bus.subscribe("oracle.directory_ingested", self._on_oracle_directory_ingested)
                self.event_bus.subscribe("oracle.route", self._on_oracle_route)
        except Exception:
            pass

    def _on_oracle_route(self, evt: Any) -> None:
        """
        Aggregate Oracle route events into per-floor summaries.

        Oracle emits `oracle.route` when extraction finds keyword matches (and we added
        fallback routing for code/data + always-Morpheus indexing). This worker batches
        those into a small number of review tasks that appear in Trinity and per-floor inboxes.
        """
        # Respect smoke/verify safety: avoid side effects when background workers are explicitly disabled.
        try:
            if os.environ.get("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS", "").strip() == "1":
                return
        except Exception:
            return

        data = None
        try:
            data = evt.data if hasattr(evt, "data") else evt
        except Exception:
            data = None
        if not isinstance(data, dict):
            return

        target = str(data.get("target_floor") or "").strip()
        if not target:
            return

        buf = self._route_buffer.setdefault(
            target,
            {"count": 0, "samples": [], "last_seen_at": None},
        )
        buf["count"] = int(buf.get("count") or 0) + 1
        buf["last_seen_at"] = datetime.now().isoformat()

        if len(buf["samples"]) < int(self._route_max_samples):
            try:
                fm = data.get("file_metadata") if isinstance(data.get("file_metadata"), dict) else {}
                sample = {
                    "vault_id": data.get("vault_id"),
                    "matched_keywords": data.get("matched_keywords") if isinstance(data.get("matched_keywords"), list) else [],
                    "original_name": fm.get("original_name"),
                    "original_path": fm.get("original_path"),
                    "vault_path": fm.get("vault_path"),
                }
                buf["samples"].append(sample)
            except Exception:
                pass

        try:
            self._wake.set()
        except Exception:
            pass

    def _on_oracle_directory_ingested(self, evt: Any) -> None:
        """
        When Oracle completes a directory ingestion batch, stage one reconciliation task into Trinity.

        This keeps the automation loop observable and ensures operators see a single actionable item
        instead of a silent batch.
        """
        # Respect smoke/verify safety: avoid side effects when background workers are explicitly disabled.
        try:
            if os.environ.get("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS", "").strip() == "1":
                return
        except Exception:
            return

        data = None
        try:
            data = evt.data if hasattr(evt, "data") else evt
        except Exception:
            data = None
        if not isinstance(data, dict):
            return

        directory = str(data.get("directory") or "").strip()
        if not directory:
            return

        # Stage a single summary task for any directory ingest (deduped by digest).
        is_legacy = "legacy_packs" in directory.replace("\\", "/").lower()

        # Deduplicate: ignore identical summaries.
        try:
            digest_src = json.dumps(
                {
                    "directory": directory,
                    "files_total": data.get("files_total"),
                    "files_ingested": data.get("files_ingested"),
                    "files_deduped": data.get("files_deduped"),
                    "files_failed": data.get("files_failed"),
                },
                sort_keys=True,
                ensure_ascii=True,
                default=str,
            )
            digest = hashlib.sha256(digest_src.encode("utf-8", errors="replace")).hexdigest()
        except Exception:
            digest = None

        if digest and digest == self._last_dir_ingest_digest:
            return
        self._last_dir_ingest_digest = digest

        # Build a single high-signal task for Trinity review (approval-gated).
        try:
            results = data.get("results") if isinstance(data.get("results"), list) else []
        except Exception:
            results = []

        sample = []
        for r in (results or [])[:50]:
            if not isinstance(r, dict):
                continue
            sample.append(
                {
                    "path": r.get("path"),
                    "success": bool(r.get("success")),
                    "already_archived": bool(r.get("already_archived")),
                    "vault_id": r.get("vault_id"),
                }
            )

        task = {
            "kind": "task",
            "id": f"legacy_packs_reconcile_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": ("Legacy packs reconciliation sweep (Oracle vault -> V1R alignment)" if is_legacy else "Oracle directory ingestion summary"),
            "description": (
                (
                    "Oracle completed a legacy_packs directory sweep. Review the sample vault_ids/paths, "
                    "then decide what to merge into the canonical 8-floor runtime via Z Direct approvals."
                )
                if is_legacy
                else (
                    "Oracle completed a directory ingestion batch. Review the sample vault_ids/paths and the "
                    "routing summaries, then decide what to execute/commit via Z Direct approvals."
                )
            ),
            "status": "todo",
            "priority": int(getattr(TaskPriority.HIGH, "value", 2)),
            "tags": (["legacy_packs", "reconciliation", "oracle", "v1r"] if is_legacy else ["oracle", "ingestion", "summary"]),
            "details": {
                "directory": directory,
                "files_total": data.get("files_total"),
                "files_ingested": data.get("files_ingested"),
                "files_deduped": data.get("files_deduped"),
                "files_failed": data.get("files_failed"),
                "sample": sample,
                "operator_steps": [
                    (
                        "Open Trinity IT Portal -> Z Direct -> filter tags legacy_packs"
                        if is_legacy
                        else "Open Trinity IT Portal -> Z Direct -> filter tags oracle/ingestion"
                    ),
                    "Review sample vault_ids and open items via Oracle floor (Library/IP Vault/Encyclopedia)",
                    "Triage into floor-owned actions (Neo objectify, Morpheus index, Architect projects, etc.)",
                ],
            },
        }

        try:
            from core.services import get_z_direct  # type: ignore

            zd = get_z_direct()
            env = zd.make_envelope(
                kind="object",
                channel="Z-3",
                payload=task,
                z_context="Z-3_Smith",
                source="smith.oracle_ingestion.directory",
                tags=(["task", "legacy_packs", "reconciliation"] if is_legacy else ["task", "oracle", "ingestion"]),
            )
            # Keep Smith observable and route to Trinity for review/commit.
            try:
                zd.append_object("Z-3", env)
            except Exception:
                pass
            try:
                zd.append_channel_outbox(from_channel="Z-3", to_channel="Z+3", payload=env)
            except Exception:
                pass
            try:
                zd.append_channel_inbox(to_channel="Z+3", from_channel="Z-3", payload=env)
            except Exception:
                pass
        except Exception:
            return

    def _flush_route_buffer(self) -> None:
        """
        Emit at most one routed-task per floor every `_route_min_flush_seconds` seconds.

        Tasks are staged into Trinity (for governance) and also copied into the target floor inbox
        for floor-local visibility (still non-durable; approvals happen in Trinity).
        """
        if not self._route_buffer:
            return

        try:
            from core.services import get_z_direct  # type: ignore
            zd = get_z_direct()
        except Exception:
            return

        now = time.monotonic()

        def _floor_to_channel(floor_id: str) -> str:
            s = (floor_id or "").strip().upper()
            # Expected shapes: "Z+2_Neo", "Z-1_Morpheus", "Z0_TheConstruct"
            if s.startswith("Z+3"):
                return "Z+3"
            if s.startswith("Z+2"):
                return "Z+2"
            if s.startswith("Z+1"):
                return "Z+1"
            if s.startswith("Z0"):
                return "Z0"
            if s.startswith("Z-1"):
                return "Z-1"
            if s.startswith("Z-2"):
                return "Z-2"
            if s.startswith("Z-3"):
                return "Z-3"
            if s.startswith("Z-4"):
                return "Z-4"
            return "Z+3"

        for target_floor, buf in list(self._route_buffer.items()):
            last = float(self._route_last_flush.get(target_floor, 0.0) or 0.0)
            if (now - last) < float(self._route_min_flush_seconds):
                continue

            count = int(buf.get("count") or 0)
            samples = buf.get("samples") if isinstance(buf.get("samples"), list) else []
            if count <= 0 and not samples:
                self._route_buffer.pop(target_floor, None)
                continue

            task = {
                "kind": "task",
                "id": f"oracle_route_{target_floor.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "title": f"Oracle routed items -> {target_floor} ({count})",
                "description": (
                    "Oracle extracted/routed new items for this floor. Review samples and decide whether to "
                    "run automation / objectification or keep as indexed references."
                ),
                "status": "todo",
                "priority": int(getattr(TaskPriority.MEDIUM, "value", 3)),
                "tags": ["oracle", "route", "handoff", target_floor],
                "details": {
                    "target_floor": target_floor,
                    "count": count,
                    "samples": samples[: int(self._route_max_samples)],
                    "operator_steps": [
                        "Open Trinity IT Portal -> Z Direct -> filter tags oracle/route",
                        "Open the target floor tab and inspect the routed samples",
                        "If approved, stage/commit the resulting objects/workflows via Z Direct",
                    ],
                },
            }

            env = zd.make_envelope(
                kind="object",
                channel="Z-3",
                payload=task,
                z_context="Z-3_Smith",
                source="smith.oracle_ingestion.route",
                tags=["task", "oracle", "route", target_floor],
            )

            # Smith is the Z Direct manager for automation: keep an internal ledger of staged tasks.
            try:
                zd.append_object("Z-3", env)
            except Exception:
                pass

            # Route to Trinity (governance)
            try:
                zd.append_channel_outbox(from_channel="Z-3", to_channel="Z+3", payload=env)
            except Exception:
                pass
            try:
                zd.append_channel_inbox(to_channel="Z+3", from_channel="Z-3", payload=env)
            except Exception:
                pass

            # Also make the task visible in the target floor channel inbox.
            target_channel = _floor_to_channel(target_floor)
            try:
                zd.append_channel_inbox(to_channel=target_channel, from_channel="Z-3", payload=env)
            except Exception:
                pass

            # Reset per-floor buffer after flushing.
            self._route_last_flush[target_floor] = now
            self._route_buffer.pop(target_floor, None)

    def start(self):
        with type(self)._singleton_lock:
            if type(self)._singleton_started:
                return
            type(self)._singleton_started = True

        self._thread = threading.Thread(
            target=self._run_loop,
            name="OracleIngestionAutoWorker",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._wake.set()

    def run_once(self) -> Dict[str, Any]:
        """Run a single ingestion cycle (useful for tests/smoke checks)."""
        return self._cycle()

    def _run_loop(self):
        try:
            self._ensure_job_row()
        except Exception:
            pass

        if self.logger:
            try:
                self.logger.info("[SmithQueue] Oracle ingestion auto-worker started")
            except Exception:
                pass

        while not self._stop.is_set():
            self._cycle()
            # Wait either for wake event or next tick
            self._wake.wait(self.tick_seconds)
            self._wake.clear()

    def _cycle(self) -> Dict[str, Any]:
        now = datetime.now().isoformat()

        oracle = self._get_oracle_integrator()
        if oracle is None:
            self._update_job(status="failed", error="OracleSmartFloorIntegrator unavailable", updated_at=now)
            return {"success": False, "error": "integrator_unavailable"}

        try:
            before = oracle.get_queue_status()
        except Exception:
            before = {}

        processed = 0
        failed = 0
        try:
            out = oracle.process_pending_tasks(max_tasks=int(self.batch_size))
            for r in out or []:
                if r.get("success"):
                    processed += 1
                else:
                    failed += 1
        except Exception as e:
            self._update_job(status="failed", error=str(e), updated_at=now)
            return {"success": False, "error": str(e)}

        try:
            after = oracle.get_queue_status()
        except Exception:
            after = {}

        payload = {
            "success": True,
            "processed": processed,
            "failed": failed,
            "queue_before": before,
            "queue_after": after,
            "last_run_at": now,
        }

        self._update_job(
            status="running",
            result_json=json.dumps(payload, ensure_ascii=False),
            updated_at=now,
        )

        try:
            if self.event_bus is not None and (processed or failed):
                self.event_bus.publish("smith.oracle_ingestion.cycle", payload)
        except Exception:
            pass

        # Best-effort: flush aggregated Oracle routing events into Trinity review queue.
        try:
            self._flush_route_buffer()
        except Exception:
            pass

        return payload

    def _ensure_job_row(self):
        if self._job_id is not None:
            return
        if not self.db or not hasattr(self.db, "get_connection"):
            return

        created_at = datetime.now().isoformat()
        params = json.dumps({"tick_seconds": self.tick_seconds, "batch_size": self.batch_size}, ensure_ascii=False)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO jobs (job_type, params_json, status, scheduled_for, created_at, started_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("oracle_ingestion_worker", params, "running", None, created_at, created_at, created_at),
            )
            self._job_id = int(cur.lastrowid)

    def _update_job(self, **fields: Any):
        if self._job_id is None:
            try:
                self._ensure_job_row()
            except Exception:
                return
        if self._job_id is None:
            return
        if not self.db or not hasattr(self.db, "get_connection"):
            return

        allowed = {"status", "started_at", "completed_at", "result_json", "error", "updated_at"}
        cols = []
        params = []
        for k, v in fields.items():
            if k in allowed:
                cols.append(f"{k}=?")
                params.append(v)
        if not cols:
            return
        params.append(self._job_id)
        q = f"UPDATE jobs SET {', '.join(cols)} WHERE id=?"
        try:
            with self.db.get_connection() as conn:
                conn.cursor().execute(q, tuple(params))
        except Exception:
            return

    def _get_oracle_integrator(self):
        if self._oracle is not None:
            return self._oracle

        # Load from file so we don't depend on invalid module names (Z-2_Oracle).
        try:
            root = Path(__file__).resolve()
            for cand in (root, *root.parents):
                if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                    lightspeed_root = cand
                    break
            else:
                lightspeed_root = root.parents[4]

            oracle_path = (
                lightspeed_root
                / "Z Axis"
                / "Z-2_Oracle"
                / "components"
                / "oracle_smart_floor_integrator.py"
            ).resolve()
            spec = spec_from_file_location("lightspeed_oracle_integrator", oracle_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load Oracle integrator from {oracle_path}")
            mod = module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            cls = getattr(mod, "OracleSmartFloorIntegrator")
            self._oracle = cls()
            return self._oracle
        except Exception as e:
            if self.logger:
                try:
                    self.logger.warning(f"[SmithQueue] Oracle integrator load failed: {e}")
                except Exception:
                    pass
            return None


# Standalone test
if __name__ == '__main__':
    queue = SmithTaskQueue()
    print("[SmithQueue] Smith Task Queue ready")
    print(f"Floor quotas: {queue.floor_quotas}")

    # Test: Add some tasks
    t1 = queue.add_task('test_1', {}, 'Z-2_Oracle', priority=1)
    t2 = queue.add_task('test_2', {}, 'Z-2_Oracle', priority=2, dependencies=[t1])
    t3 = queue.add_task('test_3', {}, 'Z0_TheConstruct', priority=1)

    print(f"\nAdded 3 tasks")
    print(f"Queue status: {queue.get_queue_status()}")

    # Execute tasks
    task = queue.get_next_task()
    if task:
        print(f"\nNext task: {task['task_id']} - {task['task_type']}")
        queue.complete_task(task['task_id'], result={'status': 'success'})

    print(f"\nQueue status after execution: {queue.get_queue_status()}")
