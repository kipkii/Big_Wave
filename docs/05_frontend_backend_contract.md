# Frontend Backend Contract

## POST /api/analyze

Request:

```json
{
  "keyword": "두쫀쿠",
  "sources": ["youtube", "naver_news", "naver_blog"],
  "period": { "type": "relative", "days": 30 },
  "include_related": true,
  "limit_per_term": 20,
  "data_mode": "real"
}
```

Response:

```json
{
  "keyword": "두쫀쿠",
  "analysis_run": {
    "run_id": "run_xxx",
    "keyword_set_mode": "preset",
    "sources": ["youtube"],
    "period": {
      "type": "relative",
      "days": 30,
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD"
    },
    "include_related": true,
    "data_mode": "real"
  },
  "keyword_set": {
    "canonical": "두쫀쿠",
    "alias": [],
    "typo": [],
    "related": []
  },
  "summary": {
    "ts_score": 65.7,
    "status_label": "Rising",
    "collected_items": 480,
    "last_updated": "YYYY-MM-DD"
  },
  "charts": {
    "trend_index_series": [],
    "content_series": [],
    "source_breakdown": []
  },
  "methodology": {},
  "report": {},
  "raw_preview": []
}
```
