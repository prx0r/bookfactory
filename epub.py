#!/usr/bin/env python3
"""Reflowable EPUB3 builder for bookkit books (KDP/Kindle-ready).

Reuses the bookkit engine (same entries, same derived Devanagari, same CSS
classes) and emits a valid EPUB3: stored mimetype first, container, OPF,
EPUB3 nav + legacy NCX (Kindle), embedded OFL fonts (Tiro for Devanagari),
one chapter per section, intro/afterword chapters from front/back.html.

Usage: factory.py epub --book <slug>     (see factory.py CLI)
Build: prints/<book>/<book>.epub
"""
import html
import io
import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PRINTS = Path(__import__('os').environ.get('BOOKFACTORY_PRINTS', ROOT / 'prints'))

REFLOW_OVERRIDES = """
/* reflow overrides — undo the print-sheet geometry */
html,body{background:#fff;margin:0;padding:0}
body{font-size:1em;line-height:1.5}
.page{width:auto!important;min-height:auto!important;margin:0 0 2em!important;
  padding:0!important;box-shadow:none!important;position:static!important;
  page-break-after:auto!important;background:none!important}
.spread{display:block!important;gap:0!important;flex-wrap:nowrap!important;margin:0!important}
.pnum,.draft-mark{display:none!important}
.epi .lines,.prayer .dev,.prayer .iast,.prayer .en,.prayer h3{text-align:left}
.prayer .dev{margin:.4em 0 .2em;white-space:normal}
.prayer .en{margin:.6em 0 0}
.guide{border-top:1px solid #d9d5cc;padding-top:1em;margin-top:1.5em}
.toc ol{column-count:1}
h2.blk{margin-top:1.4em}
"""

