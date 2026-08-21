"""Export canonical implementation cells from the two submitted notebooks."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
EXPORTS={
    "Group030_solution.ipynb":("### 0.2 Complete workflow implementation","Group030_solution.py"),
    "Group030_EDA.ipynb":("### 0.1 Complete EDA implementation","Group030_EDA.py"),
}
for notebook,(marker,target) in EXPORTS.items():
    cells=json.loads((ROOT/notebook).read_text(encoding="utf-8"))["cells"]
    for i,cell in enumerate(cells[:-1]):
        if cell["cell_type"]=="markdown" and marker in "".join(cell["source"]):
            code=cells[i+1]
            if code["cell_type"]!="code":raise RuntimeError(f"{notebook}: export cell missing")
            (ROOT/target).write_text("".join(code["source"]),encoding="utf-8")
            break
    else:raise RuntimeError(f"{notebook}: marker not found")
    print(f"exported {target} from {notebook}")
