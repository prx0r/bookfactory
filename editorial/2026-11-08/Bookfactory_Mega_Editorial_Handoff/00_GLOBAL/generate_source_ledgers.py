from pathlib import Path
import json,csv
ROOT=Path(__file__).resolve().parent.parent

def mk(folder,title,config, intro, end, notes):
    D=ROOT/folder;D.mkdir(exist_ok=True)
    ledger=[]
    for sec in config:
        for ix in range(1,sec['count']+1):
            ref=(f"{sec['siva_chapter']}.{ix}" if sec.get('siva_chapter') else f"{sec['label']} {ix}" if sec.get('independent') else f"{sec['global_start']+ix-1}" if sec.get('global_start') else f"{sec['label']}:{ix}")
            ledger.append({'canonical_id':f"{sec['slug']}-{ix:03d}",'text_ref':ref,'group':sec['label'],'role_of_group':sec['purpose'], 'sanskrit_iast':None,'sanskrit_devanagari':None,'translation_original':None,'morphology':None,'edition':None,'editor_note':None,'proof_status':'UNREVIEWED','required_before_print':['select_public_domain_print_witness','collate_full_text','verify_numbers','prepare_original_translation','grammatical_review','human_signoff','rights_record']})
    (D/'COMPLETE_SOURCE_SLOT_LEDGER.json').write_text(json.dumps({'volume':title,'note':'Complete numbered/rostered editorial index only. Empty Sanskrit and translation fields are intentional and block publication. They do not imply the original work is absent upstream.', 'total_slots':len(ledger),'groups':config,'rows':ledger},ensure_ascii=False,indent=2))
    md=f'# {title}\n\n**Editorial preface and complete source-slot ledger.** NOT a complete reconstructed Sanskrit book: verified root texts and translations have NOT been copied from the source corpus. Slots are explicitly UNREVIEWED to prevent invented verses.\n\n## Proposed preface\n\n{intro.strip()}\n\n## Why the existing specification needs correction\n\n{notes.strip()}\n\n## Complete numbered editorial table\n\n'
    for sec in config:
        md+=f"### {sec['label']}: {sec['purpose']} — {sec['count']} entries\n\n"
        items=[z for z in ledger if z['group']==sec['label']]
        md+=' | '.join(x['text_ref'] for x in items)+'\n\n'
    md+=f'## Proposed closing note\n\n{end.strip()}\n\n## Required reader-facing layout\n\nFor each unit: source-verified Sanskrit line, readable Devanāgarī, correct IAST, a faithful new English translation, only the minimum lexical clarification needed to avoid a false reading, and one short interpretive sentence when allowed by the genre. Any empty unit in this ledger BLOCKS release; no prose or filler should masquerade as the root.\n'
    (D/'EDITORIAL_PREFACE_AND_COMPLETE_INDEX.md').write_text(md)
    return len(ledger)

siva=[{'label':n,'slug':'siva-'+str(i),'count':ct,'purpose':p,'independent':True,'siva_chapter':i} for i,(n,ct,p) in enumerate([
('I Śāmbhavopāya',22,'the way of Śiva; reveal the entire sūtra sequence without an imposed theme'),
('II Śāktopāya',10,'the way of Śakti; meaning, sound and recognitional knowledge'),
('III Āṇavopāya',45,'the way of the individual, including embodied activity')],1)]
a=mk('06_Siva_Sutras','The Seventy-Seven Śiva Sūtras',siva,
'''The first sentence says that the Self is consciousness. The next sentences do not give you permission to stop thinking. They ask what knowing is, what counts as bondage, and what freedom could mean if awareness is not an object among the others. This is Vasugupta's text as transmitted through particular later commentarial witnesses, not a sequence of motivational quotations. Its brevity deserves accuracy: every consonant, every sūtra boundary, every chapter heading. Begin without assuming the path ends where your favourite phrase does.''',
'''Aphorism is not shorthand for a view already held. The seventy-seven statements form a difficult, sometimes startling work. If this small book is successful, the reader closes it with the whole scripture present, and with more accurate questions than they brought to it.''',
'''**Change title and total:** 75 → **77** in the widely used Kṣemarāja form, 22+10+45. The live `translation-work/sivasutra/passages.jsonl` source lacks canonical first-section sūtras 1.7 and 1.15 and misnumbers subsequent sūtras; this MUST be fixed upstream from a collated print witness before any printing. Retain the three original sections, rather than nine artificial equal chunks; a nine-page visual navigation can be an optional index, not an alteration of scripture. One entry/sūtra with one new, literal gloss sentence. Confirm differences against a named recension. Don't call these Abhinavagupta's own authored aphorisms: tradition attributes them to Vasugupta.''')

