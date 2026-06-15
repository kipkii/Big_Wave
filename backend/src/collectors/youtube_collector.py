from datetime import UTC, date, datetime, timedelta
import argparse
import json
import os
from pathlib import Path
import sys

import pandas as pd

LOCAL_YOUTUBE_API_KEY = ""
LOCAL_YOUTUBE_API_KEYS = []

try:
    from .contract import ensure_raw_schema
except ImportError:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from src.collectors.contract import ensure_raw_schema
    except Exception:
        RAW_COLUMNS = [
            "source",
            "term",
            "term_type",
            "term_weight",
            "title",
            "url",
            "published_at",
            "collected_at",
            "views",
            "likes",
            "comments",
            "engagements",
            "author",
            "snippet",
            "raw_payload",
        ]

        def ensure_raw_schema(df):
            for column in RAW_COLUMNS:
                if column not in df:
                    df[column] = None
            return df[RAW_COLUMNS]


def collect_youtube_terms(
    terms: list[dict],
    start_date,
    end_date,
    limit_per_term: int = 20,
    api_key: str | None = None,
) -> pd.DataFrame:
    api_keys = [api_key] if api_key else _get_youtube_api_keys()
    api_keys = [key.strip() for key in api_keys if key and key.strip()]
    if not api_keys:
        raise RuntimeError("YOUTUBE_API_KEY is required for real youtube collection")

    last_error = None
    for index, candidate_key in enumerate(api_keys, start=1):
        try:
            return _collect_youtube_terms_with_key(
                terms=terms,
                start_date=start_date,
                end_date=end_date,
                limit_per_term=limit_per_term,
                api_key=candidate_key,
            )
        except Exception as exc:
            last_error = exc
            if api_key or not _is_retryable_key_error(exc):
                raise
            print(f"YouTube API key #{index} failed; trying next key.")

    raise RuntimeError("All configured YouTube API keys failed") from last_error


def _collect_youtube_terms_with_key(
    terms: list[dict],
    start_date,
    end_date,
    limit_per_term: int,
    api_key: str,
) -> pd.DataFrame:
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("google-api-python-client is required") from exc

    youtube = build("youtube", "v3", developerKey=api_key)
    rows = []
    collected_at = datetime.now(UTC).isoformat()

    for term_item in terms:
        next_page_token = None
        fetched = 0
        while fetched < limit_per_term:
            response = (
                youtube.search()
                .list(
                    q=term_item["term"],
                    part="snippet",
                    maxResults=min(50, limit_per_term - fetched),
                    type="video",
                    order="viewCount",
                    pageToken=next_page_token,
                    publishedAfter=f"{start_date.isoformat()}T00:00:00Z",
                    publishedBefore=f"{end_date.isoformat()}T23:59:59Z",
                )
                .execute()
            )

            video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
            if not video_ids:
                break

            stats_response = (
                youtube.videos()
                .list(part="snippet,statistics", id=",".join(video_ids))
                .execute()
            )
            for item in stats_response.get("items", []):
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                views = int(stats.get("viewCount", 0))
                likes = int(stats.get("likeCount", 0))
                comments = int(stats.get("commentCount", 0))
                rows.append(
                    {
                        "source": "youtube",
                        "term": term_item["term"],
                        "term_type": term_item["term_type"],
                        "term_weight": term_item["term_weight"],
                        "title": snippet.get("title", ""),
                        "url": f"https://www.youtube.com/watch?v={item.get('id')}",
                        "published_at": snippet.get("publishedAt"),
                        "collected_at": collected_at,
                        "views": views,
                        "likes": likes,
                        "comments": comments,
                        "engagements": likes + comments,
                        "author": snippet.get("channelTitle"),
                        "snippet": snippet.get("description", ""),
                        "raw_payload": json.dumps(item, ensure_ascii=False),
                    }
                )

            fetched += len(video_ids)
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

    return ensure_raw_schema(pd.DataFrame(rows))


