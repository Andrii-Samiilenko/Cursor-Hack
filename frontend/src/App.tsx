import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";

type RankedFile = {
  path: string;
  score: number;
  confidence: number;
  reasons: string[];
};

type Stats = {
  original_tokens: number;
  compressed_tokens: number;
  tokens_saved: number;
  reduction_pct: number;
  original_chars: number;
  compressed_chars: number;
  ready_message_tokens: number;
  risk_note: string;
  tokenizer_note: string;
};

type Cost = {
  model_label: string;
  estimated_original_cost_usd: number;
  estimated_compressed_cost_usd: number;
  cost_saved_usd: number;
};

type AnalyzeResponse = {
  ok: boolean;
  error: string | null;
  cleaned_prompt: string;
  audit_log: string[];
  source_label: string;
  files_scanned: number;
  files_selected: number;
  ranked_files: RankedFile[];
  compressed_context: string;
  compressed_context_md: string;
  ready_prompt: string;
  stats: Stats | null;
  cost: Cost | null;
  raw_bundle_preview: string;
  export_markdown: string;
  stats_before_label: string;
  stats_after_label: string;
};

const ERRORS: Record<string, string> = {
  network: "Could not reach the API. Start the backend (see README).",
  empty_prompt: "Write your prompt — what should the model do?",
  bad_repo: "Repository path is not a valid folder on this machine.",
  empty_repo: "That folder has no matching code files (.py, .js, .ts, .md, …).",
  no_source: "Add a repository path or paste files using the -----FILE: markers.",
  analysis_failed: "Analysis crashed on the server — check the API terminal log.",
  server: "Server returned an error. Is the API running on port 8000?",
  bad_json: "Bad response from server.",
};

/** Huge markdown kills the tab (ReactMarkdown). Previews are clipped; Copy / Download stay full. */
const MAX_MD_PREVIEW_CHARS = 18_000;
const MAX_PRE_PREVIEW_CHARS = 28_000;

function num(v: unknown, fallback = 0): number {
  return typeof v === "number" && Number.isFinite(v) ? v : fallback;
}

function normalizeAnalyzeResponse(raw: Record<string, unknown>): AnalyzeResponse {
  const st = raw.stats as Record<string, unknown> | undefined;
  const co = raw.cost as Record<string, unknown> | undefined;
  const stats: Stats | null =
    st && typeof st === "object"
      ? {
          original_tokens: num(st.original_tokens),
          compressed_tokens: num(st.compressed_tokens),
          tokens_saved: num(st.tokens_saved),
          reduction_pct: num(st.reduction_pct),
          original_chars: num(st.original_chars),
          compressed_chars: num(st.compressed_chars),
          ready_message_tokens: num(st.ready_message_tokens),
          risk_note: typeof st.risk_note === "string" ? st.risk_note : "",
          tokenizer_note: typeof st.tokenizer_note === "string" ? st.tokenizer_note : "",
        }
      : null;
  const cost: Cost | null =
    co && typeof co === "object"
      ? {
          model_label: typeof co.model_label === "string" ? co.model_label : "",
          estimated_original_cost_usd: num(co.estimated_original_cost_usd),
          estimated_compressed_cost_usd: num(co.estimated_compressed_cost_usd),
          cost_saved_usd: num(co.cost_saved_usd),
        }
      : null;
  return {
    ok: Boolean(raw.ok),
    error: typeof raw.error === "string" ? raw.error : null,
    cleaned_prompt: typeof raw.cleaned_prompt === "string" ? raw.cleaned_prompt : "",
    audit_log: Array.isArray(raw.audit_log) ? (raw.audit_log as string[]) : [],
    source_label: typeof raw.source_label === "string" ? raw.source_label : "",
    files_scanned: num(raw.files_scanned),
    files_selected: num(raw.files_selected),
    ranked_files: Array.isArray(raw.ranked_files) ? (raw.ranked_files as RankedFile[]) : [],
    compressed_context: typeof raw.compressed_context === "string" ? raw.compressed_context : "",
    compressed_context_md: typeof raw.compressed_context_md === "string" ? raw.compressed_context_md : "",
    ready_prompt: typeof raw.ready_prompt === "string" ? raw.ready_prompt : "",
    stats,
    cost,
    raw_bundle_preview: typeof raw.raw_bundle_preview === "string" ? raw.raw_bundle_preview : "",
    export_markdown: typeof raw.export_markdown === "string" ? raw.export_markdown : "",
    stats_before_label: typeof raw.stats_before_label === "string" ? raw.stats_before_label : "",
    stats_after_label: typeof raw.stats_after_label === "string" ? raw.stats_after_label : "",
  };
}

