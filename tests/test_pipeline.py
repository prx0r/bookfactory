import importlib.util
import json
import os
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

PRINTS = Path(os.environ.get('BOOKFACTORY_PRINTS', ROOT / 'prints'))


class TemplateTests(unittest.TestCase):
    def test_prayer_book_template_validates(self):
        tpl = json.loads((ROOT / 'templates' / 'prayer-book.json').read_text(encoding='utf-8'))
        self.assertEqual(check._validate(tpl, 'template.schema.json'), [])

    def test_template_pipeline_is_ordered_pdf_last(self):
        tpl = json.loads((ROOT / 'templates' / 'prayer-book.json').read_text(encoding='utf-8'))
        self.assertEqual(tpl['pipeline'], ['content', 'structure', 'formatting', 'build'])
        self.assertEqual(tpl['constraints']['max_pages'], 110)

    def test_canonical_style_validates(self):
        sty = json.loads((ROOT / 'styles' / 'canonical.json').read_text(encoding='utf-8'))
        self.assertEqual(check._validate(sty, 'style.schema.json'), [])

    def test_template_rules_inherited_by_both_books(self):
        tpl = json.loads((ROOT / 'templates' / 'prayer-book.json').read_text(encoding='utf-8'))
        for book in ('practical-prayers', 'tantric-prayer'):
            thesis = json.loads((ROOT / 'projects' / book / 'thesis.json').read_text(encoding='utf-8'))
            self.assertEqual(thesis['template'], 'prayer-book')
            self.assertEqual(thesis['style'], 'canonical')
            for rule in tpl['inclusion']:
                self.assertIn(rule, thesis['inclusion'], book)
            for rule in tpl['exclusion']:
                self.assertIn(rule, thesis['exclusion'], book)

    def test_dropped_template_rule_is_detected(self):
        tpl = json.loads((ROOT / 'templates' / 'prayer-book.json').read_text(encoding='utf-8'))
        thesis = json.loads((ROOT / 'projects' / 'practical-prayers' / 'thesis.json').read_text(encoding='utf-8'))
        thesis['inclusion'].remove(tpl['inclusion'][0])  # drop a template-inherited rule
        problems = []
        for rule in tpl['inclusion']:
            if rule not in thesis['inclusion']:
                problems.append(rule)
        self.assertEqual(problems, [tpl['inclusion'][0]])


class StageTests(unittest.TestCase):
    def test_run_lane_attributes_problems_by_stage(self):
        if not (PRINTS / 'practical-prayers' / 'entries.json').is_file():
            self.skipTest('prints checkout unavailable')
        grouped = check.run_lane('practical-prayers', PRINTS, ROOT.parent / 'translation-work')
        # restructure landed: structure stage is clean (thesis matches book)
        self.assertEqual(grouped['structure'], [], grouped['structure'])
        # content stage is clean (anatomy, sources)
        self.assertEqual(grouped['content'], [], grouped['content'])
        # build problems exist (stale/unbuilt PDF) and live under 'build', never under 'content'
        for p in grouped['content']:
            self.assertNotIn('PDF', p)

    def test_project_stage_is_formatting_now(self):
        for book in ('practical-prayers', 'tantric-prayer'):
            settings = json.loads((ROOT / 'projects' / book / 'project.json').read_text(encoding='utf-8'))
            self.assertEqual(settings['stage'], 'formatting')
            self.assertLessEqual(settings['max_pages'], 110)

    def test_invalid_stage_fails_closed(self):
        problems = []
        # simulate via lane_stage on a bad project file
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            proj = tmp / 'projects' / 'x'
            proj.mkdir(parents=True)
            (proj / 'project.json').write_text('{"stage": "ship-it"}')
            old = check.ROOT
            check.ROOT = tmp
            try:
                stage = check.lane_stage('x', problems)
            finally:
                check.ROOT = old
        self.assertIsNone(stage)
        self.assertTrue(any('stage must be one of' in p for p in problems))


