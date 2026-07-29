#!/usr/bin/env python3
"""
make_catchment_map_ndvi_closeups.py

2x5 grid, one zoomed-in panel per catchment, showing its actual per-pixel
NDVI (not a spatial mean) — real Sentinel-2 imagery clipped to that
catchment's exact boundary, from fetch_ndvi_closeups.py's cached PNGs.
Panels are ordered to match the other catchment-map figures (same order as
ten_catchment_summary_corrected_boundaries.csv).

Each panel's axes are individually sized (not a uniform grid of equal
square cells) to match that catchment's own aspect ratio, so every map
fills as much of its grid cell as possible instead of being letterboxed
inside a fixed square. Panel letter + catchment name sit top-left of each
cell; a fixed 10 km scale bar is centered below each image (its horizontal
position follows that catchment's own footprint, since panels are different
sizes/shapes). One shared horizontal colorbar (-1 to 1) since every
thumbnail was rendered with the same NDVI palette/scale.

Run with the 'gee' conda env (no network access needed here — reads the
cached PNGs from fetch_ndvi_closeups.py):
    conda activate gee && python make_catchment_map_ndvi_closeups.py
"""

import json
from math import cos, radians

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as mticker
from matplotlib.transforms import blended_transform_factory

from make_catchment_map import SCRIPT_DIR, load_data
from fetch_ndvi_closeups import OUT_DIR, VIS_MIN, VIS_MAX, NDVI_PALETTE

OUT_PATH = SCRIPT_DIR / "catchments_ndvi_closeups.png"
NDVI_CMAP = mcolors.LinearSegmentedColormap.from_list("ndvi", [f"#{h}" for h in NDVI_PALETTE])

KM_PER_DEG_LAT = 111.32
SCALE_BAR_KM = 10

# Grid geometry, all in inches.
NROWS, NCOLS = 2, 5
COL_W_IN = 3.0           # each column's available width for the image itself
ROW_H_IN = 4.8           # each row's available height for the image itself (portrait cell)
TITLE_STRIP_IN = 0.30    # room above the image for the letter + catchment name
SCALEBAR_STRIP_IN = 0.30  # room below the image for the scale bar
COL_GAP_IN = 0.35
ROW_GAP_IN = 0.75        # extra breathing room between the two rows
LEFT_MARGIN_IN, RIGHT_MARGIN_IN = 0.1, 0.1
TOP_MARGIN_IN, BOTTOM_MARGIN_IN = 0.4, 0.9  # bottom leaves room for the colorbar


def add_scale_bar(ax, minx, maxx, mean_lat):
    """Fixed 10 km horizontal bar, centered under the image (so its position
    naturally follows that panel's own width/shape rather than a fixed
    corner). Blended transform: data-space x for an accurate length,
    axes-fraction y so it sits just below the image regardless of the
    image's own data range."""
    km_per_deg_lon = KM_PER_DEG_LAT * cos(radians(mean_lat))
    scale_deg = SCALE_BAR_KM / km_per_deg_lon
    x_center = (minx + maxx) / 2

    trans = blended_transform_factory(ax.transData, ax.transAxes)
    y_line, y_text = -0.06, -0.11
    ax.plot([x_center - scale_deg / 2, x_center + scale_deg / 2], [y_line, y_line],
             color="black", linewidth=1.8, solid_capstyle="butt",
             transform=trans, clip_on=False, zorder=10)
    ax.text(x_center, y_text, f"{SCALE_BAR_KM} km", ha="center", va="top",
             fontsize=7, transform=trans, clip_on=False, zorder=10)


def main():
    gdf = load_data()
    sites = gdf["site"].tolist()

    with open(OUT_DIR / "bounds.json") as f:
        bounds = json.load(f)

    fig_width_in = (
        LEFT_MARGIN_IN + NCOLS * COL_W_IN + (NCOLS - 1) * COL_GAP_IN + RIGHT_MARGIN_IN
    )
    fig_height_in = (
        TOP_MARGIN_IN
        + NROWS * (TITLE_STRIP_IN + ROW_H_IN + SCALEBAR_STRIP_IN)
        + (NROWS - 1) * ROW_GAP_IN
        + BOTTOM_MARGIN_IN
    )
    fig = plt.figure(figsize=(fig_width_in, fig_height_in))

    for i, site in enumerate(sites):
        row, col = divmod(i, NCOLS)
        img = plt.imread(OUT_DIR / f"{site}.png")
        minx, maxx, miny, maxy = bounds[site]
        mean_lat = (miny + maxy) / 2
        km_per_deg_lon = KM_PER_DEG_LAT * cos(radians(mean_lat))
        width_km = (maxx - minx) * km_per_deg_lon
        height_km = (maxy - miny) * KM_PER_DEG_LAT
        aspect = width_km / height_km

        # Largest (w, h) that fits in (COL_W_IN, ROW_H_IN) at this aspect.
        if aspect >= COL_W_IN / ROW_H_IN:
            w_in = COL_W_IN
            h_in = w_in / aspect
        else:
            h_in = ROW_H_IN
            w_in = h_in * aspect

        slot_x0_in = LEFT_MARGIN_IN + col * (COL_W_IN + COL_GAP_IN)
        slot_top_in = fig_height_in - TOP_MARGIN_IN - row * (
            TITLE_STRIP_IN + ROW_H_IN + SCALEBAR_STRIP_IN + ROW_GAP_IN
        ) - TITLE_STRIP_IN
        # Top- and left-aligned within the slot (not centered), so the
        # letter/name anchored at the slot's top-left stay flush against
        # the image regardless of how much smaller it is than the slot.
        ax_rect = [
            slot_x0_in / fig_width_in,
            (slot_top_in - h_in) / fig_height_in,
            w_in / fig_width_in,
            h_in / fig_height_in,
        ]
        ax = fig.add_axes(ax_rect)

        ax.imshow(img, extent=(minx, maxx, miny, maxy), origin="upper")
        ax.set_aspect(1.0 / cos(radians(mean_lat)))
        add_scale_bar(ax, minx, maxx, mean_lat)

        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Letter top-left of the grid square, catchment name directly to
        # its right (rather than a centered title above the image).
        ax.text(0.0, 1.06, chr(ord("a") + i), transform=ax.transAxes,
                 fontsize=11, fontweight="bold", va="bottom", ha="left")
        ax.text(0.10, 1.06, site, transform=ax.transAxes,
                 fontsize=9, va="bottom", ha="left")

    fig.suptitle("Actual NDVI per catchment (Sentinel-2, 10 m, JJA median composite, 2021-2023)",
                 fontsize=9, y=0.995)

    # Shared horizontal colorbar — every thumbnail used this same palette/scale.
    cax = fig.add_axes([0.25, 0.05, 0.5, 0.025])
    sm = plt.cm.ScalarMappable(norm=mcolors.Normalize(VIS_MIN, VIS_MAX), cmap=NDVI_CMAP)
    cbar = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cbar.set_label("NDVI", fontsize=8)
    cbar.ax.xaxis.set_major_locator(mticker.MultipleLocator(0.2))
    cbar.ax.tick_params(labelsize=8)

    fig.savefig(OUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_PATH.relative_to(SCRIPT_DIR.parents[1])}")


if __name__ == "__main__":
    main()
