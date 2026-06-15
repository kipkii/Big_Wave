from datetime import UTC, datetime, timedelta
import hashlib

import pandas as pd

from .contract import ensure_raw_schema


def _stable_int(value: str, modulo: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulo


def collect_sample_terms(
    source: str,
    terms: list[dict],
    start_date,
    end_date,
    limit_per_term: int = 20,
) -> pd.DataFrame:
    rows = []
    collected_at = datetime.now(UTC).isoformat()
    total_days = max((end_date - start_date).days, 1)

    for term_item in terms:
        term = term_item["term"]
        base = 100 + _stable_int(f"{source}:{term}", 1200)
        for index in range(limit_per_term):
            day_offset = index % total_days
            published_at = end_date - timedelta(days=day_offset)
            views = base + (total_days - day_offset) * (3 + _stable_int(term, 9))
            likes = int(views * 0.03) if source == "youtube" else 0
            comments = int(views * 0.006) if source == "youtube" else 0
            rows.append(
                {
                    "source": source,
                    "term": term,
                    "term_type": term_item["term_type"],
                    "term_weight": term_item["term_weight"],
                    "title": f"[sample] {term} {source} item {index + 1}",
                    "url": f"https://sample.bigwave.local/{source}/{_stable_int(term + str(index), 999999)}",
                    "published_at": published_at.isoformat(),
                    "collected_at": collected_at,
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "engagements": likes + comments,
                    "author": "sample",
                    "snippet": "Sample data generated for verification.",
                    "raw_payload": "{}",
                }
            )

    return ensure_raw_schema(pd.DataFrame(rows))
