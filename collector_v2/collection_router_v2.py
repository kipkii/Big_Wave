import sys
from pathlib import Path

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from naver_blog_collector_v2 import collect_naver_blog
from naver_news_collector_v2 import collect_naver_news
from storage_v2 import make_run_id, save_raw_all, save_raw_result, save_run_meta
from youtube_collector_v2 import collect_youtube


DEFAULT_SOURCES = ["youtube", "naver_news", "naver_blog"]
DEFAULT_LIMITS = {
    "youtube": 50,
    "naver_news": 300,
    "naver_blog": 300,
}

PROJECT_ROOT = CURRENT_DIR.parent
RAW_ROOT = PROJECT_ROOT / "data" / "raw"


def single_term_keyword_set(keyword):
    return {
        "keyword_set": {
            "canonical": keyword,
            "alias": [],
            "typo": [],
            "related": [],
        },
        "keyword_set_mode": "single_term_fallback",
        "terms": [
            {"term": keyword, "term_type": "canonical", "term_weight": 1.0},
        ],
        "core_terms": [keyword],
        "expansion_terms": [],
    }


def run_collection(keyword_set, sources=None, days=30, limits=None, run_id=None):
    sources = sources or DEFAULT_SOURCES
    limits = {**DEFAULT_LIMITS, **(limits or {})}
    canonical_keyword = keyword_set["keyword_set"]["canonical"]
    run_id = run_id or make_run_id(canonical_keyword)

    collectors = {
        "youtube": lambda: collect_youtube(keyword_set, days=days, limit=limits["youtube"]),
        "naver_news": lambda: collect_naver_news(keyword_set, limit=limits["naver_news"]),
        "naver_blog": lambda: collect_naver_blog(keyword_set, limit=limits["naver_blog"]),
    }

    source_frames = []
    saved_files = {}
    errors = {}
    fallback_sources = {}

    for source in sources:
        if source not in collectors:
            errors[source] = "unknown source"
            continue

        try:
            print(f"\ncollecting {source}...")
            df = collectors[source]()
            source_frames.append(df)
            saved_files[source] = str(save_raw_result(df, source, run_id))
            print(f"{source} rows: {len(df)}")
        except Exception as exc:
            if source == "youtube":
                fallback = load_cached_source(source, canonical_keyword, days=days, exclude_run_id=run_id)
                if fallback is not None:
                    df, fallback_run_id = fallback
                    source_frames.append(df)
                    saved_files[source] = str(save_raw_result(df, source, run_id))
                    fallback_sources[source] = {
                        "from_run_id": fallback_run_id,
                        "reason": str(exc),
                    }
                    print(f"{source} failed: {exc}")
                    print(f"{source} cache fallback rows: {len(df)} from {fallback_run_id}")
                    continue

            errors[source] = str(exc)
            print(f"{source} failed: {exc}")

    raw_all, raw_all_path = save_raw_all(source_frames, run_id)
    saved_files["raw_all"] = str(raw_all_path)

    meta_path = save_run_meta(
        run_id,
        {
            "keyword": canonical_keyword,
            "keyword_set": keyword_set.get("keyword_set", {}),
            "keyword_set_mode": keyword_set.get("keyword_set_mode"),
            "terms": keyword_set.get("terms", []),
            "sources": sources,
            "days": days,
            "limits": limits,
            "saved_files": saved_files,
            "errors": errors,
            "fallback_sources": fallback_sources,
        },
    )

    return {
        "run_id": run_id,
        "raw_all": raw_all,
        "saved_files": saved_files,
        "run_meta": str(meta_path),
        "errors": errors,
        "fallback_sources": fallback_sources,
    }


def load_cached_source(source, canonical_keyword, days=30, exclude_run_id=None):
    if not RAW_ROOT.exists():
        return None

    for run_dir in sorted(RAW_ROOT.glob("run_*"), key=lambda path: path.stat().st_mtime, reverse=True):
        if exclude_run_id and run_dir.name == exclude_run_id:
            continue

        source_path = run_dir / f"{source}.csv"
        if not source_path.exists():
            continue

        try:
            df = pd.read_csv(source_path)
        except Exception:
            continue

        if df.empty:
            continue
        if "canonical_keyword" in df.columns:
            df = df[df["canonical_keyword"].astype(str) == str(canonical_keyword)]
        if df.empty:
            continue

        if "published_at" in df.columns and days:
            parsed = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
            if parsed.notna().any():
                max_date = parsed.max()
                cutoff = max_date - pd.Timedelta(days=days - 1)
                df = df[parsed >= cutoff]

        if not df.empty:
            return df.reset_index(drop=True), run_dir.name

    return None


def parse_sources(raw):
    if not raw.strip():
        return DEFAULT_SOURCES
    return [item.strip() for item in raw.split(",") if item.strip()]


def main():
    keyword = input("keyword: ").strip()
    sources = parse_sources(input("sources comma separated (default all): "))
    days_raw = input("days (default 30): ").strip()
    youtube_limit_raw = input("youtube limit per term (default 250): ").strip()
    news_limit_raw = input("naver_news limit per term (default 100): ").strip()
    blog_limit_raw = input("naver_blog limit per term (default 100): ").strip()

    days = int(days_raw) if days_raw else 30
    limits = {
        "youtube": int(youtube_limit_raw) if youtube_limit_raw else 250,
        "naver_news": int(news_limit_raw) if news_limit_raw else 100,
        "naver_blog": int(blog_limit_raw) if blog_limit_raw else 100,
    }

    result = run_collection(
        keyword_set=single_term_keyword_set(keyword),
        sources=sources,
        days=days,
        limits=limits,
    )

    print("\nrun_id:", result["run_id"])
    print("raw_all rows:", len(result["raw_all"]))
    print("run_meta:", result["run_meta"])
    for source, path in result["saved_files"].items():
        print(f"{source}: {path}")
    if result["errors"]:
        print("errors:", result["errors"])


if __name__ == "__main__":
    main()
