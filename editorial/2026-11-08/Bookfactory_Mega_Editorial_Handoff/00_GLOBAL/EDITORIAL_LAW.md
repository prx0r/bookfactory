# Editorial law for the bookfactory shelf — candidate revision 2026-11-08

## North star
Each book must be faithful to its **actual source and genre**, not to the page quota. Beauty is not licence to invent Sanskrit or certainty. The shortest text that communicates an entire thought is preferable to a slogan broken from an argument.

## Three claims never merged
1. **Witness:** exactly what the selected Sanskrit edition prints, with edition/page/verse and a stable hash. A variant is labelled as a variant, not a typo until collated.
2. **Grammar and translation:** recover padaccheda, cases, syntax and compounds before providing idiomatic English. If the text is ambiguous, record the competing analyses and one reason for the chosen reading.
3. **Trika interpretation / contemporary practice:** distinguish words of the root author, traditional commentator, recorded teacher, and the present editor. Contemplative suggestions are optional suggestions, not claims of historical prescription or guaranteed signs.

## Genre separation
- **Prayer books:** original complete verse plus a short memory handle if contiguous and syntactically defensible. Facing explanation in this order: literal petition/assertion; when; act; the turn; return; source note. Treat a half-verse as EXTRACT, never a new ancient mantra.
- **Reference books:** COMPLETE and ordered Sanskrit root text, original source-collated English, minimal word help. No invented practice program; no verse removed to fit nine equal sections or 108 pages.
- **Learning book:** ten layers in sequence: witness, recitation, padaccheda, morphology, compounds, sandhi, syntax, grammar-derived translation, sourced exegesis, exercise. The learner should be able to reverse derivations.
- **Recognition manual:** mark original modern prompts as editorial synthesis until owner approves abandoning a strict extract-and-place rule; never claim to quote untranslated Tantrasāra.
- **Parables:** original stories with no forced source quotation or moralising coda; art is separate and needs human signoff.

## Length and memorisation
- Pocket: 2–10 words, only a grammatically meaningful continuous extract; label EXTRACT and show parent verse.
- Complete short verse: default when the verse is 16–32 syllables; permit half-verse as training wheels.
- Long verse / multiple verses: keep complete text for reference and offer an accurately framed reading key rather than an untransmitted mini-mantra.
- Distinguish mantra, prayer/petition, praise, philosophical assertion, and meditation instruction.

## What to remove
- Sensation-based success tests (warm chest, disappearing bodily boundary, promised analgesia, guaranteed visions).
- Blanket claims that Abhinavagupta invented a rasa or a ritual without a witness.
- Placing an aesthetic category on a private emotion as though theatrical rasa and an ordinary mood were identical.
- Misleading exact page targets; never pad with blank leaves to falsify completeness.
- Unattributed commentary/literary translations imported from copyrighted modern editions.

## Required proof record (per Sanskrit unit)
`unit_id, work, author_attribution, recension, edition, page, chapter, verse, script_transcription, IAST, normalized_padaccheda, reading_variants, grammatical_validation, literal_translation, editorial_interpretation, rights_basis, proof_status, reviewer, signed_date, source_sha256`.
`proof_status` must be an explicit `PASS / BLOCKED / UNREVIEWED`. UNREVIEWED is **not** PASS.

## Print gate
1. No Sanskrit unit in BLOCKED/UNREVIEWED state reaches a commercial release.
2. Exact content roster matches edition numbering, with section boundaries defined by source not divisibility.
3. The digital text and PDF share hashes of the final printed IAST and English.
4. KDP PDF geometry/trim/embedded glyphs/cover sizing/spine/barcode verified on the **final** artifact.
5. Rights clearance recorded for Sanskrit transcription, English original prose, source artwork, audio and fonts.
6. Owner reviews every creative/interpretive change; no implied approval.

The attached drafts are agent-facing candidate copy. They do not supersede the upstream witness and should not be automatically published.
