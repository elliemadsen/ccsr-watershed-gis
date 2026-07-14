#!/usr/bin/env python3
"""
resiliency_indicators.py

Compute Critical Slowing Down (CSD) indicators — lag-1 temporal autocorrelation
(TAC) and variance — for the Cannonsville Watershed using a 5-year sliding window
stepped annually. Follows Boulton et al. (2022).

Datasets:
  LAI_MODIS   — MODIS monthly rasters, 2006–2020
  LAI_GIMMS   — GIMMS LAI3g monthly rasters, 1982–2011
  LAI_spliced — GIMMS LAI3g (1982–2005) concatenated with MODIS (2006–2020), no bias correction
  VOD         — VODCA daily CSV, Cannonsville NY, 1987–2021 (resampled to monthly means)
  vod-all     — all VOD_SITES water-supply catchments (Cannonsville, Hinckley, Catskills,
                Sebago, Alcove, Scituate, Hemlock, Barkhamsted, Quabbin, Wachusett, Massabesic)
  Biomass_GCM  — L-Range total aboveground live biomass (talb), monthly rasters, 1990–2065
  LAI_1_GCM    — L-Range LAI, herbs layer, monthly rasters, 1990–2065
  LAI_2_GCM    — L-Range LAI, shrubs layer, monthly rasters, 1990–2065
  LAI_3_GCM    — L-Range LAI, trees layer, monthly rasters, 1990–2065
  LAI_GCM      — L-Range total canopy LAI (sum of herbs+shrubs+trees layers), 1990–2065

  The five *_GCM datasets are also available across a 5-GCM ensemble (--model):
  ACCESS, CMCC, CNRM, INM, IPSL (all SSP3-7.0). Default --model all runs every
  GCM and overlays all five lines on one plot per dataset/metric; pick a single
  model (e.g. --model INM) for a faster single-GCM run. Ignored for non-LR data.

Usage:
  python csd_analysis.py [--data {LAI_MODIS,LAI_GIMMS,LAI_spliced,VOD,vod-all,Biomass_GCM,LAI_1_GCM,LAI_2_GCM,LAI_3_GCM,LAI_GCM,all}] [--analysis {TAC,Var,all}]
                         [--model {ACCESS,CMCC,CNRM,INM,IPSL,all}]
                         [--detrend {stl,climatology}] [--window {5,10}] [--step {12,6}]
                         [--significance {surrogate,mk,both}]
                         [--changepoint {PELT[:K],minimax-p[:K],fisher-p[:K],YYYY-MM[,YYYY-MM...]}]
                         [--n-surrogates N]

Examples:
  python csd_analysis.py
  python csd_analysis.py --data LAI_spliced --step 6 --detrend stl
  python csd_analysis.py --data LAI_GCM --model INM         # single GCM, faster
  python csd_analysis.py --data Biomass_GCM                 # default: all 5 GCMs overlaid
  python csd_analysis.py --changepoint 2003-01              # manual split date
  python csd_analysis.py --changepoint PELT                 # ruptures PELT breakpoint detection
  python csd_analysis.py --changepoint PELT:3                # force 3 segments via Binseg
  python csd_analysis.py --changepoint minimax-p             # single split minimising worst p
  python csd_analysis.py --changepoint minimax-p:3           # 3-segment minimax-p partition
  python csd_analysis.py --changepoint fisher-p:3             # 3-segment split minimising
                                                                # the product of segment p-values
                                                                # (rewards 2 great + 1 bad over
                                                                # 3 mediocre, the opposite of
                                                                # minimax-p's preference)
"""

import argparse
import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import rasterio
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family":        "sans-serif",
    "font.sans-serif":    ["Helvetica", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size":          8,
    "axes.titlesize":     8,
    "axes.labelsize":     8,
    "xtick.labelsize":    8,
    "ytick.labelsize":    8,
    "legend.fontsize":    8,
    "figure.dpi":         300,
    "savefig.dpi":        300,
})

try:
    import pymannkendall as mk
    _HAS_MK = True
except ImportError:
    _HAS_MK = False
    print("Warning: pymannkendall not installed. Mann-Kendall tests will be skipped.")

try:
    import ruptures as rpt
    _HAS_RPT = True
except ImportError:
    _HAS_RPT = False
    print("Warning: ruptures not installed. Changepoint detection will be skipped.")

try:
    from statsmodels.tsa.seasonal import STL
    _HAS_STL = True
except ImportError:
    _HAS_STL = False
    print("Warning: statsmodels STL not available — '--detrend stl' (the default) will raise "
          "an error. Install statsmodels, or pass '--detrend climatology' explicitly.")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT     = Path(__file__).parents[3]
LAI_DIR       = REPO_ROOT / "data" / "L-Range" / "MODIS_baseline_obs" / "LAI"
GIMMS_LAI_DIR = REPO_ROOT / "data" / "LAI" / "raw_data" / "processed_monthly"
VOD_DIR   = REPO_ROOT / "data" / "VOD"
VOD_CSV   = VOD_DIR / "VODCA_CXKu_Cannonsville.csv"  # backward-compat alias

# All VOD water-supply catchments: dataset key → CSV path
VOD_SITES = {
    "VOD":            VOD_DIR / "VODCA_CXKu_Cannonsville.csv",   # Cannonsville, NY
    "Hinckley_NY":    VOD_DIR / "VODCA_CXKu_Hinckley_NY.csv",    # Hinckley Reservoir (Utica)
    "Catskills_NY":   VOD_DIR / "VODCA_CXKu_Catskills_NY.csv",   # Catskills (New York City)
    "Sebago_ME":      VOD_DIR / "VODCA_CXKu_Sebago_ME.csv",      # Sebago Lake (Portland)
    "Alcove_NY":      VOD_DIR / "VODCA_CXKu_Alcove_NY.csv",      # Alcove Reservoir (Albany)
    "Scituate_RI":    VOD_DIR / "VODCA_CXKu_Scituate_RI.csv",    # Scituate Reservoir (Providence)
    "Hemlock_NY":     VOD_DIR / "VODCA_CXKu_Hemlock_NY.csv",     # Hemlock Lake (Rochester)
    "Barkhamsted_CT": VOD_DIR / "VODCA_CXKu_Barkhamsted_CT.csv", # Barkhamsted Reservoir (Hartford)
    "Quabbin_MA":     VOD_DIR / "VODCA_CXKu_Quabbin_MA.csv",     # Quabbin Reservoir (Boston)
    "Wachusett_MA":   VOD_DIR / "VODCA_CXKu_Wachusett_MA.csv",   # Wachusett Reservoir (Boston)
    "Massabesic_NH":  VOD_DIR / "VODCA_CXKu_Massabesic_NH.csv",  # Lake Massabesic (Manchester)
}

# Human-readable display names for legend labels (keys not listed use the key itself)
VOD_SITE_LABELS: dict[str, str] = {
    "VOD": "Cannonsville",
}

# Site colors sampled from the magma colormap (evenly spaced, avoiding near-black and near-white ends)
_magma = plt.cm.magma
VOD_SITE_COLORS = {
    k: _magma(t) for k, t in zip(
        VOD_SITES.keys(),
        np.linspace(0.15, 0.88, len(VOD_SITES)),
    )
}
LRANGE_ALL_DIR = REPO_ROOT / "data" / "L-Range"
OUT_DIR   = Path(__file__).parent / "output"

# GCM ensemble for L-Range datasets (Biomass_GCM, LAI_1_GCM, LAI_2_GCM, LAI_3_GCM, LAI_GCM).
# All 5 models are run for the same SSP3-7.0 scenario, watershed domain, and variable set.
LRANGE_MODELS = {
    "ACCESS": "ACCESS_EMS1_5_SSP370",
    "CMCC":   "CMCC_EMS2_SSP370",
    "CNRM":   "CNRM_CM6_1_SSP370",
    "INM":    "INM_CM5_0_SSP370",
    "IPSL":   "IPSL_CM6A_LR_SSP370",
}

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WINDOW_MONTHS    = 60   # default: 5-year sliding window (overridable via --window)
STEP_MONTHS      = 12   # annual step
MIN_OBS_MONTHLY  = 10   # minimum valid daily obs to accept a VOD monthly mean

