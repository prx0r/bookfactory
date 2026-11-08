# BOOKFACTORY — MEGA EDITORIAL HANDOFF
**Dated 2026-11-08 · `prx0r/bookfactory` reviewed against `prx0r/translation-work`**

## Read this before using the manuscripts
This is an **editorial research and revision handoff**, NOT ten publication-ready Sanskrit editions. There is substantial new original English copy, complete story and lesson drafts, and a source-critical diagnosis of errors in the specifications. Where authoritative Sanskrit witnesses, rights or human review are absent, the reference books intentionally contain **numbered verification slots, not manufactured verses**. The package records the difference. It does not certify proofs, print PDFs or publish to GitHub.

**The priority is accurate, beautiful books, not filling the 108-page template.** The large source-only references cannot honestly be called “full corrected books” until their Sanskrit has been collated. Their complete editorial *indexes* are supplied so another agent can close the gap with source proofs.

## Inventory

| Directory | Book | Actual deliverable | Status |
|---|---|---|---|
| `01_Tantric_Prayer/` | *Tantric Prayer* | 36 **new, individually edited** English-facing guides, new intro and conclusion, per-entry candidate JSON and justifications | Complete *candidate English manuscript*. Sanskrit/rights/owner approval pending |
| `02_Learn_Sanskrit/` | *Learn Sanskrit with Abhinavagupta*, I | 10 full teaching chapters with derivations, exercises, solutions; alphabet reference | Complete *candidate teaching manuscript*. Source/grammatical specialist review pending |
| `03_Parables_of_Recognition/` | *Parables of Recognition*, I | 36 **original complete fictional parables**, 9 groups of 4; art briefs | Complete *original story manuscript*. Owner and illustration approval pending |
| `04_Recognition_Manual/` | *Recognition: A Manual* | 36 original candidate lesson-spreads and a new framing | Complete *candidate original English*. Conflicts with repo's “no agent-written prose” law; needs approval |
| `05_Tantrasara_Essence/` | *Tantrasāra: The Essence* | 36 sharply selected teaching *questions/slots*, new intro/ending | **Not a full translated book**. Needs 36 gold-source excerpts; a06/a08/a13 have legacy holds |
| `06_Siva_Sutras/` | *Śiva Sūtras* | Editorial preface, corrected 77-slot recension-dependent worklist | **Not full Sanskrit text**; upstream 75-source omits standard 1.7 and 1.15 |
| `07_Vijnanabhairava/` | *Vijñānabhairava* | Preface, continuous 163-slot provisional source worklist | **Not full Sanskrit text**; 162/163 + method count unresolved |
| `08_Paratrisika/` | *Parātrīśikā* | Preface, 37-slot provisional source worklist | **Not full Sanskrit text**; upstream contains only 35 (v2–36) |
| `09_Poetry_Abhinavagupta/` | *The Poetry Attributed to Abhinavagupta* | Preface, nine-work 172-slot *provisional* editorial register | **Not full Sanskrit text**; author and verse boundaries await collation |
| `10_Proofs_of_the_Self/` | *Proofs of the Self* | Preface, 106-slot trilogy index and argumentative structure | **Not full Sanskrit text**; rights restrictions in source manifests |
| `11_Practical_Prayers_Prior_Handoff/` | *Practical Prayers* | Earlier ZIP with 36 revised English explanations and release audit | Included for consistency, not rewritten here |

**Total new complete original-English units:** 36 Tantric facing guides + 10 detailed Sanskrit lessons + 36 original parables + 36 Recognition candidate spreads = **118**. Separate **36** Tantrasāra teaching selection notes are not scripture. The five larger reference worklists contain **555 UNREVIEWED slots** (77 + 163 + 37 + 172 + 106); these are *indexes*, not approved translation units.

## The highest-priority findings

1. `translation-work/sivasutra/passages.jsonl` omits standard first-section 1.7 and 1.15 and renumbers the rest: 75 current source units vs standard 77. Correct upstream BEFORE releasing a purportedly complete text.
2. `translation-work/paratrimshika/passages.jsonl` starts v2, ends v36 (35 verses); some published root editions go to v37. Neither the bookfactory 36-count nor our 37-slot worklist is independently signed off.
3. VBT’s 112 methods are **not** its verse total; 162/163 enumeration needs a locked edition.
4. *Tantric Prayer* misleadingly credits Kṣemarāja as author of *Ghaṭakarpara* and overstates Abhinavagupta as originator of śānta rasa; several guides promise somatic 'success' sensations that the Sanskrit does not warrant.
5. *Learn Sanskrit* production JSON contains demonstrably wrong sandhi/compound/padaccheda labels. The new lesson manuscript addresses these, subject to a second independent proofread.
6. Source manifests for the three *Siddhi* works carry NC/NC-SA conditions on existing electronic editions; **commercial clearance not established**.
7. The shelf's literal “one verse, one book” rule is logically inconsistent with the planned learning book and compact prayer selections quoting the same canonical works. Prefer canonical *home* + fully attributed excerpt.

Details, precise source paths, and justifications are in `00_GLOBAL/CRITICAL_FINDINGS.md` and `00_GLOBAL/UPSTREAM_SOURCE_HANDOFF.md`.

## Agent reading order

1. `00_GLOBAL/EDITORIAL_LAW.md` (the doctrine of proof, source and genre)
2. `00_GLOBAL/CRITICAL_FINDINGS.md`
3. `00_GLOBAL/UPSTREAM_SOURCE_HANDOFF.md`
4. `00_GLOBAL/FIVE_WORKSTREAM_AGENT_BRIEF.md`
5. Each book's manuscript and its JSON ledger / source-slot index
6. `00_GLOBAL/QUALITY_REPORT.json` and `00_GLOBAL/MANIFEST.sha256` for package integrity.

## What to do with the candidate records

`candidate_guiderows.json` is a revised **English-only** overlay candidate for the Tantric Prayer roster. `candidate_36_spreads.json` and `candidate_36_slots.json` similarly map text and source-selection proposals. **Do not merge them as a direct replacement for upstream Sanskrit or bypass the owner's decisions**. They are designed for verse-by-verse comparison and approval.

All reference entries are marked `UNREVIEWED` and carry `sanskrit_iast:null`, `translation_original:null`. This is deliberate. The actual code/data to recover and proof the root lives in `prx0r/translation-work`. The source texts must be independently collated and commercially rights-cleared, then proof status updated with a named reviewer.

The previous Practical Prayers editorial ZIP is nested as-is for convenience. No GitHub push or PR has been attempted in this handoff, and no final KDP preflight has been performed.