vbt=[]
for i,(start,end) in enumerate([(1,17),(18,34),(35,51),(52,68),(69,85),(86,102),(103,119),(120,136),(137,153),(154,163)],1):
 vbt.append({'label':f'Navigation {i}: verses {start}–{end}','slug':f'vbt-{i}','count':end-start+1,'purpose':'continuous canonical order; navigation grouping only, not an ancient chapter or dhāraṇā count','global_start':start})
b=mk('07_Vijnanabhairava','The Vijñānabhairava — A Complete Reference, Edition to Be Fixed',vbt,
'''The Goddess does not ask for an improved mood. She asks what Bhairava is. The Lord's response takes many forms: breath, intervals, sensory shocks, attention, emptiness, fullness, wonder. A reference should not turn those forms into a compulsory daily programme. It should let each instruction retain its own syntax, conditions and degree of difficulty. Read the beginning and end as carefully as the much-repeated middle. The dialogue matters; so do the moments in which it ceases to sound like a technique.''',
'''It is possible to read the full exchange without deciding to practise all its contemplations. The text is not a shopping list of altered states. Its force lies in the question that returns after every example: what, exactly, is being recognised?''',
'''**Do not print “162 complete” yet.** Several published editions number **163 ślokas**, and 112 dhāraṇās are practices rather than the total verse count. The existing 9×18 grid is an arbitrary packaging device, not source divisions. Adopt 1–163 **provisionally**, verify against KSTS 1918 and at least one additional primary witness, then generate a continuous reference. 'Practice' classifications in modern sites are editorial, not scriptural apparatus. Modern teachers' prose cannot be reproduced without rights clearance.''')

para=[{'label':'Parātrīśikā root', 'slug':'paratri','count':37,'purpose':'unbroken root sequence; verse 37 and colophon status to be established','global_start':1}]
c=mk('08_Paratrisika','The Goddess’s Question — The Parātrīśikā',para,
'''A question about the unsurpassable opens this astonishing exchange. Its answer moves through letters, powers, bodies and the conditions of knowing. Abhinavagupta's vast commentary should not be mistaken for thirty-six detachable daily prayers. Here the reader receives the root text first, in order, and a spare explanatory facing note only where it prevents a false literal reading. The textual problem at the end is a feature to adjudicate, not a reason to amputate the text.''',
'''The last numbered verse is not the end of the question. The answer has moved the reader from asking what a secret is to asking who the hearer is. The full commentary may remain on another shelf; the root does not need to become a slogan.''',
'''**HOLD title *The Goddess's Thirty-Six*.** Live upstream `paratrimshika/passages.jsonl` runs from v.2 through v.36, and its T1 header declares only 35 verses; a published Parātrīśikāvivaraṇa TOC has a root verse 37. Reconcile 36/37 with KSTS and Gnoli, including whether a final stanza is supplementary, before printing “complete”. Abhinavagupta **commented on** the root dialogue; do not credit him as the author of every root verse. Strict distinction between root verses, his commentary, his closing autobiographical verses and modern colophon.''')

