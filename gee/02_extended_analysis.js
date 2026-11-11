/**
 * Exposed Caspian seabed, Azerbaijan, 2017-2026: extended analysis
 *
 * Companion to exposed_seabed_2017_2026 (the main script). It reads the two image assets that
 * script exported and answers six further questions, one per RUN. Set RUN, press Run, then copy
 * each "#CSV_BEGIN name ... #CSV_END" block from the Console into a file called name.csv.
 * The Python script analysis_extended.py turns those files into the tables and figures.
 *
 *   RUN 1  what is still bare, what is protected    -> bare_by_zone, protected_areas, pa_union
 *   RUN 2  shoreline retreat distance, 2017 to 2026 -> retreat_by_zone
 *   RUN 3  long-term record, 1998 to 2026           -> jrc_water_core, s2_water_core
 *   RUN 4  people living near the exposed seabed    -> population_near_seabed, population_region_total
 *   RUN 5  depth test against GEBCO 2023            -> gebco_hyps_core, gebco_core_totals, gebco_hyps_wide50km
 *   RUN 6  vegetation on stable reference land      -> reference_ndvi
 *   RUN 7  map panels for the before/after figure   (set SITE 0-2 and PANEL 0-2; replaces the map
 *          with one square image; any other RUN brings the map back)
 *
 * Each run takes about 20 to 130 seconds in the Code Editor. Runs 1 to 5 were re-run on
 * 10 November 2026 and gave the published tables.
 */
var RUN = 1;
var SITE = 0, PANEL = 0;        // RUN 7 only. PANEL 0 = summer 2017, 1 = summer 2026, 2 = year of emergence

// ---- common setup (same definitions as exposed_seabed_2017_2026) ----
var BASE_YEAR = 2017, LAST_YEAR = 2026, VEG_START = 2019;
var SCALE = 20, CRS = 'EPSG:32639', NDVI_BARE = 0.2, BUILT_THR = 50;
var ASSET_DIR = 'projects/caspian-seabed/assets/';
var stack = ee.Image(ASSET_DIR + 'az_seabed_stack_2017_2026');
var extras = ee.Image(ASSET_DIR + 'az_seabed_extras_2017_2026');
var years = []; for (var yy = BASE_YEAR; yy <= LAST_YEAR; yy++) years.push(yy);
var azerbaijan = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filter(ee.Filter.eq('country_na', 'Azerbaijan'));
var coastBox = ee.Geometry.Rectangle([48.3, 38.42, 51.2, 41.87]);
var caspian = ee.FeatureCollection('projects/sat-io/open-datasets/HydroLakes/lake_poly_v10').filterBounds(ee.Geometry.Point([50.5, 40.0]));
var caspianCore = caspian.geometry().intersection(coastBox, 100);
var coreStrip = caspianCore.intersection(azerbaijan.geometry().buffer(10000, 200), 100);
var region = coreStrip.buffer(500, 100);
var water = {}, exposed = {}, persistent = {};
years.forEach(function (y) { water[y] = stack.select('water_' + y); });
var baseWater = water[BASE_YEAR].eq(1);
years.forEach(function (y) { exposed[y] = baseWater.and(water[y].eq(0)).unmask(0); });
persistent[LAST_YEAR] = exposed[LAST_YEAR];
for (var ii = years.length - 2; ii >= 0; ii--) persistent[years[ii]] = exposed[years[ii]].and(persistent[years[ii] + 1]);
var inRing = ee.Image(0).byte().paint(ee.FeatureCollection([ee.Feature(caspianCore)]), 1).not();
var built = extras.select('built_' + LAST_YEAR).gte(BUILT_THR).unmask(0);
var clean = inRing.eq(0).and(built.eq(0));
var expo = persistent[LAST_YEAR].and(clean);                 // screened exposed seabed, 2026
var ndvi26 = stack.select('ndvi_' + LAST_YEAR).divide(10000);
var bare26 = expo.and(ndvi26.lt(NDVI_BARE).unmask(0));       // exposed and still bare in 2026
var lat = ee.Image.pixelLonLat().select('latitude');
var zone = ee.Image(5).where(lat.gte(38.85), 4).where(lat.gte(39.50), 3).where(lat.gte(40.25), 2)
  .where(lat.gte(41.00), 1).toInt().rename('zone');
