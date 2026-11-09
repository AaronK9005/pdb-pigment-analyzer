# main script which will be run in the end
# determines data folder with input
# and calls all other scripts

from chimerax.core.commands import run
from chimerax.core.session import Session
from pathlib import Path
import time
from functools import wraps

session: Session

script_dir = Path(__file__).resolve().parent
base_dir = script_dir.parent
output_dir = base_dir / 'data/output'

log_dir = base_dir / 'data' / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)
log_path = log_dir / 'main.log'
log_path.unlink(missing_ok=True)

def log(log_level: str, text: str):
    with log_path.open('a', encoding='utf-8') as file:
        file.write(text)

    if hasattr(session.logger, log_level):
        method = getattr(session.logger, log_level)
        method(text)

def execute(script_name: str, argstr: str = '', time_it: bool = True): #-> ('Any' | list):
    start = time.perf_counter()
    result = run(session, f'runscript "{script_dir.as_posix()}/{script_name}" {argstr}')
    elapsed = time.perf_counter() - start # seconds

    if time_it:
        log('info', f'Script \'{script_name}\' took {elapsed:.3f} seconds\n')

    return result

# close all
run(session, 'close')

execute('split.py')
execute('filter.py')
execute('match.py')
# execute('open.py', argstr = output_dir.as_posix(), time_it=False)
execute('extract.py')