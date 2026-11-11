# Data dictionary

All areas are in km². Zones run north to south: 1 North coast, 2 Absheron–Baku,
3 Sangachal–Alat, 4 Kura delta–Kizilagach, 5 Lankaran–Astara. Zone 0 means the whole coast.

## `earth_engine/` (printed by `gee/01_exposed_seabed.js`)

| File | Columns |
|---|---|
| `by_year.csv` | `year`; `exposed_all_km2` before screening; `exposed_clean_km2` after screening; `set_aside_ring_km2` and `set_aside_built_km2`, the two screens; `persistent_clean_km2`, exposed in that year and every later year; `mean_ndvi`, `mean_msavi`, `vegetated_pct` on exposed seabed (from 2019) |
| `by_zone_year.csv` | `zone`, `year`, `exposed_km2` (screened), `persistent_km2`, `mean_ndvi`, `vegetated_pct` |
| `class_by_zone.csv` | `zone`; `bare_at_emergence_km2` and `green_at_emergence_km2`, by peak NDVI in the year of emergence (threshold 0.2); `emerged_2018_km2`, not classed because the vegetation record starts in 2019 |
| `trajectories.csv` | `climate`, the zone group (`arid` = zones 1–3, `humid` = zones 4–5; group names only); `class`, bare or green at emergence; `cohort`, the year of emergence; `year`; `years_since`; `area_km2`; `mean_ndvi`; `mean_msavi`; `vegetated_pct` |
| `sensitivity.csv` | `mndwi_thr`, `water_freq`, `exposed_total_km2`, and `z1` to `z5` for the zones |

## `earth_engine_extended/` (printed by `gee/02_extended_analysis.js`)

| File | Columns |
|---|---|
| `bare_by_zone.csv` | `zone`, `exposed_km2`, `bare_km2` (peak NDVI below 0.2 in 2026) |
| `protected_areas.csv` | `name`, `designation`, `iucn`, `year` of designation, `rep_area_km2` reported area, `exposed_km2`, `bare_km2` inside the site |
| `pa_union.csv` | `quantity`, `km2`: exposed and bare seabed inside any designated site, and inside nationally designated areas (sites overlap, so these are computed on the union) |
| `retreat_by_zone.csv` | `zone`; `p10` to `p99`, `max`, `mean`: distance in meters from the 2026 waterline back to the nearest 2017 land; `count` of waterline pixels |
| `jrc_water_core.csv` | `year`; `perm1` to `perm5`, permanent water by zone; `seas_tot`, seasonal water; `notw_tot`, not water; `nodata_tot`; `seas4`, `notw4` for zone 4. From JRC Global Surface Water, 30 m |
| `s2_water_core.csv` | `year`; `w1` to `w5`, summer water by zone; `land_total`; `nodata_total`. From this project's Sentinel-2 maps, 20 m |
| `population_near_seabed.csv` | `distance_km`; `pop_near_bare_exposed`; `pop_near_any_exposed`. GHS-POP 2020 |
| `population_region_total.csv` | population of the region counted (Azerbaijan east of 48° E) |
| `gebco_hyps_core.csv` | `z_m`, GEBCO 2023 height in whole meters; `water2017_km2`; `exposed_km2`; `land2017_km2` |
| `gebco_core_totals.csv` | totals of the three columns above over all heights |
| `gebco_hyps_wide50km.csv` | `z_m`, `area_km2` within 50 km of the coast (context only) |
| `reference_ndvi.csv` | `zone`; `in_ring`, 1 = old coastal land in the 500 m landward band, 0 = seabed that emerged before 2017; `year`; `area_km2`; `mean_ndvi`; `vegetated_pct` |

## `sea_level/`

Caspian Sea level from satellite altimetry, NASA Global Water Monitor, lake 000270
(https://earth.gsfc.nasa.gov/gwm/lake/270). Meters on the EGM2008 datum.

| File | Columns |
|---|---|
| `caspian_level_summer_2012_2026.csv` | `year`; `n_JJAS`, `mean_JJAS_m`, `sd_JJAS_m` for June to September; `n_all`, `mean_all_m` for the whole year; `missions` |
| `caspian_level_1992_2026.csv` | the same, from 1992, with yearly `max_m` and `min_m` |

The two files were retrieved a few days apart. One more observation had been added for
2026 by then, so the 2026 whole-year mean differs slightly between them. The summer
means, which the analysis uses, are identical.

## `accuracy/`

| File | Columns |
|---|---|
| `sample_points.csv` | `id`; `stratum`, the mapped class (1 exposed seabed, 2 stable water, 3 stable land); `lon`, `lat` |
| `reference_labels.csv` | `id`; `label_2017` and `label_2026` (water, land or unsure) from visual interpretation of Sentinel-2 image chips; `note` |

## `map_panels/`

Nine images, `site{0,1,2}_col{0,1,2}.png`, 700 by 700 pixels. Sites: 0 Kizilagach Bay and
southern Kura delta, 1 Kura delta spit, 2 Shah Dili spit. Columns: 0 summer 2017,
1 summer 2026, 2 year of emergence. Contains modified Copernicus Sentinel data.
