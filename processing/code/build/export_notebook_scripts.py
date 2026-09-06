"""Export the submitted Python scripts from the final self-contained notebooks."""
from __future__ import annotations

import ast
from pathlib import Path

import nbformat


PROJECT_ROOT = Path(__file__).resolve().parents[3]
NOTEBOOK_DIR = PROJECT_ROOT / "processing" / "notebooks"
CODE_DIR = PROJECT_ROOT / "processing" / "code"


def notebook_functions(path):
    notebook = nbformat.read(path, as_version=4)
    functions = {}
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        tree = ast.parse(cell.source)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions[node.name] = ast.get_source_segment(cell.source, node)
    return functions


def notebook_code(path):
    notebook = nbformat.read(path, as_version=4)
    return "\n\n".join(cell.source for cell in notebook.cells if cell.cell_type == "code")


solution_order = [
    "money", "boolean", "text", "date", "timestamp", "xml_record",
    "normalise_order", "normalise_item", "normalise_delivery", "normalise_review",
    "reconcile", "build_tables", "validate",
]
solution_functions = notebook_functions(NOTEBOOK_DIR / "Group030_solution.ipynb")
missing = set(solution_order) - set(solution_functions)
if missing:
    raise RuntimeError(f"Solution notebook is missing functions: {sorted(missing)}")

solution_header = '''"""Reproducible Group030 JSON/XML integration and validation workflow."""
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

from Group030_text_functions import (
    MISSING, build_latin_analysis, clean_narrative_text,
    contains_non_latin_script, extract_order_reference,
    extract_product_sku, extract_promo_code,
)

GROUP_ID = "Group030"
TABLES = ["orders", "order_items", "customers", "deliveries", "products", "product_reviews"]
'''
solution_cli = '''
PROJECT_ROOT = Path.cwd()
if (PROJECT_ROOT / "assignment_materials" / "allocated_package").is_dir():
    DEFAULT_DATA_ROOT = PROJECT_ROOT / "assignment_materials" / "allocated_package"
    DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "processing" / "outputs"
else:
    DEFAULT_DATA_ROOT = PROJECT_ROOT
    DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"


def main(input_dir=None, output_dir=None, dictionary_path=None):
    input_dir = DEFAULT_DATA_ROOT / "raw_input" if input_dir is None else Path(input_dir)
    output_dir = DEFAULT_OUTPUT_DIR if output_dir is None else Path(output_dir)
    dictionary_path = DEFAULT_DATA_ROOT / "public_data_dictionary.csv" if dictionary_path is None else Path(dictionary_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    tables, profile = build_tables(input_dir, dictionary_path)
    dictionary = pd.read_csv(dictionary_path)
    for name, frame in tables.items():
        frame.to_csv(output_dir / f"{GROUP_ID}_{name}_standardised.csv", index=False, na_rep=MISSING)
    validations = validate(tables, dictionary, profile)
    validations.to_csv(output_dir / f"{GROUP_ID}_validation_register.csv", index=False)
    print(validations.to_string(index=False))
    print("\\nRow counts:", {name: len(frame) for name, frame in tables.items()})
    if validations.status.eq("FAIL").any():
        raise SystemExit("Validation failures require investigation")
    return tables, validations, profile


if __name__ == "__main__" and "get_ipython" not in globals():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_DATA_ROOT / "raw_input")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DATA_ROOT / "public_data_dictionary.csv")
    args = parser.parse_args()
    main(args.input_dir, args.output_dir, args.dictionary)
'''
(CODE_DIR / "Group030_solution.py").write_text(
    solution_header + "\n\n" + "\n\n".join(solution_functions[name] for name in solution_order) + "\n" + solution_cli,
    encoding="utf-8",
)

(CODE_DIR / "Group030_EDA.py").write_text(
    '"""EDA code exported cell-by-cell from Group030_EDA.ipynb."""\n\n'
    + notebook_code(NOTEBOOK_DIR / "Group030_EDA.ipynb")
    + "\n",
    encoding="utf-8",
)
print("Exported Group030_solution.py and Group030_EDA.py from the final notebooks")
