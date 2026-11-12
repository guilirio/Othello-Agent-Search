"""Color-balanced experiments with raw records and explicit failed games."""
import csv
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import platform

from .matches import play_match
from .providers import default_model, get_provider, validate_provider


def summarize(matches, a, b):
    summary = {key: {"agent": name, "wins": 0, "draws": 0, "losses": 0,
                     "points": 0, "moves": 0, "turns": 0, "seconds": 0.0,
                     "llm_calls": 0, "llm_seconds": 0.0, "tool_calls": 0}
               for key, name in (("a", a), ("b", b))}
    completed = [match for match in matches if "error" not in match]
    for match in completed:
        winner = match["status"]["winner"]
        for key, color in (("a", match["a_color"]), ("b", -match["a_color"])):
            item = summary[key]
            outcome = "draws" if winner == 0 else "wins" if winner == color else "losses"
            item[outcome] += 1
            item["points"] += 1 if winner == 0 else 3 if winner == color else 0
            for turn in match["turns"]:
                if turn["event"]["player"] != color:
                    continue
                item["moves"] += turn["event"]["move"] is not None
                item["turns"] += 1
                item["seconds"] += turn["seconds"]
                item["llm_calls"] += turn["llm_calls"]
                item["llm_seconds"] += turn["llm_seconds"]
                item["tool_calls"] += len(turn["tool_calls"])
    for item in summary.values():
        item["win_rate"] = item["wins"] / len(completed) if completed else None
        item["mean_turn_seconds"] = item["seconds"] / item["turns"] if item["turns"] else None
        item["mean_llm_seconds"] = item["llm_seconds"] / item["llm_calls"] if item["llm_calls"] else None
    return {"requested": len(matches), "completed": len(completed),
            "failed": len(matches) - len(completed), "agents": summary}


def run_experiments(a, b, games=20, seed=0, model=None, output=Path("artifacts/experiment")):
    if games < 2 or games % 2:
        raise ValueError("Use um número par de partidas, pelo menos 2, para equilibrar as cores.")
    provider = None
    if "llm" in (a, b):
        provider = get_provider()
        model = model or default_model(provider)
        validate_provider(model)  # falha já aqui (chave/pacote ausentes), e não como N partidas "com erro"
    matches = []
    for index in range(games):
        a_color = 1 if index % 2 == 0 else -1
        black, white = (a, b) if a_color == 1 else (b, a)
        match_seed = seed + index // 2
        try:
            match = play_match(black, white, match_seed, model)
        except Exception as exc:
            match = {"black": black, "white": white, "seed": match_seed, "error": str(exc)}
        matches.append({"index": index, "a_color": a_color, **match})
    packages = {}
    for name in ("langgraph", "langchain-ollama", "langchain-google-genai", "langchain-groq"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = "not installed"
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
              "platform": platform.platform(), "packages": packages, "seed": seed,
              "provider": provider, "model": model, "summary": summarize(matches, a, b), "matches": matches}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = [{"participant": key, **value} for key, value in report["summary"]["agents"].items()]
    with (output / "summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "summary.json").write_text(json.dumps({key: value for key, value in report.items() if key != "matches"},
                                                  ensure_ascii=False, indent=2), encoding="utf-8")
    return report