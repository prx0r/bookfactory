from pathlib import Path
import json
P=Path(__file__).parent
# Nine sections × 4; these are editorial questions / slots, not attributed paraphrases of particular Sanskrit passages
DATA='''means|What would liberation mean?|Define the goal before comparing practices|Stop beginning with techniques; first establish what the tradition means by freedom|Locate a source passage where the author distinguishes liberation from mere acquisition
means|Knowledge and ignorance|Two kinds of ignorance are not identical|The difference between mistaken judgment and embodied limitation alters what a practice can accomplish|Select from gold āhnika 1 and proof its compound morphology
means|The most immediate entry|Do not mistake proximity for ease|The direct approach to recognition needs careful exposition without making a state claim|Choose a verified source on anupāya/śāmbhavopāya
means|The usefulness of means|A means works within an actual structure of attention|Avoid ranking practitioners by allegedly superior experiences|Select a verified sequence of upāyas

tattvas|How a world appears|Manifestation is an account, not a diagram replacing experience|Explain the root distinction between a principle and the object it classifies|Choose a gold source defining tattva
 tattvas|Contraction and differentiation|The language of limitation must not imply a cosmic mistake|Name the difference between free manifestation and bound perception|Choose gold āhnika with the relevant māyā analysis
 tattvas|The limited subject|The individual is not merely a small object|Differentiate āṇu as subject-position from aṇu as dictionary 'minute'|Find a source with explicit aṇu or āṇava language
 tattvas|Freedom inside manifestation|Do not portray liberation as deletion of the 36 principles|Show how recognition can transform understanding without abolishing perceptual difference|Select gold discussion of the tattva series
body|The body as participant|Embodiment must remain concrete|Distinguish body-practice from literary body metaphor|Choose a verified practice instruction with bodily referents
body|The senses are active|Sensation is not automatically a distraction|Avoid the false move that every pleasure is already liberation|Select gold discussion of the senses
body|The breath and its intervals|Breathing is not a performance of supernatural control|Explain where breath practice sits among the means|Select a verified gold passage with no unlicensed breath retention instruction
body|A locus for attention|The body's point can be a location or an image|Do not conflate traditional nyāsa with anatomical fact|Source precise body placement from witness
mantra|Speech before words|Technical vocabulary must not float without grammar|Separate varṇa, mantra and ordinary language|Find gold passage on phonemes and manifestation
mantra|The first vowel|Phonemic symbolism is not phonological derivation|Teach the symbolic status of a only with the commentator's actual wording|Select exact cited line
mantra|Mantra and the knower|Pronunciation alone and recognition are not the same question|Keep theology from becoming an invented etymology|Choose gold mantra passage
mantra|The alphabet's body|Different orders require different witnesses|Do not substitute Mālinī for Mātṛkā without naming the tradition|Use gold body-phoneme passage
mandala|The circle of powers|The diagram is a relation, not a magic map|Describe what is represented and why|Select gold source defining cakra
mandala|Central and peripheral|The middle is a ritual position and a philosophical relation|Avoid an unsupported neural or quantum interpretation|Select sourced mandala passage
mandala|Appearance as worship|The senses can be understood as participants in offering|Distinguish text instruction from modern adaptation|Select exact ritual source
mandala|The mandala dissolves|A construction has a procedure and a completion|Show what a text means by withdrawal without describing a guaranteed experience|Select closing passage
ritual|What an offering gives|An omnipresent deity requires no food|Explain the paradox of giving to the all-pervading without erasing practice|Choose gold offering line
ritual|Whom is ritual for?|The rite does something to a practitioner|Do not claim ritual is useless when a text discusses its transformations|Choose gold instruction with stated purpose
ritual|The everyday and the initiated|Do not conceal ritual prerequisites|Distinguish a householder analogy from restricted initiation procedures|Choose permissible gold passage
ritual|How a rite ends|Dismissal and continuity are both meaningful categories|Avoid treating the end as a failure of nonduality|Choose verified source on concluding ritual
paths|Āṇavopāya|Embodied practices work with differentiated means|Do not rank this as morally inferior|Choose source with operational definition
paths|Śāktopāya|Conceptual attention can turn upon itself|Avoid describing it as merely 'thinking harder'|Choose source with precise technical example
paths|Śāmbhavopāya|A direct movement is not a guaranteed revelation|Interpret immediate will without exotic claims|Choose gold source distinguishing method
paths|Anupāya|Non-method does not make other methods frauds|State what the text actually allows|Use a source where anupāya is defined
powers|What a siddhi claims|A traditional claim is not a scientific demonstration|Present contextual meaning and textual genre first|Choose gold power-claims passage
powers|Recognition is not a spectacle|Avoid promises of visions and bodily signs|Distinguish doctrine from testimony|Select source about fruit/signs
powers|The guru and knowledge|Transmission does not erase individual critical judgment|Give technical definition only after witness check|Select gold initiation passage
powers|Freedom in action|Action need not stop when agency is recognised differently|Do not turn this into 'all actions are beyond ethics'|Choose gold reflection on liberated action
recognition|Who recognises?|The subject cannot simply be turned into an object|Distinguish grammatical first person from metaphysical self|Select gold I-consciousness passage
recognition|What is recognised?|Recognition changes the relation of knower and known|Do not claim that difference ceases phenomenologically|Select gold pratyabhijñā passage
recognition|Freedom and the world|Return to manifestation without contempt|Keep nature and moral reality present|Choose a late gold passage on freedom
recognition|The ordinary after the teaching|An accurate ending requires less explanation|Distil the final claim to a sourced paragraph|Select a gold concluding passage'''
entries=[]
for ln in DATA.splitlines():
 if not ln.strip():continue
 arr=[s.strip() for s in ln.split('|')]
 if len(arr)!=5:raise Exception((len(arr),ln))
 sect,title,one,turn,source=arr
 entries.append({'id':f'tsa-ess-{len(entries)+1:02d}','section':sect,'title':title,'editorial_thesis':one,'interpretive_constraint':turn,'source_selection_instruction':source,'selected_passage':None,'sanskrit':None,'literal_translation':None,'status':'BLOCKED_PENDING_GOLD_SOURCE'})
