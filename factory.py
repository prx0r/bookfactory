#!/usr/bin/env python3
"""Source-bound publishing previews and reusable artwork for bookkit.

A preview is deliberately not a shipping decision. See PIPELINE.md for the
separate text, rights, proof and owner-review requirements.
"""
import argparse
import hashlib
import html
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parent
PRINTS = Path(os.environ.get('BOOKFACTORY_PRINTS', ROOT / 'prints'))
DEFAULT_TRANSLATIONS = Path(os.environ.get('BOOKFACTORY_TRANSLATIONS', ROOT.parent / 'translation-work'))
SAFE = re.compile(r'^[a-z0-9][a-z0-9-]*$')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_schema(value, filename):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ValueError('jsonschema is required; install prints/requirements-publishing.txt') from exc
    schema = json.loads((ROOT / 'schemas' / filename).read_text(encoding='utf-8'))
    problems = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(map(str, e.path)))
    if problems:
        err = problems[0]
        raise ValueError(f"schema {filename}: {'/'.join(map(str, err.path)) or '/'}: {err.message}")


def relative_file(root, path):
    root = Path(root).resolve()
    candidate = Path(path)
    if candidate.is_absolute():
        raise ValueError('absolute paths are not permitted in manifests')
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f'missing or outside permitted root: {path}')
    return resolved


def clean_work(work):
    if not SAFE.fullmatch(work):
        raise ValueError(f'unsafe text identifier: {work!r}')
    return work


def normalized(text):
    # Only compare characters and whitespace, retaining all IAST diacritics.
    text = unicodedata.normalize('NFC', text)
    return ' '.join(''.join(c if c.isalnum() else ' ' for c in text).split())


def git_state(root, paths):
    def run(*args):
        try:
            return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    commit = run('rev-parse', 'HEAD')
    dirty = run('status', '--porcelain', '--', *[str(p) for p in paths]) if commit else None
    return {'commit': commit, 'input_files_dirty': None if dirty is None else bool(dirty)}


def record(path, root):
    root = Path(root).resolve()
    relative = Path(path).relative_to(root)
    safe_path = relative_file(root, relative)
    return {'path': relative.as_posix(), 'sha256': digest(safe_path)}


def extract(translations, text, ref, layer='l3', gate_id=None):
    text = clean_work(text)
    root = Path(translations).resolve()
    work = (root / text).resolve()
    if not work.is_relative_to(root) or not work.is_dir():
        raise ValueError(f'missing translation work: {work}')
    verse_id, sep, line_number = ref.partition(':')
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9-]*', verse_id):
        raise ValueError('ref must be an exact verse_id, optionally followed by :line')
    if sep and (not line_number.isdigit() or int(line_number) < 1):
        raise ValueError('line number must be a positive integer')
    matches = []
    for path in sorted((work / 'data').glob(f'*.{layer}.json')):
        path = relative_file(root, path.relative_to(root))
        rows = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(rows, list):
            raise ValueError(f'expected a list: {path}')
        matches.extend((path, row) for row in rows if isinstance(row, dict) and row.get('verse_id') == verse_id)
    if len(matches) != 1:
        raise ValueError(f'{verse_id}: expected one {layer} record, found {len(matches)}')
    layer_file, verse = matches[0]
    iast = verse.get('sanskrit_cite')
    lines = verse.get('lines') if layer == 'l3' else [verse.get('plain_english')]
    if not isinstance(iast, str) or not iast.strip() or not isinstance(lines, list) or not lines or not all(isinstance(x, str) and x.strip() for x in lines):
        raise ValueError(f'{verse_id}: missing IAST or translation lines')
    if sep:
        n = int(line_number)
        if n > len(lines):
            raise ValueError(f'{verse_id} has only {len(lines)} lines')
        lines = [lines[n-1]]
    source_file = work / 'SOURCE.txt'
    source_match = False
    inputs = [record(layer_file, root)]
    if source_file.is_file():
        inputs.append(record(source_file, root))
        # This is a useful comparison, not a byte-exact textual edition proof.
        needle = normalized(iast)
        source_match = bool(needle and needle in normalized(source_file.read_text(encoding='utf-8')))
    gate_status = 'unmapped'
    gate_file, passage_file = work / 'GATE.json', work / 'passages.jsonl'
    if gate_id:
        if not gate_file.is_file() or not passage_file.is_file():
            raise ValueError('an explicit gate id requires GATE.json and passages.jsonl')
        passages = [json.loads(row) for row in passage_file.read_text(encoding='utf-8').splitlines() if row.strip()]
        bound = [x for x in passages if x.get('locator') == gate_id]
        if len(bound) != 1 or not normalized(iast) or normalized(iast) not in normalized(bound[0].get('sanskrit', '')):
            raise ValueError('gate id does not unambiguously contain this Sanskrit citation')
        gate = json.loads(gate_file.read_text(encoding='utf-8')).get(gate_id)
        if not isinstance(gate, dict) or gate.get('deterministic_gate') not in ('PASS', 'BLOCKED'):
            raise ValueError('gate id has no recognised deterministic decision')
        gate_status = gate['deterministic_gate']
        inputs.extend([record(gate_file, root), record(passage_file, root)])
    state = git_state(root, [x['path'] for x in inputs])
    return {
        'version': '1.0', 'kind': 'translation-candidate', 'status': 'draft',
        'work': text, 'verse_id': verse_id, 'ref': ref, 'layer': layer,
        'iast': iast, 'english_lines': lines, 'inputs': inputs,
        'source_match': 'normalized-match' if source_match else 'unverified',
        'deterministic_gate': {'id': gate_id, 'status': gate_status},
        'human_review': 'not-established', 'commercial_rights': 'not-established',
        'needs': verse.get('needs', []), 'git': state,
    }


