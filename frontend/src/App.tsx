import { useCallback, useEffect, useState, type ReactNode } from "react";
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
  reduction_pct: number;
  original_chars: number;
  compressed_chars: number;
  risk_note: string;
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
};

const ERRORS: Record<string, string> = {
  empty_prompt: "Write your prompt — what should the model do?",
  bad_repo: "Repository path is not a valid folder on this machine.",
  empty_repo: "That folder has no matching code files (.py, .js, .ts, .md, …).",
  no_source: "Add a repository path or paste files using the -----FILE: markers.",
};

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
    <section className="rounded-2xl bg-surface-800/80 shadow-card p-5 border border-white/[0.06]">
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

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [repoPath, setRepoPath] = useState("");
  const [pasted, setPasted] = useState("");
  const [mockModel, setMockModel] = useState("gpt-4o-mini (mock)");
  const [models, setModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [copyState, setCopyState] = useState<"idle" | "ok" | "err">("idle");

  useEffect(() => {
    fetch("/api/pricing-models")
      .then((r) => r.json())
      .then((d: { models: string[] }) => setModels(d.models || []))
      .catch(() => setModels(["gpt-4o-mini (mock)"]));
  }, []);

  const loadDemo = useCallback(async () => {
    try {
      const r = await fetch("/api/demo");
      const d = await r.json();
      setPrompt(d.prompt || "");
      setRepoPath(d.repo_path || "");
      setPasted(d.pasted || "");
      setResult(null);
    } catch {
      setPrompt("Demo failed — is the API running on port 8000?");
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
          mock_model: mockModel,
        }),
      });
      const data: AnalyzeResponse = await r.json();
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
      });
    } finally {
      setLoading(false);
    }
  }, [prompt, repoPath, pasted, mockModel]);

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

  const errMsg =
    result && !result.ok
      ? result.error === "network"
        ? "Could not reach the API. Start the backend: uvicorn main:app --port 8000"
        : ERRORS[result.error || ""] || result.error
      : null;

  return (
    <div className="min-h-screen px-4 py-8 md:px-8 lg:px-12 max-w-[1600px] mx-auto">
      <header className="mb-10 md:mb-12">
        <p className="text-accent text-sm font-medium tracking-wide mb-1">Local · deterministic · no LLM in the loop</p>
        <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">Context Surgeon</h1>
        <p className="mt-2 text-slate-400 max-w-2xl text-[15px] leading-relaxed">
          Paste <strong className="text-slate-300">one prompt</strong> (task + messy details). We clean it, pick the most relevant files,
          compress structure, and give you a <strong className="text-slate-300">ready-to-paste block</strong> for Cursor — with token estimates.
        </p>
      </header>

      <div className="grid lg:grid-cols-2 gap-8 lg:gap-10 items-start">
        {/* Input column */}
        <div className="space-y-5">
          <div className="rounded-2xl bg-surface-800/90 shadow-card p-6 border border-white/[0.07]">
            <label className="block mb-4">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Mock pricing model</span>
              <select
                value={mockModel}
                onChange={(e) => setMockModel(e.target.value)}
                className="mt-1 w-full rounded-xl bg-surface-900 border border-surface-600 px-4 py-2.5 text-sm text-slate-200"
              >
                {(models.length ? models : [mockModel]).map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </label>

            <div className="flex flex-wrap gap-3 mb-5">
              <button
                type="button"
                onClick={analyze}
                disabled={loading}
                className="flex-1 min-w-[140px] rounded-xl bg-accent px-5 py-3 text-surface-900 font-semibold text-sm hover:bg-accent-glow transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Analyzing…" : "Analyze context"}
              </button>
              <button
                type="button"
                onClick={loadDemo}
                className="rounded-xl border border-surface-600 bg-surface-700/50 px-5 py-3 text-sm font-medium text-slate-200 hover:border-accent/40 hover:bg-surface-700 transition-colors"
              >
                Load demo
              </button>
            </div>

            <label className="block">
              <span className="text-sm font-medium text-slate-300 mb-2 block">Your prompt</span>
              <span className="text-xs text-slate-500 block mb-2">
                Everything in one place: goal, constraints, messy notes — we dedupe and trim filler.
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
                Absolute path on <strong className="text-slate-400">this computer</strong> (same machine as the API). Leave empty if you paste files below.
              </span>
              <input
                type="text"
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
                placeholder="C:\Users\you\project or /home/you/project"
                className="w-full rounded-xl bg-surface-900 border border-surface-600 px-4 py-3 text-sm font-mono text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-accent/40"
              />
            </label>

            <label className="block mt-5">
              <span className="text-sm font-medium text-slate-300 mb-2 block">Or paste codebase</span>
              <span className="text-xs text-slate-500 block mb-2 font-mono">
                -----FILE: src/app.py----- then content. Multiple files = repeat the marker line.
              </span>
              <textarea
                value={pasted}
                onChange={(e) => setPasted(e.target.value)}
                rows={5}
                className="w-full rounded-xl bg-surface-900 border border-surface-600 px-4 py-3 text-sm font-mono text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-accent/40 resize-y scrollbar-thin"
                placeholder=""
              />
            </label>
          </div>

          <p className="text-xs text-slate-500 px-1">
            Token counts ≈ chars÷4 (estimate). Mock $ rates are illustrative only.
          </p>
        </div>

        {/* Output column */}
        <div className="space-y-5 lg:sticky lg:top-8">
          {!result && !loading && (
            <div className="rounded-2xl border border-dashed border-surface-600 bg-surface-800/30 p-10 text-center text-slate-500 text-sm">
              Run <span className="text-accent font-medium">Analyze context</span> or <span className="text-accent font-medium">Load demo</span> to see cleaned prompt,
              file picks, compression, and the final paste block.
            </div>
          )}

          {loading && (
            <div className="rounded-2xl bg-surface-800/50 p-10 text-center text-slate-400 animate-pulse">Scanning repo and building context…</div>
          )}

          {errMsg && (
            <div className="rounded-2xl border border-red-500/30 bg-red-950/20 px-5 py-4 text-red-200 text-sm">{errMsg}</div>
          )}

          {result?.ok && result.stats && (
            <>
              <Section n={1} title="Cleaned prompt">
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
                    <li key={f.path} className="text-sm rounded-lg bg-surface-900/80 px-3 py-2 border border-white/[0.04]">
                      <span className="font-mono text-accent-glow text-xs">{f.path}</span>
                      <span className="text-slate-500 text-xs ml-2">confidence {Math.round(f.confidence)}%</span>
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
                <div className="prose prose-invert prose-sm max-w-none prose-p:text-slate-400 prose-strong:text-accent-glow font-mono text-xs leading-relaxed max-h-72 overflow-y-auto scrollbar-thin pr-2">
                  <ReactMarkdown>{result.compressed_context_md || result.compressed_context}</ReactMarkdown>
                </div>
              </Section>

              <Section n={4} title="Stats (estimated)">
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="rounded-xl bg-surface-900 p-3 text-center border border-white/[0.05]">
                    <div className="text-[10px] uppercase tracking-wider text-slate-500">Before</div>
                    <div className="text-lg font-semibold text-slate-200">{result.stats.original_tokens.toLocaleString()}</div>
                    <div className="text-[10px] text-slate-600">~tokens</div>
                  </div>
                  <div className="rounded-xl bg-surface-900 p-3 text-center border border-white/[0.05]">
                    <div className="text-[10px] uppercase tracking-wider text-slate-500">After</div>
                    <div className="text-lg font-semibold text-accent">{result.stats.compressed_tokens.toLocaleString()}</div>
                    <div className="text-[10px] text-slate-600">~tokens</div>
                  </div>
                  <div className="rounded-xl bg-surface-900 p-3 text-center border border-accent/20">
                    <div className="text-[10px] uppercase tracking-wider text-slate-500">Cut</div>
                    <div className="text-lg font-semibold text-white">{result.stats.reduction_pct}%</div>
                    <div className="text-[10px] text-slate-600">reduction</div>
                  </div>
                </div>
                <p className="text-xs text-slate-500 mb-3">
                  {result.stats.original_chars.toLocaleString()} → {result.stats.compressed_chars.toLocaleString()} chars
                </p>
                {result.cost && (
                  <p className="text-xs text-slate-500">
                    ~${result.cost.estimated_original_cost_usd.toFixed(4)} → ~${result.cost.estimated_compressed_cost_usd.toFixed(4)} input (save ~$
                    {result.cost.cost_saved_usd.toFixed(4)} per bundle, illustrative)
                  </p>
                )}
                <p className="text-xs text-slate-400 mt-2 border-l-2 border-accent/40 pl-3">{result.stats.risk_note}</p>
              </Section>

              <Section n={5} title="Ready to paste">
                <p className="text-xs text-slate-500 mb-3">Copy into Cursor, ChatGPT, or your agent as one message.</p>
                <pre className="rounded-xl bg-black/40 border border-surface-600 p-4 text-xs font-mono text-slate-300 whitespace-pre-wrap max-h-64 overflow-y-auto scrollbar-thin mb-3">
                  {result.ready_prompt}
                </pre>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={copyReady}
                    className="rounded-lg bg-accent/20 text-accent border border-accent/40 px-4 py-2 text-sm font-medium hover:bg-accent/30"
                  >
                    {copyState === "ok" ? "Copied!" : copyState === "err" ? "Copy failed" : "Copy to clipboard"}
                  </button>
                  <button
                    type="button"
                    onClick={downloadMd}
                    className="rounded-lg border border-surface-600 px-4 py-2 text-sm text-slate-300 hover:border-slate-500"
                  >
                    Download .md
                  </button>
                </div>
              </Section>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="rounded-xl bg-surface-800/50 border border-white/[0.05] p-4">
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Before (raw bundle)</h4>
                  <pre className="text-[10px] font-mono text-slate-500 max-h-48 overflow-y-auto scrollbar-thin whitespace-pre-wrap">
                    {result.raw_bundle_preview}
                  </pre>
                </div>
                <div className="rounded-xl bg-surface-800/50 border border-white/[0.05] p-4">
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">After (ready prompt)</h4>
                  <pre className="text-[10px] font-mono text-slate-400 max-h-48 overflow-y-auto scrollbar-thin whitespace-pre-wrap">
                    {result.ready_prompt}
                  </pre>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
