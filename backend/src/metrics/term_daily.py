import pandas as pd


def build_term_daily_metrics(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame(
            columns=["date", "source", "term", "term_type", "term_weight", "mentions", "views", "engagements"]
        )

    df = raw_df.copy()
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    df = df.dropna(subset=["published_at"])
    df["date"] = df["published_at"].dt.date.astype(str)

    for column in ["views", "engagements", "term_weight"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    return (
        df.groupby(["date", "source", "term", "term_type", "term_weight"], as_index=False)
        .agg(mentions=("title", "count"), views=("views", "sum"), engagements=("engagements", "sum"))
        .sort_values(["date", "source", "term"])
    )
