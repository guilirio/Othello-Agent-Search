"""Agent contract: one call executes exactly one valid action through tools."""
from dataclasses import dataclass, field
import random
from time import perf_counter
from typing import Protocol

from .game import Game
from .tools import GameTools


@dataclass
class TurnResult:
    event: dict
    seconds: float
    llm_calls: int = 0
    llm_seconds: float = 0
    tool_calls: list[dict] = field(default_factory=list)
    plan: dict = field(default_factory=dict)


class Agent(Protocol):
    name: str

    def take_turn(self, game: Game) -> TurnResult: ...


class ClassicAgent:
    def __init__(self, name: str = "heuristic", seed: int = 0):
        if name not in ("random", "heuristic"):
            raise ValueError("Agente clássico desconhecido.")
        self.name = name
        self.rng = random.Random(seed)

    def take_turn(self, game: Game) -> TurnResult:
        start, tools = perf_counter(), GameTools(game)
        moves = tools.invoke("get_valid_moves")
        explanation = "Passe obrigatório: não há jogada válida."
        move = None
        if moves:
            if self.name == "random":
                move = self.rng.choice(moves)
                explanation = "Escolha aleatória uniforme entre jogadas válidas."
            else:
                ranked = tools.invoke("evaluate_moves")
                best = [item for item in ranked if item["score"] == ranked[0]["score"]]
                chosen = self.rng.choice(best)
                move = chosen["move"]
                explanation = f"Heurística balanced: score={chosen['score']}, componentes={chosen['features']}."
        event = tools.invoke("make_move", row=move[0] if move else None,
                             column=move[1] if move else None, explanation=explanation)
        return TurnResult(event, perf_counter() - start, tool_calls=tools.calls)
