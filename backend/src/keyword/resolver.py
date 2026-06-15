from typing import Any

TERM_WEIGHTS = {
    "canonical": 1.0,
    "alias": 1.0,
    "typo": 0.8,
    "related": 0.3,
}


def _public_keyword_set(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical": item.get("canonical") or item["keyword"],
        "alias": item.get("alias", []),
        "typo": item.get("typo", []),
        "related": item.get("related", []),
    }


def _matches(keyword: str, item: dict[str, Any]) -> bool:
    candidates = [
        item.get("keyword"),
        item.get("canonical"),
        *item.get("alias", []),
        *item.get("typo", []),
    ]
    normalized = keyword.strip()
    return normalized in {str(candidate).strip() for candidate in candidates if candidate}


def _build_terms(keyword_set: dict[str, Any], include_related: bool) -> list[dict[str, Any]]:
    groups = [
        ("canonical", [keyword_set["canonical"]]),
        ("alias", keyword_set["alias"]),
        ("typo", keyword_set["typo"]),
    ]
    if include_related:
        groups.append(("related", keyword_set["related"]))

    seen = set()
    terms = []
    for term_type, values in groups:
        for value in values:
            term = str(value).strip()
            if not term or term in seen:
                continue
            seen.add(term)
            terms.append(
                {
                    "term": term,
                    "term_type": term_type,
                    "term_weight": TERM_WEIGHTS[term_type],
                }
            )
    return terms


def resolve_keyword(
    keyword: str,
    keyword_sets: list[dict[str, Any]],
    include_related: bool = True,
) -> dict[str, Any]:
    normalized = keyword.strip()
    if not normalized:
        raise ValueError("keyword must not be empty")

    matched = next((item for item in keyword_sets if _matches(normalized, item)), None)
    if matched:
        keyword_set = _public_keyword_set(matched)
        mode = "preset"
    else:
        keyword_set = {"canonical": normalized, "alias": [], "typo": [], "related": []}
        mode = "single_term_fallback"

    terms = _build_terms(keyword_set, include_related)
    return {
        "keyword_set": keyword_set,
        "keyword_set_mode": mode,
        "terms": terms,
        "core_terms": [item["term"] for item in terms if item["term_type"] != "related"],
        "expansion_terms": [item["term"] for item in terms if item["term_type"] == "related"],
    }
