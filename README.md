# OME-Zarr Conversion of CATNIP Images

## Exlusion of laslabel_def_origspace_masked images in packaging

In the `210810_45670_ko_female_LH_14-48-50_decon_2021-10-28_12-39-11` folder, there are two subfolders both with the prefixes `atlaslabel_def_origspace`. Most of the images in the two folders, although differing in the number of zero-padding, are the same. Josh Lawrimore determined this using a pixel value value hashing function. Results of the hashing comparison can be found in `comparison_results.csv`. However, there are a subset of images that a differing by hash, those images are listed in the `different.csv`. Visual inspection of those images show drastic differences in image `Z0990.tif` vs `Z00990.tif`. The region masks were almost all absent in the `atlaslabel_def_origspace_masked` image `Z00990.tif`. Given that Snehashish Roy said to use `atlastlabel_def_origspace` and the image I checked in `laslabel_def_origspace_masked` had less information (as the term masked implies) I will only package up the `atlaslabel_def_origspace`.