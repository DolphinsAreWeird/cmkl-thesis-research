# Hand decisions for taxonomy v3 (print subject headings), written 13 Oct 2026 after reading the parser output
# (profile/lcsh_cores_review.csv) and the embedding proposals (profile/placement_review.csv).
# The approved v2 tree is fixed; these entries only say where new values go. Every entry has a reason.
#   ALIAS          heading core -> existing v2 theme value (same meaning, different wording)
#   CORE_FACETS    heading core that is not a theme -> facet parts
#   VALUE_PLACE    new value -> ('join', v2 value) narrow node of that value; ('mid', v2 value) middle node of that value;
#                  ('broad', v2 value) broad node; ('new', key) a new narrow node below; ('none', '') not placed
#   PLACE_RULES    regular expressions applied to new values not listed in VALUE_PLACE (first match wins)
#   NEW_NARROW_V3  new narrow nodes: key -> (label, a v2 value inside the parent middle node, reason)

ALIAS = {
    'indians of north america': 'native americans', 'indians of south america': 'indigenous', 'indians of central america': 'indigenous',
    'indians of mexico': 'indigenous', 'eskimos': 'indigenous', 'inuit': 'indigenous', 'finance personal': 'personal finance',
    'homosexuality': 'lgbtq', 'gay men': 'gay men', 'lesbians': 'lesbian', 'bisexuals': 'bisexual', 'bisexuality': 'bisexual',
    'anti racism': 'antiracism', 'antiracism': 'antiracism', 'rape': 'sexual violence', 'quarantine': 'epidemics and pandemics',
    'pandemics': 'epidemics and pandemics', 'epidemics': 'epidemics and pandemics', 'global warming fiction': 'climate change',
    'climate change': 'climate change', 'climatic change': 'climate change', 'bereavement': 'grief', 'loss psychology': 'grief',
    # the print heading 'Violence' is general violence; the v2 value 'violence' sits in the sexual and domestic violence control
    # (v2 placement, kept for the sources v2 used), so the heading gets its own value, which goes to the new violence node
    'violence': 'violence in general',
}

def _f(s):
    return [tuple(x.split(':', 1)) for x in s.split('+')]

CORE_FACETS = {k: _f(v) for k, v in {
    'adventure and adventurers': 'genre:adventure', 'americans': 'place:united states', 'supernatural': 'genre:paranormal',
    'pictorial': 'form:pictorial works', 'color': 'audience:children', 'medical novels': 'genre:thriller+theme:medicine',
    'english language textbooks for foreign speakers': 'theme:language learning+form:textbook', 'middle ages': 'period:middle ages',
    'autobiographical': 'genre:memoir', 'x men fictitious characters': 'other:franchise', 'star wars': 'other:franchise',
    'star trek': 'other:franchise', 'star wars fictitious characters': 'other:franchise', 'harry potter fictitious character': 'other:franchise',
    'questions and answers': 'form:nonfiction', 'public opinion': 'other:ambiguous', 'georgia': 'place:georgia', 'las vegas': 'place:las vegas',
    'industrial': 'other:ambiguous', 'competition': 'other:ambiguous', 'lost and found possessions': 'audience:children',
    'national characteristics': 'theme:culture and heritage', 'hardy boys fictitious characters': 'other:franchise',
    'nancy drew fictitious character': 'other:franchise', 'readers for new literates': 'theme:literacy+form:early reader',
}.items()}

GLOSS = {}   # extra embedding glosses for new values (none needed so far)

