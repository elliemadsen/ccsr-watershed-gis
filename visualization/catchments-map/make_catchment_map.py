#!/usr/bin/env python3
"""
make_catchment_map.py

Two-panel figure for publication, produced as separate PNGs that share the
same panel (a)/(b) structure and differ in content:
  (a) The ten water-supply catchments (named boundaries), a line to the city
      each one feeds, and a named dot at the city. In catchments_ET_regression
      .png each catchment is filled by β_VPD (darker = higher), with a scale
      below the map; catchments_properties.png uses a flat fill.
  (b) catchments_ET_regression.png — grouped horizontal bars, one row per
      catchment, comparing 4 present-period CSD trend indicators (β_VPD,
      β_SM, β_Rg, β_LAI) in raw (unnormalized) units on a shared axis, since
      the metrics are already dimensionless regression coefficients.
      catchments_properties.png — small-multiple horizontal bar charts (one
      per metric: mean VPD, mean temperature, mean soil moisture), each in
      its own raw units/axis (not normalized, since the units don't share
      a scale).

Captions for both are in captions.txt; variable definitions/units are in
variables.txt.

Reads:
  ten_catchment_corrected_watersheds.geojson  (boundaries, outlet coords, supplies)
  ten_catchment_summary_corrected_boundaries.csv  (site list / order + metrics)

Requires geopandas, shapely, cartopy, adjustText — run with the 'gee' conda
env (adjustText installed there via pip; not bundled with the env by default):
    conda activate gee && python make_catchment_map.py

Natural Earth basemap layers (50m states/coastline/lakes) are fetched by
cartopy on first run and cached under ~/.local/share/cartopy/shapefiles/.
"""

import colorsys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import matplotlib.transforms as mtransforms
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from adjustText import adjust_text

SCRIPT_DIR = Path(__file__).parent
GEOJSON_PATH = SCRIPT_DIR / "ten_catchment_corrected_watersheds.geojson"
CSV_PATH = SCRIPT_DIR / "ten_catchment_summary_corrected_boundaries.csv"

# ---------------------------------------------------------------------------
# Style — Helvetica, 8 pt labels, 300 dpi (matches other figures in this repo)
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.family":     "sans-serif",
    "font.sans-serif": ["Helvetica", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size":       8,
    "axes.labelsize":  8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi":      300,
    "savefig.dpi":     300,
})

PANEL_LETTER_FONTSIZE = 11
LABEL_FONTSIZE = 8

# Land/ocean basemap colors — flat grey land per user request.
LAND_COLOR = "#d4d4d4"
OCEAN_COLOR = "#eef2f5"

# Watershed fill color — swapped with β_Rg's bar color (below) per request:
# the map is now the purple that β_Rg used to be, and β_Rg now takes the
# orange the map used to be.
WATERSHED_COLOR = plt.get_cmap("magma")(0.28)
BAR_COLOR_RANGE = (0.12, 0.60)

# catchments_ET_regression.png bar colors, explicit per metric (rather than
# bar_colors()'s even spread) so β_Rg can be swapped to the orange point
# that used to belong to the map, without disturbing β_VPD/β_SM/β_LAI.
PRESENT_METRIC_COLOR_POINTS = {
    "bvpd_present": 0.12,
    "bsm_present":  0.40,
    "brg_present":  0.60,
    "blai_present": 0.79,
}

# catchments_ET_regression.png's map fill: each catchment shaded by β_VPD,
# same hue as the β_VPD bar color (point 0.12 above), ramped from a pale
# near-white tint (low value) to a dark shade (high value) via HLS
# lightness — not swept across magma's hue range.
VPD_MAP_LIGHTNESS_RANGE = (0.14, 0.64)  # (dark, light)

# Panel (a) / panel (b) share this vertical extent so both read the same
# height in the saved figure.
PANEL_Y0 = 0.05
PANEL_HEIGHT = 0.90

