from pathlib import Path
import json, re, hashlib
ROOT=Path(__file__).resolve().parent.parent
out={'date':'2026-11-08','status':'EDITORIAL_CANDIDATES_NOT_COMMERCIALLY_CLEARED','checks':{},'warnings':[],'failures':[]}
for p,n,key in [('01_Tantric_Prayer/candidate_guiderows.json',36,'tantric_guide_entries'),('04_Recognition_Manual/candidate_36_spreads.json',36,'recognition_spreads'),('05_Tantrasara_Essence/candidate_36_slots.json',36,'tantrasara_selection_slots')]:
 x=json.loads((ROOT/p).read_text());
 if isinstance(x,list): m=len(x)
 elif isinstance(x,dict): m=len(x.get('rows',x.get('entries',x.get('spreads',x.get('slots',[])))))
 else: m=-1
 out['checks'][key]={'actual':m,'expected':n,'pass':m==n};
 if m!=n:out['failures'].append(f'{key} mismatch {m} != {n}')
p=ROOT/'03_Parables_of_Recognition/FULL_36_STORIES.md'
s=p.read_text(); matches=list(re.finditer(r'(?m)^## (\d\d)\. (.+)$',s));out['checks']['original_parables']={'actual':len(matches),'expected':36,'pass':len(matches)==36}
if len(matches)!=36:out['failures'].append('original parables != 36')
lengths=[]
for i,x in enumerate(matches):
 end=matches[i+1].start() if i<len(matches)-1 else len(s)
 chunk=s[x.end():end];story=chunk.split('*Art brief:*')[0];lengths.append(len(story.split()))
out['checks']['parable_story_word_count']={'minimum':min(lengths),'maximum':max(lengths),'mean':round(sum(lengths)/len(lengths),1),'all_between_150_and_400':all(150<=n<=400 for n in lengths)}
if not all(150<=n<=400 for n in lengths):out['warnings'].append('Some stories fall outside 150-400 words')
ls=(ROOT/'02_Learn_Sanskrit/FULL_TEN_LESSON_MANUSCRIPT.md').read_text();num=len(re.findall(r'(?m)^## Lesson (\d+)\b',ls));out['checks']['sanskrit_lessons']={'actual':num,'expected':10,'pass':num==10}
if num!=10:out['failures'].append('sanskrit lesson count != 10')
tot=0
for folder,n in [('06_Siva_Sutras',77),('07_Vijnanabhairava',163),('08_Paratrisika',37),('09_Poetry_Abhinavagupta',172),('10_Proofs_of_the_Self',106)]:
 x=json.loads((ROOT/folder/'COMPLETE_SOURCE_SLOT_LEDGER.json').read_text()); a=x['rows'];tot+=len(a)
 vals={r['proof_status'] for r in a};out['checks'][folder]={'actual':len(a),'expected':n,'pass':len(a)==n,'proof_statuses':sorted(vals),'sanskrit_filled':sum(1 for y in a if y['sanskrit_iast']),'english_filled':sum(1 for y in a if y['translation_original'])}
 if len(a)!=n or vals!={'UNREVIEWED'}:out['failures'].append(f'{folder} slot count/proof-status issue')
out['checks']['total_reference_slots']={'actual':tot,'expected':555,'pass':tot==555}
out['checks']['practical_prior_handoff']={'exists':(ROOT/'11_Practical_Prayers_Prior_Handoff/Practical_Prayers_Editorial_Handoff_2026-11-07.zip').is_file()}
out['checks']['global_docs_present']={'required':['README.md','00_GLOBAL/EDITORIAL_LAW.md','00_GLOBAL/CRITICAL_FINDINGS.md','00_GLOBAL/UPSTREAM_SOURCE_HANDOFF.md','00_GLOBAL/FIVE_WORKSTREAM_AGENT_BRIEF.md'],'all_present':all((ROOT/x).exists() for x in ['README.md','00_GLOBAL/EDITORIAL_LAW.md','00_GLOBAL/CRITICAL_FINDINGS.md','00_GLOBAL/UPSTREAM_SOURCE_HANDOFF.md','00_GLOBAL/FIVE_WORKSTREAM_AGENT_BRIEF.md'])}
out['warnings']+=['Reference worklists are intentionally UNREVIEWED: NOT five finished translations.','No rights, source-witness or human approval is implied by a passing package QA.','No PDFs were generated or tested in this handoff.']
(ROOT/'00_GLOBAL/QUALITY_REPORT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
for k,v in out['checks'].items():print(k,v)
if out['failures']:raise SystemExit('FAILURES: '+str(out['failures']))
