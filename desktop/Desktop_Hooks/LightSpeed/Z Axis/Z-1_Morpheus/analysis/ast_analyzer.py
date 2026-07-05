"""
Python AST Analyzer
LightSpeed Platform - Morpheus Floor (Z+2)

Analyzes Python code using Abstract Syntax Tree (AST) parsing.
Extracts functions, classes, imports, and calculates complexity metrics.

Author: LightSpeed Team / ACHILLES
Date: December 9, 2025
"""

import ast
import json
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from ..services import get_db, EventBus


@dataclass
class FunctionInfo:
    """Information about a function."""
    name: str
    lineno: int
    args: List[str]
    returns: Optional[str]
    decorators: List[str]
    docstring: Optional[str]
    complexity: int  # Cyclomatic complexity
    is_async: bool


@dataclass
class ClassInfo:
    """Information about a class."""
    name: str
    lineno: int
    bases: List[str]
    decorators: List[str]
    docstring: Optional[str]
    methods: List[FunctionInfo]


@dataclass
class ImportInfo:
    """Information about an import."""
    module: str
    names: List[str]  # Imported names (or ['*'] for import *)
    alias: Optional[str]
    lineno: int


@dataclass
class CodeAnalysis:
    """Complete code analysis result."""
    file_path: str
    language: str
    imports: List[ImportInfo]
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    global_variables: List[str]
    complexity: int  # Total complexity
    loc: int  # Lines of code
    docstring: Optional[str]  # Module docstring


