import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Search,
  HelpCircle,
  Youtube,
  PanelLeftClose,
  PanelLeftOpen,
  Clock,
  X,
  ShieldCheck,
  Sparkles,
  Loader2,
  Newspaper,
  BookOpen,
} from "lucide-react";
import { analyze, getKeywords, type KeywordRecommendation } from "@/lib/api";
import { SOURCE_LABEL, type SourceKey } from "@/lib/types";

export const Route = createFileRoute("/")({
  component: Index,
});

type Recent = { id: string; term: string; at: string };

const PERIODS = [7, 14, 30, 90] as const;
type Period = (typeof PERIODS)[number];

const CHANNELS: {
  key: SourceKey;
  icon: React.ReactNode;
  dot: string;
}[] = [
  { key: "youtube", icon: <Youtube className="size-3.5" />, dot: "oklch(0.62 0.22 25)" },
  { key: "naver_news", icon: <Newspaper className="size-3.5" />, dot: "oklch(0.65 0.18 150)" },
  { key: "naver_blog", icon: <BookOpen className="size-3.5" />, dot: "oklch(0.55 0.16 150)" },
];

const RECENTS_KEY = "bigwave_recents_v1";

function loadRecents(): Recent[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(RECENTS_KEY);
    return raw ? (JSON.parse(raw) as Recent[]) : [];
  } catch {
    return [];
  }
}

