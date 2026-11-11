/**************************************************************************
 * Newly exposed Caspian seabed along Azerbaijan's coast, 2017–2026  (v2)
 * Earth Engine project: caspian-seabed
 *
 *  1. Yearly summer water masks (Sentinel-2 L1C, MNDWI water frequency)
 *  2. Seabed exposed since BASE_YEAR + year of persistent emergence
 *  3. Screening: pixels inland of the c. 2000 shoreline (ponds, fields) and
 *     new built-up land (ports, reclamation; Dynamic World) are set aside
 *  4. Vegetation: seabed classed as bare or already green in its emergence
 *     year, then NDVI/MSAVI followed year by year after emergence
 *  5. Threshold sensitivity and an accuracy-assessment mode
 *
 * HOW TO RUN
 *  First run creates two batch tasks if their assets are missing:
 *  'AZ_seabed_stack' (~35 min) and 'AZ_seabed_extras' (~10 min). Run them
 *  in the Tasks tab, then run the script again.
 *  MODE = 'analysis'  map, statistics, charts, CSV blocks in the console
 *  MODE = 'accuracy'  blind stratified sample with Sentinel-2 chips for
 *                     labelling water/land in BASE_YEAR and LAST_YEAR
 **************************************************************************/

var MODE = 'analysis';          // 'analysis' or 'accuracy'
var PAGE = 0;                   // accuracy mode: which page of points to show

// ------------------------------------------------------------ 1. Settings
var BASE_YEAR  = 2017;          // reference (pre-retreat) shoreline year
var LAST_YEAR  = 2026;
var VEG_START  = 2019;          // first year with full S2 L2A coverage here
var MNDWI_THR  = 0.0;           // pixel = water if MNDWI > threshold
var WATER_FREQ = 0.5;           // season = water if water in >= 50% of clear looks
var MIN_OBS    = 3;             // min clear looks per pixel per season
var CS_THR     = 0.6;           // Cloud Score+ cs_cdf threshold (higher = stricter)
var NDVI_VEG   = 0.2;           // "vegetated" if peak NDVI above this
var NDVI_BARE  = 0.2;           // emergence-year peak NDVI below this = bare
var BUILT_THR  = 50;            // Dynamic World built probability (%), summer mean
var STRIP_KM   = 10;            // Caspian within this distance of Azerbaijan
var SCALE      = 20;            // m (native resolution of B11)
var CRS        = 'EPSG:32639';  // UTM 39N
var DRIVE_DIR  = 'caspian_seabed';
var SENS_MNDWI = [-0.1, 0.0, 0.1];   // sensitivity: MNDWI thresholds
var SENS_FREQ  = [0.25, 0.5, 0.75];  // sensitivity: water-frequency cut-offs
var SAMPLE_N   = 50;            // accuracy: points per stratum
var NEAR_KM    = 1;             // accuracy: stable strata within this of 2017 shore
var PAGE_SIZE  = 12;            // accuracy: points per page
var ASSET_DIR  = 'projects/caspian-seabed/assets/';
var ASSET_ID   = ASSET_DIR + 'az_seabed_stack_' + BASE_YEAR + '_' + LAST_YEAR;
var EXTRAS_ID  = ASSET_DIR + 'az_seabed_extras_' + BASE_YEAR + '_' + LAST_YEAR;

var years = [];
for (var yr = BASE_YEAR; yr <= LAST_YEAR; yr++) years.push(yr);
var yearsAfter = years.slice(1);
var vegYears = years.filter(function (y) { return y >= VEG_START; });

// Coastal zones, north to south (latitude bands); 1–3 arid, 4–5 humid
var ZONES = [
  {name: 'North coast (Samur–Siyazan)',  south: 41.00},
  {name: 'Sumgayit–Absheron–Baku',       south: 40.25},
  {name: 'Sangachal–Alat–Byandovan',     south: 39.50},
  {name: 'Kura delta–Kizilagach',        south: 38.85},
  {name: 'Lankaran–Astara',              south: 38.00}
];
var ARID = [1, 2, 3], HUMID = [4, 5];

// ------------------------------------------------------------ 2. Study area
var azerbaijan = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
  .filter(ee.Filter.eq('country_na', 'Azerbaijan'));

// Latitude limits ~ Samur mouth (RU border) to Astarachay (IR border)
var coastBox = ee.Geometry.Rectangle([48.3, 38.42, 51.2, 41.87]);

