"""
Code Extractor - V1.0.0
Extracts code blocks from documents and generates AST representations

Supports:
- Python (full AST with ast module)
- JavaScript/TypeScript
- Java
- C/C++
- Markdown fenced code blocks
- Inline code snippets
- Jupyter notebook cells

Outputs:
- Abstract Syntax Trees (AST)
- Code structure analysis
- Function/class definitions
- Import statements
- Complexity metrics
- Documentation extraction

Author: LightSpeed Team
Date: December 27, 2025
"""

import re
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


# ==============================================================================
# Code Languages
# ==============================================================================

class CodeLanguage(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    R = "r"
    MATLAB = "matlab"
    SQL = "sql"
    SHELL = "shell"
    UNKNOWN = "unknown"


# ==============================================================================
# Data Models
# ==============================================================================

@dataclass
class CodeEntity:
    """
    Represents a code entity (function, class, etc.)

    Attributes:
        name: Entity name
        type: Entity type (function, class, method, etc.)
        start_line: Starting line number
        end_line: Ending line number
        docstring: Documentation string
        parameters: Function parameters
        return_type: Return type annotation
        decorators: List of decorators
        complexity: Cyclomatic complexity
    """
    name: str
    type: str
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    complexity: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'type': self.type,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'docstring': self.docstring,
            'parameters': self.parameters,
            'return_type': self.return_type,
            'decorators': self.decorators,
            'complexity': self.complexity
        }


@dataclass
class ExtractedCode:
    """
    Extracted code block with analysis

    Attributes:
        code_id: Unique identifier
        source_file: Source document path
        source_position: Position in document
        language: Programming language
        code: Raw code text
        ast_tree: AST representation (if available)
        entities: List of code entities (functions, classes)
        imports: Import statements
        complexity: Overall complexity metric
        lines_of_code: Number of lines
        metadata: Additional metadata
    """
    code_id: str
    source_file: Path
    source_position: Optional[int] = None
    language: CodeLanguage = CodeLanguage.UNKNOWN
    code: str = ""
    ast_tree: Optional[Any] = None
    entities: List[CodeEntity] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    complexity: int = 0
    lines_of_code: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'code_id': self.code_id,
            'source_file': str(self.source_file),
            'source_position': self.source_position,
            'language': self.language.value,
            'code': self.code,
            'entities': [e.to_dict() for e in self.entities],
            'imports': self.imports,
            'complexity': self.complexity,
            'lines_of_code': self.lines_of_code,
            'metadata': self.metadata
        }

        if self.ast_tree is not None and self.language == CodeLanguage.PYTHON:
            try:
                data['ast_dump'] = ast.dump(self.ast_tree)
            except:
                pass

        return data


# ==============================================================================
# Code Extractor
# ==============================================================================