function Index() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [recents, setRecents] = useState<Recent[]>([]);
  const [helpOpen, setHelpOpen] = useState(false);
  const [enabled, setEnabled] = useState<Record<SourceKey, boolean>>({
    youtube: true,
    naver_news: true,
    naver_blog: true,
  });
  const [period, setPeriod] = useState<Period>(30);
  const [includeRelated, setIncludeRelated] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recs, setRecs] = useState<KeywordRecommendation | null>(null);

  useEffect(() => {
    setRecents(loadRecents());
    getKeywords()
      .then(setRecs)
      .catch(() => {
        // backend may be offline; show fallback
        setRecs({
          domain: "F&B",
          keywords: [
            { keyword: "두쫀쿠" },
            { keyword: "버터떡" },
            { keyword: "우베" },
          ],
        });
      });
  }, []);

  const persistRecents = (next: Recent[]) => {
    setRecents(next);
    try {
      window.localStorage.setItem(RECENTS_KEY, JSON.stringify(next));
    } catch {
      /* ignore */
    }
  };

  const toggle = (k: SourceKey) =>
    setEnabled((s) => ({ ...s, [k]: !s[k] }));

  const submit = async (term?: string) => {
    const q = (term ?? query).trim();
    if (!q || loading) return;
    const sources = CHANNELS.filter((c) => enabled[c.key]).map((c) => c.key);
    if (sources.length === 0) {
      setError("검색할 채널을 한 개 이상 켜주세요");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const data = await analyze({
        keyword: q,
        sources,
        analysis_days: period,
        collection_days: Math.max(90, period),
        include_related: includeRelated,
        limits: { youtube: 250, naver_news: 300, naver_blog: 300 },
        save: true,
      });
      const entry: Recent = {
        id: crypto.randomUUID(),
        term: q,
        at: new Date().toISOString(),
      };
      const next = [entry, ...recents.filter((r) => r.term !== q)].slice(0, 20);
      persistRecents(next);
      navigate({ to: "/analysis/$runId", params: { runId: data.run_id } });
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "분석을 완료하지 못했습니다. API 키, 네트워크, 선택한 채널을 확인해주세요.",
      );
    } finally {
      setLoading(false);
    }
  };

  const activeCount = Object.values(enabled).filter(Boolean).length;

  return (
    <main className="flex min-h-screen bg-background text-foreground">
      {/* Sidebar */}
      <aside
        className={`shrink-0 border-r border-border bg-sidebar transition-[width] duration-300 ease-out ${
          sidebarOpen ? "w-72" : "w-0"
        } overflow-hidden`}
      >
        <div className="w-72 h-screen sticky top-0 flex flex-col">
          <div className="flex items-center justify-between px-4 h-14 border-b border-sidebar-border">
            <div className="flex items-center gap-2">
              <Clock className="size-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold">최근 검색어</h2>
            </div>
            <span className="text-xs text-muted-foreground">{recents.length}</span>
          </div>

          <div className="flex-1 overflow-y-auto px-2 py-2">
            {recents.length === 0 ? (
              <p className="px-2 py-10 text-center text-xs text-muted-foreground">
                아직 검색 기록이 없어요
              </p>
            ) : (
              recents.map((r) => (
                <div
                  key={r.id}
                  className="group flex items-center gap-1 rounded-lg hover:bg-sidebar-accent transition-colors"
                >
                  <button
                    onClick={() => setQuery(r.term)}
                    className="flex-1 min-w-0 px-3 py-2.5 text-left"
                  >
                    <p className="truncate text-sm">{r.term}</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      {formatRel(r.at)}
                    </p>
                  </button>
                  <button
                    onClick={() =>
                      persistRecents(recents.filter((x) => x.id !== r.id))
                    }
                    aria-label="삭제"
                    className="opacity-0 group-hover:opacity-100 mr-2 rounded p-1 hover:bg-background transition"
                  >
                    <X className="size-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>

          {recents.length > 0 && (
            <div className="border-t border-sidebar-border p-2">
              <button
                onClick={() => persistRecents([])}
                className="w-full text-xs text-muted-foreground hover:text-foreground py-2 rounded-md hover:bg-sidebar-accent transition"
              >
                전체 지우기
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Main */}
      <section className="relative flex-1 flex flex-col min-w-0">
        <header className="flex items-center justify-between px-4 h-14 border-b border-border">
          <button
            onClick={() => setSidebarOpen((s) => !s)}
            aria-label="사이드바 열기/닫기"
            className="inline-flex size-9 items-center justify-center rounded-md hover:bg-accent transition-colors"
          >
            {sidebarOpen ? <PanelLeftClose className="size-4" /> : <PanelLeftOpen className="size-4" />}
          </button>
          <button
            onClick={() => setHelpOpen(true)}
            aria-label="도움말"
            className="inline-flex size-9 items-center justify-center rounded-md hover:bg-accent transition-colors"
          >
            <HelpCircle className="size-4" />
          </button>
        </header>

        <div className="flex-1 flex flex-col items-center justify-center px-6 py-10">
          <div className="w-full max-w-2xl">
            <div className="flex flex-col items-center mb-8">
              <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-center">
                무엇이든 물어보세요
              </h1>
              <p className="mt-3 text-sm text-muted-foreground text-center">
                선택한 기간과 채널에서 키워드 트렌드를 분석해요
              </p>
              <div className="mt-5 inline-flex items-center gap-1 rounded-full border border-border bg-card p-1">
                {PERIODS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPeriod(p)}
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
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                void submit();
              }}
              className="relative"
            >
              <div className="flex items-center gap-2 rounded-2xl bg-card border border-border pl-4 pr-2 py-1.5 shadow-[var(--shadow-soft)] focus-within:border-ring transition-colors">
                <Search className="size-4 text-muted-foreground shrink-0" />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="키워드를 입력하세요"
                  disabled={loading}
                  className="flex-1 bg-transparent py-2.5 text-base outline-none placeholder:text-muted-foreground disabled:opacity-60"
                />
                <button
                  type="submit"
                  disabled={!query.trim() || activeCount === 0 || loading}
                  className="shrink-0 inline-flex items-center gap-1.5 rounded-xl bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed transition"
                >
                  {loading ? <Loader2 className="size-4 animate-spin" /> : null}
                  {loading ? "분석 중" : "분석"}
                </button>
              </div>
            </form>

            <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
              {CHANNELS.map((c) => (
                <ChannelChip
                  key={c.key}
                  label={SOURCE_LABEL[c.key]}
                  dot={c.dot}
                  icon={c.icon}
                  on={enabled[c.key]}
                  onToggle={() => toggle(c.key)}
                />
              ))}
            </div>

            <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => setIncludeRelated((v) => !v)}
                aria-pressed={includeRelated}
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-all ${
                  includeRelated
                    ? "border-primary/30 bg-primary/10 text-foreground"
                    : "border-border bg-card text-muted-foreground hover:text-foreground"
                }`}
              >
                <Sparkles className="size-3.5" />
                연관 키워드 포함
                <SwitchDot on={includeRelated} />
              </button>
            </div>

            <p className="mt-4 text-center text-xs text-muted-foreground">
              {activeCount === 0
                ? "검색할 채널을 한 개 이상 켜주세요"
                : `${activeCount}개 채널 · 최근 ${period}일 분석`}
            </p>

            {error && (
              <div className="mt-4 rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
                {error}
              </div>
            )}

            {recs && recs.keywords.length > 0 && (
              <div className="mt-10">
                <p className="text-xs text-muted-foreground mb-2 text-center">
                  추천 키워드 · {recs.domain}
                </p>
                <div className="flex flex-wrap items-center justify-center gap-2">
                  {recs.keywords.slice(0, 8).map((k) => (
                    <button
                      key={k.keyword}
                      type="button"
                      disabled={loading}
                      onClick={() => {
                        setQuery(k.keyword);
                        void submit(k.keyword);
                      }}
                      className="rounded-full border border-border bg-card px-3 py-1.5 text-xs hover:bg-accent transition disabled:opacity-50"
                    >
                      {k.label ?? k.keyword}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {loading && (
              <p className="mt-6 text-center text-xs text-muted-foreground">
                선택한 채널에서 데이터를 수집하고 있어요. 잠시만요…
              </p>
            )}
          </div>
        </div>

        <footer className="border-t border-border px-6 py-4 flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="size-3.5" />
          입력한 키워드는 기기에만 저장돼요
        </footer>

        {helpOpen && (
          <div
            className="fixed inset-0 z-50 bg-foreground/30 backdrop-blur-sm flex items-center justify-center px-4 animate-fade-in"
            onClick={() => setHelpOpen(false)}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-md rounded-2xl bg-card p-6 shadow-[var(--shadow-elegant)] border border-border animate-scale-in"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">사용 방법</h3>
                <button
                  onClick={() => setHelpOpen(false)}
                  className="rounded-md p-1 hover:bg-accent"
                  aria-label="닫기"
                >
                  <X className="size-4" />
                </button>
              </div>
              <ol className="space-y-2 text-sm text-muted-foreground list-decimal list-inside">
                <li>분석할 채널을 스위치로 켜요.</li>
                <li>분석 기간과 연관 키워드 포함 여부를 선택해요.</li>
                <li>키워드를 입력하고 분석을 눌러요.</li>
                <li>결과 페이지에서 옵션을 바꾸면 빠르게 재분석돼요.</li>
              </ol>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

function formatRel(iso: string): string {
  try {
    const t = new Date(iso).getTime();
    const diff = Date.now() - t;
    if (diff < 60_000) return "방금 전";
    if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}분 전`;
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}시간 전`;
    return `${Math.floor(diff / 86_400_000)}일 전`;
  } catch {
    return iso;
  }
}


function SwitchDot({ on }: { on: boolean }) {
  return (
    <span
      className={`relative ml-1 inline-flex h-4 w-7 shrink-0 items-center rounded-full transition-colors ${
        on ? "bg-primary" : "bg-input"
      }`}
    >
      <span
        className={`inline-block size-3 rounded-full bg-white shadow-sm transition-transform duration-200 ${
          on ? "translate-x-[14px]" : "translate-x-0.5"
        }`}
      />
    </span>
  );
}

function ChannelChip({
  label,
  dot,
  icon,
  on,
  onToggle,
}: {
  label: string;
  dot: string;
  icon: React.ReactNode;
  on: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={on}
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-all ${
        on
          ? "border-primary/30 bg-primary/10 text-foreground"
          : "border-border bg-card text-muted-foreground hover:text-foreground hover:bg-accent"
      }`}
    >
      <span
        className="size-1.5 rounded-full"
        style={{ backgroundColor: on ? dot : "oklch(0.78 0.004 285)" }}
        aria-hidden
      />
      {icon}
      <span>{label}</span>
      <SwitchDot on={on} />
    </button>
  );
}
