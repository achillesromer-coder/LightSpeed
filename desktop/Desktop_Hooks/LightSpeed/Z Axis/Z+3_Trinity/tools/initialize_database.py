"""
Database Initialization Script
LightSpeed Type I Civilization Platform

Creates (or migrates) the canonical V1 database schema.

V1 policy:
- Trinity (Z+3) owns explicit schema creation/migrations.
- Runtime validates schema read-only (no silent schema mutation).

Author: LightSpeed Team
Version: 1.0.0
Date: January 18, 2026
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def initialize_database(db_path: Optional[Union[str, Path]] = None, *, quiet: bool = True) -> Dict[str, Any]:
    """
    Create/migrate the canonical schema (idempotent).

    Args:
        db_path: DB file path (defaults to floor-native Merovingian DB)
        quiet: Suppress prints (UI callers should set True)

    Returns:
        Dict report with keys: ok, db_path, created_tables, added_columns, errors
    """
    if db_path is None:
        db_path = Path(__file__).resolve().parents[3] / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db"

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    report: Dict[str, Any] = {
        "ok": True,
        "db_path": str(db_path),
        "created_tables": [],
        "added_columns": {},
        "errors": [],
    }

    def _log(msg: str) -> None:
        if not quiet:
            print(msg)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    def _table_exists(name: str) -> bool:
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cursor.fetchone() is not None

    def _cols(table: str) -> set:
        cursor.execute(f"PRAGMA table_info({table})")
        return {row[1] for row in cursor.fetchall() if row and len(row) > 1}

    def _create_table(name: str, sql: str) -> None:
        existed = _table_exists(name)
        cursor.execute(sql)
        if not existed and _table_exists(name):
            report["created_tables"].append(name)

    def _add_column(table: str, col_def: str) -> None:
        col_name = col_def.split()[0].strip()
        if col_name in _cols(table):
            return
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
        report["added_columns"].setdefault(table, []).append(col_name)

    try:
        _log(f"[DB] Initializing schema: {db_path}")

        _create_table(
            "users",
            """
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
            """,
        )
        _create_table(
            "companies",
            """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                industry TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        _create_table(
            "z_contexts",
            """
            CREATE TABLE IF NOT EXISTS z_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        _create_table(
            "projects",
            """
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
            """,
        )
        _create_table(
            "tasks",
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                project_id INTEGER,
                assigned_to INTEGER,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'normal',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                metadata_json TEXT,
                company_id INTEGER,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (assigned_to) REFERENCES users(id)
            )
            """,
        )
        _create_table(
            "files",
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                name TEXT NOT NULL,
                extension TEXT,
                size_bytes INTEGER,
                hash_sha256 TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                analyzed_at TEXT,
                metadata_json TEXT,
                project_id INTEGER,
                vault_id TEXT,
                ingestion_queue_position INTEGER,
                extraction_status TEXT DEFAULT 'pending',
                routed_floors TEXT,
                deleted_at TEXT
            )
            """,
        )
        _create_table(
            "oracle_ingestion_tasks",
            """
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
            """,
        )
        _create_table(
            "encyclopedia_entries",
            """
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
            """,
        )
        _create_table(
            "system_logs",
            """
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
            """,
        )
        _create_table(
            "telemetry_data",
            """
            CREATE TABLE IF NOT EXISTS telemetry_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        _create_table(
            "jobs",
            """
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
            """,
        )

        # V1 jobs extensions (additive, backward-compatible)
        for col_def in (
            "tool_key TEXT",
            "z_context TEXT",
            "task_id INTEGER",
            "project_id INTEGER",
            "run_dir TEXT",
            "manifest_path TEXT",
            "progress_json TEXT",
        ):
            try:
                _add_column("jobs", col_def)
            except Exception as e:
                report["errors"].append(f"jobs add_column {col_def}: {e}")

        _create_table(
            "artifacts",
            """
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
            """,
        )
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_job ON artifacts(job_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_zctx ON artifacts(z_context)")
        except Exception:
            pass

        # Seed canonical Z-context taxonomy if empty (idempotent)
        try:
            cursor.execute("SELECT COUNT(*) FROM z_contexts")
            count = int((cursor.fetchone() or [0])[0])
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
        _create_table(
            "templates",
            """
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
            """,
        )
        _create_table(
            "ai_interactions",
            """
            CREATE TABLE IF NOT EXISTS ai_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                prompt TEXT,
                response TEXT,
                model TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        _create_table(
            "chat_conversations",
            """
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
            """,
        )
        _create_table(
            "chat_messages",
            """
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
            """,
        )
        _create_table(
            "doc_task_markers",
            """
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
            """,
        )
        _create_table(
            "interfloor_tasks",
            """
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
            """,
        )
        _create_table(
            "simulations",
            """
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
            """,
        )
        _create_table(
            "calculator_modules",
            """
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
            """,
        )
        _create_table(
            "scientific_datasets",
            """
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
            """,
        )
        _create_table(
            "calculator_usage",
            """
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
            """,
        )
        _create_table(
            "ip_assets",
            """
            CREATE TABLE IF NOT EXISTS ip_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                asset_type TEXT,
                description TEXT,
                owner TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                metadata_json TEXT,
                owner_company_id INTEGER,
                updated_at TEXT
            )
            """,
        )
        _create_table(
            "user_preferences",
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                theme TEXT DEFAULT 'dark',
                font_size INTEGER DEFAULT 10,
                font_family TEXT DEFAULT 'Segoe UI',
                accent_color TEXT DEFAULT '#007acc',
                widget_layout TEXT,
                preferences_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        _create_table(
            "time_entries",
            """
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
            """,
        )

        # Safe additive migrations (add missing columns when possible)
        for col_def in ("industry TEXT", "updated_at TEXT"):
            _add_column("companies", col_def)
        for col_def in ("fullname TEXT", "email TEXT", "role TEXT", "clearance INTEGER", "updated_at TEXT"):
            _add_column("users", col_def)
        for col_def in ("company_id INTEGER", "owner_id INTEGER", "type TEXT", "path TEXT", "metadata TEXT", "updated_at TEXT"):
            _add_column("projects", col_def)
        for col_def in ("company_id INTEGER", "metadata_json TEXT", "updated_at TEXT"):
            _add_column("tasks", col_def)
        # Note: Older DBs may have used `filename` instead of `name`. We add `name`
        # additively and best-effort backfill below.
        for col_def in ("name TEXT", "project_id INTEGER", "vault_id TEXT", "ingestion_queue_position INTEGER", "extraction_status TEXT", "routed_floors TEXT", "deleted_at TEXT"):
            _add_column("files", col_def)
        for col_def in ("owner_company_id INTEGER", "updated_at TEXT"):
            _add_column("ip_assets", col_def)

        # Best-effort backfill for newly added canonical columns (non-destructive).
        try:
            files_cols = _cols("files")
            if "name" in files_cols:
                legacy_name_col = None
                for cand in ("filename", "file_name"):
                    if cand in files_cols:
                        legacy_name_col = cand
                        break

                if legacy_name_col:
                    cursor.execute(
                        f"UPDATE files SET name = COALESCE(name, {legacy_name_col}) "
                        "WHERE name IS NULL OR name = ''"
                    )

                cursor.execute("SELECT id, path FROM files WHERE name IS NULL OR name = ''")
                rows = cursor.fetchall() or []
                for row in rows:
                    try:
                        fid, fpath = row[0], row[1]
                        if not fpath:
                            continue
                        name = Path(str(fpath)).name
                        if not name:
                            continue
                        cursor.execute("UPDATE files SET name = ? WHERE id = ?", (name, fid))
                    except Exception:
                        continue
        except Exception:
            pass

        # Indexes (best-effort)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_hash_sha256 ON files(hash_sha256)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_company_id ON projects(company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_task_markers_file ON doc_task_markers(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calculator_modules_floor ON calculator_modules(floor)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calculator_modules_status ON calculator_modules(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scientific_datasets_category ON scientific_datasets(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calculator_usage_calculator ON calculator_usage(calculator_id)")

        conn.commit()
        _log("[DB] Schema OK")
    except Exception as e:
        conn.rollback()
        report["ok"] = False
        report["errors"].append(str(e))
    finally:
        conn.close()

    return report


def reset_database(db_path: Optional[Union[str, Path]] = None, *, force: bool = False) -> Dict[str, Any]:
    """
    Reset database by deleting and recreating all tables.

    WARNING: This will delete all data!

    Args:
        db_path: Path to database file
        force: Required to perform destructive reset (prevents accidental use)
    """
    if db_path is None:
        db_path = Path(__file__).resolve().parents[3] / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db"

    db_path = Path(db_path)
    if not force:
        return {
            "ok": False,
            "db_path": str(db_path),
            "created_tables": [],
            "added_columns": {},
            "errors": ["Refusing to reset database without force=True"],
        }

    if db_path.exists():
        backup_path = db_path.with_suffix('.db.backup')
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
        except Exception:
            pass

        try:
            db_path.unlink()
        except Exception:
            pass

    return initialize_database(db_path, quiet=True)


if __name__ == "__main__":
    import sys

    print("="*60)
    print("  LIGHTSPEED DATABASE INITIALIZATION (V1 CANONICAL)")
    print("="*60)
    print()

    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        # Non-interactive: requires explicit --force
        force = ("--force" in sys.argv)
        res = reset_database(force=force)
    else:
        res = initialize_database(quiet=False)

    print()
    print("="*60)
    print("  Result: " + ("OK" if res.get("ok") else "FAILED"))
    print("="*60)
