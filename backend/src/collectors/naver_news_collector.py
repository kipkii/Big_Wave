from datetime import UTC, datetime
import json
import os

import pandas as pd
import requests

from .contract import ensure_raw_schema


def collect_naver_news_terms(terms: list[dict], start_date, end_date, limit_per_term: int = 20) -> pd.DataFrame:
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("NAVER_CLIENT_ID and NAVER_CLIENT_SECRET are required for real naver_news collection")

    rows = []
    collected_at = datetime.now(UTC).isoformat()
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}

    for term_item in terms:
        response = requests.get(
            "https://openapi.naver.com/v1/search/news.json",
            headers=headers,
            params={"query": term_item["term"], "display": min(limit_per_term, 100), "sort": "date"},
            timeout=20,
        )
        response.raise_for_status()
        for item in response.json().get("items", []):
            rows.append(
                {
                    "source": "naver_news",
                    "term": term_item["term"],
                    "term_type": term_item["term_type"],
                    "term_weight": term_item["term_weight"],
                    "title": item.get("title", ""),
                    "url": item.get("link") or item.get("originallink"),
                    "published_at": item.get("pubDate"),
                    "collected_at": collected_at,
                    "views": 0,
                    "likes": 0,
                    "comments": 0,
                    "engagements": 0,
                    "author": None,
                    "snippet": item.get("description", ""),
                    "raw_payload": json.dumps(item, ensure_ascii=False),
                }
            )

    return ensure_raw_schema(pd.DataFrame(rows))
