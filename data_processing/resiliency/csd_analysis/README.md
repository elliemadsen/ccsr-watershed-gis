# Ecosystem Resilience Indicators — Proposed Approach

Analysis of Critical Slowing Down (CSD) indicators for the Cannonsville Watershed using
lag-1 temporal autocorrelation (TAC) and variance computed within a sliding window.

---

## Datasets

### LAI_MODIS (Leaf Area Index — MODIS)

- **Source:** MODIS baseline observations (`data/L-Range/MODIS_baseline_obs/LAI/`)
- **Format:** Monthly raster grids (`.asc`), one file per month
- **Period:** January 2006 – December 2020 (180 months total)
- **Spatial summary:** Watershed-mean (spatial mean over all valid pixels)

### LAI_GIMMS (Leaf Area Index — GIMMS LAI3g)

- **Source:** GIMMS LAI3g (`data/LAI/raw_data/processed_monthly/`), monthly GeoTIFFs
- **Derivation:** Generated from GIMMS NDVI3g (1/12° resolution) using a neural network trained on MODIS LAI. See Zhu et al. (2013), _Remote Sensing_, 5(2), 927–948. doi:10.3390/rs5020927; and Pinzon & Tucker (2014), _Remote Sensing_, 6, 6929–6960. doi:10.3390/rs6076929 for the underlying NDVI3g dataset.
- **Period:** January 1982 – December 2011 (360 months)
- **Spatial summary:** Watershed-mean over valid pixels

### LAI_spliced (Leaf Area Index — GIMMS + MODIS)

- **Source (pre-2006):** GIMMS LAI3g (`data/LAI/raw_data/processed_monthly/`), monthly GeoTIFFs
- **Source (2006–2020):** MODIS (same as above)
- **Period:** January 1982 – December 2020 (~468 months)
- **Splice point:** 2006-01. GIMMS provides 1982–2005; MODIS provides 2006 onward.
- **Current method:** Direct concatenation — no bias correction applied. Absolute LAI values differ between sensors; any mean offset persists (STL detrending absorbs much of it).
- **Spatial summary:** Watershed-mean over valid pixels

### VOD (Vegetation Optical Depth — Cannonsville, NY)

- **Source:** VODCA CX+Ku band (`data/VOD/VODCA_CXKu_Cannonsville.csv`)
- **Format:** Daily time series, pre-averaged over the watershed boundary
- **Period:** July 1987 – December 2021 (~12,500 daily rows)
- **Spatial extent:** −75.38 to −74.55°W, 42.06 to 42.46°N
- **Spatial summary:** Watershed-mean (spatial mean over all valid pixels)
- **Missingness:** ~46% of daily values are NaN; median ~18 valid observations per month.
- **Temporal aggregation:** daily VOD is resampled to calendar-month means. Only valid (non-NaN) daily values contribute to the monthly mean.
  A minimum of 10 valid daily observations is required to accept a monthly value;
  months with fewer valid obs are set to NaN and treated as missing in following steps.

### VOD_VT (Vegetation Optical Depth — Green Mtns, VT)

- **Source:** VODCA CX+Ku band (`data/VOD/VODCA_CXKu_VT.csv`)
- **Format:** Daily time series, pre-averaged over the catchment boundary
- **Period:** July 1987 – December 2021
- **Center:** −72.75°W, 44.25°N; **Bounding box:** −73.0 to −72.4°W, 44.0 to 44.5°N
- **Temporal aggregation:** same as VOD (monthly means, min 10 obs/month)

### VOD_ME (Vegetation Optical Depth — Sebago, ME)

- **Source:** VODCA CX+Ku band (`data/VOD/VODCA_CXKu_ME.csv`)
- **Format:** Daily time series, pre-averaged over the catchment boundary
- **Period:** July 1987 – December 2021
- **Center:** −70.56°W, 43.85°N; **Bounding box:** −70.85 to −70.25°W, 43.65 to 44.05°N
- **Temporal aggregation:** same as VOD (monthly means, min 10 obs/month)

### VOD_MA (Vegetation Optical Depth — Quabbin, MA)

- **Source:** VODCA CX+Ku band (`data/VOD/VODCA_CXKu_MA.csv`)
- **Format:** Daily time series, pre-averaged over the catchment boundary
- **Period:** July 1987 – December 2021
- **Center:** −72.33°W, 42.33°N; **Bounding box:** −72.55 to −72.10°W, 42.20 to 42.50°N
- **Temporal aggregation:** same as VOD (monthly means, min 10 obs/month)

