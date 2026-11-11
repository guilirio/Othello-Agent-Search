"""Create the requested ZIP only when real author names, report and video URL are provided."""
import argparse
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse
from zipfile import ZipFile, ZIP_DEFLATED


def main():
    parser = argparse.ArgumentParser(description="Empacota código versionado e entrega acadêmica.")
    parser.add_argument("--authors", nargs=2, required=True, metavar=("NOME1", "NOME2"))
    parser.add_argument("--video-url", required=True)
    parser.add_argument("--report", type=Path, required=True, help="Relatório final revisado")
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    args = parser.parse_args()
    if any(not re.fullmatch(r"[A-Za-z0-9-]+", name) for name in args.authors):
        parser.error("Use nomes sem espaços, acentos ou caminhos; exemplo: guilherme colega.")
    url = urlparse(args.video_url)
    if url.scheme != "https" or not url.netloc:
        parser.error("Forneça o link HTTPS real do vídeo.")
    if not args.report.is_file() or args.report.suffix.lower() not in (".pdf", ".md", ".docx"):
        parser.error("Informe um relatório existente em PDF, Markdown ou DOCX.")
    if args.report.suffix.lower() == ".md" and "STATUS: DRAFT" in args.report.read_text(encoding="utf-8"):
        parser.error("O relatório ainda está marcado como rascunho; finalize os experimentos e revise-o.")
    root = Path(__file__).resolve().parents[1]
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    if status.strip():
        parser.error("Faça commit das alterações antes de gerar a entrega.")
    files = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode("utf-8").split("\0")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / ("_".join(args.authors) + ".zip")
    with ZipFile(output, "x", ZIP_DEFLATED) as archive:
        for name in filter(None, files):
            archive.write(root / name, "codigo/" + name)
        archive.write(args.report, "relatorio" + args.report.suffix.lower())
        archive.writestr("video-link.txt", args.video_url + "\n")
        archive.writestr("autores.txt", "\n".join(args.authors) + "\n")
    print(output.resolve())


if __name__ == "__main__":
    main()