VALUE_PLACE = {
    # most frequent new values whose nearest node was wrong or weak (similarity in brackets)
    'man woman relationships': ('join', 'marriage', 'romantic relationships; nearest was men / masculinity (0.76)'),
    'schools': ('join', 'school life', 'school settings; nearest was teaching (0.66)'),
    'interpersonal relations': ('mid', 'friendship', 'social relations in general: middle node Friendship, happiness and identity'),
    'conduct of life': ('join', 'ethics', 'LCSH "Conduct of life" is about how to live; nearest was college life (0.40)'),
    'good and evil': ('join', 'ethics', 'moral theme; weak similarity (0.40)'),
    'young women': ('mid', 'feminism', "young women's lives: middle node Feminism and gender"),
    'interior decoration': ('join', 'home and interior design', 'nearest was drawing / artists (0.61)'),
    'missing persons': ('join', 'kidnapping', 'weak similarity (0.46) to the right node'),
    'self actualization': ('join', 'motivation', 'personal growth; nearest was identity (0.51)'),
    'high school students': ('join', 'school life', 'school setting'),
    'dating social customs': ('join', 'marriage', 'dating is in the marriage node (v2 hand edit); 0.47'),
    'heroes': ('join', 'superheroes', 'LCSH Heroes is used mostly for comics and hero stories (0.41)'),
    'princesses': ('join', 'monarchy', 'royalty; nearest was fairies (0.63)'),
    'family secrets': ('join', 'family life', 'family drama; nearest was genealogy (0.57)'),
    'singers': ('mid', 'rock music', 'music in general (0.52 to opera)'), 'composers': ('mid', 'rock music', 'music in general'),
    'widows': ('join', 'grief', 'widowhood; nearest was genealogy (0.51)'), 'widowers': ('join', 'grief', 'widowhood'),
    'women authors': ('join', 'writers', 'writers; nearest was feminism (0.74)'), 'women novelists': ('join', 'writers', 'writers'),
    'girls': ('join', 'childhood', "girls in children's books; nearest was feminism (0.61)"), 'boys': ('join', 'childhood', 'children; 0.44'),
    'authorship': ('join', 'writing', 'the craft of writing (0.39)'), 'motion pictures': ('join', 'film', 'nearest was photography (0.63)'),
    'motion picture industry': ('join', 'film', 'nearest was photography (0.63)'), 'theater': ('join', 'musical theatre', 'stage'),
    'life change events': ('join', 'change', 'personal change (0.39)'), 'women private investigators': ('join', 'police', 'detectives'),
    'sex role': ('join', 'gender', 'gender roles; nearest was sexuality (0.73)'), 'women journalists': ('join', 'media', 'journalism'),
    'country life': ('join', 'farming', 'rural life; nearest was international relations (0.48)'),
    'aristocracy': ('join', 'monarchy', 'nobility and royalty'), 'national characteristics': ('none', '', 'not a theme'),
    'boys and girls': ('join', 'childhood', 'children'), 'young men': ('join', 'men', 'men'), 'intelligence officers': ('join', 'intelligence agencies', 'spies'),
    'triangles interpersonal relations': ('join', 'marriage', 'love triangles'), 'self realization': ('join', 'motivation', 'personal growth'),
    'world politics': ('join', 'international relations', 'nearest was political philosophy (0.65)'),
    'islands': ('join', 'geography', 'places (0.41)'), 'ranch life': ('join', 'farming', 'ranching (0.42)'), 'ranchers': ('join', 'farming', 'ranching'),
    'birthdays': ('join', 'holidays', 'celebrations (0.47)'), 'parties': ('join', 'holidays', 'celebrations; nearest was government (0.36)'),
    'older people': ('join', 'aging', 'nearest was grandparents (0.60)'), 'middle aged women': ('join', 'aging', 'aging'), 'older women': ('join', 'aging', 'aging'),
    'women lawyers': ('broad', 'police', 'law and lawyers: broad node Crime, police and law'), 'toys': ('join', 'games', 'play (0.44)'),
    'middle schools': ('join', 'school life', 'school setting'), 'vocational guidance': ('join', 'careers and work', 'careers (0.45)'),
    'career development': ('join', 'careers and work', 'careers'), 'desserts': ('join', 'baking', 'baking (0.46)'),
    'missing children': ('join', 'kidnapping', 'nearest was orphans (0.54)'), 'patchwork': ('join', 'quilting', 'quilting (0.29)'),
    'self care health': ('broad', 'mental health', 'wellness: broad node Health, illness and addiction'),
    'businessmen': ('join', 'entrepreneurship', 'business people (0.41)'), 'businesswomen': ('join', 'entrepreneurship', 'business people'),
    'experiments': ('mid', 'chemistry', 'science experiments: middle node Mathematics, physics and chemistry'),
    'cowboys': ('join', 'pioneers', 'the American frontier (0.42)'), 'presidents spouses': ('join', 'presidents', 'nearest was marriage (0.58)'),
    'mind and body': ('join', 'healing', 'mind-body healing (0.62 to body image)'), 'industrial': ('none', '', 'not a theme'),
    'aristocracy social class': ('join', 'social issues', 'social class (0.44)'), 'contests': ('join', 'games', 'contests (0.45)'),
    'automobile travel': ('join', 'road trips', 'road trips'), 'magicians': ('join', 'magic', 'magic (0.49)'),
    'chickens': ('join', 'farm animals', 'farm animals; nearest was birds (0.51)'), 'restaurants': ('join', 'cooking', 'food (0.44)'),
    'camps': ('join', 'outdoor recreation', 'summer camps (0.49)'), 'entertaining': ('join', 'cooking', 'hosting and food (0.45)'),
    'curiosities and wonders': ('join', 'trivia', 'odd facts (0.39)'), 'woodwork': ('join', 'diy', 'woodworking (0.42)'),
    'jewelry making': ('join', 'crafts and hobbies', 'crafts (0.47)'), 'stress': ('join', 'depression', 'stress and mental health; nearest was trauma (0.59)'),
    'prehistoric peoples': ('join', 'archaeology', 'prehistory (0.49)'), 'courage': ('join', 'virtue', 'moral virtue (0.42)'),
    'swindlers and swindling': ('join', 'heist', 'con artists (0.45)'), 'vacations': ('mid', 'geography', 'travel: middle node Travel, exploration and mountains'),
    'publishers and publishing': ('join', 'books and reading', 'books (0.48)'), 'shapeshifting': ('join', 'shapeshifters', 'nearest was drawing (0.45)'),
    'arab israeli conflict': ('join', 'international relations', 'conflict between states; nearest was islam (0.57)'),
    'childrens literature': ('join', 'books and reading', "books about children's books"), 'gifts': ('join', 'holidays', 'gift giving (0.49)'),
    'veterans': ('mid', 'naval warfare', 'military: middle node Military, naval and air warfare'), 'future life': ('join', 'afterlife', 'afterlife (0.47)'),
    'nonprofit organizations': ('join', 'management', 'organizations (0.34)'), 'summer': ('join', 'seasons', 'seasons (0.47)'),
    'diabetes': ('join', 'disease', 'disease (0.43)'), 'historic buildings': ('join', 'architecture', 'buildings (0.43)'),
    'readers for new literates': ('join', 'literacy', 'literacy'), 'anger': ('broad', 'ethics', 'emotions: broad node Mind, self and philosophy'),
    'aggressiveness': ('broad', 'ethics', 'behaviour and emotions'), 'tuberculosis': ('join', 'disease', 'disease (0.42)'),
    'hurricane katrina': ('join', 'disasters', 'natural disaster; nearest was the climate node (0.40)'),
    'air pollution': ('join', 'sustainability', 'environment; kept out of the climate node'), 'ozone layer depletion': ('join', 'sustainability', 'environment'),
    'everglades': ('none', '', 'a place'), 'rainier mount': ('none', '', 'a place'), 'heat': ('none', '', 'physics or weather; unclear'),
    'thermodynamics': ('join', 'physics', 'physics'), 'respiration': ('join', 'anatomy', 'the body'),
    'immune system': ('join', 'human body', 'the body, not epidemics'), 'immunity': ('join', 'human body', 'the body, not epidemics'),
    'natural immunity': ('join', 'human body', 'the body'), 'immunology': ('join', 'disease', 'medicine'), 'immunodeficiency': ('join', 'disease', 'disease'),
    'autoimmune diseases': ('join', 'disease', 'non-infectious disease'), 'environmentally induced diseases': ('join', 'disease', 'non-infectious disease'),
    'environmentally induced diseases in children': ('join', 'disease', 'non-infectious disease'), 'parasites': ('join', 'disease', 'disease'),
    'biological invasions': ('join', 'ecology', 'invasive species, not epidemics'), 'host parasite relationships': ('join', 'biology', 'biology'),
    'poultry diseases': ('join', 'farm animals', 'animal health'), 'overpopulation': ('join', 'social issues', 'population'),
    'biological warfare': ('mid', 'naval warfare', 'weapons: middle node Military, naval and air warfare'),
    'microorganisms': ('join', 'biology', 'biology'), 'bacteria': ('join', 'biology', 'biology'), 'toxins': ('none', '', 'unclear'),
    'minorities': ('join', 'multicultural', 'minority groups in general, not race specifically'), 'discrimination': ('join', 'social justice', 'discrimination in general'),
    'discrimination in': ('join', 'social justice', 'discrimination in employment, education and so on'),
    'american literature minority authors': ('join', 'multicultural', 'diverse authors'), 'minority authors': ('join', 'multicultural', 'diverse authors'),
    'children of minorities': ('join', 'multicultural', 'minority children'), 'minority youth': ('join', 'multicultural', 'minority youth'),
    'minorities in sports': ('join', 'multicultural', 'minorities'), 'minority students': ('join', 'multicultural', 'minorities'),
    'minorities legal status laws etc': ('join', 'social justice', 'legal rights'), 'working class whites': ('join', 'social issues', 'social class'),
    'poor whites': ('join', 'poverty', 'poverty'), 'white men': ('none', '', 'unclear'), 'white': ('none', '', 'unclear'),
    'whites relations with indians': ('join', 'native americans', 'Native American history'),
    'social science ethnic studies african american studies': ('join', 'african american life', 'African American studies'),
    'human skin color': ('join', 'multicultural', "children's books on skin colour and diversity"),
    'color therapeutic use': ('none', '', 'not a theme'), 'color experiments': ('none', '', 'not a theme'), 'color guides': ('none', '', 'not a theme'),
    'hate': ('none', '', 'unclear'), 'albinos and albinism': ('join', 'disability', 'a condition'), 'burgundy': ('none', '', 'a place'),
    'blues': ('mid', 'rock music', 'music'), 'purple': ('none', '', 'not a theme'), 'white minor': ('none', '', 'not a theme'), 'maroons': ('join', 'slavery', 'escaped slaves'),
    'segregation in transportation alabama montgomery': ('join', 'civil rights movement', 'Montgomery bus boycott'),
    'covid 19': ('join', 'plague', 'COVID-19 pandemic (new value from print headings)'),
    'metoo movement': ('join', 'sexual violence', '#MeToo movement (new value from print headings)'),
    'black lives matter movement': ('join', 'racism', 'Black Lives Matter (new value from print headings)'),
    'influenza pandemic 1918': ('join', 'plague', '1918 influenza pandemic'),
    'computer viruses': ('join', 'computers', 'computers, not disease'),
    'trials rape': ('join', 'sexual violence', 'rape trials'),
}

