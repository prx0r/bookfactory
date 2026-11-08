# Critical source and concept corrections — release blockers

## 1. Śiva Sūtras: the number 75
`specs/siva-sutra-aphorisms.thesis.json` promises **75**, but the widely printed Kṣemarāja version is **77 = 22 + 10 + 45**. Rename to *The Seventy-Seven Śiva Sūtras* provisionally, select a witness, and check any rare recension difference explicitly. Do not silently discard 2 sūtras to preserve a 75-page layout. **Live upstream check identifies the omitted standard 1.7 (jāgratsvapnasuṣuptabhede turyābhogasambhavaḥ) and 1.15 (hṛdaye cittasaṅghaṭṭād dṛśyasvāpadarśanam); the next entries have been renumbered.** The first 20-item upstream section is therefore not a source for the 22-item standard recension. See `UPSTREAM_SOURCE_HANDOFF.md`.
Evidence: https://indike.org/pramana/in.sampradaya.saiva.trika.darsana.spanda.sivasutra ; https://www.sanatanarahasya.com/lineages/tantra-texts/the-shiva-sutras/

## 2. Vijñānabhairava: 162 vs 163; verses vs dhāraṇās
Common printed presentations number **163 verses**, with **112 dhāraṇā methods** within the dialogue. A complete reference must define its primary edition's line numbering, opening/closing verses, and exactly what is counted. The proposed nine arbitrary blocks of 18 are a layout convenience, not the scripture's chapter structure.
Evidence: https://www.in.yoga/en/vijnana-bhairava-tantra/ ; https://indike.org/pramana/in.sampradaya.saiva.agama.trika.vijnanabhairava

## 3. Parātrīśikā: 36 vs 37
A published Parātrīśikāvivaraṇa edition prints an explicitly numbered verse **37**; current *Goddess's Thirty-Six* specification says complete 36. Collate the KSTS/Gnoli/Bäumer numbering and clarify whether any verse is closing or supplementary. **The upstream `paratrimshika/passages.jsonl` contains only ranges 2–10, 11–19, 20–28 and 29–36 (35 verses); the upstream T1 header itself says 35.** The discrepancy involves both ends, not simply a renamed title; see `UPSTREAM_SOURCE_HANDOFF.md`. Rename to *The Goddess's Question: The Parātrīśikā* until the count is settled.
Evidence: https://www.motilalbanarsidass.com/products/para-trisika-vivarana-of-abhinavagupta-the-secret-of-tantric-mysticism

## 4. Poetry of Abhinavagupta: what counts as his composition
The 172-verse / nine-hymn total must be rechecked hymn by hymn: whether introductory/invocation verses belong to the work, whether differing recensions alter counts, whether Kramastotra attribution is secure, whether Dehasthadevatācakra includes the common *deho devālayaḥ* prefatory maxim. Distinguish Abhinavagupta's poems from works on which he wrote commentary.
Evidence: https://mahanaya.org/en/scriptures/dehasthadevatacakrastotram/ ; https://sanskritdocuments.org/doc_deities_misc/dehasthadevatAchakrastotram.html

## 5. Tantric Prayer: conceptual and attribution problems
The printed intro says Abhinavagupta *added* śānta to a definitive eight-rasa system. This is too definite: he systematised/defended its status amid earlier theories and variant Nāṭyaśāstra traditions. The nine rasas are aesthetic experiences of represented emotion, not nine guaranteed spiritual transmutations of raw personal states.
Evidence: https://www.namami.gov.in/sites/default/files/book_pdf/The%20Recensions%20of%20Natyasastra.pdf ; https://ebooks.inflibnet.ac.in/engp11/chapter/abhinavagupta-abhinavabharati/
The entry `srg-3` attributes *Ghaṭakarpara* to **Kṣemarāja** as author. Bibliographic research treats the poem's authorship as disputed, variously Kālidāsa or Ghaṭakarpara, and associates Abhinavagupta with a commentary. Mark authorship disputed; recheck whether the verse is from the correct work and the 'Kṣemarāja' is a mistaken author line. Evidence: https://ci.nii.ac.jp/ncid/BA71616307 ; https://www.britishlibrary.uk/ ; https://www.revivetantra.org/ksts-kashmir-texts-and-series
In `has-2`, *upahāsa* is presented as a cosmic joke without checking the literal poetic context; in `kar-3`, `duḥkha -> ghṛta` and 'ghee' require source verification. `adb-3` and `bib-4` explicitly derive from **machine-proposed L4** with human-review requirements; hold until human proof.

## 6. Existing learn-Sanskrit lesson structures contain grammar mistakes
- `l08`'s `padaccheda` inexplicably includes words from the **second half** of a verse not printed in that lesson. Fix scope.
- `l09` treats `sarvam ekam idaṃ` as a compound. It is a syntactic sequence of separately inflected words with external sandhi; don't conflate this with samāsa.
- `l09` treats `śāntamiti` as `śānta + iti`; the correct split is `śāntam + iti` (neuter accusative/nominative form remains).
- `l09` repeats `tvadbhaktirasacarvaṇāt` in the structured padaccheda with **underlying = ca**. Schema-level error.
- `l07` treats the dual ending `-yor` as though it were sandhi; it is an inflectional ending (genitive/locative dual).
- `l03` and `l04` supply ellipses inside the displayed IAST. Excerpt ellipsis is a typesetting marker, not a Sanskrit word; witness must be separately preserved.
- `l10` source is marked machine-proposed. The grammar may be useful but it is not a publish-cleared source witness.

## 7. Cross-book uniqueness policy contradiction
`specs/INDEX.md` says every complete reference text owns *all* its verses, while *Practical Prayers* and *Tantric Prayer* quote Śivastotrāvalī and the learner quotes Mahopadeśa. A literal cross-book IAST uniqueness gate rejects the current shelf. Replace with **canonical home + attributed quotations**; no verbatim duplicated entry pretending to be a separate owner. Shared source snippets are necessary pedagogically.

## 8. Proofs of the Self / 106 versus argument structure
The proposed 106 (= 27 + 56 + 23) might describe a particular source extraction of three siddhi texts rather than independently established canonical versification. Confirm actual title, text boundaries, prose/verse units and that all verses belong to Utpaladeva before locking total. Argument summaries are *editorial reconstructions*, not logical proofs that compel acceptance.

## 9. Tantrasāra and Recognition Manual
*Tantrasāra: The Essence* spec excludes a06/a08/a13 until the gold transformation; its proposed content can only be an editorial selection ledger, never a source-verified complete book at this stage. *Recognition: A Manual* says both 'original prompts that produce recognition' and 'no agent-written connective prose'; an edited primer needs an owner-approved human-composed prose exception or remains an extract-only reader. Cannot say 'nothing to believe' and then assert nondual metaphysics is a logical theorem.

## 10. Rights and release
Sanskrit in old editions may be public-domain; volunteer e-text encodings, apparatus, contemporary English renderings, scholarly commentary and audio have distinct rights. Use a scanned public-domain edition for fresh transcription; log its source and all deviations. No output in this handoff represents completed copyright clearance or a final print proof.
