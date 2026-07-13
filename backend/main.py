"""
FastAPI backend for the DBTL multi-agent website.

Endpoints:
  GET  /                     -> serves the frontend (index.html)
  GET  /api/agents           -> list the 4 DBTL agents
  POST /api/agent/{agent_id} -> run one agent
  POST /api/cycle            -> run the full Design->Build->Test->Learn loop
  POST /api/upload           -> upload a dataset (csv/tsv/txt) and get a summary

Run it with:  uvicorn main:app --reload   (from the backend/ folder)
"""

import io
import os

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents import list_agents
from orchestrator import run_agent, run_cycle

app = FastAPI(title="DBTL Multi-Agent API")

# Allow the frontend to call the API during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BACKEND_DIR, "..", "frontend")
UPLOAD_DIR = os.path.join(BACKEND_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory store of the most recent dataset summary, so agents can reference it.
LATEST_DATASET = {"summary": ""}


# ---------- Request models ----------
class AgentRequest(BaseModel):
    message: str = ""
    use_dataset: bool = True


class CycleRequest(BaseModel):
    objective: str
    use_dataset: bool = True


# ---------- API routes ----------
@app.get("/api/agents")
def api_agents():
    return {"agents": list_agents()}


@app.post("/api/agent/{agent_id}")
def api_run_agent(agent_id: str, req: AgentRequest):
    ctx = LATEST_DATASET["summary"] if req.use_dataset else ""
    result = run_agent(agent_id, req.message, dataset_context=ctx)
    return result


@app.post("/api/cycle")
def api_run_cycle(req: CycleRequest):
    ctx = LATEST_DATASET["summary"] if req.use_dataset else ""
    steps = run_cycle(req.objective, dataset_context=ctx)
    return {"steps": steps}


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    """Accept a dataset file, save it, and compute a lightweight text summary."""
    raw = await file.read()
    dest = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest, "wb") as f:
        f.write(raw)

    summary = _summarize_dataset(file.filename, raw)
    LATEST_DATASET["summary"] = summary
    return {"filename": file.filename, "summary": summary}


def _summarize_dataset(filename: str, raw: bytes) -> str:
    """
    Build a small text summary of a tabular file (rows, columns, first rows).
    Uses pandas when the file looks tabular; falls back to a byte/line count.
    """
    text = None
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        pass

    lower = filename.lower()
    if lower.endswith((".csv", ".tsv", ".txt")) and text is not None:
        try:
            import pandas as pd

            sep = "\t" if lower.endswith(".tsv") else ","
            df = pd.read_csv(io.StringIO(text), sep=sep)
            cols = ", ".join(map(str, df.columns))

            # Missing values, per column (so Learn can reason about gaps).
            missing_by_col = df.isna().sum()
            missing_lines = "\n".join(
                f"  - {c}: {int(n)} missing" for c, n in missing_by_col.items() if n
            ) or "  (none)"

            # Value counts for low-cardinality columns — this is where the Learn
            # agent's "undefined tokens" (rare parts/labels) actually live.
            cat_lines = []
            for c in df.columns:
                if df[c].dtype == object or df[c].nunique(dropna=True) <= 20:
                    vc = df[c].value_counts(dropna=False).head(15)
                    pairs = ", ".join(f"{k!r}x{int(v)}" for k, v in vc.items())
                    cat_lines.append(
                        f"  - {c} ({df[c].nunique(dropna=True)} unique): {pairs}"
                    )
            cat_block = "\n".join(cat_lines) or "  (no low-cardinality columns)"

            # Include the actual rows inline so Learn can analyze them directly,
            # without needing file/code tools. Bound the size for big datasets.
            if len(df) <= 100:
                table = df.to_string(index=False)
            else:
                table = (
                    df.head(20).to_string(index=False)
                    + f"\n... ({len(df) - 25} more rows omitted) ...\n"
                    + df.tail(5).to_string(index=False)
                )

            return (
                f"File: {filename}\n"
                f"Rows: {len(df)}, Columns: {df.shape[1]}\n"
                f"Column names: {cols}\n"
                f"Missing values by column:\n{missing_lines}\n"
                f"Value counts (low-cardinality columns):\n{cat_block}\n"
                f"Data rows:\n{table}"
            )
        except Exception as e:
            # Not clean tabular data — fall through to the generic summary.
            note = f"(Could not parse as a table: {e})\n"
            preview = text[:800]
            return f"File: {filename}\n{note}Preview:\n{preview}"

    return f"File: {filename}\nSize: {len(raw)} bytes (non-text or unsupported for summary)."


# ---------- Serve the frontend ----------
# Static assets (app.js, style.css) live in ../frontend.
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found. See the frontend/ folder."}