# City center coordinates (lon, lat) — the point each catchment "feeds",
# distinct from the dam/outlet coordinates already in the geojson.
CITY_COORDS = {
    "New York City": (-74.0060, 40.7128),
    "Portland":   (-70.2568, 43.6591),
    "Boston":        (-71.0589, 42.3601),
    "Providence":    (-71.4128, 41.8240),
    "Hartford":      (-72.6734, 41.7658),
    "Manchester": (-71.4548, 42.9956),
    "Rochester":     (-77.6088, 43.1566),
    "Albany":        (-73.7562, 42.6526),
    "Utica":         (-75.2327, 43.1009),
}

# Hand-tuned label nudges applied on top of adjustText's automatic placement
# (in inches, +x = right, +y = up) — fine adjustments requested for specific
# labels that adjustText's collision-avoidance didn't quite get right.
MANUAL_LABEL_NUDGES = {
    "Hinckley NY":        (0.3,  0.00),
    "Cannonsville NY":    (0.0,  0.35),
    "Alcove NY":          (0.0,   0.26),
    "New York City":      (0.00,   0.04),
    "Barkhamsted CT":     (-0.01,  -0.05),
    "Quabbin MA":         (0.1,   0.2),
    "Wachusett MA":       (0.00,  -0.12),
    "Scituate RI":        (-0.18,   0.14),
    "Sebago ME":          (-0.26,  0.00),
    "Boston":             (0.00,  -0.045),
    "Manchester":         (-0.56,  -0.1),
    "Massabesic NH":      (0.5,   0.2),
    "Albany":         (0.0,  0.1),


}

# Display label for every metric that can appear in panel (b), keyed by CSV
# column name. Colors are assigned per-variant from MAGMA_SAMPLE_POINTS
# (see bar_colors()), not stored here.
METRIC_LABELS = {
    "meanVPD":      "Mean Vapor\nPressure Deficit (kPa)",
    "meanT":        "Mean\nTemperature (°C)",
    "meanSM":       "Mean Soil\nMoisture",
    "bvpd_present": "β_VPD",
    "bsm_present":  "β_SM",
    "brg_present":  "β_Rg",
    "blai_present": "β_LAI",
}

# Present-period indicators (dimensionless regression coefficients, already
# on comparable scales) — one grouped bar chart panel, raw units.
PRESENT_METRICS = ["bvpd_present", "bsm_present", "brg_present", "blai_present"]

# Physical/climate summary stats, kept in raw units — small-multiples panel.
PHYSICAL_METRICS = ["meanVPD", "meanT", "meanSM"]


def load_data():
    gdf = gpd.read_file(GEOJSON_PATH)
    df = pd.read_csv(CSV_PATH)
    # csv 'site' order drives plotting/color order; pull geometry from geojson
    merged = df.merge(
        gdf[["catchment", "geometry"]],
        left_on="site", right_on="catchment", how="left",
    )
    merged = gpd.GeoDataFrame(merged, geometry="geometry", crs="EPSG:4326")
    return merged


def bar_colors(n):
    """n evenly spread magma colors (never adjacent-and-similar, unlike a
    fixed point list where two picks could land close together)."""
    cmap = plt.get_cmap("magma")
    lo, hi = BAR_COLOR_RANGE
    return [cmap(t) for t in np.linspace(lo, hi, n)]


def present_bar_colors(metric_cols):
    cmap = plt.get_cmap("magma")
    return [cmap(PRESENT_METRIC_COLOR_POINTS[c]) for c in metric_cols]


def vpd_map_colormap_and_norm(gdf):
    """Colormap + norm mapping raw β_VPD -> the map fill: a single-hue ramp
    (same hue as the β_VPD bar color) from a pale, near-white tint at the
    low end to a dark shade at the high end — not a sweep across magma's
    hue range, which would drift toward magenta/orange. Shared by
    plot_panel_a's per-catchment fill and the scale bar drawn below it, so
    both agree on the same value->color mapping."""
    base_r, base_g, base_b, _ = plt.get_cmap("magma")(PRESENT_METRIC_COLOR_POINTS["bvpd_present"])
    hue, _, sat = colorsys.rgb_to_hls(base_r, base_g, base_b)
    lo_l, hi_l = VPD_MAP_LIGHTNESS_RANGE
    lightnesses = np.linspace(hi_l, lo_l, 256)  # low value -> light, high value -> dark
    cmap = mcolors.ListedColormap([colorsys.hls_to_rgb(hue, l, sat) for l in lightnesses])
    vals = gdf["bvpd_present"].astype(float)
    norm = mcolors.Normalize(vmin=vals.min(), vmax=vals.max())
    return cmap, norm


