# BigWave Analyzer V2: E3 Trend Analyzer

E3 starts after E2 has already collected data.

E2 produces raw CSV files. E3 reads those files and creates trend analysis outputs for the frontend.

## Role

```text
raw_all.csv
-> filter by source / period / related option
-> build time series metrics
-> build Trend Index
-> calculate temporary TS Score
-> package dashboard_data.json
```

E3 does not call collectors.

## Rerun Policy

```text
Reanalyze = E3 only
- selected_sources
- analysis_days
- include_related

Recollect = E2 -> E3
- edited keyword set
- term add/remove
- term_weight change
- source data that does not exist in the current run
```

E3 receives only `run_dir` and filter options. It never receives API keys or collector settings.

## Input

```text
bigwave_mvp_v2/data/raw/{run_id}/
  raw_all.csv
  run_meta.json
```

## Output

Processed:

```text
bigwave_mvp_v2/data/processed/{run_id}/
  filtered_raw.csv
  term_daily_metrics.csv
  keyword_set_daily_metrics.csv
  weekly_partition.csv
  trend_features.csv
```

Results:

```text
bigwave_mvp_v2/data/results/{run_id}/
  trend_index.csv
  ts_score.json
  dashboard_data.json
```

## Main Function

```python
from analyzer_v2 import run_e3_analysis

dashboard_data = run_e3_analysis(
    run_dir="bigwave_mvp_v2/data/raw/run_xxx",
    selected_sources=None,
    analysis_days=30,
    include_related=True,
    save=True,
)
```

## Filtering Policy

- Time series and period filters use `published_at`.
- Run folders and collection history use collection/execution time.
- `analysis_days` is anchored to the latest `published_at` in the filtered raw data.
- If filtered data is empty, E3 returns a valid empty dashboard instead of crashing.
- If selected sources are missing from the current run, E3 returns `missing_sources` and `warnings`; it does not collect new data.
- `include_related=False` excludes `term_type == "related"` and is handled as E3 reanalysis.

## Trend Index vs TS Score

Trend Index is a date-level chart signal.

TS Score is a period-level judgment score.

They are intentionally separate.

## TS_v1_temp

Temporary component scores:

- `growth_score`: recent Trend Index growth
- `reaction_score`: views and engagements per item
- `saturation_score`: recent level compared with peak
- `decline_risk`: peak decline and recent downward slope

Temporary formula:

```text
ts_score =
  growth_score * 0.38
  + reaction_score * 0.28
  + saturation_score * 0.20
  + (100 - decline_risk) * 0.14
```

This is a validation formula, not the final BigWave scoring model.

## Future Calibration Points

- Better normalization when YouTube views dominate Naver mentions
- More robust period comparison for sparse data
- Separate source-specific signal weights
- More explicit handling of related terms
- Better label thresholds after reviewing real cases
