"""Shared paths, zone names and figure style for the analysis scripts."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _dir(*parts):
    """Absolute path of a folder inside the repository, with a trailing separator."""
    path = os.path.join(ROOT, *parts)
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, "")


EE = _dir("data", "earth_engine")                # CSV blocks printed by gee/01_exposed_seabed.js
EE_EXT = _dir("data", "earth_engine_extended")   # CSV blocks printed by gee/02_extended_analysis.js
LEVEL = _dir("data", "sea_level")                # NASA Global Water Monitor altimetry
ACC = _dir("data", "accuracy")                   # accuracy sample and reference labels
PANELS = _dir("data", "map_panels")              # map panels for the before/after figure
TAB = _dir("results", "tables")
FIG = _dir("results", "figures")

ZONES = {1: "North coast (Samur–Siyazan)", 2: "Sumgayit–Absheron–Baku",
         3: "Sangachal–Alat–Byandovan", 4: "Kura delta–Kizilagach",
         5: "Lankaran–Astara"}
SHORT = {1: "North coast", 2: "Absheron–Baku", 3: "Sangachal–Alat",
         4: "Kura delta–Kizilagach", 5: "Lankaran–Astara", 0: "Whole coast"}

# categorical palette, fixed order
PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
INK, INK2, GRID, MUTED = "#0b0b0b", "#52514e", "#e4e3df", "#b9b8b2"

plt.rcParams.update({
    "font.family": ["Inter", "DejaVu Sans"], "font.size": 9, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "legend.frameon": False, "figure.dpi": 150,
    "savefig.dpi": 300, "savefig.bbox": "tight",
})