assert len(entries)==36
intro='''# TANTRASĀRA: THE ESSENCE — COMPLETE 36-TEACHING CONTENT ARCHITECTURE

**Status:** The 36 chapter questions and precise editorial theses below are complete **as a selection architecture**, not as 36 translated Tantrasāra passages. No original Sanskrit or source-verified English has been invented. Under the repository's 'extract-and-place' law, every unit remains **BLOCKED** until its exact witness and translated passage are chosen from gold source layers.

## Proposed opening

Abhinavagupta condensed an immense system because he believed the essential path could be understood as a single movement. It begins not with a diagram but with a question: how is liberation possible, and what must be known? The answer reaches through body, sound, world, power and rite, then returns to the one who has asked. A further condensation must preserve that argument, not display thirty-six isolated pieces of esoteric vocabulary. A book that does nothing but name a tattva has not taught it. A book that invents an easy practice has not transmitted it.

This edition will present thirty-six exact teachings, each anchored in one gold-source passage, with a literal gloss, one explanatory bridge, and the consequence for the reader. The printed order is editorial, not the historical order of all āhnikas; cross-reference every passage by actual chapter and location.

---
'''
md=intro
for i,e in enumerate(entries,1):
 if (i-1)%4==0:md+=f"\n## {e['section'].title()}\n\n"
 md+=f'''### {i:02d}. {e['title']} [{e['id']}]
**In one sentence:** {e['editorial_thesis']}.
**Editorial consequence:** {e['interpretive_constraint']}.
**Source selection instruction:** {e['source_selection_instruction']}.
**Sanskrit:** HELD until primary witness proof.  
**Translation:** HELD until grammar-derived source approval.  
**Status:** {e['status']}.

'''
md+='''## Closing proposal

The final page should be the shortest. Knowledge was introduced as the cause of freedom; the preceding pages must now have given that proposition concrete content. The reader should be able to name what ignorance means, what body and word contribute, and why the teaching does not despise the appearing world. The end of a path described in words is not the disappearance of speech, but its proper proportion.

## Blocking requirements

Do not use a06, a08 or a13 from the repo while they are labelled legacy, even if they happen to furnish an elegant quotation. Every quote needs work, āhnika, segment, source hash and rights. Reject a formula that forces 36 items by inserting the same philosophical point with another title. The goal is a precise portable map, not an exact 108-page count.
'''
(P/'FULL_36_TEACHING_SELECTION_MANUSCRIPT.md').write_text(md)
(P/'candidate_36_slots.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2))
print(len(entries))
