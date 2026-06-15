from datetime import datetime, timezone
import json
from pathlib import Path
import re

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = PROJECT_ROOT / "data" / "raw"


def safe_name(value):
    value = str(value).strip()
    value = re.sub(r'[\\/:*?"<>|\\s]+', "_", value)
    return value.strip("_") or "keyword"


def make_run_id(keyword):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"run_{timestamp}_{safe_name(keyword)}"


def get_run_dir(run_id):
    run_dir = RAW_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_raw_csv(df, source, run_id):
    run_dir = get_run_dir(run_id)
    path = run_dir / f"{source}.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def save_raw_all(source_frames, run_id):
    frames = [df for df in source_frames if df is not None and not df.empty]
    raw_all = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    raw_all = dedupe_raw(raw_all)
    path = save_raw_csv(raw_all, "raw_all", run_id)
    return raw_all, path


def dedupe_raw(df):
    if df.empty:
        return df

    with_url = df[df["url"].notna() & (df["url"].astype(str) != "")]
    without_url = df.drop(with_url.index)

    deduped = []
    if not with_url.empty:
        deduped.append(with_url.drop_duplicates(subset=["source", "url"]))
    if not without_url.empty:
        deduped.append(without_url.drop_duplicates(subset=["source", "title", "published_at"]))

    return pd.concat(deduped, ignore_index=True) if deduped else df


def save_run_meta(run_id, meta):
    run_dir = get_run_dir(run_id)
    path = run_dir / "run_meta.json"
    payload = {
        **meta,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "storage_backend": "csv",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def save_raw_result(df, source, run_id, backend="csv"):
    if backend != "csv":
        raise NotImplementedError("Only csv storage is implemented in collector_v2.")
    return save_raw_csv(df, source, run_id)
