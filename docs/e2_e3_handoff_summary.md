# BigWave MVP v2 Handoff Summary

작성 시점: 2026-05-26

이 문서는 BigWave MVP v2의 현재 구조, E2 Collection Engine 마감 상태, 그리고 다음 단계인 E3 Trend Analyzer 설계를 논의하기 위한 핸드오프 요약이다.

## 1. 현재 개발 철학

BigWave v2는 처음부터 완성형 웹서비스로 과하게 만들기보다, 각 단계를 사람이 이해하고 검증할 수 있는 구조로 나눈다.

핵심 방향:

- E1: 키워드 세트 생성/해석
- E2: 수집 및 raw CSV 생산
- E3: 시계열화, 분석, TS Score, dashboard data 생성
- UI/App Layer: E3 결과를 보여주는 화면

현재 단계에서는 서버 DB를 바로 쓰지 않는다. 로컬 CSV를 기준으로 검증하고, 이후 같은 저장 인터페이스를 SQLite/DB로 자연스럽게 교체할 수 있게 둔다.

중요한 원칙:

- 누구든지 로컬/코랩/웹앱에서 같은 흐름으로 실행 가능해야 한다.
- collector는 분석/시각화를 하지 않는다.
- collector는 raw CSV producer다.
- 분석과 시각화용 데이터 생성은 E3에서 한다.
- 프론트는 계산하지 않고 `dashboard_data.json` 또는 API response를 렌더링한다.

## 2. E1 Keyword Resolver 개념

E1의 최종 출력은 단순 문자열이 아니라 keyword set dictionary다.

예시:

```python
{
    "keyword_set": {
        "canonical": "두쫀쿠",
        "alias": ["두바이 쫀득 쿠키"],
        "typo": ["두존쿠"],
        "related": ["카다이프", "피스타치오"]
    },
    "keyword_set_mode": "preset",
    "terms": [
        {"term": "두쫀쿠", "term_type": "canonical", "term_weight": 1.0},
        {"term": "두바이 쫀득 쿠키", "term_type": "alias", "term_weight": 1.0},
        {"term": "두존쿠", "term_type": "typo", "term_weight": 0.8},
        {"term": "카다이프", "term_type": "related", "term_weight": 0.3},
        {"term": "피스타치오", "term_type": "related", "term_weight": 0.3}
    ],
    "core_terms": ["두쫀쿠", "두바이 쫀득 쿠키", "두존쿠"],
    "expansion_terms": ["카다이프", "피스타치오"]
}
```

MVP preset keywords:

- 두쫀쿠
- 버터떡
- 우베

미지원 키워드 개념은 두지 않는다. preset에 없으면 `single_term_fallback`으로 처리한다.

Fallback 예시:

```python
{
    "keyword_set": {
        "canonical": "버터떡",
        "alias": [],
        "typo": [],
        "related": []
    },
    "keyword_set_mode": "single_term_fallback",
    "terms": [
        {"term": "버터떡", "term_type": "canonical", "term_weight": 1.0}
    ],
    "core_terms": ["버터떡"],
    "expansion_terms": []
}
```

## 3. E2 Collection Engine 상태

E2는 MVP 기준으로 마감 가능 상태다.

현재 위치:

```text
bigwave_mvp_v2/
  collector_v2/
    youtube_collector_v2.py
    naver_news_collector_v2.py
    naver_blog_collector_v2.py
    storage_v2.py
    collection_router_v2.py
    README.md
```

E2의 역할:

```text
E1 keyword set dict 입력
→ selected sources 순회
→ 각 source collector 실행
→ 각 term 수집
→ term_type / term_weight row에 부착
→ source별 CSV 저장
→ raw_all.csv 통합 저장
→ run_meta.json 저장
```

지원 source:

- youtube
- naver_news
- naver_blog

E2는 다음 입력을 받을 수 있다.

- 단일 문자열 keyword
- E1 keyword set dictionary

단일 문자열이 들어오면 내부적으로 single term fallback 형태로 normalize한다.

## 4. E2 저장 구조

현재 저장 위치:

```text
bigwave_mvp_v2/data/raw/{run_id}/
  youtube.csv
  naver_news.csv
  naver_blog.csv
  raw_all.csv
  run_meta.json
```

예시:

```text
bigwave_mvp_v2/data/raw/run_20260526_150843_두쫀쿠/
```

실제 검수 결과 생성 파일:

```text
youtube.csv
naver_news.csv
naver_blog.csv
raw_all.csv
run_meta.json
```

검수 실행 조건:

