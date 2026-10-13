# Parser for the print-book subject headings in the SPL data (v3). SPL exports Library of Congress style headings
# with the punctuation removed: 'Vietnam War, 1961-1975 -- Fiction' arrives as 'Vietnam War 1961 1975 Fiction', and
# 'Racism -- United States -- History -- 20th century -- Juvenile literature' as
# 'Racism United States History 20th century Juvenile literature'. Headings in one record are separated by ', '.
# parse_heading() strips known subdivisions, places and dates from the right, recognizes person and fictional
# character headings, dated events and genre/form headings, and returns (core, components) where components are
# (facet, value) pairs with facet in theme / genre / audience / form / place / period / person / other.
import re
import _lexicon as L

# ---------------------------------------------------------------- subdivisions (matched case-insensitively at the right end)
def _c(s):
    return [tuple(x.split(':', 1)) for x in s.split('+')] if s else []


SUBDIV = {k: _c(v) for k, v in {
    'juvenile fiction': 'audience:children+form:fiction', 'juvenile literature': 'audience:children+form:nonfiction',
    'juvenile poetry': 'audience:children+form:poetry', 'juvenile drama': 'audience:children+form:drama',
    'juvenile humor': 'audience:children+genre:humor', 'juvenile films': 'audience:children', 'juvenile sound recordings': 'audience:children',
    'young adult fiction': 'audience:young adult+form:fiction', 'young adult literature': 'audience:young adult+form:nonfiction',
    'fiction': 'form:fiction', 'comic books strips etc': 'form:comics and graphic novels', 'comics graphic works': 'form:comics and graphic novels',
    'graphic novels': 'form:comics and graphic novels', 'cartoons and comics': 'form:comics and graphic novels',
    'caricatures and cartoons': 'form:comics and graphic novels', 'biography': 'genre:biography', 'drama': 'form:drama', 'poetry': 'form:poetry',
    'humor': 'genre:humor', 'wit and humor': 'genre:humor', 'pictorial works': 'form:pictorial works', 'popular works': '', 'miscellanea': '',
    'anecdotes': '', 'case studies': '', 'handbooks manuals etc': 'form:how-to guide', 'amateurs manuals': 'form:how-to guide',
    'guidebooks': 'theme:travel+form:guidebook', 'description and travel': 'theme:travel', 'recipes': 'theme:cooking+form:cookbook',
    'patterns': '', 'technique': '', 'exhibitions': '', 'catalogs': '', 'dictionaries': 'form:reference', 'encyclopedias': 'form:reference',
    'interviews': 'form:interviews', 'correspondence': 'form:letters', 'diaries': 'form:diary', 'sources': '',
    'criticism and interpretation': 'genre:literary criticism', 'history and criticism': 'genre:literary criticism',
    'translations into english': 'other:language', 'study guides': 'form:textbook', 'problems exercises etc': 'form:textbook',
    'examinations study guides': 'form:textbook', 'examinations': 'form:textbook', 'textbooks': 'form:textbook', 'identification': '',
    'quotations maxims etc': 'form:quotations', 'personal narratives': 'genre:memoir', 'early works to 1800': 'period:before 1800',
    'psychological aspects': 'theme:psychology', 'social aspects': 'theme:society', 'political aspects': 'theme:politics',
    'economic aspects': 'theme:economics', 'moral and ethical aspects': 'theme:ethics', 'religious aspects': 'theme:religion',
    'religious aspects christianity': 'theme:christianity', 'religious aspects buddhism': 'theme:buddhism', 'religious aspects judaism': 'theme:judaism',
    'religious aspects islam': 'theme:islam', 'religious aspects zen buddhism': 'theme:buddhism', 'health aspects': 'theme:health',
    'environmental aspects': 'theme:environment', 'law and legislation': 'theme:law', 'study and teaching': 'theme:education',
    'social conditions': 'theme:society', 'economic conditions': 'theme:economics', 'politics and government': 'theme:politics',
    'social life and customs': 'theme:customs', 'foreign relations': 'theme:international relations', 'race relations': 'theme:race relations',
    'ethnic relations': 'theme:ethnic relations', 'emigration and immigration': 'theme:immigration', 'civilization': 'theme:culture',
    'antiquities': 'theme:archaeology', 'military history': 'theme:military', 'kings and rulers': 'theme:monarchy', 'religion': 'theme:religion',
    'intellectual life': 'theme:culture', 'climate': 'theme:weather', 'environmental conditions': 'theme:environment', 'historiography': 'theme:history',
    'prevention': '', 'treatment': '', 'therapy': '', 'diagnosis': '', 'complications': '', 'care': '', 'training': '', 'behavior': '',
    'diet therapy': 'theme:nutrition', 'nutrition': 'theme:nutrition', 'psychology': 'theme:psychology', 'philosophy': 'theme:philosophy',
    'influence': '', 'adaptations': 'other:adaptation', 'film adaptations': 'other:adaptation', 'television adaptations': 'other:adaptation',
    'in literature': '', 'in art': '', 'themes motives': '', 'authorship': 'theme:writing', 'vocational guidance': 'theme:careers and work',
    'computer programs': 'theme:computers', 'digital techniques': '', 'data processing': 'theme:computers', 'statistics': '', 'research': '',
    'methodology': '', 'periodicals': '', 'congresses': '', 'bilingual': 'other:language', 'spanish language materials': 'other:language',
    'chinese language materials': 'other:language', 'japanese language materials': 'other:language', 'korean language materials': 'other:language',
    'vietnamese language materials': 'other:language', 'russian language materials': 'other:language', 'french language materials': 'other:language',
    'readers': 'form:early reader', 'readers primary': 'form:early reader', 'readers beginner': 'form:early reader', 'conversation and phrase books': 'theme:language learning',
    'self instruction': 'theme:language learning', 'grammar': 'theme:grammar and language usage', 'terminology': '', 'evaluation': '',
    'employment': 'theme:careers and work', 'finance': 'theme:finance', 'management': 'theme:management', 'marketing': 'theme:marketing',
    'planning': '', 'design and construction': 'theme:architecture', 'maintenance and repair': 'theme:diy', 'equipment and supplies': '',
    'safety measures': '', 'social life and customs juvenile literature': 'theme:customs+audience:children+form:nonfiction',
    'crimes against': 'theme:violent crimes', 'abuse of': 'theme:abuse', 'family relationships': 'theme:family',
    'mental health': 'theme:mental health', 'health and hygiene': 'theme:health', 'childhood and youth': 'theme:childhood',
    'genealogy': 'theme:genealogy', 'portraits': '', 'homes and haunts': '', 'collectibles': 'theme:antiques and collectibles',
    'history': 'theme:history', 'civil rights': 'theme:civil rights', 'segregation': 'theme:segregation', 'suffrage': 'theme:politics',
    'violence against': 'theme:violence against groups', 'sexual behavior': 'theme:sexuality', 'mortality': 'theme:death', 'suicidal behavior': 'theme:suicide',
    'drug use': 'theme:drugs', 'alcohol use': 'theme:alcoholism', 'education': 'theme:education', 'medical care': 'theme:health care',
    'mental health services': 'theme:mental health', 'identity': 'theme:identity', 'race identity': 'theme:race', 'ethnic identity': 'theme:identity',
    'attitudes': '', 'public opinion': '', 'social networks': 'theme:social media',
}.items()}
# subdivisions that mean 'about the history of X': kept only when X is a place or nothing else is left
HISTORY_LIKE = {'history'}
MAXSUB = max(len(k.split()) for k in SUBDIV)

