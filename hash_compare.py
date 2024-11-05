import hashlib
from pathlib import Path
from typing import Tuple, Union
import pandas as pd

import tifffile


def calculate_tiff_hash(image_path: Union[str, Path]) -> str:
    """
    Calculate SHA256 hash from TIFF image data.

    Args:
        image_path: Path to the TIFF image file

    Returns:
        str: Hexadecimal string representation of the SHA256 hash

    Raises:
        FileNotFoundError: If the image file doesn't exist
        ValueError: If there's an error reading the TIFF file
    """
    try:
        # Read the TIFF file
        with tifffile.TiffFile(image_path) as tif:
            image_data = tif.asarray()

        # Convert image data to bytes
        image_bytes = image_data.tobytes()

        # Calculate SHA256 hash
        hash_obj = hashlib.sha256()
        hash_obj.update(image_bytes)

        return hash_obj.hexdigest()

    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found: {image_path}")
    except Exception as e:
        raise ValueError(f"Error reading TIFF file: {str(e)}")


def compare_tiff_images(
    image1_path: Union[str, Path], image2_path: Union[str, Path]
) -> Tuple[bool, str, str]:
    """
    Compare two TIFF images by calculating and comparing their hashes.

    Args:
        image1_path: Path to the first TIFF image
        image2_path: Path to the second TIFF image

    Returns:
        Tuple containing:
            - Boolean indicating if images are identical
            - Hash of first image
            - Hash of second image

    Raises:
        FileNotFoundError: If either image file doesn't exist
        ValueError: If there's an error reading either TIFF file
    """
    hash1 = calculate_tiff_hash(image1_path)
    hash2 = calculate_tiff_hash(image2_path)

    return hash1 == hash2, hash1, hash2


if __name__ == "__main__":
    root1 = Path(
        r"./data/210810_45670_ko_female_LH_14-48-50_decon_2021-10-28_12-39-11/atlaslabel_def_origspace"
    )
    root2 = Path(
        r"./data/210810_45670_ko_female_LH_14-48-50_decon_2021-10-28_12-39-11/atlaslabel_def_origspace_masked/"
    )
    image_results = []
    for file in root1.glob("Z*.tif"):
        base_name = file.name.lstrip("Z").lstrip("0").removesuffix(".tif")
        convert_name = "Z" + base_name.zfill(5) + ".tif"
        file_path2 = root2.joinpath(convert_name)
        assert file_path2.exists()
        result, hash1, hash2 = compare_tiff_images(file, file_path2)
        my_dict = {
            "filepath_1": file,
            "filepath_2": file_path2,
            "same_hash": result,
            "hash_1": hash1,
            "hash_2": hash2,
        }
        image_results.append(my_dict)
    df = pd.DataFrame(image_results)
    df.to_csv("comparison_results.csv", index=False)