// HydroLAKES Caspian polygon: SRTM-era shoreline (c. 2000), when the sea
// stood ~1–2 m higher, so it contains every pixel exposed since 2017.
var caspian = ee.FeatureCollection('projects/sat-io/open-datasets/HydroLakes/lake_poly_v10')
  .filterBounds(ee.Geometry.Point([50.5, 40.0]));
var caspianCore = caspian.geometry().intersection(coastBox, 100);

var region = caspianCore
  .intersection(azerbaijan.geometry().buffer(STRIP_KM * 1000, 200), 100)
  .buffer(500, 100);

// ------------------------------------------------------------ 3. Sentinel-2
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');

function s2Clear(collectionId, start, end) {
  return ee.ImageCollection(collectionId)
    .filterBounds(coastBox)
    .filterDate(start, end)
    .linkCollection(csPlus, ['cs_cdf'])
    .map(function (img) {
      return ee.Image(img.select(['B2', 'B3', 'B4', 'B8', 'B11'])
        .divide(10000)
        .updateMask(img.select('cs_cdf').gte(CS_THR))
        .copyProperties(img, ['system:time_start']));
    });
}
function summer(year) { return [ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 10, 1)]; }

// Summer (Jun–Sep) water mask from L1C TOA: consistent archive back to 2017
function waterMask(year) {
  var s = summer(year);
  var looks = s2Clear('COPERNICUS/S2_HARMONIZED', s[0], s[1])
    .map(function (img) {
      return img.normalizedDifference(['B3', 'B11']).gt(MNDWI_THR);
    });
  return looks.mean().gte(WATER_FREQ)
    .updateMask(looks.count().gte(MIN_OBS))
    .rename('water').clip(region);
}

// Water frequency (%) for each sensitivity MNDWI threshold
function waterFreqs(year) {
  var s = summer(year);
  var looks = s2Clear('COPERNICUS/S2_HARMONIZED', s[0], s[1])
    .map(function (img) {
      var m = img.normalizedDifference(['B3', 'B11']);
      return ee.Image.cat(SENS_MNDWI.map(function (t, i) {
        return m.gt(t).rename('w' + i);
      }));
    });
  return looks.mean().multiply(100).round()
    .updateMask(looks.select(0).count().gte(MIN_OBS))
    .toInt16()
    .rename(SENS_MNDWI.map(function (t, i) { return 'wf' + i + '_' + year; }))
    .clip(region);
}

// Dynamic World built-up probability (%), summer mean
function builtProb(year) {
  var s = summer(year);
  return ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
    .filterBounds(coastBox).filterDate(s[0], s[1])
    .select('built').mean().multiply(100).round().toInt16()
    .rename('built_' + year).clip(region);
}

// Peak-season (Apr–Sep, 90th percentile) NDVI and MSAVI from L2A SR
function vegIndices(year) {
  var col = s2Clear('COPERNICUS/S2_SR_HARMONIZED',
                    ee.Date.fromYMD(year, 4, 1), ee.Date.fromYMD(year, 10, 1))
    .map(function (img) {
      var nir = img.select('B8'), red = img.select('B4');
      var ndvi = img.normalizedDifference(['B8', 'B4']).rename('ndvi');
      var msavi = nir.multiply(2).add(1)
        .subtract(nir.multiply(2).add(1).pow(2)
                     .subtract(nir.subtract(red).multiply(8)).sqrt())
        .divide(2).rename('msavi');
      return ndvi.addBands(msavi);
    });
  return col.reduce(ee.Reducer.percentile([90]))
    .rename(['ndvi', 'msavi']).clip(region);
}

// ------------------------------------------------------------ 4. Assets
function assetExists(id) {
  try { ee.data.getAsset(id); return true; } catch (e) { return false; }
}
var stackExists = assetExists(ASSET_ID);
var extrasExists = assetExists(EXTRAS_ID);
var stack = stackExists ? ee.Image(ASSET_ID) : null;
var extras = extrasExists ? ee.Image(EXTRAS_ID) : null;

function getWater(y) {
  return stack ? stack.select('water_' + y).rename('water') : waterMask(y);
}
function getVeg(y) {
  return stack ? stack.select(['ndvi_' + y, 'msavi_' + y]).divide(10000)
                      .rename(['ndvi', 'msavi'])
               : vegIndices(y);
}

