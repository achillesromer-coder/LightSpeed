"""
Code Analysis System
LightSpeed Platform - Morpheus Floor (Z+2)

Provides Python code analysis, project indexing, and knowledge management:
- AST (Abstract Syntax Tree) parsing and analysis
- Function and class extraction
- Import dependency tracking
- Code complexity metrics
- Project-wide indexing with semantic search
- Knowledge graph construction

This module enables the platform to understand and navigate codebases,
track dependencies, and provide intelligent code insights.
"""

# ---------------------------------------------------------------------------
# Z-Floor placement (Morpheus)
#
# The analysis subsystem lives under `Z Axis/Z-1_Morpheus/analysis`.
# Keep `core.analysis.*` imports stable by extending this package's search path.
# ---------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path

try:
    from core.config.paths import LIGHTSPEED_ROOT as _LIGHTSPEED_ROOT  # type: ignore
except Exception:
    _LIGHTSPEED_ROOT = Path(__file__).resolve()
    for _cand in (_LIGHTSPEED_ROOT, *_LIGHTSPEED_ROOT.parents):
        if (_cand / "N.py").exists() and (_cand / "Z Axis").exists():
            _LIGHTSPEED_ROOT = _cand
            break

_MORPHEUS_ANALYSIS = Path(_LIGHTSPEED_ROOT) / "Z Axis" / "Z-1_Morpheus" / "analysis"
try:
    if _MORPHEUS_ANALYSIS.exists():
        __path__.append(str(_MORPHEUS_ANALYSIS))  # type: ignore[name-defined]
except Exception:
    pass

from .ast_analyzer import PythonASTAnalyzer, CodeAnalysis
from .indexer import ProjectIndexer
from .dependencies import DependencyTracker, PlatformDependencyMapper

__all__ = [
    'PythonASTAnalyzer',
    'CodeAnalysis',
    'ProjectIndexer',
    'DependencyTracker',
    'PlatformDependencyMapper',
]
