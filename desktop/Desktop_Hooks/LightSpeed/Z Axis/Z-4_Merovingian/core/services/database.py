"""
Database Service - Core Infrastructure Layer
LightSpeed Type I Civilization Platform

This service provides the foundational database abstraction layer connecting
all Z-axis floors through the unified SQLite database (lightspeed_unified.db).

Supports all 9 floors:
- Neo (Z+3): AI Integration & Cognigrex
- Morpheus (Z+2): Knowledge & File Analysis
- Architect (Z+1): Time & Mission Planning
- TheConstruct (Z0): Physics & Simulations
- Oracle (Z-1): Archives & IP Vault
- Smith (Z-2): Background Jobs & SOPs
- Merovingian (Z-3): Diagnostics & Telemetry
- Trinity: Cross-layer Dashboards
- Services: Shared basement layer

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
"""

import sqlite3
import json
import datetime
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
import logging
from functools import wraps

# V1 dataspace (immutable job outputs)
from .dataspace import get_dataspace, sha256_file

# Centralized paths (Z-floor aware)
try:
    from core.config.paths import LIGHTSPEED_ROOT, MEROVINGIAN_DATA  # type: ignore
except Exception:
    LIGHTSPEED_ROOT = Path(__file__).resolve()
    for _cand in (LIGHTSPEED_ROOT, *LIGHTSPEED_ROOT.parents):
        if (_cand / "N.py").exists() and (_cand / "Z Axis").exists():
            LIGHTSPEED_ROOT = _cand
            break
    MEROVINGIAN_DATA = LIGHTSPEED_ROOT / "Z Axis" / "Z-4_Merovingian" / "data"

