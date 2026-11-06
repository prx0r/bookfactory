# Publishing handoff: translation → book → reusable products

This document is the current implementation status for the publishing bridge.
`FACTORY-SPEC.md` remains the owner's destination and design brief; statements
in it describing shipping gates are goals until implemented and demonstrated.
The books and renderer now live IN this repo under `prints/` (migrated
2026-11-06 — one repo for books). `translation-work` remains the source of
translation layers; `tantrasara` remains the source of its video assets. No
upstream text, video approvals, or published work is changed here.

## What works today

1. `factory.py inspect` selects one **exact** L2 or L3 `verse_id`, hashes the
   layer and available source files, and can attach a passage gate only when
   its explicit locator actually contains the Sanskrit citation. Its
   punctuation/whitespace-normalized source comparison is useful evidence,
   not a byte-exact edition or a claim of philological correctness. A
   passage-level deterministic PASS is not a human review.
2. `factory.py quote` builds **draft only** postcards and social previews
   through the in-repo renderer. They carry `DRAFT · NOT FOR SALE`.
   It supports an existing book entry or a translation layer record. It does
   not invent explanatory text when the layers have not supplied it. Each
   product has a namespaced filename, a preview index, and a JSON handoff
   validated against `schemas/quote-handoff.schema.json`. Handoffs record
   input, renderer, font, factory and output SHA-256 hashes; Git commits,
   dirty-input indicators and runtime versions are recorded separately.
3. `factory.py verify` recomputes those hashes. This verifies consistency
   relative to a trusted handoff; hashes are not signatures, licences,
   scholarly approvals, or proof that the text was accurate.
4. `factory.py import-asset` accepts `schemas/asset.schema.json`, checks the
   actual image bytes, declared format, repository/commit/blob and recorded
   uses, and can copy the image into a book and opt it into a new opening
   page. Rights or origin missing means draft-only and requires `--preview`.
   A rights statement is evidence supplied by the operator, not automatic
   legal clearance. The canonical video files are never modified.
5. The preflight (`prints/kdp_preflight.py`) checks the **actual PDF**, not only CSS: all page
   sizes, page limits, embedded fonts, text sizes and safe margins, plus image
   resolution. It reports KDP-oriented mechanical failures. It cannot detect
   every case of text clipped *before* PDF generation, substitution, wrong
   translations, inappropriate wording, copyright, or cover errors.

There is currently **no automated production/ship command**. `check.py` is
fail-closed and returns nonzero for queued projects and for the two existing
prayer books, whose per-entry proofs, rights and reviewed revisions are not
bound to the current release contract. Do not turn a preview or a content
hash into a publishing approval.

## Setup and examples

Check out `bookfactory` and `translation-work` as siblings (books are
in-repo under `prints/`), or set `BOOKFACTORY_PRINTS` and
`BOOKFACTORY_TRANSLATIONS`. Install the dependencies in an isolated
environment using `prints/requirements-publishing.txt`.
Poppler's `pdfinfo`, `pdffonts`, `pdftotext` and `pdftoppm` and Chrome/Chromium
are also needed. Rendering may take more than ten seconds: use the background
job/log convention in `AGENTS.md`.

```sh
python3 factory.py inspect --text tantrasara-a01 --ref tsa-a01-v01 \
  --gate-id tsa01-p01
python3 factory.py quote --text tantrasara-a01 --ref tsa-a01-v01 \
  --gate-id tsa01-p01 --output /tmp/quote-preview
python3 factory.py quote --text practical-prayers --ref gita-424 \
  --output /tmp/quote-preview
python3 factory.py verify --manifest /tmp/quote-preview/tantrasara-a01__tsa-a01-v01__manifest.json
python3 check.py practical-prayers
python3 prints/kdp_preflight.py --max-pages 110 \
  prints/practical-prayers/practical-prayers-preview.pdf
```

