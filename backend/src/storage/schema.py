SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS analysis_runs (
  run_id TEXT PRIMARY KEY,
  keyword TEXT,
  keyword_set_mode TEXT,
  sources TEXT,
  period_type TEXT,
  start_date TEXT,
  end_date TEXT,
  include_related INTEGER,
  data_mode TEXT,
  created_at TEXT,
  status TEXT,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS raw_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT,
  term TEXT,
  term_type TEXT,
  term_weight REAL,
  title TEXT,
  url TEXT,
  published_at TEXT,
  collected_at TEXT,
  views REAL,
  likes REAL,
  comments REAL,
  engagements REAL,
  author TEXT,
  snippet TEXT,
  raw_payload TEXT,
  run_id TEXT
);

CREATE TABLE IF NOT EXISTS term_daily_metrics (
  date TEXT,
  source TEXT,
  term TEXT,
  term_type TEXT,
  term_weight REAL,
  mentions REAL,
  views REAL,
  engagements REAL,
  run_id TEXT
);

CREATE TABLE IF NOT EXISTS keyword_set_daily_metrics (
  date TEXT,
  keyword TEXT,
  mentions REAL,
  weighted_mentions REAL,
  views REAL,
  engagements REAL,
  source_count REAL,
  run_id TEXT
);

CREATE TABLE IF NOT EXISTS analysis_results (
  run_id TEXT PRIMARY KEY,
  ts_score REAL,
  status_label TEXT,
  growth_score REAL,
  reaction_score REAL,
  saturation_score REAL,
  decline_risk REAL,
  report_json TEXT,
  created_at TEXT
);
"""
