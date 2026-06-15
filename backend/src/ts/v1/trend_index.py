import pandas as pd


def _normalize(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").fillna(0)
    minimum = numeric.min()
    maximum = numeric.max()
    if maximum == minimum:
        return pd.Series([50.0] * len(numeric), index=numeric.index)
    return ((numeric - minimum) / (maximum - minimum) * 100).clip(0, 100)


def calculate_trend_index_v1(feature_df: pd.DataFrame) -> list[dict]:
    if feature_df.empty:
        return []

    weighted_mentions = _normalize(feature_df["weighted_mentions"])
    engagements = _normalize(feature_df["engagements"])
    source_count = _normalize(feature_df["source_count"])
    value = weighted_mentions * 0.55 + engagements * 0.35 + source_count * 0.10

    return [
        {"period": str(row["date"]), "value": round(float(score), 2)}
        for (_, row), score in zip(feature_df.iterrows(), value)
    ]
