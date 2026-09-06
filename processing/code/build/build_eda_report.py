"""Build the concise EDA report from the executed notebook and saved figures."""

from __future__ import annotations

import html
import re
import subprocess
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[3]
NOTEBOOK = ROOT / "processing" / "notebooks" / "Group030_EDA.ipynb"
FIGURES = ROOT / "processing" / "figures"
LOGO = ROOT / "processing" / "assets" / "monash-university-logo.svg"
REPORT_DIR = ROOT / "processing" / "report"
HTML_PATH = REPORT_DIR / "Group030_EDA_report.html"
PDF_PATH = ROOT / "Group030_EDA.pdf"


def markdown_text() -> str:
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    return "\n\n".join(
        cell.source for cell in notebook.cells if cell.cell_type == "markdown"
    )


def section(text: str, start: str, end: str | None = None) -> str:
    start_at = text.index(start) + len(start)
    end_at = text.index(end, start_at) if end else len(text)
    return text[start_at:end_at].strip()


def inline(text: str) -> str:
    escaped = html.escape(text.strip())
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    escaped = re.sub(
        r"(https?://[^\s<]+)",
        lambda match: f'<a href="{match.group(1)}">{match.group(1)}</a>',
        escaped,
    )
    return escaped


def paragraphs(text: str) -> str:
    return "".join(
        f"<p>{inline(block.replace(chr(10), ' '))}</p>"
        for block in re.split(r"\n\s*\n", text.strip())
        if block.strip()
    )


def figure_contract(text: str, number: int) -> tuple[str, str]:
    pattern = rf"## Figure {number} — (.+?)\n\n(.+?)(?=\n\n## Figure {number + 1} —|\n\n## 4\.)"
    match = re.search(pattern, text, flags=re.S)
    if not match:
        raise ValueError(f"Figure {number} section not found")
    title = match.group(1).strip()
    body = match.group(2).strip()
    parts = re.split(r"\n\n", body)
    contract = parts[0]
    interpretation = parts[-1]
    return title, contract + "\n\n" + interpretation


def figure_block(text: str, number: int, css_class: str = "") -> str:
    title, body = figure_contract(text, number)
    image_uri = (FIGURES / f"Figure_{number}.png").resolve().as_uri()
    return f"""
    <article class="figure-block {css_class}">
      <h3>Figure {number}. {inline(title)}</h3>
      <img src="{image_uri}" alt="Figure {number}">
      <div class="figure-note">{paragraphs(body)}</div>
    </article>
    """


def findings(text: str) -> list[str]:
    body = section(text, "## 5. Ten evidence-based findings", "## 6. Five future machine-learning questions")
    result = re.findall(r"(?ms)^\d+\. (.*?)(?=^\d+\. |\Z)", body)
    if len(result) != 10:
        raise ValueError(f"Expected 10 findings, found {len(result)}")
    return [item.strip() for item in result]


def ml_rows(text: str) -> list[list[str]]:
    body = section(text, "## 6. Five future machine-learning questions", "## 7. Limitations and conclusion")
    rows = []
    for line in body.splitlines():
        if line.startswith("| **MLQ-"):
            rows.append([cell.strip() for cell in line.strip("|").split("|")])
    if len(rows) != 5:
        raise ValueError(f"Expected 5 ML questions, found {len(rows)}")
    return rows


def finding_list(items: list[str], start: int) -> str:
    return "".join(
        f'<div class="finding"><span>{number}</span><p>{inline(item)}</p></div>'
        for number, item in enumerate(items, start=start)
    )


def ml_cards(rows: list[list[str]], start: int) -> str:
    cards = []
    labels = ["Question and decision", "Unit and target", "Decision-time predictors", "Validation", "Risk"]
    for row in rows:
        title = re.sub(r"\*", "", row[0])
        details = "".join(
            f"<dt>{label}</dt><dd>{inline(value)}</dd>"
            for label, value in zip(labels, row[1:])
        )
        cards.append(f'<article class="ml-card"><h3>{title}</h3><dl>{details}</dl></article>')
    return "".join(cards)


