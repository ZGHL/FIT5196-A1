# FIT5196 A1 — Group030

Reproducible integration of the allocated JSON and XML exports into six standardised relational tables, followed by validation and focused EDA.

## Repository layout

Teacher-supplied files are under `assignment_materials/`. Working notebooks, code, generated tables, mapping and figures are under `processing/`. The project root is reserved for the README, submission checklist and the two final Moodle upload files.

## Reproduce

From the project root, run:

```bash
python3 processing/code/Group030_solution.py
python3 processing/code/Group030_EDA.py
```

The first command recreates all submitted CSVs and the validation register. The second recreates Figures 1–7 and the ten-page EDA PDF. Both workflows run offline.

The working notebooks are in `processing/notebooks/`. They are self-contained and do not import the main workflow from the corresponding Python exports.

After changing either notebook, regenerate the Python exports with:

```bash
python3 processing/code/build/export_notebook_scripts.py
```

When the signed declaration and AI records are complete, create the Moodle archive with:

```bash
python3 processing/code/build/build_final_submission.py
```

## Important submission note

The final Moodle files are `Group030_A1_submission.zip` and `Group030_EDA.pdf` in the project root. The allocated raw data are never copied into the submission archive. Before final packaging, all group members must sign `Group030_AI_declaration.pdf`; complete genuine conversation exports and the English index remain under `AI_records/`.
