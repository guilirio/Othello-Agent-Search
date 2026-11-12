import json
from types import SimpleNamespace
import unittest

from othello.game import Board, Game
from othello.llm_agent import AgentError, LLMAgent


class ScriptedModel:
    """Test double only; never presented as an LLM benchmark."""
    def __init__(self, responses):
        self.responses = iter(responses)
        self.messages = []

    def invoke(self, messages):
        self.messages.append(messages)
        return SimpleNamespace(content=next(self.responses))


MOVE = json.dumps({"strategy": "balanced", "row": 2, "column": 3,
                   "explanation": "Jogada legal com avaliação disponível."})


class WorkflowTests(unittest.TestCase):
    def test_real_graph_tools_memory_and_metrics(self):
        model = ScriptedModel([MOVE])
        game = Game()
        result = LLMAgent(model).take_turn(game)
        self.assertEqual(result.llm_calls, 1)
        self.assertEqual(len(game.history), 1)
        self.assertEqual([c["name"] for c in result.tool_calls], [
            "get_board_state", "get_valid_moves", "get_game_status", "evaluate_moves",
            "evaluate_moves", "evaluate_moves", "make_move", "get_game_status"])
        game.apply(game.board.legal_moves(game.player)[0])
        move = game.board.legal_moves(game.player)[0]
        model = ScriptedModel([json.dumps({"strategy": "balanced", "row": move[0],
                                           "column": move[1], "explanation": "Legal"})])
        LLMAgent(model).take_turn(game)
        payload = json.loads(model.messages[0][1][1])
        self.assertEqual(len(payload["data"]["observation"]["history"]), 2)

    def test_invalid_output_retries_but_never_falls_back(self):
        game = Game()
        with self.assertRaises(AgentError):
            LLMAgent(ScriptedModel(['{"strategy":"balanced","row":0,"column":0,"explanation":"bad"}',
                                    'invalid', 'still invalid'])).take_turn(game)
        self.assertEqual(game.history, [])
        result = LLMAgent(ScriptedModel(["invalid", MOVE])).take_turn(game)
        self.assertEqual(result.llm_calls, 2)

    def test_forced_pass_avoids_unnecessary_model_call(self):
        cells = [1] * 64
        cells[0], cells[1] = 0, -1
        game = Game(Board(tuple(cells)), -1)
        result = LLMAgent(ScriptedModel([])).take_turn(game)
        self.assertIsNone(result.event["move"])
        self.assertEqual(result.llm_calls, 0)
