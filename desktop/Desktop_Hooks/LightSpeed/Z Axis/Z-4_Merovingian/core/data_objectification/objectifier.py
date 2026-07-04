"""
Document Objectifier - V1.0.0
Main engine for transforming unstructured documents into structured objects

This module orchestrates all extraction systems to convert document content
into standards-compliant structured data objects.

Author: LightSpeed Team
Date: December 27, 2025
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import json


# ==============================================================================
# Object Types and Data Models
# ==============================================================================

class ObjectType(Enum):
    """Types of objects that can be extracted"""
    TABLE = "table"
    CITATION = "citation"
    CODE = "code"
    METADATA = "metadata"
    DIAGRAM = "diagram"
    EQUATION = "equation"
    FIGURE = "figure"
    FOOTNOTE = "footnote"
    HEADING = "heading"
    LIST = "list"


@dataclass
class ExtractedObject:
    """
    Base class for all extracted objects

    Attributes:
        object_id: Unique identifier for this object
        object_type: Type of extracted object
        source_file: Path to source document
        source_page: Page number where found (if applicable)
        source_position: Character/line position in source
        content: Raw extracted content
        structured_data: Structured representation
        confidence: Extraction confidence (0.0-1.0)
        metadata: Additional metadata about extraction
        standards_compliant: Dict of standard → compliance status
        extracted_at: Timestamp of extraction
    """
    object_id: str
    object_type: ObjectType
    source_file: Path
    source_page: Optional[int] = None
    source_position: Optional[int] = None
    content: str = ""
    structured_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    standards_compliant: Dict[str, bool] = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['object_type'] = self.object_type.value
        data['source_file'] = str(self.source_file)
        data['extracted_at'] = self.extracted_at.isoformat()
        return data

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ObjectificationResult:
    """
    Results from document objectification

    Attributes:
        source_file: Path to source document
        objects: List of all extracted objects
        summary: Summary statistics
        errors: List of errors encountered
        processing_time: Time taken to process
    """
    source_file: Path
    objects: List[ExtractedObject] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    processing_time: float = 0.0

    def get_objects_by_type(self, object_type: ObjectType) -> List[ExtractedObject]:
        """Get all objects of a specific type"""
        return [obj for obj in self.objects if obj.object_type == object_type]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'source_file': str(self.source_file),
            'objects': [obj.to_dict() for obj in self.objects],
            'summary': self.summary,
            'errors': self.errors,
            'processing_time': self.processing_time
        }


# ==============================================================================
# Document Objectifier
# ==============================================================================

class DocumentObjectifier:
    """
    Main objectification engine

    Orchestrates extraction of structured objects from unstructured documents.
    Supports PDF, DOCX, TXT, Markdown, HTML, and other formats.
    """

    def __init__(self):
        """Initialize objectifier with all extractors"""
        # Lazy import to avoid circular dependencies
        self.extractors = {}
        self._initialize_extractors()

    def _initialize_extractors(self):
        """Initialize all available extractors"""
        try:
            from .table_extractor import create_table_extractor
            self.extractors['table'] = create_table_extractor()
        except ImportError:
            pass

        try:
            from .citation_extractor import create_citation_extractor
            self.extractors['citation'] = create_citation_extractor()
        except ImportError:
            pass

        try:
            from .code_extractor import create_code_extractor
            self.extractors['code'] = create_code_extractor()
        except ImportError:
            pass

        try:
            from .metadata_extractor import create_metadata_extractor
            self.extractors['metadata'] = create_metadata_extractor()
        except ImportError:
            pass

        try:
            from .diagram_extractor import create_diagram_extractor
            self.extractors['diagram'] = create_diagram_extractor()
        except ImportError:
            pass

    def objectify_document(
        self,
        file_path: Union[str, Path],
        extract_types: Optional[List[ObjectType]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> ObjectificationResult:
        """
        Extract all structured objects from a document

        Args:
            file_path: Path to document
            extract_types: Types to extract (None = all)
            options: Extraction options

        Returns:
            ObjectificationResult with all extracted objects
        """
        start_time = datetime.now()
        file_path = Path(file_path)

        if not file_path.exists():
            return ObjectificationResult(
                source_file=file_path,
                errors=[f"File not found: {file_path}"]
            )

        # Read document content
        try:
            content = self._read_document(file_path)
        except Exception as e:
            return ObjectificationResult(
                source_file=file_path,
                errors=[f"Failed to read document: {str(e)}"]
            )

        # Determine which types to extract
        if extract_types is None:
            extract_types = list(ObjectType)

        # Extract objects
        result = ObjectificationResult(source_file=file_path)

        for obj_type in extract_types:
            try:
                objects = self._extract_type(
                    content,
                    file_path,
                    obj_type,
                    options or {}
                )
                result.objects.extend(objects)
            except Exception as e:
                result.errors.append(f"Error extracting {obj_type.value}: {str(e)}")

        # Generate summary
        result.summary = self._generate_summary(result.objects)

        # Calculate processing time
        end_time = datetime.now()
        result.processing_time = (end_time - start_time).total_seconds()

        return result

    def _read_document(self, file_path: Path) -> str:
        """
        Read document content based on file type

        Args:
            file_path: Path to document

        Returns:
            Document content as string
        """
        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            return self._read_pdf(file_path)
        elif suffix in ['.docx', '.doc']:
            return self._read_docx(file_path)
        elif suffix in ['.txt', '.md', '.markdown']:
            return file_path.read_text(encoding='utf-8')
        elif suffix in ['.html', '.htm']:
            return self._read_html(file_path)
        else:
            # Try as plain text
            try:
                return file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                return file_path.read_text(encoding='latin-1')

    def _read_pdf(self, file_path: Path) -> str:
        """Extract text from PDF"""
        try:
            import PyPDF2
            text = []
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text())
            return '\n\n'.join(text)
        except ImportError:
            # Fallback: try pdfplumber
            try:
                import pdfplumber
                text = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text.append(page.extract_text())
                return '\n\n'.join(text)
            except ImportError:
                raise ImportError("PDF reading requires PyPDF2 or pdfplumber")

    def _read_docx(self, file_path: Path) -> str:
        """Extract text from DOCX"""
        try:
            import docx
            doc = docx.Document(file_path)
            return '\n\n'.join([para.text for para in doc.paragraphs])
        except ImportError:
            raise ImportError("DOCX reading requires python-docx")

    def _read_html(self, file_path: Path) -> str:
        """Extract text from HTML"""
        try:
            from bs4 import BeautifulSoup
            html = file_path.read_text(encoding='utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text()
        except ImportError:
            # Fallback: basic HTML stripping
            html = file_path.read_text(encoding='utf-8')
            return re.sub(r'<[^>]+>', '', html)

    def _extract_type(
        self,
        content: str,
        file_path: Path,
        object_type: ObjectType,
        options: Dict[str, Any]
    ) -> List[ExtractedObject]:
        """
        Extract objects of a specific type

        Args:
            content: Document content
            file_path: Source file path
            object_type: Type to extract
            options: Extraction options

        Returns:
            List of extracted objects
        """
        type_key = object_type.value

        if type_key in self.extractors:
            extractor = self.extractors[type_key]
            return extractor.extract(content, file_path, options)
        else:
            # Use built-in extraction
            return self._builtin_extract(content, file_path, object_type)

    def _builtin_extract(
        self,
        content: str,
        file_path: Path,
        object_type: ObjectType
    ) -> List[ExtractedObject]:
        """
        Built-in extraction for basic object types

        Args:
            content: Document content
            file_path: Source file
            object_type: Type to extract

        Returns:
            List of extracted objects
        """
        if object_type == ObjectType.HEADING:
            return self._extract_headings(content, file_path)
        elif object_type == ObjectType.LIST:
            return self._extract_lists(content, file_path)
        elif object_type == ObjectType.EQUATION:
            return self._extract_equations(content, file_path)
        elif object_type == ObjectType.FIGURE:
            return self._extract_figures(content, file_path)
        elif object_type == ObjectType.FOOTNOTE:
            return self._extract_footnotes(content, file_path)
        else:
            return []

    def _extract_headings(self, content: str, file_path: Path) -> List[ExtractedObject]:
        """Extract headings (Markdown-style)"""
        objects = []
        for i, line in enumerate(content.split('\n')):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                heading_text = match.group(2).strip()

                obj = ExtractedObject(
                    object_id=f"heading_{i}",
                    object_type=ObjectType.HEADING,
                    source_file=file_path,
                    source_position=i,
                    content=heading_text,
                    structured_data={
                        'level': level,
                        'text': heading_text
                    }
                )
                objects.append(obj)

        return objects

    def _extract_lists(self, content: str, file_path: Path) -> List[ExtractedObject]:
        """Extract lists (Markdown-style)"""
        objects = []
        list_pattern = re.compile(r'^(\s*)([-*+]|\d+\.)\s+(.+)$')
        current_list = []
        list_start = 0

        for i, line in enumerate(content.split('\n')):
            match = list_pattern.match(line)
            if match:
                if not current_list:
                    list_start = i
                current_list.append({
                    'indent': len(match.group(1)),
                    'marker': match.group(2),
                    'text': match.group(3)
                })
            elif current_list:
                # End of list
                obj = ExtractedObject(
                    object_id=f"list_{list_start}",
                    object_type=ObjectType.LIST,
                    source_file=file_path,
                    source_position=list_start,
                    content='\n'.join([item['text'] for item in current_list]),
                    structured_data={
                        'items': current_list,
                        'ordered': current_list[0]['marker'][0].isdigit()
                    }
                )
                objects.append(obj)
                current_list = []

        # Handle list at end of document
        if current_list:
            obj = ExtractedObject(
                object_id=f"list_{list_start}",
                object_type=ObjectType.LIST,
                source_file=file_path,
                source_position=list_start,
                content='\n'.join([item['text'] for item in current_list]),
                structured_data={
                    'items': current_list,
                    'ordered': current_list[0]['marker'][0].isdigit()
                }
            )
            objects.append(obj)

        return objects

    def _extract_equations(self, content: str, file_path: Path) -> List[ExtractedObject]:
        """Extract equations (LaTeX-style)"""
        objects = []

        # Display equations: $$...$$
        display_pattern = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
        for i, match in enumerate(display_pattern.finditer(content)):
            obj = ExtractedObject(
                object_id=f"equation_display_{i}",
                object_type=ObjectType.EQUATION,
                source_file=file_path,
                source_position=match.start(),
                content=match.group(1).strip(),
                structured_data={
                    'latex': match.group(1).strip(),
                    'display': True
                }
            )
            objects.append(obj)

        # Inline equations: $...$
        inline_pattern = re.compile(r'\$(.+?)\$')
        for i, match in enumerate(inline_pattern.finditer(content)):
            # Skip if part of display equation
            if not any(obj.source_position <= match.start() < obj.source_position + len(obj.content)
                      for obj in objects):
                obj = ExtractedObject(
                    object_id=f"equation_inline_{i}",
                    object_type=ObjectType.EQUATION,
                    source_file=file_path,
                    source_position=match.start(),
                    content=match.group(1).strip(),
                    structured_data={
                        'latex': match.group(1).strip(),
                        'display': False
                    }
                )
                objects.append(obj)

        return objects

    def _extract_figures(self, content: str, file_path: Path) -> List[ExtractedObject]:
        """Extract figure references"""
        objects = []

        # Markdown figures: ![alt](path)
        pattern = re.compile(r'!\[([^\]]*)\]\(([^\)]+)\)')
        for i, match in enumerate(pattern.finditer(content)):
            obj = ExtractedObject(
                object_id=f"figure_{i}",
                object_type=ObjectType.FIGURE,
                source_file=file_path,
                source_position=match.start(),
                content=match.group(0),
                structured_data={
                    'alt_text': match.group(1),
                    'path': match.group(2),
                    'caption': match.group(1)
                }
            )
            objects.append(obj)

        return objects

    def _extract_footnotes(self, content: str, file_path: Path) -> List[ExtractedObject]:
        """Extract footnotes"""
        objects = []

        # Markdown footnotes: [^1]: text
        pattern = re.compile(r'^\[\^(\d+)\]:\s*(.+)$', re.MULTILINE)
        for match in pattern.finditer(content):
            obj = ExtractedObject(
                object_id=f"footnote_{match.group(1)}",
                object_type=ObjectType.FOOTNOTE,
                source_file=file_path,
                source_position=match.start(),
                content=match.group(2),
                structured_data={
                    'number': int(match.group(1)),
                    'text': match.group(2)
                }
            )
            objects.append(obj)

        return objects

    def _generate_summary(self, objects: List[ExtractedObject]) -> Dict[str, int]:
        """Generate summary statistics"""
        summary = {}
        for obj_type in ObjectType:
            count = sum(1 for obj in objects if obj.object_type == obj_type)
            if count > 0:
                summary[obj_type.value] = count

        summary['total'] = len(objects)
        return summary

    def export_objects(
        self,
        result: ObjectificationResult,
        output_path: Union[str, Path],
        format: str = 'json'
    ) -> bool:
        """
        Export extracted objects to file

        Args:
            result: Objectification result
            output_path: Output file path
            format: Output format ('json', 'csv', 'yaml')

        Returns:
            True if successful
        """
        output_path = Path(output_path)

        try:
            if format == 'json':
                output_path.write_text(
                    json.dumps(result.to_dict(), indent=2),
                    encoding='utf-8'
                )
            elif format == 'csv':
                self._export_csv(result, output_path)
            elif format == 'yaml':
                self._export_yaml(result, output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")

            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False

    def _export_csv(self, result: ObjectificationResult, output_path: Path):
        """Export to CSV"""
        import csv

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Object ID', 'Type', 'Content', 'Page',
                'Position', 'Confidence', 'Metadata'
            ])

            for obj in result.objects:
                writer.writerow([
                    obj.object_id,
                    obj.object_type.value,
                    obj.content[:100] + '...' if len(obj.content) > 100 else obj.content,
                    obj.source_page or '',
                    obj.source_position or '',
                    obj.confidence,
                    json.dumps(obj.metadata)
                ])

    def _export_yaml(self, result: ObjectificationResult, output_path: Path):
        """Export to YAML"""
        try:
            import yaml
            output_path.write_text(
                yaml.dump(result.to_dict(), default_flow_style=False),
                encoding='utf-8'
            )
        except ImportError:
            raise ImportError("YAML export requires PyYAML")


# ==============================================================================
# Factory Function
# ==============================================================================

def create_objectifier() -> DocumentObjectifier:
    """
    Create a new DocumentObjectifier instance

    Returns:
        Configured DocumentObjectifier
    """
    return DocumentObjectifier()


# ==============================================================================
# Standalone Test
# ==============================================================================

if __name__ == '__main__':
    # Test with a sample markdown document
    test_content = """
