import type {
  AnalyzeRequest,
  DashboardData,
  ReanalyzeRequest,
  RecollectRequest,
} from "./types";
import { mockAnalyze, mockGetDashboard, mockReanalyze } from "./mock";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
const USE_MOCK = !API_BASE;

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
  return res.json() as Promise<T>;
}

async function tryReal<T>(fn: () => Promise<T>, fallback: () => T): Promise<T> {
  if (USE_MOCK) return fallback();
  return fn();
}

export type KeywordRecommendation = {
  domain: string;
  keywords: Array<{ keyword: string; label?: string; description?: string }>;
};

export function getKeywords() {
  return tryReal(
    () => request<KeywordRecommendation>("/api/keywords"),
    () => ({
      domain: "F&B",
      keywords: [
        { keyword: "두쫀쿠" },
        { keyword: "버터떡" },
        { keyword: "우베" },
      ],
    }),
  );
}

export function getKeywordSet(keyword: string) {
  return request<unknown>(`/api/keyword-set/${encodeURIComponent(keyword)}`);
}

export function analyze(payload: AnalyzeRequest) {
  return tryReal(
    () =>
      request<DashboardData>("/api/analyze", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    () => mockAnalyze(payload),
  );
}

export function getDashboard(runId: string) {
  return tryReal(
    () => request<DashboardData>(`/api/runs/${encodeURIComponent(runId)}/dashboard`),
    () => mockGetDashboard(runId),
  );
}

export function reanalyze(runId: string, payload: ReanalyzeRequest) {
  return tryReal(
    () =>
      request<DashboardData>(`/api/runs/${encodeURIComponent(runId)}/reanalyze`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    () => mockReanalyze(runId, payload),
  );
}

export function recollect(runId: string, payload: RecollectRequest) {
  return request<DashboardData>(
    `/api/runs/${encodeURIComponent(runId)}/recollect`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export { API_BASE, USE_MOCK };
