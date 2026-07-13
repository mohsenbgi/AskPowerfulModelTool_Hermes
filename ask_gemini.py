import json
import os
import re
import logging
import sys
import asyncio

logger = logging.getLogger(__name__)

# Resolve the background execution script relative to this tool file,
# not to hermes's current working directory at launch.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPT_PATH = os.path.join(_SCRIPT_DIR, "gemini_web_latest_claude.py")


# --- Availability check ---

def check_ask_gemini_requirements() -> bool:
    """Return True if the local background execution script exists."""
    return (
        bool(os.getenv("GEMINI_COOKIES"))
        and os.path.exists(_SCRIPT_PATH)
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



# --- Handler ---

async def ask_gemini(query: str, model: str = "flash", task_id: str = None) -> str:
    """Query the configured powerful/free model and return clean,
    de-duplicated text. Returns a JSON string.

    `task_id` identifies the calling session/task (passed through by the
    registry from the agent loop, per-session — not read from env) and is
    used to key the background script's own session so parallel
    tasks/conversations don't clobber each other's Gemini session state.
    """
    cookies = os.getenv("GEMINI_COOKIES")

    if not os.path.exists(_SCRIPT_PATH):
        return json.dumps({"error": f"gemini_web_latest_claude.py not found at: {_SCRIPT_PATH}"})

    # Fall back to a stable default if no task_id was supplied (e.g. tool
    # invoked outside the normal agent loop / tests).
    session_id = task_id or "default"

    try:
        # Translate model names and dynamically append flags matching your architecture
        target_model = "pro" if "pro" in model.lower() else "flash"
        cmd = [sys.executable, _SCRIPT_PATH, "--session", session_id, "--model", target_model]

        cmd.append("--headed")
        cmd.append(query)

        sub_env = os.environ.copy()
        sub_env["GEMINI_COOKIES"] = cookies

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=sub_env
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return json.dumps({
                "error": f"Model script returned exit code {proc.returncode}",
                "body": stderr.decode(errors="ignore")[:500],
            })
        try:
            data = json.loads(stdout.decode().strip())
        except ValueError:
            return json.dumps({
                "error": "Model script did not return valid JSON",
                "status_code": proc.returncode,
                "body": stdout.decode(errors="ignore")[:500],
            })

        if not data.get("ok"):
            return json.dumps({
                "error": data.get("error", "Execution failed inside background daemon"),
                "body": stderr.decode(errors="ignore")[:500],
            })

        raw_text = data["text"]
    except Exception as e:
        return json.dumps({"error": str(e)})

    try:
        cleaned = _keep_last_repeated_block(raw_text)
    except Exception as e:
        return json.dumps({"error": f"Repair model call failed: {e}"})

    return json.dumps({"result": cleaned})

# --- Schema ---

ASK_GEMINI_SCHEMA = {
    "name": "ask_gemini",
    "description": (
        "Ask the configured powerful/free Gemini model a question or give it a "
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
            },
            "model": {
                "type": "string",
                "description": "The target model variant (e.g., 'flash' for common tasks or 'pro' for complex tasks). Defaults to 'flash'.",
                "default": "flash"
            }
        },
        "required": ["query"]
    }
}


# --- Registration ---

from tools.registry import registry


def _handle_ask_gemini(args, **kw):
    # task_id is injected by the registry/agent loop via kwargs, not read
    # from an environment variable, so it's correct per-session even when
    # multiple sessions/tasks run concurrently.
    task_id = kw.get("task_id")
    return ask_gemini(
        query=args.get("query", ""),
        model=args.get("model", "flash"),
        task_id=task_id,
    )


registry.register(
    name="ask_gemini",
    toolset="ask_gemini",
    schema=ASK_GEMINI_SCHEMA,
    handler=_handle_ask_gemini,
    check_fn=check_ask_gemini_requirements,
    requires_env=["GEMINI_COOKIES"],
    is_async=True,
)