"""
AI Orchestrator - Unified AI Management for Neo Floor
Consolidates Ollama (current) and Achilles (future) AI systems

This module serves as the umbrella object for all AI operations:
- Ollama integration (current LLM backend)
- Achilles integration (future custom AI)
- Voice command processing
- Context management across sessions
- Governed tool routing through runtime/Smith
- Dual-mode prompting (Clippy vs Orchestrator)

Clean Code: Single point of truth for AI operations
Replaces: Multiple scattered AI files
Version: 0.9.5
Date: December 20, 2025
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import json

try:
    from lightspeed_runtime.ai_settings import ai_backend_summary, load_ai_settings
    from lightspeed_runtime.storage_paths import resolve_ai_settings_path
except Exception:  # pragma: no cover - runtime fallback when package path is unavailable
    ai_backend_summary = None
    load_ai_settings = None
    resolve_ai_settings_path = None


class AIMode(Enum):
    """AI operational modes"""
    CLIPPY = "clippy"              # Friendly assistant for clients
    ORCHESTRATOR = "orchestrator"  # System orchestrator for IT/Founder
    ACHILLES = "achilles"          # Future: Custom Achilles AI


class AIBackend(Enum):
    """Available AI backends"""
    OLLAMA = "ollama"        # Current: Ollama LLM
    ACHILLES = "achilles"    # Future: Custom Achilles AI
    HYBRID = "hybrid"        # Both active


@dataclass
class AIContext:
    """AI conversation context"""
    user_id: str
    company: str
    project: str
    mode: AIMode
    history: List[Dict[str, str]]
    tools_available: List[str]
    metadata: Dict[str, Any]


class AIOrchestrator:
    """
    Unified AI management system

    Consolidates:
    - core/ai/ollama_connector.py
    - core/ai/ai_context.py
    - runtime/Smith governed tool routing
    - core/ai/ai_code_assistant.py
    - Future Achilles integration

    Single Responsibility: AI operations management
    """

    def __init__(self, lightspeed_root: Path):
        self.lightspeed_root = lightspeed_root
        self.current_backend = AIBackend.OLLAMA
        self.ollama_instance = None
        self.achilles_instance = None
        self.active_contexts: Dict[str, AIContext] = {}
        self.runtime_ai_settings: Dict[str, Any] = {}
        self.ai_summary: Dict[str, Any] = {}

        # Configuration
        self.config = self._load_config()

        # Initialize backends
        self._initialize_backends()

    def _load_config(self) -> Dict[str, Any]:
        """Load AI configuration"""
        default_config = {
            "ollama": {
                "host": "http://localhost:11434",
                "model": "qwen3:8b",
                "temperature": 0.7,
                "max_tokens": 2048,
                "timeout": 30,
                "available_models": ["qwen3:8b", "deepseek-r1:8b"],
            },
            "achilles": {
                "enabled": True,
                "transition_date": "local_staged_runtime",
                "backend_url": "https://romer.industries/achilles",
                "voice_enabled": True
            },
            "modes": {
                "clippy": {
                    "system_prompt": "You are Clippy, a friendly LightSpeed assistant. Be helpful, concise, and approachable.",
                    "tone": "friendly",
                    "emoji": True
                },
                "orchestrator": {
                    "system_prompt": "You are the LightSpeed Orchestrator AI. Provide expert technical guidance with precision.",
                    "tone": "professional",
                    "emoji": False
                },
                "achilles": {
                    "system_prompt": "You are Achilles, the advanced AI helm of LightSpeed. Integrate Cognigrex research capabilities.",
                    "tone": "expert",
                    "emoji": False,
                    "voice_activated": True
                }
            }
        }

        settings_path = None
        if callable(resolve_ai_settings_path):
            try:
                settings_path = resolve_ai_settings_path(self.lightspeed_root)
            except Exception:
                settings_path = None

        if callable(load_ai_settings):
            try:
                settings = load_ai_settings(self.lightspeed_root)
                if isinstance(settings, dict) and settings:
                    self.runtime_ai_settings = settings
                    if callable(ai_backend_summary):
                        try:
                            self.ai_summary = ai_backend_summary(settings)
                        except Exception:
                            self.ai_summary = {}

                    backends = dict(settings.get("backends") or {})
                    active_backend_id = str(settings.get("active_backend") or "ollama_local")
                    active_backend = dict(backends.get(active_backend_id) or backends.get("ollama_local") or {})
                    fallback_backend = dict(backends.get("ollama_local") or {})
                    merged_backend = dict(fallback_backend)
                    merged_backend.update(active_backend)
                    personas = dict(settings.get("personas") or {})
                    achilles = dict(settings.get("achilles") or {})

                    available_models: List[str] = []
                    for backend in backends.values():
                        if isinstance(backend, dict) and backend.get("type") == "ollama" and backend.get("model"):
                            model_name = str(backend["model"]).strip()
                            if model_name and model_name not in available_models:
                                available_models.append(model_name)

                    default_config.update(
                        {
                            "settings_path": str(settings_path) if settings_path else None,
                            "active_backend": active_backend_id,
                            "active_profile": settings.get("active_profile", "low_lag_local"),
                            "ollama": {
                                "enabled": bool(merged_backend.get("enabled", True))
                                and str(merged_backend.get("type", "ollama")) == "ollama",
                                "host": merged_backend.get("host", "http://localhost:11434"),
                                "model": merged_backend.get("model", default_config["ollama"]["model"]),
                                "temperature": float(merged_backend.get("temperature", 0.7)),
                                "max_tokens": int(merged_backend.get("max_tokens", 2048)),
                                "timeout": int(merged_backend.get("timeout_s", 30)),
                                "available_models": available_models or default_config["ollama"]["available_models"],
                            },
                            "achilles": {
                                "enabled": bool(achilles.get("enabled", True)),
                                "approval_gated": bool(achilles.get("approval_gated", True)),
                                "transition_date": achilles.get("transition_date", "local_staged_runtime"),
                                "backend_url": achilles.get("backend_url", "https://romer.industries/achilles"),
                                "voice_enabled": bool(achilles.get("voice_enabled", True)),
                                "operator_mode": achilles.get("operator_mode", "desktop_orchestrator"),
                                "auto_safe_actions": bool(achilles.get("auto_safe_actions", True)),
                                "primary_console": achilles.get("primary_console", "Neo"),
                            },
                            "modes": personas or default_config["modes"],
                        }
                    )
                    return default_config
            except Exception as e:
                print(f"[AIOrchestrator] Runtime AI settings load error: {e}")

        config_path = self.lightspeed_root / "config" / "ai_config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                print(f"[AIOrchestrator] Config load error: {e}")

        return default_config

    def _initialize_backends(self):
        """Initialize available AI backends"""
        # Ollama (current)
        try:
            from core.ai.ollama_connector import OllamaConnector, OllamaConfig
            cfg = OllamaConfig(
                base_url=self.config["ollama"].get("host", "http://localhost:11434"),
                default_model=self.config["ollama"].get("model", "qwen3:8b"),
                temperature=float(self.config["ollama"].get("temperature", 0.7)),
                max_tokens=int(self.config["ollama"].get("max_tokens", 2048)),
                timeout=int(self.config["ollama"].get("timeout", 30)),
                available_models=list(self.config["ollama"].get("available_models") or []),
            )
            self.ollama_instance = OllamaConnector(cfg)
            success, msg = self.ollama_instance.test_connection()
            if success:
                try:
                    discovered_models = self.ollama_instance.list_models()
                    if discovered_models:
                        self.config["ollama"]["available_models"] = discovered_models
                except Exception:
                    pass
                print(f"[AIOrchestrator] Ollama connected: {msg}")
            else:
                print(f"[AIOrchestrator] Ollama unavailable: {msg}")
                self.ollama_instance = None
        except ImportError:
            print("[AIOrchestrator] Ollama connector not available")
            self.ollama_instance = None

        # Achilles is a governed local persona over the active Ollama connector.
        if self.config['achilles']['enabled']:
            if self._bind_local_achilles():
                print("[AIOrchestrator] Achilles connected through local Ollama (approval-gated)")
            else:
                print("[AIOrchestrator] Achilles waiting for local Ollama")

    def _bind_local_achilles(self) -> bool:
        if not self.config.get("achilles", {}).get("enabled") or self.ollama_instance is None:
            self.achilles_instance = None
            return False
        self.achilles_instance = self.ollama_instance
        return True

    def create_context(
        self,
        user_id: str,
        company: str,
        project: str,
        mode: AIMode = AIMode.CLIPPY
    ) -> AIContext:
        """
        Create AI conversation context

        Clean Code: Factory method for context creation
        """
        context = AIContext(
            user_id=user_id,
            company=company,
            project=project,
            mode=mode,
            history=[],
            tools_available=self._get_available_tools(),
            metadata={}
        )

        self.active_contexts[f"{user_id}_{company}_{project}"] = context
        return context

    def _get_available_tools(self) -> List[str]:
        """Get list of available AI tools"""
        tools = [
            "database_query",
            "file_search",
            "code_analysis",
            "project_management",
            "visualization",
            "workflow_automation",
            "local_llm_runtime",
            "temp_shell_orchestration",
        ]

        # Add Cognigrex research tools if available
        try:
            from importlib.util import module_from_spec, spec_from_file_location
            from pathlib import Path
            import sys

            z_axis_root = Path(__file__).resolve().parents[2]
            cog_file = (z_axis_root / "Z+2_Neo" / "components" / "cognigrex_foundation.py").resolve()
            spec = spec_from_file_location("lightspeed_dynamic_cognigrex_foundation", cog_file)
            if spec is not None and spec.loader is not None and cog_file.exists():
                mod = module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
                get_cognigrex = getattr(mod, "get_cognigrex", None)
            else:
                get_cognigrex = None

            if callable(get_cognigrex) and get_cognigrex():
                tools.extend([
                    "research_workspace",
                    "dataset_analysis",
                    "knowledge_graph"
                ])
        except:
            pass

        return tools

    def process_message(
        self,
        context_key: str,
        message: str,
        stream: bool = False
    ) -> str:
        """
        Process AI message with appropriate backend

        Args:
            context_key: Context identifier (user_company_project)
            message: User message
            stream: Whether to stream response

        Returns:
            AI response
        """
        context = self.active_contexts.get(context_key)
        if not context:
            return "Error: Context not found"

        # Add to history
        context.history.append({"role": "user", "content": message})

        # Route to appropriate backend
        if self.achilles_instance and self.current_backend == AIBackend.ACHILLES:
            response = self._process_with_achilles(context, message, stream)
        elif self.ollama_instance:
            response = self._process_with_ollama(context, message, stream)
        else:
            response = self._process_without_backend(context, message)

        # Add to history
        context.history.append({"role": "assistant", "content": response})

        return response

    def _process_with_ollama(
        self,
        context: AIContext,
        message: str,
        stream: bool
    ) -> str:
        """Process with Ollama backend"""
        if not self.ollama_instance:
            return "Ollama not available"

        # Get mode-specific system prompt
        mode_config = self.config['modes'][context.mode.value]
        system_prompt = mode_config['system_prompt']

        # Add context
        full_prompt = f"{system_prompt}\n\n"
        full_prompt += f"Company: {context.company}\n"
        full_prompt += f"Project: {context.project}\n"
        full_prompt += f"Available tools: {', '.join(context.tools_available)}\n\n"
        full_prompt += f"User: {message}"

        try:
            response = self.ollama_instance.generate(
                prompt=full_prompt,
                stream=stream
            )
            return response
        except Exception as e:
            return f"Error: {str(e)}"

    def _process_with_achilles(
        self,
        context: AIContext,
        message: str,
        stream: bool
    ) -> str:
        """Process with the governed Achilles persona on local Ollama."""
        if not self.achilles_instance:
            return "Achilles is waiting for the local Ollama backend."

        mode_config = self.config.get("modes", {}).get("achilles", {})
        system_prompt = mode_config.get(
            "system_prompt",
            "You are Achilles, the local Cognigrex operator for LightSpeed.",
        )
        approval_policy = (
            "approval-gated: request operator approval before write, execute, publish, "
            "or destructive actions."
            if self.config.get("achilles", {}).get("approval_gated", True)
            else "operator-authorized local execution."
        )
        prompt = (
            f"{system_prompt}\n\n"
            f"Operating policy: {approval_policy}\n"
            f"Company: {context.company}\n"
            f"Project: {context.project}\n"
            f"Available tools: {', '.join(context.tools_available)}\n\n"
            f"User: {message}"
        )
        try:
            return self.achilles_instance.generate(prompt=prompt, stream=stream)
        except Exception as exc:
            return f"Error: {exc}"

    def _process_without_backend(
        self,
        context: AIContext,
        message: str
    ) -> str:
        """Fallback response with heuristic processing when no backend available"""
        mode = context.mode.value

        # Try to provide helpful responses based on keywords
        message_lower = message.lower()

        # Programming help
        if any(keyword in message_lower for keyword in ['code', 'function', 'class', 'debug', 'error']):
            return self._generate_code_help_fallback(message, mode)

        # Documentation request
        if any(keyword in message_lower for keyword in ['doc', 'explain', 'what is', 'how to']):
            return self._generate_documentation_fallback(message, mode)

        # General query
        return self._generate_general_fallback(message, mode)

    def _generate_code_help_fallback(self, message: str, mode: str) -> str:
        """Generate code-related fallback response"""
        if mode == "clippy":
            return (
                f" Hi! I'd love to help with your code question: '{message}'\n\n"
                f"While my AI backend is offline, here are some quick tips:\n"
                f"- Check syntax and indentation\n"
                f"- Review variable names and types\n"
                f"- Look for common errors (missing imports, undefined variables)\n"
                f"- Use print() statements for debugging\n\n"
                f"For full AI assistance, please configure the AI backend in Settings."
            )
        else:
            return (
                f" Code assistance request logged: '{message}'\n\n"
                f"AI backend offline. Suggesting:\n"
                f"1. Review code documentation in Morpheus floor\n"
                f"2. Check similar examples in project files\n"
                f"3. Configure AI backend (Ollama/OpenAI) for full support"
            )

    def _generate_documentation_fallback(self, message: str, mode: str) -> str:
        """Generate documentation-related fallback response"""
        if mode == "clippy":
            return (
                f" Great question: '{message}'\n\n"
                f"While I'm offline, you can:\n"
                f" Check the Morpheus floor for documentation\n"
                f" Browse Z Axis/Z-1_Morpheus/documentation/\n"
                f" Review README.md files in each component\n"
                f" Use the platform's built-in help system\n\n"
                f"Connect an AI backend for interactive assistance!"
            )
        else:
            return (
                f" Documentation query: '{message}'\n\n"
                f"Resources available:\n"
                f" Morpheus floor documentation index\n"
                f" Component README files\n"
                f" LightSpeed/README.md for platform overview\n\n"
                f"Enable AI backend for intelligent search and explanations."
            )

    def _generate_general_fallback(self, message: str, mode: str) -> str:
        """Generate general fallback response"""
        if mode == "clippy":
            return (
                f" Hi! You asked: '{message}'\n\n"
                f"I'm currently offline, but I can still help you navigate:\n"
                f" Use the floor navigation to explore different areas\n"
                f" Check the Trinity dashboard for system overview\n"
                f" Browse available tools in each Z-floor\n"
                f" Review documentation in Morpheus\n\n"
                f"Configure AI backend in Settings for full AI capabilities!"
            )
        else:
            return (
                f" Query received: '{message}'\n\n"
                f"AI backend unavailable. Available actions:\n"
                f"- Explore platform manually via UI\n"
                f"- Check documentation (Morpheus floor)\n"
                f"- Configure AI backend: Settings -> AI Configuration\n"
                f"- Supported backends: Ollama (local), OpenAI (API)\n\n"
                f"Your query has been logged for when AI comes online."
            )

    def switch_mode(self, context_key: str, new_mode: AIMode):
        """Switch AI mode for a context"""
        context = self.active_contexts.get(context_key)
        if context:
            context.mode = new_mode
            print(f"[AIOrchestrator] Switched to {new_mode.value} mode")

    def switch_backend(self, backend: AIBackend):
        """Switch AI backend"""
        if backend == AIBackend.ACHILLES and not self.achilles_instance:
            print("[AIOrchestrator] Achilles not available yet")
            return False

        self.current_backend = backend
        print(f"[AIOrchestrator] Switched to {backend.value} backend")
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get AI orchestrator status"""
        return {
            "current_backend": self.current_backend.value,
            "active_profile": self.config.get("active_profile"),
            "ollama_available": self.ollama_instance is not None,
            "achilles_available": self.achilles_instance is not None,
            "active_contexts": len(self.active_contexts),
            "settings_path": self.config.get("settings_path"),
            "local_first": bool(self.ai_summary.get("local_first", True)),
            "backends": {
                "ollama": {
                    "status": "connected" if self.ollama_instance else "offline",
                    "model": self.config["ollama"]["model"],
                    "host": self.config["ollama"].get("host"),
                    "available_models": self.config["ollama"].get("available_models") or [],
                },
                "achilles": {
                    "status": "connected_local" if self.achilles_instance else "pending",
                    "transition_date": self.config["achilles"].get("transition_date"),
                    "approval_gated": bool(self.config["achilles"].get("approval_gated", True)),
                }
            }
        }

    def clear_history(self, context_key: str):
        """Clear conversation history"""
        context = self.active_contexts.get(context_key)
        if context:
            context.history = []

    def export_context(self, context_key: str) -> Optional[Dict[str, Any]]:
        """Export context for persistence"""
        context = self.active_contexts.get(context_key)
        if not context:
            return None

        return {
            "user_id": context.user_id,
            "company": context.company,
            "project": context.project,
            "mode": context.mode.value,
            "history": context.history,
            "tools_available": context.tools_available,
            "metadata": context.metadata
        }


