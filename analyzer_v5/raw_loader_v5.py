import json
from pathlib import Path
import pandas as pd

def load_run_raw(run_dir: str) -> tuple[pd.DataFrame, dict]:
    run_path = Path(run_dir)
    return pd.read_csv(run_path / "raw_all.csv"), json.loads((run_path / "run_meta.json").read_text(encoding="utf-8"))

def filter_raw(raw_df, selected_sources, analysis_days, include_related):
    filtered = raw_df.copy()
    
    # 데이터 타입 강제 변환 및 안전 처리
    filtered["published_at"] = pd.to_datetime(filtered["published_at"], errors="coerce", utc=True)
    
    if selected_sources: 
        filtered = filtered[filtered["source"].isin(selected_sources)]
    if not include_related: 
        filtered = filtered[filtered["term_type"] != "related"]
        
    if analysis_days and not filtered.empty:
        # NaT(변환 실패 날짜) 제거 후 필터링
        filtered = filtered.dropna(subset=["published_at"])
        max_date = filtered["published_at"].max()
        cutoff = max_date - pd.Timedelta(days=analysis_days - 1)
        filtered = filtered[filtered["published_at"] >= cutoff]
        
    return filtered.sort_values("published_at").reset_index(drop=True)