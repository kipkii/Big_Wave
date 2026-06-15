from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd

# Add teammate keys here. The collector tries keys in order.
YOUTUBE_API_KEYS = [
    "AIzaSyBb9yD8FnPAMAXq8L-gpuX951ZRggPJtHc",
    "AIzaSyAiIOgmEPQMYUp0xRpyqkUWxQ_hO9GDgKI",
    # "PASTE_TEAMMATE_YOUTUBE_API_KEY_HERE",
]


def get_build():
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-api-python-client"])
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    return build, HttpError


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


def collect_youtube(keyword_input, days=30, limit=250):
    build, HttpError = get_build()
    resolved = normalize_keyword_input(keyword_input)
    canonical_keyword = resolved["canonical_keyword"]
    keyword_set_mode = resolved["keyword_set_mode"]
    terms = resolved["terms"]
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    last_error = None

    for key_index, api_key in enumerate(YOUTUBE_API_KEYS, start=1):
        if not api_key or "PASTE_" in api_key:
            continue
        try:
            youtube = build("youtube", "v3", developerKey=api_key)
            rows = []
            collected_at = datetime.now(timezone.utc).isoformat()

            for term_item in terms:
                term = term_item["term"]
                term_type = term_item.get("term_type", "canonical")
                term_weight = float(term_item.get("term_weight", 1.0))
                term_rows = 0
                next_page_token = None

                while term_rows < limit:
                    search = youtube.search().list(
                        q=term,
                        part="snippet",
                        type="video",
                        order="date",
                        maxResults=min(50, limit - term_rows),
                        pageToken=next_page_token,
                        publishedAfter=f"{start_date.isoformat()}T00:00:00Z",
                        publishedBefore=f"{end_date.isoformat()}T23:59:59Z",
                    ).execute()

                    video_ids = [item["id"]["videoId"] for item in search.get("items", [])]
                    if not video_ids:
                        break

                    stats = youtube.videos().list(
                        part="snippet,statistics",
                        id=",".join(video_ids),
                    ).execute()

                    for item in stats.get("items", []):
                        snippet = item.get("snippet", {})
                        stat = item.get("statistics", {})
                        video_id = item.get("id", "")
                        view_count = int(stat.get("viewCount", 0))
                        like_count = int(stat.get("likeCount", 0))
                        comment_count = int(stat.get("commentCount", 0))
                        rows.append({
                            "canonical_keyword": canonical_keyword,
                            "keyword_set_mode": keyword_set_mode,
                            "keyword": term,
                            "video_id": video_id,
                            "title": snippet.get("title", ""),
                            "published_at": snippet.get("publishedAt"),
                            "view_count": view_count,
                            "like_count": like_count,
                            "comment_count": comment_count,
                            "url": "https://www.youtube.com/watch?v=" + video_id,
                            "source": "youtube",
                            "term": term,
                            "term_type": term_type,
                            "term_weight": term_weight,
                            "collected_at": collected_at,
                            "views": view_count,
                            "likes": like_count,
                            "comments": comment_count,
                            "engagements": like_count + comment_count,
                            "author": snippet.get("channelTitle"),
                            "snippet": snippet.get("description", ""),
                            "raw_payload": json.dumps(item, ensure_ascii=False),
                        })

                    term_rows += len(video_ids)
                    next_page_token = search.get("nextPageToken")
                    if not next_page_token:
                        break

            return pd.DataFrame(rows)
        except HttpError as exc:
            last_error = exc
            status = getattr(exc.resp, "status", None)
            if status in [400, 401, 403, 429]:
                print(f"API key #{key_index} failed. Trying next key...")
                continue
            raise

    raise RuntimeError("All YouTube API keys failed.") from last_error


def main():
    keyword = input("keyword: ").strip()
    days_raw = input("days (default 30): ").strip()
    limit_raw = input("limit (default 250): ").strip()
    days = int(days_raw) if days_raw else 30
    limit = int(limit_raw) if limit_raw else 250

    df = collect_youtube(keyword, days, limit)
    print("\nrows:", len(df))
    if not df.empty:
        print(df[["keyword", "video_id", "title", "published_at", "view_count", "like_count", "comment_count"]].head(20))

    save = input("\nsave csv? (y/N): ").strip().lower()
    if save == "y":
        output_dir = Path(__file__).resolve().parent / "data" / "raw"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"youtube_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print("saved:", path)


if __name__ == "__main__":
    main()
