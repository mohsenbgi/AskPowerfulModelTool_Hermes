"""
gemini_web.py — Gemini Web tool for Hermes (single-file)

Talks to Google Gemini's *web* interface (not the official API) using
browser cookies + Playwright automation. Built as a background daemon + a
thin one-shot CLI so it can be wired into Hermes as a normal subprocess tool:

    - Every invocation of this script (without --daemon) is a CLIENT:
      it parses args, makes ONE request, prints ONE line of JSON to stdout,
      and exits. It never blocks waiting on stdin — the LLM only ever talks
      to argv/stdout, never to an interactive terminal.
    - On the FIRST call, if no daemon is running yet, the client silently
      spawns one as a detached background process (its own session, not
      attached to your terminal) and waits for it to finish loading the
      browser before sending the request. Every call after that reuses the
      same already-running daemon — the browser is never relaunched.
    - Each Hermes "session" gets its own persistent browser TAB inside the
      daemon (keyed by --session <id>). A new session id → a new Gemini tab
      / fresh conversation. Same session id again → same tab, same
      conversation, still there.

Reliability features:
    - Strict model active-check: after (re)selecting Flash/Pro, re-reads the
      mode-picker's aria-label and confirms it actually matches. If the
      account has been silently downgraded to Gemini Lite (a common sign of
      a hit rate/usage limit), or any other mismatch is detected, the
      request is treated as failed and the daemon rotates to the next
      cookie automatically.
    - UI-driven completion detection instead of a fixed timeout: watches the
      "Stop generating" button / typing indicator so long code responses
      aren't cut off early, rather than racing a fixed network timeout.
    - 10 MB Unix-socket line limits on both client and daemon, so large code
      payloads don't trip asyncio's "Separator is found, but chunk is longer
      than limit" error.
    - Aggressive recovery: detects the prompt text "bouncing back" into the
      input box mid-generation (a common Gemini UI error signal), forces the
      input box empty before typing, reloads if the Send button never lights
      up, and retries the whole workspace-load sequence up to 3 times before
      giving up on a tab.

Install:
    pip install playwright --break-system-packages
    python -m playwright install chromium

Cookies (see _cookies_from_env for all supported forms):
    export GEMINI_COOKIES="__Secure-1PSID=aaa; __Secure-1PSIDTS=bbb|||__Secure-1PSID=ccc; __Secure-1PSIDTS=ddd"

Basic use (this is what Hermes would shell out to):
    python gemini_web.py --session chat-123 --model flash "What is the capital of France?"
    → {"ok": true, "session_id": "chat-123", "model": "gemini-3.5-flash", "text": "Paris."}

    python gemini_web.py --session chat-123 --model pro --thinking "Now explain why."
    → same tab/conversation, switches to Pro + extended thinking first.

Housekeeping:
    python gemini_web.py --session chat-123 --close-session   # close that one tab
    python gemini_web.py --shutdown                           # stop the whole daemon
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import signal as signal_module
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Optional

# ─── Constants ──────────────────────────────────────────────────────────────

GEMINI_URL = "https://gemini.google.com/app"

GEMINI_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
)

_MISSING_BROWSER_RE = re.compile(
    r"executable doesn't exist|executablenotfound|playwright install|chromium.*download",
    re.IGNORECASE,
)

_COOKIE_ATTR_NAMES = {
    "path", "domain", "expires", "max-age", "secure", "httponly", "samesite",
}

# Short names you can pass as --model → real model id.
MODEL_ALIASES = {
    "flash": "gemini-3.5-flash",
    "pro": "gemini-3-pro",
}

# ─── Daemon IPC paths (override via env if you need multiple daemons) ─────
SOCK_PATH = os.environ.get("GEMINI_WEB_SOCK", "/tmp/gemini_web_daemon.sock")
PID_PATH = os.environ.get("GEMINI_WEB_PID", "/tmp/gemini_web_daemon.pid")
LOG_PATH = os.environ.get("GEMINI_WEB_LOG", "/tmp/gemini_web_daemon.log")

# Unix-socket line-buffer limit. Default asyncio limit is 64 KB, which a
# single big code response blows through ("Separator is found, but chunk is
# longer than limit" error). 10 MB comfortably covers huge code payloads.
SOCKET_LINE_LIMIT = 10 * 1024 * 1024

# ─── UI selectors (BEST-EFFORT — Gemini's web DOM changes over time) ───────
# If model switching / thinking toggling / message sending stops working,
# open gemini.google.com, right-click the relevant control → Inspect, and
# update the selectors/text below to match. Everything UI-related is
# centralized here on purpose.

CHAT_INPUT_SELECTOR = ".ql-editor, [contenteditable='true']"

# Confirmed via live DOM inspection (2026-07-13):
#   <button data-test-id="bard-mode-menu-button"
#           aria-label="Open mode picker, currently Flash" ...>
MODEL_SWITCHER_BUTTON_SELECTORS = [
    "[data-test-id='bard-mode-menu-button']",
    "button[aria-label*='mode picker' i]",
    "button[aria-label*='model' i]",
]

# Text fragments to match against menu items once the model picker is open.
MODEL_UI_LABELS = {
    "gemini-3.5-flash": ["3.5 Flash", "Flash"],
    "gemini-3-pro": ["3.1 Pro", "Pro"],
}

# Fragments in the mode-picker's aria-label that indicate the account has
# been silently downgraded (usually from hitting a rate/usage limit), not a
# model the user ever asked for.
DOWNGRADE_LABELS = ["lite"]

# Candidate selectors for the "extended thinking" toggle.
THINKING_TOGGLE_SELECTORS = [
    "button[aria-label*='thinking' i]",
    "[data-test-id*='thinking' i]",
    "text=/extended thinking/i",
]

# Candidate selectors for the send button.
SEND_BUTTON_SELECTORS = [
    "button[aria-label*='send' i]",
    "[data-test-id*='send-button' i]",
]

# Candidate selectors for the "Stop generating" button, shown only while
# Gemini is actively producing a response.
STOP_GENERATING_BUTTON_SELECTORS = [
    "button[aria-label*='stop' i]",
    "[data-test-id*='stop-generating' i]",
    "button:has-text('Stop')",
]

# Candidate selectors for any "still typing / thinking" indicator shown in
# the main content area while a response is being generated.
TYPING_INDICATOR_SELECTORS = [
    "[data-test-id*='loading' i]",
    ".loading-indicator",
    "[aria-label*='generating' i]",
]

# Phrases that indicate the account hit a usage/rate limit.
RATE_LIMIT_PHRASES = [
    "reached your limit",
    "rate limit",
    "try again later",
    "unable to process",
    "quota",
    "temporarily unavailable",
    "you've hit your limit",
]


def is_missing_browser_executable(message: str) -> bool:
    if not message:
        return False
    return bool(_MISSING_BROWSER_RE.search(message))


def _looks_rate_limited(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(phrase in lowered for phrase in RATE_LIMIT_PHRASES)


# ─── Cookie helpers ─────────────────────────────────────────────────────────

def parse_cookies(raw: str) -> list[dict[str, str]]:
    """Parse a 'name=value; name2=value2' string, stripping cookie attributes."""
    result: list[dict[str, str]] = []
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        eq_idx = part.find("=")
        if eq_idx == -1:
            continue
        name = part[:eq_idx].strip()
        value = part[eq_idx + 1:].strip()
        if not name or not value:
            continue
        if name.lower() in _COOKIE_ATTR_NAMES:
            continue
        result.append({"name": name, "value": value})
    return result


def _normalize_gemini_cookie_input(raw: str, cookie_name: str = "__Secure-1PSID") -> str:
    trimmed = raw.strip()
    if not trimmed:
        return ""
    return trimmed if "=" in trimmed else f"{cookie_name}={trimmed}"


def _cookies_from_env() -> list[str]:
    """
    Supported env vars, checked in order:
      - GEMINI_COOKIES: one or more full cookie strings separated by "|||"
      - GEMINI_COOKIE_1, GEMINI_COOKIE_2, ...: numbered full cookie strings
      - GEMINI_SECURE_1PSID / GEMINI_SECURE_1PSIDTS: single legacy pair
    """
    raw = os.environ.get("GEMINI_COOKIES", "").strip()
    if raw:
        return [_normalize_gemini_cookie_input(c) for c in raw.split("|||") if c.strip()]

    numbered: list[str] = []
    i = 1
    while True:
        val = os.environ.get(f"GEMINI_COOKIE_{i}", "").strip()
        if not val:
            break
        numbered.append(_normalize_gemini_cookie_input(val))
        i += 1
    if numbered:
        return numbered

    psid = os.environ.get("GEMINI_SECURE_1PSID", "").strip()
    psidts = os.environ.get("GEMINI_SECURE_1PSIDTS", "").strip()
    if psid:
        cookie = f"__Secure-1PSID={psid}"
        if psidts:
            cookie += f"; __Secure-1PSIDTS={psidts}"
        return [cookie]

    return []


def parse_stream_response(raw: str) -> str:
    """
    Parse Gemini StreamGenerate response text.

    Format:
        )]}'
        <length>
        [["wrb.fr", null, "<JSON string>"]]
        ...

    The JSON string nests: inner[4][0][1] = ["text chunks"]. Each
    StreamGenerate response is generally a full snapshot (not a delta), so
    callers should treat the LATEST successfully-parsed non-empty result as
    the best-known text, not concatenate across responses.
    """
    text_chunks: list[str] = []
    for raw_line in raw.split("\n"):
        line = raw_line.strip()
        if not line or line == ")]}'" or line.isdigit():
            continue
        if "wrb.fr" not in line:
            continue
        try:
            arr = json.loads(line)
            if not isinstance(arr, list) or not arr or not isinstance(arr[0], list):
                continue
            if arr[0][0] != "wrb.fr":
                continue
            payload = arr[0][2] if len(arr[0]) > 2 else None
            if not isinstance(payload, str):
                continue
            inner = json.loads(payload)
            response_array = _safe_get(inner, 4, 0, 1)
            if not isinstance(response_array, list):
                continue
            text = "".join(c for c in response_array if isinstance(c, str))
            if text:
                text_chunks.append(text)
        except (json.JSONDecodeError, TypeError, IndexError):
            continue
    return "".join(text_chunks)


def _safe_get(obj: Any, *path: int) -> Any:
    cur = obj
    for idx in path:
        if not isinstance(cur, list) or idx >= len(cur):
            return None
        cur = cur[idx]
    return cur


# ─── Core: multi-session browser manager (lives inside the daemon) ────────

class GeminiWebManager:
    """
    Owns ONE Playwright browser for the whole daemon's lifetime. Each Hermes
    session gets its own `page` (browser tab) inside a shared browser
    context. If the active cookie gets rate-limited, downgraded, or its tabs
    end up in a broken state that can't be recovered, rotates to the next
    cookie by opening a fresh context — this closes and re-opens all
    currently-tracked tabs (documented trade-off; simpler and more reliable
    than juggling one context per cookie x per session).
    """

    def __init__(self, cookies: list[str], *, headless: bool = True, debug_dir: Optional[str] = None) -> None:
        if not cookies:
            raise ValueError("GeminiWebManager requires at least one cookie")
        self._cookies = cookies
        self._cookie_index = 0
        self._headless = headless
        self._debug_dir = debug_dir

        self._playwright = None
        self._browser = None
        self._context = None

        self._pages: dict[str, Any] = {}
        self._page_model: dict[str, Optional[str]] = {}
        self._page_thinking: dict[str, Optional[bool]] = {}

        self._lock = asyncio.Lock()

    # ── lifecycle ──────────────────────────────────────────────────────

    async def ensure_browser(self) -> None:
        from playwright.async_api import async_playwright

        if self._playwright is None:
            self._playwright = await async_playwright().start()
        if self._browser is None:
            self._browser = await self._playwright.chromium.launch(headless=self._headless)
        if self._context is None:
            await self._new_context(self._cookies[self._cookie_index])

    async def _new_context(self, cookie: str) -> None:
        # Any tabs that existed under the old context are no longer valid —
        # close them; callers will lazily re-open a fresh tab per session_id
        # the next time that session sends a message.
        for session_id in list(self._pages.keys()):
            try:
                await self._pages[session_id].close()
            except Exception:
                pass
        self._pages.clear()
        self._page_model.clear()
        self._page_thinking.clear()

        if self._context is not None:
            try:
                await self._context.close()
            except Exception:
                pass

        self._context = await self._browser.new_context(user_agent=GEMINI_USER_AGENT)
        cookie_pairs = parse_cookies(cookie)
        await self._context.add_cookies(
            [
                {
                    "name": pair["name"],
                    "value": pair["value"],
                    "domain": ".google.com",
                    "path": "/",
                    "secure": True,
                }
                for pair in cookie_pairs
            ]
        )

    async def _rotate_cookie(self) -> bool:
        if self._cookie_index + 1 >= len(self._cookies):
            return False
        self._cookie_index += 1
        await self._new_context(self._cookies[self._cookie_index])
        return True

    async def shutdown(self) -> None:
        for page in list(self._pages.values()):
            try:
                await page.close()
            except Exception:
                pass
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
        self._playwright = None
        self._browser = None
        self._context = None

    # ── per-session tabs ───────────────────────────────────────────────

    async def _get_or_create_page(self, session_id: str):
        page = self._pages.get(session_id)
        if page is not None and not page.is_closed():
            return page

        page = await self._context.new_page()
        await page.goto(GEMINI_URL, wait_until="networkidle", timeout=180000)
        await self._ensure_workspace_ready(page)

        self._pages[session_id] = page
        self._page_model[session_id] = await self._detect_current_model(page)
        self._page_thinking[session_id] = None
        return page

    async def close_session(self, session_id: str) -> bool:
        page = self._pages.pop(session_id, None)
        self._page_model.pop(session_id, None)
        self._page_thinking.pop(session_id, None)
        if page is not None:
            try:
                await page.close()
            except Exception:
                pass
            return True
        return False

    def list_sessions(self) -> list[str]:
        return list(self._pages.keys())

    # ── workspace readiness / resilient reload loop ────────────────────

    async def _ensure_workspace_ready(self, page, attempts: int = 3) -> None:
        """
        Confirms the Gemini workspace has *truly* finished loading: not
        authenticated-redirected, chat input present, and input box empty
        (no leftover debris from a previous failed attempt). Reloads and
        retries up to `attempts` times before giving up.
        """
        last_err: Optional[Exception] = None
        for attempt in range(1, attempts + 1):
            try:
                try:
                    await page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass
                await page.wait_for_timeout(1500)

                current_url = page.url
                if "accounts.google.com" in current_url or "consent" in current_url:
                    raise RuntimeError(
                        f"Not authenticated — Gemini redirected to {current_url}. "
                        "This cookie is likely missing, expired, or invalid."
                    )

                await page.wait_for_selector(CHAT_INPUT_SELECTOR, timeout=25000)

                loc = page.locator(CHAT_INPUT_SELECTOR).first
                leftover = (await loc.inner_text(timeout=2000)).strip()
                if leftover:
                    raise RuntimeError("input box has leftover content on load")

                return  # truly ready
            except Exception as e:
                last_err = e
                print(
                    f"[gemini_web] workspace not ready (attempt {attempt}/{attempts}): {e}",
                    file=sys.stderr,
                )
                if self._debug_dir:
                    await self._dump_debug(page, f"workspace_not_ready_attempt{attempt}")
                if attempt < attempts:
                    try:
                        await page.reload(wait_until="domcontentloaded", timeout=30000)
                    except Exception:
                        pass
                    await asyncio.sleep(1.0)

        raise RuntimeError(
            f"Gemini workspace did not fully load after {attempts} attempts: {last_err}"
        )

    async def _ensure_clean_input(self, page) -> None:
        """Make sure the chat input is empty before typing a new prompt."""
        try:
            loc = page.locator(CHAT_INPUT_SELECTOR).first
            current = (await loc.inner_text(timeout=2000)).strip()
        except Exception:
            current = ""
        if not current:
            return

        # Try a quick manual clear first (cheaper than a full reload).
        try:
            await loc.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Delete")
            await page.wait_for_timeout(200)
            current = (await loc.inner_text(timeout=1000)).strip()
        except Exception:
            pass

        if current:
            print(
                "[gemini_web] input box still has leftover text after clearing; "
                "forcing a full workspace reload",
                file=sys.stderr,
            )
            await self._ensure_workspace_ready(page)

    # ── UI interaction ─────────────────────────────────────────────────

    async def _click_first_match(self, page, selectors: list[str], timeout: int = 4000) -> bool:
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                await locator.click(timeout=timeout)
                return True
            except Exception:
                continue
        return False

    async def _element_visible(self, page, selectors: list[str]) -> bool:
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if await loc.is_visible():
                    return True
            except Exception:
                continue
        return False

    async def _detect_current_model(self, page) -> Optional[str]:
        try:
            btn = page.locator(MODEL_SWITCHER_BUTTON_SELECTORS[0]).first
            aria_label = await btn.get_attribute("aria-label", timeout=3000)
        except Exception:
            return None
        if not aria_label:
            return None
        lowered = aria_label.lower()

        for downgrade_label in DOWNGRADE_LABELS:
            if downgrade_label in lowered:
                return "gemini-lite"

        for model_id, labels in MODEL_UI_LABELS.items():
            for label in labels:
                if label.lower() in lowered:
                    return model_id
        return None

    async def _check_model_active(
        self, session_id: str, page, desired_model: Optional[str]
    ) -> None:
        """
        Strict active-model check: re-reads the mode picker and confirms it
        actually reflects `desired_model`. Raises if the account has been
        silently downgraded (e.g. to Gemini Lite from a rate/usage limit) or
        otherwise doesn't match — the caller (send()) treats any exception
        here as grounds to rotate to the next cookie.
        """
        if not desired_model:
            return
        detected = await self._detect_current_model(page)
        if detected == "gemini-lite":
            raise RuntimeError(
                f"Account appears downgraded to Gemini Lite (expected {desired_model}) — "
                "likely hit a rate/usage limit."
            )
        if detected and detected != desired_model:
            raise RuntimeError(
                f"Active model mismatch: expected {desired_model}, detected {detected}."
            )
        if detected:
            self._page_model[session_id] = detected

    async def _ensure_model(self, session_id: str, page, model: Optional[str]) -> None:
        if not model or model == self._page_model.get(session_id):
            return
        labels = MODEL_UI_LABELS.get(model, [model])
        try:
            opened = await self._click_first_match(page, MODEL_SWITCHER_BUTTON_SELECTORS)
            if not opened:
                raise RuntimeError("Could not find the model switcher button")
            await page.wait_for_timeout(500)
            picked = False
            for label in labels:
                try:
                    await page.get_by_text(label, exact=False).first.click(timeout=3000)
                    picked = True
                    break
                except Exception:
                    continue
            if not picked:
                raise RuntimeError(f"Could not find a menu item matching {labels!r}")
            await page.wait_for_timeout(300)
            confirmed = await self._detect_current_model(page)
            self._page_model[session_id] = confirmed or model
        except Exception as e:
            print(
                f"[gemini_web] WARNING: could not switch model to {model!r} ({e}). "
                "Continuing with whatever model is currently active. Inspect the "
                "page and update MODEL_SWITCHER_BUTTON_SELECTORS / MODEL_UI_LABELS.",
                file=sys.stderr,
            )
            if self._debug_dir:
                await self._dump_debug(page, "model_switch_failed")

    async def _ensure_thinking(self, session_id: str, page, extended_thinking: Optional[bool]) -> None:
        if extended_thinking is None or extended_thinking == self._page_thinking.get(session_id):
            return
        try:
            toggled = await self._click_first_match(page, THINKING_TOGGLE_SELECTORS)
            if not toggled:
                raise RuntimeError("Could not find the extended-thinking toggle")
            self._page_thinking[session_id] = extended_thinking
        except Exception as e:
            print(
                f"[gemini_web] WARNING: could not set extended thinking to "
                f"{extended_thinking!r} ({e}). Inspect the page and update "
                "THINKING_TOGGLE_SELECTORS.",
                file=sys.stderr,
            )
            if self._debug_dir:
                await self._dump_debug(page, "thinking_toggle_failed")

    async def _wait_send_button_ready(self, page, timeout: float = 8.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            for selector in SEND_BUTTON_SELECTORS:
                try:
                    loc = page.locator(selector).first
                    if not await loc.is_visible():
                        continue
                    disabled = await loc.get_attribute("disabled")
                    aria_disabled = await loc.get_attribute("aria-disabled")
                    if disabled is None and aria_disabled not in ("true", "True"):
                        return True
                except Exception:
                    continue
            await asyncio.sleep(0.3)
        return False

    async def _prompt_bounced_back(self, page, original_prompt: str) -> bool:
        """
        Detects the classic Gemini-UI error signal: the prompt we just sent
        reappears in the (supposedly empty, mid-generation) input box.
        """
        try:
            loc = page.locator(CHAT_INPUT_SELECTOR).first
            current_text = (await loc.inner_text(timeout=1000)).strip()
        except Exception:
            return False
        if not current_text:
            return False
        probe_len = min(len(original_prompt), 40)
        if probe_len == 0:
            return False
        return current_text[:probe_len] == original_prompt[:probe_len]

    async def _wait_for_generation_complete(
        self,
        page,
        prompt: str,
        *,
        overall_timeout: float = 180000.0,
        poll_interval: float = 2.0,
    ) -> None:
        """
        UI-driven completion wait, instead of racing a fixed network
        timeout: waits for the "Stop generating" control to appear (real
        generation started), then polls until it (and any typing indicator)
        disappears — so long code responses aren't cut off early. Also
        checks every poll for the prompt bouncing back into the input box,
        which signals a UI-level error.
        """
        start = time.time()

        appear_deadline = start + 15
        appeared = False
        while time.time() < appear_deadline:
            if await self._element_visible(page, STOP_GENERATING_BUTTON_SELECTORS):
                appeared = True
                break
            await asyncio.sleep(0.5)

        if not appeared:
            # Very short/instant reply — give the UI a moment to settle.
            await asyncio.sleep(1.5)
            return

        while time.time() - start < overall_timeout:
            if await self._prompt_bounced_back(page, prompt):
                raise RuntimeError(
                    "Prompt text bounced back into the input box — Gemini UI likely hit an error"
                )
            still_generating = await self._element_visible(
                page, STOP_GENERATING_BUTTON_SELECTORS
            ) or await self._element_visible(page, TYPING_INDICATOR_SELECTORS)
            if not still_generating:
                return
            await asyncio.sleep(poll_interval)

        raise RuntimeError(f"Generation did not finish within {overall_timeout:.0f}s")

    async def _send_once(self, page, prompt: str) -> str:
        # Each StreamGenerate response is generally a full snapshot, not a
        # delta — keep only the latest non-empty parse as the best-known text.
        captured = {"text": ""}

        async def _capture(resp) -> None:
            if "StreamGenerate" not in resp.url:
                return
            try:
                raw = await resp.text()
                parsed = parse_stream_response(raw)
                if parsed:
                    captured["text"] = parsed
            except Exception:
                pass

        def handler(resp) -> None:
            asyncio.ensure_future(_capture(resp))

        page.on("response", handler)
        try:
            max_send_attempts = 2
            sent = False
            for send_attempt in range(1, max_send_attempts + 1):
                await self._ensure_clean_input(page)
                input_el = await page.wait_for_selector(CHAT_INPUT_SELECTOR, timeout=15000)
                await input_el.click()
                await input_el.fill(prompt)
                await page.wait_for_timeout(200)

                if not await self._wait_send_button_ready(page):
                    print(
                        f"[gemini_web] send button not active after typing "
                        f"(attempt {send_attempt}/{max_send_attempts}); "
                        "reloading workspace and retrying",
                        file=sys.stderr,
                    )
                    if self._debug_dir:
                        await self._dump_debug(page, "send_button_not_ready")
                    await self._ensure_workspace_ready(page)
                    continue

                await page.keyboard.press("Enter")
                sent = True
                break

            if not sent:
                raise RuntimeError("Send button never became active after multiple reload attempts")

            await self._wait_for_generation_complete(page, prompt)
        finally:
            page.remove_listener("response", handler)

        text = captured["text"]
        if not text and self._debug_dir:
            await self._dump_debug(page, "empty_response")
        return text

    async def _dump_debug(self, page, tag: str) -> None:
        if not self._debug_dir:
            return
        os.makedirs(self._debug_dir, exist_ok=True)
        stamp = int(time.time())
        try:
            await page.screenshot(path=os.path.join(self._debug_dir, f"{tag}_{stamp}.png"))
        except Exception:
            pass
        try:
            html = await page.content()
            with open(os.path.join(self._debug_dir, f"{tag}_{stamp}.html"), "w") as f:
                f.write(html)
        except Exception:
            pass
        try:
            with open(os.path.join(self._debug_dir, f"{tag}_{stamp}_url.txt"), "w") as f:
                f.write(page.url)
        except Exception:
            pass
        print(f"[gemini_web] wrote debug artifacts ({tag}_{stamp}.*) to {self._debug_dir}", file=sys.stderr)

    # ── public API ──────────────────────────────────────────────────────

    async def send(
        self,
        session_id: str,
        prompt: str,
        *,
        model: Optional[str] = None,
        extended_thinking: Optional[bool] = None,
    ) -> str:
        """
        Send one message on this session's tab (creating the tab if this is
        a new session_id). Rotates to the next cookie and retries if the
        active account looks rate-limited, downgraded, or otherwise broken.
        """
        async with self._lock:
            await self.ensure_browser()

            last_error: Optional[Exception] = None
            remaining_accounts = len(self._cookies) - self._cookie_index

            for _ in range(max(1, remaining_accounts)):
                try:
                    page = await self._get_or_create_page(session_id)
                    target_model = model or self._page_model.get(session_id)

                    await page.wait_for_selector(CHAT_INPUT_SELECTOR, timeout=30000)

                    await self._ensure_model(session_id, page, model)
                    await self._check_model_active(session_id, page, target_model)

                    text = await self._send_once(page, prompt)

                    if not text or _looks_rate_limited(text):
                        raise RuntimeError(
                            f"empty or rate-limited response from cookie #{self._cookie_index + 1}"
                        )
                    return text

                except Exception as e:
                    last_error = e
                    print(
                        f"[gemini_web] cookie #{self._cookie_index + 1} failed ({e}); "
                        "rotating to next cookie if available...",
                        file=sys.stderr,
                    )
                    rotated = await self._rotate_cookie()
                    if not rotated:
                        break

            raise last_error or RuntimeError("All cookies exhausted with no response")


# ─── Daemon: Unix-socket JSON-line server wrapping GeminiWebManager ────────

async def _handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, manager: GeminiWebManager) -> None:
    try:
        raw = await reader.readline()
        if not raw:
            return
        try:
            req = json.loads(raw.decode())
        except json.JSONDecodeError:
            writer.write((json.dumps({"ok": False, "error": "invalid JSON request"}) + "\n").encode())
            await writer.drain()
            return

        cmd = req.get("cmd")

        if cmd == "ping":
            resp: dict[str, Any] = {"ok": True, "pong": True, "sessions": manager.list_sessions()}

        elif cmd == "send":
            session_id = str(req.get("session_id") or "default")
            prompt = req.get("prompt", "")
            model = req.get("model")
            extended_thinking = req.get("extended_thinking")
            if not prompt:
                resp = {"ok": False, "error": "prompt is required"}
            else:
                try:
                    text = await manager.send(
                        session_id, prompt, model=model, extended_thinking=extended_thinking
                    )
                    resp = {"ok": True, "session_id": session_id, "model": model, "text": text}
                except Exception as e:
                    resp = {"ok": False, "session_id": session_id, "error": str(e)}

        elif cmd == "close_session":
            session_id = str(req.get("session_id") or "default")
            closed = await manager.close_session(session_id)
            resp = {"ok": True, "session_id": session_id, "closed": closed}

        elif cmd == "shutdown":
            writer.write((json.dumps({"ok": True, "shutting_down": True}) + "\n").encode())
            await writer.drain()
            writer.close()
            asyncio.get_event_loop().create_task(_shutdown_daemon(manager))
            return

        else:
            resp = {"ok": False, "error": f"unknown cmd {cmd!r}"}

        writer.write((json.dumps(resp) + "\n").encode())
        await writer.drain()
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def _shutdown_daemon(manager: GeminiWebManager) -> None:
    await manager.shutdown()
    for path in (SOCK_PATH, PID_PATH):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
    asyncio.get_event_loop().stop()


async def run_daemon(cookies: list[str], headless: bool, debug_dir: Optional[str]) -> None:
    manager = GeminiWebManager(cookies, headless=headless, debug_dir=debug_dir)

    # Pre-warm the browser now, so the first real "send" doesn't pay the
    # launch cost — the CLI client is already waiting on us to become ready.
    await manager.ensure_browser()

    if os.path.exists(SOCK_PATH):
        os.remove(SOCK_PATH)
    server = await asyncio.start_unix_server(
        lambda r, w: _handle_client(r, w, manager),
        path=SOCK_PATH,
        limit=SOCKET_LINE_LIMIT,
    )
    with open(PID_PATH, "w") as f:
        f.write(str(os.getpid()))

    loop = asyncio.get_event_loop()
    for sig in (signal_module.SIGTERM, signal_module.SIGINT):
        loop.add_signal_handler(
            sig, lambda: asyncio.ensure_future(_shutdown_daemon(manager))
        )

    print(f"[gemini_web daemon] ready — listening on {SOCK_PATH} (pid {os.getpid()})", file=sys.stderr)
    async with server:
        await server.serve_forever()


# ─── Client: one-shot request to the daemon, spawning it if needed ────────

async def _send_request(req: dict, timeout: float = 120.0) -> dict:
    reader, writer = await asyncio.open_unix_connection(SOCK_PATH, limit=SOCKET_LINE_LIMIT)
    try:
        writer.write((json.dumps(req) + "\n").encode())
        await writer.drain()
        raw = await asyncio.wait_for(reader.readline(), timeout=timeout)
        return json.loads(raw.decode())
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def _daemon_alive() -> bool:
    if not os.path.exists(SOCK_PATH):
        return False
    try:
        resp = await _send_request({"cmd": "ping"}, timeout=3)
        return resp.get("ok") is True
    except Exception:
        return False


def _spawn_daemon(headless: bool, debug_dir: Optional[str]) -> None:
    args = [sys.executable, os.path.abspath(__file__), "--daemon"]
    if not headless:
        args.append("--headed")
    if debug_dir:
        args += ["--debug-dir", debug_dir]
    log_f = open(LOG_PATH, "a")
    subprocess.Popen(
        args,
        stdout=log_f,
        stderr=log_f,
        stdin=subprocess.DEVNULL,
        start_new_session=True,  # detach from this terminal — keeps running after we exit
    )


async def _ensure_daemon_running(headless: bool, debug_dir: Optional[str], startup_timeout: float = 90.0) -> None:
    if await _daemon_alive():
        return
    print(
        "[gemini_web] no daemon running — starting one in the background "
        "(first run loads the browser, can take a bit)...",
        file=sys.stderr,
    )
    _spawn_daemon(headless, debug_dir)
    start = time.time()
    while time.time() - start < startup_timeout:
        if await _daemon_alive():
            print("[gemini_web] daemon ready.", file=sys.stderr)
            return
        await asyncio.sleep(1)
    raise RuntimeError(
        f"Daemon did not become ready within {startup_timeout}s — check {LOG_PATH} for errors."
    )


# ─── CLI entrypoint ─────────────────────────────────────────────────────────

async def _tool_main() -> None:
    parser = argparse.ArgumentParser(
        description="Gemini Web tool — one-shot, non-interactive, backed by a persistent daemon."
    )
    parser.add_argument("prompt", nargs="*", help="Prompt text to send")
    parser.add_argument(
        "--session",
        default=os.environ.get("HERMES_SESSION_ID", "default"),
        help="Session id. A new id opens a new Gemini tab/conversation; reusing one continues it.",
    )
    parser.add_argument("--model", choices=list(MODEL_ALIASES.keys()), default="flash")
    parser.add_argument("--thinking", action="store_true", help="Enable extended thinking")
    parser.add_argument("--close-session", action="store_true", help="Close this session's tab and exit")
    parser.add_argument("--shutdown", action="store_true", help="Stop the whole daemon and exit")
    parser.add_argument("--headed", action="store_true", help="(only affects daemon startup) show the browser window")
    parser.add_argument("--debug-dir", default=None)
    args = parser.parse_args()

    if args.shutdown:
        try:
            resp = await _send_request({"cmd": "shutdown"}, timeout=10)
        except Exception as e:
            resp = {"ok": False, "error": str(e)}
        print(json.dumps(resp))
        sys.exit(0 if resp.get("ok") else 1)

    if args.close_session:
        await _ensure_daemon_running(not args.headed, args.debug_dir)
        resp = await _send_request({"cmd": "close_session", "session_id": args.session}, timeout=10)
        print(json.dumps(resp))
        sys.exit(0 if resp.get("ok") else 1)

    prompt = " ".join(args.prompt).strip()
    if not prompt:
        print(json.dumps({"ok": False, "error": "no prompt provided"}))
        sys.exit(1)

    if not _cookies_from_env():
        print(json.dumps({"ok": False, "error": "No Gemini cookies found in environment. See _cookies_from_env()."}))
        sys.exit(1)

    try:
        await _ensure_daemon_running(not args.headed, args.debug_dir)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)

    model = MODEL_ALIASES[args.model]
    try:
        resp = await _send_request(
            {
                "cmd": "send",
                "session_id": args.session,
                "prompt": prompt,
                "model": model,
                "extended_thinking": args.thinking,
            },
            timeout=930,  # a bit above the manager's own 900s generation ceiling
        )
    except Exception as e:
        resp = {"ok": False, "error": str(e)}

    print(json.dumps(resp))
    sys.exit(0 if resp.get("ok") else 1)


def _daemon_entrypoint() -> None:
    daemon_parser = argparse.ArgumentParser()
    daemon_parser.add_argument("--daemon", action="store_true")
    daemon_parser.add_argument("--headed", action="store_true")
    daemon_parser.add_argument("--debug-dir", default=None)
    dargs = daemon_parser.parse_args()

    cookies = _cookies_from_env()
    if not cookies:
        print(
            "No cookies found in environment (GEMINI_COOKIES / GEMINI_COOKIE_n / "
            "GEMINI_SECURE_1PSID).",
            file=sys.stderr,
        )
        sys.exit(1)

    asyncio.run(run_daemon(cookies, headless=not dargs.headed, debug_dir=dargs.debug_dir))


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        _daemon_entrypoint()
    else:
        asyncio.run(_tool_main())