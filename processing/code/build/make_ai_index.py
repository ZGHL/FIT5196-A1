"""Build the English Group030 AI records index from the five declared records."""

from __future__ import annotations

import html
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
AI_DIR = PROJECT_ROOT / "AI_records"
HTML_PATH = PROJECT_ROOT / "processing" / "report" / "Group030_AI_index.html"
PDF_PATH = AI_DIR / "Group030_AI_index.pdf"

RECORDS = [
    {"id": "AI-01", "member": "Xinhang Ren (35134410)", "file": "AI-01.pdf",
     "purpose": "Assignment planning, interpretation of the specification and rubric, and quality-control guidance for the solution, mapping, text functions, EDA and report.",
     "affected": "Group030_solution.ipynb; Group030_source_to_target_mapping.csv; Group030_text_functions.py; Group030_EDA.ipynb; Group030_EDA.pdf; validation register; submission checklist.",
     "verification": "Requirements were checked against the official specification and rubric. The final workflow passed 18/18 public text tests, 8/8 student-designed tests and 64/64 validation checks. Both notebooks were rerun in a clean offline marking-style workspace."},
    {"id": "AI-02", "member": "Sizhe Hong (35381949)", "file": "AI-02.pdf",
     "purpose": "Development of the validation framework for schema, types, missing values, keys, source row flow, overlap, arithmetic, temporal consistency and text processing.",
     "affected": "Validation and quality-control sections of Group030_solution.ipynb and the validation evidence referred to in the EDA report.",
     "verification": "Recommendations were checked against the public data dictionary, source reconciliation counts and executable VAL-* register. The final register contains 64/64 PASS results and reports observed values rather than relying only on hard-coded expected counts."},
    {"id": "AI-03", "member": "Yinglin Fang (34814248)", "file": "AI-03.pdf",
     "purpose": "Review of the six-table relational design, observation grain, primary and foreign keys, field allocation, cleaning and JSON/XML reconciliation logic.",
     "affected": "Relational transformations in Group030_solution.ipynb; field lineage in Group030_source_to_target_mapping.csv; schema, key, arithmetic and temporal validation.",
     "verification": "The design was checked against the public data dictionary. Executable PK/FK assertions, arithmetic reconciliation and temporal checks passed, and a clean rerun recreated all six standardised tables exactly."},
    {"id": "AI-04", "member": "Guohou Zhang (35800275)", "file": "AI-04.pdf",
     "purpose": "Review of bounded regular expressions, Unicode normalisation, multilingual preservation, narrative cleaning and related validation.",
     "affected": "Group030_text_functions.py; text-processing sections of Group030_solution.ipynb; related validation-register entries.",
     "verification": "The implementation was checked against the published text contract, 18/18 public cases and 8/8 student-designed edge cases. Multilingual checks confirm that 303 reviews containing non-Latin script remain identified after cleaning."},
    {"id": "AI-05", "member": "King Man Chan (36550779)", "file": "AI-05.pdf",
     "purpose": "Design of additional tests for narrative cleaning, order and product reference extraction, promotion extraction and Unicode helper functions.",
     "affected": "Student-designed test section of Group030_solution.ipynb and quality-control evidence for Group030_text_functions.py.",
     "verification": "The additional cases were executed through the same expected-versus-actual test harness as the public suite. The final notebook reports 18/18 public cases and 8/8 student-designed cases passing."},
]


def record_html(record: dict[str, str]) -> str:
    esc = {key: html.escape(value) for key, value in record.items()}
    return f"""<article class="record"><h2>{esc['id']} — {esc['member']}</h2><table>
    <tr><th>Tool and model</th><td>ChatGPT (OpenAI); exact model not recorded in the supplied PDF</td></tr>
    <tr><th>Complete export filename</th><td><code>{esc['file']}</code></td></tr>
    <tr><th>Record language</th><td>Chinese</td></tr>
    <tr><th>Purpose</th><td>{esc['purpose']}</td></tr>
    <tr><th>Affected submission work</th><td>{esc['affected']}</td></tr>
    <tr><th>Independent verification</th><td>{esc['verification']}</td></tr>
    </table></article>"""


def page(records: list[dict[str, str]], number: int, intro: bool = False) -> str:
    opening = """<h1>Group030 AI Records Index</h1>
    <p class="course">FIT5196 Data Wrangling · Assessment 1 · Semester 2, 2026</p>
    <p class="note">This English index identifies each supplied conversational-AI record, its purpose, the affected submission work and the independent checks applied by the group. It does not replace the complete conversation files in <code>AI_records/</code>. Each member must confirm that their listed file is complete before signing the separate AI-use declaration.</p>""" if intro else ""
    return f'<section class="page">{opening}{"".join(record_html(r) for r in records)}<footer>{number}</footer></section>'


def build_html() -> str:
    css = """
    @page { size: A4; margin: 17mm 18mm 16mm; }
    * { box-sizing: border-box; }
    body { margin: 0; color: #111; font-family: Arial, Helvetica, sans-serif; font-size: 9.5pt; line-height: 1.35; }
    .page { min-height: 264mm; break-after: page; position: relative; }
    .page:last-child { break-after: auto; }
    h1 { margin: 0 0 2mm; font-size: 20pt; }
    .course { margin: 0 0 6mm; font-size: 10pt; }
    .note { margin: 0 0 6mm; padding: 3mm 4mm; border: 0.5pt solid #777; }
    .record { break-inside: avoid; margin: 0 0 7mm; }
    h2 { margin: 0 0 2mm; font-size: 12pt; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border-top: 0.5pt solid #888; padding: 1.6mm 2mm; text-align: left; vertical-align: top; }
    th { width: 39mm; font-weight: bold; }
    tr:last-child th, tr:last-child td { border-bottom: 0.5pt solid #888; }
    code { font-family: "Courier New", monospace; font-size: 8.7pt; }
    footer { position: absolute; bottom: 0; left: 0; right: 0; text-align: center; font-size: 8.5pt; }
    """
    pages = page(RECORDS[:2], 1, True) + page(RECORDS[2:], 2)
    return f'<!doctype html><html><head><meta charset="utf-8"><title>Group030 AI Records Index</title><style>{css}</style></head><body>{pages}</body></html>'


def main() -> None:
    missing = [record["file"] for record in RECORDS if not (AI_DIR / record["file"]).is_file()]
    if missing:
        raise SystemExit(f"Cannot build AI index; missing conversation files: {missing}")
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(build_html(), encoding="utf-8")
    subprocess.run([
        "google-chrome", "--headless", "--no-sandbox", "--disable-gpu",
        "--allow-file-access-from-files", "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_PATH}", HTML_PATH.resolve().as_uri(),
    ], check=True)
    print(f"Built {PDF_PATH}")


if __name__ == "__main__":
    main()
