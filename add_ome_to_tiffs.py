from typing import Literal

import numpy as np
import tifffile


def add_ome_metadata(
    input_path, output_path, image_type: Literal["original", "downsampled"], dry_run: bool = False
):
    """
    Add OME metadata to an existing TIFF stack and save as OME-TIFF.

    Parameters
    ----------
    input_path : str
        Path to the input TIFF stack
    output_path : str
        Path where the output OME-TIFF will be saved
    """
    if image_type == "original":
        metadata = {
            "axes": "ZYX",
            "PhysicalSizeZ": 5.0,  # Z step size in micrometers
            "PhysicalSizeX": 3.7,  # X pixel size in micrometers
            "PhysicalSizeY": 3.7,  # Y pixel size in micrometers
            "PhysicalSizeXUnit": "µm",
            "PhysicalSizeYUnit": "µm",
            "PhysicalSizeZUnit": "µm",
        }
    elif image_type == "downsampled":
        metadata = {
            "axes": "ZYX",
            "PhysicalSizeZ": 25,  # Z step size in micrometers
            "PhysicalSizeX": 25,  # X pixel size in micrometers
            "PhysicalSizeY": 25,  # Y pixel size in micrometers
            "PhysicalSizeXUnit": "µm",
            "PhysicalSizeYUnit": "µm",
            "PhysicalSizeZUnit": "µm",
        }
    if dry_run:
        if input_path.exists():
            print(f"DRY RUN: {input_path} exists")
            stack = np.zeros((16, 256, 256), dtype=np.uint8)
        else:
            raise FileNotFoundError(f"DRY RUN: {input_path} does not exist")
    else:
        # Read the input TIFF stack
        print(f"Reading TIFF stack from {input_path}")
        stack = tifffile.imread(input_path)

    # Save as OME-TIFF with metadata
    print(f"Saving OME-TIFF to {output_path}")
    print(f"Image type: {image_type}")

    tifffile.imwrite(
        output_path,
        stack,
        bigtiff=True,
        ome=True,
        imagej=False,
        metadata=metadata,
        compression="ADOBE_DEFLATE",
    )
    print("Done!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Add OME metadata to TIFF stack and save as OME-TIFF"
    )
    parser.add_argument("input_path", help="Path to input TIFF stack")
    parser.add_argument("output_path", help="Path for output OME-TIFF file")
    parser.add_argument(
        "--image-type",
        type=str,
        choices=["original", "downsampled"],
        default="original",
        help="Type of TIFF stack to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode",
    )

    args = parser.parse_args()

    add_ome_metadata(args.input_path, args.output_path, args.image_type, args.dry_run)
