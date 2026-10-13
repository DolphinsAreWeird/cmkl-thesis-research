# Hand inputs for the GDELT code mapping (01, 02). Everything is keyed by GKG theme code, so reruns and new GDELT
# weeks keep the same decisions. Reasons are given next to each rule; the report summarises them.

# ---- families (for reporting only), first match wins ----
FAMILIES = [
    ('WB (World Bank topics)', r'^WB_\d+_'), ('TAX_FNCACT (job titles and roles)', r'^TAX_FNCACT_'),
    ('TAX_DISEASE', r'^TAX_(DISEASE|CHRONICDISEASE)_'), ('TAX_ETHNICITY', r'^TAX_ETHNICITY_'), ('TAX_RELIGION', r'^TAX_RELIGION_'),
    ('TAX species lists', r'^TAX_(WORLD[A-Z]+|AGRICULHARMINSECTS|PLANTDISEASE)_'), ('TAX_TERROR (group names)', r'^TAX_TERROR_'),
    ('TAX_POLITICAL (party names)', r'^TAX_POLITICAL_'), ('TAX_WEAPONS', r'^TAX_WEAPONS_'), ('TAX_MILITARY (ranks)', r'^TAX_MILITARY_'),
    ('TAX_AIDGROUPS', r'^TAX_AIDGROUPS_'), ('TAX_FOODSTAPLES', r'^TAX_FOODSTAPLES_'), ('TAX other', r'^TAX_'),
    ('EPU', r'^EPU_'), ('CRISISLEX', r'^CRISISLEX_'), ('UNGP', r'^UNGP_'), ('SOC', r'^SOC_'), ('ECON', r'^ECON_'),
    ('USPEC', r'^USPEC_'), ('NATURAL_DISASTER', r'^NATURAL_'), ('MANMADE_DISASTER', r'^MANMADE_'), ('HUMAN_RIGHTS', r'^HUMAN_'),
    ('DISCRIMINATION', r'^DISCRIMINATION'), ('UNREST', r'^UNREST_'), ('SLFID', r'^SLFID_'), ('ENV', r'^ENV_'),
]

# ---- prefix stripping for the readable text, first match wins ----
STRIP = [
    (r'^WB_\d+_', ''), (r'^TAX_FNCACT_', ''), (r'^TAX_(CHRONIC)?DISEASE_', ''), (r'^TAX_ETHNICITY_', ''), (r'^TAX_RELIGION_', ''),
    (r'^TAX_WORLD[A-Z]+_', ''), (r'^TAX_TERROR_GROUP_', ''), (r'^TAX_POLITICAL_PARTY_', ''), (r'^TAX_MILITARY_TITLE_', ''),
    (r'^TAX_ECON_FREETRADEAGREEMENTS_', ''), (r'^TAX_SPECIAL_ISSUES_', ''), (r'^TAX_SPECIALDEATH$', 'DEATH'), (r'^TAX_[A-Z]+_', ''),
    (r'^EPU_ECONOMY_HISTORIC$', 'ECONOMY'), (r'^EPU_(POLICY|CATS)_', ''), (r'^EPU_', ''),
    (r'^CRISISLEX_[A-Z]\d\d_', ''), (r'^CRISISLEX_', ''), (r'^UNGP_', ''), (r'^SOC_POINTSOFINTEREST_', ''), (r'^SOC_', ''),
    (r'^ECON_WORLDCURRENCIES_', ''), (r'^ECON_DEVELOPMENTORGS_', ''), (r'^ECON_', ''), (r'^USPEC_', ''),
    (r'^NATURAL_DISASTER_', ''), (r'^MANMADE_DISASTER_', ''), (r'^HUMAN_RIGHTS_ABUSES_', ''), (r'^DISCRIMINATION_', ''),
    (r'^UNREST_', ''), (r'^SLFID_', ''), (r'^ENV_', ''), (r'^GENERAL_', ''), (r'^GEN_', ''), (r'^GOV_', ''),
    (r'^(ACT|MED|EMERG|CRM|LEG|POL|TECH|REL|MIL|INFO|ETH|AID|HEALTH)_', ''),
]
ACRONYMS = {
    'msm': 'mainstream news media', 'wmd': 'weapons of mass destruction', 'ict': 'information and communication technology',
    'ngo': 'non governmental organizations', 'ngos': 'non governmental organizations', 'ipo': 'initial public offering',
    'sme': 'small business', 'smes': 'small business', 'ppp': 'public private partnership', 'gmo': 'genetically modified food',
    'localgov': 'local government', 'msme': 'small business', 'msmes': 'small business',
}
EXTRA_WORDS = {'coronavirus', 'coronaviruses', 'internet', 'lgbt', 'cyber', 'cybersecurity', 'online', 'smartphone', 'bitcoin',
               'obamacare', 'covid', 'ebola', 'healthcare', 'microfinance', 'cryptocurrency', 'blockchain', 'website', 'email',
               'homophobia', 'homophobic', 'xenophobia', 'xenophobic', 'islamophobia', 'islamophobic', 'antisemitism', 'transgender',
               'sexting', 'cyberbullying', 'deforestation', 'desertification', 'biodiversity', 'telecom', 'wellbeing', 'ebook',
               'trafficking', 'gentrification', 'sustainability', 'programming', 'broadband', 'outsourcing', 'crowdsourcing',
               'interoperability', 'downsizing', 'wastewater', 'groundwater', 'freshwater', 'hydropower', 'peacekeeping',
               'ceasefire', 'whistleblower', 'checkpoint', 'macroeconomic', 'macroprudential', 'benchmarking', 'databases', 'bushfires',
               'heatwaves', 'mudslides', 'wiretapping', 'microwork', 'peoplesoft', 'landmine', 'intergovernmental', 'warrantless', 'deregulation', 'misallocations', 'homophobes', 'hackathons'}