- canonical: 두쫀쿠
- alias: 두바이 쫀득 쿠키
- typo: 두존쿠
- related: 카다이프, 피스타치오
- sources: youtube, naver_news, naver_blog
- limit per term: 2

검수 결과:

```text
youtube rows: 10
naver_news rows: 10
naver_blog rows: 10
raw_all rows after dedupe: 26
errors: {}
```

## 5. E2 Raw Schema

E2는 원본 호환 컬럼과 BigWave 공통 컬럼을 함께 저장한다.

공통 핵심 컬럼:

```text
canonical_keyword
keyword_set_mode
keyword
source
term
term_type
term_weight
title
url
published_at
collected_at
views
likes
comments
engagements
author
snippet
raw_payload
```

YouTube 원본 호환 컬럼:

```text
keyword
video_id
title
published_at
view_count
like_count
comment_count
url
```

Naver News 원본 호환 컬럼:

```text
keyword
title
url
published_at
description
originallink
```

Naver Blog 원본 호환 컬럼:

```text
keyword
title
url
published_at
description
bloggername
bloggerlink
```

`keyword`는 원본 호환을 위해 실제 검색에 사용한 term과 동일하게 둔다.

`canonical_keyword`는 분석 기준의 대표 키워드다.

중복 제거 기준:

- 기본: `source + url`
- url이 없는 경우: `source + title + published_at`

## 6. E2에서 의도적으로 하지 않는 것

E2는 다음을 하지 않는다.

- 시계열화
- trend index 계산
- TS Score 계산
- 그래프 생성
- report 생성
- DB 저장

E2는 raw CSV 생산기다.

## 7. Frontend 입력 페이지 구상

사용자 입력 페이지는 검색 중심이다.

입력 요소:

- keyword input
- source toggle
  - YouTube
  - Naver News
  - Naver Blog
- period selector
  - 7일
  - 14일
  - 30일
  - 90일
  - 180일/365일은 고급 옵션으로 추후 검토
- analyze button
- 최근 검색/run list
- 도움말

source 기본값:

```text
youtube: ON
naver_news: ON
naver_blog: ON
```

중요한 설계:

- E2는 선택된 source만 수집한다.
- E3는 저장된 `raw_all.csv`에서 source/period/include_related 기준으로 다시 필터링할 수 있다.
- 즉 결과 페이지에서 source toggle이나 period를 바꿀 때, 가능한 경우 API 재수집 없이 E3만 재실행한다.

## 8. 기간 정책 논의 상태

아직 확정하지 않았다.

현재 유력한 방향:

```text
E2 collection period = 넉넉히 수집
E3 analysis period = 사용자가 선택한 기간으로 필터링
```

추천 기본안:

- E2 기본 수집 기간: 90일
- E3 기본 분석 기간: 30일
- 1년은 기본값으로는 길고, 고급 옵션으로 검토

고민 포인트:

- YouTube 1년 수집은 quota와 노이즈 문제가 있다.
- Naver는 검색 API 결과가 1년 전체를 안정적으로 대표한다고 보기 어렵다.
- BigWave MVP가 "지금 뜨는 트렌드"를 보려면 90일이 더 자연스럽다.

## 9. E3 Trend Analyzer 방향

E3는 `raw_all.csv`부터 결과 제공까지 담당한다.

E3 범위:

```text
raw_all.csv 로드
→ source/period/include_related 필터
→ 시계열화
→ feature 계산
→ TS Score 산출
→ chart data 생성
→ dashboard_data.json 생성
```

E3는 별도 엔진으로 두되, 내부 하위 모듈로 쪼갠다.

추천 구조:

```text
bigwave_mvp_v2/
  analyzer_v2/
    raw_loader_v2.py
    time_series_v2.py
    feature_builder_v2.py
    ts_scorer_v2.py
    dashboard_packager_v2.py
    analyzer_router_v2.py
    README.md
```

E3 하위 역할:

```text
E3-1 Raw Loader
- raw_all.csv 읽기
- selected_sources 필터
- analysis_days 필터
- include_related 필터

E3-2 Time Series Aggregator
- term_daily_metrics
- keyword_set_daily_metrics
- weekly_partition
- source_breakdown
- term_breakdown

E3-3 Feature Builder
- weighted_mentions
- velocity
- demand_pressure
- source_diversity
- peak_ratio
- decline_from_peak

E3-4 TS Scorer
- growth_score
- reaction_score
- saturation_score
- decline_risk
- ts_score
- status_label

E3-5 Dashboard Packager
- summary
- charts
- report
- raw_preview
- methodology
- dashboard_data.json
```