References for layer records are the actual immutable IDs, not guesses from
verse numbers. A single exact L3 line is selected with `--ref tsa-a01-v01:1`;
the original full Sanskrit citation remains shown. `--gate-id` is optional,
but omitted gates remain `unmapped`. The sample's upstream passage is
currently BLOCKED. Supplying that locator records the block; it does not
release the verse. `--backend weasyprint` is an optional **experimental draft
preview** for hosts where Chromium cannot run; it is not a parity or KDP proof.

For a reusable image, create a manifest matching `schemas/asset.schema.json`:
`file.path` is relative to `--asset-root`; `file.sha256` is the hash of those
exact bytes; `origin.repository` is `owner/repo`, with a full commit SHA and
project reference. Record rights holder and evidence, and list each intended
use. Then:

```sh
python3 factory.py import-asset --manifest asset.json \
  --asset-root ../tantrasara --book-dir prints/practical-prayers \
  --preview --set-opening
```

That command changes the chosen book's `book.json` and stages a copy and its
manifest inside that book. Omit `--set-opening` to stage without changing the
layout. The optional page consumes one page and its image must meet the final
print resolution and book page-budget checks. A committed image with recorded
rights may be staged without `--preview`, but its use is still blocked by the
publication gate pending independent review. Never treat a generated thumbnail,
an old video approval or the existence of a licence field as permission to
sell the same image in a book.

## Thesis + decision log (every book's source of truth)

> **BOOKS.md is the canonical full-system doc** (template genre → thesis →
> decision log → pipeline stages → products → `new-book` generator). This
> section is the summary.

A book lane is not canonical without a **thesis** (`projects/<book>/thesis.json`:
its `template` (genre — `templates/prayer-book.json`: 110pp ceiling, entry
anatomy, pipeline), `style` pack, the claim (intro derives from it), the
structure law — sections x entries x total —, inherited + book-specific
inclusion/exclusion rules, and the full product stack: paperback, postcard,
social, **audiobook**, **chant**). Nothing about shape is hand-maintained prose.

Every construction change is a line in `projects/<book>/decisions.jsonl`:

```sh
python3 factory.py decide --book practical-prayers \
  --action move-entry --target bahurupa-close \
  --from tantric-prayer/sangha --to practical-prayers/anytime \
  --thesis-ref inclusion/2 \
  --justification "its own text says recited in every action — definitionally anytime"
```

- `--justification` fails below 40 characters (empty why = no decision).
- `--thesis-ref` must resolve into the thesis (e.g. `exclusion/0`, `structure`)
  or the command refuses to append.
- `check.py` enforces all of it: thesis/template/style present, every decision
  valid + resolvable, book sections/counts matching the thesis exactly,
  remove/add decisions agreeing with the book's current state, entry anatomy,
  and no entry shared between the two books (one prayer, one book).
- **Pipeline stages** (`project.json stage`): `content → structure →
  formatting → build` — the PDF is rendered **LAST**, after content/structure/
  formatting gates pass. The gate attributes problems to stages: current-stage
  problems print `[BLOCKED]`, later ones `[DUE-LATER ...]` (the worklist).
  Advance verified with `factory.py stage --book B --to <stage>`; new books
  scaffold with `factory.py new-book --template prayer-book ...`.

Audio products live in the thesis too: per-prayer **chant** clips bind to
`prx0r/kashaudio` aligned verses (769 across 28 works — both books' source texts
are already rendered) or Swamiji archival (`aghora-swamiji.mp3`,
`bahurupa-swamiji.m4a`); the **audiobook** readout derives from entries.json
fields only. Both are declared `planned` with per-work coverage in
`products.chant.coverage` — a clip manifest ships with the digital edition.

## Rights: the GRETIL problem and the routes around it (researched 2026-11-06)

