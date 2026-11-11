import tempfile
import unittest
from unittest.mock import patch

from othello.experiments import run_experiments
from othello.matches import play_match


class ExperimentTests(unittest.TestCase):
    def test_seed_reproduces_moves(self):
        first = play_match("random", "heuristic", 17)
        second = play_match("random", "heuristic", 17)
        self.assertEqual(first["history"], second["history"])

    def test_colors_metrics_and_export(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run_experiments("heuristic", "random", 2, 17, output=directory)
        self.assertEqual([m["a_color"] for m in report["matches"]], [1, -1])
        self.assertEqual(report["summary"]["completed"], 2)
        for metrics in report["summary"]["agents"].values():
            self.assertEqual(metrics["wins"] + metrics["losses"] + metrics["draws"], 2)
            self.assertEqual(metrics["llm_calls"], 0)
            self.assertGreater(metrics["tool_calls"], 0)

    def test_failures_are_not_losses_or_draws(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("othello.experiments.play_match", side_effect=RuntimeError("offline")):
                report = run_experiments("llm", "heuristic", 2, output=directory)
        self.assertEqual(report["summary"]["failed"], 2)
        self.assertIsNone(report["summary"]["agents"]["a"]["win_rate"])
        self.assertEqual(report["summary"]["agents"]["a"]["losses"], 0)

    def test_odd_game_counts_are_rejected(self):
        with self.assertRaises(ValueError):
            run_experiments("heuristic", "random", 3)
