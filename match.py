# filtered -> output

from chimerax.core.commands import run
from chimerax.core.session import Session
from pathlib import Path

session: Session

base_dir = Path(__file__).resolve().parent.parent

template_folder = base_dir / 'data' / 'input' / 'template'
template_files = sorted(template_folder.glob("*.pdb"))
input_pdb_files = sorted( (base_dir / "data" / "filtered").glob('*.pdb') )

output_pdb_folder = base_dir / "data" / "output"
output_pdb_folder.mkdir(parents=True, exist_ok=True)

# match_command = (
#     f'mm #2 to #1'
# )

MIN_COVERAGE = 0.85
MIN_CORE_RETENTION = 0.5
MAX_CORE_RMSD = 2.0

counter: int = 1

def log(text: str, log_level: str):
    with open(base_dir / 'logs' / f'match.log') as log:
        file.write_text(text)

    if hasattr(session.logger, log_level):
        method = getattr(session.logger, log_level)
        method(text)
    

def flatten(value):
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from flatten(item)
    else:
        yield value

def get_structures(value):
    return [
        item for item in flatten(value)
        if hasattr(item, "chains") and hasattr(item, "id_string")
    ]

def get_match_results(value):
    return [
        item for item in flatten(value)
        if isinstance(item, dict) and "final RMSD" in item
    ]

if not template_files:
    raise RuntimeError(f'No template PDB found in {template_folder}')

template_models = get_structures(run(session, f'open "{template_files[0].as_posix()}"'))

if len(template_models) != 1:
    raise RuntimeError(f'Expected only one template structure, found {len(template_models)}')

template = template_models[0]
template_id = template.id_string

try:
    for file in input_pdb_files:
        candidate_models = []

        try:
            candidate_models = get_structures(
                run(session, f'open "{file.as_posix()}"')
            )

            if len(candidate_models) != 1:
                session.logger.warning(
                    f"Skipping {file.name}: expected one structure, "
                    f"found {len(candidate_models)}"
                )
                continue

            candidate = candidate_models[0]
            candidate_id = candidate.id_string

            # Match the best chain pair between the two structures.
            raw_result = run(
                session,
                f"mm #{candidate_id} to #{template_id}"
            )

            results = get_match_results(raw_result)

            if not results:
                session.logger.warning(
                    f"No usable match for {file.name}"
                )
                continue

            result = results[0]

            # RMSD and pruned-pair statistics.
            core_rmsd = float(result["final RMSD"])
            full_rmsd = float(result["full RMSD"])

            core_pairs = len(result["final match atoms"])
            full_pairs = len(result["full match atoms"])

            core_retention = (
                core_pairs / full_pairs if full_pairs else 0.0
            )

            # Estimate coverage from the aligned sequences.
            ref_seq = result["aligned ref seq"].characters.upper()
            match_seq = result["aligned match seq"].characters.upper()

            gaps = {"-", "."}

            paired_residues = sum(
                a not in gaps and b not in gaps
                for a, b in zip(ref_seq, match_seq)
            )

            ref_length = sum(a not in gaps for a in ref_seq)
            match_length = sum(b not in gaps for b in match_seq)

            ref_coverage = (
                paired_residues / ref_length if ref_length else 0.0
            )
            match_coverage = (
                paired_residues / match_length if match_length else 0.0
            )

            session.logger.info(
                f"{file.name}: "
                f"core RMSD={core_rmsd:.2f} Å, "
                f"full RMSD={full_rmsd:.2f} Å, "
                f"core pairs={core_pairs}/{full_pairs}, "
                f"coverage={ref_coverage:.1%}/{match_coverage:.1%}"
            )

            # Apply acceptance criteria.
            if (
                core_rmsd > MAX_CORE_RMSD
                or ref_coverage < MIN_COVERAGE
                or match_coverage < MIN_COVERAGE
                or core_retention < MIN_CORE_RETENTION
                or core_pairs < 30
            ):
                session.logger.info(f"Rejected: {file.name}")
                continue

            output_file = output_pdb_folder / f"chain_{counter}.pdb"

            run(
                session,
                f'save "{output_file.as_posix()}" #{candidate_id}'
            )

            session.logger.info(f"Accepted: {file.name}")
            counter += 1

        finally:
            # Close only models opened for this candidate.
            for model in candidate_models:
                if model in session.models.list():
                    run(session, f"close #{model.id_string}")

finally:
    # Close the template model opened by this script.
    for model in template_models:
        if model in session.models.list():
            run(session, f"close #{model.id_string}")

session.logger.info(f"Finished. Saved {counter - 1} structures.")

#* for file in input_pdb_files:
#*     run(session, f'open "{file.as_posix()}"')
#*     result = run(session, match_command)[0]

#*     ref_coverage = len(result["final ref atoms"]) / len(result["full ref atoms"])
#*     match_covarage = len(result["final match atoms"]) / len(result["full match atoms"])

#*     # if (
#*     #     result["final RMSD"] > 2.0
#*     #     or ref_coverage < 0.85
#*     #     or match_covarage < 0.85
#*     #     # (
#*     #     #     result["final RMSD"] < 0.2 and
#*     #     #     match_covarage < 0.4
#*     #     # )
#*     # ):
#*     #     run(session, f'close #2')
#*     #     continue

#*     run(session, f'save "{output_pdb_folder}/chain_{counter}.pdb" #2')
#*     counter += 1
#*     run(session, f'close #2')

#* run(session, 'close #1')