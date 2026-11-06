# AGENTS.md — bookfactory

Read FACTORY-SPEC.md first, then BOOKS.md (the full system doc: template →
thesis → decisions → stages → products). One-liner: translation layers in,
gated print products out. ONE repo: the books and their renderer live IN
this repo under `prints/` (bookkit engine, kdp_preflight, postcards, every
book dir). This repo owns lanes, gates, theses, decision logs, the quote
loop AND the typography.

## Layout
- BOOKS.md — THE system doc (templates, theses, decision logs, pipeline stages, new-book)
- FACTORY-SPEC.md — the law (position, products, layer stack, bars, migration)
- PIPELINE.md — commands, setup, current blockers
- AUTONOMY.md — how the factory runs without a human in the loop: queue, agent
  contract, proof records, readiness matrix, the produce→gate→critic→proof loop,
  and the six things that never automate (structure law, taste, rights, spend,
  ship, gate weakening)
- REGISTRY.json — live lanes + milestones (update on every state change)
- check.py — the only gate; stage-aware (content→structure→formatting→build, PDF last); exit 0 = canonical
- templates/<genre>.json — overall thesis of a KIND of book (prayer-book: 110pp ceiling, anatomy, products)
- styles/<id>.json — style packs (canonical; owner can save more — presentation only)
- projects/<text>/ — one lane per text: `thesis.json` (what the book IS) +
  `decisions.jsonl` (every change justified vs thesis) + `lane.py` (data paths)
  + `project.json` (stage + outputs + max_pages)
- schemas/ — thesis, decision, template, style, asset, quote-handoff (all fail-closed)
- projects/_template/ — copy to start a non-book lane

## Commands
```bash
python3 check.py                        # whole registry (DUE-LATER = upcoming stages)
python3 check.py practical-prayers      # one lane
python3 factory.py new-book --template prayer-book --slug S --claim "..." --section id:purpose
python3 factory.py decide --book B --action A --target T --thesis-ref R --justification "..."
python3 factory.py stage --book B --to structure|formatting|build  # PDF is the LAST stage
# build (renderer is in-repo):
cd prints/<book> && python3 compile.py                    # needs patala venv
python3 prints/kdp_preflight.py <pdf>
python3 prints/postcards/render_postcards.py <book> [ids...]
```

## Rules
1. No retyped text. Strings come from layer files; fix upstream, rebuild.
2. Devanagari is transliterated from IAST at build; never hand-written bytes.
3. Verdicts: `pdftotext`/`pdfinfo` only. The image-read tool is not evidence.
4. Anything >10s is a background job (`setsid nohup` + own log + notify-send).
5. GATE.json BLOCKED = verse does not ship, no exceptions without a recorded
   owner adjudication (put the ruling in the lane's project.json).
6. KDP Select off; free ISBN first; covers via Cover Calculator at upload.
7. Copyright: our English only. Lakshmanjoo/Dyczkowski prose never printed;
   trust material = brief attributed quote in front matter.
8. Pipeline order is law: content → structure → formatting → build. The PDF
   is rendered LAST (after gates pass); forward stage moves are verified by
   `factory.py stage`. See BOOKS.md §5.
