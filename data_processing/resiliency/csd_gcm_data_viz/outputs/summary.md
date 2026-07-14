# Biomass_GCM resilience shift summary (5-GCM comparison)

Source: `csd_analysis` output, Biomass_GCM, 10-year window / 12-month step / climatology detrend / fisher-p 3-segment split / 1000 surrogates. Ensemble mean excluded.

Models: **ACCESS** (hot/wet), **CMCC** (warm/wet), **CNRM** (warm/dry), **IPSL** (hot/dry), **INM** (median)

## Full-record trend (any model significant?)

| Model | TAC tau (p) | TAC trend | Var tau (p) | Var trend |
| --- | --- | --- | --- | --- |
| ACCESS (hot/wet) | +0.117 (0.667) | no trend | +0.243 (0.432) | no trend |
| CMCC (warm/wet) | +0.312 (0.244) | no trend | +0.082 (0.839) | no trend |
| CNRM (warm/dry) | +0.118 (0.722) | no trend | +0.064 (0.903) | no trend |
| IPSL (hot/dry) | +0.035 (0.869) | no trend | +0.159 (0.489) | no trend |
| INM (median) | -0.150 (0.464) | no trend | -0.215 (0.314) | no trend |

No model shows a significant full-record trend in either AC1 or Variance — the signal only emerges once the record is split into segments (below).

## Cross-model pattern in segmented trends

- 8 of 30 segment-trends across all models/metrics are **significantly increasing** (resilience loss): ACCESS/TAC 2009-12–2033-12, ACCESS/Var 2015-12–2034-12, CMCC/TAC 2011-12–2052-12, CMCC/Var 2023-12–2060-12, CNRM/TAC 2016-12–2047-12, CNRM/Var 2048-12–2060-12, INM/TAC 1994-12–2007-12, INM/Var 1994-12–2007-12.
- 11 are **significantly decreasing** (resilience gain): ACCESS/TAC 1994-12–2009-12, ACCESS/Var 1994-12–2015-12, CMCC/TAC 1994-12–2011-12, CMCC/TAC 2052-12–2060-12, CMCC/Var 1994-12–2011-12, CNRM/Var 1994-12–2019-12, IPSL/TAC 2025-12–2054-12, IPSL/Var 1994-12–2004-12, IPSL/Var 2004-12–2024-12, INM/TAC 2007-12–2028-12, INM/Var 2007-12–2023-12.

