# Cadence — a multi-agent Learn-phase copilot for the DBTL cycle

> Turn raw Test-stage data into trusted, decision-ready findings — automatically.

Cadence runs the synthetic-biology **Design → Build → Test → Learn (DBTL)** loop with four
Claude-powered agents. The **Learn** agent ingests a Test dataset, flags undefined,
duplicated, and anomalous data *tokens*, scores each with a **reproducible confidence
index**, and feeds prioritized fixes back into the next Design — closing the loop with no
analyst in the middle.

Built end to end with **Claude (Cowork)** for a hackathon (Builder track). See
[`RESEARCH.md`](RESEARCH.md) for the methodology and results, [`SUMMARY.md`](SUMMARY.md) for the
overview, and [`CRITERIA.md`](CRITERIA.md) for how the project maps to the judging rubric
(Impact / Claude Use / Depth / Demo).

**Why it matters:** the same SRT proteins are produced by fermentation as **Procell™ fiber**
(Tandem Repeat) — a 7,000-ton/year plant targeted for 2027, worn as **Sonachic** knitwear. Cadence
targets the Learn step that decides which sequences are worth scaling; at that scale a 1% yield gain
compounds into tons of product.

**Validated against:** Singhal, Allen, Gaddes, Baer & Demirel, *"Biomanufacturability of a Squid
Ring Teeth Protein Library via Orthogonal High-Throughput Screening"* (2026). Cadence's Learn agent
reproduced the paper's Figure 5–6 conclusions from the per-bin summary — FACS saturates as a yield
predictor (Cliff's δ +0.46 / −0.03), growth isn't the bottleneck, and CAI carries the residual
signal (R² = 0.91) — the "learned models feeding back into design" Learn stage the paper argues for.

---

## What it does (in one screen)

- **Four specialist agents**, each a system prompt + role, chained so each phase's output
  is the next phase's input.
- **Learn agent** = the star: on the Squid Ring Teeth case study it reproduced the paper's
  Figure 5/6 conclusions from a summary table and caught **three data defects unprompted**,
  each with a confidence score:
  - `dG_dG_cds_only` — malformed double-prefixed column (CI 0.80)
  - `ra_dG_cds_only` — undefined token + exact duplicate, r = 1.000 (CI 0.80)
  - `dG_junction` — zero-variance "dead" feature (High)
- **Web UI** — upload a CSV, enter an objective, run one agent or the whole cycle, watch
  each phase resolve. **Demo mode** works with no API key.
- **Animated schematic** — `results/schematic/dbtl_flow.html` shows a data packet running
  the loop plus a confidence-index-vs-cycle chart. Open it in any browser.

## Quick start

```bash
cd backend
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

# optional: real Claude output (else demo mode)
export ANTHROPIC_API_KEY=sk-ant-...  # or copy .env.example -> .env and edit

uvicorn main:app --reload
```

Open **http://127.0.0.1:8000**. Upload `data/dave-plots/summary_stats.csv`, enter an
objective, and click **Run full DBTL cycle**.

### Reproduce the case study headless

```bash
cd backend
python run_srt_cycle.py                    # uses the bundled sample dataset
python run_srt_cycle.py /path/to/your.csv  # or your own Test dataset
```

The captured output of a real run is in [`results/real_cycle_output.md`](results/real_cycle_output.md)
and [`results/learn_phase_full_report.txt`](results/learn_phase_full_report.txt).

### Or open the notebook (no API key needed)

[`notebooks/cadence_learn_demo.ipynb`](notebooks/cadence_learn_demo.ipynb) reproduces the Learn-phase
analysis on the sample data — the data-integrity flags and the Figure 5–6 relationships — with
outputs already embedded so it renders on GitHub. A final optional cell calls the real Claude agent
if `ANTHROPIC_API_KEY` is set.

## Repository layout

```
cadence-dbtl/
├── backend/
│   ├── main.py            # FastAPI app + routes + dataset summarizer, serves the frontend
│   ├── agents.py          # the 4 agent definitions + system prompts
│   ├── orchestrator.py    # the only file that calls Claude; run_agent + run_cycle
│   ├── run_srt_cycle.py   # scripted case-study harness (Design→Build→Test→Learn)
│   ├── requirements.txt
│   └── .env.example
├── frontend/              # index.html · style.css · app.js (no build step)
├── data/dave-plots/       # small, schema-faithful sample dataset (contains the 3 defects)
├── notebooks/             # cadence_learn_demo.ipynb — reproduce the Learn analysis (no key needed)
├── results/               # captured real-run output + the animated schematics + demo video
├── docs/                  # architecture.md · changelog.md (engineering log)
├── RESEARCH.md            # methodology, results, limitations, future work
├── SUMMARY.md             # 180-word summary
└── LICENSE                # MIT
```

## How Claude is used

The four agents *are* Claude with distinct system prompts, orchestrated in a loop. The
orchestrator reads `stop_reason` and retries when a hidden reasoning block exhausts the
token budget (see `docs/changelog.md` for that bug hunt). And the whole project —
scaffolding, a from-Drive v3 reconstruction and fix, the live run, decks, the animated
schematic, and the write-up — was produced with Claude (Cowork) in one session.

## Limitations

The Learn agent reasons over a pre-aggregated summary, not the raw per-clone table;
multivariate claims need real code execution (roadmap). Undefined-token detection is
model-judgment, not yet grounded in a reference vocabulary. Only cycle 1 is measured; the
confidence-vs-cycle trajectory in the schematic is modeled and labeled as such. Details in
[`RESEARCH.md`](RESEARCH.md) §6.

## License

MIT — see [`LICENSE`](LICENSE).
