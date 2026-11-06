# lane template

Copy to `projects/<text>/` then fill:

- `lane.py` — one dict `LANE`:
  ```python
  LANE = {
    "text": "<name>",                 # upstream dir in ~/repos/translation-work
    "source_paths": {"<layer>": "<relative file or glob>"},
    "id_map": None,                   # future explicit literal verse -> entry map
    "entries_from": "L3",             # L3 | L2 | L200
    "gate_file": "<text>/GATE.json",  # None only while gate is unrun
    "sections": [...],                # book.json section plan
    "products": ["paperback", "postcard", "social"],
    "book_dir": None,                 # None until the lane is wired to a book dir under prints/
  }
  ```
- `project.json` — outputs wanted + any owner adjudications (verbatim).

The core reads a literal `LANE` dictionary using `ast.literal_eval`; executable
lane code and callable mappings are not supported. Mapping, decisions and
rights are not yet a production gate. Queued lanes stay blocked until that
gate is implemented rather than becoming canonical merely because paths exist.
