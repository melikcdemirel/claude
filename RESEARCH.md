# Cadence: A Multi-Agent Learn-Phase Copilot for the DBTL Cycle

*A hackathon write-up. **Track: Builder** — a working tool, validated against a real research paper.*

> **Case-study source.** Singhal, K., Allen, B. D., Gaddes, D., Baer, T. M., & Demirel, M. C.
> *"Biomanufacturability of a Squid Ring Teeth Protein Library via Orthogonal High-Throughput
> Screening."* (2026, manuscript). The paper argues that the path to predictable structural-protein
> biomanufacturing "runs through models learned from library-scale data rather than through
> hand-tuned sequence indices," closing the DBTL loop with AI/ML. **Cadence operationalizes the
> Learn stage of exactly that arc.**

## Abstract

Synthetic-biology labs run the **Design–Build–Test–Learn (DBTL)** cycle: propose constructs, build them, measure them, and learn from the data to seed the next design. The **Learn** step — turning a raw Test-stage dataset into trusted, decision-ready findings — is where a scientist manually hunts for junk, duplicates, undefined labels, and non-reproducible signals. It is slow, inconsistent, and it gates the next experiment.

**Cadence** is a four-agent system, built on Claude, that runs the whole DBTL loop and specializes the Learn phase: it ingests Test data, flags undefined/anomalous *tokens* (columns, labels, values) and scores each with a **reproducible confidence index**, then hands prioritized fixes back to Design. Given the per-bin summary behind the SRT paper's Figures 5–6, the Learn agent reproduced the paper's headline conclusions from the summary alone — FACS brightness saturates as a yield predictor above a moderate gate, growth is not the bottleneck, and codon-adaptation index (CAI) carries the residual signal — and, on a schema-faithful stand-in dataset, caught three data-integrity defects unprompted, each with a scored confidence.

## 1. Problem & motivation

A bio-foundry can generate thousands of clones and dozens of sequence/measurement features per DBTL cycle. Before any modelling, someone must answer unglamorous but critical questions: *Which columns are malformed? Which features are duplicates or aliases? Which are dead (zero-variance) and can't contribute? Which labels aren't in the controlled vocabulary? How confident are we that a flag is real versus noise?*

Today this is manual QA. It doesn't scale, it isn't reproducible between analysts, and undetected bad data silently corrupts the *next* design. Cadence targets exactly this handoff.

## 2. System

Four agents, each a **system prompt + role**, chained so each phase's output is the next phase's input (a linear pipeline — the simplest orchestration that is easy to reason about and extend):

