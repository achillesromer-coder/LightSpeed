"""
System Configuration and Metadata Models
System-wide settings and metadata
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func, CheckConstraint
from ..base import BaseModel


class SystemConfiguration(BaseModel):
    """Model for system-wide configuration"""
    __tablename__ = 'system_configuration'

    config_key = Column(String(200), unique=True, nullable=False)
    config_value = Column(Text, nullable=False)
    config_type = Column(String(20))  # string, integer, float, boolean, json
    description = Column(Text)
    last_modified = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<SystemConfiguration('{self.config_key}' = '{self.config_value}')>"

    def get_typed_value(self):
        """Get the configuration value in its proper type"""
        if self.config_type == 'integer':
            return int(self.config_value)
        elif self.config_type == 'float':
            return float(self.config_value)
        elif self.config_type == 'boolean':
            return self.config_value.lower() in ('true', '1', 'yes')
        elif self.config_type == 'json':
            import json
            return json.loads(self.config_value)
        else:  # string or unknown
            return self.config_value

    def set_value(self, value, session):
        """Set configuration value with type conversion"""
        if self.config_type == 'json':
            import json
            self.config_value = json.dumps(value)
        else:
            self.config_value = str(value)

        self.last_modified = func.now()
        session.commit()

    @classmethod
    def get_config(cls, session, key, default=None):
        """Get a configuration value by key"""
        config = session.query(cls).filter_by(config_key=key).first()
        if config:
            return config.get_typed_value()
        return default

    @classmethod
    def set_config(cls, session, key, value, config_type='string', description=None):
        """Set a configuration value"""
        config = session.query(cls).filter_by(config_key=key).first()

        if config:
            config.set_value(value, session)
        else:
            # Create new configuration
            import json
            value_str = json.dumps(value) if config_type == 'json' else str(value)

            config = cls(
                config_key=key,
                config_value=value_str,
                config_type=config_type,
                description=description
            )
            session.add(config)
            session.commit()

        return config


class SystemMetadata(BaseModel):
    """Model for system metadata (singleton)"""
    __tablename__ = 'system_metadata'
    __table_args__ = (
        CheckConstraint('id = 1', name='singleton_check'),
    )

    # Override id to enforce singleton pattern
    id = Column(Integer, primary_key=True, default=1)

    schema_version = Column(String(20), default='1.0.0')
    system_name = Column(String(100), default='LightSpeed')
    initialized_at = Column(DateTime, default=func.now())
    last_migration = Column(DateTime)
    total_floors = Column(Integer, default=9)
    total_modules = Column(Integer, default=0)
    total_datasets = Column(Integer, default=0)

    def __repr__(self):
        return f"<SystemMetadata('{self.system_name}' v{self.schema_version})>"

    @classmethod
    def get_metadata(cls, session):
        """Get the singleton system metadata"""
        metadata = session.query(cls).filter_by(id=1).first()
        if not metadata:
            # Create default metadata
            metadata = cls(id=1)
            session.add(metadata)
            session.commit()
        return metadata

    def update_counts(self, session):
        """Update counts of modules and datasets"""
        from .calculators import CalculatorModule
        from .datasets import ScientificDataset

        self.total_modules = session.query(CalculatorModule).count()
        self.total_datasets = session.query(ScientificDataset).count()
        session.commit()

    def record_migration(self, session):
        """Record that a migration was performed"""
        self.last_migration = func.now()
        session.commit()

    def get_info(self):
        """Get formatted system information"""
        return {
            'system_name': self.system_name,
            'schema_version': self.schema_version,
            'initialized_at': self.initialized_at.isoformat() if self.initialized_at else None,
            'last_migration': self.last_migration.isoformat() if self.last_migration else None,
            'total_floors': self.total_floors,
            'total_modules': self.total_modules,
            'total_datasets': self.total_datasets,
        }