function fmtUsd(n: number) {
  if (n === 0) return "0.00";
  if (n < 0.0001) return n.toExponential(2);
  if (n < 0.01) return n.toFixed(5);
  if (n < 1) return n.toFixed(4);
  return n.toFixed(3);
}

function Section({
  n,
  title,
  children,
}: {
  n: number;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-2xl bg-surface-800/75 backdrop-blur-sm shadow-card p-5 border border-white/[0.07] transition-shadow hover:border-accent/15">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-accent mb-3 flex items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-accent/15 text-accent text-sm font-mono">
          {n}
        </span>
        {title}
      </h3>
      {children}
    </section>
  );
}

function TruncatedPre({
  text,
  maxChars,
  className,
}: {
  text: string;
  maxChars: number;
  className?: string;
}) {
  const truncated = text.length > maxChars;
  const shown = truncated ? text.slice(0, maxChars) : text;
  return (
    <div>
      <pre className={className}>{shown}</pre>
      {truncated && (
        <p className="text-[11px] text-amber-200/85 mt-2 border border-amber-500/30 rounded-lg px-2 py-1.5 bg-amber-950/25 leading-relaxed">
          Preview truncated at <strong>{maxChars.toLocaleString()}</strong> characters (total{" "}
          <strong>{text.length.toLocaleString()}</strong>). The browser cannot render megabytes smoothly — use{" "}
          <strong>Copy for Cursor</strong> or <strong>Download .md</strong> for the full text.
        </p>
      )}
    </div>
  );
}