var areaKm2 = ee.Image.pixelArea().divide(1e6);
var T0 = Date.now();
function csv(name, header, rows) {
  print('#CSV_BEGIN ' + name + ' [' + ((Date.now() - T0) / 1000).toFixed(0) + ' s]\n' + header.join(',') + '\n' +
        rows.map(function (r) { return r.join(','); }).join('\n') + '\n#CSV_END');
}
function rnd(v, d) { return (v === undefined || v === null || isNaN(v)) ? '' : Number(Number(v).toFixed(d)); }
function fail(what) { return function (e) { print('#FAIL ' + what + ': ' + e); }; }

var RED = {geometry: region, scale: SCALE, crs: CRS, maxPixels: 1e13, tileScale: 4};
function opts(extra) { var o = {}; for (var k in RED) o[k] = RED[k]; for (var j in extra) o[j] = extra[j]; return o; }

// ---- run 1: what is still bare, and what lies inside protected areas ----
function run1() {
  var two = ee.Image.cat([areaKm2.multiply(expo), areaKm2.multiply(bare26)]).rename(['exposed_km2', 'bare_km2']);
  two.addBands(zone).reduceRegion(opts({
    reducer: ee.Reducer.sum().repeat(2).group({groupField: 2, groupName: 'zone'})
  })).evaluate(function (r, e) {
    if (e) return fail('bare_by_zone')(e);
    csv('bare_by_zone', ['zone', 'exposed_km2', 'bare_km2'],
        r.groups.map(function (g) { return [g.zone, rnd(g.sum[0], 3), rnd(g.sum[1], 3)]; }));
  });
  // World Database on Protected Areas: one row per site that holds exposed seabed
  var wdpa = ee.FeatureCollection('WCMC/WDPA/current/polygons').filterBounds(region);
  two.reduceRegions({collection: wdpa, reducer: ee.Reducer.sum(), scale: SCALE, crs: CRS, tileScale: 4})
    .filter(ee.Filter.gt('exposed_km2', 0.05))
    .map(function (f) {
      return ee.Feature(null, f.toDictionary(['NAME', 'DESIG_ENG', 'IUCN_CAT', 'STATUS_YR', 'REP_AREA', 'exposed_km2', 'bare_km2']));
    })
    .evaluate(function (fc, e) {
      if (e) return fail('protected_areas')(e);
      csv('protected_areas', ['name', 'designation', 'iucn', 'year', 'rep_area_km2', 'exposed_km2', 'bare_km2'],
          fc.features.map(function (f) {
            var p = f.properties;
            return [p.NAME, p.DESIG_ENG, p.IUCN_CAT, p.STATUS_YR > 0 ? p.STATUS_YR : '', rnd(p.REP_AREA, 1),
                    rnd(p.exposed_km2, 3), rnd(p.bare_km2, 3)];
          }));
    });
  // the sites overlap, so the totals come from painted unions
  var anyPA = ee.Image(0).byte().paint(wdpa, 1);
  var natPA = ee.Image(0).byte().paint(wdpa.filter(ee.Filter.neq('DESIG_ENG', 'Emerald Network')), 1);
  ee.Image.cat([two.multiply(anyPA), two.multiply(natPA)])
    .rename(['any_exposed', 'any_bare', 'nat_exposed', 'nat_bare'])
    .reduceRegion(opts({reducer: ee.Reducer.sum()})).evaluate(function (r, e) {
      if (e) return fail('pa_union')(e);
      csv('pa_union', ['quantity', 'km2'], [
        ['any_designation_exposed_km2', rnd(r.any_exposed, 3)], ['any_designation_bare_km2', rnd(r.any_bare, 3)],
        ['national_pa_exposed_km2', rnd(r.nat_exposed, 3)], ['national_pa_bare_km2', rnd(r.nat_bare, 3)]]);
    });
}

// ---- run 2: how far the shoreline moved, 2017 to 2026 ----
// Distance from each pixel on the 2026 waterline (exposed seabed touching 2026 water) back to the nearest 2017 land.
function run2() {
  var land17 = water[BASE_YEAR].eq(0).unmask(0);
  var dist = land17.fastDistanceTransform(512, 'pixels', 'squared_euclidean').sqrt().multiply(SCALE)
    .reproject({crs: CRS, scale: SCALE});
  var water26 = water[LAST_YEAR].eq(1).unmask(0);
  var front = expo.and(water26.focalMax(1, 'square', 'pixels').reproject({crs: CRS, scale: SCALE}));
  var d = dist.updateMask(front).rename('retreat_m');
  var red = ee.Reducer.percentile([10, 25, 50, 75, 90, 95, 99])
    .combine(ee.Reducer.max(), '', true).combine(ee.Reducer.mean(), '', true).combine(ee.Reducer.count(), '', true);
  var KEYS = ['p10', 'p25', 'p50', 'p75', 'p90', 'p95', 'p99', 'max', 'mean', 'count'];
  function row(z, g) { return [z].concat(KEYS.map(function (k) { return rnd(g[k], 1); })); }
  d.addBands(zone).reduceRegion(opts({reducer: red.group({groupField: 1, groupName: 'zone'})}))
    .evaluate(function (r, e) {
      if (e) return fail('retreat_by_zone')(e);
      d.reduceRegion(opts({reducer: red})).evaluate(function (all, e2) {
        if (e2) return fail('retreat_all')(e2);
        var a = {}; KEYS.forEach(function (k) { a[k] = all['retreat_m_' + k]; });
        csv('retreat_by_zone', ['zone'].concat(KEYS),
            r.groups.map(function (g) { return row(g.zone, g); }).concat([row(0, a)]));
      });
    });
}