# pattern rules for the control categories and for general violence (applied after VALUE_PLACE)
PLACE_RULES = [
    (r'^(sexual harassment|rape\b|rapists|date rape|acquaintance rape|marital rape|male rape|gang rape|statutory rape|sexual assault|sexual abuse|'
     r'sex crimes|sex offenders|sexual consent|metoo|me too|family violence|domestic violence|intimate partner violence|marital violence|'
     r'conjugal violence|dating violence|abused women|abused wives|abused husbands|abusive men|abusive women|wife abuse|battered|'
     r'child sexual abuse|sexually abused|adult child sexual abuse|incest victims|victims of family violence|serial rape|trials rape|'
     r'violence against women)',
     'join', 'sexual violence', 'sexual violence, harassment, consent or domestic violence (control category, hand rule)'),
    (r'^(epidemics|pandemics|plague|black death|communicable diseases|virus diseases|viruses$|influenza|avian influenza|covid|coronavirus|'
     r'sars|smallpox|cholera|yellow fever|typhoid|typhus|ebola|zika|measles|poliomyelitis|emerging infectious|epidemiolog|bacterial diseases$|'
     r'infection$|parasitic diseases$|vaccination|vaccines|influenza vaccines|epidemic encephalitis|escherichia coli infections|virus diseases patients|'
     r'diseases causes and theories)',
     'join', 'plague', 'epidemic or infectious disease (control category, hand rule)'),
    (r'^(racism|race relations|race discrimination|race awareness|racially mixed|interracial (marriage|dating|friendship|couples)|segregation|'
     r'white supremacy|lynching|hate groups|racial profiling|discrimination in (housing|law enforcement|criminal justice)|affirmative action|'
     r'post racialism|race riots|crime and race|music and race|black race|afrocentrism|reverse discrimination|congress of racial equality|'
     r'national association for the advancement of colored people|universal negro improvement association|whites$|whites race identity|prejudices)',
     'join', 'racism', 'race, racism or racial discrimination (control category, hand rule)'),
    (r'^(climatic changes|climate change|global warming|greenhouse effect|greenhouse gas|global temperature|global environmental change|'
     r'carbon dioxide mitigation|atmospheric carbon dioxide|paleoclimatology|climatology)',
     'join', 'climate change', 'climate change (control category, hand rule)'),
    (r'^(violence|violent crimes|victims of violent crimes|youth and violence|children and violence|urban violence|school violence|'
     r'campus violence|threats of violence|assault and battery|cruelty|hate crimes|violence in )',
     'new', 'violence', 'general violence; kept out of the sexual and domestic violence control'),
]

