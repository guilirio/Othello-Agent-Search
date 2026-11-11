import unittest
from othello.agents import ClassicAgent
from othello.evaluation import evaluate, rank_moves
from othello.game import Board, Game
from othello.tools import GameTools


class ToolsTests(unittest.TestCase):
    def test_scope_prevents_two_actions(self):
        game = Game()
        tools = GameTools(game)
        tools.invoke("make_move", row=2, column=3)
        with self.assertRaises(ValueError):
            tools.invoke("make_move", row=2, column=2)
        self.assertEqual(len(game.history), 1)
        self.assertIn("error", tools.calls[-1])

    def test_bad_types_and_history_isolation(self):
        game = Game()
        tools = GameTools(game)
        for row, column in ((True, 3), (2, None), (2.0, 3)):
            with self.assertRaises(ValueError):
                tools.invoke("make_move", row=row, column=column)
        tools.get_board_state()["history"].append({"fake": True})
        self.assertEqual(game.history, [])

    def test_heuristic_symmetry_and_terminal(self):
        board = Board.initial().play((2, 3), 1)
        self.assertEqual(evaluate(board, 1)["score"], -evaluate(board, -1)["score"])
        self.assertEqual(len(rank_moves(Board.initial(), 1)), 4)
        self.assertGreater(evaluate(Board((1,) * 64), 1)["score"], 100000)

    def test_complete_classic_match(self):
        game = Game()
        agents = {1: ClassicAgent("heuristic"), -1: ClassicAgent("random")}
        while not game.board.terminal:
            result = agents[game.player].take_turn(game)
            self.assertTrue(result.tool_calls)
        self.assertLessEqual(len(game.history), 120)