poetrybase=[('Bhairavastava',10,'prayer addressed to Bhairava and its attributed closing'),('Dehasthadevatācakrastotra',16,'deities of the senses/body; decide whether prefatory maxim counts'),('Kramastotra',30,'sequence, goddess and time; verify author and stanza boundaries'),('Anuttarāṣṭikā',8,'the unsurpassable and the critique of means'),('Paramārthadvādaśikā',13,'highest truth; 12-title vs 13-count discrepancy requires edition note'),('Mahopadeśaviṃśatikā',20,'devotion, ritual paradoxes and nondual language'),('Paryantapañcāśikā',52,'long-form poem; count must be corroborated'),('Bodhapañcadaśikā',15,'Śiva, Śakti and the account of manifestation'),('Paramārthacarcā',8,'explorations of ultimate meaning; text boundary to verify')]
poetry=[{'label':name,'slug':f'poem-{i}', 'count':ct,'purpose':p,'independent':True} for i,(name,ct,p) in enumerate(poetrybase,1)]
d=mk('09_Poetry_Abhinavagupta','The Poetry Attributed to Abhinavagupta — Nine-Text Editorial Audit',poetry,
'''A philosopher may explain a doctrine and a poet may address a beloved. These hymns do not become clearer when every line is replaced with a sentence about nonduality. Let the poems be poems. A prayer's vocative, a refusal, a reproach, a question, a silence—these are acts of language. A complete collection earns its beauty by retaining their order and their distinct voices. Where authorship is uncertain, honest attribution is more beautiful than confident misnaming.''',
'''To read the poems whole is to hear the changes in their addresses. No one line can stand in for that movement. The best commentary here will be the one concise note that helps the reader hear a difficult line, then steps away.''',
'''172 is currently **spec-summed**, not independently re-collated. Source texts are nine different works and recensions. The Dehastha hymn may or may not count the prefatory 'deho devālayaḥ' as a root stanza. A “twelve-verse” title may contain 13 printed stanzas. Do not collapse these ambiguities. Attribute each hymn conservatively and audit every stanza against scanned print. **Do not add Ghaṭakarpara** as an Abhinavagupta-authored hymn: it is a separate, disputed-attribution poem historically associated with his commentary.''')

proofbase=[('Ajadapramātṛsiddhi',27,'is the knower inert?'),('Īśvarasiddhi',56,'what is universal agency and what would establish it?'),('Sambandhasiddhi',23,'what is relation and how can recognition concern it?')]
proofs=[{'label':name,'slug':f'proof-{i}', 'count':ct,'purpose':p,'independent':True} for i,(name,ct,p) in enumerate(proofbase,1)]
e=mk('10_Proofs_of_the_Self','Proofs of the Self — Utpaladeva’s Siddhi Trilogy (Draft Corpus Count)',proofs,
'''An argument differs from an invocation. It can be reconstructed, resisted, and answered. The three siddhi texts confront difficulties that recur in every philosophy of consciousness: whether awareness is inert, whether agency can be only local, and what kind of relation makes recognition possible. A faithful edition must let the Sanskrit do the argumentative work. An elegant English slogan cannot substitute for a premise, a reason and an objection.''',
'''The book should leave the reader with reasons they can repeat accurately, objections they can state fairly, and an awareness of which conclusions remain contestable. Recognition is neither secured by typography nor refuted by unfamiliar terminology.''',
'''The present 27+56+23=106 comes from the repository's own extraction, not yet confirmed against a primary print. The nine aesthetic section headings are secondary argument maps. Preserve each treatise's actual sequence, and let short marginal headings show where premises, objections and answers occur. Source attribution: **Utpaladeva**, not Abhinavagupta as original author; commentary by later writers must be distinguished from root. A student may disagree with an argument without being labelled unreceptive.''')

report={'siva_sutra_slots':a,'vijnanabhairava_slots':b,'paratrisika_slots':c,'poetry_slots':d,'proofs_slots':e}
(ROOT/'00_GLOBAL'/'SOURCE_LEDGER_TOTALS.json').write_text(json.dumps(report,indent=2))
print(report, 'sum',sum(report.values()))