# ---------------------------------------------------------------- places (matched only on Capitalized words)
US_ABBR = {'n y': 'new york', 'calif': 'california', 'wash': 'washington state', 'fla': 'florida', 'mass': 'massachusetts', 'ill': 'illinois',
           'tex': 'texas', 'd c': 'washington dc', 'n j': 'new jersey', 'pa': 'pennsylvania', 'mich': 'michigan', 'or': 'oregon', 'ore': 'oregon',
           'minn': 'minnesota', 'wis': 'wisconsin', 'colo': 'colorado', 'ariz': 'arizona', 'ga': 'georgia state', 'la': 'louisiana',
           'va': 'virginia', 'n c': 'north carolina', 's c': 'south carolina', 'md': 'maryland', 'conn': 'connecticut', 'ky': 'kentucky',
           'tenn': 'tennessee', 'ala': 'alabama', 'miss': 'mississippi', 'mo': 'missouri', 'okla': 'oklahoma', 'kan': 'kansas', 'neb': 'nebraska',
           'ind': 'indiana', 'nev': 'nevada', 'n m': 'new mexico', 'mont': 'montana', 'wyo': 'wyoming', 'me': 'maine', 'vt': 'vermont',
           'n h': 'new hampshire', 'r i': 'rhode island', 'del': 'delaware', 'w va': 'west virginia', 'ark': 'arkansas', 'b c': 'british columbia',
           'ont': 'ontario', 'que': 'quebec', 'n s': 'nova scotia', 'alta': 'alberta', 'n d': 'north dakota', 's d': 'south dakota'}
EXTRA_PLACES = {'united states', 'great britain', 'washington state', 'northwest pacific', 'pacific northwest', 'north america', 'south america',
                'central america', 'latin america', 'middle east', 'soviet union', 'russia federation', 'puget sound region', 'puget sound',
                'imaginary place', 'imaginary places', 'imaginary wars and battles', 'new england', 'great plains', 'west u s', 'southern states',
                'southwest new', 'europe eastern', 'africa west', 'africa east', 'africa southern', 'asia southeastern', 'asia south', 'east asia',
                'seattle', 'portland', 'tacoma', 'spokane', 'bellingham', 'olympia', 'vancouver', 'victoria', 'manhattan new york', 'brooklyn new york',
                'new york', 'harlem new york', 'chicago', 'boston', 'los angeles', 'san francisco', 'new orleans', 'philadelphia', 'detroit',
                'atlanta', 'baltimore', 'miami', 'houston', 'dallas', 'denver', 'minneapolis', 'washington', 'alaska', 'hawaii', 'arctic regions',
                'antarctica', 'west', 'south', 'midwest', 'appalachian region', 'mississippi river', 'columbia river', 'oregon trail',
                'cascade range', 'rocky mountains', 'olympic peninsula', 'mount rainier', 'yellowstone national park', 'grand canyon'}
PLACE_WORDS = {p for p in (L.PLACES | set(L.DEMONYM) | EXTRA_PLACES | set(US_ABBR))}
PLACE_TAIL_WORDS = {'region', 'island', 'islands', 'river', 'mountains', 'lake', 'valley', 'county', 'state', 'province', 'peninsula', 'bay',
                    'coast', 'national park', 'sound', 'city', 'empire'}
MAXPLACE = 4

# ---------------------------------------------------------------- dates and periods
DATE_TOK = re.compile(r'^(\d{3,4}|\d{1,2}(st|nd|rd|th)|century|centuries|b|c|ca|to|a|d|early|late|middle|ages|bce|ce|\d{3,4}s)$', re.I)
CENT_RE = re.compile(r'(\d{1,2})(st|nd|rd|th) century', re.I)

# ---------------------------------------------------------------- events with dates (core words, first year) -> theme value
EVENT_WORDS = re.compile(r'\b(war|wars|revolution|epidemic|pandemic|depression|movement|crisis|massacre|riots?|holocaust|genocide|attacks?|'
                         r'assassination|disaster|expedition|olympics|rebellion|strike|earthquake|hurricane|eruption|explosion|famine|'
                         r'invasion|occupation|internment|campaign|battle|siege|reconstruction|civil rights|era|period|dynasty|shipwreck|'
                         r'sinking|bombing|bombings|uprising|protests?|demonstrations?|conflict)\b', re.I)
EVENT_CANON = [  # (regex on lowercased core+years, theme value)
    (r'^world war 1939 1945', 'world war ii'), (r'^world war 1914 1918', 'world war i'), (r'^holocaust jewish', 'holocaust'),
    (r'^vietnam war', 'vietnam war'), (r'^korean war', 'korean war'), (r'^iraq war', 'iraq war'), (r'^persian gulf war', 'iraq war'),
    (r'^afghan war', 'afghanistan war'), (r'^september 11 terrorist attacks', 'september 11 attacks'), (r'^cold war', 'cold war'),
    (r'^influenza epidemic', 'influenza pandemic 1918'), (r'^covid 19 pandemic', 'covid 19'), (r'^covid 19', 'covid 19'),
    (r'^great depression|^depressions 1929', 'great depression'), (r'^civil rights movements?', 'civil rights movement'),
    (r'^metoo movement|^me too movement', 'metoo movement'), (r'^black lives matter', 'black lives matter movement'),
    (r'^japanese americans evacuation and relocation', 'japanese american internment'), (r'^titanic steamship', 'titanic'),
    # LC renames of dated event headings (see _review_v3.LC_RENAMES_EVENTS): the new form takes the old form's value
    (r'^vietnamese conflict', 'vietnam war'), (r'^japanese americans forced removal and (internment|incarceration)', 'japanese american internment'),
]
PLACE_EVENTS = {  # (place value, event words) -> theme value, for '<Place> History <Event> <years>'
    ('united states', 'civil war'): 'american civil war', ('united states', 'revolution'): 'american revolution',
    ('france', 'revolution'): 'french revolution', ('russia', 'revolution'): 'russian revolution', ('soviet union', 'revolution'): 'russian revolution',
    ('spain', 'civil war'): 'spanish civil war', ('great britain', 'civil war'): 'english civil war', ('england', 'civil war'): 'english civil war',
    ('united states', 'war of 1812'): 'war of 1812', ('united states', 'colonial period'): 'colonial era',
    ('united states', 'civil war 1861 1865'): 'american civil war', ('united states', 'revolution 1775 1783'): 'american revolution',
}

# ---------------------------------------------------------------- whole-heading genre and form terms (library genre headings)
GENRE_HEADINGS = {k: _c(v) for k, v in {
    'mystery fiction': 'genre:mystery', 'detective and mystery fiction': 'genre:mystery', 'detective and mystery stories': 'genre:mystery',
    'mystery and detective stories': 'genre:mystery', 'detective and mystery comic books strips etc': 'genre:mystery+form:comics and graphic novels',
    'love stories': 'genre:romance', 'romance fiction': 'genre:romance', 'romantic suspense fiction': 'genre:romance+genre:suspense',
    'regency fiction': 'genre:historical romance+period:regency era', 'historical fiction': 'genre:historical fiction',
    'domestic fiction': 'genre:domestic fiction', 'psychological fiction': 'genre:psychological fiction', 'fantasy fiction': 'genre:fantasy',
    'fantasy': 'genre:fantasy', 'science fiction': 'genre:science fiction', 'suspense fiction': 'genre:suspense', 'thrillers fiction': 'genre:thriller',
    'thrillers': 'genre:thriller', 'humorous stories': 'genre:humor', 'humorous fiction': 'genre:humor', 'short stories': 'form:short stories',
    'fairy tales': 'genre:fairy tales', 'bildungsromans': 'genre:coming of age novel+theme:coming of age', 'christian fiction': 'genre:christian fiction+theme:christianity',
    'graphic novels': 'form:comics and graphic novels', 'comic books strips etc': 'form:comics and graphic novels', 'cartoons and comics': 'form:comics and graphic novels',
    'comics graphic works': 'form:comics and graphic novels', 'manga': 'form:comics and graphic novels', 'large type books': 'other:large print',
    'picture books': 'form:picture book+audience:children', 'picture books for children': 'form:picture book+audience:children',
    'board books': 'form:picture book+audience:children', 'stories in rhyme': 'form:poetry+audience:children', 'western stories': 'genre:western',
    'adventure fiction': 'genre:adventure', 'adventure stories': 'genre:adventure', 'war stories': 'genre:war fiction+theme:war',
    'war fiction': 'genre:war fiction+theme:war', 'horror fiction': 'genre:horror', 'horror tales': 'genre:horror', 'ghost stories': 'genre:horror+theme:ghosts',
    'spy stories': 'genre:spy fiction', 'legal stories': 'genre:legal thriller+theme:law', 'political fiction': 'genre:political thriller+theme:politics',
    'occult fiction': 'genre:paranormal+theme:occult', 'paranormal fiction': 'genre:paranormal', 'paranormal romance stories': 'genre:paranormal romance',
    'biographical fiction': 'genre:historical fiction', 'young adult fiction': 'audience:young adult+form:fiction', 'cookbooks': 'form:cookbook+theme:cooking',
    'cookery': 'theme:cooking', 'autobiographies': 'genre:memoir', 'biographies': 'genre:biography', 'diaries': 'form:diary', 'essays': 'form:essays',
    'poetry': 'form:poetry', 'novels in verse': 'form:poetry', 'childrens poetry': 'form:poetry+audience:children', 'american poetry': 'form:poetry+place:united states',
    'english poetry': 'form:poetry+place:england', 'readers primary': 'form:early reader+audience:children', 'readers': 'form:early reader+audience:children',
    'science fiction comic books strips etc': 'genre:science fiction+form:comics and graphic novels',
    'fantasy comic books strips etc': 'genre:fantasy+form:comics and graphic novels', 'superhero comic books strips etc': 'form:comics and graphic novels+theme:superheroes',
    'humorous comic books strips etc': 'genre:humor+form:comics and graphic novels', 'horror comic books strips etc': 'genre:horror+form:comics and graphic novels',
    'adventure comic books strips etc': 'genre:adventure+form:comics and graphic novels', 'romance comic books strips etc': 'genre:romance+form:comics and graphic novels',
    'erotic fiction': 'genre:erotica', 'erotic stories': 'genre:erotica', 'erotica': 'genre:erotica', 'satire': 'genre:satire', 'satirical literature': 'genre:satire',
    'dystopias': 'genre:dystopian', 'dystopian fiction': 'genre:dystopian', 'apocalyptic fiction': 'genre:post-apocalyptic', 'utopian fiction': 'genre:speculative fiction+theme:utopia',
    'alternative histories fiction': 'genre:alternate history', 'magic realism literature': 'genre:magical realism', 'magical realism': 'genre:magical realism',
    'gothic fiction': 'genre:gothic', 'noir fiction': 'genre:crime', 'crime fiction': 'genre:crime', 'detective and mystery television programs': '',
    'chick lit': 'genre:chick lit', 'sea stories': 'genre:adventure+theme:seafaring', 'animal stories': 'genre:animal stories+theme:animals',
    'nursery rhymes': 'genre:folklore and fables+audience:children', 'fables': 'genre:folklore and fables', 'folklore': 'genre:folklore and fables',
    'legends': 'genre:folklore and fables', 'tales': 'genre:folklore and fables', 'mythology': 'theme:mythology', 'parodies imitations etc': 'genre:satire',
    'epistolary fiction': 'form:letters', 'experimental fiction': 'genre:literary fiction', 'sports stories': 'genre:sports fiction+theme:sports',
    'school stories': 'theme:school life', 'christmas stories': 'theme:christmas', 'medical fiction': 'genre:thriller+theme:medicine',
    'spanish language materials': 'other:language', 'chinese language materials': 'other:language', 'audiobooks': 'other:format',
    'childrens stories': 'audience:children+form:fiction', 'childrens questions and answers': 'audience:children+form:nonfiction',
    'counting': 'audience:children', 'alphabet': 'audience:children', 'concept books': 'audience:children', 'toy and movable books': 'audience:children+form:picture book',
    'lift the flap books': 'audience:children+form:picture book', 'bedtime': 'audience:children', 'pop up books': 'audience:children+form:picture book',
    'urban fiction': 'genre:urban fiction', 'horror stories': 'genre:horror', 'gay fiction': 'form:fiction+theme:gay men',
    'lesbian fiction': 'form:fiction+theme:lesbian', 'christian romance': 'genre:christian fiction+genre:romance', 'amish fiction': 'genre:christian fiction+theme:amish',
    'historical romance fiction': 'genre:historical romance', 'detective and mystery stories english': 'genre:mystery+place:england',
    'mystery comic books strips etc': 'genre:mystery+form:comics and graphic novels', 'crime comic books strips etc': 'genre:crime+form:comics and graphic novels',
    'war comic books strips etc': 'genre:war fiction+form:comics and graphic novels+theme:war', 'western comic books strips etc': 'genre:western+form:comics and graphic novels',
    'nonfiction comics': 'form:comics and graphic novels+form:nonfiction', 'biographical comics': 'form:comics and graphic novels+genre:biography',
    'autobiographical comics': 'form:comics and graphic novels+genre:memoir', 'picture books': 'form:picture book+audience:children',
    'instructional and educational works': 'form:how-to guide', 'informational works': 'form:nonfiction', 'novels': 'form:novel',
    'nonfiction': 'form:nonfiction', 'fiction': 'form:fiction', 'literature': 'form:literature', 'short stories american': 'form:short stories+place:united states',
    'american fiction': 'form:fiction+place:united states', 'english fiction': 'form:fiction+place:england', 'american literature': 'form:literature+place:united states',
    'english literature': 'form:literature+place:england', 'american essays': 'form:essays+place:united states', 'quotations': 'form:quotations',
}.items()}

