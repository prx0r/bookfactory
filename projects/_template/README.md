# lane template

Copy to `projects/<text>/` then fill:

- `lane.py` — one dict `LANE`:
  ```python
  LANE = {
    "text": "<name>",                 # upstream dir in ~/repos/translation-work
    "source_paths": {"<layer>": "<relative file or glob>"},
    "id_map": None,                   # or callable verse -> entries id
    "entries_from": "L3",             # L3 | L2 | L200
    "gate_file": "<text>/GATE.json",  # None only while gate is unrun
    "sections": [...],                # book.json section plan
    "products": ["paperback", "postcard", "social"],
    "book_dir": None,                 # None until parity lane wired to visuals
  }
  ```
- `project.json` — outputs wanted + any owner adjudications (verbatim).

The core reads LANE, never guesses paths.
