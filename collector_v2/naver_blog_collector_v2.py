from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd
import requests

NAVER_CLIENT_ID = "799akmjBLWabHq1xjD8W"
NAVER_CLIENT_SECRET = "z2U_2bGCh5"


def normalize_keyword_input(keyword_input):
    if isinstance(keyword_input, str):
        return {
            "canonical_keyword": keyword_input,
            "keyword_set_mode": "single_term_fallback",
            "terms": [{"term": keyword_input, "term_type": "canonical", "term_weight": 1.0}],
        }

    keyword_set = keyword_input.get("keyword_set", {})
    canonical = keyword_set.get("canonical") or keyword_input.get("canonical_keyword") or ""
    terms = keyword_input.get("terms", [])
    if not terms and canonical:
        terms = [{"term": canonical, "term_type": "canonical", "term_weight": 1.0}]

    return {
        "canonical_keyword": canonical,
        "keyword_set_mode": keyword_input.get("keyword_set_mode", "preset"),
        "terms": terms,
    }


def collect_naver_blog(keyword_input, limit=100):
    resolved = normalize_keyword_input(keyword_input)
    canonical_keyword = resolved["canonical_keyword"]
    keyword_set_mode = resolved["keyword_set_mode"]
    terms = resolved["terms"]
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }

    rows = []
    collected_at = datetime.now(timezone.utc).isoformat()
    for term_item in terms:
        term = term_item["term"]
        term_type = term_item.get("term_type", "canonical")
        term_weight = float(term_item.get("term_weight", 1.0))
        fetched = 0
        start = 1

        while fetched < limit and start <= 1000:
            display = min(100, limit - fetched)
            response = requests.get(
                "https://openapi.naver.com/v1/search/blog.json",
                headers=headers,
                params={"query": term, "display": display, "start": start, "sort": "date"},
                timeout=20,
            )
            response.raise_for_status()
            items = response.json().get("items", [])
            if not items:
                break

            for item in items:
                rows.append({
                    "canonical_keyword": canonical_keyword,
                    "keyword_set_mode": keyword_set_mode,
                    "keyword": term,
                    "title": item.get("title", ""),
                    "url": item.get("link"),
                    "published_at": item.get("postdate"),
                    "description": item.get("description", ""),
                    "bloggername": item.get("bloggername"),
                    "bloggerlink": item.get("bloggerlink"),
                    "source": "naver_blog",
                    "term": term,
                    "term_type": term_type,
                    "term_weight": term_weight,
                    "collected_at": collected_at,
                    "views": 0,
                    "likes": 0,
                    "comments": 0,
                    "engagements": 0,
                    "author": item.get("bloggername"),
                    "snippet": item.get("description", ""),
                    "raw_payload": json.dumps(item, ensure_ascii=False),
                })

            fetched += len(items)
            start += len(items)
            if len(items) < display:
                break
    return pd.DataFrame(rows)


def main():
    keyword = input("keyword: ").strip()
    limit_raw = input("limit (default 100): ").strip()
    limit = int(limit_raw) if limit_raw else 100

    df = collect_naver_blog(keyword, limit)
    print("\nrows:", len(df))
    if not df.empty:
        print(df[["keyword", "title", "url", "published_at", "bloggername", "description"]].head(20))

    save = input("\nsave csv? (y/N): ").strip().lower()
    if save == "y":
        output_dir = Path(__file__).resolve().parent / "data" / "raw"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"naver_blog_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print("saved:", path)


if __name__ == "__main__":
    main()
