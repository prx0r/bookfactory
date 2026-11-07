# EXPLAINER — house formula for every facing-page guide (canonical)

**Adopted:** 2026-11-07 from `prints/practical-prayers/editorial/00_explainer_standard.md`
(PP editorial handoff). **Wins over** older “brief / what / how / sign + feel”
prose habits wherever they conflict. Field *names* in `entries.json` stay
stable for the gate; this doc defines **what goes in them**.

## Reader-facing order (always)

1. **THE TEXT** — full Sanskrit (Deva + IAST) + exact work/verse + attribution.
   Pocket line only if contiguous, intelligible, witnessed — label **EXTRACT**.
2. **IN ONE SENTENCE** → field **`brief`** — the literal proposition/petition.
   No ecstatic claims.
3. **WHEN** → start of **`howto`** — one concrete moment of the day.
4. **THE ACT** → **`howto`** — one 5–30s safe action. Label:
   *Textual instruction* | *Recorded traditional practice* | *Suggested modern adaptation*.
5. **THE TURN** → field **`logic`** — one recognitional insight from syntax +
   Trika, as contemplation, not a guaranteed event.
6. **RETURN** → end of **`howto`** (and **`sign`** if used) — ordinary next
   action. **No** required warmth, bliss, energy, breath, or “sign of success.”
7. **SOURCE NOTE** → `source` / `source_ref` / `source_path` + contested
   readings noted in copy when needed.

## Field map (gate anatomy unchanged)

| Field | Carries |
|-------|---------|
| `brief` | IN ONE SENTENCE |
| `logic` | THE TURN (recognitional insight) |
| `howto` | **When:** … **Practice/Act:** … **Return:** … (labels required) |
| `sign` | RETURN only — ordinary integration; never a somatic test |
| `feel` | optional; if present, a contemplative cue, **not** a success metric |

## Speech acts (never blur)

- **Mantra** — traditional formula; no invented bīja; no edited text as canonical.
- **Prayer** — petition; keep grammar legible.
- **Hymn/description** — praise; do not mistranslate into a request.
- **Philosophical / practice verse** — assertion or instruction; contemplative use ≠ mantra.

## Lengths

- **Pocket** 2–10 words (EXTRACT if cut from a larger verse)
- **Verse** 16–32 syllables — full is canonical; teach in chunks
- **Extended** appendix / long recitation — never disguised as an instant pocket line

## Non-negotiable

**Literal Sanskrit → commentarial Trika reading → modern devotional suggestion**
are three separate claims. Never cite modern coaching as historical ritual.
When wording is disputed: **transparent hold > pretty error.**

## Forbidden copy (examples)

- “On bite three your chest warms; the goddess has received the offering.”
- “If the skin boundary does not thin, you have failed…”
- “The mantra will remove illness/anxiety.”
- “The verse instructs you to put your hand on your throat…” (unless the source says so)
- “All prayers of this kind are by Abhinavagupta.”

## Tonal model

Warm, lucid, reverent, concrete — e.g. *“The senses bring their own flowers.
Taste this bite without fighting it.”*

## Source law still applies

Guide prose must be **owner-approved editorial content** (this formula +
approved manuscript), not silent agent invention. Sanskrit/witness still
fail-closed per `AGENTS.md` / `07_publication_gate.md`.
