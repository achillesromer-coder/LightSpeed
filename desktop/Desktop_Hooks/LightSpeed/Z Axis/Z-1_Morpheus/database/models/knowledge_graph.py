"""
Knowledge Graph Models
Nodes and Edges for representing system architecture as a knowledge graph
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from ..base import BaseModel


class KnowledgeGraphNode(BaseModel):
    """Model for knowledge graph nodes"""
    __tablename__ = 'knowledge_graph_nodes'
    __table_args__ = (
        UniqueConstraint('node_type', 'node_name', name='_node_type_name_uc'),
    )

    node_type = Column(String(50), nullable=False)  # floor, module, function, dataset, concept, api, hook
    node_name = Column(String(500), nullable=False)
    node_id_ref = Column(Integer)  # Reference to ID in related table
    description = Column(Text)
    properties = Column(Text)  # JSON properties

    # Relationships
    outgoing_edges = relationship('KnowledgeGraphEdge', foreign_keys='KnowledgeGraphEdge.source_node_id', back_populates='source_node')
    incoming_edges = relationship('KnowledgeGraphEdge', foreign_keys='KnowledgeGraphEdge.target_node_id', back_populates='target_node')

    @validates('node_type')
    def validate_node_type(self, key, node_type):
        """Validate node type"""
        valid_types = ['floor', 'module', 'function', 'dataset', 'concept', 'api', 'hook']
        if node_type not in valid_types:
            raise ValueError(f"Invalid node type: {node_type}. Must be one of {valid_types}")
        return node_type

    def __repr__(self):
        return f"<KnowledgeGraphNode({self.node_type}: '{self.node_name}')>"

    def get_connections(self, session, relationship_type=None, direction='both'):
        """Get all connected nodes

        Args:
            session: Database session
            relationship_type: Filter by relationship type (optional)
            direction: 'outgoing', 'incoming', or 'both'
        """
        if direction == 'outgoing':
            edges = self.outgoing_edges
        elif direction == 'incoming':
            edges = self.incoming_edges
        else:
            edges = self.outgoing_edges + self.incoming_edges

        if relationship_type:
            edges = [e for e in edges if e.relationship_type == relationship_type]

        return edges

    @classmethod
    def get_nodes_by_type(cls, session, node_type):
        """Get all nodes of a specific type"""
        return session.query(cls).filter_by(node_type=node_type).all()

    @classmethod
    def find_node(cls, session, node_type, node_name):
        """Find a specific node by type and name"""
        return session.query(cls).filter_by(node_type=node_type, node_name=node_name).first()


class KnowledgeGraphEdge(BaseModel):
    """Model for knowledge graph edges (relationships)"""
    __tablename__ = 'knowledge_graph_edges'

    source_node_id = Column(Integer, ForeignKey('knowledge_graph_nodes.id', ondelete='CASCADE'), nullable=False)
    target_node_id = Column(Integer, ForeignKey('knowledge_graph_nodes.id', ondelete='CASCADE'), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # uses, calls, produces, requires, extends, implements, contains, documents
    strength = Column(Float, default=1.0)  # 0.0 to 1.0
    extra_metadata = Column('metadata', Text)  # JSON metadata - mapped to 'metadata' column in DB

    # Relationships
    source_node = relationship('KnowledgeGraphNode', foreign_keys=[source_node_id], back_populates='outgoing_edges')
    target_node = relationship('KnowledgeGraphNode', foreign_keys=[target_node_id], back_populates='incoming_edges')

    @validates('relationship_type')
    def validate_relationship(self, key, rel_type):
        """Validate relationship type"""
        valid_types = ['uses', 'calls', 'produces', 'requires', 'extends', 'implements', 'contains', 'documents']
        if rel_type not in valid_types:
            raise ValueError(f"Invalid relationship type: {rel_type}. Must be one of {valid_types}")
        return rel_type

    @validates('strength')
    def validate_strength(self, key, strength):
        """Validate strength is between 0.0 and 1.0"""
        if not 0.0 <= strength <= 1.0:
            raise ValueError(f"Strength must be between 0.0 and 1.0, got {strength}")
        return strength

    def __repr__(self):
        return f"<KnowledgeGraphEdge({self.source_node_id} --[{self.relationship_type}]-> {self.target_node_id})>"

    @classmethod
    def get_relationships(cls, session, relationship_type):
        """Get all edges of a specific relationship type"""
        return session.query(cls).filter_by(relationship_type=relationship_type).all()

    @classmethod
    def find_path(cls, session, source_id, target_id, max_depth=5):
        """Find shortest path between two nodes (simplified BFS)"""
        # This is a simplified implementation
        # For production, consider using a graph database or specialized pathfinding
        visited = set()
        queue = [(source_id, [source_id])]

        while queue:
            (node_id, path) = queue.pop(0)

            if node_id == target_id:
                return path

            if len(path) > max_depth:
                continue

            if node_id in visited:
                continue

            visited.add(node_id)

            # Get all outgoing edges
            edges = session.query(cls).filter_by(source_node_id=node_id).all()

            for edge in edges:
                if edge.target_node_id not in visited:
                    queue.append((edge.target_node_id, path + [edge.target_node_id]))

        return None  # No path found
