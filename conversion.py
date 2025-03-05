from pathlib import Path
from typing import Generator

import dask.array as da
import numpy as np
import pandas as pd
import tifffile as tf
import zarr
from matplotlib import pyplot as plt
from ome_zarr.io import parse_url
from ome_zarr.writer import write_image
from tqdm import tqdm

STACKS_ROOT: Path = Path(
    r"data/210810_45670_ko_female_LH_14-48-50_decon_2021-10-28_12-39-11"
)
IMAGE_SUBDIR: Path = STACKS_ROOT.joinpath(r"640_N4")
ATLAS_SUBDIR: Path = STACKS_ROOT.joinpath(r"atlaslabel_def_origspace")
SEGMENTATION_SUBDIR: Path = STACKS_ROOT.joinpath(r"640_FRST_seg")
STORE: Path = STACKS_ROOT.joinpath(STACKS_ROOT.name + ".zarr")
HEATMAP_STORE: Path = STACKS_ROOT.joinpath(
    STACKS_ROOT.name + "_heatmaps" + ".zarr"
)
HEATMAP_SUBDIR: Path = STACKS_ROOT.joinpath(r"heatmaps_atlasspace_corrected")
ATLAS_COLOR_MAP: Path = Path(r"atlas_info_v3.csv")

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
            "color": "FFFFFF",
            "window": {
                "start": int(min_value),
                "end": int(max_value),
                "min": 0,
                "max": 65535,
            },
            "label": "c-Fos",
            "active": True,
        }
    ]
}
del total_array

# labels section
# convert labels CSV into dict
atlas_images: Generator = ATLAS_SUBDIR.rglob("*.tif")
sorted_atlas_images: list = sorted(list(atlas_images))
with tf.TiffFile(sorted_atlas_images[0]) as atlas_tif:
    atlas_y_dim, atlas_x_dim = atlas_tif.pages[0].shape
print("Creating the Atlas dask array...")
atlas_array = da.zeros(
    (len(sorted_atlas_images), atlas_y_dim, atlas_x_dim), dtype=da.uint16
)
unique_atlas_values = set()
for i, atlas_image in tqdm(
    enumerate(sorted_atlas_images), total=len(sorted_atlas_images)
):
    with tf.TiffFile(atlas_image) as atlas_tif:
        atlas_tif_array = atlas_tif.asarray()
        unique_values = set(np.unique(atlas_tif_array).astype(int))
        unique_atlas_values.update(unique_values)
        atlas_array[i, :, :] = atlas_tif_array
labels_grp = root.create_group("labels")
label_name = "atlas_regions"
labels_grp.attrs["labels"] = [label_name]
label_grp = labels_grp.create_group(label_name)
# create dictionary containing a list of dictionaries
# that assigns rgba color for region id value
atlas_df = pd.read_csv(ATLAS_COLOR_MAP)
mapped_colors = atlas_df["id"].unique()
missing_colors = list(unique_atlas_values - set(mapped_colors.astype(int)))
missing_colors = [int(x) for x in missing_colors if x > 0]

colors_list = []
for _, row in atlas_df.iterrows():
    color_dict = {
        "label_value": int(row["id"]),
        "rgba": [row["red"], row["green"], row["blue"], 255],
    }
    colors_list.append(color_dict)
for missing_color in missing_colors:
    missing_color_dict = {"label_value": missing_color, "rgba": [0, 0, 0, 255]}
    colors_list.append(missing_color_dict)
atlas_labels_dict = {"colors": colors_list}
label_grp.attrs["image-label"] = atlas_labels_dict
write_image(atlas_array, label_grp, axes="zyx")


# add-in the thresholds
# color maps
def get_rgb_from_cmap(
    cmap_name: str,
    num_colors: int,
    starting_value: float = 0,
    ending_value: float = 1,
) -> np.ndarray:
    cmap = plt.get_cmap(cmap_name)
    rgb_values = (
        cmap(np.linspace(starting_value, ending_value, num_colors))[:, :3]
        * 255
    ).astype(int)
    return rgb_values


mask_generator = Path(
    r"./data/210810_45670_ko_female_LH_14-48-50_decon_2021-10-28_12-39-11/640_FRST_seg"
).glob("*.tif")
sorted_mask_files = sorted(list(mask_generator))
mask_color_values = get_rgb_from_cmap(
    "inferno", len(sorted_mask_files), starting_value=0.7, ending_value=1
)
for mask_idx, mask_file in enumerate(sorted_mask_files):
    threshold_value = int(mask_file.stem.split("_")[-1].lstrip("0"))
    mask_name = f"FRSTseg {threshold_value}"
    mask_grp = root.labels.create_group(mask_name)
    with tf.TiffFile(mask_file) as mask_tif:
        mask_y_dim, mask_x_dim = mask_tif.pages[0].shape
        mask_z_dim = len(mask_tif.pages)
        print("Making the mask dask array...")
        mask_array = da.zeros(
            (mask_z_dim, mask_y_dim, mask_x_dim), dtype=da.uint8
        )
        print("...done!")
        print("Propagating mask array...")
        for i, page in tqdm(enumerate(mask_tif.pages), total=mask_z_dim):
            mask_array[i, :, :] = page.asarray()
        mask_colors = {
            "colors": [
                {
                    "label_value": 255,
                    "rgba": mask_color_values[mask_idx].tolist() + [255],
                }
            ]
        }
        mask_grp.attrs["image-label"] = mask_colors
        root["labels"].attrs["labels"] += [mask_name]
        write_image(mask_array, mask_grp, axes="zyx")

# heatmap section
# due to contraints on OME-Zarr format, need to package separately
heatmap_store = parse_url(HEATMAP_STORE, mode="w").store
heatmap_root = zarr.group(store=heatmap_store)
heatmap_images: Generator = HEATMAP_SUBDIR.rglob("*.tif")
sorted_heatmap_images: list = sorted(list(heatmap_images))
with tf.TiffFile(sorted_heatmap_images[0]) as heatmap_tif:
    heatmap_y_dim, heatmap_x_dim = heatmap_tif.pages[0].shape
    heatmap_z_dim = len(heatmap_tif.pages)
print("Creating the dask array...")
heatmap_array = np.zeros(
    (len(sorted_heatmap_images), heatmap_z_dim, heatmap_y_dim, heatmap_x_dim),
    dtype=np.float32,
)
print("...done!")
for thresh_idx, heatmap_image in enumerate(sorted_heatmap_images):
    with tf.TiffFile(heatmap_image) as heatmap_tif:
        heatmap_y_dim, heatmap_x_dim = heatmap_tif.pages[0].shape
        heatmap_z_dim = len(heatmap_tif.pages)
        for i, page in tqdm(enumerate(heatmap_tif.pages), total=heatmap_z_dim):
            heatmap_array[thresh_idx, i, :, :] = page.asarray()
scaler: np.float32 = np.float32(65535) / heatmap_array.max().item()
heatmap_scaled_array = np.round((heatmap_array * scaler)).astype(np.uint16)
write_image(image=heatmap_scaled_array, group=heatmap_root, axes="czyx")
