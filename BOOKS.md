# BOOKS — how a book is defined, built, and shipped (canonical doc)

Everything in bookfactory hangs off one idea: **a book is a thesis with a
pipeline, not a folder of files.** This file documents the whole system —
template (genre) → thesis (this book) → decisions (every change justified) →
stages (content → structure → formatting → **build last**) → products
(print + audio). Read order after this: `FACTORY-SPEC.md` (product law),
`PIPELINE.md` (commands + current blockers).

---

## 1. The stack

```
templates/<genre>.json     the OVERALL thesis of a KIND of book (110pp ceiling,
        │                  entry anatomy, product stack, pipeline, genre rules)
        ▼ instantiates
projects/<book>/thesis.json    THIS book: claim (intro derives from it),
        │                      structure law (sections x entries = total),
        │                      inherited template rules + book-specific rules
        ▼ records every change in
projects/<book>/decisions.jsonl    append-only: action + target + justification
        │                          (>=40 chars, MUST cite a thesis clause)
        ▼ enforced by
check.py    the only gate. Stage-aware. Exit 0 = canonical.
        ▼ produces (in prints/<book>/ — in-repo, one repo for books)
bookkit HTML -> (LAST STAGE) Chrome PDF -> kdp_preflight -> ship pack
```

Supporting packs:
- `styles/<id>.json` — presentation only, never content. `canonical` is the
  house style both prayer books wear. Future: save your own style packs here
  and point `thesis.style` at them — anatomy/gates stay identical, only the
  look changes.
- `schemas/` — thesis, decision, template, style, asset, quote-handoff.
  Everything is schema-validated; validation failures fail closed.

## 2. The genre template (the "overall thesis of a prayer book")

`templates/prayer-book.json` — what ALL prayer books share:

| Field | Value |
|---|---|
| `constraints.max_pages` | **110** — the creative boundary (KDP flat $2.30 tier ends at 110pp). Overflow = new volume, never a fatter book. |
| `constraints.min_font_pt` | 7 (KDP floor) |
| `constraints.trim` | A5 148x210mm no-bleed |
| `pipeline` | `content → structure → formatting → build` (PDF always last) |
| `entry_anatomy` | required: brief, what (`what`\|`logic`), how (`how`\|`howto`), sign; optional: feel |
| `products` | paperback, postcard, social, **audiobook**, **chant** |
| `style_default` | `canonical` |
| `structure_defaults.entries_per_section` | 4 |
| `series_pattern` | One book = one thesis within the ceiling; overflow -> numbered volumes (`thesis.series`) |
| `inclusion` / `exclusion` | genre rules **inherited verbatim** by every member thesis — dropping one blocks the gate |

Members today: `practical-prayers`, `tantric-prayer`. More generate from it
(§6).

## 3. The thesis (`projects/<book>/thesis.json`)

The book's definition. Fields:

- `claim` (min 80 chars) — the argument. **The intro/front-matter derives
  from `claim` + `structure`;** prose that restates counts by hand is stale.
- `template` — genre it instantiates (must exist in `templates/`).
- `style` — style pack (must exist in `styles/`).
- `structure` — `sections`, `entries_per_section`, `total_entries` (the
  gate checks `sections x entries_per_section == total_entries`), and
  `sections_plan` (id + purpose per section — order is the book's order).
- `inclusion` / `exclusion` — template-inherited rules + book-specific ones.
  Each is a citable clause: decisions reference them by path (`exclusion/0`).
- `products` — must match the template's product set; per-product status/spec;
  `chant.coverage` names which kashaudio works / Swamiji archival / render
  queue feed the audio.
- `series` (optional) — `{name, volume}` when this is a numbered volume.

Current law (both books): **9 sections x 4 entries = 36 total, <= 110pp.**

## 4. The decision log (`projects/<book>/decisions.jsonl`)

One JSON line per construction decision — the audit trail that answers
"why is this in the book?":

```json
{"ts":"2026-11-06","action":"move-entry","target":"aghora",
 "from":"tantric-prayer/sangha","to":"tantric-prayer/bhayanaka",
 "justification":"its own howto says at any moment of fear — Bhayānaka's four
 are verses ABOUT fear, none is the operative practice",
 "thesis_ref":"inclusion/1","status":"live","decided_by":"owner"}
```

Rules (all fail-closed):
- `justification` **min 40 chars** — empty/thin why = no decision.
- `thesis_ref` must **resolve** into this book's thesis (e.g. `exclusion/0`,
  `structure`, `products/paperback/spec`). Unresolvable = refused at append
  time AND reported by the gate for pre-existing lines.