CLIM_PERIODS = {
    # VOD sites — full VODCA record for all
    "VOD":            (1987, 2021),
    "Hinckley_NY":    (1987, 2021),
    "Catskills_NY":   (1987, 2021),
    "Sebago_ME":      (1987, 2021),
    "Alcove_NY":      (1987, 2021),
    "Scituate_RI":    (1987, 2021),
    "Hemlock_NY":     (1987, 2021),
    "Barkhamsted_CT": (1987, 2021),
    "Quabbin_MA":     (1987, 2021),
    "Wachusett_MA":   (1987, 2021),
    "Massabesic_NH":  (1987, 2021),
    "LAI_MODIS":   (2006, 2020),  # full available MODIS record
    "LAI_GIMMS":   (1982, 2011),  # full available GIMMS LAI3g record
    "LAI_spliced": (1982, 2020),  # full GIMMS+MODIS spliced record
    "Biomass_GCM":  (1990, 2065),  # full L-Range model record
    "LAI_1_GCM":    (1990, 2065),  # full L-Range model record
    "LAI_2_GCM":    (1990, 2065),  # full L-Range model record
    "LAI_3_GCM":    (1990, 2065),  # full L-Range model record
    "LAI_GCM":      (1990, 2065),  # full L-Range model record
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_lai_modis() -> pd.Series:
    """
    Glob all lai__YYYY_MM.asc files, read each with rasterio, and return
    a monthly pd.Series of watershed-mean LAI values (MODIS, 2006–2020).
    Nodata pixels (value = -9999) are excluded from the mean via rasterio masking.
    """
    pattern = re.compile(r"lai__(\d{4})_(\d{2})\.asc$")
    records = []
    for f in sorted(LAI_DIR.glob("lai__*.asc")):
        m = pattern.match(f.name)
        if not m:
            continue
        year, month = int(m.group(1)), int(m.group(2))
        with rasterio.open(f) as src:
            data = src.read(1, masked=True)  # nodata -> masked
            value = float(data.mean()) if data.count() > 0 else np.nan
        records.append((pd.Timestamp(year=year, month=month, day=1), value))

    if not records:
        raise FileNotFoundError(f"No LAI .asc files found in {LAI_DIR}")

    dates, values = zip(*records)
    return pd.Series(values, index=pd.DatetimeIndex(dates), name="LAI_MODIS")


def load_lai_gimms() -> pd.Series:
    """
    Glob all gimms_lai3g_YYYY_MM.tif files, read each with rasterio, and return
    a monthly pd.Series of watershed-mean LAI values (GIMMS LAI3g, 1982–2011).
    Nodata pixels are excluded from the mean via rasterio masking.

    GIMMS LAI3g was derived from GIMMS NDVI3g using a neural network trained on
    MODIS LAI. See Zhu et al. (2013), Remote Sensing, 5(2), 927–948.
    doi:10.3390/rs5020927; and Pinzon & Tucker (2014), Remote Sensing, 6, 6929–6960.
    doi:10.3390/rs6076929 for the underlying NDVI3g dataset.
    """
    pattern = re.compile(r"gimms_lai3g_(\d{4})_(\d{2})\.tif$")
    records = []
    for f in sorted(GIMMS_LAI_DIR.glob("gimms_lai3g_*.tif")):
        m = pattern.match(f.name)
        if not m:
            continue
        year, month = int(m.group(1)), int(m.group(2))
        with rasterio.open(f) as src:
            data = src.read(1, masked=True)
            value = float(data.mean()) if data.count() > 0 else np.nan
        records.append((pd.Timestamp(year=year, month=month, day=1), value))

    if not records:
        raise FileNotFoundError(f"No GIMMS LAI3g .tif files found in {GIMMS_LAI_DIR}")

    dates, values = zip(*records)
    return pd.Series(values, index=pd.DatetimeIndex(dates), name="LAI_GIMMS")


def load_lai_spliced() -> pd.Series:
    """
    Splice GIMMS LAI3g (1982–2005) with MODIS LAI (2006–2020).
    MODIS is used for all months from 2006 onward; GIMMS fills 1982–2005.

    Current implementation: direct concatenation — no bias correction is applied.
    Absolute LAI values differ between sensors; any mean offset persists in the
    spliced series (though STL detrending absorbs much of it).

    More rigorous splicing approaches (potential future improvements):

    1. Additive mean-bias correction
       Compute offset = mean(MODIS_2006–2011) − mean(GIMMS_2006–2011) and add to
       all pre-2006 GIMMS values. Corrects the inter-sensor mean shift. The
       simplest possible correction; no specific citation needed — standard
       remote sensing pre-processing practice.

    2. Linear (OLS) regression rescaling
       Fit MODIS ~ a + b·GIMMS on the 2006–2011 overlap via OLS; apply to all
       pre-2006 GIMMS. Corrects both offset and gain differences. Can be fit
       per calendar month to also remove seasonal bias between sensors.
       Reference: Zhu et al. (2013), Remote Sensing, 5(2), 927–948.
       doi:10.3390/rs5020927

    3. Quantile mapping (CDF matching)
       Match the empirical distribution of GIMMS to MODIS over the overlap period
       and apply the transfer function to pre-2006 GIMMS. Corrects not just the
       mean but the full distribution, including variance differences.
       Reference: Gudmundsson et al. (2012), Hydrology and Earth System Sciences,
       16, 3383–3390. doi:10.5194/hess-16-3383-2012

    4. Structural break detection + BFAST correction
       Use BFAST to detect a structural discontinuity at the splice point in the
       combined series; its estimated magnitude is applied as an additive correction,
       separating the splice artefact from genuine trend and seasonal signals.
       Reference: Verbesselt et al. (2010), Remote Sensing of Environment, 114(1),
       106–115. doi:10.1016/j.rse.2009.08.014  (R package: bfast)

    5. Bayesian changepoint correction (BEAST)
       Fits a Bayesian ensemble model that simultaneously estimates trend, seasonal
       component, and abrupt change points; identifies and quantifies the splice
       discontinuity without needing to know its location a priori.
       Reference: Zhao et al. (2019), Remote Sensing of Environment, 232, 111181.
       doi:10.1016/j.rse.2019.04.034  (R package: Rbeast)
    """
    gimms = load_lai_gimms()
    modis = load_lai_modis()

    # Additive mean-bias correction: shift all GIMMS values so that the mean
    # over the 2006–2011 overlap period matches the MODIS mean for those months.
    overlap_years = (gimms.index.year >= 2006) & (gimms.index.year <= 2011)
    gimms_overlap = gimms[overlap_years]
    modis_overlap = modis[modis.index.year <= 2011]
    common_idx = gimms_overlap.index.intersection(modis_overlap.index)
    if len(common_idx) == 0:
        raise RuntimeError("No overlapping months found between GIMMS and MODIS for bias correction.")
    offset = modis_overlap.loc[common_idx].mean() - gimms_overlap.loc[common_idx].mean()
    gimms_corrected = gimms + offset

    gimms_pre = gimms_corrected[gimms_corrected.index.year < 2006]
    combined = pd.concat([gimms_pre, modis]).sort_index()
    combined.name = "LAI_spliced"
    return combined


def _load_vod_csv(csv_path: Path, name: str, min_obs: int = MIN_OBS_MONTHLY) -> pd.Series:
    """
    Read a VODCA daily CSV and resample to calendar-month means.
    A month requires at least `min_obs` valid daily observations; otherwise NaN.
    Result has a MonthStart DatetimeIndex.
    """
    df = pd.read_csv(csv_path, parse_dates=["date"], index_col="date")
    daily = df["VOD_mean"]

    def _monthly_mean(x: pd.Series) -> float:
        n_valid = x.notna().sum()
        return float(x.mean()) if n_valid >= min_obs else np.nan

    monthly = daily.resample("MS").agg(_monthly_mean)
    monthly.name = name
    return monthly


def load_vod(min_obs: int = MIN_OBS_MONTHLY) -> pd.Series:
    """Cannonsville, NY — VODCA CX+Ku, resampled to monthly means."""
    return _load_vod_csv(VOD_CSV, "VOD", min_obs)


# Loaders for all VOD_SITES entries, built dynamically from the path dict.
_VOD_SITE_LOADERS: dict[str, callable] = {
    name: (lambda p, n: (lambda min_obs=MIN_OBS_MONTHLY: _load_vod_csv(p, n, min_obs)))(path, name)
    for name, path in VOD_SITES.items()
}


def _lrange_spatial_mean(path: Path) -> float:
    """
    Watershed-mean of an L-Range .asc grid.

    The L-Range domain rectangle extends beyond the watershed boundary; cells
    outside the watershed are filled with 0.0 (not NODATA_value), matching the
    convention used by the model's own zone-summary outputs (`*_zones.txt`,
    see data/L-Range/summarize.py `read_zones_values`). Both NODATA_value
    (-9999) and the 0.0 padding are excluded from the mean.
    """
    with rasterio.open(path) as src:
        data = src.read(1, masked=True)
        data = np.ma.masked_equal(data, 0.0)
        return float(data.mean()) if data.count() > 0 else np.nan


def load_biomass_lr(lrange_dir: Path) -> pd.Series:
    """
    Glob all talb__1_M_YYYY_avg_cells.asc files (total aboveground live
    biomass, layer 1) under `lrange_dir`, and return a monthly pd.Series of
    watershed-mean values (L-Range, SSP3-7.0, 1990–2065).
    """
    pattern = re.compile(r"talb__1_(\d{1,2})_(\d{4})_avg_cells\.asc$")
    records = []
    for f in lrange_dir.glob("talb__1_*_*_avg_cells.asc"):
        m = pattern.match(f.name)
        if not m:
            continue
        month, year = int(m.group(1)), int(m.group(2))
        value = _lrange_spatial_mean(f)
        records.append((pd.Timestamp(year=year, month=month, day=1), value))

    if not records:
        raise FileNotFoundError(f"No L-Range talb .asc files found in {lrange_dir}")

    dates, values = zip(*records)
    series = pd.Series(values, index=pd.DatetimeIndex(dates), name="Biomass_GCM")
    return series.sort_index()


def _load_lai_lr_layer(layer: int, lrange_dir: Path) -> pd.Series:
    """
    Glob all lai___{layer}_M_YYYY_avg_cells.asc files under `lrange_dir` for a
    single L-Range PFT layer (1=herbs, 2=shrubs, 3=trees) and return a monthly
    pd.Series of watershed-mean values (L-Range, SSP3-7.0, 1990–2065).
    """
    pattern = re.compile(rf"lai___{layer}_(\d{{1,2}})_(\d{{4}})_avg_cells\.asc$")
    records = []
    for f in lrange_dir.glob(f"lai___{layer}_*_*_avg_cells.asc"):
        m = pattern.match(f.name)
        if not m:
            continue
        month, year = int(m.group(1)), int(m.group(2))
        value = _lrange_spatial_mean(f)
        records.append((pd.Timestamp(year=year, month=month, day=1), value))

    if not records:
        raise FileNotFoundError(f"No L-Range lai layer {layer} .asc files found in {lrange_dir}")

    dates, values = zip(*records)
    series = pd.Series(values, index=pd.DatetimeIndex(dates), name=f"LAI_{layer}_GCM")
    return series.sort_index()


def load_lai_1_lr(lrange_dir: Path) -> pd.Series:
    """L-Range LAI, herbs layer (layer 1)."""
    return _load_lai_lr_layer(1, lrange_dir)


def load_lai_2_lr(lrange_dir: Path) -> pd.Series:
    """L-Range LAI, shrubs layer (layer 2)."""
    return _load_lai_lr_layer(2, lrange_dir)


def load_lai_3_lr(lrange_dir: Path) -> pd.Series:
    """L-Range LAI, trees layer (layer 3)."""
    return _load_lai_lr_layer(3, lrange_dir)


def load_lai_lr(lrange_dir: Path) -> pd.Series:
    """
    Total canopy LAI: sum of the three L-Range PFT layers (herbs, shrubs,
    trees). A month is only summed if all three layers have a valid value.
    """
    layers = [_load_lai_lr_layer(i, lrange_dir) for i in (1, 2, 3)]
    combined = pd.concat(layers, axis=1)
    total = combined.sum(axis=1, min_count=3)
    total.name = "LAI_GCM"
    return total

# ---------------------------------------------------------------------------
# De-trending
# ---------------------------------------------------------------------------

def compute_stl_residuals(series: pd.Series) -> pd.Series:
    """
    Decompose the series using STL (Seasonal-Trend Decomposition by Loess)
    and return the residual component. Matches Boulton et al. (2022), who used
    R's stl() with period=12 and seasonal='periodic'.

    STL simultaneously removes the long-term trend and the repeating annual
    cycle, leaving only the residual. Unlike fixed climatology subtraction, STL
    adapts to a shifting seasonal cycle and a non-stationary trend.

    NaN values in the series are linearly interpolated before decomposition
    (STL requires a complete series); interpolated positions are re-masked
    as NaN in the returned residual.
    """
    if not _HAS_STL:
        raise ImportError("statsmodels is required for STL detrending.")

    nan_mask = series.isna()
    filled = series.interpolate(method="linear", limit_direction="both")

    stl = STL(filled, period=12, seasonal=13, robust=True)
    result = stl.fit()
    residual = pd.Series(result.resid, index=series.index, name=series.name + "_stl_resid")
    residual[nan_mask] = np.nan
    return residual


def compute_anomalies(series: pd.Series, clim_start: int, clim_end: int) -> pd.Series:
    """
    Subtract the long-term monthly climatology computed over [clim_start, clim_end].
    For each calendar month m, the climatological mean mu_m is subtracted:
        x'_t = x_t - mu_m   where m = month(t)
    Returns a pd.Series of anomalies with the same index as `series`.
    """
    clim_mask = (series.index.year >= clim_start) & (series.index.year <= clim_end)
    clim_series = series[clim_mask]
    clim = clim_series.groupby(clim_series.index.month).mean()  # index: 1..12

    anomalies = series.copy().astype(float)
    for month_num in range(1, 13):
        mask = series.index.month == month_num
        if month_num in clim.index and not np.isnan(clim[month_num]):
            anomalies[mask] = series[mask] - clim[month_num]
        else:
            anomalies[mask] = np.nan

    anomalies.name = series.name + "_anom"
    return anomalies


def detrend(series: pd.Series, method: str, clim_start: int, clim_end: int) -> pd.Series:
    """
    Dispatcher: apply the chosen detrending method and return residuals.

    Raises RuntimeError if 'stl' is requested but statsmodels is unavailable —
    deliberately does NOT silently fall back to climatology, since that's a
    different method (it doesn't remove the inter-annual trend, only the
    seasonal cycle) and output filenames/run_params would still say "stl"
    while actually having used climatology, silently corrupting the record
    of what was run.
    """
    if method == "stl":
        if not _HAS_STL:
            raise RuntimeError(
                "--detrend stl requires statsmodels, which is not installed in this "
                "environment. Install it (`pip install statsmodels` or `conda install "
                "statsmodels`) or pass --detrend climatology explicitly."
            )
        return compute_stl_residuals(series)
    return compute_anomalies(series, clim_start, clim_end)

# ---------------------------------------------------------------------------
# Resilience metrics
# ---------------------------------------------------------------------------

def compute_tac(vals: np.ndarray) -> float:
    """
    AR(1) OLS coefficient using all valid consecutive pairs (Boulton et al. 2022):

        phi_hat = sum( (x_t - xbar)(x_{t+1} - xbar) )
                  / sum( (x_t - xbar)^2 )

    xbar is the mean of all valid observations in the window.
    Only pairs where both x_t and x_{t+1} are non-NaN are used in the numerator;
    denominator uses all valid x_t that form the lagged pair.
    """
    xbar = np.nanmean(vals)
    x = vals - xbar
    x_t  = x[:-1]
    x_t1 = x[1:]
    valid = ~(np.isnan(x_t) | np.isnan(x_t1))
    x_t, x_t1 = x_t[valid], x_t1[valid]
    if len(x_t) < 2:
        return np.nan
    denom = np.sum(x_t ** 2)
    if denom == 0:
        return np.nan
    return float(np.sum(x_t * x_t1) / denom)


def compute_var(vals: np.ndarray) -> float:
    """
    Unbiased sample variance (ddof=1) over valid values in the window.

    `vals` is expected to already be normalized by the full-record residual
    std (see `main`), so this returns a dimensionless variance comparable
    across datasets with different native units/scales, rather than raw
    squared units (e.g. (g/m^2)^2 for Biomass_GCM vs (m^2/m^2)^2 for LAI).
    """
    valid = vals[~np.isnan(vals)]
    if len(valid) < 2:
        return np.nan
    return float(np.var(valid, ddof=1))

# ---------------------------------------------------------------------------
# Sliding window
# ---------------------------------------------------------------------------

def sliding_window(
    anomalies: pd.Series,
    analyses: list[str],
    window_months: int = WINDOW_MONTHS,
    step_months:   int = STEP_MONTHS,
    min_obs:       Optional[int] = None,
) -> pd.DataFrame:
    """
    Compute TAC and/or Var within a sliding window of `window_months` length.

    `min_obs` defaults to 50% of `window_months` when not given explicitly.

    Window labeling: the index is the centre-month timestamp
    (middle position = window_months // 2 - 1). When step_months=12 every
    label falls on a January; when step_months=6 labels alternate Jan/Jul,
    giving twice the temporal resolution at the cost of highly overlapping
    windows (59 of 60 months shared between adjacent windows).

    Returns a pd.DataFrame with a DatetimeIndex (centre month) and one
    column per metric.
    """
    if min_obs is None:
        min_obs = window_months // 2

    n = len(anomalies)
    records = []

    for start in range(0, n - window_months + 1, step_months):
        segment = anomalies.iloc[start : start + window_months]
        n_valid = int(segment.notna().sum())
        if n_valid < min_obs:
            continue

        centre_date = segment.index[window_months // 2 - 1]
        vals = segment.values.astype(float)

        row: dict = {"centre_date": centre_date}
        if "TAC" in analyses:
            row["TAC"] = compute_tac(vals)
        if "Var" in analyses:
            row["Var"] = compute_var(vals)
        records.append(row)

    return pd.DataFrame(records).set_index("centre_date")

# ---------------------------------------------------------------------------
# Trend significance: phase-surrogate Kendall tau test
# ---------------------------------------------------------------------------

def _kendall_tau(x: np.ndarray) -> float:
    """Kendall's tau for a 1-D array against its integer index."""
    n = len(x)
    if n < 4:
        return np.nan
    # Use scipy for speed
    from scipy.stats import kendalltau
    tau, _ = kendalltau(np.arange(n), x)
    return float(tau)


def phase_surrogate_test(
    series: pd.Series,
    n_surrogates: int = 1000,
    rng: Optional[np.random.Generator] = None,
) -> dict:
    """
    Test the statistical significance of Kendall's tau using phase-shuffled
    surrogates, following Boulton et al. (2022) and Smith et al. (2022).

    Procedure:
      1. Compute the observed Kendall tau of the (dropna) indicator series.
      2. Generate n_surrogates surrogate series by:
         a. Taking the FFT of the series.
         b. Randomly permuting the phases (preserving conjugate symmetry
            so the inverse FFT remains real-valued).
         c. Applying the inverse FFT.
        3. Compute Kendall tau for each surrogate.
        4. p-value = fraction of surrogates with |tau| >= |observed tau|
            (two-sided test for any monotonic trend, increasing or decreasing).

    Because phase shuffling preserves the power spectral density, and hence
    (by the Wiener-Khinchin theorem) the autocorrelation function, the null
    distribution correctly accounts for the serial correlation induced by
    overlapping sliding windows.

    Returns a dict with keys: tau, p, n, n_surrogates.
    """
    vals = series.dropna().values.astype(float)
    n = len(vals)
    if n < 4:
        return {"tau": np.nan, "p": np.nan, "n": n, "n_surrogates": n_surrogates}

    if rng is None:
        rng = np.random.default_rng()

    obs_tau = _kendall_tau(vals)

    # FFT-based phase shuffling
    fft = np.fft.rfft(vals)
    n_fft = len(fft)
    surrogate_taus = np.empty(n_surrogates)

    for i in range(n_surrogates):
        phases = rng.uniform(0, 2 * np.pi, n_fft)
        # preserve DC (index 0) and Nyquist (last if n even) phases
        phases[0] = 0.0
        if n % 2 == 0:
            phases[-1] = 0.0
        shuffled_fft = np.abs(fft) * np.exp(1j * phases)
        surrogate = np.fft.irfft(shuffled_fft, n=n)
        surrogate_taus[i] = _kendall_tau(surrogate)

    # Two-sided Monte Carlo p-value based on absolute Kendall tau.
    # The +1 continuity correction avoids exact 0.000 or 1.000 from finite sampling.
    n_extreme = int(np.sum(np.abs(surrogate_taus) >= abs(obs_tau)))
    p_value = float((n_extreme + 1) / (n_surrogates + 1))
    return {"tau": obs_tau, "p": p_value, "n": n, "n_surrogates": n_surrogates}


def _segment_bounds(cp_dates: list[pd.Timestamp]) -> list[tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]]:
    """Turn a sorted list of changepoints into (lo, hi) bounds for each segment, lo/hi=None at the ends."""
    edges = [None] + list(cp_dates) + [None]
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]


