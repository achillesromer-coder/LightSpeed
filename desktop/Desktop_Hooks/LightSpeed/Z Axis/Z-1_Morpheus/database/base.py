"""
Database Base Configuration
SQLAlchemy setup and session management
"""

from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import Column, Integer, DateTime, func
import json

# Database path - floor-native location (Merovingian data)
try:
    from core.config.paths import MEROVINGIAN_DATA
    _db_root = Path(MEROVINGIAN_DATA) / "legacy_databases"
except Exception:
    # Fallback to the sibling Merovingian floor. parents[2] is the Z Axis root.
    _db_root = Path(__file__).resolve().parents[2] / "Z-4_Merovingian" / "data" / "legacy_databases"

DB_PATH = _db_root / "lightspeed_system.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Create engine
engine = create_engine(
    f'sqlite:///{DB_PATH.as_posix()}',
    echo=False,  # Set to True for SQL debugging
    connect_args={'check_same_thread': False}
)

# Session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Declarative base
Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields and methods"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result

    def to_json(self):
        """Convert model to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data):
        """Create model instance from dictionary"""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


def get_session():
    """Get a new database session"""
    return Session()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(engine)


def close_session():
    """Close current session"""
    Session.remove()


# Import datetime for to_dict method
from datetime import datetime
