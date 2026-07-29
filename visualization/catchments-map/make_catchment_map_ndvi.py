#!/usr/bin/env python3
"""
make_catchment_map_ndvi.py

Same panel (a) map as make_catchment_map.py (catchment boundaries, city
dots, connector lines), but each catchment is filled by its growing-season
mean NDVI instead of a flat color, with a vertical NDVI colorbar in place of
panel (b)'s bar chart.

NDVI values come from ndvi_by_catchment.csv (MODIS MOD13Q1, JJA mean,
2001-2020 — see fetch_ndvi.py, run once via Earth Engine to produce that
CSV). Run this script itself with the same 'gee' conda env as
make_catchment_map.py (no network access needed here — it just reads the
cached CSV):
    conda activate gee && python make_catchment_map_ndvi.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs

from make_catchment_map import (
    SCRIPT_DIR, load_data, get_map_extent, compute_map_aspect, _build_figure,
)

NDVI_CSV = SCRIPT_DIR / "ndvi_by_catchment.csv"
OUT_PATH = SCRIPT_DIR / "catchments_ndvi.png"

# Google Earth Engine's standard NDVI palette (tan/brown = sparse vegetation,
# through yellow, to dark green = dense vegetation) — used here so the map
# reads as "NDVI" to anyone who has seen it rendered in GEE itself.
NDVI_PALETTE = [
    "#FFFFFF", "#CE7E45", "#DF923D", "#F1B555", "#FCD163",
    "#99B718", "#74A901", "#66A000", "#529400", "#3E8601",
    "#207401", "#056201", "#004C00", "#023B01", "#012E01",
    "#011D01", "#011301",
]
NDVI_CMAP = mcolors.LinearSegmentedColormap.from_list("ndvi", NDVI_PALETTE)


def main():
    gdf = load_data()
    ndvi_df = pd.read_csv(NDVI_CSV)
    ndvi_by_site = dict(zip(ndvi_df["catchment"], ndvi_df["ndvi"]))

    # Min-max (with a little padding) rather than a fixed 0-1 scale: these
    # are all forested/vegetated watersheds so raw NDVI only spans ~0.80-0.88
    # here — a fixed scale would render them nearly indistinguishable.
    vals = gdf["site"].map(ndvi_by_site)
    vlo, vhi = vals.min(), vals.max()
    pad = (vhi - vlo) * 0.1
    norm = mcolors.Normalize(vmin=vlo - pad, vmax=vhi + pad)
    fill_colors = {site: NDVI_CMAP(norm(v)) for site, v in zip(gdf["site"], vals)}

    proj = ccrs.UTM(18)
    aspect = compute_map_aspect(proj, get_map_extent(gdf))

    fig, ax_a, b_rect = _build_figure(gdf, proj, aspect, b_width_in=0.55, fill_colors=fill_colors)

    # Narrow vertical colorbar in place of panel (b)'s bar chart.
    cax = fig.add_axes(b_rect)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=NDVI_CMAP)
    cbar = fig.colorbar(sm, cax=cax)
    cbar.set_label("NDVI (JJA mean, 2001–2020)", fontsize=8)
    cbar.ax.tick_params(labelsize=8)

    fig.savefig(OUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_PATH.relative_to(SCRIPT_DIR.parents[1])}")


if __name__ == "__main__":
    main()
