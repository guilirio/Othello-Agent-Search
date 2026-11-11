"""Shared match execution for CLI and experiments."""
from dataclasses import asdict
from .agents import ClassicAgent
from .game import Game

AGENTS = ("random", "heuristic", "llm")


def make_agent(name, seed=0, model=None, base_url=None):
    if name == "llm":
        from .llm_agent import LLMAgent
        return LLMAgent(model_name=model, base_url=base_url)
    return ClassicAgent(name, seed)


def play_match(black="heuristic", white="random", seed=0, model=None, base_url=None):
    game = Game()
    agents = {1: make_agent(black, seed, model, base_url),
              -1: make_agent(white, seed + 1, model, base_url)}
    turns = []
    while not game.board.terminal:
        turns.append(asdict(agents[game.player].take_turn(game)))
    return {"black": black, "white": white, "seed": seed, "model": model,
            "status": game.status(), "history": game.history, "turns": turns}