if (!stackExists) {
  var parts = [], policy = {'.default': 'mean'};
  years.forEach(function (y) {
    parts.push(waterMask(y).toInt16().rename('water_' + y));
    policy['water_' + y] = 'mode';
  });
  vegYears.forEach(function (y) {
    parts.push(vegIndices(y).multiply(10000).round().toInt16()
                 .rename(['ndvi_' + y, 'msavi_' + y]));
  });
  Export.image.toAsset({
    image: ee.Image.cat(parts), description: 'AZ_seabed_stack',
    assetId: ASSET_ID, region: region, scale: SCALE, crs: CRS,
    maxPixels: 1e13, pyramidingPolicy: policy
  });
}
if (!extrasExists) {
  Export.image.toAsset({
    image: ee.Image.cat([waterFreqs(BASE_YEAR), waterFreqs(LAST_YEAR),
                         builtProb(BASE_YEAR), builtProb(LAST_YEAR)]),
    description: 'AZ_seabed_extras', assetId: EXTRAS_ID, region: region,
    scale: SCALE, crs: CRS, maxPixels: 1e13,
    pyramidingPolicy: {'.default': 'mean'}
  });
}

// ------------------------------------------------------------ 5. Exposure
var water = {}, exposed = {}, persistent = {}, veg = {};
years.forEach(function (y) { water[y] = getWater(y); });
var baseWater = water[BASE_YEAR].eq(1);

// Exposed in year y = water in BASE_YEAR and land in y (0/1, no mask)
years.forEach(function (y) {
  exposed[y] = baseWater.and(water[y].eq(0)).unmask(0).rename('exposed');
});

// Persistent = exposed in y AND in every later year up to LAST_YEAR
persistent[LAST_YEAR] = exposed[LAST_YEAR];
for (var i = years.length - 2; i >= 0; i--) {
  persistent[years[i]] = exposed[years[i]].and(persistent[years[i] + 1]);
}

// Year each pixel emerged and stayed dry through LAST_YEAR
var emergence = ee.ImageCollection(yearsAfter.map(function (y) {
  return ee.Image.constant(y).toInt16().updateMask(persistent[y]);
})).min().rename('emergence').clip(region);
var em0 = emergence.unmask(0);

vegYears.forEach(function (y) { veg[y] = getVeg(y); });

// ------------------------------------------------------------ 6. Screening
// Inland ring: inside the 500 m buffer but outside the c. 2000 Caspian
// polygon -> coastal ponds, fields, lagoons rather than open-sea seabed
var inRing = ee.Image(0).byte()
  .paint(ee.FeatureCollection([ee.Feature(caspianCore)]), 1).not().rename('ring');
// New built-up land (ports, reclamation) in LAST_YEAR
var built = extras
  ? extras.select('built_' + LAST_YEAR).gte(BUILT_THR).unmask(0).rename('built')
  : ee.Image(0).rename('built');
var clean = inRing.eq(0).and(built.eq(0));

// ------------------------------------------------------------ 7. Bare vs green
// Peak NDVI in the year each pixel emerged (VEG_START onward)
var ndviAtEm = ee.Image(-9).toFloat();
vegYears.forEach(function (y) {
  ndviAtEm = ndviAtEm.where(em0.eq(y), veg[y].select('ndvi').unmask(-9));
});
// 1 = bare at emergence, 2 = green at emergence, 3 = emerged before VEG_START
// or no NDVI, 0 = not persistently exposed
var emClass = ee.Image(0)
  .where(em0.gt(0), 3)
  .where(em0.gt(0).and(ndviAtEm.gt(-9)).and(ndviAtEm.lt(NDVI_BARE)), 1)
  .where(em0.gt(0).and(ndviAtEm.gte(NDVI_BARE)), 2)
  .rename('cls');

// ------------------------------------------------------------ 8. Statistics
var areaKm2 = ee.Image.pixelArea().divide(1e6);
var bands = [], names = [];
function addBand(img, name) { bands.push(img.rename(name)); names.push(name); }

