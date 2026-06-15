import pandas as pd

from .labels import assign_status_label


def _normalize(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").fillna(0)
    minimum = numeric.min()
    maximum = numeric.max()
    if maximum == minimum:
        return pd.Series([50.0] * len(numeric), index=numeric.index)
    return ((numeric - minimum) / (maximum - minimum) * 100).clip(0, 100)


def _last(series: pd.Series, default: float = 50.0) -> float:
    return float(series.iloc[-1]) if not series.empty else default


def calculate_ts_v1(feature_df: pd.DataFrame) -> dict:
    if feature_df.empty:
        result = {"growth_score": 50.0, "reaction_score": 50.0, "saturation_score": 35.0, "decline_risk": 30.0}
    else:
        growth_score = _last(_normalize(feature_df["mention_velocity"]))
        reaction_score = _last(_normalize(feature_df["engagement_rate"]))
        saturation_score = _last((feature_df["peak_ratio"] * 100).clip(0, 100))
        decline_risk = _last((feature_df["decline_from_peak"] * 100).clip(0, 100), 30.0)
        result = {
            "growth_score": round(growth_score, 2),
            "reaction_score": round(reaction_score, 2),
            "saturation_score": round(saturation_score, 2),
            "decline_risk": round(decline_risk, 2),
        }

    ts_score = (
        result["growth_score"] * 0.38
        + result["reaction_score"] * 0.32
        + result["saturation_score"] * 0.18
        + (100 - result["decline_risk"]) * 0.12
    )
    result["ts_score"] = round(float(ts_score), 2)
    result["status_label"] = assign_status_label(
        result["ts_score"],
        result["growth_score"],
        result["decline_risk"],
    )
    return result
