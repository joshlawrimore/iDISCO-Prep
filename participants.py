import os
from pathlib import Path

FLOXED_STRAIN: str = "C57BL/6N"
KO_STRAIN: str = "C57BL6/N"
SPECIES: str = "mus musculus"
SUBJECTS_DIR: Path = Path("data/bids/derivatives")
TSV_FILEPATH: Path = Path("data/bids/derivatives/participants.tsv")


def list_subjects(root_dir: str | Path) -> list[str]:
    subdirs = []
    for entry in os.listdir(root_dir):
        entry_path = os.path.join(root_dir, entry)
        if os.path.isdir(entry_path):
            subdirs.append(Path(entry_path).name)
    return subdirs


def map_subject_info(
    subjects: list[str], floxed_strain: str, ko_strain: str, species: str
) -> list[dict]:
    rows: list[dict] = []
    for subject in subjects:
        if subject.endswith("ko"):
            strain: str = ko_strain
        elif subject.endswith("floxed"):
            strain = floxed_strain
        else:
            raise ValueError("Subject ending not recognized!")
        row: dict = {
            "participant_id": subject,
            "species": species,
            "strain": strain,
        }
        rows.append(row)
    return rows


def write_participants(rows: list[dict], outfile: Path) -> None:
    with open(outfile, "w") as f_out:
        f_out.write("\t".join(rows[0].keys()) + "\n")
        for row in rows:
            f_out.write("\t".join(row.values()) + "\n")
    return None


def main() -> None:
    subjects: list[str] = list_subjects(SUBJECTS_DIR)
    rows: list[dict] = map_subject_info(
        subjects=subjects,
        floxed_strain=FLOXED_STRAIN,
        ko_strain=KO_STRAIN,
        species=SPECIES,
    )
    write_participants(rows=rows, outfile=TSV_FILEPATH)
    return None


if __name__ == "__main__":
    main()