yearsAfter.forEach(function (y) {
  addBand(areaKm2.multiply(exposed[y]), 'exposed_' + y);
  addBand(areaKm2.multiply(persistent[y]), 'persistent_' + y);
});
vegYears.forEach(function (y) {
  var ndvi = veg[y].select('ndvi'), msavi = veg[y].select('msavi');
  var a = areaKm2.multiply(persistent[y]).multiply(ndvi.mask().gt(0)).unmask(0);
  addBand(a, 'vegobs_' + y);
  addBand(ndvi.unmask(0).multiply(a), 'ndviA_' + y);
  addBand(msavi.unmask(0).multiply(a), 'msaviA_' + y);
  addBand(a.multiply(ndvi.unmask(0).gt(NDVI_VEG)), 'vegetated_' + y);
});

var lat = ee.Image.pixelLonLat().select('latitude');
var zone = ee.Image(5);
ZONES.slice(0, 4).reverse().forEach(function (z, k) {
  zone = zone.where(lat.gte(z.south), 4 - k);
});
// key = (ring*2 + built)*1e6 + class*1e5 + zone*1e4 + emergence year
var key = inRing.multiply(2).add(built).multiply(1000000)
  .add(emClass.multiply(100000)).add(zone.multiply(10000)).add(em0)
  .toInt().rename('key');

var grouped = ee.Image.cat(bands).addBands(key).reduceRegion({
  reducer: ee.Reducer.sum().repeat(names.length)
             .group({groupField: names.length, groupName: 'key'}),
  geometry: region, scale: SCALE, crs: CRS, maxPixels: 1e13, tileScale: 4
});

// Sensitivity: exposure BASE->LAST for each MNDWI threshold x frequency cut-off
var sensBands = [], sensNames = [];
if (extras) {
  SENS_MNDWI.forEach(function (t, a) {
    SENS_FREQ.forEach(function (f, b) {
      var w0 = extras.select('wf' + a + '_' + BASE_YEAR);
      var w1 = extras.select('wf' + a + '_' + LAST_YEAR);
      var e = w0.gte(f * 100).and(w1.lt(f * 100)).unmask(0).and(clean);
      sensBands.push(areaKm2.multiply(e).rename('s' + a + b));
      sensNames.push('mndwi' + t + '_freq' + f);
    });
  });
}

// ------------------------------------------------------------ helpers
function csv(name, header, rows) {
  print('#CSV_BEGIN ' + name + '\n' + header.join(',') + '\n' +
        rows.map(function (r) { return r.join(','); }).join('\n') + '\n#CSV_END');
}
function rnd(v, d) {
  return (v === undefined || v === null || isNaN(v)) ? null : Number(Number(v).toFixed(d));
}
function dataTable(rows, cols) {   // cols: [{label, type}], rows: arrays
  return {cols: cols.map(function (c, i) { return {id: 'c' + i, label: c.label, type: c.type}; }),
          rows: rows.map(function (r) { return {c: r.map(function (v) { return {v: v}; })}; })};
}

