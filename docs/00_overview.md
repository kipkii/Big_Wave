# Overview

BigWave v2 is organized as an understandable pipeline rather than a one-off dashboard.

User input:

- keyword
- sources
- period
- include_related
- limit_per_term
- data_mode

Pipeline:

```text
Keyword Input
-> E1 Keyword Resolver
-> Collection Router
-> Channel Collectors
-> Raw Data Pool
-> Term Daily Metrics
-> Keyword Set Daily Metrics
-> Feature Engineering
-> TS Engine
-> Trend Index
-> Rule-based Report
-> API Response
-> Dashboard
```

The frontend should never treat an unregistered keyword as unsupported. It should present it as a single-term analysis.