function TokenBar({
  label,
  value,
  max,
  accent,
}: {
  label: string;
  value: number;
  max: number;
  accent: boolean;
}) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="mb-3 last:mb-0">
      <div className="flex justify-between text-[11px] text-slate-500 mb-1">
        <span>{label}</span>
        <span className="font-mono text-slate-400">{value.toLocaleString()} tok</span>
      </div>
      <div className="h-2 rounded-full bg-surface-900 overflow-hidden border border-white/[0.06]">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${accent ? "metric-bar-fill" : "bg-slate-600"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [repoPath, setRepoPath] = useState("");
  const [pasted, setPasted] = useState("");
  const [pricingModel, setPricingModel] = useState("gpt-4o-mini");
  const [modelRows, setModelRows] = useState<{ id: string; label: string; tokenizer_note?: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [copyState, setCopyState] = useState<"idle" | "ok" | "err">("idle");
  const [runsPerDay, setRunsPerDay] = useState(8);
  const [workdaysOnly, setWorkdaysOnly] = useState(true);
  const [demoHint, setDemoHint] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/pricing-models")
      .then((r) => r.json())
      .then((d: { models?: unknown }) => {
        const raw = d.models;
        if (Array.isArray(raw) && raw.length > 0 && typeof raw[0] === "object" && raw[0] !== null && "id" in (raw[0] as object)) {
          setModelRows(raw as { id: string; label: string; tokenizer_note?: string }[]);
        } else if (Array.isArray(raw)) {
          setModelRows((raw as string[]).map((id) => ({ id, label: id })));
        } else {
          setModelRows([{ id: "gpt-4o-mini", label: "GPT-4o mini" }]);
        }
      })
      .catch(() => setModelRows([{ id: "gpt-4o-mini", label: "GPT-4o mini" }]));
  }, []);

  const loadDemo = useCallback(async (variant: "small" | "big" = "small") => {
    try {
      const r = await fetch(`/api/demo?variant=${variant}`);
      const d = await r.json();
      setPrompt(d.prompt || "");
      setRepoPath(d.repo_path || "");
      setPasted(d.pasted || "");
      setResult(null);
      setDemoHint(d.hint || null);
    } catch {
      setPrompt("Demo failed — is the API running on port 8000?");
      setDemoHint(null);
    }
  }, []);

  const analyze = useCallback(async () => {
    setLoading(true);
    setResult(null);
    setCopyState("idle");
    try {
      const r = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          repo_path: repoPath,
          pasted,
          pricing_model: pricingModel,
        }),
      });
      let raw: Record<string, unknown>;
      try {
        raw = (await r.json()) as Record<string, unknown>;
      } catch {
        setResult({
          ok: false,
          error: "bad_json",
          cleaned_prompt: "",
          audit_log: [],
          source_label: "",
          files_scanned: 0,
          files_selected: 0,
          ranked_files: [],
          compressed_context: "",
          compressed_context_md: "",
          ready_prompt: "",
          stats: null,
          cost: null,
          raw_bundle_preview: "",
          export_markdown: "",
        stats_before_label: "",
        stats_after_label: "",
      });
        return;
      }
      const data = normalizeAnalyzeResponse(raw);
      if (!r.ok) {
        setResult({
          ...data,
          ok: false,
          error: data.error || "server",
        });
        return;
      }
      if (data.ok && (!data.stats || !data.cost)) {
        setResult({
          ...data,
          ok: false,
          error: "analysis_failed",
        });
        return;
      }
      setResult(data);
    } catch {
      setResult({
        ok: false,
        error: "network",
        cleaned_prompt: "",
        audit_log: [],
        source_label: "",
        files_scanned: 0,
        files_selected: 0,
        ranked_files: [],
        compressed_context: "",
        compressed_context_md: "",
        ready_prompt: "",
        stats: null,
        cost: null,
        raw_bundle_preview: "",
        export_markdown: "",
        stats_before_label: "",
        stats_after_label: "",
      });
    } finally {
      setLoading(false);
    }
  }, [prompt, repoPath, pasted, pricingModel]);

  const copyReady = useCallback(async () => {
    if (!result?.ready_prompt) return;
    try {
      await navigator.clipboard.writeText(result.ready_prompt);
      setCopyState("ok");
      setTimeout(() => setCopyState("idle"), 2000);
    } catch {
      setCopyState("err");
    }
  }, [result?.ready_prompt]);

  const downloadMd = useCallback(() => {
    if (!result?.export_markdown) return;
    const blob = new Blob([result.export_markdown], { type: "text/markdown" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "context_surgeon_export.md";
    a.click();
    URL.revokeObjectURL(a.href);
  }, [result?.export_markdown]);

  const projections = useMemo(() => {
    if (!result?.ok || !result.cost || !result.stats) return null;
    const daysPerMonth = workdaysOnly ? 22 : 30;
    const dailyUsd = result.cost.cost_saved_usd * runsPerDay;
    const monthlyUsd = dailyUsd * daysPerMonth;
    return { dailyUsd, monthlyUsd, daysPerMonth };
  }, [result, runsPerDay, workdaysOnly]);

  const errMsg = result && !result.ok ? ERRORS[result.error || ""] || result.error || "Unknown error" : null;

  return (
    <div className="min-h-screen px-4 py-8 md:px-8 lg:px-12 max-w-[1680px] mx-auto pb-16">
      <header className="mb-10 md:mb-12 relative">
        <div className="absolute -left-4 top-0 h-24 w-1 rounded-full bg-gradient-to-b from-accent to-transparent opacity-60" aria-hidden />
        <p className="text-accent text-sm font-medium tracking-wide mb-1">Review + QA · local · deterministic · no extra LLM call</p>
        <h1 className="text-3xl md:text-5xl font-bold text-white tracking-tight">Context Surgeon</h1>
        <p className="mt-3 text-slate-400 max-w-2xl text-[15px] leading-relaxed">
          One messy prompt in → we <strong className="text-slate-300">clean</strong> it, <strong className="text-slate-300">rank</strong> repo files,
          <strong className="text-slate-300"> compress</strong> structure, then you paste <strong className="text-accent">one Cursor-ready block</strong> out.
        </p>
      </header>

      <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-start">
        <div className="space-y-5">
          <div className="rounded-2xl bg-surface-800/90 backdrop-blur-md shadow-card p-6 border border-white/[0.08]">
            <label className="block mb-4">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Model · tokenizer & list price</span>
              <select
                value={pricingModel}
                onChange={(e) => setPricingModel(e.target.value)}
                className="mt-1 w-full rounded-xl bg-surface-900 border border-surface-600 px-4 py-2.5 text-sm text-slate-200 focus:ring-2 focus:ring-accent/30"
              >
                {(modelRows.length ? modelRows : [{ id: pricingModel, label: pricingModel }]).map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
              {modelRows.find((m) => m.id === pricingModel)?.tokenizer_note && (
                <p className="text-[10px] text-slate-600 mt-1.5 leading-relaxed">
                  {modelRows.find((m) => m.id === pricingModel)?.tokenizer_note}
                </p>
              )}
            </label>

            <div className="flex flex-wrap gap-2 mb-2">
              <button
                type="button"
                onClick={analyze}
                disabled={loading}
                className="flex-1 min-w-[120px] rounded-xl bg-accent px-4 py-3.5 text-surface-900 font-semibold text-sm hover:bg-accent-glow transition-all hover:shadow-[0_0_24px_rgba(61,214,198,0.25)] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none"
              >
                {loading ? "Analyzing…" : "Analyze context"}
              </button>
            </div>
            <div className="flex flex-wrap gap-2 mb-5">
              <button
                type="button"
                onClick={() => loadDemo("small")}
                className="rounded-lg border border-surface-600 bg-surface-700/40 px-3 py-2 text-xs font-medium text-slate-300 hover:border-accent/35"
              >
                Demo 1 · small repo
              </button>
              <button
                type="button"
                onClick={() => loadDemo("big")}
                className="rounded-lg border border-amber-500/40 bg-amber-950/20 px-3 py-2 text-xs font-medium text-amber-200/90 hover:border-amber-400/60"
              >
                Demo 2 · large repo
              </button>
            </div>
            {demoHint && (
              <p className="text-[11px] text-slate-500 mb-4 border-l-2 border-amber-500/40 pl-2">{demoHint}</p>
            )}

            <label className="block">
              <span className="text-sm font-medium text-slate-300 mb-2 block">Your prompt</span>
              <span className="text-xs text-slate-500 block mb-2">
                Task + messy notes in one box — we dedupe and trim filler before ranking files.
              </span>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={8}
                placeholder="Example: Fix the login 401 for valid users. Check token validation and session order…"
                className="w-full rounded-xl bg-surface-900 border border-surface-600 px-4 py-3 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent/50 resize-y min-h-[160px] scrollbar-thin font-sans"
              />
            </label>

            <label className="block mt-5">
              <span className="text-sm font-medium text-slate-300 mb-2 block">Repository path</span>
              <span className="text-xs text-slate-500 block mb-2">
                Absolute path on <strong className="text-slate-400">this machine</strong> (where the API runs). Empty = use paste below.
              </span>
              <input
                type="text"
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
                placeholder="C:\Users\you\project"
                className="w-full rounded-xl bg-surface-900 border border-surface-600 px-4 py-3 text-sm font-mono text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-accent/40"
              />
            </label>

            <label className="block mt-5">
              <span className="text-sm font-medium text-slate-300 mb-2 block">Or paste codebase</span>
              <span className="text-xs text-slate-500 block mb-2 font-mono">
                -----FILE: src/app.py----- then file body (repeat for more files).
              </span>
              <textarea
                value={pasted}
                onChange={(e) => setPasted(e.target.value)}
                rows={5}
                className="w-full rounded-xl bg-surface-900 border border-surface-600 px-4 py-3 text-sm font-mono text-slate-200 focus:outline-none focus:ring-2 focus:ring-accent/40 resize-y scrollbar-thin"
              />
            </label>
          </div>

          <p className="text-xs text-slate-500 px-1 leading-relaxed">
            OpenAI options use <strong className="text-slate-400">tiktoken</strong> for counts; Claude uses a <strong className="text-slate-400">~chars÷4</strong> estimate. Dollar totals use{" "}
            <strong className="text-slate-400">published input list prices</strong> — verify against your provider before reconciling bills.
          </p>
        </div>

        <div className="space-y-5 lg:sticky lg:top-6">
          {!result && !loading && (
            <div className="rounded-2xl border border-dashed border-surface-600 bg-surface-800/25 backdrop-blur-sm p-12 text-center text-slate-500 text-sm leading-relaxed">
              <p className="text-slate-400 mb-2">Nothing analyzed yet.</p>
              <span className="text-accent font-medium">Analyze context</span> or <span className="text-accent font-medium">Demo 2 · large repo</span> → big metrics, file picks,
              Cursor-ready paste.
            </div>
          )}

          {loading && (
            <div className="rounded-2xl bg-surface-800/60 border border-accent/10 p-12 text-center">
              <div className="inline-block h-8 w-8 rounded-full border-2 border-accent border-t-transparent animate-spin mb-3" />
              <p className="text-slate-400 text-sm">Scanning repo, ranking files, compressing…</p>
            </div>
          )}

          {errMsg && (
            <div className="rounded-2xl border border-red-500/35 bg-red-950/25 px-5 py-4 text-red-200 text-sm">{errMsg}</div>
          )}

          {result?.ok && result.stats && result.cost && (
            <>
              <Section n={1} title="Cleaned prompt">
                <p className="text-[10px] text-slate-500 mb-2 leading-relaxed">
                  <strong className="text-slate-400">Your</strong> task after <strong className="text-slate-400">rule-based</strong> cleanup (dedupe, filler) — <strong className="text-slate-400">not</strong> an LLM; often
                  unchanged if already tight. Small token delta here; <strong className="text-slate-400">Impact</strong> is where <strong className="text-slate-400">which code</strong> you send matters.{" "}
                  <strong className="text-slate-400">Step 5 · Ready for Cursor</strong> below = full paste block.
                </p>
                <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{result.cleaned_prompt || "—"}</p>
                {result.audit_log.length > 0 && (
                  <details className="mt-3 group">
                    <summary className="text-xs text-accent cursor-pointer hover:underline">Prompt audit ({result.audit_log.length})</summary>
                    <ul className="mt-2 space-y-1 text-xs text-slate-500 list-disc pl-4">
                      {result.audit_log.map((line, i) => (
                        <li key={i}>{line}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </Section>

              <Section n={2} title="Relevant files">
                <p className="text-xs text-slate-500 mb-3">
                  {result.files_scanned} scanned → <strong className="text-slate-300">{result.files_selected}</strong> selected · {result.source_label}
                </p>
                <ul className="space-y-3">
                  {result.ranked_files.map((f) => (
                    <li key={f.path} className="text-sm rounded-xl bg-surface-900/80 px-3 py-2.5 border border-white/[0.05]">
                      <span className="font-mono text-accent-glow text-xs">{f.path}</span>
                      <span className="text-slate-500 text-xs ml-2">{Math.round(f.confidence)}% match</span>
                      <ul className="mt-1 text-xs text-slate-500 space-y-0.5">
                        {f.reasons.map((r, i) => (
                          <li key={i}>· {r}</li>
                        ))}
                      </ul>
                    </li>
                  ))}
                </ul>
              </Section>

              <Section n={3} title="Compressed context">
                {(() => {
                  const full = result.compressed_context_md || result.compressed_context;
                  if (full.length > MAX_MD_PREVIEW_CHARS) {
                    return (
                      <div className="max-h-80 overflow-y-auto scrollbar-thin pr-1">
                        <TruncatedPre
                          text={full}
                          maxChars={MAX_MD_PREVIEW_CHARS}
                          className="text-[11px] font-mono text-slate-400 whitespace-pre-wrap leading-relaxed"
                        />
                      </div>
                    );
                  }
                  return (
                    <div className="prose prose-invert prose-sm max-w-none prose-p:text-slate-400 prose-strong:text-accent-glow font-mono text-xs leading-relaxed max-h-72 overflow-y-auto scrollbar-thin pr-2">
                      <ReactMarkdown>{full}</ReactMarkdown>
                    </div>
                  );
                })()}
              </Section>

              <Section n={4} title="Impact — token & cost story">
                <details className="mb-4 rounded-xl border border-sky-500/25 bg-sky-950/20 px-3 py-2.5 text-[12px] text-slate-400 leading-relaxed">
                  <summary className="cursor-pointer text-sky-200/95 font-medium text-xs list-none flex items-center gap-2">
                    <span aria-hidden>▸</span> Why compare prompt + code — not “prompts only”?
                  </summary>
                  <div className="mt-2 pl-1 space-y-2 border-l border-sky-500/20 ml-1 pl-3">
                    <p>
                      We <strong className="text-slate-300">never rewrite your repo on disk</strong>. The files in your folder stay the same.
                    </p>
                    <p>
                      What changes is what you <strong className="text-slate-300">send into the model’s context window</strong>. Billing and attention are driven by{" "}
                      <strong className="text-slate-300">that</strong> payload — prompt <em>plus</em> whatever file text you attach or paste.
                    </p>
                    <p>
                      Comparing <strong className="text-slate-300">prompts alone</strong> would miss the usual problem: people dump the{" "}
                      <strong className="text-slate-300">whole project</strong> into chat. Our “before” baseline is that worst case:{" "}
                      <strong className="text-slate-300">your prompt + full contents of every scanned file</strong>.
                    </p>
                    <p>
                      The “after” side is the <strong className="text-slate-300">smaller bundle we recommend</strong>: cleaned task + only the top files, compressed to
                      signatures/snippets. That’s the real token and quality story.
                    </p>
                  </div>
                </details>

                <div className="grid gap-3 mb-5 text-[13px] leading-snug">
                  <div className="rounded-xl bg-red-950/20 border border-red-500/20 px-3 py-2.5 text-slate-400">
                    <span className="text-red-300/90 font-semibold text-xs uppercase tracking-wide">Before · </span>
                    {result.stats_before_label || "Full prompt + every scanned file (worst-case paste)."}
                  </div>
                  <div className="rounded-xl bg-emerald-950/20 border border-emerald-500/25 px-3 py-2.5 text-slate-400">
                    <span className="text-emerald-300/90 font-semibold text-xs uppercase tracking-wide">After · </span>
                    {result.stats_after_label || "Cleaned task + compressed excerpts from top files only."}
                  </div>
                </div>

                <div className="mb-5">
                  <div className="flex justify-between items-end mb-2 gap-2">
                    <span className="text-[11px] uppercase tracking-wider text-slate-500 leading-tight">Context window: full repo paste vs curated bundle</span>
                    <span className="text-2xl font-bold text-white font-mono shrink-0">{result.stats.reduction_pct.toFixed(1)}%</span>
                  </div>
                  <div className="h-3 rounded-full bg-surface-900 overflow-hidden border border-white/[0.06]">
                    <div
                      className="h-full metric-bar-fill rounded-full transition-[width] duration-1000 ease-out"
                      style={{ width: `${Math.min(100, result.stats.reduction_pct)}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    <strong className="text-accent">{result.stats.tokens_saved.toLocaleString()}</strong> fewer input tokens for the{" "}
                    <strong className="text-slate-400">combined message to the model</strong> — not a diff of your files on disk. Baseline:{" "}
                    <em>prompt + every file’s full text</em> · Recommended: <em>cleaned task + compressed excerpts from chosen files</em>.
                  </p>
                  {result.stats.tokenizer_note && (
                    <p className="text-[10px] text-slate-600 mt-2 font-mono leading-relaxed">Counting: {result.stats.tokenizer_note}</p>
                  )}
                  {result.stats.tokens_saved < 500 && (
                    <p className="text-xs text-amber-200/80 mt-2 border border-amber-500/25 rounded-lg px-2 py-1.5 bg-amber-950/20">
                      Numbers look flat? Try <strong>Demo 2 · large repo</strong> (~16 noisy files) for a strong before/after (~70% cut in tests).
                    </p>
                  )}
                </div>

                <TokenBar
                  label="① Full paste (prompt + all files)"
                  value={result.stats.original_tokens}
                  max={result.stats.original_tokens}
                  accent={false}
                />
                <TokenBar
                  label="② Core payload (task + compressed context)"
                  value={result.stats.compressed_tokens}
                  max={result.stats.original_tokens}
                  accent
                />
                <div className="mt-2 rounded-lg bg-surface-900/80 border border-white/[0.06] px-3 py-2 text-[11px] text-slate-500">
                  <span className="text-slate-400 font-medium">③ Full Cursor message (copy block): </span>
                  <span className="font-mono text-slate-300">
                    ~{Number(result.stats.ready_message_tokens ?? 0).toLocaleString()} tok
                  </span>
                  <span className="text-slate-600"> — includes extra safety lines for Cursor; ①→② is the “signal” win.</span>
                </div>

                <div className="mt-5 pt-5 border-t border-white/[0.06] space-y-4">
                  <div>
                    <label className="flex justify-between text-xs text-slate-400 mb-2">
                      <span>Similar runs per day</span>
                      <span className="font-mono text-accent">{runsPerDay}</span>
                    </label>
                    <input
                      type="range"
                      min={1}
                      max={40}
                      value={runsPerDay}
                      onChange={(e) => setRunsPerDay(Number(e.target.value))}
                      className="w-full h-2 rounded-full appearance-none bg-surface-900 accent-accent cursor-pointer"
                    />
                  </div>
                  <label className="flex items-center gap-2 text-xs text-slate-500 cursor-pointer">
                    <input type="checkbox" checked={workdaysOnly} onChange={(e) => setWorkdaysOnly(e.target.checked)} className="rounded border-surface-600" />
                    Count month as ~22 workdays (not 30 calendar days)
                  </label>

                  {projections && (
                    <div className="grid sm:grid-cols-2 gap-3">
                      <div className="rounded-xl bg-surface-900/90 p-4 border border-accent/15">
                        <div className="text-[10px] uppercase text-slate-500 tracking-wider">Est. input $ / day</div>
                        <div className="text-xl font-semibold text-accent font-mono mt-1">${fmtUsd(projections.dailyUsd)}</div>
                        <div className="text-[10px] text-slate-600 mt-1">{runsPerDay}× save/run @ {result.cost.model_label}</div>
                      </div>
                      <div className="rounded-xl bg-surface-900/90 p-4 border border-white/[0.06]">
                        <div className="text-[10px] uppercase text-slate-500 tracking-wider">Est. input $ / month (~{projections.daysPerMonth}d)</div>
                        <div className="text-xl font-semibold text-slate-200 font-mono mt-1">${fmtUsd(projections.monthlyUsd)}</div>
                        <div className="text-[10px] text-slate-600 mt-1">List-price math only (input tokens)</div>
                      </div>
                    </div>
                  )}
                </div>

                <p className="text-xs text-slate-500 mt-4">
                  Per-run input (list price est.): ~${result.cost.estimated_original_cost_usd.toFixed(5)} → ~${result.cost.estimated_compressed_cost_usd.toFixed(5)} · save ~$
                  {fmtUsd(result.cost.cost_saved_usd)}
                </p>
                <p className="text-xs text-slate-400 mt-2 border-l-2 border-accent/40 pl-3">{result.stats.risk_note}</p>
              </Section>

              <Section n={5} title="Ready for Cursor">
                <p className="text-xs text-slate-500 mb-3">
                  Paste as <strong className="text-slate-400">one</strong> message in <strong className="text-slate-400">Composer</strong> or Chat. Rule file:{" "}
                  <code className="text-accent/90">.cursor/rules/context-surgeon.mdc</code>
                </p>
                <div className="rounded-xl bg-black/50 border border-surface-600 p-4 max-h-64 overflow-y-auto scrollbar-thin mb-3">
                  <TruncatedPre
                    text={result.ready_prompt}
                    maxChars={MAX_PRE_PREVIEW_CHARS}
                    className="text-[11px] font-mono text-slate-300 whitespace-pre-wrap leading-relaxed"
                  />
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={copyReady}
                    className="rounded-lg bg-accent/20 text-accent border border-accent/40 px-4 py-2.5 text-sm font-medium hover:bg-accent/30 transition-colors"
                  >
                    {copyState === "ok" ? "Copied!" : copyState === "err" ? "Copy failed" : "Copy for Cursor"}
                  </button>
                  <button
                    type="button"
                    onClick={downloadMd}
                    className="rounded-lg border border-surface-600 px-4 py-2.5 text-sm text-slate-300 hover:border-slate-500"
                  >
                    Download .md
                  </button>
                </div>
              </Section>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="rounded-xl bg-surface-800/40 border border-white/[0.05] p-4">
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Before (raw bundle)</h4>
                  <pre className="text-[10px] font-mono text-slate-500 max-h-52 overflow-y-auto scrollbar-thin whitespace-pre-wrap leading-relaxed">
                    {result.raw_bundle_preview}
                  </pre>
                </div>
                <div className="rounded-xl bg-surface-800/40 border border-white/[0.05] p-4">
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">After (ready prompt)</h4>
                  <div className="max-h-52 overflow-y-auto scrollbar-thin">
                    <TruncatedPre
                      text={result.ready_prompt}
                      maxChars={Math.min(MAX_PRE_PREVIEW_CHARS, 12000)}
                      className="text-[10px] font-mono text-slate-400 whitespace-pre-wrap leading-relaxed"
                    />
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
