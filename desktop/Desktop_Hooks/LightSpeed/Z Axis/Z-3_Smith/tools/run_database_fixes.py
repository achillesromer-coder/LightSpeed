"""
LightSpeed V0.9.5 - Database Schema Fix Script
Fixes critical production blocker database errors
Date: January 2, 2026
"""

import sqlite3
import os
from pathlib import Path

def run_database_fixes():
    """Run database schema fixes safely"""

    # Get database path
    script_dir = Path(__file__).parent
    db_path = script_dir.parent.parent.parent / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db"

    if not db_path.exists():
        print(f"[ERROR] Database not found at: {db_path}")
        return False

    print("=" * 70)
    print("LIGHTSPEED V1.0.0 - DATABASE SCHEMA FIXES")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print(f"Size: {os.path.getsize(db_path) / 1024:.2f} KB\n")

    # Backup database first
    backup_path = db_path.parent / f"{db_path.stem}_backup_{Path(__file__).stem}.db"
    print(f"[1/4] Creating backup: {backup_path.name}")

    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print("[OK] Backup created\n")
    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")
        return False

    # Connect to database
    print("[2/4] Connecting to database...")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    print("[OK] Connected\n")

    # Get current schema
    print("[3/4] Checking current schema...")
    cursor.execute("PRAGMA table_info(files)")
    files_columns = {row[1] for row in cursor.fetchall()}
    print(f"[INFO] files table has {len(files_columns)} columns")
    print(f"       Columns: {', '.join(sorted(files_columns))}")

    missing_columns = []
    required_columns = ['project_id', 'vault_id', 'ingestion_queue_position', 'extraction_status', 'routed_floors']
    for col in required_columns:
        if col not in files_columns:
            missing_columns.append(col)

    if missing_columns:
        print(f"[WARN] Missing columns: {', '.join(missing_columns)}\n")
    else:
        print("[OK] All required columns present\n")

    # Apply fixes
    print("[4/4] Applying schema fixes...")
    fixes_applied = 0
    errors = []

    try:
        # Fix 1: Add project_id if missing
        if 'project_id' not in files_columns:
            print("  [FIX] Adding project_id column to files table...")
            cursor.execute("ALTER TABLE files ADD COLUMN project_id INTEGER")
            fixes_applied += 1
            print("  [OK] Added project_id\n")

        # Fix 2: Add vault_id if missing
        if 'vault_id' not in files_columns:
            print("  [FIX] Adding vault_id column to files table...")
            cursor.execute("ALTER TABLE files ADD COLUMN vault_id TEXT")
            fixes_applied += 1
            print("  [OK] Added vault_id\n")

        # Fix 3: Add ingestion_queue_position if missing
        if 'ingestion_queue_position' not in files_columns:
            print("  [FIX] Adding ingestion_queue_position column...")
            cursor.execute("ALTER TABLE files ADD COLUMN ingestion_queue_position INTEGER")
            fixes_applied += 1
            print("  [OK] Added ingestion_queue_position\n")

        # Fix 4: Add extraction_status if missing
        if 'extraction_status' not in files_columns:
            print("  [FIX] Adding extraction_status column...")
            cursor.execute("ALTER TABLE files ADD COLUMN extraction_status TEXT DEFAULT 'pending'")
            fixes_applied += 1
            print("  [OK] Added extraction_status\n")

        # Fix 5: Add routed_floors if missing
        if 'routed_floors' not in files_columns:
            print("  [FIX] Adding routed_floors column...")
            cursor.execute("ALTER TABLE files ADD COLUMN routed_floors TEXT")
            fixes_applied += 1
            print("  [OK] Added routed_floors\n")

        # Fix 6: Create indexes
        print("  [FIX] Creating indexes...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_vault_id ON files(vault_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")
            print("  [OK] Indexes created\n")
        except Exception as e:
            print(f"  [WARN] Index creation: {e}\n")

        # Fix 7: Ensure encyclopedia_entries table exists
        print("  [FIX] Ensuring encyclopedia_entries table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS encyclopedia_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL,
                volume TEXT NOT NULL,
                category_letter TEXT,
                definition TEXT,
                data_object TEXT,
                references_list TEXT,
                metadata_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(term, volume)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_encyclopedia_term ON encyclopedia_entries(term)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_encyclopedia_volume ON encyclopedia_entries(volume)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_encyclopedia_category ON encyclopedia_entries(category_letter)")
        print("  [OK] Encyclopedia table ready\n")

        # Fix 8: Ensure oracle_ingestion_tasks table exists
        print("  [FIX] Ensuring oracle_ingestion_tasks table...")
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
                error_message TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oracle_tasks_status ON oracle_ingestion_tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oracle_tasks_vault_id ON oracle_ingestion_tasks(vault_id)")
        print("  [OK] Oracle ingestion table ready\n")

        # Fix 9: Ensure interfloor_tasks table exists
        print("  [FIX] Ensuring interfloor_tasks table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interfloor_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                source_floor TEXT NOT NULL,
                target_floors TEXT NOT NULL,
                parameters TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 3,
                status TEXT NOT NULL,
                requires_neo_signoff INTEGER NOT NULL DEFAULT 0,
                neo_approval TEXT,
                floor_results TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interfloor_status ON interfloor_tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interfloor_source ON interfloor_tasks(source_floor)")
        print("  [OK] Inter-floor tasks table ready\n")

        # Commit all changes
        conn.commit()
        print(f"[SUCCESS] Applied {fixes_applied} schema fixes\n")

    except Exception as e:
        conn.rollback()
        errors.append(str(e))
        print(f"[ERROR] Schema fix failed: {e}\n")
        return False

    finally:
        conn.close()

    # Verify fixes
    print("=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check files table
    cursor.execute("PRAGMA table_info(files)")
    files_columns_after = {row[1] for row in cursor.fetchall()}
    print(f"\nfiles table now has {len(files_columns_after)} columns:")
    for col in sorted(files_columns_after):
        status = "[NEW]" if col not in files_columns else "[OK] "
        print(f"  {status} {col}")

    # Check other tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\nTotal tables in database: {len(tables)}")

    key_tables = ['files', 'encyclopedia_entries', 'oracle_ingestion_tasks', 'interfloor_tasks', 'projects']
    print("\nKey tables status:")
    for table in key_tables:
        status = "[OK]" if table in tables else "[MISSING]"
        print(f"  {status} {table}")

    conn.close()

    print("\n" + "=" * 70)
    print("DATABASE SCHEMA FIXES COMPLETE")
    print("=" * 70)
    print(f"\nBackup saved to: {backup_path.name}")
    print(f"Fixes applied: {fixes_applied}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nErrors encountered:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("\n[SUCCESS] All database schema fixes applied successfully!")
    print("          Platform should now be able to start without schema errors.\n")
    return True

if __name__ == "__main__":
    success = run_database_fixes()
    exit(0 if success else 1)
