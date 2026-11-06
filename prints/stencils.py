#!/usr/bin/env python3
"""Stencils — geometric line-art for the prayer books.

Vector (SVG) by design: print-crisp at any size, CMYK-safe, deterministic —
better than AI raster for these small monoline glyphs. Traditional grammar:
bindu + ring + petals (maṇḍala/navāvaraṇa for the rasa yantra); homa-triangle,
candra-kalā, triśūla, dhāra-drops for the activities. Stroke 1.4, ink colour.
"""

INK = "#17140f"


def _svg(body, size=22, extra=""):
    return (f'<svg viewBox="0 0 100 100" width="{size}mm" height="{size}mm" '
            f'xmlns="http://www.w3.org/2000/svg" {extra}>'
            f'<g fill="none" stroke="{INK}" stroke-width="2.4" '
            f'stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>')


def rasa_rosette(n=0, size=26):
    n = 0 if n > 9 else n  # appendix sections (IX+) get the full rosette
    """Nine-petal rosette (navāvaraṇa grammar: bindu + ring + nine rays).
    Emphasises petal n (1..9) when given; n=0 → all equal."""
    import math
    cx = cy = 50
    parts = []
    # outer ring
    parts.append('<circle cx="50" cy="50" r="44"/>')
    # inner ring
    parts.append('<circle cx="50" cy="50" r="30"/>')
    # nine petals: lens shapes between the rings
    for i in range(9):
        a0 = (i / 9) * 2 * math.pi - math.pi / 2
        a1 = ((i + 1) / 9) * 2 * math.pi - math.pi / 2
        am = (a0 + a1) / 2
        x0, y0 = cx + 44 * math.cos(a0), cy + 44 * math.sin(a0)
        x1, y1 = cx + 44 * math.cos(a1), cy + 44 * math.sin(a1)
        xm, ym = cx + 30 * math.cos(am), cy + 30 * math.sin(am)
        # petal tip at inner ring mid, shoulders at outer ring ends
        w = 1.0
        sw = "2.4" if (n == 0 or i + 1 == n) else "1.1"
        op = "1" if (n == 0 or i + 1 == n) else "0.45"
        parts.append(
            f'<path d="M {x0:.1f} {y0:.1f} Q {xm + (ym - y0) * .1:.1f} {ym:.1f} {x1:.1f} {y1:.1f} '
            f'Q {xm - (ym - y1) * .1:.1f} {ym:.1f} {x0:.1f} {y0:.1f} Z" stroke-width="{sw}" opacity="{op}"/>')
    # nine rays from inner to centre
    for i in range(9):
        a = (i / 9) * 2 * math.pi - math.pi / 2
        x, y = cx + 30 * math.cos(a), cy + 30 * math.sin(a)
        sw = "2.4" if (n == 0 or i + 1 == n) else "1.1"
        op = "1" if (n == 0 or i + 1 == n) else "0.45"
        parts.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{cx}" y2="{cy}" stroke-width="{sw}" opacity="{op}"/>')
    # bindu
    parts.append('<circle cx="50" cy="50" r="6" fill="' + INK + '" stroke="none"/>')
    return _svg("".join(parts), size)


def activity_glyph(key, size=20):
    """Small monoline stencil per Practical Prayers section."""
    G = {
        # dawn: sun crest over horizon
        "wake": '<path d="M18 66 A32 32 0 0 1 82 66"/><line x1="10" y1="76" x2="90" y2="76"/><circle cx="50" cy="52" r="4" fill="#17140f" stroke="none"/>',
        # bath: three falling drops
        "bath": '<path d="M35 18 Q42 32 35 34 Q28 32 35 18"/><path d="M60 40 Q67 54 60 56 Q53 54 60 40"/><path d="M42 64 Q49 78 42 80 Q35 78 42 64"/>',
        # social: two interlocking circles (maṇḍala of union)
        "social": '<circle cx="38" cy="50" r="24"/><circle cx="62" cy="50" r="24"/>',
        # work: the angle of action — two strokes meeting, bindu in the corner
        "work": '<path d="M24 76 L24 30 L70 30"/><circle cx="38" cy="44" r="4.5" fill="#17140f" stroke="none"/>',
        # food: homa flame in the pit
        "food": '<path d="M28 78 L72 78 L50 30 Z"/><path d="M50 60 Q44 52 50 44 Q56 52 50 60"/>',
        # waiting: the open spiral — paused turn
        "wait": '<path d="M50 50 m0 -6 a6 6 0 1 1 -6 6 a14 14 0 1 0 14 -14 a24 24 0 1 1 -24 24"/>',
        # negative: descending triangle (the downward pull)
        "negative": '<path d="M22 30 L78 30 L50 80 Z"/>',
        # sick: the body-temple — square with bindu
        "sick": '<rect x="26" y="26" width="48" height="48"/><circle cx="50" cy="50" r="6" fill="#17140f" stroke="none"/>',
        # positive: eight-petal bloom
        "positive": '<circle cx="50" cy="50" r="14"/><path d="M50 10 Q60 30 50 36 Q40 30 50 10 M90 50 Q70 60 64 50 Q70 40 90 50 M50 90 Q40 70 50 64 Q60 70 50 90 M10 50 Q30 40 36 50 Q30 60 10 50"/>',
        # alone: one bindu alone inside the circle
        "alone": '<circle cx="50" cy="50" r="30"/><circle cx="50" cy="50" r="5" fill="#17140f" stroke="none"/>',
        # flatness: the level plane — horizon with resting bindu
        "flatness": '<line x1="14" y1="58" x2="86" y2="58"/><circle cx="50" cy="44" r="5" fill="#17140f" stroke="none"/>',
        # gratitude: the receiving bowl with a drop arriving
        "gratitude": '<path d="M24 44 Q50 84 76 44"/><path d="M50 16 Q57 30 50 32 Q43 30 50 16"/><line x1="50" y1="36" x2="50" y2="42"/>',
        # sleep: candra-kalā (crescent of Śiva)
        "sleep": '<path d="M64 22 A34 34 0 1 0 64 78 A26 26 0 1 1 64 22 Z"/>',
        # sangha: triśūla — the three Aghora energies
        "sangha": '<line x1="50" y1="86" x2="50" y2="34"/><path d="M30 42 L30 16 L50 34 L70 16 L70 42"/><circle cx="50" cy="86" r="0"/>',
    }
    return _svg(G[key], size)


ACTIVITY_KEYS = ["wake", "bath", "social", "work", "food", "wait",
                 "negative", "sick", "positive", "sleep", "sangha"]