NEW_NARROW_V3 = {
    'violence': ('Violence and violent crime', 'abuse',
                 'Print headings bring many general violence subjects (urban violence, violence in mass media, violent crimes). The only '
                 'existing narrow node for violence is the sexual and domestic violence control; putting them there would mix the control. '
                 'New node under the same middle node (Abuse, sexual violence and revenge).'),
}

# weather headings go to the climate change and weather node by rule (the control nodes take hand rules only)
PLACE_RULES.insert(4, (r'^(weather|meteorolog|rain and rainfall|rain$|storms$|severe storms|hurricanes|thunderstorms|tornadoes|droughts|monsoons|'
                       r'ice storms|heat waves|blizzards|clouds$|winds$|lightning$|floods$|typhoons|dust storms|weather forecasting|marine meteorology)',
                       'join', 'weather', 'weather (the node holds both climate change and weather in the approved v2 tree; hand rule)'))
# the four control nodes accept values only from hand placements and hand rules
CONTROL_ANCHORS = ['racism', 'plague', 'sexual violence', 'climate change']

# most frequent values still unplaced after the 0.50 threshold (similarity below 0.50), placed by hand
_UNPLACED = {
    'national parks and reserves': ('join', 'conservation', 'protected areas'), 'science experiments': ('mid', 'chemistry', 'science experiments'),
    'science projects': ('mid', 'chemistry', 'science projects'), 'judges': ('broad', 'police', 'courts and law'), 'trials': ('broad', 'police', 'courts and law'),
    'courts and courtiers': ('join', 'monarchy', 'royal courts'), 'nature effect of human beings on': ('join', 'ecology', 'human impact on nature'),
    'letters': ('none', '', 'a form, not a theme'), 'pottery': ('join', 'crafts and hobbies', 'crafts'), 'life skills': ('broad', 'ethics', 'personal development'),
    'characters': ('none', '', 'not a theme'), 'characters and characteristics': ('none', '', 'not a theme'),
    'overland journeys to the pacific': ('join', 'pioneers', 'westward migration'), 'ninjas': ('join', 'samurai', 'warriors of Japan'),
    'paper work': ('join', 'crafts and hobbies', 'paper crafts'), 'origami': ('join', 'crafts and hobbies', 'paper crafts'),
    'prime ministers': ('join', 'government', 'heads of government'), 'businesspeople': ('join', 'entrepreneurship', 'business people'),
    'first loves': ('join', 'dating', 'first love'), 'size': ('none', '', "children's concept books"), 'middle': ('none', '', 'not a theme'),
    'america discovery and exploration': ('join', 'exploration', 'exploration'), 'clubs': ('none', '', 'unclear'),
    'missing persons investigation': ('join', 'kidnapping', 'missing persons'), 'strategic': ('join', 'strategy', 'strategic planning'),
    'eccentrics and eccentricities': ('none', '', 'unclear'), 'caribbean area': ('none', '', 'a place'), 'names personal': ('join', 'parenting', 'baby names'),
    'stepfamilies': ('join', 'family life', 'stepfamilies'), 'upper class': ('join', 'social issues', 'social class'), 'middle class': ('join', 'social issues', 'social class'),
    'dramatists': ('join', 'writers', 'playwrights'), 'hotels': ('mid', 'geography', 'travel'), 'bed and breakfast accommodations': ('mid', 'geography', 'travel'),
    'dinners and dining': ('join', 'cooking', 'food'), 'menus': ('join', 'cooking', 'food'), 'cake': ('join', 'baking', 'baking'), 'cookies': ('join', 'baking', 'baking'),
    'soups': ('join', 'cooking', 'food'), 'gastronomy': ('join', 'cooking', 'food'), 'eggs': ('join', 'cooking', 'food'), 'caterers and catering': ('join', 'cooking', 'food'),
    'restaurateurs': ('join', 'cooking', 'food'), 'toy and movable books specimens': ('none', '', 'a format'), 'wishes': ('none', '', 'unclear'),
    'united states supreme court': ('broad', 'police', 'courts and law'), 'united states social policy': ('join', 'social issues', 'social policy'),
    'corporate culture': ('join', 'management', 'organizations'), 'corporations': ('join', 'management', 'organizations'),
    'models persons': ('join', 'fashion', 'fashion models'), 'gold mines and mining': ('join', 'pioneers', 'gold rush and mining'),
    'biography': ('none', '', 'a genre (biography), not a theme'), 'fire fighters': ('broad', 'police', 'emergency services'),
    'prophecies': ('join', 'mysticism', 'prophecy'), 'pollution': ('join', 'sustainability', 'environment'), 'recycling waste etc': ('join', 'sustainability', 'environment'),
    'criticism': ('none', '', 'a genre (criticism)'), 'intimacy': ('join', 'relationships', 'intimate relationships'),
    'antislavery movements': ('join', 'slavery', 'abolition of slavery'), 'honesty': ('join', 'virtue', 'moral virtue'), 'responsibility': ('join', 'virtue', 'moral virtue'),
    'swordsmen': ('join', 'knights', 'swordsmen'), 'extortion': ('broad', 'police', 'crime'), 'petroleum industry and trade': ('join', 'energy', 'oil industry'),
    'holmes sherlock': ('none', '', 'a fictional character'), 'riddles': ('join', 'puzzles', 'riddles'), 'riddles juvenile': ('join', 'puzzles', 'riddles'),
    'puzzles': ('join', 'games', 'puzzles'), 'epic': ('none', '', 'a genre'), 'plot your own stories': ('none', '', 'a format'),
    'career changes': ('join', 'careers and work', 'careers'), 'lewis and clark expedition': ('join', 'exploration', 'exploration'),
    'intellectuals': ('none', '', 'unclear'), 'monologues': ('none', '', 'a form'), 'obama barack': ('none', '', 'a person'),
    'valentines day': ('join', 'holidays', 'holidays'), 'family owned business enterprises': ('join', 'entrepreneurship', 'family business'),
    'first day of school': ('join', 'school life', 'school'), 'middle school students': ('join', 'school life', 'school'),
    'earthquakes': ('join', 'disasters', 'natural disasters'), 'naturopathy': ('join', 'herbalism', 'alternative medicine'),
    'senses and sensation': ('join', 'human body', 'the senses'), 'land use': ('join', 'sustainability', 'land use'), 'sharing': ('none', '', "children's behaviour"),
    'olympics': ('mid', 'baseball', 'sports'), 'tiger': ('join', 'wildlife', 'wild animals'), 'polar bear': ('join', 'wildlife', 'wild animals'),
    'bees': ('join', 'insects', 'insects'), 'ability': ('none', '', 'unclear'), 'reconstruction': ('join', 'american civil war', 'Reconstruction after the Civil War'),
    'firearms': ('mid', 'naval warfare', 'weapons'), 'literature modern': ('none', '', 'not a theme'), 'hats': ('join', 'fashion', 'fashion'),
    'growth': ('none', '', 'unclear'), 'metamorphosis': ('none', '', 'unclear'), 'jealousy': ('broad', 'ethics', 'emotions'), 'loneliness': ('broad', 'ethics', 'emotions'),
    'blogs': ('join', 'internet', 'internet'), 'attention deficit hyperactivity disorder': ('join', 'depression', 'mental health condition'),
    'didactic': ('none', '', 'not a theme'), 'prints': ('join', 'drawing', 'printmaking'), 'printing': ('join', 'books and reading', 'printing'),
    'retirement': ('join', 'aging', 'retirement'), 'retirement income': ('join', 'personal finance', 'retirement money'),
    'supervillains': ('join', 'superheroes', 'comics'), 'pastoral': ('none', '', 'a genre'), 'giants': ('join', 'monsters', 'giants'),
    'separation': ('none', '', 'unclear'), 'equality': ('join', 'social justice', 'equality'), 'symbolism': ('none', '', 'not a theme'),
    'canoes and canoeing': ('join', 'outdoor recreation', 'outdoor recreation'), 'spring': ('join', 'seasons', 'seasons'), 'allegories': ('none', '', 'a genre'),
    'sound': ('join', 'physics', 'physics'), 'amusements': ('join', 'games', 'games'), 'vigilantes': ('broad', 'police', 'crime'),
    'extrasensory perception': ('join', 'psychic powers', 'psychic powers'), 'telepathy': ('join', 'psychic powers', 'psychic powers'),
    'jewelry': ('join', 'fashion', 'fashion'), 'orderliness': ('join', 'organizing', 'orderliness'), 'mistresses': ('join', 'infidelity', 'affairs'),
    'new hampshire': ('none', '', 'a place'), 'boy scouts': ('join', 'outdoor recreation', 'scouting'), 'bars drinking establishments': ('join', 'wine', 'drinking'),
    'alzheimers disease': ('join', 'dementia', 'dementia'), 'alzheimers disease patients': ('join', 'dementia', 'dementia'),
    'escapes': ('none', '', 'unclear'), 'action and adventure': ('none', '', 'a genre'), 'skin care and hygiene': ('join', 'beauty', 'personal care'),
    'social responsibility of business': ('join', 'management', 'business ethics'), 'traffic accidents': ('join', 'disasters', 'accidents'),
    'puppets': ('none', '', 'unclear'), 'literature and society': ('none', '', 'not a theme'), 'nineteen sixties': ('none', '', 'a period'),
    'nannies': ('join', 'parenting', 'childcare'), 'witnesses': ('broad', 'police', 'crime and law'), 'gifted children': ('join', 'child development', 'children'),
    'report writing': ('join', 'writing', 'writing'), 'autobiography': ('none', '', 'a genre'), 'deserts': ('join', 'wilderness', 'natural places'),
    'italian americans': ('join', 'immigration', 'immigrant communities'), 'hotelkeepers': ('mid', 'geography', 'travel'),
    'california northern': ('none', '', 'a place'), 'censorship': ('join', 'liberty', 'freedom of expression'), 'voluntarism': ('join', 'activism', 'volunteering'),
    'adjustment': ('none', '', 'unclear'), 'economic forecasting': ('join', 'money', 'economics'), 'cleanliness': ('join', 'health', 'hygiene'),
    'wood carving': ('join', 'crafts and hobbies', 'crafts'), 'critics': ('none', '', 'unclear'), 'visual perception': ('join', 'neuroscience', 'perception'),
    'speculation': ('join', 'investing', 'speculation'), 'white house': ('join', 'presidents', 'the presidency'),
    'united states territorial expansion': ('join', 'pioneers', 'westward expansion'), 'smuggling': ('broad', 'police', 'crime'),
    'apprentices': ('join', 'careers and work', 'work'), 'soul': ('join', 'spirituality', 'spirituality'), 'safety': ('none', '', 'unclear'),
    'childrens songs': ('mid', 'rock music', 'music'), 'nature': ('join', 'wilderness', 'nature'),
}
VALUE_PLACE.update(_UNPLACED)

