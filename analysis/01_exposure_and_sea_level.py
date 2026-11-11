"""Exposure by year and zone, link to sea level, vegetation trajectories, threshold sensitivity.

Inputs
  data/earth_engine/      by_year, by_zone_year, class_by_zone, trajectories, sensitivity
                          (CSV blocks printed by gee/01_exposed_seabed.js)
  data/sea_level/         caspian_level_summer_2012_2026.csv (NASA Global Water Monitor, EGM2008 meters)
Outputs
  results/tables/         table_by_year, table_by_zone_year, table_class_by_zone, table_trajectories,
                          table_trajectories_pooled, table_sensitivity, area_vs_level_regression
  results/figures/        fig01 to fig04
"""
import json

import numpy as np
import pandas as pd
from scipy import stats

from common import EE, LEVEL, TAB, FIG, ZONES, SHORT, PAL, INK, INK2, plt

by_year = pd.read_csv(EE + "by_year.csv")
zy = pd.read_csv(EE + "by_zone_year.csv")
cls = pd.read_csv(EE + "class_by_zone.csv")
traj = pd.read_csv(EE + "trajectories.csv")
sens = pd.read_csv(EE + "sensitivity.csv")
lev = pd.read_csv(LEVEL + "caspian_level_summer_2012_2026.csv")

# ---------------------------------------------------------------- sea level
lv = lev.set_index("year")["mean_JJAS_m"]
by_year["level_m"] = by_year["year"].map(lv)
by_year["drop_m"] = lv[2017] - by_year["level_m"]
zy["level_m"] = zy["year"].map(lv)
zy["drop_m"] = lv[2017] - zy["level_m"]

reg = {}
def fit(x, y):
    r = stats.linregress(x, y)
    return {"slope_km2_per_m": r.slope, "slope_se": r.stderr,
            "intercept": r.intercept, "r2": r.rvalue ** 2, "p": r.pvalue,
            "n": len(x)}
reg["total"] = fit(by_year["drop_m"], by_year["exposed_clean_km2"])
for z in ZONES:
    s = zy[zy.zone == z]
    reg[f"zone{z}"] = fit(s["drop_m"], s["exposed_km2"])
reg_df = pd.DataFrame(reg).T
reg_df.index = ["All zones"] + [ZONES[z] for z in ZONES]
reg_df.to_csv(TAB + "area_vs_level_regression.csv", float_format="%.4f")

# ---------------------------------------------------------------- tables
by_year.to_csv(TAB + "table_by_year.csv", index=False, float_format="%.4f")
zy2 = zy.copy(); zy2["zone_name"] = zy2.zone.map(ZONES)
zy2.to_csv(TAB + "table_by_zone_year.csv", index=False, float_format="%.4f")
cls2 = cls.copy(); cls2["zone_name"] = cls2.zone.map(ZONES)
cls2.to_csv(TAB + "table_class_by_zone.csv", index=False, float_format="%.4f")
traj.to_csv(TAB + "table_trajectories.csv", index=False, float_format="%.4f")
sens.to_csv(TAB + "table_sensitivity.csv", index=False, float_format="%.4f")

# pooled trajectories (area-weighted across cohorts)
traj["w"] = traj["area_km2"] * traj["mean_ndvi"]
traj["wm"] = traj["area_km2"] * traj["mean_msavi"]
pool = (traj.groupby(["climate", "class", "years_since"])
        .agg(area=("area_km2", "sum"), w=("w", "sum"), wm=("wm", "sum"),
             n_cohorts=("cohort", "nunique")).reset_index())
pool["ndvi"] = pool.w / pool.area
pool["msavi"] = pool.wm / pool.area
pool["coast"] = pool.climate.map({"arid": "northern and central (zones 1-3)", "humid": "southern (zones 4-5)"})
pool.drop(columns=["w", "wm"]).to_csv(TAB + "table_trajectories_pooled.csv",
                                      index=False, float_format="%.4f")

# ---------------------------------------------------------------- Fig 1
fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.3, 5.2), sharex=True,
                             gridspec_kw={"height_ratios": [2.2, 1]})
yrs = sorted(zy.year.unique())
bottom = np.zeros(len(yrs))
for i, z in enumerate(ZONES):
    v = zy[zy.zone == z].set_index("year").loc[yrs, "exposed_km2"].values
    a1.bar(yrs, v, bottom=bottom, color=PAL[i], width=0.72,
           edgecolor="white", linewidth=1.0, label=SHORT[z])
    bottom += v
for x, t in zip(yrs, bottom):
    a1.text(x, t + 4, f"{t:.0f}", ha="center", va="bottom", fontsize=7.5, color=INK2)
