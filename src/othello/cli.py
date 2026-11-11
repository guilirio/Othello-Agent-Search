import argparse
import json
from pathlib import Path
import sys

from .matches import AGENTS, play_match


def main():
    parser = argparse.ArgumentParser(description="Othello Agent Search")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("gui", help="Abre a interface desktop")
    play = commands.add_parser("play", help="Executa uma partida entre agentes")
    play.add_argument("--black", choices=AGENTS, default="heuristic")
    play.add_argument("--white", choices=AGENTS, default="random")
    play.add_argument("--seed", type=int, default=0)
    play.add_argument("--model")
    play.add_argument("--json", type=Path, dest="output")
    experiment = commands.add_parser("experiment", help="Compara estratégias com cores alternadas")
    experiment.add_argument("--a", choices=AGENTS, default="heuristic")
    experiment.add_argument("--b", choices=AGENTS, default="random")
    experiment.add_argument("--games", type=int, default=20)
    experiment.add_argument("--seed", type=int, default=0)
    experiment.add_argument("--model")
    experiment.add_argument("--output", type=Path, default=Path("artifacts/experiment"))
    args = parser.parse_args()
    try:
        if args.command in (None, "gui"):
            from .gui import launch
            launch()
        elif args.command == "experiment":
            from .experiments import run_experiments
            result = run_experiments(args.a, args.b, args.games, args.seed, args.model, args.output)
            print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
            return 1 if result["summary"]["failed"] else 0
        else:
            result = play_match(args.black, args.white, args.seed, args.model)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(result["status"], ensure_ascii=False))
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    return 0
