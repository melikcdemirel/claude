# Architecture guide — DBTL Multi-Agent Lab

This is the "why" behind the code, written for someone new to building web apps. Read it
top to bottom once; you don't need to memorize it.

## 1. The big picture

A website is really two programs talking to each other:

- A **frontend** — the page in the browser. It's what the user sees and clicks. Built
  from HTML (structure), CSS (looks), and JavaScript (behavior).
- A **backend** — a program running on a server. It does the work the browser can't or
  shouldn't do: talking to the AI model, holding secrets like your API key, and
  processing files.

They talk over **HTTP** using small messages called **API requests**. Our frontend sends
a request like "run the Learn agent with this text," and the backend replies with the
agent's answer as **JSON** (a simple text format for data).

```
  Browser (frontend)                    Server (backend)                 Anthropic
 ┌───────────────────┐   HTTP/JSON   ┌────────────────────┐   HTTPS   ┌────────────┐
 │ index.html        │ ───────────▶  │ FastAPI (main.py)  │ ────────▶ │  Claude    │
 │ app.js  style.css │ ◀───────────  │ orchestrator.py    │ ◀──────── │  model     │
 └───────────────────┘               │ agents.py          │           └────────────┘
                                      └────────────────────┘
```

Keeping the API key on the backend matters: if the browser called Anthropic directly,
anyone could open the page source and steal your key.

## 2. Why this tech stack (for a beginner)

- **Python + FastAPI** for the backend. Python is beginner-friendly and is the default
  language for data and AI work, so the Learn agent's future data analysis fits naturally.
  FastAPI turns Python functions into API endpoints with very little code.
- **Plain HTML/CSS/JS** for the frontend, with **no build step**. Fancier setups (React,
  Vite, TypeScript) are great later, but they add tooling that gets in the way while
  you're learning. You can open the files and see exactly what runs.
- **The Anthropic Python SDK** to call Claude. One function call, `messages.create(...)`,
  gives an agent its answer.

When you outgrow this, the natural upgrades are: React for the frontend, a database
(Postgres) for saving results, and a hosting platform for deployment. The API contract
between frontend and backend stays the same, so you can swap either side independently.

## 3. What "multiple agents" means here

An "agent" in this project is just **a system prompt + a role**. The system prompt is the
instruction block that tells Claude who it is and how to behave. We have four, one per
DBTL phase, defined in `agents.py`:

| Agent  | Phase  | Job |
|--------|--------|-----|
| Design | Design | Turn goals + last cycle's learnings into concrete design candidates. |
| Build  | Build  | Turn designs into a build plan / protocol with traceable sample IDs. |
| Test   | Test   | Define measurements and the dataset schema; summarize incoming data. |
| Learn  | Learn  | Analyze the dataset, flag **undefined tokens**, score confidence. *(your prompt)* |

They are **specialists that hand off to each other**. That's what makes this a
multi-agent system rather than one chatbot: each phase has focused instructions, and the
output of one becomes the input of the next.

## 4. How the handoff (orchestration) works

`orchestrator.py` is the conductor. Two functions matter:

- `run_agent(agent_id, message, dataset_context)` — runs **one** agent. It looks up that
  agent's system prompt, sends your message (plus any dataset summary) to Claude, and
  returns the text.
- `run_cycle(objective, dataset_context)` — runs **all four in order**. It starts with
  your objective, and after each phase it builds the next agent's message as:
  *"Here's the objective, here's what the previous phase produced, now do your phase."*
  That passing-of-text forward is the whole trick behind the DBTL loop.

This is deliberately the simplest form of orchestration: a fixed, linear pipeline. It's
easy to reason about and easy to extend (see §7).

## 5. Following one request end to end

When you click **Run full DBTL cycle**:

1. `app.js` reads your objective and sends `POST /api/cycle` to the backend.
2. `main.py` receives it and calls `run_cycle(...)`.
3. `run_cycle` calls Claude four times — Design, then Build, then Test, then Learn —
   threading each output into the next prompt.
4. The backend returns all four results as JSON.
5. `app.js` renders each result and lights up the matching agent card.

If no API key is set, step 3 returns friendly placeholder text instead of calling Claude,
so the UI still works while you explore ("demo mode").

## 6. The files, in one line each

- `backend/agents.py` — the four agents and their system prompts (the Learn one is yours).
- `backend/orchestrator.py` — the only file that calls Claude; single-agent + full-cycle.
- `backend/main.py` — the web server: defines the URLs, handles uploads, serves the page.
- `frontend/index.html` — the page structure.
- `frontend/style.css` — the styling.
- `frontend/app.js` — reads your input, calls the API, shows results.

## 7. Sensible next steps (in a good order)

1. **Stream responses** so text appears as it's generated (nicer UX). The Anthropic SDK
   supports `messages.stream(...)`; you'd send it to the browser with Server-Sent Events.
2. **Save cycle history** to a database (start with SQLite — a single file — then move to
   Postgres) so you can compare cycles over time.
3. **Give the Learn agent real reference vocabularies.** Right now it reasons over the
   dataset summary text. You could load a known-parts list (e.g. from a CSV or a registry)
   and pass it in so "undefined token" detection is grounded in real data, and even
   compute the confidence index in Python rather than leaving it to the model.
4. **Let agents actually run code / read files** for true data analysis (the Learn prompt
   mentions file and code tools). This is where the Anthropic tool-use / agent features come in.
5. **Add accounts and auth** if more than one person will use it.
6. **Deploy it** so others can reach it (a platform like Render, Railway, or Fly.io can
   host the FastAPI app; the frontend is served by the same app).

## 8. A few good habits

- Never commit your API key. Keep it in an environment variable or an untracked `.env`.
- Keep the boundary clean: the frontend should only ever talk to *your* backend, never to
  Anthropic directly.
- Change one thing at a time and reload — with `--reload`, the server restarts on save.
