# main script which will be run in the end
# determines data folder with input
# and calls all other scripts

from chimerax.core.commands import run
from chimerax.core.session import Session
from pathlib import Path

session: Session

script_dir = Path(__file__).resolve().parent

# close all to not interfere with hardcoded #2 in match.py
run(session, 'close')

run(session, f'runscript "{script_dir.as_posix()}/split.py"')
run(session, f'runscript "{script_dir.as_posix()}/filter.py"')
run(session, f'runscript "{script_dir.as_posix()}/match.py"')

output_dir = script_dir.parent / "data" / 'output'
output_files = sorted(output_dir.glob('*.pdb'))

for file in output_files:
    run(session, f'open "{file.as_posix()}"')