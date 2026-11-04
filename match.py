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

rejected_pdb_foler = base_dir / 'data' / 'rejected'
rejected_pdb_foler.mkdir(parents=True, exist_ok=True)

log_dir = base_dir / 'data' / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)
log_path = log_dir / 'match.log'
log_path.unlink(missing_ok=True)

# match_command = (
#     f'mm #2 to #1'
# )

MIN_COVERAGE = 0.1
MIN_CORE_RETENTION = 0.1
MAX_CORE_RMSD = 2.0
MIN_CORE_PAIRS = 30

counter: int = 1
counter_rejected: int = 0
counter_used: int = 0

def log(log_level: str, text: str):
    with log_path.open('a', encoding='utf-8') as file:
        file.write(text)

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
                log('warning',
                    f"Skipping {file.name}: expected one structure, "
                    f"found {len(candidate_models)}\n"
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
                log('warning', f"No usable match for {file.name}\n")
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

            log('info',
                f"{file.name}: \n"
                f"\tcore RMSD={core_rmsd:.2f} Å, \n"
                f"\tfull RMSD={full_rmsd:.2f} Å, \n"
                f"\tcore pairs={core_pairs}/{full_pairs}, \n"
                f"\tcoverage={ref_coverage:.1%}/{match_coverage:.1%}\n"
            )

            # Apply acceptance criteria.
            reject = True
            reason = ''

            if core_rmsd > MAX_CORE_RMSD:
                reason = f"core_rmsd '{core_rmsd}' > MAX_CORE_RMSD '{MAX_CORE_RMSD}'"
            elif ref_coverage < MIN_COVERAGE:
                reason = f"ref_coverage '{ref_coverage}' < MIN_COVERAGE '{MIN_COVERAGE}'"
            elif match_coverage < MIN_COVERAGE:
                reason = f"match_coverage '{match_coverage}' < MIN_COVERAGE '{MIN_COVERAGE}'"
            elif core_retention < MIN_CORE_RETENTION:
                reason = f"core_retention '{core_retention}' < MIN_CORE_RETENTION '{MIN_CORE_RETENTION}'"
            elif core_pairs < MIN_CORE_PAIRS:
                reason = f"core_pairs '{core_pairs}' < MIN_CORE_PAIRS '{MIN_CORE_PAIRS}'"
            else:
                reject = False

            output_file = base_dir / 'data'

            if reject:
                counter_rejected += 1
                output_file /= 'rejected'
                log('info', f"\tRejected: {file.name}, rejected_count: {counter_rejected}, reason: {reason}\n")
            else:
                counter_used += 1
                output_file /= 'output'
                log('info',f"\tAccepted: {file.name}\n")

            output_file /= f'{file.name}'

            run(
                session,
                f'save "{output_file.as_posix()}" #{candidate_id}'
            )

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

log('info',f"Finished. Saved {counter_used} structures.\n")

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