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
    args = parser.parse_args()
    try:
        if args.command in (None, "gui"):
            from .gui import launch
            launch()
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
