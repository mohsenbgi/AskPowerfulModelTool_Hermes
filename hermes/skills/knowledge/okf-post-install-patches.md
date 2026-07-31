# Post-Install Patches for the `okf` Skill

When the official `okf` skill is installed or updated via `hermes skill install okf`
(or equivalent), three customisations must be applied to align it with this project's
conventions. The upstream skill ships with different defaults — always patch after
(re)install.

---

## Patch 1 — Cross-links: absolute bundle-relative → relative paths

**Location:** `okf/okf/SKILL.md` / Conventions section

The upstream recommends absolute bundle-relative form (`/services/auth-api.md`).
This project uses **relative paths** from the current file (e.g. `member.md`,
`../data/event-system.md`).

### What to replace

```markdown
- **Cross-links:** standard markdown links; prefer absolute bundle-relative
  form (`/services/auth-api.md`). A link asserts a relationship; its *kind* lives
  in the surrounding prose, not the link.
```

### With

```markdown
- **Cross-links:** standard markdown links using **relative paths** from the
  current file (e.g., `member.md`, `../data/event-system.md`). Every concept
  file must have a `## Related Concepts` section (before `# Computation` or
  `# Citations`) listing all directly related concepts with relative links.
  A link asserts a relationship; its *kind* lives in the section heading and
  surrounding prose, not the link syntax.
- **Citation links:** source file references use relative paths from the concept
  file to the repo source (e.g., `../../../shared/src/.../File.kt`). Never use
  `file:///` absolute paths.
```

---

## Patch 2 — Produce step: add Related Concepts instruction

**Location:** `okf/okf/SKILL.md` / produce mode step 4

### What to replace

```markdown
4. Write each concept from [templates/concept.md](templates/concept.md): set a
   descriptive `type`, fill recommended fields, record `generated` and the
   `sources` you actually read, cross-link related concepts.
```

### With

```markdown
4. Write each concept from [templates/concept.md](templates/concept.md): set a
   descriptive `type`, fill recommended fields, record `generated` and the
   `sources` you actually read. Add a `## Related Concepts` section with
   relative links to every directly related concept, then cite source files
   under `# Citations` using relative paths.
```

---

## Patch 3 — Consume mode: Two-Pass Progressive Disclosure

**Location:** `okf/okf/SKILL.md` / consume section

### What to replace

The entire `### consume — use a bundle as context` section (upstream has
a flat numbered list).

### With

```markdown
### consume — use a bundle as context

#### Two-Pass Progressive Disclosure

Protect context — never read full concept bodies in a single bulk pass.

**Pass 1 — Discovery (header-only):**
1. Read the bundle-root `index.md` first to understand the structure.
2. Parse *only* the YAML frontmatter (the block between the `---` delimiters)
   of candidate `.md` files. Evaluate only `type`, `title`, and `description`.
3. Identify which specific concept files contain the information you need.

**Pass 2 — Deep Read (body-on-demand):**
1. Open only the targeted concept files identified in Pass 1.
2. Search for relevant section headings: `# Schema`, `# Examples`,
   `## Related Concepts`, `# Computation`, `# Citations`.
3. If a body links to another concept via `[Title](relative-path.md)`,
   evaluate its frontmatter first before reading its full body.

**Weigh what you read:** `status: draft`/`deprecated`, a `stale_after` already
past, or no `verified` entry all mean "check before relying on this". Treat
broken links as not-yet-written knowledge, not errors.

Need a number an `Attested Computation` covers? Run *its* computation with
values bound to the declared `parameters` — never write your own query.

If you learn something durable while working, switch to **maintain** and write
it back.
```

---

## Patch 4 — Template: add Related Concepts and Citations sections

**Location:** `okf/okf/templates/concept.md`

### What to replace

Everything after the `# Schema` table (lines below `|       |      |             |`).

### With

```markdown
|       |      |             |

## Related Concepts

- [Related Concept Title](../path/to/related.md) - what relationship exists
- [Another Concept](../path/to/another.md) - what relationship exists

# Citations

[^short-key]: <Human-readable label of the source>

[1] [Source title](<relative-path-to-source>)
```

---

## Quick reapply script

After an install/update, these can be applied together by running the
validate/visualize companion skills' parent directory patches, or manually
with the four find-and-replace blocks above.

Verify with:

```bash
uv run /home/mohsen/.hermes/skills/knowledge/okf/validate/scripts/okf_validate.py .okf/ --strict
```
