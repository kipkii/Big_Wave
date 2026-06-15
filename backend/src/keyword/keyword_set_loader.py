import json
from pathlib import Path
from typing import Any


def load_keyword_sets(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as file:
        payload = json.load(file)

    keyword_sets = payload.get("keywords")
    if not isinstance(keyword_sets, list):
        raise ValueError("keyword_sets.json must contain a keywords list")
    return keyword_sets