| Agent | Role |
|---|---|
| **Design** | Turn goals + last cycle's learnings into concrete, testable design candidates. |
| **Build** | Convert designs into a build plan / protocol with traceable sample IDs. |
| **Test** | Define assays, measurements, and the dataset schema handed to Learn. |
| **Learn** | Ingest the dataset, flag undefined/anomalous tokens, and score each with a confidence index. *(Uses the project's analyst system prompt.)* |

- **Backend:** Python + FastAPI. A single `orchestrator.py` is the only place that calls Claude (`run_agent` for one agent, `run_cycle` for the full loop).
- **Frontend:** plain HTML/CSS/JS (no build step). Upload a CSV, enter an objective, run one agent or the whole cycle, watch each phase resolve.
- **Dataset summarizer** (`main._summarize_dataset`): computes per-column missing counts, value counts for low-cardinality columns (where "undefined tokens" live), and inlines the rows so the Learn agent can analyze the data directly.

## 3. Methodology — the confidence index

The Learn agent does not invent an ad-hoc score per finding. It defines a **reusable 0–1 scale** and a **weighted formula**, then applies it — the reproducibility the analyst brief demands.

```
CI_f = w1·cardinality_signal
     + w2·schema_violation_signal
     + w3·biological_implausibility_signal
     + w4·reproducibility_signal        (weights sum to 1.0)
```

| CI range | Interpretation | Action |
|---|---|---|
| 0.90–1.00 | Certain error / confirmed anomaly | Must resolve before modelling |
| 0.70–0.89 | High-confidence issue | Strongly recommend fixing |
| 0.50–0.69 | Probable | Investigate; carry as uncertainty |
| 0.30–0.49 | Possible | Document; monitor next cycle |
| 0.00–0.29 | Low suspicion | Note only |

## 4. Case study & results

**Case (from the paper).** A combinatorial **Squid Ring Teeth (SRT)** library of ~1.2 M
four-fragment variants (33⁴) from 33 natural amorphous fragments across six squid species,
crystalline region held constant (`AAASVSTVHHP`), expressed in *E. coli* as a translationally-
coupled **mCherry** reporter. Two orthogonal readouts: **FACS** gates single cells into Low
(30–100 a.u.), Medium (100–300), High (300–3,000) by mCherry (n = 301,661 events); a
**microcapillary array** measures per-clone fluorescence and brightfield OD (~17,000 capillaries
per bin) at t = 15/25/35 h. Sequenced clones (n = 13,963) link genotype to bin. The paper's
central result: hand-crafted amino-acid descriptors sit at the **43.8%** majority baseline, while
the **codon-adaptation index (CAI) alone reaches 68.1 ± 1.2%** — statistically indistinguishable
from all feature classes combined (**69.0 ± 0.6%**), and learned token features recover the same
signal. CAI ranges only **0.73–0.95** (mean 0.85 ± 0.04), i.e. the signal persists *despite* codon
optimization.

**4.1 Cadence's Learn agent reproduced the paper's conclusions from the summary alone.**
Given the per-bin summary behind Figures 5–6, it independently recovered:
- **FACS saturates as a yield predictor.** Low separates cleanly from the rest, but the
  **Medium↔High boundary is negligible** — matching the paper's Cliff's δ of **+0.46** (Low→Medium,
  "medium" effect) versus **−0.03** (Medium→High, "negligible"), stable across all three timepoints.
- **Growth is not the bottleneck.** Per-capillary OD is equivalent across bins (paper: all |δ| < 0.13),
  shifting the explanation from toxicity toward translation-rate limits.
- **CAI carries the residual signal**, rising monotonically Low→Medium→High (the paper's bin-mean CAI
  is log-linear in bin-mean mCherry, **R² = 0.91**). The agent correctly flagged that the full
  CAI-dominance claim rests on a *multivariate Random Forest* that cannot be rebuilt from marginal
  summary statistics — the honest boundary of a summary-level analysis.

**4.2 Data-integrity check (on a schema-faithful stand-in).** The paper's raw tables
(`library_data.xlsx`, `sequence-features-by-bin.xlsx`) were not in hand, so the repo ships a small
sample that mirrors their schema *and deliberately seeds three defects*. Running only on the data,
the Learn agent caught all three, unprompted, each scored:

| Flag | Finding | CI |
|---|---|---|
| `dG_dG_cds_only` | Malformed **double-prefixed** column name — pipeline concatenation bug; schema expects `dG_cds_only`. | 0.80 |
| `ra_dG_cds_only` | **Undefined** `ra_` token *and* an **exact duplicate** of the column above (Pearson r = 1.000). Recommend dropping one, renaming the survivor. | 0.80 |
| `dG_junction` | **Zero-variance / "dead" feature** — one value across all rows; cannot contribute to learning; likely a placeholder. | High |

This is the capability the Learn phase adds on top of the science: before any classifier runs, is the
Test table even clean? Swap in the real per-clone tables to run it against the paper's actual features.

**4.3 Feedback to the next Design.** The Learn phase emitted prioritized actions consistent with the
paper's own reframing (screen codon- and amino-acid axes in parallel): push CAI within the informative
window, treat Medium+High as one merged tier for enrichment (don't iterate top-bin FACS), fix the
malformed/duplicate columns before the classifier ingests them, and introduce variation into dead
features so they can carry signal.

## 5. Engineering depth

This was wrestled with, not hacked in one pass:

- **Silent-blank Learn bug (two rounds).** On the full cycle the Learn phase rendered *empty* and Build/Test truncated mid-sentence. Root cause: on a model that emits a hidden `thinking` block, reasoning consumes the `max_tokens` budget *before* any visible `text` is produced, and the orchestrator only joins `text` blocks. Fix: raise/parameterize the budget (`DBTL_MAX_TOKENS`), read `stop_reason`, retry once at double budget when the visible text is empty, and never return a silently-blank phase — emit an explicit `[NO OUTPUT]` / `[TRUNCATED]` marker naming the knob to turn.
- **Inline data analysis without tools.** The dataset summarizer was upgraded to inline value-counts and rows so the Learn agent reasons over real data (not a schema description) even without file/code tools, and the message explicitly tells it the data is inline so it doesn't wait for attachments.
- **Demo mode.** With no API key the app returns labeled placeholders so the UI is fully explorable before setup.

## 6. Limitations (honest)

- The Learn agent currently reasons over a **pre-aggregated summary**, not the raw per-clone table. Multivariate claims (the paper's Random Forest, Cliff's δ) require real **code execution** over the full data — the highest-value next step.
- "Undefined token" detection is model-judgment, not yet grounded in a **real reference vocabulary** (known parts, gate definitions, feature schema).
- Only **one cycle is measured**. The confidence-index-vs-cycle trajectory in the visualization is *modeled* (anchored at the measured cycle-1 value of 0.80) to express the hypothesis that confidence rises as the loop grounds its reference set; it is labeled as such.

## 7. Future work

1. Give Learn a code-execution tool + Files API over the raw clone table (compute the RF / Cliff's δ itself).
2. Ground undefined-token detection in a real reference vocabulary and compute the confidence index deterministically in Python, with the agent interpreting it.
3. Thread a compact running cycle-memory so Learn sees Design's pre-registered anomaly checklist and Build's assumptions of record.
4. Connectors into LIMS / part registries; persist cycle history; validate catch-rate against expert review on live foundry data.

## 8. How Claude was used

The project itself is a demonstration of creative Claude use: the four agents *are* Claude with distinct system prompts, orchestrated in a loop. Beyond that, the **entire deliverable set** — scaffolding the app, reconstructing and fixing a collaborator's v3 from Google Drive, diagnosing the hidden-`thinking` token bug, running a real DBTL cycle end to end, building the results deck, the pitch, the animated schematic, and this write-up — was produced with **Claude (Cowork)** driving file, shell, browser, and connector tools in a single session.

## Reproducibility

See `README.md`. In short: `cd backend`, create a venv, `pip install -r requirements.txt`, set `ANTHROPIC_API_KEY`, `uvicorn main:app --reload`, open `http://127.0.0.1:8000`. To reproduce the case study headless: `python run_srt_cycle.py` (uses the bundled sample at `data/dave-plots/summary_stats.csv`). The captured live-run output is in `results/`. For a no-key, GitHub-renderable walkthrough of the Learn-phase analysis, open `notebooks/cadence_learn_demo.ipynb`.

*Note: the sample dataset ships as a small, schema-faithful stand-in (it deliberately contains the three defects above); swap in the real per-clone tables (`library_data.xlsx`, `sequence-features-by-bin.xlsx`) to reproduce the full multivariate analysis.*

## Impact & commercial context

The Learn phase Cadence targets is not academic. The same class of squid-ring-teeth proteins is
produced at industrial scale by fermentation as **Procell™ fiber** (Tandem Repeat, Inc.) — a
protein pulp spun into staple fibers much like Lyocell, with a **7,000 metric-ton/year plant
targeted for 2027** and a consumer knitwear brand, **Sonachic**, already in market and in the press.
Which sequences are worth building and scaling is decided at the Learn step; at 7,000-ton scale a
**1% improvement in sequence-level yield compounds into tons of product and real cost**. A tool that
makes the Learn phase faster, more reproducible, and self-checking is therefore directly useful to
materials-protein biomanufacturers. See `CRITERIA.md` for the full mapping to the judging rubric.

## References

Singhal, K., Allen, B. D., Gaddes, D., Baer, T. M., & Demirel, M. C. (2026).
*Biomanufacturability of a Squid Ring Teeth Protein Library via Orthogonal High-Throughput
Screening.* Manuscript. Source data: `library_data.xlsx` (FACS and per-bin sheets),
`sequence-features-by-bin.xlsx` (CAI). Key results used here: majority baseline 43.8%;
CAI-only classifier 68.1 ± 1.2%; all-features 69.0 ± 0.6%; FACS Low→Medium Cliff's δ = +0.46,
Medium→High δ = −0.03; bin-mean CAI vs bin-mean mCherry R² = 0.91; CAI range 0.73–0.95.
