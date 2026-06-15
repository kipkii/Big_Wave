import { SOURCE_LABEL, type DashboardData, type SourceKey } from "@/lib/types";

function sanitize(name: string) {
  return name.replace(/[^\w가-힣.-]+/g, "_").slice(0, 60) || "data";
}

export function downloadRawCsv(data: DashboardData) {
  const headers = ["title", "source", "term", "views", "engagements", "url"];
  const escape = (v: unknown) => {
    const s = v == null ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const rows = data.raw_preview.map((r) =>
    [
      r.title,
      SOURCE_LABEL[r.source as SourceKey] ?? r.source,
      r.term,
      r.views,
      r.engagements,
      r.url ?? "",
    ]
      .map(escape)
      .join(","),
  );
  const csv = "\ufeff" + [headers.join(","), ...rows].join("\r\n");
  const filename = `${sanitize(data.keyword)}-raw-${data.run_id}.csv`;

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });

  // IE/Edge legacy
  const nav = navigator as Navigator & {
    msSaveBlob?: (b: Blob, n: string) => boolean;
  };
  if (typeof nav.msSaveBlob === "function") {
    nav.msSaveBlob(blob, filename);
    return;
  }

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  a.target = "_blank";
  a.style.display = "none";
  document.body.appendChild(a);

  try {
    a.click();
  } catch {
    // Sandboxed iframe fallback: open in top window
    window.open(url, "_blank", "noopener,noreferrer");
  }

  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 1000);
}