# Introduction

This is a test document with various elements.

## Lists

- Item 1
- Item 2
  - Nested item
- Item 3

1. First
2. Second
3. Third

## Equations

The equation $E = mc^2$ is famous.

Display equation:
$$
\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}
$$

## Figures

![Test Figure](./test.png)

## Footnotes

This has a footnote[^1].

[^1]: This is the footnote text.
"""

    # Create test file
    test_file = Path('test_objectification.md')
    test_file.write_text(test_content)

    # Create objectifier
    objectifier = create_objectifier()

    # Objectify document
    result = objectifier.objectify_document(test_file)

    # Print results
    print(f"\n=== Objectification Results ===")
    print(f"Source: {result.source_file}")
    print(f"Processing Time: {result.processing_time:.3f}s")
    print(f"\nSummary:")
    for obj_type, count in result.summary.items():
        print(f"  {obj_type}: {count}")

    print(f"\nExtracted Objects:")
    for obj in result.objects:
        print(f"\n{obj.object_type.value.upper()} ({obj.object_id}):")
        print(f"  Content: {obj.content[:80]}...")
        print(f"  Data: {obj.structured_data}")

    # Export to JSON
    objectifier.export_objects(result, 'test_objectification.json')
    print(f"\nExported to test_objectification.json")

    # Cleanup
    test_file.unlink()
