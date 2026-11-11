"""Pure Othello rules. Coordinates are zero-based (row, column)."""
from dataclasses import dataclass, field

BLACK, WHITE, EMPTY = 1, -1, 0
DIRECTIONS = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if (r, c) != (0, 0))
Move = tuple[int, int]


@dataclass(frozen=True)
class Board:
    cells: tuple[int, ...]

    def __post_init__(self):
        if len(self.cells) != 64 or any(v not in (BLACK, WHITE, EMPTY) for v in self.cells):
            raise ValueError("O tabuleiro deve conter 64 casas com valores -1, 0 ou 1.")

    @classmethod
    def initial(cls):
        cells = [EMPTY] * 64
        cells[27] = cells[36] = WHITE
        cells[28] = cells[35] = BLACK
        return cls(tuple(cells))

    def flips(self, move: Move, player: int) -> tuple[int, ...]:
        if player not in (BLACK, WHITE):
            raise ValueError("Jogador inválido.")
        r, c = move
        if not (0 <= r < 8 and 0 <= c < 8) or self.cells[r * 8 + c] != EMPTY:
            return ()
        result = []
        for dr, dc in DIRECTIONS:
            rr, cc, line = r + dr, c + dc, []
            while 0 <= rr < 8 and 0 <= cc < 8 and self.cells[rr * 8 + cc] == -player:
                line.append(rr * 8 + cc)
                rr, cc = rr + dr, cc + dc
            if line and 0 <= rr < 8 and 0 <= cc < 8 and self.cells[rr * 8 + cc] == player:
                result.extend(line)
        return tuple(result)

    def legal_moves(self, player: int) -> tuple[Move, ...]:
        return tuple((r, c) for r in range(8) for c in range(8) if self.flips((r, c), player))

    def play(self, move: Move, player: int):
        flips = self.flips(move, player)
        if not flips:
            raise ValueError("Jogada ilegal.")
        cells = list(self.cells)
        cells[move[0] * 8 + move[1]] = player
        for index in flips:
            cells[index] = player
        return Board(tuple(cells))

    @property
    def terminal(self):
        return not self.legal_moves(BLACK) and not self.legal_moves(WHITE)

    def score(self):
        return {"black": self.cells.count(BLACK), "white": self.cells.count(WHITE)}


@dataclass
class Game:
    board: Board = field(default_factory=Board.initial)
    player: int = BLACK
    history: list[dict] = field(default_factory=list)

    def status(self):
        score = self.board.score()
        finished = self.board.terminal
        difference = score["black"] - score["white"]
        return {"finished": finished, "player": self.player, "score": score,
                "winner": (BLACK if difference > 0 else WHITE if difference < 0 else 0) if finished else None,
                "must_pass": not finished and not self.board.legal_moves(self.player),
                "turn": len(self.history)}

    def apply(self, move: Move | None, explanation: str = ""):
        if self.board.terminal:
            raise ValueError("A partida já terminou.")
        if move is None:
            if self.board.legal_moves(self.player):
                raise ValueError("Passe proibido: existem jogadas válidas.")
        else:
            self.board = self.board.play(move, self.player)
        event = {"turn": len(self.history) + 1, "player": self.player,
                 "move": list(move) if move is not None else None,
                 "explanation": explanation, "score": self.board.score()}
        self.history.append(event)
        self.player = -self.player
        return dict(event)