// ---- run 3: the long-term record ----
// Land inside the c. 2000 sea outline, within 10 km of the coast (coreStrip), from two independent sources:
// JRC Global Surface Water yearly history (Landsat, 30 m) and this project's Sentinel-2 summer water maps.
function run3() {
  var jrc = ee.ImageCollection('JRC/GSW1_4/YearlyHistory');
  var jy = []; for (var y = 1998; y <= 2021; y++) jy.push(y);
  var NAMES = ['perm1', 'perm2', 'perm3', 'perm4', 'perm5', 'seas_tot', 'notw_tot', 'nodata_tot', 'seas4', 'notw4'];
  var rows = [], left = jy.length;
  jy.forEach(function (y) {          // one small request per year, run in parallel
    var c = jrc.filter(ee.Filter.eq('year', y)).first().select('waterClass').unmask(0);
    var b = [1, 2, 3, 4, 5].map(function (z) { return areaKm2.multiply(c.eq(3)).multiply(zone.eq(z)); });
    b.push(areaKm2.multiply(c.eq(2)), areaKm2.multiply(c.eq(1)), areaKm2.multiply(c.eq(0)),
           areaKm2.multiply(c.eq(2)).multiply(zone.eq(4)), areaKm2.multiply(c.eq(1)).multiply(zone.eq(4)));
    ee.Image.cat(b).rename(NAMES).reduceRegion({reducer: ee.Reducer.sum(), geometry: coreStrip, scale: 30, crs: CRS,
                                                maxPixels: 1e13, tileScale: 4})
      .evaluate(function (r, e) {
        if (e) fail('jrc ' + y)(e); else rows.push([y].concat(NAMES.map(function (k) { return rnd(r[k], 1); })));
        if (--left === 0) {
          rows.sort(function (p, q) { return p[0] - q[0]; });
          csv('jrc_water_core', ['year'].concat(NAMES), rows);
        }
      });
  });
  // Sentinel-2: pixels are counted when their center lies inside the strip
  var inStrip = ee.Image(0).byte().paint(ee.FeatureCollection([ee.Feature(coreStrip)]), 1);
  var sb = [], sn = [];
  years.forEach(function (y) {
    var w = water[y].unmask(2).updateMask(inStrip);       // 1 water, 0 land, 2 no clear look
    [1, 2, 3, 4, 5].forEach(function (z) {
      sb.push(areaKm2.multiply(w.eq(1)).multiply(zone.eq(z)), areaKm2.multiply(w.eq(0)).multiply(zone.eq(z)));
      sn.push('w' + z + '_' + y, 'l' + z + '_' + y);
    });
    sb.push(areaKm2.multiply(w.eq(2))); sn.push('nodata_' + y);
  });
  ee.Image.cat(sb).rename(sn).reduceRegion({reducer: ee.Reducer.sum(), geometry: coreStrip, scale: SCALE, crs: CRS,
                                            maxPixels: 1e13, tileScale: 4})
    .evaluate(function (r, e) {
      if (e) return fail('s2_water_core')(e);
      csv('s2_water_core', ['year', 'w1', 'w2', 'w3', 'w4', 'w5', 'land_total', 'nodata_total'], years.map(function (y) {
        var w = [1, 2, 3, 4, 5].map(function (z) { return rnd(r['w' + z + '_' + y], 2); });
        var land = [1, 2, 3, 4, 5].reduce(function (p, z) { return p + rnd(r['l' + z + '_' + y], 2); }, 0);
        return [y].concat(w, [land.toFixed(2), rnd(r['nodata_' + y], 2).toFixed(2)]);
      }));
    });
}

