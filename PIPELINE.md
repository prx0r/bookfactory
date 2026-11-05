# Publishing handoff: translation → book → reusable products

This document is the current implementation status for the publishing bridge.
`FACTORY-SPEC.md` remains the owner's destination and design brief; statements
in it describing shipping gates are goals until implemented and demonstrated.
The companion implementation is in `prx0r/visuals` on the same
`codex/publishing-handoff` branch. `translation-work` remains the source of
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
   through the existing visuals renderer. They carry `DRAFT · NOT FOR SALE`.
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
5. The visuals preflight checks the **actual PDF**, not only CSS: all page
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

Check out `bookfactory`, `visuals` and `translation-work` as siblings, or set
`BOOKFACTORY_VISUALS` and `BOOKFACTORY_TRANSLATIONS`. Install the dependencies
in an isolated environment using `visuals/prints/requirements-publishing.txt`.
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
python3 ../visuals/prints/kdp_preflight.py --max-pages 110 \
  ../visuals/prints/practical-prayers/practical-prayers-preview.pdf
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
  --asset-root ../tantrasara --book-dir ../visuals/prints/practical-prayers \
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

## Current blockers and next work

- The checked-in 108-page Practical Prayers proof contains text down to 6.08pt
  and text beyond margins on pages 19, 39 and 102. Tantric Prayer contains
  text down to 5.78pt and margin overflows on pages 69 and 83. The old
  preflight silently accepted these. Both old proofs are blocked. The shared
  book CSS now allows long lines to wrap, and entry Sanskrit display
  transliterates from IAST; rebuild **both books in Chrome**, then inspect
  every page with the new gate and verify pagination and content. Those source
  changes alone are not evidence that the existing PDFs are fixed. User design
  choices, legibility and page budget still need a review.
- The actual source for Śivastotrāvalī in `translation-work/sivastotravali/`
  records GRETIL/Bailly as CC BY-NC-SA. The age of a Sanskrit work does not by
  itself clear the specific edition, translation, transcription, illustrations
  or commentary for a commercial product. Resolve rights separately per source.
- The legacy prayer entries are curated inside visuals, not a complete,
  immutable L2/L3-to-entry mapping with decision and rights records. Build
  that mapping per verse without guessing, preserve the exact provenance and
  record owner adjudications against the exact revision. Implement full-book
  source/text/rights gate verification before adding a production release path.
- Card/social layout still needs a full no-clipping and text-coverage proof for
  both renderers, and a physical product proof before sale. The explanatory
  back of a fresh layer-only card stays empty until cited L2/ARGMAP/C1 practice
  content is explicitly selected and reviewed; do not synthesize instructions
  or promised effects from a bare quote.
- A5 no-bleed black-ink white-paper is the existing profile. The prayer-book
  **110-page ceiling is a project cost target**, not KDP's universal page
  limit. Current KDP US regular-trim black-ink pricing is fixed through 110
  pages; Australia is fixed through 108. Check the current marketplace table
  and KDP calculator when publishing. A full-wrap cover is a separate file;
  use the current KDP Cover Calculator and previewer for spine/bleed. KDP Select
  is an e-book exclusivity decision, not a paperback formatting setting.
- The owner's edition ladder in the latest visuals `prints/EDITIONS.md` is
  English (translation), Study (Sanskrit plus English), and Complete (Study
  plus essays, glossary and notes). These are planned products; the current
  factory does not yet construct those three editions. Apply a page ceiling
  only when a particular project declares one; long Study/Complete editions
  should be honestly sized, not cut to fit the prayer books' budget.

KDP sources: [paperback submission requirements](https://kdp.amazon.com/en_US/help/topic/G201857950),
[print options](https://kdp.amazon.com/en_US/help/topic/G201834180),
[paperback costs](https://kdp.amazon.com/en_US/help/topic/G201834340),
and [cover sizing](https://kdp.amazon.com/en_US/help/topic/G201953020).
