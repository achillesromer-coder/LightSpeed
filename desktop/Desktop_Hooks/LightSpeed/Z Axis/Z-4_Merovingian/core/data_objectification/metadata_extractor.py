"""
Metadata Extractor - V1.0.0
Extracts document metadata and converts to Dublin Core standard

Supports:
- Document headers (title, author, date)
- YAML/TOML frontmatter
- HTML meta tags
- PDF metadata
- DOCX properties
- Markdown metadata
- Dublin Core mapping
- Schema.org mapping

Outputs:
- Dublin Core metadata
- Schema.org JSON-LD
- Custom metadata schemas

Author: LightSpeed Team
Date: December 27, 2025
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


# ==============================================================================
# Dublin Core Elements
# ==============================================================================

DUBLIN_CORE_ELEMENTS = {
    # Core elements
    'dc.title': 'Title of the resource',
    'dc.creator': 'Entity primarily responsible for making the resource',
    'dc.subject': 'Topic of the resource',
    'dc.description': 'Description of the resource',
    'dc.publisher': 'Entity responsible for making the resource available',
    'dc.contributor': 'Entity responsible for making contributions',
    'dc.date': 'Point or period of time associated with the resource',
    'dc.type': 'Nature or genre of the resource',
    'dc.format': 'File format, physical medium, or dimensions',
    'dc.identifier': 'Unambiguous reference to the resource',
    'dc.source': 'Related resource from which the resource is derived',
    'dc.language': 'Language of the resource',
    'dc.relation': 'Related resource',
    'dc.coverage': 'Spatial or temporal topic',
    'dc.rights': 'Information about rights held in and over the resource',
}


# ==============================================================================
# Data Models
# ==============================================================================

@dataclass
class ExtractedMetadata:
    """
    Extracted document metadata

    Attributes:
        metadata_id: Unique identifier
        source_file: Source document path
        title: Document title
        authors: List of authors
        date: Creation/publication date
        description: Document description/abstract
        keywords: List of keywords/subjects
        language: Document language
        publisher: Publisher
        rights: Copyright/license information
        version: Document version
        dublin_core: Dublin Core metadata
        schema_org: Schema.org JSON-LD
        raw_metadata: Raw metadata as extracted
        confidence: Extraction confidence (0.0-1.0)
    """
    metadata_id: str
    source_file: Path
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    date: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    language: str = "en"
    publisher: Optional[str] = None
    rights: Optional[str] = None
    version: Optional[str] = None
    dublin_core: Dict[str, str] = field(default_factory=dict)
    schema_org: Dict[str, Any] = field(default_factory=dict)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'metadata_id': self.metadata_id,
            'source_file': str(self.source_file),
            'title': self.title,
            'authors': self.authors,
            'date': self.date,
            'description': self.description,
            'keywords': self.keywords,
            'language': self.language,
            'publisher': self.publisher,
            'rights': self.rights,
            'version': self.version,
            'dublin_core': self.dublin_core,
            'schema_org': self.schema_org,
            'raw_metadata': self.raw_metadata,
            'confidence': self.confidence
        }


# ==============================================================================
# Metadata Extractor
# ==============================================================================

class MetadataExtractor:
    """
    Extracts metadata from documents and converts to standard formats
    """

    def __init__(self):
        """Initialize metadata extractor"""
        pass

    def extract(
        self,
        content: str,
        file_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Extract metadata from content

        Args:
            content: Document content
            file_path: Source file path
            options: Extraction options

        Returns:
            List with single ExtractedMetadata wrapped as ExtractedObject
        """
        from .objectifier import ExtractedObject, ObjectType

        options = options or {}

        # Extract metadata using multiple methods
        metadata = ExtractedMetadata(
            metadata_id="metadata",
            source_file=file_path
        )

        # Try different extraction methods
        self._extract_yaml_frontmatter(content, metadata)
        self._extract_html_meta(content, metadata)
        self._extract_markdown_headers(content, metadata)
        self._extract_document_properties(file_path, metadata)

        # Generate standard formats
        self._generate_dublin_core(metadata)
        self._generate_schema_org(metadata)

        # Wrap in ExtractedObject
        obj = ExtractedObject(
            object_id=metadata.metadata_id,
            object_type=ObjectType.METADATA,
            source_file=metadata.source_file,
            content=self._metadata_to_string(metadata),
            structured_data=metadata.to_dict(),
            confidence=metadata.confidence
        )

        return [obj]

    def _extract_yaml_frontmatter(
        self,
        content: str,
        metadata: ExtractedMetadata
    ):
        """Extract YAML frontmatter from Markdown documents"""
        # YAML frontmatter: ---\nkey: value\n---
        yaml_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        match = yaml_pattern.match(content)

        if match:
            yaml_content = match.group(1)

            # Parse YAML-like content (simple key: value pairs)
            for line in yaml_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()

                    # Remove quotes
                    value = value.strip('"\'')

                    # Map to metadata fields
                    if key == 'title':
                        metadata.title = value
                        metadata.confidence = min(metadata.confidence + 0.3, 1.0)
                    elif key in ['author', 'authors']:
                        # Handle multiple authors
                        if ',' in value:
                            metadata.authors = [a.strip() for a in value.split(',')]
                        else:
                            metadata.authors = [value]
                        metadata.confidence = min(metadata.confidence + 0.2, 1.0)
                    elif key == 'date':
                        metadata.date = value
                        metadata.confidence = min(metadata.confidence + 0.1, 1.0)
                    elif key in ['description', 'abstract', 'summary']:
                        metadata.description = value
                    elif key in ['keywords', 'tags']:
                        if ',' in value:
                            metadata.keywords = [k.strip() for k in value.split(',')]
                        else:
                            metadata.keywords = [value]
                    elif key == 'language':
                        metadata.language = value
                    elif key == 'publisher':
                        metadata.publisher = value
                    elif key in ['license', 'rights', 'copyright']:
                        metadata.rights = value
                    elif key == 'version':
                        metadata.version = value

                    # Store in raw metadata
                    metadata.raw_metadata[key] = value

    def _extract_html_meta(
        self,
        content: str,
        metadata: ExtractedMetadata
    ):
        """Extract HTML meta tags"""
        # Meta tags: <meta name="..." content="...">
        meta_pattern = re.compile(
            r'<meta\s+(?:name|property)=["\']([^"\']+)["\']\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE
        )

        for match in meta_pattern.finditer(content):
            name = match.group(1).lower()
            value = match.group(2)

            # Map meta tags to metadata fields
            if name in ['title', 'og:title', 'twitter:title']:
                if not metadata.title:
                    metadata.title = value
                    metadata.confidence = min(metadata.confidence + 0.2, 1.0)
            elif name in ['author', 'creator']:
                if not metadata.authors:
                    metadata.authors = [value]
            elif name in ['description', 'og:description', 'twitter:description']:
                if not metadata.description:
                    metadata.description = value
            elif name in ['keywords', 'tags']:
                if not metadata.keywords:
                    metadata.keywords = [k.strip() for k in value.split(',')]
            elif name == 'language':
                metadata.language = value
            elif name == 'date':
                metadata.date = value

            metadata.raw_metadata[name] = value

    def _extract_markdown_headers(
        self,
        content: str,
        metadata: ExtractedMetadata
    ):
        """Extract metadata from Markdown document structure"""
        lines = content.split('\n')

        # First H1 is likely the title
        if not metadata.title:
            for line in lines[:20]:  # Check first 20 lines
                match = re.match(r'^#\s+(.+)$', line.strip())
                if match:
                    metadata.title = match.group(1).strip()
                    metadata.confidence = min(metadata.confidence + 0.15, 1.0)
                    break

        # Look for "Author:" or "By:" patterns
        if not metadata.authors:
            for line in lines[:30]:
                # Pattern: Author: Name
                match = re.match(r'^\*?\*?(?:Author|By)s?:?\*?\*?\s+(.+)$', line.strip(), re.IGNORECASE)
                if match:
                    authors_str = match.group(1)
                    # Remove common formatting
                    authors_str = re.sub(r'[\*_]', '', authors_str)
                    metadata.authors = [a.strip() for a in authors_str.split(',')]
                    break

        # Look for "Date:" pattern
        if not metadata.date:
            for line in lines[:30]:
                match = re.match(r'^\*?\*?Date:?\*?\*?\s+(.+)$', line.strip(), re.IGNORECASE)
                if match:
                    metadata.date = match.group(1).strip()
                    break

    def _extract_document_properties(
        self,
        file_path: Path,
        metadata: ExtractedMetadata
    ):
        """Extract metadata from document file properties"""
        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            self._extract_pdf_metadata(file_path, metadata)
        elif suffix in ['.docx', '.doc']:
            self._extract_docx_metadata(file_path, metadata)

        # Use filename as fallback title
        if not metadata.title:
            # Remove extension and clean up filename
            title = file_path.stem
            title = re.sub(r'[_-]+', ' ', title)
            title = title.title()
            metadata.title = title
            metadata.confidence = min(metadata.confidence + 0.05, 1.0)

    def _extract_pdf_metadata(
        self,
        file_path: Path,
        metadata: ExtractedMetadata
    ):
        """Extract metadata from PDF properties"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                info = reader.metadata

                if info:
                    if '/Title' in info and not metadata.title:
                        metadata.title = str(info['/Title'])
                        metadata.confidence = min(metadata.confidence + 0.25, 1.0)

                    if '/Author' in info and not metadata.authors:
                        metadata.authors = [str(info['/Author'])]

                    if '/Subject' in info and not metadata.description:
                        metadata.description = str(info['/Subject'])

                    if '/Keywords' in info and not metadata.keywords:
                        keywords_str = str(info['/Keywords'])
                        metadata.keywords = [k.strip() for k in keywords_str.split(',')]

                    if '/CreationDate' in info and not metadata.date:
                        metadata.date = str(info['/CreationDate'])

                    metadata.raw_metadata['pdf_metadata'] = {
                        str(k): str(v) for k, v in info.items()
                    }

        except ImportError:
            pass
        except Exception:
            pass

    def _extract_docx_metadata(
        self,
        file_path: Path,
        metadata: ExtractedMetadata
    ):
        """Extract metadata from DOCX properties"""
        try:
            import docx
            doc = docx.Document(file_path)
            props = doc.core_properties

            if props.title and not metadata.title:
                metadata.title = props.title
                metadata.confidence = min(metadata.confidence + 0.25, 1.0)

            if props.author and not metadata.authors:
                metadata.authors = [props.author]

            if props.subject and not metadata.description:
                metadata.description = props.subject

            if props.keywords and not metadata.keywords:
                metadata.keywords = [k.strip() for k in props.keywords.split(',')]

            if props.created and not metadata.date:
                metadata.date = props.created.isoformat()

            metadata.raw_metadata['docx_properties'] = {
                'title': props.title,
                'author': props.author,
                'subject': props.subject,
                'keywords': props.keywords,
                'created': str(props.created) if props.created else None,
                'modified': str(props.modified) if props.modified else None,
            }

        except ImportError:
            pass
        except Exception:
            pass

    def _generate_dublin_core(self, metadata: ExtractedMetadata):
        """Generate Dublin Core metadata"""
        dc = {}

        if metadata.title:
            dc['dc.title'] = metadata.title

        if metadata.authors:
            for i, author in enumerate(metadata.authors):
                dc[f'dc.creator.{i+1}'] = author

        if metadata.description:
            dc['dc.description'] = metadata.description

        if metadata.keywords:
            for i, keyword in enumerate(metadata.keywords):
                dc[f'dc.subject.{i+1}'] = keyword

        if metadata.date:
            dc['dc.date'] = metadata.date

        if metadata.publisher:
            dc['dc.publisher'] = metadata.publisher

        if metadata.rights:
            dc['dc.rights'] = metadata.rights

        if metadata.language:
            dc['dc.language'] = metadata.language

        # Identifier (use filename)
        dc['dc.identifier'] = metadata.source_file.name

        # Type (infer from file extension)
        suffix = metadata.source_file.suffix.lower()
        type_map = {
            '.pdf': 'Text',
            '.docx': 'Text',
            '.doc': 'Text',
            '.txt': 'Text',
            '.md': 'Text',
            '.html': 'Text',
            '.jpg': 'Image',
            '.png': 'Image',
            '.mp4': 'MovingImage',
            '.mp3': 'Sound',
        }
        dc['dc.type'] = type_map.get(suffix, 'Text')

        # Format
        dc['dc.format'] = f'application/{suffix[1:]}' if suffix else 'text/plain'

        metadata.dublin_core = dc

    def _generate_schema_org(self, metadata: ExtractedMetadata):
        """Generate Schema.org JSON-LD metadata"""
        schema = {
            '@context': 'https://schema.org',
            '@type': 'CreativeWork',
        }

        if metadata.title:
            schema['name'] = metadata.title

        if metadata.authors:
            schema['author'] = [
                {'@type': 'Person', 'name': author}
                for author in metadata.authors
            ]

        if metadata.description:
            schema['description'] = metadata.description

        if metadata.keywords:
            schema['keywords'] = ', '.join(metadata.keywords)

        if metadata.date:
            schema['datePublished'] = metadata.date

        if metadata.publisher:
            schema['publisher'] = {
                '@type': 'Organization',
                'name': metadata.publisher
            }

        if metadata.language:
            schema['inLanguage'] = metadata.language

        if metadata.rights:
            schema['license'] = metadata.rights

        metadata.schema_org = schema

    def _metadata_to_string(self, metadata: ExtractedMetadata) -> str:
        """Convert metadata to string representation"""
        lines = []

        if metadata.title:
            lines.append(f"Title: {metadata.title}")

        if metadata.authors:
            lines.append(f"Authors: {', '.join(metadata.authors)}")

        if metadata.date:
            lines.append(f"Date: {metadata.date}")

        if metadata.description:
            lines.append(f"Description: {metadata.description}")

        if metadata.keywords:
            lines.append(f"Keywords: {', '.join(metadata.keywords)}")

        if metadata.language:
            lines.append(f"Language: {metadata.language}")

        if metadata.publisher:
            lines.append(f"Publisher: {metadata.publisher}")

        if metadata.rights:
            lines.append(f"Rights: {metadata.rights}")

        return '\n'.join(lines)


# ==============================================================================
# Factory Function
# ==============================================================================

def create_metadata_extractor() -> MetadataExtractor:
    """
    Create a new MetadataExtractor instance

    Returns:
        Configured MetadataExtractor
    """
    return MetadataExtractor()


# ==============================================================================
# Standalone Test
# ==============================================================================

if __name__ == '__main__':
    test_content = """---
