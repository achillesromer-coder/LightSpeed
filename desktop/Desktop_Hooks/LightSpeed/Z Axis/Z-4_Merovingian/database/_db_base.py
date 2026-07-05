"""
Database Base - Unified database interface for all database operations

Provides consistent database access across SQLite, MySQL, and PostgreSQL.
Eliminates code duplication in D1, D3, D4 components.

Following Clean Code principles:
- Single Responsibility: Database connection management
- Open/Closed: Extensible for new database types
- Dependency Inversion: Components depend on interface, not implementation
"""

import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import os
from abc import ABC, abstractmethod


# ============================================================================
# Enums and Data Classes
# ============================================================================

class DatabaseType(Enum):
    """Supported database types"""
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_type: DatabaseType
    database: str
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None

    @staticmethod
    def for_sqlite(database_path: str) -> 'DatabaseConfig':
        """Create config for SQLite database"""
        return DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            database=database_path
        )

    @staticmethod
    def for_mysql(host: str, database: str, user: str, password: str, port: int = 3306) -> 'DatabaseConfig':
        """Create config for MySQL database"""
        return DatabaseConfig(
            db_type=DatabaseType.MYSQL,
            database=database,
            host=host,
            port=port,
            user=user,
            password=password
        )

    @staticmethod
    def for_postgresql(host: str, database: str, user: str, password: str, port: int = 5432) -> 'DatabaseConfig':
        """Create config for PostgreSQL database"""
        return DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            database=database,
            host=host,
            port=port,
            user=user,
            password=password
        )


@dataclass
class QueryResult:
    """Query result container with scientific research support"""
    columns: List[str]
    rows: List[Tuple]
    row_count: int

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert rows to list of dictionaries"""
        return [dict(zip(self.columns, row)) for row in self.rows]

    def to_csv_string(self) -> str:
        """Export results as CSV string for scientific datasets"""
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(self.columns)
        writer.writerows(self.rows)
        return output.getvalue()

    def to_numpy_array(self):
        """Convert results to numpy array (requires numpy)"""
        try:
            import numpy as np
            return np.array(self.rows)
        except ImportError:
            raise ImportError("numpy required for scientific data analysis")

    def to_pandas_dataframe(self):
        """Convert results to pandas DataFrame (requires pandas)"""
        try:
            import pandas as pd
            return pd.DataFrame(self.rows, columns=self.columns)
        except ImportError:
            raise ImportError("pandas required for scientific data analysis")

    def get_column_stats(self, column_name: str) -> Dict[str, Any]:
        """Calculate statistics for a numeric column"""
        if column_name not in self.columns:
            raise ValueError(f"Column '{column_name}' not found")

        col_idx = self.columns.index(column_name)
        values = [row[col_idx] for row in self.rows if row[col_idx] is not None]

        if not values:
            return {'count': 0}

        try:
            numeric_values = [float(v) for v in values]
            return {
                'count': len(numeric_values),
                'min': min(numeric_values),
                'max': max(numeric_values),
                'mean': sum(numeric_values) / len(numeric_values),
                'sum': sum(numeric_values)
            }
        except (ValueError, TypeError):
            return {
                'count': len(values),
                'type': 'non-numeric'
            }


# ============================================================================
# Abstract Database Interface
# ============================================================================

class IDatabaseConnection(ABC):
    """Abstract database interface (Dependency Inversion Principle)"""

    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection"""
        pass

    @abstractmethod
    def disconnect(self):
        """Close database connection"""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
        """Execute SELECT query and return results"""
        pass

    @abstractmethod
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows"""
        pass

    @abstractmethod
    def get_tables(self) -> List[str]:
        """Get list of all tables"""
        pass

    @abstractmethod
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema (columns, types, constraints)"""
        pass

    @abstractmethod
    def begin_transaction(self):
        """Start transaction"""
        pass

    @abstractmethod
    def commit(self):
        """Commit transaction"""
        pass

    @abstractmethod
    def rollback(self):
        """Rollback transaction"""
        pass


# ============================================================================
# SQLite Implementation
# ============================================================================

