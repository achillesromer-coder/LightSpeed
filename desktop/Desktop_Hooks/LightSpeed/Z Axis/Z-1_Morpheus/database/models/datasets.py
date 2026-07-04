"""
Scientific Datasets Model
Tracks all scientific data files (Planck CMB, LIGO, simulations, etc.)
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.orm import relationship
from ..base import BaseModel


class ScientificDataset(BaseModel):
    """Model for scientific datasets"""
    __tablename__ = 'scientific_datasets'

    filename = Column(String(500), unique=True, nullable=False)
    filepath = Column(String(1000), nullable=False)
    category = Column(String(50), nullable=False)  # planck_cmb, ligo_gw, simulation, database, other
    format = Column(String(20), nullable=False)  # FITS, HDF5, GWF, GIF, MP4, DB, JSON, CSV
    size_bytes = Column(Integer, nullable=False)
    mission = Column(String(100))  # Planck, LIGO, Custom
    observation_date = Column(String(50))
    description = Column(Text)
    extra_metadata = Column('metadata', Text)  # JSON string - mapped to 'metadata' column in DB
    last_accessed = Column(DateTime)
    access_count = Column(Integer, default=0)

    # Relationships
    calculator_usage = relationship('CalculatorUsage', back_populates='dataset')

    def __repr__(self):
        return f"<ScientificDataset('{self.filename}', '{self.category}', {self.size_bytes/1e9:.2f}GB)>"

    @property
    def size_gb(self):
        """Get size in gigabytes"""
        return self.size_bytes / (1024 ** 3)

    @property
    def size_mb(self):
        """Get size in megabytes"""
        return self.size_bytes / (1024 ** 2)

    def record_access(self, session):
        """Record that this dataset was accessed"""
        self.last_accessed = func.now()
        self.access_count += 1
        session.commit()