# Configure logging for database operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def retry_on_locked(max_retries=3, backoff_factor=0.5):
    """
    Decorator to retry database operations on 'database is locked' errors.
    Uses exponential backoff between retries.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Multiplier for delay between retries (default: 0.5s)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if 'locked' in str(e).lower() and attempt < max_retries - 1:
                        delay = backoff_factor * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Database locked, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        raise
            return func(*args, **kwargs)
        return wrapper
    return decorator


class DatabaseService:
    """
    Unified database service for all LightSpeed layers.

    Provides connection pooling, transaction management, and
    standardized query interfaces across all Z-axis floors.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database service.

        Parameters:
            db_path: Path to SQLite database file
                     Default: Z Axis/Z-4_Merovingian/data/db/lightspeed_unified.db
        """
        if db_path is None:
            # Canonical: prefer floor-native Merovingian data store.
            # Trinity (Z+3) owns setup flow and explicit schema migrations; runtime must not silently mutate schema.
            self.legacy_db_path = Path(LIGHTSPEED_ROOT) / "Data" / "lightspeed_unified.db"
            self.db_path = Path(MEROVINGIAN_DATA) / "db" / "lightspeed_unified.db"
            self.legacy_db_found = bool(self.legacy_db_path.exists() and not self.db_path.exists())
        else:
            self.db_path = Path(db_path)
            self.legacy_db_path = None
            self.legacy_db_found = False

        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        # Ensure database exists
        if not self.db_path.exists():
            logger.warning(f"Database not found at {self.db_path}")
            logger.info("Database will be created on first connection")

        logger.info(f"Database service initialized: {self.db_path}")

        # Validate schema (read-only). Trinity (Z+3) owns explicit schema migrations.
        self.schema_report: Optional[Dict[str, Any]] = None
        self.schema_ok: Optional[bool] = None
        try:
            self.schema_report = self.validate_schema()
            self.schema_ok = bool((self.schema_report or {}).get("ok"))
        except Exception as e:
            logger.warning(f"Schema validation failed: {e}")

    def validate_schema(self) -> Dict[str, Any]:
        """
        Validate DB schema without mutating it.

        Returns a report that the UI can surface and that Trinity (Z+3) can use
        to decide which migration steps to run.
        """
        required: Dict[str, List[str]] = {
            "companies": ["id", "name"],
            "users": ["id", "username", "role", "clearance"],
            "z_contexts": ["id", "key", "name"],
            "projects": ["id", "name", "company_id", "owner_id", "created_at"],
            "tasks": ["id", "title", "project_id", "status", "priority", "created_at"],
            "jobs": ["id", "job_type", "status", "created_at"],
            "artifacts": ["id", "job_id", "z_context", "kind", "path", "sha256", "created_at"],
            "files": ["id", "path", "name", "hash_sha256", "status", "project_id", "vault_id", "extraction_status"],
            "templates": ["id", "name", "category", "created_at"],
            "oracle_ingestion_tasks": ["id", "vault_id", "task_type", "status", "created_at"],
            "calculator_modules": ["id", "name", "filepath", "floor", "category", "status", "created_at"],
            "scientific_datasets": ["id", "filename", "filepath", "category", "format", "size_bytes", "created_at"],
            # Per-user UI/layout persistence (created by Trinity migrations).
            "user_preferences": ["user_id", "theme", "font_size", "font_family", "accent_color", "widget_layout", "preferences_json", "updated_at"],
        }

        report: Dict[str, Any] = {
            "ok": True,
            "missing_tables": [],
            "missing_columns": {},
            "legacy_db_found": bool(getattr(self, "legacy_db_found", False)),
        }

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            present_tables = set()
            for row in cursor.fetchall():
                try:
                    name = row.get("name") if isinstance(row, dict) else row[0]
                except Exception:
                    name = None
                if name:
                    present_tables.add(name)

            for table, cols in required.items():
                if table not in present_tables:
                    report["missing_tables"].append(table)
                    report["ok"] = False
                    continue

                cursor.execute(f"PRAGMA table_info({table})")
                present_cols = set()
                for row in cursor.fetchall():
                    try:
                        col = row.get("name") if isinstance(row, dict) else row[1]
                    except Exception:
                        col = None
                    if col:
                        present_cols.add(col)
                missing = [c for c in cols if c not in present_cols]
                if missing:
                    report["missing_columns"][table] = missing
                    report["ok"] = False

        return report

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Ensures proper connection handling and automatic cleanup.

        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ...")
        """
        def dict_factory(cursor, row):
            """
            Custom row factory that returns dict-like objects supporting .get()
            This fixes compatibility issues with code expecting dict.get() method
            """
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        conn = sqlite3.connect(str(self.db_path), timeout=30.0)  # 30 second timeout
        conn.row_factory = dict_factory  # Return dicts for .get() compatibility

        # Enable WAL mode for better concurrency (allows simultaneous readers + 1 writer)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")  # 30 seconds
        except Exception as e:
            logger.warning(f"Could not enable WAL mode: {e}")

        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    @retry_on_locked(max_retries=3, backoff_factor=0.5)
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute SELECT query and return results as list of dicts.

        Parameters:
            query: SQL SELECT query
            params: Query parameters (for parameterized queries)

        Returns:
            List of dictionaries (one per row)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            if not rows:
                return []

            # When using dict_factory row_factory, rows are already dicts.
            if isinstance(rows[0], dict):
                logger.debug(f"Query returned {len(rows)} rows")
                return rows  # type: ignore[return-value]

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = [dict(zip(columns, row)) for row in rows]
            logger.debug(f"Query returned {len(results)} rows")
            return results

    @retry_on_locked(max_retries=3, backoff_factor=0.5)
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """
        Execute INSERT/UPDATE/DELETE query.

        Parameters:
            query: SQL modification query
            params: Query parameters

        Returns:
            Number of rows affected
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows_affected = cursor.rowcount
            logger.debug(f"Query affected {rows_affected} rows")
            return rows_affected

    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        Execute batch INSERT/UPDATE operations.

        Parameters:
            query: SQL query
            params_list: List of parameter tuples

        Returns:
            Number of rows affected
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            rows_affected = cursor.rowcount
            logger.debug(f"Batch query affected {rows_affected} rows")
            return rows_affected

    # ========================================================================
    # COMPATIBILITY METHODS (legacy callers)
    # ========================================================================

    def execute(self, query: str, params: Tuple = ()) -> int:
        """
        Compatibility wrapper for legacy code that expects `db.execute(...)`.

        Returns:
            Number of rows affected (SQLite cursor.rowcount where available).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount

    def fetchall(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """
        Compatibility wrapper returning sqlite3.Row objects (indexable + dict-like).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def fetchone(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """
        Compatibility wrapper returning a single sqlite3.Row (or None).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    def executemany(self, query: str, params_list: List[Tuple]) -> int:
        """
        Compatibility wrapper for batch operations.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount

    # ========================================================================
    # FLOOR-SPECIFIC METHODS
    # ========================================================================

    # --- NEO LAYER (Z+3): AI Integration & Cognigrex ---

    def log_ai_interaction(self, user_id: int, prompt: str, response: str,
                          model: str = "cognigrex") -> int:
        """
        Log AI interaction to Neo layer database.

        Parameters:
            user_id: User ID
            prompt: User prompt/query
            response: AI response
            model: AI model used

        Returns:
            Interaction ID
        """
        query = """
        INSERT INTO ai_interactions (user_id, prompt, response, model, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """
        timestamp = datetime.datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, prompt, response, model, timestamp))
            interaction_id = cursor.lastrowid
            logger.info(f"Logged AI interaction: {interaction_id}")
            return interaction_id

    # --- MORPHEUS LAYER (Z+2): Knowledge & File Analysis ---

    def register_file(
        self,
        filename: str,
        filepath: str,
        file_type: str,
        size_bytes: int,
        checksum: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Register file in Morpheus knowledge database.

        Parameters:
            filename: Name of file
            filepath: Full path to file
            file_type: File extension/type (file extension like '.txt')
            size_bytes: File size in bytes
            checksum: SHA256 checksum (optional)
            metadata: Optional metadata dict (stored as JSON when supported)

        Returns:
            File ID
        """
        metadata_json = None
        try:
            if metadata is not None:
                metadata_json = json.dumps(metadata)
        except Exception:
            metadata_json = None

        # If schema is known-bad, avoid hard failures/spam during startup.
        # UI should prompt an IT Portal migration (Trinity-owned); runtime should keep operating in read-only mode.
        if getattr(self, "schema_ok", None) is False:
            logger.warning("DB schema invalid; skipping file registration until migration is applied")
            return -1

        def _table_columns(cursor: sqlite3.Cursor, table: str) -> set:
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                return {row.get("name") if isinstance(row, dict) else row[1] for row in cursor.fetchall()}
            except Exception:
                return set()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cols = _table_columns(cursor, "files")
            if not cols:
                raise RuntimeError("files table missing or unreadable")

            path_col = "path" if "path" in cols else ("filepath" if "filepath" in cols else ("original_path" if "original_path" in cols else None))
            name_col = "name" if "name" in cols else ("filename" if "filename" in cols else None)
            ext_col = "extension" if "extension" in cols else ("file_type" if "file_type" in cols else None)
            size_col = "size_bytes" if "size_bytes" in cols else ("file_size" if "file_size" in cols else None)
            hash_col = "hash_sha256" if "hash_sha256" in cols else ("checksum" if "checksum" in cols else ("file_hash" if "file_hash" in cols else None))
            status_col = "status" if "status" in cols else None
            meta_col = "metadata_json" if "metadata_json" in cols else ("metadata" if "metadata" in cols else None)
            created_col = "created_at" if "created_at" in cols else None

            if path_col is None or name_col is None:
                raise RuntimeError("Unsupported files table schema (missing path/name equivalents)")

            insert_cols: List[str] = []
            params: List[Any] = []

            insert_cols.append(path_col)
            params.append(filepath)

            insert_cols.append(name_col)
            params.append(filename)

            if ext_col is not None:
                insert_cols.append(ext_col)
                params.append(str(file_type or ""))

            if size_col is not None:
                insert_cols.append(size_col)
                params.append(int(size_bytes))

            if hash_col is not None:
                insert_cols.append(hash_col)
                params.append(checksum)

            if status_col is not None:
                insert_cols.append(status_col)
                params.append("pending")

            if meta_col is not None:
                insert_cols.append(meta_col)
                params.append(metadata_json)

            if created_col is not None:
                insert_cols.append(created_col)
                params.append(datetime.datetime.now().isoformat())

            placeholders = ", ".join(["?"] * len(insert_cols))
            col_sql = ", ".join(insert_cols)
            cursor.execute(f"INSERT INTO files ({col_sql}) VALUES ({placeholders})", tuple(params))
            file_id = cursor.lastrowid
            logger.info(f"Registered file: {filename} (ID: {file_id})")
            return int(file_id)

    def get_file_analysis(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve file analysis results from Morpheus layer.

        Parameters:
            file_id: File ID

        Returns:
            Analysis data or None
        """
        query = "SELECT * FROM files WHERE id = ?"
        results = self.execute_query(query, (file_id,))
        return results[0] if results else None

    # --- ARCHITECT LAYER (Z+1): Time & Mission Planning ---

    def create_task(self, title: str, description: str, project_id: Optional[int] = None,
                   assigned_to: Optional[int] = None, priority: str = "medium",
                   status: str = "pending") -> int:
        """
        Create task in Architect mission planning system.

        Parameters:
            title: Task title
            description: Task description
            project_id: Associated project ID
            assigned_to: User ID assigned to task
            priority: low, medium, high, critical
            status: pending, in_progress, completed, blocked

        Returns:
            Task ID
        """
        query = """
        INSERT INTO tasks (title, description, project_id, assigned_to,
                          priority, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        timestamp = datetime.datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (title, description, project_id, assigned_to,
                                 priority, status, timestamp))
            task_id = cursor.lastrowid
            logger.info(f"Created task: {title} (ID: {task_id})")
            return task_id

    def get_active_tasks(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get active tasks from Architect layer.

        Parameters:
            user_id: Filter by assigned user (None = all tasks)

        Returns:
            List of active tasks
        """
        if user_id:
            query = """
            SELECT * FROM v_active_tasks
            WHERE assigned_to = ?
            ORDER BY priority DESC, created_at ASC
            """
            return self.execute_query(query, (user_id,))
        else:
            query = "SELECT * FROM v_active_tasks ORDER BY priority DESC, created_at ASC"
            return self.execute_query(query)

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get a single task by ID."""
        rows = self.execute_query("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return rows[0] if rows else None

    def update_task(self, task_id: int, **updates: Any) -> bool:
        """
        Update a task (title/description/status/priority/etc.).

        Returns:
            True if any row was updated.
        """
        allowed = {"title", "description", "status", "priority", "assigned_to", "project_id", "company_id", "metadata_json"}
        set_parts: list[str] = []
        params: list[Any] = []
        for key, value in updates.items():
            if key not in allowed:
                continue
            set_parts.append(f"{key} = ?")
            params.append(value)

        # Touch updated_at when present.
        set_parts.append("updated_at = ?")
        params.append(datetime.datetime.now().isoformat())

        if not set_parts:
            return False

        params.append(task_id)
        query = "UPDATE tasks SET " + ", ".join(set_parts) + " WHERE id = ?"
        try:
            return self.execute_update(query, tuple(params)) > 0
        except Exception:
            return False

    def create_interfloor_task(
        self,
        source_floor: str,
        target_floor: str,
        task_type: str,
        payload: Dict[str, Any],
        priority: str = "medium",
        deadline: Optional[str] = None,
        requires_neo_signoff: bool = False,
    ) -> int:
        """
        Create an inter-floor task for Smith/Neo coordination.

        `priority` is normalized into an integer (1=critical..5=low).
        `deadline` is stored into parameters for forward compatibility.
        """
        priority_map = {"critical": 1, "high": 2, "medium": 3, "normal": 3, "low": 4}
        prio = priority_map.get((priority or "medium").strip().lower(), 3)

        parameters: Dict[str, Any] = dict(payload or {})
        if deadline:
            parameters["deadline"] = deadline

        created_at = datetime.datetime.now().isoformat()
        target_floors_json = json.dumps([str(target_floor)])
        parameters_json = json.dumps(parameters)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO interfloor_tasks
                  (task_type, source_floor, target_floors, parameters, priority, status, requires_neo_signoff, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    str(task_type),
                    str(source_floor),
                    target_floors_json,
                    parameters_json,
                    int(prio),
                    1 if requires_neo_signoff else 0,
                    created_at,
                ),
            )
            return int(cursor.lastrowid)

    def get_interfloor_tasks_by_floor(self, floor_name: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks targeting a given floor (best-effort JSON LIKE match)."""
        floor = (floor_name or "").strip()
        if not floor:
            return []
        query = "SELECT * FROM interfloor_tasks WHERE target_floors LIKE ?"
        params: list[Any] = [f'%\"{floor}\"%']
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"
        return self.execute_query(query, tuple(params))

    def get_interfloor_tasks_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get tasks filtered by status."""
        return self.execute_query(
            "SELECT * FROM interfloor_tasks WHERE status = ? ORDER BY created_at DESC",
            (status,),
        )

    def log_time_entry(self, user_id: int, task_id: int, duration_seconds: int,
                      description: str, billable: bool = True) -> int:
        """
        Log time entry for ClockedOut integration.

        Parameters:
            user_id: User ID
            task_id: Task ID
            duration_seconds: Time spent in seconds
            description: Work description
            billable: Whether time is billable

        Returns:
            Time entry ID
        """
        query = """
        INSERT INTO time_entries (user_id, task_id, duration_seconds, description,
                                 billable, logged_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        timestamp = datetime.datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, task_id, duration_seconds, description,
                                 billable, timestamp))
            entry_id = cursor.lastrowid
            logger.info(f"Logged time entry: {duration_seconds}s for task {task_id}")
            return entry_id

    # --- THECONSTRUCT LAYER (Z0): Physics & Simulations ---

    def save_simulation(self, name: str, sim_type: str, parameters: Dict[str, Any],
                       results: Dict[str, Any], user_id: int) -> int:
        """
        Save simulation results to TheConstruct database.

        Parameters:
            name: Simulation name
            sim_type: Type (raphael, big_bang, orbital, quantum, rfs, emff)
            parameters: Input parameters as dict
            results: Output results as dict
            user_id: User who ran simulation

        Returns:
            Simulation ID
        """
        query = """
        INSERT INTO simulations (name, type, parameters, results, user_id, run_at, status)
        VALUES (?, ?, ?, ?, ?, ?, 'completed')
        """
        timestamp = datetime.datetime.now().isoformat()
        params_json = json.dumps(parameters)
        results_json = json.dumps(results)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (name, sim_type, params_json, results_json,
                                 user_id, timestamp))
            sim_id = cursor.lastrowid
            logger.info(f"Saved simulation: {name} (ID: {sim_id}, type: {sim_type})")
            return sim_id

    def get_recent_simulations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent simulations from TheConstruct.

        Parameters:
            limit: Maximum number of results

        Returns:
            List of recent simulations
        """
        query = "SELECT * FROM v_recent_simulations LIMIT ?"
        return self.execute_query(query, (limit,))

    # --- ORACLE LAYER (Z-1): Archives & IP Vault ---

    def register_ip_asset(self, title: str, asset_type: str, description: str,
                         owner_company_id: int, status: str = "draft") -> int:
        """
        Register IP asset in Oracle vault.

        Parameters:
            title: IP asset title
            asset_type: patent, trademark, innovation, trade_secret
            description: Asset description
            owner_company_id: Company ID (EMASSC, Römer, etc.)
            status: draft, filed, granted, published

        Returns:
            IP asset ID
        """
        query = """
        INSERT INTO ip_assets (title, type, description, owner_company_id,
                              status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        timestamp = datetime.datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (title, asset_type, description,
                                 owner_company_id, status, timestamp))
            asset_id = cursor.lastrowid
            logger.info(f"Registered IP asset: {title} (ID: {asset_id})")
            return asset_id

    def search_documents(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Full-text search across Oracle document archive.

        Parameters:
            search_term: Search query
            limit: Maximum results

        Returns:
            List of matching documents
        """
        query = """
        SELECT * FROM documents
        WHERE title LIKE ? OR content LIKE ?
        ORDER BY created_at DESC
        LIMIT ?
        """
        pattern = f"%{search_term}%"
        return self.execute_query(query, (pattern, pattern, limit))

    # --- SMITH LAYER (Z-2): Background Jobs & SOPs ---

    def create_background_job(self, job_type: str, parameters: Dict[str, Any],
                              scheduled_for: Optional[str] = None) -> int:
        """
        Schedule background job in Smith automation layer.

        Parameters:
            job_type: Type of job (backup, sync, analysis, etc.)
            parameters: Job parameters as dict
            scheduled_for: ISO timestamp for scheduled execution

        Returns:
            Job ID
        """
        query = """
        INSERT INTO jobs (job_type, params_json, status, scheduled_for, created_at)
        VALUES (?, ?, 'pending', ?, ?)
        """
        timestamp = datetime.datetime.now().isoformat()
        params_json = json.dumps(parameters)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (job_type, params_json, scheduled_for, timestamp))
            job_id = cursor.lastrowid
            logger.info(f"Created background job: {job_type} (ID: {job_id})")
            return job_id

    # ========================================================================
    # V1 JOB LEDGER + IMMUTABLE DATASPACE
    # ========================================================================

    def create_job_v1(
        self,
        *,
        job_type: str,
        tool_key: str,
        z_context: str,
        params: Optional[Dict[str, Any]] = None,
        task_id: Optional[int] = None,
        project_id: Optional[int] = None,
        status: str = "pending",
        tags: Optional[List[str]] = None,
        inputs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a job ledger entry and allocate an immutable dataspace run directory.

        Notes:
        - The run directory is created immediately.
        - The canonical `manifest.json` is written by `finalize_job_v1()` so it is not overwritten.
        """
        params_json = json.dumps(params or {}, ensure_ascii=False)
        metadata_json = json.dumps({"tags": tags or [], "inputs": inputs or []}, ensure_ascii=False)
        timestamp = datetime.datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(jobs)")
            cols = {row.get("name") if isinstance(row, dict) else row[1] for row in cursor.fetchall()}

            insert_cols: List[str] = ["job_type", "params_json", "status", "created_at"]
            values: List[Any] = [job_type, params_json, status, timestamp]

            if "tool_key" in cols:
                insert_cols.append("tool_key")
                values.append(tool_key)
            if "z_context" in cols:
                insert_cols.append("z_context")
                values.append(z_context)
            if "task_id" in cols:
                insert_cols.append("task_id")
                values.append(task_id)
            if "project_id" in cols:
                insert_cols.append("project_id")
                values.append(project_id)
            if "metadata_json" in cols:
                insert_cols.append("metadata_json")
                values.append(metadata_json)

            placeholders = ", ".join(["?"] * len(insert_cols))
            cursor.execute(
                f"INSERT INTO jobs ({', '.join(insert_cols)}) VALUES ({placeholders})",
                tuple(values),
            )
            job_id = int(cursor.lastrowid)

            run_dir = get_dataspace().job_run_dir(tool_key=tool_key, job_id=job_id)
            run_dir.mkdir(parents=True, exist_ok=True)

            if "run_dir" in cols:
                try:
                    cursor.execute("UPDATE jobs SET run_dir = ?, updated_at = ? WHERE id = ?", (str(run_dir), timestamp, job_id))
                except Exception:
                    pass

        return {
            "job_id": job_id,
            "job_type": job_type,
            "tool_key": tool_key,
            "z_context": z_context,
            "status": status,
            "run_dir": str(run_dir),
        }

    def register_artifact_v1(
        self,
        *,
        job_id: int,
        z_context: str,
        kind: str,
        path: str,
        sha256: str,
        size_bytes: int = 0,
        name: Optional[str] = None,
        media_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Register an immutable artifact produced by a job."""
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
        created_at = datetime.datetime.now().isoformat()
        query = """
        INSERT INTO artifacts (job_id, z_context, kind, name, path, sha256, size_bytes, media_type, created_at, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (job_id, z_context, kind, name, path, sha256, int(size_bytes or 0), media_type, created_at, metadata_json),
            )
            return int(cursor.lastrowid)

    def finalize_job_v1(
        self,
        *,
        job_id: int,
        status: str,
        z_context: Optional[str] = None,
        outputs: Optional[List[Dict[str, Any]]] = None,
        timings: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[str]:
        """
        Finalize a job:
        - write `manifest.json` exactly once (best-effort)
        - register manifest + outputs in artifacts ledger
        - update job status/result/error fields
        """
        outputs = outputs or []
        timings = timings or {}
        result = result or {}

        row: Optional[Dict[str, Any]] = None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()

        if not row:
            return None

        job_tool_key = (row.get("tool_key") or "unknown") if isinstance(row, dict) else "unknown"
        job_zctx = z_context or (row.get("z_context") if isinstance(row, dict) else None) or "unknown"
        run_dir = row.get("run_dir") if isinstance(row, dict) else None
        if not run_dir:
            run_dir = str(get_dataspace().job_run_dir(job_tool_key, job_id))
        run_path = Path(str(run_dir))
        run_path.mkdir(parents=True, exist_ok=True)

        try:
            meta = json.loads(row.get("metadata_json") or "{}") if isinstance(row, dict) else {}
        except Exception:
            meta = {}

        manifest = get_dataspace().build_manifest(
            job_id=job_id,
            tool_key=job_tool_key,
            z_context=job_zctx,
            status=status,
            inputs=meta.get("inputs") or [],
            outputs=outputs,
            timings=timings,
            extra={"result": result, "error": error},
            task_id=row.get("task_id") if isinstance(row, dict) else None,
            project_id=row.get("project_id") if isinstance(row, dict) else None,
        )

        manifest_path = run_path / "manifest.json"
        if not manifest_path.exists():
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            # If a manifest already exists, do not overwrite it (immutability preference).
            # Write a sidecar final manifest instead.
            (run_path / "manifest.final.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
            manifest_path = run_path / "manifest.final.json"

        manifest_sha = sha256_file(manifest_path)
        manifest_size = manifest_path.stat().st_size if manifest_path.exists() else 0

        now = datetime.datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE jobs SET status = ?, completed_at = ?, updated_at = ?, result_json = ?, error = ?, manifest_path = ? WHERE id = ?",
                (status, now, now, json.dumps(result, ensure_ascii=False), error, str(manifest_path), job_id),
            )

        try:
            self.register_artifact_v1(
                job_id=job_id,
                z_context=job_zctx,
                kind="manifest",
                name=manifest_path.name,
                path=str(manifest_path),
                sha256=manifest_sha,
                size_bytes=manifest_size,
                media_type="application/json",
            )
        except Exception:
            pass

        return str(manifest_path)

    # --- MEROVINGIAN LAYER (Z-3): Diagnostics & Telemetry ---

    def log_system_event(self, level: str, source: str, message: str,
                        details: Optional[Dict[str, Any]] = None) -> int:
        """
        Log system event to Merovingian telemetry database.

        Parameters:
            level: DEBUG, INFO, WARNING, ERROR, CRITICAL
            source: Component/floor that generated log
            message: Log message
            details: Additional context as dict

        Returns:
            Log ID
        """
        query = """
        INSERT INTO system_logs (level, source, message, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """
        timestamp = datetime.datetime.now().isoformat()
        details_json = json.dumps(details) if details else None

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (level, source, message, details_json, timestamp))
            log_id = cursor.lastrowid
            return log_id

    def get_system_health(self) -> Dict[str, Any]:
        """
        Get current system health metrics from Merovingian.

        Returns:
            System health summary
        """
        query = "SELECT * FROM v_system_health_summary"
        results = self.execute_query(query)
        return results[0] if results else {}

    def record_telemetry(self, component: str, metric_name: str, value: float,
                        unit: str = "") -> int:
        """
        Record telemetry data point.

        Parameters:
            component: Component name (Neo, Morpheus, etc.)
            metric_name: Metric identifier (cpu_usage, memory_mb, etc.)
            value: Numeric value
            unit: Unit of measurement

        Returns:
            Telemetry ID
        """
        query = """
        INSERT INTO telemetry_data (component, metric_name, value, unit, recorded_at)
        VALUES (?, ?, ?, ?, ?)
        """
        timestamp = datetime.datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (component, metric_name, value, unit, timestamp))
            telemetry_id = cursor.lastrowid
            return telemetry_id

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get schema information for a table.

        Parameters:
            table_name: Name of table

        Returns:
            List of column definitions
        """
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)

    def ensure_schema(self) -> None:
        """
        Ensure a minimal, launch-safe schema exists.

        This method is designed to prevent runtime crashes in UI code paths that
        query core tables (users/companies/projects/system logs/templates/etc.).
        """

        def table_exists(cursor, name: str) -> bool:
            cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
            return cursor.fetchone() is not None

        def current_columns(cursor, table: str) -> set[str]:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = set()
            for row in cursor.fetchall():
                try:
                    if isinstance(row, dict):
                        cols.add(row.get("name"))
                    else:
                        cols.add(row[1])  # pragma table_info: row[1] = name
                except Exception:
                    continue
            return {c for c in cols if c}

        def add_column(cursor, table: str, col_def: str) -> None:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Core identities
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    fullname TEXT,
                    email TEXT,
                    role TEXT DEFAULT 'user',
                    clearance INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    industry TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Canonical Z-context registry (required for job/task/artifact tagging)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS z_contexts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    type TEXT,
                    status TEXT DEFAULT 'active',
                    owner_id INTEGER,
                    company_id INTEGER,
                    floor TEXT,
                    path TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (owner_id) REFERENCES users(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Logs & telemetry
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    source TEXT,
                    floor TEXT,
                    component TEXT,
                    message TEXT NOT NULL,
                    details TEXT,
                    user_id TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Knowledge/files
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    name TEXT NOT NULL,
                    extension TEXT,
                    size_bytes INTEGER,
                    project_id INTEGER,
                    hash_sha256 TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    analyzed_at TEXT,
                    metadata_json TEXT
                )
            """)

            # Launch-safe migrations for historical schemas (no destructive changes).
            if table_exists(cursor, "files"):
                cols = current_columns(cursor, "files")

                # Common historical variants
                # - `filename` instead of `name`
                # - missing `project_id`
                # - missing `metadata_json`
                required_additions: list[tuple[str, str]] = [
                    ("name", "name TEXT"),
                    ("project_id", "project_id INTEGER"),
                    # Oracle ingestion + routing (schema may predate V1.0 floor enablement)
                    ("vault_id", "vault_id TEXT"),
                    ("ingestion_queue_position", "ingestion_queue_position INTEGER"),
                    ("extraction_status", "extraction_status TEXT DEFAULT 'pending'"),
                    ("routed_floors", "routed_floors TEXT"),
                    ("extension", "extension TEXT"),
                    ("size_bytes", "size_bytes INTEGER"),
                    ("hash_sha256", "hash_sha256 TEXT"),
                    ("status", "status TEXT"),
                    ("analyzed_at", "analyzed_at TEXT"),
                    ("deleted_at", "deleted_at TEXT"),
                    ("metadata_json", "metadata_json TEXT"),
                ]

                for col_name, col_def in required_additions:
                    if col_name not in cols:
                        try:
                            add_column(cursor, "files", col_def)
                        except Exception:
                            pass

                # Backfill `name` if added or empty; prefer `filename` when present.
                try:
                    cols = current_columns(cursor, "files")
                    has_filename = "filename" in cols
                    cursor.execute("SELECT id, path" + (", filename" if has_filename else "") + " FROM files")
                    rows = cursor.fetchall() or []
                    for row in rows:
                        try:
                            rid = row.get("id") if isinstance(row, dict) else row[0]
                            rpath = row.get("path") if isinstance(row, dict) else row[1]
                            rfilename = None
                            if has_filename:
                                rfilename = row.get("filename") if isinstance(row, dict) else row[2]

                            derived = (rfilename or Path(str(rpath)).name or "").strip()
                            if not derived:
                                continue
                            cursor.execute("UPDATE files SET name = COALESCE(NULLIF(name,''), ?) WHERE id = ?", (derived, rid))
                        except Exception:
                            continue
                except Exception:
                    pass

            # Encyclopedia (Oracle) - structured knowledge entries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS encyclopedia_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT NOT NULL,
                    volume TEXT NOT NULL,
                    category_letter TEXT,
                    definition TEXT,
                    data_object TEXT,
                    references_json TEXT,
                    metadata_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(term, volume)
                )
            """)
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_encyclopedia_term ON encyclopedia_entries(term)""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_encyclopedia_volume ON encyclopedia_entries(volume)""")

            # Oracle ingestion queue (Smith can process these)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oracle_ingestion_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vault_id INTEGER NOT NULL,
                    task_type TEXT NOT NULL,
                    file_metadata_json TEXT,
                    priority INTEGER DEFAULT 3,
                    status TEXT DEFAULT 'queued',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    started_at TEXT,
                    completed_at TEXT,
                    routing_results_json TEXT,
                    encyclopedia_updates INTEGER DEFAULT 0,
                    error TEXT,
                    FOREIGN KEY (vault_id) REFERENCES files(id)
                )
            """)
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_oracle_ingestion_status ON oracle_ingestion_tasks(status)""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_oracle_ingestion_vault ON oracle_ingestion_tasks(vault_id)""")

            # Inter-floor task queue (Smith/Neo coordination)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interfloor_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    source_floor TEXT NOT NULL,
                    target_floors TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    priority INTEGER NOT NULL DEFAULT 3,
                    status TEXT NOT NULL DEFAULT 'pending',
                    requires_neo_signoff INTEGER NOT NULL DEFAULT 0,
                    neo_approval TEXT,
                    floor_results TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_interfloor_status ON interfloor_tasks(status)""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_interfloor_source ON interfloor_tasks(source_floor)""")

            # Tasks/time tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    project_id INTEGER,
                    company_id INTEGER,
                    assigned_to INTEGER,
                    status TEXT DEFAULT 'pending',
                    priority TEXT DEFAULT 'normal',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    FOREIGN KEY (assigned_to) REFERENCES users(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS time_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    task_id INTEGER,
                    duration_seconds INTEGER DEFAULT 0,
                    description TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)

            # Simulations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    sim_type TEXT,
                    params_json TEXT,
                    results_json TEXT,
                    status TEXT DEFAULT 'pending',
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Construct calculators/tools registry. This table is queried by legacy
            # Morpheus SQLAlchemy models and the diagnostic launcher.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calculator_modules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    filepath TEXT NOT NULL,
                    floor TEXT NOT NULL DEFAULT 'Z0_TheConstruct',
                    category TEXT NOT NULL DEFAULT 'general',
                    subcategory TEXT,
                    description TEXT,
                    version TEXT DEFAULT '1.0.0',
                    input_schema TEXT,
                    output_schema TEXT,
                    dependencies TEXT,
                    dataset_requirements TEXT,
                    status TEXT DEFAULT 'active',
                    last_modified TEXT,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_calculator_modules_floor ON calculator_modules(floor)""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_calculator_modules_status ON calculator_modules(status)""")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scientific_datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    filepath TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'other',
                    format TEXT NOT NULL DEFAULT 'unknown',
                    size_bytes INTEGER NOT NULL DEFAULT 0,
                    mission TEXT,
                    observation_date TEXT,
                    description TEXT,
                    metadata TEXT,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_scientific_datasets_category ON scientific_datasets(category)""")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calculator_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    calculator_id INTEGER NOT NULL,
                    dataset_id INTEGER,
                    execution_time_ms REAL,
                    input_params TEXT,
                    output_size_bytes INTEGER,
                    success INTEGER,
                    error_message TEXT,
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (calculator_id) REFERENCES calculator_modules(id),
                    FOREIGN KEY (dataset_id) REFERENCES scientific_datasets(id)
                )
            """)
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_calculator_usage_calculator ON calculator_usage(calculator_id)""")

            # IP Vault
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ip_assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    asset_type TEXT,
                    description TEXT,
                    owner_company_id INTEGER,
                    owner TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT
                )
            """)

            # Background jobs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_type TEXT NOT NULL,
                    params_json TEXT,
                    status TEXT DEFAULT 'pending',
                    scheduled_for TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT,
                    result_json TEXT,
                    error TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # V1 ledger extensions (additive, backward-compatible)
            if table_exists(cursor, "jobs"):
                cols = current_columns(cursor, "jobs")
                for col_def in (
                    "tool_key TEXT",
                    "z_context TEXT",
                    "task_id INTEGER",
                    "project_id INTEGER",
                    "run_dir TEXT",
                    "manifest_path TEXT",
                    "progress_json TEXT",
                ):
                    name = col_def.split()[0]
                    if name not in cols:
                        try:
                            add_column(cursor, "jobs", col_def)
                        except Exception:
                            pass

            # Immutable artifact ledger (job outputs + manifests)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    z_context TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    name TEXT,
                    path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    size_bytes INTEGER DEFAULT 0,
                    media_type TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
            """)

            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_job ON artifacts(job_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_zctx ON artifacts(z_context)")
            except Exception:
                pass

            # Seed canonical Z-context taxonomy if empty (idempotent)
            try:
                cursor.execute("SELECT COUNT(*) AS c FROM z_contexts")
                row = cursor.fetchone()
                count = int(row.get("c") if isinstance(row, dict) else row[0])
                if count == 0:
                    seed = [
                        ("trinity", "Trinity", "Interface patterns, UX standards, layout language"),
                        ("neo", "Neo", "Code, automation, APIs, scripts"),
                        ("architect", "Architect", "Tasks, PMO, schedules, roadmap"),
                        ("oracle", "Oracle", "Research, references, bibliographies, summaries"),
                        ("construct", "TheConstruct", "Models, sims, calculators, datasets"),
                        ("smith", "Smith", "SOPs, build procedures, QA checklists"),
                        ("merovingian", "Merovingian", "Rules, policies, access, compliance logic"),
                    ]
                    cursor.executemany(
                        "INSERT INTO z_contexts (key, name, description) VALUES (?, ?, ?)",
                        seed,
                    )
            except Exception:
                pass

            # AI interactions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    prompt TEXT,
                    response TEXT,
                    model TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Templates (used by template_system.BaseTemplate.save_to_db)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    category TEXT,
                    subcategory TEXT,
                    version TEXT,
                    author TEXT,
                    settings_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # Minimal view for system health. If telemetry is absent, values will be NULL.
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_system_health_summary AS
                SELECT
                    (SELECT value FROM telemetry_data WHERE metric_name='cpu_percent' ORDER BY recorded_at DESC LIMIT 1) AS cpu_percent,
                    (SELECT value FROM telemetry_data WHERE metric_name='memory_percent' ORDER BY recorded_at DESC LIMIT 1) AS memory_percent,
                    (SELECT value FROM telemetry_data WHERE metric_name='disk_percent' ORDER BY recorded_at DESC LIMIT 1) AS disk_percent,
                    (SELECT recorded_at FROM telemetry_data ORDER BY recorded_at DESC LIMIT 1) AS recorded_at
            """)

            # Migrate known tables from older schemas (best-effort)
            if table_exists(cursor, "users"):
                cols = current_columns(cursor, "users")
                for col_def in ("fullname TEXT", "clearance INTEGER DEFAULT 1", "updated_at TEXT"):
                    name = col_def.split()[0]
                    if name not in cols:
                        add_column(cursor, "users", col_def)
                        cols.add(name)

            if table_exists(cursor, "companies"):
                cols = current_columns(cursor, "companies")
                for col_def in ("industry TEXT", "updated_at TEXT"):
                    name = col_def.split()[0]
                    if name not in cols:
                        add_column(cursor, "companies", col_def)
                        cols.add(name)

            if table_exists(cursor, "ip_assets"):
                cols = current_columns(cursor, "ip_assets")
                for col_def in ("owner_company_id INTEGER", "updated_at TEXT", "metadata_json TEXT"):
                    name = col_def.split()[0]
                    if name not in cols:
                        add_column(cursor, "ip_assets", col_def)
                        cols.add(name)

            if table_exists(cursor, "jobs"):
                cols = current_columns(cursor, "jobs")
                for col_def in ("metadata_json TEXT", "result_json TEXT", "error TEXT", "updated_at TEXT"):
                    name = col_def.split()[0]
                    if name not in cols:
                        add_column(cursor, "jobs", col_def)
                        cols.add(name)

            # Chat / conversation archive (GPT export + future sources)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER,
                    source TEXT NOT NULL,
                    conversation_uid TEXT NOT NULL,
                    title TEXT,
                    create_time_ts REAL,
                    update_time_ts REAL,
                    message_count INTEGER DEFAULT 0,
                    metadata_json TEXT,
                    imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, conversation_uid)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_conversations_company ON chat_conversations(company_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_conversations_source ON chat_conversations(source)")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    message_uid TEXT NOT NULL,
                    parent_uid TEXT,
                    role TEXT,
                    author_name TEXT,
                    create_time_ts REAL,
                    content_text TEXT,
                    content_json TEXT,
                    metadata_json TEXT,
                    imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(conversation_id, message_uid)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_conv ON chat_messages(conversation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_role ON chat_messages(role)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_time ON chat_messages(create_time_ts)")

            # Doc marker extraction (MD/TXT -> tasks)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doc_task_markers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    line_no INTEGER NOT NULL,
                    marker TEXT NOT NULL,
                    content TEXT,
                    hash_sha256 TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(file_path, line_no, marker)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_task_markers_hash ON doc_task_markers(hash_sha256)")

            # Seed baseline companies if missing (non-destructive; only inserts when absent).
            try:
                cursor.execute("SELECT name FROM companies")
                rows = cursor.fetchall() or []
                existing: set[str] = set()
                for r in rows:
                    try:
                        name_val = r.get("name") if isinstance(r, dict) else r[0]
                        if name_val:
                            existing.add(str(name_val).strip().lower())
                    except Exception:
                        continue

                # Treat "Romer" and "Römer" as the same company for seeding purposes.
                romer_variants = {"romer industries", "römer industries"}
                if existing.intersection(romer_variants):
                    existing.update(romer_variants)

                for name, industry in (
                    ("Römer Industries", "aerospace / research"),
                    ("EMASSC", "research / systems"),
                ):
                    if name.strip().lower() not in existing:
                        cursor.execute(
                            "INSERT INTO companies (name, industry, created_at, updated_at) VALUES (?, ?, ?, ?)",
                            (name, industry, datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat()),
                        )
                        existing.add(name.strip().lower())
            except Exception:
                pass

            if table_exists(cursor, "projects"):
                cols = current_columns(cursor, "projects")
                for col_def in (
                    "description TEXT",
                    "type TEXT",
                    "status TEXT DEFAULT 'active'",
                    "owner_id INTEGER",
                    "company_id INTEGER",
                    "floor TEXT",
                    "path TEXT",
                    "metadata TEXT",
                    "created_at TEXT",
                    "updated_at TEXT",
                ):
                    name = col_def.split()[0]
                    if name not in cols:
                        add_column(cursor, "projects", col_def)
                        cols.add(name)

            if table_exists(cursor, "tasks"):
                cols = current_columns(cursor, "tasks")
                for col_def in ("company_id INTEGER",):
                    name = col_def.split()[0]
                    if name not in cols:
                        try:
                            add_column(cursor, "tasks", col_def)
                            cols.add(name)
                        except Exception:
                            pass

            if table_exists(cursor, "system_logs"):
                cols = current_columns(cursor, "system_logs")
                for col_def in ("source TEXT", "floor TEXT", "component TEXT", "details TEXT", "user_id TEXT"):
                    name = col_def.split()[0]
                    if name not in cols:
                        add_column(cursor, "system_logs", col_def)
                        cols.add(name)

            # Smith jobs: extend minimal schema with metadata + results for task queue compatibility
            if table_exists(cursor, "jobs"):
                cols = current_columns(cursor, "jobs")
                for col_def in (
                    "metadata_json TEXT",
                    "result_json TEXT",
                    "error TEXT",
                    "updated_at TEXT",
                ):
                    name = col_def.split()[0]
                    if name not in cols:
                        add_column(cursor, "jobs", col_def)
                        cols.add(name)

            # Files: extend older schemas to match current code expectations
            if table_exists(cursor, "files"):
                cols = current_columns(cursor, "files")
                for col_def in (
                    # Some older DBs used filename/filepath; keep new columns as canonical.
                    "name TEXT",
                    "path TEXT",
                    "extension TEXT",
                    "size_bytes INTEGER",
                    "hash_sha256 TEXT",
                    "status TEXT",
                    "created_at TEXT",
                    "analyzed_at TEXT",
                    "metadata_json TEXT",
                    "project_id INTEGER",
                ):
                    col_name = col_def.split()[0]
                    if col_name not in cols:
                        add_column(cursor, "files", col_def)
                        cols.add(col_name)

                # Best-effort backfill from common legacy column names so UI/search has data.
                try:
                    if "filename" in cols and "name" in cols:
                        cursor.execute(
                            "UPDATE files SET name = filename WHERE (name IS NULL OR name = '') AND filename IS NOT NULL"
                        )
                    if "filepath" in cols and "path" in cols:
                        cursor.execute(
                            "UPDATE files SET path = filepath WHERE (path IS NULL OR path = '') AND filepath IS NOT NULL"
                        )
                    if "original_path" in cols and "path" in cols:
                        cursor.execute(
                            "UPDATE files SET path = original_path WHERE (path IS NULL OR path = '') AND original_path IS NOT NULL"
                        )
                    if "checksum" in cols and "hash_sha256" in cols:
                        cursor.execute(
                            "UPDATE files SET hash_sha256 = checksum WHERE (hash_sha256 IS NULL OR hash_sha256 = '') AND checksum IS NOT NULL"
                        )
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_hash_sha256 ON files(hash_sha256)")
                except Exception:
                    pass

    def get_all_tables(self) -> List[str]:
        """
        Get list of all tables in database.

        Returns:
            List of table names
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        results = self.execute_query(query)
        return [row['name'] for row in results]

    def vacuum(self):
        """
        Optimize database (reclaim space, rebuild indexes).
        """
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        logger.info("Database optimized (VACUUM completed)")


# Singleton instance for global access
_db_service = None

def get_db() -> DatabaseService:
    """
    Get global database service instance (singleton pattern).

    Returns:
        DatabaseService instance
    """
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


if __name__ == "__main__":
    # Test database service
    print("Database Service - Test Suite")
    print("=" * 50)

    db = get_db()

    # Test 1: Database connection
    print("\nTest 1: Database connection")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            print(f"  SQLite version: {version}")
            print(f"  Database path: {db.db_path}")
    except Exception as e:
        print(f"  Error: {e}")

    # Test 2: List tables
    print("\nTest 2: Database tables")
    try:
        tables = db.get_all_tables()
        print(f"  Total tables: {len(tables)}")
        print(f"  Sample tables: {tables[:5]}")
    except Exception as e:
        print(f"  Error: {e}")

    # Test 3: System health
    print("\nTest 3: System health check")
    try:
        health = db.get_system_health()
        if health:
            print(f"  System status: Available")
        else:
            print(f"  System status: No health data (expected for new DB)")
    except Exception as e:
        print(f"  Error: {e}")

    print("\n" + "=" * 50)
    print("Database service ready for inter-floor communication!")