def candidate_for_book(prints_root, text, ref):
    text = clean_work(text)
    root = Path(prints_root).resolve()
    book = root / text
    entries_file = book / 'entries.json'
    entries = json.loads(entries_file.read_text(encoding='utf-8'))
    matches = [x for x in entries if x.get('id') == ref]
    if len(matches) != 1:
        raise ValueError(f'{ref}: expected one existing entry, found {len(matches)}')
    entry = matches[0]
    source = relative_file(book, entry['source_path'])
    return {'version':'1.0', 'kind':'book-entry', 'status':'draft', 'work':text,
            'ref':ref, 'inputs':[record(entries_file,root), record(source,root), record(book/'book.json',root)],
            'human_review':'not-established', 'commercial_rights':'not-established',
            'deterministic_gate':{'id':None,'status':'unmapped'},
            'git':git_state(root, [entries_file.relative_to(root), source.relative_to(root), (book/'book.json').relative_to(root)])}


def quote(args):
    prints_root = args.prints.resolve()
    renderer = prints_root / 'postcards/render_postcards.py'
    if not renderer.is_file():
        raise ValueError(f'missing renderer: {renderer}')
    existing = (prints_root / args.text / 'entries.json').is_file()
    c = candidate_for_book(prints_root, args.text, args.ref) if existing else extract(args.translations, args.text, args.ref, args.layer, args.gate_id)
    font_dir = prints_root / (args.text if existing else 'practical-prayers') / 'fonts'
    render_paths = [renderer, visual_root/'prints/bookkit/engine.py', visual_root/'prints/stencils.py', font_dir/'TiroDevanagariSanskrit-Regular.ttf', font_dir/'CormorantGaramond[wght].ttf']
    renderer_files = [record(relative_file(prints_root,p.relative_to(prints_root)),prints_root) for p in render_paths]
    factory_files = [record(ROOT/p,ROOT) for p in ('factory.py','schemas/quote-handoff.schema.json')]
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.bookfactory-quote-', dir=destination) as temp:
        staging = Path(temp)
        if existing:
            bookdir = prints_root / args.text
            entry_id = args.ref
        else:
            # Adapt verbatim machine-layer text into bookkit's existing entry shape;
            # explanatory fields remain empty until sourced, never invented.
            bookdir = staging / 'book'
            bookdir.mkdir()
            shutil.copytree(prints_root / 'practical-prayers/fonts', bookdir / 'fonts')
            (bookdir / 'book.json').write_text(json.dumps({'meta': {'title':args.text}, 'sections':[{'id':'text','title':args.text}]},ensure_ascii=False),encoding='utf-8')
            entry_id = c['verse_id'] + (('-line-' + args.ref.split(':')[1]) if ':' in args.ref else '')
            entry = {'id':entry_id,'section':'text','title':c['verse_id'],'source':args.text,'source_ref':c['ref'],
                     'source_path':c['inputs'][0]['path'],'iast':c['iast'],'en':'\n'.join(c['english_lines']),'brief':''}
            (bookdir / 'entries.json').write_text(json.dumps([entry],ensure_ascii=False),encoding='utf-8')
        products_dir = staging / 'products'
        cmd = [sys.executable, str(renderer), args.text, entry_id, '--book-dir',str(bookdir), '--draft', '--social', '--backend', args.backend, '--output', str(products_dir)]
        subprocess.run(cmd, check=True)
        input_root = prints_root if existing else args.translations.resolve()
        for inp in c['inputs']:
            if digest(relative_file(input_root, inp['path'])) != inp['sha256']:
                raise ValueError(f"input changed during render: {inp['path']}")
        for inp in renderer_files:
            if digest(relative_file(prints_root, inp['path'])) != inp['sha256']:
                raise ValueError(f"renderer input changed during render: {inp['path']}")
        for inp in factory_files:
            if digest(relative_file(ROOT, inp['path'])) != inp['sha256']:
                raise ValueError(f"factory input changed during render: {inp['path']}")
        outputs=[]
        for suffix in ('front','back','social-square','social-portrait'):
            p = products_dir / f'{entry_id}__{suffix}.png'
            if not p.is_file():
                raise ValueError(f'missing product {p}')
            dest_name=f'{args.text}__{entry_id}__{suffix}.png'
            outputs.append({'path':dest_name,'sha256':digest(p)})
            os.replace(p, destination / dest_name)
        index_name=f'{args.text}__{entry_id}__index.html'
        index=products_dir/index_name
        images=''.join(f'<figure><figcaption>{html.escape(o["path"])}</figcaption><img src="{html.escape(o["path"],quote=True)}" style="max-width:100%;height:auto"></figure>' for o in outputs)
        index.write_text(f'<!doctype html><meta charset="utf-8"><title>Draft preview</title><h1>Draft — not for sale</h1><p>{html.escape(args.text)} · {html.escape(args.ref)}</p>{images}',encoding='utf-8')
        outputs.append({'path':index_name,'sha256':digest(index)})
        os.replace(index,destination/index_name)
    c['outputs'] = outputs
    c['renderer'] = git_state(prints_root, [renderer.relative_to(prints_root)])
    c['renderer_files'] = renderer_files
    c['factory_git'] = git_state(ROOT, [x['path'] for x in factory_files])
    c['factory_files'] = factory_files
    c['render_backend'] = args.backend
    def package_version(name):
        try: return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: return None
    c['runtime'] = {'python':sys.version.split()[0], 'indic_transliteration':package_version('indic-transliteration'), 'weasyprint':package_version('weasyprint') if args.backend=='weasyprint' else None}
    c['note'] = 'Preview only. Not approved for sale or publication; text, rights and print proof remain separate.'
    validate_schema(c, 'quote-handoff.schema.json')
    manifest = destination / f'{args.text}__{entry_id}__manifest.json'
    manifest.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'DRAFT handoff: {manifest}')


