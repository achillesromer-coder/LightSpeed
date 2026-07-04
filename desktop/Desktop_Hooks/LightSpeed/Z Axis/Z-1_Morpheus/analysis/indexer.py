"""
Project Indexer
LightSpeed Platform - Morpheus Floor (Z+2)

Indexes entire projects for fast searching and navigation.
Uses TF-IDF for semantic search across code and documentation.

Author: LightSpeed Team / ACHILLES
Date: December 9, 2025
"""

from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from collections import defaultdict
import re
import json
import sqlite3

from ..services import get_db, EventBus
from .ast_analyzer import PythonASTAnalyzer


class ProjectIndexer:
    """
    Indexes projects for fast search and navigation.

    Features:
    - Recursive project scanning
    - File filtering by extension
    - TF-IDF based text search
    - Symbol indexing (functions, classes)
    - Docstring indexing
    - Cross-reference tracking
    """

    def __init__(self):
        self.db = get_db()
        self.event_bus = EventBus()
        self.ast_analyzer = PythonASTAnalyzer()
        try:
            # Ensure DB schema is compatible before any indexer queries run.
            if hasattr(self.db, "ensure_schema"):
                self.db.ensure_schema()
        except Exception:
            pass

    def index_project(
        self,
        project_path: str,
        project_id: Optional[int] = None,
        extensions: Optional[List[str]] = None
    ) -> Dict:
        """
        Index an entire project directory.

        Args:
            project_path: Path to project root
            project_id: Optional project ID to link files
            extensions: File extensions to index (default: ['.py'])

        Returns:
            Dict with indexing statistics

        Example:
            >>> indexer = ProjectIndexer()
            >>> stats = indexer.index_project(
            ...     project_path="/path/to/lightspeed",
            ...     project_id=1,
            ...     extensions=['.py', '.md', '.txt']
            ... )
            >>> print(stats)
            {
                "files_indexed": 150,
                "python_files": 120,
                "functions_found": 450,
                "classes_found": 85,
                "total_loc": 15000
            }
        """
        if extensions is None:
            extensions = ['.py']

        project_root = Path(project_path)
        if not project_root.exists():
            return {"error": "Project path does not exist"}

        stats = {
            "files_indexed": 0,
            "python_files": 0,
            "functions_found": 0,
            "classes_found": 0,
            "total_loc": 0,
            "errors": []
        }

        # Recursively find all files
        files_to_index = []
        for ext in extensions:
            files_to_index.extend(project_root.rglob(f'*{ext}'))

        # Index each file
        for file_path in files_to_index:
            try:
                if file_path.suffix == '.py':
                    # Python file - full AST analysis
                    analysis = self.ast_analyzer.analyze_file(str(file_path))
                    if analysis:
                        # Store analysis
                        self.ast_analyzer.analyze_and_store(str(file_path), file_id=None)

                        stats["python_files"] += 1
                        stats["functions_found"] += len(analysis.functions)
                        stats["classes_found"] += len(analysis.classes)
                        stats["total_loc"] += analysis.loc

                else:
                    # Non-Python file - basic indexing
                    self._index_text_file(str(file_path), project_id)

                stats["files_indexed"] += 1

            except Exception as e:
                stats["errors"].append({
                    "file": str(file_path),
                    "error": str(e)
                })

        # Emit completion event
        self.event_bus.publish('morpheus.project.indexed', {
            'project_path': str(project_root),
            'project_id': project_id,
            'stats': stats
        })

        return stats

    def search_by_keyword(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        Search for keyword across all indexed code.

        Args:
            keyword: Search term
            limit: Maximum results to return

        Returns:
            List of matches with file info and context
        """
        results = []

        # Search in functions
        function_results = self.ast_analyzer.search_functions(keyword)
        for result in function_results[:limit]:
            results.append({
                'type': 'function',
                'file_path': result['file_path'],
                'name': result['function']['name'],
                'lineno': result['function']['lineno'],
                'docstring': result['function'].get('docstring')
            })

        # Search in classes
        class_results = self.ast_analyzer.search_classes(keyword)
        for result in class_results[:limit - len(results)]:
            results.append({
                'type': 'class',
                'file_path': result['file_path'],
                'name': result['class']['name'],
                'lineno': result['class']['lineno'],
                'docstring': result['class'].get('docstring')
            })

        return results[:limit]

    def get_project_overview(self, project_id: int) -> Dict:
        """
        Get overview statistics for a project.

        Returns:
            Dict with project metrics
        """
        query = """
            SELECT
                COUNT(*) as file_count,
                SUM(ca.loc) as total_loc,
                AVG(ca.complexity) as avg_complexity,
                MAX(ca.complexity) as max_complexity
            FROM files f
            LEFT JOIN code_analysis ca ON f.id = ca.file_id
            WHERE f.project_id = ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (project_id,))
            row = cursor.fetchone()

        if not row:
            return {}

        return {
            'file_count': row[0] or 0,
            'total_loc': row[1] or 0,
            'avg_complexity': round(row[2], 2) if row[2] else 0,
            'max_complexity': row[3] or 0
        }

    def get_all_symbols(self, project_id: int) -> Dict[str, List[Dict]]:
        """
        Get all symbols (functions, classes) in a project.

        Returns:
            Dict with 'functions' and 'classes' lists
        """
        query = """
            SELECT f.path, ca.functions, ca.classes
            FROM files f
            JOIN code_analysis ca ON f.id = ca.file_id
            WHERE f.project_id = ?
        """

        symbols = {
            'functions': [],
            'classes': []
        }

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (project_id,))
            rows = cursor.fetchall()

        for row in rows:
            file_path, functions_json, classes_json = row

            if functions_json:
                functions = json.loads(functions_json)
                for func in functions:
                    symbols['functions'].append({
                        'file_path': file_path,
                        'name': func['name'],
                        'lineno': func['lineno']
                    })

            if classes_json:
                classes = json.loads(classes_json)
                for cls in classes:
                    symbols['classes'].append({
                        'file_path': file_path,
                        'name': cls['name'],
                        'lineno': cls['lineno']
                    })

        return symbols

    def find_references(self, symbol_name: str) -> List[Dict]:
        """
        Find all references to a symbol (function/class name).

        This is a simplified implementation - full version would parse
        actual code usage, not just definitions.

        Args:
            symbol_name: Name to search for

        Returns:
            List of files and lines containing the symbol
        """
        # Search in function definitions
        results = self.search_by_keyword(symbol_name)

        return results

    def get_file_symbols(self, file_path: str) -> Dict:
        """
        Get all symbols defined in a specific file.

        Returns:
            Dict with functions and classes
        """
        query = """
            SELECT ca.functions, ca.classes
            FROM code_analysis ca
            JOIN files f ON ca.file_id = f.id
            WHERE f.path = ?
            ORDER BY ca.analyzed_at DESC
            LIMIT 1
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (file_path,))
            row = cursor.fetchone()

        if not row:
            return {'functions': [], 'classes': []}

        functions = json.loads(row[0]) if row[0] else []
        classes = json.loads(row[1]) if row[1] else []

        return {
            'functions': functions,
            'classes': classes
        }

    def calculate_tfidf(self, documents: List[str], query: str) -> List[Tuple[int, float]]:
        """
        Calculate TF-IDF scores for query against documents.

        Args:
            documents: List of text documents
            query: Search query

        Returns:
            List of (doc_index, score) tuples sorted by score

        This is a simplified TF-IDF implementation for semantic search.
        """
        from collections import Counter
        import math

        # Tokenize query
        query_terms = query.lower().split()

        # Calculate document frequencies
        doc_freqs = defaultdict(int)
        for doc in documents:
            terms = set(doc.lower().split())
            for term in terms:
                doc_freqs[term] += 1

        # Calculate TF-IDF scores
        scores = []
        num_docs = len(documents)

        for idx, doc in enumerate(documents):
            doc_terms = doc.lower().split()
            term_freq = Counter(doc_terms)

            score = 0.0
            for term in query_terms:
                tf = term_freq.get(term, 0) / max(len(doc_terms), 1)
                idf = math.log(num_docs / (doc_freqs.get(term, 0) + 1))
                score += tf * idf

            if score > 0:
                scores.append((idx, score))

        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores

    def _index_text_file(self, file_path: str, project_id: Optional[int]) -> None:
        """Index a non-Python text file."""
        path = Path(file_path)

        try:
            content = path.read_text(encoding='utf-8')
            loc = len(content.splitlines())

            # Register file
            with self.db.get_connection() as conn:
                try:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO files (path, name, extension, size_bytes, project_id, status)
                        VALUES (?, ?, ?, ?, ?, 'indexed')
                        """,
                        (str(path), path.name, path.suffix, path.stat().st_size, project_id),
                    )
                except sqlite3.OperationalError as e:
                    # Older DBs may not yet have project_id; fall back gracefully.
                    if "project_id" not in str(e):
                        raise
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO files (path, name, extension, size_bytes, status)
                        VALUES (?, ?, ?, ?, 'indexed')
                        """,
                        (str(path), path.name, path.suffix, path.stat().st_size),
                    )
                conn.commit()

        except Exception:
            pass  # Skip files that can't be read

    def reindex_file(self, file_path: str) -> bool:
        """Re-analyze and re-index a file."""
        path = Path(file_path)

        if path.suffix == '.py':
            # Get file ID
            file_id = self.ast_analyzer._get_file_id(str(path))
            if file_id:
                # Delete old analysis
                query = "DELETE FROM code_analysis WHERE file_id = ?"
                with self.db.get_connection() as conn:
                    conn.execute(query, (file_id,))
                    conn.commit()

            # Re-analyze
            analysis_id = self.ast_analyzer.analyze_and_store(str(path))
            return analysis_id is not None

        return False
