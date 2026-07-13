"""
Execute the DBTL cycle for the SRT (Squid Ring Teeth) library case study,
exactly the way the web app does it (main._summarize_dataset -> run_cycle),
but scripted so we can capture all four phase outputs.

Phases requested:
  Design : n4 squid-ring-teeth combinatorial library
  Build  : codon optimization
  Test   : FACS + microcapillary uHTS
  Learn  : Figures 5 and 6 (FACS<->capillary saturation; CAI as RF predictor)
"""
import os, sys, pathlib

# Load .env (key + DBTL_MODEL) the same way uvicorn --env-file does — if present.
env = pathlib.Path(__file__).with_name(".env")
if env.exists():
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v.strip())

from main import _summarize_dataset          # the app's real dataset summarizer
from orchestrator import run_cycle, DEFAULT_MODEL

# Dataset to feed the Test/Learn phases. Override with the first CLI argument or the
# SRT_DATA env var; otherwise fall back to the bundled sample under ../data/.
_DEFAULT_DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "dave-plots" / "summary_stats.csv"
DATA = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SRT_DATA", str(_DEFAULT_DATA))
if not pathlib.Path(DATA).exists():
    sys.exit(
        f"Dataset not found: {DATA}\n"
        "Pass a CSV path as the first argument, set SRT_DATA, or place the file at\n"
        f"  {_DEFAULT_DATA}\n"
        "A small sample ships at data/dave-plots/summary_stats.csv."
    )
raw = pathlib.Path(DATA).read_bytes()
dataset_context = _summarize_dataset(os.path.basename(DATA), raw)

OBJECTIVE = (
    "Case study: heterologous expression optimization of an n4 Squid Ring Teeth (SRT) "
    "tandem-repeat structural protein library in E. coli, run around one DBTL cycle.\n\n"
    "DESIGN: an n4 SRT segmented copolymer — four amorphous fragments (GGXY-type) drawn "
    "combinatorially from 33 natural amorphous blocks across six squid species, each flanked "
    "by the constant crystalline motif AAASVSTVHHP (theoretical 33^4 ~ 1.2M variants; ~20-25k "
    "transformants sampled), expressed as an mCherry reporter fusion.\n"
    "BUILD: codon optimization of the four variable fragments for E. coli; track per-fragment "
    "codon-adaptation index (CAI) and translation-initiation strength per construct.\n"
    "TEST: two-stage screen — FACS sorts the parental library into Low/Medium/High mCherry "
    "gates (n=301,661 events; Low 30-100, Medium 100-300, High 300-3000 a.u.), then a "
    "microcapillary uHTS array measures per-clone fluorescence and brightfield OD per bin "
    "(~17k capillaries/bin) at t=15,25,35 h.\n"
    "LEARN: reproduce and interpret the analysis behind Figures 5 and 6 — does single-cell "
    "FACS brightness predict per-clone population yield across bins, and is codon usage (CAI) "
    "the dominant sequence predictor of the FACS bin? Quantify effects with Cliff's delta, "
    "note where the Medium<->High boundary is weak, and flag any tokens/values in the provided "
    "Test dataset that are undefined, anomalous, or inconsistent, with a confidence index.\n\n"
    "The dataset provided to the Test and Learn phases is the Figure 5/6 per-bin summary "
    "(CAI and fluorescence-per-OD statistics by sort bin and timepoint)."
)

print(f"MODEL: {DEFAULT_MODEL}")
print("=" * 80)
print("DATASET CONTEXT (as the app builds it):")
print(dataset_context)
print("=" * 80)

steps = run_cycle(OBJECTIVE, dataset_context=dataset_context)
for s in steps:
    print("\n" + "#" * 80)
    print(f"## {s['phase'].upper()} PHASE — {s['agent']}  ({len(s['output'])} chars)")
    print("#" * 80)
    print(s["output"])

print("\n" + "=" * 80)
print("PER-PHASE OUTPUT LENGTHS:", {s["phase"]: len(s["output"]) for s in steps})
empty = [s["phase"] for s in steps if not s["output"].strip()]
print("EMPTY PHASES:", empty or "none")