a1.set_ylabel("Exposed seabed since 2017 (km²)")
a1.legend(loc="upper left", ncol=2, fontsize=7.5)
a1.set_ylim(0, bottom.max() * 1.15)
a1.grid(axis="x", visible=False)
ly = lev[lev.year.between(2017, 2026)]
a2.plot(ly.year, ly.mean_JJAS_m, color=INK, lw=1.6, marker="o", ms=4)
a2.errorbar(ly.year, ly.mean_JJAS_m, yerr=ly.sd_JJAS_m, fmt="none",
            ecolor=INK2, elinewidth=0.8, capsize=2)
a2.set_ylabel("Summer level (m)")
a2.set_xticks(range(2017, 2027))
a2.text(0.01, 0.06, "Jun–Sep mean, satellite altimetry (NASA GWM), EGM2008 datum",
        transform=a2.transAxes, fontsize=7, color=INK2)
fig.align_ylabels()
fig.savefig(FIG + "fig01_exposed_area_by_zone_and_sea_level.png")
plt.close(fig)

# ---------------------------------------------------------------- Fig 3
fig, ax = plt.subplots(figsize=(4.6, 3.6))
x = by_year["drop_m"]; y = by_year["exposed_clean_km2"]
ax.scatter(x, y, s=28, color=PAL[0], edgecolor="white", linewidth=1.2, zorder=3)
OFF = {2020: (-26, 4), 2025: (-26, 4)}
for xi, yi, yr in zip(x, y, by_year.year):
    ax.annotate(str(yr), (xi, yi), xytext=OFF.get(yr, (5, -4)), textcoords="offset points",
                fontsize=7, color=INK2)
r = reg["total"]
xx = np.linspace(0, x.max() * 1.05, 50)
ax.plot(xx, r["intercept"] + r["slope_km2_per_m"] * xx, color=INK2, lw=1, ls="--")
ax.set_xlabel("Fall in summer level since 2017 (m)")
ax.set_ylabel("Exposed seabed (km²)")
ax.text(0.03, 0.95, f"{r['slope_km2_per_m']:.0f} ± {r['slope_se']:.0f} km² per metre\n"
        f"R² = {r['r2']:.2f}, n = {r['n']}", transform=ax.transAxes, va="top",
        fontsize=8, color=INK)
fig.savefig(FIG + "fig02_area_vs_sea_level.png")
plt.close(fig)

# ---------------------------------------------------------------- Fig 4
fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.0), sharey=True)
# the Earth Engine script labels zones 1-3 "arid" and zones 4-5 "humid"; these are group names only
for ax, (clim, title) in zip(axs, [("arid", "Northern and central coast (zones 1–3)"),
                                    ("humid", "Southern coast (zones 4–5)")]):
    for c, col, ls in [("bare", PAL[1], "-"), ("green", PAL[2], "--")]:
        s = pool[(pool.climate == clim) & (pool["class"] == c) & (pool.area > 0.05)]
        ax.plot(s.years_since, s.ndvi, color=col, lw=2, ls=ls, marker="o", ms=4,
                label=f"{c} when it emerged")
    ax.set_title(title, fontsize=9, loc="left", color=INK)
    ax.set_xlabel("Years since emergence")
    ax.axhline(0.2, color=INK2, lw=0.8, ls=":")
axs[0].set_ylabel("Peak NDVI (area-weighted)")
axs[0].legend(fontsize=7.5, loc="upper left")
fig.savefig(FIG + "fig03_ndvi_after_emergence.png")
plt.close(fig)

# ---------------------------------------------------------------- Fig 5
fig, ax = plt.subplots(figsize=(4.6, 3.0))
labels, vals = [], []
for _, r_ in sens.iterrows():
    labels.append(f"MNDWI>{r_.mndwi_thr:+.1f}, freq≥{r_.water_freq:.2f}")
    vals.append(r_.exposed_total_km2)
cols = [PAL[0] if (abs(r_.mndwi_thr) < 1e-9 and abs(r_.water_freq - 0.5) < 1e-9)
        else "#9ec5f4" for _, r_ in sens.iterrows()]
yy = np.arange(len(vals))
ax.barh(yy, vals, color=cols, height=0.7)
ax.set_yticks(yy); ax.set_yticklabels(labels, fontsize=7)
ax.invert_yaxis()
for yi, v in zip(yy, vals):
    ax.text(v + 3, yi, f"{v:.0f}", va="center", fontsize=7, color=INK2)
ax.set_xlabel(f"Exposed seabed 2017→2026 (km²)")
ax.grid(axis="y", visible=False)
fig.savefig(FIG + "fig04_threshold_sensitivity.png")
plt.close(fig)

print(json.dumps({k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in reg.items()}, indent=1))
print(pool.to_string())
