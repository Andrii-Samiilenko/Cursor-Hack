# Context Surgeon — ~3 minute pitch (Cursor hackathon)

**Pacing:** ~150 words/min ≈ **450 words** total. Adjust pauses for demo clicks.

---

### 0:00–0:25 — Hook & problem

“Hi — we’re **Context Surgeon**.  

Cursor and other agents are only as good as what you **feed** them. In practice, people paste **huge prompts**, dump **whole repos**, or say vague things like ‘fix auth.’ The model gets **tons of tokens**, **loses focus**, **hallucinates paths**, and burns **money** on noise.  

That’s not a ‘smarter model’ problem first — it’s a **context quality** problem. We treat it like a **Review + QA gate** *before* the LLM runs.”

---

### 0:25–0:55 — Main road (Review + QA)

“Our **main road** is **Review + QA**: we’re not building another generic agent. We’re building a **checkpoint** that **inspects and trims** what goes to the model.  

**Concrete workflow:** you paste **one** messy prompt, point at a folder — we **clean** the text, **scan** the repo, **rank** files by relevance with **explainable reasons**, **compress** them to signatures and high-signal snippets, and output **one block** you paste into **Cursor Composer**.  

Everything is **deterministic** — **no second LLM** inside our tool — so the demo is **reproducible** and **verifiable**.”

---

### 0:55–1:35 — Live demo (say what you click)

“Let me show it. I’ll hit **Demo 2 · large repo** — that’s a **stress repo** with lots of legacy noise — then **Analyze**.  

You see **before vs after**: we compare **‘prompt plus every file’** — the worst case — to **‘cleaned task plus only the compressed excerpts we kept.’** That’s where the **big token and mock-dollar savings** come from.  

The **copy block** adds **Cursor-specific rules**: work only with listed paths, don’t invent APIs. That’s our **Cursor-native workflow** angle.”

*(Pause on Impact section: % cut, $/day slider, optional Wh disclaimer.)*

---

### 1:35–2:15 — Solution & why it wins

“So we’re **not** replacing Cursor’s search — we’re **briefing** it. We give a **map and excerpts**, not the entire book.  

**Reliability:** you can read **why** each file scored high. **Safety / quality:** less junk in context means **less drift** and fewer **invented files**; the prompt **forces** explicit assumptions.  

**Developer tool:** it’s local, fast, hackathon-sized — **backend plus React**, one command to run.”

---

### 2:15–2:45 — Side quests (one line each)

“For **side quests**: **best dev tool** — obvious. **Cursor-native** — paste-ready block plus `.cursor/rules`. **Reliability system** — audit trail and deterministic pipeline. **AI safety** — narrower context and explicit ‘don’t hallucinate paths’ instructions. We’re honest that **$ and Wh** numbers use **mock** rates for storytelling.”

---

### 2:45–3:00 — Close

“**Context Surgeon**: **Review + QA for context** — smaller, cleaner inputs, better answers, measurable **before/after**.  

Thanks — happy to take questions.”

---

### Backup one-liner (if cut short)

“We **clean** your prompt, **pick** the right files, **compress** the repo to signal, and give you **one Cursor-ready paste** — **Review + QA** on what the model sees.”