# second round (13 Oct, after refreshing the print snapshot to 20.15 million rows, covering to mid-2020)
CORE_FACETS.update({k: _f(v) for k, v in {
    'guidebooks': 'theme:travel+form:guidebook', 'readers publications': 'form:early reader', 'western': 'genre:western',
    'romance comics': 'genre:romance+form:comics and graphic novels', 'legal fiction literature': 'genre:legal thriller+theme:law',
    'handbooks and manuals': 'form:how-to guide', 'interviews': 'form:interviews', 'study guides': 'form:textbook', 'best books': 'other:award_list',
    'alphabet books': 'audience:children', 'shapes': 'audience:children', 'star wars films': 'other:franchise', 'pok mon fictitious characters': 'other:franchise',
    'boxcar children fictitious characters': 'other:franchise', 'disney characters': 'other:franchise', 'justice league of america fictitious characters': 'other:franchise',
    'stilton geronimo': 'other:franchise', 'beatles': 'person:beatles', 'reagan ronald': 'person:reagan ronald', 'clinton hillary rodham': 'person:clinton hillary rodham',
    'korea north': 'place:north korea', 'bronx': 'place:new york city', 'charleston s': 'place:charleston', 'marthas vineyard': 'place:marthas vineyard',
    'east and': 'other:ambiguous', 'haiku': 'form:poetry', 'beat generation': 'genre:beat literature', 'surrealism': 'genre:surrealism',
}.items()})
VALUE_PLACE.update({
    'lost articles': ('none', '', "children's lost-and-found stories"), 'impostors and imposture': ('none', '', 'unclear'), 'impersonation': ('none', '', 'unclear'),
    'helping': ('join', 'kindness', 'helping others'), 'homecoming': ('none', '', 'unclear'), 'truthfulness and falsehood': ('join', 'virtue', 'honesty'),
    'judicial error': ('broad', 'police', 'courts and law'), 'attorney and client': ('broad', 'police', 'law'), 'amusement parks': ('join', 'games', 'amusements'),
    'vendetta': ('join', 'revenge', 'revenge'), 'detoxification health': ('broad', 'mental health', 'health'), 'human behavior': ('broad', 'ethics', 'psychology (broad node)'),
    'trolls': ('join', 'monsters', 'fantasy creatures'), 'hamsters': ('join', 'pets', 'pets'), 'human beings': ('none', '', 'too general'),
    'accidents': ('join', 'disasters', 'accidents'), 'traffic accident victims': ('join', 'disasters', 'accidents'), 'fire': ('join', 'disasters', 'fires'),
    'fires': ('join', 'disasters', 'fires'), 'rescue work': ('join', 'disasters', 'rescue'), 'stalkers': ('new', 'violence', 'stalking'), 'stalking': ('new', 'violence', 'stalking'),
    'texas rangers': ('join', 'police', 'law enforcement'), 'educational change': ('join', 'teaching', 'education'), 'advanced placement programs': ('join', 'teaching', 'education'),
    'singing': ('mid', 'rock music', 'music'), 'sound recording industry': ('mid', 'rock music', 'music'), 'simplicity': ('join', 'minimalism', 'simple living'),
    'cooperativeness': ('join', 'friendship', 'getting along'), 'cliques sociology': ('join', 'friendship', 'peer groups'), 'privacy right of': ('join', 'liberty', 'rights'),
    'arson': ('broad', 'police', 'crime'), 'regression': ('none', '', 'unclear'), 'shoes': ('join', 'fashion', 'fashion'), 'tattooing': ('join', 'fashion', 'body art'),
    'project apollo u s': ('join', 'space exploration', 'space exploration'), 'apples': ('join', 'cooking', 'food'), 'fruit': ('join', 'cooking', 'food'),
    'pumpkin': ('join', 'cooking', 'food'), 'salads': ('join', 'cooking', 'food'), 'chocolate': ('join', 'cooking', 'food'), 'canning and preserving': ('join', 'cooking', 'food'),
    'electric cooking slow': ('join', 'cooking', 'food'), 'beer': ('join', 'wine', 'drinks'), 'income distribution': ('join', 'money', 'economics'),
    'toleration': ('join', 'diversity', 'tolerance'), 'retirees': ('join', 'aging', 'retirement'), 'mistaken': ('none', '', 'unclear'), 'new products': ('join', 'marketing', 'products'),
    'light': ('join', 'physics', 'physics'), 'values': ('join', 'ethics', 'values'), 'ranches': ('join', 'farming', 'ranching'), 'gun control': ('join', 'social issues', 'a policy issue'),
    'lighthouses': ('join', 'seafaring', 'the sea'), 'bashfulness': ('join', 'self esteem', 'shyness'), 'refuse and refuse disposal': ('join', 'sustainability', 'waste'),
    'west u s discovery and exploration': ('join', 'exploration', 'exploration'), 'roommates': ('none', '', 'unclear'), 'glassware': ('join', 'antiques and collectibles', 'collecting'),
    'genius': ('none', '', 'unclear'), 'bee culture': ('join', 'farming', 'beekeeping'), 'ants': ('join', 'insects', 'insects'), 'garden ornaments and furniture': ('join', 'gardening', 'gardens'),
    'aztecs': ('join', 'indigenous', 'indigenous peoples of the Americas'), 'qaida organization': ('join', 'terrorism', 'al-Qaeda'), 'suffragists': ('join', 'feminism', "women's suffrage"),
    'soft toy making': ('join', 'crafts and hobbies', 'crafts'), 'oral history': ('broad', 'world war ii', 'history (broad node)'), 'surgeons': ('mid', 'disease', 'medicine'),
    'human experimentation in medicine': ('mid', 'disease', 'medicine'), 'microsoft excel computer file': ('join', 'software', 'software'), 'loyalty': ('join', 'virtue', 'virtue'),
    'literary landmarks': ('join', 'books and reading', 'literary places'), 'bridges': ('join', 'engineering', 'engineering'), 'alchemy': ('join', 'occult', 'occult'),
    'california gold discoveries': ('join', 'pioneers', 'gold rush'), 'guerrillas': ('mid', 'world war ii', 'war'), 'battles': ('mid', 'world war ii', 'war'),
    'twenty first century forecasts': ('join', 'future studies', 'the future'), 'spirit possession': ('join', 'demons', 'possession'), 'androids': ('join', 'robots', 'robots'),
    'green movement': ('join', 'sustainability', 'environmentalism'), 'propaganda': ('join', 'media', 'propaganda'), 'fur trade': ('join', 'pioneers', 'frontier trade'),
    'creation': ('join', 'theology', 'creation in religion'), 'women archaeologists': ('join', 'archaeology', 'archaeology'), 'hope': ('broad', 'ethics', 'emotions'),
    'trust': ('broad', 'ethics', 'emotions'), 'dissenters': ('join', 'activism', 'dissent'), 'college choice': ('join', 'college life', 'college'),
})

