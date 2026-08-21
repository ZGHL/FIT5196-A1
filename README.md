# FIT5196 A1 — Group030

Reproducible integration of the allocated JSON and XML exports into six standardised relational tables, followed by validation and focused EDA.

## Reproduce

Place the allocated `Group030_commerce.json` and `Group030_operations.xml` in `raw_input/`, and keep `public_data_dictionary.csv` in the project root. Then run:

```bash
python3 Group030_solution.py
python3 Group030_EDA.py
```

The first command recreates all submitted CSVs and the validation register. The second recreates Figures 1–7 and the ten-page EDA PDF. Both workflows run offline.

The submitted notebooks are self-contained: they do not import `Group030_solution.py` or `Group030_EDA.py`. Those scripts are exports of the canonical implementation cells and can be regenerated with `python3 export_notebook_scripts.py`.

## Important submission note

The allocated raw data are intentionally excluded from Git and from the submission archive, as required by the specification. Before Moodle submission, all group members must complete and sign `Group030_AI_declaration.pdf`, and the group must add the complete assignment conversation export plus an English index under `AI_records/`.
