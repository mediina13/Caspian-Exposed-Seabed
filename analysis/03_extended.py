"""Extended analysis: long-term record, retreat, bare and protected seabed, population,
depth test and projection, reference vegetation.

Inputs
  data/earth_engine_extended/   CSV blocks printed by gee/02_extended_analysis.js
  data/earth_engine/by_year.csv
  data/sea_level/caspian_level_1992_2026.csv (NASA Global Water Monitor)
Outputs
  results/tables/               extended_summary.json and the extended tables
  results/figures/              fig05 to fig09 and fig11 (fig10 is made by 04_map_figure.py)
"""
import json

import numpy as np
import pandas as pd
from scipy import stats

from common import EE, EE_EXT, LEVEL, TAB, FIG, SHORT, PAL, INK, INK2, MUTED, plt

R = {}

# ------------------------------------------------------------ long-term record
lev = pd.read_csv(LEVEL + "caspian_level_1992_2026.csv").set_index("year")
j = pd.read_csv(EE_EXT + "jrc_water_core.csv").set_index("year")
s = pd.read_csv(EE_EXT + "s2_water_core.csv").set_index("year")
j["perm_tot"] = j[["perm1", "perm2", "perm3", "perm4", "perm5"]].sum(axis=1)
s["water_tot"] = s[["w1", "w2", "w3", "w4", "w5"]].sum(axis=1)
ov = j.index.intersection(s.index)                       # 2017-2021
k = ((s.loc[ov, "land_total"] - j.loc[ov, "notw_tot"]) / j.loc[ov, "seas_tot"])
R["overlap_years"] = [int(ov.min()), int(ov.max())]
R["k_seasonal_share"] = {"mean": k.mean(), "min": k.min(), "max": k.max()}
R["change_2017_2021_km2"] = {"jrc_notwater": j.loc[2021, "notw_tot"] - j.loc[2017, "notw_tot"],
                             "jrc_permanent_loss": j.loc[2017, "perm_tot"] - j.loc[2021, "perm_tot"],
                             "s2_land": s.loc[2021, "land_total"] - s.loc[2017, "land_total"]}
# Sentinel-2-equivalent land for Landsat years: not-water + k * seasonal
j["land_s2eq"] = j["notw_tot"] + k.mean() * j["seas_tot"]
lt = pd.DataFrame({"jrc_notwater_km2": j["notw_tot"], "jrc_seasonal_km2": j["seas_tot"],
                   "jrc_land_s2equiv_km2": j["land_s2eq"], "s2_land_km2": s["land_total"]})
lt = lt.reindex(range(1993, 2027))
lt["level_JJAS_m"] = lev["mean_JJAS_m"]; lt["level_annual_m"] = lev["mean_all_m"]
lt.to_csv(TAB + "table_longterm_land_and_level.csv", float_format="%.3f")
base05 = j.loc[2005, "land_s2eq"]
R["land_in_2000_sea_polygon_km2"] = {"2005_s2equiv": base05, "2010_jrc_notwater": j.loc[2010, "notw_tot"],
    "2017_s2": s.loc[2017, "land_total"], "2026_s2": s.loc[2026, "land_total"],
    "emerged_2005_to_2026": s.loc[2026, "land_total"] - base05}
R["level_fall_m"] = {"1995_2026": lev.mean_JJAS_m[1995] - lev.mean_JJAS_m[2026],
                     "2005_2026": lev.mean_JJAS_m[2005] - lev.mean_JJAS_m[2026],
                     "2017_2026": lev.mean_JJAS_m[2017] - lev.mean_JJAS_m[2026]}
# rate from the Landsat record alone, 2010-2021 (land vs summer level)
jj = j.loc[2010:2021]
r = stats.linregress(-(lev.mean_JJAS_m.loc[2010:2021]), jj["notw_tot"])
R["jrc_rate_2010_2021_km2_per_m"] = {"slope": r.slope, "se": r.stderr, "r2": r.rvalue ** 2}
r2 = stats.linregress(-(lev.mean_JJAS_m.loc[2017:2026]), s["land_total"])
R["s2_rate_2017_2026_km2_per_m"] = {"slope": r2.slope, "se": r2.stderr, "r2": r2.rvalue ** 2}

