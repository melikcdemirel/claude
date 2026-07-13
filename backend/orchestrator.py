"""
Orchestration logic: how we actually call Claude for a single agent, and how we
run the full DBTL cycle by chaining agents so each one's output feeds the next.

Design goal: this file is the ONLY place that talks to the Anthropic API, so the
rest of the app doesn't need to know how the model is called.
"""

import os

from agents import AGENTS, DBTL_ORDER, get_agent

# The model the agents use. See https://platform.claude.com/docs/en/about-claude/models
# claude-sonnet-4-6 is Anthropic's recommended general-purpose default (good speed +
# intelligence). You can change this to any current model id.
DEFAULT_MODEL = os.environ.get("DBTL_MODEL", "claude-sonnet-4-6")
# These agents are verbose and (on models that emit a hidden `thinking` block) the
# reasoning is counted against this budget before any visible `text` is produced.
# At 8000 the Learn phase — which receives the largest handoff — spent the whole
# budget on reasoning and rendered blank, and Build/Test truncated mid-answer.
# Configurable via DBTL_MAX_TOKENS.
MAX_TOKENS = int(os.environ.get("DBTL_MAX_TOKENS", "20000"))


def _get_client():
    """
    Create an Anthropic client if an API key is present.
    Returns None when no key is set, so the app can run in 'demo mode'.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    # Imported lazily so the app can still start without the package/key.
    from anthropic import Anthropic

    return Anthropic(api_key=api_key)


def _demo_reply(agent, user_message):
    """A canned response used when no ANTHROPIC_API_KEY is configured."""
    return (
        f"[DEMO MODE] The {agent['name']} ({agent['phase']} phase) received your input "
        f"but no ANTHROPIC_API_KEY is set, so this is a placeholder.\n\n"
        f"Your input was:\n{user_message[:500]}\n\n"
        f"Set ANTHROPIC_API_KEY (see README) to get a real analysis from Claude."
    )


def run_agent(agent_id: str, user_message: str, dataset_context: str = "") -> dict:
    """
    Run a single agent once.

    - agent_id: which agent (design/build/test/learn)
    - user_message: the task/instruction or the upstream agent's output
    - dataset_context: optional text summary of an uploaded dataset

    Returns a dict: {agent, phase, output}.
    """
    agent = get_agent(agent_id)
    if agent is None:
        raise ValueError(f"Unknown agent: {agent_id}")

    # Assemble the user-facing content: the task, plus any dataset context.
    content = user_message or ""
    if dataset_context:
        content += (
            "\n\n--- DATASET CONTEXT (provided inline below) ---\n"
            "The dataset is included directly in this message. Analyze it as given; "
            "no external file or code tools are available in this session, so do not "
            "wait for files to be attached.\n\n" + dataset_context
        )

    client = _get_client()
    if client is None:
        return {
            "agent": agent["name"],
            "phase": agent["phase"],
            "output": _demo_reply(agent, content),
        }

    def _call(max_tokens):
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=max_tokens,
            system=agent["system_prompt"],
            messages=[{"role": "user", "content": content}],
        )
        # The Messages API returns a list of content blocks; join the text ones.
        # (Models that emit a hidden `thinking` block spend budget on it before any
        # `text` appears, so an empty join with stop_reason == "max_tokens" means the
        # answer was cut off mid-reasoning, not that the model had nothing to say.)
        text = "".join(
            b.text for b in response.content if getattr(b, "type", "") == "text"
        )
        return text, getattr(response, "stop_reason", None)

    output_text, stop_reason = _call(MAX_TOKENS)

    # If the visible answer came back empty because the budget was exhausted (e.g. a
    # long `thinking` block consumed all of MAX_TOKENS), retry once with more room
    # rather than returning a silently-blank result to the next phase / the user.
    if stop_reason == "max_tokens" and not output_text.strip():
        output_text, stop_reason = _call(MAX_TOKENS * 2)

    # Never hand downstream a blank string with no explanation. If it is still empty
    # or was truncated, say so explicitly so the UI/next phase can see what happened.
    if not output_text.strip():
        output_text = (
            f"[NO OUTPUT] The {agent['name']} returned no visible text "
            f"(stop_reason={stop_reason}). This usually means the token budget was "
            f"spent on hidden reasoning before any answer was produced. Raise "
            f"DBTL_MAX_TOKENS (currently {MAX_TOKENS}) and re-run this phase."
        )
    elif stop_reason == "max_tokens":
        output_text += (
            f"\n\n[TRUNCATED] Output stopped at the {MAX_TOKENS}-token limit "
            f"(stop_reason=max_tokens); the answer above may be incomplete. Raise "
            f"DBTL_MAX_TOKENS to get the full response."
        )

    return {
        "agent": agent["name"],
        "phase": agent["phase"],
        "output": output_text,
    }


def run_cycle(objective: str, dataset_context: str = "") -> list:
    """
    Run the full DBTL loop once: Design -> Build -> Test -> Learn.

    Each agent receives the objective plus the previous agent's output, so the
    'handoff' between phases is just passing text forward. Returns a list of
    step results in order.
    """
    steps = []
    handoff = f"Objective for this DBTL cycle:\n{objective}"

    for agent_id in DBTL_ORDER:
        # Only the Learn phase gets the raw dataset context by default, since that
        # is where the provided prompt does its analysis. (Test also gets it so it
        # can describe the schema.)
        ctx = dataset_context if agent_id in ("test", "learn") else ""
        result = run_agent(agent_id, handoff, dataset_context=ctx)
        steps.append(result)

        # The next agent's task is "continue the cycle using what the last agent produced".
        handoff = (
            f"Objective for this DBTL cycle:\n{objective}\n\n"
            f"Output from the previous phase ({result['phase']}):\n{result['output']}\n\n"
            f"Now perform your phase."
        )

    return steps
