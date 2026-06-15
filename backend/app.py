from datetime import datetime

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import KEYWORD_SETS_PATH
from src.keyword import load_keyword_sets, resolve_keyword
from src.pipeline import run_analysis

app = FastAPI(title="BigWave API v2", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PeriodRequest(BaseModel):
    type: str = "relative"
    days: int | None = 30
    start_date: str | None = None
    end_date: str | None = None


class AnalyzeRequest(BaseModel):
    keyword: str
    sources: list[str] = Field(default_factory=lambda: ["youtube", "naver_news", "naver_blog"])
    period: PeriodRequest = Field(default_factory=PeriodRequest)
    include_related: bool = True
    limit_per_term: int = Field(default=20, ge=1, le=100)
    data_mode: str = "real"


def _records(df: pd.DataFrame, limit: int | None = None) -> list[dict]:
    if df.empty:
        return []
    source = df.head(limit).copy() if limit else df.copy()
    return source.astype(object).where(pd.notnull(source), None).to_dict(orient="records")


def _source_breakdown(raw_df: pd.DataFrame) -> list[dict]:
    if raw_df.empty:
        return []
    counts = raw_df["source"].value_counts()
    total = int(counts.sum()) or 1
    return [
        {"source": source, "count": int(count), "ratio": round(float(count / total * 100), 1)}
        for source, count in counts.items()
    ]


def _content_series(keyword_daily_df: pd.DataFrame) -> list[dict]:
    return [
        {"period": str(row["date"]), "value": int(row["mentions"])}
        for row in _records(keyword_daily_df)
    ]


def _raw_preview(raw_df: pd.DataFrame) -> list[dict]:
    return _records(raw_df, limit=10)


def _methodology() -> dict:
    return {
        "formula_version": "TS_v1",
        "description": "TS는 성장성, 반응 강도, 포화도, 하락 위험을 종합한 기간 대표 점수입니다.",
        "components": [
            {"name": "growth_score", "description": "최근 weighted mentions 증가 속도"},
            {"name": "reaction_score", "description": "조회수와 참여도 기반 반응 강도"},
            {"name": "saturation_score", "description": "피크 이후 유지력"},
            {"name": "decline_risk", "description": "최근 하락 위험"},
        ],
    }


def _serialize(result: dict) -> dict:
    ts = result["ts_result"]
    raw_df = result["raw_df"]
    keyword_daily_df = result["keyword_daily_df"]
    return {
        "keyword": result["keyword"],
        "analysis_run": result["analysis_run"],
        "keyword_set": result["keyword_set"],
        "terms": result["terms"],
        "core_terms": result["core_terms"],
        "expansion_terms": result["expansion_terms"],
        "summary": {
            "ts_score": ts["ts_score"],
            "status_label": ts["status_label"],
            "collected_items": int(len(raw_df)),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "growth_score": ts["growth_score"],
            "reaction_score": ts["reaction_score"],
            "saturation_score": ts["saturation_score"],
            "decline_risk": ts["decline_risk"],
        },
        "charts": {
            "trend_index_series": result["trend_index_series"],
            "content_series": _content_series(keyword_daily_df),
            "source_breakdown": _source_breakdown(raw_df),
        },
        "methodology": _methodology(),
        "report": result["report"],
        "raw_preview": _raw_preview(raw_df),
    }


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": "v2"}


@app.get("/api/keywords")
def keywords() -> dict:
    keyword_sets = load_keyword_sets(KEYWORD_SETS_PATH)
    return {
        "keywords": [
            {
                "keyword": item.get("canonical") or item["keyword"],
                "category": item.get("category", "Demo"),
                "description": item.get("description", ""),
            }
            for item in keyword_sets
        ]
    }


@app.get("/api/keyword-set/{keyword}")
def keyword_set(keyword: str, include_related: bool = True) -> dict:
    try:
        return resolve_keyword(keyword, load_keyword_sets(KEYWORD_SETS_PATH), include_related=include_related)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/analyze")
def analyze(payload: AnalyzeRequest) -> dict:
    try:
        result = run_analysis(
            keyword=payload.keyword,
            sources=payload.sources,
            period=payload.period.model_dump(),
            include_related=payload.include_related,
            limit_per_term=payload.limit_per_term,
            data_mode=payload.data_mode,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(result)
