"""
Z Floor Functions and Directory Structure Models
Tracks all functions across the 9 Z Floors and their directory organization

NOTE (2026-02-03): This is legacy Morpheus DB scaffolding that still describes a 9-floor model (Z+4..Z-4).
Canonical runtime stack is now 8 floors (Z+3..Z-4) and `Z+4_FirstRun` is legacy-only (setup/login consolidated
into Trinity). Keep `Z+4_FirstRun` here for historical DB compatibility.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import validates
from ..base import BaseModel


class ZFloorFunction(BaseModel):
    """Model for tracking functions across Z Floors"""
    __tablename__ = 'z_floor_functions'

    floor = Column(String(50), nullable=False)  # Z-4_Merovingian through Z+4_FirstRun
    floor_number = Column(Integer, nullable=False)  # -4 to +4
    function_name = Column(String(200), nullable=False)
    function_type = Column(String(50))  # core, utility, api, hook, handler, processor
    purpose = Column(Text)
    input_types = Column(Text)  # JSON array
    output_types = Column(Text)  # JSON array
    dependencies = Column(Text)  # JSON array
    calls_to = Column(Text)  # JSON array of floors this calls
    called_by = Column(Text)  # JSON array of floors that call this
    file_location = Column(String(1000))
    line_number = Column(Integer)
    status = Column(String(20), default='active')  # active, deprecated, testing
    documentation_path = Column(String(1000))

    @validates('floor')
    def validate_floor(self, key, floor):
        """Validate floor name"""
        valid_floors = [
            'Z-4_Merovingian', 'Z-3_Smith', 'Z-2_Oracle', 'Z-1_Morpheus',
            'Z0_TheConstruct', 'Z+1_Architect', 'Z+2_Neo', 'Z+3_Trinity', 'Z+4_FirstRun'
        ]
        if floor not in valid_floors:
            raise ValueError(f"Invalid floor: {floor}. Must be one of {valid_floors}")
        return floor

    @validates('floor_number')
    def validate_floor_number(self, key, number):
        """Validate floor number is between -4 and +4"""
        if not -4 <= number <= 4:
            raise ValueError(f"Floor number must be between -4 and +4, got {number}")
        return number

    def __repr__(self):
        return f"<ZFloorFunction('{self.floor}.{self.function_name}', {self.function_type})>"


class FloorDirectoryStructure(BaseModel):
    """Model for tracking A-Z directory organization per floor"""
    __tablename__ = 'floor_directory_structure'

    floor = Column(String(50), nullable=False)
    directory_path = Column(String(1000), nullable=False)
    directory_name = Column(String(200), nullable=False)
    umbrella_category = Column(String(1))  # A-Z single letter
    purpose = Column(Text)
    file_types = Column(Text)  # JSON array of expected file types
    parent_directory = Column(String(1000))

    @validates('umbrella_category')
    def validate_category(self, key, category):
        """Validate umbrella category is A-Z"""
        if category and (len(category) != 1 or not 'A' <= category <= 'Z'):
            raise ValueError(f"Umbrella category must be a single letter A-Z, got '{category}'")
        return category

    def __repr__(self):
        return f"<FloorDirectoryStructure('{self.floor}/{self.directory_name}', [{self.umbrella_category}])>"

    @classmethod
    def get_floor_structure(cls, session, floor_name):
        """Get all directories for a specific floor"""
        return session.query(cls).filter_by(floor=floor_name).order_by(cls.umbrella_category).all()

    @classmethod
    def get_by_category(cls, session, floor_name, category):
        """Get directories for a specific floor and category letter"""
        return session.query(cls).filter_by(
            floor=floor_name,
            umbrella_category=category
        ).all()
