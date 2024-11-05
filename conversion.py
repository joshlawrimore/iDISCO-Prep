from pathlib import Path
from typing import Generator

import dask.array as da
import tifffile as tf
import zarr
from ome_zarr.io import parse_url
from ome_zarr.writer import write_image
from tqdm import tqdm

STACKS_ROOT: Path = Path(
    r"data/210810_45670_ko_female_LH_14-48-50_decon_2021-10-28_12-39-11"
)
IMAGE_SUBDIR: Path = STACKS_ROOT.joinpath(r"640_N4")
ATLAS_SUBDIR: Path = STACKS_ROOT.joinpath(r"atlaslabel_df_origspace")
SEGMENTATION_SUBDIR: Path = STACKS_ROOT.joinpath(r"640_FRST_seg")
STORE: Path = STACKS_ROOT.joinpath(STACKS_ROOT.name + ".zarr")

# Process the N4 deconned images as the primary images in the zarr directory
store = parse_url(STORE, mode="w").store
root = zarr.group(store=store)
deconned_images: Generator = IMAGE_SUBDIR.rglob("*.tif")
sorted_deconned_images: list = sorted(list(deconned_images))
with tf.TiffFile(sorted_deconned_images[0]) as tif:
    y_dim, x_dim = tif.pages[0].shape
print("Creating the dask array...")
total_array = da.zeros(
    (len(sorted_deconned_images), y_dim, x_dim), dtype=da.uint16
)
print("...done!")
min_value = da.uint16((2**16) - 1)
max_value = da.uint16(0)
for i, deconned_image in tqdm(
    enumerate(sorted_deconned_images), total=len(sorted_deconned_images)
):
    with tf.TiffFile(deconned_image) as tif:
        tif_array = tif.asarray()
        if tif_array.min() < min_value:
            min_value = tif_array.min()
        if tif_array.max() > max_value:
            max_value = tif_array.max()
        total_array[i, :, :] = tif_array
write_image(
    image=total_array,
    group=root,
    axes="zyx",
)
# optional rendering settings
root.attrs["omero"] = {
    "channels": [
        {
            "color": "00FF00",
            "window": {
                "start": int(min_value),
                "end": int(max_value),
                "min": 0,
                "max": 65535,
            },
            "label": "random",
            "active": True,
        }
    ]
}