class PythonASTAnalyzer:
    """
    Analyzes Python source code using AST parsing.

    Features:
    - Extract all functions with signatures and metadata
    - Extract all classes with methods and bases
    - Track all imports and dependencies
    - Calculate cyclomatic complexity
    - Count lines of code
    - Store analysis in database
    """

    def __init__(self):
        self.db = get_db()
        self.event_bus = EventBus()

    def analyze_file(self, file_path: str) -> Optional[CodeAnalysis]:
        """
        Analyze a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            CodeAnalysis object with extracted information
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            source_code = path.read_text(encoding='utf-8')
            tree = ast.parse(source_code, filename=str(path))

            # Extract module docstring
            docstring = ast.get_docstring(tree)

            # Extract imports
            imports = self._extract_imports(tree)

            # Extract functions
            functions = self._extract_functions(tree)

            # Extract classes
            classes = self._extract_classes(tree)

            # Extract global variables
            global_vars = self._extract_global_variables(tree)

            # Calculate metrics
            loc = len(source_code.splitlines())
            total_complexity = sum(f.complexity for f in functions)
            for cls in classes:
                total_complexity += sum(m.complexity for m in cls.methods)

            analysis = CodeAnalysis(
                file_path=str(path),
                language="python",
                imports=imports,
                functions=functions,
                classes=classes,
                global_variables=global_vars,
                complexity=total_complexity,
                loc=loc,
                docstring=docstring
            )

            return analysis

        except SyntaxError as e:
            # Log syntax error but don't crash
            return None
        except Exception as e:
            return None

    def analyze_and_store(self, file_path: str, file_id: Optional[int] = None) -> Optional[int]:
        """
        Analyze file and store results in database.

        Args:
            file_path: Path to Python file
            file_id: Optional file ID from files table

        Returns:
            ID of code_analysis record
        """
        analysis = self.analyze_file(file_path)
        if not analysis:
            return None

        # If no file_id provided, try to find it
        if file_id is None:
            file_id = self._get_file_id(file_path)

        if file_id is None:
            # Register file first
            file_id = self._register_file(file_path)

        # Store in database
        imports_json = json.dumps([asdict(imp) for imp in analysis.imports])
        functions_json = json.dumps([asdict(func) for func in analysis.functions])
        classes_json = json.dumps([asdict(cls) for cls in analysis.classes])

        query = """
            INSERT INTO code_analysis
            (file_id, language, imports, functions, classes, complexity, loc)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                query,
                (file_id, analysis.language, imports_json, functions_json,
                 classes_json, analysis.complexity, analysis.loc)
            )
            analysis_id = cursor.lastrowid
            conn.commit()

        # Emit event
        self.event_bus.publish('morpheus.code.analyzed', {
            'analysis_id': analysis_id,
            'file_id': file_id,
            'file_path': file_path,
            'complexity': analysis.complexity,
            'loc': analysis.loc
        })

        return analysis_id

    def get_analysis(self, file_id: int) -> Optional[CodeAnalysis]:
        """Get stored analysis for a file."""
        query = """
            SELECT ca.*, f.path
            FROM code_analysis ca
            JOIN files f ON ca.file_id = f.id
            WHERE ca.file_id = ?
            ORDER BY ca.analyzed_at DESC
            LIMIT 1
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (file_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_analysis(row)

    def search_functions(self, name_pattern: str) -> List[Dict]:
        """
        Search for functions by name pattern.

        Args:
            name_pattern: SQL LIKE pattern (e.g., "%analyze%")

        Returns:
            List of matching functions with file info
        """
        query = """
            SELECT ca.file_id, f.path, ca.functions
            FROM code_analysis ca
            JOIN files f ON ca.file_id = f.id
            WHERE ca.functions LIKE ?
        """

        results = []
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (f'%{name_pattern}%',))
            rows = cursor.fetchall()

        for row in rows:
            file_id, file_path, functions_json = row
            functions = json.loads(functions_json) if functions_json else []

            for func in functions:
                if name_pattern.lower() in func['name'].lower():
                    results.append({
                        'file_id': file_id,
                        'file_path': file_path,
                        'function': func
                    })

        return results

    def search_classes(self, name_pattern: str) -> List[Dict]:
        """Search for classes by name pattern."""
        query = """
            SELECT ca.file_id, f.path, ca.classes
            FROM code_analysis ca
            JOIN files f ON ca.file_id = f.id
            WHERE ca.classes LIKE ?
        """

        results = []
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (f'%{name_pattern}%',))
            rows = cursor.fetchall()

        for row in rows:
            file_id, file_path, classes_json = row
            classes = json.loads(classes_json) if classes_json else []

            for cls in classes:
                if name_pattern.lower() in cls['name'].lower():
                    results.append({
                        'file_id': file_id,
                        'file_path': file_path,
                        'class': cls
                    })

        return results

    def get_high_complexity_files(self, threshold: int = 20) -> List[Dict]:
        """Get files with complexity above threshold."""
        query = """
            SELECT ca.file_id, f.path, ca.complexity, ca.loc
            FROM code_analysis ca
            JOIN files f ON ca.file_id = f.id
            WHERE ca.complexity > ?
            ORDER BY ca.complexity DESC
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (threshold,))
            rows = cursor.fetchall()

        return [
            {
                'file_id': row[0],
                'file_path': row[1],
                'complexity': row[2],
                'loc': row[3]
            }
            for row in rows
        ]

    def _extract_imports(self, tree: ast.AST) -> List[ImportInfo]:
        """Extract all imports from AST."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[alias.name],
                        alias=alias.asname,
                        lineno=node.lineno
                    ))

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                names = [alias.name for alias in node.names]
                imports.append(ImportInfo(
                    module=module,
                    names=names,
                    alias=None,
                    lineno=node.lineno
                ))

        return imports

    def _extract_functions(self, tree: ast.AST, top_level_only: bool = True) -> List[FunctionInfo]:
        """Extract all functions from AST."""
        functions = []

        nodes = tree.body if top_level_only else ast.walk(tree)

        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._analyze_function(node))

        return functions

    def _extract_classes(self, tree: ast.AST) -> List[ClassInfo]:
        """Extract all classes from AST."""
        classes = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes.append(self._analyze_class(node))

        return classes

    def _extract_global_variables(self, tree: ast.AST) -> List[str]:
        """Extract global variable assignments."""
        variables = []

        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append(target.id)

        return variables

    def _analyze_function(self, node: ast.FunctionDef) -> FunctionInfo:
        """Analyze a function node."""
        # Extract arguments
        args = [arg.arg for arg in node.args.args]

        # Extract return annotation
        returns = None
        if node.returns:
            returns = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)

        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)

        # Get docstring
        docstring = ast.get_docstring(node)

        # Calculate complexity
        complexity = self._calculate_complexity(node)

        return FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            args=args,
            returns=returns,
            decorators=decorators,
            docstring=docstring,
            complexity=complexity,
            is_async=isinstance(node, ast.AsyncFunctionDef)
        )

    def _analyze_class(self, node: ast.ClassDef) -> ClassInfo:
        """Analyze a class node."""
        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)

        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)

        # Get docstring
        docstring = ast.get_docstring(node)

        # Extract methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._analyze_function(item))

        return ClassInfo(
            name=node.name,
            lineno=node.lineno,
            bases=bases,
            decorators=decorators,
            docstring=docstring,
            methods=methods
        )

    def _calculate_complexity(self, node: ast.AST) -> int:
        """
        Calculate cyclomatic complexity.

        Complexity increases for:
        - if/elif statements
        - for/while loops
        - try/except blocks
        - boolean operators (and/or)
        - comprehensions
        """
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1

        return complexity

    def _get_file_id(self, file_path: str) -> Optional[int]:
        """Get file ID from files table."""
        query = "SELECT id FROM files WHERE path = ?"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (file_path,))
            row = cursor.fetchone()

        return row[0] if row else None

    def _register_file(self, file_path: str) -> int:
        """Register file in files table."""
        path = Path(file_path)

        query = """
            INSERT INTO files (path, name, extension, size_bytes, hash_sha256, status)
            VALUES (?, ?, ?, ?, '', 'analyzed')
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                query,
                (str(path), path.name, path.suffix, path.stat().st_size)
            )
            file_id = cursor.lastrowid
            conn.commit()

        return file_id

    def _row_to_analysis(self, row) -> CodeAnalysis:
        """Convert database row to CodeAnalysis."""
        imports = [ImportInfo(**imp) for imp in json.loads(row[2])] if row[2] else []
        functions = [FunctionInfo(**func) for func in json.loads(row[3])] if row[3] else []
        classes_data = json.loads(row[4]) if row[4] else []
        classes = []
        for cls_dict in classes_data:
            cls_dict['methods'] = [FunctionInfo(**m) for m in cls_dict.get('methods', [])]
            classes.append(ClassInfo(**cls_dict))

        return CodeAnalysis(
            file_path=row[8],  # From JOIN with files table
            language=row[1],
            imports=imports,
            functions=functions,
            classes=classes,
            global_variables=[],  # Not stored in current schema
            complexity=row[5],
            loc=row[6],
            docstring=None  # Not stored in current schema
        )