def _slice_segment(series: pd.Series, lo: Optional[pd.Timestamp], hi: Optional[pd.Timestamp]) -> pd.Series:
    seg = series
    if lo is not None:
        seg = seg[seg.index >= lo]
    if hi is not None:
        seg = seg[seg.index < hi]
    return seg


def _segment_label(lo: Optional[pd.Timestamp], hi: Optional[pd.Timestamp]) -> str:
    if lo is None:
        return f"before {hi.strftime('%Y-%m')}"
    if hi is None:
        return f"from {lo.strftime('%Y-%m')}"
    return f"{lo.strftime('%Y-%m')} – {hi.strftime('%Y-%m')}"


def surrogate_report(
    df: pd.DataFrame,
    dataset_name: str,
    n_surrogates: int,
    changepoints: Optional[dict[str, list[pd.Timestamp]]] = None,
) -> None:
    """Run phase-surrogate Kendall tau test and print results, with optional multi-segment splits."""
    for col in df.columns:
        print(f"  {dataset_name} {col} (phase-surrogate, n_surr={n_surrogates}):")
        series = df[col]

        def _report(s: pd.Series, label: str) -> None:
            res = phase_surrogate_test(s, n_surrogates=n_surrogates)
            if np.isnan(res["tau"]):
                print(f"    {label}: too few points (n={res['n']})")
                return
            sig = " *" if res["p"] < 0.05 else ""
            print(f"    {label} (n={res['n']}): tau={res['tau']:+.3f}, p={res['p']:.3f}{sig}")

        _report(series, "full record")

        if changepoints is not None:
            cp_dates = changepoints.get(col) or []
            if cp_dates:
                for lo, hi in _segment_bounds(cp_dates):
                    _report(_slice_segment(series, lo, hi), _segment_label(lo, hi))
        else:
            valid = series.dropna()
            if len(valid) >= 8:
                mid_date = valid.index[len(valid) // 2]
                _report(series[series.index < mid_date], f"first half (before {mid_date.strftime('%Y-%m')})")
                _report(series[series.index >= mid_date], f"second half (from   {mid_date.strftime('%Y-%m')})")


# ---------------------------------------------------------------------------
# Minimax-p changepoint search
# ---------------------------------------------------------------------------

def minimax_split_search(
    df: pd.DataFrame,
    dataset_name: str,
    n_segments: int = 2,
    min_segment_windows: int = 5,
) -> dict[str, list[pd.Timestamp]]:
    """
    Data-driven multi-changepoint search: partition the record into `n_segments`
    contiguous segments, choosing the (n_segments - 1) cut points that minimise
    the WORST (max) Kendall tau p-value across all segments.

    This is a middle ground between PELT (optimises a distributional cost on the
    raw indicator signal, agnostic of trend direction) and manual/visual inspection.
    Minimizing the max (rather than a sum-of-p objective) specifically targets
    partitions where EVERY segment is individually significant, rather than one
    highly-significant segment compensating for an insignificant one elsewhere.

    Solved via dynamic programming (classic "partition into k parts minimising
    the worst part" DP): first score every candidate segment [i, j) by its
    analytical Kendall tau p-value — O(n^2) — then find the optimal k-way
    partition — O(n_segments * n^2). For n_segments=2 this reduces to the
    original single-split grid search.

    **Significance measure used for the search:** scipy.stats.kendalltau analytical
    p-value (equivalent to standard Mann-Kendall, assumes independence). Phase-surrogate
    tests are far too expensive to run at every candidate partition. The analytical
    p-value is used only as a ranking criterion to find the split; the final reported
    significance in the output report uses whichever --significance method was
    requested (surrogate/mk). Because overlapping windows induce serial correlation,
    the analytical p-values used here are anti-conservative — the split location
    should be treated as a data-driven suggestion, not a formally tested result.

    **Multiple-comparisons caveat:** this scans every candidate partition (and more
    of them as `n_segments` grows), which inflates the chance of finding a
    significant-looking split by chance alone. Treat the result as a hypothesis to
    follow up with `--changepoint YYYY-MM` and a dedicated test, not as a
    formally-corrected significance result in itself.

    Only segments with at least `min_segment_windows` windows are considered. If
    no valid `n_segments`-way partition exists, an empty list is returned for
    that column.

    Returns a dict mapping column name -> list of (n_segments - 1) changepoint
    Timestamps (empty list if no valid partition was found).
    """
    from scipy.stats import kendalltau as _ktu

    changepoints: dict[str, list[pd.Timestamp]] = {}

    for col in df.columns:
        series = df[col].dropna()
        n = len(series)
        if n < n_segments * min_segment_windows:
            print(
                f"  {dataset_name} {col}: too few windows for a {n_segments}-segment "
                f"minimax-p search (n={n}, need >= {n_segments * min_segment_windows})"
            )
            changepoints[col] = []
            continue

        values = series.values.astype(float)

        # cost[i, j] = analytical Kendall tau p-value of the candidate segment [i, j)
        cost = np.full((n + 1, n + 1), np.inf)
        for i in range(n):
            for j in range(i + min_segment_windows, n + 1):
                _, p = _ktu(np.arange(j - i), values[i:j])
                cost[i, j] = p if not np.isnan(p) else np.inf

        # dp[k, j] = best (min-max) cost of partitioning [0, j) into k segments
        dp   = np.full((n_segments + 1, n + 1), np.inf)
        back = np.full((n_segments + 1, n + 1), -1, dtype=int)
        dp[0, 0] = -np.inf  # sentinel: zero segments, zero cost so far

        for kk in range(1, n_segments + 1):
            prev_row = dp[kk - 1]
            for j in range(1, n + 1):
                best_score, best_i = np.inf, -1
                for i in range(0, j - min_segment_windows + 1):
                    prev = prev_row[i]
                    c = cost[i, j]
                    if prev == np.inf or c == np.inf:
                        continue
                    score = c if prev == -np.inf else max(prev, c)
                    if score < best_score:
                        best_score, best_i = score, i
                dp[kk, j], back[kk, j] = best_score, best_i

        if dp[n_segments, n] == np.inf:
            print(f"  {dataset_name} {col}: no valid {n_segments}-segment partition found")
            changepoints[col] = []
            continue

        # Backtrack to recover the (n_segments - 1) interior boundaries
        boundaries = []
        j = n
        for kk in range(n_segments, 0, -1):
            i = back[kk, j]
            if kk > 1:
                boundaries.append(i)
            j = i
        boundaries.sort()

        cp_dates = [series.index[b] for b in boundaries]
        changepoints[col] = cp_dates

        bounds_full = [0] + boundaries + [n]
        seg_ps = [cost[bounds_full[s], bounds_full[s + 1]] for s in range(n_segments)]
        date_str = ", ".join(d.strftime("%Y-%m") for d in cp_dates) if cp_dates else "—"
        seg_str = ", ".join(f"p={p:.3f}" for p in seg_ps)
        print(
            f"  {dataset_name} {col}: minimax-p {n_segments}-segment split at [{date_str}] "
            f"({seg_str}, max={max(seg_ps):.3f})"
        )

    return changepoints


# ---------------------------------------------------------------------------
# Fisher-p changepoint search
# ---------------------------------------------------------------------------

def fisher_split_search(
    df: pd.DataFrame,
    dataset_name: str,
    n_segments: int = 2,
    min_segment_windows: int = 5,
) -> dict[str, list[pd.Timestamp]]:
    """
    Data-driven multi-changepoint search: partition the record into `n_segments`
    contiguous segments, choosing the (n_segments - 1) cut points that minimise
    the COMBINED significance via Fisher's method for combining independent
    p-values: minimise the PRODUCT of the segment p-values (equivalently,
    maximise Fisher's statistic -2 * sum(log(p_i))).

    This is the opposite trade-off from minimax_split_search: minimax-p
    optimises for the worst segment, so it prefers several mediocre segments
    over a mix of very-significant and very-insignificant ones. Fisher's
    method rewards a partition with even one or two extremely significant
    segments, since a product is dominated by its smallest factors —
    p=[0.01, 0.01, 0.9] (product ~9e-5) beats p=[0.2, 0.2, 0.2] (product
    8e-3) here, the reverse of minimax-p's ranking.

    Solved via the same dynamic-programming structure as minimax_split_search
    (score every candidate segment, then find the optimal k-way partition),
    just maximising a sum (of -log(p)) instead of minimising a max.

    **Significance measure, anti-conservativeness, and multiple-comparisons
    caveats are identical to minimax_split_search** — see that docstring.
    The search is purely a ranking criterion over candidate partitions, not a
    formally tested result; analytical Kendall tau p-values are anti-
    conservative under the overlapping-window serial correlation here, and
    scanning more candidate partitions (larger n_segments) inflates the
    chance of finding a significant-looking combination by chance alone.

    Returns a dict mapping column name -> list of (n_segments - 1) changepoint
    Timestamps (empty list if no valid partition was found).
    """
    from scipy.stats import kendalltau as _ktu

    eps = 1e-12
    changepoints: dict[str, list[pd.Timestamp]] = {}

    for col in df.columns:
        series = df[col].dropna()
        n = len(series)
        if n < n_segments * min_segment_windows:
            print(
                f"  {dataset_name} {col}: too few windows for a {n_segments}-segment "
                f"fisher-p search (n={n}, need >= {n_segments * min_segment_windows})"
            )
            changepoints[col] = []
            continue

        values = series.values.astype(float)

        # p_matrix[i, j] = analytical Kendall tau p-value of segment [i, j)
        # score[i, j] = -log(p), Fisher's per-segment contribution (higher = more significant)
        p_matrix = np.full((n + 1, n + 1), np.nan)
        score = np.full((n + 1, n + 1), -np.inf)
        for i in range(n):
            for j in range(i + min_segment_windows, n + 1):
                _, p = _ktu(np.arange(j - i), values[i:j])
                if np.isnan(p):
                    continue
                p_matrix[i, j] = p
                score[i, j] = -np.log(max(p, eps))

        # dp[k, j] = best (max) cumulative Fisher score partitioning [0, j) into k segments
        dp   = np.full((n_segments + 1, n + 1), -np.inf)
        back = np.full((n_segments + 1, n + 1), -1, dtype=int)
        dp[0, 0] = 0.0

        for kk in range(1, n_segments + 1):
            prev_row = dp[kk - 1]
            for j in range(1, n + 1):
                best_score, best_i = -np.inf, -1
                for i in range(0, j - min_segment_windows + 1):
                    prev = prev_row[i]
                    s = score[i, j]
                    if prev == -np.inf or s == -np.inf:
                        continue
                    total = prev + s
                    if total > best_score:
                        best_score, best_i = total, i
                dp[kk, j], back[kk, j] = best_score, best_i

        if dp[n_segments, n] == -np.inf:
            print(f"  {dataset_name} {col}: no valid {n_segments}-segment partition found")
            changepoints[col] = []
            continue

        # Backtrack to recover the (n_segments - 1) interior boundaries
        boundaries = []
        j = n
        for kk in range(n_segments, 0, -1):
            i = back[kk, j]
            if kk > 1:
                boundaries.append(i)
            j = i
        boundaries.sort()

        cp_dates = [series.index[b] for b in boundaries]
        changepoints[col] = cp_dates

        bounds_full = [0] + boundaries + [n]
        seg_ps = [p_matrix[bounds_full[s], bounds_full[s + 1]] for s in range(n_segments)]
        product_p = float(np.prod(seg_ps))
        date_str = ", ".join(d.strftime("%Y-%m") for d in cp_dates) if cp_dates else "—"
        seg_str = ", ".join(f"p={p:.3f}" for p in seg_ps)
        print(
            f"  {dataset_name} {col}: fisher-p {n_segments}-segment split at [{date_str}] "
            f"({seg_str}, product={product_p:.2e})"
        )

    return changepoints


# ---------------------------------------------------------------------------
# Changepoint detection
# ---------------------------------------------------------------------------

def detect_changepoints(df: pd.DataFrame, dataset_name: str) -> dict[str, list[pd.Timestamp]]:
    """
    Use ruptures PELT with an RBF cost function to find changepoints in each
    indicator column. PELT jointly chooses both the number and location of
    breakpoints via a penalised cost (pen=log(n), the BIC-equivalent penalty
    for Gaussian signals) — it may return zero, one, or several breaks
    depending on the indicator. A minimum segment length of max(5, n // 5)
    windows is enforced to avoid boundary artefacts.

    Use `detect_changepoints_binseg` instead if you need to force an exact
    number of breakpoints — PELT's penalty does not reliably return more
    than one break in practice.

    Returns a dict mapping column name -> list of changepoint Timestamps
    (possibly empty).
    """
    changepoints: dict[str, list[pd.Timestamp]] = {}
    if not _HAS_RPT:
        print("  [changepoint detection skipped — ruptures not installed]")
        return changepoints

    for col in df.columns:
        series = df[col].dropna()
        n = len(series)
        if n < 10:
            print(f"  {dataset_name} {col}: too few windows for changepoint detection (n={n})")
            changepoints[col] = []
            continue

        signal = series.values.reshape(-1, 1)
        min_size = max(5, n // 5)  # at least 5 windows per segment
        algo = rpt.Pelt(model="rbf", min_size=min_size).fit(signal)
        # pen=np.log(n) is the BIC penalty for Gaussian signals
        result = algo.predict(pen=np.log(n))
        # result is a list of breakpoint indices (last entry = n, not a real break)
        internal_breaks = [i for i in result if i < n]
        if not internal_breaks:
            print(f"  {dataset_name} {col}: no changepoint found")
            changepoints[col] = []
        else:
            cp_dates = [series.index[i] for i in internal_breaks]
            changepoints[col] = cp_dates
            date_str = ", ".join(d.strftime("%Y-%m") for d in cp_dates)
            print(f"  {dataset_name} {col}: {len(cp_dates)} changepoint(s) at [{date_str}]")

    return changepoints


def detect_changepoints_binseg(
    df: pd.DataFrame,
    dataset_name: str,
    n_segments: int,
) -> dict[str, list[pd.Timestamp]]:
    """
    Use ruptures Binary Segmentation (RBF cost) to force exactly
    `n_segments - 1` changepoints in each indicator column. Unlike PELT,
    Binseg requires the number of breaks to be specified up front; use this
    when PELT's penalty-driven search (--changepoint PELT) doesn't return as
    many breaks as you want (e.g. `--changepoint PELT:3` for a forced
    2-changepoint, 3-segment partition).

    Returns a dict mapping column name -> list of (n_segments - 1) changepoint
    Timestamps (empty list if there are too few windows for the request).
    """
    changepoints: dict[str, list[pd.Timestamp]] = {}
    if not _HAS_RPT:
        print("  [changepoint detection skipped — ruptures not installed]")
        return changepoints

    n_bkps = n_segments - 1
    for col in df.columns:
        series = df[col].dropna()
        n = len(series)
        min_size = max(5, n // 5)
        if n < n_segments * min_size:
            print(
                f"  {dataset_name} {col}: too few windows for a {n_segments}-segment "
                f"Binseg search (n={n}, need >= {n_segments * min_size})"
            )
            changepoints[col] = []
            continue

        signal = series.values.reshape(-1, 1)
        algo = rpt.Binseg(model="rbf", min_size=min_size).fit(signal)
        result = algo.predict(n_bkps=n_bkps)
        internal_breaks = [i for i in result if i < n]
        cp_dates = [series.index[i] for i in internal_breaks]
        changepoints[col] = cp_dates
        date_str = ", ".join(d.strftime("%Y-%m") for d in cp_dates) if cp_dates else "—"
        print(f"  {dataset_name} {col}: Binseg {n_segments}-segment split at [{date_str}]")

    return changepoints


# ---------------------------------------------------------------------------
# Mann-Kendall trend test
# ---------------------------------------------------------------------------

def _mk_line(series: pd.Series, label: str) -> None:
    """Run MK on a series and print a single formatted result line."""
    series = series.dropna()
    n = len(series)
    if n < 4:
        print(f"    {label}: too few points (n={n})")
        return
    result = mk.original_test(series)
    sig = " *" if result.p < 0.05 else ""
    print(
        f"    {label} (n={n}): "
        f"tau={result.Tau:+.3f}, p={result.p:.3f}{sig}, "
        f"trend={result.trend}, slope={result.slope:.4f}"
    )


def mannkendall_report(
    df: pd.DataFrame,
    dataset_name: str,
    changepoints: Optional[dict[str, list[pd.Timestamp]]] = None,
) -> None:
    """
    Apply original Mann-Kendall test to each indicator.
    If changepoints are provided for a column, also run MK separately on each
    segment bounded by those changepoints (N changepoints -> N+1 segments).
    """
    if not _HAS_MK:
        print("  [skipped — pymannkendall not installed]")
        return
    for col in df.columns:
        print(f"  {dataset_name} {col}:")
        series = df[col]
        _mk_line(series, "full record")

        if changepoints is not None:
            cp_dates = changepoints.get(col) or []
            if cp_dates:
                for lo, hi in _segment_bounds(cp_dates):
                    _mk_line(_slice_segment(series, lo, hi), _segment_label(lo, hi))
        else:
            # No changepoint: split at the temporal midpoint of the series
            valid = series.dropna()
            if len(valid) >= 8:
                mid_date = valid.index[len(valid) // 2]
                before = series[series.index < mid_date]
                after  = series[series.index >= mid_date]
                _mk_line(before, f"first half (before {mid_date.strftime('%Y-%m')})")
                _mk_line(after,  f"second half (from   {mid_date.strftime('%Y-%m')})")

# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _run_mk_silent(series: pd.Series) -> dict:
    """Run Mann-Kendall and return result dict; returns NaN fields if not enough data."""
    series = series.dropna()
    n = len(series)
    if n < 4 or not _HAS_MK:
        return {"tau": np.nan, "p": np.nan, "n": n, "trend": "—"}
    r = mk.original_test(series)
    return {"tau": r.Tau, "p": r.p, "n": n, "trend": r.trend}


def _run_surrogate_silent(series: pd.Series, n_surrogates: int) -> dict:
    """Run phase-surrogate test and return result dict."""
    r = phase_surrogate_test(series, n_surrogates=n_surrogates)
    return r


def _surrogate_period_rows(
    series: pd.Series,
    cp_dates: Optional[list[pd.Timestamp]],
    n_surrogates: int,
) -> list[tuple[str, int, float, float, str]]:
    """Return surrogate-test rows for the full record plus each changepoint-bounded segment."""
    def _row(label: str, s: pd.Series) -> tuple[str, int, float, float, str]:
        r = _run_surrogate_silent(s, n_surrogates)
        if np.isnan(r["tau"]):
            return (label, int(r["n"]), np.nan, np.nan, "—")
        if r["p"] < 0.05:
            trend = "increasing" if r["tau"] > 0 else "decreasing"
        else:
            trend = "no trend"
        return (label, int(r["n"]), float(r["tau"]), float(r["p"]), trend)

    rows = [_row("Full record", series)]
    if cp_dates:
        for lo, hi in _segment_bounds(cp_dates):
            label = _segment_label(lo, hi).strip().capitalize()
            rows.append(_row(label, _slice_segment(series, lo, hi)))
    elif cp_dates is None:
        valid = series.dropna()
        if len(valid) >= 8:
            mid_date = valid.index[len(valid) // 2]
            rows.append(_row(f"First half (before {mid_date.strftime('%Y-%m')})", series[series.index < mid_date]))
            rows.append(_row(f"Second half (from {mid_date.strftime('%Y-%m')})", series[series.index >= mid_date]))
    return rows


def generate_report(
    report_path: Path,
    run_params: dict,
    all_results: dict[str, dict[str, pd.DataFrame]],
    all_changepoints: dict[str, dict[str, dict[str, list[pd.Timestamp]]]],
    n_surrogates: int,
    sig_method: str,
) -> None:
    """
    Write a Markdown report alongside the output PNG summarising run parameters
    and surrogate trend significance results (tau, p) per dataset × model × metric × period.

    `all_results[dataset]` is a dict of label -> DataFrame; for non-ensemble
    datasets (no GCM dimension) there is a single label. For L-Range datasets
    run with --model all, each of the 5 GCM labels gets its own subsection.
    """
    lines: list[str] = []
    lines.append("# CSD Analysis Report")
    lines.append("")
    lines.append("## Run parameters")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("| --- | --- |")
    for k, v in run_params.items():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    for dataset, label_dfs in all_results.items():
        lines.append(f"## {dataset}")
        lines.append("")
        cps_by_label = all_changepoints.get(dataset, {})
        multi = len(label_dfs) > 1

        for label, df in label_dfs.items():
            if multi:
                lines.append(f"### Model: {label}")
                lines.append("")
            cps = cps_by_label.get(label, {})

            for col in df.columns:
                heading = "####" if multi else "###"
                lines.append(f"{heading} {col}")
                lines.append("")
                series = df[col]
                cp_dates = cps.get(col)

                lines.append("| Period | n | Test | tau | p | Trend |")
                lines.append("| --- | --- | --- | --- | --- | --- |")
                for row_label, n, tau, p, trend in _surrogate_period_rows(series, cp_dates, n_surrogates):
                    sig = " *" if (not np.isnan(p) and p < 0.05) else ""
                    if np.isnan(tau):
                        lines.append(f"| {row_label} | {n} | Surrogate | — | — | — |")
                    else:
                        lines.append(f"| {row_label} | {n} | Surrogate | {tau:+.3f} | {p:.3f}{sig} | {trend} |")

                lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Saved report: {report_path.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_results(
    results: dict[str, dict[str, pd.DataFrame]],
    analyses: list[str],
    out_path: Path,
    all_changepoints: Optional[dict[str, dict[str, dict[str, list[pd.Timestamp]]]]] = None,
    n_surrogates: int = 1000,
    show_summary: bool = True,
) -> None:
    """
    Grid of one column per dataset x one row per metric. `results[dataset]` is
    a dict of label -> DataFrame; a single-label dataset plots one line as
    before, while a multi-label (multi-GCM ensemble) dataset overlays all
    labels' lines on the same panel, color-coded by model, with a legend.
    Detected changepoints are drawn as vertical dashed lines (model-colored
    when overlaid, crimson with a date legend for single-series panels).

    `show_summary` controls the right-hand trend/significance text panel —
    pass False to omit it entirely (e.g. when no --changepoint was requested,
    or for a "just the images" plot) rather than reserving blank space for it.
    """
    datasets = list(results.keys())
    n_rows = len(analyses)
    n_cols = len(datasets)

    if show_summary:
        fig = plt.figure(figsize=(6 * n_cols + 4.5, 4 * n_rows))
        gs = fig.add_gridspec(n_rows, n_cols + 1, width_ratios=[1] * n_cols + [0.95])
        summary_ax = fig.add_subplot(gs[:, -1])
        summary_ax.axis("off")
    else:
        fig = plt.figure(figsize=(6 * n_cols, 4 * n_rows))
        gs = fig.add_gridspec(n_rows, n_cols)
        summary_ax = None
    axes = np.empty((n_rows, n_cols), dtype=object)
    for row_i in range(n_rows):
        for col_i in range(n_cols):
            axes[row_i, col_i] = fig.add_subplot(gs[row_i, col_i])

    colors   = {
        "LAI_MODIS": "#2ca02c", "LAI_GIMMS": "#d62728", "LAI_spliced": "#8c6d31",
        "Biomass_GCM": "#9467bd", "LAI_1_GCM": "#17becf", "LAI_2_GCM": "#bcbd22",
        "LAI_3_GCM": "#e377c2", "LAI_GCM": "#7f7f7f",
        **VOD_SITE_COLORS,
    }
    model_colors = {
        "ACCESS": "#1f77b4", "CMCC": "#ff7f0e", "CNRM": "#2ca02c", "INM": "#d62728", "IPSL": "#9467bd",
        "mean": "black",
    }
    ylabels  = {"TAC": "AR(1) coefficient", "Var": "Normalized variance"}
    titles   = {"TAC": "Lag-1 TAC", "Var": "Variance"}

    for col_i, dataset in enumerate(datasets):
        label_dfs = results[dataset]
        multi = len(label_dfs) > 1
        cps_by_label = (all_changepoints or {}).get(dataset, {})
        # Title suffix names which model/mean/the full ensemble this panel
        # shows — "[all]" for the multi-line overlay, "[MODEL]"/"[mean]" for
        # a single-series (individual model or mean) plot. Non-LR datasets
        # have a single label equal to the dataset name itself — no suffix.
        if multi:
            title_suffix = " [all]"
        else:
            only_label = next(iter(label_dfs))
            title_suffix = f" [{only_label}]" if only_label != dataset else ""
        for row_i, metric in enumerate(analyses):
            ax = axes[row_i][col_i]
            plotted = False
            legend_needed = False
            for label, df in label_dfs.items():
                if metric not in df.columns:
                    continue
                plotted = True
                # Always use each model's/mean's own color (matching the
                # combined overlay plot), even on an individual single-series
                # panel — falls back to the dataset's color only for non-LR
                # datasets, which have no per-model color concept.
                color = model_colors.get(label, colors.get(dataset, "gray"))
                is_mean = label == "mean"
                ax.plot(
                    df.index, df[metric],
                    marker=None if is_mean else "o",
                    color=color,
                    linewidth=2.5 if is_mean else 1.5,
                    markersize=3 if multi else 4,
                    zorder=10 if is_mean else 2,
                    label=label if multi else None,
                )
                if multi:
                    legend_needed = True

                cp_dates = (cps_by_label.get(label) or {}).get(metric) or []
                if cp_dates and multi:
                    for cp_date in cp_dates:
                        ax.axvline(cp_date, color=color, linewidth=1.0, linestyle="--", alpha=0.6)
                elif cp_dates:
                    legend_label = "changepoints: " + ", ".join(d.strftime("%Y-%m") for d in cp_dates)
                    for cp_i, cp_date in enumerate(cp_dates):
                        ax.axvline(
                            cp_date, color="crimson", linewidth=1.5,
                            linestyle="--", label=legend_label if cp_i == 0 else None,
                        )
                    legend_needed = True

            if not plotted:
                ax.set_visible(False)
                continue
            if legend_needed:
                ax.legend(ncol=2 if multi else 1)
            ax.set_title(f"{dataset}{title_suffix} — {titles.get(metric, metric)}")
            ax.set_xlabel("Centre date")
            ax.set_ylabel(ylabels.get(metric, metric))
            ax.grid(True, linestyle="--", alpha=0.4)

    # Right-hand summary panel: surrogate-only trend tables. Shows every
    # segment (full record + each changepoint-bounded period), per model when
    # ensembled — NOT just the full-record row — so the panel matches what's
    # actually drawn (one trend per analysis window per model).
    if show_summary:
        summary_lines: list[str] = []
        summary_lines.append("Surrogate trend summary")
        summary_lines.append("")
        for dataset in datasets:
            summary_lines.append(dataset)
            summary_lines.append("-" * len(dataset))
            label_dfs = results[dataset]
            multi = len(label_dfs) > 1
            cps_by_label = (all_changepoints or {}).get(dataset, {})
            for label, df in label_dfs.items():
                cps = cps_by_label.get(label, {})
                indent = "  " if multi else ""
                if multi:
                    summary_lines.append(f"  [{label}]")
                for col in df.columns:
                    summary_lines.append(f"{indent}{col}")
                    for row_label, n, tau, p, trend in _surrogate_period_rows(df[col], cps.get(col), n_surrogates):
                        if np.isnan(tau):
                            summary_lines.append(f"{indent}  {row_label}: n={n}, tau=—, p=—, trend=—")
                        else:
                            summary_lines.append(f"{indent}  {row_label}: n={n}, tau={tau:+.3f}, p={p:.3f}, trend={trend}")
                    summary_lines.append("")
            summary_lines.append("")

        summary_ax.text(
            0.0,
            1.0,
            "\n".join(summary_lines),
            va="top",
            ha="left",
            family="monospace",
            fontsize=8,
            linespacing=1.15,
            transform=summary_ax.transAxes,
        )

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"  Saved plot: {out_path.relative_to(REPO_ROOT)}")
    plt.close(fig)

# ---------------------------------------------------------------------------
# Multi-site VOD plots (for paper figures)
# ---------------------------------------------------------------------------

def plot_raw_vod(
    raw_series: dict[str, pd.Series],
    out_path: Path,
) -> None:
    """
    Small-multiples grid of raw monthly VOD for every site in `raw_series`.
    One panel per site, stacked vertically, with a shared x-axis. Useful as
    a data-quality / spatial-context figure showing coverage gaps, absolute
    VOD levels, and seasonal cycles across catchments.
    """
    sites = list(raw_series.keys())
    n = len(sites)
    fig, axes = plt.subplots(n, 1, figsize=(12, 2.2 * n), sharex=True)
    if n == 1:
        axes = [axes]

    for idx, (ax, site) in enumerate(zip(axes, sites)):
        color = VOD_SITE_COLORS.get(site, "steelblue")
        label = VOD_SITE_LABELS.get(site, site)
        s = raw_series[site]
        ax.axvspan(pd.Timestamp("2000-01-01"), pd.Timestamp("2006-01-01"),
                   color="grey", alpha=0.08, zorder=0, lw=0)
        ax.plot(s.index, s.values, color=color, linewidth=0.9, alpha=0.85)
        ax.set_ylabel(label, rotation=0, labelpad=90, va="center")
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.text(0.01, 0.97, chr(ord('a') + idx), transform=ax.transAxes,
                fontsize=11, fontweight='bold', va='top', ha='left')

    axes[-1].set_xlabel("Date")
    fig.suptitle("Raw monthly VOD (VODCA CX+Ku) by catchment", fontsize=9, y=1.01)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"  Saved plot: {out_path.relative_to(REPO_ROOT)}")
    plt.close(fig)


def plot_vod_multisite(
    results: dict[str, dict[str, pd.DataFrame]],
    analyses: list[str],
    out_path: Path,
    all_changepoints: Optional[dict[str, dict[str, dict[str, list[pd.Timestamp]]]]] = None,
) -> None:
    """
    Single figure with one panel per metric (rows), all VOD sites overlaid as
    colored lines. This is the primary multi-catchment CSD comparison figure
    for a paper — analogous to the --model all ensemble overlay but across
    geographic locations rather than GCMs.
    """
    n_rows = len(analyses)
    fig, axes = plt.subplots(n_rows, 1, figsize=(13, 4 * n_rows), sharex=True)
    if n_rows == 1:
        axes = [axes]

    ylabels = {"TAC": "AR(1) coefficient", "Var": "Normalized variance"}
    titles  = {"TAC": "Lag-1 TAC", "Var": "Variance"}

    for row_i, metric in enumerate(analyses):
        ax = axes[row_i]
        ax.axvspan(pd.Timestamp("2000-01-01"), pd.Timestamp("2006-01-01"),
                   color="grey", alpha=0.08, zorder=0, lw=0)
        for site, label_dfs in results.items():
            df = next(iter(label_dfs.values()))
            if metric not in df.columns:
                continue
            color = VOD_SITE_COLORS.get(site, "gray")
            display = VOD_SITE_LABELS.get(site, site)
            ax.plot(df.index, df[metric], color=color, linewidth=1.6,
                    marker="o", markersize=3, label=display, alpha=0.85)

            if all_changepoints:
                cp_dates = (all_changepoints.get(site, {})
                            .get(next(iter(results[site])), {})
                            .get(metric, []))
                for cp in cp_dates:
                    ax.axvline(cp, color=color, linewidth=1.0, linestyle="--", alpha=0.5)

        ax.set_ylabel(ylabels.get(metric, metric))
        ax.set_title(titles.get(metric, metric))
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(ncol=3, loc="best")
        ax.text(0.01, 0.97, chr(ord('a') + row_i), transform=ax.transAxes,
                fontsize=11, fontweight='bold', va='top', ha='left')

    axes[-1].set_xlabel("Centre date")
    fig.suptitle("CSD indicators — all VOD catchments", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"  Saved plot: {out_path.relative_to(REPO_ROOT)}")
    plt.close(fig)


def plot_significance_heatmap(
    results: dict[str, dict[str, pd.DataFrame]],
    analyses: list[str],
    out_path: Path,
    n_surrogates: int,
) -> None:
    """
    Heatmap of Kendall τ across sites (rows) × metrics (columns).
    Cell color encodes τ (diverging RdBu_r: blue = decreasing, red = increasing).
    Cell text shows τ and p; asterisk marks p < 0.05. Gives a compact,
    paper-ready summary of which catchments show significant CSD trends.
    """
    sites = list(results.keys())
    n_sites = len(sites)
    n_metrics = len(analyses)

    tau_mat = np.full((n_sites, n_metrics), np.nan)
    p_mat   = np.full((n_sites, n_metrics), np.nan)

    for si, site in enumerate(sites):
        df = next(iter(results[site].values()))
        for mi, metric in enumerate(analyses):
            if metric not in df.columns:
                continue
            r = phase_surrogate_test(df[metric], n_surrogates=n_surrogates)
            tau_mat[si, mi] = r["tau"]
            p_mat[si, mi]   = r["p"]

    vmax = np.nanmax(np.abs(tau_mat)) if not np.all(np.isnan(tau_mat)) else 1.0
    fig, ax = plt.subplots(figsize=(max(4, 2.5 * n_metrics), max(4, 0.55 * n_sites + 1.5)))
    im = ax.imshow(tau_mat, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)

    ax.set_xticks(range(n_metrics))
    ax.set_xticklabels(analyses)
    ax.set_yticks(range(n_sites))
    ax.set_yticklabels([VOD_SITE_LABELS.get(s, s) for s in sites])
    ax.set_title("Kendall τ by catchment and metric\n(phase-surrogate p; * p < 0.05)")

    for si in range(n_sites):
        for mi in range(n_metrics):
            tau = tau_mat[si, mi]
            p   = p_mat[si, mi]
            if np.isnan(tau):
                ax.text(mi, si, "—", ha="center", va="center")
            else:
                sig = "*" if (not np.isnan(p) and p < 0.05) else ""
                ax.text(mi, si, f"τ={tau:+.2f}\np={p:.2f}{sig}",
                        ha="center", va="center",
                        color="white" if abs(tau) > 0.5 * vmax else "black")

    plt.colorbar(im, ax=ax, label="Kendall τ", shrink=0.7)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"  Saved plot: {out_path.relative_to(REPO_ROOT)}")
    plt.close(fig)


def plot_vod_tac_grid(
    results: dict[str, dict[str, pd.DataFrame]],
    out_path: Path,
) -> None:
    """
    5-row × 2-column grid of TAC time series, one panel per water-supply
    catchment (the 10 non-Cannonsville VOD sites). Intended as a compact
    per-site panel figure for a paper supplement or results section.
    2000–2006 is shaded grey as a regime-shift reference period.
    """
    grid_sites = [s for s in VOD_SITES if s != "VOD"]  # 10 sites, preserves insertion order
    nrows, ncols = 5, 2

    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 3.5 * nrows), sharex=True, sharey=False)
    axes_flat = axes.flatten()

    for i, site in enumerate(grid_sites):
        ax = axes_flat[i]
        color = VOD_SITE_COLORS.get(site, "steelblue")
        display = VOD_SITE_LABELS.get(site, site)

        ax.axvspan(pd.Timestamp("2000-01-01"), pd.Timestamp("2006-01-01"),
                   color="grey", alpha=0.08, zorder=0, lw=0)

        if site in results and "TAC" in next(iter(results[site].values())).columns:
            df = next(iter(results[site].values()))
            ax.plot(df.index, df["TAC"], color=color, linewidth=1.5,
                    marker="o", markersize=3.5, alpha=0.9)

        ax.set_title(display, pad=3)
        ax.set_ylabel("AR(1) coeff.")
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.text(0.01, 0.97, chr(ord('a') + i), transform=ax.transAxes,
                fontsize=11, fontweight='bold', va='top', ha='left')

    for ax in axes_flat[len(grid_sites):]:
        ax.set_visible(False)

    for ax in axes[-1]:
        ax.set_xlabel("Centre date")

    fig.suptitle("Lag-1 TAC by catchment (VOD, VODCA CX+Ku)", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"  Saved plot: {out_path.relative_to(REPO_ROOT)}")
    plt.close(fig)


def plot_vod_split_grid(
    results: dict[str, dict[str, pd.DataFrame]],
    metric: str,
    out_path: Path,
    all_changepoints: dict[str, dict[str, dict[str, list[pd.Timestamp]]]],
    n_surrogates: int = 500,
) -> None:
    """
    5×2 grid of one CSD metric for the 10 water-supply catchments.
    Background: light red = post-split trend significantly increasing (p<0.05,
    analytical Kendall tau); light blue = significantly decreasing.
    Per-segment τ and p annotations inside each panel.
    """
    from scipy.stats import kendalltau as _ktu
    grid_sites = [s for s in VOD_SITES if s != "VOD"]
    nrows, ncols = 5, 2
    ylabels = {"TAC": "AR(1) coeff.", "Var": "Norm. variance"}

    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 3.8 * nrows),
                             sharex=False, sharey=False)
    axes_flat = axes.flatten()

    for i, site in enumerate(grid_sites):
        ax = axes_flat[i]
        color = VOD_SITE_COLORS.get(site, "steelblue")
        display = VOD_SITE_LABELS.get(site, site)

        if site not in results:
            ax.set_visible(False)
            continue
        df = next(iter(results[site].values()))
        if metric not in df.columns:
            ax.set_visible(False)
            continue

        series = df[metric]
        site_label = next(iter(results[site]))
        cps = all_changepoints.get(site, {}).get(site_label, {}).get(metric, [])

        x_min = df.index.min()
        x_max = df.index.max()

        # Per-segment background shading: axvspan only covers that segment
        if cps:
            pre = series[series.index < cps[0]].dropna()
            post = series[series.index >= cps[0]].dropna()
            if len(pre) >= 4:
                tau_pre, p_pre = _ktu(np.arange(len(pre)), pre.values)
                if p_pre < 0.05:
                    c_pre = "#ffe8e8" if tau_pre > 0 else "#e8eeff"
                    ax.axvspan(x_min, cps[0], color=c_pre, alpha=0.45, zorder=0, lw=0)
            if len(post) >= 4:
                tau_post, p_post = _ktu(np.arange(len(post)), post.values)
                if p_post < 0.05:
                    c_post = "#ffe8e8" if tau_post > 0 else "#e8eeff"
                    ax.axvspan(cps[0], x_max, color=c_post, alpha=0.45, zorder=0, lw=0)

        # Changepoint line(s)
        for cp in cps:
            ax.axvline(cp, color="dimgray", linewidth=1.2, linestyle="--", alpha=0.7)

        ax.plot(df.index, df[metric], color=color, linewidth=1.5,
                marker="o", markersize=3, alpha=0.9)
        ax.set_title(display, pad=3)
        ax.set_ylabel(ylabels.get(metric, metric))
        ax.grid(True, linestyle="--", alpha=0.3)

        # Year labels on every panel
        import matplotlib.dates as mdates
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", rotation=90)

        # Panel letter
        ax.text(0.01, 0.97, chr(ord('a') + i), transform=ax.transAxes,
                fontsize=11, fontweight='bold', va='top', ha='left')

        # Segment significance annotation
        segs = (
            [("pre", series[series.index < cps[0]]),
             ("post", series[series.index >= cps[0]])]
            if cps else [("full", series)]
        )
        parts = []
        for seg_name, seg in segs:
            v = seg.dropna()
            if len(v) < 4:
                parts.append(f"{seg_name}: n<4")
            else:
                tau, p = _ktu(np.arange(len(v)), v.values)
                parts.append(f"{seg_name}: τ={tau:+.2f} p={p:.2f}{'*' if p < 0.05 else ''}")
        ax.annotate(
            "   ".join(parts),
            xy=(0.02, 0.04), xycoords="axes fraction", va="bottom",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.65, lw=0),
        )

    for ax in axes_flat[len(grid_sites):]:
        ax.set_visible(False)

    title = {"TAC": "Lag-1 TAC", "Var": "Variance"}.get(metric, metric)
    fig.suptitle(f"{title} by catchment — changepoint 2000-01\n"
                 "background: red = sig. increasing post-split, blue = sig. decreasing  (analytical p<0.05)",
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"  Saved plot: {out_path.relative_to(REPO_ROOT)}")
    plt.close(fig)


