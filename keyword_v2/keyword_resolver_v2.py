import json
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
DEFAULT_KEYWORD_SETS_PATH = CURRENT_DIR / "keyword_sets.json"

WEIGHTS = {
    "canonical": 1.0,
    "alias": 1.0,
    "typo": 0.8,
    "related": 0.3,
}


def load_keyword_sets(path: str | Path = DEFAULT_KEYWORD_SETS_PATH) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_demo_keywords(path: str | Path = DEFAULT_KEYWORD_SETS_PATH) -> list[dict]:
    rows = []
    for item in load_keyword_sets(path):
        keyword_set = item["keyword_set"]
        rows.append(
            {
                "keyword": keyword_set["canonical"],
                "canonical": keyword_set["canonical"],
                "category": item.get("category", "F&B"),
                "alias": keyword_set.get("alias", []),
                "related": keyword_set.get("related", []),
            }
        )
    return rows


def resolve_keyword(
    keyword: str,
    include_related: bool = True,
    keyword_sets: list[dict] | None = None,
) -> dict:
    keyword = keyword.strip()
    keyword_sets = keyword_sets or load_keyword_sets()

    for item in keyword_sets:
        keyword_set = item["keyword_set"]
        if matches_keyword_set(keyword, keyword_set):
            return build_resolved_keyword_set(keyword_set, "preset", include_related)

    return build_resolved_keyword_set(
        {
            "canonical": keyword,
            "alias": [],
            "typo": [],
            "related": [],
        },
        "single_term_fallback",
        include_related,
    )


def matches_keyword_set(keyword: str, keyword_set: dict) -> bool:
    candidates = [
        keyword_set.get("canonical", ""),
        *keyword_set.get("alias", []),
        *keyword_set.get("typo", []),
    ]
    normalized = normalize_text(keyword)
    return any(normalize_text(candidate) == normalized for candidate in candidates)


def build_resolved_keyword_set(keyword_set: dict, mode: str, include_related: bool) -> dict:
    canonical = keyword_set.get("canonical", "")
    alias = keyword_set.get("alias", [])
    typo = keyword_set.get("typo", [])
    related = keyword_set.get("related", [])

    terms = [
        {"term": canonical, "term_type": "canonical", "term_weight": WEIGHTS["canonical"]},
        *[
            {"term": term, "term_type": "alias", "term_weight": WEIGHTS["alias"]}
            for term in alias
        ],
        *[
            {"term": term, "term_type": "typo", "term_weight": WEIGHTS["typo"]}
            for term in typo
        ],
    ]
    if include_related:
        terms.extend(
            {"term": term, "term_type": "related", "term_weight": WEIGHTS["related"]}
            for term in related
        )

    return {
        "keyword_set": {
            "canonical": canonical,
            "alias": alias,
            "typo": typo,
            "related": related,
        },
        "keyword_set_mode": mode,
        "terms": terms,
        "core_terms": [canonical, *alias, *typo],
        "expansion_terms": related if include_related else [],
    }


def normalize_text(value: str) -> str:
    return "".join(str(value).lower().split())
