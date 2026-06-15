# BigWave MVP v2 Team Handoff

이 문서는 BigWave MVP v2를 팀원에게 zip으로 전달하기 위한 빠른 안내서입니다.

## 1. 프로젝트 한 줄 요약

BigWave MVP v2는 F&B 키워드의 온라인 반응을 수집하고, 시계열화한 뒤, Trend Index와 TS Score를 만들어 React 대시보드로 보여주는 프로토타입입니다.

## 2. 현재 핵심 구조

```text
사용자 키워드 입력
-> E1 keyword_v2
-> E2 collector_v2
-> E3 analyzer_v2
-> backend_v2 FastAPI
-> frontend React dashboard
```

## 3. 엔진별 역할

### E1 Keyword Resolver

위치:

```text
keyword_v2/
data/keyword_sets.json
```

역할:

- preset keyword set 확인
- canonical / alias / typo / related 구조 반환
- 등록되지 않은 키워드는 `single_term_fallback`으로 단일 키워드 분석

현재 preset:

- 두쫀쿠
- 버터떡
- 우베

### E2 Collector

위치:

```text
collector_v2/
```

역할:

- YouTube / Naver News / Naver Blog 수집
- E1에서 넘어온 keyword set 전체를 term 단위로 순회
- `term_type`, `term_weight`를 raw row에 같이 저장
- 결과를 `data/raw/{run_id}/`에 저장

주요 출력:

```text
data/raw/{run_id}/raw_all.csv
data/raw/{run_id}/run_meta.json
```

### E3 Trend Analyzer

위치:

```text
analyzer_v2/
```

역할:

- E2 결과 CSV를 읽음
- source / 기간 / related 포함 여부 필터링
- term daily metrics 생성
- keyword-set daily metrics 생성
- Trend Index 생성
- TS Score 계산
- dashboard_data.json 생성

주요 출력:

```text
data/processed/{run_id}/filtered_raw.csv
data/processed/{run_id}/term_daily_metrics.csv
data/processed/{run_id}/keyword_set_daily_metrics.csv
data/processed/{run_id}/weekly_partition.csv
data/processed/{run_id}/trend_features.csv

data/results/{run_id}/trend_index.csv
data/results/{run_id}/ts_score.json
data/results/{run_id}/dashboard_data.json
```

## 4. Backend

위치:

```text
backend_v2/
```

역할:

- FastAPI API 제공
- keyword resolver, collector, analyzer를 연결
- frontend가 호출하는 dashboard response 생성

실행:

```powershell
python -m uvicorn backend_v2.app:app --host 0.0.0.0 --port 8010 --reload
```

확인:

```text
http://127.0.0.1:8010/api/health
```

## 5. Frontend

위치:

```text
frontend/
```

역할:

- 키워드 입력 화면
- source 선택
- 분석 결과 dashboard
- TS Score, Trend Index, source/term breakdown, raw preview 표시

실행:

```powershell
cd frontend
npm install
npm run dev
```

API URL 설정:

```text
frontend/.env
```

예시:

```text
VITE_API_BASE_URL=http://127.0.0.1:8010
```

## 6. 중요한 설계 철학

- E1/E2/E3는 서로 고립된 함수형 모듈로 유지한다.
- frontend는 계산하지 않는다.
- E3가 dashboard용 JSON을 만든다.
- YouTube는 조회수/댓글/좋아요가 있는 핵심 reaction source다.
- Naver News/Blog는 mention/supply를 보는 보조 source다.
- 등록되지 않은 키워드는 분석 불가가 아니라 단일 키워드 분석으로 처리한다.
- 실제 수집 실패 시 sample data로 몰래 대체하지 않는다.

## 7. 먼저 볼 문서

```text
README.md
docs/e2_e3_handoff_summary.md
docs/e3_formula_spec.md
docs/05_frontend_backend_contract.md
docs/lovable_frontend_implementation_prompt.md
```

## 8. 다음 작업 후보

- YouTube collector를 legacy notebook 흐름에 더 가깝게 튜닝
- YouTube reaction 분석과 Naver supply 분석을 dashboard에서 더 명확히 분리
- TS 산식 보정
- frontend 지표 정리
- 배포 환경에서 API key 관리 방식 정리