class AIOrchestratorComponent:
    """
    Backwards-compatible wrapper for floor bootstrap code.

    Some floor runners expect a symbol named `AIOrchestratorComponent` with a
    no-arg constructor; this delegates to the module-level singleton.
    """

    def __init__(self, lightspeed_root: Optional[Path] = None):
        self._inner = get_orchestrator(lightspeed_root)

    def __getattr__(self, item: str):
        return getattr(self._inner, item)


# Module-level instance
_orchestrator: Optional[AIOrchestrator] = None

def _find_lightspeed_root() -> Path:
    here = Path(__file__).resolve()
    for cand in (here, *here.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return here.parents[3]

def get_orchestrator(lightspeed_root: Optional[Path] = None) -> AIOrchestrator:
    """Get global AI orchestrator instance"""
    global _orchestrator

    if _orchestrator is None:
        if lightspeed_root is None:
            lightspeed_root = _find_lightspeed_root()
        _orchestrator = AIOrchestrator(lightspeed_root)

    return _orchestrator


# Testing
if __name__ == "__main__":
    from pathlib import Path

    root = _find_lightspeed_root()
    orchestrator = AIOrchestrator(root)

    print("\n" + "=" * 70)
    print("AI ORCHESTRATOR TEST")
    print("=" * 70)

    # Create context
    ctx = orchestrator.create_context(
        user_id="test_user",
        company="Romer Industries",
        project="LightSpeed",
        mode=AIMode.CLIPPY
    )

    print(f"\n[TEST] Created context: {ctx.user_id} - {ctx.company}")

    # Process message
    response = orchestrator.process_message(
        context_key="test_user_Romer Industries_LightSpeed",
        message="Hello, can you help me?"
    )

    print(f"\n[TEST] Response: {response}")

    # Get status
    status = orchestrator.get_status()
    print(f"\n[TEST] Status:")
    print(f"  Backend: {status['current_backend']}")
    print(f"  Ollama: {status['backends']['ollama']['status']}")
    print(f"  Achilles: {status['backends']['achilles']['status']}")

    print("\n" + "=" * 70)
