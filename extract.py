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
position_file = maps_dir / 'mg_positions.txt'

log_dir = base_dir / 'data' / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)
log_path = log_dir / 'extract.log'
log_path.unlink(missing_ok=True)

pigments = {'CLA', 'CHL', 'CL0', 'KC1', 'KC2', 'KC3'}

serial = 1

def log(log_level: str, text: str):
    with log_path.open('a', encoding='utf-8') as file:
        file.write(text)

    if hasattr(session.logger, log_level):
        method = getattr(session.logger, log_level)
        method(text.strip())

class vec3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __eq__(self, other):
        if not isinstance(other, vec3):
            return NotImplemented

        return self.x == other.x and self.y == other.y and self.z == other.z

    # def __str__(self):
    #     return f'({self.x}, {self.y}, {self.z})'
    def __format__(self, format_spec):
        return f'({self.x:.2f}, {self.y:.2f}, {self.z:.2f})'

    def __repr__(self):
        return f'vec3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})'

    def __add__(self, other):
        return vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __truediv__(self, value: float):
        return vec3(self.x / value, self.y / value, self.z / value)
    
    def __sub__(self, other):
        return vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def sum_sq(self) -> float:
        return self.x ** 2 + self.y ** 2 + self.z ** 2

    def dist(self, value) -> float:
        return (self - value).sum_sq() ** 0.5

class Pigment:
    def __init__(self, pos, file, residue):
        self.pos = pos
        self.file = file
        self.residue = residue

    def __str__(self):
        return (
            f'processed: {self.file.stem.split('_')[0]}\n'
            f'file: {self.file.name}\n'
            f'residue: {self.residue}\n'
        )

class center:
    def __init__(self, pigment):
        self.pos = pigment.pos # vec3
        self.pigments = [pigment] # list of vec3's
        self.farthest = 0.0 # float

    def __str__(self):
        return f'center: pos = {self.pos}, number of pigments = {len(self.pigments)}'

    def __repr__(self):
        return f'center: pos = {self.pos}, pigments: {self.pigments}'

    def add_pigment(self, pigment_pos: vec3):
        self.pigments.append(pigment_pos)
        self.pos = sum(self.pigments, vec3(0.0, 0.0, 0.0)) / len(self.pigments)
        self.farthest = max(
            (self.pos.dist(pigment) for pigment in self.pigments),
            default = 0.0
        )

# centers for pigments (mg clusters)
pigm_centers: list[center] = []

# in angstremss
MAX_MG_DISPERSION = 5

with map_file.open('w', encoding='utf-8') as out_pdb_file:

    out_pdb_file.write("HEADER    PIGMENT ATOM MAP\n")

    for pdb_path in sorted(process_dir.glob('*.pdb')):

        with pdb_path.open('r', encoding='ascii') as in_file:

            for line in in_file:

                if not line.startswith(('ATOM', 'HETATM')):
                    continue

                if line[76:78].strip().upper()!= 'MG':
                    continue

                if line[17:20].strip().upper() not in pigments:
                    continue

                line = f'{line[:6]}{serial:5d}{line[11:]}'
                out_pdb_file.write(line)

                pigment = vec3(
                    float(line[30:38]),
                    float(line[38:46]),
                    float(line[46:54])
                )

                placed = False
                for cent in pigm_centers:
                    if cent.pos.dist(pigment) < MAX_MG_DISPERSION:
                        cent.add_pigment(pigment)
                        placed = True
                        break

                if (not placed):
                    pigm_centers.append(center(pigment))

                serial += 1
                
    out_pdb_file.write('END\n')

# closes all previously opened models
run(session, 'close')

template_files = sorted((data_dir / 'input/template').glob('*.pdb'))
if len(template_files) != 1:
    raise RuntimeError(f'Expected 1 template file. Got {len(template_files)}')
template = template_files[0]

template_models = run(session, f'open "{template.as_posix()}"')
for template in template_models:
    run(session, f'hide {template.atomspec} atoms')

pigm_map_models = run(session, f'open "{map_file.as_posix()}"')

def render_ball(session, position: vec3, radius, name = 'sphere', color = 'red'):
    x, y, z = position
    if radius < 0.05:
        radius = 0.05
    run(session, f'shape sphere radius {radius} center {x},{y},{z} name {name}')# color{color}')

# log and render spheres
log('info', f'Found {len(pigm_centers)} pigment centers:\n')
for i in range(len(pigm_centers)):
    log('info',
        f'\t{i + 1:6d}: pos = {pigm_centers[i].pos}'
        f',\tfarthest = {pigm_centers[i].farthest:.3f}'
        f',\tnumber of pigments = {len(pigm_centers[i].pigments)}'
        '\n')
    # render_ball(session, pigm_centers[i].pos, pigm_centers[i].farthest, f's{i+1}')
log('info', f'Found {len(pigm_centers)} pigment centers:\n')