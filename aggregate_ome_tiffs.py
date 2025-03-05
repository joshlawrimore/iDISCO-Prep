from pathlib import Path
import numpy as np
import tifffile


def aggregate_tiffs_to_ome(input_dir, output_path, pattern="*.tif"):
    """
    Aggregate single-plane TIFF files into a single OME-TIFF file.

    Parameters
    ----------
    input_dir : str
        Directory containing the input TIFF files
    output_path : str
        Path where the output OME-TIFF will be saved
    pattern : str, optional
        Glob pattern to match the TIFF files (default: "*.tif")
    """
    # Get list of all TIFF files in the directory
    input_path = Path(input_dir)
    tiff_files = sorted(input_path.glob(pattern))

    if not tiff_files:
        raise ValueError(
            f"No TIFF files found in {input_dir} matching pattern {pattern}"
        )

    # Read the first image to get dimensions
    first_image = tifffile.imread(tiff_files[0])
    height, width = first_image.shape
    depth = len(tiff_files)

    # Create 3D array to hold all planes
    stack = np.zeros((depth, height, width), dtype=first_image.dtype)

    # Read all images into the stack
    print(f"Reading {depth} TIFF files...")
    for i, tiff_file in enumerate(tiff_files):
        stack[i] = tifffile.imread(tiff_file)

    # Save as OME-TIFF
    print(f"Saving OME-TIFF to {output_path}")
    tifffile.imwrite(
        output_path,
        stack,
        bigtiff=True,
        ome=True,
        imagej=False,
        metadata={
            "axes": "ZYX",
            "PhysicalSizeZ": 5.0,
            "PhysicalSizeXUnit": "µm",
            "PhysicalSizeYUnit": "µm",
            "PhysicalSizeZUnit": "µm",
            "PhysicalSizeX": 3.7,
            "PhysicalSizeY": 3.7,
        },
        compression="ADOBE_DEFLATE",
    )
    print("Done!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert single-plane TIFFs to OME-TIFF"
    )
    parser.add_argument(
        "input_dir", help="Directory containing single-plane TIFF files"
    )
    parser.add_argument("output_path", help="Path for output OME-TIFF file")
    parser.add_argument(
        "--pattern",
        default="*.tif",
        help="Glob pattern to match TIFF files (default: *.tif)",
    )

    args = parser.parse_args()

    aggregate_tiffs_to_ome(args.input_dir, args.output_path, args.pattern)
