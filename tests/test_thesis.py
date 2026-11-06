import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bf_check', ROOT / 'check.py')
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)
fspec = importlib.util.spec_from_file_location('bf_factory', ROOT / 'factory.py')
factory = importlib.util.module_from_spec(fspec)
fspec.loader.exec_module(factory)


def real_thesis(book):
    return json.loads((ROOT / 'projects' / book / 'thesis.json').read_text(encoding='utf-8'))


def real_decisions(book):
    path = ROOT / 'projects' / book / 'decisions.jsonl'
    return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]


class ThesisSchemaTests(unittest.TestCase):
    def test_both_real_theses_validate(self):
        for book in ('practical-prayers', 'tantric-prayer'):
            errors = check._validate(real_thesis(book), 'thesis.schema.json')
            self.assertEqual(errors, [], f'{book}: {errors}')

    def test_thesis_structure_math(self):
        for book in ('practical-prayers', 'tantric-prayer'):
            st = real_thesis(book)['structure']
            self.assertEqual(st['sections'] * st['entries_per_section'], st['total_entries'])
            self.assertEqual(len(st['sections_plan']), st['sections'])
            self.assertEqual(st['total_entries'], 36)

    def test_all_real_decisions_validate_and_refs_resolve(self):
        for book in ('practical-prayers', 'tantric-prayer'):
            thesis = real_thesis(book)
            decisions = real_decisions(book)
            self.assertGreaterEqual(len(decisions), 5)
            for d in decisions:
                errors = check._validate(d, 'decision.schema.json')
                self.assertEqual(errors, [], f"{book} {d['target']}: {errors}")
                check.resolve_thesis_ref(thesis, d['thesis_ref'])

    def test_justification_floor(self):
        # thin justification must fail schema
        bad = {'ts': '2026-11-06', 'action': 'remove-section', 'target': 'x',
               'justification': 'no', 'thesis_ref': 'exclusion/0',
               'status': 'live', 'decided_by': 'owner'}
        self.assertTrue(check._validate(bad, 'decision.schema.json'))


class ThesisRefTests(unittest.TestCase):
    def test_resolves_paths(self):
        t = real_thesis('practical-prayers')
        self.assertIn('mood-state sections', check.resolve_thesis_ref(t, 'exclusion/0'))
        self.assertIn('sections_plan', check.resolve_thesis_ref(t, 'structure'))
        self.assertIn('A5', check.resolve_thesis_ref(t, 'products/paperback/spec'))

    def test_bad_refs_raise(self):
        t = real_thesis('practical-prayers')
        for bad in ('exclusion/9', 'nope', 'structure/sections_plan/99', 'products/nothing'):
            with self.assertRaises(ValueError):
                check.resolve_thesis_ref(t, bad)


class DecisionFlowTests(unittest.TestCase):
    def test_decide_appends_valid_line(self):
        # copy a project into tmp — decide writes into ROOT/projects
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / 'projects' / 'demo').mkdir(parents=True)
            (tmp / 'schemas').mkdir()
            for s in ('thesis.schema.json', 'decision.schema.json'):
                (tmp / 'schemas' / s).write_bytes((ROOT / 'schemas' / s).read_bytes())
            thesis = {'version': '1.0', 'book': 'demo', 'title': 'Demo',
                      'template': 'prayer-book', 'style': 'canonical',
                      'claim': 'x' * 90,
                      'structure': {'sections': 1, 'entries_per_section': 1, 'total_entries': 1,
                                    'sections_plan': [{'id': 'one', 'purpose': 'the one section'}]},
                      'inclusion': ['entries must be sourced and justified clearly'],
                      'exclusion': ['nothing unsourced may ever appear in this book at all'],
                      'products': {k: {'status': 'planned', 'spec': 'spec text here'}
                                   for k in ('paperback', 'postcard', 'social', 'audiobook', 'chant')}}
            (tmp / 'projects' / 'demo' / 'thesis.json').write_text(json.dumps(thesis))
            old_root = factory.ROOT
            factory.ROOT = tmp
            try:
                import argparse
                args = argparse.Namespace(book='demo', action='add-entry', target='mantra-one',
                                          from_section=None, to_section='one',
                                          justification='owner ordered this pocket mantra into the one section',
                                          thesis_ref='structure', decided_by='owner', date='2026-11-06')
                factory.decide(args)
                lines = (tmp / 'projects' / 'demo' / 'decisions.jsonl').read_text().splitlines()
                self.assertEqual(len(lines), 1)
                d = json.loads(lines[0])
                self.assertEqual(d['thesis_ref'], 'structure')
                # second run with broken ref must fail and append nothing
                args.thesis_ref = 'exclusion/7'
                with self.assertRaises(ValueError):
                    factory.decide(args)
                self.assertEqual(len((tmp / 'projects' / 'demo' / 'decisions.jsonl').read_text().splitlines()), 1)
            finally:
                factory.ROOT = old_root

    def test_thesis_missing_fails_closed(self):
        problems = check.check_thesis('no-such-lane')
        self.assertTrue(any('thesis missing' in p for _, p in problems))


class GateOnRealBooksTests(unittest.TestCase):
    """The gate reads real state — currently BLOCKED until the restructure lands."""

    def test_thesis_gate_passes_on_real_projects(self):
        for book in ('practical-prayers', 'tantric-prayer'):
            problems = check.check_thesis(book)
            self.assertEqual(problems, [], f'{book}: {problems}')

    def test_structure_matches_thesis_after_restructure(self):
        book = ROOT / 'prints' / 'practical-prayers'
        if not (book / 'entries.json').is_file():
            self.skipTest('prints checkout unavailable')
        entries = json.loads((book / 'entries.json').read_text(encoding='utf-8'))
        book_data = json.loads((book / 'book.json').read_text(encoding='utf-8'))
        errors = check.check_structure_against_thesis(real_thesis('practical-prayers'), entries, book_data)
        # restructure landed 2026-11-06: book IS the thesis (9x4=36)
        self.assertEqual(errors, [], errors)
        self.assertEqual(len(entries), 36)


if __name__ == '__main__':
    unittest.main()
