# AGENTS.md — bookfactory

Read FACTORY-SPEC.md first. One-liner: translation layers in, gated print
products out. The renderer lives in ~/visuals/prints (bookkit); this repo
owns lanes, gates and the quote loop — not typography.

## Layout
- FACTORY-SPEC.md — the law (position, products, layer stack, bars, migration)
- REGISTRY.json — live lanes + milestones (update on every state change)
- check.py — the only gate; exit 0 = canonical
- projects/<text>/ — one lane per text: `lane.py` (data paths + id map + section
  plan) + `project.json` (outputs wanted)
- projects/_template/ — copy this to start a lane

## Commands
```bash
python3 check.py                        # whole registry
python3 check.py practical-prapers      # one lane   (NOTE: lane dirs are spelled
                                         # as the visuals book dirs)
# build (renderer side, unchanged):
cd ~/visuals/prints/<book> && python3 <book>/compile.py   # needs patala venv
python3 ~/visuals/prints/kdp_preflight.py <pdf>
python3 ~/visuals/prints/postcards/render_postcards.py <book> [ids...]
```

## Rules
1. No retyped text. Strings come from layer files; fix upstream, rebuild.
2. Devanagari is transliterated from IAST at build; never hand-written bytes.
3. Verdicts: `pdftotext`/`pdfinfo` only. The image-read tool is not evidence.
4. Anything >10s is a background job (`setsid nohup` + own log + notify-send).
5. GATE.json BLOCKED = verse does not ship, no exceptions without a recorded
   owner adjudication (put the ruling in the lane's project.json).
6. KDP Select off; free ISBN first; covers via Cover Calculator at upload.
7. Copyright: our English only. Lakshmanjoo/Dyczkowski prose never printed;
   trust material = brief attributed quote in front matter.
