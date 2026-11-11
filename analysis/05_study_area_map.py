"""Study-area map: Azerbaijan's Caspian coast, the five zones and the three sites of the
before/after figure.

Coastline and borders: GSHHG as packaged with basemap. The coastline is an older shoreline
and is for location only.

This script needs two extra packages that the other scripts do not use:
    pip install basemap basemap-data-hires

Output: results/figures/fig12_study_area.png
"""
import os

import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.basemap import Basemap

plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 8})
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8983"
LAND, SEA = "#efeeea", "#d8e7f3"
PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
ZONES = [("1  North coast", 41.00, 41.87), ("2  Absheron–Baku", 40.25, 41.00), ("3  Sangachal–Alat", 39.50, 40.25),
         ("4  Kura delta–Kizilagach", 38.85, 39.50), ("5  Lankaran–Astara", 38.42, 38.85)]
CITIES = [("Baku", 49.87, 40.41, "left", (5, 4)), ("Sumgayit", 49.67, 40.59, "right", (-5, 3)), ("Siyazan", 49.11, 41.08, "right", (-5, 0)),
          ("Alat", 49.41, 39.94, "right", (-5, 0)), ("Neftchala", 49.25, 39.38, "right", (-5, 2)),
          ("Lankaran", 48.85, 38.75, "right", (-5, 0)), ("Astara", 48.87, 38.46, "right", (-5, -2))]
SITES = [("A", 49.07, 39.08, 20.0), ("B", 49.40, 39.31, 9.0), ("C", 50.355, 40.27, 6.5)]

fig = plt.figure(figsize=(6.9, 6.6))
ax = fig.add_axes([0.07, 0.06, 0.62, 0.9])
m = Basemap(projection="merc", llcrnrlon=47.6, llcrnrlat=38.25, urcrnrlon=51.15, urcrnrlat=42.05, resolution="h", ax=ax)
m.drawmapboundary(fill_color=SEA, linewidth=0.6, color=INK2)
m.fillcontinents(color=LAND, lake_color=SEA)
m.drawcoastlines(linewidth=0.5, color=INK2)
m.drawcountries(linewidth=0.6, color=MUTED)
m.drawparallels(np.arange(38.5, 42.1, 0.5), labels=[1, 0, 0, 0], fontsize=7, color="#c9c8c2", linewidth=0.3, dashes=[2, 2], textcolor=INK2)
m.drawmeridians(np.arange(48, 51.1, 1), labels=[0, 0, 0, 1], fontsize=7, color="#c9c8c2", linewidth=0.3, dashes=[2, 2], textcolor=INK2)
# zone boundaries across the sea side
for lat in (41.00, 40.25, 39.50, 38.85):
    x0, y = m(48.3, lat); x1, _ = m(51.15, lat)
    ax.plot([x0, x1], [y, y], color=INK, lw=0.7, ls=(0, (4, 3)), zorder=5)
# zone bars at the right edge
for (name, lo, hi), col in zip(ZONES, PAL):
    x, y0 = m(51.02, lo); _, y1 = m(51.02, hi)
    ax.plot([x, x], [y0 + 2500, y1 - 2500], color=col, lw=6, solid_capstyle="butt", zorder=6)
# cities
for name, lon, lat, ha, off in CITIES:
    x, y = m(lon, lat)
    ax.plot(x, y, "o", ms=3.2, mfc="white", mec=INK, mew=0.8, zorder=7)
    ax.annotate(name, (x, y), xytext=off, textcoords="offset points", ha=ha, va="center", fontsize=7.5, color=INK, zorder=8)
# site boxes
for lab, lon, lat, half in SITES:
    dlat = half / 111.0; dlon = half / (111.0 * np.cos(np.radians(lat)))
    x0, y0 = m(lon - dlon, lat - dlat); x1, y1 = m(lon + dlon, lat + dlat)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="#b3261e", lw=1.1, zorder=9))
    if lab == "A":
        ax.text(x0 - 4000, y0, lab, fontsize=8.5, fontweight="bold", color="#b3261e", ha="right", va="bottom", zorder=9)
    else:
        ax.text(x1 + 4000, y1, lab, fontsize=8.5, fontweight="bold", color="#b3261e", ha="left", va="top", zorder=9)
