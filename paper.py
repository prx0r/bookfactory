#!/usr/bin/env python3
"""Make private draft book and narrated video proofs from one saved essay.

The web reader downloads a scholar-media/1 packet; this runner never uploads it.
Run `python paper.py --help`. The offline Flite voice is a preview, not a
philological reading or a substitute for human review/sign-off.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from functools import lru_cache
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent
VISUALS = Path(os.environ.get('BOOKFACTORY_VISUALS', ROOT.parent / 'visuals'))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(data):
    if isinstance(data, str): data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def packet(snapshot, origin):
    return {'format':'scholar-media/1', 'status':'private-draft', 'origin':origin,
            'snapshot':snapshot, 'snapshot_sha256':sha(canonical(snapshot)),
            'text_sha256':sha(snapshot['content']['text'])}


def validate(data):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ValueError('install requirements-paper.txt for packet validation') from exc
    schema=json.loads((ROOT/'schemas/scholar-media.schema.json').read_text(encoding='utf-8'))
    errors=list(Draft202012Validator(schema).iter_errors(data))
    if errors:
        error=errors[0]
        raise ValueError(f"invalid packet field {'/'.join(map(str,error.path)) or '/'} ({error.validator})")
    if not isinstance(data,dict) or set(data)!={'format','status','origin','snapshot','snapshot_sha256','text_sha256'}:
        raise ValueError('invalid media packet fields')
    if data['format']!='scholar-media/1' or data['status']!='private-draft':
        raise ValueError('only scholar-media/1 private drafts are supported')
    origin,snap=data['origin'],data['snapshot']
    if not isinstance(origin,dict) or not isinstance(snap,dict) or set(snap)!={'kind','work','target','layer','title','content'}:
        raise ValueError('invalid source snapshot')
    if snap['kind']!='essay' or not all(isinstance(snap[k],str) for k in ('work','target','layer','title')) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}',snap['work']) or len(snap['title'])>300:
        raise ValueError('an essay with valid identifying fields is required')
    if not isinstance(snap['content'],dict) or not isinstance(snap['content'].get('text'),str) or not snap['content']['text'].strip():
        raise ValueError('essay text is empty')
    if len(snap['content']['text'])>60000:
        raise ValueError('essay exceeds the Scholar 60,000-character limit')
    if not set(snap['content']).issubset({'text','base_sha256','parent','assisted','model','agent_source','citations'}):
        raise ValueError('unrecognised essay content field')
    citations=snap['content'].get('citations',[])
    if not isinstance(citations,list) or len(citations)>10:
        raise ValueError('invalid passage references')
    for c in citations:
        if not isinstance(c,dict) or set(c)!={'work','target','t1_sha256','projection_sha256'} or not isinstance(c.get('work'),str) or not isinstance(c.get('target'),str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}',c['work']) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}',c['target']) or any(not isinstance(c.get(k),str) or not re.fullmatch(r'[a-f0-9]{64}',c[k]) for k in ('t1_sha256','projection_sha256')):
            raise ValueError('invalid passage reference')
    if len({(c['work'],c['target']) for c in citations}) != len(citations):
        raise ValueError('duplicate passage reference')
    if origin.get('type')=='scholar':
        if set(origin)!={'type','document_id','revision','author'} or not isinstance(origin['document_id'],str) or not origin['document_id'] or type(origin['revision']) is not int or origin['revision']<1 or not isinstance(origin['author'],str):
            raise ValueError('invalid saved Scholar revision')
    elif origin.get('type')=='git':
        if set(origin)!={'type','repository','commit','path','author'} or not all(isinstance(origin[x],str) for x in ('repository','commit','path','author')) or not re.fullmatch(r'[a-f0-9]{40}',origin['commit']):
            raise ValueError('invalid Git example origin')
    else:
        raise ValueError('unrecognised source origin')
    if sha(canonical(snap))!=data['snapshot_sha256'] or sha(snap['content']['text'])!=data['text_sha256']:
        raise ValueError('snapshot or text hash does not match: create a fresh packet')
    return data


def create_example(args):
    repo=args.repo.resolve(); source=args.file.resolve()
    if not source.is_file() or not source.is_relative_to(repo): raise ValueError('source must be a file inside --repo')
    relative=source.relative_to(repo).as_posix()
    commit=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
    remote=subprocess.run(['git','-C',str(repo),'remote','get-url','origin'],check=True,capture_output=True,text=True).stdout.strip()
    remote=re.sub(r'^git@github\.com:', '', remote)
    remote=re.sub(r'^https://github\.com/', '', remote)
    remote=re.sub(r'\.git$', '', remote)
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',args.repository) or remote.lower()!=args.repository.lower():
        raise ValueError('repository name does not match the Git origin')
    tracked=subprocess.run(['git','-C',str(repo),'show',f'{commit}:{relative}'],check=True,capture_output=True).stdout
    if source.read_bytes()!=tracked: raise ValueError('example source differs from the committed Git file')
    text=tracked.decode('utf-8')
    title=next((line.lstrip('# ').strip() for line in text.splitlines() if line.startswith('# ')),source.stem)
    snap={'kind':'essay','work':args.work,'target':'','layer':'','title':title,'content':{'text':text}}
    data=validate(packet(snap,{'type':'git','repository':args.repository,'commit':commit,'path':relative,'author':args.author}))
    target=args.output.resolve()
    if target.exists(): raise ValueError('output packet already exists')
    target.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
    print(f'Created private draft packet {target} from Git commit {commit[:12]}.')


def segments(text,limit=220):
    result=[];start=0
    while start<len(text):
        end=min(len(text),start+limit)
        if end<len(text):
            window=text[start:end]
            boundary=max(window.rfind('\n\n'),window.rfind('. '),window.rfind('? '),window.rfind('! '))
            if boundary>=limit//3: end=start+boundary+(2 if window[boundary]=='\n' else 1)
            else:
                boundary=max(window.rfind(' '),window.rfind('\n'))
                if boundary>0: end=start+boundary+1
        if end<=start: raise ValueError('failed to split text')
        result.append({'start':start,'end':end,'text':text[start:end]});start=end
    if ''.join(x['text'] for x in result)!=text: raise ValueError('source segmentation mismatch')
    return result


def reading_text(text):
    """Remove common Markdown decoration for speech; retain original spans separately."""
    text=re.sub(r'(?m)^\s*\|[\s:|\-]+\|\s*$', '', text)
    text=re.sub(r'(?m)^\s*[-_]{3,}\s*$', '', text)
    text=re.sub(r'(?m)^\s{0,3}#{1,6}\s+', '', text)
    text=re.sub(r'(?m)^[ \t]{0,3}>[ \t]?', '', text)
    text=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'\1', text)
    text=text.replace('**','').replace('`','').replace('|',' · ')
    text=re.sub(r'(?<!\w)\*(?=\w)|(?<=\w)\*(?!\w)', '', text)
    return re.sub(r'\s+',' ',text).strip()


def run(cmd):
    try: subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f'{Path(cmd[0]).name} failed: {exc.stderr.decode(errors="replace")[-1000:]}') from exc


def clock(seconds):
    ms=round(seconds*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


@lru_cache(maxsize=8)
def font_coverage(path):
    from fontTools.ttLib import TTFont
    with TTFont(path) as font:
        return frozenset(font.getBestCmap())


def media_frame(text,title,index,total,fonts,dest):
    from PIL import Image, ImageDraw, ImageFont
    fallbacks=[fonts/'CormorantGaramond[wght].ttf',fonts/'TiroDevanagariSanskrit-Regular.ttf',Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    # Refuse missing glyphs rather than silently drawing replacement boxes.
    chars={ord(c) for c in text+title if not c.isspace() and ord(c)>=32}
    chosen=None
    for candidate in fallbacks:
        if candidate.is_file() and chars.issubset(font_coverage(str(candidate))): chosen=candidate;break
    if chosen is None: raise ValueError(f'no installed font covers every character on slide {index}; choose a supported font')
    image=Image.new('RGB',(1280,720),'white');d=ImageDraw.Draw(image)
    heading=ImageFont.truetype(str(chosen),28);footer=ImageFont.truetype(str(chosen),22)
    # Shrink only as needed; never paint text outside the safe area.
    for size in (40,36,32,28,24):
        font=ImageFont.truetype(str(chosen),size);lines=[]
        for source_line in text.splitlines() or ['']:
            words=source_line.split();line=''
            if not words: lines.append('');continue
            for word in words:
                test=(line+' '+word).strip()
                if d.textlength(test,font=font)<=1080:line=test;continue
                if line:lines.append(line);line=''
                while word and d.textlength(word,font=font)>1080:
                    n=len(word)
                    while n>1 and d.textlength(word[:n],font=font)>1080:n-=1
                    lines.append(word[:n]);word=word[n:]
                line=word
            if line:lines.append(line)
        lineheight=int(size*1.35)
        if len(lines)*lineheight<=430:break
    else: raise ValueError(f'slide {index} does not fit the text area')
    safe_title=title
    while safe_title and d.textlength(safe_title,font=heading)>900:safe_title=safe_title[:-1]
    d.text((70,52),safe_title,font=heading,fill='#38332d');d.line((70,100,1210,100),fill='#c9c1b8',width=2)
    y=128
    for line in lines:d.text((80,y),line,font=font,fill='#17140f');y+=lineheight
    d.line((70,642,1210,642),fill='#c9c1b8',width=2)
    d.text((75,660),f'DRAFT · OFFLINE VOICE · {index}/{total}',font=footer,fill='#76736e')
    image.save(dest)


def video(essay,work,fonts,out):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'): raise ValueError('ffmpeg and ffprobe are required')
    pieces=segments(essay['text']);duration=0;records=[];subs=[];pcm=[];transcript=[]
    for i,piece in enumerate(pieces,1):
        phrase=reading_text(piece['text'])
        if not phrase: continue
        text_file=work/f'{i:04d}.txt';text_file.write_text(phrase,encoding='utf-8')
        wav=work/f'{i:04d}.wav'
        # Temporary path is generated by us, and is not interpolated by a shell.
        run(['ffmpeg','-v','error','-f','lavfi','-i',f'flite=voice=slt:textfile={text_file}','-ar','22050','-ac','1','-c:a','pcm_s16le','-y',str(wav)])
        with wave.open(str(wav),'rb') as w:
            if w.getframerate()!=22050 or w.getsampwidth()!=2 or w.getnchannels()!=1: raise ValueError('unexpected synthesized audio format')
            frames=w.readframes(w.getnframes());seconds=w.getnframes()/22050
        if not frames or seconds<=0: raise ValueError(f'empty narration for segment {i}')
        image=work/f'{i:04d}.png';media_frame(phrase,essay['title'],i,len(pieces),fonts,image)
        pcm.append(frames);transcript.append(phrase)
        records.append({'start':piece['start'],'end':piece['end'],'source_sha256':sha(piece['text']),
                        'spoken_sha256':sha(phrase),'start_seconds':duration,'duration_seconds':seconds,'image':image})
        subs.append(f'{len(subs)+1}\n{clock(duration)} --> {clock(duration+seconds)}\n{phrase}\n')
        duration+=seconds
    if not records: raise ValueError('no narratable text')
    with wave.open(str(work/'audio.wav'),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(22050)
        for frames in pcm:w.writeframes(frames)
    concat=work/'slides.txt'
    concat.write_text(''.join(f"file '{x['image']}'\nduration {x['duration_seconds']:.6f}\n" for x in records)+f"file '{records[-1]['image']}'\n",encoding='utf-8')
    (out/'captions.srt').write_text('\n'.join(subs),encoding='utf-8')
    (out/'transcript.txt').write_text('\n\n'.join(transcript)+'\n',encoding='utf-8')
    run(['ffmpeg','-v','error','-f','concat','-safe','0','-i',str(concat),'-i',str(work/'audio.wav'),
         '-map','0:v:0','-map','1:a:0','-vf','fps=1,format=yuv420p','-c:v','libx264','-preset','ultrafast',
         '-tune','stillimage','-c:a','aac','-b:a','96k','-af','apad=pad_dur=1',
         '-t',f'{duration+1:.3f}','-shortest','-movflags','+faststart','-y',str(out/'video-draft.mp4')])
    (out/'segments.json').write_text(json.dumps({'offset_unit':'unicode-codepoints','segments':[{k:v for k,v in x.items() if k!='image'} for x in records]},indent=2)+'\n',encoding='utf-8')
    return duration,len(records)


def render(args):
    input_bytes=args.input.read_bytes()
    data=validate(json.loads(input_bytes.decode('utf-8')))
    source=data['snapshot'];origin=data['origin'];text=source['content']['text']
    essay={'title':source['title'] or 'Untitled','author':origin.get('author',''), 'work':source['work'],
           'revision':origin.get('revision'), 'text':text,'citations':source['content'].get('citations',[])}
    dest=args.output.resolve()
    if dest.exists(): raise ValueError('output directory already exists; choose a new one')
    dest.parent.mkdir(parents=True,exist_ok=True)
    visuals=args.visuals.resolve();renderer=visuals/'prints/bookkit/prose.py';fonts=visuals/'prints/practical-prayers/fonts'
    if not renderer.is_file(): raise ValueError('missing visuals bookkit/prose.py; check out its matching branch')
    programs={str(p):sha(p.read_bytes()) for p in (Path(__file__).resolve(),renderer)}
    spec=importlib.util.spec_from_file_location('bookkit_prose',renderer);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix='scholar-paper-',dir=dest.parent) as stage_dir, tempfile.TemporaryDirectory(prefix='scholar-paper-work-') as work_dir:
        stage=Path(stage_dir);work=Path(work_dir);os.chmod(stage,0o700)
        (stage/'source-packet.json').write_bytes(input_bytes)
        html=module.write_book(essay,stage/'book',fonts)
        try: from weasyprint import HTML, default_url_fetcher
        except ImportError as exc: raise ValueError('install WeasyPrint to generate the book PDF') from exc
        allowed=(stage/'book').resolve();denied=[]
        def local_only(url):
            parsed=urlsplit(url)
            path=Path(unquote(parsed.path)).resolve()
            if parsed.scheme!='file' or parsed.netloc not in ('','localhost') or not path.is_relative_to(allowed) or not path.is_file():
                denied.append(True)
                raise ValueError('external or outside-book resource blocked')
            return default_url_fetcher(url)
        HTML(filename=str(html),url_fetcher=local_only).write_pdf(str(stage/'book-draft.pdf'))
        if denied: raise ValueError('book proof attempted to load an external resource')
        seconds,count=video(essay,work,fonts,stage)
        if any(sha(Path(path).read_bytes())!=digest for path,digest in programs.items()):
            raise ValueError('renderer changed during the build; rerun it')
        entries=[]
        for p in sorted(stage.rglob('*')):
            if p.is_file():entries.append({'path':p.relative_to(stage).as_posix(),'sha256':sha(p.read_bytes())})
        manifest={'format':'scholar-media-result/1','status':'private-draft','source_snapshot_sha256':data['snapshot_sha256'],
                  'source_text_sha256':data['text_sha256'],'narration':'offline Flite slt; pronunciation requires human review',
                  'renderer_sha256':{'bookfactory/paper.py':programs[str(Path(__file__).resolve())],
                                     'visuals/prints/bookkit/prose.py':programs[str(renderer)]},
                  'narration_seconds':round(seconds,3),'segments':count,'files':entries,
                  'notes':['No automatic publication or sign-off.','PDF is a draft proof, not KDP approved.',
                           'Common Markdown decoration is removed for speech; source offsets and hashes refer to the unchanged original.',
                           'Captions are segment-timed; review pronunciation and timing.']}
        (stage/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        os.rename(stage,dest)
    print(f'Created private drafts in {dest}: PDF, narrated MP4, captions, source and manifest ({count} segments).')


def verify(args):
    root=args.output.resolve()
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('format')!='scholar-media-result/1' or manifest.get('status')!='private-draft':
        raise ValueError('invalid draft result manifest')
    files=manifest.get('files')
    if not isinstance(files,list) or not files: raise ValueError('missing output file list')
    seen=set()
    for entry in files:
        if not isinstance(entry,dict) or set(entry)!={'path','sha256'} or not isinstance(entry['path'],str):
            raise ValueError('invalid output file record')
        rel=Path(entry['path']);path=(root/rel).resolve()
        if rel.is_absolute() or not path.is_relative_to(root) or not path.is_file() or entry['path'] in seen:
            raise ValueError('invalid or duplicate output path')
        seen.add(entry['path'])
        if sha(path.read_bytes())!=entry['sha256']: raise ValueError(f"output hash mismatch: {entry['path']}")
    required={'source-packet.json','book-draft.pdf','video-draft.mp4','captions.srt','transcript.txt','segments.json','book/index.html'}
    if not required.issubset(seen): raise ValueError('required product missing from manifest')
    data=validate(json.loads((root/'source-packet.json').read_text(encoding='utf-8')))
    if data['snapshot_sha256']!=manifest.get('source_snapshot_sha256') or data['text_sha256']!=manifest.get('source_text_sha256'):
        raise ValueError('result refers to another source revision')
    text=data['snapshot']['content']['text']
    expected=[p for p in segments(text) if reading_text(p['text'])]
    actual=json.loads((root/'segments.json').read_text(encoding='utf-8'))
    if actual.get('offset_unit')!='unicode-codepoints' or len(actual.get('segments',[]))!=len(expected):
        raise ValueError('segment count or offset convention does not match')
    for p,record in zip(expected,actual['segments']):
        if record.get('start')!=p['start'] or record.get('end')!=p['end'] or record.get('source_sha256')!=sha(p['text']) or record.get('spoken_sha256')!=sha(reading_text(p['text'])):
            raise ValueError('segment text does not match the source')
    run(['pdfinfo',str(root/'book-draft.pdf')])
    probe=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_type,duration','-of','json',str(root/'video-draft.mp4')],check=True,capture_output=True,text=True)
    streams=json.loads(probe.stdout).get('streams',[])
    audio=next((x for x in streams if x.get('codec_type')=='audio'),None)
    if not audio or not any(x.get('codec_type')=='video' for x in streams): raise ValueError('video must contain audio and picture')
    duration=manifest.get('narration_seconds')
    if not isinstance(duration,(int,float)) or not math.isfinite(duration) or float(audio.get('duration',0))+0.05<duration:
        raise ValueError('video audio ends before narration is complete')
    print('INTEGRITY PASS: source, segment and output hashes match; video includes audio. All products remain draft.')


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    demo=sub.add_parser('package-git',help='make an example packet from an exact committed file')
    demo.add_argument('--repo',type=Path,required=True);demo.add_argument('--file',type=Path,required=True)
    demo.add_argument('--repository',required=True);demo.add_argument('--work',required=True);demo.add_argument('--author',default='');demo.add_argument('--output',type=Path,required=True)
    build=sub.add_parser('render',help='render a saved-revision packet locally')
    build.add_argument('--input',type=Path,required=True);build.add_argument('--output',type=Path,required=True);build.add_argument('--visuals',type=Path,default=VISUALS)
    check=sub.add_parser('verify',help='verify a draft bundle and its source hashes')
    check.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    try:
        if args.cmd=='package-git':create_example(args)
        elif args.cmd=='render':render(args)
        else:verify(args)
    except (ValueError,OSError,RuntimeError,subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);return 1
    return 0


if __name__=='__main__':sys.exit(main())
