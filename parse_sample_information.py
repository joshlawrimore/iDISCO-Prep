from pathlib import Path


import re
import pandas as pd

KO_DIR: Path = Path("./final/KO")
FLOXED_DIR: Path = Path("./final/FLOX")
DERVIATIVE_SUBDIRS: list[str] = [
    "640_N4",
    "atlaslabel_def_origspace",
    "640_FRST",
    "640_FRST_seg",
    "heatmaps_atlasspace",
]


def parse_directories(path: Path) -> pd.DataFrame:
    dir_dicts: list[dict] = []

    for dir_path in path.iterdir():
        if not dir_path.is_dir():
            continue
        found_subdirs = True
        all_subdirs: list[Path] = []
        for subdir_name in DERVIATIVE_SUBDIRS:
            found_this_subdir = False
            for subdir in dir_path.rglob(subdir_name):
                if subdir.is_dir():
                    found_this_subdir = True
                    all_subdirs.append(subdir)
                    subdir_corrected = subdir.parent.joinpath(
                        subdir.name + "_corrected"
                    )
                    subdir_corr = subdir.parent.joinpath(subdir.name + "_corr")
                    subdir_masked = subdir.parent.joinpath(
                        subdir.name + "_masked"
                    )
                    subdir_hemisphere = subdir.parent.joinpath(
                        subdir.name + "_hemisphere"
                    )
                    extended_subdir_list = [
                        subdir_corrected,
                        subdir_corr,
                        subdir_masked,
                        subdir_hemisphere,
                    ]
                    for extended_subdir in extended_subdir_list:
                        if extended_subdir.exists():
                            print(f"Found {extended_subdir} in {dir_path}")
                            all_subdirs.append(extended_subdir)
                    break
            if not found_this_subdir:
                print(
                    f"Warning: Directory {dir_path} does not contain '{subdir_name}' subdirectory anywhere in its tree"
                )
                found_subdirs = False
        if not found_subdirs:
            print(
                f"Skipping {dir_path} due to missing required subdirectories..."
            )
            continue
        dir_dict: dict = {"species": "mus musculus", "sample_type": "tissue"}

        # Parse participant ID from directory name
        parent_name = dir_path.parent.name
        dir_parts = dir_path.name.split("_")
        for part in dir_parts:
            match = re.search(r"4\d{4}", part)
            if match:
                if parent_name.endswith("FLOX"):
                    dir_dict["participant_id"] = f"sub-{match.group()}flox"
                elif parent_name.endswith("KO"):
                    dir_dict["participant_id"] = f"sub-{match.group()}ko"

            # Check for hemisphere
            if "LH" in part:
                dir_dict["sample_id"] = "sample-LeftHemisphere"
            elif "RH" in part:
                dir_dict["sample_id"] = "sample-RightHemisphere"

        # Set strain and pathology based on parent directory
        if parent_name.endswith("FLOX"):
            dir_dict["strain"] = "C57BL/6N"
            dir_dict["pathology"] = "PACAP_fl/fl"
        elif parent_name.endswith("KO"):
            dir_dict["strain"] = "C57BL6/N"
            dir_dict["pathology"] = "PACAPko"

        # Add the paths to the directory dictionary
        dir_dict["paths"] = all_subdirs

        dir_dicts.append(dir_dict)
    df = pd.DataFrame(dir_dicts)
    return df


def combine_sample_info() -> pd.DataFrame:
    ko_df: pd.DataFrame = parse_directories(KO_DIR)
    floxed_df: pd.DataFrame = parse_directories(FLOXED_DIR)
    return pd.concat([ko_df, floxed_df], axis=0, ignore_index=True)


def process_paths(df: pd.DataFrame) -> pd.DataFrame:
    # Get all unique subdirectory names
    all_subdirs = set()
    for paths in df["paths"]:
        for path in paths:
            all_subdirs.add(path.name)

    # Create new columns for each subdirectory type
    result_df = df.copy()
    for subdir in all_subdirs:
        result_df[subdir] = None

    # Fill in the full paths for each subdirectory
    for idx, row in result_df.iterrows():
        for path in row["paths"]:
            result_df.at[idx, path.name] = path

    # Drop the original paths column
    result_df = result_df.drop("paths", axis=1)

    return result_df


def create_bids(root_dir: Path, df: pd.DataFrame) -> None:
    root_dir.mkdir(parents=True, exist_ok=True)
    derivatives_dir: Path = root_dir.joinpath("derivatives")
    derivatives_dir.mkdir(parents=True, exist_ok=True)
    dir_types: list[str] = df.columns.drop(
        [
            "participant_id",
            "sample_id",
            "species",
            "strain",
            "pathology",
            "sample_type",
        ]
    )
    for _, row in df.iterrows():
        if row["640_N4"] is not None:
            subject_dir: Path = derivatives_dir.joinpath(row["participant_id"])
            subject_dir.mkdir(parents=True, exist_ok=True)
            micro_dir: Path = subject_dir.joinpath("micr")


if __name__ == "__main__":
    df = combine_sample_info()
    df = process_paths(df)
    participants_df = df[
        ["participant_id", "species", "strain"]
    ].drop_duplicates()
    sample_df = df[
        ["sample_id", "participant_id", "sample_type", "pathology"]
    ].sort_values(by=["pathology", "participant_id"])
    df.to_csv("all_sample_information.tsv", sep="\t", index=False)
    participants_df.to_csv("participants.tsv", sep="\t", index=False)
    sample_df.to_csv("samples.tsv", sep="\t", index=False)
