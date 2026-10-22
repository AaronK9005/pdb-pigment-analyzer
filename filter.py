# sliced -> filtered
# discards obviously noncompatible chains

# from chimerax.core.commands import run
# from chimerax.core.session import Session
from pathlib import Path
import shutil

# provided by ChimeraX when the script runs
# session: Session

base_dir = Path(__file__).resolve().parent.parent

input_pdb_files = sorted(
    (base_dir / "data" / "sliced").glob('*.pdb')
)

output_pdb_folder = base_dir / "data" / "filtered"
output_pdb_folder.mkdir(parents=True, exist_ok=True)

for file in input_pdb_files:
    shutil.copy2(file ,output_pdb_folder / file.name)