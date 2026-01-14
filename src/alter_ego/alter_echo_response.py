"""Combine LLM output, echo metadata, and persona styling."""

from __future__ import annotations

from pathlib import Path

try:
    from Lyss.modules.emotional_parser import analyze_emotion  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    from echo_whisper_layer import analyze_emotion  # type: ignore

if __package__:
    from .configuration import get_persona_root
else:
    from configuration import get_persona_root
from persona_fronting import PersonaFronting
from persona_simulator import PersonaSimulator


class AlterEchoResponse:
    def __init__(self, persona_dir: str | Path | None = None) -> None:
        root = Path(persona_dir) if persona_dir is not None else get_persona_root()
        root = Path(root)
        if not root.exists():
            root = Path(__file__).resolve().parent / "personas"
        self.simulator = PersonaSimulator(root)
        self.fronting = PersonaFronting()

    def respond(self, prompt: str, llm_output: str):
        echo = analyze_emotion((prompt or "") + (llm_output or ""))
        persona = self.fronting.get_active() or "Rhea"
        styled = self.simulator.simulate(persona, llm_output)
        if isinstance(styled, str) and styled.startswith("[Error: Persona"):
            styled = llm_output
        return styled, echo


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    aer = AlterEchoResponse()
    response, echo = aer.respond("I'm feeling scattered today...", "Maybe we slow down and breathe together?")
    print(response)
    print("-- Echo:", echo)
