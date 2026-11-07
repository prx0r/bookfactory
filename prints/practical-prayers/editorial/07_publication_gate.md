# Publish gate — Practical Prayers

1. **Textual freeze:** each of 36 entries linked to an exact full Sanskrit witness and verse ID; no reconstructed or incomplete passages. Flag textual alternatives explicitly. Source rights cleared. Somananda 1.1; Dehastha reference corrections; Śivastotrāvalī 16.1 repaired or replaced; Bahurūpa recension reconciled; Anuttarāṣṭikā 4 retranslated. Correct all IAST and regenerate Devanāgarī from source only.
2. **Content freeze:** new reader-facing copy approved as original editorial content; no fake somatic success tests; documented traditional practice distinguished from suggested action. Short phrases always marked excerpt; full verse always accessible. Any move/replace has thesis/decision record.
3. **Consistency freeze:** intro's list of hymns matches 36 actual entries (no fictitious Krama Stotra); Bahurūpa passages correctly identified as parts of one hymn; back matter matches clock sections. No placeholder QR/audio promised while clips are absent.
4. **Production QA:** compile from frozen sources; run repository `check.py practical-prayers`, `prints/kdp_preflight.py` on exact final interior; check embedded Devanāgarī, 6x9 margins, page count, cover geometry; proof pages in KDP Previewer and actual EPUB on Kindle. Blank notes pages intentional and legible.
5. **Shipping:** publish only after editorial/witness/rights signoffs. Capture final SHA, file checksums, KDP metadata and release manifest. Do not mistake generated PDF existence or source-layer stage ‘formatting’ for approval.

The `03_content_overlay_proposals.json` is not a ready-to-ship Sanskrit edition. Source checks are still hard gates.
