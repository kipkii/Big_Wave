import type {
  AnalyzeRequest,
  DashboardData,
  ReanalyzeRequest,
  SourceKey,
} from "./types";
import { SOURCE_LABEL } from "./types";

function seeded(seed: string) {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) | 0;
  return () => {
    h = (h * 1103515245 + 12345) | 0;
    return ((h >>> 16) & 0x7fff) / 0x7fff;
  };
}

function makeSeries(days: number, rng: () => number, base = 50, vol = 25) {
  const out: { period: string; value: number }[] = [];
  const today = new Date();
  let v = base;
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    v = Math.max(5, v + (rng() - 0.45) * vol);
    out.push({
      period: `${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`,
      value: Math.round(v),
    });
  }
  return out;
}

export function buildMockDashboard(args: {
  runId: string;
  keyword: string;
  sources: SourceKey[];
  analysis_days: number;
  include_related: boolean;
}): DashboardData {
  const { runId, keyword, sources, analysis_days, include_related } = args;
  const rng = seeded(`${runId}:${keyword}:${sources.join(",")}:${analysis_days}`);
  const trend = makeSeries(analysis_days, rng, 55, 18);
  const content = trend.map((p) => ({
    period: p.period,
    value: Math.round(p.value * (0.6 + rng() * 0.6)),
    weighted_value: Math.round(p.value * (0.8 + rng() * 0.7)),
  }));
  const totals: Record<string, number> = {};
  sources.forEach((s) => (totals[s] = Math.round(80 + rng() * 300)));
  const sum = Object.values(totals).reduce((a, b) => a + b, 0) || 1;
  const breakdown = sources.map((s) => ({
    source: s,
    count: totals[s],
    ratio: totals[s] / sum,
  }));
  const ts = Math.round((40 + rng() * 55) * 10) / 10;
  const labels = ["관망", "성장", "과열", "주의"];

  const baseTerms = [
    { term: keyword, term_type: "canonical" },
    { term: `${keyword} 추천`, term_type: "related" },
    { term: `${keyword} 후기`, term_type: "related" },
    { term: `${keyword} 가격`, term_type: "related" },
    { term: `${keyword} 비교`, term_type: "alias" },
  ];
  const terms = (include_related ? baseTerms : baseTerms.slice(0, 2)).map((t) => {
    const count = Math.round(20 + rng() * 200);
    return { ...t, count, weighted_count: count * (0.8 + rng() * 0.6) };
  });

  const titles = [
    `${keyword}, 요즘 왜 이렇게 핫할까`,
    `${keyword} 솔직 후기 모음`,
    `${keyword} 구매 전 꼭 봐야 할 영상`,
    `${keyword} vs 경쟁 키워드 비교`,
    `${keyword} 트렌드 한 달 정리`,
    `초보를 위한 ${keyword} 가이드`,
    `${keyword}의 진짜 가치`,
    `${keyword} 관련 뉴스 브리핑`,
  ];
  const raw = titles.map((title, i) => ({
    title,
    source: sources[i % sources.length],
    term: terms[i % terms.length].term,
    term_type: terms[i % terms.length].term_type,
    published_at: new Date(Date.now() - i * 86_400_000).toISOString(),
    url: "https://example.com",
    views: Math.round(500 + rng() * 50000),
    engagements: Math.round(10 + rng() * 2000),
  }));

  return {
    run_id: runId,
    keyword,
    keyword_set: {
      canonical: keyword,
      alias: [`${keyword} 비교`],
      typo: [],
      related: include_related ? [`${keyword} 추천`, `${keyword} 후기`, `${keyword} 가격`] : [],
    },
    keyword_set_mode: "single_term_fallback",
    analysis_options: {
      selected_sources: sources,
      analysis_days,
      include_related,
      date_basis: "published_at",
      period_anchor: "today",
      rerun_policy: "manual",
    },
    available_sources: sources,
    missing_sources: [],
    warnings: ["목업 데이터입니다. 백엔드 연결 시 실제 데이터로 대체돼요."],
    summary: {
      ts_score: ts,
      status_label: labels[Math.floor(rng() * labels.length)],
      collected_items: raw.length * 12,
      last_updated: new Date().toLocaleString("ko-KR"),
    },
    component_scores: {
      growth_score: Math.round(rng() * 1000) / 10,
      reaction_score: Math.round(rng() * 1000) / 10,
      saturation_score: Math.round(rng() * 1000) / 10,
      decline_risk: Math.round(rng() * 1000) / 10,
    },
    charts: {
      trend_index_series: trend,
      content_series: content,
      source_breakdown: breakdown,
    },
    term_breakdown: terms,
    raw_preview: raw,
    methodology: {
      formula_version: "mock-v0.1",
      description:
        "성장·반응·포화·하락 위험 네 가지 지표를 가중 평균해 TS Score를 계산합니다.",
      components: [
        { name: "Growth", description: "최근 구간의 검색·노출 증가율" },
        { name: "Reaction", description: "조회 대비 좋아요·댓글 비율" },
        { name: "Saturation", description: "콘텐츠 공급량의 누적 정도" },
        { name: "Decline", description: "최근 7일 추세 하락 위험" },
      ],
      notice: "본 화면은 목업이며, 실제 분석 결과와 다를 수 있습니다.",
    },
    report: {
      summary: `"${keyword}" 키워드는 최근 ${analysis_days}일간 ${
        ts >= 70 ? "강한 상승세" : ts >= 50 ? "안정적인 관심도" : "완만한 흐름"
      }을 보이고 있어요. ${SOURCE_LABEL[sources[0]] ?? sources[0]} 채널의 반응이 가장 두드러집니다.`,
      evidence: `총 ${raw.length * 12}건 수집, 일평균 트렌드 지수 ${Math.round(
        trend.reduce((a, b) => a + b.value, 0) / trend.length,
      )}.`,
      risk: ts < 40 ? "콘텐츠 포화로 노출 경쟁이 치열할 수 있어요." : "단기 변동성 주의.",
      recommendation: include_related
        ? "연관 키워드를 묶어서 시리즈 콘텐츠로 풀어보세요."
        : "핵심 키워드 단일 노출로 메시지를 선명하게 유지하세요.",
    },
  };
}