The Śivastotrāvalī transcription feeding `translation-work/sivastotravali` is recorded
CC BY-NC-SA 4.0 — confirmed at source: the GRETIL/TextGrid edition page carries
`Distributed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0`
(https://betaportal.textgrid.d.sub.uni-goettingen.de/browse/49kq9.0), and GRETIL's own
front page says files are "STRICTLY FOR SCHOLARLY REFERENCE... ANY COMMERCIAL USE IS
EXPLICITLY EXCLUDED". The verses themselves are 10th-century (public domain everywhere);
it is the *transcription/edition* that carries the NC clause. Routes to clear commercial
print:

1. **PD-scan re-transcription (recommended, cleanest).** Witness our IAST against an old
   printed edition scan — e.g. archive.org `Sivastotravali.of.Utpaladeva.With.the.commentary.of.Ksemaraja`
   (Rājānaka Lakṣmaṇa ed.) or any pre-1929 print (Nirṇāya Sāgar/Bombay series). Verify the
   scan's publication date first; the Sanskrit text of a 10th-c. work is PD; our own
   transcription from a PD scan carries no NC. Record the collation as a `decide` decision
   citing the thesis rights clause.
2. **Sanskrit Wikisource** — page texts under CC BY-SA 4.0: attribution + share-alike,
   **commercial use allowed**; SA applies to derivatives of the Sanskrit text, not to our
   English. Viable with a credit line; weaker than route 1 (still a share-alike obligation).
3. **sanskritdocuments.org** — full Śivastotrāvalī in Devanagari (all 20 stotras); terms
   are per-use — verify their current license statement before relying on it.
4. **License request to GRETIL/inputter** — possible but slow; the per-text inputters
   sometimes grant commercial terms on request (their headers say "contact to negotiate").

Until one route lands: no commercial ship. Front-matter attributed quotations stay fine.

## Current blockers and next work

**Status 2026-11-06 (restructure landed, build green):**

- Both books restructured to thesis law: **PP 36 (9x4, mood sections out,
  Anytime in with oṃ namaḥ śivāya + 3 Bahurūpa hymns), TP 36 (9 rasas,
  Sangha dissolved, aghora at the fear door, bha-3 + 3 dhyana retired).**
- Layout rebuilt on the merged engine: line-budget-aware Devanagari sizing,
  tightened type geometry. **PP 90pp / TP 93pp — both preflight PASS**
  (A5, fonts embedded, >=7pt, margins clean, zero continuation sheets).
  Previews: `prints/<book>/<book>-preview.pdf`.
- **Stage: both lanes at `build`; `stage --to build` is blocked by the
  per-entry handoff gate** — the honest remaining work before any ship:
  1. Per-entry source/gate/review records (entries carry source_path+ref,
     but no per-entry binding of passage, gate decision, review signoff).
  2. **Rights resolution per source** — `translation-work/sivastotravali`
     records GRETIL/Bailly as CC BY-NC-SA: the age of a Sanskrit work does
     not clear the specific edition/transcription for a commercial product.
     Resolve per source before sale (front-matter attributed quotes are fine).
  3. New proofs after any content change (Chrome render + preflight), then
     KDP Cover Calculator for covers, KDP previewer at upload.
- Cards/social layout still needs its no-clipping proof for the 36-entry
  books; the explanatory back of a fresh layer-only card stays empty until
  cited content is selected (no synthesis).
- Audio (thesis products): chant = kashaudio clips bound per entry
  (PP:8/8 source works rendered there; TP: shivastotravali+krama) +
  Swamiji archival for aghora/bahurupa; audiobook readout = entries.json
  fields only. Manifests not built yet.

KDP sources: [paperback submission requirements](https://kdp.amazon.com/en_US/help/topic/G201857950),
[print options](https://kdp.amazon.com/en_US/help/topic/G201834180),
[paperback costs](https://kdp.amazon.com/en_US/help/topic/G201834340),
and [cover sizing](https://kdp.amazon.com/en_US/help/topic/G201953020).