class CodeExtractor:
    """
    Extracts code blocks from documents and analyzes structure
    """

    def __init__(self):
        """Initialize code extractor"""
        # Language detection patterns
        self.language_keywords = {
            CodeLanguage.PYTHON: ['def ', 'class ', 'import ', 'from ', 'self.'],
            CodeLanguage.JAVASCRIPT: ['function', 'const ', 'let ', 'var ', '=>', 'console.'],
            CodeLanguage.JAVA: ['public class', 'private ', 'public static void'],
            CodeLanguage.CPP: ['#include', 'std::', 'cout', 'endl'],
            CodeLanguage.C: ['#include', 'printf', 'malloc', 'void main'],
            CodeLanguage.SQL: ['SELECT ', 'FROM ', 'WHERE ', 'INSERT ', 'UPDATE '],
        }

    def extract(
        self,
        content: str,
        file_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Extract code blocks from content

        Args:
            content: Document content
            file_path: Source file path
            options: Extraction options

        Returns:
            List of ExtractedCode objects wrapped as ExtractedObject
        """
        from .objectifier import ExtractedObject, ObjectType

        options = options or {}
        code_blocks = []

        # Extract fenced code blocks (Markdown)
        code_blocks.extend(self._extract_fenced_blocks(content, file_path))

        # Extract inline code
        if options.get('extract_inline', False):
            code_blocks.extend(self._extract_inline_code(content, file_path))

        # If file is a code file, analyze the whole file
        if self._is_code_file(file_path):
            code_blocks.extend(self._extract_file_code(content, file_path))

        # Convert to ExtractedObject format
        objects = []
        for code_block in code_blocks:
            obj = ExtractedObject(
                object_id=code_block.code_id,
                object_type=ObjectType.CODE,
                source_file=code_block.source_file,
                source_position=code_block.source_position,
                content=code_block.code,
                structured_data=code_block.to_dict(),
                metadata=code_block.metadata
            )
            objects.append(obj)

        return objects

    def _extract_fenced_blocks(
        self,
        content: str,
        file_path: Path
    ) -> List[ExtractedCode]:
        """Extract fenced code blocks from Markdown"""
        blocks = []

        # Pattern for fenced code blocks: ```lang\ncode\n```
        pattern = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)

        for i, match in enumerate(pattern.finditer(content)):
            lang_str = match.group(1).lower()
            code_text = match.group(2)

            # Detect language
            language = self._detect_language(code_text, lang_str)

            # Create code block
            code_block = ExtractedCode(
                code_id=f"code_block_{i}",
                source_file=file_path,
                source_position=match.start(),
                language=language,
                code=code_text,
                lines_of_code=len(code_text.split('\n')),
                metadata={
                    'format': 'fenced',
                    'declared_language': lang_str
                }
            )

            # Analyze code
            self._analyze_code(code_block)

            blocks.append(code_block)

        return blocks

    def _extract_inline_code(
        self,
        content: str,
        file_path: Path
    ) -> List[ExtractedCode]:
        """Extract inline code snippets"""
        blocks = []

        # Pattern for inline code: `code`
        pattern = re.compile(r'`([^`]+)`')

        for i, match in enumerate(pattern.finditer(content)):
            code_text = match.group(1)

            # Skip if too short
            if len(code_text) < 5:
                continue

            language = self._detect_language(code_text)

            code_block = ExtractedCode(
                code_id=f"code_inline_{i}",
                source_file=file_path,
                source_position=match.start(),
                language=language,
                code=code_text,
                lines_of_code=1,
                metadata={'format': 'inline'}
            )

            blocks.append(code_block)

        return blocks

    def _extract_file_code(
        self,
        content: str,
        file_path: Path
    ) -> List[ExtractedCode]:
        """Extract code from a code file"""
        # Detect language from file extension
        language = self._detect_language_from_file(file_path)

        code_block = ExtractedCode(
            code_id="file_code",
            source_file=file_path,
            source_position=0,
            language=language,
            code=content,
            lines_of_code=len(content.split('\n')),
            metadata={'format': 'file'}
        )

        # Analyze code
        self._analyze_code(code_block)

        return [code_block]

    def _detect_language(
        self,
        code: str,
        declared_lang: Optional[str] = None
    ) -> CodeLanguage:
        """Detect programming language from code content"""
        # Use declared language if available
        if declared_lang:
            lang_map = {
                'python': CodeLanguage.PYTHON,
                'py': CodeLanguage.PYTHON,
                'javascript': CodeLanguage.JAVASCRIPT,
                'js': CodeLanguage.JAVASCRIPT,
                'typescript': CodeLanguage.TYPESCRIPT,
                'ts': CodeLanguage.TYPESCRIPT,
                'java': CodeLanguage.JAVA,
                'c': CodeLanguage.C,
                'cpp': CodeLanguage.CPP,
                'c++': CodeLanguage.CPP,
                'csharp': CodeLanguage.CSHARP,
                'cs': CodeLanguage.CSHARP,
                'go': CodeLanguage.GO,
                'rust': CodeLanguage.RUST,
                'r': CodeLanguage.R,
                'matlab': CodeLanguage.MATLAB,
                'sql': CodeLanguage.SQL,
                'shell': CodeLanguage.SHELL,
                'bash': CodeLanguage.SHELL,
                'sh': CodeLanguage.SHELL,
            }

            if declared_lang in lang_map:
                return lang_map[declared_lang]

        # Heuristic detection based on keywords
        scores = {}
        for language, keywords in self.language_keywords.items():
            score = sum(1 for keyword in keywords if keyword in code)
            if score > 0:
                scores[language] = score

        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        return CodeLanguage.UNKNOWN

    def _detect_language_from_file(self, file_path: Path) -> CodeLanguage:
        """Detect language from file extension"""
        ext_map = {
            '.py': CodeLanguage.PYTHON,
            '.js': CodeLanguage.JAVASCRIPT,
            '.ts': CodeLanguage.TYPESCRIPT,
            '.java': CodeLanguage.JAVA,
            '.c': CodeLanguage.C,
            '.cpp': CodeLanguage.CPP,
            '.cc': CodeLanguage.CPP,
            '.cxx': CodeLanguage.CPP,
            '.h': CodeLanguage.C,
            '.hpp': CodeLanguage.CPP,
            '.cs': CodeLanguage.CSHARP,
            '.go': CodeLanguage.GO,
            '.rs': CodeLanguage.RUST,
            '.r': CodeLanguage.R,
            '.m': CodeLanguage.MATLAB,
            '.sql': CodeLanguage.SQL,
            '.sh': CodeLanguage.SHELL,
        }

        return ext_map.get(file_path.suffix.lower(), CodeLanguage.UNKNOWN)

    def _is_code_file(self, file_path: Path) -> bool:
        """Check if file is a code file"""
        code_extensions = {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h',
                          '.hpp', '.cs', '.go', '.rs', '.r', '.m', '.sql', '.sh'}
        return file_path.suffix.lower() in code_extensions

    def _analyze_code(self, code_block: ExtractedCode):
        """
        Analyze code block structure

        Updates code_block in-place with analysis results
        """
        if code_block.language == CodeLanguage.PYTHON:
            self._analyze_python(code_block)
        elif code_block.language == CodeLanguage.JAVASCRIPT:
            self._analyze_javascript(code_block)
        elif code_block.language == CodeLanguage.SQL:
            self._analyze_sql(code_block)
        # Add more language-specific analyzers as needed

    def _analyze_python(self, code_block: ExtractedCode):
        """Analyze Python code using AST"""
        try:
            tree = ast.parse(code_block.code)
            code_block.ast_tree = tree

            # Extract entities
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    entity = self._extract_python_function(node, code_block.code)
                    code_block.entities.append(entity)

                elif isinstance(node, ast.ClassDef):
                    entity = self._extract_python_class(node, code_block.code)
                    code_block.entities.append(entity)

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_str = self._extract_python_import(node)
                    code_block.imports.append(import_str)

            # Calculate complexity
            code_block.complexity = sum(e.complexity for e in code_block.entities)

        except SyntaxError as e:
            code_block.metadata['parse_error'] = str(e)

    def _extract_python_function(
        self,
        node: ast.FunctionDef,
        code: str
    ) -> CodeEntity:
        """Extract Python function details"""
        # Get docstring
        docstring = ast.get_docstring(node)

        # Get parameters
        parameters = []
        for arg in node.args.args:
            param = {'name': arg.arg}

            # Type annotation
            if arg.annotation:
                try:
                    param['type'] = ast.unparse(arg.annotation)
                except:
                    pass

            parameters.append(param)

        # Get return type
        return_type = None
        if node.returns:
            try:
                return_type = ast.unparse(node.returns)
            except:
                pass

        # Get decorators
        decorators = []
        for dec in node.decorator_list:
            try:
                decorators.append(ast.unparse(dec))
            except:
                pass

        # Calculate complexity (count decision points)
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        entity = CodeEntity(
            name=node.name,
            type='function',
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=docstring,
            parameters=parameters,
            return_type=return_type,
            decorators=decorators,
            complexity=complexity
        )

        return entity

    def _extract_python_class(
        self,
        node: ast.ClassDef,
        code: str
    ) -> CodeEntity:
        """Extract Python class details"""
        docstring = ast.get_docstring(node)

        # Get decorators
        decorators = []
        for dec in node.decorator_list:
            try:
                decorators.append(ast.unparse(dec))
            except:
                pass

        # Count methods
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]

        entity = CodeEntity(
            name=node.name,
            type='class',
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=docstring,
            decorators=decorators,
            complexity=len(methods)
        )

        entity.metadata = {'method_count': len(methods)}

        return entity

    def _extract_python_import(self, node: Union[ast.Import, ast.ImportFrom]) -> str:
        """Extract Python import statement"""
        try:
            return ast.unparse(node)
        except:
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
                return f"import {', '.join(names)}"
            else:
                module = node.module or ''
                names = [alias.name for alias in node.names]
                return f"from {module} import {', '.join(names)}"

    def _analyze_javascript(self, code_block: ExtractedCode):
        """Analyze JavaScript code (basic pattern matching)"""
        code = code_block.code

        # Extract function declarations
        func_pattern = re.compile(
            r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>))'
        )

        for match in func_pattern.finditer(code):
            name = match.group(1) or match.group(2)
            if name:
                entity = CodeEntity(
                    name=name,
                    type='function',
                    start_line=code[:match.start()].count('\n') + 1,
                    end_line=code[:match.start()].count('\n') + 1
                )
                code_block.entities.append(entity)

        # Extract class declarations
        class_pattern = re.compile(r'class\s+(\w+)')
        for match in class_pattern.finditer(code):
            entity = CodeEntity(
                name=match.group(1),
                type='class',
                start_line=code[:match.start()].count('\n') + 1,
                end_line=code[:match.start()].count('\n') + 1
            )
            code_block.entities.append(entity)

        # Extract imports
        import_pattern = re.compile(r'(?:import|require)\s*\([\'"]([^\'"]+)')
        for match in import_pattern.finditer(code):
            code_block.imports.append(match.group(1))

    def _analyze_sql(self, code_block: ExtractedCode):
        """Analyze SQL code"""
        code = code_block.code.upper()

        # Count different SQL operations
        operations = {
            'SELECT': code.count('SELECT'),
            'INSERT': code.count('INSERT'),
            'UPDATE': code.count('UPDATE'),
            'DELETE': code.count('DELETE'),
            'CREATE': code.count('CREATE'),
            'DROP': code.count('DROP'),
        }

        code_block.metadata['operations'] = operations
        code_block.complexity = sum(operations.values())


# ==============================================================================
# Factory Function
# ==============================================================================

def create_code_extractor() -> CodeExtractor:
    """
    Create a new CodeExtractor instance

    Returns:
        Configured CodeExtractor
    """
    return CodeExtractor()


# ==============================================================================
# Standalone Test
# ==============================================================================

if __name__ == '__main__':
    test_content = """
# Code Examples

Here's a Python function:

```python
def calculate_distance(x1, y1, x2, y2):
    \"\"\"Calculate Euclidean distance between two points\"\"\"
    import math
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx**2 + dy**2)

class Point:
    \"\"\"Represents a 2D point\"\"\"
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

And some JavaScript:

```javascript
function greet(name) {
    console.log(`Hello, ${name}!`);
}

const add = (a, b) => a + b;
```
"""

    test_file = Path('test_code_extraction.md')
    test_file.write_text(test_content)

    extractor = create_code_extractor()
    code_blocks = extractor.extract(test_content, test_file, {})

    print(f"\n=== Code Extraction Results ===")
    print(f"Found {len(code_blocks)} code blocks\n")

    for obj in code_blocks:
        code_data = obj.structured_data
        print(f"Code Block: {obj.object_id}")
        print(f"Language: {code_data['language']}")
        print(f"Lines: {code_data['lines_of_code']}")
        print(f"Entities: {len(code_data['entities'])}")

        for entity in code_data['entities']:
            print(f"  - {entity['type']}: {entity['name']} " +
                  f"(lines {entity['start_line']}-{entity['end_line']})")

        if code_data['imports']:
            print(f"Imports: {code_data['imports']}")

        print(f"Complexity: {code_data['complexity']}")
        print("\n" + "=" * 50 + "\n")

    test_file.unlink()