def build_html() -> str:
    text = markdown_text()
    assurance = section(text, "## Data-preparation assurance", "## 0. Configuration")
    limits = section(text, "## 7. Limitations and conclusion", "## References used for method choices")
    refs = section(text, "## References used for method choices")
    finding_items = findings(text)
    questions = ml_rows(text)
    logo_uri = LOGO.resolve().as_uri()

    css = """
    @page { size: A4; margin: 18mm 20mm 17mm; }
    @page cover { margin: 0; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: "Times New Roman", Times, serif; color: #111;
           font-size: 10.5pt; line-height: 1.38; }
    .page { break-after: page; min-height: 262mm; position: relative; }
    .page:last-child { break-after: auto; }
    .cover { page: cover; height: 297mm; padding: 30mm 28mm; text-align: center; }
    .cover img { width: 72mm; margin-top: 12mm; }
    .cover h1 { margin: 48mm auto 0; font-size: 25pt; line-height: 1.2; font-weight: normal; }
    .cover h2 { margin: 8mm 0 0; font-size: 16pt; font-weight: normal; }
    .cover .course { margin-top: 45mm; font-size: 13pt; }
    .cover .members { margin-top: 7mm; line-height: 1.8; }
    h1.section-title { font-size: 16pt; margin: 0 0 6mm; border-bottom: 0.5pt solid #111;
                       padding-bottom: 2mm; font-weight: bold; }
    h2 { font-size: 13pt; margin: 5mm 0 2.5mm; }
    h3 { font-size: 11pt; margin: 0 0 2mm; }
    p { margin: 0 0 3mm; }
    code { font-family: "Courier New", monospace; font-size: 8.5pt; }
    .table-summary { width: 100%; border-collapse: collapse; margin: 5mm 0; }
    .table-summary th, .table-summary td { padding: 2.2mm 3mm; border-bottom: 0.5pt solid #777; text-align: left; }
    .table-summary th { border-top: 1pt solid #111; border-bottom: 1pt solid #111; }
    .figure-block { break-inside: avoid; margin-bottom: 5mm; }
    .figure-block img { display: block; width: 100%; max-height: 105mm; object-fit: contain; margin: 1mm auto 2mm; }
    .figure-block.large img { max-height: 150mm; }
    .figure-block.medium img { max-height: 94mm; }
    .figure-block.compact { margin-bottom: 3mm; }
    .figure-block.compact img { max-height: 62mm; }
    .figure-block.compact .figure-note { font-size: 8pt; line-height: 1.25; }
    .figure-block.compact .figure-note p { margin-bottom: 1.5mm; }
    .figure-note { font-size: 8.6pt; }
    .finding { display: grid; grid-template-columns: 7mm auto; gap: 2mm; margin-bottom: 4mm; break-inside: avoid; }
    .finding > span { font-weight: bold; }
    .finding p { margin: 0; }
    .ml-card { break-inside: avoid; border-top: 0.75pt solid #111; padding: 3mm 0 2mm; margin-bottom: 3mm; }
    dl { display: grid; grid-template-columns: 35mm auto; margin: 0; font-size: 8.8pt; }
    dt { font-weight: bold; padding: 1mm 2mm 1mm 0; }
    dd { margin: 0; padding: 1mm 0; }
    .conclusion { margin-top: 5mm; padding-top: 4mm; border-top: 0.75pt solid #111; }
    .footer { position: absolute; bottom: 0; left: 0; right: 0; text-align: center; font-size: 9pt; }
    .references { font-size: 9pt; }
    a { color: #111; text-decoration: none; }
    """

    def page(title: str, body: str, number: str = "") -> str:
        footer = f'<div class="footer">{number}</div>' if number else ""
        return f'<section class="page"><h1 class="section-title">{title}</h1>{body}{footer}</section>'

    html_doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>Group030 EDA</title>
    <style>{css}</style></head><body>
    <section class="page cover"><img src="{logo_uri}" alt="Monash University">
      <h1>Exploratory Data Analysis</h1><h2>Assessment 1 · Group030</h2>
      <div class="course">FIT5196 Data Wrangling</div>
      <div class="members">King Man Chan · Yinglin Fang · Sizhe Hong<br>Xinhang Ren · Guohou Zhang</div>
    </section>
    {page('1. Context, preparation and analytical approach', '<p>This report examines commercial and operational patterns in six standardised relational tables created from the allocated Group030 JSON and XML sources: 5,000 orders, 15,723 order-item lines, 500 customers, 5,000 deliveries, 1,000 products and 7,000 reviews. It follows the EDA notebook sequence and recreates every reported statistic from the submitted CSV files.</p>' + paragraphs(assurance) + '<h2>Analytical approach</h2><p>Identifiers are retained as strings, while the date, numeric and Boolean fields required for analysis are converted explicitly. Primary-key completeness and parent-key uniqueness are checked before each join.</p><p>Metrics are calculated at their stated observation unit. Order items join many-to-one to products; orders are aggregated before the customer join; and multiple reviews are averaged to order grain before joining deliveries. Every relational step confirms that the left-hand row count is unchanged.</p><p>The seven figures cover the six required EDA categories. They combine distributions, group comparisons, temporal rates, density, confidence intervals and checked relational analysis. The results describe associations in this export and are not interpreted as causal effects.</p>', '1')}
    {page('2. Assessed visualisations', figure_block(text, 1, 'compact') + figure_block(text, 2, 'compact'), '2')}
    {page('2. Assessed visualisations', figure_block(text, 3, 'compact') + figure_block(text, 4, 'compact'), '3')}
    {page('2. Assessed visualisations', figure_block(text, 5, 'compact') + figure_block(text, 6, 'compact'), '4')}
    {page('2. Assessed visualisations', figure_block(text, 7, 'medium') + '<h2>3. Evidence-based findings</h2>' + finding_list(finding_items[:2], 1), '5')}
    {page('3. Evidence-based findings', finding_list(finding_items[2:], 3), '6')}
    {page('4. Future machine-learning questions', ml_cards(questions[:3], 1), '7')}
    {page('4. Future machine-learning questions', ml_cards(questions[3:], 4) + '<div class="conclusion"><h2>5. Limitations and conclusion</h2>' + paragraphs(limits) + '</div>', '8')}
    {page('References', '<div class="references">' + paragraphs(refs) + '</div>')}
    </body></html>"""
    return html_doc


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(build_html(), encoding="utf-8")
    subprocess.run(
        [
            "google-chrome",
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--allow-file-access-from-files",
            "--no-pdf-header-footer",
            f"--print-to-pdf={PDF_PATH}",
            HTML_PATH.resolve().as_uri(),
        ],
        check=True,
    )
    print(f"Built {PDF_PATH}")


if __name__ == "__main__":
    main()