# reasons for the hand aliases and hand facet decisions (written to profile/hand_decisions.csv by 14)
ALIAS_REASON = {
    'indians of north america': 'LCSH wording for the v2 value', 'indians of south america': 'LCSH wording; indigenous peoples',
    'indians of central america': 'LCSH wording; indigenous peoples', 'indians of mexico': 'LCSH wording; indigenous peoples',
    'eskimos': 'LCSH wording; indigenous peoples', 'inuit': 'indigenous peoples', 'finance personal': 'LCSH inverted wording',
    'homosexuality': 'LCSH wording for the v2 value', 'gay men': 'kept as the v2 value', 'lesbians': 'LCSH plural of the v2 value',
    'bisexuals': 'LCSH plural of the v2 value', 'bisexuality': 'same as the v2 value', 'anti racism': 'spelling', 'antiracism': 'spelling',
    'rape': 'control category: rape is sexual violence', 'quarantine': 'control category: quarantine headings are about epidemics',
    'pandemics': 'control category wording', 'epidemics': 'control category wording', 'global warming fiction': 'control category wording',
    'climate change': 'control category wording', 'climatic change': 'LCSH wording (Climatic changes)', 'bereavement': 'same as grief',
    'loss psychology': 'LCSH wording for grief',
    'violence': 'the print heading Violence is general violence; the v2 value violence sits in the sexual and domestic violence control '
                '(v2 placement, kept for the sources v2 used), so the heading gets its own value, placed in the new violence node',
}
FACET_REASON = 'the core is a genre, form, audience, place, period, franchise or too vague to be a theme; given the facet shown'

