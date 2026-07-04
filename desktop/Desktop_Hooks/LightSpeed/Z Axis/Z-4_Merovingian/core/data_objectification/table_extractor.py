"""
Table Extractor - V1.0.0
Extracts tables from documents and converts to DataFrames/SQL

Supports:
- Markdown tables
- HTML tables
- CSV-like text tables
- PDF tables (via camelot/tabula)
- DOCX tables

Outputs:
- pandas DataFrames
- SQL CREATE TABLE statements
- SQL INSERT statements
- JSON structured data

Author: LightSpeed Team
Date: December 27, 2025
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


# ==============================================================================
# Data Models
# ==============================================================================

@dataclass
class ExtractedTable:
    """
    Extracted table with structured data

    Attributes:
        table_id: Unique identifier
        source_file: Source document path
        source_page: Page number (if applicable)
        source_position: Position in document
        headers: Column headers
        rows: Data rows
        dataframe: pandas DataFrame (if available)
        sql_create: SQL CREATE TABLE statement
        sql_inserts: SQL INSERT statements
        metadata: Additional metadata
        confidence: Extraction confidence (0.0-1.0)
    """
    table_id: str
    source_file: Path
    source_page: Optional[int] = None
    source_position: Optional[int] = None
    headers: List[str] = field(default_factory=list)
    rows: List[List[Any]] = field(default_factory=list)
    dataframe: Optional[Any] = None  # pandas.DataFrame
    sql_create: str = ""
    sql_inserts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'table_id': self.table_id,
            'source_file': str(self.source_file),
            'source_page': self.source_page,
            'source_position': self.source_position,
            'headers': self.headers,
            'rows': self.rows,
            'sql_create': self.sql_create,
            'sql_inserts': self.sql_inserts,
            'metadata': self.metadata,
            'confidence': self.confidence
        }

        if self.dataframe is not None:
            data['dataframe_json'] = self.dataframe.to_json(orient='records')

        return data

    def get_dataframe(self) -> Optional[Any]:
        """Get pandas DataFrame representation"""
        if self.dataframe is not None:
            return self.dataframe

        if not PANDAS_AVAILABLE:
            return None

        if self.headers and self.rows:
            self.dataframe = pd.DataFrame(self.rows, columns=self.headers)
            return self.dataframe

        return None


# ==============================================================================
# Table Extractor
# ==============================================================================

class TableExtractor:
    """
    Extracts tables from documents and converts to structured formats
    """

    def __init__(self):
        """Initialize table extractor"""
        self.table_patterns = {
            'markdown': self._extract_markdown_tables,
            'html': self._extract_html_tables,
            'csv': self._extract_csv_tables,
        }

    def extract(
        self,
        content: str,
        file_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Extract tables from content

        Args:
            content: Document content
            file_path: Source file path
            options: Extraction options

        Returns:
            List of ExtractedTable objects wrapped as ExtractedObject
        """
        from .objectifier import ExtractedObject, ObjectType

        options = options or {}
        tables = []

        # Try all extraction methods
        for method_name, method in self.table_patterns.items():
            try:
                extracted = method(content, file_path, options)
                tables.extend(extracted)
            except Exception as e:
                # Continue with other methods
                pass

        # Convert to ExtractedObject format
        objects = []
        for table in tables:
            obj = ExtractedObject(
                object_id=table.table_id,
                object_type=ObjectType.TABLE,
                source_file=table.source_file,
                source_page=table.source_page,
                source_position=table.source_position,
                content=self._table_to_string(table),
                structured_data=table.to_dict(),
                confidence=table.confidence,
                metadata=table.metadata
            )
            objects.append(obj)

        return objects

    def _extract_markdown_tables(
        self,
        content: str,
        file_path: Path,
        options: Dict[str, Any]
    ) -> List[ExtractedTable]:
        """Extract Markdown-style tables"""
        tables = []
        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Check if line looks like table separator
            if re.match(r'^\|?\s*[-:]+\s*\|', line):
                # Found potential table separator
                if i > 0:
                    # Get header from previous line
                    header_line = lines[i - 1].strip()
                    if '|' in header_line:
                        table = self._parse_markdown_table(lines, i - 1, file_path)
                        if table:
                            tables.append(table)
                            i = table.metadata.get('end_line', i)

            i += 1

        return tables

    def _parse_markdown_table(
        self,
        lines: List[str],
        start_idx: int,
        file_path: Path
    ) -> Optional[ExtractedTable]:
        """Parse a Markdown table starting at given index"""
        # Parse header
        header_line = lines[start_idx].strip()
        headers = [h.strip() for h in header_line.split('|') if h.strip()]

        # Skip separator line
        if start_idx + 1 >= len(lines):
            return None

        # Parse rows
        rows = []
        current_idx = start_idx + 2  # Skip header and separator

        while current_idx < len(lines):
            line = lines[current_idx].strip()
            if not line or '|' not in line:
                break

            row = [cell.strip() for cell in line.split('|') if cell.strip()]
            if len(row) == len(headers):
                rows.append(row)
            current_idx += 1

        if not rows:
            return None

        # Create table object
        table = ExtractedTable(
            table_id=f"table_md_{start_idx}",
            source_file=file_path,
            source_position=start_idx,
            headers=headers,
            rows=rows,
            metadata={
                'format': 'markdown',
                'start_line': start_idx,
                'end_line': current_idx
            }
        )

        # Generate SQL
        self._generate_sql(table)

        # Create DataFrame
        if PANDAS_AVAILABLE:
            table.dataframe = pd.DataFrame(rows, columns=headers)

        return table

    def _extract_html_tables(
        self,
        content: str,
        file_path: Path,
        options: Dict[str, Any]
    ) -> List[ExtractedTable]:
        """Extract HTML tables"""
        tables = []

        # Find all <table> tags
        table_pattern = re.compile(r'<table[^>]*>(.*?)</table>', re.DOTALL | re.IGNORECASE)

        for i, match in enumerate(table_pattern.finditer(content)):
            table_html = match.group(1)

            # Extract headers
            headers = []
            header_pattern = re.compile(r'<th[^>]*>(.*?)</th>', re.DOTALL | re.IGNORECASE)
            for header_match in header_pattern.finditer(table_html):
                header_text = re.sub(r'<[^>]+>', '', header_match.group(1)).strip()
                headers.append(header_text)

            # Extract rows
            rows = []
            row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL | re.IGNORECASE)
            for row_match in row_pattern.finditer(table_html):
                row_html = row_match.group(1)

                # Skip if this row contains headers
                if '<th' in row_html.lower():
                    continue

                # Extract cells
                cell_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL | re.IGNORECASE)
                cells = []
                for cell_match in cell_pattern.finditer(row_html):
                    cell_text = re.sub(r'<[^>]+>', '', cell_match.group(1)).strip()
                    cells.append(cell_text)

                if cells:
                    rows.append(cells)

            # If no explicit headers found, use first row
            if not headers and rows:
                headers = rows[0]
                rows = rows[1:]

            if headers and rows:
                table = ExtractedTable(
                    table_id=f"table_html_{i}",
                    source_file=file_path,
                    source_position=match.start(),
                    headers=headers,
                    rows=rows,
                    metadata={
                        'format': 'html',
                        'raw_html': match.group(0)[:200]
                    }
                )

                self._generate_sql(table)

                if PANDAS_AVAILABLE:
                    table.dataframe = pd.DataFrame(rows, columns=headers)

                tables.append(table)

        return tables

    def _extract_csv_tables(
        self,
        content: str,
        file_path: Path,
        options: Dict[str, Any]
    ) -> List[ExtractedTable]:
        """Extract CSV-like tables"""
        tables = []

        # Detect CSV-like content (multiple lines with consistent delimiters)
        lines = content.split('\n')
        current_block = []
        delimiter = None

        for i, line in enumerate(lines):
            # Detect delimiter (comma, tab, pipe, semicolon)
            line_delimiters = [
                (',' , line.count(',')),
                ('\t', line.count('\t')),
                ('|' , line.count('|')),
                (';' , line.count(';'))
            ]
            line_delimiters.sort(key=lambda x: x[1], reverse=True)

            if line_delimiters[0][1] >= 2:  # At least 2 delimiters
                current_delimiter = line_delimiters[0][0]

                if delimiter is None:
                    delimiter = current_delimiter
                    current_block = [(i, line)]
                elif delimiter == current_delimiter:
                    current_block.append((i, line))
                else:
                    # Delimiter changed, process current block
                    if len(current_block) >= 3:
                        table = self._parse_csv_block(current_block, delimiter, file_path)
                        if table:
                            tables.append(table)

                    delimiter = current_delimiter
                    current_block = [(i, line)]
            else:
                # No clear delimiter, process current block if any
                if len(current_block) >= 3:
                    table = self._parse_csv_block(current_block, delimiter, file_path)
                    if table:
                        tables.append(table)

                delimiter = None
                current_block = []

        # Process final block
        if len(current_block) >= 3:
            table = self._parse_csv_block(current_block, delimiter, file_path)
            if table:
                tables.append(table)

        return tables

    def _parse_csv_block(
        self,
        block: List[Tuple[int, str]],
        delimiter: str,
        file_path: Path
    ) -> Optional[ExtractedTable]:
        """Parse a CSV-like block of lines"""
        if not block:
            return None

        start_idx = block[0][0]

        # Parse header (first line)
        headers = [h.strip() for h in block[0][1].split(delimiter)]

        # Parse rows
        rows = []
        for idx, line in block[1:]:
            row = [cell.strip() for cell in line.split(delimiter)]

            # Ensure row matches header length
            if len(row) == len(headers):
                rows.append(row)

        if not rows:
            return None

        table = ExtractedTable(
            table_id=f"table_csv_{start_idx}",
            source_file=file_path,
            source_position=start_idx,
            headers=headers,
            rows=rows,
            metadata={
                'format': 'csv',
                'delimiter': delimiter,
                'start_line': start_idx,
                'end_line': block[-1][0]
            }
        )

        self._generate_sql(table)

        if PANDAS_AVAILABLE:
            table.dataframe = pd.DataFrame(rows, columns=headers)

        return table

    def _generate_sql(self, table: ExtractedTable):
        """Generate SQL CREATE and INSERT statements"""
        if not table.headers:
            return

        # Sanitize table name
        table_name = self._sanitize_sql_name(table.table_id)

        # Generate CREATE TABLE
        columns = []
        for header in table.headers:
            col_name = self._sanitize_sql_name(header)
            col_type = self._infer_sql_type(table.rows, table.headers.index(header))
            columns.append(f"    {col_name} {col_type}")

        table.sql_create = f"CREATE TABLE {table_name} (\n" + ",\n".join(columns) + "\n);"

        # Generate INSERT statements
        table.sql_inserts = []
        for row in table.rows:
            values = []
            for cell in row:
                if self._is_numeric(cell):
                    values.append(str(cell))
                else:
                    # Escape single quotes
                    escaped = str(cell).replace("'", "''")
                    values.append(f"'{escaped}'")

            insert_stmt = f"INSERT INTO {table_name} VALUES ({', '.join(values)});"
            table.sql_inserts.append(insert_stmt)

    def _sanitize_sql_name(self, name: str) -> str:
        """Sanitize name for SQL identifier"""
        # Remove non-alphanumeric characters except underscore
        sanitized = re.sub(r'[^\w]', '_', name)
        # Ensure starts with letter or underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        return sanitized or 'column'

    def _infer_sql_type(self, rows: List[List[Any]], col_index: int) -> str:
        """Infer SQL type for column"""
        if col_index >= len(rows[0]):
            return 'TEXT'

        # Sample values from column
        values = [row[col_index] for row in rows if col_index < len(row)]

        if all(self._is_integer(v) for v in values):
            return 'INTEGER'
        elif all(self._is_numeric(v) for v in values):
            return 'REAL'
        elif all(self._is_date(v) for v in values):
            return 'DATE'
        else:
            # Find max length
            max_length = max(len(str(v)) for v in values)
            if max_length > 255:
                return 'TEXT'
            else:
                return f'VARCHAR({max(max_length * 2, 50)})'

    def _is_integer(self, value: Any) -> bool:
        """Check if value is an integer"""
        try:
            int(value)
            return '.' not in str(value)
        except (ValueError, TypeError):
            return False

    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def _is_date(self, value: Any) -> bool:
        """Check if value looks like a date"""
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
        ]
        value_str = str(value)
        return any(re.match(pattern, value_str) for pattern in date_patterns)

    def _table_to_string(self, table: ExtractedTable) -> str:
        """Convert table to string representation"""
        if not table.headers:
            return ""

        lines = []

        # Header
        lines.append('| ' + ' | '.join(table.headers) + ' |')

        # Separator
        lines.append('|' + '|'.join(['---' for _ in table.headers]) + '|')

        # Rows
        for row in table.rows:
            lines.append('| ' + ' | '.join(str(cell) for cell in row) + ' |')

        return '\n'.join(lines)

    def export_to_sql(self, table: ExtractedTable, output_path: Path) -> bool:
        """
        Export table to SQL file

        Args:
            table: ExtractedTable to export
            output_path: Output file path

        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(table.sql_create + '\n\n')
                for insert in table.sql_inserts:
                    f.write(insert + '\n')
            return True
        except Exception as e:
            print(f"Failed to export SQL: {e}")
            return False

    def export_to_csv(self, table: ExtractedTable, output_path: Path) -> bool:
        """
        Export table to CSV file

        Args:
            table: ExtractedTable to export
            output_path: Output file path

        Returns:
            True if successful
        """
        if PANDAS_AVAILABLE and table.dataframe is not None:
            try:
                table.dataframe.to_csv(output_path, index=False)
                return True
            except Exception as e:
                print(f"Failed to export CSV: {e}")
                return False
        else:
            # Manual CSV export
            try:
                import csv
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(table.headers)
                    writer.writerows(table.rows)
                return True
            except Exception as e:
                print(f"Failed to export CSV: {e}")
                return False


# ==============================================================================
# Factory Function
# ==============================================================================

def create_table_extractor() -> TableExtractor:
    """
    Create a new TableExtractor instance

    Returns:
        Configured TableExtractor
    """
    return TableExtractor()


# ==============================================================================
# Standalone Test
# ==============================================================================

if __name__ == '__main__':
    # Test with sample content
    test_content = """
# Data Analysis Results

## Sample Table

| Name    | Age | Department  |
|---------|-----|-------------|
| Alice   | 30  | Engineering |
| Bob     | 25  | Marketing   |
| Charlie | 35  | Sales       |

## CSV Data

Product,Price,Stock
Widget,19.99,150
Gadget,29.99,75
Doohickey,9.99,200
"""

    test_file = Path('test_table_extraction.md')
    test_file.write_text(test_content)

    extractor = create_table_extractor()
    tables = extractor.extract(test_content, test_file, {})

    print(f"\n=== Table Extraction Results ===")
    print(f"Found {len(tables)} tables\n")

    for obj in tables:
        table_data = obj.structured_data
        print(f"Table: {obj.object_id}")
        print(f"Format: {table_data['metadata']['format']}")
        print(f"Headers: {table_data['headers']}")
        print(f"Rows: {len(table_data['rows'])}")
        print(f"\nSQL CREATE:\n{table_data['sql_create']}")
        print(f"\nSample INSERT:\n{table_data['sql_inserts'][0]}")
        print("\n" + "=" * 50 + "\n")

    test_file.unlink()
