# STYLE — house voice & page-as-art (owner law)

Two things the owner locked and every rebuild must honour:

## 1. Translation voice (owner English)

Sharp, logical, exact — Trika-aware without mysticism. Models:

**Gītā 4.24 (meal prayer)** — `prints/prayers/brahmarpanam.json`:
> whatever i take is offered to śiva;
> what i offer is itself śiva;
> in the fire that is śiva, offered by śiva;
> śiva alone, by himself, attains the goal — all activity is śiva

**Other owner lines (PP entries — leave untouched unless owner rewrites):**
- *somananda:* śiva, having entered the form that is myself, bows — by his own power — to śiva, for the removal of the obstacle that is himself.
- *mpa-8:* enough of difference-talk — chewing the sap of devotion to you: all this is one, at peace; and even to say so feels shy.

Rules of the voice:
- English first as **what the words warrant**; Trika reading second, attributed.
- Concrete, lowercase where the owner writes lowercase (śiva in meal lines).
- No somatic success tests, no “guaranteed” sensations (see `EXPLAINER.md`).
- Guide fields follow `EXPLAINER.md` (When / Act / Turn / Return).
- Source text (Sanskrit/IAST) never rewritten; only our English.

## 2. Prayer page = full-page art

From engine `bookkit/engine.py` (house default):
- **Full `.page`**, content **vertically + horizontally centred**
- Source label top (tracked caps) · title · hairline rule
- **Devanagari maximised** — `dev_size` tiers 54→16pt, budget **380pt**
  (owner art-page fill, not a caption)
- IAST + English centred under; page number low
- Black KDP wrap remains `cover-canonical` (Svatantrya centre back)

Tune live: `http://127.0.0.1:8610/layout?book=practical-prayers`
(tokens → `prints/<book>/layout.json` → engine override).

## Pipeline note

Changing `en` = content edit (`entries.json`) → rebuild via `compile.py` →
`check.py <book>`. Changing layout tokens = `layout.json` only (no content law).
