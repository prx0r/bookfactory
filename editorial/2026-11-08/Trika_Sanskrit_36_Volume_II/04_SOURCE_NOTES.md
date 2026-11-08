# Witness and source audit

All 36 excerpts are identified by traditional work and individual verse/sūtra in the JSON and source ledger. The web witnesses below enabled a first-pass comparison; do not mistake their availability for commercial publishing rights or proof against a historical printed edition.

- **SS** — Vasugupta (traditionally attributed); *Śivasūtra*. https://indike.org/pramana/in.sampradaya.saiva.trika.darsana.spanda.sivasutra. 77-sūtra recension 22+10+45; source has been independently checked; differs from repo 75-count transcript.
- **BP** — Abhinavagupta; *Bodhapañcadaśikā*. https://mahanaya.org/en/scriptures/bodhapancadasika/. Mahānaya + GRETIL transcription; punctuation, compounds and variant vowels still require printed-witness rights check.
- **PS** — Abhinavagupta; *Paramārthasāra*. https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_abhinavagupta-paramArthasAra.htm. GRETIL transliteration checked against SanskritDocuments where appropriate; commercial reuse of GRETIL transcription not cleared.
- **SV** — Utpaladeva; *Śivastotrāvalī*. https://mahanaya.org/en/scriptures/sivastotravali/. Mahānaya + GRETIL Bailly text; individual readings require final comparison with Kṣemarāja commentary.
- **SP** — Kallaṭa / Vasugupta tradition; exact authorship debated; *Spandakārikā*. https://mahanaya.org/en/scriptures/spandakarikah/. GRETIL + Mahānaya; do not assert sole authorship with certainty.

## Cross-checks / priority corrections

- **Śivasūtra recension:** Use Kṣemarāja-family 77 arrangement (22+10+45); `translation-work/sivasutra` currently declares 75 and must not be used to infer a canonical 75-sūtra count. None of these 8 selected locators are the omitted 1.7 or 1.15.
- **Spandakārikā authorship:** Published corpora variously attribute it to Vasugupta or his disciple Kallaṭa; the book is framed as the Spanda tradition, not a settled authorial signature.
- **Bodhapañcadaśikā 5:** A witness prints `sarvabhaveṣu` (short a), so the gloss is modes of *becoming*; do not normalize silently to `sarvabhāveṣu`.
- **Śivastotrāvalī 1.10:** `saṃvinmārgaḥ` has a complex internal junction; no invented external sandhi rule is printed.
- **Paramārthasāra 8:** The selected half-verse borrows *prakāśate* from the preceding comparative half. That dependence is labelled.
- **Utpaladeva 1.12 / Spanda 1.18:** The selected passages are syntactically incomplete and are explicitly marked as extracts.
- **Final Bodha 14:** `etau`, `bandhavimokṣau`, and `bhidyete` are **dual**, not plural; maintain the restriction “from the standpoint of the Lord’s nature.”
- **Devanāgarī:** generated mechanically from IAST and normalized with simple joining for avagraha; in a printed edition verify repha, conjuncts, word separation and anusvāra usage.

## Never silently promote

`source text / variant` → `translation` → `interpretation` → `modern reflection` are different levels of claim. Commercial rights approval and independent philological review are external release gates, not things this draft can assert.
