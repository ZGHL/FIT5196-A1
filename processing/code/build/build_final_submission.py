"""Create the Moodle ZIP only when mandatory human/AI records are present."""
from pathlib import Path
import zipfile

R=Path(__file__).resolve().parents[3]; G="Group030"
members={
    f"{G}_solution.ipynb":R/"processing"/"notebooks"/f"{G}_solution.ipynb",
    f"{G}_solution.py":R/"processing"/"code"/f"{G}_solution.py",
    f"{G}_EDA.ipynb":R/"processing"/"notebooks"/f"{G}_EDA.ipynb",
    f"{G}_text_functions.py":R/"processing"/"code"/f"{G}_text_functions.py",
    f"{G}_source_to_target_mapping.csv":R/"processing"/"mapping"/f"{G}_source_to_target_mapping.csv",
    f"{G}_AI_declaration.pdf":R/f"{G}_AI_declaration.pdf",
}
for name in ["orders","order_items","customers","deliveries","products","product_reviews"]:
    members[f"outputs/{G}_{name}_standardised.csv"]=R/"processing"/"outputs"/f"{G}_{name}_standardised.csv"
ai_dir=R/"AI_records";ai_index=ai_dir/f"{G}_AI_index.pdf"
missing=[archive_name for archive_name,path in members.items() if not path.is_file()]
exports=[p for p in ai_dir.iterdir() if p.is_file() and p.name not in {"README.md",ai_index.name}]
if not ai_index.is_file():missing.append(f"AI_records/{ai_index.name}")
if not exports:missing.append("AI_records/<complete_chat_export>")
if missing:raise SystemExit("FINAL ZIP BLOCKED — missing mandatory files:\n- "+"\n- ".join(missing))
members[f"AI_records/{ai_index.name}"]=ai_index
for path in exports:members[f"AI_records/{path.name}"]=path
if (R/"requirements.txt").is_file():members["requirements.txt"]=R/"requirements.txt"
target=R/f"{G}_A1_submission.zip"
with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as z:
    for archive_name,path in members.items():z.write(path,archive_name)
with zipfile.ZipFile(target) as z:
    names=z.namelist();assert not any("raw_input" in x or x.endswith((".json",".xml")) for x in names)
print(f"created {target.name}: {len(names)} files; raw data absent")
