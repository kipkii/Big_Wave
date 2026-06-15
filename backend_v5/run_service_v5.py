from pathlib import Path
import sys

# 프로젝트 경로 설정
PROJECT_ROOT = Path(__file__).resolve().parents[1]
for path in [PROJECT_ROOT, PROJECT_ROOT / "collector_v2"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# 💡 필수 라이브러리 및 엔진 임포트 (이 부분이 누락되어 에러 발생)
from analyzer_v5 import run_e3_analysis
from collector_v2.collection_router_v2 import run_collection
from keyword_v2 import get_demo_keywords, resolve_keyword
from .e1_keyword_resolver import generate_keyword_set_via_llm
from .utils import auto_filter_noise

RAW_ROOT = PROJECT_ROOT / "data" / "raw"
RESULTS_ROOT = PROJECT_ROOT / "data" / "results"

def list_keywords() -> list[dict]:
    return get_demo_keywords()

def get_keyword_set(keyword: str, include_related: bool = True) -> dict:
    return resolve_keyword(keyword, include_related=include_related)

def run_full_analysis(
    keyword: str,
    sources: list[str],
    analysis_days: int,
    collection_days: int,
    include_related: bool,
    trend_type: str = "F&B", 
    limits: dict[str, int] | None = None,
    save: bool = True,
    strict_mode: bool = True  # 💡 [핵심] strict_mode 추가
) -> dict:
    
    # 1. 키워드 세트 준비
    if strict_mode:
        # LLM을 타지 않고 입력 키워드만 고정하여 수집 (팬덤 오염 원천 차단)
        print(f"🔒 [Strict Mode] '{keyword}' 키워드만 사용하여 데이터를 수집합니다.")
        keyword_set = {
            "keyword": keyword,
            "keyword_set": {
                "canonical": keyword,
                "terms": [{"term": keyword, "term_type": "canonical", "term_weight": 1.0}]
            }
        }
    else:
        # 기존 LLM 확장 모드
        try:
            print(f"🤖 LLM으로 '{keyword}' 연관 키워드를 확장 중...")
            keyword_set = generate_keyword_set_via_llm(keyword)
        except Exception as e:
            print(f"⚠️ LLM 확장 실패: {e}")
            keyword_set = resolve_keyword(keyword, include_related=include_related)

    # 2. 수집 실행
    collection_result = run_collection(
        keyword_set=keyword_set,
        sources=sources,
        days=collection_days,
        limits=limits or {},
    )
    
    # 3. 데이터 정제 (Auto-Filtering)
    import pandas as pd
    for source in sources:
        file_path = RAW_ROOT / collection_result["run_id"] / f"{source}.csv"
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                # 정제 로직 실행
                df_filtered = auto_filter_noise(df, keyword)
                df_filtered.to_csv(file_path, index=False)
                print(f"✅ [{source}] 정제 완료: {len(df)} -> {len(df_filtered)} 행")
            except Exception as e:
                print(f"⚠️ [{source}] 정제 오류: {e}")

    # 4. 분석 실행
    run_dir = RAW_ROOT / collection_result["run_id"]
    dashboard_data = run_e3_analysis(
        run_dir=str(run_dir),
        selected_sources=sources,
        analysis_days=analysis_days,
        include_related=include_related,
        trend_type=trend_type, 
        save=save,
    )
    
    dashboard_data["collection"] = summarize_collection(collection_result)
    return dashboard_data

def reanalyze_run(
    run_id: str,
    selected_sources: list[str] | None,
    analysis_days: int,
    include_related: bool,
    trend_type: str = "F&B", 
    save: bool = True,
) -> dict:
    run_dir = resolve_run_dir(run_id)
    return run_e3_analysis(
        run_dir=str(run_dir),
        selected_sources=selected_sources,
        analysis_days=analysis_days,
        include_related=include_related,
        trend_type=trend_type,
        save=save,
    )

def recollect_run(
    keyword_set: dict,
    sources: list[str],
    analysis_days: int,
    collection_days: int,
    include_related: bool,
    trend_type: str = "F&B",
    limits: dict[str, int] | None = None,
    save: bool = True,
) -> dict:
    collection_result = run_collection(
        keyword_set=keyword_set,
        sources=sources,
        days=collection_days,
        limits=limits or {},
    )
    run_dir = RAW_ROOT / collection_result["run_id"]
    dashboard_data = run_e3_analysis(
        run_dir=str(run_dir),
        selected_sources=sources,
        analysis_days=analysis_days,
        include_related=include_related,
        trend_type=trend_type,
        save=save,
    )
    dashboard_data["collection"] = summarize_collection(collection_result)
    append_collection_warnings(dashboard_data, collection_result)
    return dashboard_data

def get_dashboard(run_id: str) -> dict:
    dashboard_path = RESULTS_ROOT / run_id / "dashboard_data.json"
    if not dashboard_path.exists():
        raise FileNotFoundError(f"dashboard_data.json not found for run_id={run_id}")
    import json
    return json.loads(dashboard_path.read_text(encoding="utf-8"))

def resolve_run_dir(run_id: str) -> Path:
    run_dir = RAW_ROOT / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"run not found: {run_id}")
    return run_dir

def summarize_collection(collection_result: dict) -> dict:
    raw_all = collection_result.get("raw_all")
    return {
        "run_id": collection_result.get("run_id"),
        "raw_rows": int(len(raw_all)) if raw_all is not None else 0,
        "saved_files": collection_result.get("saved_files", {}),
        "run_meta": collection_result.get("run_meta"),
        "errors": collection_result.get("errors", {}),
        "fallback_sources": collection_result.get("fallback_sources", {}),
    }

def append_collection_warnings(dashboard_data: dict, collection_result: dict) -> None:
    warnings = dashboard_data.setdefault("warnings", [])
    for source, detail in (collection_result.get("fallback_sources") or {}).items():
        from_run_id = detail.get("from_run_id", "")
        message = f"{source} 실시간 수집이 실패해 최근 성공한 실제 수집 데이터({from_run_id})를 재사용했습니다."
        if message not in warnings:
            warnings.append(message)
    for source, error in (collection_result.get("errors") or {}).items():
        message = f"{source} 수집 실패: {error}"
        if message not in warnings:
            warnings.append(message)