# BigWave Backend V5

FastAPI bridge between the React frontend and BigWave Python engines.

## Engine Boundary

```text
E1 keyword_v2
-> E2 collector_v2
-> E3 analyzer_v5
-> dashboard_data response
```

## Run

```bash
cd bigwave_mvp_v5
uvicorn backend_v5.app:app --reload --port 8000
```

## Endpoints

```text
GET  /api/health
GET  /api/keywords
GET  /api/keyword-set/{keyword}
POST /api/analyze
POST /api/runs/{run_id}/reanalyze
POST /api/runs/{run_id}/recollect
GET  /api/runs/{run_id}/dashboard
```

## API Payload Example (V5 Update)

In V5, the core quant algorithms dynamically adapt based on the `trend_type`. When calling `POST /api/analyze`, pass the appropriate category to trigger the optimized logic (EMA windows, decay rates, etc.).

**Example Request (`POST /api/analyze`):**
```json
{
  "keyword": "오버핏 셔츠",
  "sources": [
    "youtube",
    "naver_news",
    "naver_blog"
  ],
  "analysis_days": 30,
  "collection_days": 90,
  "include_related": true,
  "trend_type": "Fashion",  // Options: "F&B" (Default, short-term meme) or "Fashion", "IT", etc.
  "save": true
}

## Rerun Policy

```text
reanalyze = E3 only
recollect = E2 -> E3 with a new run_id
```

Filter changes use reanalyze.

Keyword set edits use recollect.