- actions: `add-section · remove-section · add-entry · remove-entry ·
  move-entry · retire-entry · replace-entry · declare-structure`.
- `status`: `live` or `superseded` (supersede, never edit history).

Write one with:

```bash
python3 factory.py decide --book practical-prayers \
  --action move-entry --target bahurupa-close \
  --from tantric-prayer/sangha --to practical-prayers/anytime \
  --thesis-ref inclusion/2 \
  --justification "its own text says recited in every action — definitionally anytime"
```

The gate cross-checks live decisions **against the book's actual state**:
a decision that says X left, while X is still in entries.json, blocks.

## 5. The pipeline (PDF is the LAST step)

`projects/<book>/project.json` carries `"stage"`. The gate attributes every
problem to the stage that owns it; problems at or before your stage print
`[BLOCKED]`, later-stage problems print `[DUE-LATER ...]` (visible worklist,
not yet due).

| Stage | Meaning | Gate owns |
|---|---|---|
| `content` | words exist and are sourced | thesis/template/style/decisions valid; every entry passes anatomy (brief/what/how/sign), has id/title/source/source_ref/source_path/en + IAST/corpus, source file inside the book; no dup ids; opening art rights |
| `structure` | the thesis's shape is realized | sections match `sections_plan` exactly (order too); counts = thesis law; live decisions agree with book state; cross-book id/IAST uniqueness (one prayer, one book) |
| `formatting` | style pass, still no PDF | both book fonts present; `index.html` built; **no source font-size below the 7pt floor** |
| `build` | **LAST** | render Chrome PDF -> `kdp_preflight.py` actual-PDF geometry (page size, embedded fonts, text >=7pt, margins, image ppi) + `max_pages` ceiling |

Advance (forward moves are **verified** — failing checks refuse the move;
backward moves are free because they re-open earlier work):

```bash
python3 factory.py stage --book practical-prayers --to structure
python3 factory.py stage --book practical-prayers --to formatting
python3 factory.py stage --book practical-prayers --to build   # renders PDF only after all pass
```

Why PDF last: content risk >> formatting risk. A 147pp broken render of
unconfirmed content is pure waste (mistakes log, 2026-10-29); structure and
type floor are checkable without pixels. Rendering is also a fleet job —
see AGENTS.md global rule 8, builds dispatched detached with logs.

## 6. Generate a new book

```bash
python3 factory.py new-book --template prayer-book \
  --slug rebirth-explained \
  --title "Rebirth Explained" \
  --claim "What happens when you die — the Kashmir Shaiva account of transition, ..." \
  --section dying:"the moment the bonds loosen" \
  --section between:"where awareness goes" \
  --section return:"what carries forward" \
  --section practice:"what you can do about it"
```

This scaffolds `projects/<slug>/`: thesis (from template: rules inherited,
`max_pages` 110, style canonical, 4 entries/section), the
`declare-structure` decision, `lane.py`, `project.json` (stage `content`).
Then: build `prints/<slug>/` (book.json sections + entries.json via
the bookkit compile loop), work the stages.

- `--entries-per-section`, `--max-pages` (never above the template ceiling),
  `--style` override, `--series "Name" --volume 2` for numbered volumes.
- Ideas that fit the genre: *a practical guide to the Tantraloka*, *a
  practical guide to recognition*, *rebirth explained (what happens when you
  die)*, "X highlights" — highest-signal condensation of a powerful work,
  ≤110pp, same anatomy, same gates. Split to vol 2 instead of growing.
- Different KIND of book (colour, hardback, full-page art) = **new template**
  (`templates/<kind>.json`), not a fork of prayer-book: new constraints
  (colour, stock, art-per-spread), same thesis/decision/stage machinery.

## 7. Products (per book)