def verify_handoff(args):
    manifest = args.manifest.resolve()
    data = json.loads(manifest.read_text(encoding='utf-8'))
    validate_schema(data, 'quote-handoff.schema.json')
    input_root = args.prints.resolve() if data['kind'] == 'book-entry' else args.translations.resolve()
    for root, items in ((manifest.parent,data['outputs']), (input_root,data['inputs']), (args.prints.resolve(),data['renderer_files']), (ROOT,data['factory_files'])):
        for item in items:
            if digest(relative_file(root,item['path'])) != item['sha256']:
                raise ValueError(f"hash mismatch: {item['path']}")
    print('INTEGRITY PASS: source, renderer and output hashes match. Status remains DRAFT; this is not publication approval.')


def import_asset(args):
    data=json.loads(args.manifest.read_text(encoding='utf-8'))
    validate_schema(data, 'asset.schema.json')
    required={'version','asset_id','file','origin','rights','allowed_uses','alt'}
    if set(data) != required or data['version'] != '1.0' or not SAFE.fullmatch(data['asset_id']):
        raise ValueError('invalid asset manifest fields, version, or id')
    f, rights, origin = data['file'], data['rights'], data['origin']
    if not isinstance(f,dict) or set(f)!={'path','sha256','media_type'} or not re.fullmatch(r'[a-f0-9]{64}',f['sha256']):
        raise ValueError('invalid asset file record')
    if f['media_type'] not in ('image/png','image/jpeg'):
        raise ValueError('asset must be PNG or JPEG')
    if not isinstance(origin,dict) or set(origin)!={'repository','commit','project_ref'} or not all(isinstance(v,str) and v.strip() for v in origin.values()):
        raise ValueError('asset origin needs repository, commit and project_ref')
    if not re.fullmatch(r'[a-f0-9]{40}', origin['commit']):
        raise ValueError('asset origin commit must be a full Git commit SHA')
    if not isinstance(rights,dict) or set(rights)!={'commercial_use','holder','evidence'} or rights['commercial_use'] not in ('allowed','prohibited','unknown') or not isinstance(rights['holder'],str) or not isinstance(rights['evidence'],str):
        raise ValueError('invalid rights record')
    if not isinstance(data['allowed_uses'],list) or any(not isinstance(x,str) or x not in ('book-interior','postcard','social','video') for x in data['allowed_uses']) or len(set(data['allowed_uses']))!=len(data['allowed_uses']):
        raise ValueError('invalid allowed uses')
    if not isinstance(data['alt'],str) or not data['alt'].strip():
        raise ValueError('asset alt text is required')
    src=relative_file(args.asset_root, f['path'])
    if digest(src)!=f['sha256']:
        raise ValueError('asset bytes do not match manifest sha256')
    # A declared origin is evidence only if the exact bytes are in that commit.
    origin_verified = False
    try:
        repo = Path(subprocess.run(['git','-C',str(args.asset_root),'rev-parse','--show-toplevel'],check=True,capture_output=True,text=True).stdout.strip()).resolve()
        remote = subprocess.run(['git','-C',str(repo),'remote','get-url','origin'],check=True,capture_output=True,text=True).stdout.strip()
        remote = re.sub(r'^git@github\.com:', '', remote)
        remote = re.sub(r'^https://github\.com/', '', remote)
        remote = re.sub(r'\.git$', '', remote).lower()
        rel = src.relative_to(repo).as_posix()
        blob = subprocess.run(['git','-C',str(repo),'show',f"{origin['commit']}:{rel}"],check=True,capture_output=True).stdout
        origin_verified = remote == origin['repository'].lower() and hashlib.sha256(blob).hexdigest() == f['sha256']
    except (OSError, ValueError, subprocess.CalledProcessError):
        pass
    cleared = rights['commercial_use']=='allowed' and bool(rights['holder'].strip()) and bool(rights['evidence'].strip()) and 'book-interior' in data['allowed_uses'] and origin_verified
    if not cleared and not args.preview:
        raise ValueError('commercial rights evidence or committed origin missing; use --preview only for a draft')
    from PIL import Image
    with Image.open(src) as im:
        im.verify()
        if {'PNG':'image/png','JPEG':'image/jpeg'}.get(im.format) != f['media_type']:
            raise ValueError('image type does not match its bytes')
    book=args.book_dir.resolve()
    book_json=book/'book.json'
    if not book_json.is_file(): raise ValueError('book.json missing')
    target_dir=book/'assets'
    target_dir.mkdir(exist_ok=True)
    suffix='.png' if f['media_type']=='image/png' else '.jpg'
    dest=target_dir/(data['asset_id']+'-'+f['sha256'][:12]+suffix)
    if dest.exists() and digest(dest)!=f['sha256']: raise ValueError('asset destination collision')
    shutil.copyfile(src,dest)
    manifest_bytes=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    manifest_dest=target_dir/(dest.name+'--'+hashlib.sha256(manifest_bytes).hexdigest()[:12]+'.json')
    if manifest_dest.exists() and manifest_dest.read_bytes()!=manifest_bytes:
        raise ValueError('asset manifest destination collision')
    manifest_dest.write_bytes(manifest_bytes)
    if args.set_opening:
        book_data=json.loads(book_json.read_text(encoding='utf-8'))
        book_data['opening_image']={'path':dest.relative_to(book).as_posix(),'alt':data['alt'],'manifest':manifest_dest.relative_to(book).as_posix(),'draft_only':not cleared}
        temp=book_json.with_suffix('.json.tmp')
        temp.write_text(json.dumps(book_data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        os.replace(temp,book_json)
    print(f'Imported {dest}; rights evidence and committed origin recorded: {cleared}; opening page: {args.set_opening}')


def decide(args):
    """Append a justified content decision to a book's decision log."""
    proj = ROOT / 'projects' / args.book
    thesis_path = proj / 'thesis.json'
    if not thesis_path.is_file():
        raise ValueError(f'thesis missing: {thesis_path}')
    thesis = json.loads(thesis_path.read_text(encoding='utf-8'))
    validate_schema(thesis, 'thesis.schema.json')
    decision = {
        'ts': args.date or __import__('datetime').date.today().isoformat(),
        'action': args.action,
        'target': args.target,
        'from': args.from_section,
        'to': args.to_section,
        'justification': args.justification,
        'thesis_ref': args.thesis_ref,
        'status': 'live',
        'decided_by': args.decided_by,
    }
    validate_schema(decision, 'decision.schema.json')
    # The justification must actually cite something in this thesis.
    _resolve_thesis_ref(thesis, args.thesis_ref)
    log = proj / 'decisions.jsonl'
    with open(log, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(decision, ensure_ascii=False) + '\n')
    print(f'DECIDED {args.action} {args.target} -> {log} (thesis_ref={args.thesis_ref})')


def _resolve_thesis_ref(thesis, ref):
    node = thesis
    for part in ref.split('/'):
        if isinstance(node, list):
            try:
                node = node[int(part)]
            except (ValueError, IndexError) as exc:
                raise ValueError(f'thesis_ref {ref!r}: no index {part!r}') from exc
        elif isinstance(node, dict):
            if part not in node:
                raise ValueError(f'thesis_ref {ref!r}: no key {part!r}')
            node = node[part]
        else:
            raise ValueError(f'thesis_ref {ref!r}: cannot descend into {part!r}')
    return node


def new_book(args):
    """Instantiate a genre template into a fresh book lane (content stage).

    With --thesis PATH: load a full thesis object (e.g. specs/<id>.thesis.json),
    validate it, and scaffold the lane from that object — claim, structure
    (variable counts), purpose, products all come from the file.

    Without --thesis: build a thesis from --claim/--section flags as before.
    Creates thesis.json, decisions.jsonl (declare-structure), lane.py,
    project.json — then the book is built in prints/<slug>/ by the normal
    compile loop. PDF stays out of reach until content/structure/formatting pass.
    """
    if getattr(args, 'thesis', None):
        thesis_path = Path(args.thesis)
        if not thesis_path.is_file():
            raise ValueError(f'thesis file missing: {thesis_path}')
        thesis = json.loads(thesis_path.read_text(encoding='utf-8'))
        errs = validate_schema(thesis, 'thesis.schema.json')
        if errs:
            raise ValueError(f'thesis invalid: {errs}')
        if not SAFE.fullmatch(args.slug):
            raise ValueError(f'unsafe book slug: {args.slug}')
        if thesis.get('book') != args.slug:
            raise ValueError(f'thesis book field {thesis.get("book")!r} != --slug {args.slug!r}')
        tpl_path = ROOT / 'templates' / f"{thesis['template']}.json"
        if not tpl_path.is_file():
            raise ValueError(f'template missing: {tpl_path}')
        tpl = json.loads(tpl_path.read_text(encoding='utf-8'))
        errs = validate_schema(tpl, 'template.schema.json')
        if errs:
            raise ValueError(f'template invalid: {errs}')
        proj = ROOT / 'projects' / args.slug
        if proj.exists():
            raise ValueError(f'lane already exists: {proj}')
        plan = thesis['structure']['sections_plan']
        total = thesis['structure']['total_entries']
        st = thesis['structure']
        if 'entries_per_section' in st:
            per = st['entries_per_section']
        else:
            per = 'variable'
        max_pages = tpl['constraints']['max_pages']
        if thesis.get('pages', {}).get('target') == 400 or thesis.get('pages', {}).get('fallback') == 400:
            # study-edition theses may declare up to the fallback ceiling
            max_pages = max(max_pages, thesis['pages'].get('fallback', max_pages))
        style = thesis.get('style') or tpl['style_default']
        if not (ROOT / 'styles' / f'{style}.json').is_file():
            raise ValueError(f'style pack missing: styles/{style}.json')
        proj.mkdir(parents=True)
        (proj / 'thesis.json').write_text(json.dumps(thesis, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        decision = {
            'ts': __import__('datetime').date.today().isoformat(),
            'action': 'declare-structure',
            'target': args.slug,
            'justification': (f'Book scaffolded from thesis {thesis_path}: '
                              f'{len(plan)} sections, {total} entries, template {thesis["template"]}, '
                              f'ceiling {max_pages}pp. Structure and claim supplied by the owner thesis file; this ruling fixes the structure law.'),
            'thesis_ref': 'structure',
            'status': 'live',
            'decided_by': 'owner',
        }
        validate_schema(decision, 'decision.schema.json')
        (proj / 'decisions.jsonl').write_text(json.dumps(decision, ensure_ascii=False) + '\n', encoding='utf-8')
        (proj / 'lane.py').write_text(
            'LANE = {\n'
            f'    "text": "{args.slug}",\n'
            f'    "source_paths": {{"book": "{args.slug}/entries.json"}},\n'
            '    "id_map": None,\n'
            '    "entries_from": "hand-curated (scaffold from thesis)",\n'
            '    "gate_file": None,\n'
            f'    "sections": {[p["id"] for p in plan]!r},\n'
            f'    "products": {sorted(tpl["products"])!r},\n'
            f'    "book_dir": "{args.slug}",\n'
            '}\n', encoding='utf-8')
        (proj / 'project.json').write_text(json.dumps({
            'stage': 'content',
            'outputs': ['lesson-preview', 'paperback-preview'],
            'gate_note': 'Scaffolded from thesis file: content first, PDF build is the last stage — see BOOKS.md.',
            'max_pages': max_pages,
            'adjudications': [],
            'thesis_source': str(thesis_path),
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'NEW BOOK {args.slug} from {thesis_path}: {len(plan)} sections, {total} entries, '
              f'template {thesis["template"]}, style {style}, stage content')
        print(f'  next: create prints/{args.slug}/ (book.json sections + entries.json), '
              f'then factory.py stage --book {args.slug} --to structure')
        return

    tpl_path = ROOT / 'templates' / f'{args.template}.json'
    if not tpl_path.is_file():
        raise ValueError(f'template missing: {tpl_path}')
    tpl = json.loads(tpl_path.read_text(encoding='utf-8'))
    errs = validate_schema(tpl, 'template.schema.json')
    if errs:
        raise ValueError(f'template invalid: {errs}')
    if not SAFE.fullmatch(args.slug):
        raise ValueError(f'unsafe book slug: {args.slug}')
    proj = ROOT / 'projects' / args.slug
    if proj.exists():
        raise ValueError(f'lane already exists: {proj}')
    if not args.claim or len(args.claim.strip()) < 80:
        raise ValueError('a thesis needs a real claim — --claim with at least 80 characters')
    if not args.section:
        raise ValueError('at least one --section "id:purpose" required (the structure plan IS the book)')
    seen, plan = set(), []
    for raw in args.section:
        sid, sep, purpose = raw.partition(':')
        if not sep or not SAFE.fullmatch(sid) or not purpose.strip():
            raise ValueError(f'--section must be "id:purpose", got {raw!r}')
        if sid in seen:
            raise ValueError(f'duplicate section id: {sid}')
        seen.add(sid)
        plan.append({'id': sid, 'purpose': purpose.strip()})
    per = args.entries_per_section or tpl['structure_defaults']['entries_per_section']
    total = len(plan) * per
    if args.max_pages is None:
        args.max_pages = tpl['constraints']['max_pages']
    if args.max_pages > tpl['constraints']['max_pages']:
        raise ValueError(f'--max-pages {args.max_pages} exceeds template ceiling {tpl["constraints"]["max_pages"]}')
    style = args.style or tpl['style_default']
    if not (ROOT / 'styles' / f'{style}.json').is_file():
        raise ValueError(f'style pack missing: styles/{style}.json')
    thesis = {
        'version': '1.0',
        'book': args.slug,
        'title': args.title or args.slug.replace('-', ' ').title(),
        'template': args.template,
        'style': style,
        'claim': args.claim.strip(),
        'structure': {
            'sections': len(plan),
            'entries_per_section': per,
            'total_entries': total,
            'sections_plan': plan,
        },
        'inclusion': list(tpl['inclusion']),
        'exclusion': list(tpl['exclusion']),
        'products': json.loads(json.dumps(tpl['products'])),  # deep copy
    }
    if args.series:
        if not args.volume:
            raise ValueError('--series requires --volume N')
        thesis['series'] = {'name': args.series, 'volume': args.volume}
    errs = validate_schema(thesis, 'thesis.schema.json')
    if errs:
        raise ValueError(f'thesis invalid: {errs}')
    proj.mkdir(parents=True)
    (proj / 'thesis.json').write_text(json.dumps(thesis, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    decision = {
        'ts': __import__('datetime').date.today().isoformat(),
        'action': 'declare-structure',
        'target': args.slug,
        'justification': (f'Book scaffolded from template {args.template}: '
                          f'{len(plan)} sections x {per} = {total} entries, ceiling {args.max_pages}pp. '
                          f'Claim and section plan supplied by the owner at creation; this ruling fixes the structure law.'),
        'thesis_ref': 'structure',
        'status': 'live',
        'decided_by': 'owner',
    }
    validate_schema(decision, 'decision.schema.json')
    (proj / 'decisions.jsonl').write_text(json.dumps(decision, ensure_ascii=False) + '\n', encoding='utf-8')
    (proj / 'lane.py').write_text(
        'LANE = {\n'
        f'    "text": "{args.slug}",\n'
        f'    "source_paths": {{"book": "{args.slug}/entries.json"}},\n'
        '    "id_map": None,\n'
        '    "entries_from": "hand-curated (scaffold)",\n'
        '    "gate_file": None,\n'
        f'    "sections": {[p["id"] for p in plan]!r},\n'
        f'    "products": {sorted(tpl["products"])!r},\n'
        f'    "book_dir": "{args.slug}",\n'
        '}\n', encoding='utf-8')
    (proj / 'project.json').write_text(json.dumps({
        'stage': 'content',
        'outputs': ['paperback-preview', 'postcards'],
        'gate_note': 'Scaffolded lane: content first, PDF build is the last stage — see BOOKS.md.',
        'max_pages': args.max_pages,
        'adjudications': [],
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'NEW BOOK {args.slug}: {len(plan)}x{per}={total} entries, {args.max_pages}pp ceiling, '
          f'style {style}, stage content')
    print(f'  next: create prints/{args.slug}/ (book.json sections + entries.json), '
          f'then factory.py stage --book {args.slug} --to structure')



def handoff(args):
    """Write/refresh prints/<book>/handoff.jsonl — one record per entry.

    Binds entry -> source file sha256 + gate + rights + review state.
    --gate-pp uses editorial/05_source_qa.csv gates when present (PP).
    Default gate=review, rights=see-source-qa, review=mechanical.
    Does NOT equal ship approval (owner-approved + cleared rights still required).
    """
    import hashlib
    from datetime import date
    book_dir = PRINTS / args.book
    entries_path = book_dir / 'entries.json'
    if not entries_path.is_file():
        raise ValueError(f'entries.json missing: {entries_path}')
    entries = json.loads(entries_path.read_text(encoding='utf-8'))
    qa = {}
    qa_path = book_dir / 'editorial' / '05_source_qa.csv'
    if qa_path.is_file() and args.qa:
        import csv as _csv
        with qa_path.open(encoding='utf-8') as fh:
            for row in _csv.DictReader(fh):
                qa[row.get('id') or row.get('entry_id')] = row
    rights_default = args.rights or 'see-source-qa'
    lines = []
    n = 0
    for e in entries:
        eid = e.get('id')
        if not eid:
            raise ValueError('entry missing id')
        sp = e.get('source_path') or ''
        fpath = book_dir / sp
        if not fpath.is_file():
            raise ValueError(f'{eid}: source file missing {sp}')
        sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
        gate = args.gate or 'review'
        rights = rights_default
        note = ''
        if eid in qa:
            g = (qa[eid].get('gate') or '').strip().lower()
            if g in ('pass', 'review', 'blocked', 'check'):
                gate = 'pass' if g == 'pass' else ('blocked' if g == 'blocked' else 'review')
            rights = rights_default if args.rights else 'source-qa:' + (qa[eid].get('gate') or 'REVIEW')
            note = (qa[eid].get('issue') or '')[:400]
        rec = {
            'entry_id': eid,
            'source_path': sp,
            'source_ref': e.get('source_ref') or '',
            'source_sha256': sha,
            'gate': gate,
            'rights': rights,
            'review': args.review,
            'ts': date.today().isoformat(),
        }
        if note:
            rec['note'] = note
        from jsonschema import Draft202012Validator
        schema = json.loads((ROOT / 'schemas' / 'handoff.schema.json').read_text())
        errs = list(Draft202012Validator(schema).iter_errors(rec))
        if errs:
            raise ValueError(f'{eid}: handoff invalid: {errs[0].message}')
        lines.append(json.dumps(rec, ensure_ascii=False))
        n += 1
    out = book_dir / 'handoff.jsonl'
    if not args.dry_run:
        out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'HANDOFF {args.book}: {n} records -> {out}' + (' (dry-run)' if args.dry_run else ''))


def audio(args):
    """Plan per-entry clips in the videofactory speaker format (NO API calls).

    verse voice reads the IAST line, granny voice reads the how-to — one Fish
    Audio clip each, cache key sha1(voice|text), receipts path reserved.
    Writes prints/<book>/audio-plan.json (schema audio-plan.schema.json).
    Rendering happens only after an explicit owner go + FISH key.
    """
    book_id = clean_work(args.book)
    book = PRINTS / book_id
    entries_file = book / 'entries.json'
    if not entries_file.is_file():
        raise ValueError(f'no book at {book}')
    entries = json.loads(entries_file.read_text(encoding='utf-8'))
    # resolve corpus IAST exactly like the bookkit build does
    sys.path.insert(0, str(PRINTS / 'bookkit'))
    try:
        from engine import load_entries
        entries = load_entries(book, entries)
    finally:
        sys.path.pop(0)
    voices = {'verse': '4e873c37d4cb439e9bccc4dc1f633290',
              'granny': '614f8afd83f841048c040b2c6234d2c1'}
    plan_entries = []
    for e in entries:
        iast = (e.get('iast') or '').strip()
        if not iast:
            raise ValueError(f"{e.get('id')}: no IAST to speak")
        howto = (e.get('how') or e.get('howto') or '').strip()
        if not howto:
            raise ValueError(f"{e.get('id')}: no how-to text to read")
        def clip(voice, text):
            return {'voice': voice, 'voice_id': voices[voice], 'text': text,
                    'chars': len(text),
                    'cache_key': hashlib.sha1(f'{voice}|{text}'.encode('utf-8')).hexdigest()}
        plan_entries.append({'id': e['id'],
                             'verse': clip('verse', iast),
                             'howto': clip('granny', howto)})
    plan = {
        'version': '1.0',
        'book': book_id,
        'engine': {'tts': 'fish-audio',
                   'pattern_source': 'prx0r/videofactory render_chapter'},
        'voices': voices,
        'entries': plan_entries,
        'totals': {'clips': 2 * len(plan_entries),
                   'chars': sum(c['chars'] for pe in plan_entries for c in (pe['verse'], pe['howto']))},
        'receipts': f'prints/{book_id}/audio/receipts/calls.jsonl',
        'note': ('Plan only — no API call made. Render after owner go with FISH key; '
                 'append receipts to the path above; VOICE_DB -21dB normalization.'),
    }
    validate_schema(plan, 'audio-plan.schema.json')
    out = book / 'audio-plan.json'
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'AUDIO PLAN {book_id}: {plan["totals"]["clips"]} clips, '
          f'{plan["totals"]["chars"]} chars -> {out}')
    print('  render: NOT enabled — owner go + FISH key required (videofactory pattern)')


def make_epub(args):
    """Build the reflowable EPUB3 (Kindle/KDP) from the bookkit book."""
    book_id = clean_work(args.book)
    book = PRINTS / book_id
    if not (book / 'entries.json').is_file():
        raise ValueError(f'no book at {book}')
    sys.path.insert(0, str(ROOT))
    try:
        import epub as _epub
    finally:
        sys.path.pop(0)
    stats = _epub.build(book)
    problems = _epub.validate(stats['epub'])
    if problems:
        for p in problems:
            print(f'  x {p}', file=sys.stderr)
        raise ValueError(f'EPUB invalid: {len(problems)} problem(s)')
    print(f'EPUB {book_id}: {stats["chapters"]} chapters, {stats["entries"]} entries, '
          f'{stats["bytes"] // 1024} KiB -> {stats["epub"]}')
    print('  validated: mimetype-first/stored, XML well-formed, manifest+spine+fonts consistent')


def package(args):
    """Assemble the customer package: EPUB + interior PDF + audio (when rendered)
    + sha256 manifest. Audio clips absent = status 'pending' (render after owner go)."""
    book_id = clean_work(args.book)
    book = PRINTS / book_id
    if not (book / 'entries.json').is_file():
        raise ValueError(f'no book at {book}')
    out = PRINTS / book_id / 'package'
    out.mkdir(exist_ok=True)
    included, missing = [], []
    # epub (build fresh if missing)
    epub_path = book / f'{book_id}.epub'
    if not epub_path.is_file():
        sys.path.insert(0, str(ROOT))
        try:
            import epub as _epub
            _epub.build(book)
        finally:
            sys.path.pop(0)
    # interior pdf
    pdf_path = book / f'{book_id}-preview.pdf'
    # audio
    audio_dir = book / 'audio'
    plan = json.loads((book / 'audio-plan.json').read_text(encoding='utf-8')) \
        if (book / 'audio-plan.json').is_file() else None
    clips = []
    if plan:
        have = {p.stem for p in audio_dir.glob('*.mp3')} if audio_dir.is_dir() else set()
        for pe in plan['entries']:
            for kind in ('verse', 'howto'):
                if f'{pe["id"]}__{kind}' in have:
                    clips.append(f'{pe["id"]}__{kind}.mp3')
                else:
                    missing.append(f'{pe["id"]}__{kind}.mp3')
    files = []
    def add(path, dest_name=None):
        if path.is_file():
            dest_name = dest_name or path.name
            data = path.read_bytes()
            (out / dest_name).write_bytes(data)
            files.append({'path': dest_name, 'sha256': hashlib.sha256(data).hexdigest(),
                          'size': len(data)})
            return True
        return False
    add(epub_path)
    add(pdf_path)
    add(book / 'cover.pdf')
    if audio_dir.is_dir():
        for mp3 in sorted(audio_dir.rglob('*.mp3')):
            add(mp3, f'audio/{mp3.name}')
    add(book / 'audio-plan.json')
    planned = plan['totals']['clips'] if plan else 0
    audio_status = ('no-plan' if not plan else
                    'included' if len(clips) >= planned else 'pending-render')
    manifest = {
        'version': '1.0',
        'book': book_id,
        'title': json.loads((book / 'book.json').read_text(encoding='utf-8'))['meta']['title'],
        'built': __import__('datetime').date.today().isoformat(),
        'audio': {'status': audio_status, 'clips_present': len(clips),
                  'clips_planned': plan['totals']['clips'] if plan else 0,
                  'voices': plan['voices'] if plan else None},
        'channels': {
            'physical': 'interior PDF -> KDP; QR in colophon -> hosted audio package (see BOOKS.md 7b)',
            'kindle': 'EPUB -> KDP ebook; colophon link -> hosted audio package',
            'direct': 'zip this package/ dir (EPUB + PDF + audio + manifest) as the one-link delivery',
        },
        'files': files,
        'note': ('Customer package staging. Physical ships via KDP (audio via QR/link once '
                 'rendered); direct digital ships as this folder zipped. Clips absent until '
                 'owner-go render.'),
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n',
                                       encoding='utf-8')
    total = sum(f['size'] for f in files)
    print(f'PACKAGE {book_id} -> {out}')
    print(f'  {len(files)} files, {total // 1048576} MiB, audio={audio_status} '
          f'({len(clips)}/{plan["totals"]["clips"] if plan else 0} clips)')
    if missing and audio_status == 'pending-render':
        print(f'  {len(missing)} clips pending — factory.py audio render after owner go')


def set_stage(args):
    """Advance (or hold) a lane's pipeline stage after verifying stage gates.

    Forward moves are verified: the stages you claim complete must actually
    pass. Backward moves are free (a regression re-opens earlier work).
    """
    proj = ROOT / 'projects' / args.book
    project = proj / 'project.json'
    if not project.is_file():
        raise ValueError(f'project.json missing: {project}')
    import check as gate
    STAGES = gate.STAGES
    settings = json.loads(project.read_text(encoding='utf-8'))
    cur = settings.get('stage')
    if cur not in STAGES:
        raise ValueError(f'current stage {cur!r} not one of {STAGES}')
    if args.to not in STAGES:
        raise ValueError(f'target stage {args.to!r} not one of {STAGES}')
    if STAGES.index(args.to) <= STAGES.index(cur):
        settings['stage'] = args.to  # backward/same: re-opens work, no gate to pass
        project.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'{args.book}: stage {cur} -> {args.to} (backward/same move)')
        return
    # forward: every stage up to and including the target must pass
    grouped = gate.run_lane(args.book, gate.PRINTS.resolve(), gate.DEFAULT_TRANSLATIONS.resolve())
    target_idx = STAGES.index(args.to)
    fails = []
    for i in range(target_idx + 1):
        fails += grouped[STAGES[i]]
    if fails:
        for f in fails:
            print(f'  x {f}')
        raise ValueError(f'cannot advance {args.book} {cur} -> {args.to}: {len(fails)} failing check(s)')
    settings['stage'] = args.to
    project.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{args.book}: stage {cur} -> {args.to} (all gates to {args.to} pass)')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    subs=p.add_subparsers(dest='command',required=True)
    inspect=subs.add_parser('inspect',help='inspect one exact translation-layer verse and its recorded gate')
    quote_p=subs.add_parser('quote',help='render watermarked postcard and social previews')
    for sub in (inspect,quote_p):
        sub.add_argument('--text',required=True)
        sub.add_argument('--ref',required=True,help='exact verse_id or existing book entry id; optional :line for layer records')
        sub.add_argument('--layer',choices=['l2','l3'],default='l3')
        sub.add_argument('--gate-id',help='explicit passage locator; never inferred from a verse number')
        sub.add_argument('--translations',type=Path,default=DEFAULT_TRANSLATIONS)
    quote_p.add_argument('--prints',type=Path,default=PRINTS)
    quote_p.add_argument('--output',type=Path,required=True)
    quote_p.add_argument('--backend',choices=['chrome','weasyprint'],default='chrome')
    asset=subs.add_parser('import-asset',help='stage a hash-pinned reusable image from video or another project')
    asset.add_argument('--manifest',type=Path,required=True)
    asset.add_argument('--asset-root',type=Path,required=True)
    asset.add_argument('--book-dir',type=Path,required=True)
    asset.add_argument('--preview',action='store_true',help='allow uncleared artwork for draft use')
    asset.add_argument('--set-opening',action='store_true',help='also use it as this book’s opening image')
    verify=subs.add_parser('verify',help='verify a draft handoff against its current input and output bytes')
    verify.add_argument('--manifest',type=Path,required=True)
    verify.add_argument('--prints',type=Path,default=PRINTS)
    verify.add_argument('--translations',type=Path,default=DEFAULT_TRANSLATIONS)
    decide_p=subs.add_parser('decide',help='append a justified content decision citing a thesis clause')
    decide_p.add_argument('--book',required=True,help='book lane name (e.g. practical-prayers)')
    decide_p.add_argument('--action',required=True,
        choices=['add-section','remove-section','add-entry','remove-entry','move-entry','retire-entry','replace-entry','declare-structure'])
    decide_p.add_argument('--target',required=True,help='entry id or section id the decision is about')
    decide_p.add_argument('--from',dest='from_section',default=None)
    decide_p.add_argument('--to',dest='to_section',default=None)
    decide_p.add_argument('--justification',required=True,help='full why — min 40 chars, empty fails')
    decide_p.add_argument('--thesis-ref',required=True,help='path into thesis.json, e.g. exclusion/0 or structure')
    decide_p.add_argument('--decided-by',default='owner')
    decide_p.add_argument('--date',default=None,help='YYYY-MM-DD (default: today)')
    nb=subs.add_parser('new-book',help='instantiate a genre template into a fresh book lane (content stage)')
    nb.add_argument('--thesis',default=None,help='path to a full thesis JSON (e.g. specs/<id>.thesis.json); overrides --claim/--section/--template')
    nb.add_argument('--template',default=None,help='genre template id (templates/<id>.json, e.g. prayer-book); required unless --thesis')
    nb.add_argument('--slug',required=True,help='book id / lane name (lowercase, hyphens)')
    nb.add_argument('--title',default=None,help='display title (default: titleized slug)')
    nb.add_argument('--claim',default=None,help='the thesis claim, >=80 chars — required unless --thesis')
    nb.add_argument('--section',action='append',default=None,metavar='ID:PURPOSE',
                    help='one section per flag: --section wake:"on rising" (repeat); required unless --thesis')
    nb.add_argument('--entries-per-section',type=int,default=None,help='default from template (prayer-book: 4)')
    nb.add_argument('--max-pages',type=int,default=None,help='default from template ceiling (prayer-book: 110)')
    nb.add_argument('--style',default=None,help='style pack id (default: template style_default)')
    nb.add_argument('--series',default=None,help='series name when this is a numbered volume')
    nb.add_argument('--volume',type=int,default=None,help='volume number (requires --series)')
    stg=subs.add_parser('stage',help='advance a lane through content->structure->formatting->build (PDF last)')
    stg.add_argument('--book',required=True)
    stg.add_argument('--to',required=True,choices=['content','structure','formatting','build'])
    hp=subs.add_parser('handoff',help='per-entry source/gate/rights/review binding for build')
    hp.add_argument('--book',required=True)
    hp.add_argument('--gate',choices=['pass','review','blocked'],default=None)
    hp.add_argument('--rights',default=None)
    hp.add_argument('--review',choices=['mechanical','owner-pending','owner-approved'],default='mechanical')
    hp.add_argument('--qa',action='store_true',help='fold editorial/05_source_qa.csv gates when present')
    hp.add_argument('--dry-run',action='store_true')
    aud=subs.add_parser('audio',help='plan per-entry clips (videofactory speakers: verse + granny); NO API calls')
    aud.add_argument('--book',required=True)
    ep=subs.add_parser('epub',help='build the reflowable EPUB3 (Kindle/KDP) from the bookkit book')
    ep.add_argument('--book',required=True)
    pkg=subs.add_parser('package',help='assemble customer package: EPUB + PDF + audio + sha256 manifest')
    pkg.add_argument('--book',required=True)
    args=p.parse_args()
    try:
        if args.command=='inspect': print(json.dumps(extract(args.translations,args.text,args.ref,args.layer,args.gate_id),ensure_ascii=False,indent=2))
        elif args.command=='quote': quote(args)
        elif args.command=='import-asset': import_asset(args)
        elif args.command=='decide': decide(args)
        elif args.command=='new-book': new_book(args)
        elif args.command=='stage': set_stage(args)
        elif args.command=='handoff': handoff(args)
        elif args.command=='audio': audio(args)
        elif args.command=='epub': make_epub(args)
        elif args.command=='package': package(args)
        else: verify_handoff(args)
    except (ValueError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
