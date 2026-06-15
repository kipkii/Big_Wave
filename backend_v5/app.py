from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 💡 v5 모듈들로 import (backend_v5 폴더 기준)
from backend_v5.run_service_v5 import (
    get_dashboard,
    get_keyword_set,
    list_keywords,
    reanalyze_run,
    recollect_run,
    run_full_analysis,
)
from backend_v5.schemas_v5 import AnalyzeRequest, ReanalyzeRequest, RecollectRequest


# 💡 여기서 app 객체가 생성됩니다! (이 부분이 지워져서 났던 에러입니다)
app = FastAPI(title="BigWave MVP v5 API", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "service": "bigwave_mvp_v5"}


@app.get("/api/keywords")
def keywords() -> dict:
    return {"domain": "F&B", "keywords": list_keywords()}


@app.get("/api/keyword-set/{keyword}")
def keyword_set(keyword: str, include_related: bool = True) -> dict:
    return get_keyword_set(keyword, include_related=include_related)


# 💡 v5 동적 파라미터(trend_type) 연동 및 예외 처리 부분
@app.post("/api/analyze")
def analyze(payload: AnalyzeRequest) -> dict:
    try:
        return run_full_analysis(
            keyword=payload.keyword,
            sources=list(payload.sources),
            analysis_days=payload.analysis_days,
            collection_days=payload.collection_days,
            include_related=payload.include_related,
            trend_type=payload.trend_type,  
            limits=payload.limits,
            save=payload.save,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/runs/{run_id}/reanalyze")
def reanalyze(run_id: str, payload: ReanalyzeRequest) -> dict:
    try:
        return reanalyze_run(
            run_id=run_id,
            selected_sources=list(payload.selected_sources) if payload.selected_sources else None,
            analysis_days=payload.analysis_days,
            include_related=payload.include_related,
            trend_type=payload.trend_type,  
            save=payload.save,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/runs/{run_id}/recollect")
def recollect(run_id: str, payload: RecollectRequest) -> dict:
    try:
        result = recollect_run(
            keyword_set=payload.keyword_set,
            sources=list(payload.sources),
            analysis_days=payload.analysis_days,
            collection_days=payload.collection_days,
            include_related=payload.include_related,
            trend_type=payload.trend_type,  
            limits=payload.limits,
            save=payload.save,
        )
        result["previous_run_id"] = run_id
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/runs/{run_id}/dashboard")
def dashboard(run_id: str) -> dict:
    try:
        return get_dashboard(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc