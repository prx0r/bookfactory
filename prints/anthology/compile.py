#!/usr/bin/env python3
"""Compile the Anuttara invocation anthology -> JSON + print-ready HTML."""

import json, html, pathlib, sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, "/home/box/Documents/patala/.venv/lib")
try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate as _tr
except Exception:
    _tr = None

META = {
    "title": "Anuttara",
    "subtitle": "Invocations of the Heart",
    "blurb": "A book of Kashmir Śaiva prayer",
    "epigraph_iast": "na tyāgī na parigrahī bhaja sukhaṃ sarvaṃ yathāvasthitaḥ",
    "epigraph_en": "Neither renouncer nor possessor — enjoy happiness, all of it, staying exactly as you are.",
    "epigraph_src": "Abhinavagupta, Anuttarāṣṭikā 1",
}

from guides import GUIDES

SOURCES = {
    "om-namah-shivaya": ("sources/namah-shivaya.json", "practice file"),
    "soham": ("sources/mantras.json", "so'haṃ entry"),
    "shivoham": ("sources/parapravesika.md", "pūrṇāhantā, par-p02–p03"),
    "bhairavastava-1": ("sources/bhairavastava.md", "bh-p01"),
    "bhairavastava-5": ("sources/bhairavastava.md", "bh-p05"),
    "anuttarastika-1": ("sources/anuttarastika.md", "anu-p01"),
    "anuttarastika-8": ("sources/anuttarastika.md", "anu-p08"),
    "pancashloki-1": ("sources/pancashloki.md", "pan-p01"),
    "pancashloki-2": ("sources/pancashloki.md", "pan-p02"),
    "somananda": ("sources/mealtime-yajna.md", "Śivadṛṣṭi 7.103 (provisional)"),
    "parapravesika": ("sources/parapravesika.md", "par-p01"),
    "spandakarika-1": ("sources/spanda.md", "Spandakārikā 1.1"),
    "spandasandoha-1": ("sources/spandasandoha.md", "v.1"),
    "paratrimshika-1": ("sources/paratrimshika.md", "para-p01"),
    "sst-17-19": ("sources/sivastotravali_corpus.json", "17.19"),
    "sst-17-26": ("sources/sivastotravali_corpus.json", "17.26"),
    "sst-9-14": ("sources/sivastotravali_corpus.json", "9.14"),
    "sst-16-8": ("sources/sivastotravali_corpus.json", "16.8"),
    "sst-2-1": ("sources/sivastotravali_corpus.json", "2.1"),
    "sst-2-8": ("sources/sivastotravali_corpus.json", "2.8"),
    "sst-2-19": ("sources/sivastotravali_corpus.json", "2.19"),
    "sst-2-25": ("sources/sivastotravali_corpus.json", "2.25"),
    "sst-20-9": ("sources/sivastotravali_corpus.json", "20.9"),
}

SECTIONS = [
    ("mangala", "I", "Maṅgala", "Invocation"),
    ("nama", "II", "Nāma", "The Name"),
    ("stuti", "III", "Stuti", "Invocations of Śiva"),
    ("shakti", "IV", "Śakti", "The Goddess"),
    ("kriya", "V", "Kriyā", "The Daily Practice"),
    ("namaskara", "VI", "Namaskāra", "Salutations"),
    ("shanti", "VII", "Śānti", "Peace"),
]

