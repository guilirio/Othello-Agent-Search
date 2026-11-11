"""Validated tools scoped to exactly one player's turn."""
from copy import deepcopy
from time import perf_counter

from .evaluation import rank_moves
from .game import Game


class GameTools:
    def __init__(self, game: Game):
        self.game = game
        self.player = game.player
        self.start_turn = len(game.history)
        self.calls: list[dict] = []

    def invoke(self, name: str, **arguments):
        allowed = {"get_board_state", "get_valid_moves", "make_move", "get_game_status", "evaluate_moves"}
        if name not in allowed:
            raise ValueError("Ferramenta desconhecida.")
        start = perf_counter()
        record = {"name": name, "arguments": arguments}
        try:
            result = getattr(self, name)(**arguments)
            record["result"] = deepcopy(result)
            return result
        except (ValueError, TypeError, KeyError) as exc:
            record["error"] = str(exc)
            raise
        finally:
            record["seconds"] = perf_counter() - start
            self.calls.append(record)

    def get_board_state(self):
        return {"cells": list(self.game.board.cells), "player": self.game.player,
                "history": deepcopy(self.game.history)}

    def get_valid_moves(self):
        return [list(move) for move in self.game.board.legal_moves(self.game.player)]

    def get_game_status(self):
        return self.game.status()

    def evaluate_moves(self, strategy: str = "balanced"):
        return rank_moves(self.game.board, self.game.player, strategy)

    def make_move(self, row: int | None = None, column: int | None = None, explanation: str = ""):
        if len(self.game.history) != self.start_turn or self.game.player != self.player:
            raise ValueError("Esta ferramenta já executou uma ação ou o turno mudou.")
        if not isinstance(explanation, str):
            raise ValueError("A explicação deve ser texto.")
        if row is None and column is None:
            move = None
        elif type(row) is int and type(column) is int and 0 <= row < 8 and 0 <= column < 8:
            move = (row, column)
        else:
            raise ValueError("Coordenadas devem ser inteiros de 0 a 7, ou ambas nulas para passe.")
        return self.game.apply(move, explanation)
