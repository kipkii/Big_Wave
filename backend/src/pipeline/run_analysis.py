from datetime import date, datetime, timedelta
import uuid

from src.collectors import collect_sources
from src.config import DB_PATH, KEYWORD_SETS_PATH
from src.keyword import load_keyword_sets, resolve_keyword
from src.metrics import build_features, build_keyword_set_daily_metrics, build_term_daily_metrics
from src.report import generate_rule_report
from src.storage import save_analysis_run
from src.ts.v1 import calculate_trend_index_v1, calculate_ts_v1


def resolve_period(period: dict | None) -> dict:
    period = period or {"type": "relative", "days": 30}
    if period.get("type") == "relative":
        days = int(period.get("days", 30))
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        return {
            "type": "relative",
            "days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    if period.get("type") == "custom":
        return {
            "type": "custom",
            "days": None,
            "start_date": period["start_date"],
            "end_date": period["end_date"],
        }

    raise ValueError(f"Unsupported period type: {period.get('type')}")


def run_analysis(
    keyword: str,
    sources: list[str],
    period: dict | None = None,
    include_related: bool = True,
    limit_per_term: int = 20,
    data_mode: str = "real",
    save: bool = True,
) -> dict:
    if data_mode not in {"real", "sample"}:
        raise ValueError("data_mode must be real or sample")

    resolved_period = resolve_period(period)
    start_date = date.fromisoformat(resolved_period["start_date"])
    end_date = date.fromisoformat(resolved_period["end_date"])
    keyword_sets = load_keyword_sets(KEYWORD_SETS_PATH)
    resolved = resolve_keyword(keyword, keyword_sets, include_related=include_related)
    canonical = resolved["keyword_set"]["canonical"]
    run_id = f"run_{uuid.uuid4().hex[:12]}"

    raw_df = collect_sources(
        sources=sources,
        terms=resolved["terms"],
        start_date=start_date,
        end_date=end_date,
        limit_per_term=limit_per_term,
        data_mode=data_mode,
    )
    term_daily_df = build_term_daily_metrics(raw_df)
    keyword_daily_df = build_keyword_set_daily_metrics(term_daily_df, canonical)
    feature_df = build_features(keyword_daily_df)
    ts_result = calculate_ts_v1(feature_df)
    trend_index_series = calculate_trend_index_v1(feature_df)
    report = generate_rule_report(canonical, ts_result, data_mode)

    run_metadata = {
        "run_id": run_id,
        "keyword": canonical,
        "keyword_set_mode": resolved["keyword_set_mode"],
        "sources": sources,
        "period": resolved_period,
        "include_related": include_related,
        "data_mode": data_mode,
        "created_at": datetime.now().isoformat(),
        "status": "success",
        "error_message": None,
    }

    if save:
        save_analysis_run(
            DB_PATH,
            run_metadata,
            raw_df,
            term_daily_df,
            keyword_daily_df,
            ts_result,
            report,
        )

    return {
        "keyword": canonical,
        "analysis_run": run_metadata,
        **resolved,
        "raw_df": raw_df,
        "term_daily_df": term_daily_df,
        "keyword_daily_df": keyword_daily_df,
        "feature_df": feature_df,
        "ts_result": ts_result,
        "trend_index_series": trend_index_series,
        "report": report,
    }
