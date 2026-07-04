"""
Calculator Modules and Usage Models
Tracks physics calculator modules and their execution analytics
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, func
from sqlalchemy.orm import relationship
from ..base import BaseModel


class CalculatorModule(BaseModel):
    """Model for physics calculator modules"""
    __tablename__ = 'calculator_modules'

    name = Column(String(200), unique=True, nullable=False)
    filepath = Column(String(1000), nullable=False)
    floor = Column(String(50), nullable=False)  # Z0_TheConstruct
    category = Column(String(50), nullable=False)  # cosmology, quantum, atomic, nuclear, orbital, chemistry
    subcategory = Column(String(100))
    description = Column(Text)
    version = Column(String(20), default='1.0.0')
    input_schema = Column(Text)  # JSON string
    output_schema = Column(Text)  # JSON string
    dependencies = Column(Text)  # JSON array of module names
    dataset_requirements = Column(Text)  # JSON array of dataset requirements
    status = Column(String(20), default='active')  # active, deprecated, testing, inactive
    last_modified = Column(DateTime)
    usage_count = Column(Integer, default=0)

    # Relationships
    usage_records = relationship('CalculatorUsage', back_populates='calculator')

    def __repr__(self):
        return f"<CalculatorModule('{self.name}', '{self.category}', usage={self.usage_count})>"

    def record_usage(self, session):
        """Record that this calculator was used"""
        self.usage_count += 1
        self.last_modified = func.now()
        session.commit()


class CalculatorUsage(BaseModel):
    """Model for calculator execution analytics"""
    __tablename__ = 'calculator_usage'

    calculator_id = Column(Integer, ForeignKey('calculator_modules.id'), nullable=False)
    dataset_id = Column(Integer, ForeignKey('scientific_datasets.id'))
    execution_time_ms = Column(Float)
    input_params = Column(Text)  # JSON string
    output_size_bytes = Column(Integer)
    success = Column(Boolean)
    error_message = Column(Text)
    executed_at = Column(DateTime, default=func.now())

    # Relationships
    calculator = relationship('CalculatorModule', back_populates='usage_records')
    dataset = relationship('ScientificDataset', back_populates='calculator_usage')

    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"<CalculatorUsage(calc_id={self.calculator_id}, {status}, {self.execution_time_ms}ms)>"
