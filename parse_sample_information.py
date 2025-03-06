from pathlib import Path
from aggregate_ome_tiffs import aggregate_tiffs_to_ome
from add_ome_to_tiffs import add_ome_metadata
from tqdm import tqdm
import json
import re
from shutil import copy2
import pandas as pd
from typing import Generator
KO_DIR: Path = Path("./final/KO")
FLOXED_DIR: Path = Path("./final/FLOX")
DERVIATIVE_SUBDIRS: list[str] = [
    "640_N4",
    "atlaslabel_def_origspace",
    "640_FRST",
    "640_FRST_seg",
    "heatmaps_atlasspace",
]
ROOT_DIR: Path = Path("./final/test_bids")


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


def create_bids(root_dir: Path, df: pd.DataFrame, dry_run: bool = False) -> None:
    root_dir.mkdir(parents=True, exist_ok=True)
    derivatives_dir: Path = root_dir.joinpath("derivatives")
    derivatives_dir.mkdir(parents=True, exist_ok=True)
    root_dict: dict = {
        "PixelSize": [
            3.7,
            3.7,
            5.0
        ],
        "PixelSizeUnits": "um",
        "BodyPart": "BRAIN",
        "Description": "Deconvolved and N4 corrected image stack from the lightsheet microscope"
    }
    with open(root_dir.joinpath("SPIM.json"), "w") as f:
        json.dump(root_dict, f)
    
    # Just going to iterate over the rows manually for now
    # dir_types: list[str] = df.columns.drop(
    #     [
    #         "participant_id",
    #         "sample_id",
    #         "species",
    #         "strain",
    #         "pathology",
    #         "sample_type",
    #     ]
    # )
    for _, row in df.iterrows():
        if row["640_N4"] is not None:
            subject_dir: Path = root_dir.joinpath(row["participant_id"])
            subject_dir.mkdir(parents=True, exist_ok=True)
            micro_dir: Path = subject_dir.joinpath("micr")
            micro_dir.mkdir(parents=True, exist_ok=True)
            filepath_bft: Path = micro_dir.joinpath(f"{row['participant_id']}_{row['sample_id']}_SPIM.ome.btf")
            aggregate_tiffs_to_ome(row["640_N4"], filepath_bft, max_workers=16, dry_run=dry_run)
        if row["640_FRST"] is not None:
            frst_dir: Path = derivatives_dir.joinpath("FastRadialSymmetryTransform")
            frst_dir.mkdir(parents=True, exist_ok=True)
            frst_json: Path = frst_dir.joinpath("SPIM.json")
            if not frst_json.exists():
                with open(frst_json, "w") as f:
                    json.dump(root_dict, f)
            subject_dir: Path = frst_dir.joinpath(row["participant_id"])
            subject_dir.mkdir(parents=True, exist_ok=True)
            micro_dir: Path = subject_dir.joinpath("micr")
            micro_dir.mkdir(parents=True, exist_ok=True)
            filepath_bft: Path = micro_dir.joinpath(f"{row['participant_id']}_{row['sample_id']}_SPIM.ome.btf")
            aggregate_tiffs_to_ome(row["640_FRST"], filepath_bft, max_workers=16, dry_run=dry_run)
        if row["640_FRST_hemisphere"] is not None:
            frst_hemisphere_dir: Path = derivatives_dir.joinpath("FastRadialSymmetryTransformHemisphere")
            frst_hemisphere_dir.mkdir(parents=True, exist_ok=True)
            frst_hemisphere_json: Path = frst_hemisphere_dir.joinpath("SPIM.json")
            if not frst_hemisphere_json.exists():
                with open(frst_hemisphere_json, "w") as f:
                    json.dump(root_dict, f)
            subject_dir: Path = frst_hemisphere_dir.joinpath(row["participant_id"])
            subject_dir.mkdir(parents=True, exist_ok=True)
            micro_dir: Path = subject_dir.joinpath("micr")
            micro_dir.mkdir(parents=True, exist_ok=True)
            filepath_bft: Path = micro_dir.joinpath(f"{row['participant_id']}_{row['sample_id']}_SPIM.ome.btf")
            aggregate_tiffs_to_ome(row["640_FRST_hemisphere"], filepath_bft, max_workers=16, dry_run=dry_run)
        if row["atlaslabel_def_origspace"] is not None:
            atlaslabel_dir: Path = derivatives_dir.joinpath("AtlasLabel")
            atlaslabel_dir.mkdir(parents=True, exist_ok=True)
            atlaslabel_json: Path = atlaslabel_dir.joinpath("SPIM.json")
            if not atlaslabel_json.exists():
                with open(atlaslabel_json, "w") as f:
                    json.dump(root_dict, f)
            subject_dir: Path = atlaslabel_dir.joinpath(row["participant_id"])
            subject_dir.mkdir(parents=True, exist_ok=True)
            micro_dir: Path = subject_dir.joinpath("micr")
            micro_dir.mkdir(parents=True, exist_ok=True)
            filepath_bft: Path = micro_dir.joinpath(f"{row['participant_id']}_{row['sample_id']}_SPIM.ome.btf")
            aggregate_tiffs_to_ome(row["atlaslabel_def_origspace"], filepath_bft, max_workers=16, dry_run=dry_run)
        if row["atlaslabel_def_origspace_masked"] is not None:
            atlaslabel_masked_dir: Path = derivatives_dir.joinpath("AtlasLabelMasked")
            atlaslabel_masked_dir.mkdir(parents=True, exist_ok=True)
            atlaslabel_masked_json: Path = atlaslabel_masked_dir.joinpath("SPIM.json")
            if not atlaslabel_masked_json.exists():
                with open(atlaslabel_masked_json, "w") as f:
                    json.dump(root_dict, f)
            subject_dir: Path = atlaslabel_masked_dir.joinpath(row["participant_id"])
            subject_dir.mkdir(parents=True, exist_ok=True)
            micro_dir: Path = subject_dir.joinpath("micr")
            micro_dir.mkdir(parents=True, exist_ok=True)
            filepath_bft: Path = micro_dir.joinpath(f"{row['participant_id']}_{row['sample_id']}_SPIM.ome.btf")
            aggregate_tiffs_to_ome(row["atlaslabel_def_origspace_masked"], filepath_bft, max_workers=16, dry_run=dry_run)
        if row["640_FRST_seg"] is not None:
            frst_seg_dir: Path = derivatives_dir.joinpath("FastRadialSymmetryTransformSegmentation")
            frst_seg_dir.mkdir(parents=True, exist_ok=True)
            frst_seg_json: Path = frst_seg_dir.joinpath("SPIM.json")
            if not frst_seg_json.exists():
                with open(frst_seg_json, "w") as f:
                    json.dump(root_dict, f)
            subject_dir: Path = frst_seg_dir.joinpath(row["participant_id"])
            subject_dir.mkdir(parents=True, exist_ok=True)
            micro_dir: Path = subject_dir.joinpath("micr")
            micro_dir.mkdir(parents=True, exist_ok=True)
            # TODO: iterate over all the existing tiff stacks
            frst_seg_tifs: Generator[Path, None, None] = row["640_FRST_seg"].glob("*.tif")
            for tif in frst_seg_tifs:
                acq_string: str = tif.stem.split("_")[-1]
                filepath_bft: Path = micro_dir.joinpath(f"{row['participant_id']}_{row['sample_id']}_acq-{acq_string}_SPIM.ome.btf")
                add_ome_metadata(tif, filepath_bft, "original", dry_run=dry_run)

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
    participants_df.to_csv(ROOT_DIR.joinpath("participants.tsv"), sep="\t", index=False)
    sample_df.to_csv(ROOT_DIR.joinpath("samples.tsv"), sep="\t", index=False)
    create_bids(ROOT_DIR, df, dry_run=True)
    copy2("./LICENSE", ROOT_DIR.joinpath("LICENSE"))
    copy2("./data_README.md", ROOT_DIR.joinpath("README.md"))
    copy2("./dataset_description.json", ROOT_DIR.joinpath("dataset_description.json"))
