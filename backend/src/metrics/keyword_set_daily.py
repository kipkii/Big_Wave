import pandas as pd


def build_keyword_set_daily_metrics(term_daily_df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    if term_daily_df.empty:
        return pd.DataFrame(
            columns=["date", "keyword", "mentions", "weighted_mentions", "views", "engagements", "source_count"]
        )

    df = term_daily_df.copy()
    df["weighted_mentions"] = df["mentions"] * df["term_weight"]
    grouped = (
        df.groupby("date", as_index=False)
        .agg(
            mentions=("mentions", "sum"),
            weighted_mentions=("weighted_mentions", "sum"),
            views=("views", "sum"),
            engagements=("engagements", "sum"),
            source_count=("source", "nunique"),
        )
        .sort_values("date")
    )
    grouped["keyword"] = keyword
    return grouped[["date", "keyword", "mentions", "weighted_mentions", "views", "engagements", "source_count"]]
