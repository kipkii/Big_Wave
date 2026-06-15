import pandas as pd

from .contract import ensure_raw_schema
from .naver_blog_collector import collect_naver_blog_terms
from .naver_news_collector import collect_naver_news_terms
from .sample_collector import collect_sample_terms
from .youtube_collector import collect_youtube_terms

REAL_COLLECTORS = {
    "youtube": collect_youtube_terms,
    "naver_news": collect_naver_news_terms,
    "naver_blog": collect_naver_blog_terms,
}


def collect_sources(
    sources: list[str],
    terms: list[dict],
    start_date,
    end_date,
    limit_per_term: int = 20,
    data_mode: str = "real",
) -> pd.DataFrame:
    frames = []
    for source in sources:
        if data_mode == "sample":
            frames.append(collect_sample_terms(source, terms, start_date, end_date, limit_per_term))
            continue

        collector = REAL_COLLECTORS.get(source)
        if collector is None:
            raise ValueError(f"Unsupported source: {source}")
        frames.append(collector(terms, start_date, end_date, limit_per_term))

    if not frames:
        return ensure_raw_schema(pd.DataFrame())

    raw_df = pd.concat(frames, ignore_index=True)
    if "url" in raw_df:
        raw_df = raw_df.drop_duplicates(subset=["source", "url"], keep="first")
    return ensure_raw_schema(raw_df)
