#!/usr/bin/env python3
"""Produce a *candidate* entries JSON from proposals; does not modify source tree.
Usage: python apply_preview.py /path/to/bookfactory [output_file]
"""
from pathlib import Path
import sys,json
if len(sys.argv)<2:
    raise SystemExit("Usage: python apply_preview.py /path/to/bookfactory [output_file]")
repo=Path(sys.argv[1]).resolve()
src=repo/'prints/practical-prayers/entries.json'
proposals=json.loads((Path(__file__).resolve().parent/'03_content_overlay_proposals.json').read_text(encoding='utf-8'))
original=json.loads(src.read_text(encoding='utf-8'))
assert len(original)==36, "Source has changed: stop and review, do not blindly merge"
assert set(proposals)=={e['id'] for e in original}
out=[]
for e in original:
    q=proposals[e['id']]
    x=dict(e)
    for k in ('brief','logic','howto','sign'):
        x[k]=q[k]
    # Deliberately preserve Sanskrit, source references, and author attributions.
    assert all(x.get(k)==e.get(k) for k in ('iast','corpus','source','source_ref','source_path'))
    out.append(x)
path=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else Path.cwd()/'practical-prayers.candidate-UNAPPROVED.json'
if path == src: raise SystemExit('Refusing to overwrite live entries.json')
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'UNAPPROVED PREVIEW: wrote {len(out)} records to {path}')
print('This does not satisfy witness verification, repository source-law, or KDP release gates.')