def plot_tac_heatmap(
    results: dict[str, dict[str, pd.DataFrame]],
    out_path: Path,
    metric: str = "TAC",
) -> None:
    """
    Sites × window-centre-date heatmap of a CSD metric.
    Diverging colormap (blue = low/decreasing, red = high/increasing) reveals
    when the regime shift occurred at each site simultaneously.
    """
    grid_sites = [s for s in VOD_SITES if s != "VOD"]
    all_dates = sorted({
        d
        for site in grid_sites if site in results
        for d in next(iter(results[site].values())).index
    })
    if not all_dates:
        return

    date_idx = {d: i for i, d in enumerate(all_dates)}
    mat = np.full((len(grid_sites), len(all_dates)), np.nan)
    for si, site in enumerate(grid_sites):
        if site not in results:
            continue
        df = next(iter(results[site].values()))
        if metric not in df.columns:
            continue
        for d, val in df[metric].items():
            if d in date_idx:
                mat[si, date_idx[d]] = val

    vmax = float(np.nanpercentile(np.abs(mat[~np.isnan(mat)]), 95)) if not np.all(np.isnan(mat)) else 1.0
    fig, ax = plt.subplots(figsize=(13, 0.52 * len(grid_sites) + 1.8))
    im = ax.imshow(mat, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                   interpolation="nearest")

    seen_years: set[int] = set()
    year_ticks = []
    for i, d in enumerate(all_dates):
        if d.year not in seen_years:
            year_ticks.append(i)
            seen_years.add(d.year)
    ax.set_xticks(year_ticks)
    ax.set_xticklabels([all_dates[i].strftime("%Y") for i in year_ticks], rotation=90)
    ax.set_yticks(range(len(grid_sites)))
    ax.set_yticklabels([VOD_SITE_LABELS.get(s, s) for s in grid_sites])

    cp = pd.Timestamp("2000-01-01")
    if cp in date_idx:
        ax.axvline(date_idx[cp] - 0.5, color="black", linewidth=1.5, linestyle="--",
                   alpha=0.8, label="2000-01")
        ax.legend(loc="upper left")

    plt.colorbar(im, ax=ax, label={"TAC": "AR(1) coeff.", "Var": "Norm. variance"}.get(metric, metric),
                 shrink=0.7)
    title = {"TAC": "Lag-1 TAC", "Var": "Variance"}.get(metric, metric)
    ax.set_title(f"{title} across catchments and time (VODCA CX+Ku)\n"
                 "blue = low / decreasing resilience loss,  red = high / increasing resilience loss")
    ax.set_xlabel("Window centre date")
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"  Saved plot: {out_path.relative_to(REPO_ROOT)}")
    plt.close(fig)