# ------------------------------------------------------------ retreat and slope
rt = pd.read_csv(EE_EXT + "retreat_by_zone.csv")
fall = R["level_fall_m"]["2017_2026"]
rt["slope_1_in"] = rt["p50"] / fall
rt["slope_pct"] = 100 * fall / rt["p50"]
rt.to_csv(TAB + "table_retreat_by_zone.csv", index=False, float_format="%.2f")

# ------------------------------------------------------------ affected
b = pd.read_csv(EE_EXT + "bare_by_zone.csv")
b["vegetated_km2"] = b.exposed_km2 - b.bare_km2; b["bare_pct"] = 100 * b.bare_km2 / b.exposed_km2
b.to_csv(TAB + "table_bare_by_zone.csv", index=False, float_format="%.2f")
tot = b.exposed_km2.sum(); bare = b.bare_km2.sum()
R["bare_2026_km2"] = {"total": bare, "share_of_exposed": bare / tot,
                      "zones_1_3": b[b.zone <= 3].bare_km2.sum(),
                      "zones_1_3_share_of_bare": b[b.zone <= 3].bare_km2.sum() / bare}
pa = pd.read_csv(EE_EXT + "pa_union.csv").set_index("quantity")["km2"]
R["protected"] = {"any_designation_km2": pa["any_designation_exposed_km2"], "any_share": pa["any_designation_exposed_km2"] / tot,
                  "national_km2": pa["national_pa_exposed_km2"], "national_share": pa["national_pa_exposed_km2"] / tot,
                  "outside_km2": tot - pa["any_designation_exposed_km2"]}
pd.read_csv(EE_EXT + "protected_areas.csv").sort_values("exposed_km2", ascending=False).to_csv(TAB + "table_protected_areas.csv", index=False)
pop = pd.read_csv(EE_EXT + "population_near_seabed.csv"); pop.to_csv(TAB + "table_population_near_seabed.csv", index=False)
R["population_region_total"] = int(pd.read_csv(EE_EXT + "population_region_total.csv").iloc[0, 0])

# ------------------------------------------------------------ depth test and projection
g = pd.read_csv(EE_EXT + "gebco_hyps_core.csv").sort_values("z_m", ascending=False).reset_index(drop=True)
g["exposed_share"] = g.exposed_km2 / g.water2017_km2
gt = pd.read_csv(EE_EXT + "gebco_core_totals.csv").iloc[0]
obs = 297.988
# skill: how much of GEBCO's shallowest 298 km2 actually dried out
cum = 0; hit = 0
for _, row in g.iterrows():
    take = min(row.water2017_km2, obs - cum)
    if take <= 0: break
    hit += row.exposed_km2 * take / row.water2017_km2; cum += take
R["gebco_skill"] = {"overlap_km2": hit, "overlap_share": hit / obs, "random_share": obs / gt.water2017_km2,
                    "share_exposed_by_bin": {int(z): round(v, 3) for z, v in zip(g.z_m, g.exposed_share) if -32 <= z <= -28}}
def F(zthr):      # 2017 water area with GEBCO z >= zthr; integer bins spread over [z-0.5, z+0.5]
    a = 0.0
    for _, row in g.iterrows():
        lo, hi = row.z_m - 0.5, row.z_m + 0.5
        a += row.water2017_km2 * np.clip((hi - zthr) / (hi - lo), 0, 1)
    return a
zs = np.linspace(-27, -40, 13001); Fs = np.array([F(z) for z in zs])
zstar = zs[np.argmin(np.abs(Fs - obs))]                 # GEBCO-equivalent 2026 waterline
rate = 234.06
proj = []
for d in [1, 2, 3, 5, 7.5, 10]:                      # further fall below the 2026 summer level
    proj.append({"further_fall_below_2026_m": d, "constant_rate_additional_km2": rate * d,
                 "gebco_calibrated_additional_km2": F(zstar - d) - obs})