NOT_WORDS = set()
TEXT_FIX = {
    'MEDIA_SOCIAL': 'social media', 'MANMADE_DISASTER_IMPLIED': 'man made disaster', 'EPU_ECONOMY_HISTORIC': 'economy',
    'CRISISLEX_T11_UPDATESSYMPATHY': 'sympathy and condolences after a disaster', 'CRISISLEX_C03_WELLBEING_HEALTH': 'wellbeing and health',
    'TAX_SPECIALDEATH': 'death', 'SOC_EXPRESSREGRET': 'expressing regret', 'MOVEMENT_GENERAL': 'social movements',
    'USPEC_POLITICS_GENERAL1': 'politics', 'USPEC_POLICY1': 'public policy', 'USPEC_UNCERTAINTY1': 'uncertainty',
    'MEDIA_MSM': 'mainstream news media', 'MOVEMENT_WOMENS': 'womens movement', 'MOVEMENT_SOCIAL': 'social movements',
    'MOVEMENT_ENVIRONMENTAL': 'environmental movement', 'MOVEMENT_OTHER': 'protest movements', 'ETH_INDIGINOUS': 'indigenous peoples',
    'HEALTH_SEXTRANSDISEASE': 'sexually transmitted diseases', 'CHARASMATIC_LEADERSHIP': 'charismatic leadership',
    'TECH_BIGDATA': 'big data', 'GOV_FOIA': 'freedom of information requests', 'EMERG_HAZMAT': 'hazardous materials',
    'SEIGE': 'siege', 'MARITIME_INCIDENT_SELF_IDENTIFIED': 'maritime incident', 'GOV_DISSOLVEGOV': 'dissolving a government',
    'EMERG_EMERGSHELTER': 'emergency shelter', 'TAX_DISEASE_H7N9': 'h7n9 bird flu', 'TAX_DISEASE_SWINE_FLU_H1N1': 'swine flu h1n1',
    'AID_HUMANITARIAN': 'humanitarian aid', 'AID_ECONOMIC': 'economic aid', 'INFO_RUMOR': 'rumors', 'INFO_HOAX': 'hoaxes',
    'CRISISLEX_C02_NEEDSPROVIDE_FOOD': 'food needs in a crisis', 'CRISISLEX_T08_MISSINGFOUNDTRAPPEDPEOPLE': 'missing and trapped people',
    'CRISISLEX_O02_RESPONSEAGENCIESATCRISIS': 'response agencies at a crisis', 'POL_HOSTVISIT': 'hosting a state visit',
    'GENERAL_PUBLIC_OPINION': 'public opinion', 'SOC_INTELSHARING': 'intelligence sharing', 'ECON_CUTOUTLOOK': 'cut economic outlook', 'CRISISLEX_T01_CAUTION_ADVICE': 'caution and advice in a crisis',
}

