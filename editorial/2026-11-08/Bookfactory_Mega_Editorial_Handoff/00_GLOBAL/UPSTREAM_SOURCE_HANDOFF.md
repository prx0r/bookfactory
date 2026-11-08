# Upstream source audit and exact recovery plan

**Checked live** against `prx0r/translation-work` (`master`) and `prx0r/bookfactory` (`master`) on 2026-11-08. The bookfactory repository's last examined head was `be09663f0e` (2026-11-07). These notes are for editorial agents; source text, licences and approvals have NOT been silently imported.

## Śiva Sūtras: the precise 75 → 77 defect

Upstream: `translation-work/sivasutra/passages.jsonl`, with eight `sivs-p01` … `sivs-p08` grouped passages. The first grouped record labels `1.1-1.10`, but it runs directly from `1.6 śakticakrasaṃdhāne viśvasaṃhāraḥ` to `1.7 jñānaṃ jāgrat`. The latter is **1.8** in the 22 + 10 + 45 recension. The second record later proceeds from its `1.13 dṛśyaṃ śarīram` to `1.14 śuddhatattvasaṃdhānād ...`, again missing the canonical **1.15** and renumbering later material.

The two absent sūtras in the widely followed recension are:

- 1.7 `jāgratsvapnasuṣuptabhede turyābhogasambhavaḥ` (orthographic variants and occasional `saṃvit` expansions should be recorded).
- 1.15 `hṛdaye cittasaṅghaṭṭād dṛśyasvāpadarśanam` (spelling/segmentation varies by edition).

Independent references:
https://www.in.yoga/en/shiva-sutras/
https://trikayoga.org/texts/shiva-sutra/
https://indike.org/pramana/in.sampradaya.saiva.trika.darsana.spanda.sivasutra

**Task:** choose an exact public-domain print witness; compare all 22 first-section sūtras, including deviations besides these two. Correct *upstream* and reassign every 1.x locator after the omissions; reconcile verse hashes and L0/L1/L2 and dependent page references. Do NOT patch 1.7 and 1.15 into output alone or claim the current 75-source is a verified alternative recension. After reconciliation recalculate all 77; then verify 2.1-2.10 and 3.1-3.45.

## Parātrīśikā: initial and final boundary problem

`translation-work/paratrimshika/passages.jsonl` currently groups verse ranges `2-10`, `11-19`, `20-28`, `29-36`, **35 numbered verses** in total. `paratrimshika/T1.md` explicitly calls it a frozen `35 verses (4 passages)` text. This does not support the bookfactory `complete 36` claim. Certain print editions number the root text through v.37. At minimum, the beginning (v.1) and closing (v.37) require adjudication, along with whether introductory speech / colophon material is counted. No automatically assumed 37-verse reconstruction is authorised.

**Task:** collate against KSTS, editions by Gnoli/Bäumer and source manuscript recensions; separate (1) root dialogue, (2) Abhinavagupta's commentary, (3) Abhinavagupta's later authorial closing verses, (4) editorial colophons. Preserve variant counts transparently. Do not print “all 36” while the source starts at v.2.

## Vijñānabhairava: count is not method count

`translation-work/vbt/passages.jsonl` is in **grouped** records (e.g., `vbt-p01`, `verses 2-11`); the Sanskrit is not a one-line-per-sūtra inventory. Current bookfactory proposed 9×18=162 entries. Multiple editions have 163 numbered verses and 112 contemplative methods in the whole dialogue. Do not derive method indexing by dividing numbers into blocks or by dropping opening verses. Source-to-unit alignment must be explicitly verified against a print witness.

## Proofs of the Self: actual source identifiers and licensing

- `translation-work/ajadapramatrsiddhi/source/volumes/ajadapramatrsiddhi.json`
- `translation-work/isvarasiddhi/source/volumes/isvarasiddhi.json`
- `translation-work/sambandhasiddhi/source/volumes/sambandhasiddhi.json`

Each `svatantrya-source-volume/1` manifest provides `content_sha256`, per-passage start/end offsets, and per-passage text hashes. **Validate offsets and hashes against the source bytes** before extracting. Rights metadata explicitly describes the working source as GRETIL **CC BY-NC-SA 4.0** for Ajada, and Muktabodha **CC BY-NC 4.0** for the other two. These are NOT default permissions for selling a commercial paperback. Obtain permission or independently transcribe a public-domain print edition, keeping a source-rights ledger. Only then reconcile the 27/56/23 extraction counts with the actual work.

## Abhinavagupta poems: source names and boundaries

The selected nine poems are available as different upstream directories: `bhairavastava/`, `dehastha/`, `kramastotra/`, `anuttarastika/`, `paramarthadvadasika/`, `mahopadeshavimshatika/`, `paryantapancasika/`, `bodhapancadasika/`, `paramarthacarca/`. Do not take summed index slots as proof that these nine texts have exactly 172 genuine Abhinavagupta-authored stanzas. Audit editorial prefatory verses, colophons and contested attributions. *Ghaṭakarpara* is not safely credited to Kṣemarāja or to Abhinavagupta as author.

## Tantrasāra

Upstream chapters `translation-work/tantrasara-a01/` through `tantrasara-a22/` have their own T1/L0/ARGMAP/L2/C1/proof records. The bookfactory spec currently holds a06, a08 and a13 as *legacy, not gold*. In the candidate 36-teaching ledger these slots must NOT be filled from machine guesses. After the chapter passes, select a continuous authorial excerpt and preserve reference to āhnika, text witness, passage locator and layer version.

## Cross-book interface and release

**One work → canonical scholarly source, not one work → only one physical appearance.** The learner and devotional books must quote parent works. Treat the source's reference edition as its *canonical home* and any short appearance elsewhere as an explicitly attributed *quotation/extract*, not duplicated ownership. An overlap gate based only on IAST bytes would wrongly block this project's core curriculum.

Source workflow for each entry: choose witness → verify edition and author → transcribe and independently collate Sanskrit → padaccheda/morphology → original literal translation → optional source-supported interpretation → record rights → human signoff → final render preflight. A machine-proposed translation or L4 song remains a candidate, regardless of how beautiful its style is.