proj = pd.DataFrame(proj)
proj["constant_rate_total_since_2017_km2"] = proj.constant_rate_additional_km2 + obs
proj["gebco_total_since_2017_km2"] = proj.gebco_calibrated_additional_km2 + obs
proj.to_csv(TAB + "table_projection.csv", index=False, float_format="%.1f")
R["gebco_zstar_2026"] = zstar
dd = np.linspace(0, 10, 201)
curve = pd.DataFrame({"further_fall_m": dd, "constant_rate_km2": rate * dd,
                      "gebco_km2": [F(zstar - x) - obs for x in dd]})
curve.to_csv(TAB + "projection_curves.csv", index=False, float_format="%.2f")

# ------------------------------------------------------------ reference vegetation on stable land
ref = pd.read_csv(EE_EXT + "reference_ndvi.csv")
ref["surface"] = ref.in_ring.map({1: "old coastal land (500 m band)", 0: "seabed emerged before 2017"})
ref[["zone", "surface", "year", "area_km2", "mean_ndvi", "vegetated_pct"]].to_csv(TAB + "table_reference_ndvi.csv", index=False)
old = ref[(ref.in_ring == 0) & (ref.zone <= 3)]
pooled = old.groupby("year").apply(lambda q: (q.vegetated_pct * q.area_km2).sum() / q.area_km2.sum())
R["old_seabed_zones_1_3"] = {"area_km2": old[old.year == 2026].area_km2.sum(),
                             "vegetated_pct_2019": pooled[2019], "vegetated_pct_2026": pooled[2026]}
R["old_land_vegetated_pct"] = {int(z): {"2019": q[q.year == 2019].vegetated_pct.iloc[0], "2026": q[q.year == 2026].vegetated_pct.iloc[0]}
                               for z, q in ref[ref.in_ring == 1].groupby("zone")}

json.dump(R, open(TAB + "extended_summary.json", "w"), indent=1, default=float)
print(json.dumps(R, indent=1, default=lambda x: round(float(x), 3)))
print(rt.round(1).to_string(index=False)); print(b.round(2).to_string(index=False)); print(proj.round(0).to_string(index=False))
print(lt.loc[1998:2026].round(1).to_string())

# ============================================================ figures
# ---- fig 5: long-term record
fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.3, 5.0), sharex=True, gridspec_kw={"height_ratios": [1, 1.5]})
L = lev.loc[1993:2026]
a1.plot(L.index, L.mean_JJAS_m, color=INK, lw=1.6, marker="o", ms=3)
a1.set_ylabel("Summer sea level\n(m, EGM2008)")
a1.annotate("2005 high stand", (2005, L.mean_JJAS_m[2005]), xytext=(2006.5, -25.95), fontsize=7.5, color=INK2,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
a1.text(2008.5, -28.2, f"−{R['level_fall_m']['2005_2026']:.1f} m from 2005 to 2026", fontsize=8, color=INK)
a2.plot(j.index, j.notw_tot, color=PAL[0], lw=2, marker="o", ms=3.5, label="Landsat (JRC), land all year")
a2.plot(s.index, s.land_total, color=PAL[1], lw=2, marker="o", ms=3.5, label="Sentinel-2 (this study), summer land")
a2.set_ylabel("Land inside the c. 2000\nsea outline (km²)")
a2.legend(loc="upper left", fontsize=7.5)
a2.annotate("seabed starts to emerge\n(about 2010)", (2010, j.notw_tot[2010]), xytext=(2001.5, 130), fontsize=7.5, color=INK2,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
a2.text(2026.3, s.land_total[2026], f"{s.land_total[2026]:.0f}", fontsize=8, color=INK, va="center")
a2.set_xlim(1992.5, 2028.5); a2.set_xticks(range(1995, 2027, 5))
fig.align_ylabels(); fig.savefig(FIG + "fig05_longterm_land_and_level.png"); plt.close(fig)

# ---- fig 6: retreat distance by zone
fig, ax = plt.subplots(figsize=(6.0, 2.9))
order = [0, 1, 2, 3, 4, 5]; ypos = {z: i for i, z in enumerate(order)}
for z in order:
    r_ = rt[rt.zone == z].iloc[0]; y = ypos[z]; c = INK if z == 0 else PAL[0]
    ax.plot([r_.p10, r_.p90], [y, y], color=c, lw=5, alpha=0.28, solid_capstyle="round")
    ax.plot([r_.p25, r_.p75], [y, y], color=c, lw=5, alpha=0.55, solid_capstyle="round")
    ax.plot(r_.p50, y, "o", color=c, ms=7, mec="white", mew=1.2, zorder=3)
    ax.plot(r_["max"], y, "|", color=INK2, ms=9, mew=1.4)
    ax.text(r_["max"] * 1.12, y, f"median {r_.p50:.0f} m · max {r_['max']/1000:.1f} km", va="center", fontsize=7.5, color=INK2)
ax.set_xscale("log"); ax.set_xlim(15, 60000)
ax.set_xticks([20, 50, 100, 200, 500, 1000, 2000, 5000]); ax.set_xticklabels(["20", "50", "100", "200", "500", "1 km", "2 km", "5 km"])
ax.set_yticks(list(ypos.values())); ax.set_yticklabels([SHORT[z] for z in order]); ax.invert_yaxis()
ax.grid(axis="y", visible=False); ax.minorticks_off()
ax.set_xlabel("Shoreline retreat 2017→2026 (dot = median, bars = 25–75% and 10–90%, tick = maximum)")
fig.savefig(FIG + "fig06_retreat_by_zone.png"); plt.close(fig)

# ---- fig 7: bare vs vegetated by zone, and protection status
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.8, 2.7), gridspec_kw={"width_ratios": [1.5, 1]})
yy = np.arange(5)
a1.barh(yy, b.bare_km2, color=PAL[1], height=0.62, label="Still bare in 2026", edgecolor="white", lw=1)
a1.barh(yy, b.vegetated_km2, left=b.bare_km2, color=PAL[2], height=0.62, label="Vegetated", edgecolor="white", lw=1)
for y, r_ in zip(yy, b.itertuples()):
    a1.text(r_.exposed_km2 + 3, y, f"{r_.bare_km2:.0f} bare of {r_.exposed_km2:.0f}", va="center", fontsize=7.5, color=INK2)
