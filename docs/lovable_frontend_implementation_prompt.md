# BigWave MVP v2 Lovable Frontend Implementation Prompt

아래 지시사항을 기준으로 BigWave MVP v2 프론트엔드를 구현하라.

현재 프로젝트에는 이미 Python backend/API가 존재한다.
프론트는 계산하지 않고, FastAPI 응답을 렌더링하는 클라이언트 역할만 한다.

## 0. 절대 원칙

1. 현재 목업의 큰 UX 구조는 유지한다.
2. 첫 화면은 분석 대시보드가 아니라 검색 중심 입력 페이지다.
3. 프론트에서 TS Score, Trend Index, metric aggregation을 계산하지 않는다.
4. 모든 계산은 backend_v2 API가 수행한다.
5. mock/static data는 fallback UI 용도로만 남기고, 실제 화면은 API response 기반으로 렌더링한다.
6. 키워드 세트 수정은 HIL 영역이다. 키워드 세트를 바꾸면 E2부터 다시 수집해야 한다.
7. source/period/include_related 필터 변경은 E3 reanalyze만 수행한다.
8. API 호출 중 loading state와 error state를 반드시 표시한다.

## 1. Backend API 정보

FastAPI 서버 실행:

```bash
cd bigwave_mvp_v2
uvicorn backend_v2.app:app --reload --port 8000
```

API Base URL:

```ts
http://127.0.0.1:8000
```

엔드포인트:

```text
GET  /api/health
GET  /api/keywords
GET  /api/keyword-set/{keyword}
POST /api/analyze
POST /api/runs/{run_id}/reanalyze
POST /api/runs/{run_id}/recollect
GET  /api/runs/{run_id}/dashboard
```

## 2. BigWave v2 흐름

```text
E1 Keyword Resolver
-> E2 Collection Engine
-> E3 Trend Analyzer
-> dashboard_data.json/API response
-> React frontend rendering
```

프론트는 다음 두 종류의 실행을 구분해야 한다.

```text
reanalyze
= E3만 다시 실행
= source toggle / period / include_related 변경

recollect
= E2부터 다시 실행
= keyword set 수정 / term 추가삭제 / term_weight 변경 / 없는 source 추가 필요
```

## 3. Page 1: Search/Input Page

현재 목업 구조를 유지한다.

화면 구성:

```text
왼쪽 사이드바
- 최근 검색어 또는 최근 run list
- 없으면 localStorage 기반 최근 검색어만 보여줘도 됨

중앙
- "무엇이든 물어보세요"
- keyword input
- 검색/분석 버튼
- source toggle chips
- period selector
- include_related toggle
- loading / error message

하단
- 짧은 안내 문구
- "입력한 키워드는 기기에만 저장돼요" 또는 유사 문구
```

초기 source toggle 기본값:

```ts
{
  youtube: true,
  naver_news: true,
  naver_blog: true
}
```

화면 표시명:

```text
youtube -> 유튜브
naver_news -> 네이버 뉴스
naver_blog -> 네이버 블로그
```

기간 selector:

```text
[7일] [14일] [30일] [90일]
```

기본값:

```ts
analysis_days = 30
collection_days = 90
```

include_related:

```text
연관 키워드 포함
```

기본값:

```ts
include_related = true
```

추천 키워드:

```text
GET /api/keywords
```

MVP 추천 키워드는 F&B 3개:

```text
두쫀쿠
버터떡
우베
```

## 4. Search Submit 동작

사용자가 keyword를 입력하고 분석 버튼을 누르면:

```http
POST /api/analyze
```

Request:

```json
{
  "keyword": "두쫀쿠",
  "sources": ["youtube", "naver_news", "naver_blog"],
  "analysis_days": 30,
  "collection_days": 90,
  "include_related": true,
  "limits": {
    "youtube": 250,
    "naver_news": 100,
    "naver_blog": 100
  },
  "save": true
}
```

개발/데모 중 API quota를 줄이고 싶으면 limits를 작게 둔다.

```json
{
  "limits": {
    "youtube": 5,
    "naver_news": 5,
    "naver_blog": 5
  }
}
```

Response는 `DashboardData`다.

응답의 `run_id`를 사용해 결과 페이지로 이동한다.

권장 route:

```text
/analysis/{run_id}
```

기존 route가 `/analysis/{keyword}`라면 반드시 `{run_id}` 중심으로 바꾼다.
같은 keyword라도 source/period/keyword set에 따라 run이 달라지기 때문이다.

## 5. Page 2: Analysis/Dashboard Page

Route:

```text
/analysis/{run_id}
```

진입 시:

```http
GET /api/runs/{run_id}/dashboard
```

