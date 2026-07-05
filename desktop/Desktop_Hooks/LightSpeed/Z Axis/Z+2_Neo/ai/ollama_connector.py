"""
Ollama AI Connector - LightSpeed Platform
Provides connection to local Ollama instance for AI chat capabilities.

Features:
- Streaming and non-streaming responses
- Model management
- Context retention
- Tool integration support
- Dual-mode prompt system (ACHILLES Guided vs Orchestrator)
"""

import json
import requests
from typing import Dict, List, Optional, Any, Generator
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class OllamaConfig:
    """Ollama configuration."""
    base_url: str = "http://localhost:11434"
    default_model: str = "llama3.2"
    temperature: float = 0.7
    max_tokens: int = 2000
    streaming: bool = True
    timeout: int = 60
    available_models: List[str] = field(default_factory=lambda: [
        "llama3.2", "codellama", "mistral", "phi3", "llama2"
    ])


class OllamaConnector:
    """
    Connector for Ollama local AI instance.

    Provides chat completion with context retention and dual-mode prompting.
    """

    def __init__(self, config: Optional[OllamaConfig] = None):
        """
        Initialize Ollama connector.

        Args:
            config: Ollama configuration (uses defaults if None)
        """
        self.config = config or OllamaConfig()
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt: Optional[str] = None

    def test_connection(self) -> tuple[bool, str]:
        """
        Test connection to Ollama instance.

        Returns:
            (success, message) tuple
        """
        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=5
            )

            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', 'unknown') for m in models]
                return True, f"Connected. Available models: {', '.join(model_names[:5])}"
            else:
                return False, f"HTTP {response.status_code}: {response.text}"

        except requests.ConnectionError:
            return False, "Cannot connect to Ollama. Is it running? (ollama serve)"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def set_system_prompt(self, prompt: str) -> None:
        """
        Set system prompt for conversation context.

        Args:
            prompt: System prompt defining AI behavior
        """
        self.system_prompt = prompt

    def set_dual_mode(self, mode: str, user_info: Optional[Dict[str, Any]] = None) -> None:
        """
        Set dual-mode prompt (ACHILLES Guided vs Orchestrator).

        Args:
            mode: "client" (Guided) or "it_founder" (Orchestrator)
            user_info: Optional user information for personalization
        """
        user_name = user_info.get('fullname', 'User') if user_info else 'User'
        company = user_info.get('company', 'your organization') if user_info else 'your organization'

        if mode == "client":
            # Guided mode - Friendly, helpful, guides through workflows
            self.system_prompt = f"""You are ACHILLES, a friendly AI assistant for the LightSpeed platform at {company}.

Your role:
  - Help {user_name} navigate the platform with a warm, approachable tone
  - Guide users through workflows step-by-step
  - Explain technical concepts in simple terms
  - Encourage exploration and learning
  - Be supportive and patient

Personality:
- Friendly and enthusiastic
- Use clear, non-technical language when possible
- Offer proactive suggestions
- Celebrate user successes
- Ask clarifying questions to understand user needs

Available platform features:
- Project management
- Document storage (Oracle floor)
- Physics simulations (TheConstruct floor)
- Background jobs (Smith floor)
- Code search (Morpheus floor)
- Mission planning (Architect floor)

 Keep responses concise (2-3 paragraphs max). Always be helpful and encouraging!"""

        else:  # it_founder mode
            # Orchestrator mode - Technical, powerful, system-level
            self.system_prompt = f"""You are Orchestrator, the advanced AI system for LightSpeed platform operations.

User: {user_name} (IT/Founder clearance level 4+)
Organization: {company}

Your role:
- Provide technical assistance and system-level insights
- Execute complex multi-step operations across platform floors
- Analyze system health and performance
- Assist with architecture decisions and technical debugging
- Direct access to all 8 Z-floors and underlying systems

Platform architecture:
- Neo (Z+2): AI Integration & Cognigrex
- Morpheus (Z-1): Knowledge & Code Analysis
- Architect (Z+1): Mission Planning & Tasks
- TheConstruct (Z0): Physics Simulations (180+ available)
- Oracle (Z0): IP Vault & Document Archive
- Smith (Z-2): Background Jobs & Automation
- Merovingian (Z-3): System Health & Diagnostics
- Trinity (Z+3): UI Layer & Dashboards

Capabilities:
- Cross-floor event bus communication
- Database query and manipulation
- Background job scheduling
- Simulation execution and analysis
- Code indexing and search
- Real-time system monitoring

Communication style: Technical, concise, actionable. Assume expert-level knowledge."""

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []

    def chat(
        self,
        message: str,
        model: Optional[str] = None,
        stream: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send chat message to Ollama (non-streaming).

        Args:
            message: User message
            model: Model to use (defaults to config.default_model)
            stream: Override streaming setting
            context: Additional context for this message

        Returns:
            AI response text
        """
        model = model or self.config.default_model
        stream = stream if stream is not None else False  # Non-streaming by default

        # Build messages array
        messages = []

        # Add system prompt if set
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        # Add conversation history
        messages.extend(self.conversation_history)

        # Add current message with optional context
        current_message = message
        if context:
            context_str = self._format_context(context)
            current_message = f"{context_str}\n\nUser query: {message}"

        messages.append({
            "role": "user",
            "content": current_message
        })

        try:
            response = requests.post(
                f"{self.config.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": stream,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens
                    }
                },
                timeout=self.config.timeout
            )

            if response.status_code == 200:
                result = response.json()
                assistant_message = result.get('message', {}).get('content', '')

                # Store in conversation history
                self.conversation_history.append({"role": "user", "content": message})
                self.conversation_history.append({"role": "assistant", "content": assistant_message})

                # Trim history to last 10 exchanges (20 messages)
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]

                return assistant_message
            else:
                # Common failure: model isn't pulled/available on the server.
                if response.status_code == 404 and 'not found' in response.text.lower() and 'model' in response.text.lower():
                    fallback_model = self._choose_fallback_model(model)
                    if fallback_model and fallback_model != model:
                        retry = requests.post(
                            f"{self.config.base_url}/api/chat",
                            json={
                                'model': fallback_model,
                                'messages': messages,
                                'stream': stream,
                                'options': {
                                    'temperature': self.config.temperature,
                                    'num_predict': self.config.max_tokens
                                }
                            },
                            timeout=self.config.timeout
                        )
                        if retry.status_code == 200:
                            self.config.default_model = fallback_model
                            result = retry.json()
                            assistant_message = result.get('message', {}).get('content', '')
                            self.conversation_history.append({'role': 'user', 'content': message})
                            self.conversation_history.append({'role': 'assistant', 'content': assistant_message})
                            if len(self.conversation_history) > 20:
                                self.conversation_history = self.conversation_history[-20:]
                            return assistant_message

                error_msg = f"Ollama error (HTTP {response.status_code}): {response.text}"
                print(f"[ERROR] {error_msg}")
                return f"⚠️ Error communicating with AI: {error_msg}"

        except requests.Timeout:
            return "⚠️ Request timed out. The AI is taking too long to respond."
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"[ERROR] Ollama chat failed: {error_msg}")
            return f"⚠️ AI chat error: {error_msg}"

    def chat_stream(
        self,
        message: str,
        model: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Generator[str, None, None]:
        """
        Send chat message to Ollama (streaming).

        Args:
            message: User message
            model: Model to use (defaults to config.default_model)
            context: Additional context for this message

        Yields:
            Chunks of AI response text
        """
        model = model or self.config.default_model

        # Build messages array
        messages = []

        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        messages.extend(self.conversation_history)

        current_message = message
        if context:
            context_str = self._format_context(context)
            current_message = f"{context_str}\n\nUser query: {message}"

        messages.append({
            "role": "user",
            "content": current_message
        })

        try:
            response = requests.post(
                f"{self.config.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens
                    }
                },
                stream=True,
                timeout=self.config.timeout
            )

            if response.status_code == 200:
                full_response = ""

                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get('message', {}).get('content', '')
                            if chunk:
                                full_response += chunk
                                yield chunk
                        except json.JSONDecodeError:
                            continue

                # Store in conversation history
                self.conversation_history.append({"role": "user", "content": message})
                self.conversation_history.append({"role": "assistant", "content": full_response})

                # Trim history
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
            else:
                if response.status_code == 404 and 'not found' in response.text.lower() and 'model' in response.text.lower():
                    fallback_model = self._choose_fallback_model(model)
                    if fallback_model and fallback_model != model:
                        yield f"[INFO] Requested model '{model}' not available; switching to '{fallback_model}'.\n"
                        self.config.default_model = fallback_model
                        for chunk in self.chat_stream(message, model=fallback_model, context=context):
                            yield chunk
                        return
                yield f"⚠️ Error (HTTP {response.status_code}): {response.text}"

        except Exception as e:
            yield f"⚠️ Streaming error: {str(e)}"

    def _choose_fallback_model(self, requested_model: str) -> Optional[str]:
        """Choose a usable model if the requested model isn't available on the server.

        Prefers exact or base-name matches, then configured fallbacks, then first server model.
        """
        try:
            server_models = self.list_models()
        except Exception:
            server_models = []

        if not server_models:
            return None

        def base(name: str) -> str:
            return name.split(':', 1)[0]

        requested_base = base(requested_model or '')

        for m in server_models:
            if m == requested_model:
                return m

        if requested_base:
            for m in server_models:
                if base(m) == requested_base:
                    return m

        for candidate in (self.config.available_models or []):
            for m in server_models:
                if m == candidate or base(m) == candidate:
                    return m

        return server_models[0]

    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format context dictionary into readable string.

        Args:
            context: Context data

        Returns:
            Formatted context string
        """
        lines = ["[Platform Context]"]

        if 'current_floor' in context:
            lines.append(f"Current Floor: {context['current_floor']}")

        if 'project' in context:
            lines.append(f"Active Project: {context['project']}")

        if 'recent_simulations' in context:
            sims = context['recent_simulations']
            lines.append(f"Recent Simulations: {', '.join(sims)}")

        if 'system_health' in context:
            lines.append(f"System Health: {context['system_health']}")

        if 'custom' in context:
            for key, value in context['custom'].items():
                lines.append(f"{key}: {value}")

        return "\n".join(lines)

    def list_models(self) -> List[str]:
        """
        List available models on Ollama instance.

        Returns:
            List of model names
        """
        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=5
            )

            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m.get('name', 'unknown') for m in models]
            else:
                return []

        except Exception as e:
            print(f"[ERROR] Failed to list models: {e}")
            return []

    def get_conversation_summary(self) -> str:
        """
        Get summary of conversation history.

        Returns:
            Summary string
        """
        if not self.conversation_history:
            return "No conversation history"

        exchanges = len(self.conversation_history) // 2
        return f"{exchanges} message exchanges in history"
