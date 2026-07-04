"""
Data Objectification System - V1.0.0
Transforms unstructured document content into structured, standards-compliant objects

This module provides intelligent extraction and transformation of:
- Tables → pandas DataFrames → SQL databases
- Citations → BibTeX/RIS formats
- Code → AST representations
- Metadata → Dublin Core
- Diagrams → SVG/structured formats

Author: LightSpeed Team
Date: December 27, 2025
"""

from .objectifier import (
    DocumentObjectifier,
    ExtractedObject,
    ObjectType,
    create_objectifier
)

from .table_extractor import (
    TableExtractor,
    ExtractedTable,
    create_table_extractor
)

from .citation_extractor import (
    CitationExtractor,
    ExtractedCitation,
    CitationFormat,
    create_citation_extractor
)

from .code_extractor import (
    CodeExtractor,
    ExtractedCode,
    CodeLanguage,
    create_code_extractor
)

from .metadata_extractor import (
    MetadataExtractor,
    ExtractedMetadata,
    create_metadata_extractor
)

from .diagram_extractor import (
    DiagramExtractor,
    ExtractedDiagram,
    create_diagram_extractor
)

__all__ = [
    # Main objectifier
    'DocumentObjectifier',
    'ExtractedObject',
    'ObjectType',
    'create_objectifier',

    # Table extraction
    'TableExtractor',
    'ExtractedTable',
    'create_table_extractor',

    # Citation extraction
    'CitationExtractor',
    'ExtractedCitation',
    'CitationFormat',
    'create_citation_extractor',

    # Code extraction
    'CodeExtractor',
    'ExtractedCode',
    'CodeLanguage',
    'create_code_extractor',

    # Metadata extraction
    'MetadataExtractor',
    'ExtractedMetadata',
    'create_metadata_extractor',

    # Diagram extraction
    'DiagramExtractor',
    'ExtractedDiagram',
    'create_diagram_extractor',
]
