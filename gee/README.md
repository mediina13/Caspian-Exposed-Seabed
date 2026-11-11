# Earth Engine scripts

Both scripts run in the [Earth Engine Code Editor](https://code.earthengine.google.com/).
You need an Earth Engine account and a Cloud project.

## 1. `01_exposed_seabed.js`

Builds the yearly water maps and everything that follows from them.

1. Paste the script into the Code Editor.
2. Set `ASSET_DIR` near the top to a folder in your own project, for example
   `projects/your-project/assets/`.
3. Press **Run**. On the first run the script creates two export tasks, because the
   yearly composites are too heavy to compute live:
   - `AZ_seabed_stack`: water maps for 2017–2026, NDVI and MSAVI for 2019–2026
     (about 35 minutes)
   - `AZ_seabed_extras`: water frequencies for the sensitivity test and built-up
     probability (about 10 minutes)
4. Start both tasks in the **Tasks** tab. When they finish, press **Run** again.
5. With `MODE = 'analysis'` the script draws the map and prints tables to the Console.
   Each table sits between `#CSV_BEGIN name` and `#CSV_END`. Copy each block into
   `data/earth_engine/name.csv`.
6. With `MODE = 'accuracy'` the script draws the stratified sample of 150 points and
   shows a Sentinel-2 image chip for 2017 and 2026 at each point, 12 points per page
   (`PAGE = 0, 1, ...`). The mapped class is not shown. The labels go in
   `data/accuracy/reference_labels.csv`.

Settings are at the top of the script: base year, water index threshold, water
frequency, cloud threshold, NDVI thresholds, strip width and grid.

The script labels the three northern zones `arid` and the two southern zones `humid`.
These are group names only. The reference vegetation check in the extended script shows
that climate alone does not separate the two groups.

## 2. `02_extended_analysis.js`

Reads the two assets made by the first script and answers six further questions, one
per value of `RUN`.

| RUN | Question | Tables printed | Typical time |
|---|---|---|---|
| 1 | What is still bare, and what lies in protected areas? | `bare_by_zone`, `protected_areas`, `pa_union` | 50 s |
| 2 | How far did the shoreline move? | `retreat_by_zone` | 90 s |
| 3 | What does the longer record show? | `jrc_water_core`, `s2_water_core` | 50 s |
| 4 | How many people live near the exposed seabed? | `population_near_seabed`, `population_region_total` | 75 to 130 s |
| 5 | Do public depth data predict where the seabed dried out? | `gebco_hyps_core`, `gebco_core_totals`, `gebco_hyps_wide50km` | 15 s |
| 6 | How green is stable land beside the seabed? | `reference_ndvi` | 10 s |
| 7 | Map panels for the before/after figure (`SITE` 0–2, `PANEL` 0–2) | one image and `#BOX` extent | 20 s |

Set `ASSET_DIR` to the same folder as in the first script, set `RUN`, press **Run**, and
copy each printed block into `data/earth_engine_extended/name.csv`.

RUN 7 replaces the map with one square image. Any other RUN brings the map back.

## Notes

- All areas are computed on a 20 m grid in UTM zone 39N (EPSG:32639).
- The World Database on Protected Areas collection (`WCMC/WDPA/current/polygons`) is
  updated over time, so RUN 1 can give slightly different numbers at a later date. The
  tables here were produced on 10 November 2026.
- The assets are not public. Anyone can rebuild them with step 3 above.
