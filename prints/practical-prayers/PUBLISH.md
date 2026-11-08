# Practical Prayers — publish pack

## Download / edit
- **Interior PDF (108pp, 6×9):** `practical-prayers-preview.pdf`
- **Cover (full wrap):** `cover.pdf`
- **Kindle EPUB:** `practical-prayers.epub`
- **Page samples:** `p01.png` … `p107_notes.png`, `cover_wrap.png`
- **Content source (edit this):** `entries.json` — one JSON object per prayer
- **Book layout:** `book.json` (sections, title, trim)
- **Rendered HTML:** `interior.html` / `index.html` (rebuild intermediate)

## Edit → rebuild → push (git)

Repo: **https://github.com/prx0r/bookfactory**

```bash
git clone https://github.com/prx0r/bookfactory.git
cd bookfactory
# edit content only:
#   prints/practical-prayers/entries.json   ← wording, translations, how-to
#   prints/practical-prayers/book.json      ← title, sections, trim
git add prints/practical-prayers/entries.json prints/practical-prayers/book.json
git commit -m "PP: edit content"
git push
```

**Do not** hand-edit the PDF in Google Docs for the print master — edit `entries.json`, then rebuild:

```bash
# after push (or locally):
python3 prints/bookkit/engine.py prints/practical-prayers
# then Chrome print-to-pdf → practical-prayers-preview.pdf
# preflight:
python3 prints/kdp_preflight.py prints/practical-prayers/practical-prayers-preview.pdf
```

Or ask the agent: “rebuild practical-prayers PDF after my entries.json push.”

## Rules (fail closed)
- One prayer, one book — don’t move entries across lanes without `factory.py decide`
- Devanāgarī comes from IAST at build — don’t hand-type Deva in JSON
- KDP: upload **cover.pdf** + **practical-prayers-preview.pdf**; use KDP Previewer before submit

## Cover style (house template — locked 2026-11-08)

Practical Prayers cover **is** the template: black ground `#121110`, ivory type,
**Svatantrya mantra-ring logo centred on the blank back** (30 mm, opacity 0.95).
All books use `styles/cover-canonical.json` + `prints/bookkit/cover.py`.
Only the front emblem swaps (`book.json` `meta.cover_image`). See BOOKS.md §7c.