ENTRIES = [
# ---------------- I. MANGALA ----------------
dict(id="ganesha-pranama", section="mangala", title="Invocation to Gaṇeśa",
 source="Traditional praṇāma",
 iast="śuklāmbaradharaṁ viṣṇuṁ śaśivarṇaṁ caturbhujam | prasannavadanaṁ dhyāyet sarvavighnopaśāntyaye ||",
 en="Clothed in white, all-pervading, moon-hued, four-armed, with a serene face — meditate on him for the stilling of every obstacle.",
 note="Gaṇeśa is invoked before the way is walked. White is sattva, the moon is reflective clarity, the four arms are the inner faculties brought to rest."),
dict(id="ganesha-vighna", section="mangala", title="Remover of Obstacles",
 source="Traditional",
 iast="vakratuṇḍa mahākāya sūryakoṭisamaprabha | nirvighnaṁ kuru me deva sarvakāryeṣu sarvadā ||",
 en="O curved-trunked one, great of body, radiant as a million suns — make me free of obstacles, O God, in every undertaking, always.",
 note="The curved trunk is the bent course of grace: nothing goes straight, and yet nothing is lost. Ask for the obstacle to be removed, not avoided."),
dict(id="ganesha-dhyana", section="mangala", title="The Single Tusked",
 source="Traditional dhyāna śloka",
 iast="agajānana padmārkaṁ gajānanaṁ aharṇiśam | anekadantaṁ bhaktānāṁ ekadantaṁ upāsmahe ||",
 en="The face born of the mountain, sun to the lotus — the elephant-faced one, day and night; many-tusked, and single-tusked for the sake of devotees, him we worship.",
 note="ekadanta, the one tusk, is the single point of attention. Many forms for the world, one point for the devotee."),
dict(id="guru-vandana", section="mangala", title="Invocation to the Guru",
 source="Traditional",
 iast="gurur brahmā gurur viṣṇuḥ gurur devo maheśvaraḥ | guruḥ sākṣāt paraṁ brahma tasmai śrī gurave namaḥ ||",
 en="The guru is Brahmā, the guru is Viṣṇu, the guru is the god Maheśvara; the guru is the supreme Brahman made visible — to that holy guru, namas.",
 note="Trika reads the guru not as a person but as the point where consciousness turns to recognise itself. The three gods are the three powers — will, knowledge, action — and the guru is their source."),
dict(id="sarasvati", section="mangala", title="Invocation to Sarasvatī",
 source="Traditional Sarasvatī vandana",
 iast="yā kundendutuṣārahāradhavalā yā śubhravastrāvṛtā | yā vīṇāvaradaṇḍamaṇḍitakarā yā śvetapadmāsanā | yā brahmācyutaśaṅkaraprabhṛtibhir devaiḥ sadā pūjitā | sā māṁ pātu sarasvatī bhagavatī niḥśeṣajāḍyāpahā ||",
 en="She who is white as jasmine, the moon, snow and a string of pearls; wrapped in bright cloth; her hands adorned with the vīṇā and the boon-giving staff; seated on a white lotus; ever worshipped by Brahmā, Acyuta, Śaṅkara and the gods — may that goddess Sarasvatī protect me, who takes away all dullness.",
 note="Sarasvatī is vāgdevī, the power of speech; in Trika the same power is the world-making throb of consciousness. Ask not for information but for the removal of jāḍya, the inertness that cannot see."),
dict(id="gayatri", section="mangala", title="Gāyatrī",
 source="Ṛgveda 3.62.10",
 iast="oṁ bhūr bhuvaḥ svaḥ | tat savitur vareṇyaṁ | bhargo devasya dhīmahi | dhiyo yo naḥ pracodayāt ||",
 en="Oṁ — earth, mid-air, heaven. We meditate on that desirable radiance of the divine Sun; may it impel our thoughts.",
 note="The oldest mantra of the light. Trika reads the three worlds as the three states — waking, dream, deep sleep — and the Sun as the witness-consciousness that lights all three."),
dict(id="purnam", section="mangala", title="The Fullness",
 source="Īśa Upaniṣad, invocation",
 iast="oṁ pūrṇam adaḥ pūrṇam idaṁ pūrṇāt pūrṇam udacyate | pūrṇasya pūrṇam ādāya pūrṇam evāvaśiṣyate ||",
 en="Oṁ. That is full, this is full. From the full the full proceeds. Taking the full from the full, the full alone remains.",
 note="The purest statement of pūrṇāhantā, the full I. Manifestation does not diminish the source; the world is the fullness in another key."),

# ---------------- II. NAMA ----------------
dict(id="om-namah-shivaya", section="nama", title="Oṁ Namaḥ Śivāya",
 source="Pañcākṣara mantra",
 iast="oṁ namaḥ śivāya",
 en="Oṁ — I bow to Śiva.",
 note="The five syllables are the five acts: naḥ creation, maḥ preservation, śi dissolution, vā concealment, ya grace. Oṁ, a+u+ṃ, is the triad of will, knowledge and action. To repeat it is to let the whole cycle turn inside you."),
dict(id="shivoham", section="nama", title="Śivo'ham",
 source="Recognition mantra",
 iast="śivo'ham",
 en="I am Śiva.",
 note="The recognition, pratyabhijñā, in two words. Not I will become Śiva — the I that says it is already the light."),
dict(id="soham", section="nama", title="So'ham",
 source="The breath mantra",
 iast="so'ham",
 en="That am I.",
 note="The natural mantra of the breath: sa on the in-breath, haṃ on the out — haṃsa. You do not recite it; you notice it has been reciting you."),
dict(id="aham-brahmasmi", section="nama", title="Ahaṁ Brahmāsmi",
 source="Bṛhadāraṇyaka Upaniṣad 1.4.10",
 iast="ahaṁ brahmāsmi",
 en="I am Brahman.",
 note="Read in the Trika key, the I is not the ego but the full, self-luminous Śiva. The mahāvākya is a recognition, not a claim."),
dict(id="mrityunjaya", section="nama", title="Mṛtyuñjaya",
 source="Ṛgveda 7.59.12",
 iast="oṁ tryambakaṁ yajāmahe sugandhiṁ puṣṭivardhanam | urvārukam iva bandhanān mṛtyor mukṣīya māmṛtāt ||",
 en="Oṁ. We worship the three-eyed one, fragrant, who increases fullness. As a cucumber is freed from its vine, may we be freed from death — and not from immortality.",
 note="Trika reads mṛtyu as the death-contraction: the ego that thinks it can die. The vine is the bond of limited identity; the freedom asked is not escape from life but release into the deathless."),
dict(id="karpura-gaura", section="nama", title="The Camphor-White Lord",
 source="Traditional Śiva dhyāna",
 iast="karpūragauraṁ karuṇāvatāraṁ saṁsārasāraṁ bhujagendrahāram | sadāvasantaṁ hṛdayāravinde bhavaṁ bhavānīsahitaṁ namāmi ||",
 en="Camphor-white, the very descent of compassion, the essence of the world, wearing the king of serpents as a garland — ever dwelling in the lotus of the heart, I bow to Bhava with Bhavānī beside him.",
 note="The white of camphor is the brightness of pure consciousness; the serpent garland is the coiled power worn openly. Bhava with Bhavānī is not two: the one heart."),

# ---------------- III. STUTI ----------------
dict(id="bhairavastava-1", section="stuti", title="Refuge in Bhairava",
 source="Abhinavagupta, Bhairavastava 1",
 iast="vyāptacarācarabhāvaviśeṣaṁ cinmayam ekam anantam anādim | bhairavanātham anāthaśaraṇyaṁ tvanmayacittatayā hṛdi vande ||",
 en="Pervading every particular state of the moving and unmoving, made of consciousness, one, endless, beginningless — Bhairava the Lord, refuge of the refugeless: with a mind become you, in the heart I bow.",
 note="Abhinavagupta opens: the Lord is not a being among beings but the consciousness that pervades every state. The bow is made by the mind becoming him, not by the body bending."),
dict(id="bhairavastava-5", section="stuti", title="I Never Fear",
 source="Abhinavagupta, Bhairavastava 5",
 iast="ittham upoḍhabhavanmayasaṁviddīdhitidāritabhūritamisraḥ | mṛtyuyamāntakakarmapiśācair nātha namo'stu na jātu bibhemi ||",
 en="Thus, with the great darkness torn open by the rays of the consciousness become you — Lord, namas; I never fear, not from death, from Yama, from the ender, from the ghosts of karma.",
 note="Fearlessness is not courage; it is what remains when the darkness has been burned by awareness. The devotee still names death and karma, but salutes them instead of fleeing."),
dict(id="anuttarastika-1", section="stuti", title="No Method",
 source="Abhinavagupta, Anuttarāṣṭikā 1",
 iast="saṁkrāmo 'tra na bhāvanā na ca kathāyuktir na carcā na ca dhyānaṁ vā na ca dhāraṇā na ca japābhyāsaprayāso na ca | tat kiṁ nāma suniścitaṁ vada paraṁ satyaṁ ca tacchrūyatāṁ na tyāgī na parigrahī bhaja sukhaṁ sarvaṁ yathāvasthitaḥ ||",
 en="There is no crossing over here — no contemplation, no connecting speech, no discussion, no visualization, no steadying, no effort of japa. So what is decided? Speak the supreme truth; hear it: not a renouncer, not a possessor — enjoy happiness, all of it, staying exactly as you are.",
 note="The anupāya, the no-means. When every method is denied, what is left is recognition: you are already what you seek. Staying as you are is not passivity; it is the end of the search."),
dict(id="anuttarastika-8", section="stuti", title="Lordhood",
 source="Abhinavagupta, Anuttarāṣṭikā 8",
 iast="yat satyaṁ yad asatyam alpabahulaṁ nityaṁ na nityaṁ ca yat yan māyāmalinaṁ yad ātmavimalaṁ ciddarpaṇe rājate | tat sarvaṁ svavimarśasaṁvidudayād rūpaprakāśātmakaṁ jñātvā svānubhavādhirūḍhamahimā viśveśvaratvaṁ bhaja ||",
 en="Whatever is real and whatever is unreal, little or much, eternal or not; whatever shines stained by māyā or pure as the self in the mirror of consciousness — know it all to be the light of form arising from one's own self-awareness; then, with a glory mounted on your own experience, enjoy the Lordhood of the universe.",
 note="The last verse of the Anuttarāṣṭikā: the world is neither to be rejected nor grasped, but seen as the shining of one's own awareness. Lordhood is not a title but the taste of that seeing."),
dict(id="pancashloki-1", section="stuti", title="The Offering of Pride",
 source="Abhinavagupta, Pañcaślokī 1",
 iast="yat satyaṁ tu mayā kṛtaṁ mama vibho kṛtyaṁ tu nātaḥ paraṁ yan manmānam aiśapādakamale bhaktyā mayaivārpitam | sarvasvam ata evam etad itaran nāsīva jānāmy atas tyaktvā kṣipram anāthanātha karuṇāsindho prasanno bhava ||",
 en="Whatever I have truly done, O Lord — my duty goes no further than this: my pride has been offered by me, with devotion, at the lotus feet of the Lord. This is my all; apart from this I know nothing else. Therefore, casting everything else aside, quickly — O protector of the refugeless, O ocean of compassion — be pleased.",
 note="The one offering that costs everything: not wealth, but pride. Abhinavagupta asks for nothing except that the offering be accepted."),
dict(id="pancashloki-2", section="stuti", title="Victory at the Door",
 source="Abhinavagupta, Pañcaślokī 2",
 iast="maheśa tvaddvāri sphuratu rucirā vāg atitarāṁ mama eṣā nirdoṣaṁ jaya jaya maheśeti satatam | śivā saiṣā vāṇī bhavatu śivadā mahyam aniśaṁ maheśanāthaṁ māṁ śaraṇada sanāthaṁ kuru vibho ||",
 en="O Maheśa, may this lovely speech of mine flash forth at your door, faultlessly, again and again: Victory, victory to Maheśa! May this auspicious speech be giver of bliss to me, unceasingly. O Lord, O giver of refuge, make me — whose protector is Maheśanātha — to have a protector.",
 note="The prayer of one who has nothing to offer but speech. Make me to have a protector is the whole of śaraṇāgati: not to become strong, but to be held."),
dict(id="somananda", section="stuti", title="Śiva Bows to Śiva",
 source="Somananda, Śivadṛṣṭi 7.103",
 iast="asmadrūpa samāviṣṭaḥ svātmanātma nivāraṇe | śivaḥ karotu nijayā namaḥ śaktyā tatātmane ||",
 en="Śiva, having entered the form that is myself, bows — by his own power — to Śiva, for the removal of the obstacle that is himself.",
 note="The most Trika of prayers: the one who bows, the one bowed to, and the obstacle removed are all Śiva. Nothing is outside the recognition, not even the thing that blocks it."),
dict(id="parapravesika", section="stuti", title="The Heart of the Supreme",
 source="Kṣemarāja, Parāprāveśikā, opening",
 iast="viśvātmikāṁ taduttirṇāṁ hṛdayaṁ parameśituḥ | parādiśaktirūpeṇa sphurantīṁ saṁvidaṁ numaḥ ||",
 en="We bow to consciousness itself — the heart of the supreme Lord, whose very self is the world, and which yet transcends it, pulsing in the form of the supreme power.",
 note="Kṣemarāja opens by bowing to consciousness: not to a god, but to the heart that is both the world and beyond it. This is the doorway into the Supreme."),
dict(id="spandakarika-1", section="stuti", title="The Wheel of Powers",
 source="Vasugupta, Spandakārikā 1.1",
 iast="yasyonmeṣanimeṣābhyāṁ jagataḥ pralayodayau | taṁ śakticakravibhavaprabhavaṁ śaṅkaraṁ stumaḥ ||",
 en="To him by whose opening and closing the world dissolves and arises — to Śaṅkara, source of the glory of the wheel of powers, we sing.",
 note="The opening of the Spandakārikā. The opening and closing is the pulse, spanda, of consciousness: the world appears and dissolves in the blink of the one who sees."),
dict(id="spandasandoha-1", section="stuti", title="He Alone Wins",
 source="Kṣemarāja, Spandasandoha 1",
 iast="sa jayati śiva ekaḥ spandavān svapratiṣṭhaḥ yo'ntarvaktraṁ rasayati",
 en="He alone wins — Śiva, possessor of the pulse, self-established, who makes the inner face taste.",
 note="A one-line victory song. The inner face is attention turned back on itself; to taste it is the whole of the practice."),

# ---------------- IV. SHAKTI ----------------
dict(id="paratrimshika-1", section="shakti", title="The Secret of the Heart",
 source="Parātrīśikā 1",
 iast="etad guhyaṁ mahāguhyaṁ kathayasva mama prabho | hṛdayasthā tu yā śaktiḥ kaulinī kulanāyikā | tām me kathaya deveśa yena tṛptiṁ vrajāmy aham ||",
 en="Tell me, Lord, this secret — the great secret: the power that dwells in the heart, the Kaulinī, the leader of the clan. Tell me that, O Lord of gods, by which I may reach fulfilment.",
 note="The Goddess asks for the secret of the heart, and the answer is the anuttara, the unsurpassed. The whole Parātrīśikā is this question and its answer."),
dict(id="devi-shakti", section="shakti", title="The Power in All Beings",
 source="Devī Māhātmya, traditional",
 iast="yā devī sarvabhūteṣu śaktirūpeṇa saṁsthitā | namastasyai namastasyai namastasyai namo namaḥ ||",
 en="The goddess who dwells in all beings in the form of power — to her, to her, to her, namas, namas.",
 note="In Trika this power in all beings is Śakti: not a goddess beside Śiva but the very throb by which consciousness knows itself. The triple namas dissolves the threefold difference."),

# ---------------- V. KRIYA ----------------
dict(id="gita-4-24", section="kriya", title="The Meal Offering",
 source="Bhagavad Gītā 4.24",
 iast="brahmārpaṇaṁ brahma havir brahmāgnau brahmaṇā hutam | brahmaiva tena gantavyaṁ brahmakarmasamādhinā ||",
 en="The offering is Brahman, the oblation is Brahman, poured by Brahman into the fire that is Brahman; Brahman alone is reached by one absorbed in the action that is Brahman.",
 note="Lakshmanjoo's mealtime yajña. Read Brahman as Śiva throughout: what you eat, the eating, the eater, and the fire of digestion are one. Say it with water in the palm before food."),
dict(id="gita-15-14", section="kriya", title="The Fire Within",
 source="Bhagavad Gītā 15.14",
 iast="ahaṁ vaiśvānaro bhūtvā prāṇināṁ deham āśritaḥ | prāṇāpānasamāyuktaḥ pacāmy annaṁ caturvidham ||",
 en="Becoming the fire of digestion, I dwell in the bodies of living beings; joined with the in-breath and the out-breath, I digest the four kinds of food.",
 note="Śiva as vaiśvānara, the inner fire: kriyā-śakti at work in the body. The meal is not merely eaten; it is cooked by consciousness."),
dict(id="gita-9-26", section="kriya", title="A Leaf, a Flower",
 source="Bhagavad Gītā 9.26",
 iast="patraṁ puṣpaṁ phalaṁ toyaṁ yo me bhaktyā prayacchati | tad ahaṁ bhaktyupahṛtam aśnāmi prayatātmanaḥ ||",
 en="Whoever offers me a leaf, a flower, a fruit or water with devotion — that offering of the pure-hearted, given with love, I eat.",
 note="Bhakti is the only currency. The smallest thing, given wholly, is the whole. In Trika the gift and the giver are already Śiva."),
dict(id="gita-18-66", section="kriya", title="The Final Refuge",
 source="Bhagavad Gītā 18.66",
 iast="sarvadharmān parityajya mām ekaṁ śaraṇaṁ vraja | ahaṁ tvāṁ sarvapāpebhyo mokṣayiṣyāmi mā śucaḥ ||",
 en="Abandoning all dharmas, take refuge in me alone. I will free you from all sins — do not grieve.",
 note="The anupāya again: when every rule is set down, only turning remains. Do not grieve is the promise that the turning is enough."),
dict(id="isha-1", section="kriya", title="All This Is Pervaded",
 source="Īśa Upaniṣad 1",
 iast="īśāvāsyam idaṁ sarvaṁ yat kiṁ ca jagatyāṁ jagat | tena tyaktena bhuñjīthā mā gṛdhaḥ kasyasvid dhanam ||",
 en="All this — whatever moves in the moving world — is pervaded by the Lord. Enjoy by renunciation; do not covet anyone's wealth.",
 note="The world is not to be fled but seen as pervaded. Enjoy by renunciation is the Trika paradox: possess nothing, and the whole is yours."),
dict(id="sst-17-19", section="kriya", title="In Every Action",
 source="Utpaladeva, Śivastotrāvalī 17.19",
 iast="anubhūyāsam īśāna pratikarma kṣaṇāt kṣaṇam | bhavatpūjāmṛtāpānamadāsvādamahāmudam ||",
 en="O Lord, may I experience, moment by moment, in every action, the great joy of drinking the nectar of your worship.",
 note="Utpaladeva's prayer for the ordinary: not more ritual, but the taste of worship inside every action. Moment by moment is the practice."),
dict(id="sst-17-26", section="kriya", title="This Body for Worship",
 source="Utpaladeva, Śivastotrāvalī 17.26",
 iast="antarullasadacchācchabhaktipīyūṣapoṣitam | bhavatpūjopayogāya śarīram idam astu me ||",
 en="May this body of mine — nourished by the clear, bright nectar of devotion rising within — be fit only for your worship.",
 note="The body is not renounced; it is turned into an instrument of worship. Nourished by devotion, it becomes the offering itself."),
dict(id="sst-9-14", section="kriya", title="At Your Cool Feet",
 source="Utpaladeva, Śivastotrāvalī 9.14",
 iast="aśeṣaviṣayāśūnyaśrīsamāśleṣasusthitaḥ | śayīyam iva śītāṅghrikuśeśayayuge kadā ||",
 en="When will I lie down — free of every object, settled in the embrace of undiminished glory — at your two cool lotus feet?",
 note="The sleep prayer. Free of every object is not blankness but the rest that remains when the mind stops reaching. The cool feet are the peace of Śiva."),
dict(id="sst-16-8", section="kriya", title="I Don't Mind",
 source="Utpaladeva, Śivastotrāvalī 16.8",
 iast="viṣamastho'pi svastho'pi rudann api hasann api | gambhīro'pi vicitto'pi bhaveyaṁ bhaktitaḥ prabho ||",
 en="In crisis or at ease, weeping or laughing, grave or unhinged — by devotion, Lord, let me be so.",
 note="The api-chain refuses resolution: sorrow and joy, sanity and its loss, are all allowed. Devotion is not the absence of any of them; it is what holds them."),

# ---------------- VI. NAMASKARA ----------------
dict(id="sst-2-1", section="namaskara", title="Fire, Moon, Sun",
 source="Utpaladeva, Śivastotrāvalī 2.1",
 iast="agnīṣomaravibrahmaviṣṇusthāvarajaṅgama | svarūpa bahurūpāya namaḥ saṁvinmayāya te ||",
 en="Fire, moon, sun, Brahmā, Viṣṇu, the moving and the unmoving — to you whose own form is many-formed, to you made of consciousness, namas.",
 note="A salutation to the many-formed one. The many forms are not a veil; they are how consciousness shows itself. The name of the many is still made of consciousness."),
dict(id="sst-2-8", section="namaskara", title="Saṁsāra and Beyond",
 source="Utpaladeva, Śivastotrāvalī 2.8",
 iast="saṁsāraikanimittāya saṁsāraikavirodhine | namaḥ saṁsārarūpāya niḥsaṁsārāya śambhave ||",
 en="To the one who is the sole cause of saṁsāra and the sole opponent of saṁsāra; to Śambhu, who is the form of saṁsāra and is beyond saṁsāra, namas.",
 note="A paradox of the recognition: the world's bondage and its release are the same Lord. There is no enemy outside."),
dict(id="sst-2-19", section="namaskara", title="All Conduct, No Conduct",
 source="Utpaladeva, Śivastotrāvalī 2.19",
 iast="dakṣiṇācārasārāya vāmācārābhilāṣiṇe | sarvācārāya śarvāya nirācārāya te namaḥ ||",
 en="To the essence of the right-hand way, to the one who longs for the left-hand way, to the all-way, to Śarva, to the wayless — to you, namas.",
 note="Every path is his, and no path is. The verse exhausts all conduct — and then the wayless remains."),
dict(id="sst-2-25", section="namaskara", title="Mass of Nectar",
 source="Utpaladeva, Śivastotrāvalī 2.25",
 iast="paramāmṛtakośāya paramāmṛtarāśaye | sarvapāramyapāramyaprāpyāya bhavate namaḥ ||",
 en="To you, the treasure of supreme nectar, the mass of supreme nectar, the goal of every goal and of the goal beyond — to you, namas.",
 note="The Name as nectar: not a word about sweetness, but the sweetness itself. The goal of every goal is the recognition that there is nothing beyond."),
dict(id="sst-20-9", section="namaskara", title="The Five Acts",
 source="Utpaladeva, Śivastotrāvalī 20.9",
 iast="sadā sṛṣṭivinodāya sadā sthitisukhāsine sadā tribhuvanāhāratṛptāya svāmine namaḥ ||",
 en="To the Master who ever delights in creation, ever sits at ease in preservation, ever is satisfied with the three worlds as food — namas.",
 note="One bow contains the five acts: creation, preservation, and the devouring that is dissolution — with grace hidden in delight and ease."),

# ---------------- VII. SHANTI ----------------
dict(id="kayena", section="shanti", title="Whatever I Do",
 source="Traditional offering verse",
 iast="kāyena vācā manasendriyair vā buddhyātmanā vā prakṛteḥ svabhāvāt | karomi yad yat sakalaṁ parasmai nārāyaṇāyeti samarpayāmi ||",
 en="Whatever I do with body, speech, mind or senses, with intellect or self, by the nature of my constitution — all of it I offer to the Supreme, to Nārāyaṇa.",
 note="The closing offering. Every act, conscious or automatic, is handed over. In the non-dual reading Nārāyaṇa is Śiva, the one who dwells in all."),
dict(id="sarve-bhavantu", section="shanti", title="May All Be Happy",
 source="Traditional śānti",
 iast="oṁ sarve bhavantu sukhinaḥ sarve santu nirāmayāḥ | sarve bhadrāṇi paśyantu mā kaścid duḥkhabhāg bhavet ||",
 en="Oṁ. May all be happy; may all be free of illness; may all see what is good; may no one be touched by sorrow.",
 note="The universal śānti. In the recognition, all is not a crowd outside; it is the one consciousness in many forms."),
dict(id="om-shanti", section="shanti", title="Oṁ Śāntiḥ",
 source="Traditional",
 iast="oṁ śāntiḥ śāntiḥ śāntiḥ",
 en="Oṁ — peace, peace, peace.",
 note="Three śāntis for the three disturbances: body, speech and mind — or the three worlds, the three powers, the three states."),
]