const STORE_KEY = "bigwave_mock_runs_v1";

type Stored = { runId: string; keyword: string; sources: SourceKey[]; analysis_days: number; include_related: boolean };

function readStore(): Record<string, Stored> {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(window.sessionStorage.getItem(STORE_KEY) ?? "{}");
  } catch {
    return {};
  }
}
function writeStore(s: Record<string, Stored>) {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(STORE_KEY, JSON.stringify(s));
  } catch {
    /* ignore */
  }
}

export function mockAnalyze(req: AnalyzeRequest): DashboardData {
  const runId = `mock-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
  const stored: Stored = {
    runId,
    keyword: req.keyword,
    sources: req.sources,
    analysis_days: req.analysis_days,
    include_related: req.include_related,
  };
  const s = readStore();
  s[runId] = stored;
  writeStore(s);
  return buildMockDashboard(stored);
}

export function mockGetDashboard(runId: string): DashboardData {
  const s = readStore();
  const stored = s[runId] ?? {
    runId,
    keyword: "샘플 키워드",
    sources: ["youtube", "naver_news", "naver_blog"] as SourceKey[],
    analysis_days: 30,
    include_related: true,
  };
  return buildMockDashboard(stored);
}

export function mockReanalyze(runId: string, req: ReanalyzeRequest): DashboardData {
  const s = readStore();
  const prev = s[runId];
  const stored: Stored = {
    runId,
    keyword: prev?.keyword ?? "샘플 키워드",
    sources: req.selected_sources,
    analysis_days: req.analysis_days,
    include_related: req.include_related,
  };
  s[runId] = stored;
  writeStore(s);
  return buildMockDashboard(stored);
}