def vpd_fill_colors(gdf):
    cmap, norm = vpd_map_colormap_and_norm(gdf)
    return {
        row["site"]: cmap(norm(float(row["bvpd_present"])))
        for _, row in gdf.iterrows()
    }


def add_basemap_features(ax, scale="50m", states=True, lakes=True):
    ax.add_feature(cfeature.NaturalEarthFeature(
        "physical", "land", scale, facecolor=LAND_COLOR, edgecolor="none"), zorder=0)
    ax.add_feature(cfeature.NaturalEarthFeature(
        "physical", "ocean", scale, facecolor=OCEAN_COLOR, edgecolor="none"), zorder=0)
    if lakes:
        ax.add_feature(cfeature.NaturalEarthFeature(
            "physical", "lakes", scale, facecolor=OCEAN_COLOR, edgecolor="#9a9a9a",
            linewidth=0.4), zorder=1)
    if states:
        ax.add_feature(cfeature.NaturalEarthFeature(
            "cultural", "admin_1_states_provinces_lines", scale,
            facecolor="none", edgecolor="#888888", linewidth=0.4), zorder=2)
    ax.add_feature(cfeature.NaturalEarthFeature(
        "cultural", "admin_0_countries", scale,
        facecolor="none", edgecolor="#555555", linewidth=0.6), zorder=2)


def add_panel_letter(ax, letter):
    ax.text(
        -0.02, 1.02, letter, transform=ax.transAxes,
        fontsize=PANEL_LETTER_FONTSIZE, fontweight="bold",
        va="bottom", ha="left",
    )


