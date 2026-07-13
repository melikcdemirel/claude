"""Run the real DBTL cycle, writing each phase to disk the moment it finishes."""
import os, pathlib
from main import _summarize_dataset
from orchestrator import run_agent
from agents import DBTL_ORDER

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "dave-plots" / "summary_stats.csv"
ctx = _summarize_dataset(DATA.name, DATA.read_bytes())
OUT = pathlib.Path("/root/phases")
OUT.mkdir(exist_ok=True)

OBJECTIVE = (
    "Optimize expression of an n4 Squid Ring Teeth (SRT) mCherry reporter library in E. coli "
    "around one DBTL cycle. The Test dataset is a per-bin summary (FACS Low/Medium/High gates x "
    "timepoints) of CAI and fluorescence-per-OD plus RNA folding-energy features. In the Learn "
    "phase, flag any undefined, duplicated, or anomalous tokens/columns with a confidence index."
)

handoff = f"Objective for this DBTL cycle:\n{OBJECTIVE}"
for aid in DBTL_ORDER:
    c = ctx if aid in ("test", "learn") else ""
    res = run_agent(aid, handoff, dataset_context=c)
    (OUT / f"{aid}.txt").write_text(res["output"])
    (OUT / f"{aid}.done").write_text(str(len(res["output"])))
    handoff = (
        f"Objective for this DBTL cycle:\n{OBJECTIVE}\n\n"
        f"Output from the previous phase ({res['phase']}):\n{res['output']}\n\n"
        f"Now perform your phase."
    )
(OUT / "ALL_DONE").write_text("ok")
print("done")