a1.set_yticks(yy); a1.set_yticklabels([SHORT[z] for z in b.zone]); a1.invert_yaxis(); a1.set_xlim(0, 285)
a1.set_xlabel("Exposed seabed, 2026 (km²)"); a1.legend(fontsize=7.5, loc="lower right"); a1.grid(axis="y", visible=False)
P = R["protected"]; parts = [("National park or reserve", P["national_km2"], PAL[0]),
     ("Emerald Network site only", P["any_designation_km2"] - P["national_km2"], "#86b6ef"), ("No designation", P["outside_km2"], MUTED)]
bottom = 0
for name, v, c in parts:
    a2.bar([0], [v], bottom=bottom, color=c, width=0.5, edgecolor="white", lw=1)
    a2.text(0.32, bottom + v / 2, f"{name}\n{v:.0f} km² ({100 * v / tot:.0f}%)", va="center", fontsize=7.5, color=INK)
    bottom += v
a2.set_xlim(-0.4, 1.9); a2.set_xticks([]); a2.set_ylabel("Exposed seabed (km²)"); a2.grid(axis="x", visible=False)
a2.spines["bottom"].set_visible(False)
fig.tight_layout(); fig.savefig(FIG + "fig07_bare_and_protected.png"); plt.close(fig)

# ---- fig 8: population near bare exposed seabed
fig, ax = plt.subplots(figsize=(4.4, 2.8))
x = np.arange(len(pop)); v = pop.pop_near_bare_exposed / 1e6
ax.bar(x, v, color=PAL[0], width=0.6)
for xi, vi in zip(x, v): ax.text(xi, vi + 0.04, f"{vi:.2f} M" if vi >= 1 else f"{vi * 1000:.0f} k", ha="center", fontsize=8, color=INK)
ax.set_xticks(x); ax.set_xticklabels([f"within {d} km" for d in pop.distance_km]); ax.set_ylabel("People (millions, GHSL 2020)")
ax.grid(axis="x", visible=False); ax.set_ylim(0, v.max() * 1.15)
fig.savefig(FIG + "fig08_population_near_bare_seabed.png"); plt.close(fig)

