import pandas as pd


def build_features(keyword_daily_df: pd.DataFrame) -> pd.DataFrame:
    if keyword_daily_df.empty:
        return keyword_daily_df.copy()

    df = keyword_daily_df.copy()
    for column in ["mentions", "weighted_mentions", "views", "engagements", "source_count"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    df["mention_velocity"] = df["weighted_mentions"].diff().fillna(0)
    df["engagement_rate"] = df["engagements"] / df["views"].replace(0, 1)
    rolling_peak = df["weighted_mentions"].rolling(window=7, min_periods=1).max().replace(0, 1)
    df["peak_ratio"] = df["weighted_mentions"] / rolling_peak
    df["recent_slope"] = df["weighted_mentions"].rolling(window=3, min_periods=1).mean().diff().fillna(0)
    df["volatility"] = df["weighted_mentions"].rolling(window=7, min_periods=1).std().fillna(0)
    peak = df["weighted_mentions"].cummax().replace(0, 1)
    df["decline_from_peak"] = (peak - df["weighted_mentions"]) / peak
    return df
