# TS Methodology

## TS Score

TS Score is the final summary score for the selected analysis period.

TS_v1 components:

- `growth_score`: recent growth in weighted mentions
- `reaction_score`: engagement pressure
- `saturation_score`: peak retention and saturation
- `decline_risk`: recent decline risk

Initial formula:

```text
ts_score =
  growth_score * 0.38
  + reaction_score * 0.32
  + saturation_score * 0.18
  + (100 - decline_risk) * 0.12
```

## Trend Index

Trend Index is not TS Score. It is a chart-facing 0-100 daily series calculated from mentions, weighted mentions, views, and engagements.

API naming:

```text
charts.trend_index_series
```

Do not use `charts.ts_series`.
