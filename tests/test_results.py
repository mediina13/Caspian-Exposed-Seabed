"""Checks on the headline numbers.

Run `make all` first (or the four scripts in analysis/), then `python -m pytest -q`.
"""
import json
import os

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB = os.path.join(ROOT, "results", "tables")
FIG = os.path.join(ROOT, "results", "figures")


def table(name, **kw):
    return pd.read_csv(os.path.join(TAB, name), **kw)


@pytest.fixture(scope="module")
def summary():
    with open(os.path.join(TAB, "extended_summary.json")) as f:
        return json.load(f)


def test_exposed_area_2026():
    by = table("table_by_year.csv").set_index("year")
    assert by.loc[2026, "exposed_clean_km2"] == pytest.approx(297.988, abs=0.001)
    assert by.loc[2026, "exposed_all_km2"] == pytest.approx(320.145, abs=0.001)
    assert by.loc[2025, "exposed_clean_km2"] == pytest.approx(308.214, abs=0.001)


def test_zones_sum_to_total():
    zy = table("table_by_zone_year.csv")
    total = zy[zy.year == 2026].exposed_km2.sum()
    assert total == pytest.approx(297.988, abs=0.01)
    share_zone4 = zy[(zy.year == 2026) & (zy.zone == 4)].exposed_km2.iloc[0] / total
    assert share_zone4 == pytest.approx(0.67, abs=0.01)


def test_sea_level_fall():
    by = table("table_by_year.csv").set_index("year")
    assert by.loc[2026, "drop_m"] == pytest.approx(1.292, abs=0.001)


def test_rate_per_meter():
    reg = table("area_vs_level_regression.csv", index_col=0)
    assert reg.loc["All zones", "slope_km2_per_m"] == pytest.approx(234.06, abs=0.01)
    assert reg.loc["All zones", "slope_se"] == pytest.approx(6.83, abs=0.01)
    assert reg.loc["All zones", "r2"] > 0.99
    ratio = reg.loc["Kura delta–Kizilagach", "slope_km2_per_m"] / reg.loc["Lankaran–Astara", "slope_km2_per_m"]
    assert ratio == pytest.approx(25.6, abs=0.1)


def test_accuracy():
    acc = table("accuracy_summary.csv", index_col=0)["value"]
    assert acc["n_labelled"] == 139 and acc["n_unsure"] == 11
    assert acc["exposed_user_acc"] == pytest.approx(0.9545, abs=0.0001)
    assert acc["exposed_producer_acc"] == pytest.approx(0.823, abs=0.001)
    assert acc["overall_acc_area_weighted"] == pytest.approx(0.9207, abs=0.0001)
    assert acc["exposed_area_estimated_km2"] == pytest.approx(345.5, abs=0.1)
    assert acc["exposed_area_95ci_km2"] == pytest.approx(60.8, abs=0.1)


def test_threshold_sensitivity():
    sens = table("table_sensitivity.csv")
    assert sens.exposed_total_km2.min() == pytest.approx(275, abs=1)
    assert sens.exposed_total_km2.max() == pytest.approx(308, abs=1)


def test_long_term_record(summary):
    land = summary["land_in_2000_sea_polygon_km2"]
    assert land["emerged_2005_to_2026"] == pytest.approx(425.2, abs=0.1)
    assert land["2026_s2"] == pytest.approx(441.06, abs=0.01)
    assert summary["level_fall_m"]["2005_2026"] == pytest.approx(2.311, abs=0.001)
    assert summary["jrc_rate_2010_2021_km2_per_m"]["slope"] == pytest.approx(194.0, abs=0.1)
    assert summary["s2_rate_2017_2026_km2_per_m"]["slope"] == pytest.approx(232.3, abs=0.1)
    change = summary["change_2017_2021_km2"]
    assert change["jrc_notwater"] == pytest.approx(99.6, abs=0.1)
    assert change["s2_land"] == pytest.approx(110.8, abs=0.1)


def test_retreat():
    rt = table("table_retreat_by_zone.csv").set_index("zone")
    assert rt.loc[0, "p50"] == pytest.approx(208.4, abs=0.1)
    assert rt.loc[4, "p50"] == pytest.approx(751.7, abs=0.1)
    assert rt.loc[0, "max"] == pytest.approx(6777.3, abs=0.1)
    assert rt.loc[0, "count"] == 67403


def test_bare_and_protected(summary):
    bare = summary["bare_2026_km2"]
    assert bare["total"] == pytest.approx(71.48, abs=0.01)
    assert bare["share_of_exposed"] == pytest.approx(0.240, abs=0.001)
    assert bare["zones_1_3_share_of_bare"] == pytest.approx(0.805, abs=0.001)
    prot = summary["protected"]
    assert prot["any_share"] == pytest.approx(0.599, abs=0.001)
    assert prot["national_km2"] == pytest.approx(79.0, abs=0.1)


def test_population():
    pop = table("table_population_near_seabed.csv").set_index("distance_km")
    assert pop.loc[5, "pop_near_bare_exposed"] == 1367239
    assert pop.loc[1, "pop_near_bare_exposed"] == 122517


def test_depth_test_and_projection(summary):
    skill = summary["gebco_skill"]
    assert skill["overlap_share"] == pytest.approx(0.569, abs=0.001)
    assert skill["random_share"] == pytest.approx(0.044, abs=0.001)
    proj = table("table_projection.csv").set_index("further_fall_below_2026_m")
    assert proj.loc[5.0, "constant_rate_additional_km2"] == pytest.approx(1170.3, abs=0.1)
    assert proj.loc[5.0, "gebco_calibrated_additional_km2"] == pytest.approx(1898.6, abs=0.1)


def test_reference_vegetation(summary):
    old = summary["old_seabed_zones_1_3"]
    assert old["vegetated_pct_2019"] == pytest.approx(23.0, abs=0.1)
    assert old["vegetated_pct_2026"] == pytest.approx(33.7, abs=0.1)
    assert summary["old_land_vegetated_pct"]["1"]["2026"] == pytest.approx(89.2, abs=0.1)


def test_vegetation_classes():
    cls = table("table_class_by_zone.csv").set_index("zone")
    south_green = cls.loc[[4, 5], "green_at_emergence_km2"].sum()
    south_all = south_green + cls.loc[[4, 5], "bare_at_emergence_km2"].sum()
    assert south_green == pytest.approx(153.0, abs=0.1)
    assert south_all == pytest.approx(199.7, abs=0.1)


@pytest.mark.parametrize("name", [
    "fig01_exposed_area_by_zone_and_sea_level.png", "fig02_area_vs_sea_level.png",
    "fig03_ndvi_after_emergence.png", "fig04_threshold_sensitivity.png",
    "fig05_longterm_land_and_level.png", "fig06_retreat_by_zone.png",
    "fig07_bare_and_protected.png", "fig08_population_near_bare_seabed.png",
    "fig09_projection_range.png", "fig10_before_after_maps.png",
    "fig11_reference_vegetation.png",
])
def test_figure_exists(name):
    path = os.path.join(FIG, name)
    assert os.path.exists(path) and os.path.getsize(path) > 10_000