def plot_panel_a(ax, gdf, fill_colors=None):
    """fill_colors: optional {site_name: color} override for the flat
    WATERSHED_COLOR, e.g. to color each catchment by a data value instead."""
    add_basemap_features(ax, scale="50m")
    # set_extent first — adjustText below needs the axes' final data limits
    # (and projected transform) to place labels correctly.
    ax.set_extent(get_map_extent(gdf), crs=ccrs.PlateCarree())
    proj = ax.projection

    texts, anchor_x, anchor_y = [], [], []

    for _, row in gdf.iterrows():
        name = row["site"]
        cx, cy = row.geometry.centroid.x, row.geometry.centroid.y
        city = row["supplies"]
        clon, clat = CITY_COORDS[city]

        # Connector line from watershed centroid to the city it feeds
        ax.plot(
            [cx, clon], [cy, clat], transform=ccrs.PlateCarree(),
            color="black", linewidth=0.6, linestyle=(0, (3, 2)),
            alpha=0.6, zorder=2,
        )
        color = fill_colors[name] if fill_colors is not None else WATERSHED_COLOR
        ax.add_geometries(
            [row.geometry], crs=ccrs.PlateCarree(),
            facecolor=color, edgecolor="black", linewidth=0.6, alpha=0.85,
            zorder=3,
        )

        # Text is placed in the axes' own projected coordinates (not
        # transform=PlateCarree) so adjustText's overlap-avoidance — which
        # moves text.set_position() in data/transData space — lines up with
        # what's actually on screen.
        px, py = proj.transform_point(cx, cy, ccrs.PlateCarree())
        texts.append(ax.text(
            px, py, name, fontsize=LABEL_FONTSIZE, ha="center", va="center",
            zorder=5, path_effects=_text_halo(),
        ))
        anchor_x.append(px)
        anchor_y.append(py)

    for city, (lon, lat) in CITY_COORDS.items():
        ax.scatter(
            [lon], [lat], transform=ccrs.PlateCarree(),
            s=22, facecolor="black", edgecolor="white", linewidth=0.5,
            zorder=6,
        )

        px, py = proj.transform_point(lon, lat, ccrs.PlateCarree())
        texts.append(ax.text(
            px, py, city, fontsize=LABEL_FONTSIZE, fontstyle="italic",
            ha="left", va="center", zorder=6, path_effects=_text_halo(),
        ))
        anchor_x.append(px)
        anchor_y.append(py)

    # Automatic label placement instead of hand-tuned per-name offsets: repels
    # the 19 labels from each other, and draws a thin leader line back to
    # each label's true anchor point when it gets moved. (Passing the city
    # dot scatter artists in as `objects` to also repel labels from the dots
    # themselves trips a cartopy/adjustText bbox bug — PathCollections using
    # a non-PlateCarree transform report a NaN window extent — so labels are
    # only repelled from each other, not the dots.)
    _, arrow_patches = adjust_text(
        texts, x=anchor_x, y=anchor_y, ax=ax,
        expand=(1.25, 1.4), force_text=(0.3, 0.5), force_static=(0.3, 0.4),
        arrowprops=dict(arrowstyle="-", color="#555555", lw=0.6, shrinkA=0, shrinkB=3),
    )
    arrow_by_text = {p.patchA: p for p in arrow_patches}

    # Hand-tuned fine adjustments on top of the automatic placement above,
    # applied as a fixed screen-space (inches) offset so they're independent
    # of the map's data scale/projection. Where adjustText drew a leader
    # line to this label, its tail (posA) is nudged by the equivalent
    # data-space delta so it still points at the moved label; its head
    # (posB) is left alone since that's the true catchment/city anchor.
    fig = ax.figure
    disp_origin = ax.transData.inverted().transform((0, 0))
    for t in texts:
        name = t.get_text()
        if name in MANUAL_LABEL_NUDGES:
            dx, dy = MANUAL_LABEL_NUDGES[name]
            t.set_transform(t.get_transform() + mtransforms.ScaledTranslation(dx, dy, fig.dpi_scale_trans))
            arrow = arrow_by_text.get(t)
            if arrow is not None:
                data_delta = ax.transData.inverted().transform(
                    np.array([dx, dy]) * fig.dpi
                ) - disp_origin
                posA, posB = arrow._posA_posB
                arrow.set_positions((posA[0] + data_delta[0], posA[1] + data_delta[1]), posB)

    add_panel_letter(ax, "a")


def get_map_extent(gdf):
    minx, miny, maxx, maxy = _combined_bounds(gdf)
    pad_x, pad_y = 0.60, 0.35
    return [minx - pad_x, maxx + pad_x, miny - pad_y, maxy + pad_y]


def compute_map_aspect(proj, extent):
    """width/height of the map extent once projected, so panel (a) can be
    given a starting box close to its natural aspect instead of relying on
    cartopy's equal-aspect letterboxing to fix a badly-guessed one."""
    tmp_fig = plt.figure()
    tmp_ax = tmp_fig.add_axes([0, 0, 1, 1], projection=proj)
    tmp_ax.set_extent(extent, crs=ccrs.PlateCarree())
    x0, x1 = tmp_ax.get_xlim()
    y0, y1 = tmp_ax.get_ylim()
    plt.close(tmp_fig)
    return (x1 - x0) / (y1 - y0)


