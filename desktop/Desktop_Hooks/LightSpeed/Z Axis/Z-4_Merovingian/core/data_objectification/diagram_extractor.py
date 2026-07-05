"""
Diagram Extractor - V1.0.0
Extracts diagrams from documents and converts to structured formats

Supports:
- Mermaid diagrams
- PlantUML diagrams
- Graphviz DOT
- ASCII art diagrams
- Embedded SVG
- Image-based diagrams (with OCR)

Outputs:
- SVG representations
- JSON graph structures
- Diagram metadata
- Node/edge lists

Author: LightSpeed Team
Date: December 27, 2025
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ==============================================================================
# Diagram Types
# ==============================================================================

class DiagramType(Enum):
    """Types of diagrams"""
    MERMAID = "mermaid"
    PLANTUML = "plantuml"
    GRAPHVIZ = "graphviz"
    ASCII_ART = "ascii_art"
    SVG = "svg"
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    CLASS_DIAGRAM = "class_diagram"
    ERD = "erd"
    UNKNOWN = "unknown"


# ==============================================================================
# Data Models
# ==============================================================================

@dataclass
class DiagramNode:
    """
    Represents a node in a diagram

    Attributes:
        node_id: Unique identifier
        label: Node label/text
        type: Node type (e.g., 'process', 'decision', 'entity')
        properties: Additional properties
    """
    node_id: str
    label: str
    type: str = "default"
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'node_id': self.node_id,
            'label': self.label,
            'type': self.type,
            'properties': self.properties
        }


@dataclass
class DiagramEdge:
    """
    Represents an edge/connection in a diagram

    Attributes:
        source: Source node ID
        target: Target node ID
        label: Edge label
        type: Edge type (e.g., 'arrow', 'line', 'dashed')
        properties: Additional properties
    """
    source: str
    target: str
    label: str = ""
    type: str = "arrow"
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'source': self.source,
            'target': self.target,
            'label': self.label,
            'type': self.type,
            'properties': self.properties
        }


@dataclass
class ExtractedDiagram:
    """
    Extracted diagram with structured representation

    Attributes:
        diagram_id: Unique identifier
        source_file: Source document path
        source_position: Position in document
        diagram_type: Type of diagram
        raw_content: Raw diagram source
        nodes: List of nodes
        edges: List of edges
        svg: SVG representation (if available)
        metadata: Additional metadata
    """
    diagram_id: str
    source_file: Path
    source_position: Optional[int] = None
    diagram_type: DiagramType = DiagramType.UNKNOWN
    raw_content: str = ""
    nodes: List[DiagramNode] = field(default_factory=list)
    edges: List[DiagramEdge] = field(default_factory=list)
    svg: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'diagram_id': self.diagram_id,
            'source_file': str(self.source_file),
            'source_position': self.source_position,
            'diagram_type': self.diagram_type.value,
            'raw_content': self.raw_content,
            'nodes': [n.to_dict() for n in self.nodes],
            'edges': [e.to_dict() for e in self.edges],
            'svg': self.svg,
            'metadata': self.metadata
        }


# ==============================================================================
# Diagram Extractor
# ==============================================================================

class DiagramExtractor:
    """
    Extracts diagrams from documents and converts to structured formats
    """

    def __init__(self):
        """Initialize diagram extractor"""
        pass

    def extract(
        self,
        content: str,
        file_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Extract diagrams from content

        Args:
            content: Document content
            file_path: Source file path
            options: Extraction options

        Returns:
            List of ExtractedDiagram objects wrapped as ExtractedObject
        """
        from .objectifier import ExtractedObject, ObjectType

        options = options or {}
        diagrams = []

        # Extract different diagram types
        diagrams.extend(self._extract_mermaid(content, file_path))
        diagrams.extend(self._extract_plantuml(content, file_path))
        diagrams.extend(self._extract_graphviz(content, file_path))
        diagrams.extend(self._extract_svg(content, file_path))

        # Convert to ExtractedObject format
        objects = []
        for diagram in diagrams:
            obj = ExtractedObject(
                object_id=diagram.diagram_id,
                object_type=ObjectType.DIAGRAM,
                source_file=diagram.source_file,
                source_position=diagram.source_position,
                content=diagram.raw_content,
                structured_data=diagram.to_dict(),
                metadata=diagram.metadata
            )
            objects.append(obj)

        return objects

    def _extract_mermaid(
        self,
        content: str,
        file_path: Path
    ) -> List[ExtractedDiagram]:
        """Extract Mermaid diagrams"""
        diagrams = []

        # Pattern for fenced Mermaid blocks
        pattern = re.compile(r'```mermaid\n(.*?)```', re.DOTALL)

        for i, match in enumerate(pattern.finditer(content)):
            mermaid_code = match.group(1)

            diagram = ExtractedDiagram(
                diagram_id=f"diagram_mermaid_{i}",
                source_file=file_path,
                source_position=match.start(),
                diagram_type=DiagramType.MERMAID,
                raw_content=mermaid_code,
                metadata={'format': 'mermaid'}
            )

            # Parse Mermaid syntax
            self._parse_mermaid(diagram)

            diagrams.append(diagram)

        return diagrams

    def _parse_mermaid(self, diagram: ExtractedDiagram):
        """Parse Mermaid diagram syntax"""
        lines = diagram.raw_content.strip().split('\n')

        if not lines:
            return

        # Determine diagram type from first line
        first_line = lines[0].strip().lower()
        if 'graph' in first_line or 'flowchart' in first_line:
            diagram.diagram_type = DiagramType.FLOWCHART
            self._parse_mermaid_flowchart(diagram, lines[1:])
        elif 'sequencediagram' in first_line.replace(' ', ''):
            diagram.diagram_type = DiagramType.SEQUENCE
            self._parse_mermaid_sequence(diagram, lines[1:])
        elif 'classdiagram' in first_line.replace(' ', ''):
            diagram.diagram_type = DiagramType.CLASS_DIAGRAM
            self._parse_mermaid_class(diagram, lines[1:])
        elif 'erdiagram' in first_line.replace(' ', ''):
            diagram.diagram_type = DiagramType.ERD
            self._parse_mermaid_erd(diagram, lines[1:])

    def _parse_mermaid_flowchart(self, diagram: ExtractedDiagram, lines: List[str]):
        """Parse Mermaid flowchart"""
        node_counter = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Node definitions: A[Label] or A(Label) or A{Label}
            node_pattern = re.compile(r'(\w+)([\[\(\{])(.*?)([\]\)\}])')
            for match in node_pattern.finditer(line):
                node_id = match.group(1)
                bracket = match.group(2)
                label = match.group(3)

                # Determine node type from brackets
                node_type = {
                    '[': 'process',
                    '(': 'rounded',
                    '{': 'decision'
                }.get(bracket, 'default')

                # Check if node already exists
                if not any(n.node_id == node_id for n in diagram.nodes):
                    diagram.nodes.append(DiagramNode(
                        node_id=node_id,
                        label=label,
                        type=node_type
                    ))

            # Edge definitions: A --> B or A --- B or A -.-> B
            edge_pattern = re.compile(r'(\w+)\s*(-->|---|-\.-?>)\s*(\w+)(?:\|([^\|]+)\|)?')
            for match in edge_pattern.finditer(line):
                source = match.group(1)
                arrow = match.group(2)
                target = match.group(3)
                label = match.group(4) or ""

                edge_type = {
                    '-->': 'arrow',
                    '---': 'line',
                    '-.->': 'dashed'
                }.get(arrow, 'arrow')

                diagram.edges.append(DiagramEdge(
                    source=source,
                    target=target,
                    label=label.strip(),
                    type=edge_type
                ))

    def _parse_mermaid_sequence(self, diagram: ExtractedDiagram, lines: List[str]):
        """Parse Mermaid sequence diagram"""
        participants = set()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Participant definitions
            participant_pattern = re.compile(r'participant\s+(\w+)(?:\s+as\s+(.+))?')
            match = participant_pattern.match(line)
            if match:
                participant_id = match.group(1)
                label = match.group(2) or participant_id
                participants.add(participant_id)

                diagram.nodes.append(DiagramNode(
                    node_id=participant_id,
                    label=label,
                    type='participant'
                ))
                continue

            # Message definitions: A->>B: Message
            message_pattern = re.compile(r'(\w+)\s*(->>|-->>|->>?)\s*(\w+)\s*:\s*(.+)')
            match = message_pattern.match(line)
            if match:
                source = match.group(1)
                arrow = match.group(2)
                target = match.group(3)
                message = match.group(4)

                # Add participants if not already defined
                for participant in [source, target]:
                    if participant not in participants:
                        participants.add(participant)
                        diagram.nodes.append(DiagramNode(
                            node_id=participant,
                            label=participant,
                            type='participant'
                        ))

                diagram.edges.append(DiagramEdge(
                    source=source,
                    target=target,
                    label=message,
                    type='message'
                ))

    def _parse_mermaid_class(self, diagram: ExtractedDiagram, lines: List[str]):
        """Parse Mermaid class diagram"""
        current_class = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Class definition: class ClassName
            class_pattern = re.compile(r'class\s+(\w+)')
            match = class_pattern.match(line)
            if match:
                current_class = match.group(1)
                diagram.nodes.append(DiagramNode(
                    node_id=current_class,
                    label=current_class,
                    type='class',
                    properties={'methods': [], 'attributes': []}
                ))
                continue

            # Relationship: ClassA <|-- ClassB
            relation_pattern = re.compile(r'(\w+)\s*(<\|--|<\.\.|o--|<--)\s*(\w+)')
            match = relation_pattern.match(line)
            if match:
                source = match.group(1)
                relation = match.group(2)
                target = match.group(3)

                relation_type = {
                    '<|--': 'inheritance',
                    '<..': 'implements',
                    'o--': 'aggregation',
                    '<--': 'association'
                }.get(relation, 'association')

                diagram.edges.append(DiagramEdge(
                    source=source,
                    target=target,
                    type=relation_type
                ))

    def _parse_mermaid_erd(self, diagram: ExtractedDiagram, lines: List[str]):
        """Parse Mermaid entity-relationship diagram"""
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Entity definition: ENTITY_NAME { ... }
            entity_pattern = re.compile(r'(\w+)\s*\{')
            match = entity_pattern.match(line)
            if match:
                entity_id = match.group(1)
                diagram.nodes.append(DiagramNode(
                    node_id=entity_id,
                    label=entity_id,
                    type='entity'
                ))
                continue

            # Relationship: ENTITY1 ||--o{ ENTITY2 : "relationship"
            rel_pattern = re.compile(r'(\w+)\s+(\|\|--o\{|\}o--\|\|)\s+(\w+)\s*:\s*"([^"]+)"')
            match = rel_pattern.match(line)
            if match:
                source = match.group(1)
                rel_symbol = match.group(2)
                target = match.group(3)
                label = match.group(4)

                diagram.edges.append(DiagramEdge(
                    source=source,
                    target=target,
                    label=label,
                    type='relationship'
                ))

    def _extract_plantuml(
        self,
        content: str,
        file_path: Path
    ) -> List[ExtractedDiagram]:
        """Extract PlantUML diagrams"""
        diagrams = []

        # Pattern for PlantUML blocks
        pattern = re.compile(r'```plantuml\n(.*?)```', re.DOTALL)

        for i, match in enumerate(pattern.finditer(content)):
            plantuml_code = match.group(1)

            diagram = ExtractedDiagram(
                diagram_id=f"diagram_plantuml_{i}",
                source_file=file_path,
                source_position=match.start(),
                diagram_type=DiagramType.PLANTUML,
                raw_content=plantuml_code,
                metadata={'format': 'plantuml'}
            )

            # Basic PlantUML parsing
            self._parse_plantuml(diagram)

            diagrams.append(diagram)

        return diagrams

    def _parse_plantuml(self, diagram: ExtractedDiagram):
        """Parse PlantUML diagram (basic)"""
        lines = diagram.raw_content.strip().split('\n')

        for line in lines:
            line = line.strip()

            # Arrow definitions: A --> B : label
            arrow_pattern = re.compile(r'(\w+)\s*(-->|->|\.\.>)\s*(\w+)(?:\s*:\s*(.+))?')
            match = arrow_pattern.match(line)
            if match:
                source = match.group(1)
                target = match.group(3)
                label = match.group(4) or ""

                # Add nodes if not exist
                for node_id in [source, target]:
                    if not any(n.node_id == node_id for n in diagram.nodes):
                        diagram.nodes.append(DiagramNode(
                            node_id=node_id,
                            label=node_id,
                            type='default'
                        ))

                diagram.edges.append(DiagramEdge(
                    source=source,
                    target=target,
                    label=label.strip()
                ))

    def _extract_graphviz(
        self,
        content: str,
        file_path: Path
    ) -> List[ExtractedDiagram]:
        """Extract Graphviz DOT diagrams"""
        diagrams = []

        # Pattern for Graphviz blocks
        pattern = re.compile(r'```(?:dot|graphviz)\n(.*?)```', re.DOTALL)

        for i, match in enumerate(pattern.finditer(content)):
            dot_code = match.group(1)

            diagram = ExtractedDiagram(
                diagram_id=f"diagram_graphviz_{i}",
                source_file=file_path,
                source_position=match.start(),
                diagram_type=DiagramType.GRAPHVIZ,
                raw_content=dot_code,
                metadata={'format': 'graphviz'}
            )

            # Basic DOT parsing
            self._parse_graphviz(diagram)

            diagrams.append(diagram)

        return diagrams

    def _parse_graphviz(self, diagram: ExtractedDiagram):
        """Parse Graphviz DOT format (basic)"""
        content = diagram.raw_content

        # Node definitions: node_id [label="..."]
        node_pattern = re.compile(r'(\w+)\s*\[label="([^"]+)"\]')
        for match in node_pattern.finditer(content):
            node_id = match.group(1)
            label = match.group(2)

            diagram.nodes.append(DiagramNode(
                node_id=node_id,
                label=label,
                type='default'
            ))

        # Edge definitions: A -> B [label="..."]
        edge_pattern = re.compile(r'(\w+)\s*->\s*(\w+)(?:\s*\[label="([^"]+)"\])?')
        for match in edge_pattern.finditer(content):
            source = match.group(1)
            target = match.group(2)
            label = match.group(3) or ""

            # Add nodes if not exist
            for node_id in [source, target]:
                if not any(n.node_id == node_id for n in diagram.nodes):
                    diagram.nodes.append(DiagramNode(
                        node_id=node_id,
                        label=node_id,
                        type='default'
                    ))

            diagram.edges.append(DiagramEdge(
                source=source,
                target=target,
                label=label
            ))

    def _extract_svg(
        self,
        content: str,
        file_path: Path
    ) -> List[ExtractedDiagram]:
        """Extract embedded SVG diagrams"""
        diagrams = []

        # Pattern for SVG tags
        pattern = re.compile(r'<svg[^>]*>(.*?)</svg>', re.DOTALL | re.IGNORECASE)

        for i, match in enumerate(pattern.finditer(content)):
            svg_content = match.group(0)

            diagram = ExtractedDiagram(
                diagram_id=f"diagram_svg_{i}",
                source_file=file_path,
                source_position=match.start(),
                diagram_type=DiagramType.SVG,
                raw_content=svg_content,
                svg=svg_content,
                metadata={'format': 'svg'}
            )

            diagrams.append(diagram)

        return diagrams