def deva(iast):
    if _tr is None:
        return ""
    try:
        out = _tr(iast, sanscript.IAST, sanscript.DEVANAGARI)
    except Exception:
        return ""
    # normalise the transliterator's Devanagari-Extended anusvara to the standard sign
    return out.replace("\U0000A8F3", "\u0902").replace("\U0000A8F2", "\u0901")


def build_json():
    secmap = {s[0]: {"id": s[0], "numeral": s[1], "title": s[2], "subtitle": s[3], "entries": []} for s in SECTIONS}
    for e in ENTRIES:
        out = dict(e)
        out["devanagari"] = deva(e["iast"])
        secmap[e["section"]]["entries"].append(out["id"])
    data = {"meta": META, "sections": list(secmap.values()), "entries": [
        {**e, "devanagari": deva(e["iast"]),
         "guide": GUIDES.get(e["id"], ""),
         "source_path": SOURCES.get(e["id"], (None, None))[0],
         "source_ref": SOURCES.get(e["id"], (None, None))[1]}
        for e in ENTRIES]}
    (HERE / "invocations.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def esc(s):
    return html.escape(s)


def split_paras(text, n=2):
    import re
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    if len(sents) <= n:
        return [text]
    total = sum(len(s) for s in sents)
    target = total / n
    out, cur = [], ""
    for s in sents:
        if cur and len(cur) + len(s) > target * 1.15:
            out.append(cur.strip())
            cur = s + " "
        else:
            cur += s + " "
    if cur.strip():
        out.append(cur.strip())
    return out


def type_sizes(e):
    L = max(len(e["iast"]), len(e["devanagari"]) * 0.9)
    if L > 190:
        d, en = "15pt", "13.5pt"
    elif L > 150:
        d, en = "16.5pt", "14pt"
    elif L > 110:
        d, en = "18pt", "14.5pt"
    else:
        d, en = "21pt", "15pt"
    return d, en


def build_html(data):
    byid = {e["id"]: e for e in data["entries"]}
    S = lambda s: [x for x in data["sections"] if x["id"] == s][0]

    css = """
@font-face{font-family:'Tiro';src:url('fonts/TiroDevanagariSanskrit-Regular.ttf');}
@font-face{font-family:'Cormorant';src:url('fonts/CormorantGaramond[wght].ttf');font-weight:400 700;}
:root{--ink:#17140f;--grey:#76736e;--hair:#d9d5cc;}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#efece5;color:var(--ink);}
body{font-family:'Cormorant',Georgia,serif;font-size:15pt;line-height:1.5;}
.page{background:#fff;width:148mm;min-height:210mm;margin:0 auto 10mm;padding:20mm 18mm;
  box-shadow:0 2px 14px rgba(0,0,0,.12);position:relative;page-break-after:always;}
.cover{display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;}
.cover .om{font-family:'Tiro';font-size:64pt;line-height:1;margin-bottom:18mm;color:var(--ink);}
.cover h1{font-family:'Cormorant';font-weight:600;font-size:34pt;letter-spacing:.06em;
  margin:0;text-transform:uppercase;}
.cover .sub{font-size:16pt;font-style:italic;color:var(--grey);margin-top:4mm;letter-spacing:.02em;}
.cover .rule{width:40mm;height:1px;background:var(--ink);margin:10mm auto;}
.cover .blurb{font-size:11pt;text-transform:uppercase;letter-spacing:.22em;color:var(--grey);}
.toc h2,.sec-div h2{font-family:'Cormorant';font-weight:600;letter-spacing:.12em;text-transform:uppercase;font-size:13pt;color:var(--grey);}
.toc ol{list-style:none;padding:0;margin:8mm 0 0;}
.toc .sec{margin-top:7mm;font-size:10pt;letter-spacing:.2em;text-transform:uppercase;color:var(--grey);}
.toc li{margin:1.5mm 0;font-size:12pt;}
.toc .n{color:var(--grey);display:inline-block;width:8mm;}
.sec-div{display:flex;flex-direction:column;justify-content:center;text-align:center;}
.sec-div .num{font-family:'Cormorant';font-size:11pt;letter-spacing:.3em;color:var(--grey);}
.sec-div h2{font-size:26pt;letter-spacing:.08em;margin:4mm 0 0;color:var(--ink);}
.sec-div .sub{font-style:italic;color:var(--grey);font-size:13pt;margin-top:3mm;}
.sec-div .rule{width:30mm;height:1px;background:var(--ink);margin:8mm auto 0;}
.entry{display:flex;flex-direction:column;}
.entry .dev{font-family:'Tiro';font-size:20pt;line-height:1.75;text-align:center;margin:6mm 0 3mm;white-space:pre-line;}
.entry .iast{font-style:italic;color:var(--grey);text-align:center;font-size:12pt;line-height:1.5;}
.entry .en{margin:7mm 0 0;font-size:15pt;line-height:1.55;}
.entry .note{margin-top:auto;font-size:10.5pt;color:var(--grey);border-top:1px solid var(--hair);padding-top:4mm;line-height:1.45;}
.entry .src{font-size:9.5pt;letter-spacing:.12em;text-transform:uppercase;color:var(--grey);margin-bottom:3mm;}
.entry h3{font-family:'Cormorant';font-weight:600;font-size:17pt;margin:0 0 6mm;text-align:center;letter-spacing:.02em;}
.pnum{position:absolute;bottom:10mm;left:0;right:0;text-align:center;font-size:9pt;color:var(--grey);letter-spacing:.1em;}
.spread{display:flex;gap:8mm;justify-content:center;flex-wrap:wrap;margin:0 auto 10mm;}
.spread .page{margin:0;}
.guide .label{font-size:9pt;letter-spacing:.24em;text-transform:uppercase;color:var(--grey);margin-bottom:3mm;}
.guide h3{text-align:left;font-size:19pt;margin:0 0 2mm;}
.guide .src{text-align:left;margin-bottom:5mm;}
.guide .brief{font-style:italic;color:var(--grey);font-size:12pt;line-height:1.45;padding-bottom:4mm;margin-bottom:5mm;border-bottom:1px solid var(--hair);}
.guide .body{font-size:12.5pt;line-height:1.62;color:#241f19;}
.guide .body p{margin:0 0 4mm;}
.guide .src-foot{margin-top:auto;border-top:1px solid var(--hair);padding-top:4mm;font-size:9.5pt;color:var(--grey);}
.guide .src-foot a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--hair);}
.bib h2{font-family:'Cormorant';font-weight:600;letter-spacing:.12em;text-transform:uppercase;font-size:13pt;color:var(--grey);}
.bib ul{list-style:none;padding:0;margin:8mm 0 0;}
.bib li{margin:0 0 5mm;font-size:11pt;line-height:1.5;}
.bib li .t{font-size:10pt;letter-spacing:.12em;text-transform:uppercase;color:var(--grey);}
.bib li a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--hair);word-break:break-all;}
.epi{display:flex;flex-direction:column;justify-content:center;text-align:center;}
.epi .skt{font-family:'Tiro';font-size:15pt;line-height:2;margin-bottom:8mm;}
.epi .en{font-style:italic;font-size:13pt;color:var(--grey);max-width:90mm;margin:0 auto;}
.epi .src{font-size:9.5pt;letter-spacing:.15em;text-transform:uppercase;color:var(--grey);margin-top:8mm;}
@media print{html,body{background:#fff}.page{margin:0;box-shadow:none;width:auto;min-height:auto}.spread{display:block;margin:0}@page{size:A5;margin:0}}
"""

    pages = []
    pages.append(f"""<section class="page cover">
<div class="om">ॐ</div>
<h1>{esc(META['title'])}</h1>
<div class="sub">{esc(META['subtitle'])}</div>
<div class="rule"></div>
<div class="blurb">{esc(META['blurb'])}</div>
</section>""")

    pages.append(f"""<section class="page epi"><div class="skt">{esc(deva(META['epigraph_iast']))}</div>
<div class="en">{esc(META['epigraph_en'])}</div>
<div class="src">{esc(META['epigraph_src'])}</div></section>""")

    # TOC
    toc = ['<section class="page toc"><h2>Contents</h2><ol>']
    n = 0
    for sec in data["sections"]:
        toc.append(f'<div class="sec">{esc(sec["numeral"])} &nbsp; {esc(sec["title"])} &nbsp; <span style="opacity:.6">{esc(sec["subtitle"])}</span></div>')
        for eid in sec["entries"]:
            n += 1
            toc.append(f'<li><span class="n">{n}</span>{esc(byid[eid]["title"])}</li>')
    toc.append("</ol></section>")
    pages.append("".join(toc))

    n = 0
    for sec in data["sections"]:
        pages.append(f"""<section class="page sec-div"><div class="num">{esc(sec['numeral'])}</div>
<h2>{esc(sec['title'])}</h2><div class="sub">{esc(sec['subtitle'])}</div><div class="rule"></div></section>""")
        for eid in sec["entries"]:
            n += 1
            e = byid[eid]
            dev_html = esc(e["devanagari"]).replace("\n", "<br>")
            dsz, esz = type_sizes(e)
            body = "".join(f"<p>{esc(p)}</p>" for p in split_paras(e["guide"] or e["note"]))
            if e.get("source_path"):
                tref = f'<a href="{esc(e["source_path"])}">{esc(e["source_ref"] or "translation")}</a>'
                sfoot = f'<div class="src-foot">Translation: {tref}</div>'
            else:
                sfoot = '<div class="src-foot">Traditional text.</div>'
            pages.append(f"""<div class="spread">
<section class="page prayer">
<div class="src">{esc(e['source'])}</div>
<h3>{esc(e['title'])}</h3>
<div class="dev" style="font-size:{dsz}">{dev_html}</div>
<div class="iast">{esc(e['iast'])}</div>
<div class="en" style="font-size:{esz}">{esc(e['en'])}</div>
<div class="pnum">{n}</div></section>
<section class="page guide">
<div class="label">The Guide</div>
<h3>{esc(e['title'])}</h3>
<div class="src">{esc(e['source'])}</div>
<div class="brief">{esc(e['note'])}</div>
<div class="body">{body}</div>
{sfoot}
<div class="pnum">{n} · guide</div></section>
</div>""")

    pages.append(f"""<section class="page epi"><div class="skt">ॐ शान्तिः शान्तिः शान्तिः</div>
<div class="en">peace, peace, peace</div>
<div class="src">Anuttara</div></section>""")

    # bibliography of translations
    seen, blist = set(), []
    for e in data["entries"]:
        p = e.get("source_path")
        if p and p not in seen:
            seen.add(p)
            refs = [x["source_ref"] for x in data["entries"] if x.get("source_path") == p]
            blist.append((p, refs))
    bib = ['<section class="page bib"><h2>Sources</h2><ul>']
    for p, refs in blist:
        bib.append(f'<li><div class="t">{esc(p.replace("sources/","").replace("_"," "))}</div>'
                   f'<a href="{esc(p)}">{esc(p)}</a><br>'
                   f'<span style="color:#76736e">{esc(", ".join(refs))}</span></li>')
    bib.append("</ul></section>")
    pages.append("".join(bib))

    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(META['title'])} — {esc(META['subtitle'])}</title>
<style>{css}</style></head><body>{''.join(pages)}</body></html>"""
    (HERE / "index.html").write_text(doc, encoding="utf-8")


if __name__ == "__main__":
    data = build_json()
    build_html(data)
    print(f"entries: {len(data['entries'])}  sections: {len(data['sections'])}")
    for s in data["sections"]:
        print(f"  {s['numeral']}. {s['title']:<12} {len(s['entries'])}")
