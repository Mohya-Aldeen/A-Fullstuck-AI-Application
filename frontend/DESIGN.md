# Document Copilot — design system

Concept: **"The Ledger."** A monochrome research instrument. The AI answer is typeset like a
research note; citations are treated like footnotes in a printed dossier. Evidence is a
first-class, always-traceable path: **Answer → `[n]` mark → evidence ledger row → source panel.**

This is a serious research workstation that happens to have an AI assistant — not a chatbot.

## Principles

- Evidence is the product. Every factual claim is traceable in one click.
- Typography and hairline rules carry hierarchy — not cards, shadows, or color.
- One column, left-aligned transcript. No chat bubbles, no left/right alignment games.
- Spend boldness in one place: the citation apparatus and the editorial answer type.
- Density with air. Information-dense without clutter.

## Color (tokens in `src/index.css`)

Monochrome only. There is **no chromatic accent** — contrast is the accent (ink for
primary/active). Red is reserved strictly for genuine errors.

| Role | Light (paper) | Meaning |
| --- | --- | --- |
| `--background` | `oklch(0.988)` | paper |
| `--foreground` | `oklch(0.205)` | ink (body, primary) |
| `--muted-foreground` | `oklch(0.505)` | graphite (metadata, secondary) |
| `--border` / `--rule` | `oklch(0.908)` | hairline |
| `--rule-strong` | `oklch(0.84)` | emphasized divider |
| `--primary` | `oklch(0.22)` | primary action = ink |
| `--destructive` | red | errors only |

Dark ("carbon") variant retains the same relationships. shadcn token names are preserved so
primitives keep working.

## Typography

Two families, clearly distinct:

- **Newsreader** (editorial serif) — wordmark, hero, answer/section headings. Used as an
  active design element, never as filler.
- **IBM Plex Sans** — UI, body, long-form answer text. Institutional and legible.

Rules:

- Financial figures, tickers, years, pages use `.tabular` (tabular + lining numerals) on the
  sans — numerical clarity without a monospace-label cliché.
- Answer measure ≤ ~68ch for long-form reading.
- Sentence case. Avoid all-caps tracked eyebrows and `A · B · C` middle-dot meta strings;
  metadata is rendered as structured fields or spaced spans.

Loaded via Google Fonts `<link>` in `index.html` (no npm dependency; avoids the 7-day
release-age gate).

## Space, radius, borders

- Radius is restrained: `--radius: 0.375rem`. Structural dividers use hairlines, not cards.
- Prefer a single 1px `--rule` to separate regions over boxes-with-shadows.
- Shadows are near-absent; used only for the mobile slide-over.

## Motion

Deliberate and few, all reduced-motion aware:

- Evidence panel slide-in (mobile drawer).
- One indeterminate retrieval bar (`.animate-scan`).
- Streaming caret; thread-switch fade.

No hover animation on every element.

## Layout

Three regions on desktop:

1. **Left rail** (`~300px`, quiet): wordmark + corpus tag, New research, client-side
   conversation search, threads grouped by recency, account footer. Drawer below `lg`.
2. **Center workspace** (focus): single left-aligned transcript at reading measure. Question
   blocks (left rule) → answer notes with inline `[n]` marks → evidence ledger. Composer pinned.
3. **Right evidence panel** (first-class): persistent column at `xl`, slide-over drawer below
   `xl`. Structured metadata + readable excerpt + SEC link.

## Citation apparatus

- Inline `[n]` marks in the answer are parsed and mapped to `citation_index`; clickable once
  citations load (after the turn persists). During streaming they render as quiet marks.
- The **evidence ledger** under an answer is a hairline-divided list (reference square,
  company, spaced metadata, excerpt preview) — not a row of pills.
- Selecting a mark or ledger row opens the **source panel** with the full excerpt.

## States designed

Loading skeletons, retrieval indicator, streaming, completed, insufficient-evidence (a calm
callout, not an error), grounding failure, network/backend errors, not-found, empty history,
long answer/excerpt, mobile drawers.

## Known backend gaps (designed around, not faked)

- No thread rename/delete endpoint → not offered in the UI.
- No thread-search endpoint → conversation search is client-side over loaded threads.
- No HTTP endpoint for a chunk's surrounding context (`read_surrounding_chunks` is agent-only)
  → the source panel shows excerpt + metadata + SEC link, without a fake "read in context."
