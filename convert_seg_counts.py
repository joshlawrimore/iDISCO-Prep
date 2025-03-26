from pathlib import Path

import pandas as pd

DERIVATIVE_ROOT: Path = Path(r"/home/lawrimorejg/data/final/001362/derivatives/FastRadialSymmetryTransformSegmentation")
assert DERIVATIVE_ROOT.exists()
ORIGINAL_ROOT: Path = Path(r"/home/lawrimorejg/data/final")
assert ORIGINAL_ROOT.exists()

def map_directories(derivative_root: Path = DERIVATIVE_ROOT, original_root: Path = ORIGINAL_ROOT) -> dict[Path, Path]:
    subdirs: list[Path] = [x for x in derivative_root.iterdir() if x.is_dir()]
    path_map: dict[Path, Path] = {}
    for subdir in subdirs:
        micr_dir: Path = subdir.joinpath("micr")
        if not micr_dir.exists():
            raise ValueError(f"{subdir} has no micr directory!")
        if subdir.name.endswith('ko'):
            og_path: Path = original_root.joinpath("KO")
        elif subdir.name.endswith("flox"):
            og_path = original_root.joinpath("FLOX")
        else:
            raise ValueError(f"{subdir.name} not recognized!")
        subject_id: str = subdir.name.split("-")[-1][:5]
        matching_originals: list[Path] = []
        for og_subpath in og_path.iterdir():
            if og_subpath.is_dir() and subject_id in og_subpath.name:
                matching_originals.append(og_subpath)
        if len(matching_originals) > 0:
            for matching_original in matching_originals:
                og_seg_dir: Path = matching_original.joinpath("640_FRST_seg")
                if og_seg_dir.exists():
                    path_map[micr_dir] = og_seg_dir
                else:
                    og_subdirs: list[Path] = [x for x in matching_original.iterdir() if x.is_dir()]
                    if len(og_subdirs) == 1:
                        og_seg_dir: Path = og_subdirs[0].joinpath("640_FRST_seg")
                        if og_seg_dir.exists():
                            path_map[micr_dir] = og_seg_dir
                        else:
                            raise ValueError(f"{matching_original} has no 640_FRST_seg dir!")
                    else:
                        raise ValueError(f"{matching_original} has no 640_FRST_seg dir!")
        else:
            raise ValueError(f"{subdir} had no matching original directory!")
    
    return path_map

def map_filepaths(path_map: dict[Path, Path]) -> dict[Path, Path]:
    file_map: dict[Path, Path] = {}
    for derivative_dir, og_seg_dir in path_map.items():
        if "_LH" in str(og_seg_dir):
            hemisphere: str = "LeftHemisphere"
        elif "_RH" in str(og_seg_dir):
            hemisphere = "RightHemisphere"
        else:
            raise ValueError(f"{og_seg_dir} has no hemisphere information")
        for derivative_filepath in derivative_dir.iterdir():
            if derivative_filepath.is_file() and derivative_filepath.suffix == '.btf' and hemisphere in derivative_filepath.name:
                threshold: str = derivative_filepath.stem.split('-')[-1].split('_')[0]
                og_tif: Path = og_seg_dir.joinpath(f"FRSTseg_{threshold}.tif")
                if not og_tif.exists():
                    raise ValueError(f"{og_tif} does not exist!")
                og_csv:Path = og_seg_dir.joinpath(f"FRSTseg_{threshold}.csv")
                if not og_csv.exists():
                    raise ValueError(f"{og_csv} does not exist!")
                file_map[derivative_filepath] = og_csv

    return file_map

if __name__ == "__main__":
    path_map = map_directories()
    file_map = map_filepaths(path_map=path_map)
    for derivative_filepath, og_csv in file_map.items():
        print(derivative_filepath, og_csv)
