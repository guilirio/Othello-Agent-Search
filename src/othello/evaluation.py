"""Explainable one-ply evaluation, always from the acting player's perspective."""
from .game import Board

CORNERS = (0, 7, 56, 63)
NEIGHBORS = {0: (1, 8, 9), 7: (6, 14, 15), 56: (48, 49, 57), 63: (54, 55, 62)}
WEIGHTS = {
    "balanced": {"corners": 30, "mobility": 5, "discs": 1, "risk": -10},
    "mobility": {"corners": 25, "mobility": 10, "discs": 1, "risk": -10},
    "corners": {"corners": 50, "mobility": 4, "discs": 1, "risk": -15},
}


def evaluate(board: Board, player: int, strategy: str = "balanced") -> dict:
    weights = WEIGHTS[strategy]
    cells = board.cells
    features = {
        "corners": sum(cells[i] * player for i in CORNERS),
        "mobility": len(board.legal_moves(player)) - len(board.legal_moves(-player)),
        "discs": cells.count(player) - cells.count(-player),
        "risk": sum(cells[i] * player for corner, neighbors in NEIGHBORS.items()
                    if cells[corner] == 0 for i in neighbors),
    }
    score = sum(features[key] * value for key, value in weights.items())
    if board.terminal:
        difference = features["discs"]
        score = (100000 if difference > 0 else -100000 if difference < 0 else 0) + difference
    return {"score": score, "features": features}


def rank_moves(board: Board, player: int, strategy: str = "balanced") -> list[dict]:
    return sorted(({"move": list(move), **evaluate(board.play(move, player), player, strategy)}
                   for move in board.legal_moves(player)), key=lambda item: -item["score"])
