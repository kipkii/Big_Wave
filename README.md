# BigWave MVP v2

BigWave MVP v2 is an F&B trend-analysis prototype.

The project is organized as a real-first pipeline:

```text
E1 Keyword Resolver
-> E2 Collector
-> E3 Trend Analyzer
-> FastAPI Backend
-> React Frontend Dashboard
```

The main preset keyword sets are:

- 두쫀쿠
- 버터떡
- 우베

Unknown keywords are not treated as unsupported. If a keyword is not registered in `keyword_sets.json`, BigWave analyzes it with `single_term_fallback`, using the input keyword as a one-term canonical keyword set.

## Main Folders

```text
keyword_v2/       E1 keyword resolver and preset keyword-set logic
collector_v2/     E2 YouTube, Naver News, Naver Blog collectors and collection router
analyzer_v2/      E3 time-series analyzer, Trend Index, TS Score, dashboard packager
backend_v2/       FastAPI app that connects E1/E2/E3 to API endpoints
frontend/         React dashboard UI
data/             keyword sets, raw runs, processed outputs, result JSON files
docs/             architecture notes, API contract, formulas, handoff documents
notebooks/        module-level verification notebooks
```

## Backend Run

From the project root:

```powershell
python -m uvicorn backend_v2.app:app --host 0.0.0.0 --port 8010 --reload
```

Health check:

```text
http://127.0.0.1:8010/api/health
```

## Frontend Run

```powershell
cd frontend
npm install
npm run dev
```

The frontend reads the backend URL from:

```text
frontend/.env
```

Example:

```text
VITE_API_BASE_URL=http://127.0.0.1:8010
```

## Current MVP Philosophy

- The frontend does not calculate trend scores.
- E3 creates `dashboard_data.json`.
- E2 stores raw collection results under `data/raw/{run_id}/`.
- E3 stores processed files under `data/processed/{run_id}/`.
- E3 stores dashboard/result files under `data/results/{run_id}/`.
- YouTube is the main reaction source because it has views/comments/likes.
- Naver News and Naver Blog are auxiliary supply/mention sources.
- Demo/sample data must not silently replace real collection results.

## Documents To Read First

```text
docs/team_handoff.md
docs/e2_e3_handoff_summary.md
docs/e3_formula_spec.md
docs/05_frontend_backend_contract.md
docs/lovable_frontend_implementation_prompt.md
```

## Notes For Teammates

This zip intentionally keeps source code, docs, notebooks, keyword data, and small local run outputs together so the current working state can be inspected. `node_modules`, frontend build outputs, cache folders, and log files do not need to be shared because they can be regenerated.
