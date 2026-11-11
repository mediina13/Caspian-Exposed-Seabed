"""Workflow diagram: data, processing in Google Earth Engine, analysis, and checks on the map.

Output: results/figures/fig13_workflow.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 8})
INK, INK2 = "#0b0b0b", "#52514e"
F = {"data": ("#e7f0fa", "#2a78d6"), "step": ("#f3f2ee", "#8a8983"), "out": ("#e6f4ec", "#1b8f5f"), "check": ("#fbefe0", "#c77a00")}

fig, ax = plt.subplots(figsize=(7.2, 6.3)); ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)

def box(x, y, w, h, title, lines, kind):
    fc, ec = F[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.0", fc=fc, ec=ec, lw=0.9))
    ax.text(x + w / 2, y + h - 1.9, title, ha="center", va="top", fontsize=7.8, fontweight="bold", color=INK)
    if lines:
        ax.text(x + w / 2, y + h - 5.3, "\n".join(lines), ha="center", va="top", fontsize=6.8, color=INK2, linespacing=1.3)

def arrow(x0, y0, x1, y1, lw=0.9, ms=9):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=ms, lw=lw, color=INK2, shrinkA=0, shrinkB=0))

W = 29.0; X = [1.0, 35.5, 70.0]; TOP = 93.0
for x, t in zip(X, ["Data", "Processing in Google Earth Engine", "Analysis"]):
    ax.text(x + W / 2, 98.3, t, ha="center", va="center", fontsize=8.6, fontweight="bold", color=INK)

# column 1: data
d = [("Sentinel-2 Level-1C", ["June to September, 2017–2026"]),
     ("Sentinel-2 Level-2A", ["April to September, 2019–2026"]),
     ("Sea level", ["satellite altimetry, 10-day series"]),
     ("Sea outline, c. 2000", ["HydroLAKES; 10 km coastal strip"]),
     ("Protected areas, population, depth", ["WDPA, GHS-POP, GEBCO"])]
h = 11.2; gap = 3.4; y = TOP
for t, l in d:
    y -= h; box(X[0], y, W, h, t, l, "data"); y -= gap
# column 2: processing
p = [("1  Cloud masking", ["Cloud Score+ of 0.6 or more"], 11.2),
     ("2  Summer water map, each year", ["water when MNDWI is above 0 in at", "least half of the clear observations"], 14.4),
     ("3  Exposed seabed, 20 m grid", ["water in 2017, land in year y;", "landward band and built-up land", "set aside; year of emergence"], 17.6),
     ("4  Peak greenness, each year", ["90th percentile of NDVI and MSAVI;", "vegetated when NDVI is above 0.2"], 14.4)]
y = TOP; ys = []
for t, l, hh in p:
    y -= hh; box(X[1], y, W, hh, t, l, "step"); ys.append((y, hh)); y -= 4.2
for (y0, h0), (y1, h1) in zip(ys[:-1], ys[1:]):
    arrow(X[1] + W / 2, y0 - 0.3, X[1] + W / 2, y1 + h1 + 0.5)
# column 3: analysis
a = [("Response to sea level", ["area against fall in level,", "whole coast and five zones"], 13.0),
     ("Shoreline retreat", ["2026 waterline to 2017 land"], 10.6),
     ("Vegetation paths", ["bare or green at emergence,", "followed for up to seven years"], 13.0),
     ("Protected areas and people", ["overlay; population within", "1 to 10 km of bare seabed"], 13.0),
     ("Projection range", ["observed rate held, and", "GEBCO depth distribution"], 13.0)]
y = TOP
for t, l, hh in a:
    y -= hh; box(X[2], y, W, hh, t, l, "out"); y -= 2.85
ybot = y + 2.85
# column arrows
ymid = (TOP + ybot) / 2
arrow(X[0] + W + 0.8, ymid, X[1] - 0.8, ymid, lw=1.6, ms=13)
arrow(X[1] + W + 0.8, ymid, X[2] - 0.8, ymid, lw=1.6, ms=13)
# checks band
box(X[0], 3.0, 99.0 - X[0], 13.0, "Checks on the map",
    ["150 stratified reference points with area-adjusted accuracy   ·   nine combinations of index threshold and water frequency",
     "independent Landsat record of land inside the sea outline, 1998–2021"], "check")
arrow(X[1] + W / 2, ys[-1][0] - 0.3, X[1] + W / 2, 16.6)
FIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "figures")
fig.savefig(os.path.join(FIG, "fig13_workflow.png"), dpi=300)
print("fig13_workflow.png written")