TS 계산은 E4가 아니라 E3 내부의 `ts_scorer_v2.py`가 담당한다.

E4는 만들지 않는다. 만들더라도 계산 엔진이 아니라 UI/API/Delivery layer로 본다.

## 10. 레거시 분석에서 가져올 핵심

레거시 노트북에서 실제로 하던 분석:

1. 월별/주차별 조회수 집계

```python
df_raw["year_month"] = df_raw["published_at"].dt.to_period("M")
trend_df = df_raw.groupby(["keyword", "year_month"])["view_count"].sum()
```

2. 최초 등장 시점 기준 T+n 정렬

```text
month_t = 현재월 - 최초등장월
view_ratio = view_count / max_views * 100
rolling mean
```

3. 주차별 공급/반응 분석

```text
content_supply = video_id count
view_count = sum
comment_count = sum
view_per_video = view_count / content_supply
```

4. Velocity 기반 분석

```text
views_per_day
avg_velocity
video_supply
demand_pressure = avg_velocity / video_supply
```

5. Z-score 표준화

```text
video_supply_Z
avg_velocity_Z
demand_pressure_Z
```

6. 시각화

```text
공급량 bar
조회수/반응 line
Z-score line
댓글 작성 시점 histogram
```

E3 v1에서는 그래프 자체보다 그래프를 그릴 수 있는 데이터 CSV/JSON을 먼저 만든다.

## 11. E3 v1 로직 기준 제안

E3 구현 자체는 pandas groupby 중심이라 어렵지 않다. 중요한 것은 지표 정의다.

기본 단위:

- daily
- weekly

mentions:

```text
mentions = row count
```

weighted_mentions:

```text
weighted_mentions = sum(term_weight)
```

term weight:

```text
canonical: 1.0
alias: 1.0
typo: 0.8
related: 0.3
```

views:

```text
views = sum(views)
```

YouTube는 실제 views가 있고, Naver는 0이다.

engagements:

```text
engagements = likes + comments
```

YouTube는 실제 likes/comments가 있고, Naver는 0이다.

source_count:

```text
source_count = nunique(source)
```

term_daily_metrics 단위:

```text
date + source + term + term_type + term_weight
```

컬럼:

```text
date
source
term
term_type
term_weight
mentions
weighted_mentions
views
likes
comments
engagements
```

keyword_set_daily_metrics 단위:

```text
date + canonical_keyword
```

컬럼:

```text
date
canonical_keyword
mentions
weighted_mentions
views
likes
comments
engagements
source_count
core_mentions
related_mentions
```

core terms:

```text
canonical + alias + typo
```

related terms:

```text
related
```

weekly_partition:

```text
week
content_supply
weighted_supply
views
comments
engagements
view_per_item
engagement_per_item
```

## 12. Trend Index와 TS Score 분리

Trend Index:

- 그래프용 날짜별 0~100 흐름 지표
- `ts_score`와 다르다.
- weighted_mentions, views, engagements를 정규화해서 생성한다.

TS Score:

- 현재 분석 기간 전체를 종합한 최종 판단 점수
- summary card에 표시된다.

TS v1 후보:

```text
growth_score
reaction_score
saturation_score
decline_risk
```

가중합 후보:

```text
ts_score =
  growth_score * 0.38
  + reaction_score * 0.32
  + saturation_score * 0.18
  + (100 - decline_risk) * 0.12
```

이 공식은 추후 조정 가능하다. 중요한 것은 먼저 설명 가능한 v1을 만드는 것이다.

## 13. E3 최종 산출물 제안

Processed:

```text
bigwave_mvp_v2/data/processed/{run_id}/
  term_daily_metrics.csv
  keyword_set_daily_metrics.csv
  weekly_partition.csv
  trend_features.csv
```

Results:

```text
bigwave_mvp_v2/data/results/{run_id}/
  trend_index.csv
  ts_score.json
  dashboard_data.json
```

`dashboard_data.json`은 프론트/API가 바로 먹는 최종 결과다.

예상 구조:

```json
{
  "summary": {
    "ts_score": 72,
    "status_label": "Rising",
    "collected_items": 128,
    "last_updated": "2026-05-26"
  },
  "component_scores": {
    "growth_score": 68,
    "reaction_score": 74,
    "saturation_score": 55,
    "decline_risk": 22
  },
  "charts": {
    "trend_index_series": [],
    "content_series": [],
    "source_breakdown": []
  },
  "term_breakdown": [],
  "raw_preview": [],
  "methodology": {},
  "report": {}
}
```

## 14. Frontend 연결 관점