def plot_tac_changepoint_bars(
    results: dict[str, dict[str, pd.DataFrame]],
    out_path: Path,
    all_changepoints: dict[str, dict[str, dict[str, list[pd.Timestamp]]]],
    metric: str = "TAC",
) -> None:
    """
    Horizontal bar chart of Kendall τ for pre-split and post-split periods.
    Pre-2000: steel blue; post-2000: coral. Full opacity = p<0.05; faded = not
    significant. Dotted vertical lines mark the approximate p=0.05 critical τ
    for the median segment length (normal approximation to Kendall distribution).
    """
    from scipy.stats import kendalltau as _ktu
    from scipy.stats import norm as _norm

    grid_sites = [s for s in VOD_SITES if s != "VOD"]
    PRE_COLOR  = "#4393c3"  # steel blue
    POST_COLOR = "#d6604d"  # coral-red

    pre_tau, post_tau, pre_sig, post_sig = [], [], [], []
    pre_ns, post_ns = [], []

    for site in grid_sites:
        if site not in results:
            for lst in (pre_tau, post_tau, pre_sig, post_sig, pre_ns, post_ns):
                lst.append(np.nan if lst in (pre_tau, post_tau) else False if lst in (pre_sig, post_sig) else 0)
            continue
        df = next(iter(results[site].values()))
        if metric not in df.columns:
            pre_tau.append(np.nan); post_tau.append(np.nan)
            pre_sig.append(False);  post_sig.append(False)
            pre_ns.append(0);       post_ns.append(0)
            continue
        series = df[metric]
        site_label = next(iter(results[site]))
        cps = all_changepoints.get(site, {}).get(site_label, {}).get(metric, [])
        if not cps:
            pre_tau.append(np.nan); post_tau.append(np.nan)
            pre_sig.append(False);  post_sig.append(False)
            pre_ns.append(0);       post_ns.append(0)
            continue
        for seg, tau_list, sig_list, n_list in [
            (series[series.index < cps[0]].dropna(),  pre_tau,  pre_sig,  pre_ns),
            (series[series.index >= cps[0]].dropna(), post_tau, post_sig, post_ns),
        ]:
            if len(seg) >= 4:
                t, p = _ktu(np.arange(len(seg)), seg.values)
                tau_list.append(float(t)); sig_list.append(p < 0.05); n_list.append(len(seg))
            else:
                tau_list.append(np.nan); sig_list.append(False); n_list.append(0)

    # Critical τ for p=0.05 (two-sided) via normal approx: τ_crit = z * sqrt(2(2n+5)/(9n(n-1)))
    def _tau_crit(n: float) -> float:
        if n < 4:
            return np.nan
        return float(_norm.ppf(0.975) * np.sqrt(2 * (2 * n + 5) / (9 * n * (n - 1))))

    med_pre_n  = float(np.nanmedian([n for n in pre_ns  if n > 0]))
    med_post_n = float(np.nanmedian([n for n in post_ns if n > 0]))
    crit_pre  = _tau_crit(med_pre_n)
    crit_post = _tau_crit(med_post_n)

    y = np.arange(len(grid_sites))
    bar_h = 0.35
    fig, ax = plt.subplots(figsize=(7.5, 0.65 * len(grid_sites) + 1.8))

    for i in range(len(grid_sites)):
        if not np.isnan(pre_tau[i]):
            ax.barh(y[i] + bar_h / 2, pre_tau[i], height=bar_h,
                    color=PRE_COLOR, alpha=0.85 if pre_sig[i] else 0.28,
                    edgecolor="none", label="pre-2000" if i == 0 else "")
        if not np.isnan(post_tau[i]):
            ax.barh(y[i] - bar_h / 2, post_tau[i], height=bar_h,
                    color=POST_COLOR, alpha=0.85 if post_sig[i] else 0.28,
                    edgecolor="none", label="post-2000" if i == 0 else "")

    ax.axvline(0, color="black", linewidth=0.8, alpha=0.6)

    # Significance threshold lines
    if not np.isnan(crit_pre):
        ax.axvline( crit_pre, color=PRE_COLOR,  linewidth=1.0, linestyle=":", alpha=0.7,
                    label=f"pre p=0.05 (n≈{int(med_pre_n)})")
        ax.axvline(-crit_pre, color=PRE_COLOR,  linewidth=1.0, linestyle=":", alpha=0.7)
    if not np.isnan(crit_post):
        ax.axvline( crit_post, color=POST_COLOR, linewidth=1.0, linestyle=":", alpha=0.7,
                    label=f"post p=0.05 (n≈{int(med_post_n)})")
        ax.axvline(-crit_post, color=POST_COLOR, linewidth=1.0, linestyle=":", alpha=0.7)

    ax.set_yticks(y)
    ax.set_yticklabels([VOD_SITE_LABELS.get(s, s) for s in grid_sites])
    ax.set_xlabel(f"Kendall τ ({metric})")
    ax.set_title(f"Pre- vs post-2000 {metric} trend by catchment\n"
                 "faded = not significant (analytical p≥0.05); dotted lines = p=0.05 threshold")
    ax.legend(loc="lower right")
    ax.grid(True, axis="x", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"  Saved plot: {out_path.relative_to(REPO_ROOT)}")
    plt.close(fig)


