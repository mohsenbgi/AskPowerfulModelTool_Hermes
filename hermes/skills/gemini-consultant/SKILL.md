---
name: gemini-consultant
description: "Use when needing library versions, sample code, API usage, debugging help, or facing a complex multi-step task. Consult Gemini via ask_gemini before proceeding."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gemini, consultation, research, second-opinion, library-lookup]
    related_skills: [plan]
---

# Gemini Consultant

## Overview

A second AI opinion is available via the `ask_gemini` tool. Consult Gemini before starting work, or mid-task, when the situation calls for information that benefits from external lookup or a different model's perspective. Gemini often has fresh knowledge about library versions, API quirks, and idiomatic patterns.

The goal is partnership: Hermes leads the task, uses repo context (`read_file`, `search_files`, `terminal`), and calls Gemini for specific questions where a second model adds value.

## When to Use

**Before starting a complex task**, do a short Gemini consultation even if you think you know the answer — your training cutoff may be stale and Gemini may have fresher knowledge of library versions, API shapes, and current idioms. This is the default trigger, not a fallback.

Consult Gemini when ANY of these apply:

- **Before starting a complex task:** Get current state + idiom check up front so you don't build on a stale assumption. Cheap insurance.
- **Library / framework lookups:** Which version of a library is current? What's the latest API shape? Is feature X available in version Y?
- **Sample code / idioms:** How do you idiomatically do X in framework Y? A short example to anchor your implementation.
- **Debugging a blocker:** You hit an unfamiliar error, a platform-specific quirk, or a runtime crash you can't immediately explain.
- **Complex tasks:** Multi-step reasoning, architectural decisions, algorithm selection, or anything where a second opinion de-risks the approach.
- **Uncertainty about external state:** API rate limits, deprecation timelines, compatibility between versions, or anything that changes over time outside the repo.

## When NOT to Use

Skip the call when it would slow things down without adding value:

- Simple edits already scoped by repo context (patch a string, fix a typo, rename a symbol).
- Tasks where you already have the answer from files you just read.
- Pure repo-local operations (git, build, test, file I/O) that don't need external knowledge.
- Trivial yes/no checks better served by a quick `terminal` call.

## Model Selection

`ask_gemini` has a `model` parameter:

- **`model='flash'`** (default) — quick lookups: library versions, simple API questions, short code samples, fast fact checks. Use this for lightweight tasks.
- **`model='pro'`** — complex reasoning: architectural decisions, nuanced debugging, multi-constraint design problems, deep analysis. Use when the question needs careful reasoning over breadth.

Rule of thumb: start with `flash`. Upgrade to `pro` only when the question is genuinely complex or the flash answer feels shallow.

## Workflow

1. **Identify the question.** Be specific. "What's the current Kotlin coroutines version and how do I use Channel?" beats "coroutines help."
2. **Frame the query.** Give Gemini context: what you're trying to do, what language/framework, what you already tried or know. A well-framed question gets a much better answer.
3. **Call `ask_gemini`** with the appropriate `model`.
4. **Synthesize.** Don't blindly copy Gemini's answer. Cross-check it against your repo context (imports, existing patterns, `pyproject.toml` / `build.gradle.kts` / etc.) before applying.
5. **Cite it.** When you use Gemini's answer, mention it briefly in your summary so the user knows where the info came from.

## Consultation Loop (Complex Tasks)

For architecture decisions or multi-step problems, a single shot rarely settles it. Run the loop:

1. **Ask for options.** Send Gemini the context + goal + constraints and ask for 2-3 candidate approaches, not one. Request tradeoffs for each.
2. **Weigh against the repo.** Read through the options, discard any that conflict with repo constraints you can see (versions, existing patterns, module boundaries) or that you can rule out with a quick `terminal` / `read_file` check.
3. **Follow up with the tradeoffs.** Send Gemini a second query that names the surviving options + the repo-specific constraints you just confirmed, and ask which fits best and why. `model='pro'` for this round is usually right.
4. **Decide and cite.** Pick the approach that best fits the repo, note in your summary that Gemini was consulted and which option you chose and why.

**Second opinion on your plan, before implementing.** Once you've drafted an approach (especially after running `plan`), run the plan past Gemini as a sanity check: "Here's my plan: <…>. Repo constraints: <…>. What's wrong with this, what am I missing?" A wrong assumption caught here costs one call; the same bug caught after implementation costs a refactor. Use `model='pro'` for plan review.

Stop the loop early when: (a) only one candidate survived step 2, (b) Gemini's follow-up gave a clear best-fit with no red flags, or (c) you've done two follow-ups and the answer isn't sharpening. More rounds than that means the question is underspecified — go read repo files and come back with better constraints.

## Fallback: ask_powerful_model (CRUCIAL!!!!!!)

If `ask_gemini` fails (expired cookies, network error, rate limit), fall back to `ask_powerful_model` — it hits a different backend and often succeeds when Gemini doesn't. Use the same query framing; no need to rephrase.

## Common Pitfalls

1. **Calling Gemini for everything.** Easy repo-local tasks don't need a second opinion. Use it when it adds value, not reflexively.
2. **Asking vague questions.** "Help with Gradle" gets a generic answer. "How do I configure a KMP plugin in build.gradle.kts with Kotlin 2.4?" gets a useful one.
3. **Trusting a stale or mismatched answer.** Gemini's version numbers, API shapes, or suggested patterns may not match what's installed in the repo. Failure signals to check: (a) Gemini's version is older than what `build.gradle.kts` / `pyproject.toml` reports — trust the repo. (b) Gemini's API suggestion doesn't match the installed library major version — verify via a quick `terminal` call or doc lookup before applying.
4. **Using flash for hard problems.** If the question needs real reasoning, spring for `pro`. A shallow flash answer wastes both calls.
5. **Forgetting to synthesize.** The value is in merging Gemini's breadth with your repo-specific context. Don't skip the cross-check step.

## Verification Checklist

- [ ] Question is specific and well-framed (language, framework, goal, constraints)
- [ ] Chose the right model: `flash` for lookups, `pro` for complex reasoning
- [ ] Cross-checked Gemini's answer against repo context before applying
- [ ] Noted Gemini as the source when the answer informed your work
