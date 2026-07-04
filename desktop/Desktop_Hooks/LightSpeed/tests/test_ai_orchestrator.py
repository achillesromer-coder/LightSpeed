from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "Z Axis" / "Z+2_Neo" / "components" / "ai_orchestrator.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("lightspeed_test_ai_orchestrator", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _FakeOllama:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, *, prompt: str, stream: bool) -> str:
        self.prompts.append(prompt)
        return "local-achilles-response"


def test_achilles_binds_to_local_ollama_with_governed_persona() -> None:
    module = _load_module()
    orchestrator = module.AIOrchestrator.__new__(module.AIOrchestrator)
    orchestrator.ollama_instance = _FakeOllama()
    orchestrator.achilles_instance = None
    orchestrator.current_backend = module.AIBackend.OLLAMA
    orchestrator.active_contexts = {}
    orchestrator.config = {
        "achilles": {"enabled": True, "approval_gated": True},
        "modes": {
            "achilles": {
                "system_prompt": "You are Achilles, the local Cognigrex operator.",
            }
        },
    }

    assert orchestrator._bind_local_achilles() is True
    assert orchestrator.switch_backend(module.AIBackend.ACHILLES) is True

    context = orchestrator.create_context(
        user_id="operator",
        company="Romer",
        project="LightSpeed",
        mode=module.AIMode.ACHILLES,
    )
    response = orchestrator.process_message("operator_Romer_LightSpeed", "Review the queue.")

    assert response == "local-achilles-response"
    assert "approval-gated" in orchestrator.achilles_instance.prompts[0]
    assert context.history[-1]["content"] == response
