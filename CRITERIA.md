# How Cadence addresses the judging criteria

**Track: Builder** — a working tool, validated against a real research paper (Singhal, Allen,
Gaddes, Baer & Demirel, *"Biomanufacturability of a Squid Ring Teeth Protein Library via
Orthogonal High-Throughput Screening,"* 2026) and tied to a real commercialization path
(Tandem Repeat's Procell™ fiber / Sonachic knitwear).

## 1. Impact — 25%
**Who benefits and how much it matters.** Structural-protein biomanufacturing is gated by the
Learn step: deciding which sequences actually express well enough to make. That decision flows
straight into scale-up — Tandem Repeat produces the same class of proteins by fermentation as
**Procell™ fiber**, with a **7,000 metric-ton/year plant targeted for 2027** and a consumer brand
(**Sonachic**) already on the cover of *Textiles Panamericanos*. At that scale a **1% improvement in
sequence-level yield compounds into tons of product and real cost**. Cadence targets exactly the
Learn phase that produces higher-yielding, more-manufacturable designs — a tool bio-foundries and
materials-protein companies could actually adopt. It fits the Builder problem statement: something
people could use, not a toy.

## 2. Claude Use — 25%
**Creative, beyond a basic app.** The four DBTL agents *are* Claude with distinct system prompts,
orchestrated in a loop — the product itself is a multi-agent Claude system. Beyond that, the entire
project was built agentically with **Claude (Cowork)** in one session: it scaffolded the FastAPI app,
reconstructed and fixed a collaborator's v3 from Google Drive, **ran a real DBTL cycle end-to-end
against a live API key**, read the source paper, and generated the animated figures, the dynamic
schematics, the decks, and the demo video. It also **surfaced a real model behavior**: a hidden
`thinking` block silently exhausting the `max_tokens` budget before any visible text — diagnosed via
`stop_reason` and fixed with a retry. Claude was the builder, the analyst, and the subject.

## 3. Depth & Execution — 20%
**Pushed past the first idea; real craft.** It didn't stop at "a 4-agent chatbot." Iterations:
two rounds of the silent-blank Learn bug (2000 → 8000 → 20000 tokens + `stop_reason` handling +
explicit `[NO OUTPUT]`/`[TRUNCATED]` markers); a dataset summarizer rewritten to inline value-counts
and rows so the agent reasons over data, not schema; a **defined, reproducible confidence-index
formula** rather than ad-hoc scores; and a write-up grounded in the paper's **actual numbers**
(CAI-only 68.1% vs 43.8% baseline; Cliff's δ +0.46/−0.03; R² = 0.91). Limitations are stated
honestly (summary-level analysis, modeled multi-cycle trajectory).

## 4. Demo — 30%
**Working and compelling.** There is a runnable app (demo mode needs no key; a real cycle runs with
one). The demo video shows the actual live run, the anomaly catches with confidence scores, animated
re-creations of the paper's Figures 4–6 with its real numbers, and dynamic schematics of the library
design, the orthogonal screen, and the fermentation scale-up. It's software you could use and
findings you can trust — and it's genuinely watchable.

---

### One-line self-assessment
A working multi-agent Claude tool for the DBTL Learn phase, validated on a real published dataset and
pointed at a real 7,000-ton scale-up — built, run, and documented end-to-end by Claude in a single session.
