#!/usr/bin/env python3
"""
compare_outputs.py

Overlay two csd_analysis.py output CSVs (TAC + Var columns) over their
overlapping years, save a combined comparison plot, and report Pearson/
Spearman correlation between the two TAC curves and the two Var curves.

Also overlays the underlying *raw* monthly values of two datasets (before
any windowing/de-trending) and quantifies how similar they are via Pearson
and Spearman correlation, both on the raw values and on STL-deseasonalized
anomalies (the latter strips out the shared annual cycle, which otherwise
dominates a raw correlation between any two vegetation time series).
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

import csd_analysis as csd

OUT_DIR = Path(__file__).parent / "output" / "comparisons"


def load(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["centre_date"], index_col="centre_date")
    return df


def compare(csv_a: Path, label_a: str, csv_b: Path, label_b: str, out_name: str) -> None:
    df_a = load(csv_a)
    df_b = load(csv_b)

    start = max(df_a.index.min(), df_b.index.min())
    end = min(df_a.index.max(), df_b.index.max())
    df_a = df_a[(df_a.index >= start) & (df_a.index <= end)]
    df_b = df_b[(df_b.index >= start) & (df_b.index <= end)]

    metrics = [m for m in ("TAC", "Var") if m in df_a.columns and m in df_b.columns]

    fig, axes = plt.subplots(len(metrics), 1, figsize=(9, 4 * len(metrics)), squeeze=False)
    titles = {"TAC": "Lag-1 TAC", "Var": "Normalized Variance"}

    print(f"  {label_a} vs {label_b}:")
    for i, metric in enumerate(metrics):
        ax = axes[i, 0]
        ax.plot(df_a.index, df_a[metric], marker="o", markersize=4, label=label_a, color="#1f77b4")
        ax.plot(df_b.index, df_b[metric], marker="o", markersize=4, label=label_b, color="#d62728")

        # Correlation between the two indicator curves over their shared centre dates.
        # Window centre dates may not line up exactly if window/step settings differ
        # between the two runs, so align on the index intersection rather than
        # assuming a 1:1 row correspondence.
        paired = pd.concat([df_a[metric].rename("a"), df_b[metric].rename("b")], axis=1).dropna()
        if len(paired) >= 4:
            r, p = pearsonr(paired["a"], paired["b"])
            rho, p_rho = spearmanr(paired["a"], paired["b"])
            sig = " *" if p < 0.05 else ""
            metric_title = (
                f"{titles.get(metric, metric)} — "
                f"r={r:+.3f}{sig} (p={p:.3f}), ρ={rho:+.3f} (p={p_rho:.3f}), n={len(paired)}"
            )
            print(
                f"    {metric} (n={len(paired)}): Pearson r={r:+.3f} (p={p:.3f}), "
                f"Spearman rho={rho:+.3f} (p={p_rho:.3f})"
            )
        else:
            metric_title = f"{titles.get(metric, metric)} — too few overlapping windows (n={len(paired)})"
            print(f"    {metric}: too few overlapping windows (n={len(paired)})")

        ax.set_title(metric_title, fontsize=10)
        ax.set_xlabel("Centre date")
        ax.set_ylabel(metric)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(fontsize=9)

    fig.suptitle(f"{label_a} vs {label_b} — overlapping years ({start.strftime('%Y')}–{end.strftime('%Y')})")
    fig.tight_layout()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / out_name
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def load_lr_ensemble_mean(loader, name: str) -> pd.Series:
    """
    Average a raw L-Range monthly series (e.g. csd.load_lai_lr) across all 5
    GCMs, matching the cross-GCM mean csd_analysis.py builds internally for
    `--model mean` / `--model all`.
    """
    series_list = [
        loader(csd.LRANGE_ALL_DIR / model_dir)
        for model_dir in csd.LRANGE_MODELS.values()
    ]
    combined = pd.concat(series_list, axis=1)
    mean_series = combined.mean(axis=1, skipna=True)
    mean_series.name = name
    return mean_series


def compare_raw(series_a: pd.Series, label_a: str, series_b: pd.Series, label_b: str, out_name: str) -> None:
    """
    Overlay the raw monthly values of two datasets (dual y-axes, since the
    two are generally in different units/scales) and quantify how similar
    they are with two correlation measures over their overlapping months:

      - Pearson r / Spearman rho on the raw values — easy to interpret but
        inflated by any shared seasonal cycle (both datasets being high in
        summer and low in winter will correlate well regardless of whether
        their year-to-year behavior tracks at all).
      - Pearson r on STL-deseasonalized anomalies — removes the shared
        annual cycle and trend, isolating whether the inter-annual /
        residual variability actually co-varies. This is the more honest
        answer to "do these two datasets track the same underlying signal."
    """
    df = pd.concat([series_a.rename("a"), series_b.rename("b")], axis=1).dropna()
    if len(df) < 4:
        print(f"  {label_a} vs {label_b}: too few overlapping months (n={len(df)}) — skipping.")
        return

    r_raw, p_raw = pearsonr(df["a"], df["b"])
    rho_raw, p_rho = spearmanr(df["a"], df["b"])

    if csd._HAS_STL:
        anom_a = csd.compute_stl_residuals(series_a)
        anom_b = csd.compute_stl_residuals(series_b)
        df_anom = pd.concat([anom_a.rename("a"), anom_b.rename("b")], axis=1).dropna()
        if len(df_anom) >= 4:
            r_anom, p_anom = pearsonr(df_anom["a"], df_anom["b"])
            n_anom = len(df_anom)
        else:
            r_anom, p_anom, n_anom = np.nan, np.nan, len(df_anom)
    else:
        r_anom, p_anom, n_anom = np.nan, np.nan, 0

    fig, ax1 = plt.subplots(figsize=(10, 4.5))
    ax1.plot(series_a.index, series_a.values, color="#1f77b4", linewidth=1.2, label=label_a)
    ax1.set_ylabel(label_a, color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")
    ax1.grid(True, linestyle="--", alpha=0.4)

    ax2 = ax1.twinx()
    ax2.plot(series_b.index, series_b.values, color="#d62728", linewidth=1.2, label=label_b)
    ax2.set_ylabel(label_b, color="#d62728")
    ax2.tick_params(axis="y", labelcolor="#d62728")

    ax1.set_xlim(df.index.min(), df.index.max())
    ax1.set_xlabel("Date")

    sig_raw = " *" if p_raw < 0.05 else ""
    sig_anom = " *" if (not np.isnan(p_anom) and p_anom < 0.05) else ""
    anom_str = (
        f"deseasonalized r={r_anom:+.3f}{sig_anom} (p={p_anom:.3f}, n={n_anom})"
        if not np.isnan(r_anom) else "deseasonalized r=n/a"
    )
    title = (
        f"{label_a} vs {label_b} — raw monthly values (n={len(df)})\n"
        f"Pearson r={r_raw:+.3f}{sig_raw} (p={p_raw:.3f}), "
        f"Spearman ρ={rho_raw:+.3f} (p={p_rho:.3f}) | {anom_str}"
    )
    ax1.set_title(title, fontsize=10)
    fig.tight_layout()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / out_name
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")
    print(
        f"  {label_a} vs {label_b} (raw, n={len(df)}): "
        f"Pearson r={r_raw:+.3f} (p={p_raw:.3f}), Spearman rho={rho_raw:+.3f} (p={p_rho:.3f}), "
        f"{anom_str}"
    )


def main() -> None:
    base = Path(__file__).parent / "output"

    compare(
        base / "LAI_GIMMS" / "LAI_GIMMS_step12_stl_nosplit_nsurr1000.csv", "LAI_GIMMS",
        base / "LAI_GCM" / "LAI_GCM_mean_step12_stl_nosplit_nsurr1000.csv", "LAI_GCM_mean",
        "LAI_GIMMS_vs_LAI_GCM_mean.png",
    )
    compare(
        base / "VOD" / "VOD_step12_stl_nosplit_nsurr1000.csv", "VOD",
        base / "Biomass_GCM" / "Biomass_GCM_mean_step12_stl_nosplit_nsurr1000.csv", "Biomass_GCM_mean",
        "VOD_vs_Biomass_GCM_mean.png",
    )

    # --- Raw monthly value comparisons (same dataset pairs, before windowing/de-trending) ---
    compare_raw(
        csd.load_lai_gimms(), "LAI_GIMMS",
        load_lr_ensemble_mean(csd.load_lai_lr, "LAI_GCM_mean"), "LAI_GCM_mean",
        "LAI_GIMMS_vs_LAI_GCM_mean_raw.png",
    )
    compare_raw(
        csd.load_vod(), "VOD",
        load_lr_ensemble_mean(csd.load_biomass_lr, "Biomass_GCM_mean"), "Biomass_GCM_mean",
        "VOD_vs_Biomass_GCM_mean_raw.png",
    )


if __name__ == "__main__":
    main()