### Biomass_GCM (Total Aboveground Live Biomass — L-Range)

- **Source:** L-Range (localized G-Range) model output, SSP3-7.0 scenario (`data/L-Range/{MODEL}/talb__1_M_YYYY_avg_cells.asc`)
- **GCM ensemble:** 5 GCMs are available — `ACCESS` (ACCESS-ESM1-5), `CMCC` (CMCC-ESM2), `CNRM` (CNRM-CM6-1), `INM` (INM-CM5-0), `IPSL` (IPSL-CM6A-LR), all under SSP3-7.0. Select with `--model`; default `all` runs every GCM. See "GCM ensemble" below.
- **Format:** Monthly raster grids (`.asc`, 340×225 cells, 200 m resolution), one file per month
- **Period:** January 1990 – December 2065 (912 months)
- **Spatial summary:** Watershed-mean over valid pixels. The L-Range domain rectangle extends beyond the watershed boundary; cells outside the watershed are filled with `0.0` rather than `NODATA_value` (matching the convention used in the model's own `*_zones.txt` summaries). Both `NODATA_value` (-9999) and the `0.0` padding are excluded from the spatial mean.

### LAI_1_GCM / LAI_2_GCM / LAI_3_GCM / LAI_GCM (Leaf Area Index — L-Range)

- **Source:** Same L-Range run(s) as Biomass_GCM (`data/L-Range/{MODEL}/lai___{layer}_M_YYYY_avg_cells.asc`), same 5-GCM ensemble
- **Layers:** L-Range reports LAI per plant functional type: `LAI_1_GCM` = herbs, `LAI_2_GCM` = shrubs, `LAI_3_GCM` = trees. `LAI_GCM` = total canopy LAI, the sum of all three layers (a month is only summed if all three layers have a valid value for that month).
- **Period:** January 1990 – December 2065 (912 months)
- **Spatial summary:** Watershed-mean over valid pixels, same `0.0`-padding exclusion as Biomass_GCM.

### GCM ensemble (`--model`)

The five `*_GCM` datasets are each available across 5 CMIP6 GCMs (all forced with SSP3-7.0), stored as sibling directories under `data/L-Range/`. `--model` selects which to use — ignored for non-LR datasets (`LAI_MODIS`, `LAI_GIMMS`, `LAI_spliced`, `VOD`), which have no GCM dimension.

- **`--model all` (default):** runs all 5 GCMs independently — each gets its own load → de-trend → normalize → sliding window → changepoint search → significance test pipeline — then overlays all six (5 GCMs + the ensemble mean, see below) as separate colored lines on one plot per dataset/metric, with a shared legend. Each model's CSV, console output, and `.md` report section are kept separate (see "Output filenames" below); only the top-level plot and report combine them.
- **`--model {ACCESS,CMCC,CNRM,INM,IPSL}`:** runs a single GCM, ~5x faster, no ensemble overlay.
- **Ensemble mean ("mean"):** when `--model all`, a 6th series is built by averaging the raw monthly vegetation-state series across the 5 GCMs (date-aligned, skipping any model missing a given month) _before_ de-trending, then running it through the identical pipeline. This is deliberately done on the raw state, not on the final TAC/Var curves — averaging raw vegetation state suppresses each GCM's own internal/chaotic variability and isolates the multi-model forced-response signal, whereas averaging already-computed TAC values afterward wouldn't have a well-defined interpretation (TAC of a mean ≠ mean of TACs). Plotted as a thick black line to distinguish it from the individual GCM lines; saved as `..._{DATASET}_mean.csv`.
- Each individual GCM's CSV/analysis is **not averaged or otherwise combined with the others** for its own significance testing — every model (and the "mean") gets independently de-trended, windowed, changepoint-searched, and significance-tested, so disagreement between GCMs is directly visible rather than smoothed away.

---

## Resilience Metrics

### Lag-1 Temporal Autocorrelation (TAC / AC1)

TAC is computed as the Pearson correlation between the time series and itself shifted by one
time step (lag-1). Following Boulton et al. (2022), an AR(1) model is fit by OLS within each
window, and the AR(1) coefficient $\hat{\phi}$ is taken as the indicator:

$$
\hat{\phi} = \frac{\sum_{t=1}^{N-1}(x_t - \bar{x})(x_{t+1} - \bar{x})}{\sum_{t=1}^{N-1}(x_t - \bar{x})^2}
$$

where $x_t$ is the de-trended anomaly at time $t$ and $\bar{x}$ is the within-window mean.
A value of $\hat{\phi}$ approaching 1 indicates slower recovery from perturbations,
suggesting CSD and reduced resilience.

### Variance

Rolling variance within each window:

$$
\sigma^2 = \frac{1}{N-1} \sum_{t=1}^{N}(x_t - \bar{x})^2
$$

Increasing variance is another CSD indicator.

**Normalization:** before the sliding window is computed, the de-trended anomaly series for
each dataset is divided by its own full-record residual standard deviation. TAC is exactly
invariant to this positive rescaling (it's a ratio of sums in matching squared units), so
trend results are unaffected. Variance, however, is in squared units of the rescaled
("normalized") anomaly, which puts every dataset on a comparable scale — without this,
Variance values are in squared native units (e.g. (g/m²)² for Biomass_GCM vs (m² m⁻¹)² for
LAI), and a dataset like Biomass_GCM with absolute values in the hundreds produces Variance
values orders of magnitude larger than LAI's, even though neither is more "variable" in any
meaningful sense. Only the trend/direction of each dataset's own Variance series over time —
not cross-dataset magnitude comparisons of the raw value — should be interpreted as a CSD signal.

---

## De-trending

Raw LAI and VOD time series are dominated by the seasonal cycle. Computing TAC on the
raw series would bias $\hat{\phi}$ strongly upward, conflating phenological patterns with
resilience dynamics.

**Default method: STL (Seasonal-Trend Decomposition by Loess)**

Following Boulton et al. (2022) and Smith et al. (2022), we apply STL decomposition
(`statsmodels.tsa.seasonal.STL`, equivalent to R's `stl()` with `s.window='periodic'`).
STL simultaneously removes the long-term trend _and_ the repeating seasonal cycle,
leaving only the residual for CSD analysis:

$$
x'_{t} = x_{t} - T_{t} - S_{t}
$$

where $T_t$ is the locally-smooth trend component and $S_t$ is the seasonal component.
The residual $x'_t$ has no systematic seasonal pattern and no long-term trend, isolating
the irregularity that CSD theory predicts should grow near a tipping point. STL is
preferred over climatology subtraction because it adapts to a non-stationary trend and to
a slowly shifting seasonal cycle (e.g., earlier spring green-up).

**Requires `statsmodels`.** If it's not installed, `--detrend stl` (the default) raises
a `RuntimeError` rather than silently falling back to climatology — climatology subtraction
doesn't remove the inter-annual trend, so a silent fallback would produce different
numbers while every filename and the run-parameters table still said `stl`, corrupting the
record of what was actually run. Install it (`pip install statsmodels` in the active
environment) or pass `--detrend climatology` explicitly if you really want that method.

**Legacy method: monthly climatology subtraction**

Available via `--detrend climatology`. For each calendar month $m$, the climatological mean
$\mu_m$ computed over a fixed reference period is subtracted:

$$
x'_{t} = x_{t} - \mu_m \quad \text{where } m = \text{month}(t)
$$

This removes the seasonal cycle but not the inter-annual trend, so any monotonic change in
the raw series will be present in the anomalies. Reference periods:

| Dataset     | Climatology period      |
| ----------- | ----------------------- |
| VOD         | 1987–2021 (full record) |
| VOD_VT      | 1987–2021 (full record) |
| VOD_ME      | 1987–2021 (full record) |
| VOD_MA      | 1987–2021 (full record) |
| LAI_MODIS   | 2006–2020 (15-yr)       |
| LAI_GIMMS   | 1982–2011 (full record) |
| LAI_spliced | 1982–2020 (full record) |
| Biomass_GCM | 1990–2065 (full record) |
| LAI_1_GCM   | 1990–2065 (full record) |
| LAI_2_GCM   | 1990–2065 (full record) |
| LAI_3_GCM   | 1990–2065 (full record) |
| LAI_GCM     | 1990–2065 (full record) |

---

## Sliding Window

Both metrics are computed within a 5-year sliding window stepped 6 or 12 months, producing a time series of each indicator. This follows Boulton et al. (2022) and Smith et al. (2022).

### Window parameters

| Parameter     | LAI_MODIS (monthly) | VOD (daily → monthly) |
| ------------- | ------------------- | --------------------- |
| Window length | 60 months (5 yr)    | 60 months (5 yr)      |
| Step size     | 6 or 12 months      | 6 or 12 months        |
| Window label  | Centre month        | Centre month          |

**Resulting output time series (step=12):**

| Dataset     | First window      | Last window       | Centre years | # windows |
| ----------- | ----------------- | ----------------- | ------------ | --------- |
| LAI_MODIS   | 2006-01 – 2010-12 | 2016-01 – 2020-12 | 2008–2018    | 11        |
| LAI_GIMMS   | 1982-01 – 1986-12 | 2007-01 – 2011-12 | 1984–2009    | 26        |
| LAI_spliced | 1982-01 – 1986-12 | 2016-01 – 2020-12 | 1984–2018    | 35        |
| VOD         | 1987-07 – 1992-06 | 2017-01 – 2021-12 | ~1990–2019   | ~29       |

---

## Python Implementation Plan

### Script flags (CLI)

```
python csd_analysis.py [--data {LAI_MODIS,LAI_GIMMS,LAI_spliced,VOD,VOD_VT,VOD_ME,VOD_MA,Biomass_GCM,LAI_1_GCM,LAI_2_GCM,LAI_3_GCM,LAI_GCM,all}] [--analysis {TAC,Var,all}]
                       [--model {ACCESS,CMCC,CNRM,INM,IPSL,all}]
                       [--detrend {stl,climatology}] [--n-surrogates N]
                       [--step {6,12}] [--significance {surrogate,mk,both}]
                       [--changepoint {PELT[:K],minimax-p[:K],fisher-p[:K],YYYY-MM[,YYYY-MM...]}]
```

| Flag                          | Choices                                                                                                                | Default     | Description                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--data`                      | `LAI_MODIS`, `LAI_GIMMS`, `LAI_spliced`, `VOD`, `VOD_VT`, `VOD_ME`, `VOD_MA`, `Biomass_GCM`, `LAI_1_GCM`, `LAI_2_GCM`, `LAI_3_GCM`, `LAI_GCM`, `all` | `all`       | Dataset(s) to process. `VOD` = Cannonsville NY; `VOD_VT` = Green Mtns VT; `VOD_ME` = Sebago ME; `VOD_MA` = Quabbin MA. `LAI_spliced` concatenates GIMMS (1982–2005) with MODIS (2006–2020) without bias correction. `LAI_GCM` sums the three L-Range PFT layers (herbs/shrubs/trees) into total canopy LAI.                                                                                                                 |
| `--model`                     | `ACCESS`, `CMCC`, `CNRM`, `INM`, `IPSL`, `all`                                                                         | `all`       | GCM(s) for `*_GCM` datasets only — ignored otherwise. `all` runs the 5-GCM ensemble and overlays all five on one plot per dataset/metric; a single model runs ~5x faster with no overlay.                                                                                                                                                                                                                                    |
| `--analysis`                  | `TAC`, `Var`, `all`                                                                                                    | `all`       | Indicator(s) to compute                                                                                                                                                                                                                                                                                                                                                                                                      |
| `--detrend`                   | `stl`, `climatology`                                                                                                   | `stl`       | De-trending method. `stl` matches Boulton/Smith; `climatology` subtracts long-term monthly means                                                                                                                                                                                                                                                                                                                             |
| `--n-surrogates`              | integer                                                                                                                | `1000`      | Number of phase-shuffled surrogates for significance testing. Boulton used 100,000; 1,000 is sufficient for exploration                                                                                                                                                                                                                                                                                                      |
| `--step`                      | `6`, `12`                                                                                                              | `12`        | Sliding window step in months. Use `6` for a smoother curve; note adjacent windows share 59/60 months so output is not independent samples                                                                                                                                                                                                                                                                                   |
| `--significance`              | `surrogate`, `mk`, `both`                                                                                              | `surrogate` | Significance testing method. `surrogate` uses phase-shuffled Fourier surrogates (accounts for serial correlation); `mk` uses standard Mann-Kendall (assumes independence); `both` runs and prints both                                                                                                                                                                                                                       |
| `--changepoint PELT`          | —                                                                                                                      | off         | Run ruptures PELT changepoint detection (RBF cost, BIC-equivalent penalty). PELT picks both the number and location of breaks itself — may find 0, 1, or several.                                                                                                                                                                                                                                                            |
| `--changepoint PELT:K`        | integer K ≥ 2                                                                                                          | off         | Force exactly K segments (K−1 breaks) using ruptures **Binary Segmentation** instead of PELT's penalty-driven search. Use this when plain `PELT` doesn't return as many breaks as you want.                                                                                                                                                                                                                                  |
| `--changepoint minimax-p`     | —                                                                                                                      | off         | Scan all candidate single-split dates (2 segments) and pick the one minimising the WORST (max) Kendall τ p-value across both segments — i.e. the split where the least-significant half is as significant as possible. Stricter than a sum-of-p objective, since it rejects splits where one half "carries" the significance for both.                                                                                       |
| `--changepoint minimax-p:K`   | integer K ≥ 2                                                                                                          | off         | Generalizes the above to a K-way partition (K−1 changepoints), solved via dynamic programming: minimise the worst p-value across all K segments. A data-driven middle ground between PELT and manual visual inspection.                                                                                                                                                                                                      |
| `--changepoint fisher-p`      | —                                                                                                                      | off         | Scan all candidate single-split dates (2 segments) and pick the one minimising the PRODUCT of the segment p-values (Fisher's method for combining p-values) — the opposite trade-off from `minimax-p`: a product is dominated by its smallest factors, so e.g. p=[0.01, 0.9] beats p=[0.2, 0.2], rewarding a split with one extremely significant segment even if the other isn't significant at all.                        |
| `--changepoint fisher-p:K`    | integer K ≥ 2                                                                                                          | off         | Generalizes the above to a K-way partition, solved via the same dynamic-programming structure as `minimax-p:K` but maximising the summed Fisher statistic (`-Σlog(p_i)`) instead of minimising the worst p-value. Prefers a couple of extremely significant segments over several mediocre ones — use this instead of `minimax-p` when you'd rather have 2 of 3 segments strongly significant and one bad than all 3 medium. |
| `--changepoint YYYY-MM[,...]` | date string(s)                                                                                                         | —           | Manually fix one or more split dates (e.g. `--changepoint 2003-01` or `--changepoint 2003-01,2015-06` for two splits / three segments).                                                                                                                                                                                                                                                                                      |

The `--changepoint` modes are mutually exclusive — it takes a single value, with optional `:K` suffix for `PELT`/`minimax-p`/`fisher-p` or comma-separated dates for manual splits.

**All output for a run is written under `output/{DATA}/`**, where `{DATA}` is exactly
the `--data` value (e.g. `output/Biomass_GCM/`, `output/all/`).

Within that directory, filenames encode every other input parameter:

Per-(dataset, model) CSV — always produced, one per L-Range model actually run
(including `mean` when ensembled), or one per non-LR dataset:

```
{DATASET}_{MODEL}_step{STEP}_{DETREND}_{SPLIT}_nsurr{N}.csv   ← L-Range dataset (model name always present, even for a single explicit --model)
{DATASET}_step{STEP}_{DETREND}_{SPLIT}_nsurr{N}.csv           ← non-LR dataset (no model dimension)
```

Top-level combined plot + report — one per run, overlaying every model selected for
each dataset (see "GCM ensemble" above):

```
{NAME}_step{STEP}_{DETREND}_{SPLIT}_nsurr{N}.png
{NAME}_step{STEP}_{DETREND}_{SPLIT}_nsurr{N}.md   ← report
```

`{NAME}` is `{DATASET}_{MODEL}` only when the whole run is a single L-Range dataset
with a single explicit `--model` (e.g. `--data Biomass_GCM --model ACCESS` →
`Biomass_GCM_ACCESS_...`, matching its own CSV exactly — one set of 3 files total, all
identically named, just different extensions). Otherwise `{NAME}` is just `{DATASET}`
(an ensemble of models combined into one overlay plot) or `all` (multiple datasets via
`--data all`).

**When ensembled (`--model all`), each individual model — and the `mean` series — also
gets its own single-series plot + report**, in addition to the combined overlay, using
the same name as its CSV (`{DATASET}_{MODEL}_step{STEP}_..._nsurr{N}.png`/`.md`). So a
`--model all` run on one dataset produces 6 individual CSV+PNG+MD triples (5 GCMs + mean)
plus one combined overlay PNG+MD — 19 files total.

`{SPLIT}` is `nosplit`, `PELT`, `PELTn{K}` (Binseg-forced), `minimaxp`, `minimaxpn{K}`,
`fisherp`, `fisherpn{K}`, or `split{YYYYMM}[_{YYYYMM}...]` depending on the `--changepoint`
mode used.

A Markdown report (same base name as the `.png`, `.md` extension) is written alongside every run, containing a parameter table and a significance-results table (τ, p per dataset × metric × period).

### Method choices and comparison with Boulton et al. (2022) and Smith et al. (2022)

**De-trending:**
We now use **STL (Seasonal-Trend Decomposition by Loess)** as the default, matching
Boulton et al. and Smith et al., who used R's `stl()` with a 'periodic' seasonal window.
STL simultaneously removes a slowly varying long-term trend _and_ the seasonal cycle,
keeping only the residual. Boulton et al. specifically note robustness to varying the
trend window. Monthly climatology subtraction is retained as a legacy option
(`--detrend climatology`).

**TAC computation:**
We use the OLS AR(1) coefficient via the formula in `Boulton_2022/functions.R` (equivalent
to Pearson lag-1 correlation on a zero-mean series). Boulton et al. used the same `ar.ols`
approach in R. Smith et al. computed Pearson AC1 directly. All three are mathematically
equivalent for lag-1 on a zero-mean residual series.

**Variance:**
All studies use sample variance of the residuals within each rolling window.

**Window length:**
All three use a **5-year (60-month) sliding window**. Boulton et al. note their results
are robust to varying window length.

**Trend statistic:**
All studies use **Kendall's τ** (rank correlation coefficient) to quantify the monotonic
tendency in the indicator time series. We use `pymannkendall`, which computes the standard
Mann-Kendall test (equivalent to Kendall's τ with a two-sided p-value).

**Trend significance:**
We use **phase-surrogate Kendall τ tests**, matching Boulton et al. (100,000 surrogates)
and Smith et al. (10,000 surrogates). The procedure: (1) FFT of the indicator series;
(2) randomly permute the Fourier phases while preserving the DC component (and Nyquist
for even-length series) so that the inverse FFT is real-valued; (3) compute Kendall τ
for each surrogate; (4) p-value = fraction of surrogates with τ ≥ observed τ (one-sided,
testing for a positive — resilience-loss — trend). Because phase shuffling preserves the
power spectral density and hence (by the Wiener–Khinchin theorem) the autocorrelation
function, the null distribution correctly accounts for serial correlation from overlapping
windows. The default is 1,000 surrogates (`--n-surrogates 1000`); increase to 10,000 or
100,000 for final reporting. Standard Mann-Kendall results (via `pymannkendall`) are also
printed for comparison, but their p-values are anti-conservative when windows overlap and
should not be used as primary evidence.

**Period splitting:**
Neither Boulton et al. nor Smith et al. used automated changepoint detection. Boulton et
al. report both full-period (1991–2016) and **2003-onwards** Kendall τ values, where 2003
was chosen by visual inspection of when resilience loss becomes most apparent. Smith et al.
compared **1992–2017**, **1992–2004**, and **2004–2017** as fixed periods. Four approaches
are available:

- `--changepoint PELT[:K]`: ruptures PELT (or Binseg if `:K` is given) — objective but
  optimises a distributional cost on the raw indicator, not trend significance; may miss
  gradual slope changes. Plain `PELT` lets the penalty decide the number of breaks (often
  0 or 1 in practice); `PELT:K` forces exactly K segments via Binary Segmentation.
- `--changepoint YYYY-MM[,...]`: fixed manual split(s) — transparent and reproducible; use
  `--changepoint 2003-01` to match Boulton or `--changepoint 2004-01` to match Smith. Comma-
  separate multiple dates for more than one manual split.
- `--changepoint minimax-p[:K]`: scans all candidate K-segment partitions (default K=2, a
  single split) and selects the one minimising the WORST (max) Kendall τ p-value across all
  segments, via dynamic programming. More objective than visual inspection while remaining
  directly tied to the trend-significance question. Minimizing the max specifically targets
  partitions where every segment is individually significant — but as a result it actively
  _prefers_ several mediocre segments (e.g. p=[0.2, 0.2, 0.2]) over a partition with a couple
  of extremely significant segments and one bad one (e.g. p=[0.01, 0.01, 0.9], rejected here
  because its max, 0.9, is worse). If that's not the trade-off you want, use `fisher-p`.
- `--changepoint fisher-p[:K]`: same DP search structure as `minimax-p[:K]`, but minimises
  the PRODUCT of the segment p-values (Fisher's method for combining independent p-values,
  equivalent to maximising `-Σlog(p_i)`) instead of the worst one. A product is dominated by
  its smallest factors, so it picks the _opposite_ partition from the example above —
  p=[0.01, 0.01, 0.9] (product ≈9e-5) beats p=[0.2, 0.2, 0.2] (product 8e-3). Use this when
  you'd rather have most segments strongly significant even if one isn't significant at all,
  rather than every segment landing in a mediocre middle ground.

**Multi-segment caveat (multiple comparisons):** `minimax-p:K`, `fisher-p:K`, and `PELT:K`
search over many more candidate partitions as K grows, which inflates the chance of finding a
significant-looking split purely by chance — the search itself is not corrected for this.
Treat a multi-segment result as a data-driven hypothesis to confirm with a fixed
`--changepoint YYYY-MM,...` run and independent reasoning about why a break should exist
there (e.g. a known forcing change), not as a formally-tested partition. This caveat already
existed for the single-split case but is more important as K increases.

### Processing steps (pseudocode outline)

```
1. Load data
   - LAI_MODIS: glob lai__YYYY_MM.asc → rasterio → spatial mean → pd.Series (monthly index)
   - LAI_GIMMS: glob gimms_lai3g_YYYY_MM.tif → rasterio → spatial mean → pd.Series
   - LAI_spliced: GIMMS pre-2006 + MODIS 2006– concatenated
   - VOD / VOD_VT / VOD_ME / VOD_MA: read CSV → parse dates → resample to monthly mean (min 10 obs/month)
   - Biomass_GCM: glob talb__1_M_YYYY_avg_cells.asc → rasterio → spatial mean
     (excluding NODATA and 0.0 domain-padding cells) → pd.Series
   - LAI_1_GCM / LAI_2_GCM / LAI_3_GCM: glob lai___{layer}_M_YYYY_avg_cells.asc per layer → same spatial mean
   - LAI_GCM: sum of LAI_1_GCM + LAI_2_GCM + LAI_3_GCM (months require all three layers valid)

2. De-trend
   - Compute monthly climatology over reference period (or STL trend+seasonal, default)
   - Subtract → anomaly/residual series

2b. Normalize
   - Divide the residual series by its own full-record std, so Variance is on a
     comparable scale across datasets (TAC is unaffected — see "Normalization" above)

3. Sliding window loop (step = 12 months)
   for each window start in range(0, N - window_len + 1, 12):
       segment = anomaly[start : start + window_len]
       drop NaN from segment
       if len(segment) < min_obs: continue
       TAC[window] = AR1_OLS(segment).params  # statsmodels AutoReg
       Var[window] = segment.var(ddof=1)

4. Output
   - pd.DataFrame with DatetimeIndex (centre month), columns: [TAC, Var]
   - Save to CSV; plot indicator curves

5. Changepoint detection
   - --changepoint PELT: fit ruptures PELT with RBF cost; the BIC-equivalent penalty
     (pen=log(n)) picks both the number and location of breaks — may return zero,
     one, or several, unlike the original implementation which only ever reported
     the first break found.
   - --changepoint PELT:K: same RBF cost, but via ruptures Binary Segmentation
     with a forced n_bkps=K-1, for when PELT's penalty doesn't return as many
     breaks as wanted.
   - --changepoint minimax-p[:K]: dynamic-programming search over all K-segment
     partitions, minimising the worst per-segment Kendall tau p-value (K=2 default).
     Does not have PELT's "gradual slope change" blind spot, since it directly
     searches for trend-significant splits rather than distributional breaks —
     e.g. it recovers the LAI TAC upward shift from ~2013 that PELT misses.
   - --changepoint fisher-p[:K]: same DP structure as minimax-p[:K], but maximises
     the summed Fisher statistic (-Σlog(p_i)) instead of minimising the worst
     p-value — i.e. minimises the product of segment p-values. Prefers a couple
     of extremely significant segments over several mediocre ones, the opposite
     trade-off from minimax-p.
   - All three return a (possibly empty) list of changepoint Timestamps per
     indicator column; N changepoints partition the record into N+1 segments,
     each independently trend-tested.

6. Trend test (Mann-Kendall)
   - Full record: pymannkendall.original_test(indicator_series)
   - If changepoints found: also run MK separately on each of the N+1 segments
   - If no --changepoint requested: split at temporal midpoint and run MK on each half
   - Report n, Kendall's tau, p-value, Sen's slope for each period
   Note: with a 60-month window, step=12 gives 80% overlap between adjacent windows
   and step=6 gives 90% overlap. In both cases the indicator values are serially
   correlated, which violates MK's independence assumption. MK p-values are
   anti-conservative at any step size — use phase-surrogate results for reporting.
```

### Minimum observations threshold

For valid window estimates: require at least **30 non-NaN observations** within the
60-month window (50% completeness). Tighter thresholds can be tested.

---

## Results

All results below use STL detrending (`--detrend stl`, the default), a 60-month window
stepped every 6 months (`--step 6`), with changepoint detection (`--changepoint`) and
5,000 phase-surrogate significance tests (`--n-surrogates 5000`). This gives 21 windows
for LAI (centre dates 2008–2018) and 60 windows for VOD (centre dates 1989–2018).

Output files: `output/results_{LAI,VOD}_step6_stl_changepoint.csv`,
`output/resilience_indicators_step6_stl_changepoint.png`

---

### VOD — no significant monotonic trend with STL residuals

| Indicator | Period                       | n   | Kendall τ | p (surrogate) | Trend    |
| --------- | ---------------------------- | --- | --------- | ------------- | -------- |
| TAC       | Full record (1989–2018)      | 60  | −0.080    | 0.629         | no trend |
| TAC       | Before 2000-01 (changepoint) | 20  | +0.189    | 0.338         | no trend |
| TAC       | From 2000-01 onwards         | 40  | +0.118    | 0.352         | no trend |
| Var       | Full record                  | 60  | −0.156    | 0.829         | no trend |
| Var       | Before 2012-06 (changepoint) | 45  | +0.087    | 0.341         | no trend |
| Var       | From 2012-06 onwards         | 15  | +0.067    | 0.366         | no trend |

**Interpretation:** After STL detrending, no significant monotonic trend in VOD TAC or
Variance survives the phase-surrogate test. This is in contrast to the climatology-based
results, where both indicators showed strong split trends. The difference arises because
STL removes the inter-annual trend component from VOD before analysis. Any long-term
monotonic change in mean VOD (which constitutes a trend in the raw series) is absorbed
into the STL trend component and is not present in the residuals. The CSD signal measured
here is therefore the autocorrelation structure of short-term irregularity around the
long-term trajectory — arguably the more precise quantity for resilience inference, as it
is not confounded with the baseline trend.

---

### LAI — significant TAC increase in second half (post-2013) survives phase-surrogate test

| Indicator | Period                       | n   | Kendall τ | p (surrogate) | Trend          |
| --------- | ---------------------------- | --- | --------- | ------------- | -------------- |
| TAC       | Full record (2008–2018)      | 21  | −0.238    | 0.691         | no trend       |
| TAC       | Before 2013-06 (changepoint) | 10  | −0.467    | 0.891         | no trend       |
| TAC       | From 2013-06 onwards         | 11  | +0.782    | 0.003 ★       | **increasing** |
| Var       | Full record                  | 21  | +0.171    | 0.387         | no trend       |
| Var       | Before 2015-12 (changepoint) | 15  | −0.410    | 0.915         | no trend       |
| Var       | From 2015-12 onwards         | 6   | +0.067    | 0.459         | no trend       |

★ p < 0.05

**Interpretation:** The LAI TAC second-half trend (τ = +0.782, p = 0.003) is the only
result that survives phase-surrogate significance testing. Notably, PELT now detects a
changepoint in LAI TAC at 2013-06 (with STL residuals), which was absent in the
climatology-based run. The 11-window post-2013 period shows strong and significant
monotonic growth in TAC, consistent with declining resilience. Variance results are
not significant under the stricter surrogate test, suggesting those patterns may have
been artefacts of the climatology-based residuals.

---

### Caveats

1. **STL removes the inter-annual trend.** The phase-surrogate test detects structure in
   _short-term irregularity_ around the long-term trajectory. If resilience loss manifests
   as a slow monotonic shift in baseline autocorrelation rather than irregular fluctuations,
   STL residuals may understate the signal. This is why Boulton et al. and Smith et al.
   also report full-period (non-split) Kendall τ on the STL residuals.

2. **Full-record tests can mask reversals.** For VOD (where a non-monotonic trajectory is
   plausible), the split analysis is more informative than the full-record result. None of
   the VOD split tests are significant after phase-surrogate correction.

3. **Small n for sub-period tests.** The LAI pre-2013 sub-period has n = 10 windows;
   the VOD pre-2000 sub-period has n = 20. Phase-surrogate tests remain valid at small n
   but have low power. Interpret non-significant small-n results with caution.

4. **LAI record length.** 15 years / 21 windows is marginal. The post-2013 LAI TAC result
   is encouraging but should be confirmed with a longer record.

---

## References

Boulton, C. A., Lenton, T. M., & Boers, N. (2022). Pronounced loss of Amazon rainforest
resilience since the early 2000s. _Nature Climate Change_, 12, 271–278.
https://doi.org/10.1038/s41558-022-01287-8

Smith, T., et al. (2022). Reliability of resilience estimation based on multi-instrument
time series. _Nature Climate Change_, 12, 1098–1104.
https://doi.org/10.1038/s41558-022-01352-2
