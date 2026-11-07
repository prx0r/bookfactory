#!/usr/bin/env python3
"""Fail-closed publishing gate with a staged pipeline.

    content -> structure -> formatting -> build        (PDF is ALWAYS last)

A lane's project.json declares its stage. Checks are attributed to a stage:
problems at or before the current stage BLOCK; later-stage problems print as
DUE-LATER (visible worklist, not yet due). Every book carries a thesis
(what it IS), a decision log (every change justified against the thesis),
and a template (the genre it instantiates). Structure is derived from the
thesis — a book that drifts from its own thesis blocks itself.
"""
import argparse
import ast
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent
PRINTS = Path(os.environ.get('BOOKFACTORY_PRINTS', ROOT / 'prints'))
DEFAULT_TRANSLATIONS = Path(os.environ.get('BOOKFACTORY_TRANSLATIONS', ROOT.parent / 'translation-work'))
STAGES = ['content', 'structure', 'formatting', 'build']


def lane_config(path):
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Assign) or len(tree.body[0].targets) != 1 \
            or not isinstance(tree.body[0].targets[0], ast.Name) or tree.body[0].targets[0].id != 'LANE':
        raise ValueError('lane.py must contain only a literal LANE assignment')
    value = ast.literal_eval(tree.body[0].value)
    if not isinstance(value, dict):
        raise ValueError('LANE must be a dictionary')
    return value


def _load_schema(filename):
    return json.loads((ROOT / 'schemas' / filename).read_text(encoding='utf-8'))


def _validate(instance, filename):
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ['jsonschema missing; install prints/requirements-publishing.txt']
    problems = sorted(Draft202012Validator(_load_schema(filename)).iter_errors(instance),
                      key=lambda e: list(map(str, e.path)))
    return [f"{filename}: {'/'.join(map(str, e.path)) or '/'}: {e.message}" for e in problems]


def resolve_thesis_ref(thesis, ref):
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


def _norm_iast(text):
    text = unicodedata.normalize('NFC', text)
    return ' '.join(''.join(c if c.isalnum() else ' ' for c in text).split())


def lane_stage(name, problems):
    """Read project.json stage for an active book lane. Stage itself gates content."""
    project = ROOT / 'projects' / name / 'project.json'
    if not project.is_file():
        problems.append('project.json missing — no stage, no lane')
        return None
    try:
        settings = json.loads(project.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f'project.json unreadable: {exc}')
        return None
    stage = settings.get('stage')
    if stage not in STAGES:
        problems.append(f'stage must be one of {STAGES}, got {stage!r}')
        return None
    return stage


def load_template(thesis, problems):
    """thesis.template -> templates/<id>.json, schema-valid. Fail-closed."""
    tpl_id = thesis.get('template')
    if not tpl_id:
        problems.append(('content', 'thesis has no template — a book must name its genre'))
        return None
    path = ROOT / 'templates' / f'{tpl_id}.json'
    if not path.is_file():
        problems.append(('content', f'template missing: {path}'))
        return None
    try:
        tpl = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(('content', f'template unreadable: {exc}'))
        return None
    errs = _validate(tpl, 'template.schema.json')
    problems.extend(('content', f'template {tpl_id}: {e}') for e in errs)
    return None if errs else tpl