프론트 작성자도 동일한 사람이므로, E3는 프론트가 계산하지 않아도 되게 만들어야 한다.

프론트 매핑:

```text
AnalysisSummaryCards ← dashboard_data.summary
TrendChartSection ← dashboard_data.charts.trend_index_series
Content volume chart ← dashboard_data.charts.content_series
Source breakdown ← dashboard_data.charts.source_breakdown
KeywordSetPanel ← run_meta.keyword_set
RawDataPreview ← dashboard_data.raw_preview
Methodology card ← dashboard_data.methodology
InsightReportCard ← dashboard_data.report
```

프론트에서는 계산하지 않고 렌더링만 한다.

## 15. 다음 논의 질문

ChatGPT와 논의할 핵심 질문:

1. E3 v1의 TS Score 공식은 위 후보로 충분한가?
2. Trend Index는 weighted_mentions/views/engagements를 어떤 비율로 섞는 게 좋은가?
3. YouTube views가 너무 큰 값이라 Naver mentions를 압도하지 않게 하려면 어떤 normalization이 적절한가?
4. related term weight 0.3은 E3에서 기본 포함하되, 사용자가 include_related=false로 끌 수 있게 하는 게 좋은가?
5. E2는 90일을 기본 수집하고, E3에서 7/14/30/90일 필터링하는 정책이 적절한가?
6. TS Score와 Trend Index를 프론트에서 어떻게 설명해야 사용자에게 납득 가능한가?
7. E3 output `dashboard_data.json`의 스키마를 확정해도 되는가?

## 16. 현재 결론

E2 Collection Engine MVP는 마감 가능하다.

다음 단계는 E3 Trend Analyzer다.

E3는 복잡한 AI 모델이 아니라, 먼저 다음을 안정적으로 만드는 것이 목표다.

```text
raw_all.csv
→ filtered raw
→ daily metrics
→ weekly partition
→ trend index
→ ts score
→ dashboard_data.json
```

이후 프론트는 `dashboard_data.json`을 렌더링한다.

## 17. E3 Finalized MVP Policy

E3 구현 중 확정한 정책:

```text
Reanalyze = E3만 다시 실행
- selected_sources 변경
- analysis_days 변경
- include_related 변경

Recollect = E2부터 다시 실행
- keyword set 수정
- term 추가/삭제
- term_weight 변경
- 현재 run에 없는 source를 새로 분석해야 하는 경우
```

E3 입력 계약:

```python
run_e3_analysis(
    run_dir: str,
    selected_sources: list[str] | None = None,
    analysis_days: int = 30,
    include_related: bool = True,
    save: bool = True
) -> dict
```

E3는 collector를 호출하지 않는다.
E3는 API key, collector config, edited keyword set을 받지 않는다.

빈 데이터 정책:

```text
raw_all.csv 없음 = error
raw_all.csv는 있으나 필터 후 0개 = 정상 empty dashboard
empty dashboard의 ts_score = 0
status_label = Low
```

날짜 정책:

```text
run_id / 저장 이력 = 수집 실행 시각 기준
기간 필터 / 시계열 분석 = published_at 기준
analysis_days = filtered raw의 max(published_at) 기준 최근 N일
```

사용자 설명 문구:

```text
분석 기간은 수집 데이터의 최신 발행일(published_at)을 기준으로 계산됩니다.
API 제공사 검색 결과가 오늘까지의 데이터를 항상 포함하지 않을 수 있습니다.
```

source toggle 정책:

```text
E3는 없는 source를 자동 수집하지 않는다.
없는 source는 missing_sources / warnings로 반환한다.
새 source가 필요하면 recollect다.
```

include_related 정책:

```text
include_related 토글 변경 = E3 reanalyze
related term 추가/삭제/수정 = E2 recollect
```

E3 dashboard output에 추가된 프론트 보조 필드:

```text
analysis_options
available_sources
missing_sources
warnings
```

## 18. E3 Formula Documents

산식 설명은 별도 문서로 분리했다.

```text
bigwave_mvp_v2/docs/e3_formula_spec.md
bigwave_mvp_v2/docs/e3_formula_spec.html
bigwave_mvp_v2/docs/e3_formula_spec.pdf
```

산식 구현 위치:

```text
bigwave_mvp_v2/analyzer_v2/feature_builder_v2.py
bigwave_mvp_v2/analyzer_v2/ts_scorer_v2.py
```

Trend Index와 TS Score는 분리한다.

```text
Trend Index = 날짜별 그래프용 흐름 지표
TS Score = 분석 기간 전체의 최종 판단 점수
```
