#!/usr/bin/env python3
"""
csd_analysis.py

Critical Slowing Down (CSD) indicator analysis for a VOD residual time
series. Lag-1 autocorrelation (AC-1) and variance are computed within a
sliding window over climatology-detrended VOD. Trend significance is
assessed with a phase-surrogate Kendall tau test, and the record can
optionally be partitioned into segments via a Fisher's-method
changepoint search or a manually specified split date.

Usage:
  python csd_analysis.py path/to/vod.csv --changepoint fisher-p
  python csd_analysis.py path/to/vod.csv --changepoint fisher-p:3
  python csd_analysis.py path/to/vod.csv --changepoint 2000-01
"""

import argparse
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import kendalltau

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
N_SURR = 1000                      # phase-surrogate resamples for the trend significance test
WINDOW_YEARS = 10
WINDOW_MONTHS = WINDOW_YEARS * 12
STEP_MONTHS = 12
MIN_OBS_MONTHLY = 10                # min valid daily obs required to accept a VOD monthly mean
CLIM_START, CLIM_END = 1987, 2021   # climatology baseline period

OUT_CSV = Path(__file__).parent / "csd_analysis_output.csv"

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_vod(csv_path: Path) -> pd.Series:
    """
    Read a VODCA daily CSV (columns: date, VOD_mean) and resample to
    calendar-month means. A month requires at least MIN_OBS_MONTHLY valid
    daily observations, otherwise NaN.
    """
    df = pd.read_csv(csv_path, parse_dates=["date"], index_col="date")
    daily = df["VOD_mean"]

    def _monthly_mean(x: pd.Series) -> float:
        return float(x.mean()) if x.notna().sum() >= MIN_OBS_MONTHLY else np.nan

    monthly = daily.resample("MS").agg(_monthly_mean)
    monthly.name = "VOD"
    return monthly

# ---------------------------------------------------------------------------
# De-trending: climatology residuals
# ---------------------------------------------------------------------------

def compute_residuals(series: pd.Series) -> pd.Series:
    """
    Deseasonalize by subtracting each calendar month's climatological mean,
    computed over [CLIM_START, CLIM_END]:
        x'_t = x_t - mu_m   where m = month(t)
    """
    clim_mask = (series.index.year >= CLIM_START) & (series.index.year <= CLIM_END)
    clim = series[clim_mask].groupby(series[clim_mask].index.month).mean()  # index: 1..12

    residuals = series.astype(float).copy()
    for month in range(1, 13):
        mask = series.index.month == month
        residuals[mask] = series[mask] - clim.get(month, np.nan)
    residuals.name = series.name + "_anom"
    return residuals

# ---------------------------------------------------------------------------
# Resilience metrics
# ---------------------------------------------------------------------------

def compute_tac(vals: np.ndarray) -> float:
    """
    Lag-1 autocorrelation (AC-1), Eq. X:
        phi_hat = sum_t (x_t - xbar)(x_{t+1} - xbar) / sum_t (x_t - xbar)^2
    xbar is the mean of all valid observations in the window; only pairs
    where both x_t and x_{t+1} are non-NaN contribute.
    """
    xbar = np.nanmean(vals)
    x = vals - xbar
    x_t, x_t1 = x[:-1], x[1:]
    valid = ~(np.isnan(x_t) | np.isnan(x_t1))
    x_t, x_t1 = x_t[valid], x_t1[valid]
    if len(x_t) < 2:
        return np.nan
    denom = np.sum(x_t ** 2)
    return float(np.sum(x_t * x_t1) / denom) if denom else np.nan


def compute_var(vals: np.ndarray) -> float:
    """Unbiased sample variance, Eq. X: sigma^2 = 1/(N-1) * sum_t (x_t - xbar)^2."""
    valid = vals[~np.isnan(vals)]
    return float(np.var(valid, ddof=1)) if len(valid) >= 2 else np.nan

# ---------------------------------------------------------------------------
# Sliding window
# ---------------------------------------------------------------------------

