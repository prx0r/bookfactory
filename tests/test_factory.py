import importlib.util
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('factory',ROOT/'factory.py')
factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
check_spec=importlib.util.spec_from_file_location('factory_check',ROOT/'check.py')
check=importlib.util.module_from_spec(check_spec);check_spec.loader.exec_module(check)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.work=self.root/'demo'
        (self.work/'data').mkdir(parents=True)
        self.source='śivaḥ prakāśaḥ / sa eva ātmā'
        (self.work/'SOURCE.txt').write_text(self.source,encoding='utf-8')
        self.row={'verse_id':'demo-v01','sanskrit_cite':'śivaḥ prakāśaḥ | sa eva ātmā','lines':['The first line.','The second line.'],'needs':['human-review']}
        (self.work/'data/demo.l3.json').write_text(json.dumps([self.row],ensure_ascii=False),encoding='utf-8')
        (self.work/'passages.jsonl').write_text(json.dumps({'locator':'demo-p01','sanskrit':self.source},ensure_ascii=False)+'\n',encoding='utf-8')
        (self.work/'GATE.json').write_text(json.dumps({'demo-p01':{'deterministic_gate':'BLOCKED'}}),encoding='utf-8')
    def tearDown(self): self.tmp.cleanup()

    def test_exact_verse_gate_and_line(self):
        c=factory.extract(self.root,'demo','demo-v01:2','l3','demo-p01')
        self.assertEqual(c['english_lines'],['The second line.'])
        self.assertEqual(c['source_match'],'normalized-match')
        self.assertEqual(c['deterministic_gate']['status'],'BLOCKED')
        self.assertEqual(c['human_review'],'not-established')
        self.assertEqual(c['commercial_rights'],'not-established')
        self.assertEqual(len(c['inputs']),4)

    def test_mismatched_gate_does_not_bind(self):
        (self.work/'passages.jsonl').write_text(json.dumps({'locator':'demo-p01','sanskrit':'unrelated'})+'\n')
        with self.assertRaisesRegex(ValueError,'does not unambiguously contain'):
            factory.extract(self.root,'demo','demo-v01','l3','demo-p01')

    def test_duplicate_or_unrecognised_verse_fails(self):
        (self.work/'data/other.l3.json').write_text(json.dumps([self.row]))
        with self.assertRaisesRegex(ValueError,'expected one'):
            factory.extract(self.root,'demo','demo-v01')
        with self.assertRaisesRegex(ValueError,'expected one'):
            factory.extract(self.root,'demo','demo-v99')
        with self.assertRaises(ValueError): factory.extract(self.root,'../demo','demo-v01')

    def test_path_traversal_and_symlink_rejected(self):
        outside=self.root.parent/'not-under-root'
        outside.write_text('x')
        try:
            (self.root/'link').symlink_to(outside)
            for path in ('../not-under-root','link'):
                with self.assertRaises(ValueError): factory.relative_file(self.root,path)
        finally: outside.unlink()

    def test_schema_rejects_claims_without_required_rights_fields(self):
        malformed={'version':'1.0','asset_id':'seal','file':{},'origin':{},'rights':{'commercial_use':'allowed'},'allowed_uses':['book-interior'],'alt':'seal'}
        with self.assertRaisesRegex(ValueError,'schema asset'):
            factory.validate_schema(malformed,'asset.schema.json')

    def test_untrusted_lane_is_not_executed(self):
        lane=self.root/'lane.py'; sentinel=self.root/'executed'
        lane.write_text(f'open({str(sentinel)!r}, "w").write("bad")\nLANE = {{}}\n')
        with self.assertRaises(ValueError): check.lane_config(lane)
        self.assertFalse(sentinel.exists())

    def test_queued_lane_cannot_pass(self):
        problems=check.check_content('demo',{'book_dir':None},self.root,None)
        self.assertTrue(any('queued lane' in s for _,s in problems))

    def test_asset_import_binds_bytes_and_rights(self):
        from PIL import Image
        repo=self.root/'video';repo.mkdir()
        subprocess.run(['git','init','-q',str(repo)],check=True)
        subprocess.run(['git','-C',str(repo),'config','user.name','Fixture'],check=True)
        subprocess.run(['git','-C',str(repo),'config','user.email','fixture@example.invalid'],check=True)
        subprocess.run(['git','-C',str(repo),'remote','add','origin','https://github.com/example/video.git'],check=True)
        image=repo/'seal.png';Image.new('RGB',(20,20),'white').save(image)
        subprocess.run(['git','-C',str(repo),'add','seal.png'],check=True)
        subprocess.run(['git','-C',str(repo),'commit','-qm','fixture'],check=True)
        commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
        book=self.root/'book';book.mkdir();(book/'book.json').write_text('{}')
        data={'version':'1.0','asset_id':'seal','file':{'path':'seal.png','sha256':factory.digest(image),'media_type':'image/png'},
              'origin':{'repository':'example/video','commit':commit,'project_ref':'chapter-one'},
              'rights':{'commercial_use':'unknown','holder':'','evidence':''},'allowed_uses':['book-interior'],'alt':'Seal'}
        manifest=self.root/'asset.json';manifest.write_text(json.dumps(data))
        args=SimpleNamespace(manifest=manifest,asset_root=repo,book_dir=book,preview=False,set_opening=True)
        with self.assertRaisesRegex(ValueError,'commercial rights'):
            factory.import_asset(args)
        args.preview=True
        factory.import_asset(args)
        opening=json.loads((book/'book.json').read_text())['opening_image']
        self.assertTrue(opening['draft_only'])
        self.assertEqual(factory.digest(book/opening['path']),factory.digest(image))
        image.write_bytes(b'altered')
        with self.assertRaisesRegex(ValueError,'do not match'):
            factory.import_asset(args)

    def test_handoff_detects_changed_source_or_output(self):
        prints=self.root/'prints';prints.mkdir()
        for i in range(5): (prints/f'render-{i}').write_text(str(i))
        output=self.root/'products';output.mkdir()
        for i in range(5): (output/f'out-{i}').write_text(str(i))
        c=factory.extract(self.root,'demo','demo-v01','l3','demo-p01')
        c.update({'outputs':[factory.record(output/f'out-{i}',output) for i in range(5)],
                  'renderer':{'commit':None,'input_files_dirty':None},
                  'renderer_files':[factory.record(prints/f'render-{i}',prints) for i in range(5)],
                  'factory_git':{'commit':None,'input_files_dirty':None},
                  'factory_files':[factory.record(ROOT/p,ROOT) for p in ('factory.py','schemas/quote-handoff.schema.json')],
                  'render_backend':'chrome','runtime':{'python':'3','indic_transliteration':'1','weasyprint':None},'note':'draft'})
        manifest=output/'manifest.json';manifest.write_text(json.dumps(c))
        args=SimpleNamespace(manifest=manifest,prints=prints,translations=self.root)
        factory.verify_handoff(args)
        (output/'out-0').write_text('tampered')
        with self.assertRaisesRegex(ValueError,'hash mismatch'): factory.verify_handoff(args)


class ActualPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/'prints/kdp_preflight.py'
        if not path.exists(): raise unittest.SkipTest('prints checkout is unavailable')
        spec=importlib.util.spec_from_file_location('preflight',path)
        cls.preflight=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.preflight)
        try: import fitz
        except ImportError: raise unittest.SkipTest('PyMuPDF is unavailable')
        cls.fitz=fitz

    def pdf(self, path, bad=False):
        doc=self.fitz.open()
        font='/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'
        if not Path(font).exists(): self.skipTest('test font unavailable')
        for i in range(24):
            p=doc.new_page(width=148/25.4*72,height=210/25.4*72)
            p.insert_font(fontname='TestFont',fontfile=font)
            p.insert_text((10 if bad and i==0 else 40,60),'Readable proof text',fontname='TestFont',fontsize=6 if bad and i==0 else 10)
        doc.save(path);doc.close()

    def test_embedded_proof_passes_and_tiny_margin_text_fails(self):
        with tempfile.TemporaryDirectory() as td:
            good,bad=Path(td)/'good.pdf',Path(td)/'bad.pdf'
            self.pdf(good);self.pdf(bad,True)
            errors,_=self.preflight.preflight(str(good),110)
            self.assertEqual(errors,[])
            errors,_=self.preflight.preflight(str(bad),110)
            self.assertTrue(any('below 7pt' in x for x in errors),errors)
            self.assertTrue(any('outside KDP margins' in x for x in errors),errors)


class VisualSourceTests(unittest.TestCase):
    def test_corpus_uses_the_declared_file(self):
        path=ROOT/'prints/bookkit/engine.py'
        if not path.exists(): self.skipTest('prints checkout is unavailable')
        spec=importlib.util.spec_from_file_location('bookkit_engine',path)
        engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
        engine.deva=lambda text:'DEVA:' + text
        with tempfile.TemporaryDirectory() as td:
            book=Path(td);(book/'sources').mkdir()
            def corpus(iast): return {'chapters':[{'number':1,'verses':[{'number':1,'iast':iast}]}]}
            (book/'sources/declared.json').write_text(json.dumps(corpus('declared')))
            (book/'sources/shivastotravali_corpus.json').write_text(json.dumps(corpus('wrong copy')))
            entry={'id':'one','source_path':'sources/declared.json','corpus':[1,1]}
            loaded=engine.load_entries(book,[entry])[0]
            self.assertEqual(loaded['iast'],'declared')
            self.assertEqual(loaded['devanagari'],'DEVA:declared')
            entry['source_path']='../outside.json'
            with self.assertRaises(ValueError): engine.load_entries(book,[entry])


if __name__=='__main__': unittest.main()