// ---- run 4: people living near the exposed seabed (GHSL population grid, 2020, 100 m) ----
function run4() {
  var pop = ee.Image('JRC/GHSL/P2023A/GHS_POP/2020').select('population_count');
  var pproj = pop.projection();
  var azDetailed = ee.FeatureCollection('USDOS/LSIB/2017').filter(ee.Filter.eq('COUNTRY_NA', 'Azerbaijan'));
  var popRegion = azDetailed.geometry().intersection(ee.Geometry.Rectangle([48.0, 38.3, 51.3, 42.0]), 100);
  var G100 = {crs: CRS, scale: 100};
  function cells(mask) {             // 100 m cells that are at least half bare / half exposed
    return mask.unmask(0).reproject({crs: CRS, scale: SCALE})
      .reduceResolution({reducer: ee.Reducer.mean(), maxPixels: 256}).reproject(G100).gte(0.5);
  }
  function distM(src) {              // distance to the nearest such cell, in meters (UTM grid, so distances are true)
    return src.fastDistanceTransform(256, 'pixels', 'squared_euclidean').sqrt().multiply(100).reproject(G100);
  }
  var dBare = distM(cells(bare26)), dAny = distM(cells(expo));
  var D = [1, 2, 5, 10], b = [], n = [];
  D.forEach(function (km) {
    b.push(pop.updateMask(dBare.lte(km * 1000)).unmask(0), pop.updateMask(dAny.lte(km * 1000)).unmask(0));
    n.push('bare_' + km, 'any_' + km);
  });
  b.push(pop.unmask(0)); n.push('total');
  // people are summed on the population grid's own projection, so no person is resampled
  ee.Image.cat(b).rename(n).reduceRegion({reducer: ee.Reducer.sum(), geometry: popRegion, crs: pproj,
                                          maxPixels: 1e13, tileScale: 4}).evaluate(function (r, e) {
    if (e) return fail('population')(e);
    csv('population_near_seabed', ['distance_km', 'pop_near_bare_exposed', 'pop_near_any_exposed'],
        D.map(function (km) { return [km, rnd(r['bare_' + km], 0), rnd(r['any_' + km], 0)]; }));
    csv('population_region_total', ['region_total_population'], [[rnd(r.total, 0)]]);
  });
}

// ---- run 5: do public depth data predict where the seabed dried out? (GEBCO 2023, 15 arc-seconds, whole meters) ----
function run5() {
  var z = ee.ImageCollection('projects/sat-io/open-datasets/gebco/gebco_grid').mosaic().select('b1').round().toInt().rename('z');
  var w17 = water[BASE_YEAR].eq(1).unmask(0), l17 = water[BASE_YEAR].eq(0).unmask(0);
  ee.Image.cat([areaKm2.multiply(w17), areaKm2.multiply(expo), areaKm2.multiply(l17)]).addBands(z)
    .reduceRegion({reducer: ee.Reducer.sum().repeat(3).group({groupField: 3, groupName: 'z'}),
                   geometry: coreStrip, scale: SCALE, crs: CRS, maxPixels: 1e13, tileScale: 4})
    .evaluate(function (r, e) {
      if (e) return fail('gebco_hyps_core')(e);
      var tot = [0, 0, 0];
      r.groups.forEach(function (g) { for (var k = 0; k < 3; k++) tot[k] += g.sum[k]; });
      csv('gebco_hyps_core', ['z_m', 'water2017_km2', 'exposed_km2', 'land2017_km2'],
          r.groups.filter(function (g) { return g.z >= -40 && g.z <= -15; })
            .map(function (g) { return [g.z, rnd(g.sum[0], 2), rnd(g.sum[1], 2), rnd(g.sum[2], 2)]; }));
      csv('gebco_core_totals', ['water2017_km2', 'exposed_km2', 'land2017_km2'], [tot.map(function (v) { return rnd(v, 1); })]);
    });
  var wide = caspianCore.intersection(azerbaijan.geometry().buffer(50000, 500), 100);
  areaKm2.addBands(z).reduceRegion({reducer: ee.Reducer.sum().group({groupField: 1, groupName: 'z'}),
                                    geometry: wide, scale: 100, crs: CRS, maxPixels: 1e13, tileScale: 4})
    .evaluate(function (r, e) {
      if (e) return fail('gebco_hyps_wide50km')(e);
      csv('gebco_hyps_wide50km', ['z_m', 'area_km2'],
          r.groups.filter(function (g) { return g.z >= -45 && g.z <= -24; }).map(function (g) { return [g.z, rnd(g.sum, 1)]; }));
    });
}

