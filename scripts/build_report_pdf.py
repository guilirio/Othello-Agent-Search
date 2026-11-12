from pathlib import Path
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle, KeepTogether)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "report.md"
OUTPUT = ROOT / "output" / "pdf" / "relatorio-othello.pdf"
FONT_DIR = Path("C:/Windows/Fonts")


def register_fonts():
    pdfmetrics.registerFont(TTFont("Arial", str(FONT_DIR / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_DIR / "arialbd.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Italic", str(FONT_DIR / "ariali.ttf")))
    pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic")


def inline_markup(text):
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    return text


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BodyPT", fontName="Arial", fontSize=9.4, leading=14,
                              textColor=colors.HexColor("#26332F"), spaceAfter=6, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="H1PT", fontName="Arial-Bold", fontSize=16, leading=21,
                              textColor=colors.HexColor("#174B3A"), spaceBefore=15, spaceAfter=8,
                              keepWithNext=True))
    styles.add(ParagraphStyle(name="H2PT", fontName="Arial-Bold", fontSize=11.5, leading=15,
                              textColor=colors.HexColor("#24745A"), spaceBefore=10, spaceAfter=5,
                              keepWithNext=True))
    styles.add(ParagraphStyle(name="SmallPT", fontName="Arial", fontSize=8, leading=11,
                              textColor=colors.HexColor("#52615B"), spaceAfter=4))
    styles.add(ParagraphStyle(name="CodePT", fontName="Courier", fontSize=8, leading=11,
                              textColor=colors.HexColor("#22342D"), backColor=colors.HexColor("#EEF3F0"),
                              borderPadding=7, leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=8))
    styles.add(ParagraphStyle(name="BulletPT", parent=styles["BodyPT"], leftIndent=14,
                              firstLineIndent=-9, spaceAfter=4))
    styles.add(ParagraphStyle(name="TablePT", fontName="Arial", fontSize=7.8, leading=10,
                              textColor=colors.HexColor("#26332F")))
    styles.add(ParagraphStyle(name="TableHeadPT", fontName="Arial-Bold", fontSize=7.8, leading=10,
                              textColor=colors.white))
    return styles


def on_page(canvas, doc):
    canvas.saveState()
    width, height = A4
    if doc.page > 1:
        canvas.setStrokeColor(colors.HexColor("#D8E1DC"))
        canvas.setLineWidth(0.5)
        canvas.line(22 * mm, height - 15 * mm, width - 22 * mm, height - 15 * mm)
        canvas.setFont("Arial-Bold", 7.5)
        canvas.setFillColor(colors.HexColor("#24745A"))
        canvas.drawString(22 * mm, height - 12 * mm, "Othello Agent Search")
        canvas.setFont("Arial", 7.5)
        canvas.setFillColor(colors.HexColor("#65736D"))
        canvas.drawRightString(width - 22 * mm, 12 * mm, f"Relatório técnico  •  {doc.page}")
    canvas.restoreState()


def to_story(markdown, styles):
    lines = markdown.splitlines()
    story = []
    i = 0
    in_code = False
    code = []
    paragraph = []

    def flush_paragraph():
        if paragraph:
            story.append(Paragraph(inline_markup(" ".join(part.strip() for part in paragraph)), styles["BodyPT"]))
            paragraph.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                story.append(Paragraph(escape("\n".join(code)), styles["CodePT"]))
                code.clear()
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code.append(line)
            i += 1
            continue
        if not line.strip():
            flush_paragraph()
            i += 1
            continue
        if line.startswith("# "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[2:]), styles["H1PT"]))
            i += 1
            continue
        if line.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[3:]), styles["H2PT"]))
            i += 1
            continue
        if line.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[4:]), styles["SmallPT"]))
            i += 1
            continue
        if line.startswith("| "):
            flush_paragraph()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                raw = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-: ]+", cell or " ") for cell in raw):
                    rows.append(raw)
                i += 1
            table_data = []
            for row_idx, row in enumerate(rows):
                style = styles["TableHeadPT"] if row_idx == 0 else styles["TablePT"]
                table_data.append([Paragraph(inline_markup(cell), style) for cell in row])
            widths = available_width = A4[0] - 44 * mm
            count = max(1, len(rows[0]))
            col_widths = [available_width / count] * count
            # Give long descriptive columns more room in two-column requirement/result tables.
            if count == 2:
                col_widths = [available_width * 0.32, available_width * 0.68]
            table = Table(table_data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#174B3A")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CAD6D0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F7F5")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.extend([Spacer(1, 3), table, Spacer(1, 6)])
            continue
        if line.startswith("- "):
            flush_paragraph()
            story.append(Paragraph("•  " + inline_markup(line[2:]), styles["BulletPT"]))
            i += 1
            continue
        if line.startswith("**") and line.endswith("  "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line.rstrip()), styles["SmallPT"]))
            i += 1
            continue
        paragraph.append(line)
        i += 1
    flush_paragraph()
    return story


def main():
    register_fonts()
    styles = make_styles()
    text = SOURCE.read_text(encoding="utf-8")
    text = text[text.index("## Resumo"):]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(OUTPUT), pagesize=A4, title="Agentes Inteligentes para Othello",
                          author="Projeto Othello Agent Search",
                          leftMargin=22 * mm, rightMargin=22 * mm,
                          topMargin=23 * mm, bottomMargin=20 * mm)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=on_page)])

    title = [Spacer(1, 36 * mm),
             Paragraph("AGENTES INTELIGENTES<br/>PARA OTHELLO", ParagraphStyle(
                 "CoverTitle", fontName="Arial-Bold", fontSize=27, leading=33,
                 textColor=colors.HexColor("#174B3A"), alignment=TA_CENTER, spaceAfter=12)),
             Paragraph("Relatório técnico", ParagraphStyle(
                 "CoverSub", fontName="Arial", fontSize=17, leading=23,
                 textColor=colors.HexColor("#5A6C64"), alignment=TA_CENTER, spaceAfter=26)),
             Paragraph("GCC128 - Inteligência Artificial", ParagraphStyle(
                 "CoverCourse", fontName="Arial-Bold", fontSize=12, leading=17,
                 textColor=colors.HexColor("#26332F"), alignment=TA_CENTER, spaceAfter=6)),
             Paragraph("Projeto Othello Agent Search", ParagraphStyle(
                 "CoverProject", fontName="Arial", fontSize=11, leading=16,
                 textColor=colors.HexColor("#52615B"), alignment=TA_CENTER)),
             Spacer(1, 75 * mm),
             Paragraph("11 de novembro de 2026", ParagraphStyle(
                 "CoverDate", fontName="Arial", fontSize=10, leading=14,
                 textColor=colors.HexColor("#52615B"), alignment=TA_CENTER)),
             PageBreak()]
    body = to_story(text, styles)
    doc.build(title + body)
    print(OUTPUT)


if __name__ == "__main__":
    main()