title: "Advanced Machine Learning Techniques"
author: "Dr. Jane Smith, Prof. John Doe"
date: "2025-12-27"
keywords: "machine learning, AI, deep learning"
description: "Comprehensive guide to modern ML techniques"
---

# Advanced Machine Learning Techniques

By Dr. Jane Smith and Prof. John Doe

This document explores cutting-edge approaches in machine learning.

## Introduction

Machine learning has revolutionized artificial intelligence...
"""

    test_file = Path('test_metadata_extraction.md')
    test_file.write_text(test_content)

    extractor = create_metadata_extractor()
    metadata_list = extractor.extract(test_content, test_file, {})

    print(f"\n=== Metadata Extraction Results ===\n")

    if metadata_list:
        obj = metadata_list[0]
        metadata_data = obj.structured_data

        print(f"Title: {metadata_data['title']}")
        print(f"Authors: {', '.join(metadata_data['authors'])}")
        print(f"Date: {metadata_data['date']}")
        print(f"Keywords: {', '.join(metadata_data['keywords'])}")
        print(f"Description: {metadata_data['description']}")
        print(f"Confidence: {metadata_data['confidence']:.2f}")

        print(f"\n--- Dublin Core ---")
        for key, value in metadata_data['dublin_core'].items():
            print(f"{key}: {value}")

        print(f"\n--- Schema.org ---")
        import json
        print(json.dumps(metadata_data['schema_org'], indent=2))

    test_file.unlink()