# phrases that must not be cut further (known theme and genre phrases, and main headings that end like a subdivision);
# filled by the caller from the v2 vocabulary, plus a few headings listed here
PROTECT = {'indians of north america', 'indians of south america', 'indians of central america', 'indians of mexico',
           'eskimos', 'inuit', 'human behavior', 'animal behavior', 'consumer behavior', 'organizational behavior', 'love poetry', 'child sexual abuse',
           'sexual abuse victims', 'adult child sexual abuse victims', 'human biology', 'social history', 'natural history', 'oral history',
           'world history', 'military history', 'church history', 'local history', 'art history', 'mental health', 'public health',
           'family violence', 'political science', 'social psychology', 'child psychology', 'cognitive psychology', 'positive psychology',
           'religion and science', 'religion and politics', 'philosophy and religion', 'food habits', 'diet therapy'}

PERSON_YEARS = re.compile(r"^([A-Z][\w'’\-\.]*(?: (?:[A-Z][\w'’\-\.]*|de|da|del|van|von|der|la|le|du|di|bin|ibn|al)){1,6}) (\d{3,4})(?: (\d{3,4}))?\b")
FICT_CHAR = re.compile(r'\bFictitious characters?\b|\bLegendary characters?\b|\bMythological characters?\b', re.I)   # plural too: 'Avengers Fictitious characters'


