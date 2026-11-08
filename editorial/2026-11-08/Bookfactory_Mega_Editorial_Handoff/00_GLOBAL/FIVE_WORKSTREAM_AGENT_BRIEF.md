# Five autonomous editorial workstreams — execution brief

**Input:** this package, `prx0r/bookfactory` current master, `prx0r/translation-work` current master and any signed source witnesses. The package is a **candidate proposal**, not permission to override gates, canonical upstream source, owner rulings or licences. Run workstreams in dependency order; create reviewable PR checkpoints with clear diffs and audit receipts.

## Workstream 1 — Source integrity and rights (highest priority)
1. Fix source-witness enumeration: 77 Śiva Sūtras, including missing 1.7 and 1.15; adjudicate Parātrīśikā 35/36/37 including its first/final verses; fix VBT 162/163; independently certify Poetry 172 and Proofs 106.
2. For *Tantric Prayer*, check all 36 Sanskrit witness rows and translations, especially Ghaṭakarpara authorship, Gītārthasaṅgraha invocation, Kramastotra, and any machine-proposed L4.
3. Record witness scan, edition, folio/page, source SHA, variants and licence for every passage. **If missing or NC-restricted for commercial publication, leave BLOCKED.** No automatic workaround.
4. Pull upstream `translation-work` from source manifests; never create invented 'canonical' Sanskrit. Keep the existing Git corpus's 75/35 defects explicit until resolved.
**Done when:** source ledger and rights ledger exist, and exact per-unit PASS/BLOCKED statuses are reproducible.

## Workstream 2 — Manuscripts and philosophical accuracy
1. Apply `01_Tantric_Prayer/FULL_ENGLISH_MANUSCRIPT.md` to all 36 facing-page guides as a **review candidate**, preserving the original Sanskrit and source references. Remove physiological 'sign' promises. Keep aesthetic rasas distinct from ordinary moods; correct attribution and śānta origin claim.
2. Edit the ten *Learn Sanskrit* lessons according to `02_Learn_Sanskrit/…`: correct mislabeled compound/sandhi/padaccheda, verify underlying forms, show exact reversible grammatical steps, mark excerpt boundaries, gradually shift to Devanāgarī.
3. Get owner adjudication for the original prose exception in *Recognition*: 36 candidate spreads are NEW synthesis, not preexisting canonical translation layers.
4. For *Tantrasāra* fill the proposed 36 teaching outline with **actual gold source text**, giving exact refs, and retain holds for a06/a08/a13 until verified.
5. Preserve the 36 original Parables as literary prose, not fabricated scriptural anecdotes; get owner text approval and write art briefs, but do not claim finished art.
**Done when:** every accepted English sentence has status and no claim exceeds its source.

## Workstream 3 — Complete reference volumes (NOT arbitrary page-quota editions)
1. Use `06`–`10` indexed source-ledger JSON files as complete **worklists**. They are not manuscripts and must never be sent to KDP until fields are populated and approved.
2. Assign an appropriate *named print edition and recension* per work, not a collage of unrelated modern transcriptions.
3. Populate per-verse Sanskrit/IAST, original literal English, reference, and tiny lexical note. Restore original divisions; do not force nine groups/108 pages.
4. Independently collate both beginnings and ends; mark authorial vs commentarial vs colophon. For *Poetry*, test all nine titles and manuscript attributions; for *Proofs*, preserve the argumentative order and don't assert a syllogism where only an editorial synthesis exists.
**Done when:** all ledger slots PASS, final count reconciled to witness, original translations approved, rights clear. Until then the books are *held drafts*, not corrected editions.

## Workstream 4 — Production + accessibility
1. Make machine-readable `source_version`, `rights_record`, `proof_status`, `editorial_signoff` required by content gates. Adapt 'one verse one book' to 'canonical scholarly home + attributed quotation/extract' so learner/prayer books can quote source references legally and accurately.
2. Rebuild all accepted books from canonical record. Proof Devanāgarī shaping, IAST, compound punctuation, footnotes, crossrefs, source notes and blank page count. Do not add note pages merely to reach 108.
3. Run tests, text extraction, font/trim and cover preflight on the **final PDFs**, and verify EPUB navigation/Unicode; update manifest hashes.
4. Keep audio off printed QR unless URL resolves, has valid permission, clips exist and pronunciations have been reviewed. No AI voice imitates a living or identifiable teacher without permission.
**Done when:** tests green and every listed external link and publishing claim is real.

## Workstream 5 — Editorial signoff and go/no-go
1. Present one changeset per book with a diff from live repo, reasons per change, new/corrected source references and any omitted content.
2. Run a critical review on every passage with focus on Sanskrit derivation, exact literal meaning, doctrinal overstatement and source/genre boundaries.
3. Get owner approval for interpretations, original stories, parable art, cuts and external publishing. Keep source specialist adjudication for unresolved variants.
4. Release only books whose all print rights, witness, technical and creative checks pass. File a hold note for the rest. No fake success reports, no silent overriding of a 'BLOCKED' gate.
**Done when:** every shipped unit links to a human-signed proof receipt.

## Proposed PR checkpoints
`source-integrity-foundations` → `tantric-prayer-edit-candidate` → `learn-sanskrit-grammar-audit` → `original-prose-owner-review` → `reference-sets-collated` → `final-publishing-preflight`.

## Key check commands (local repo; do not assume these passed here)
```
python3 check.py
python3 check.py tantric-prayer
python3 check.py learn-sanskrit
python3 factory.py stage --book tantric-prayer --to build
python3 prints/kdp_preflight.py prints/tantric-prayer/tantric-prayer-preview.pdf
```
Run only as applicable and only after source and rights requirements pass. `factory.py stage` changes repo state: use branch/PR, never silently rewrite master.
