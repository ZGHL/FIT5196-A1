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
    escaped = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", escaped)
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
    pattern = rf"## Figure {number} — (.+?)\n\n(.+?)(?=\n\n## Figure \d+ —|\n\n## 4\.)"
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
      <h3>2.{number} {inline(title)}</h3>
      <img src="{image_uri}" alt="Figure {number}">
      <div class="figure-note">{paragraphs(body)}</div>
    </article>
    """


def figure_pair(text: str, first: int) -> str:
    return (
        '<section class="figure-pair">'
        + figure_block(text, first)
        + figure_block(text, first + 1)
        + '</section>'
    )


def supporting_table(number: int) -> str:
    """Return compact numerical detail where the chart is not precise enough on its own."""
    tables = {
        2: """
        <div class="supporting-table"><p><strong>Table 1. Discount-group summary</strong></p>
        <table class="table-summary"><thead><tr><th>Discount</th><th>Orders</th><th>Mean gross basket</th><th>Median</th><th>Mean 95% CI</th></tr></thead><tbody>
        <tr><td>0%</td><td>1,797</td><td>$3,194.58</td><td>$2,830.16</td><td>±$100.69</td></tr><tr><td>5%</td><td>1,008</td><td>$3,249.81</td><td>$2,741.96</td><td>±$137.06</td></tr><tr><td>10%</td><td>959</td><td>$3,202.16</td><td>$2,731.51</td><td>±$146.45</td></tr><tr><td>15%</td><td>726</td><td>$3,195.56</td><td>$2,807.36</td><td>±$170.41</td></tr><tr><td>20%</td><td>354</td><td>$3,351.24</td><td>$2,780.20</td><td>±$265.50</td></tr><tr><td>25%</td><td>156</td><td>$3,358.61</td><td>$3,004.11</td><td>±$348.44</td></tr>
        </tbody></table></div>""",
        4: """
        <div class="supporting-table"><p><strong>Table 2. Monthly values used in Figure 4</strong></p>
        <table class="table-summary"><thead><tr><th>Month</th><th>Orders/day</th><th>Mean order value</th><th>Month</th><th>Orders/day</th><th>Mean order value</th></tr></thead><tbody>
        <tr><td>Jan</td><td>14.13</td><td>$2,997.25</td><td>Jul</td><td>13.35</td><td>$3,115.23</td></tr><tr><td>Feb</td><td>13.00</td><td>$3,019.50</td><td>Aug</td><td>13.65</td><td>$3,110.49</td></tr><tr><td>Mar</td><td>13.45</td><td>$2,942.67</td><td>Sep</td><td>13.97</td><td>$2,896.78</td></tr><tr><td>Apr</td><td>14.53</td><td>$3,071.36</td><td>Oct</td><td>13.19</td><td>$2,971.34</td></tr><tr><td>May</td><td>13.39</td><td>$2,934.45</td><td>Nov</td><td>14.37</td><td>$2,884.01</td></tr><tr><td>Jun</td><td>14.27</td><td>$3,063.32</td><td>Dec</td><td>13.10</td><td>$2,998.45</td></tr>
        </tbody></table></div>""",
        6: """
        <div class="supporting-table"><p><strong>Table 3. Delivery-group estimates</strong></p>
        <table class="table-summary"><thead><tr><th>Carrier</th><th>Service</th><th>n</th><th>OTIF (95% Wilson CI)</th><th>Median fulfilment</th></tr></thead><tbody>
        <tr><td>AusPost</td><td>Express</td><td>205</td><td>89.3% (84.3–92.8%)</td><td>42.0 h</td></tr><tr><td>AusPost</td><td>Standard</td><td>1,050</td><td>88.6% (86.5–90.4%)</td><td>40.0 h</td></tr><tr><td>DHL</td><td>Express</td><td>216</td><td>87.0% (81.9–90.9%)</td><td>36.5 h</td></tr><tr><td>DHL</td><td>Standard</td><td>1,029</td><td>87.5% (85.3–89.4%)</td><td>38.0 h</td></tr><tr><td>Direct Freight</td><td>Express</td><td>254</td><td>92.1% (88.2–94.9%)</td><td>38.0 h</td></tr><tr><td>Direct Freight</td><td>Standard</td><td>989</td><td>89.4% (87.3–91.2%)</td><td>38.0 h</td></tr><tr><td>StarTrack</td><td>Express</td><td>253</td><td>90.9% (86.7–93.9%)</td><td>40.0 h</td></tr><tr><td>StarTrack</td><td>Standard</td><td>1,004</td><td>91.1% (89.2–92.7%)</td><td>38.0 h</td></tr>
        </tbody></table></div>""",
        7: """
        <div class="supporting-table"><p><strong>Table 4. Order-level rating by delivery timing</strong></p>
        <table class="table-summary"><thead><tr><th>Delivery timing</th><th>Rated orders</th><th>Mean rating</th><th>Mean 95% CI</th></tr></thead><tbody>
        <tr><td>Early</td><td>2,442</td><td>3.709</td><td>3.667–3.751</td></tr><tr><td>On promised date</td><td>1,166</td><td>3.717</td><td>3.659–3.775</td></tr><tr><td>Late</td><td>436</td><td>3.752</td><td>3.658–3.846</td></tr>
        </tbody></table></div>""",
    }
    return tables.get(number, "")


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
        f'<div class="finding"><span>3.{number}</span><p>{inline(item)}</p></div>'
        for number, item in enumerate(items, start=start)
    )


def ml_cards(rows: list[list[str]], start: int) -> str:
    names = ["OTIF-failure classification", "Fulfilment-hours regression",
             "Low-rating classification", "Future customer-frequency regression",
             "Product clustering"]
    sections = []
    for offset, row in enumerate(rows):
        number = start + offset
        sections.append(
            f'<section class="ml-question"><h3>4.{number} {names[number - 1]}</h3>'
            f'<p><strong>Use case, unit and target.</strong> {inline(row[1])}</p>'
            f'<p><strong>Decision-time predictors.</strong> {inline(row[2])}</p>'
            f'<p><strong>Validation and metrics.</strong> {inline(row[3])}</p>'
            f'<p><strong>Risk and EDA grounding.</strong> {inline(row[4])}</p></section>'
        )
    return "".join(sections)


def apa_references(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    entries = [line[2:] for line in lines if line.startswith("- ")]
    note = " ".join(line for line in lines if not line.startswith("- "))
    rendered = "".join(f'<p class="apa-entry">{inline(entry)}</p>' for entry in entries)
    return rendered + (f'<p class="reference-note">{inline(note)}</p>' if note else "")


def build_html() -> str:
    text = markdown_text()
    limits = section(text, "## 7. Limitations and conclusion", "## References used for method choices")
    refs = section(text, "## References used for method choices")
    finding_items = findings(text)
    questions = ml_rows(text)
    logo_uri = LOGO.resolve().as_uri()

    css = """
    @page {
      size: A4;
      margin: 18mm 20mm 17mm;
      @bottom-center { content: counter(page); font-family: "Times New Roman", Times, serif; font-size: 9pt; }
    }
    @page cover { margin: 0; @bottom-center { content: none; } }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: "Times New Roman", Times, serif; color: #111;
           font-size: 10.5pt; line-height: 1.38; }
    .cover { page: cover; break-after: page; height: 297mm; padding: 30mm 28mm; text-align: center; }
    .report-flow { margin: 0; }
    .cover img { width: 72mm; margin-top: 12mm; }
    .cover h1 { margin: 48mm auto 0; font-size: 25pt; line-height: 1.2; font-weight: normal; }
    .cover h2 { margin: 8mm 0 0; font-size: 16pt; font-weight: normal; }
    .cover .course { margin-top: 45mm; font-size: 13pt; }
    .cover .members { margin-top: 7mm; line-height: 1.8; }
    h1.section-title { font-size: 16pt; margin: 0 0 5mm; font-weight: bold; break-after: avoid; }
    h2 { font-size: 13pt; margin: 5mm 0 2.5mm; }
    h3 { font-size: 11pt; margin: 0 0 2mm; }
    p { margin: 0 0 3mm; }
    code { font-family: "Courier New", monospace; font-size: 8.5pt; }
    .table-summary { width: 100%; border-collapse: collapse; margin: 5mm 0; }
    .table-summary th, .table-summary td { padding: 2.2mm 3mm; border-bottom: 0.5pt solid #777; text-align: left; }
    .table-summary th { border-top: 1pt solid #111; border-bottom: 1pt solid #111; }
    .table-summary.coverage { margin: 3mm 0 0; font-size: 9pt; }
    .table-summary.coverage th, .table-summary.coverage td { padding: 1.1mm 2mm; }
    .supporting-table { break-inside: avoid; margin: 2mm 0 5mm; font-size: 8.3pt; }
    .supporting-table p { margin-bottom: 1mm; }
    .supporting-table .table-summary { margin: 0; }
    .supporting-table .table-summary th, .supporting-table .table-summary td { padding: 1mm 1.8mm; }
    .figure-pair { break-after: page; }
    .figure-pair:last-of-type { break-after: auto; }
    .figure-block { margin-bottom: 4mm; break-inside: avoid; }
    .figure-block h3 { break-after: avoid; }
    .figure-block .rationale { break-after: avoid; }
    .figure-block img { display: block; width: 100%; max-height: 72mm; object-fit: contain; margin: 1mm auto 1.5mm; break-inside: avoid; }
    .figure-block.large img { max-height: 150mm; }
    .figure-block.medium img { max-height: 94mm; }
    .figure-block.compact { margin-bottom: 3mm; }
    .figure-block.compact img { max-height: 62mm; }
    .figure-block.compact .figure-note { font-size: 8pt; line-height: 1.25; }
    .figure-block.compact .figure-note p { margin-bottom: 1.5mm; }
    .figure-note { font-size: 7.7pt; line-height: 1.24; }
    .figure-note p { margin-bottom: 1.2mm; }
    .rationale { font-size: 8.7pt; margin-bottom: 1.5mm; }
    .finding { display: grid; grid-template-columns: 7mm auto; gap: 2mm; margin-bottom: 1.8mm; break-inside: avoid; font-size: 8.25pt; line-height: 1.25; }
    .finding > span { font-weight: bold; }
    .finding p { margin: 0; }
    .chapter-transition { margin-top: 6mm; break-inside: avoid; }
    .chapter-transition h2 { margin-top: 0; }
    .ml-question { break-inside: avoid; margin-bottom: 2.4mm; }
    .ml-question p { font-size: 8.2pt; line-height: 1.22; margin-bottom: 0.8mm; }
    .conclusion { margin-top: 4mm; }
    .references { font-size: 10pt; }
    .references-section { break-before: page; }
    .apa-entry { margin: 0 0 4mm 10mm; text-indent: -10mm; }
    .reference-note { margin-top: 8mm; font-size: 9pt; }
    a { color: #111; text-decoration: none; }
    """

    html_doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>Group030 EDA</title>
    <style>{css}</style></head><body>
    <section class="cover"><img src="{logo_uri}" alt="Monash University">
      <h1>Exploratory Data Analysis</h1><h2>Assessment 1 · Group030</h2>
      <div class="course">FIT5196 Data Wrangling</div>
      <div class="members">King Man Chan · Yinglin Fang · Sizhe Hong<br>Xinhang Ren · Guohou Zhang</div>
    </section>
    <main class="report-flow">
      <h1 class="section-title">1. Data and analytical approach</h1>
      <h2>1.1 Start from the submitted relational data</h2><p>The analysis begins by loading the six standardised CSV files produced in the solution notebook. The tables contain 5,000 orders, 15,723 order-item lines, 500 customers, 5,000 deliveries, 1,000 products and 7,000 reviews. Identifiers remain strings; only the numeric, date and Boolean fields used below are converted after loading.</p>
      <table class="table-summary coverage"><thead><tr><th>Table</th><th>Rows</th><th>Columns</th><th>Role in the EDA</th></tr></thead><tbody><tr><td>orders</td><td>5,000</td><td>23</td><td>Order value, discount and time</td></tr><tr><td>order_items</td><td>15,723</td><td>6</td><td>Product-level sales contribution</td></tr><tr><td>customers</td><td>500</td><td>20</td><td>Prior customer activity</td></tr><tr><td>deliveries</td><td>5,000</td><td>20</td><td>OTIF and fulfilment</td></tr><tr><td>products</td><td>1,000</td><td>21</td><td>Category and catalogue cost</td></tr><tr><td>product_reviews</td><td>7,000</td><td>21</td><td>Rating and review timing</td></tr></tbody></table>
      <h2>1.2 Check the data before analysis</h2><p>Before choosing the figures, we rechecked that the row count of each table matched its primary-key count. All six checks passed. For relational figures, the parent key was required to be unique and the left-hand row count had to remain unchanged. Orders were aggregated before the customer analysis, and multiple reviews were averaged within order before the delivery join. These checks protect the observation unit used in each chart.</p>
      <p>The solution notebook provides the complete transformation and validation record. For this EDA, the most relevant results are zero orphan keys across the submitted relationships, a $0.00 maximum arithmetic difference, consistent delivery and OTIF fields, and preservation of the 303 reviews containing non-Latin script.</p>
      <h2>1.3 Move from table structure to analytical questions</h2><p>We first examined order-value distribution and composition, then customer groups, product categories and time. We next tested review behaviour, multilingual text measurement, delivery operations and the delivery-review relationship. This sequence progresses from single-table description to checked relational analysis.</p>
      <p>Continuous group means are reported with 95% confidence intervals, and OTIF proportions use Wilson 95% intervals. The figures describe associations in this export and are not interpreted as causal effects.</p>
      <h2>1.4 Assessed EDA coverage</h2><table class="table-summary coverage"><thead><tr><th>Requirement</th><th>Evidence</th><th>Observation unit</th></tr></thead><tbody><tr><td>Univariate distribution/composition</td><td>Figure 1</td><td>Order</td></tr><tr><td>Bivariate comparison</td><td>Figures 2 and 5</td><td>Order, customer or review</td></tr><tr><td>Multivariate/segmented analysis</td><td>Figures 3, 7 and 8</td><td>Item, delivery or review</td></tr><tr><td>Temporal pattern</td><td>Figure 4</td><td>Order aggregated by time</td></tr><tr><td>Review/text behaviour</td><td>Figures 5, 6 and 8</td><td>Review</td></tr><tr><td>Delivery/operational performance</td><td>Figures 7 and 8</td><td>Delivery or review</td></tr><tr><td>Checked relational analysis</td><td>Figures 2, 3, 7 and 8</td><td>Order, item, delivery and review</td></tr></tbody></table>
      <h1 class="section-title">2. Assessed visualisations</h1>
      {figure_pair(text, 1)}{figure_pair(text, 3)}{figure_pair(text, 5)}{figure_pair(text, 7)}
      <h1 class="section-title">3. Evidence-based findings</h1>{finding_list(finding_items, 1)}
      <div class="chapter-transition"><h1 class="section-title">4. Future machine-learning questions</h1><p>No model is trained in this assignment. Each question is grounded in an EDA result and uses predictors available at the proposed decision time.</p></div>
      {ml_cards(questions, 1)}
      <div class="conclusion"><h1 class="section-title">5. Limitations and conclusion</h1>{paragraphs(limits)}</div>
      <section class="references-section"><h1 class="section-title">References</h1><div class="references">{apa_references(refs)}</div></section>
    </main>
    </body></html>"""
    return html_doc


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_html = "\n".join(line.rstrip() for line in build_html().splitlines()) + "\n"
    HTML_PATH.write_text(report_html, encoding="utf-8")
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