def plot_tac_pre_post_scatter(
    results: dict[str, dict[str, pd.DataFrame]],
    out_path: Path,
    all_changepoints: dict[str, dict[str, dict[str, list[pd.Timestamp]]]],
    metric: str = "TAC",
) -> None:
    """
    Scatter: pre-split Kendall τ (x) vs post-split Kendall τ (y) per catchment.
    Upper-left quadrant = shifted from decreasing to increasing TAC after 2000.
    Filled markers = post-split p < 0.05 (analytical).
    """
    from scipy.stats import kendalltau as _ktu
    grid_sites = [s for s in VOD_SITES if s != "VOD"]

    fig, ax = plt.subplots(figsize=(6, 5.5))

    pts: list[tuple] = []
    for site in grid_sites:
        if site not in results:
            continue
        df = next(iter(results[site].values()))
        if metric not in df.columns:
            continue
        series = df[metric]
        site_label = next(iter(results[site]))
        cps = all_changepoints.get(site, {}).get(site_label, {}).get(metric, [])
        if not cps:
            continue
        pre = series[series.index < cps[0]].dropna()
        post = series[series.index >= cps[0]].dropna()
        if len(pre) < 4 or len(post) < 4:
            continue
        pre_tau, _ = _ktu(np.arange(len(pre)), pre.values)
        post_tau, post_p = _ktu(np.arange(len(post)), post.values)
        pts.append((site, float(pre_tau), float(post_tau), post_p < 0.05))

    if not pts:
        plt.close(fig)
        return

    xs = [p[1] for p in pts]; ys = [p[2] for p in pts]
    xlim = (-1.0, 1.0)
    ylim = (-1.0, 1.0)
    ax.set_xlim(xlim); ax.set_ylim(ylim)

    # Quadrant text labels
    qpad = 0.04
    ax.text(xlim[0] + qpad, ylim[1] - qpad, "dec → inc\n(regime shift)",
            ha="left", va="top", color="#b03030",
            bbox=dict(fc="white", alpha=0.6, lw=0, pad=2))
    ax.text(xlim[1] - qpad, ylim[1] - qpad, "inc → inc",
            ha="right", va="top", color="#555",
            bbox=dict(fc="white", alpha=0.6, lw=0, pad=2))
    ax.text(xlim[0] + qpad, ylim[0] + qpad, "dec → dec",
            ha="left", va="bottom", color="#555",
            bbox=dict(fc="white", alpha=0.6, lw=0, pad=2))
    ax.text(xlim[1] - qpad, ylim[0] + qpad, "inc → dec",
            ha="right", va="bottom", color="#3050b0",
            bbox=dict(fc="white", alpha=0.6, lw=0, pad=2))

    ax.axhline(0, color="black", linewidth=0.8, alpha=0.6, zorder=1)
    ax.axvline(0, color="black", linewidth=0.8, alpha=0.6, zorder=1)

    for site, xt, yt, sig in pts:
        c = VOD_SITE_COLORS.get(site, "gray")
        display = VOD_SITE_LABELS.get(site, site)
        if sig:
            ax.scatter(xt, yt, s=110, color=c, zorder=4)
        else:
            ax.scatter(xt, yt, s=110, facecolors="none", edgecolors=c, linewidths=2.0, zorder=4)
        ax.annotate(display, (xt, yt), textcoords="offset points",
                    xytext=(7, 4), color=c, zorder=5)

    # Legend for marker style only
    from matplotlib.lines import Line2D
    legend_els = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="gray",
               markersize=9, label="post-2000 p<0.05"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="none",
               markeredgecolor="gray", markeredgewidth=2, markersize=9, label="post-2000 p≥0.05"),
    ]
    ax.legend(handles=legend_els, loc="lower right", framealpha=0.85, edgecolor="lightgray")

    ax.set_xlabel(f"Pre-2000 Kendall τ ({metric})")
    ax.set_ylabel(f"Post-2000 Kendall τ ({metric})")
    ax.set_title(
        f"Regime shift: pre- vs post-2000 {metric} trend per catchment\n"
        "(analytical Kendall τ, p<0.05 = filled marker)",
    )
    ax.grid(True, linestyle="--", alpha=0.3, zorder=0)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"  Saved plot: {out_path.relative_to(REPO_ROOT)}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute CSD resilience indicators (TAC, Variance) for the "
            "Cannonsville Watershed using a sliding window (--window, default 5 years)."
        )
    )
    parser.add_argument(
        "--data",
        choices=[
            "LAI_MODIS", "LAI_GIMMS", "LAI_spliced",
            "VOD",
            *[k for k in VOD_SITES if k != "VOD"],  # Hinckley_NY … Massabesic_NH
            "Biomass_GCM", "LAI_1_GCM", "LAI_2_GCM", "LAI_3_GCM", "LAI_GCM",
            "vod-all", "all",
        ],
        default="all",
        help="Dataset(s) to process (default: all)",
    )
    parser.add_argument(
        "--analysis",
        choices=["TAC", "Var", "all"],
        default="all",
        help="Indicator(s) to compute (default: all)",
    )
    parser.add_argument(
        "--model",
        choices=list(LRANGE_MODELS.keys()) + ["all", "mean"],
        default="all",
        help=(
            "GCM(s) to use for L-Range datasets only (Biomass_GCM, LAI_1_GCM, LAI_2_GCM, "
            "LAI_3_GCM, LAI_GCM) — ignored for LAI_MODIS/LAI_GIMMS/LAI_spliced/VOD, which "
            "have no GCM dimension. 'all' (default) runs the full 5-model ensemble and "
            "overlays all five as separate colored lines on one plot per dataset/metric, "
            "with independent de-trending, changepoint detection, and significance testing "
            "for each model. Pick a single model (e.g. 'INM') for a faster single-GCM run. "
            "'mean' runs the analysis on just the cross-GCM ensemble mean (the raw monthly "
            "vegetation state averaged across all 5 GCMs before de-trending) — skips the "
            "5 individual per-model analyses and outputs a single result, like a single-model "
            "run but for the ensemble mean instead of one GCM."
        ),
    )
    parser.add_argument(
        "--detrend",
        choices=["stl", "climatology"],
        default="stl",
        help=(
            "De-trending method (default: stl). "
            "'stl' uses Seasonal-Trend Decomposition by Loess, matching Boulton et al. (2022) "
            "and Smith et al. (2022); removes both trend and seasonal cycle adaptively. "
            "'climatology' subtracts the long-term monthly mean over the reference period."
        ),
    )
    parser.add_argument(
        "--n-surrogates",
        type=int,
        default=1000,
        help=(
            "Number of phase-shuffled surrogates for significance testing "
            "(default: 1000; Boulton et al. used 100,000 for pixel-level tests, "
            "Smith et al. used 10,000; 1000 is sufficient for exploratory analysis)."
        ),
    )
    parser.add_argument(
        "--window",
        type=int,
        choices=[5, 10],
        default=5,
        help=(
            "Sliding window length in years (default: 5). "
            "Minimum valid months per window is 50%% of the window length "
            "(30 for a 5-year window, 60 for a 10-year window)."
        ),
    )
    parser.add_argument(
        "--step",
        type=int,
        choices=[6, 12],
        default=12,
        help=(
            "Sliding window step in months (default: 12). "
            "Use 6 for semi-annual steps and a smoother indicator curve. "
            "With a 60-month (--window 5) window, step=12 gives 80%% overlap between "
            "adjacent windows (48/60 shared months); step=6 gives 90%% overlap (54/60 "
            "shared months). Overlap is even higher with --window 10. In both cases the "
            "indicator values are serially correlated, so standard Mann-Kendall p-values "
            "are anti-conservative. Use --significance surrogate."
        ),
    )
    parser.add_argument(
        "--significance",
        choices=["surrogate", "mk", "both"],
        default="surrogate",
        help=(
            "Significance testing method (default: surrogate). "
            "'surrogate' uses phase-shuffled Fourier surrogates — accounts for serial "
            "correlation from overlapping windows; matches Boulton et al. (2022) and "
            "Smith et al. (2022). "
            "'mk' uses the standard Mann-Kendall test — fast but assumes independence; "
            "p-values are anti-conservative at both step=12 (80%% window overlap) and "
            "step=6 (90%% overlap). Use only for quick exploration; prefer surrogate for reporting. "
            "'both' runs and prints both methods for comparison."
        ),
    )
    parser.add_argument(
        "--changepoint",
        metavar="{PELT[:K],minimax-p[:K],fisher-p[:K],YYYY-MM[,YYYY-MM...]}",
        default=None,
        help=(
            "Split the record into sub-periods and run trend tests on each segment "
            "separately (default: off, full-record only). Four modes: "
            "'PELT' runs ruptures PELT changepoint detection (RBF cost), which picks both "
            "the number and location of breaks via a BIC-equivalent penalty (may find 0, 1, "
            "or several); "
            "'minimax-p' scans all candidate partitions and picks the one minimising the "
            "WORST (max) Kendall tau p-value across all segments — i.e. the partition where "
            "every segment is most likely to be individually significant, at the cost of "
            "preferring several mediocre segments over a mix of great and terrible ones "
            "(defaults to a single split, 2 segments); "
            "'fisher-p' scans all candidate partitions and picks the one minimising the "
            "PRODUCT of the segment p-values (Fisher's method for combining p-values) — the "
            "opposite trade-off from minimax-p: a product is dominated by its smallest "
            "factors, so e.g. p=[0.01, 0.01, 0.9] beats p=[0.2, 0.2, 0.2], rewarding a "
            "partition with a couple of extremely significant segments even if another "
            "segment is not significant at all (also defaults to a single split); "
            "'YYYY-MM' (e.g. '2003-01') manually fixes a split date, matching the approach "
            "of Boulton et al. (2022, split at 2003) and Smith et al. (2022, split at 2004); "
            "comma-separate multiple dates (e.g. '2003-01,2015-06') for more than one "
            "manual split. "
            "Append ':K' to 'PELT', 'minimax-p', or 'fisher-p' to force exactly K segments "
            "(K-1 changepoints), e.g. '--changepoint PELT:3' or '--changepoint fisher-p:3'. "
            "For PELT, ':K' switches to ruptures Binary Segmentation (forces an exact "
            "break count); without ':K', PELT's penalty determines the break count itself."
        ),
    )
    return parser.parse_args()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    if args.data == "all":
        datasets = [
            "LAI_MODIS", "LAI_GIMMS", "LAI_spliced",
            "VOD",
            "Biomass_GCM", "LAI_1_GCM", "LAI_2_GCM", "LAI_3_GCM", "LAI_GCM",
        ]
    elif args.data == "vod-all":
        datasets = list(VOD_SITES.keys())
    else:
        datasets = [args.data]
    analyses       = ["TAC", "Var"] if args.analysis == "all" else [args.analysis]
    window_years   = args.window
    window_months  = window_years * 12
    step           = args.step
    detrend_method = args.detrend
    n_surrogates   = args.n_surrogates
    sig_method     = args.significance
    run_surrogate  = sig_method in ("surrogate", "both")
    run_mk         = sig_method in ("mk", "both")

    # Parse --changepoint into one of four mutually exclusive modes.
    # Syntax: 'PELT[:K]', 'minimax-p[:K]', 'fisher-p[:K]', or comma-separated 'YYYY-MM[,YYYY-MM...]'.
    cp_arg       = args.changepoint
    run_pelt     = False
    run_minimax  = False
    run_fisher   = False
    run_binseg   = False  # PELT:K forces ruptures Binseg with an exact break count
    n_segments   = None   # only meaningful for PELT/minimax-p/fisher-p
    split_dates: list[pd.Timestamp] = []
    split_label  = None

    if cp_arg is not None:
        method_part, _, k_part = cp_arg.partition(":")
        if k_part:
            try:
                n_segments = int(k_part)
            except ValueError:
                raise ValueError(
                    f"--changepoint '{cp_arg}': invalid segment count '{k_part}' after ':' "
                    "(expected an integer, e.g. 'PELT:3')"
                )
            if n_segments < 2:
                raise ValueError(
                    f"--changepoint '{cp_arg}': segment count must be >= 2 "
                    "(K segments implies K-1 changepoints)"
                )

        if method_part == "PELT":
            run_pelt = True
            run_binseg = n_segments is not None
        elif method_part == "minimax-p":
            run_minimax = True
            if n_segments is None:
                n_segments = 2  # legacy default: single split
        elif method_part == "fisher-p":
            run_fisher = True
            if n_segments is None:
                n_segments = 2  # default: single split
        else:
            if n_segments is not None:
                raise ValueError(
                    f"--changepoint '{cp_arg}': ':K' segment-count syntax is only valid "
                    "with 'PELT', 'minimax-p', or 'fisher-p', not manual dates."
                )
            try:
                split_dates = sorted(pd.Timestamp(d.strip()) for d in cp_arg.split(","))
            except Exception:
                raise ValueError(
                    f"--changepoint value '{cp_arg}' not recognized. "
                    "Use 'PELT[:K]', 'minimax-p[:K]', 'fisher-p[:K]', or comma-separated YYYY-MM dates."
                )
            split_label = cp_arg

    lr_loaders = {
        "Biomass_GCM": load_biomass_lr, "LAI_1_GCM": load_lai_1_lr, "LAI_2_GCM": load_lai_2_lr,
        "LAI_3_GCM": load_lai_3_lr, "LAI_GCM": load_lai_lr,
    }
    non_lr_loaders = {
        "LAI_MODIS": load_lai_modis, "LAI_GIMMS": load_lai_gimms, "LAI_spliced": load_lai_spliced,
        "VOD": load_vod,
        **_VOD_SITE_LOADERS,
    }

    model_arg = args.model
    if model_arg != "all" and not any(d in lr_loaders for d in datasets):
        print(f"  Note: --model {model_arg} has no effect — no L-Range datasets selected.")

    # Build filenames that encode every input parameter.
    if run_pelt:
        split_tag = f"PELTn{n_segments}" if run_binseg else "PELT"
    elif run_minimax:
        split_tag = "minimaxp" if n_segments == 2 else f"minimaxpn{n_segments}"
    elif run_fisher:
        split_tag = "fisherp" if n_segments == 2 else f"fisherpn{n_segments}"
    elif split_dates:
        split_tag = "split" + "_".join(d.strftime("%Y%m") for d in split_dates)
    else:
        split_tag = "nosplit"

    params_suffix = f"win{window_years}y_step{step}_{detrend_method}_{split_tag}_nsurr{n_surrogates}"

    # The top-level combined plot/report name embeds which model(s) it covers:
    # a single explicit --model embeds that model's name; the 5-GCM ensemble
    # embeds "_all_" (it overlays every model); multi-dataset/non-LR runs have
    # no model dimension and stay at the dataset (or "all") level.
    single_lr_dataset = args.data in lr_loaders
    if single_lr_dataset and model_arg != "all":
        base_name = f"{args.data}_{model_arg}_{params_suffix}"
    elif single_lr_dataset:
        base_name = f"{args.data}_all_{params_suffix}"
    else:
        base_name = f"{args.data}_{params_suffix}"

    # All output for this run lives under output/{data_param}/
    run_out_dir = OUT_DIR / args.data
    run_out_dir.mkdir(parents=True, exist_ok=True)

    run_params = {
        "data":         args.data,
        "analysis":     args.analysis,
        "model":        args.model,
        "window_years": window_years,
        "step":         step,
        "detrend":      detrend_method,
        "significance": sig_method,
        "split_mode":   split_tag,
        "n_surrogates": n_surrogates,
    }

    all_results:      dict[str, dict[str, pd.DataFrame]] = {}
    all_changepoints: dict[str, dict[str, dict[str, list[pd.Timestamp]]]] = {}
    all_raw:          dict[str, pd.Series] = {}  # raw monthly series, collected for vod-all plots

    for dataset in datasets:
        is_lr = dataset in lr_loaders
        mean_only = is_lr and model_arg == "mean"
        if is_lr:
            # "mean" needs every model's raw series to average, same as "all"
            model_keys = list(LRANGE_MODELS.keys()) if model_arg in ("all", "mean") else [model_arg]
        else:
            model_keys = [None]
        ensemble = is_lr and model_arg == "all"

        # --- Load raw series for every requested model up front ---
        # (needed before de-trending so the ensemble mean, if any, is built from
        # raw monthly values, not from already-detrended/normalized output)
        raw_series: dict[str, pd.Series] = {}
        for model_key in model_keys:
            if is_lr:
                lrange_dir = LRANGE_ALL_DIR / LRANGE_MODELS[model_key]
                raw_series[model_key] = lr_loaders[dataset](lrange_dir)
            else:
                raw_series[dataset] = non_lr_loaders[dataset]()

        if ensemble or mean_only:
            # Cross-GCM ensemble mean: average the raw monthly series across all
            # models (date-aligned, skipping any model missing a given month),
            # then run it through the identical pipeline as a "mean" series.
            # This is NOT the same as averaging the final TAC/Var curves —
            # averaging raw vegetation state suppresses each GCM's own internal
            # variability before CSD analysis, giving a cleaner multi-model
            # consensus signal; averaging TAC/Var post-hoc would not have a
            # well-defined CSD interpretation (TAC of a mean != mean of TACs).
            combined = pd.concat([raw_series[m] for m in model_keys], axis=1)
            mean_series = combined.mean(axis=1, skipna=True)
            mean_series.name = dataset
            if ensemble:
                # Ensemble mode: keep all 5 individual models AND the mean.
                raw_series["mean"] = mean_series
                labels = model_keys + ["mean"]
            else:
                # --model mean: discard the individual models — only the mean
                # itself gets de-trended/windowed/analyzed/output.
                raw_series = {"mean": mean_series}
                labels = ["mean"]
        elif is_lr:
            labels = list(model_keys)
        else:
            labels = [dataset]

        dataset_results: dict[str, pd.DataFrame] = {}
        dataset_cps:     dict[str, dict[str, list[pd.Timestamp]]] = {}

        for label in labels:
            series_key = label if is_lr else dataset
            series = raw_series[series_key]
            header = f"{dataset} [{label}]" if is_lr else dataset
            sep = "=" * 52
            print(f"\n{sep}\n  {header}\n{sep}")

            n_valid = int(series.notna().sum())
            n_total = len(series)
            print(
                f"  {n_valid}/{n_total} valid monthly values  "
                f"({series.index[0].strftime('%Y-%m')} – {series.index[-1].strftime('%Y-%m')})"
            )

            # --- De-trend ---
            clim_start, clim_end = CLIM_PERIODS[dataset]
            print(f"  De-trending ({detrend_method})...")
            anomalies = detrend(series, detrend_method, clim_start, clim_end)
            resid_std = anomalies.std()
            print(f"  Residual std = {resid_std:.4f}")

            # --- Normalize ---
            # Divide by the full-record residual std so Variance is expressed in
            # comparable units across datasets (e.g. Biomass_GCM's g/m^2 scale vs
            # LAI's ~O(1) m^2/m^2 scale). TAC is a ratio of sums in matching squared
            # units, so it is exactly invariant to this positive rescaling — only
            # the Variance column's absolute magnitude changes.
            if resid_std and not np.isnan(resid_std) and resid_std > 0:
                anomalies = anomalies / resid_std

            # --- Sliding window ---
            print(f"  Sliding window ({window_months}-month, {step}-month step)...")
            df = sliding_window(anomalies, analyses, window_months=window_months, step_months=step)
            print(f"  Windows computed: {len(df)}")
            print(df.to_string())

            # --- Save CSV ---
            # L-Range datasets always carry the model name (or "mean" for the
            # ensemble mean) in the filename, even for a single-model run —
            # avoids an ambiguous filename that doesn't say which GCM it's from.
            if is_lr:
                csv_name = f"{dataset}_{label}_{params_suffix}.csv"
            else:
                csv_name = f"{dataset}_{params_suffix}.csv"
            csv_path = run_out_dir / csv_name
            df.to_csv(csv_path)
            print(f"  Saved: {csv_path.relative_to(REPO_ROOT)}")

            # --- Changepoint / manual split ---
            if run_pelt:
                if run_binseg:
                    print(f"  Changepoint detection (Binseg/RBF, forced {n_segments} segments):")
                    changepoints = detect_changepoints_binseg(df, header, n_segments)
                else:
                    print("  Changepoint detection (PELT/RBF):")
                    changepoints = detect_changepoints(df, header)
            elif run_minimax:
                print(f"  Minimax-p split search ({n_segments}-segment, min of max p across segments):")
                changepoints = minimax_split_search(df, header, n_segments=n_segments)
            elif run_fisher:
                print(f"  Fisher-p split search ({n_segments}-segment, min product of p across segments):")
                changepoints = fisher_split_search(df, header, n_segments=n_segments)
            elif split_dates:
                # Apply the same manual split date(s) to every indicator column
                changepoints = {col: split_dates for col in df.columns}
                print(f"  Manual split at {split_label} applied to all indicators.")
            else:
                changepoints = {}

            # --- Trend significance: phase-surrogate Kendall tau ---
            use_split = run_pelt or run_minimax or run_fisher or bool(split_dates)
            if run_surrogate:
                print(f"  Trend significance — phase-surrogate (n={n_surrogates}):")
                surrogate_report(df, header, n_surrogates, changepoints if use_split else None)

            # --- Mann-Kendall (standard) ---
            if run_mk:
                print("  Trend significance — Mann-Kendall (WARNING: assumes independence; p-values anti-conservative due to overlapping windows):")
                mannkendall_report(df, header, changepoints if use_split else None)

            dataset_results[label] = df
            dataset_cps[label] = changepoints

        all_results[dataset] = dataset_results
        all_changepoints[dataset] = dataset_cps
        if not is_lr:
            all_raw[dataset] = raw_series[dataset]

    # --- Plot + Report ---
    if all_results:
        print("\n  Plotting...")
        use_cps = run_pelt or run_minimax or run_fisher or bool(split_dates)
        # For vod-all, exclude the legacy "VOD" (Cannonsville) series from the
        # combined plot — the 10 water-supply catchments are the focus there.
        plot_results_input = (
            {k: v for k, v in all_results.items() if k != "VOD"}
            if args.data == "vod-all" else all_results
        )
        png_path = run_out_dir / f"{base_name}.png"
        plot_results(
            plot_results_input, analyses,
            png_path,
            all_changepoints=all_changepoints if use_cps else None,
            show_summary=use_cps,
        )
        generate_report(
            png_path.with_suffix(".md"),
            run_params,
            all_results,
            all_changepoints if use_cps else {},
            n_surrogates,
            sig_method,
        )

        # --- vod-all: additional multi-site paper figures ---
        if args.data == "vod-all":
            print("\n  Generating multi-site VOD figures...")
            plot_raw_vod(
                all_raw,
                run_out_dir / f"raw_vod_{params_suffix}.png",
            )
            plot_vod_multisite(
                all_results, analyses,
                run_out_dir / f"vod_multisite_{params_suffix}.png",
                all_changepoints=all_changepoints if use_cps else None,
            )
            plot_significance_heatmap(
                all_results, analyses,
                run_out_dir / f"vod_significance_{params_suffix}.png",
                n_surrogates=n_surrogates,
            )
            plot_vod_tac_grid(
                all_results,
                run_out_dir / f"vod_tac_grid_{params_suffix}.png",
            )
            # Split-focused paper figures (only generated when changepoints were used)
            if use_cps:
                for met in analyses:
                    plot_vod_split_grid(
                        all_results, met,
                        run_out_dir / f"vod_split_grid_{met}_{params_suffix}.png",
                        all_changepoints=all_changepoints,
                        n_surrogates=min(n_surrogates, 500),
                    )
                plot_tac_heatmap(
                    all_results,
                    run_out_dir / f"vod_tac_heatmap_{params_suffix}.png",
                    metric="TAC",
                )
                plot_tac_changepoint_bars(
                    all_results,
                    run_out_dir / f"vod_changepoint_bars_{params_suffix}.png",
                    all_changepoints=all_changepoints,
                    metric="TAC",
                )
                plot_tac_pre_post_scatter(
                    all_results,
                    run_out_dir / f"vod_prepost_scatter_{params_suffix}.png",
                    all_changepoints=all_changepoints,
                    metric="TAC",
                )

        # For ensembled L-Range datasets, also save each model's (and the
        # ensemble mean's) own single-series plot/report, matching its CSV's
        # filename. The mean's plot is always just the bare image — no
        # trend/significance panel and no changepoint markers — since the
        # mean isn't independently meaningful for trend testing the way each
        # individual model is; per-model plots show trends when changepoints
        # are enabled, same as the combined plot.
        for dataset, label_dfs in all_results.items():
            if len(label_dfs) <= 1:
                continue
            cps_by_label = all_changepoints.get(dataset, {})
            for label, df in label_dfs.items():
                indiv_name = f"{dataset}_{label}_{params_suffix}"
                indiv_png = run_out_dir / f"{indiv_name}.png"
                indiv_results = {dataset: {label: df}}
                is_mean = label == "mean"
                indiv_cps = None if is_mean else {dataset: {label: cps_by_label.get(label, {})}}
                plot_results(
                    indiv_results, analyses,
                    indiv_png,
                    all_changepoints=(indiv_cps if (use_cps and not is_mean) else None),
                    show_summary=(use_cps and not is_mean),
                )
                generate_report(
                    indiv_png.with_suffix(".md"),
                    run_params,
                    indiv_results,
                    (indiv_cps if (use_cps and not is_mean) else {}),
                    n_surrogates,
                    sig_method,
                )

    print("\nDone.")


if __name__ == "__main__":
    main()
