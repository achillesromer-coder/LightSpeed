"""
LightSpeed Database Initialization Script
Creates the lightspeed_system.db database with complete schema
"""

import sqlite3
import os
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
SCHEMA_FILE = SCRIPT_DIR / "schema.sql"
#
# V1 canonical storage:
# - DB artifacts should live floor-native (Merovingian data), not in a legacy root `Data/` folder.
# - This script is a legacy initializer for `lightspeed_system.db` and is kept for compatibility.
#
try:
    from core.config.paths import MEROVINGIAN_DATA  # type: ignore

    _db_root = Path(MEROVINGIAN_DATA) / "legacy_databases"
except Exception:
    # Safe fallback if `core` is not importable (e.g., isolated execution).
    _db_root = (
        Path(__file__).resolve().parents[3]
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "legacy_databases"
    )

DB_PATH = _db_root / "lightspeed_system.db"

def create_database():
    """Create and initialize the LightSpeed system database"""

    # Ensure databases directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Read schema
    with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Create database
    print(f"Creating database at: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Execute schema
    try:
        cursor.executescript(schema_sql)
        conn.commit()
        print("[OK] Database schema created successfully")

        # Verify tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()

        print(f"\n[TABLES] Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")

        # Verify views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
        views = cursor.fetchall()

        print(f"\n[VIEWS]  Created {len(views)} views:")
        for view in views:
            print(f"  - {view[0]}")

        # Check system metadata
        cursor.execute("SELECT * FROM system_metadata WHERE id = 1")
        metadata = cursor.fetchone()
        if metadata:
            print(f"\n[CONFIG] System Metadata:")
            print(f"  Schema Version: {metadata[1]}")
            print(f"  System Name: {metadata[2]}")
            print(f"  Initialized: {metadata[3]}")
            print(f"  Total Floors: {metadata[5]}")

        print(f"\n[OK] Database created successfully at:")
        print(f"   {DB_PATH}")
        print(f"   Size: {DB_PATH.stat().st_size / 1024:.2f} KB")

    except sqlite3.Error as e:
        print(f"[ERROR] Error creating database: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    create_database()
