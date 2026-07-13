# Change Log — DBTL Multi-Agent Lab

All notable setup steps and code changes are recorded here.

## 2026-07-12

### Bug fix — Learn agent returned empty output again (large-handoff case)
- **File:** `backend/orchestrator.py`
- **Symptom:** On the full SRT n4 DBTL cycle, the Learn phase rendered completely
  blank and the Build/Test phases truncated mid-sentence. Cause was the same hidden
  `thinking`-block-eats-the-budget failure fixed earlier at 2000 tokens, now recurring
  at 8000 because these agents are verbose and Learn receives the largest handoff.
- **Changes:**
  - `MAX_TOKENS` raised 8000 → 20000 and made configurable via `DBTL_MAX_TOKENS`.
  - `run_agent` now reads `stop_reason`. If the visible text is empty because the
    budget was spent on reasoning (`stop_reason == "max_tokens"`), it retries once
    with double the budget.
  - A phase is never returned silently blank: an empty result becomes an explicit
    `[NO OUTPUT]` note, and a truncated one gets a `[TRUNCATED]` marker — both name
    `DBTL_MAX_TOKENS` so the operator knows the knob to turn.
- **Verified:** Learn phase went from 0 chars to a full Fig 5/6 analysis (Cohen's d,
  η², defined confidence index, and correct undefined-token flags — e.g. the
  `ra_dG_cds_only` duplicate column).
- **Added:** `backend/run_srt_cycle.py` — a scripted harness that runs the SRT n4
  case-study cycle (Design=n4 SRT, Build=codon optimization, Test=FACS+uHTS,
  Learn=Figs 5/6) over `data/dave-plots/summary_stats.csv`, mirroring the web app's
  `_summarize_dataset` → `run_cycle` path.
### SRT n4 DBTL cycle — run findings
Ran the full cycle (`claude-sonnet-5`) on the paper's case study: Design = n4 SRT
combinatorial library, Build = codon optimization, Test = FACS + microcapillary uHTS,
Learn = Figures 5/6. Dataset handed to Test/Learn = `data/dave-plots/summary_stats.csv`.
- **Pipeline defect found (now fixed above):** Learn returned blank; Build/Test truncated.
- **Learn analysis, post-fix, reproduces the paper's Fig 5/6 conclusions from the summary:**
  - FACS bin predicts uHTS yield only coarsely: **Low separates cleanly** (Cohen's d up
    to 1.40 at t=35h; η² up to 27.6%) but the **Medium↔High boundary is negligible**
    (d = 0.03–0.09) and its sign flips across t=15/25/35 h — a non-reproducible ranking.
    Matches the paper's "FACS saturates as a predictor above a moderate brightness
    threshold; treat Medium+High as one merged tier."
  - Sequence features are all weak individually (each <5% of bin variance); the Learn
    agent correctly notes the paper's CAI-dominance claim must rest on a *multivariate*
    Random Forest, which cannot be reconstructed from marginal summary stats.
  - Undefined-token flags (with confidence index): `ra_dG_cds_only` = exact duplicate of
    `dG_dG_cds_only` (CI 0.05, aliasing artifact); `dG_junction`/`dG_utr_cds30` invariant
    (zero std across all bins) — excluded from predictive ranking.

### Recommendations — improving the Learn agent (prioritized)
- **Tier 1 (DONE, above):** token-budget + `stop_reason` handling so Learn is never
  silently blank.
- **Tier 2 (NOT done — highest-value next step): give Learn real code execution.**
  It currently only sees a 30-row pre-aggregated summary and its own system prompt's
  "use file and code tools" line is overridden to "no tools available." So it can narrate
  but cannot compute the paper's Random Forest / Cliff's-δ. Fix: code-execution tool +
  Files API (or a local Python tool-loop) over the raw 13,963-clone table
  (`data/sequence-features-by-bin.xlsx`, 56 features). ARCHITECTURE.md §7.4.
- **Ground "undefined tokens" in a real reference vocabulary** (the 33 amorphous blocks,
  6 species, gate a.u. definitions, feature schema) instead of letting the model guess
  what "known" means. ARCHITECTURE.md §7.3.
