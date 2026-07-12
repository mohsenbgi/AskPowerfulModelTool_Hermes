# tools/ask_powerful_model_tool.py
"""Ask Powerful Model Tool -- queries a free/powerful OpenAI-compatible
model and automatically repairs duplicated/stuttered text before
returning the result, so callers never see corrupted output."""

import json
import os
import re
import logging

import httpx

logger = logging.getLogger(__name__)


# --- Availability check ---

def check_ask_powerful_model_requirements() -> bool:
    """Return True if the tool's dependencies are available."""
    return (
        bool(os.getenv("POWERFUL_MODEL_API_URL"))
        and bool(os.getenv("POWERFUL_MODEL_API_KEY"))
        and bool(os.getenv("REPAIR_MODEL_API_URL"))
        and bool(os.getenv("REPAIR_MODEL_API_KEY"))
    )


# --- Repair logic (LLM-based only) ---

def _keep_last_repeated_block(text: str, min_block_chars: int = 20) -> str:
    """
    Repair text mangled by a streaming bug that re-sends the message
    from the beginning one or more times, where the final, complete
    version of the message ends up appearing twice in a row.

    Observed shape (this is what the bug produces):

        "<partial><longer partial>...<complete><complete>"

    i.e. a series of ever-growing prefixes of the real answer,
    directly concatenated with no separator, ending with the
    complete answer duplicated back-to-back.

    Approach
    --------
    Scan for the LARGEST block length L such that the last L
    characters of `text` are an exact, immediate repeat of the L
    characters right before them::

        text[-2L : -L] == text[-L:]

    That trailing duplicated block is the complete, correct message.
    Returning just one copy of it automatically discards every
    earlier, truncated restart too -- there's no need to separately
    detect or account for each partial chunk that came before it.

    We search from the largest possible L down to `min_block_chars`
    and stop at the first (i.e. largest) match, so a big genuine
    duplicated answer is always found before any small, incidental
    repeat (e.g. a repeated word) could be mistaken for it.

    Safety
    ------
    If no repeated block of at least `min_block_chars` characters is
    found, `text` is returned completely unchanged. This is
    deliberately conservative: it's far safer to leave a rare,
    undetected duplication in place than to risk cutting real content
    out of a message that was never affected by this bug.

    Parameters
    ----------
    text : str
        The possibly-duplicated text to repair.
    min_block_chars : int, optional
        Minimum length (in characters) a trailing duplicated block
        must have before it's treated as a genuine repeat rather than
        coincidental short repetition (e.g. "the the"). Defaults to 20.

    Returns
    -------
    str
        The repaired text (a single clean copy of the final block),
        or the original text if no qualifying duplication is found.
    """
    n = len(text)
    if n < min_block_chars * 2:
        return text

    # Try the largest possible block first; the first match we find
    # (scanning from big L to small L) is the correct, complete one.
    for block_len in range(n // 2, min_block_chars - 1, -1):
        split = n - block_len
        if text[split - block_len:split] == text[split:]:
            return text[split:]

    return text



async def _llm_repair(broken_text: str) -> str:
    repair_url = os.getenv("REPAIR_MODEL_API_URL")
    repair_key = os.getenv("REPAIR_MODEL_API_KEY")
    repair_model = os.getenv("REPAIR_MODEL_NAME", "gpt-4o-mini")
    if not repair_url or not repair_key:
        raise RuntimeError("REPAIR_MODEL_API_URL / REPAIR_MODEL_API_KEY not configured")

    # Extreme duplication (the same block repeated dozens of times) can blow
    # past the repair model's context window or the provider's payload size
    # limit, causing the repair call itself to fail. First try to remove
    # the redundant repeats algorithmically (keeping only the last, most
    # complete occurrence); only if it's still oversized after that do we
    # fall back to a hard truncation as a safety net.
    broken_text = _keep_last_repeated_block(broken_text)
    max_chars = int(os.getenv("REPAIR_MAX_INPUT_CHARS", "8000"))
    if len(broken_text) > max_chars:
        broken_text = broken_text[:max_chars]

    prompt = (
        "The following text was corrupted by a text-generation bug that "
        "duplicated and stuttered phrases. Reconstruct the single, clean, "
        "non-repeated version of what the speaker meant to say. "
        "Return ONLY the corrected text, nothing else.\n\n"
        f"Corrupted text:\n{broken_text}"
    )
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            repair_url,
            headers={"Authorization": f"Bearer {repair_key}"},
            json={
                "model": repair_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "stream": False,
            },
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Repair API returned HTTP {resp.status_code}: {resp.text[:500]}"
            )
        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError(
                f"Repair API did not return valid JSON (status {resp.status_code}): {resp.text[:500]}"
            )
        return data["choices"][0]["message"]["content"].strip()


# --- Handler ---

async def ask_powerful_model_tool(query: str) -> str:
    """Query the configured powerful/free model and return clean,
    de-duplicated text. Returns a JSON string."""
    model_url = os.getenv("POWERFUL_MODEL_API_URL")
    model_key = os.getenv("POWERFUL_MODEL_API_KEY")
    model_name = os.getenv("POWERFUL_MODEL_NAME", "default-model")

    if not model_url or not model_key:
        return json.dumps({"error": "POWERFUL_MODEL_API_URL / POWERFUL_MODEL_API_KEY not configured"})

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                model_url,
                headers={"Authorization": f"Bearer {model_key}"},
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": query}],
                    "stream": False,
                },
            )
        if resp.status_code != 200:
            return json.dumps({
                "error": f"Model API returned HTTP {resp.status_code}",
                "body": resp.text[:500],
            })
        try:
            data = resp.json()
        except ValueError:
            return json.dumps({
                "error": "Model API did not return valid JSON",
                "status_code": resp.status_code,
                "body": resp.text[:500],
            })
        raw_text = data["choices"][0]["message"]["content"]
    except Exception as e:
        return json.dumps({"error": str(e)})

    try:
        # cleaned = await _llm_repair(raw_text)
        cleaned = _keep_last_repeated_block(raw_text)
    except Exception as e:
        return json.dumps({"error": f"Repair model call failed: {e}"})

    return json.dumps({"result": cleaned})


# --- Schema ---

ASK_POWERFUL_MODEL_SCHEMA = {
    "name": "ask_powerful_model",
    "description": (
        "Ask the configured powerful/free model a question or give it a "
        "task (search-style query, question to answer, content to "
        "analyze). Automatically repairs duplicated/stuttered text the "
        "model's API is known to sometimes return."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The question, prompt, or task to send to the model."
            }
        },
        "required": ["query"]
    }
}


# --- Registration ---

from tools.registry import registry

registry.register(
    name="ask_powerful_model",
    toolset="ask_powerful_model",
    schema=ASK_POWERFUL_MODEL_SCHEMA,
    handler=lambda args, **kw: ask_powerful_model_tool(
        query=args.get("query", "")),
    check_fn=check_ask_powerful_model_requirements,
    requires_env=[
        "POWERFUL_MODEL_API_URL", "POWERFUL_MODEL_API_KEY",
        "REPAIR_MODEL_API_URL", "REPAIR_MODEL_API_KEY",
    ],
    is_async=True,
)