# third round (13 Oct, final run on the full print file, rows to August 2026): frequent new values from 2020-2026 headings.
# (a) Newer Library of Congress genre/form terms are genres or forms, not themes (same facet rules as before).
_GF = 'a genre or form term of the newer LC genre/form vocabulary, not a theme'
_R3_FACETS = {
    'large print books': ('other:large print', 'large print format (LCGFT; replaces "Large type books")'),
    'livres en gros caractères': ('other:large print', 'large print format (French)'),
    'shonen manga': ('form:comics and graphic novels', _GF), 'shojo manga': ('form:comics and graphic novels', _GF),
    'isekai manga': ('genre:fantasy+form:comics and graphic novels', _GF),
    'boys love manga': ('genre:boys love+form:comics and graphic novels', _GF),
    'manga comic books': ('form:comics and graphic novels', _GF), 'bandes dessinées': ('form:comics and graphic novels', _GF),
    'slice of life comics': ('genre:slice of life+form:comics and graphic novels', _GF),
    'humorous comics': ('genre:humor+form:comics and graphic novels', _GF),
    'action and adventure comics': ('genre:adventure+genre:action+form:comics and graphic novels', _GF + '; embedding had put it in vampires / superheroes (0.53)'),
    'fantasy comics': ('genre:fantasy+form:comics and graphic novels', _GF + '; embedding had put it in vampires / superheroes (0.61)'),
    'science fiction comics': ('genre:science fiction+form:comics and graphic novels', _GF + '; embedding had put it in vampires / superheroes (0.62)'),
    'social issue comics': ('theme:social issues+form:comics and graphic novels', _GF + '; the theme part is social issues'),
    'political comics': ('theme:politics+form:comics and graphic novels', _GF + '; the theme part is politics'),
    'light novels': ('form:fiction', _GF), 'choral novels': ('form:fiction', _GF), 'linked stories': ('form:short stories', _GF),
    'nonfiction novels': ('genre:narrative nonfiction', _GF), 'creative nonfiction': ('genre:narrative nonfiction', _GF + '; embedding had put it in writing / writers'),
    'decodable books': ('form:early reader', _GF), 'decodables': ('form:early reader', _GF), 'dyslexia friendly books': ('form:early reader', _GF),
    'self instructional works': ('form:nonfiction', _GF + '; embedding had put it in teaching / homeschooling'),
    'paranormal romance': ('genre:paranormal romance', _GF), 'romance stories': ('genre:romance', _GF + '; embedding had put it in marriage'),
    'cozy mysteries': ('genre:cozy mystery', _GF), 'fiction thrillers suspense': ('genre:suspense', 'a bookseller (BISAC) genre term'),
    'fiction thrillers psychological': ('genre:psychological thriller', 'a bookseller (BISAC) genre term'),
    'fiction women': ('genre:womens fiction', 'a bookseller (BISAC) genre term; embedding had put it in feminism / gender'),
    'wordless picture books': ('audience:children+form:pictorial works', _GF + '; embedding had put it in photography (0.51)'),
    'self help publications': ('genre:self-help', _GF + '; embedding had put it in self harm (0.56), which is wrong'),
    'illustrated works': ('form:pictorial works', _GF + '; embedding had put it in drawing / artists'),
}
CORE_FACETS.update({k: _f(v) for k, (v, _) in _R3_FACETS.items()})
FACET_REASON_ITEM = {k: why for k, (_, why) in _R3_FACETS.items()}
# (b) frequent new topical values whose embedding placement was wrong, or that stayed unplaced although a node fits.
#     Control contents are not changed (coordinator decision): renamed LCSH headings that would belong to a control
#     ('multiracial people' for 'Racially mixed people', 'white people' for 'Whites', 'racial justice', 'climate justice')
#     are left unplaced and reported for a decision.
VALUE_PLACE.update({
    'woman woman relationships': ('join', 'lgbtq', 'LCSH term for lesbian relationships; embedding put it in feminism / gender (0.79)'),
    'man man relationships': ('join', 'lgbtq', 'LCSH term for gay male relationships; embedding put it in men / masculinity (0.87)'),
    'drag queens': ('join', 'lgbtq', 'drag culture; embedding put it in fashion / cosplay (0.51)'),
    'treasure hunting': ('join', 'exploration', 'treasure hunts are adventure and exploration; embedding put it in hunting (0.62), which is animal hunting'),
    'estranged families': ('join', 'family', 'family relationships; embedding put it in genealogy / grandparents (0.62)'),
    'noncitizens': ('join', 'immigration', 'LCSH term replacing "Aliens" (2021); unplaced at 0.28'),
    'freed persons': ('join', 'slavery', 'LCSH term replacing "Freedmen"; unplaced'),
    'day of the dead': ('join', 'holidays', 'a holiday; embedding put it in suicide / death and dying (0.59)'),
    'día de los muertos': ('join', 'holidays', 'a holiday; embedding put it in suicide / death and dying (0.61)'),
    'mythical animals': ('join', 'dragons', 'mythical creatures; embedding put it in shapeshifters / werewolves (0.65)'),
    'neurodiversity': ('join', 'autism', 'neurodiversity books are mostly about autism and ADHD; embedding put it in neuroscience (0.71)'),
    'neurodivergent people': ('join', 'autism', 'as neurodiversity; embedding put it in neuroscience (0.61)'),
    'attention deficit hyperactivity disorder in adults': ('join', 'mental health', 'ADHD (there is no ADHD value); unplaced at 0.45'),
    'school': ('join', 'school life', 'same as "schools" (hand placement); embedding put it in teaching / homeschooling (0.64)'),
    'animal comics': ('join', 'animals', 'comics about animals; embedding put it in farm animals / animal rights (0.62)'),
})
# (c) found in the final random spot check: cross-dressing headings had gone to transhumanism by embedding
VALUE_PLACE.update({
    'transvestites': ('join', 'lgbtq', 'cross-dressing (LCSH "Transvestites"); embedding put it in transhumanism (0.53), found in the random spot check'),
    'transvestism': ('join', 'lgbtq', 'cross-dressing; embedding put it in transhumanism (0.56)'),
    'cross dressers': ('join', 'lgbtq', 'LCSH term replacing "Transvestites"; unplaced at 0.44'),
})

