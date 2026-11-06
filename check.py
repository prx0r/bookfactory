#!/usr/bin/env python3
"""Fail-closed publishing gate. A queued or unproved lane is not canonical."""
import argparse
import ast
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
DEFAULT_VISUALS=Path(os.environ.get('BOOKFACTORY_VISUALS',ROOT.parent/'visuals'))
DEFAULT_TRANSLATIONS=Path(os.environ.get('BOOKFACTORY_TRANSLATIONS',ROOT.parent/'translation-work'))


def lane_config(path):
    tree=ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.Assign) or len(tree.body[0].targets)!=1 or not isinstance(tree.body[0].targets[0],ast.Name) or tree.body[0].targets[0].id!='LANE':
        raise ValueError('lane.py must contain only a literal LANE assignment')
    value=ast.literal_eval(tree.body[0].value)
    if not isinstance(value,dict): raise ValueError('LANE must be a dictionary')
    return value


def check_lane(name, spec, visuals, translations, pdf_override=None):
    errors=[]
    book_id=spec.get('book_dir')
    if not book_id:
        errors.append('queued lane: no book, verse-to-gate mapping, production rights or proof configured')
        return errors
    prints=(visuals/'prints').resolve()
    book=(prints/book_id).resolve()
    if not book.is_relative_to(prints) or not book.is_dir():
        return [f'book directory missing or outside visuals: {book_id}']
    try:
        entries=json.loads((book/'entries.json').read_text(encoding='utf-8'))
        book_data=json.loads((book/'book.json').read_text(encoding='utf-8'))
    except (OSError,ValueError) as exc:
        return [f'cannot load book data: {exc}']
    if not isinstance(entries,list) or not entries:
        return ['entries.json must be a nonempty list']
    ids=[]
    for e in entries:
        if not isinstance(e,dict):
            errors.append('entry is not an object'); continue
        entry_id=e.get('id')
        if not isinstance(entry_id,str) or not entry_id:
            errors.append('entry missing id'); continue
        ids.append(entry_id)
        for field in ('title','source','source_ref','source_path','en'):
            if not isinstance(e.get(field),str) or not e[field].strip():
                errors.append(f'{entry_id}: missing {field}')
        if not e.get('iast') and not e.get('corpus'):
            errors.append(f'{entry_id}: missing IAST/corpus reference')
        source=e.get('source_path')
        if isinstance(source,str) and source:
            path=(book/source).resolve()
            if Path(source).is_absolute() or not path.is_relative_to(book) or not path.is_file():
                errors.append(f'{entry_id}: source path missing or outside book')
    if len(ids)!=len(set(ids)): errors.append('duplicate entry ids')
    # The legacy entries do not yet bind each entry's exact text to a specific
    # upstream passage, recorded decision, rights evidence and reviewed revision.
    # Their prose gate_note is not a machine-verifiable owner adjudication.
    errors.append(f'{len(entries)} entries lack a verified per-entry source, gate, rights and review handoff')
    art=book_data.get('opening_image')
    if art:
        if not isinstance(art,dict):
            errors.append('opening artwork record must be an object')
        elif art.get('draft_only',True): errors.append('opening artwork is draft-only or has no rights evidence')
        if not isinstance(art,dict) or not art.get('manifest'): errors.append('opening artwork has no asset manifest')
        # Until the production gate verifies artwork rights and asset hashes,
        # an opening image must never accidentally become a shippable PDF.
        errors.append('opening artwork requires asset provenance and rights review')
    pdf=Path(pdf_override) if pdf_override else book/f'{book_id}-preview.pdf'
    preflight=prints/'kdp_preflight.py'
    project=ROOT/'projects'/name/'project.json'
    settings=json.loads(project.read_text(encoding='utf-8')) if project.is_file() else {}
    ceiling=settings.get('max_pages')
    if ceiling is not None and (type(ceiling) is not int or ceiling < 24):
        errors.append('project max_pages must be an integer of at least 24')
        ceiling=None
    if not pdf.is_file(): errors.append(f'PDF proof missing: {pdf}')
    elif not preflight.is_file(): errors.append('KDP preflight missing')
    else:
        command=[sys.executable,str(preflight)]
        if ceiling is not None: command += ['--max-pages',str(ceiling)]
        result=subprocess.run(command+[str(pdf)],capture_output=True,text=True)
        if result.returncode:
            detail='; '.join(x.strip() for x in result.stdout.splitlines() if x.strip().startswith('x '))
            errors.append(f'PDF preflight failed: {detail or result.stderr.strip() or "unknown failure"}')
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lane',nargs='?')
    parser.add_argument('--visuals',type=Path,default=DEFAULT_VISUALS)
    parser.add_argument('--translations',type=Path,default=DEFAULT_TRANSLATIONS)
    parser.add_argument('--pdf',type=Path,help='specific proof for the selected lane')
    args=parser.parse_args()
    if args.pdf and not args.lane: parser.error('--pdf requires one lane')
    reg=json.loads((ROOT/'REGISTRY.json').read_text(encoding='utf-8'))
    names=list(reg['lanes'])
    if args.lane and args.lane not in names:
        print(f'[FAIL] {args.lane}: not in REGISTRY lanes');return 1
    if args.lane: names=[args.lane]
    total=0
    for name in names:
        try:
            spec=lane_config(ROOT/'projects'/name/'lane.py')
            problems=check_lane(name,spec,args.visuals.resolve(),args.translations.resolve(),args.pdf)
        except (OSError,ValueError,SyntaxError,TypeError) as exc:
            problems=[str(exc)]
        for problem in problems: print(f'[BLOCKED] {name}: {problem}')
        if not problems: print(f'[PASS] {name}: canonical')
        total+=len(problems)
    print(f'{"BLOCKED" if total else "CANONICAL"} — {total} problem(s)')
    return int(bool(total))


if __name__=='__main__': sys.exit(main())