# ---- family rules: codes that name actors or entities rather than topics are excluded (name, regex, reason) ----
FAMILY_RULES = [
    ('actor: job title or role', r'^TAX_FNCACT_', 'marks a person by role (president, police, children, victim); not a topic of interest'),
    ('actor: military rank', r'^TAX_MILITARY_', 'military ranks and titles (officer, colonel)'),
    ('actor: ethnic or national group', r'^TAX_ETHNICITY_', 'adjectives of nationality and ethnicity (russian, american, black); mostly actor mentions'),
    ('entity: religious group or place of worship', r'^TAX_RELIGION_', 'members, denominations and buildings (muslims, church, mosque); belief systems themselves are whitelisted'),
    ('entity: named militant or political group', r'^TAX_TERROR_', 'names of groups (taliban, hamas, farc)'),
    ('entity: named political party', r'^TAX_POLITICAL_', 'names of parties (republican, labour party)'),
    ('entity: named aid or development organisation', r'^(TAX_AIDGROUPS_|ECON_DEVELOPMENTORGS_)', 'names of organisations (red cross, unicef, world bank)'),
    ('entity: named cartel', r'^TAX_CARTELS_', 'names of cartels'),
    ('entity: weapon type', r'^TAX_WEAPONS_', 'weapon names (gun, bomb, submarine)'),
    ('entity: species name', r'^TAX_(WORLD(BIRDS|MAMMALS|FISH|INSECTS|REPTILES|ARACHNIDS|CRUSTACEANS|MYRIAPODA)|AGRICULHARMINSECTS|PLANTDISEASE)_',
     'species names matched as words, very noisy (bear market, fox news, navy seal, jaguar cars)'),
    ('entity: food commodity', r'^TAX_FOODSTAPLES_', 'commodity names (rice, wheat, meat); mostly market and supply news'),
    ('entity: currency name', r'^ECON_WORLDCURRENCIES_', 'currency names (dollar, euro)'),
    ('entity: named trade agreement', r'^TAX_ECON_FREETRADEAGREEMENTS_', 'names of agreements (nafta, mercosur); generic free trade codes whitelisted'),
    ('place type, not a topic', r'^SOC_POINTSOFINTEREST_', 'type of place mentioned (school, hospital, airport)'),
    ('technical tag', r'^CRISISLEX_CRISISLEXREC$', 'flags that an article matched the crisis lexicon; no topic'),
]

# ---- whitelist: codes inside an excluded family that name a topic (belief systems, generic topics) ----
ALLOW = {
    # belief systems and practices themselves (not members or buildings)
    'TAX_RELIGION_ISLAM', 'TAX_RELIGION_CHRISTIANITY', 'TAX_RELIGION_BUDDHISM', 'TAX_RELIGION_JUDAISM', 'TAX_RELIGION_CATHOLICISM',
    'TAX_RELIGION_HINDUISM', 'TAX_RELIGION_SIKHISM', 'TAX_RELIGION_TAOISM', 'TAX_RELIGION_CONFUCIANISM', 'TAX_RELIGION_OCCULT',
    'TAX_RELIGION_WITCHCRAFT', 'TAX_RELIGION_PAGANISM', 'TAX_RELIGION_SHAMANISM', 'TAX_RELIGION_ATHEISM', 'TAX_RELIGION_SUFISM',
    'TAX_RELIGION_WICCA', 'TAX_RELIGION_KABBALAH', 'TAX_RELIGION_MORMONISM', 'TAX_RELIGION_PROTESTANTISM', 'TAX_RELIGION_SHARIA',
    # roles named after a control theme itself (epidemics, climate change)
    'TAX_FNCACT_EPIDEMIOLOGIST', 'TAX_FNCACT_EPIDEMIOLOGISTS', 'TAX_FNCACT_VIROLOGIST', 'TAX_FNCACT_VIROLOGISTS',
    'TAX_FNCACT_CLIMATOLOGIST', 'TAX_FNCACT_CLIMATOLOGISTS',
    # generic free trade codes
    'TAX_ECON_FREETRADEAGREEMENTS_FREE_TRADE_AGREEMENT', 'TAX_ECON_FREETRADEAGREEMENTS_FREE_TRADE_AGREEMENTS',
    'TAX_ECON_FREETRADEAGREEMENTS_FREETRADE_AGREEMENT', 'TAX_ECON_FREETRADEAGREEMENTS_FREETRADE_AGREEMENTS',
}
