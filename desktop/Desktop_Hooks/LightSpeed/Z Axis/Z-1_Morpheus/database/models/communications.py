"""
Inter-Floor Communications and Data Flow Models
Tracks communication patterns between Z Floors
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, func
from ..base import BaseModel


class InterFloorComm(BaseModel):
    """Model for inter-floor communication patterns"""
    __tablename__ = 'inter_floor_comms'

    source_floor = Column(String(50), nullable=False)
    target_floor = Column(String(50), nullable=False)
    communication_type = Column(String(50))  # data_flow, function_call, event, query, response
    source_function = Column(String(200))
    target_function = Column(String(200))
    data_schema = Column(Text)  # JSON schema
    frequency = Column(String(20))  # high, medium, low, on_demand, rare
    latency_ms = Column(Float)
    description = Column(Text)
    established_at = Column(DateTime, default=func.now())
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<InterFloorComm('{self.source_floor}' → '{self.target_floor}', {self.communication_type})>"

    def record_usage(self, session, latency_ms=None):
        """Record that this communication occurred"""
        self.last_used = func.now()
        self.usage_count += 1
        if latency_ms:
            # Update latency with exponential moving average
            if self.latency_ms:
                self.latency_ms = 0.7 * self.latency_ms + 0.3 * latency_ms
            else:
                self.latency_ms = latency_ms
        session.commit()

    @classmethod
    def get_floor_communications(cls, session, floor_name, direction='both'):
        """Get all communications for a floor

        Args:
            session: Database session
            floor_name: Name of the floor
            direction: 'incoming', 'outgoing', or 'both'
        """
        if direction == 'outgoing':
            return session.query(cls).filter_by(source_floor=floor_name).all()
        elif direction == 'incoming':
            return session.query(cls).filter_by(target_floor=floor_name).all()
        else:  # both
            return session.query(cls).filter(
                (cls.source_floor == floor_name) | (cls.target_floor == floor_name)
            ).all()


class DataFlowPattern(BaseModel):
    """Model for documented data flow patterns across floors"""
    __tablename__ = 'data_flow_patterns'

    pattern_name = Column(String(200), unique=True, nullable=False)
    start_floor = Column(String(50), nullable=False)
    end_floor = Column(String(50), nullable=False)
    intermediate_floors = Column(Text)  # JSON array of floors in path
    data_type = Column(String(100))
    transformation_steps = Column(Text)  # JSON array of transformation descriptions
    purpose = Column(Text)
    example_data = Column(Text)  # JSON example
    diagram_path = Column(String(1000))

    def __repr__(self):
        return f"<DataFlowPattern('{self.pattern_name}': {self.start_floor} → {self.end_floor})>"

    @property
    def path_length(self):
        """Get the number of floors in this data flow path"""
        import json
        intermediate = json.loads(self.intermediate_floors) if self.intermediate_floors else []
        return len(intermediate) + 2  # +2 for start and end floors

    @classmethod
    def get_patterns_for_floor(cls, session, floor_name):
        """Get all data flow patterns involving a specific floor"""
        return session.query(cls).filter(
            (cls.start_floor == floor_name) |
            (cls.end_floor == floor_name) |
            (cls.intermediate_floors.like(f'%{floor_name}%'))
        ).all()