// ================================================================ ANALYSIS
if (MODE === 'analysis') {
  Map.setOptions('SATELLITE');
  Map.setCenter(49.30, 39.40, 10);   // Kura delta & Kizilagach Bay

  Map.addLayer(water[BASE_YEAR].selfMask(), {palette: ['1f78b4']},
               'Water ' + BASE_YEAR, false);
  Map.addLayer(water[LAST_YEAR].selfMask(), {palette: ['6baed6']},
               'Water ' + LAST_YEAR, false);
  var EMERGE_PAL = ['440154', '472d7b', '3b528b', '2c728e', '21918c',
                    '28ae80', '5ec962', 'addc30', 'fde725'];   // viridis, 1 per year
  Map.addLayer(emergence.updateMask(clean),
               {min: BASE_YEAR + 1, max: LAST_YEAR, palette: EMERGE_PAL},
               'Year of persistent emergence');
  Map.addLayer(emClass.updateMask(emClass.gt(0).and(clean)),
               {min: 1, max: 3, palette: ['d8b365', '1a9641', 'bdbdbd']},
               'Bare (tan) / green (green) at emergence', false);
  Map.addLayer(veg[LAST_YEAR].select('ndvi').updateMask(persistent[LAST_YEAR].and(clean)),
               {min: 0, max: 0.5, palette: ['8c510a', 'd8b365', 'f6e8c3', 'a6d96a', '1a9641']},
               'Peak NDVI ' + LAST_YEAR + ' on exposed seabed', false);
  Map.addLayer(persistent[LAST_YEAR].and(inRing).selfMask(), {palette: ['ff00ff']},
               'Set aside: inland ring', false);
  Map.addLayer(persistent[LAST_YEAR].and(built).selfMask(), {palette: ['ff0000']},
               'Set aside: built-up', false);
  Map.addLayer(ee.Image().paint(ee.FeatureCollection([ee.Feature(region)]), 0, 1),
               {palette: ['ffffff']}, 'Analysis strip', false);

  var legend = ui.Panel({style: {position: 'bottom-left', padding: '6px 8px'}});
  legend.add(ui.Label('Year of emergence', {fontWeight: 'bold', margin: '0 0 4px 0'}));
  yearsAfter.forEach(function (y, i) {
    var idx = Math.round(i * (EMERGE_PAL.length - 1) / Math.max(1, yearsAfter.length - 1));
    legend.add(ui.Panel([
      ui.Label('', {backgroundColor: '#' + EMERGE_PAL[idx], padding: '7px', margin: '1px 6px 1px 0'}),
      ui.Label(String(y), {margin: '1px 0'})
    ], ui.Panel.Layout.flow('horizontal')));
  });
  Map.add(legend);

  print('Exposed Caspian seabed, Azerbaijan coast ' + BASE_YEAR + '–' + LAST_YEAR + ' (v2)');

  if (!stackExists || !extrasExists) {
    print('Missing assets. Tasks tab -> Run ' +
          (!stackExists ? '"AZ_seabed_stack" ' : '') +
          (!extrasExists ? '"AZ_seabed_extras"' : '') + ', then run this script again.');
  } else {
    grouped.evaluate(function (r, err) {
      if (err) { print('Statistics failed: ' + err); return; }
      var G = r.groups.map(function (g) {
        var k = g.key, o = {cls: Math.floor(k / 1e5) % 10, zone: Math.floor(k / 1e4) % 10,
                            em: k % 10000};
        var flags = Math.floor(k / 1e6);
        o.ring = Math.floor(flags / 2); o.built = flags % 2;
        names.forEach(function (n, j) { o[n] = g.sum[j]; });
        return o;
      });
      var sum = function (rows, n) {
        return rows.reduce(function (a, o) { return a + (o[n] || 0); }, 0);
      };
      var C = G.filter(function (o) { return o.ring === 0 && o.built === 0; });
      var inZones = function (zs) { return function (o) { return zs.indexOf(o.zone) >= 0; }; };

      // T1: by year
      var t1 = yearsAfter.map(function (y) {
        var row = [y, rnd(sum(G, 'exposed_' + y), 3), rnd(sum(C, 'exposed_' + y), 3),
          rnd(sum(G.filter(function (o) { return o.ring === 1; }), 'exposed_' + y), 3),
          rnd(sum(G.filter(function (o) { return o.ring === 0 && o.built === 1; }), 'exposed_' + y), 3),
          rnd(sum(C, 'persistent_' + y), 3)];
        if (y >= VEG_START) {
          var ob = sum(C, 'vegobs_' + y);
          row.push(rnd(sum(C, 'ndviA_' + y) / ob, 4), rnd(sum(C, 'msaviA_' + y) / ob, 4),
                   rnd(100 * sum(C, 'vegetated_' + y) / ob, 2));
        } else { row.push(null, null, null); }
        return row;
      });
      csv('by_year', ['year', 'exposed_all_km2', 'exposed_clean_km2', 'set_aside_ring_km2',
                      'set_aside_built_km2', 'persistent_clean_km2', 'mean_ndvi',
                      'mean_msavi', 'vegetated_pct'], t1);

      // T2: zone x year (clean)
      var t2 = [];
      ZONES.forEach(function (z, zi) {
        var Z = C.filter(inZones([zi + 1]));
        yearsAfter.forEach(function (y) {
          var row = [zi + 1, y, rnd(sum(Z, 'exposed_' + y), 3), rnd(sum(Z, 'persistent_' + y), 3)];
          if (y >= VEG_START) {
            var ob = sum(Z, 'vegobs_' + y);
            row.push(rnd(sum(Z, 'ndviA_' + y) / ob, 4), rnd(100 * sum(Z, 'vegetated_' + y) / ob, 2));
          } else { row.push(null, null); }
          t2.push(row);
        });
      });
      csv('by_zone_year', ['zone', 'year', 'exposed_km2', 'persistent_km2', 'mean_ndvi',
                           'vegetated_pct'], t2);

      // T3: class at emergence by zone (clean, persistent in LAST_YEAR)
      var t3 = ZONES.map(function (z, zi) {
        var Z = C.filter(inZones([zi + 1]));
        var byC = [1, 2, 3].map(function (c) {
          return rnd(sum(Z.filter(function (o) { return o.cls === c; }), 'persistent_' + LAST_YEAR), 3);
        });
        return [zi + 1].concat(byC);
      });
      csv('class_by_zone', ['zone', 'bare_at_emergence_km2', 'green_at_emergence_km2',
                            'emerged_2018_km2'], t3);

      // T4: cohort trajectories (arid / humid x bare / green x cohort x year)
      var t4 = [];
      [['arid', ARID], ['humid', HUMID]].forEach(function (grp) {
        [1, 2].forEach(function (c) {
          vegYears.forEach(function (e) {
            var K = C.filter(function (o) {
              return o.cls === c && o.em === e && grp[1].indexOf(o.zone) >= 0;
            });
            vegYears.filter(function (y) { return y >= e; }).forEach(function (y) {
              var ob = sum(K, 'vegobs_' + y);
              if (ob > 0) t4.push([grp[0], c === 1 ? 'bare' : 'green', e, y, y - e, rnd(ob, 4),
                                   rnd(sum(K, 'ndviA_' + y) / ob, 4),
                                   rnd(sum(K, 'msaviA_' + y) / ob, 4),
                                   rnd(100 * sum(K, 'vegetated_' + y) / ob, 2)]);
            });
          });
        });
      });
      csv('trajectories', ['climate', 'class', 'cohort', 'year', 'years_since', 'area_km2',
                           'mean_ndvi', 'mean_msavi', 'vegetated_pct'], t4);

      // Charts
      var pivot = yearsAfter.map(function (y) {
        return [String(y)].concat(ZONES.map(function (z, zi) {
          return rnd(sum(C.filter(inZones([zi + 1])), 'exposed_' + y), 2);
        }));
      });
      print(ui.Chart(dataTable(pivot, [{label: 'Year', type: 'string'}].concat(
          ZONES.map(function (z) { return {label: z.name, type: 'number'}; }))),
        'ColumnChart', {title: 'Exposed seabed by zone, screened (km²)', isStacked: true}));

      // Pooled NDVI by years since emergence
      var maxK = LAST_YEAR - VEG_START, series = [];
      [['arid', 'bare'], ['arid', 'green'], ['humid', 'bare'], ['humid', 'green']].forEach(function (s) {
        series.push(s[0] + ' / ' + s[1] + ' at emergence');
      });
      var pooled = [];
      for (var k = 0; k <= maxK; k++) {
        var row = [k];
        [['arid', 'bare'], ['arid', 'green'], ['humid', 'bare'], ['humid', 'green']].forEach(function (s) {
          var R = t4.filter(function (t) { return t[0] === s[0] && t[1] === s[1] && t[4] === k; });
          var a = R.reduce(function (x, t) { return x + t[5]; }, 0);
          var n = R.reduce(function (x, t) { return x + t[5] * t[6]; }, 0);
          row.push(a > 0.05 ? rnd(n / a, 3) : null);
        });
        pooled.push(row);
      }
      print(ui.Chart(dataTable(pooled, [{label: 'Years since emergence', type: 'number'}].concat(
          series.map(function (s) { return {label: s, type: 'number'}; }))),
        'LineChart', {title: 'Peak NDVI after emergence (screened, pooled cohorts)',
                      pointSize: 4, hAxis: {title: 'Years since emergence'},
                      vAxis: {title: 'Peak NDVI'}}));
      print(ui.Chart(dataTable(t1, ['Year', 'Exposed all', 'Exposed screened', 'Set aside ring',
          'Set aside built', 'Persistent', 'NDVI', 'MSAVI', '% vegetated'].map(function (l, j) {
            return {label: l, type: 'number'}; })), 'Table', {title: 'By year'}));
    });

    // Sensitivity
    ee.Image.cat(sensBands).addBands(zone.toInt().rename('zone')).reduceRegion({
      reducer: ee.Reducer.sum().repeat(sensBands.length)
                 .group({groupField: sensBands.length, groupName: 'zone'}),
      geometry: region, scale: SCALE, crs: CRS, maxPixels: 1e13, tileScale: 4
    }).evaluate(function (r, err) {
      if (err) { print('Sensitivity failed: ' + err); return; }
      var rows = [];
      sensNames.forEach(function (n, j) {
        var byZ = [1, 2, 3, 4, 5].map(function (z) {
          var g = r.groups.filter(function (g) { return g.zone === z; })[0];
          return g ? g.sum[j] : 0;
        });
        var tot = byZ.reduce(function (a, b) { return a + b; }, 0);
        rows.push([SENS_MNDWI[Math.floor(j / SENS_FREQ.length)], SENS_FREQ[j % SENS_FREQ.length],
                   rnd(tot, 3)].concat(byZ.map(function (v) { return rnd(v, 3); })));
      });
      csv('sensitivity_' + BASE_YEAR + '_' + LAST_YEAR,
          ['mndwi_thr', 'water_freq', 'exposed_total_km2', 'z1', 'z2', 'z3', 'z4', 'z5'], rows);
    });

    // Raw grouped table to Drive (every number above can be rebuilt from it)
    Export.table.toDrive({
      collection: ee.FeatureCollection(ee.List(grouped.get('groups')).map(function (g) {
        g = ee.Dictionary(g);
        return ee.Feature(null, ee.Dictionary.fromLists(names, ee.List(g.get('sum')))
          .set('key', g.get('key')));
      })),
      description: 'AZ_seabed_groups_v2', folder: DRIVE_DIR, fileFormat: 'CSV'
    });
    Export.image.toDrive({
      image: ee.Image.cat([
        emergence.updateMask(clean).toFloat().rename('emergence_year'),
        emClass.updateMask(emClass.gt(0).and(clean)).toFloat().rename('class_at_emergence'),
        veg[LAST_YEAR].updateMask(persistent[LAST_YEAR].and(clean))
          .rename(['peak_ndvi', 'peak_msavi'])
      ]).unmask(-9999).toFloat(),
      description: 'AZ_seabed_maps_' + LAST_YEAR, folder: DRIVE_DIR,
      region: region, scale: SCALE, crs: CRS, maxPixels: 1e13,
      formatOptions: {cloudOptimized: true, noData: -9999}
    });
  }
}