def plot_panel_b_present(ax, gdf, metric_cols):
    """Grouped horizontal bar chart, raw (unnormalized) values, one row per
    catchment, all metrics sharing a single axis. A zero line is drawn since
    these are regression coefficients that can be negative (e.g. β_LAI)."""
    sites = gdf["site"].tolist()
    n_sites = len(sites)
    n_metrics = len(metric_cols)
    colors = present_bar_colors(metric_cols)

    vals = {col: gdf[col].astype(float) for col in metric_cols}
    all_vals = np.concatenate([v.values for v in vals.values()])
    vlo, vhi = all_vals.min(), all_vals.max()
    pad = (vhi - vlo) * 0.08

    group_height = 0.8
    bar_h = group_height / n_metrics
    y_base = np.arange(n_sites)[::-1]  # first site plotted at the top

    for m_i, col in enumerate(metric_cols):
        y = y_base - group_height / 2 + m_i * bar_h + bar_h / 2
        ax.barh(
            y, vals[col].values, height=bar_h * 0.95,
            color=colors[m_i], edgecolor="none", label=METRIC_LABELS[col],
            zorder=3,
        )

    ax.axvline(0, color="#888888", linewidth=0.6, zorder=2)
    ax.set_yticks(y_base)
    ax.set_yticklabels(sites, fontsize=LABEL_FONTSIZE)
    ax.set_xlim(vlo - pad, vhi + pad)
    ax.set_ylim(-0.6, n_sites - 1 + 0.6)
    ax.set_xlabel("ET Regression coefficient")
    ax.tick_params(axis="both", length=2)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.grid(axis="x", color="#dddddd", linewidth=0.5, zorder=0)

    ax.legend(
        loc="upper center", bbox_to_anchor=(0.5, -0.09),
        ncol=min(4, n_metrics), frameon=False, fontsize=LABEL_FONTSIZE,
        handlelength=1.0, handleheight=1.0, columnspacing=1.0,
    )
    add_panel_letter(ax, "b")


def plot_panel_b_physical(fig, rect, gdf, metric_cols):
    """Small-multiple horizontal bar charts, one per metric, each kept in its
    own raw units/axis (not normalized) since the metrics don't share units."""
    sites = gdf["site"].tolist()
    n_sites = len(sites)
    n_metrics = len(metric_cols)
    colors = bar_colors(n_metrics)

    x0, y0, w, h = rect
    wspace = 0.03
    sub_w = (w - wspace * (n_metrics - 1)) / n_metrics
    # Compress row pitch and thin the bars so rows sit closer together.
    row_pitch = 0.55
    bar_height = 0.32
    y_base = np.arange(n_sites)[::-1] * row_pitch

    first_ax = None
    for m_i, col in enumerate(metric_cols):
        ax = fig.add_axes(
            [x0 + m_i * (sub_w + wspace), y0, sub_w, h],
            sharey=first_ax,
        )
        if first_ax is None:
            first_ax = ax

        vals = gdf[col].astype(float).values
        ax.barh(y_base, vals, height=bar_height, color=colors[m_i], edgecolor="none", zorder=3)

        ax.set_ylim(y_base.min() - row_pitch / 2, y_base.max() + row_pitch / 2)
        # Don't default to a 0-origin axis — with these metrics' narrow
        # ranges (e.g. 16-18 degC) that hides the differences between
        # catchments the chart exists to show.
        vlo, vhi = vals.min(), vals.max()
        pad = (vhi - vlo) * 0.15 if vhi > vlo else 1.0
        ax.set_xlim(vlo - pad, vhi + pad)
        ax.set_xlabel(METRIC_LABELS[col])
        ax.tick_params(axis="both", length=2)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.grid(axis="x", color="#dddddd", linewidth=0.5, zorder=0)

        if m_i == 0:
            ax.set_yticks(y_base)
            ax.set_yticklabels(sites, fontsize=LABEL_FONTSIZE)
        else:
            ax.tick_params(axis="y", labelleft=False, length=2)

    add_panel_letter(first_ax, "b")


def _combined_bounds(gdf):
    minx, miny, maxx, maxy = gdf.total_bounds
    city_lons = [lon for lon, lat in CITY_COORDS.values()]
    city_lats = [lat for lon, lat in CITY_COORDS.values()]
    minx = min(minx, *city_lons)
    maxx = max(maxx, *city_lons)
    miny = min(miny, *city_lats)
    maxy = max(maxy, *city_lats)
    return minx, miny, maxx, maxy


def _text_halo():
    return [pe.withStroke(linewidth=2, foreground="white")]


