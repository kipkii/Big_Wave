RAW_COLUMNS = [
    "source",
    "term",
    "term_type",
    "term_weight",
    "title",
    "url",
    "published_at",
    "collected_at",
    "views",
    "likes",
    "comments",
    "engagements",
    "author",
    "snippet",
    "raw_payload",
]


def ensure_raw_schema(df):
    for column in RAW_COLUMNS:
        if column not in df:
            df[column] = None
    return df[RAW_COLUMNS]
