# filtered -> output

from chimerax.core.commands import run
from chimerax.core.session import Session
from pathlib import Path

session: Session

base_dir = Path(__file__).resolve().parent.parent

template_folder = base_dir / 'data' / 'input' / 'template'

template_file = sorted(template_folder.glob("*.pdb"))

input_pdb_files = sorted(
    (base_dir / "data" / "filtered").glob('*.pdb')
)

output_pdb_folder = base_dir / "data" / "output"
output_pdb_folder.mkdir(parents=True, exist_ok=True)

match_command = (
    f'mm #2 to #1'
)

counter: int = 1

run(session, f'open "{template_file[0].as_posix()}"')

for file in input_pdb_files:
    run(session, f'open "{file.as_posix()}"')
    run(session, match_command)
    run(session, f'save "{output_pdb_folder}/chain_{counter}.pdb" #2')
    counter += 1
    run(session, f'close #2')

run(session, 'close #1')