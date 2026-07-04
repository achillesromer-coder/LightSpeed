"""
Citation Extractor - V1.0.0
Extracts citations from documents and converts to BibTeX/RIS formats

Supports:
- IEEE style citations
- APA style citations
- MLA style citations
- Chicago style citations
- Numbered citations [1], [2], etc.
- Author-year citations (Smith, 2020)
- DOI/URL extraction
- arXiv references

Outputs:
- BibTeX entries
- RIS format
- JSON structured data
- Dublin Core metadata

Author: LightSpeed Team
Date: December 27, 2025
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ==============================================================================
# Citation Formats
# ==============================================================================

class CitationFormat(Enum):
    """Supported citation formats"""
    BIBTEX = "bibtex"
    RIS = "ris"
    JSON = "json"
    DUBLIN_CORE = "dublin_core"


class CitationType(Enum):
    """Types of citations"""
    ARTICLE = "article"
    BOOK = "book"
    INPROCEEDINGS = "inproceedings"
    PHDTHESIS = "phdthesis"
    MASTERSTHESIS = "mastersthesis"
    TECHREPORT = "techreport"
    MISC = "misc"
    ONLINE = "online"
    UNPUBLISHED = "unpublished"


# ==============================================================================
# Data Models
# ==============================================================================

@dataclass
class ExtractedCitation:
    """
    Extracted citation with structured data

    Attributes:
        citation_id: Unique identifier
        source_file: Source document path
        source_page: Page number (if applicable)
        source_position: Position in document
        raw_text: Raw citation text
        citation_type: Type of publication
        authors: List of authors
        title: Publication title
        year: Publication year
        venue: Journal/conference name
        volume: Volume number
        pages: Page range
        doi: DOI identifier
        url: URL
        bibtex: BibTeX formatted entry
        ris: RIS formatted entry
        dublin_core: Dublin Core metadata
        confidence: Extraction confidence (0.0-1.0)
        metadata: Additional metadata
    """
    citation_id: str
    source_file: Path
    source_page: Optional[int] = None
    source_position: Optional[int] = None
    raw_text: str = ""
    citation_type: CitationType = CitationType.MISC
    authors: List[str] = field(default_factory=list)
    title: str = ""
    year: Optional[int] = None
    venue: str = ""
    volume: str = ""
    pages: str = ""
    doi: str = ""
    url: str = ""
    publisher: str = ""
    booktitle: str = ""
    organization: str = ""
    institution: str = ""
    bibtex: str = ""
    ris: str = ""
    dublin_core: Dict[str, str] = field(default_factory=dict)
    confidence: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'citation_id': self.citation_id,
            'source_file': str(self.source_file),
            'source_page': self.source_page,
            'source_position': self.source_position,
            'raw_text': self.raw_text,
            'citation_type': self.citation_type.value,
            'authors': self.authors,
            'title': self.title,
            'year': self.year,
            'venue': self.venue,
            'volume': self.volume,
            'pages': self.pages,
            'doi': self.doi,
            'url': self.url,
            'publisher': self.publisher,
            'bibtex': self.bibtex,
            'ris': self.ris,
            'dublin_core': self.dublin_core,
            'confidence': self.confidence,
            'metadata': self.metadata
        }


# ==============================================================================
# Citation Extractor
# ==============================================================================

class CitationExtractor:
    """
    Extracts citations from documents and converts to standard formats
    """

    def __init__(self):
        """Initialize citation extractor"""
        # Compile regex patterns
        self.doi_pattern = re.compile(r'10\.\d{4,}/[\w\-\.]+')
        self.arxiv_pattern = re.compile(r'arXiv:(\d{4}\.\d{4,5})')
        self.url_pattern = re.compile(r'https?://[^\s\)]+')

        # Citation style patterns
        self.ieee_pattern = re.compile(
            r'\[(\d+)\]\s+([A-Z][\w\s,\.]+),\s*"([^"]+)",\s*([^,]+),\s*(\d{4})'
        )

        self.author_year_pattern = re.compile(
            r'([A-Z][\w\-]+(?:\s+and\s+[A-Z][\w\-]+)*)\s*\((\d{4})\)'
        )

    def extract(
        self,
        content: str,
        file_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Extract citations from content

        Args:
            content: Document content
            file_path: Source file path
            options: Extraction options

        Returns:
            List of ExtractedCitation objects wrapped as ExtractedObject
        """
        from .objectifier import ExtractedObject, ObjectType

        options = options or {}
        citations = []

        # Extract numbered citations
        citations.extend(self._extract_numbered_citations(content, file_path))

        # Extract author-year citations
        citations.extend(self._extract_author_year_citations(content, file_path))

        # Extract bibliography section
        citations.extend(self._extract_bibliography(content, file_path))

        # Convert to ExtractedObject format
        objects = []
        for citation in citations:
            # Generate formatted outputs
            self._generate_bibtex(citation)
            self._generate_ris(citation)
            self._generate_dublin_core(citation)

            obj = ExtractedObject(
                object_id=citation.citation_id,
                object_type=ObjectType.CITATION,
                source_file=citation.source_file,
                source_page=citation.source_page,
                source_position=citation.source_position,
                content=citation.raw_text,
                structured_data=citation.to_dict(),
                confidence=citation.confidence,
                metadata=citation.metadata
            )
            objects.append(obj)

        return objects

    def _extract_numbered_citations(
        self,
        content: str,
        file_path: Path
    ) -> List[ExtractedCitation]:
        """Extract numbered citations like [1], [2], etc."""
        citations = []

        # Find references section
        ref_section = self._find_references_section(content)
        if not ref_section:
            return citations

        # Extract individual references
        lines = ref_section.split('\n')
        current_citation = None
        current_text = []

        for i, line in enumerate(lines):
            # Check for numbered reference
            match = re.match(r'^\[(\d+)\]\s+(.+)$', line.strip())
            if match:
                # Save previous citation
                if current_citation:
                    current_citation.raw_text = ' '.join(current_text)
                    self._parse_citation_text(current_citation)
                    citations.append(current_citation)

                # Start new citation
                ref_num = match.group(1)
                ref_text = match.group(2)

                current_citation = ExtractedCitation(
                    citation_id=f"cite_{ref_num}",
                    source_file=file_path,
                    source_position=i,
                    metadata={'reference_number': int(ref_num)}
                )
                current_text = [ref_text]
            elif current_citation and line.strip():
                # Continuation of previous citation
                current_text.append(line.strip())

        # Save final citation
        if current_citation:
            current_citation.raw_text = ' '.join(current_text)
            self._parse_citation_text(current_citation)
            citations.append(current_citation)

        return citations

    def _extract_author_year_citations(
        self,
        content: str,
        file_path: Path
    ) -> List[ExtractedCitation]:
        """Extract author-year style citations"""
        citations = []

        for i, match in enumerate(self.author_year_pattern.finditer(content)):
            authors_str = match.group(1)
            year = int(match.group(2))

            # Parse authors
            authors = [a.strip() for a in re.split(r'\s+and\s+|\s*,\s*', authors_str)]

            citation = ExtractedCitation(
                citation_id=f"cite_ay_{i}",
                source_file=file_path,
                source_position=match.start(),
                raw_text=match.group(0),
                authors=authors,
                year=year,
                confidence=0.7,
                metadata={'style': 'author-year'}
            )

            citations.append(citation)

        return citations

    def _extract_bibliography(
        self,
        content: str,
        file_path: Path
    ) -> List[ExtractedCitation]:
        """Extract citations from bibliography section"""
        citations = []

        # Find bibliography section
        bib_section = self._find_bibliography_section(content)
        if not bib_section:
            return citations

        # Split into individual entries
        # Look for patterns like author names at start of line
        entries = []
        current_entry = []

        for line in bib_section.split('\n'):
            line = line.strip()
            if not line:
                if current_entry:
                    entries.append(' '.join(current_entry))
                    current_entry = []
            elif re.match(r'^[A-Z][\w\-]+,\s+[A-Z]', line):
                # New entry starting with author name
                if current_entry:
                    entries.append(' '.join(current_entry))
                current_entry = [line]
            else:
                current_entry.append(line)

        if current_entry:
            entries.append(' '.join(current_entry))

        # Parse each entry
        for i, entry_text in enumerate(entries):
            citation = ExtractedCitation(
                citation_id=f"cite_bib_{i}",
                source_file=file_path,
                raw_text=entry_text,
                metadata={'style': 'bibliography'}
            )

            self._parse_citation_text(citation)
            citations.append(citation)

        return citations

    def _find_references_section(self, content: str) -> Optional[str]:
        """Find the references/bibliography section"""
        # Common section headers
        headers = [
            r'^#+\s*References\s*$',
            r'^#+\s*Bibliography\s*$',
            r'^References\s*$',
            r'^Bibliography\s*$',
            r'^REFERENCES\s*$',
            r'^BIBLIOGRAPHY\s*$'
        ]

        lines = content.split('\n')
        for i, line in enumerate(lines):
            if any(re.match(pattern, line.strip()) for pattern in headers):
                return '\n'.join(lines[i+1:])

        return None

    def _find_bibliography_section(self, content: str) -> Optional[str]:
        """Alias for _find_references_section"""
        return self._find_references_section(content)

    def _parse_citation_text(self, citation: ExtractedCitation):
        """
        Parse citation text to extract structured fields

        Updates citation object in-place
        """
        text = citation.raw_text

        # Extract DOI
        doi_match = self.doi_pattern.search(text)
        if doi_match:
            citation.doi = doi_match.group(0)
            citation.confidence = min(citation.confidence + 0.2, 1.0)

        # Extract arXiv
        arxiv_match = self.arxiv_pattern.search(text)
        if arxiv_match:
            citation.url = f"https://arxiv.org/abs/{arxiv_match.group(1)}"
            citation.metadata['arxiv_id'] = arxiv_match.group(1)
            citation.confidence = min(citation.confidence + 0.2, 1.0)

        # Extract URL
        url_match = self.url_pattern.search(text)
        if url_match and not citation.url:
            citation.url = url_match.group(0)

        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match and not citation.year:
            citation.year = int(year_match.group(0))

        # Extract title (in quotes)
        title_match = re.search(r'"([^"]+)"', text)
        if title_match:
            citation.title = title_match.group(1)
            citation.confidence = min(citation.confidence + 0.15, 1.0)

        # Extract authors (before year or title)
        if not citation.authors:
            self._extract_authors(citation, text)

        # Extract venue (after title, before year)
        self._extract_venue(citation, text)

        # Extract volume and pages
        self._extract_volume_pages(citation, text)

        # Infer citation type
        self._infer_citation_type(citation, text)

    def _extract_authors(self, citation: ExtractedCitation, text: str):
        """Extract author names from citation text"""
        # Common patterns for author names
        # Last, F. M. and Last2, F. M.
        # F. M. Last and F. M. Last2

        # Split by common separators
        parts = re.split(r'[,\.]', text)

        authors = []
        for part in parts[:5]:  # Check first few parts
            part = part.strip()

            # Check if looks like author name
            if re.match(r'^[A-Z][\w\-]+(?:\s+[A-Z]\.?)+$', part):
                # Last, F. M. format
                authors.append(part)
            elif re.match(r'^[A-Z]\.\s*[A-Z]\.\s*[A-Z][\w\-]+$', part):
                # F. M. Last format
                authors.append(part)

            if len(authors) >= 3:  # Reasonable limit
                break

        if authors:
            citation.authors = authors

    def _extract_venue(self, citation: ExtractedCitation, text: str):
        """Extract publication venue"""
        # Look for italicized text or text after title
        if citation.title:
            # Get text after title
            title_pos = text.find(citation.title)
            if title_pos != -1:
                after_title = text[title_pos + len(citation.title):]

                # Extract venue (before year or volume)
                venue_match = re.search(r'[,\s]+([^,\d]+?)(?:[,\s]+(?:vol|pp|\d{4}))', after_title)
                if venue_match:
                    citation.venue = venue_match.group(1).strip()

    def _extract_volume_pages(self, citation: ExtractedCitation, text: str):
        """Extract volume and page numbers"""
        # Volume: vol. 10, volume 10, v. 10
        vol_match = re.search(r'vol(?:ume|\.)?\s*(\d+)', text, re.IGNORECASE)
        if vol_match:
            citation.volume = vol_match.group(1)

        # Pages: pp. 10-20, pages 10-20, p. 10
        pages_match = re.search(r'pp?\.\s*(\d+(?:-\d+)?)', text, re.IGNORECASE)
        if pages_match:
            citation.pages = pages_match.group(1)

    def _infer_citation_type(self, citation: ExtractedCitation, text: str):
        """Infer the type of citation"""
        text_lower = text.lower()

        if 'phd' in text_lower or 'ph.d' in text_lower or 'dissertation' in text_lower:
            citation.citation_type = CitationType.PHDTHESIS
        elif 'master' in text_lower or "master's" in text_lower or 'thesis' in text_lower:
            citation.citation_type = CitationType.MASTERSTHESIS
        elif 'proc.' in text_lower or 'proceedings' in text_lower or 'conference' in text_lower:
            citation.citation_type = CitationType.INPROCEEDINGS
        elif 'tech' in text_lower and 'report' in text_lower:
            citation.citation_type = CitationType.TECHREPORT
        elif 'book' in text_lower or 'publisher' in text_lower:
            citation.citation_type = CitationType.BOOK
        elif citation.venue or 'journal' in text_lower:
            citation.citation_type = CitationType.ARTICLE
        elif citation.url or 'online' in text_lower or 'website' in text_lower:
            citation.citation_type = CitationType.ONLINE
        else:
            citation.citation_type = CitationType.MISC

    def _generate_bibtex(self, citation: ExtractedCitation):
        """Generate BibTeX entry"""
        # Generate citation key
        if citation.authors and citation.year:
            first_author = citation.authors[0].split()[-1]  # Last name
            key = f"{first_author.lower()}{citation.year}"
        else:
            key = citation.citation_id

        # Build entry
        entry_type = citation.citation_type.value
        lines = [f"@{entry_type}{{{key},"]

        if citation.authors:
            authors_str = ' and '.join(citation.authors)
            lines.append(f"  author = {{{authors_str}}},")

        if citation.title:
            lines.append(f"  title = {{{citation.title}}},")

        if citation.year:
            lines.append(f"  year = {{{citation.year}}},")

        if citation.venue:
            if citation.citation_type == CitationType.ARTICLE:
                lines.append(f"  journal = {{{citation.venue}}},")
            elif citation.citation_type == CitationType.INPROCEEDINGS:
                lines.append(f"  booktitle = {{{citation.venue}}},")
            else:
                lines.append(f"  publisher = {{{citation.venue}}},")

        if citation.volume:
            lines.append(f"  volume = {{{citation.volume}}},")

        if citation.pages:
            lines.append(f"  pages = {{{citation.pages}}},")

        if citation.doi:
            lines.append(f"  doi = {{{citation.doi}}},")

        if citation.url:
            lines.append(f"  url = {{{citation.url}}},")

        lines.append("}")

        citation.bibtex = '\n'.join(lines)

    def _generate_ris(self, citation: ExtractedCitation):
        """Generate RIS format entry"""
        type_map = {
            CitationType.ARTICLE: 'JOUR',
            CitationType.BOOK: 'BOOK',
            CitationType.INPROCEEDINGS: 'CONF',
            CitationType.PHDTHESIS: 'THES',
            CitationType.MASTERSTHESIS: 'THES',
            CitationType.TECHREPORT: 'RPRT',
            CitationType.MISC: 'GEN',
            CitationType.ONLINE: 'ELEC',
        }

        lines = [f"TY  - {type_map.get(citation.citation_type, 'GEN')}"]

        for author in citation.authors:
            lines.append(f"AU  - {author}")

        if citation.title:
            lines.append(f"TI  - {citation.title}")

        if citation.year:
            lines.append(f"PY  - {citation.year}")

        if citation.venue:
            if citation.citation_type == CitationType.ARTICLE:
                lines.append(f"JO  - {citation.venue}")
            else:
                lines.append(f"PB  - {citation.venue}")

        if citation.volume:
            lines.append(f"VL  - {citation.volume}")

        if citation.pages:
            lines.append(f"SP  - {citation.pages.split('-')[0]}")
            if '-' in citation.pages:
                lines.append(f"EP  - {citation.pages.split('-')[1]}")

        if citation.doi:
            lines.append(f"DO  - {citation.doi}")

        if citation.url:
            lines.append(f"UR  - {citation.url}")

        lines.append("ER  -")

        citation.ris = '\n'.join(lines)

    def _generate_dublin_core(self, citation: ExtractedCitation):
        """Generate Dublin Core metadata"""
        dc = {}

        if citation.title:
            dc['dc.title'] = citation.title

        if citation.authors:
            for i, author in enumerate(citation.authors):
                dc[f'dc.creator.{i+1}'] = author

        if citation.year:
            dc['dc.date'] = str(citation.year)

        if citation.venue:
            dc['dc.publisher'] = citation.venue

        if citation.citation_type:
            dc['dc.type'] = citation.citation_type.value

        if citation.doi:
            dc['dc.identifier'] = f"doi:{citation.doi}"
        elif citation.url:
            dc['dc.identifier'] = citation.url

        dc['dc.format'] = 'text'
        dc['dc.language'] = 'en'

        citation.dublin_core = dc