# place names
def lab(txt, lon, lat, **kw):
    x, y = m(lon, lat); ax.text(x, y, txt, zorder=8, **kw)
lab("CASPIAN SEA", 50.35, 39.25, fontsize=8.5, color="#5b7f9e", style="italic", ha="center", rotation=-72)
lab("AZERBAIJAN", 48.25, 40.35, fontsize=8.5, color=MUTED, ha="center")
lab("RUSSIA", 47.95, 41.85, fontsize=7.5, color=MUTED, ha="center")
lab("IRAN", 48.2, 38.36, fontsize=7.5, color=MUTED, ha="center")
lab("Absheron Peninsula", 50.28, 40.72, fontsize=7, color=INK2, ha="center", style="italic")
lab("Kura delta", 49.66, 39.33, fontsize=7, color=INK2, ha="left", style="italic")
lab("Kizilagach\nBay", 48.62, 39.10, fontsize=7, color=INK2, ha="center", style="italic", linespacing=1.1)
lab("Samur River mouth", 48.62, 41.93, fontsize=7, color=INK2, ha="left", style="italic")
# scale bar (50 km at 40 N)
lon0, lat0 = 47.75, 38.47; km = 50; dlon = km / (111.32 * np.cos(np.radians(lat0)))
x0, y0 = m(lon0, lat0); x1, _ = m(lon0 + dlon, lat0)
ax.plot([x0, x1], [y0, y0], color=INK, lw=2, solid_capstyle="butt", zorder=9)
ax.text((x0 + x1) / 2, y0 + 5000, "50 km", ha="center", va="bottom", fontsize=7, color=INK, zorder=9)

# legend panel on the right
lx = 0.715
fig.text(lx, 0.955, "Coastal zones", fontsize=8.5, fontweight="bold", color=INK, va="top")
for i, ((name, lo, hi), col) in enumerate(zip(ZONES, PAL)):
    y = 0.918 - i * 0.047
    fig.patches.append(Rectangle((lx, y - 0.012), 0.012, 0.026, transform=fig.transFigure, fc=col, ec="none"))
    fig.text(lx + 0.022, y + 0.006, name, fontsize=7.6, color=INK, va="center")
    fig.text(lx + 0.022, y - 0.012, f"{lo:.2f}–{hi:.2f}° N", fontsize=6.6, color=INK2, va="center")
fig.text(lx, 0.668, "Sites in Figure 3", fontsize=8.5, fontweight="bold", color=INK, va="top")
for i, t in enumerate(["A  Kizilagach Bay and\n    southern Kura delta", "B  Kura delta spit", "C  Shah Dili spit,\n    Absheron National Park"]):
    fig.text(lx, 0.635 - [0, 0.052, 0.085][i], t, fontsize=7.4, color=INK, va="top", linespacing=1.25)
# inset: whole Caspian
iax = fig.add_axes([0.715, 0.06, 0.265, 0.40])
mi = Basemap(projection="merc", llcrnrlon=44.5, llcrnrlat=35.8, urcrnrlon=56.0, urcrnrlat=47.8, resolution="l", ax=iax)
mi.drawmapboundary(fill_color=SEA, linewidth=0.6, color=INK2)
mi.fillcontinents(color=LAND, lake_color=SEA); mi.drawcoastlines(linewidth=0.4, color=INK2); mi.drawcountries(linewidth=0.4, color=MUTED)
xa, ya = mi(47.6, 38.25); xb, yb = mi(51.15, 42.05)
iax.add_patch(Rectangle((xa, ya), xb - xa, yb - ya, fill=False, ec="#b3261e", lw=1.1, zorder=9))
for txt, lon, lat in [("Russia", 46.4, 46.3), ("Kazakhstan", 53.3, 45.9), ("Turkmenistan", 54.2, 39.9), ("Iran", 51.5, 36.25), ("Azerbaijan", 46.25, 40.9)]:
    x, y = mi(lon, lat); iax.text(x, y, txt, fontsize=6.2, color=INK2, ha="center", va="center", zorder=8)
x, y = mi(51.2, 43.3); iax.text(x, y, "Caspian\nSea", fontsize=6.6, color="#5b7f9e", style="italic", ha="center", va="center", linespacing=1.1)
FIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "figures")
fig.savefig(os.path.join(FIG, "fig12_study_area.png"), dpi=300)
print("fig12_study_area.png written")
