#!/usr/bin/env python3
"""Inspect an A5, no-bleed KDP paperback interior PDF.

Checks every page's dimensions, embedded fonts, rendered text size and margins,
and image effective resolution. This is a mechanical gate, not a KDP approval,
proofreading, rights review, cover check, or a check for text clipped before PDF
creation. Requires PyMuPDF and Poppler's pdffonts. Use KDP's current calculator
and previewer for the separate cover and final submission.
"""
import argparse
import math
import re
import subprocess
import sys

A5 = (148 / 25.4 * 72, 210 / 25.4 * 72)
TOLERANCE_PT = .72  # .01in: account for the renderer's rounding


def gutter(pages):
    if pages <= 150: return .375 * 72
    if pages <= 300: return .5 * 72
    if pages <= 500: return .625 * 72
    if pages <= 700: return .75 * 72
    return .875 * 72


def preflight(path, max_pages=None):
    try:
        import fitz
    except ImportError:
        return ["PyMuPDF missing; install prints/requirements-publishing.txt"], []
    fails, warns = [], []
    try:
        doc = fitz.open(path)
    except Exception as exc:
        return [f"cannot open PDF: {exc}"], []
    with doc:
        if not doc.is_pdf or doc.needs_pass:
            return ["not an accessible PDF"], []
        pages = len(doc)
        if not 24 <= pages <= 828:
            fails.append(f"{pages} pages: A5 black ink on white paper must be 24–828")
        if max_pages is not None and pages > max_pages:
            fails.append(f"{pages} pages exceeds project ceiling {max_pages}")
        if pages % 2:
            warns.append(f"{pages} pages: KDP rounds to {pages + 1}")
        try:
            result = subprocess.run(["pdffonts", path], capture_output=True, text=True, check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            return [f"pdffonts failed: {exc}"], warns
        lines = result.stdout.splitlines()[2:]
        if not lines:
            fails.append("no PDF fonts found; cannot verify text or font embedding")
        for line in lines:
            m = re.search(r"\s(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$", line)
            if not m:
                fails.append(f"unrecognised pdffonts row: {line[:120]}")
            elif m.group(1) != "yes":
                fails.append(f"font not embedded: {line.split()[0]}")
        small, out, lowres = [], [], []
        text_spans = 0
        for i, page in enumerate(doc):
            width, height = page.rect.width, page.rect.height
            if abs(width - A5[0]) > TOLERANCE_PT or abs(height - A5[1]) > TOLERANCE_PT:
                fails.append(f"page {i+1}: {width:.2f}×{height:.2f}pt, expected A5")
            left = gutter(pages) if i % 2 == 0 else 18
            right = 18 if i % 2 == 0 else gutter(pages)
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        if not span["text"].strip():
                            continue
                        text_spans += 1
                        if span["size"] < 7 - 0.01:
                            small.append((i + 1, span["size"]))
                        x0, y0, x1, y1 = span["bbox"]
                        if x0 < left - .2 or x1 > width - right + .2 or y0 < 18 - .2 or y1 > height - 18 + .2:
                            out.append(i + 1)
            for image in page.get_image_info():
                a, b, c, d, _, _ = image["transform"]
                xpt, ypt = math.hypot(a, b), math.hypot(c, d)
                if not xpt or not ypt:
                    lowres.append((i + 1, 0, 0))
                else:
                    xp, yp = image["width"] * 72 / xpt, image["height"] * 72 / ypt
                    if min(xp, yp) < 299.5:
                        lowres.append((i + 1, round(xp), round(yp)))
        if not text_spans:
            fails.append("no extractable text; cannot verify sizes and margins")
        if small:
            fails.append(f"{len(small)} text spans below 7pt; smallest {min(x[1] for x in small):.2f}pt; first page {small[0][0]}")
        if out:
            fails.append(f"{len(out)} text spans outside KDP margins; pages {sorted(set(out))[:20]}")
        if lowres:
            fails.append(f"images below 300ppi: {lowres[:10]} (page, x-ppi, y-ppi)")
    return fails, warns


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", nargs="+")
    parser.add_argument("--max-pages", type=int, help="optional project-specific ceiling")
    args = parser.parse_args()
    rc = 0
    for path in args.pdf:
        fails, warns = preflight(path, args.max_pages)
        print(f"[{'FAIL' if fails else 'PASS'}] {path}")
        for message in fails: print(f"    x {message}")
        for message in warns: print(f"    ! {message}")
        rc |= bool(fails)
    print("Mechanical checks only; review content, rights, cover and KDP preview separately.")
    return int(rc)


if __name__ == "__main__":
    sys.exit(main())
