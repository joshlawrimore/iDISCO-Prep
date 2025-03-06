# OME-Zarr Conversion of CATNIP Images

## Exlusion of laslabel_def_origspace_masked images in packaging

In the `210810_45670_ko_female_LH_14-48-50_decon_2021-10-28_12-39-11` folder, there are two subfolders both with the prefixes `atlaslabel_def_origspace`. Most of the images in the two folders, although differing in the number of zero-padding, are the same. Josh Lawrimore determined this using a pixel value hashing function `hash_compare.py`. Results of the hashing comparison can be found in `comparison_results.csv`. However, there are a subset of images that a differing by hash, those images are listed in the `different.csv`. Visual inspection of those images show drastic differences in image `Z0990.tif` vs `Z00990.tif`. The region masks were almost all absent in the `atlaslabel_def_origspace_masked` image `Z00990.tif`. Given that Snehashish Roy said to use `atlastlabel_def_origspace` and the image I checked in `laslabel_def_origspace_masked` had less information (as the term masked implies) I will only package up the `atlaslabel_def_origspace`.

## OME-TIFF processing steps

These are the steps I took to convert the TIFFs to OME-TIFFs.

1. Use `aggregate_ome_tiffs.py` to aggregate the 640_N4 images into a single OME-TIFF.
2. Use `aggregate_ome_tiffs.py` to aggregate the atlaslabel_def_origspace images into a single OME-TIFF.
3. Add OME-XML to the existing TIFF stacks in 640_FRST_seg folders and remove the csvs.
4. Add sidecar.json file to the subject level derivatives folders.
5. Change names of the subject to remove the '-' so it is `123456ko` instead of `123456-ko`.


### Follow up questions

What is the difference between the 640_FRST_seg and 640_FRST_seg_corr? Only CSVs in the 640_FRST_seg_corr folder.
See `/home/lawrimorejg/repos/iDISCO-Prep/final/FLOX/_45925_LH_flox_20211029/210816_45925_floxed_female_LH_16-09-53_decon_2021-10-29_16-57-17/640_FRST_seg_corr` vs `/home/lawrimorejg/repos/iDISCO-Prep/final/FLOX/_45925_LH_flox_20211029/210816_45925_floxed_female_LH_16-09-53_decon_2021-10-29_16-57-17/640_FRST_seg`

There are two samples with heatmaps_atlasspace_corrected subfolders. These contain tif files. What is the difference between the heatmaps_atlasspace and heatmaps_atlasspace_corrected?
