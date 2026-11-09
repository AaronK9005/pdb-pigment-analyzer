from chimerax.core.commands import run
from chimerax.core.session import Session
from pathlib import Path
import sys

session: Session

base_dir = Path(__file__).resolve().parent.parent

if len(sys.argv) < 2:
    raise RuntimeError('expected folderpath, no given')

folder = Path(sys.argv[1]).resolve()

files = sorted(folder.glob('*.pdb'))

for file in files:
    run(session, f'open "{file.as_posix()}"')