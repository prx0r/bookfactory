#!/usr/bin/env python3
"""font_sampler.py — contact sheet: the Brahmārpaṇam English line rendered in
every candidate font, labelled, for choosing the verse typeface."""
import os, sys
from PIL import Image, ImageDraw, ImageFont

FONTS = [
    ("Cormorant Garamond Medium (current)", "/root/.fonts/CormorantGaramond[wght].ttf", 500),
    ("EB Garamond", "/root/.fonts/EBGaramond.ttf", None),
    ("Source Serif 4", "/root/.fonts/SourceSerif4[opsz,wght].ttf", 400),
    ("Spectral", "/root/.fonts/Spectral-Regular.ttf", None),
    ("Marcellus (roman caps feel)", "/root/.fonts/Marcellus-Regular.ttf", None),
    ("Rozha One (display)", "/root/.fonts/RozhaOne-Regular.ttf", None),
    ("Playfair Display Italic", "/root/.fonts/PlayfairDisplay-Italic[wght].ttf", 500),
]
LINE = "śiva alone, by himself, attains the goal,"
LINE2 = "whatever i take is offered to śiva;"
W, ROW = 1600, 170
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "outputs", "print_products", "brahmarpanam", "font_sampler.png")

img = Image.new("RGB", (W, ROW * len(FONTS) + 40), (255, 255, 255))
d = ImageDraw.Draw(img)
lbl = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
y = 20
for name, path, weight in FONTS:
    f = ImageFont.truetype(path, 54)
    if weight:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    d.text((40, y + 6), name, font=lbl, fill=(140, 60, 60))
    d.text((40, y + 46), LINE2, font=f, fill=(23, 20, 15))
    d.text((40, y + 104), LINE, font=f, fill=(23, 20, 15))
    y += ROW
os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT, optimize=True)
print("saved", OUT, img.size)
