# output -> output / maps/ mg_map.pdb

from chimerax.core.commands import run
from chimerax.core.session import Session
from pathlib import Path
import shutil

session: Session

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / 'data'
process_dir = data_dir / 'output'

maps_dir = data_dir / 'maps'
maps_dir.mkdir(parents=True, exist_ok=True)
map_file = maps_dir / 'mg_map.pdb'

pigments = {'CLA', 'CHL', 'CL0'}

serial = 1

with map_file.open('w', encoding='utf-8') as out_file:

    out_file.write("HEADER    PIGMENT ATOM MAP\n")

    for pdb_path in sorted(process_dir.glob('*.pdb')):

        with pdb_path.open('r', encoding='ascii') as in_file:

            for line in in_file:

                if not line.startswith(('ATOM', 'HETATM')):
                    continue

                if line[76:78].strip().upper()!= 'MG':
                    continue

                line = f'{line[:6]}{serial:5d}{line[11:]}'

                out_file.write(line)

                serial += 1
                
    out_file.write('END\n')

run(session, 'close')

template_files = sorted((data_dir / 'input/template').glob('*.pdb'))

if len(template_files) != 1:
    raise RuntimeError(f'Expected 1 template file. Got {len(template_files)}')

template = template_files[0]

run(session, f'open "{template.as_posix()}"')
run(session, f'open "{map_file.as_posix()}"')