def _get_youtube_api_keys() -> list[str]:
    keys = []

    if LOCAL_YOUTUBE_API_KEY.strip():
        keys.append(LOCAL_YOUTUBE_API_KEY.strip())
    keys.extend(str(key).strip() for key in LOCAL_YOUTUBE_API_KEYS if str(key).strip())

    try:
        from local_youtube_key import YOUTUBE_API_KEY as local_key

        if str(local_key).strip():
            keys.append(str(local_key).strip())
    except Exception:
        pass

    try:
        from local_youtube_key import YOUTUBE_API_KEYS as local_keys

        keys.extend(str(key).strip() for key in local_keys if str(key).strip())
    except Exception:
        pass

    env_key = os.getenv("YOUTUBE_API_KEY")
    if env_key:
        keys.append(env_key.strip())

    env_keys = os.getenv("YOUTUBE_API_KEYS")
    if env_keys:
        keys.extend(key.strip() for key in env_keys.split(",") if key.strip())

    deduped = []
    for key in keys:
        if key not in deduped:
            deduped.append(key)
    return deduped


def _is_retryable_key_error(exc: Exception) -> bool:
    try:
        from googleapiclient.errors import HttpError
    except ImportError:
        HttpError = ()

    if HttpError and isinstance(exc, HttpError):
        status = getattr(exc.resp, "status", None)
        return status in {400, 401, 403, 429}

    message = str(exc).lower()
    retry_markers = [
        "api key",
        "keyinvalid",
        "quota",
        "daily limit",
        "access not configured",
        "forbidden",
    ]
    return any(marker in message for marker in retry_markers)


def _single_term(term: str) -> list[dict]:
    return [{"term": term, "term_type": "canonical", "term_weight": 1.0}]


def _print_preview(df: pd.DataFrame) -> None:
    if df.empty:
        print("수집 결과가 없습니다.")
        return

    preview_columns = ["source", "term", "title", "url", "published_at", "views", "likes", "comments"]
    preview = df[preview_columns].head(10).copy()
    print(f"\n수집 rows: {len(df)}")
    print(preview.to_string(index=False))


def _load_env_for_script() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    current = Path(__file__).resolve()
    candidates = [Path.cwd() / ".env"]
    for parent in current.parents:
        candidates.append(parent / ".env")
    for path in candidates:
        if path.exists():
            load_dotenv(path)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")

    _load_env_for_script()

    parser = argparse.ArgumentParser(description="Run the BigWave YouTube collector directly.")
    parser.add_argument("--keyword", help="Search keyword. If omitted, interactive input is used.")
    parser.add_argument("--days", type=int, default=None, help="Relative period in days. Default: 30")
    parser.add_argument("--limit", type=int, default=None, help="Number of videos to collect. Default: 5")
    parser.add_argument("--api-key", default=None, help="YouTube API key. Env YOUTUBE_API_KEY is used if omitted.")
    parser.add_argument("--save", action="store_true", help="Save output CSV without asking.")
    parser.add_argument("--output", default=None, help="CSV output path. Used with --save.")
    args = parser.parse_args()

    print("BigWave YouTube Collector")
    if args.keyword:
        keyword = args.keyword.strip()
    else:
        try:
            keyword = input("Enter keyword: ").strip()
        except EOFError:
            print("No interactive input is available. Run with --keyword, for example:")
            print("python backend\\src\\collectors\\youtube_collector.py --keyword \"두쫀쿠\" --days 30 --limit 5")
            return

    if not keyword:
        print("Keyword is empty.")
        return

    if args.days is not None:
        days = args.days
    else:
        days_raw = input("Period days (default 30): ").strip()
        days = int(days_raw) if days_raw else 30

    if args.limit is not None:
        limit = args.limit
    else:
        limit_raw = input("Result limit (default 5): ").strip()
        limit = int(limit_raw) if limit_raw else 5

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    print(f"\nRun options: keyword={keyword}, period={start_date}~{end_date}, limit={limit}")
    df = collect_youtube_terms(
        terms=_single_term(keyword),
        start_date=start_date,
        end_date=end_date,
        limit_per_term=limit,
        api_key=args.api_key,
    )
    _print_preview(df)

    if args.save:
        save_raw = "y"
    else:
        try:
            save_raw = input("\nSave CSV? (y/N): ").strip().lower()
        except EOFError:
            save_raw = "n"

    if save_raw == "y":
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = Path.cwd() / "exports"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"youtube_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