class SQLiteConnection(IDatabaseConnection):
    """SQLite database connection"""

    def __init__(self, config: DatabaseConfig):
        if config.db_type != DatabaseType.SQLITE:
            raise ValueError("Config must be for SQLite")

        self.database_path = config.database
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    def connect(self) -> bool:
        """Establish SQLite connection"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.database_path) or '.', exist_ok=True)

            self.connection = sqlite3.connect(self.database_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            print(f"SQLite connection error: {e}")
            return False

    def disconnect(self):
        """Close SQLite connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
        """Execute SELECT query"""
        if not self.cursor:
            raise RuntimeError("Not connected to database")

        params = params or ()
        self.cursor.execute(query, params)

        rows = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []

        # Convert sqlite3.Row to tuples
        row_tuples = [tuple(row) for row in rows]

        return QueryResult(
            columns=columns,
            rows=row_tuples,
            row_count=len(row_tuples)
        )

    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE"""
        if not self.cursor:
            raise RuntimeError("Not connected to database")

        params = params or ()
        self.cursor.execute(query, params)
        self.connection.commit()

        return self.cursor.rowcount

    def get_tables(self) -> List[str]:
        """Get all table names"""
        result = self.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [row[0] for row in result.rows]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema"""
        result = self.execute_query(f"PRAGMA table_info({table_name})")

        schema = []
        for row in result.rows:
            schema.append({
                'column_id': row[0],
                'name': row[1],
                'type': row[2],
                'not_null': bool(row[3]),
                'default_value': row[4],
                'is_primary_key': bool(row[5])
            })

        return schema

    def begin_transaction(self):
        """Start transaction"""
        if self.connection:
            self.connection.execute("BEGIN TRANSACTION")

    def commit(self):
        """Commit transaction"""
        if self.connection:
            self.connection.commit()

    def rollback(self):
        """Rollback transaction"""
        if self.connection:
            self.connection.rollback()


# ============================================================================
# MySQL Implementation (Optional - requires mysql-connector-python)
# ============================================================================

class MySQLConnection(IDatabaseConnection):
    """MySQL database connection"""

    def __init__(self, config: DatabaseConfig):
        if config.db_type != DatabaseType.MYSQL:
            raise ValueError("Config must be for MySQL")

        self.config = config
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """Establish MySQL connection"""
        try:
            import mysql.connector

            self.connection = mysql.connector.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database
            )
            self.cursor = self.connection.cursor()
            return True
        except ImportError:
            print("mysql-connector-python not installed")
            return False
        except Exception as e:
            print(f"MySQL connection error: {e}")
            return False

    def disconnect(self):
        """Close MySQL connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
        """Execute SELECT query"""
        if not self.cursor:
            raise RuntimeError("Not connected to database")

        params = params or ()
        self.cursor.execute(query, params)

        rows = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []

        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows)
        )

    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE"""
        if not self.cursor:
            raise RuntimeError("Not connected to database")

        params = params or ()
        self.cursor.execute(query, params)
        self.connection.commit()

        return self.cursor.rowcount

    def get_tables(self) -> List[str]:
        """Get all table names"""
        result = self.execute_query("SHOW TABLES")
        return [row[0] for row in result.rows]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema"""
        result = self.execute_query(f"DESCRIBE {table_name}")

        schema = []
        for row in result.rows:
            schema.append({
                'name': row[0],
                'type': row[1],
                'null': row[2] == 'YES',
                'key': row[3],
                'default': row[4],
                'extra': row[5]
            })

        return schema

    def begin_transaction(self):
        """Start transaction"""
        if self.connection:
            self.connection.start_transaction()

    def commit(self):
        """Commit transaction"""
        if self.connection:
            self.connection.commit()

    def rollback(self):
        """Rollback transaction"""
        if self.connection:
            self.connection.rollback()


# ============================================================================
# PostgreSQL Implementation (Optional - requires psycopg2)
# ============================================================================

class PostgreSQLConnection(IDatabaseConnection):
    """PostgreSQL database connection"""

    def __init__(self, config: DatabaseConfig):
        if config.db_type != DatabaseType.POSTGRESQL:
            raise ValueError("Config must be for PostgreSQL")

        self.config = config
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """Establish PostgreSQL connection"""
        try:
            import psycopg2

            self.connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database
            )
            self.cursor = self.connection.cursor()
            return True
        except ImportError:
            print("psycopg2 not installed")
            return False
        except Exception as e:
            print(f"PostgreSQL connection error: {e}")
            return False

    def disconnect(self):
        """Close PostgreSQL connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
        """Execute SELECT query"""
        if not self.cursor:
            raise RuntimeError("Not connected to database")

        params = params or ()
        self.cursor.execute(query, params)

        rows = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []

        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows)
        )

    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE"""
        if not self.cursor:
            raise RuntimeError("Not connected to database")

        params = params or ()
        self.cursor.execute(query, params)
        self.connection.commit()

        return self.cursor.rowcount

    def get_tables(self) -> List[str]:
        """Get all table names"""
        result = self.execute_query(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        )
        return [row[0] for row in result.rows]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema"""
        result = self.execute_query(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)

        schema = []
        for row in result.rows:
            schema.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES',
                'default': row[3]
            })

        return schema

    def begin_transaction(self):
        """Start transaction"""
        pass  # PostgreSQL auto-starts transactions

    def commit(self):
        """Commit transaction"""
        if self.connection:
            self.connection.commit()

    def rollback(self):
        """Rollback transaction"""
        if self.connection:
            self.connection.rollback()


