# Collector Contract

All collectors return a `pandas.DataFrame` with this schema:

```text
source
term
term_type
term_weight
title
url
published_at
collected_at
views
likes
comments
engagements
author
snippet
raw_payload
```

## Dedupe

Primary key:

```text
source + url
```

Fallback:

```text
source + title + published_at
```

## Data Modes

- `real`: call real collectors. Missing API keys or API errors should fail clearly.
- `sample`: call sample collectors. The UI must label the result as sample data.

Do not silently fall back from real to sample.