_XHTML = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head><meta charset="utf-8"/><title>{title}</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
{body}
</body></html>"""


def _sanitize_fragment(frag):
    """HTML-isms in authored front/back matter are illegal in XML."""
    frag = re.sub(r'<br\s*/?>', '<br/>', frag, flags=re.I)
    frag = re.sub(r'<hr\s*/?>', '<hr/>', frag, flags=re.I)
    frag = re.sub(r'&nbsp;', '&#160;', frag, flags=re.I)
    frag = re.sub(r'<img\b([^>]*?)/?>', r'<img\1/>', frag, flags=re.I)
    return frag


def _split_sections(fragment):
    """front/back.html are raw <section> fragments — split into chunks."""
    parts = re.split(r'(?=<section\b)', fragment)
    return [_sanitize_fragment(p.strip()) for p in parts if p.strip()]


def _slug(s, n):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:40] + f'-{n}'


def _entry_html(e, esc):
    en = ''.join(f'<p class="ln">{esc(l)}</p>' for l in e['en'].split('\n'))
    guide = [f'<div class="guide">',
             f'<div class="label">The Guide</div>',
             f'<h3>{esc(e.get("title",""))}</h3>',
             f'<div class="src">{esc(e.get("source",""))} · {esc(e.get("source_ref",""))}</div>']
    if e.get('brief'):
        guide.append(f'<div class="brief">{esc(e["brief"])}</div>')
    for label, key, alt in (("What is it", 'what', 'logic'),
                            ("How to perform it", 'how', 'howto'),
                            ("How to know it's working", 'sign', None),
                            ("What to feel / visualise", 'feel', None)):
        text = e.get(key) or (e.get(alt) if alt else None)
        if text:
            guide.append(f'<div class="blk"><span class="bl">{label}</span><p>{esc(text)}</p></div>')
    guide.append('</div>')
    return (f'<section class="entry">'
            f'<div class="src">{esc(e.get("source",""))}</div>'
            f'<h3>{esc(e.get("title",""))}</h3>'
            f'<div class="dev">{esc(e.get("devanagari",""))}</div>'
            f'<div class="iast">{esc(e.get("iast",""))}</div>'
            f'<div class="en">{en}</div>'
            + ''.join(guide) + '</section>')


def build(book_dir, out_path=None):
    """Build <book>.epub. Returns stats dict; raises ValueError on failure."""
    import sys
    book_dir = Path(book_dir)
    sys.path.insert(0, str(book_dir.parent / 'bookkit'))
    try:
        import engine
        entries = engine.load_entries(book_dir, __import__('json').loads(
            (book_dir / 'entries.json').read_text(encoding='utf-8')))
        css = engine.CSS
        esc = engine.esc
        book = __import__('json').loads((book_dir / 'book.json').read_text(encoding='utf-8'))
    finally:
        sys.path.pop(0)
    meta = book['meta']
    sections = book['sections']
    title = meta['title']
    out_path = Path(out_path) if out_path else book_dir / f'{book_dir.name}.epub'

    # ---- chapters: [(filename, nav_label, body_html)] ----
    chapters = []
    cover_body = (f'<section class="page cover" style="text-align:center">'
                  f'<div class="om" style="font-family:Tiro;font-size:4em">ॐ</div>'
                  f'<h1 style="font-size:2em;text-transform:uppercase">{html.escape(title)}</h1>'
                  f'<div class="sub" style="font-style:italic">{html.escape(meta.get("subtitle",""))}</div>'
                  f'<div class="rule" style="width:40mm;height:1px;background:#17140f;margin:2em auto"></div>'
                  f'<div class="blurb" style="letter-spacing:.1em">{html.escape(meta.get("blurb",""))}</div>'
                  f'</section>')
    chapters.append(('cover.xhtml', title, cover_body))

    for i, chunk in enumerate(_split_sections((book_dir / 'front.html').read_text(encoding='utf-8')), 1):
        label = re.sub(r'<[^>]+>', '', re.search(r'<h2[^>]*>(.*?)</h2>', chunk, re.S).group(1)) if re.search(r'<h2[^>]*>(.*?)</h2>', chunk, re.S) else f'Introduction {i}'
        chapters.append((f'intro-{i:02d}.xhtml', ' '.join(label.split())[:60], chunk))

    for si, s in enumerate(sections, 1):
        body = [f'<section class="page sec-div"><div class="num">{html.escape(s.get("numeral",""))}</div>'
                f'<h2>{html.escape(s["title"])}</h2>'
                f'<div class="sub">{html.escape(s.get("sub",""))}</div></section>']
        for e in [x for x in entries if x['section'] == s['id']]:
            body.append(_entry_html(e, esc))
        chapters.append((f'section-{si:02d}.xhtml', s['title'], ''.join(body)))

    for i, chunk in enumerate(_split_sections((book_dir / 'back.html').read_text(encoding='utf-8')), 1):
        label = re.search(r'<h2[^>]*>(.*?)</h2>', chunk, re.S)
        label = ' '.join(re.sub(r'<[^>]+>', '', label.group(1)).split()) if label else f'Afterword {i}'
        chapters.append((f'afterword-{i:02d}.xhtml', label[:60], chunk))

    sources = ''.join(f'<li>{html.escape(p)}</li>' for p in
                      sorted({e.get('source_path','') for e in entries if e.get('source_path')}))
    chapters.append(('sources.xhtml', 'Sources',
                     '<section class="page bib"><h2>Sources</h2><ul>' + sources + '</ul></section>'))

    # ---- package files ----
    files = {}
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    book_id = f'urn:uuid:{uuid.uuid4()}'

    nav_items = ''.join(
        f'<li><a href="{f}">{html.escape(label)}</a></li>' for f, label, _ in chapters)
    files['nav.xhtml'] = (f'<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">\n'
        '<head><meta charset="utf-8"/><title>Contents</title></head>\n<body>\n'
        '<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>' + nav_items + '</ol></nav>\n'
        '<nav epub:type="landmarks" hidden="hidden"><ol>'
        '<li><a epub:type="cover" href="cover.xhtml">Cover</a></li>'
        '<li><a epub:type="toc" href="nav.xhtml">Contents</a></li></ol></nav>\n'
        '</body></html>')

    ncx_items = ''.join(
        f'<navPoint id="np{i}" playOrder="{i}"><navLabel><text>{html.escape(label)}</text>'
        f'</navLabel><content src="{f}"/></navPoint>'
        for i, (f, label, _) in enumerate(chapters, 1))
    files['toc.ncx'] = (f'<?xml version="1.0" encoding="utf-8"?>\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
        f'<head><meta name="dtb:uid" content="{book_id}"/></head>'
        '<docTitle><text>' + html.escape(title) + '</text></docTitle><navMap>'
        + ncx_items + '</navMap></ncx>')

    manifest = []
    spine = []
    for i, (f, _, _) in enumerate(chapters, 1):
        mid = f'ch{i}'
        manifest.append(f'<item id="{mid}" href="{f}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{mid}"/>')
    font_items = []
    fonts_dir = book_dir / 'fonts'
    for fp in sorted(fonts_dir.glob('*.ttf')) if fonts_dir.is_dir() else []:
        files[f'fonts/{fp.name}'] = fp.read_bytes()
        fid = f'f{len(font_items)}'
        font_items.append(f'<item id="{fid}" href="fonts/{fp.name}" media-type="font/ttf"/>')
    files['style.css'] = css + REFLOW_OVERRIDES

    files['package.opf'] = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="en">'
        f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        f'<dc:title>{html.escape(title)}</dc:title>'
        f'<dc:language>en</dc:language>'
        f'<dc:identifier id="bookid">{book_id}</dc:identifier>'
        f'<dc:description>{html.escape(meta.get("subtitle",""))}</dc:description>'
        f'<meta property="dcterms:modified">{now}</meta>'
        f'<meta name="cover" content="cover-image"/>'
        '</metadata>'
        '<manifest>'
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
        '<item id="css" href="style.css" media-type="text/css"/>'
        + ''.join(font_items) + ''.join(manifest) +
        '</manifest>'
        '<spine toc="ncx">' + ''.join(spine) + '</spine>'
        '</package>')

    for f, _, body in chapters:
        files[f] = _XHTML.format(title=html.escape(f), body=body)

    # ---- write epub (mimetype first, stored) ----
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, 'w') as z:
        z.writestr(zipfile.ZipInfo('mimetype'), 'application/epub+zip',
                   compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml',
                   '<?xml version="1.0" encoding="utf-8"?>\n'
                   '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                   '<rootfiles><rootfile full-path="OEBPS/package.opf" '
                   'media-type="application/oebps-package+xml"/></rootfiles></container>',
                   compress_type=zipfile.ZIP_DEFLATED)
        for name, data in files.items():
            payload = data if isinstance(data, bytes) else data.encode('utf-8')
            z.writestr(f'OEBPS/{name}', payload, compress_type=zipfile.ZIP_DEFLATED)
    return {'epub': str(out_path), 'chapters': len(chapters), 'entries': len(entries),
            'bytes': out_path.stat().st_size}


def validate(epub_path):
    """Structural EPUB3 checks — returns list of problems ([] = valid)."""
    problems = []
    try:
        z = zipfile.ZipFile(epub_path)
    except (OSError, zipfile.BadZipFile) as exc:
        return [f'not a zip/epub: {exc}']
    with z:
        names = z.namelist()
        if not names or names[0] != 'mimetype':
            problems.append(f'mimetype must be first entry (got {names[:1]})')
        elif z.getinfo('mimetype').compress_type != zipfile.ZIP_STORED:
            problems.append('mimetype must be STORED (uncompressed)')
        elif z.read('mimetype') != b'application/epub+zip':
            problems.append('mimetype content wrong')
        required = ['META-INF/container.xml', 'OEBPS/package.opf', 'OEBPS/nav.xhtml']
        for r in required:
            if r not in names:
                problems.append(f'missing {r}')
        if problems:
            return problems
        # XML well-formedness
        for n in names:
            if n.endswith(('.xhtml', '.opf', '.ncx', '.xml')):
                try:
                    ET.fromstring(z.read(n))
                except ET.ParseError as exc:
                    problems.append(f'{n}: XML parse error: {exc}')
        # manifest hrefs exist
        opf = z.read('OEBPS/package.opf').decode('utf-8')
        for href in re.findall(r'href="([^"]+)"', opf):
            if not href.startswith(('http', '#')) and f'OEBPS/{href}' not in names:
                problems.append(f'opf manifest href missing in zip: {href}')
        # spine refs exist in manifest
        spine_ids = re.findall(r'<itemref idref="([^"]+)"', opf)
        man_ids = set(re.findall(r'<item id="([^"]+)"', opf))
        for sid in spine_ids:
            if sid not in man_ids:
                problems.append(f'spine idref not in manifest: {sid}')
        # font files present if css references them
        css = z.read('OEBPS/style.css').decode('utf-8')
        for furl in re.findall(r"url\('([^']+)'\)", css):
            if f'OEBPS/{furl}' not in names:
                problems.append(f'css references missing file: {furl}')
    return problems


if __name__ == '__main__':
    import sys
    b = Path(sys.argv[1])
    stats = build(b)
    print(stats)
    probs = validate(stats['epub'])
    print('VALID' if not probs else 'PROBLEMS:')
    for p in probs:
        print(' x', p)
    sys.exit(1 if probs else 0)
