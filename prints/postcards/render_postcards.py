#!/usr/bin/env python3
"""render_postcards.py — Prodigi fine-art postcards from a book's entries.json.

Product: GLOBAL-POST-GLOS-6X4 (fine-art postcard, 6x4in = 152x102mm, 300dpi,
front AND back free-form — the classic postcard back is postal-only, so the
guide goes here). Front = the prayer, back = the explainer (the same four
blocks as the book guide: What is it / How to perform it / How to know it's
working [/ What to feel]). Designed ONCE — both books inherit.

Usage:
  python3 prints/postcards/render_postcards.py practical-prayers
  python3 prints/postcards/render_postcards.py tantric-prayer mpa-1 sst-16-8
  python3 prints/postcards/render_postcards.py all            # both books
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
PRINTS = os.path.dirname(HERE)
ROOT = os.path.dirname(PRINTS)
TIO = "/root/.fonts/TiroDevanagariSanskrit-Regular.ttf"
COR = "/root/.fonts/CormorantGaramond[wght].ttf"
OUT = os.path.join(ROOT, "outputs", "print_products", "postcards")
W, H = 1800, 1200           # 6 x 4 in @ 300dpi  (GLOBAL-POST-GLOS-6X4)
SKU = "GLOBAL-POST-GLOS-6X4"

CSS = f"""
@page {{ size: 6in 4in; margin: 0; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ background:#fff; }}
@font-face {{ font-family:'Tiro'; src:url('file://{TIO}'); }}
@font-face {{ font-family:'Cormorant'; src:url('file://{COR}'); font-weight:300 700; }}
.page {{ width:6in; height:4in; overflow:hidden; background:#fff;
  color:#17140f; font-family:'Cormorant',serif; position:relative;
  padding:.37in .4in; page-break-after:always; }}
.page:last-child {{ page-break-after:auto; }}
.label {{ font-size:7.5pt; letter-spacing:.24em; text-transform:uppercase;
  color:#76736e; font-weight:600; }}
.rule {{ height:2px; background:#17140f; opacity:.75; margin:.09in 0 .11in; }}

/* ---- FRONT: the prayer ---- */
.f .src {{ font-size:7.5pt; letter-spacing:.18em; text-transform:uppercase; color:#76736e; margin-top:.05in; font-weight:600; }}
.f .cols {{ display:flex; gap:.23in; margin-top:.15in; height:2.53in; }}
.f .left {{ width:45%; }}
.f .right {{ flex:1; }}
.f .dev {{ font-family:'Tiro',serif; font-size:16pt; line-height:1.6; }}
.f .iast {{ font-size:9.5pt; line-height:1.5; color:#76736e; font-style:italic; margin-top:.15in; }}
.f .en {{ font-size:14pt; line-height:1.5; font-weight:500; }}
.f .en.sm {{ font-size:11pt; }}
.f .en.xs {{ font-size:9.5pt; }}
.f .foot, .b .foot {{ position:absolute; left:.4in; right:.4in; bottom:.25in;
  display:flex; justify-content:space-between; align-items:baseline;
  border-top:1.5px solid #17140f; padding-top:.07in; }}
.f .foot .sec, .b .foot .sec {{ font-size:7.5pt; letter-spacing:.2em; text-transform:uppercase; color:#76736e; font-weight:600; }}
.f .foot .bk, .b .foot .bk {{ font-size:7.5pt; letter-spacing:.3em; text-transform:uppercase; font-weight:600; }}

/* ---- BACK: the explainer (once, both books) ---- */
.b {{ padding-bottom:.95in; }}
.b h1 {{ font-size:16pt; font-weight:600; line-height:1.1; letter-spacing:.01em; }}
.b .brief {{ font-size:9.5pt; font-style:italic; color:#3d382f; line-height:1.4; margin-top:.07in; }}
.b .rule {{ margin:.08in 0 .1in; }}
.b .cols2 {{ column-count:2; column-gap:.23in; }}
.b .blk {{ break-inside:avoid; margin-bottom:.11in; }}
.b .blk .bl {{ font-size:7pt; letter-spacing:.2em; text-transform:uppercase;
  color:#76736e; font-weight:600; display:block; margin-bottom:.04in; }}
.b .blk p {{ font-size:9.5pt; line-height:1.45; }}
.f .dev.sm {{ font-size:13.5pt; }}
.f .iast.sm {{ font-size:8.5pt; margin-top:.1in; }}
"""


def sanskrit_of(e, idx):
    # load_entries has already resolved the declared source and transliterated.
    return e["devanagari"], e["iast"]


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def front(e, idx, book_title, section_name):
    dev, iast = sanskrit_of(e, idx)
    en_lines = esc(e.get("en", "")).replace("\n", "<br>")
    n = len(e.get("en", ""))
    cls = "en" if n < 190 else ("en sm" if n < 300 else "en xs")
    left = ""
    if dev:
        long_sanskrit = len(iast or "") > 150
        dcls = "dev sm" if long_sanskrit else "dev"
        icls = "iast sm" if long_sanskrit else "iast"
        dev_p = esc(dev).replace("/", "<br>")
        left = f'<div class="{dcls}">{dev_p}</div><div class="{icls}">{esc(iast).replace("/", "<br>")}</div>'
    return f"""<section class="page f">
<div class="label">{esc(e.get('title',''))}</div>
<div class="src">{esc(e.get('source',''))} · {esc(e.get('source_ref',''))}</div>
<div class="cols"><div class="left">{left}</div><div class="right"><div class="{cls}">{en_lines}</div></div></div>
<div class="foot"><span class="sec">{esc(section_name)}</span><span class="bk">{esc(book_title)}</span></div>
</section>"""


def back(e, idx, book_title, section_name):
    blocks = []
    what = e.get("what") or e.get("logic", "")
    how = e.get("how") or e.get("howto", "")
    for label, text in (("What is it", what), ("How to perform it", how),
                        ("How to know it's working", e.get("sign", "")),
                        ("What to feel / visualise", e.get("feel", ""))):
        if text:
            blocks.append(f'<div class="blk"><span class="bl">{label}</span><p>{esc(text)}</p></div>')
    src = (e.get("source_path", "").replace("sources/", "") + " · " +
           e.get("source_ref", ""))
    return f"""<section class="page b">
<h1>{esc(e.get('title',''))}</h1>
<div class="brief">{esc(e.get('brief',''))}</div>
<div class="rule"></div>
<div class="cols2">{"".join(blocks)}</div>
<div class="foot"><span class="sec">{esc(src)}</span><span class="bk">{esc(book_title)}</span></div>
</section>"""


def build(book, ids=None, out_dir=None, draft=True, social=False, backend="chrome", book_dir=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", book):
        raise ValueError("invalid book identifier")
    book_dir = os.fspath(book_dir) if book_dir else os.path.join(PRINTS, book)
    entries = json.load(open(os.path.join(book_dir, "entries.json")))
    book_title = json.load(open(os.path.join(book_dir, "book.json")))["meta"]["title"]
    sections = {s["id"]: s.get("title", s["id"]) for s in
                json.load(open(os.path.join(book_dir, "book.json")))["sections"]}
    if ids:
        want = set(ids)
        if len(want) != len(ids):
            raise ValueError("duplicate entry ids requested")
        entries = [e for e in entries if e["id"] in want]
        missing = want - {e["id"] for e in entries}
        if missing:
            raise ValueError(f"unknown entry ids: {sorted(missing)}")
    entry_ids = [e["id"] for e in entries]
    if len(set(entry_ids)) != len(entry_ids) or any(not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", i) for i in entry_ids):
        raise ValueError("duplicate or unsafe entry id")
    if not entries:
        raise ValueError("no entries to render")
    sys.path.insert(0, PRINTS)
    from bookkit.engine import load_entries
    entries = load_entries(Path(book_dir), entries)
    idx = {}  # kept in the front/back interface for compatibility
    pages, order = [], []
    for e in entries:
        sec = sections.get(e["section"], e["section"])
        pages.append(front(e, idx, book_title, sec))
        pages.append(back(e, idx, book_title, sec))
        order.append(e["id"])
    fonts = Path(book_dir) / "fonts"
    tiro = fonts / "TiroDevanagariSanskrit-Regular.ttf"
    cormorant = fonts / "CormorantGaramond[wght].ttf"
    if not tiro.is_file() or not cormorant.is_file():
        raise FileNotFoundError("book fonts missing")
    css = CSS.replace("file://" + TIO, tiro.resolve().as_uri()).replace("file://" + COR, cormorant.resolve().as_uri())
    if draft:
        css += ".page:before{content:'DRAFT · NOT FOR SALE';position:absolute;top:.08in;right:.15in;font:6pt sans-serif;color:#9d2424;}"
    target = (Path(out_dir) if out_dir else Path(OUT) / book).resolve()
    target.mkdir(parents=True, exist_ok=True)

    def render(doc_pages, extra_css, tmp, prefix):
        doc = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}{extra_css}</style></head><body>{''.join(doc_pages)}</body></html>"
        src, pdf = tmp / (prefix + ".html"), tmp / (prefix + ".pdf")
        src.write_text(doc, encoding="utf-8")
        if backend == "weasyprint":
            from weasyprint import HTML
            HTML(filename=str(src)).write_pdf(str(pdf))
        else:
            chrome = os.environ.get("BOOKFACTORY_CHROME") or shutil.which("google-chrome-stable") or shutil.which("chromium")
            if not chrome:
                raise RuntimeError("Chrome/Chromium missing; set BOOKFACTORY_CHROME")
            subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--disable-crash-reporter", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", src.as_uri()], check=True, timeout=180, capture_output=True)
        info = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True, text=True).stdout
        count = re.search(r"Pages:\s+(\d+)", info)
        if not count or int(count.group(1)) != len(doc_pages):
            raise RuntimeError(f"unexpected pagination for {prefix}")
        subprocess.run(["pdftoppm", "-r", "300", "-png", str(pdf), str(tmp / prefix)], check=True, capture_output=True)
        return [tmp / f"{prefix}-{i:0{len(str(len(doc_pages)))}d}.png" for i in range(1, len(doc_pages)+1)]

    # Render in isolation; only replace this selection after all files succeed.
    with tempfile.TemporaryDirectory(prefix=".bookfactory-postcards-", dir=target) as work:
        tmp = Path(work)
        files = render(pages, "", tmp, "card")
        products = [(files[2*i+j], f"{eid}__{side}.png", (1800, 1200)) for i,eid in enumerate(order) for j,side in enumerate(("front", "back"))]
        if social:
            for label, height in (("square", 3.6), ("portrait", 4.5)):
                overrides = f"""@page{{size:3.6in {height}in;margin:0}}
.page{{width:3.6in;height:{height}in;padding:.3in .28in;}}
.f .cols{{height:{height-1.15}in;gap:.12in;margin-top:.1in;}}
.f .left{{width:46%}} .f .dev{{font-size:12pt}} .f .dev.sm{{font-size:10pt}}
.f .iast{{font-size:7.5pt}} .f .iast.sm{{font-size:7pt}}
.f .en{{font-size:11pt}} .f .en.sm{{font-size:9pt}} .f .en.xs{{font-size:8pt}}
.f .foot{{left:.28in;right:.28in;bottom:.2in}}"""
                rendered = render(pages[::2], overrides, tmp, label)
                size = (1080, 1080 if label == "square" else 1350)
                products += [(rendered[i], f"{eid}__social-{label}.png", size) for i,eid in enumerate(order)]
        from PIL import Image
        for src, name, size in products:
            if not src.is_file():
                raise RuntimeError(f"missing rendered page: {src.name}")
            with Image.open(src) as image:
                if image.format != "PNG" or image.size != size:
                    raise RuntimeError(f"{name}: unexpected image format or dimensions {image.size}; expected PNG {size}")
                dpi = image.info.get("dpi", (0, 0))
                if min(dpi) < 299 or max(dpi) > 301:
                    raise RuntimeError(f"{name}: missing or incorrect 300 dpi metadata: {dpi}")
                image.verify()
        for src, name, size in products:
            os.replace(src, target / name)
        if not social:
            # These belong to the selected entry but were not regenerated;
            # preserve every unselected entry and remove only its stale sides.
            for eid in order:
                for suffix in ("social-square", "social-portrait"):
                    (target / f"{eid}__{suffix}.png").unlink(missing_ok=True)
    print(f"{book}: {len(order)} selected cards -> {len(products)} PNGs in {target}")
    print("Existing unselected cards were preserved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book")
    parser.add_argument("ids", nargs="*")
    parser.add_argument("--output", help="output directory; existing other entries are preserved")
    parser.add_argument("--draft", action="store_true", default=True, help="mark previews as not for sale (the CLI currently produces drafts only)")
    parser.add_argument("--social", action="store_true", help="also render 1080x1080 and 1080x1350")
    parser.add_argument("--backend", choices=("chrome", "weasyprint"), default="chrome", help="weasyprint is an experimental preview backend")
    parser.add_argument("--book-dir", help="explicit bookkit data directory for an isolated draft")
    args = parser.parse_args()
    if args.book == "all":
        if args.ids or args.output or args.book_dir:
            parser.error("all cannot be combined with ids, --output or --book-dir")
        for book in ("practical-prayers", "tantric-prayer"):
            build(book, draft=args.draft, social=args.social, backend=args.backend)
    else:
        build(args.book, args.ids or None, args.output, args.draft, args.social, args.backend, args.book_dir)
