"""
LightSpeed V0.9.5 - AI Integration Layer
Provides unified interface to multiple AI backends (Ollama, OpenAI, etc.)
Plus Achilles AI context tracking and document objectification

Components:
- OllamaConnector: Ollama AI backend
- DocumentObjectifier: Multi-floor document parsing
- AchillesContextSystem: Conversation tracking & workflow automation
- AchillesContextTracker: Simplified conversation tracking

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
Date: January 3, 2026
"""

# ---------------------------------------------------------------------------
# Z-Floor placement (Neo)
#
# The AI subsystem lives under `Z Axis/Z+2_Neo/ai`.
# Keep `core.ai.*` imports stable by extending this package's search path.
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

_NEO_AI = Path(_LIGHTSPEED_ROOT) / "Z Axis" / "Z+2_Neo" / "ai"
try:
    if _NEO_AI.exists():
        __path__.append(str(_NEO_AI))  # type: ignore[name-defined]
except Exception:
    pass

from .ollama_connector import OllamaConnector, OllamaConfig

from .document_objectifier import (
    DocumentObjectifier,
    AchillesContextTracker,
    ExtractedObject,
    ObjectType
)

from .achilles_context import (
    AchillesContextSystem,
    ConversationContext,
    WorkflowTask
)

__all__ = [
    'OllamaConnector',
    'OllamaConfig',
    'DocumentObjectifier',
    'AchillesContextTracker',
    'ExtractedObject',
    'ObjectType',
    'AchillesContextSystem',
    'ConversationContext',
    'WorkflowTask',
]
