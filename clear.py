# destroys all intermediate and output foldersx

# from chimerax.core.commands import run
# from chimerax.core.session import Session
from pathlib import Path
import shutil

# session: Session

base_dir = Path(__file__).resolve().parent.parent

data_dir = base_dir / 'data'

shutil.rmtree(data_dir / 'filtered', ignore_errors=True)
shutil.rmtree(data_dir / 'output', ignore_errors=True)
shutil.rmtree(data_dir / 'rejected', ignore_errors=True)
shutil.rmtree(data_dir / 'sliced', ignore_errors=True)

log_dir = data_dir / 'logs'

(log_dir / 'match.log').unlink(missing_ok=True)

maps_dir = base_dir / 'maps'

(maps_dir / 'mg_map.pdb').unlink(missing_ok=True)