# BigWave Collector V2: Local CSV Producers

These files are intentionally standalone local CSV producers.

- API keys are hardcoded at the top of each file.
- No backend package imports are required.
- Each file can be uploaded to Colab and run directly.
- Collectors do not run visualization, TS scoring, reporting, or server/database writes.
- Output CSV files preserve source-like raw columns first and BigWave common columns after that.
- Saved CSV files go to `collector_v2/data/raw/`.

Files:

- `youtube_collector_v2.py`
- `naver_news_collector_v2.py`
- `naver_blog_collector_v2.py`
- `storage_v2.py`
- `collection_router_v2.py`

Run examples:

```bash
python youtube_collector_v2.py
python naver_news_collector_v2.py
python naver_blog_collector_v2.py
python collection_router_v2.py
```

To add a teammate YouTube key, edit:

```python
YOUTUBE_API_KEYS = [
    "PRIMARY_KEY",
    "TEAMMATE_KEY",
]
```

Collector responsibility:

```text
input keyword
-> expand into term rows from E1 keyword set
-> call source API for every term
-> build raw rows
-> add BigWave common columns
-> preview rows
-> save local CSV
```

Storage policy for this stage:

```text
No remote server.
No production database.
Local CSV first.
Later analysis modules read these CSV files.
```

Default collection volume:

- YouTube: 250 videos, using `nextPageToken` in 50-item pages.
- Naver News: 100 items.
- Naver Blog: 100 items.

E1 keyword set input shape:

```python
{
    "keyword_set": {
        "canonical": "두쫀쿠",
        "alias": ["두바이 쫀득 쿠키"],
        "typo": ["두존쿠"],
        "related": ["카다이프", "피스타치오"],
    },
    "keyword_set_mode": "preset",
    "terms": [
        {"term": "두쫀쿠", "term_type": "canonical", "term_weight": 1.0},
        {"term": "두바이 쫀득 쿠키", "term_type": "alias", "term_weight": 1.0},
        {"term": "두존쿠", "term_type": "typo", "term_weight": 0.8},
        {"term": "카다이프", "term_type": "related", "term_weight": 0.3},
    ],
}
```

Every output row includes:

```text
canonical_keyword
keyword_set_mode
keyword
term
term_type
term_weight
source
```