# ==============================================================================
# Factory Function
# ==============================================================================

def create_diagram_extractor() -> DiagramExtractor:
    """
    Create a new DiagramExtractor instance

    Returns:
        Configured DiagramExtractor
    """
    return DiagramExtractor()


# ==============================================================================
# Standalone Test
# ==============================================================================

if __name__ == '__main__':
    test_content = """
# System Architecture

## Process Flow

```mermaid
graph TD
    A[Start] --> B{Check Input}
    B -->|Valid| C[Process Data]
    B -->|Invalid| D[Show Error]
    C --> E[Save Result]
    D --> F[End]
    E --> F
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database

    User->>API: Request Data
    API->>Database: Query
    Database-->>API: Results
    API-->>User: Response
```
"""

    test_file = Path('test_diagram_extraction.md')
    test_file.write_text(test_content)

    extractor = create_diagram_extractor()
    diagrams = extractor.extract(test_content, test_file, {})

    print(f"\n=== Diagram Extraction Results ===")
    print(f"Found {len(diagrams)} diagrams\n")

    for obj in diagrams:
        diagram_data = obj.structured_data

        print(f"Diagram: {obj.object_id}")
        print(f"Type: {diagram_data['diagram_type']}")
        print(f"Nodes: {len(diagram_data['nodes'])}")
        for node in diagram_data['nodes']:
            print(f"  - {node['node_id']}: {node['label']} ({node['type']})")

        print(f"Edges: {len(diagram_data['edges'])}")
        for edge in diagram_data['edges']:
            label_str = f" ({edge['label']})" if edge['label'] else ""
            print(f"  - {edge['source']} -> {edge['target']}{label_str}")

        print("\n" + "=" * 50 + "\n")

    test_file.unlink()
