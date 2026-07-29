#!/usr/bin/env python3
"""
fetch_ndvi_closeups.py

Downloads an actual (not spatially-averaged) per-pixel NDVI image for each
catchment, clipped to its exact boundary, as a small PNG thumbnail rendered
server-side by Earth Engine — so make_catchment_map_ndvi_closeups.py can
just imshow() each one, no raster/GIS library needed to read them.

Source: Sentinel-2 SR harmonized, 10 m, growing-season (JJA) cloud-masked
median composite, summers 2021-2023 (a 3-year window keeps enough cloud-free
scenes per catchment while staying a recent, "actual conditions" snapshot
rather than a long-term climatological mean).

Caches one PNG per catchment to ndvi_closeups/{catchment}.png, plus their
bounding boxes (needed to place each image correctly in the figure) to
ndvi_closeups/bounds.json.

Run with the 'gee' conda env:
    conda activate gee && python fetch_ndvi_closeups.py
"""

import json
from pathlib import Path

import ee
import requests
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

SCRIPT_DIR = Path(__file__).parent
GEOJSON_PATH = SCRIPT_DIR / "ten_catchment_corrected_watersheds.geojson"
OUT_DIR = SCRIPT_DIR / "ndvi_closeups"

EE_PROJECT = "gsapp-map"
START, END = "2021-06-01", "2023-09-01"
VIS_MIN, VIS_MAX = -1.0, 1.0
# User-specified NDVI color scale (non-uniform stops: black at -1, dark red
# through yellow across the 0-0.4 transition, into green from 0.5 up, with
# the darkest green from 0.9 to the top of the range). Built as a
# LinearSegmentedColormap from these exact (value, color) stops, then
# densely re-sampled into a flat hex list — used both as GEE's `palette`
# param (server-side rendering) and to rebuild an equivalent matplotlib
# colormap locally for the colorbar, so both match.
_NDVI_STOPS = [
    (-1.0, "#000000"),
    (-0.2, "#A50026"),
    (0.0,  "#D73027"),
    (0.1,  "#F46D43"),
    (0.2,  "#FDAE61"),
    (0.3,  "#FEE08B"),
    (0.4,  "#FFFFBF"),
    (0.5,  "#D9EF8B"),
    (0.6,  "#A6D96A"),
    (0.7,  "#66BD63"),
    (0.8,  "#1A9850"),
    (0.9,  "#006837"),
    (1.0,  "#006837"),  # extend the last defined color to the top of the range
]
_NDVI_CMAP_SRC = mcolors.LinearSegmentedColormap.from_list(
    "ndvi_custom", [((v + 1) / 2, c) for v, c in _NDVI_STOPS]
)
_N_PALETTE = 41  # dense enough that GEE's own linear interpolation between
                  # these samples reproduces the non-uniform stops above
NDVI_PALETTE = [
    mcolors.to_hex(_NDVI_CMAP_SRC(i / (_N_PALETTE - 1))).lstrip("#").upper()
    for i in range(_N_PALETTE)
]
THUMB_DIM = 600  # px, long side


def mask_s2_clouds(img):
    scl = img.select("SCL")
    # 3=cloud shadow, 8/9=cloud medium/high prob, 10=thin cirrus
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return img.updateMask(mask)


def main():
    ee.Initialize(project=EE_PROJECT)
    OUT_DIR.mkdir(exist_ok=True)

    with open(GEOJSON_PATH) as f:
        gj = json.load(f)

    bounds_out = {}
    for feat in gj["features"]:
        name = feat["properties"]["catchment"]
        geom = ee.Geometry(feat["geometry"])

        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geom)
            .filterDate(START, END)
            .filter(ee.Filter.calendarRange(6, 8, "month"))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        )
        n = s2.size().getInfo()

        ndvi = (
            s2.map(mask_s2_clouds)
            .map(lambda img: img.normalizedDifference(["B8", "B4"]).rename("NDVI"))
            .median()
            .clip(geom)
        )
        vis = ndvi.visualize(min=VIS_MIN, max=VIS_MAX, palette=NDVI_PALETTE)

        bbox_coords = geom.bounds().getInfo()["coordinates"][0]
        lons = [c[0] for c in bbox_coords]
        lats = [c[1] for c in bbox_coords]
        minx, maxx, miny, maxy = min(lons), max(lons), min(lats), max(lats)
        bbox_geom = ee.Geometry.Rectangle([minx, miny, maxx, maxy])

        url = vis.getThumbURL({"region": bbox_geom, "dimensions": THUMB_DIM, "format": "png"})
        r = requests.get(url, timeout=60)
        r.raise_for_status()

        out_path = OUT_DIR / f"{name}.png"
        out_path.write_bytes(r.content)
        bounds_out[name] = [minx, maxx, miny, maxy]
        print(f"  {name}: n_scenes={n}, saved {out_path.name} ({len(r.content)} bytes)")

    with open(OUT_DIR / "bounds.json", "w") as f:
        json.dump(bounds_out, f, indent=2)
    print(f"Saved bounds: {OUT_DIR / 'bounds.json'}")


if __name__ == "__main__":
    main()
