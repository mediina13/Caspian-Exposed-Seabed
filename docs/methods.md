# Methods

## Study area

The study area is the sea within 10 km of Azerbaijan's coast, from the mouth of the Samur
River to Astara. Its frame is the HydroLAKES outline of the Caspian, whose shoreline dates
from about 2000. The summer level was then 0.8 m higher than in 2017, so the outline
contains every pixel that has dried out since 2017. The strip inside the outline covers
6,881 km². A band 500 m wide on the landward side of the outline is used only for screening.

The coast is divided into five zones by latitude.

| Zone | Name | Latitude |
|---|---|---|
| 1 | North coast (Samur–Siyazan) | 41.00–41.87° N |
| 2 | Sumgayit–Absheron–Baku | 40.25–41.00° N |
| 3 | Sangachal–Alat–Byandovan | 39.50–40.25° N |
| 4 | Kura delta–Kizilagach | 38.85–39.50° N |
| 5 | Lankaran–Astara | 38.42–38.85° N |

## Settings

| Setting | Value |
|---|---|
| Base year and last year | 2017 and 2026 |
| Season for water maps | 1 June to 30 September |
| Water index | MNDWI = (green − SWIR) / (green + SWIR), Sentinel-2 bands 3 and 11 |
| Water threshold | MNDWI above 0 |
| Seasonal rule | water in at least 50% of clear observations, minimum 3 observations |
| Cloud mask | Cloud Score+ `cs_cdf` of 0.6 or more |
| Vegetation index | 90th percentile of NDVI, April to September, Level-2A, from 2019 |
| Vegetated | peak NDVI above 0.2 |
| Built-up screen | Dynamic World built probability of 50% or more, summer 2026 |
| Grid | 20 m, UTM zone 39N (EPSG:32639) |

## Exposed seabed

A pixel is exposed seabed in a given year when it was water in 2017 and is land in that
year. Yearly totals count all such pixels. The year of emergence is the first year from
which a pixel stays land in every later year to 2026.

Two screens remove changes that are not seabed. Pixels in the 500 m landward band are set
aside, because they are coastal ponds, lagoons and fields that switch between wet and dry.
Pixels flagged as built-up in summer 2026 are set aside as construction.

## Accuracy and sensitivity

A stratified random sample of 150 points was drawn, 50 from each mapped class: exposed
seabed, stable water and stable land. The last two classes were sampled within 1 km of the
2017 shoreline. Each point was labeled water or land in 2017 and in 2026 from a 600 m
Sentinel-2 image chip, in shuffled order and without sight of its mapped class.

Accuracy and the area of exposure use the stratified estimators of Olofsson et al. (2014),
"Good practices for estimating area and assessing accuracy of land change", which weight
each class by its mapped area.

Exposure was also recomputed for three index thresholds (−0.1, 0, +0.1) and three
frequency cut-offs (0.25, 0.50, 0.75).

## Sea level and the long-term record

Sea level is the June to September mean of the 10-day altimetry series of NASA's Global
Water Monitor for the Caspian, in meters on the EGM2008 datum. Exposed area in each year
from 2018 to 2026 is regressed on the fall in summer level since 2017, for the whole coast
and for each zone. The slope is the area of seabed that dries per meter of fall.

For the longer record, land inside the strip is computed for every year from 1998 to 2021
from the JRC Global Surface Water yearly history. That dataset classes each 30 m Landsat
pixel as permanent water, seasonal water or not water. The two records overlap from 2017
to 2021. Sentinel-2 counts ground that is dry in summer, while the Landsat class "not
water" counts ground that is dry all year. Over the overlap the gap equals about 20% of
the seasonal-water class, and that share is added to make the Landsat years comparable.

## Shoreline retreat

For every exposed pixel that touches 2026 water, the distance to the nearest 2017 land is
measured on the 20 m grid. Distances run in any direction, so in bays and around islands
they are shorter than a retreat measured along a transect.

## Vegetation

Each exposed pixel is classed as bare or green in its year of emergence, then followed in
every later year. Pixels that emerged in 2018 have no class, because the vegetation record
starts in 2019. MSAVI, which is less sensitive to soil brightness, is computed the same
way as a check.

Two reference surfaces are followed with the same index: old coastal land in the 500 m
landward band, and seabed inside the outline that had already emerged before 2017.

## Protected areas, population and depth

Exposed seabed is overlaid on the World Database on Protected Areas. Sites overlap, so
totals are computed on their union.

For population, bare exposed seabed is aggregated to 100 m cells that are at least half
bare. The distance to the nearest such cell is computed on the UTM grid, and the GHS-POP
grid for 2020 is summed within 1, 2, 5 and 10 km. The count covers Azerbaijan east of 48° E.

The GEBCO 2023 grid gives seabed height in whole meters on cells of about 450 m. Each
pixel that was water in 2017 is assigned its GEBCO height, and the share that had dried
out by 2026 is computed for each height. Two scenarios project a further fall. The first
holds the observed rate constant. The second follows the GEBCO depth distribution, shifted
so that it reproduces the area exposed by 2026.

## Limits

- Reed beds in shallow water read as land, so part of the exposure in the south may be
  standing vegetation over water.
- The reference labels come from one interpreter working with 10 to 20 m imagery.
- The vegetation record starts in 2019, and the seven-year point rests on a single cohort.
- Within a summer the standard deviation of the 10-day sea levels is 0.03 to 0.12 m. On
  very flat ground a different choice of season would shift the shoreline.
- Exposure at engineered sites near the Port of Baku at Alat and in jetty basins south of
  Baku remains in the totals. It is small next to the total.
- GEBCO is coarse, so the projection is a range, and it covers only the 10 km strip.
- The population figures measure proximity only.
