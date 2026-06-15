# Data Flow

## Raw First

Collectors return raw rows using one shared schema. Raw rows are stored before scoring.

## Time-Series First

Raw rows are not passed directly into the TS engine.

```text
raw_items
-> term_daily_metrics
-> keyword_set_daily_metrics
-> feature_engineering
-> TS_v1
```

## Analysis Run

Every analysis request creates a new `analysis_run`. Changing options should not overwrite previous results.
