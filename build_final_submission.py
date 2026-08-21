"""Create the Moodle ZIP only when mandatory human/AI records are present."""
from pathlib import Path
import zipfile

R=Path(__file__).parent; G="Group030"
required=[f"{G}_solution.ipynb",f"{G}_solution.py",f"{G}_EDA.ipynb",f"{G}_text_functions.py",f"{G}_source_to_target_mapping.csv",f"{G}_AI_declaration.pdf"]
outputs=[f"outputs/{G}_{n}_standardised.csv" for n in ["orders","order_items","customers","deliveries","products","product_reviews"]]
ai_dir=R/"AI_records";ai_index=ai_dir/f"{G}_AI_index.pdf"
missing=[x for x in required+outputs if not (R/x).is_file()]
exports=[p for p in ai_dir.iterdir() if p.is_file() and p.name not in {"README.md",ai_index.name}]
if not ai_index.is_file():missing.append(str(ai_index.relative_to(R)))
if not exports:missing.append("AI_records/<complete_chat_export>")
if missing:raise SystemExit("FINAL ZIP BLOCKED — missing mandatory files:\n- "+"\n- ".join(missing))
members=required+outputs+[str(ai_index.relative_to(R))]+[str(x.relative_to(R)) for x in exports]
if (R/"requirements.txt").is_file():members.append("requirements.txt")
target=R/f"{G}_A1_submission.zip"
with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as z:
    for x in members:z.write(R/x,x)
with zipfile.ZipFile(target) as z:
    names=z.namelist();assert not any("raw_input" in x or x.endswith((".json",".xml")) for x in names)
print(f"created {target.name}: {len(names)} files; raw data absent")