def sliding_window(residuals: pd.Series) -> pd.DataFrame:
    """
    Compute AC-1 and variance within a WINDOW_MONTHS window stepped every
    STEP_MONTHS. A window is kept only if at least half its length is valid.
    The row label is the window's centre-month timestamp.
    """
    min_obs = WINDOW_MONTHS // 2
    n = len(residuals)
    records = []
    for start in range(0, n - WINDOW_MONTHS + 1, STEP_MONTHS):
        segment = residuals.iloc[start:start + WINDOW_MONTHS]
        if int(segment.notna().sum()) < min_obs:
            continue
        centre_date = segment.index[WINDOW_MONTHS // 2 - 1]
        vals = segment.values.astype(float)
        records.append({
            "centre_date": centre_date,
            "TAC": compute_tac(vals),
            "Var": compute_var(vals),
        })
    return pd.DataFrame(records).set_index("centre_date")

# ---------------------------------------------------------------------------
# Trend significance: phase-surrogate Kendall tau test
# ---------------------------------------------------------------------------

def _kendall_tau(x: np.ndarray) -> float:
    if len(x) < 4:
        return np.nan
    tau, _ = kendalltau(np.arange(len(x)), x)
    return float(tau)


def phase_surrogate_test(series: pd.Series, rng: Optional[np.random.Generator] = None) -> dict:
    """
    Phase-surrogate Kendall tau trend test. Generates N_SURR surrogate series
    by randomizing the FFT phases of the (dropna) series — which preserves
    the power spectral density, and hence the autocorrelation and variance,
    so the null distribution correctly accounts for the serial correlation
    induced by overlapping sliding windows. The two-sided p-value is the
    fraction of surrogates with |tau| >= |observed tau|.
    """
    vals = series.dropna().values.astype(float)
    n = len(vals)
    if n < 4:
        return {"tau": np.nan, "p": np.nan, "n": n}
    rng = rng or np.random.default_rng()
    obs_tau = _kendall_tau(vals)

    fft = np.fft.rfft(vals)
    n_fft = len(fft)
    surrogate_taus = np.empty(N_SURR)
    for i in range(N_SURR):
        phases = rng.uniform(0, 2 * np.pi, n_fft)
        phases[0] = 0.0  # preserve DC phase
        if n % 2 == 0:
            phases[-1] = 0.0  # preserve Nyquist phase
        surrogate = np.fft.irfft(np.abs(fft) * np.exp(1j * phases), n=n)
        surrogate_taus[i] = _kendall_tau(surrogate)

    n_extreme = int(np.sum(np.abs(surrogate_taus) >= abs(obs_tau)))
    p = float((n_extreme + 1) / (N_SURR + 1))  # +1 continuity correction
    return {"tau": obs_tau, "p": p, "n": n}

# ---------------------------------------------------------------------------
# Fisher-p changepoint search
# ---------------------------------------------------------------------------

def fisher_split_search(series: pd.Series, n_segments: int, min_segment_windows: int = 5) -> list:
    """
    Partition `series` into n_segments contiguous segments, choosing the
    (n_segments - 1) cut points that minimise the product of the segments'
    Kendall tau p-values (Fisher's method: maximise -2 * sum(log(p_i))).

    Uses the fast analytical Kendall tau p-value purely as the search
    criterion (phase-surrogate tests are too expensive to run at every
    candidate partition); final reported significance uses
    phase_surrogate_test on the resulting segments.

    Solved via dynamic programming: O(n^2) to score every candidate segment,
    then O(n_segments * n^2) to find the optimal partition.
    """
    series = series.dropna()
    n = len(series)
    if n < n_segments * min_segment_windows:
        raise ValueError(
            f"Too few windows (n={n}) for a {n_segments}-segment fisher-p search "
            f"(need >= {n_segments * min_segment_windows})."
        )

    values = series.values.astype(float)
    eps = 1e-12

    # score[i, j] = -log(p), Fisher's per-segment contribution for candidate segment [i, j)
    score = np.full((n + 1, n + 1), -np.inf)
    for i in range(n):
        for j in range(i + min_segment_windows, n + 1):
            _, p = kendalltau(np.arange(j - i), values[i:j])
            if not np.isnan(p):
                score[i, j] = -np.log(max(p, eps))

    # dp[k, j] = best cumulative Fisher score partitioning [0, j) into k segments
    dp = np.full((n_segments + 1, n + 1), -np.inf)
    back = np.full((n_segments + 1, n + 1), -1, dtype=int)
    dp[0, 0] = 0.0
    for k in range(1, n_segments + 1):
        prev_row = dp[k - 1]
        for j in range(1, n + 1):
            best_score, best_i = -np.inf, -1
            for i in range(0, j - min_segment_windows + 1):
                if prev_row[i] == -np.inf or score[i, j] == -np.inf:
                    continue
                total = prev_row[i] + score[i, j]
                if total > best_score:
                    best_score, best_i = total, i
            dp[k, j], back[k, j] = best_score, best_i

    if dp[n_segments, n] == -np.inf:
        raise ValueError(f"No valid {n_segments}-segment partition found.")

    boundaries = []
    j = n
    for k in range(n_segments, 0, -1):
        i = back[k, j]
        if k > 1:
            boundaries.append(i)
        j = i
    boundaries.sort()
    return [series.index[b] for b in boundaries]

# ---------------------------------------------------------------------------
# Segment reporting
# ---------------------------------------------------------------------------

def _segment_bounds(cp_dates: list) -> list:
    """Turn a sorted list of changepoints into (lo, hi) bounds per segment, lo/hi=None at the ends."""
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
    return f"{lo.strftime('%Y-%m')} to {hi.strftime('%Y-%m')}"


def report_trends(df: pd.DataFrame, cp_dates: list) -> None:
    """Print the phase-surrogate Kendall tau trend test for the full record, and for each
    changepoint-bounded segment if `cp_dates` is non-empty."""
    for col in df.columns:
        print(f"\n{col} (phase-surrogate Kendall tau, n_surr={N_SURR}):")
        series = df[col]

        def _line(s: pd.Series, label: str) -> None:
            r = phase_surrogate_test(s)
            if np.isnan(r["tau"]):
                print(f"  {label}: too few points (n={r['n']})")
                return
            sig = " *" if r["p"] < 0.05 else ""
            print(f"  {label} (n={r['n']}): tau={r['tau']:+.3f}, p={r['p']:.3f}{sig}")

        _line(series, "full record")
        if cp_dates:
            for lo, hi in _segment_bounds(cp_dates):
                _line(_slice_segment(series, lo, hi), _segment_label(lo, hi))

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("vod_csv", type=Path, help="Path to a VODCA daily CSV (columns: date, VOD_mean).")
    parser.add_argument(
        "--changepoint", default=None,
        help="'fisher-p[:N]' for an N-segment (default N=2) Fisher's-method changepoint "
             "search on AC-1, or comma-separated 'YYYY-MM[,YYYY-MM...]' for manually "
             "specified split date(s). Omit for no split (full-record trend only).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    run_fisher = False
    n_segments = 2
    split_dates: list = []
    if args.changepoint is not None:
        method_part, _, k_part = args.changepoint.partition(":")
        if method_part == "fisher-p":
            run_fisher = True
            if k_part:
                n_segments = int(k_part)
                if n_segments < 2:
                    raise ValueError("--changepoint fisher-p:N requires N >= 2.")
        else:
            split_dates = sorted(pd.Timestamp(d.strip()) for d in args.changepoint.split(","))

    print(f"Loading {args.vod_csv} ...")
    monthly = load_vod(args.vod_csv)
    n_valid, n_total = int(monthly.notna().sum()), len(monthly)
    print(f"  {n_valid}/{n_total} valid monthly values "
          f"({monthly.index[0].strftime('%Y-%m')} - {monthly.index[-1].strftime('%Y-%m')})")

    residuals = compute_residuals(monthly)
    resid_std = residuals.std()
    if resid_std and not np.isnan(resid_std) and resid_std > 0:
        residuals = residuals / resid_std

    df = sliding_window(residuals)

    if run_fisher:
        cp_dates = fisher_split_search(df["TAC"], n_segments=n_segments)
        print(f"Fisher-p changepoint(s): {[d.strftime('%Y-%m') for d in cp_dates]}")
    else:
        cp_dates = split_dates

    report_trends(df, cp_dates)

    df.to_csv(OUT_CSV)
    print(f"\nSaved: {OUT_CSV}")


if __name__ == "__main__":
    main()