# ============================================================================
# Database Connection Factory
# ============================================================================

class DatabaseConnectionFactory:
    """Factory for creating database connections (Factory Pattern)"""

    @staticmethod
    def create(config: DatabaseConfig) -> IDatabaseConnection:
        """Create appropriate database connection based on config"""
        if config.db_type == DatabaseType.SQLITE:
            return SQLiteConnection(config)
        elif config.db_type == DatabaseType.MYSQL:
            return MySQLConnection(config)
        elif config.db_type == DatabaseType.POSTGRESQL:
            return PostgreSQLConnection(config)
        else:
            raise ValueError(f"Unsupported database type: {config.db_type}")


# ============================================================================
# Context Manager for Database Operations
# ============================================================================

class DatabaseSession:
    """Context manager for database operations with automatic cleanup"""

    def __init__(self, config: DatabaseConfig, auto_commit: bool = True):
        self.config = config
        self.auto_commit = auto_commit
        self.connection: Optional[IDatabaseConnection] = None

    def __enter__(self) -> IDatabaseConnection:
        """Connect to database"""
        self.connection = DatabaseConnectionFactory.create(self.config)
        if not self.connection.connect():
            raise RuntimeError("Failed to connect to database")
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Disconnect and cleanup"""
        if self.connection:
            if exc_type is None and self.auto_commit:
                self.connection.commit()
            elif exc_type is not None:
                self.connection.rollback()

            self.connection.disconnect()

        # Return False to propagate exceptions
        return False


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import tempfile
    import os

    # Create test database
    test_db = os.path.join(tempfile.gettempdir(), "test_lightspeed.db")
    config = DatabaseConfig.for_sqlite(test_db)

    # Test using context manager
    print("Testing DatabaseSession context manager...")
    with DatabaseSession(config) as db:
        # Create table
        db.execute_update("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                age INTEGER
            )
        """)

        # Insert data
        db.execute_update(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
            ("Alice", "alice@example.com", 30)
        )
        db.execute_update(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
            ("Bob", "bob@example.com", 25)
        )

        # Query data
        result = db.execute_query("SELECT * FROM users ORDER BY name")
        print(f"\nFound {result.row_count} users:")
        for row_dict in result.to_dict_list():
            print(f"  {row_dict}")

        # Get schema
        tables = db.get_tables()
        print(f"\nTables: {tables}")

        schema = db.get_table_schema('users')
        print(f"\nUsers table schema:")
        for col in schema:
            print(f"  {col}")

    print("\n✅ Database base class tests passed!")
    print(f"Test database: {test_db}")