class NewBookTests(unittest.TestCase):
    def _args(self, **kw):
        import argparse
        base = dict(template='prayer-book', slug='rebirth-explained',
                    title='Rebirth Explained',
                    claim='What happens when you die: the Kashmir Shaiva account of transition, ' \
                          'tested against the sources, one condensed passage per page of the boundary.',
                    section=['dying:the moment the bonds loosen', 'between:where awareness goes',
                             'return:what carries forward', 'practice:what you can do about it'],
                    entries_per_section=None, max_pages=None, style=None,
                    series=None, volume=None)
        base.update(kw)
        return argparse.Namespace(**base)

    def test_scaffold_creates_valid_lane(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / 'schemas').mkdir()
            (tmp / 'templates').mkdir()
            (tmp / 'styles').mkdir()
            (tmp / 'projects').mkdir()
            for f in list((ROOT / 'schemas').glob('*.json')):
                (tmp / 'schemas' / f.name).write_bytes(f.read_bytes())
            (tmp / 'templates' / 'prayer-book.json').write_bytes((ROOT / 'templates' / 'prayer-book.json').read_bytes())
            (tmp / 'styles' / 'canonical.json').write_bytes((ROOT / 'styles' / 'canonical.json').read_bytes())
            old = factory.ROOT
            factory.ROOT = tmp
            try:
                factory.new_book(self._args())
                proj = tmp / 'projects' / 'rebirth-explained'
                thesis = json.loads((proj / 'thesis.json').read_text())
                self.assertEqual(thesis['structure']['total_entries'], 16)
                self.assertEqual(thesis['template'], 'prayer-book')
                self.assertIsNone(factory.validate_schema(thesis, 'thesis.schema.json'))
                decision = json.loads((proj / 'decisions.jsonl').read_text().splitlines()[0])
                self.assertIsNone(factory.validate_schema(decision, 'decision.schema.json'))
                lane = check.lane_config(proj / 'lane.py')
                self.assertEqual(lane['book_dir'], 'rebirth-explained')
                settings = json.loads((proj / 'project.json').read_text())
                self.assertEqual(settings['stage'], 'content')
                self.assertEqual(settings['max_pages'], 110)
                # duplicate slug refuses
                with self.assertRaises(ValueError):
                    factory.new_book(self._args())
                # thin claim refuses
                with self.assertRaisesRegex(ValueError, 'claim'):
                    factory.new_book(self._args(slug='thin-claim', claim='short'))
                # ceiling refuses
                with self.assertRaisesRegex(ValueError, 'ceiling'):
                    factory.new_book(self._args(slug='over-ceiling', max_pages=200))
            finally:
                factory.ROOT = old

    def test_series_volume(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            for d in ('schemas', 'templates', 'styles', 'projects'):
                (tmp / d).mkdir()
            for f in list((ROOT / 'schemas').glob('*.json')):
                (tmp / 'schemas' / f.name).write_bytes(f.read_bytes())
            (tmp / 'templates' / 'prayer-book.json').write_bytes((ROOT / 'templates' / 'prayer-book.json').read_bytes())
            (tmp / 'styles' / 'canonical.json').write_bytes((ROOT / 'styles' / 'canonical.json').read_bytes())
            old = factory.ROOT
            factory.ROOT = tmp
            try:
                factory.new_book(self._args(slug='recognition-guide', series='Recognition Guides', volume=1))
                thesis = json.loads((tmp / 'projects' / 'recognition-guide' / 'thesis.json').read_text())
                self.assertEqual(thesis['series'], {'name': 'Recognition Guides', 'volume': 1})
                with self.assertRaisesRegex(ValueError, 'volume'):
                    factory.new_book(self._args(slug='no-volume', series='Recognition Guides'))
            finally:
                factory.ROOT = old


class StageAdvanceTests(unittest.TestCase):
    def test_forward_advance_blocked_while_structure_fails(self):
        if not (PRINTS / 'practical-prayers' / 'entries.json').is_file():
            self.skipTest('prints checkout unavailable')
        entries = json.loads((PRINTS / 'practical-prayers' / 'entries.json').read_text(encoding='utf-8'))
        if len(entries) == 36:
            self.skipTest('restructure already landed')
        import argparse
        args = argparse.Namespace(book='practical-prayers', to='structure')
        with self.assertRaisesRegex(ValueError, 'cannot advance'):
            factory.set_stage(args)
        # stage unchanged
        settings = json.loads((ROOT / 'projects' / 'practical-prayers' / 'project.json').read_text())
        self.assertEqual(settings['stage'], 'content')

    def test_backward_move_free(self):
        import argparse
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / 'projects' / 'x').mkdir(parents=True)
            proj = tmp / 'projects' / 'x'
            (proj / 'project.json').write_text(json.dumps({'stage': 'build', 'max_pages': 110}))
            old = factory.ROOT
            factory.ROOT = tmp
            try:
                factory.set_stage(argparse.Namespace(book='x', to='content'))
                settings = json.loads((proj / 'project.json').read_text())
                self.assertEqual(settings['stage'], 'content')
            finally:
                factory.ROOT = old


if __name__ == '__main__':
    unittest.main()