- **Define the confidence index** (scale + inputs + formula) in the prompt, or compute it
  deterministically in Python and have the agent interpret it — currently each run
  invents its own. ARCHITECTURE.md §7.3.
- **Thread full-cycle context into the Learn handoff.** Each phase currently forwards only
  the immediately previous phase's text, so Learn never sees Design's pre-registered
  anomaly checklist or Build's assumptions-of-record. Pass a compact running cycle-memory.
- **Feed Learn the raw per-clone table, not the pre-binned summary** — undefined-token
  detection is meant to run on the 13,963-row data, not on 30 rows of means.

## 2026-07-11

### Environment / setup
- **Restored directory write permissions.** Every project directory was `dr-x------`
  (owner read-only, no write bit), which blocked venv creation. Added the owner write
  bit back to `dbtl-agents/`, `backend/`, `frontend/`, and `backend/uploads/`.
- **Created the Python virtual environment** at `backend/venv` and installed all
  dependencies from `requirements.txt` (fastapi, uvicorn, anthropic, pandas,
  python-multipart, pydantic) on Python 3.12.3.
- **Configured the Anthropic API key.** Wrote `backend/.env` (untracked, chmod 600)
  with `ANTHROPIC_API_KEY` and `DBTL_MODEL=claude-sonnet-5`. The project's built-in
  default model id `claude-sonnet-4-6` was overridden because it was rejected/stale;
  `claude-sonnet-5` is confirmed working.
- **Started the server** with `uvicorn main:app --reload --host 0.0.0.0 --port 8002 --env-file .env`.
  - Port 8000 (README default) and 8001 were already in use, so the app runs on **8002**.
  - Bound to `0.0.0.0` so it is reachable from other devices:
    - Same LAN: `http://10.0.0.16:8002`
    - Tailscale: `http://100.82.92.117:8002`
    - Local: `http://127.0.0.1:8002`
  - NOTE: `0.0.0.0` + no auth means anyone on the LAN/tailnet can spend against the
    API key. Rebind to `127.0.0.1` if remote access is not needed.

### Bug fix — Learn agent returned empty output
- **File:** `backend/orchestrator.py`
- **Change:** `MAX_TOKENS` raised from `2000` to `8000`.
- **Why:** The model emits a hidden `thinking` block before its visible `text`. On the
  full DBTL cycle, the Learn agent's long reasoning consumed the entire 2000-token
  budget (`stop_reason: max_tokens`) before any `text` was produced. Since the
  orchestrator only joins `text` blocks, the rendered output was blank. Raising the cap
  leaves room for both the reasoning and the answer, and also stops the other phases
  from being truncated mid-sentence.
- **Side effect:** A full cycle now takes ~2-4 minutes (four sequential calls generating
  full-length output).

### Feature — Learn agent analyzes data inline (no file/code tools required)
- **File:** `backend/main.py` (`_summarize_dataset`)
  - The uploaded-dataset summary is now richer: per-column missing-value counts,
    value counts for every low-cardinality column (where "undefined tokens" live), and
    the actual data rows inline (full table for <= 100 rows; head+tail beyond that).
- **File:** `backend/orchestrator.py` (`run_agent`, dataset-context assembly)
  - The dataset block prepended to the agent message now states the data is provided
    inline and that no external file/code tools are available, so the agent should
    analyze it directly instead of waiting for attached files.
  - The owner-supplied Learn system prompt in `agents.py` was left unchanged; this
    inline instruction overrides its "use file and code tools" line at the message level.
- **Result:** The Learn agent now produces full analyses — descriptive stats, a token
  vocabulary check, and confidence-scored flagging of undefined/anomalous tokens
  (e.g. correctly flagging `J23100` appearing in the `rbs` column as a category
  mismatch) — with no tool infrastructure to build.
- **Future path:** For genuinely large Test datasets, the real file/code-tool approach
  in `ARCHITECTURE.md` §7.4 is still the eventual upgrade; the 100-row inline cap is a
  deliberate bound.