def _norm(s):
    s = re.sub(r"[’'`]", '', s.lower())
    s = re.sub(r'[^\w\s]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def parse_heading(h):
    """Return (core, components, kind). kind: person / character / event / genre / topic / place / empty."""
    core, comps, kind = _parse(h)
    return core, list(dict.fromkeys(c for c in comps if c[0] != '_years')), kind


def _parse(h):
    h = h.strip().lstrip('#')
    if not h:
        return '', [], 'empty'
    comps = []
    toks = h.split()
    # 1. subdivisions, places and dates from the right
    def strip_right(toks):
        while toks:
            low = [t.lower() for t in toks]
            whole = _norm(' '.join(toks))
            if whole in GENRE_HEADINGS or whole in PROTECT:   # 'Mystery fiction' is a genre heading, not 'Mystery -- Fiction'
                break
            hit = False
            for n in range(min(MAXSUB, len(toks)), 0, -1):
                s = ' '.join(low[-n:])
                if s in SUBDIV and len(toks) > n:
                    comps.extend(SUBDIV[s]); toks = toks[:-n]; hit = True; break
            if hit:
                continue
            # dates: '1939 1945', '20th century', 'To 1800', 'B C'
            if DATE_TOK.match(toks[-1]) and len(toks) > 1 and (re.match(r'^\d', toks[-1]) or low[-1] in ('century', 'centuries', 'c') or re.match(r'^\d', toks[-2])):
                j = len(toks)
                while j > 1 and DATE_TOK.match(toks[j - 1]):
                    j -= 1
                span = ' '.join(low[j:])
                m = CENT_RE.search(span)
                if m:
                    comps.append(('period', f'{m.group(1)}{m.group(2)} century'))
                elif re.search(r'\d{4}', span):
                    y = int(re.search(r'\d{3,4}', span).group(0))
                    comps.append(('period', f'{(y // 10) * 10}s' if y >= 1800 else f'{(y // 100) + 1}th century'))
                    comps.append(('_years', span))
                toks = toks[:j]
                continue
            # places: Capitalized words only
            for n in range(min(MAXPLACE, len(toks)), 0, -1):
                seg = toks[-n:]
                if not all(t[:1].isupper() or t in ('of', 'and') for t in seg):
                    continue
                s = ' '.join(low[-n:])
                if s in PLACE_WORDS or (n >= 2 and low[-1] in PLACE_TAIL_WORDS):
                    v = US_ABBR.get(s) or L.DEMONYM.get(s, s)
                    comps.append(('place', v)); toks = toks[:-n]; hit = True; break
            if hit:
                continue
            break
        return toks
    toks = strip_right(toks)
    # place at the start: 'United States History Civil War', 'United States Race relations', 'Seattle Wash Social life and customs'
    lead_place = None
    for n in range(min(MAXPLACE, len(toks) - 1), 0, -1):
        seg = toks[:n]
        if all(t[:1].isupper() for t in seg):
            sp = ' '.join(t.lower() for t in seg)
            if sp in PLACE_WORDS:
                rest = [t.lower() for t in toks[n:]]
                restj = ' '.join(rest)
                if rest and (rest[0] == 'history' or restj in SUBDIV or any(restj.startswith(k + ' ') for k in SUBDIV)):
                    lead_place = US_ABBR.get(sp) or L.DEMONYM.get(sp, sp)
                    comps.append(('place', lead_place))
                    toks = toks[n:]
                    break
    if lead_place:
        low_rest = ' '.join(t.lower() for t in toks)
        if low_rest.startswith('history'):
            ev = low_rest[len('history'):].strip()
            for (pl, e), val in PLACE_EVENTS.items():
                if pl == lead_place and ev.startswith(e):
                    return ev, list(dict.fromkeys(comps + [('theme', val)])), 'event'
            if not ev:
                return '', list(dict.fromkeys(comps + [('theme', 'history')])), 'place'
            toks = toks[1:]
            comps.append(('theme', 'history'))
        else:
            for k in sorted(SUBDIV, key=len, reverse=True):
                if low_rest == k or low_rest.startswith(k + ' '):
                    comps.extend(SUBDIV[k]); toks = toks[len(k.split()):]; break
        toks = strip_right(toks)
    core = ' '.join(toks)
    low = _norm(core)
    years = ' '.join(v for f, v in comps if f == '_years')
    comps = [c for c in comps if c[0] != '_years']
    # 2. fictitious characters and persons
    if FICT_CHAR.search(core):
        name = _norm(FICT_CHAR.split(core)[0])
        return name, comps + [('person', name + ' (character)')], 'character'
    m = PERSON_YEARS.match(h)
    if m and not EVENT_WORDS.search(m.group(1)) and _norm(m.group(1)) not in PLACE_WORDS:
        name = _norm(m.group(1))
        return name, comps + [('person', name)], 'person'
    # 3. dated events
    key = (low + ' ' + years).strip()
    for pat, val in EVENT_CANON:
        if re.match(pat, key):
            return low, comps + [('theme', val)], 'event'
    places = [v for f, v in comps if f == 'place']
    if places and low.startswith('history '):
        ev = low[len('history '):]
        for (pl, e), val in PLACE_EVENTS.items():
            if pl in places and ev.startswith(e):
                return low, comps + [('theme', val)], 'event'
    # 4. genre and form headings, language materials, local collection tags
    if low in GENRE_HEADINGS:
        return low, list(dict.fromkeys(comps + GENRE_HEADINGS[low])), 'genre'
    if low.endswith('language materials'):
        return low, list(dict.fromkeys(comps + [('other', 'language')])), 'genre'
    if re.search(r'\b(authors collection|collection)$', low):
        return low, list(dict.fromkeys(comps + [('other', 'collection')])), 'genre'
    # 5. a heading that is only a place (and its subdivisions)
    if not low:
        if any(f == 'place' for f, v in comps):
            return '', list(dict.fromkeys(comps)), 'place'
        return '', list(dict.fromkeys(comps)), 'empty'
    if low in PLACE_WORDS:
        return low, list(dict.fromkeys(comps + [('place', US_ABBR.get(low) or L.DEMONYM.get(low, low))])), 'place'
    # 6. otherwise the core is a topic (theme candidate); 'history' as a subdivision of a topic adds nothing
    comps = [c for c in comps if c != ('theme', 'history')] if low else comps
    return low, list(dict.fromkeys(comps)), 'topic'
