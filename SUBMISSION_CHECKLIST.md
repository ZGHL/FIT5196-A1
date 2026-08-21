# Final submission blockers and checklist

- [x] Group identifier is consistently `Group030`.
- [x] Six output CSVs match the dictionary field names/order.
- [x] Solution and EDA notebooks pass a fresh offline run.
- [x] Text public cases pass 18/18; additional near-match/Unicode cases pass.
- [x] Validation register reports 56/56 PASS and includes an explicit `check` field.
- [x] Mapping has all 111 required rows and no blank core evidence fields.
- [x] EDA PDF has 7 assessed figures, exactly 10 findings and exactly 5 ML questions in 9 pages.
- [x] Raw JSON/XML files are excluded from Git and must be excluded from the Moodle ZIP.
- [ ] All members fill and sign `Group030_AI_declaration.pdf`.
- [ ] Export this complete assignment conversation and add it with `Group030_AI_index.pdf` under `AI_records/`.
- [ ] Replace placeholder member names/IDs in notebook cover cells if required.
- [x] Clean-directory run recreated all six CSVs byte-for-byte, all figures and the 10-page PDF.
- [ ] Run `python3 build_final_submission.py` after the two AI items above are complete; it blocks incomplete archives and keeps `Group030_EDA.pdf` outside the ZIP.
- [ ] Every member reviews the final files and Moodle submission receipt.