// ---- run 6: reference vegetation series ----
// (a) old coastal land: land in every summer 2017-2026, inside the 500 m band landward of the c. 2000 shoreline
// (b) seabed that emerged before 2017: land in every summer 2017-2026, inside the c. 2000 sea outline
function run6() {
  var vegYears = years.filter(function (y) { return y >= VEG_START; });
  var stable = ee.Image(1);
  years.forEach(function (y) { stable = stable.and(water[y].eq(0).unmask(0)); });
  stable = stable.and(built.eq(0));
  var vb = [];
  vegYears.forEach(function (y) {
    var n = stack.select('ndvi_' + y).divide(10000);
    var a = areaKm2.multiply(stable).multiply(n.mask().gt(0)).unmask(0);
    vb.push(a, n.unmask(0).multiply(a), a.multiply(n.unmask(0).gt(0.2)));
  });
  var key6 = zone.multiply(10).add(inRing).toInt().rename('key');
  ee.Image.cat(vb).addBands(key6).reduceRegion({
    reducer: ee.Reducer.sum().repeat(vb.length).group({groupField: vb.length, groupName: 'key'}),
    geometry: region, scale: SCALE, crs: CRS, maxPixels: 1e13, tileScale: 4
  }).evaluate(function (r, e) {
    if (e) return fail('reference_ndvi')(e);
    var rows = [];
    r.groups.forEach(function (g) { vegYears.forEach(function (y, j) {
      var a = g.sum[3 * j];
      rows.push([Math.floor(g.key / 10), g.key % 10, y, rnd(a, 3), a > 0 ? rnd(g.sum[3 * j + 1] / a, 4) : '', a > 0 ? rnd(100 * g.sum[3 * j + 2] / a, 2) : '']); }); });
    csv('reference_ndvi', ['zone', 'in_ring', 'year', 'area_km2', 'mean_ndvi', 'vegetated_pct'], rows);
  });
}

// ---- run 7: figure panels: 2017 vs 2026 imagery and year of emergence, one panel per run ----
function run7() {
  var SITES = [
    {name: 'Kizilagach Bay and southern Kura delta', lon: 49.07, lat: 39.08, half: 20000},
    {name: 'Kura delta spit', lon: 49.40, lat: 39.31, half: 9000},
    {name: 'Shah Dili spit, Absheron National Park', lon: 50.355, lat: 40.27, half: 6500}
  ];
  var S = SITES[SITE];
  var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');
  var box = ee.Geometry.Point([S.lon, S.lat]).buffer(S.half).bounds();
  var summerImage = function (year) {
    return ee.ImageCollection('COPERNICUS/S2_HARMONIZED').filterBounds(box)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 10, 1))
      .linkCollection(csPlus, ['cs_cdf'])
      .map(function (img) { return img.select(['B11', 'B8', 'B4']).updateMask(img.select('cs_cdf').gte(0.6)); })
      .median().visualize({bands: ['B11', 'B8', 'B4'], min: 0, max: 3500, gamma: 1.2});
  };
  var PALY = ['440154', '472d7b', '3b528b', '2c728e', '21918c', '28ae80', '5ec962', 'addc30', 'fde725'];
  var yearsAfter = years.slice(1);
  var emergence = ee.ImageCollection(yearsAfter.map(function (y) {
    return ee.Image.constant(y).toInt16().updateMask(persistent[y]); })).min();
  var w26 = water[LAST_YEAR];
  var base = ee.Image(1).visualize({palette: ['f4f3ef']})
    .blend(w26.eq(0).selfMask().visualize({palette: ['d9d7d0']}))
    .blend(w26.eq(1).selfMask().visualize({palette: ['bcd6ea']}))
    .blend(emergence.updateMask(clean).visualize({min: BASE_YEAR + 1, max: LAST_YEAR, palette: PALY}));
  var thumb = function (img) {
    return ui.Thumbnail({image: img, params: {region: box, crs: CRS, dimensions: 720, format: 'png'},
      style: {width: '520px', height: '520px', margin: '0', padding: '0'}});
  };
  ui.root.clear();
  var pick = PANEL === 0 ? summerImage(BASE_YEAR) : (PANEL === 1 ? summerImage(LAST_YEAR) : base);
  ui.root.add(ui.Panel([thumb(pick)], null, {stretch: 'both', margin: '0', padding: '0', backgroundColor: 'ff00ff'}));
  // thumbnail extent in UTM meters, for the scale bar
  box.transform(CRS, 1).bounds(1, CRS).coordinates().evaluate(function (c) { print('#BOX ' + SITE + ' ' + JSON.stringify(c)); });
}

({1: run1, 2: run2, 3: run3, 4: run4, 5: run5, 6: run6, 7: run7})[RUN]();
