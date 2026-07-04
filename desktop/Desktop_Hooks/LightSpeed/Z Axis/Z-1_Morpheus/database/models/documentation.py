"""
System Documentation Model
Tracks all documentation files and enables auto-generated docs
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from ..base import BaseModel


class SystemDocumentation(BaseModel):
    """Model for system documentation tracking"""
    __tablename__ = 'system_documentation'

    doc_type = Column(String(50), nullable=False)  # floor, calculator, api, guide, architecture, tutorial, reference
    title = Column(String(500), nullable=False)
    filepath = Column(String(1000), unique=True, nullable=False)
    related_floor = Column(String(50))
    related_module = Column(String(200))
    content_summary = Column(Text)
    tags = Column(Text)  # JSON array of tags
    auto_generated = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=func.now())
    update_frequency = Column(String(20))  # on_change, hourly, daily, weekly, manual

    def __repr__(self):
        auto = " [AUTO]" if self.auto_generated else ""
        return f"<SystemDocumentation('{self.doc_type}': {self.title}{auto})>"

    def mark_updated(self, session):
        """Mark this documentation as recently updated"""
        self.last_updated = func.now()
        session.commit()

    @classmethod
    def get_floor_docs(cls, session, floor_name):
        """Get all documentation for a specific floor"""
        return session.query(cls).filter_by(related_floor=floor_name).all()

    @classmethod
    def get_auto_generated_docs(cls, session):
        """Get all auto-generated documentation"""
        return session.query(cls).filter_by(auto_generated=True).all()

    @classmethod
    def get_docs_by_type(cls, session, doc_type):
        """Get all documentation of a specific type"""
        return session.query(cls).filter_by(doc_type=doc_type).all()

    @classmethod
    def search_docs(cls, session, search_term):
        """Search documentation by title, summary, or tags"""
        search_pattern = f"%{search_term}%"
        return session.query(cls).filter(
            (cls.title.like(search_pattern)) |
            (cls.content_summary.like(search_pattern)) |
            (cls.tags.like(search_pattern))
        ).all()

    def needs_update(self):
        """Check if this document needs updating based on its update frequency"""
        if self.update_frequency == 'manual' or not self.auto_generated:
            return False

        from datetime import datetime, timedelta
        now = datetime.now()

        if isinstance(self.last_updated, str):
            last_update = datetime.fromisoformat(self.last_updated)
        else:
            last_update = self.last_updated

        if self.update_frequency == 'hourly':
            return (now - last_update) > timedelta(hours=1)
        elif self.update_frequency == 'daily':
            return (now - last_update) > timedelta(days=1)
        elif self.update_frequency == 'weekly':
            return (now - last_update) > timedelta(weeks=1)
        elif self.update_frequency == 'on_change':
            # For on_change, external trigger is needed
            return False

        return False