# ---- fig 9: projection test
by = pd.read_csv(EE + "by_year.csv")
lv17 = lev.mean_JJAS_m[2017]; lv26 = lev.mean_JJAS_m[2026]
fig, ax = plt.subplots(figsize=(6.0, 3.6))
ax.plot(lev.mean_JJAS_m.loc[by.year].values - lv26, by.exposed_clean_km2, "o", color=INK, ms=4.5, label="Observed, 2018–2026", zorder=4)
ax.fill_between(-curve.further_fall_m, curve.constant_rate_km2 + obs, curve.gebco_km2 + obs, color=PAL[0], alpha=0.13, lw=0)
ax.plot(-curve.further_fall_m, curve.constant_rate_km2 + obs, color=PAL[0], lw=2, label="If the observed rate holds (234 km² per m)")
ax.plot(-curve.further_fall_m, curve.gebco_km2 + obs, color=PAL[0], lw=2, ls="--", label="GEBCO 2023 depths, calibrated to 2026")
for d in (5, 10):
    lo = rate * d + obs; hi = F(zstar - d)
    ax.plot([-d, -d], [lo, hi], color=INK2, lw=0.8)
    ax.text(-d + 0.2, (lo + hi) / 2, f"{lo:,.0f}–{hi:,.0f} km²", fontsize=8, color=INK, va="center", ha="right")
ax.plot([0, 0], [0, 2500], color=INK2, lw=0.8, ls=":"); ax.text(0.12, 2350, "2026 level", fontsize=7.5, color=INK2, ha="right")
ax.set_xlim(1.6, -10.4); ax.set_ylim(0, 4500)
ax.set_xlabel("Summer sea level relative to 2026 (m)"); ax.set_ylabel("Seabed exposed since 2017 (km²)")
ax.legend(loc="upper left", fontsize=7.5)
fig.savefig(FIG + "fig09_projection_range.png"); plt.close(fig)

# ---- fig 11: reference vegetation (fig 10 is the map figure, made by make_map_figure.py)
TITLE2 = {1: "North coast", 2: "Absheron–Baku", 3: "Sangachal–Alat", 4: "Kura delta–\nKizilagach", 5: "Lankaran–Astara"}
SERIES = [(1, INK2, "Old coastal land beside the seabed"), (0, PAL[0], "Seabed that emerged before 2017")]
fig, axs = plt.subplots(1, 5, figsize=(7.2, 2.6), sharey=True)
for ax, z in zip(axs, [1, 2, 3, 4, 5]):
    last = {}
    for ring, col, lab in SERIES:
        q = ref[(ref.zone == z) & (ref.in_ring == ring)].sort_values("year")
        ax.plot(q.year, q.vegetated_pct, color=col, lw=2, marker="o", ms=3, label=lab)
        last[ring] = q.vegetated_pct.iloc[-1]
    gap = last[1] - last[0]                              # keep the two end labels apart when the lines meet
    off = {1: 0, 0: 0} if abs(gap) >= 9 else ({1: 5, 0: -5} if gap >= 0 else {1: -5, 0: 5})
    for ring, col, lab in SERIES:
        ax.text(2026.35, last[ring] + off[ring], f"{last[ring]:.0f}", fontsize=7.5, color=col, va="center")
    ax.set_title(TITLE2[z], fontsize=8.5, loc="left", color=INK, linespacing=1.1)
    ax.set_xticks([2019, 2022, 2026]); ax.set_xticklabels(["2019", "2022", "2026"], fontsize=7.5)
    ax.set_xlim(2018.5, 2028.6); ax.set_ylim(0, 112); ax.set_yticks([0, 20, 40, 60, 80, 100]); ax.grid(axis="x", visible=False)
axs[0].set_ylabel("Vegetated share (%)\n(peak NDVI above 0.2)")
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=2, fontsize=7.5, bbox_to_anchor=(0.5, -0.04))
fig.subplots_adjust(wspace=0.16, bottom=0.2)
fig.savefig(FIG + "fig11_reference_vegetation.png"); plt.close(fig)
print(proj.round(0).to_string(index=False))
