"""Before/after map figure (fig10) from the nine map panels.

The panels in data/map_panels/ are captures of the 720-pixel thumbnails drawn by RUN 7 of
gee/02_extended_analysis.js (SITE 0-2, PANEL 0-2), trimmed and resized to 700 x 700 pixels.
WIDTH_KM is the thumbnail extent in UTM zone 39N, printed by the same run as "#BOX".
Contains modified Copernicus Sentinel data (2017, 2026).
"""
import numpy as np
from PIL import Image
from matplotlib.patches import Rectangle
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.colorbar import ColorbarBase

from common import PANELS, FIG, plt

WIDTH_KM = {0: (353394.695537 - 312699.335314) / 1000, 1: (371185.952865 - 352936.800678) / 1000,
            2: (451687.91748 - 438643.301411) / 1000}
NAMES = {0: "Kizilagach Bay and\nsouthern Kura delta", 1: "Kura delta spit", 2: "Shah Dili spit,\nAbsheron National Park"}
BAR_KM = {0: 10, 1: 5, 2: 3}
N = 700
def load(site, col):
    return np.asarray(Image.open(f"{PANELS}site{site}_col{col}.png").convert("RGB"))

PALY = ['#440154', '#472d7b', '#3b528b', '#2c728e', '#21918c', '#28ae80', '#5ec962', '#addc30', '#fde725']
plt.rcdefaults()          # this figure uses plain image panels, not the chart style
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 8})
fig = plt.figure(figsize=(7.2, 7.95))
gs = fig.add_gridspec(3, 3, left=0.085, right=0.995, top=0.955, bottom=0.075, wspace=0.03, hspace=0.035)
COLS = ["Summer 2017", "Summer 2026", "Year the seabed emerged"]
for s in range(3):
    for c in range(3):
        ax = fig.add_subplot(gs[s, c]); ax.imshow(load(s, c)); ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values(): sp.set_edgecolor("#52514e"); sp.set_linewidth(0.6)
        if s == 0: ax.set_title(COLS[c], fontsize=9, pad=4, color="#0b0b0b")
        if c == 0: ax.set_ylabel(NAMES[s], fontsize=8.5, color="#0b0b0b", labelpad=5)
        if c == 2:   # scale bar
            px = BAR_KM[s] / WIDTH_KM[s] * N; x0 = N - px - 28; y0 = N - 34
            ax.add_patch(Rectangle((x0 - 10, y0 - 34), px + 20, 56, fc="white", ec="none", alpha=0.85, zorder=3))
            ax.plot([x0, x0 + px], [y0, y0], color="#0b0b0b", lw=2.2, solid_capstyle="butt", zorder=4)
            ax.text(x0 + px / 2, y0 - 9, f"{BAR_KM[s]} km", ha="center", va="bottom", fontsize=7.5, color="#0b0b0b", zorder=4)
# legend row
cax = fig.add_axes([0.70, 0.038, 0.285, 0.014])
cb = ColorbarBase(cax, cmap=ListedColormap(PALY), norm=BoundaryNorm(np.arange(2017.5, 2027.5, 1), 9),
                  orientation="horizontal", ticks=range(2018, 2027))
cb.ax.tick_params(labelsize=6.5, length=2, pad=1.5); cb.outline.set_linewidth(0.5)
cb.ax.set_xticklabels([str(y)[2:] if y not in (2018, 2026) else str(y) for y in range(2018, 2027)])
fig.text(0.085, 0.045, "Left and center: Sentinel-2 summer composites (shortwave-infrared, near-infrared, red).\n"
         "Water is dark blue, vegetation green, bare ground pink to tan.\n"
         "Right: gray is land in 2026, blue is water in 2026.",
         fontsize=6.6, color="#52514e", va="center", linespacing=1.35)
fig.savefig(FIG + "fig10_before_after_maps.png", dpi=300)
fig.savefig(FIG + "fig10_before_after_maps_web.png", dpi=170)
print({k: round(v, 2) for k, v in WIDTH_KM.items()})
