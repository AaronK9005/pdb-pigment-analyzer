# input -> sliced
# splits protein complex into separate chains
# and saves them separatly into folder 'sliced'

from chimerax.core.commands import run
from chimerax.core.session import Session
from pathlib import Path
# import argparse

# provided by ChimeraX when the script runs
session: Session

# parser = argparse.ArgumentParser()
# parser.add_argument("data_dir")
# parser.add_argument("--output", type=Path, default=(Path.cwd() / 'data' / 'output').resolve())

base_dir = Path(__file__).resolve().parent.parent

# session.logger.info(f'{base_dir}')

input_pdb_files = sorted(
    (base_dir / "data" / "input").glob('*.pdb')
)

output_pdb_folder = base_dir / "data" / "sliced"
output_pdb_folder.mkdir(parents=True, exist_ok=True)

counter: int = 1

if not input_pdb_files:
    session.logger.warning(
        f"No PDB files found in {base_dir / 'data' / 'input'}"
    )

for file in input_pdb_files:
    # open model
    opened_models = run(session, f'open "{file.as_posix()}"')

    try:
        for structure in opened_models:
            if not hasattr(structure, "chains"):
                continue

            model_id = structure.id_string

            for chain in structure.chains:
                chain_id = chain.chain_id

                # select current chain
                run(session, f'select #{model_id}/{chain_id}')

                # save as separate .pdb file
                output_file = (
                    output_pdb_folder / f'pdb_chain_{counter}.pdb'
                )

                run(
                    session,
                    f'save "{output_file.as_posix()}" '
                    f'#{model_id} selectedOnly true'
                )

                counter += 1

    finally:
        model_ids = ",".join(
            f"#{model.id_string}"
            for model in opened_models
        )

        if model_ids:
            run(session, f'close {model_ids}')

run(session, 'select clear')