dashboard가 없거나 404면 사용자에게 친절한 오류를 보여준다.

구성:

```text
상단
- keyword title
- TS Score
- status label
- collected_items
- last_updated
- warnings

옵션 패널
- source toggles
- period selector
- include_related toggle
- 빠른 재분석 버튼
- 키워드 세트 수정/재수집 버튼은 MVP에서 disabled 또는 coming soon 가능

본문
- Trend Index chart
- Content volume chart
- Source breakdown
- Term breakdown
- Keyword Set Panel
- Methodology card
- Insight Report Card
- Raw Data Preview
```

## 6. Reanalyze 동작

결과 페이지에서 다음 변경은 E3만 다시 실행한다.

```text
source toggle
period selector
include_related toggle
```

요청:

```http
POST /api/runs/{run_id}/reanalyze
```

Request:

```json
{
  "selected_sources": ["youtube"],
  "analysis_days": 30,
  "include_related": false,
  "save": true
}
```

Response:

```text
DashboardData
```

프론트는 응답으로 기존 dashboard state를 교체한다.
run_id는 동일하다.

## 7. Recollect 동작

키워드 세트를 수정하면 E2부터 다시 수집해야 한다.

예:

```text
alias 추가
typo 삭제
related 추가
term_weight 변경
canonical 변경
현재 run에 없는 source 추가 분석
```

요청:

```http
POST /api/runs/{run_id}/recollect
```

Request:

```json
{
  "keyword_set": {
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
      {"term": "카다이프", "term_type": "related", "term_weight": 0.3}
    ],
    "core_terms": ["두쫀쿠", "두바이 쫀득 쿠키", "두존쿠"],
    "expansion_terms": ["카다이프", "피스타치오"]
  },
  "sources": ["youtube", "naver_news", "naver_blog"],
  "analysis_days": 30,
  "collection_days": 90,
  "include_related": true,
  "limits": {
    "youtube": 250,
    "naver_news": 100,
    "naver_blog": 100
  },
  "save": true
}
```

Response는 새 `run_id`를 가진 DashboardData다.
프론트는 새 route로 이동한다.

```text
/analysis/{new_run_id}
```

MVP에서는 keyword set editor를 보기 전용으로 둬도 된다.
하지만 설계상 버튼과 정책은 준비해둔다.

## 8. DashboardData Type

TypeScript 타입을 만든다.

```ts
export type KeywordSet = {
  canonical: string;
  alias: string[];
  typo: string[];
  related: string[];
};

export type Summary = {
  ts_score: number;
  status_label: string;
  collected_items: number;
  last_updated: string;
};

export type ComponentScores = {
  growth_score: number;
  reaction_score: number;
  saturation_score: number;
  decline_risk: number;
};

export type TrendPoint = {
  period: string;
  value: number;
};

export type ContentPoint = {
  period: string;
  value: number;
  weighted_value: number;
};

export type SourceBreakdownItem = {
  source: string;
  count: number;
  ratio: number;
};

export type TermBreakdownItem = {
  term: string;
  term_type: string;
  count: number;
  weighted_count: number;
};

export type RawPreviewItem = {
  title: string;
  source: string;
  term: string;
  term_type: string;
  published_at: string;
  url: string;
  views: number;
  engagements: number;
};

export type Methodology = {
  formula_version: string;
  description: string;
  components: { name: string; description: string }[];
  notice: string;
};

export type Report = {
  summary: string;
  evidence: string;
  risk: string;
  recommendation: string;
};

export type AnalysisOptions = {
  selected_sources: string[];
  analysis_days: number;
  include_related: boolean;
  date_basis: string;
  period_anchor: string;
  rerun_policy: string;
};

export type DashboardData = {
  run_id: string;
  keyword: string;
  keyword_set: KeywordSet;
  keyword_set_mode: "preset" | "single_term_fallback" | string;
  analysis_options: AnalysisOptions;
  available_sources: string[];
  missing_sources: string[];
  warnings: string[];
  summary: Summary;
  component_scores: ComponentScores;
  charts: {
    trend_index_series: TrendPoint[];
    content_series: ContentPoint[];
    source_breakdown: SourceBreakdownItem[];
  };
  term_breakdown: TermBreakdownItem[];
  raw_preview: RawPreviewItem[];
  methodology: Methodology;
  report: Report;
  debug?: unknown;
  collection?: {
    run_id: string;
    raw_rows: number;
    saved_files: Record<string, string>;
    run_meta: string;
    errors: Record<string, string>;
  };
};
```

## 9. API Client

`src/lib/api.ts`를 만든다.

