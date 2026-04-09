# How the code works (very simple)

Think of **two pieces**: the website (React) and the server (Python).

1. **You use the site** — enter your task text, a path to your code folder (or paste files) — and click **Analyze**.
2. **The browser** sends that in one request to the server: `POST /api/analyze`.
3. **The server runs a pipeline** (no LLM calls — only rules and scripts):
   - **Clean the prompt** (`prompt_cleaner`) — removes repetition and filler from your text.
   - **Scan the folder** (`repo_scanner`) — reads allowed file types (.py, .js, .ts, .md, etc.), skips `node_modules`, `.git`, and so on. Or parses pasted blobs with `-----FILE: ...-----` markers.
   - **Rank files** (`relevance_ranker`) — scores which files match the task (filename, content, symbol names, simple import hints).
   - **Compress** (`compressor`) — keeps imports, signatures, and keyword-adjacent snippets; long bodies become placeholders like “implementation omitted.”
   - **Build the final block** (`prompt_builder`) — one Cursor-ready paste with rules like “don’t invent paths.”
   - **Numbers** (`token_estimator`) — **tiktoken** for OpenAI-style counts where available; **published list prices** for input-token $ estimates; Claude uses a ~chars÷4 approximation unless you wire Anthropic’s counter.
4. **The response** goes back to the page — you see cleaned prompt, file picks, compressed context, metrics, and copy/download.

**Bottom line:** data flows **form → API → Python modules → JSON → UI**. We **don’t rewrite your repo on disk**; we only change what we **show** and what you **paste into the chat**.

---

# Demo speech (~2 minutes)

*Speak calmly; pause on “now I’ll click” and actually click in the UI.*

---

**Problem**  
When we use AI in Cursor, the answer depends on what we **feed** the model. Often people dump a **huge prompt** and **tons of files** into context — noisy, expensive, easy to drift. Or they give **too little** and the model **hallucinates** paths and APIs. The bottleneck isn’t only “smarter model” — it’s **context quality**.

**Solution**  
**Context Surgeon** is a small **local** tool with **no second LLM inside**. You write **one** raw task and point at a repo — we **clean** the text, **pick** the most relevant files with **short reasons**, **compress** them to structure + snippets, and output **one** block to paste into Cursor. We’re not auto-fixing your codebase — we’re **writing a proper brief** for the model.

**Benefit**  
Less noise in the window → **more reliable** answers and **fewer input tokens** on your actual model call. The UI shows a clear **before vs after** on that bundle. It maps cleanly to **Review + QA**: a **quality gate on what goes in** before the agent acts.

**Demo**  
I’ll hit **Demo 2 · large repo**, then **Analyze** — you’ll see a strong cut between “paste the whole tree” and our **curated bundle**. Then **Copy for Cursor** — that’s ready for Composer.

**One-liner**  
**Context Surgeon** is **context surgery**: keep the signal, drop the noise so Cursor stays on task.

---

*To trim to ~90 seconds: keep Problem, first two sentences of Solution, one sentence on Benefit, and one screen of demo.*
