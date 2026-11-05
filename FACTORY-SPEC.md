# FACTORY-SPEC — book factory (saved 2026-11-05, owner-ordered)

The book factory renders translated works from frozen translation layers into
print-ready paperbacks, quote postcards and social cards. It changes no
authorial text, translation, gate decision, or owner ruling. The existing
Practical Prayers / Tantric Prayer builds (~/visuals/prints) are the parity
baseline: they are what "correct" means until a lane proves otherwise.

## 0. Position in the larger system

Translation-work is upstream (T1/L0/ARGMAP/L2/L3/C1/PROOF feed books through
versioned files only — never hand-copied strings; every shipped line traces to
a source file + ref). This factory is the middle (canonical text → PDF/PNG
products). KDP/Etsy/site/social are downstream (upload packs + one-link
previews only). New texts plug in as lanes (practical-prayers precedent),
never forks. Lane contract: text paths, id mapping, section plan, gate set,
front/back matter, output mix.

## 1. Product stack (one design per product, inherited by every lane)

PAPERBACK — A5 custom trim 5.83x8.27in, no bleed, white/B&W, matte cover;
prayer books cap 108pp (KDP flat $2.30 tier ends at 110pp — hard ceiling);
anthology/verse books use the same bookkit engine. Render: chrome
print-to-pdf of the bookkit HTML, gate `prints/kdp_preflight.py` (fonts
embedded, >=7pt, trim) before any upload.
QUOTE POSTCARD — Prodigi fine-art `GLOBAL-POST-GLOS-6X4`, 6x4in @300dpi,
front = the line + exact text name + ref (and Deva/IAST when present), back =
the explainer (What is it / How to perform it / How to know it's working /
What to feel — designed once in bookkit, reused everywhere).
SOCIAL — same quote, same type stack, two sizes: 1080x1080 feed and
1080x1350 portrait; white ground, ink black, ref line at foot. One CSS size
table, three canvas sizes; no redesign per post.

## 2. Layer stack (purpose, producer, gate)

SOURCE (sha-pinned; PD Sanskrit; our English only — Lakshmanjoo/Dyczkowski
prose never printed, brief attributed quotation in front matter is the sole
exception) → TEXT (canonical lines from L3 where it exists, else L2/L200;
IAST from SOURCE; Devanagari ALWAYS transliterated at build from IAST — no
hand/machine Deva bytes, ever) → CARD (entries.json: brief=C1 essence,
what=ARGMAP/L2 sense, how=practice lines the text itself gives, sign=the
text's own claimed effects/essence, feel=optional micro-line; source_path +
source_ref on every entry. **CONTENT SOURCING LAW: blocks are extract-and-place
from the named layer — never agent-written; only clarity-edits (shorten, plain,
flow) are allowed after placing; no layer source = block stays off the page
(fail closed).** See visuals/prints/EDITIONS.md Part 6 for the block→layer map.) → BOOK (book.json sections/glyph/dividers +
front.html/back.html) → TEXT-GATE (every shipped verse id must carry
deterministic_gate PASS in its text's GATE.json, or a recorded owner
adjudication — BLOCKED fails closed) → PRINT-GATE (kdp_preflight + page
ceiling + source-path/ref integrity — see check.py) → RENDER (chrome PDFs,
pdftoppm PNGs; batch runs are background jobs with logs + notify) → SHIP
(upload pack: final PDF/PNGs + proof receipt + one-link preview; stale
outputs deleted before ship).

## 3. The quote loop (the owner's core motion)

Read canonically -> a line lands -> one command renders it three ways:
`python3 bookfactory quote --text <t> --ref <v>[:<line>]` -> postcard PNG
pair + 1080x1080 + 1080x1350, named `<text>__<ref>__<kind>.png`, index page
for delivery. The ref printed on the card is the canonical ref (e.g.
`Śivastotrāvalī 16.8`, `TS āhṇika 20.1`) — exact, never paraphrased.

## 4. Absolute bars

M1 provenance: every shipped line traces to source_path + ref; check.py
proves ref exists inside the file. M2 no retyped text: strings come from
layer files; edits happen upstream, not in entries. M3 script purity:
Deva from IAST at build; IAST byte-checked against SOURCE when a corpus
index exists. M4 gates: preflight PASS or no PDF; GATE.json PASS or no
verse; page ceiling or no commit. M5 one design: explainer/postcard/social
CSS lives in one place per product; lanes set data, never styles. M6 stale
outputs deleted before rebuild (no silent mixed generations). M7 copyright:
only our English ships; trust-owned material quoted briefly and attributed.
M8 verification is pdftotext/pdfinfo/metadata — the image-read tool is not
evidence (it serves stale frames; hard rule from the visual-ontology work).

## 5. Strictness

One `check.py`: exit 0 = canonical, else the failing lane+entry named.
Lanes declare their data paths in `projects/<text>/lane.py`; the core never
pokes around ad-hoc. One concern per commit. Renders over ~10s are
backgrounded (`setsid nohup` + log + notify — repo global rule). KDP Select
stays off; free ISBN first; covers via KDP Cover Calculator at upload time.

## 6. Migration (strangler, no big bang)

Parity first: PP (44 entries, 108pp) and TP (43, 108pp) are imported as
lanes that reproduce byte-similar output from ~/visuals/prints — the engine
stays where it is, the factory wraps it. Then the queue, in owner order:
ipvv (49 published bundles, proofs running — first external lane), tantrasara
(22 units, GOLD cadence), sivastotravali/vbt/bhairavastava (stotra anthology
lane), then whatever provokes the next quote card. The site and Etsy listing
consume SHIP packs only.

## 7. Milestones (REGISTRY.json is live state)

scaffold (this spec + check.py + template) -> parity-lanes (PP/TP wrapped)
-> quote-loop (postcard+social renderer ported into factory) -> ipvv-lane
-> text-gate wiring (GATE.json enforced in check.py) -> kdp-pack
(cover+proof+upload checklist) -> ship (first external book listed).
