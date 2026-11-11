import random
import unittest

from othello.game import BLACK, WHITE, Board, Game


class RulesTests(unittest.TestCase):
    def test_opening_and_immutability(self):
        board = Board.initial()
        self.assertEqual(set(board.legal_moves(BLACK)), {(2, 3), (3, 2), (4, 5), (5, 4)})
        self.assertEqual(board.play((2, 3), BLACK).score(), {"black": 4, "white": 1})
        self.assertEqual(board.score(), {"black": 2, "white": 2})

    def test_all_eight_directions(self):
        cells = [0] * 64
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    cells[(3 + dr) * 8 + 3 + dc] = WHITE
                    cells[(3 + 2 * dr) * 8 + 3 + 2 * dc] = BLACK
        board = Board(tuple(cells))
        self.assertEqual(len(board.flips((3, 3), BLACK)), 8)
        self.assertEqual(board.play((3, 3), BLACK).score()["white"], 0)

    def test_illegal_moves_do_not_change_game(self):
        game = Game()
        for move in (None, (0, 0), (3, 3), (-1, 3), (8, 0)):
            with self.assertRaises(ValueError):
                game.apply(move)
        self.assertEqual(game.history, [])
        self.assertEqual(game.player, BLACK)

    def test_pass_and_terminal_with_empty_square(self):
        cells = [BLACK] * 64
        cells[0], cells[1] = 0, WHITE
        game = Game(Board(tuple(cells)), WHITE)
        self.assertTrue(game.status()["must_pass"])
        game.apply(None)
        game.apply((0, 0))
        self.assertEqual(game.status()["winner"], BLACK)
        cells[2] = 0
        cells[1] = BLACK
        self.assertTrue(Board(tuple(cells)).terminal)
        with self.assertRaises(ValueError):
            game.apply(None)

    def test_seeded_full_games_preserve_invariants(self):
        for seed in range(12):
            rng, game = random.Random(seed), Game()
            while not game.board.terminal:
                before = 64 - game.board.cells.count(0)
                moves = game.board.legal_moves(game.player)
                game.apply(rng.choice(moves) if moves else None)
                self.assertEqual(64 - game.board.cells.count(0), before + bool(moves))
                self.assertLessEqual(len(game.history), 120)
            self.assertIn(game.status()["winner"], (-1, 0, 1))