```ts
const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `API error: ${res.status}`);
  }

  return res.json();
}

export function getKeywords() {
  return request<{ domain: string; keywords: any[] }>("/api/keywords");
}

export function getKeywordSet(keyword: string) {
  return request(`/api/keyword-set/${encodeURIComponent(keyword)}`);
}

export function analyze(payload: AnalyzeRequest) {
  return request<DashboardData>("/api/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getDashboard(runId: string) {
  return request<DashboardData>(`/api/runs/${encodeURIComponent(runId)}/dashboard`);
}

export function reanalyze(runId: string, payload: ReanalyzeRequest) {
  return request<DashboardData>(`/api/runs/${encodeURIComponent(runId)}/reanalyze`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function recollect(runId: string, payload: RecollectRequest) {
  return request<DashboardData>(`/api/runs/${encodeURIComponent(runId)}/recollect`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
```

## 10. Component Mapping

기존 Lovable 컴포넌트를 유지하되 mock data를 props/API 기반으로 교체한다.

```text
SearchHero
-> keyword input
-> source toggles
-> period selector
-> include_related toggle
-> analyze API call

CategoryKeywordSection
-> GET /api/keywords

AnalysisSummaryCards
-> dashboard.summary
-> dashboard.component_scores

KeywordSetPanel
-> dashboard.keyword_set
-> dashboard.keyword_set_mode
-> MVP에서는 보기 전용

TrendChartSection
-> dashboard.charts.trend_index_series
-> dashboard.charts.content_series

InsightReportCard
-> dashboard.report
-> dashboard.methodology

RawDataPreview
-> dashboard.raw_preview

SourceBreakdown
-> dashboard.charts.source_breakdown

TermBreakdown
-> dashboard.term_breakdown
```

## 11. Empty / Warning State

E3는 빈 결과도 정상 dashboard로 반환한다.

빈 결과 조건:

```text
필터 후 데이터 0개
source가 현재 run에 없음
기간 안에 데이터 없음
```

프론트는 `warnings`를 상단 또는 옵션 패널 근처에 표시한다.

예:

```text
선택한 조건에 해당하는 수집 데이터가 없습니다.
선택한 source 중 현재 run에 없는 채널이 있습니다. 해당 채널을 보려면 재수집이 필요합니다.
분석 기간은 수집 데이터의 최신 발행일 기준으로 계산됩니다.
```

`missing_sources`가 있으면 해당 source toggle에 "재수집 필요" 표시를 붙인다.

## 12. Loading State

`/api/analyze`는 실제 API 수집을 포함하므로 몇 초 이상 걸릴 수 있다.

검색 버튼 클릭 후:

```text
분석 중...
선택한 채널에서 데이터를 수집하고 있어요.
```

reanalyze는 E3만 실행하므로 더 빠르다.

```text
필터 적용 중...
```

error state:

```text
분석을 완료하지 못했습니다.
API 키, 네트워크, 선택한 채널을 확인해주세요.
```

에러 상세는 개발 중에만 접을 수 있는 영역으로 보여줘도 된다.

## 13. Styling Direction

현재 목업의 톤을 유지한다.

- 넓은 흰 여백
- 왼쪽 최근 검색어 사이드바
- 중앙 검색 중심 UI
- 작은 pill/toggle 형태 source selector
- 차분한 민트/청록 accent
- 대시보드는 카드 기반이되 너무 화려하지 않게
- 숫자 카드와 그래프는 읽기 쉽게

첫 화면은 마케팅 랜딩이 아니다.
첫 화면은 바로 검색/분석 입력 페이지다.

## 14. Implementation Order

1. `src/lib/types.ts` 작성
2. `src/lib/api.ts` 작성
3. route를 `/analysis/$runId` 중심으로 수정
4. index page에서 `/api/keywords` 연결
5. index page에서 `/api/analyze` 연결
6. analysis page에서 `/api/runs/{runId}/dashboard` 연결
7. dashboard components props 기반으로 변경
8. reanalyze controls 연결
9. warnings/empty/loading/error state 정리
10. keyword set editor/recollect는 MVP 후순위로 둬도 됨

## 15. Final Goal

사용 흐름:

```text
브라우저 접속
-> 키워드 입력 또는 추천 키워드 클릭
-> source / period / related 옵션 선택
-> 분석하기
-> backend_v2 /api/analyze 호출
-> E1/E2/E3 실행
-> /analysis/{run_id} 이동
-> dashboard_data 렌더링
-> source/period/related 변경 시 /reanalyze
```

프론트는 BigWave 분석 결과를 보여주는 클라이언트다.
계산 로직은 절대 프론트에 넣지 않는다.