def check_thesis(name):
    """Thesis + template + style + decisions. Returns [(stage, problem), ...]."""
    problems = []
    proj = ROOT / 'projects' / name
    thesis_path = proj / 'thesis.json'
    decisions_path = proj / 'decisions.jsonl'
    if not thesis_path.is_file():
        return [('content', f'thesis missing: {thesis_path} — a book without a thesis is not a book')]
    try:
        thesis = json.loads(thesis_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        return [('content', f'thesis unreadable: {exc}')]
    errs = _validate(thesis, 'thesis.schema.json')
    problems.extend(('content', e) for e in errs)
    if errs:
        return problems

    tpl = load_template(thesis, problems)
    if tpl:
        # template rules are inherited verbatim — dropping one breaks the genre
        for rule in tpl['inclusion']:
            if rule not in thesis['inclusion']:
                problems.append(('content', f'thesis drops template inclusion rule: {rule[:60]}...'))
        for rule in tpl['exclusion']:
            if rule not in thesis['exclusion']:
                problems.append(('content', f'thesis drops template exclusion rule: {rule[:60]}...'))
        if set(thesis['products']) != set(tpl['products']):
            problems.append(('content', 'thesis product set differs from template product set'))
        project = proj / 'project.json'
        if project.is_file():
            try:
                ceiling = json.loads(project.read_text(encoding='utf-8')).get('max_pages')
                if isinstance(ceiling, int) and ceiling > tpl['constraints']['max_pages']:
                    problems.append(('content',
                        f'project max_pages {ceiling} exceeds template ceiling {tpl["constraints"]["max_pages"]}'))
            except (OSError, json.JSONDecodeError):
                pass  # reported by lane_stage

    style_id = thesis.get('style')
    if not style_id:
        problems.append(('content', 'thesis has no style — a book must name its style pack'))
    else:
        style_path = ROOT / 'styles' / f'{style_id}.json'
        if not style_path.is_file():
            problems.append(('content', f'style pack missing: {style_path}'))
        else:
            try:
                sty = json.loads(style_path.read_text(encoding='utf-8'))
                problems.extend(('content', f'style {style_id}: {e}')
                                for e in _validate(sty, 'style.schema.json'))
            except (OSError, json.JSONDecodeError) as exc:
                problems.append(('content', f'style unreadable: {exc}'))

    if not decisions_path.is_file():
        problems.append(('content', f'decision log missing: {decisions_path} — construction without recorded decisions fails closed'))
        return problems
    live = []
    for n, line in enumerate(decisions_path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(('content', f'decisions line {n}: not JSON: {exc}'))
            continue
        errs = _validate(d, 'decision.schema.json')
        problems.extend(('content', f'decisions line {n}: {e}') for e in errs)
        if errs:
            continue
        try:
            resolve_thesis_ref(thesis, d['thesis_ref'])
        except ValueError as exc:
            problems.append(('content', f'decisions line {n}: {exc}'))
        if d['status'] == 'live':
            live.append(d)
    if not live:
        problems.append(('content', 'decision log has no live decisions'))
    return problems


def check_content(name, spec, prints, template):
    """Entries exist and each carries the template's required anatomy."""
    problems = []
    book_id = spec.get('book_dir')
    if not book_id:
        return [('content', 'queued lane: no book, verse-to-gate mapping, production rights or proof configured')]
    book = (prints / book_id).resolve()
    if not book.is_relative_to(prints) or not book.is_dir():
        return [('content', f'book directory missing or outside prints: {book_id} — content stage begins when the book dir exists')]
    try:
        entries = json.loads((book / 'entries.json').read_text(encoding='utf-8'))
        book_data = json.loads((book / 'book.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return [('content', f'cannot load book data: {exc}')]
    if not isinstance(entries, list) or not entries:
        return [('content', 'entries.json must be a nonempty list')]
    ids = []
    anatomy = (template or {}).get('entry_anatomy', {}).get('required', {})
    for e in entries:
        if not isinstance(e, dict):
            problems.append(('content', 'entry is not an object'))
            continue
        entry_id = e.get('id')
        if not isinstance(entry_id, str) or not entry_id:
            problems.append(('content', 'entry missing id'))
            continue
        ids.append(entry_id)
        for field in ('title', 'source', 'source_ref', 'source_path', 'en'):
            if not isinstance(e.get(field), str) or not e[field].strip():
                problems.append(('content', f'{entry_id}: missing {field}'))
        if not e.get('iast') and not e.get('corpus'):
            problems.append(('content', f'{entry_id}: missing IAST/corpus reference'))
        for canon, keys in anatomy.items():
            if not any(e.get(k) for k in keys):
                problems.append(('content', f'{entry_id}: entry anatomy {canon} empty (fields {tuple(keys)})'))
        source = e.get('source_path')
        if isinstance(source, str) and source:
            path = (book / source).resolve()
            if Path(source).is_absolute() or not path.is_relative_to(book) or not path.is_file():
                problems.append(('content', f'{entry_id}: source path missing or outside book'))
    if len(ids) != len(set(ids)):
        problems.append(('content', 'duplicate entry ids'))
    # Legacy books do not yet bind each entry's exact text to a specific
    # upstream passage, recorded decision, rights evidence and reviewed revision.
    # That is a SHIP concern (per-entry handoff) — it blocks the build stage,
    # not authoring of content/structure/formatting.
    problems.append(('build', f'{len(entries)} entries lack a verified per-entry source, gate, rights and review handoff'))
    art = book_data.get('opening_image')
    if art:
        if not isinstance(art, dict):
            problems.append(('content', 'opening artwork record must be an object'))
        else:
            if art.get('draft_only', True):
                problems.append(('content', 'opening artwork is draft-only or has no rights evidence'))
            if not art.get('manifest'):
                problems.append(('content', 'opening artwork has no asset manifest'))
            problems.append(('content', 'opening artwork requires asset provenance and rights review'))
    return problems


def section_counts(st):
    """Thesis section -> exact count. Uniform entries_per_section, or per-section count."""
    if 'entries_per_section' in st:
        return {p['id']: st['entries_per_section'] for p in st['sections_plan']}
    return {p['id']: p['count'] for p in st['sections_plan']}


def check_structure_against_thesis(thesis, entries, book_data):
    """structure stage: the thesis derives sections, counts, total."""
    problems = []
    st = thesis['structure']
    plan_ids = [p['id'] for p in st['sections_plan']]
    book_sections = [s.get('id') for s in book_data.get('sections', [])]
    if book_sections != plan_ids:
        problems.append(f'section mismatch: book={book_sections} thesis={plan_ids}')
    counts = Counter(e.get('section') for e in entries)
    fixed = section_counts(st)
    if sum(fixed.values()) != st['total_entries']:
        problems.append(f'thesis internal math: section counts sum {sum(fixed.values())} != {st["total_entries"]}')
    if len(entries) != st['total_entries']:
        problems.append(f'total_entries: book has {len(entries)}, thesis fixes {st["total_entries"]}')
    for sid in plan_ids:
        if counts.get(sid, 0) != fixed.get(sid):
            problems.append(f'section {sid}: {counts.get(sid, 0)} entries, thesis fixes {fixed.get(sid)}')
    for sid in counts:
        if sid not in plan_ids:
            problems.append(f'section {sid} exists in book but not in thesis')
    return problems


def check_decisions_vs_book(live, entries):
    """structure stage: live decisions must agree with the book's current state."""
    problems = []
    ids = {e.get('id') for e in entries}
    entry_sections = {e.get('id'): e.get('section') for e in entries}
    section_ids = set(entry_sections.values())
    for d in live:
        act, t = d['action'], d['target']
        if act in ('remove-section', 'retire-entry', 'remove-entry'):
            present = t in section_ids if act == 'remove-section' else t in ids
            if present:
                problems.append(f'{act} {t}: still present in book (decision says it left)')
        elif act in ('add-section', 'add-entry', 'move-entry', 'replace-entry'):
            if act == 'add-section':
                if t not in section_ids:
                    problems.append(f'{act} {t}: thesis/decision adds it but book lacks it')
            else:
                if t not in ids:
                    problems.append(f'{act} {t}: decision adds it but entry missing from book')
                dest = (d.get('to') or '').split('/')[-1] if d.get('to') and '/' in d['to'] else None
                if dest and entry_sections.get(t) and entry_sections[t] != dest:
                    problems.append(f'move-entry {t}: decision places it in {dest}, book has {entry_sections.get(t)}')
    return problems


def check_cross_book_dupes(prints):
    """structure stage: one prayer, one book — no shared ids or IAST across PP/TP."""
    problems = []
    books = {}
    for name in ('practical-prayers', 'tantric-prayer'):
        p = (prints / name / 'entries.json').resolve()
        if p.is_file():
            try:
                books[name] = json.loads(p.read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError) as exc:
                problems.append(f'{name}: unreadable: {exc}')
    if len(books) == 2:
        a, b = books['practical-prayers'], books['tantric-prayer']
        clash = {e.get('id') for e in a} & {e.get('id') for e in b}
        if clash:
            problems.append(f'cross-book id clash: {sorted(clash)}')
        ai = {_norm_iast(e['iast']): e['id'] for e in a if e.get('iast')}
        bi = {_norm_iast(e['iast']): e['id'] for e in b if e.get('iast')}
        shared = set(ai) & set(bi)
        if shared:
            problems.append(f'cross-book IAST clash: {sorted((ai[s], bi[s]) for s in shared)}')
    return problems


def check_formatting(name, spec, prints, template):
    """formatting stage: sources renderable at the template's type floor — no PDF yet."""
    problems = []
    book_id = spec.get('book_dir')
    if not book_id:
        return problems
    book = (prints / book_id).resolve()
    if not book.is_dir():
        return problems  # content stage owns the missing-dir error
    fonts = book / 'fonts'
    ttfs = list(fonts.glob('*.ttf')) if fonts.is_dir() else []
    if len(ttfs) < 2:
        problems.append(f'formatting: need both book fonts in fonts/ (found {len(ttfs)} .ttf)')
    html = book / 'index.html'
    if not html.is_file():
        problems.append('formatting: index.html missing — run compile.py')
        return problems
    floor = (template or {}).get('constraints', {}).get('min_font_pt', 7)
    css = html.read_text(encoding='utf-8', errors='replace')
    sizes = [float(m) for m in re.findall(r'font-size:\s*([\d.]+)pt', css)]
    if not sizes:
        problems.append('formatting: no font-size declarations found in index.html')
    else:
        small = sorted({s for s in sizes if s < floor})
        if small:
            problems.append(f'formatting: source font-size below {floor}pt floor: {small}')
    return problems


def check_build(name, spec, prints, pdf_override=None):
    """build stage: THE LAST STEP — audio plan, PDF proof, actual preflight."""
    problems = []
    book_id = spec.get('book_dir')
    if not book_id:
        return problems
    book = (prints / book_id).resolve()
    if not book.is_dir():
        return problems
    # audio plan: per-entry verse+granny clips (videofactory format) must be planned
    plan_path = book / 'audio-plan.json'
    if not plan_path.is_file():
        problems.append(f'audio plan missing: run factory.py audio --book {book_id} (planned clips: verse voice reads IAST, granny reads how-to)')
    else:
        try:
            plan = json.loads(plan_path.read_text(encoding='utf-8'))
            problems.extend(f'audio-plan: {e}' for e in _validate(plan, 'audio-plan.schema.json'))
            entries = json.loads((book / 'entries.json').read_text(encoding='utf-8'))
            sys.path.insert(0, str(prints / 'bookkit'))
            try:
                from engine import load_entries
                resolved = load_entries(book, entries)
            finally:
                sys.path.pop(0)
            by_id = {e['id']: e for e in resolved}
            plan_ids = [pe['id'] for pe in plan.get('entries', [])]
            if plan_ids != [e['id'] for e in resolved]:
                problems.append('audio plan entry list out of sync with entries.json — rerun factory.py audio')
            else:
                import hashlib as _hl
                for pe in plan['entries']:
                    src = by_id[pe['id']]
                    if pe['verse']['text'] != (src.get('iast') or '').strip():
                        problems.append(f"audio plan {pe['id']}: verse text stale vs IAST — rerun factory.py audio")
                    for clip_key, voice in (('verse', 'verse'), ('howto', 'granny')):
                        clip = pe[clip_key]
                        expect = _hl.sha1(f"{clip['voice']}|{clip['text']}".encode('utf-8')).hexdigest()
                        if clip['cache_key'] != expect:
                            problems.append(f"audio plan {pe['id']}: {clip_key} cache_key corrupt")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            problems.append(f'audio plan unreadable: {exc}')
    pdf = Path(pdf_override) if pdf_override else book / f'{book_id}-preview.pdf'
    preflight = prints / 'kdp_preflight.py'
    project = ROOT / 'projects' / name / 'project.json'
    ceiling = None
    if project.is_file():
        try:
            ceiling = json.loads(project.read_text(encoding='utf-8')).get('max_pages')
            if ceiling is not None and (not isinstance(ceiling, int) or ceiling < 24):
                problems.append('project max_pages must be an integer of at least 24')
                ceiling = None
        except (OSError, json.JSONDecodeError):
            pass
    if not pdf.is_file():
        problems.append(f'PDF proof missing: {pdf} — build stage renders it LAST, after content/structure/formatting pass')
        return problems
    if not preflight.is_file():
        problems.append('KDP preflight missing')
        return problems
    command = [sys.executable, str(preflight)]
    if ceiling is not None:
        command += ['--max-pages', str(ceiling)]
    try:
        target = json.loads((book / 'book.json').read_text(encoding='utf-8')).get('target_pages')
        if isinstance(target, int):
            command += ['--expect-pages', str(target)]
    except (OSError, json.JSONDecodeError):
        pass
    result = subprocess.run(command + [str(pdf)], capture_output=True, text=True)
    if result.returncode:
        detail = '; '.join(x.strip() for x in result.stdout.splitlines() if x.strip().startswith('x '))
        problems.append(f'PDF preflight failed: {detail or result.stderr.strip() or "unknown failure"}')
    return problems


def run_lane(name, prints, translations, pdf_override=None):
    """Run all stages for one lane; return {stage: [problems]}."""
    grouped = {s: [] for s in STAGES}

    def add(stage, items):
        if isinstance(items, str):
            items = [items]
        grouped[stage].extend(items)

    spec = {}
    try:
        spec = lane_config(ROOT / 'projects' / name / 'lane.py')
    except (OSError, ValueError, SyntaxError, TypeError) as exc:
        add('content', str(exc))
        return grouped

    thesis = None
    template = None
    thesis_path = ROOT / 'projects' / name / 'thesis.json'
    if thesis_path.is_file():
        try:
            thesis = json.loads(thesis_path.read_text(encoding='utf-8'))
            if not _validate(thesis, 'thesis.schema.json'):
                template = load_template(thesis, [])
        except (OSError, json.JSONDecodeError):
            pass

    stage = lane_stage(name, grouped['content'])
    if stage is None:
        stage = 'content'  # everything else still reported below, blocked on content anyway

    for s, p in check_thesis(name):
        add(s, p)
    for s, p in check_content(name, spec, prints, template):
        add(s, p)

    # structure checks need a readable book + valid thesis
    book_id = spec.get('book_dir')
    book = (prints / book_id) if book_id else None
    if thesis is not None and book is not None and book.is_dir() and not _validate(thesis, 'thesis.schema.json'):
        try:
            entries = json.loads((book / 'entries.json').read_text(encoding='utf-8'))
            book_data = json.loads((book / 'book.json').read_text(encoding='utf-8'))
            add('structure', check_structure_against_thesis(thesis, entries, book_data))
            decisions_path = ROOT / 'projects' / name / 'decisions.jsonl'
            if decisions_path.is_file():
                live = []
                for line in decisions_path.read_text(encoding='utf-8').splitlines():
                    if line.strip():
                        d = json.loads(line)
                        if d.get('status') == 'live':
                            live.append(d)
                add('structure', check_decisions_vs_book(live, entries))
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            add('content', f'book/decision data unreadable: {exc}')

    if book_id in ('practical-prayers', 'tantric-prayer'):
        add('structure', check_cross_book_dupes(prints))

    add('formatting', check_formatting(name, spec, prints, template))
    add('build', check_build(name, spec, prints, pdf_override))
    return grouped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lane', nargs='?')
    parser.add_argument('--prints', type=Path, default=PRINTS)
    parser.add_argument('--translations', type=Path, default=DEFAULT_TRANSLATIONS)
    parser.add_argument('--pdf', type=Path, help='specific proof for the selected lane (forces build-stage check)')
    parser.add_argument('--all-stages', action='store_true',
                        help='report later-stage problems too (default: show them as DUE-LATER)')
    args = parser.parse_args()
    if args.pdf and not args.lane:
        parser.error('--pdf requires one lane')
    reg = json.loads((ROOT / 'REGISTRY.json').read_text(encoding='utf-8'))
    names = list(reg['lanes'])
    if args.lane and args.lane not in names:
        print(f'[FAIL] {args.lane}: not in REGISTRY lanes')
        return 1
    if args.lane:
        names = [args.lane]

    blocking = 0
    due_later = 0
    for name in names:
        grouped = run_lane(name, args.prints.resolve(), args.translations.resolve(), args.pdf)
        # lane's own stage for ordering (content if unknown)
        try:
            settings = json.loads((ROOT / 'projects' / name / 'project.json').read_text(encoding='utf-8'))
            stage = settings.get('stage') if settings.get('stage') in STAGES else 'content'
        except (OSError, json.JSONDecodeError):
            stage = 'content'
        cur_idx = STAGES.index(stage)
        lane_blocked = 0
        for i, s in enumerate(STAGES):
            for problem in grouped[s]:
                if i <= cur_idx:
                    print(f'[BLOCKED] {name}: {problem}')
                    lane_blocked += 1
                else:
                    if s == 'build' and args.pdf:
                        print(f'[BLOCKED] {name}: {problem}')  # explicit --pdf is due now
                        lane_blocked += 1
                    else:
                        print(f'[DUE-LATER {s}] {name}: {problem}')
                        due_later += 1
        if lane_blocked == 0:
            suffix = '' if stage == 'build' else f' at stage {stage} (ship requires build)'
            print(f'[PASS] {name}: canonical{suffix}')
        blocking += lane_blocked
    if due_later:
        print(f'({due_later} problem(s) due later — pipeline: content -> structure -> formatting -> build; PDF is last)')
    if blocking:
        print(f'BLOCKED — {blocking} problem(s)')
    else:
        print('CANONICAL — 0 blocking problem(s)')
    return int(bool(blocking))


if __name__ == '__main__':
    sys.exit(main())
