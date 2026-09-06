"""Create the final English AI records index from the verified AI-01 record."""
from pathlib import Path
import textwrap
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

OUT = Path("AI_records/Group030_AI_index.pdf")

sections = [
    ("Record identification", "Record ID: AI-01\nMember: Xinhang Ren (Student ID 35134410)\nTool/model: ChatGPT (OpenAI), GPT-5.6 Sol\nComplete export: AI-01.pdf\nLanguage: Chinese original conversation"),
    ("Purpose", "Review the official FIT5196 A1 specification and marking rubric and obtain a step-by-step, HD-oriented completion plan. The conversation discussed structured JSON/XML parsing, entity grains and keys, mapping, relational outputs, reconciliation, prescribed order arithmetic, bounded regex and multilingual text, validation, EDA coverage, findings, ML questions, and the final submission structure."),
    ("Affected submission work", "The conversation provided planning and quality-control guidance relevant to Group030_solution.ipynb, Group030_source_to_target_mapping.csv, Group030_text_functions.py, Group030_EDA.ipynb, Group030_EDA.pdf, the validation register, and the submission checklist. It did not replace the group's responsibility for implementation, interpretation, testing, or final review."),
    ("Independent verification", "1. Requirements and thresholds were checked against the official FIT5196 A1 Specification and Marking Rubric.\n2. Text functions were checked against public cases TXT-01–TXT-18 (18/18 PASS) and additional missing, Unicode and near-match tests.\n3. The executable validation register reports 56/56 PASS across schema, types, missing strings, primary/foreign keys, within-source duplicates, cross-source overlap, conflicts, arithmetic, ranges, categories, temporal relationships, references and multilingual behaviour.\n4. Relational EDA joins use explicit cardinality checks and row-count assertions.\n5. Both self-contained notebooks passed Restart & Run All in a clean directory and recreated six CSVs, seven figures and the ten-page PDF offline."),
    ("Record completeness", "AI-01.pdf is retained as the complete, unshortened Chinese-language conversation export. This index summarises its purpose and verification; it does not replace the original export. Any additional assignment-related AI conversation must be registered as AI-02, AI-03, and so on."),
    ("Separate declaration requirement", "Group030_AI_declaration.pdf remains a separate required document. It must be completed and signed by all group members and placed at the root of Group030_A1_submission.zip. This AI index and AI-01.pdf belong inside AI_records/."),
]

def wrapped(text, width=105):
    return "\n".join(textwrap.fill(line, width=width) if line else "" for line in text.splitlines())

with PdfPages(OUT) as pdf:
    for page_number, page_sections in enumerate((sections[:4], sections[4:]), start=1):
        fig = plt.figure(figsize=(8.5, 11))
        fig.text(.07, .95, "Group030 AI Records Index", fontsize=20, weight="bold", va="top")
        fig.text(.07, .915, "FIT5196 Data Wrangling — Assessment 1 — Semester 2, 2026", fontsize=10, va="top")
        y = .865
        for heading, body in page_sections:
            fig.text(.07, y, heading, fontsize=12, weight="bold", va="top")
            y -= .03
            content = wrapped(body, 100)
            fig.text(.07, y, content, fontsize=9.2, va="top", linespacing=1.35)
            y -= .0205 * (content.count("\n") + 1) + .035
        fig.text(.07, .035, f"AI-01 index — page {page_number} of 2", fontsize=8, color="#444444")
        pdf.savefig(fig)
        plt.close(fig)
