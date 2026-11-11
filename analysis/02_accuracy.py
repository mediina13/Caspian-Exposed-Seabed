"""Accuracy of the exposure map from blind visual labels (150 points, 3 strata).

Inputs   data/accuracy/sample_points.csv, data/accuracy/reference_labels.csv
Outputs  results/tables/accuracy_points_labelled.csv, accuracy_summary.csv, accuracy_confusion.csv

Estimators follow Olofsson et al. (2014), "Good practices for estimating area and assessing
accuracy of land change", Remote Sensing of Environment 148, 42-57.
"""
import numpy as np
import pandas as pd

from common import ACC, TAB

s = pd.read_csv(ACC + "sample_points.csv")
l = pd.read_csv(ACC + "reference_labels.csv")
assert len(l) == 150 and l.id.is_unique
d = s.merge(l, on="id")
AREA = {1: 297.989, 2: 717.966, 3: 503.587}   # stratum areas, km2 (from the sample asset)
NAME = {1: "Exposed (map)", 2: "Stable water near shore (map)", 3: "Stable land near shore (map)"}

def ref(r):
    a, b = r.label_2017, r.label_2026
    if "unsure" in (a, b): return "unsure"
    if a == "water" and b == "land": return "exposed"
    if a == "water" and b == "water": return "water"
    if a == "land" and b == "land": return "land"
    return "other"           # land -> water
d["ref"] = d.apply(ref, axis=1)
d["mapc"] = d.stratum.map({1: "exposed", 2: "water", 3: "land"})

# per-stratum confusion
tab = pd.crosstab(d.stratum.map(NAME), d.ref).reindex(columns=["exposed","water","land","other","unsure"], fill_value=0)
print(tab, "\n")
c = d[d.ref != "unsure"].copy()
c["correct"] = c.ref == c.mapc
n_h = c.groupby("stratum").size(); p_h = c.groupby("stratum").correct.mean()
W = pd.Series(AREA) / sum(AREA.values())

# user's accuracy of "exposed" = share of stratum-1 points that are truly exposed
ua = p_h[1]; ua_se = np.sqrt(ua * (1 - ua) / (n_h[1] - 1))
# overall (area-weighted) accuracy of the 3-class map within the sampled domain
oa = (W * p_h).sum(); oa_se = np.sqrt(((W**2) * p_h * (1 - p_h) / (n_h - 1)).sum())

# area-weighted estimate of true exposed area (Olofsson et al. 2014 style)
pe = c.assign(e=(c.ref == "exposed").astype(float)).groupby("stratum").e.mean()
pe_var = c.assign(e=(c.ref == "exposed").astype(float)).groupby("stratum").e.var(ddof=1)
A = pd.Series(AREA)
est = (A * pe).sum(); est_se = np.sqrt(((A**2) * pe_var / n_h).sum())
# producer's accuracy of exposed
pa = A[1] * pe[1] / est

res = {"n_labelled": int(len(c)), "n_unsure": int((d.ref == "unsure").sum()),
       "exposed_user_acc": ua, "exposed_user_acc_95ci": 1.96 * ua_se,
       "overall_acc_area_weighted": oa, "overall_acc_95ci": 1.96 * oa_se,
       "exposed_area_mapped_km2": A[1], "exposed_area_estimated_km2": est,
       "exposed_area_95ci_km2": 1.96 * est_se, "exposed_producer_acc": pa}
for k, v in res.items(): print(f"{k:32s} {v:.3f}" if isinstance(v, float) else f"{k:32s} {v}")

print("\nerrors:")
print(d[(d.ref != d.mapc) & (d.ref != "unsure")][["id","stratum","ref","lon","lat","note"]].to_string(index=False))
print("\nunsure:"); print(d[d.ref == "unsure"][["id","stratum","label_2017","label_2026","note"]].to_string(index=False))
# exposed points whose 2026 state involved wetland vegetation
veg = d[d.note.fillna("").str.contains("vegetation") & (d.stratum == 1)]
print("\nstratum-1 points noted with vegetation:", len(veg), veg.id.tolist())
d.to_csv(TAB + "accuracy_points_labelled.csv", index=False)
pd.Series(res).to_csv(TAB + "accuracy_summary.csv", header=["value"])
tab.to_csv(TAB + "accuracy_confusion.csv")