# fourth round (13 Oct, coordinator decision): Library of Congress renames. A heading that LC renamed takes the placement
# of the heading it replaced, in every node (controls included). Only renames that LC made are listed. Evidence: the
# SPL data itself (records of the same title whose old-form heading was replaced by the new form; counted and dated by
# 14_v3_headings.py into profile/hand_decisions.csv) and my notes of LCSH changes. The LC authority records and change
# lists were not checked online (no new downloads).
# (old form, new form, LC change as I know it)
LC_RENAMES = [
    ('racially mixed', 'multiracial', 'LCSH "Racially mixed people" (and its forms for children, families, women, youth) changed to "Multiracial ..."'),
    ('whites', 'white people', 'LCSH "Whites" changed to "White people"'),
    ('blacks', 'black people', 'LCSH "Blacks" changed to "Black people"'),
    ('gays', 'gay people', 'LCSH "Gays" changed to "Gay people"'),
    ('bisexuals', 'bisexual people', 'LCSH "Bisexuals" changed to "Bisexual people"'),
    ('slaves', 'enslaved persons', 'LCSH "Slaves" changed to "Enslaved persons"'),
    ('women slaves', 'enslaved women', 'LCSH "Women slaves" changed to "Enslaved women"'),
    ('freedmen', 'freed persons', 'LCSH "Freedmen" changed to "Freed persons"'),
    ('illegal aliens', 'undocumented noncitizens', 'LCSH "Illegal aliens" changed to "Undocumented noncitizens" (2021 revision of the "Aliens" headings)'),
    ('transvestites', 'cross dressers', 'LCSH "Transvestites" changed to "Cross-dressers"'),
    ('transvestism', 'cross dressing', 'LCSH "Transvestism" changed to "Cross-dressing"'),
    ('manic depressive illness', 'bipolar disorder', 'LCSH "Manic-depressive illness" changed to "Bipolar disorder"'),
    ('manic depressive persons', 'people with bipolar disorder', 'LCSH "Manic-depressive persons" changed to "People with bipolar disorder"'),
    ('hearing impaired', 'hard of hearing people', 'LCSH "Hearing impaired" changed to "Hard of hearing people"'),
    ('brothers and sisters', 'siblings', 'LCSH "Brothers and sisters" changed to "Siblings"'),
    ('beat generation', 'beats persons', 'LCSH "Beat generation" changed to "Beats (Persons)"'),
]
# renames handled in the parser instead (_lcsh.EVENT_CANON), because the old form is a dated event heading:
LC_RENAMES_EVENTS = [
    ('vietnamese conflict', 'vietnam war', 'LCSH "Vietnamese Conflict, 1961-1975" changed to "Vietnam War, 1961-1975" (2006); the old form had been read as a person'),
    ('japanese americans evacuation and relocation', 'japanese americans forced removal and internment',
     'LCSH "Japanese Americans--Evacuation and relocation, 1942-1945" changed to "...--Forced removal and internment, 1942-1945"'),
]
# not applied, with reason:
LC_RENAMES_NOT_APPLIED = [
    ('aliens', 'noncitizens', 'LC changed "Aliens" to "Noncitizens", but in the SPL records the old "Aliens" heading is also used for extraterrestrials '
     '(comics, juvenile fiction), so its placement (aliens / ufos) is not a placement for noncitizens; "Noncitizens" keeps its hand placement (immigration)'),
    ('cookery', 'cooking', 'LC change of 2010; the old form is a genre heading and the new form a topic, so taking the old placement would remove the cooking theme'),
    ('aged', 'older people', 'LC change of 2005; both forms already in the same node'),
]
# old-form placements corrected so that the rename carries a correct placement
VALUE_PLACE.update({
    'illegal aliens': ('join', 'immigration', 'undocumented immigration; embedding had put it in aliens / ufos because of the word "aliens"'),
    'freedmen': ('join', 'slavery', 'formerly enslaved people (emancipation); unplaced before; its new form "Freed persons" was placed in slavery by hand'),
})
