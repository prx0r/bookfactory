# FIVE COMPLETED EDITORIAL WORKSTREAMS — AGENT HANDOFF

Repository checked: `prx0r/bookfactory`, `master`, around commit `1af49bf` (2026-11-07 07:32Z). Product: `prints/practical-prayers` ONLY. Source of truth: `entries.json` 36 records, backed by `sources/`. The `prayers.json` 43-entry file is legacy and must not be merged indiscriminately.

## 1. Respec the prayer-explainer — DELIVERED
`00_explainer_standard.md` establishes **Text → One-sentence sense → When → Act → Recognition → Return → Source note**. Actions labelled traditional versus editorial adaptation. No promised felt signs.

## 2. Decide the length for all 36 entries — DELIVERED
`03_content_overlay_proposals.json` includes one entry-by-entry recitation policy and candidate pocket lines; `02_complete_english_manuscript.md` shows how to present them. Full verse stays canonical. Never truncate an utterance and call it an independent mantra. The Bahurūpa three-stanza sections need owner review: retain as extended practices or move to appendix and replace with new VERIFIED pocket entries, via decision log, not silent substitution.

## 3. Rewrite the actual guide content — DELIVERED
Fresh editor-proposed English copy for all **36** facing pages, plus new introduction and conclusion. Short purposeful ritual, grounded doctrinal turn, back to ordinary action. This is a **creative editorial proposal**, not a claim that every word already exists in translation-work L2. The repo's AGENTS.md currently prohibits agent-authored explainer text: owner/maintainer must approve sourcing policy or place approved prose into upstream human-authorised source layers before production.

## 4. Check philology and provenance — PARTIALLY VERIFIED; BLOCKING ITEMS IDENTIFIED
`05_source_qa.csv` lists all 36 and high-priority repairs. Independently confirmed: Somānanda prayer is Śivadṛṣṭi **1.1**; Dehastha printed items 5, 6, 8 align to verses **3, 5, 7** of a published witness; “deho devālayaḥ” does NOT occur as verse 1 of that checked Abhinavagupta hymn; Kṣemarāja authors Bhairavānukaraṇa; current Śivastotrāvalī 16.1 corpus line incomplete. Other items remain in textual review; do NOT mark all 36 witnessed. See links in CSV.

## 5. Make a safe handoff and release gate — DELIVERED, FINAL CHECK PENDING
These files are content-only; they do not change repo originals. To preview proposed copy, agent may run `python apply_preview.py /path/to/bookfactory`, which writes a new candidate JSON outside the repository by default and **never changes Sanskrit, source paths, source_ref, copyright or author**. It does not authorize publication. Then: fix original Sanskrit UPSTREAM; log `factory.py decide` for structural decisions; review all text against rights-cleared source editions; regenerate HTML/PDF/EPUB; run check.py + kdp_preflight + KDP Previewer; obtain human approval.

### The fastest defensible editorial cut
Keep the 9 × 4 architecture where possible. Do not insist 36/36 are memorised. Teach a handful of easy pocket lines, offer full verses for devotional depth, and put extended recitations in one clearly labelled appendix if structure and page count allow. The book is about being able to PRAY in a moment, not maintaining a daily recital quota.

### Items NOT accomplished
- Full diplomatic collation of 36 Sanskrit verses against print/critical editions.
- Rights clearance for all edition-specific e-texts, archival recordings and commercial artwork.
- Inspection/preflight of the final PDF or upload to KDP.
- GitHub commit/issue creation: earlier integration attempt returned 403. Handoff remains a local ZIP.
