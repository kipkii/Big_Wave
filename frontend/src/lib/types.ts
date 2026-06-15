export type SourceKey = "youtube" | "naver_news" | "naver_blog";

export const SOURCE_LABEL: Record<SourceKey, string> = {
  youtube: "유튜브",
  naver_news: "네이버 뉴스",
  naver_blog: "네이버 블로그",
};

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

export type TrendPoint = { period: string; value: number };
export type ContentPoint = {
  period: string;
  value: number;
  weighted_value: number;
  raw_value?: number;
  raw_weighted_value?: number;
};
export type SourceBreakdownItem = { source: string; count: number; ratio: number };
export type WeeklyPartitionPoint = {
  period: string;
  content_supply: number;
  weighted_supply: number;
  views: number;
  view_per_item: number;
  avg_velocity: number;
  demand_pressure: number;
};
export type VelocityZPoint = {
  period: string;
  supply_z: number;
  velocity_z: number;
  pressure_z: number;
  threshold: number;
  baseline: number;
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
    weekly_partition_series?: WeeklyPartitionPoint[];
    velocity_z_series?: VelocityZPoint[];
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

export type AnalyzeRequest = {
  keyword: string;
  sources: SourceKey[];
  analysis_days: number;
  collection_days: number;
  include_related: boolean;
  limits?: Partial<Record<SourceKey, number>>;
  save?: boolean;
};

export type ReanalyzeRequest = {
  selected_sources: SourceKey[];
  analysis_days: number;
  include_related: boolean;
  save?: boolean;
};

export type RecollectRequest = {
  keyword_set: {
    keyword_set: KeywordSet;
    keyword_set_mode: string;
    terms: { term: string; term_type: string; term_weight: number }[];
    core_terms: string[];
    expansion_terms: string[];
  };
  sources: SourceKey[];
  analysis_days: number;
  collection_days: number;
  include_related: boolean;
  limits?: Partial<Record<SourceKey, number>>;
  save?: boolean;
};