# ==============================================================================
# Factory Function
# ==============================================================================

def create_citation_extractor() -> CitationExtractor:
    """
    Create a new CitationExtractor instance

    Returns:
        Configured CitationExtractor
    """
    return CitationExtractor()


# ==============================================================================
# Standalone Test
# ==============================================================================

if __name__ == '__main__':
    test_content = """
# Research Paper

## References

[1] Smith, J. and Jones, A., "Deep Learning for Robotics", IEEE Transactions on Robotics, vol. 35, pp. 123-145, 2020. doi: 10.1109/TRO.2020.123456

[2] Brown, R., "Machine Learning Fundamentals", MIT Press, 2019.

[3] Davis, L. et al., "Neural Networks in Space", Proceedings of International Conference on AI, pp. 45-67, 2021.

## Additional Citations

According to Johnson (2018), this approach has been widely adopted.
"""

    test_file = Path('test_citation_extraction.md')
    test_file.write_text(test_content)

    extractor = create_citation_extractor()
    citations = extractor.extract(test_content, test_file, {})

    print(f"\n=== Citation Extraction Results ===")
    print(f"Found {len(citations)} citations\n")

    for obj in citations:
        citation_data = obj.structured_data
        print(f"Citation: {obj.object_id}")
        print(f"Authors: {citation_data['authors']}")
        print(f"Title: {citation_data['title']}")
        print(f"Year: {citation_data['year']}")
        print(f"Type: {citation_data['citation_type']}")
        print(f"Confidence: {citation_data['confidence']:.2f}")
        print(f"\nBibTeX:\n{citation_data['bibtex']}")
        print("\n" + "=" * 50 + "\n")

    test_file.unlink()
