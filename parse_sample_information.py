from pathlib import Path


import re
import pandas as pd

KO_DIR: Path = Path("./final/KO")
FLOXED_DIR: Path = Path("./final/FLOX")

def parse_directories(path: Path) -> pd.DataFrame:
    dir_dicts: list[dict] = []
    
    for dir_path in path.iterdir():
        if not dir_path.is_dir():
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
