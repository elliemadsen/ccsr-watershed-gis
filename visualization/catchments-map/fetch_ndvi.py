#!/usr/bin/env python3
"""
fetch_ndvi.py

Pulls growing-season (JJA) mean NDVI per catchment from MODIS MOD13Q1
(250 m, 16-day composite) via Google Earth Engine, averaged over 2001-2020
to match the growing-season convention used elsewhere in this project
(see visualization/catchments-map/variables.txt). Caches the result to
ndvi_by_catchment.csv so make_catchment_map_ndvi.py doesn't need network
access / an Earth Engine session on every plot rebuild.

Run with the 'gee' conda env (has the earthengine-api and existing
credentials under this project's Earth Engine account):
    conda activate gee && python fetch_ndvi.py
"""

import json
from pathlib import Path

import ee
import pandas as pd

SCRIPT_DIR = Path(__file__).parent
GEOJSON_PATH = SCRIPT_DIR / "ten_catchment_corrected_watersheds.geojson"
OUT_CSV = SCRIPT_DIR / "ndvi_by_catchment.csv"

EE_PROJECT = "gsapp-map"  # matches data/VOD/get_VODCA.py
START, END = "2001-01-01", "2021-01-01"  # 2001-2020 inclusive


def main():
    ee.Initialize(project=EE_PROJECT)

    with open(GEOJSON_PATH) as f:
        gj = json.load(f)

    modis_jja = (
        ee.ImageCollection("MODIS/061/MOD13Q1")
        .filterDate(START, END)
        .filter(ee.Filter.calendarRange(6, 8, "month"))
        .select("NDVI")
    )
    mean_img = modis_jja.mean().multiply(0.0001)  # MOD13Q1 NDVI scale factor

    rows = []
    for feat in gj["features"]:
        name = feat["properties"]["catchment"]
        geom = ee.Geometry(feat["geometry"])
        val = mean_img.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom, scale=250,
            maxPixels=1e9, bestEffort=True,
        ).getInfo()
        ndvi = val.get("NDVI")
        print(f"  {name}: NDVI={ndvi:.4f}")
        rows.append({"catchment": name, "ndvi": ndvi})

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print(f"Saved: {OUT_CSV}")


if __name__ == "__main__":
    main()