| Product | Source | State |
|---|---|---|
| paperback | bookkit HTML -> Chrome PDF -> kdp_preflight | active (PP/TP rebuilding) |
| postcard | `renders_postcards.py` (6x4in @300dpi) | active |
| social | same engine, 1080² + 1080x1350 | active |
| **chant** (verse) | per entry the IAST line in the **videofactory speaker format**: Fish Audio TTS voice `verse` (frozen ID `4e873c…`), cache key `sha1(voice|text)`, receipts → `audio/receipts/calls.jsonl` — the exact `render_chapter` pattern from prx0r/videofactory | **planned & gated** (`prints/<book>/audio-plan.json` exists = build-stage check passes; render only after owner go + FISH key) |
| **audiobook** (how-to) | per entry the how/howto block read by Fish voice **`granny`** (frozen ID `614f8afd…`), same cache/receipts pattern; digital edition plays verse → how-to per prayer | planned with chant — planned by the same `audio` plan |
| **digital** | (a) reflowable **EPUB** from bookkit HTML → Kindle/KDP ebook, (b) DRM-free interior **PDF** for direct sale; built after `build`; cover/metadata separate | declared, not built |

Audio pipeline: `python3 factory.py audio --book <B>` writes `prints/<B>/audio-plan.json`
(2 clips x every entry — PP 72 clips / 11,460 chars, TP 72 / 7,950 — trivial Fish volume).
`check.py` at build stage verifies the plan exists, matches entries, and cache keys are
sound. **Nothing renders until the owner says go.** kashaudio's 769 aligned clips remain
the pronunciation cross-check (`products.chant.coverage.reference_note` in each thesis).

## 8. The two member books (current law)

**Practical Prayers** — 9 sections x 4 = 36. Moments of the day + clockless
Anytime:
`wake · bath · social · work · food · wait · sick · sleep · anytime`.
Decisions: drop alone/flatness/gratitude (mood = TP's rasa territory);
Anytime gains oṃ namaḥ śivāya + bahurupa-core/close + bah-gayatri (from TP
Sangha). Landed: 36 entries, stage build (handoff open).

**Tantric Prayer** — 9 rasas x 4 = 36:
`srgara · hasa · karuna · raudra · vira · bhayanaka · bibhatsa · adbhuta · santa`.
Decisions: Sangha section out (practice-hymns aren't rasa verses); aghora
replaces bha-3 in Bhayanaka (the operative fear-chant); 3 dhyana mantras
retire. Landed: 36 entries, stage build (handoff open).

Both: `<=110pp`, style `canonical`, template `prayer-book`, cross-book
uniqueness enforced (verified: no shared ids/IAST today).

**Landed 2026-11-06:** restructure executed (36/36), layout rebuilt to the
line-budget Devanagari sizing — **PP 90pp / TP 93pp, preflight PASS, both
lanes at `build` stage**. What still blocks `stage --to build` = ship:
the per-entry handoff (source/gate/rights/review records) and per-source
rights resolution (GRETIL/Bailly CC BY-NC-SA flag on the Śivastotrāvalī
transcription). See PIPELINE.md blockers.

## 9. Command cheat sheet

```bash
# gate (stage-aware; DUE-LATER = worklist for upcoming stages)
python3 check.py                          # whole registry
python3 check.py practical-prayers        # one lane
python3 check.py practical-prayers --pdf path.pdf   # force build-stage check

# decisions & stages & scaffolds
python3 factory.py decide --book B --action A --target T --thesis-ref R --justification "..."
python3 factory.py new-book --template prayer-book --slug S --claim "..." --section id:purpose
python3 factory.py stage --book B --to structure|formatting|build|content
python3 factory.py audio --book B                     # plan verse+granny clips (no API calls)

# content-side (renderer is in-repo)
cd prints/<book> && python3 compile.py    # needs patala venv
python3 factory.py quote --text T --ref R --output DIR    # draft cards (never ships)
python3 factory.py verify --manifest M.json               # hash integrity
```

## 10. Laws (the short version)

1. One prayer, one book — cross-book id/IAST uniqueness is gate-enforced.
2. Extract-and-place from sources/layers; clarity-edits only; no source =
   block stays off the page (fail closed).
3. Every change carries a justification citing a thesis clause; history is
   append-only (supersede, never edit).
4. 110pp is the creative boundary; overflow = next volume.
5. PDF build is the LAST stage — content, structure, formatting first.
6. Our English only; Lakshmanjoo/Dyczkowski prose never printed beyond brief
   attributed quotation.
7. Audio binds to exact verse ids with hashes; a preview is never an approval.

Deeper law: `FACTORY-SPEC.md`. Live blockers: `PIPELINE.md`.
