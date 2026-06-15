# E1 Keyword Resolver

Preset keywords:

- 두쫀쿠
- 버터떡
- 우베

Resolver modes:

- `preset`: input matched canonical, alias, or typo in `keyword_sets.json`
- `single_term_fallback`: no preset matched

## Term Weights

```text
canonical: 1.0
alias: 1.0
typo: 0.8
related: 0.3
```

## Fallback

Unknown input is not unsupported. It becomes:

```json
{
  "keyword_set": {
    "canonical": "사용자입력",
    "alias": [],
    "typo": [],
    "related": []
  },
  "keyword_set_mode": "single_term_fallback",
  "terms": [
    { "term": "사용자입력", "term_type": "canonical", "term_weight": 1.0 }
  ],
  "core_terms": ["사용자입력"],
  "expansion_terms": []
}
```

This can later be promoted into a preset by adding alias, typo, and related terms.
