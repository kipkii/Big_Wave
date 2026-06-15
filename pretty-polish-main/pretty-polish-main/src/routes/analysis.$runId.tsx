import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  Loader2,
  AlertTriangle,
  RefreshCw,
  Sparkles,
  ExternalLink,
  Download,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { getDashboard, reanalyze } from "@/lib/api";
import { SOURCE_LABEL, type DashboardData, type SourceKey } from "@/lib/types";
import { downloadRawCsv } from "@/lib/csv";

export const Route = createFileRoute("/analysis/$runId")({
  component: AnalysisPage,
});

const PERIODS = [7, 14, 30, 90] as const;
const ALL_SOURCES: SourceKey[] = ["youtube", "naver_news", "naver_blog"];
const SOURCE_COLORS: Record<string, string> = {
  youtube: "oklch(0.62 0.22 25)",
  naver_news: "oklch(0.65 0.18 150)",
  naver_blog: "oklch(0.55 0.16 150)",
};

function AnalysisPage() {
  const { runId } = Route.useParams();
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [filtering, setFiltering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // local controls
  const [selected, setSelected] = useState<SourceKey[]>([]);
  const [period, setPeriod] = useState<number>(30);
  const [includeRelated, setIncludeRelated] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getDashboard(runId)
      .then((d) => {
        if (cancelled) return;
        setData(d);
        setSelected(d.analysis_options.selected_sources as SourceKey[]);
        setPeriod(d.analysis_options.analysis_days);
        setIncludeRelated(d.analysis_options.include_related);
      })
      .catch((e: Error) => {
        if (cancelled) return;
        setError(e.message || "대시보드를 불러오지 못했습니다.");
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [runId]);

  const applyReanalyze = async (
    next: Partial<{
      sources: SourceKey[];
      analysis_days: number;
      include_related: boolean;
    }>,
  ) => {
    const nextSources = next.sources ?? selected;
    const nextDays = next.analysis_days ?? period;
    const nextRel = next.include_related ?? includeRelated;
    if (nextSources.length === 0) return;
    setFiltering(true);
    setError(null);
    try {
      const d = await reanalyze(runId, {
        selected_sources: nextSources,
        analysis_days: nextDays,
        include_related: nextRel,
        save: true,
      });
      setData(d);
      setSelected(d.analysis_options.selected_sources as SourceKey[]);
      setPeriod(d.analysis_options.analysis_days);
      setIncludeRelated(d.analysis_options.include_related);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "재분석에 실패했습니다.",
      );
    } finally {
      setFiltering(false);
    }
  };

  if (loading) {
    return (
      <Centered>
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
        <p className="mt-3 text-sm text-muted-foreground">대시보드를 불러오고 있어요…</p>
      </Centered>
    );
  }

  if (error && !data) {
    return (
      <Centered>
        <AlertTriangle className="size-6 text-destructive" />
        <p className="mt-3 text-sm font-medium">대시보드를 불러오지 못했어요</p>
        <p className="mt-1 text-xs text-muted-foreground max-w-md">{error}</p>
        <div className="mt-4 flex gap-2">
          <button
            onClick={() => router.invalidate()}
            className="rounded-md border border-border bg-card px-3 py-1.5 text-sm hover:bg-accent"
          >
            다시 시도
          </button>
          <Link
            to="/"
            className="rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:bg-primary/90"
          >
            홈으로
          </Link>
        </div>
      </Centered>
    );
  }

  if (!data) return null;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto max-w-6xl flex items-center justify-between px-6 h-14">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="size-4" /> 새 분석
          </Link>
          <div className="text-xs text-muted-foreground">
            run · <span className="font-mono">{data.run_id.slice(0, 12)}</span>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-8 space-y-6">
        {/* Title + summary */}
        <section className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs text-muted-foreground">키워드</p>
            <h1 className="text-3xl font-semibold tracking-tight">{data.keyword}</h1>
            <p className="mt-1 text-xs text-muted-foreground">
              마지막 업데이트 · {data.summary.last_updated}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ScoreCard
              label="TS Score"
              value={data.summary.ts_score.toFixed(1)}
              status={data.summary.status_label}
            />
            <SmallStat label="수집 항목" value={data.summary.collected_items.toLocaleString()} />
          </div>
        </section>

        {/* Warnings */}
        {data.warnings?.length > 0 && (
          <div className="rounded-xl border border-amber-400/30 bg-amber-50/60 dark:bg-amber-500/10 px-4 py-3 text-sm">
            <div className="flex items-center gap-2 font-medium">
              <AlertTriangle className="size-4 text-amber-600" /> 알림
            </div>
            <ul className="mt-1.5 list-disc list-inside text-xs text-muted-foreground space-y-0.5">
              {data.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Controls */}
        <section className="rounded-2xl border border-border bg-card p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex flex-wrap items-center gap-2">
              {ALL_SOURCES.map((s) => {
                const on = selected.includes(s);
                const missing = data.missing_sources?.includes(s);
                return (
                  <button
                    key={s}
                    type="button"
                    disabled={filtering}
                    onClick={() => {
                      const nextSel = on
                        ? selected.filter((x) => x !== s)
                        : [...selected, s];
                      setSelected(nextSel);
                      void applyReanalyze({ sources: nextSel });
                    }}
                    className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs transition ${
                      on
                        ? "border-primary/30 bg-primary/10 text-foreground"
                        : "border-border bg-background text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <span
                      className="size-1.5 rounded-full"
                      style={{ backgroundColor: SOURCE_COLORS[s] }}
                    />
                    {SOURCE_LABEL[s]}
                    {missing && (
                      <span className="ml-1 rounded-full bg-amber-500/20 text-amber-700 px-1.5 py-0.5 text-[10px]">
                        재수집 필요
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="inline-flex items-center gap-1 rounded-full border border-border bg-background p-1">
              {PERIODS.map((p) => (
                <button
                  key={p}
                  type="button"
                  disabled={filtering}
                  onClick={() => {
                    setPeriod(p);
                    void applyReanalyze({ analysis_days: p });
                  }}
                  className={`px-3 py-1 text-xs rounded-full transition ${
                    period === p
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {p}일
                </button>
              ))}
            </div>

            <button
              type="button"
              disabled={filtering}
              onClick={() => {
                const v = !includeRelated;
                setIncludeRelated(v);
                void applyReanalyze({ include_related: v });
              }}
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs transition ${
                includeRelated
                  ? "border-primary/30 bg-primary/10 text-foreground"
                  : "border-border bg-background text-muted-foreground hover:text-foreground"
              }`}
            >
              <Sparkles className="size-3.5" />
              연관 키워드 포함
            </button>

            <div className="ml-auto flex items-center gap-2">
              {filtering && (
                <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Loader2 className="size-3.5 animate-spin" /> 필터 적용 중
                </span>
              )}
              <button
                type="button"
                disabled={filtering}
                onClick={() => void applyReanalyze({})}
                className="inline-flex items-center gap-1.5 rounded-md border border-border bg-background px-3 py-1.5 text-xs hover:bg-accent disabled:opacity-50"
              >
                <RefreshCw className="size-3.5" /> 재분석
              </button>
              <button
                type="button"
                disabled
                title="MVP에서 곧 제공돼요"
                className="rounded-md border border-border bg-background px-3 py-1.5 text-xs opacity-50 cursor-not-allowed"
              >
                키워드 세트 수정
              </button>
            </div>
          </div>

          {error && (
            <p className="mt-3 text-xs text-destructive">{error}</p>
          )}
        </section>

        {/* Component scores */}
        <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <SmallStat label="성장" value={data.component_scores.growth_score.toFixed(1)} />
          <SmallStat label="반응" value={data.component_scores.reaction_score.toFixed(1)} />
          <SmallStat label="포화" value={data.component_scores.saturation_score.toFixed(1)} />
          <SmallStat
            label="하락 위험"
            value={data.component_scores.decline_risk.toFixed(1)}
          />
        </section>

        {/* Charts */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card title="Trend Index">
            <ChartBox>
              <LineChart data={data.charts.trend_index_series}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="period" fontSize={11} stroke="var(--muted-foreground)" />
                <YAxis fontSize={11} stroke="var(--muted-foreground)" />
                <Tooltip contentStyle={tooltipStyle} />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="var(--primary)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ChartBox>
          </Card>

          <Card title="콘텐츠 볼륨">
            <ChartBox>
              <BarChart data={data.charts.content_series}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="period" fontSize={11} stroke="var(--muted-foreground)" />
                <YAxis fontSize={11} stroke="var(--muted-foreground)" />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="value" fill="var(--primary)" name="원본" />
                <Bar dataKey="weighted_value" fill="var(--primary-glow)" name="가중" />
              </BarChart>
            </ChartBox>
          </Card>

          <Card title="채널 비중">
            <ChartBox>
              <PieChart>
                <Pie
                  data={data.charts.source_breakdown}
                  dataKey="count"
                  nameKey="source"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={(e) => SOURCE_LABEL[e.source as SourceKey] ?? e.source}
                  fontSize={11}
                >
                  {data.charts.source_breakdown.map((s) => (
                    <Cell key={s.source} fill={SOURCE_COLORS[s.source] ?? "var(--primary)"} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ChartBox>
          </Card>

          <Card title="Term Breakdown">
            <div className="max-h-[260px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="text-xs text-muted-foreground">
                  <tr className="border-b border-border">
                    <th className="text-left py-2">Term</th>
                    <th className="text-left">유형</th>
                    <th className="text-right">건수</th>
                    <th className="text-right">가중</th>
                  </tr>
                </thead>
                <tbody>
                  {data.term_breakdown.map((t) => (
                    <tr key={t.term} className="border-b border-border/60">
                      <td className="py-1.5">{t.term}</td>
                      <td className="text-xs text-muted-foreground">{t.term_type}</td>
                      <td className="text-right tabular-nums">{t.count}</td>
                      <td className="text-right tabular-nums">{t.weighted_count.toFixed(1)}</td>
                    </tr>
                  ))}
                  {data.term_breakdown.length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-6 text-center text-xs text-muted-foreground">
                        데이터가 없어요
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </section>

        {/* Keyword set */}
        <Card title={`키워드 세트 · ${data.keyword_set_mode}`}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <KsCol label="canonical" items={[data.keyword_set.canonical]} />
            <KsCol label="alias" items={data.keyword_set.alias} />
            <KsCol label="typo" items={data.keyword_set.typo} />
            <KsCol label="related" items={data.keyword_set.related} />
          </div>
        </Card>

        {/* Report */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card title="Insight Report">
            <div className="space-y-3 text-sm">
              <ReportRow label="요약" text={data.report.summary} />
              <ReportRow label="근거" text={data.report.evidence} />
              <ReportRow label="리스크" text={data.report.risk} />
              <ReportRow label="권장" text={data.report.recommendation} />
            </div>
          </Card>

          <Card title={`방법론 · ${data.methodology.formula_version}`}>
            <p className="text-sm text-muted-foreground">{data.methodology.description}</p>
            <ul className="mt-3 space-y-1.5 text-sm">
              {data.methodology.components.map((c) => (
                <li key={c.name}>
                  <span className="font-medium">{c.name}</span>{" "}
                  <span className="text-muted-foreground">— {c.description}</span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-muted-foreground">{data.methodology.notice}</p>
          </Card>
        </section>

        {/* Raw preview */}
        <Card
          title="원본 데이터 미리보기"
          action={
            <button
              type="button"
              onClick={() => downloadRawCsv(data)}
              disabled={data.raw_preview.length === 0}
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download className="size-3.5" />
              CSV 다운로드
            </button>
          }
        >
          <div className="max-h-[360px] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground sticky top-0 bg-card">
                <tr className="border-b border-border">
                  <th className="text-left py-2">제목</th>
                  <th className="text-left">채널</th>
                  <th className="text-left">Term</th>
                  <th className="text-right">조회</th>
                  <th className="text-right">반응</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data.raw_preview.map((r, i) => (
                  <tr key={i} className="border-b border-border/60">
                    <td className="py-1.5 max-w-[360px] truncate">{r.title}</td>
                    <td className="text-xs text-muted-foreground">
                      {SOURCE_LABEL[r.source as SourceKey] ?? r.source}
                    </td>
                    <td className="text-xs">{r.term}</td>
                    <td className="text-right tabular-nums">{r.views.toLocaleString()}</td>
                    <td className="text-right tabular-nums">{r.engagements.toLocaleString()}</td>
                    <td className="text-right">
                      {r.url && (
                        <a
                          href={r.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex text-muted-foreground hover:text-foreground"
                        >
                          <ExternalLink className="size-3.5" />
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
                {data.raw_preview.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-xs text-muted-foreground">
                      미리보기 가능한 항목이 없어요
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </main>
  );
}

const tooltipStyle = {
  backgroundColor: "var(--card)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  fontSize: 12,
};

function Centered({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground px-6 text-center">
      {children}
    </main>
  );
}

function Card({
  title,
  children,
  action,
}: {
  title: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-border bg-card p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold">{title}</h3>
        {action}
      </div>
      {children}
    </div>
  );
}



function ChartBox({ children }: { children: React.ReactElement }) {
  return (
    <div className="h-[240px]">
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  );
}

function ScoreCard({
  label,
  value,
  status,
}: {
  label: string;
  value: string;
  status: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card px-4 py-3 text-right min-w-[140px]">
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <p className="text-2xl font-semibold tabular-nums">{value}</p>
      <p className="text-[11px] text-primary">{status}</p>
    </div>
  );
}

function SmallStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-card px-4 py-3">
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function KsCol({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground mb-1.5">{label}</p>
      <div className="flex flex-wrap gap-1">
        {items.filter(Boolean).length === 0 ? (
          <span className="text-xs text-muted-foreground">—</span>
        ) : (
          items.filter(Boolean).map((it) => (
            <span
              key={it}
              className="rounded-full border border-border bg-background px-2 py-0.5 text-xs"
            >
              {it}
            </span>
          ))
        )}
      </div>
    </div>
  );
}

function ReportRow({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-0.5 whitespace-pre-wrap leading-relaxed">{text || "—"}</p>
    </div>
  );
}
