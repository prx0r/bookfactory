import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('paper',ROOT/'paper.py')
paper=importlib.util.module_from_spec(spec);spec.loader.exec_module(paper)


class PaperTests(unittest.TestCase):
    def snapshot(self):
        return {'kind':'essay','work':'ipvv','target':'p01','layer':'l3','title':'Śiva',
                'content':{'text':'A source with Śiva, emoji 🙏, and exact line breaks.\n\nNext paragraph.'}}
    def origin(self):return {'type':'scholar','document_id':'essay:one','revision':2,'author':'Alice'}

    def test_segments_cover_source_once_and_keep_unicode(self):
        source=('śiva 🙏 '+('x'*280)+'\n\n')*3
        pieces=paper.segments(source)
        self.assertEqual(''.join(x['text'] for x in pieces),source)
        self.assertEqual(pieces[0]['start'],0)
        self.assertEqual(pieces[-1]['end'],len(source))
        self.assertTrue(all(x['end']-x['start']<=220 for x in pieces))
        self.assertTrue(all(a['end']==b['start'] for a,b in zip(pieces,pieces[1:])))

    def test_tampered_text_and_metadata_cannot_pass(self):
        p=paper.packet(self.snapshot(),self.origin());paper.validate(p)
        p['snapshot']['content']['text']+=' changed'
        with self.assertRaisesRegex(ValueError,'hash does not match'):paper.validate(p)
        p=paper.packet(self.snapshot(),self.origin());p['snapshot']['title']='Different title'
        with self.assertRaisesRegex(ValueError,'hash does not match'):paper.validate(p)
        p=paper.packet(self.snapshot(),self.origin());p['status']='published'
        with self.assertRaises(ValueError):paper.validate(p)

    def test_browser_packet_is_accepted_by_python_without_hash_drift(self):
        js=ROOT.parent/'svread/scholar-media.js'
        if not js.is_file():self.skipTest('svread checkout not present')
        code='''globalThis.crypto=require('node:crypto').webcrypto;
require(process.argv[1]);
ScholarMedia.createPacket({id:'essay:one',revision:2,kind:'essay',work:'ipvv',target:'p01',layer:'l3',title:'Śiva',content:{text:'A source with Śiva, emoji 🙏, and exact line breaks.\\n\\nNext paragraph.'}},{id:'u1',display_name:'Alice'}).then(p=>process.stdout.write(JSON.stringify(p)));'''
        result=subprocess.run(['node','-e',code,str(js)],check=True,capture_output=True,text=True)
        data=paper.validate(json.loads(result.stdout))
        self.assertEqual(data['snapshot'],self.snapshot());self.assertEqual(data['origin'],self.origin())

    def test_prose_escapes_html_and_renders_tables(self):
        path=ROOT.parent/'visuals/prints/bookkit/prose.py'
        if not path.is_file():self.skipTest('visuals checkout not present')
        spec=importlib.util.spec_from_file_location('prose',path);prose=importlib.util.module_from_spec(spec);spec.loader.exec_module(prose)
        out=prose.make_html({'title':'<script>x</script>','text':'# Title\n\n<script>alert(1)</script>\n\n![private](https://example.invalid/pixel)\n\n| A | B |\n|---|---|\n| 1 | 2 |','work':'ipvv'})
        self.assertNotIn('<script>',out);self.assertIn('&lt;script&gt;',out)
        self.assertNotIn('<img',out);self.assertIn('Image reference',out)
        self.assertIn('<table>',out)

    def test_speech_text_removes_markup_without_inventing_words(self):
        self.assertEqual(paper.reading_text('## A title\n\n**Śiva** and `light`'), 'A title Śiva and light')
        self.assertEqual(paper.reading_text('> A quoted line\n> continues.'), 'A quoted line continues.')

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);source=base/'packet.json';target=base/'existing';target.mkdir();(target/'keep').write_text('untouched')
            source.write_text(json.dumps(paper.packet(self.snapshot(),self.origin())))
            class Args:input=source;output=target;visuals=ROOT.parent/'visuals'
            with self.assertRaisesRegex(ValueError,'already exists'):paper.render(Args())
            self.assertEqual((target/'keep').read_text(),'untouched')


if __name__=='__main__':unittest.main()