// ================================================================ ACCURACY
if (MODE === 'accuracy') {
  var w0 = water[BASE_YEAR].unmask(2), w1 = water[LAST_YEAR].unmask(2);
  var wb = water[BASE_YEAR];
  // near the 2017 shoreline: water and land both within NEAR_KM (100 m grid)
  var near = wb.focalMax({radius: NEAR_KM * 1000, units: 'meters'})
    .and(wb.focalMin({radius: NEAR_KM * 1000, units: 'meters'}).eq(0))
    .reproject({crs: CRS, scale: 100}).unmask(0);
  // 1 = exposed (screened), 2 = stable water near shore, 3 = stable land near shore
  var stratum = ee.Image(0)
    .where(w0.eq(1).and(w1.eq(1)).and(near), 2)
    .where(w0.eq(0).and(w1.eq(0)).and(near), 3)
    .where(persistent[LAST_YEAR].and(clean), 1)
    .toInt().rename('stratum').clip(region);

  // Sampling scans the whole 20 m stack, so it runs once as a batch task
  var SAMPLE_ID = ASSET_DIR + 'az_seabed_accuracy_sample';
  if (!assetExists(SAMPLE_ID)) {
    var sample = stratum.stratifiedSample({
      numPoints: 0, classBand: 'stratum', classValues: [1, 2, 3],
      classPoints: [SAMPLE_N, SAMPLE_N, SAMPLE_N], region: region, scale: SCALE,
      projection: CRS, seed: 42, geometries: true, tileScale: 8
    }).randomColumn('r', 7);
    var areas = ee.List(areaKm2.addBands(stratum).reduceRegion({
      reducer: ee.Reducer.sum().group({groupField: 1, groupName: 'stratum'}),
      geometry: region, scale: SCALE, crs: CRS, maxPixels: 1e13, tileScale: 8
    }).get('groups'));
    var areaDict = ee.Dictionary.fromLists(
      areas.map(function (g) { return ee.Number(ee.Dictionary(g).get('stratum')).format('%d'); }),
      areas.map(function (g) { return ee.Dictionary(g).get('sum'); }));
    // each point carries its stratum's total area (needed for area-weighted accuracy)
    Export.table.toAsset({
      collection: sample.map(function (f) {
        return f.set('stratum_area_km2',
                     areaDict.get(ee.Number(f.get('stratum')).format('%d')));
      }),
      description: 'AZ_seabed_accuracy_sample', assetId: SAMPLE_ID
    });
    print('Tasks tab -> Run "AZ_seabed_accuracy_sample", then run again.');
  }
  var pts = ee.FeatureCollection(SAMPLE_ID).sort('r');   // shuffled -> blind labelling

  var chip = function (pt, year) {
    var s = summer(year);
    // clearest scene on top; the next two clearest fill swath-edge gaps
    var img = ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
      .filterBounds(pt).filterDate(s[0], s[1])
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
      .sort('CLOUDY_PIXEL_PERCENTAGE').limit(3)
      .sort('CLOUDY_PIXEL_PERCENTAGE', false).mosaic();
    var vis = img.visualize({bands: ['B11', 'B8', 'B4'], min: 0, max: 3500, gamma: 1.2});
    var box = ee.Image().byte().paint(ee.FeatureCollection([
      ee.Feature(pt.buffer(30).bounds())]), 1, 1).visualize({palette: ['ff0000']});
    return ui.Thumbnail({
      image: vis.blend(box),
      params: {region: pt.buffer(300).bounds(), dimensions: 120, format: 'png'},
      style: {width: '120px', height: '120px', margin: '1px'}
    });
  };

  if (assetExists(SAMPLE_ID)) pts.evaluate(function (fc) {
    var P = fc.features.map(function (f, i) {
      return {id: i + 1, stratum: f.properties.stratum,
              area: f.properties.stratum_area_km2,
              lon: rnd(f.geometry.coordinates[0], 6), lat: rnd(f.geometry.coordinates[1], 6)};
    });
    csv('sample', ['id', 'stratum', 'stratum_area_km2', 'lon', 'lat'], P.map(function (p) {
      return [p.id, p.stratum, rnd(p.area, 3), p.lon, p.lat];
    }));

    var labels = {};
    var pick = function (id, year) {
      return ui.Select({items: ['?', 'water', 'land', 'unsure'], value: '?',
        style: {width: '118px', margin: '1px'},
        onChange: function (v) { labels[id + '_' + year] = v; }});
    };
    var grid = ui.Panel({layout: ui.Panel.Layout.flow('horizontal', true),
                         style: {stretch: 'both'}});
    var page = P.slice(PAGE * PAGE_SIZE, (PAGE + 1) * PAGE_SIZE);
    page.forEach(function (p) {
      var pt = ee.Geometry.Point([p.lon, p.lat]);
      grid.add(ui.Panel([
        ui.Label('#' + p.id + '   ' + BASE_YEAR + ' | ' + LAST_YEAR,
                 {fontWeight: 'bold', margin: '1px 2px', fontSize: '12px'}),
        ui.Panel([chip(pt, BASE_YEAR), chip(pt, LAST_YEAR)], ui.Panel.Layout.flow('horizontal')),
        ui.Panel([pick(p.id, BASE_YEAR), pick(p.id, LAST_YEAR)], ui.Panel.Layout.flow('horizontal'))
      ], null, {border: '1px solid #bbb', margin: '3px', padding: '2px'}));
    });
    var done = ui.Button('Print labels for this page', function () {
      csv('labels_page' + PAGE, ['id', 'label_' + BASE_YEAR, 'label_' + LAST_YEAR],
          page.map(function (p) {
            return [p.id, labels[p.id + '_' + BASE_YEAR] || '?', labels[p.id + '_' + LAST_YEAR] || '?'];
          }));
    });
    ui.root.clear();
    ui.root.add(ui.Panel([
      ui.Label('Accuracy check, PAGE = ' + PAGE + ' (pages 0–' + (Math.ceil(P.length / PAGE_SIZE) - 1) + ')' +
               ': label the pixel in the red box as water or land in each year. ' +
               'Chips: single clear summer Sentinel-2 scene, SWIR-NIR-red (water is black).',
               {fontSize: '12px'}),
      done, grid], null, {stretch: 'both'}));
  });
}
