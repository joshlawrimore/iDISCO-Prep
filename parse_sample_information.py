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
    "heatmaps_atlasspace"
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
                    subdir_corrected = subdir.parent.joinpath(subdir.name + "_corrected")
                    subdir_corr = subdir.parent.joinpath(subdir.name + "_corr")
                    subdir_masked = subdir.parent.joinpath(subdir.name + "_masked")
                    subdir_hemisphere = subdir.parent.joinpath(subdir.name + "_hemisphere")
                    extended_subdir_list = [subdir_corrected, subdir_corr, subdir_masked, subdir_hemisphere]
                    for extended_subdir in extended_subdir_list:
                        if extended_subdir.exists():
                            print(f"Found {extended_subdir} in {dir_path}")
                            all_subdirs.append(extended_subdir)
                    break
            if not found_this_subdir:
                print(f"Warning: Directory {dir_path} does not contain '{subdir_name}' subdirectory anywhere in its tree")
                found_subdirs = False
        if not found_subdirs:
            print(f"Skipping {dir_path} due to missing required subdirectories...")
            continue
        dir_dict: dict = {
            "species": "mus musculus",
            "sample_type": "tissue"
        }
        
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
            
        dir_dicts.append(dir_dict)
        
    return pd.DataFrame(dir_dicts)

def combine_sample_info() -> pd.DataFrame:
    ko_df: pd.DataFrame = parse_directories(KO_DIR)
    floxed_df: pd.DataFrame = parse_directories(FLOXED_DIR)
    return pd.concat([ko_df, floxed_df], axis=0, ignore_index=True)

if __name__ == "__main__":
    df = combine_sample_info()
    participants_df = df[["participant_id", "species", "strain"]].drop_duplicates()
    sample_df = df[["sample_id", "participant_id", "sample_type", "pathology"]].sort_values(by=["pathology", "participant_id"])
    df.to_csv("all_sample_information.tsv", sep="\t", index=False)
    participants_df.to_csv("participants.tsv", sep="\t", index=False)
    sample_df.to_csv("samples.tsv", sep="\t", index=False)