def _build_figure(gdf, proj, aspect, b_width_in, fill_colors=None, a_legend_height_in=0.0):
    """Size the figure from panel (a)'s true projected aspect ratio (instead
    of guessing a width and letting cartopy's equal-aspect constraint
    letterbox it down), then place panel (a) and return (fig, ax_a, b_rect,
    a_legend_rect) with b_rect already matched to panel (a)'s real height.

    a_legend_height_in: when > 0, reserves a strip of that height below panel
    (a) (e.g. for a color scale bar) and returns its rect as a_legend_rect;
    otherwise a_legend_rect is None."""
    fig_height_in = 6.5
    top_margin_in, bottom_margin_in = 0.35, 0.30
    # gap_in has to clear both the visual gap and the y-tick label text
    # (e.g. "Hemlock-Canadice NY"), which is drawn to the *left* of panel
    # (b)'s plot spine and can otherwise run into panel (a)'s border.
    left_margin_in, gap_in, right_margin_in = 0.05, 1.3, 0.10
    legend_gap_in = 0.28 if a_legend_height_in > 0 else 0.0

    a_height_in = fig_height_in - top_margin_in - bottom_margin_in - a_legend_height_in - legend_gap_in
    a_width_in = a_height_in * aspect
    fig_width_in = left_margin_in + a_width_in + gap_in + b_width_in + right_margin_in

    fig = plt.figure(figsize=(fig_width_in, fig_height_in))
    a_bottom_in = bottom_margin_in + a_legend_height_in + legend_gap_in
    a_rect = [
        left_margin_in / fig_width_in, a_bottom_in / fig_height_in,
        a_width_in / fig_width_in, a_height_in / fig_height_in,
    ]
    ax_a = fig.add_axes(a_rect, projection=proj)
    plot_panel_a(ax_a, gdf, fill_colors=fill_colors)

    # Fine-tune: measure the actual rendered box (cartopy can still nudge it
    # slightly from the requested rect) and match panel (b) to that exactly.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox = ax_a.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())
    b_x0 = bbox.x0 + bbox.width + gap_in / fig_width_in
    b_rect = [b_x0, bbox.y0, (fig_width_in - right_margin_in) / fig_width_in - b_x0, bbox.height]

    a_legend_rect = None
    if a_legend_height_in > 0:
        a_legend_rect = [
            bbox.x0, bottom_margin_in / fig_height_in,
            bbox.width, a_legend_height_in / fig_height_in,
        ]
    return fig, ax_a, b_rect, a_legend_rect


def main():
    gdf = load_data()
    # UTM zone 18N / WGS84 (= EPSG:32618, same CRS used for this repo's 30 m
    # outputs). Using cartopy's native UTM class rather than ccrs.epsg(32618):
    # the latter enforces EPSG's registered area-of-use (-78 to -72 degrees
    # longitude), which clips Sebago/Portland ME at ~-70.5 degrees; UTM(18) is
    # the identical projection (same proj4 params) without that restriction.
    proj = ccrs.UTM(18)
    aspect = compute_map_aspect(proj, get_map_extent(gdf))

    # --- catchments_ET_regression.png ---
    vpd_cmap, vpd_norm = vpd_map_colormap_and_norm(gdf)
    fig, ax_a, b_rect, a_legend_rect = _build_figure(
        gdf, proj, aspect, b_width_in=3.4,
        fill_colors=vpd_fill_colors(gdf), a_legend_height_in=0.14,
    )
    ax_b = fig.add_axes(b_rect)
    plot_panel_b_present(ax_b, gdf, PRESENT_METRICS)
    ax_legend = fig.add_axes(a_legend_rect)
    fig.colorbar(
        plt.cm.ScalarMappable(norm=vpd_norm, cmap=vpd_cmap), cax=ax_legend,
        orientation="horizontal", label="β_VPD",
    )
    ax_legend.tick_params(labelsize=LABEL_FONTSIZE, length=2)
    ax_legend.xaxis.label.set_size(LABEL_FONTSIZE)
    out_path = SCRIPT_DIR / "catchments_ET_regression.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path.relative_to(SCRIPT_DIR.parents[1])}")

    # --- catchments_properties.png ---
    fig, ax_a, b_rect, _ = _build_figure(gdf, proj, aspect, b_width_in=5.4)
    plot_panel_b_physical(fig, b_rect, gdf, PHYSICAL_METRICS)
    out_path = SCRIPT_DIR / "catchments_properties.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path.relative_to(SCRIPT_DIR.parents[1])}")


if __name__ == "__main__":
    main()
