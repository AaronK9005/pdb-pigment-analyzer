# destroys all intermediate and output foldersx

# from chimerax.core.commands import run
# from chimerax.core.session import Session
from pathlib import Path
import shutil

# session: Session

base_dir = Path(__file__).resolve().parent.parent

data_dir = base_dir / 'data'

shutil.rmtree(data_dir / 'filtered')
shutil.rmtree(data_dir / 'output')
shutil.rmtree(data_dir / 'rejected')
shutil.rmtree(data_dir / 'sliced')

log_dir = data_dir / 'logs'

(log_dir / 'match.log').unlink()