"""
plot_VODCA.py
-------------
Charts of VODCA CXKu-band VOD (Vegetation Optical Depth) statistics
over the Cannonsville watershed, 1987–2021.

Panels:
  1. Annual mean time series with ±1 std band
  2. Seasonal means time series (DJF / MAM / JJA / SON)
  3. Mean seasonal cycle (climatological day-of-year)
  4. Monthly climatology box plots


Annual mean time series — yearly mean VOD with ±1 std shading and a linear trend line
Seasonal means over time — one line per season (DJF/MAM/JJA/SON) coloured distinctly
Climatological seasonal cycle — 10-day bin means with ±1 std, overlaid with season background shading and month labels
Monthly climatology box plots — full distribution for each calendar month, boxes coloured by season


"""

import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH   = os.path.join(SCRIPT_DIR, "VODCA_CXKu_Cannonsville.csv")
OUT_PATH   = os.path.join(SCRIPT_DIR, "VODCA_charts.png")

# ---------------------------------------------------------------------------
# Load & prepare data
# ---------------------------------------------------------------------------
df = pd.read_csv(CSV_PATH, parse_dates=["date"])
df = df.dropna(subset=["VOD_mean"]).sort_values("date").reset_index(drop=True)

df["year"]  = df["date"].dt.year
df["month"] = df["date"].dt.month
df["doy"]   = df["date"].dt.dayofyear

SEASON_MAP = {12: "DJF", 1: "DJF", 2: "DJF",
               3: "MAM", 4: "MAM", 5: "MAM",
               6: "JJA", 7: "JJA", 8: "JJA",
               9: "SON", 10: "SON", 11: "SON"}
df["season"] = df["month"].map(SEASON_MAP)

# Assign a "season-year": DJF belongs to the year of January/February
def season_year(row):
    if row["season"] == "DJF" and row["month"] == 12:
        return row["year"] + 1
    return row["year"]

df["season_year"] = df.apply(season_year, axis=1)

# ---------------------------------------------------------------------------
# Derived aggregates
# ---------------------------------------------------------------------------
annual = (df.groupby("year")["VOD_mean"]
            .agg(mean="mean", std="std")
            .reset_index())

seasonal = (df.groupby(["season_year", "season"])["VOD_mean"]
              .mean()
              .reset_index()
              .rename(columns={"VOD_mean": "mean"}))

# Climatological seasonal cycle: 10-day bin averages
df["doy_bin"] = (df["doy"] - 1) // 10 * 10 + 5   # centre of 10-day bin
clim = (df.groupby("doy_bin")["VOD_mean"]
          .agg(mean="mean", std="std")
          .reset_index())

# Monthly climatology – all individual observations per month
monthly_groups = [df[df["month"] == m]["VOD_mean"].values for m in range(1, 13)]
MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
SEASON_COLORS = {"DJF": "#4575b4", "MAM": "#74c476",
                 "JJA": "#d73027", "SON": "#fd8d3c"}
SEASON_ORDER  = ["DJF", "MAM", "JJA", "SON"]
VOD_COLOR     = "#2c7bb6"
FILL_ALPHA    = 0.20

matplotlib.rcParams.update({
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# ---------------------------------------------------------------------------
# Build figure (2 × 2)
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
fig.suptitle("VODCA CXKu-band Vegetation Optical Depth — Cannonsville Watershed",
             fontsize=13, fontweight="bold", y=0.98)

# ── Panel 1: Annual mean ± std ──────────────────────────────────────────────
ax = axes[0, 0]
ax.fill_between(annual["year"],
                annual["mean"] - annual["std"],
                annual["mean"] + annual["std"],
                color=VOD_COLOR, alpha=FILL_ALPHA, label="±1 std")
ax.plot(annual["year"], annual["mean"], color=VOD_COLOR,
        linewidth=1.8, marker="o", markersize=3, label="Annual mean")
# Trend line
z = np.polyfit(annual["year"], annual["mean"], 1)
ax.plot(annual["year"], np.polyval(z, annual["year"]),
        color="black", linewidth=1, linestyle="--", label=f"Trend ({z[0]:+.4f}/yr)")
ax.set_title("Annual Mean VOD")
ax.set_xlabel("Year")
ax.set_ylabel("VOD")
ax.legend(fontsize=8)
ax.xaxis.set_major_locator(mticker.MultipleLocator(5))

# ── Panel 2: Seasonal means time series ────────────────────────────────────
ax = axes[0, 1]
for season in SEASON_ORDER:
    s = seasonal[seasonal["season"] == season].sort_values("season_year")
    ax.plot(s["season_year"], s["mean"],
            color=SEASON_COLORS[season], linewidth=1.4,
            marker="o", markersize=2.5, label=season)
ax.set_title("Seasonal Mean VOD Over Time")
ax.set_xlabel("Year")
ax.set_ylabel("VOD")
ax.legend(title="Season", fontsize=8)
ax.xaxis.set_major_locator(mticker.MultipleLocator(5))

# ── Panel 3: Climatological seasonal cycle (10-day bins) ───────────────────
ax = axes[1, 0]
ax.fill_between(clim["doy_bin"],
                clim["mean"] - clim["std"],
                clim["mean"] + clim["std"],
                color=VOD_COLOR, alpha=FILL_ALPHA)
ax.plot(clim["doy_bin"], clim["mean"],
        color=VOD_COLOR, linewidth=2)
# Season background shading
season_spans = [(1, 59, "DJF"), (60, 151, "MAM"), (152, 243, "JJA"),
                (244, 334, "SON"), (335, 365, "DJF")]
for start, end, s in season_spans:
    ax.axvspan(start, end, color=SEASON_COLORS[s], alpha=0.08)
# Month tick labels
month_starts = [1,32,60,91,121,152,182,213,244,274,305,335]
ax.set_xticks(month_starts)
ax.set_xticklabels(MONTH_LABELS, fontsize=8)
ax.set_title("Climatological Seasonal Cycle (1987–2021)")
ax.set_xlabel("Day of Year")
ax.set_ylabel("VOD")

# ── Panel 4: Monthly climatology box plots ─────────────────────────────────
ax = axes[1, 1]
bp = ax.boxplot(monthly_groups, patch_artist=True,
                medianprops=dict(color="black", linewidth=1.5),
                whiskerprops=dict(linewidth=0.8),
                flierprops=dict(marker=".", markersize=2, alpha=0.4))

season_for_month = [SEASON_MAP[m] for m in range(1, 13)]
for patch, s in zip(bp["boxes"], season_for_month):
    patch.set_facecolor(SEASON_COLORS[s])
    patch.set_alpha(0.7)

ax.set_xticks(range(1, 13))
ax.set_xticklabels(MONTH_LABELS, fontsize=8)
ax.set_title("Monthly VOD Distribution (all years)")
ax.set_xlabel("Month")
ax.set_ylabel("VOD")

# Season legend
legend_patches = [matplotlib.patches.Patch(facecolor=SEASON_COLORS[s],
                  alpha=0.7, label=s) for s in SEASON_ORDER]
ax.legend(handles=legend_patches, fontsize=8, title="Season")

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
print(f"Saved → {OUT_PATH}")
