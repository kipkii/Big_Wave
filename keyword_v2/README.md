# BigWave Keyword V2

E1 resolves a user keyword into an F&B keyword set.

Preset keywords:

- 두쫀쿠
- 버터떡
- 우베

If a keyword is not registered, BigWave does not return an unsupported state. It returns `single_term_fallback`.

```python
from keyword_v2 import resolve_keyword

resolved = resolve_keyword("두쫀쿠", include_related=True)
```

Output is passed directly into E2 Collection Engine.