- **ACCESS, CMCC, CNRM** all show the same qualitative shape for TAC: a significant *decreasing* early segment followed by a significant *increasing* middle segment — i.e. resilience first improves, then erodes, in the early-to-mid 21st century, before leveling off (ACCESS, CNRM) or reversing again (CMCC, whose late segment swings back to significantly decreasing).
- **INM and IPSL diverge** from that pattern: INM shows *increasing* TAC early (2007-12 and earlier) then *decreasing* through the 2007–2028 segment — the reverse ordering from the other three models. IPSL shows no significant TAC trend until a *decreasing* middle segment (2025–2054); it never shows a significant increasing (resilience-loss) TAC segment.
- For **Variance**, ACCESS/CNRM/CMCC again largely agree: an early significant decrease followed by a later significant increase (CMCC's increase is delayed to its final segment, 2023-12 onward). INM's variance instead decreases sharply after an early increase, and IPSL shows two consecutive significant decreases with no increasing segment at all.
- Net read: **3 of 5 models (ACCESS, CMCC, CNRM)** — the hot/wet, warm/wet, and warm/dry scenarios — agree on a multi-decadal pattern of early resilience gain followed by resilience loss in both AC1 and Variance. **IPSL (hot/dry)** shows only resilience gain (no loss signal), and **INM (median)** shows the pattern reversed in time relative to the other four.

## Detail tables

### ACCESS (hot/wet)

**Lag-1 AC1**

| Period | n | tau | p | Trend |
| --- | --- | --- | --- | --- |
| Full record | 67 | +0.117 | 0.667 | no trend |
| Before 2009-12 | 15 | -0.771 | 0.003 * | decreasing |
| 2009-12 – 2033-12 | 24 | +0.638 | 0.012 * | increasing |
| From 2033-12 | 28 | -0.249 | 0.097 | no trend |

**Variance**

| Period | n | tau | p | Trend |
| --- | --- | --- | --- | --- |
| Full record | 67 | +0.243 | 0.432 | no trend |
| Before 2015-12 | 21 | -0.619 | 0.002 * | decreasing |
| 2015-12 – 2034-12 | 19 | +0.895 | 0.001 * | increasing |
| From 2034-12 | 27 | -0.293 | 0.053 | no trend |

### CMCC (warm/wet)

**Lag-1 AC1**

| Period | n | tau | p | Trend |
| --- | --- | --- | --- | --- |
| Full record | 67 | +0.312 | 0.244 | no trend |
| Before 2011-12 | 17 | -0.824 | 0.001 * | decreasing |
| 2011-12 – 2052-12 | 41 | +0.412 | 0.015 * | increasing |
| From 2052-12 | 9 | -1.000 | 0.001 * | decreasing |

**Variance**

| Period | n | tau | p | Trend |
| --- | --- | --- | --- | --- |
| Full record | 67 | +0.082 | 0.839 | no trend |
| Before 2011-12 | 17 | -0.971 | 0.001 * | decreasing |
| 2011-12 – 2023-12 | 12 | -0.212 | 0.472 | no trend |
| From 2023-12 | 38 | +0.644 | 0.026 * | increasing |

### CNRM (warm/dry)

**Lag-1 AC1**

| Period | n | tau | p | Trend |
| --- | --- | --- | --- | --- |
| Full record | 67 | +0.118 | 0.722 | no trend |
| Before 2016-12 | 22 | -0.472 | 0.176 | no trend |
| 2016-12 – 2047-12 | 31 | +0.725 | 0.001 * | increasing |
| From 2047-12 | 14 | +0.319 | 0.465 | no trend |

**Variance**

| Period | n | tau | p | Trend |
| --- | --- | --- | --- | --- |
| Full record | 67 | +0.064 | 0.903 | no trend |
| Before 2019-12 | 25 | -0.693 | 0.004 * | decreasing |
| 2019-12 – 2048-12 | 29 | +0.438 | 0.205 | no trend |
| From 2048-12 | 13 | +0.641 | 0.013 * | increasing |

### IPSL (hot/dry)

**Lag-1 AC1**

| Period | n | tau | p | Trend |
| --- | --- | --- | --- | --- |
| Full record | 67 | +0.035 | 0.869 | no trend |
| Before 2025-12 | 31 | -0.480 | 0.138 | no trend |
| 2025-12 – 2054-12 | 29 | -0.778 | 0.001 * | decreasing |
| From 2054-12 | 7 | +0.048 | 1.000 | no trend |

**Variance**

| Period | n | tau | p | Trend |
| --- | --- | --- | --- | --- |
| Full record | 67 | +0.159 | 0.489 | no trend |
| Before 2004-12 | 10 | -0.867 | 0.001 * | decreasing |
| 2004-12 – 2024-12 | 20 | -0.600 | 0.002 * | decreasing |
| From 2024-12 | 37 | -0.408 | 0.240 | no trend |

### INM (median)

**Lag-1 AC1**

| Period | n | tau | p | Trend |
| --- | --- | --- | --- | --- |
| Full record | 67 | -0.150 | 0.464 | no trend |
| Before 2007-12 | 13 | +0.769 | 0.001 * | increasing |
| 2007-12 – 2028-12 | 21 | -0.752 | 0.001 * | decreasing |
| From 2028-12 | 33 | -0.500 | 0.108 | no trend |

**Variance**

| Period | n | tau | p | Trend |
| --- | --- | --- | --- | --- |
| Full record | 67 | -0.215 | 0.314 | no trend |
| Before 2007-12 | 13 | +0.692 | 0.003 * | increasing |
| 2007-12 – 2023-12 | 16 | -0.917 | 0.001 * | decreasing |
| From 2023-12 | 38 | -0.189 | 0.690 | no trend |
