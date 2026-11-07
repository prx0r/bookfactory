# The book line — purpose-first theses

Nine thesis objects live here (eight reference/primer/parable + **Learn Sanskrit
with Abhinavagupta**). They are not lanes yet: `check.py` ignores
`specs/`, and each becomes a lane with `factory.py new-book --thesis
specs/<id>.thesis.json` once the purpose and cut are owner-ruled. Theses carry a
`purpose` block (kind, impact, reader, realisation, non_goals); **structure is
derived from purpose**, so if the purpose is not sharp the book is not ready.

**2026-11-07 — Learn Sanskrit with Abhinavagupta.** Gold standard verbatim in
`learn-sanskrit.thesis.md` (ten layers, seven editorial rules). Curriculum cut
verbatim in `learn-sanskrit-curriculum.md` (**10 lessons, 108pp**, five stages,
few rule boxes). Machine twin: `learn-sanskrit.thesis.json` + template
`lesson-book`. Textbook **quotes** any verse with attribution; a reference
volume remains the verse's **home**.

## The ruling (2026-11-06)

**Reference works, not our instructions.** The line is a cheap, sharp reference
shelf: Sanskrit decoded, translation exact, interpretation minimal. We do not
add practices, programmes, exercises or agent-written connective prose. Our
input is editorial (order, placement, one-glance apparatus), not doctrinal.

**Purpose = impact.** Every book must do something to the reader in one
sitting. For reference volumes the impact is direct encounter: the reader meets
the text itself, whole, and the text does the work. For the primer the impact is
the recognition itself. For parables it is the turn of a story. If a proposed
element does not serve the stated realisation, it is cut.

**Condensation is the discipline.** Minimal apparatus, maximal sharpness. One
gloss line where a paragraph would be; one page of orientation where an essay
would be; the complete text where a selection would be. A reference that
selects is a different book.

## The shelf

| Book | Template | Kind | Entries | Density | Pages |
|---|---|---|---|---|---|
| The Poetry of Abhinavagupta | treatise | reference | **172** (complete, 9 hymns) | 2–3/pp | 108 |
| Recognition: A Manual | prayer | primer | 36 | spread | 108 |
| The Seventy-Five Aphorisms of Śiva | aphorism | reference | **75** (complete) | 1/pp | 108 |
| Proofs of the Self | treatise | reference | **106** (complete) | 2–3/pp | 108 |
| Parables of Recognition (Vol. I) | parable | parable | 36 original | spread | 108 |
| Tantrasāra: The Essence | prayer | reference | 36 condensed | spread | 108 |
| The Vijñānabhairava: A Reference | treatise | reference | **162** (complete) | 3/pp | 108 |
| The Goddess’s Thirty-Six | prayer | reference | **36** (complete) | spread | 108 |
| **Learn Sanskrit with Abhinavagupta Vol. I** | **lesson** | **primer** | **10** (5 stages × 2) | 10-layer lesson | **108** |

Complete editions changed on 2026-11-06:

- **VBT: 36 curated doors → all 162**, nine blocks of eighteen in the text’s
  own order, decoded + translated, no practice programme. This was the user’s
  ruling: “a cheap reference of the Sanskrit decoded and sharp
  translation/interpretations.”
- **Poetry: 36 selected verses → all 172**, the nine hymns whole, 2–3 verses
  per page, one orientation page per hymn. No selection means no curation
  decisions and no deep-volume residue; expanded annotated editions are later
  *editions*, not new volumes.

Counts verified against `translation-work/REGISTRY.json` on 2026-11-06:
172 hymns / 75 sutras / 106 siddhi verses (27+56+23) / 36 Parātrīśikā /
162 VBT / 25 Spanda. All gold.

## Decisions

1. **Parables — trilogy, but ship one.** *The Knot / The Door / The Ordinary*,
   36 each (108 total), Vol. I in this shelf. Architecture supports three; the
   law forbids padding to reach three. The long pole is 36 owner-approved
   drawings per volume.
2. **Proofs of the Self — one 108-page reference with all 106 verses.** The
   terse reference is the book; a 300-page expanded critical edition is a later
   edition of the same book, not a second volume.
3. **Tantrasāra condensed — caveat.** a06, a08 and a13 are still legacy;
   nothing is placed from them until they are transformed to gold. The thesis
   excludes them rather than smoothing over the gap.
4. **Poetry and VBT are complete references.** No further verse is reserved for
   a "deep volume"; an expanded edition is a new printing of the same text.

## Purpose-first derivation rule

For each book, in order:

1. Write the impact in one sentence (what happens to the reader in one sitting).
2. Name the reader precisely, and the realisation the book must produce.
3. List non_goals — the tempting additions that would dilute it.
4. Only then choose the template and the structure; every section must be
   justified by the realisation, not by source symmetry.
5. Cut anything that does not serve the impact, including our own commentary.

## Verse assignment ledger (one verse, one book)

Complete references now consume their texts whole, so the ledger is simple:

| Source | Consumed by | Status |
|---|---|---|
| 172 hymns (9) | Poetry — all | assigned |
| Śiva Sūtra 75 | Aphorisms — all | assigned |
| Three siddhis 106 (27+56+23) | Proofs — all | assigned |
| Parātrīśikā 36 | Goddess’s Thirty-Six — all | assigned |
| Vijñānabhairava 162 | VBT Reference — all | assigned |
| Tantrasāra (gold āhnikas) | Essence 36 | partially assigned |
| Spanda + remaining Tantrasāra | Manual 36 | to be assigned at lane start |

The Manual is the only book that must draw from leftovers: Spanda plus
Tantrasāra gold verses not used by *The Essence*, plus transformed Tantrāloka
material later. The global gate check must reject any overlap at lane time.

## Gate and engine work before the first new lane

1. **Template-aware content gate** (`provenance: original` branch) for Parables
   — shape checks only, no verse-id requirements.
2. **Engine layouts**: `aphorism` (one entry per page + gloss), `treatise`
   (continuous verse flow + chapter openers), `parable` (story + facing art).
3. **`new_book` variable counts** — Poetry’s hymn counts and VBT’s 9×18 blocks
   come from `structure.sections_plan[].count`, not a fixed number.
4. **Global one-verse-one-book check** — scan assigned verse ids across lanes
   (and `specs/`) before a lane can claim a source.

## Promotion recipe (unchanged)

```bash
cd /home/box/repos/bookfactory
/tmp/opencode/pubvenv/bin/python3 factory.py new-book <slug> --thesis specs/<slug>.thesis.json
# then populate content, run check.py, build, preflight
```

## Page math (cream, 6×9, target 108)

- `reference/treatise`: front 10 + chapter essays + verses at 2–3/pp + glossary
  + index + end 4 → 108.
- `reference/aphorism`: 10 + 75 + 8 glossary + 6 index + 4 end + 5 pad = 108.
- `primer/prayer`: 10 + 36×spread (72) + 8 + 6 + 4 = 100 → 108.
- `parable`: 10 + 36×spread (72) + 8 + 6 + 4 = 100 → 108.

## Open dependencies

- Rights: GRETIL CC BY-NC-SA unresolved; PD-scan re-transcription recommended.
- Owner signoffs: Parables text + 36 drawings; VBT/Poetry complete-text count
  confirmed against the gold corpus.
- Two GitHub PATs still to rotate.
