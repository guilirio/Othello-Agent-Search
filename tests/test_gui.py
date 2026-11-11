"""Opt-in UI integration tests: OTHELLO_UI_TESTS=1, requires a desktop and Tk."""
import os
from time import perf_counter
from types import SimpleNamespace
import unittest


@unittest.skipUnless(os.getenv("OTHELLO_UI_TESTS") == "1", "Teste gráfico opt-in")
class GuiTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from othello.gui import OthelloApp
        self.root = tk.Tk()
        self.root.withdraw()
        original_after = self.root.after
        self.root.after = lambda ms, *args: original_after(min(ms, 1), *args)
        self.app = OthelloApp(self.root)

    def tearDown(self):
        for timer in self.root.tk.splitlist(self.root.tk.call("after", "info")):
            self.root.after_cancel(timer)
        self.root.destroy()

    def test_human_move_and_new_game(self):
        self.app.black.set("human")
        self.app.white.set("human")
        self.app.new_game()
        self.app.click(SimpleNamespace(x=24 + 3 * 56 + 10, y=24 + 2 * 56 + 10))
        self.assertEqual(len(self.app.game.history), 1)
        self.assertEqual(self.app.game.player, -1)
        generation = self.app.generation
        self.app.new_game()
        self.app.queue.put((generation, None, None, None, "stale error"))
        self.app.poll()
        self.assertFalse(self.app.paused)
        self.assertEqual(len(self.app.game.history), 0)

    def test_agent_match_completes_without_blocking_tk(self):
        self.app.black.set("heuristic")
        self.app.white.set("random")
        self.app.new_game()
        deadline = perf_counter() + 20
        while not self.app.game.board.terminal and perf_counter() < deadline:
            self.root.update()
        self.assertTrue(self.app.game.board.terminal)
        self.assertTrue(self.app.turns)
