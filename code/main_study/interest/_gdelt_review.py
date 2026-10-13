# Hand verdicts on GDELT code mappings (read by 02), written after reading the review lists on 13 Oct 2026.
# Two kinds of entries:
#   PATTERNS: group decisions written as rules (regex on the code), each with a reason. Applied to codes that have no
#             single-code verdict. action 'map' sends the code to `value`; 'drop' leaves it unmapped.
#   REVIEW:   single-code verdicts, code -> (verdict, value or None, note).
# Verdicts: correct (automatic value kept) | reassign (automatic value wrong; given value used) | add (not mapped
#   automatically; mapped by hand) | wrong (automatic value wrong and no good value; dropped) | generic (a word flag that
#   fires in a large share of all news, would swamp a node; dropped) | not a topic (an action or event type, not a theme;
#   dropped) | borderline (kept, see note) | excluded ok (a family rule excluded it and that is right) |
#   not mapped (reviewed in a control list, correctly left out of that category).
VERDICTS = {'correct', 'reassign', 'add', 'wrong', 'generic', 'not a topic', 'borderline', 'excluded ok', 'not mapped'}

# ---------------- group rules ----------------
EPIDEMIC_RX = (r'^(TAX_DISEASE_|WB_\d+_|HEALTH_|SOC_)(.*_)?(PANDEMIC|PANDEMICS|EPIDEMIC|EPIDEMICS|OUTBREAK|OUTBREAKS|CONTAGIOUS|'
               r'CORONAVIRUS|CORONAVIRUSES|SARS|MERS|EBOLA|MARBURG|LASSA|NIPAH|HANTAVIRUS|MONKEYPOX|SMALLPOX|CHOLERA|MEASLES|ZIKA|'
               r'DENGUE|YELLOW|TYPHUS|TYPHOID|POLIO|POLIOMYELITIS|DIPHTHERIA|WHOOPING|PERTUSSIS|MUMPS|CHIKUNGUNYA|PLAGUE|BLACK_DEATH|'
               r'FLU|INFLUENZA|H7N9|H1N1|TUBERCULOSIS|MENINGITIS|HEMORRHAGIC|QUARANTINE|COMMUNICABLE|TRANSMISSIBLE|TRANSMITTABLE|'
               r'INFECTIOUS|ZOONOTIC|ZOONOSES|SURVEILLANCE|PATHOGEN|PATHOGENS|RIFT|CRIMEANCONGO)(_.*)?$')
EPIDEMIC_NOT = (r'NON_COMMUNICABLE|AVIAN_CHOLERA|HOG_CHOLERA|EQUINE|CANINE|FELINE|CATTLE_PLAGUE|GOAT_PLAGUE|BOVINE|STOMACH_FLU|'
                r'HAEMOPHILUS|INFLUENZA_IN_BIRDS|MOLLUSCUM|MONONUCLEOSIS|INFECTIOUS_DIARRHEA|PERITONITIS|ANEMIA|SWINE_FEVER|POSTPOLIO|'
                r'PSEUDOTUBERCULOSIS|PARATUBERCULOSIS|LATENT_TUBERCULOSIS|BOVINE|ENDOCARDITIS|URBAN_YELLOW|'
                r'^SOC_(?!QUARANTINE)|WB_\d+_(?!.*(PANDEMICS|EBOLA|INFLUENZA|TUBERCULOSIS|COMMUNICABLE_DISEASE$|ZOONOTIC|EPIDEMIOLOGY_AND_DISEASE_SURVEILLANCE))')
WEATHER_STATE = r'^NATURAL_DISASTER_(SEVERE_WEATHER|EXTREME_WEATHER|WEATHER_EMERGENCY|BITTER_WEATHER|FREEZING_TEMPERATURES|EXTREME_COLD|SEVERE_COLD|COLD_SNAP|FRIGID|HEAT_SPELL)$'
SNOW = r'^NATURAL_DISASTER_(BLIZZARDS?|HEAVY_SNOW|HEAVY_SNOWFALL|SNOWSTORMS?|SNOW_STORMS?|WINTER_STORMS?|DUMPING_SNOW|ICY)$'
PATTERNS = [
    # name, include regex, exclude regex (or None), action, value, reason
    ('epidemic diseases and epidemic terms', EPIDEMIC_RX, EPIDEMIC_NOT, 'map', 'plague',
     'named epidemic and pandemic diseases of people (COVID-19 and other coronaviruses, flu, ebola, cholera, measles, zika, '
     'plague...) and epidemic terms (pandemic, outbreak, contagious, quarantine); the embedding model places "pandemic" near '
     '"weather", so these are mapped by hand; animal diseases and non-infectious conditions are left out'),
    ('weather conditions', WEATHER_STATE, None, 'map', 'weather', 'weather states that are not disasters'),
    ('snow and winter storms', SNOW, None, 'map', 'winter', 'snow and winter storms belong with winter (same middle node as weather)'),
    ('natural disaster events', r'^NATURAL_DISASTER_', r'^NATURAL_DISASTER_(ICE|HYPOTHERMIA|FROSTBITE|WATER_LEVEL)$', 'map', 'disasters',
     'GDELT frames hurricanes, floods, wildfires, earthquakes, droughts and heat waves as natural disasters; they go to the '
     'disasters value (survival / disasters), not to weather or to water (the swimming / water node)'),
    ('natural disaster codes that are not disasters', r'^NATURAL_DISASTER_(ICE|HYPOTHERMIA|FROSTBITE|WATER_LEVEL)$', None, 'drop', None,
     'ICE mostly matches the US immigration agency; hypothermia and frostbite are medical; water level is a measurement'),
    ('water sector codes', r'^(WB_\d+_|ENV_|UNGP_|CRISISLEX_|NATURAL_DISASTER_)', None, 'drop', None,
     'water supply, treatment, sanitation and waterways; the only "water" value sits with swimming, so these stay unmapped', {'water'}),
    ('food supply codes', r'^(WB_\d+_|UNGP_|CRISISLEX_|SOC_|FOOD_)', None, 'drop', None,
     'food security, trade, aid and supply; the food values are about cooking and eating', {'food', 'food and cooking', 'cooking'}),
    ('climate policy and science codes', r'^(WB_\d+_.*(CLIMATE|CARBON|GREENHOUSE|EMISSIONS|HYDROFLUOROCARBONS)|ENV_CARBONCAPTURE)',
     r'BUSINESS_CLIMATE|CLIMATE_SMART_AGRICULTURE', 'map', 'climate change',
     'World Bank climate change topics (mitigation, adaptation, finance, carbon pricing, climate science and services)'),
]

# ---------------- single-code verdicts ----------------
R = {}


def _s(codes, verdict, value, note):
    for c in codes.split():
        R[c] = (verdict, value, note)


# ---- control: epidemics and plagues (B15.M04.N05) ----
_s('TAX_DISEASE_EPIDEMIC TAX_DISEASE_OUTBREAK TAX_DISEASE_INFECTIOUS TAX_DISEASE_INFECTIOUS_DISEASE TAX_DISEASE_PATHOGENS '
   'TAX_DISEASE_PATHOGEN TAX_DISEASE_PLAGUE TAX_DISEASE_BUBONIC_PLAGUE', 'correct', None, 'epidemic term or epidemic disease')
_s('WB_1415_COMMUNICABLE_DISEASE TAX_DISEASE_COMMUNICABLE_DISEASES', 'reassign', 'epidemiology', 'communicable = infectious disease, the epidemics node rather than disease in general')
_s('TAX_DISEASE_BLACK_DEATH', 'reassign', 'plague', 'the Black Death is the 14th-century plague; the model matched "black" to Black life')
_s('TAX_DISEASE_MONKEYPOX', 'reassign', 'plague', 'monkeypox is an epidemic disease; the model matched "monkey" to primates')
_s('TAX_DISEASE_ZOONOSES', 'reassign', 'epidemiology', 'diseases passed from animals to people; epidemic origin, not zoology')
_s('TAX_FNCACT_EPIDEMIOLOGIST TAX_FNCACT_EPIDEMIOLOGISTS TAX_FNCACT_VIROLOGIST TAX_FNCACT_VIROLOGISTS', 'add', 'epidemiology',
   'role named after the theme itself (whitelisted from the role family); epidemiologists are quoted when epidemics are news')
_s('TAX_DISEASE_INFECTION TAX_DISEASE_VIRUS_INFECTION TAX_DISEASE_VIRAL_INFECTION TAX_DISEASE_VIRAL_DISEASE TAX_DISEASE_BACTERIAL_INFECTIONS',
   'reassign', 'disease', 'infection in general (wounds, hospitals, computer viruses); disease / illness, not the epidemics node')
_s('TAX_DISEASE_PNEUMONIA', 'add', 'disease', 'a disease, not specific to epidemics')
_s('HEALTH_SEXTRANSDISEASE', 'add', 'disease', 'sexually transmitted diseases; disease / illness')
_s('HEALTH_VACCINATION WB_1459_IMMUNIZATIONS', 'add', 'public health', 'vaccination is public health; it also rises with COVID-19 in 2021 but is not an epidemic theme itself')
_s('TAX_DISEASE_FEVER', 'not mapped', None, 'word match on "fever" (sports teams, "fever pitch"); a symptom, not a theme')
_s('TAX_DISEASE_MALARIA WB_1420_MALARIA', 'not mapped', None, 'endemic disease, mostly development news; not an epidemic theme')
_s('TAX_DISEASE_SWINE_FEVER TAX_DISEASE_AFRICAN_SWINE_FEVER', 'not mapped', None, 'animal epidemic (pigs)')
_s('TAX_DISEASE_BACTERIA TAX_DISEASE_BACTERIAL WB_178_PEST_MANAGEMENT', 'not mapped', None, 'not about epidemics')
_s('TAX_DISEASE_DISEASE WB_1406_DISEASES', 'correct', None, 'disease / illness')
_s('WB_1427_NON_COMMUNICABLE_DISEASE_AND_INJURY', 'borderline', 'disease', 'chronic disease and injury; disease / illness')

# ---- control: race and racism (B05.M02.N02) ----
_s('DISCRIMINATION_RACE_RACISM DISCRIMINATION_RACE_RACIST', 'correct', None, 'racism')
_s('WB_2890_AFFIRMATIVE_ACTION', 'add', 'race relations', 'affirmative action is a race relations topic')
_s('DISCRIMINATION_RELIGION_ANTIARAB', 'reassign', 'racism', 'anti-Arab prejudice is ethnic, not religious')
_s('DISCRIMINATION UNGP_FREEDOM_FROM_DISCRIMINATION', 'add', 'civil rights',
   'discrimination of every kind (race, sex, religion, disability, age); civil rights rather than racism, so it does not dilute the race control')
_s('HATE_SPEECH UNREST_SELF_IDENTIFIED_HATE_SPEECH UNREST_SELF_IDENTIFIED_HATE_CRIME', 'not mapped', None,
   'hate speech and hate crime cover race, religion and sexuality; left out of racism to keep that node specific (open question)')
_s('UNREST_POLICEBRUTALITY HUMAN_RIGHTS_ABUSES_POLICE_BRUTALITY', 'correct', None,
   'police brutality goes to the police node; it rose with the George Floyd protests but is not itself racism')
_s('WB_2508_ETHNIC_CLEANSING', 'add', 'genocide', 'ethnic cleansing; holocaust / genocide node')
_s('TAX_ETHNICITY_BLACK', 'excluded ok', None, 'mentions of Black people as actors (every story naming a Black person); not a theme. A sensitivity check is in the report')
_s('BAN BLACK_MARKET NATURAL_DISASTER_WHITEOUT TAX_DISEASE_COLORBLINDNESS TAX_DISEASE_BLACK_HAIRY_TONGUE WB_2889_MINORITIES_AND_DISENFRANCHISED_GROUPS_AND_JOBS WB_2565_DISCRIMINATORY_REGULATION',
   'not mapped', None, 'word overlap only, or too small and general')
_s('WB_933_ETHNIC_RELIGIOUS_AND_OTHER_MINORITIES', 'correct', None, 'minorities; multicultural / diversity node')
_s('SOC_SLAVERY WB_2511_SLAVERY', 'correct', None, 'slavery')
_s('REL_ANTISEMITISM', 'correct', None, 'antisemitism')

# ---- control: sexual and domestic violence (B12.M01.N02) ----
_s('RAPE WB_2443_RAPE_AND_SEXUAL_VIOLENCE WB_2441_DOMESTIC_VIOLENCE', 'correct', None, 'sexual or domestic violence')
_s('HARASSMENT', 'borderline', 'sexual violence',
   'GDELT has no separate sexual-harassment code; HARASSMENT is mostly sexual harassment in 2017-2018 news but also covers police and online harassment')
_s('GENDER_VIOLENCE', 'reassign', 'sexual violence', 'violence against women; the sexual and domestic violence node, not feminism / gender')
_s('WB_742_YOUTH_AND_GENDER_BASED_VIOLENCE WB_2901_GENDER_BASED_VIOLENCE', 'add', 'domestic violence', 'gender-based violence (domestic and sexual)')
_s('WB_2442_SEXUAL_TRAFICKING', 'add', 'human trafficking', 'sex trafficking; slavery / trafficking node')
_s('WB_2440_SURVIVAL_SEX', 'add', 'prostitution', 'sex for survival; slavery / prostitution node')
_s('WB_2432_FRAGILITY_CONFLICT_AND_VIOLENCE WB_2433_CONFLICT_AND_VIOLENCE WB_2462_POLITICAL_VIOLENCE_AND_WAR', 'reassign', 'war',
   'armed conflict; the taxonomy value "violence" sits in the sexual and domestic violence node, so conflict codes are sent to war instead')
_s('WB_2465_REVOLUTIONARY_VIOLENCE', 'reassign', 'revolution', 'revolutionary violence is political revolution, not interpersonal violence')
_s('VIOLENT_UNREST', 'reassign', 'activism', 'riots and violent protest; political activism and protest')
_s('WB_930_VIOLENCE_PREVENTION', 'correct', None, 'violence prevention; the value violence is in the v3 node B12.M01.N04 Violence and violent crime')
_s('UNGP_CRIME_VIOLENCE WB_741_URBAN_CRIME_AND_VIOLENCE', 'reassign', 'violence',
   'crime and violence; rechecked after the v3 move: the new node B12.M01.N04 Violence and violent crime names exactly this (cosine to crime and to violence nearly equal)')
_s('UNREST_BELLIGERENT SELF_IDENTIFIED_ATROCITY PERSECUTION HUMAN_RIGHTS_ABUSES_TORTURE HUMAN_RIGHTS_ABUSES_TORTURED HUMAN_RIGHTS_ABUSES_BEATINGS '
   'WB_2513_CRIMES_AGAINST_HUMANITY HUMAN_RIGHTS_ABUSES_EXTRAJUDICIAL HUMAN_RIGHTS_ABUSES_CONCENTRATION_CAMP HUMAN_RIGHTS_ABUSES_CONCENTRATION_CAMPS '
   'HUMAN_RIGHTS_ABUSES_MASS_GRAVES HUMAN_RIGHTS_ABUSES_TORTURING HUMAN_RIGHTS_ABUSES_ENFORCED_DISAPPEARANCE HUMAN_RIGHTS_ABUSES_ELECTRIC_SHOCKS '
   'HUMAN_RIGHTS_ABUSES_ENFORCED_DISAPPEARANCES HUMAN_RIGHTS_ABUSES_GULAG',
   'not mapped', None, 'state or armed violence, or word overlap; not sexual or domestic violence')
_s('HUMAN_RIGHTS_ABUSES_WATERBOARDING HUMAN_RIGHTS_ABUSES_WATERBOARDED HUMAN_RIGHTS_ABUSES_WATERBOARD', 'wrong', None, 'torture matched to surfing and water')
_s('TAX_DISEASE_TRAUMA TAX_DISEASE_MULTIPLE_TRAUMA', 'wrong', None, 'physical injury (trauma centres); the value means psychological trauma')
_s('HUMAN_RIGHTS_ABUSES_FORCED_MARRIAGE HUMAN_RIGHTS_ABUSES_FORCED_MARRIAGES SOC_EARLYMARRIAGE WB_2444_EARLY_MARRIAGE', 'borderline', 'arranged marriage',
   'forced and child marriage; marriage / arranged marriage node')
_s('HUMAN_TRAFFICKING WB_2458_HUMAN_TRAFFICKING', 'correct', None, 'human trafficking')
_s('BULLYING', 'correct', None, 'bullying')
_s('ASSASSINATION', 'borderline', None, 'political assassination; kept on murder')
_s('HUMAN_RIGHTS_ABUSES_ARBITRARY_KILLINGS HUMAN_RIGHTS_ABUSES_SUMMARILY_KILLED', 'borderline', None, 'killings; kept on murder')
_s('TAX_DISEASE_ETHANOL_ABUSE WB_1438_ALCOHOL_AND_SUBSTANCE_ABUSE TAX_DISEASE_SUBSTANCE_ABUSE', 'correct', None, 'addiction')
_s('TAX_DISEASE_SEXUALLY_TRANSMITTED_DISEASES TAX_DISEASE_SEXUALLY_TRANSMITTED_DISEASE TAX_DISEASE_SEXUALLY_TRANSMITTED_INFECTIONS '
   'TAX_DISEASE_SEXUALLY_TRANSMITTED_INFECTION', 'add', 'disease', 'sexually transmitted disease; disease / illness, not sexual violence')
_s('TAX_DISEASE_SEXUAL_DYSFUNCTION TAX_DISEASE_SEXUAL_IMPOTENCE', 'add', 'sexuality', 'sexual health; sexuality node')
_s('WB_739_POLITICAL_VIOLENCE_AND_CIVIL_WAR', 'correct', None, 'civil war')
_s('TERROR WB_2467_TERRORISM', 'correct', None, 'terrorism')
_s('TAX_DISEASE_PSYCHOLOGICAL_TRAUMA', 'correct', None, 'psychological trauma')

# ---- control: climate change and weather (B09.M07.N02) ----
_s('ENV_CLIMATECHANGE UNGP_CLIMATE_CHANGE_ACTION WB_567_CLIMATE_CHANGE', 'correct', None, 'climate change')
_s('CRISISLEX_O01_WEATHER', 'borderline', None,
   'weather words in crisis news (storms, snow); kept on weather, so the climate node mixes climate change and weather. The control table also shows the climate change value alone')
_s('TAX_FNCACT_CLIMATOLOGIST TAX_FNCACT_CLIMATOLOGISTS', 'add', 'climate change', 'role named after the theme itself (whitelisted)')
_s('WB_405_BUSINESS_CLIMATE', 'not mapped', None, '"business climate", not climate')
_s('WB_1949_CLIMATE_SMART_AGRICULTURE', 'borderline', None, 'climate-smart farming; kept on agriculture')
_s('MOVEMENT_ENVIRONMENTAL', 'add', 'environment', 'environmental movement; environment (middle node)')
_s('TAX_FNCACT_METEOROLOGIST TAX_FNCACT_WEATHERMAN TAX_FNCACT_WEATHERMEN TAX_FNCACT_WEATHERCASTER', 'excluded ok', None, 'forecasters quoted in weather stories (role family)')
_s('WB_525_RENEWABLE_ENERGY WB_526_RENEWABLE_ENERGY_POLICY_AND_REGULATION', 'correct', 'energy', 'renewable energy; energy node')
_s('WB_1791_AIR_POLLUTION WB_601_POLLUTION_MANAGEMENT', 'add', 'environment', 'pollution; environment (middle node)')
_s('SOC_POLARIZED', 'wrong', None, 'political polarization matched to polar exploration')
_s('TAX_DISEASE_REMISSION TAX_DISEASE_HYPOTHERMIA TAX_DISEASE_COMMON_COLD TAX_DISEASE_FROSTBITE TAX_DISEASE_SUNBURN '
   'TAX_DISEASE_CARBON_MONOXIDE_POISONING TAX_DISEASE_HEAT_EXHAUSTION TAX_DISEASE_WINTER_DEPRESSION TAX_DISEASE_PRICKLY_HEAT '
   'TAX_DISEASE_STORM_SYNDROME TAX_DISEASE_BODY_TEMPERATURE_CHANGES', 'not mapped', None, 'medical conditions; word overlap with weather')

# ---- top 100 codes by volume ----
_s('USPEC_POLITICS_GENERAL1 USPEC_POLICY1 USPEC_UNCERTAINTY1 EPU_POLICY_POLITICAL EPU_POLICY_GOVERNMENT EPU_POLICY_LAW EPU_ECONOMY_HISTORIC EPU_ECONOMY',
   'generic', None, 'word flags of the policy-uncertainty dictionaries ("politics", "government", "law", "economy"); they fire on one common word in a large share of all news')
_s('GENERAL_GOVERNMENT GENERAL_HEALTH MEDICAL', 'generic', None, 'GDELT catch-all tags for any story that mentions government, health or medicine')
_s('LEADER', 'generic', None, 'marks any story naming a leader; mapped to "leadership" (a self-help theme) by word similarity, which is wrong')
_s('MANMADE_DISASTER_IMPLIED', 'generic', None, 'catch-all accident and disaster words; would swamp the disasters node')
_s('CRISISLEX_T03_DEAD', 'generic', None, 'crisis lexicon flag for death counts in any story')
_s('KILL', 'not a topic', None, 'any killing (war, police, accidents); mapping it to murder would swamp that node')
_s('CRISISLEX_T11_UPDATESSYMPATHY', 'not a topic', None, 'crisis updates and condolences; not grief as a theme')
_s('LEGISLATION', 'generic', None, 'fires on bills and laws in all political news')
_s('WB_678_DIGITAL_GOVERNMENT', 'generic', None, 'World Bank e-government tag; fires on government plus any digital word')
_s('WB_621_HEALTH_NUTRITION_AND_POPULATION', 'generic', None, 'World Bank health sector tag on most health stories; matched to nutrition by word similarity, which is wrong')
_s('WB_840_JUSTICE', 'reassign', 'law', 'justice sector (courts); law rather than justice as fairness')
_s('WB_1350_PHARMACEUTICALS', 'reassign', 'medicine', 'medicines, not recreational drugs')
_s('WB_137_WATER', 'wrong', None, 'water supply and sanitation; the "water" value sits with swimming')
_s('WB_1618_FOOD_DISTRIBUTION', 'wrong', None, 'food aid and supply; not cooking and food')
_s('MARITIME', 'reassign', 'seafaring', 'shipping and sea news; seafaring (same node as sailing)')
_s('MARITIME_INCIDENT MARITIME_INCIDENT_SELF_IDENTIFIED', 'reassign', 'shipwrecks', 'ship accidents; same node as naval warfare')
_s('WB_2470_PEACE_OPERATIONS_AND_CONFLICT_MANAGEMENT WB_2478_PEACE_PROCESSES_AND_DIALOGUE', 'borderline', None, 'peacekeeping; the peace value shares a node with the Vietnam and Iraq wars')
_s('WB_697_SOCIAL_PROTECTION_AND_LABOR', 'borderline', None, 'welfare and labour; kept on social work')
_s('WB_1331_HEALTH_TECHNOLOGIES', 'borderline', None, 'health technology; kept on health (broad node only)')
_s('CRISISLEX_C04_LOGISTICS_TRANSPORT', 'borderline', None, 'crisis lexicon for transport; kept on transportation')
_s('WB_1497_EDUCATION_MANAGEMENT_AND_ADMINISTRATION', 'reassign', 'education', 'school administration; education, not business management')
for c in ('EDUCATION WB_470_EDUCATION WB_1467_EDUCATION_FOR_ALL WB_133_INFORMATION_AND_COMMUNICATION_TECHNOLOGIES WB_652_ICT_APPLICATIONS '
          'MEDIA_MSM WB_694_BROADCAST_AND_MEDIA MEDIA_SOCIAL WB_135_TRANSPORT WB_1803_TRANSPORT_INFRASTRUCTURE PUBLIC_TRANSPORT TRAFFIC '
          'ARMEDCONFLICT WB_831_GOVERNANCE WB_723_PUBLIC_ADMINISTRATION WB_2670_JOBS WB_2769_JOBS_STRATEGIES WB_855_LABOR_MARKETS WB_2748_EMPLOYMENT '
          'WB_2690_CATEGORIES_OF_EMPLOYMENT UNGP_HEALTHCARE EPU_CATS_HEALTHCARE WB_635_PUBLIC_HEALTH WB_1458_HEALTH_PROMOTION_AND_DISEASE_PREVENTION '
          'ELECTION WB_832_ANTI_CORRUPTION WB_2024_ANTI_CORRUPTION_AUTHORITIES CORRUPTION WB_1014_CRIMINAL_JUSTICE SOC_GENERALCRIME SCIENCE '
          'WB_698_TRADE WB_775_TRADE_POLICY_AND_INTEGRATION WB_435_AGRICULTURE_AND_FOOD_SECURITY AGRICULTURE MILITARY WB_2453_ORGANIZED_CRIME '
          'ORGANIZED_CRIME WB_2456_DRUGS_AND_NARCOTICS DRUG_TRADE CRIME_ILLEGAL_DRUGS PROTEST MOVEMENT_OTHER WB_2530_BUSINESS_ENVIRONMENT '
          'WB_1920_FINANCIAL_SECTOR_DEVELOPMENT WB_2495_DETENTION_PRISON_AND_CORRECTIONS_REFORM WB_695_POVERTY POVERTY TOURISM WB_825_TOURISM '
          'DEMOCRACY WB_566_ENVIRONMENT_AND_NATURAL_RESOURCES WB_639_REPRODUCTIVE_MATERNAL_AND_CHILD_HEALTH URBAN WB_699_URBAN_DEVELOPMENT '
          'GEN_HOLIDAY SOC_INNOVATION WB_590_ECOSYSTEMS WB_1829_ECOSYSTEM_MANAGEMENT WB_2203_HUMAN_RIGHTS SELF_IDENTIFIED_HUMAN_RIGHTS '
          'TAX_DISEASE_CANCER WB_1431_CANCER WB_843_DISPUTE_RESOLUTION WB_936_ALTERNATIVE_DISPUTE_RESOLUTION NEGOTIATIONS '
          'WB_2473_DIPLOMACY_AND_NEGOTIATIONS WB_2836_MIGRATION_POLICIES_AND_JOBS IMMIGRATION WB_1777_FORESTS WB_436_FORESTRY RELIGION '
          'WB_1986_MOUNTAINS WB_593_MOUNTAIN_ECOSYSTEMS UNGP_POLITICAL_FREEDOMS ECON_ENTREPRENEURSHIP WB_134_SOCIAL_DEVELOPMENT WB_644_NUTRITION '
          'DISABILITY WB_1464_HEALTH_OF_THE_DISABLED WB_2082_LAW_ENFORCEMENT WB_1934_CIVILLIAN_POLICE_AND_SECURITY_SERVICES '
          'WB_318_FINANCIAL_ARCHITECTURE_AND_BANKING WB_336_NON_BANK_FINANCIAL_INSTITUTIONS WB_670_ICT_SECURITY CYBER_ATTACK SOC_SUICIDE LGBT '
          'WB_615_GENDER KIDNAP WB_2439_WOMEN_ABDUCTION WB_669_SOFTWARE_INFRASTRUCTURE WB_665_SOFTWARE_AS_A_SERVICE WB_643_AGING_POPULATION '
          'SOC_AGINGPOPULATION TAX_RELIGION_ISLAM TAX_RELIGION_CHRISTIANITY TAX_RELIGION_BUDDHISM TAX_RELIGION_JUDAISM TAX_RELIGION_CATHOLICISM '
          'TAX_RELIGION_HINDUISM TAX_RELIGION_ATHEISM TAX_RELIGION_PAGANISM TAX_RELIGION_MORMONISM TAX_RELIGION_OCCULT TAX_RELIGION_WITCHCRAFT '
          'ETH_INDIGINOUS WB_2960_INDIGENOUS_PEOPLES WB_962_INTERNATIONAL_LAW WB_1028_INTERNATIONAL_BOUNDARIES WB_1430_MENTAL_HEALTH '
          'TAX_DISEASE_PREGNANCY WB_177_ANIMAL_PRODUCTION EPU_CATS_SOVEREIGN_DEBT_CURRENCY_CRISES TAX_DISEASE_HIV TAX_DISEASE_HIV_AIDS '
          'TAX_DISEASE_HIV_INFECTION TAX_DISEASE_HIV_INFECTIONS WB_508_POWER_SYSTEMS ENV_FISHERY WB_341_INVESTMENT_FUNDS ECON_FOREIGNINVEST '
          'WB_2509_GENOCIDE TAX_DISEASE_GAMBLING LITERACY TAX_DISEASE_AUTISM TAX_DISEASE_AUTISM_SPECTRUM_DISORDER WB_758_ORPHANS SOC_FASCISM '
          'AVIATION_INCIDENT MANMADE_DISASTER_PLANE_CRASH NATURAL_DISASTER_NATURAL_DISASTERS TECH_VIRTUALREALITY WB_2416_INTERNET_OF_THINGS '
          'TECH_BIGDATA WB_661_BIG_DATA WB_479_EARLY_CHILD_DEVELOPMENT WB_725_ORGANIZATIONAL_MANAGEMENT SLFID_MINERAL_RESOURCES '
          'WB_896_GEOLOGICAL_MAPPING_AND_DATABASES WB_2194_ANIMAL_WELFARE TAX_DISEASE_BLINDNESS TAX_DISEASE_DEAFNESS WB_364_CONSUMER_PROTECTION '
          'WB_655_INFORMATION_MANAGEMENT WB_1461_HEALTHY_LIFESTYLES CHARASMATIC_LEADERSHIP WB_1532_TEACHER_TRAINING WB_1526_TEACHER_CAREERS '
          'CRISISLEX_T05_MONEY WB_345_SOVEREIGN_WEALTH_FUNDS WB_2198_CHEMICAL_ENGINEERING WB_2390_TELEVISION_BROADCASTING '
          'WB_2756_LABOR_PRODUCTIVITY WB_605_WILDLIFE_RESOURCES WB_663_GEOGRAPHIC_INFORMATION_SYSTEMS WB_1558_LANGUAGE_OF_INSTRUCTION '
          'TAX_DISEASE_MEMORY_DISORDERS WB_1864_PLANT_VARIETY_PROTECTION TAX_DISEASE_SELF_MUTILATION TAX_DISEASE_COMPULSIVE_GAMBLING '
          'WB_2187_ANIMAL_HEALTH').split():
    R.setdefault(c, ('correct', None, 'checked by hand'))
_s('TAX_DISEASE_DEPRESSION', 'borderline', None, 'mostly the illness, sometimes economic depression; kept on depression')
_s('JUSTICE', 'borderline', None, 'justice in general; kept on justice')
_s('WB_180_FOOD_SAFETY', 'borderline', None, 'food safety; kept on food (middle node)')
_s('CRISISLEX_C01_CHILDREN_AND_EDUCATION', 'borderline', None, 'children in crisis news; kept on child development')
_s('WB_1927_STRATEGIC_POLICY_PLANNING', 'borderline', None, 'policy planning; kept on planning')
_s('WB_2969_SOCIAL_CONFLICT', 'borderline', None, 'social conflict; kept on social issues')
_s('TAX_DISEASE_GENETIC_DISEASES', 'borderline', None, 'genetic disease; kept on genetics')
_s('TAX_DISEASE_INSECT_BITES TAX_DISEASE_INSECT_BITE TAX_DISEASE_CANINE_DISTEMPER TAX_DISEASE_CAT_DISEASES MANMADE_DISASTER_RESCUE_DIVERS WB_2920_TELEVISION_INSTRUCTION TAX_DISEASE_SOCIOPATHIC_PERSONALITY',
   'borderline', None, 'small code, plausible node')
_s('WB_1447_GERIATRICS', 'reassign', 'aging', 'care of old people; aging, not grandparents')
_s('JIHAD', 'reassign', 'terrorism', 'news use is mostly militant jihad')
_s('FREESPEECH', 'reassign', 'liberty', 'freedom of speech; liberty, not public speaking')
_s('SUICIDE_ATTACK', 'reassign', 'terrorism', 'suicide bombing is terrorism, not suicide')
_s('WB_2599_CHANGE_MANAGEMENT', 'reassign', 'management', 'organisational change management')
_s('TAX_DISEASE_AMNESIA', 'reassign', 'amnesia', 'amnesia (same node as memory)')
_s('TAX_DISEASE_NEUROSIS TAX_DISEASE_PSYCHOSES TAX_DISEASE_PERSONALITY_DISORDERS', 'reassign', 'mental illness', 'mental illness, not neuroscience or therapy')
_s('TAX_DISEASE_NEUROTICISM', 'reassign', 'personality', 'a personality trait')
_s('TAX_DISEASE_ASTROCYTOMA', 'reassign', 'cancer', 'a brain tumour, matched to astrophysics by word form')
_s('WB_2989_RAINFED_CROPS', 'reassign', 'agriculture', 'crops; agriculture')
_s('WB_1747_PRODUCT_MARKET_REGULATION_AND_COMPETITION_ADVOCACY WB_836_POLITICAL_ECONOMY_OF_REFORM', 'wrong', None, 'competition law and reform politics; no fitting value')
_s('TAX_DISEASE_NIGHT_TERRORS TAX_DISEASE_ELEPHANTIASIS TAX_DISEASE_COMMUNICATION_DISORDERS TAX_DISEASE_SPEECH_DEVELOPMENT '
   'TAX_DISEASE_GEOGRAPHIC_ATROPHY TAX_DISEASE_TENNIS_ELBOW', 'wrong', None, 'medical term matched by word form (night, elephants, geography, tennis)')

# ---- second pass (remaining control-list and per-node codes) ----
for c in ('DISCRIMINATION_IMMIGRATION_XENOPHOBIC DISCRIMINATION_IMMIGRATION_XENOPHOBIA DISCRIMINATION_IMMIGRATION_ANTIIMMIGRANT '
          'DISCRIMINATION_IMMIGRATION_ANTIIMMIGRATION DISCRIMINATION_IMMIGRATION_ULTRANATIONALIST DISCRIMINATION_IMMIGRATION_AGAINST_IMMIGRANTS '
          'DISCRIMINATION_IMMIGRATION_ANTI_IMMIGRATION DISCRIMINATION_IMMIGRATION_ULTRA_NATIONALIST DISCRIMINATION_IMMIGRATION_ANTI_IMMIGRANTS '
          'DISCRIMINATION_IMMIGRATION_ULTRANATIONALISTS DISCRIMINATION_IMMIGRATION_XENOPHOBES DISCRIMINATION_IMMIGRATION_XENOPHOBE '
          'DISCRIMINATION_IMMIGRATION_ATTACKS_ON_IMMIGRANTS DISCRIMINATION_IMMIGRATION_ANTI_IMMIGRANT DISCRIMINATION_IMMIGRATION_OPPOSED_TO_IMMIGRATION '
          'DISCRIMINATION_IMMIGRATION_OPPOSED_TO_IMMIGRANTS DISCRIMINATION_IMMIGRATION_ULTRA_NATIONALISTS DISCRIMINATION_IMMIGRATION_ATTACKS_AGAINST_IMMIGRANTS '
          'DISCRIMINATION_IMMIGRATION_ANTIIMMIGRANTS').split():
    R[c] = ('correct', None, 'hostility to immigrants; immigration node (not racism)')
_s('DISCRIMINATION_LGBT_HOMOPHOBIC DISCRIMINATION_LGBT_HOMOPHOBIA DISCRIMINATION_LGBT_ANTIGAY DISCRIMINATION_LGBT_HOMOPHOBES '
   'DISCRIMINATION_LGBT_GAY_BASHING DISCRIMINATION_LGBT_ANTI_GAY', 'correct', None, 'homophobia; LGBTQ node')
_s('REL_ISLAMOPHOBIA DISCRIMINATION_RELIGION_ISLAMOPHOBIA DISCRIMINATION_RELIGION_ISLAMOPHOBIC DISCRIMINATION_RELIGION_ANTIISLAM '
   'DISCRIMINATION_RELIGION_ANTI_ISLAM', 'borderline', None, 'Islamophobia; kept on Islam (not racism)')
_s('DISCRIMINATION_RELIGION_RELIGIOUS_DISCRIMINATION DISCRIMINATION_RELIGION_ANTICHRISTIAN', 'correct', None, 'religious discrimination; religion nodes')
_s('WB_2507_HUMAN_RIGHTS_ABUSES_AND_VIOLATIONS WB_2519_RESPONSES_TO_HUMAN_RIGHTS_ABUSES HUMAN_RIGHTS_ABUSES_HUMAN_RIGHTS_ABUSES '
   'HUMAN_RIGHTS_ABUSES_HUMAN_RIGHTS_ABUSE', 'correct', None, 'human rights')
_s('WB_1614_NUTRITIONAL_PROGRAMS', 'correct', None, 'nutrition')
_s('UNGP_GENDER_EQUALITY', 'reassign', 'feminism', 'gender equality; feminism (same node as gender identity)')
_s('WB_1615_THERAPEUTIC', 'reassign', 'medicine', 'medical therapeutics (treatments and drugs), not psychotherapy')
_s('WB_141_WATER_RESOURCES_MANAGEMENT WB_138_WATER_SUPPLY', 'wrong', None, 'water supply; the "water" value sits with swimming')
_s('WB_942_ACCESS_TO_JUSTICE', 'borderline', None, 'access to courts; kept on justice')
_s('CRISISLEX_C02_NEEDSPROVIDE_FOOD', 'wrong', None, 'food needs in a crisis; not cooking and food')
_s('TAX_SPECIALDEATH', 'borderline', None, 'death; kept on death')
_s('TAX_DISEASE_BIPOLAR_DISORDER TAX_DISEASE_BIPOLAR_DEPRESSION TAX_DISEASE_UNIPOLAR_DEPRESSION TAX_DISEASE_TRAUMATIC_STRESS_DISORDER '
   'WB_2501_COMBATANT_AND_VETERAN_SUICIDE', 'correct', None, 'mental health and suicide')
_s('TAX_DISEASE_ACUTE_DISEASE WB_1414_BURDEN_OF_DISEASE TAX_DISEASE_BEST_DISEASE TAX_DISEASE_NEGLECTED_DISEASES TAX_DISEASE_DISEASE_MODELS '
   'TAX_DISEASE_DISEASE_SUSCEPTIBILITY TAX_DISEASE_NORRIE_DISEASE TAX_DISEASE_MAREK_DISEASE TAX_DISEASE_WEIL_DISEASE', 'correct', None, 'disease / illness (small codes)')
_s('WB_1184_COMMERCIAL_PRESENCE WB_1693_GEOGRAPHIC_TARGETING TAX_DISEASE_ZOOPHILIA', 'wrong', None, 'word-form match (marketing, geography, zoology)')
_s('TAX_DISEASE_DRUGINDUCED_PSYCHOSIS', 'reassign', 'mental illness', 'psychosis; mental illness')
_s('TAX_DISEASE_NEUROCYSTICERCOSIS TAX_DISEASE_COGNITIVE_DISEASE', 'reassign', 'disease', 'diseases, not neuroscience or cognitive science')
_s('TAX_DISEASE_BIRD_DISEASES', 'borderline', None, 'bird diseases; kept on birds')
_s('TAX_DISEASE_CATTLE_PLAGUE', 'reassign', 'farm animals', 'cattle plague (rinderpest) is an animal disease, not a human epidemic')
_s('FOOD_STAPLE', 'wrong', None, 'staple food commodities; not cooking and food')
_s('ENV_HYDRO', 'reassign', 'energy', 'hydropower; energy')
_s('ENV_WATERWAYS', 'wrong', None, 'rivers and canals; the "water" value sits with swimming')
_s('TAX_DISEASE_NEUROLOGIC_DISEASE', 'reassign', 'disease', 'a disease, not neuroscience')
_s('TAX_DISEASE_REDWATER', 'wrong', None, 'a cattle disease matched to water')
_s('NATURAL_DISASTER_VIOLENT_STORM NATURAL_DISASTER_VIOLENT_STORMS', 'add', 'disasters', 'storms; natural disaster events (corrected: had been left out by an earlier verdict)')
REVIEW = R

# ---- figurative-use check (decision of 13 Oct 2026) ----
# Every code that drives a GDELT shift at the tested levels in the main set (10_gdelt_drivers.py) gets a verdict:
# code -> ('figurative' | 'literal', reason). 'figurative' = its rises come from figurative use of the word, so 02 drops it.
FIGURATIVE = {}
_U = 'URL sample (gdelt/figurative_url_samples.csv): '
FIGURATIVE.update({
 # --- checked with URL samples of the highest-volume weeks and of every shift week the code drove ---
 'TAX_DISEASE_AMNESIA': ('figurative', _U + 'the rises are political figures of speech: "Dems accuse GOP official of amnesia on Trump vulgarity" (Jan 2018), "the people\'s republic of amnesia" (Jun 2019), "don\'t forget the GOP tried to overturn the election" (May 2021); no medical amnesia'),
 'TAX_RELIGION_WITCHCRAFT': ('literal', _U + 'no "witch hunt" in 6 sampled days; shift weeks are witchcraft and exorcism news and witch TV series (Charmed, American Horror Story); the May 2018 peak is mostly one site (unitaangola.org, 32 of 40 URLs), a feed artefact'),
 'TAX_RELIGION_OCCULT': ('literal', _U + 'shift weeks are Halloween, Satanic Temple, voodoo and occult sects; part of the June 2019 peak is the Italian "occultare" (to hide) in translated news and one site (bjhmoh.cn); mixed but not mostly figurative'),
 'TAX_RELIGION_ATHEISM': ('literal', _U + 'religion news (pope and abuse scandals Sep 2018, China and Christianity Oct 2020); Dec 2019 shift week partly one aggregator site (scotcampus.com, 15 of 37)'),
 'TAX_DISEASE_GAMBLING': ('literal', _U + 'casinos and betting (Las Vegas shooting Oct 2017, Montana casino shooting Dec 2019, illegal betting); "a gamble" not seen'),
 'TAX_DISEASE_BLINDNESS': ('literal', _U + 'eye disease and World Sight Day (October), gene therapy for blindness; "blind eye" not seen'),
 'TAX_DISEASE_DEAFNESS': ('literal', _U + 'hearing loss news, but most sampled records on the shift days come from one site (bjhmoh.cn, 13 to 34 of 40): a feed artefact, not figurative'),
 'TAX_DISEASE_CANCER': ('literal', _U + 'cancer news (Nobel prize for immunotherapy, Chadwick Boseman, World Cancer Day); some pages from bjhmoh.cn (4 to 10 of 40)'),
 'TAX_DISEASE_GENETIC_DISEASES': ('literal', _U + 'gene editing of embryos (Aug 2017), gene therapy and biotech news'),
 'TAX_DISEASE_INSECT_BITE': ('literal', _U + 'insect bites, flesh-eating bacteria, anthrax; very small code (6 to 90 records a day)'),
 'TAX_DISEASE_PSYCHOLOGICAL_TRAUMA': ('literal', _U + 'trauma of migrant children separated at the border (Jun 2018), child abduction; very small code'),
 'SOC_SUICIDE': ('literal', _U + 'suicide news (Epstein Aug 2019, Sushant Singh Rajput Jun 2020); the May 2017 peak is the Manchester suicide bombing (a different sense, not figurative)'),
 'BULLYING': ('literal', _U + 'bullying claims (Australian politics Sep 2018, Meghan and palace staff Mar 2021)'),
 'KIDNAP': ('literal', _U + 'abductions (Dapchi schoolgirls Mar 2018, hostage cases)'),
 'NATURAL_DISASTER_BLIZZARD': ('literal', _U + 'the highest-volume weeks are real blizzards (bomb cyclone Jan 2018, Storm Emma Feb 2018); the two off-season shift weeks (Oct 2018, Sep 2020) are tiny (85 to 162 records) and come from translated Italian "tormenta" (torments): noted, but not the code\'s rises'),
 'NATURAL_DISASTER_ICY': ('literal', _U + 'icy roads and winter storms; "icy relations" not seen'),
 'NATURAL_DISASTER_EARTHQUAKE': ('literal', _U + 'earthquakes (Mexico Sep 2017, Lombok Aug 2018)'),
 'CRISISLEX_O01_WEATHER': ('literal', _U + 'storms, heat waves and floods'),
 'WB_1447_GERIATRICS': ('literal', _U + 'not figurative, but 34 to 40 of 40 sampled URLs on four of its five shift weeks are template pages of one site (bjhmoh.cn): a feed artefact; Dec 2020 week is COVID-19 in care homes'),
 'WB_1532_TEACHER_TRAINING': ('literal', _U + 'not figurative, but 23 to 32 of 40 sampled URLs on its 2017 to 2019 shift weeks come from one site (bjhmoh.cn): a feed artefact; 2020 weeks are education news'),
})
_WB = 'World Bank topic code assigned from many terms, not one word, so figurative use does not apply'
for c, why in {
 'WB_2509_GENOCIDE': 'genocide cases (Rohingya, Armenian genocide anniversary, Uighurs)', 'WB_739_POLITICAL_VIOLENCE_AND_CIVIL_WAR': 'conflict news',
 'WB_2286_GEOLOGICAL_SURVEY': 'Kilauea eruption (May 2018) and earthquakes', 'WB_1430_MENTAL_HEALTH': 'mental health news, World Mental Health Day (October)',
 'WB_2198_CHEMICAL_ENGINEERING': 'chemical industry news', 'WB_364_CONSUMER_PROTECTION': 'consumer protection news', 'WB_605_WILDLIFE_RESOURCES': 'wildlife news',
 'WB_2756_LABOR_PRODUCTIVITY': 'economic news', 'WB_655_INFORMATION_MANAGEMENT': 'information systems news', 'WB_933_ETHNIC_RELIGIOUS_AND_OTHER_MINORITIES': 'minorities news (Kurds Oct 2019, George Floyd 2020)',
 'WB_2444_EARLY_MARRIAGE': 'child marriage news', 'WB_962_INTERNATIONAL_LAW': 'treaties and international law', 'WB_2465_REVOLUTIONARY_VIOLENCE': 'unrest and militias (Iran Jan 2020)',
 'WB_639_REPRODUCTIVE_MATERNAL_AND_CHILD_HEALTH': 'maternal and child health, vaccination 2021', 'WB_663_GEOGRAPHIC_INFORMATION_SYSTEMS': 'mapping and GIS news',
 'WB_758_ORPHANS': 'orphans news', 'WB_2082_LAW_ENFORCEMENT': 'policing (George Floyd May 2020)', 'WB_1777_FORESTS': 'forests (Amazon fires Aug 2019)',
 'WB_1438_ALCOHOL_AND_SUBSTANCE_ABUSE': 'addiction news', 'WB_1461_HEALTHY_LIFESTYLES': 'healthy living news', 'WB_1464_HEALTH_OF_THE_DISABLED': 'disability (International Day of Persons with Disabilities, Dec)',
 'WB_180_FOOD_SAFETY': 'food safety news', 'WB_1927_STRATEGIC_POLICY_PLANNING': 'policy planning news', 'WB_567_CLIMATE_CHANGE': 'climate news (climate strikes Sep 2019)',
 'WB_2167_PANDEMICS': 'COVID-19', 'WB_2390_TELEVISION_BROADCASTING': 'broadcasting news', 'WB_939_NEGOTIATION': 'negotiations news', 'WB_695_POVERTY': 'poverty news',
 'WB_698_TRADE': 'trade disputes (US-China 2018-2019)', 'WB_670_ICT_SECURITY': 'cyber security (SolarWinds hack Dec 2020)', 'WB_730_MANAGEMENT_INFORMATION_SYSTEMS': 'information systems news',
 'WB_635_PUBLIC_HEALTH': 'COVID-19', 'WB_341_INVESTMENT_FUNDS': 'investment funds news', 'WB_533_ENERGY_EFFICIENCY': 'energy efficiency news', 'WB_769_INVESTMENT_POLICY': 'investment policy news',
 'WB_669_SOFTWARE_INFRASTRUCTURE': 'software news', 'WB_661_BIG_DATA': 'big data news', 'WB_2466_STATE_TERRORISM': 'state terrorism accusations', 'WB_1234_BANKING_INSTITUTIONS': 'banks in the March 2020 crash',
 'WB_134_SOCIAL_DEVELOPMENT': 'social development news', 'WB_2203_HUMAN_RIGHTS': 'human rights news', 'WB_2416_INTERNET_OF_THINGS': 'internet of things news',
 'WB_2442_SEXUAL_TRAFICKING': 'sex trafficking (Epstein Jul-Aug 2019)', 'WB_1526_TEACHER_CAREERS': 'teachers news', 'WB_2508_ETHNIC_CLEANSING': 'Rohingya crisis (Sep 2017)',
 'WB_345_SOVEREIGN_WEALTH_FUNDS': 'sovereign funds news', 'WB_590_ECOSYSTEMS': 'ecosystems (Amazon fires Aug 2019)', 'WB_1986_MOUNTAINS': 'mountains (Winter Olympics Feb 2018)',
}.items():
    FIGURATIVE[c] = ('literal', f'{_WB}; top weeks: {why}')
for c, why in {
 'REL_ANTISEMITISM': 'antisemitic attacks (Pittsburgh synagogue Oct 2018, Feb 2019, May 2021)', 'ETH_INDIGINOUS': 'indigenous peoples news', 'TAX_DISEASE_AUTISM': 'World Autism Awareness Day (2 April) and autism news',
 'AVIATION_INCIDENT': 'air crashes and incidents (Ukrainian flight 752 Jan 2020, Ethiopian 302 Mar 2019)', 'ASSASSINATION': 'assassinations (Soleimani Jan 2020)',
 'DISCRIMINATION_RACE_RACIST': 'racism news (Trump tweets Jul 2019, George Floyd 2020)', 'DISCRIMINATION_RACE_RACISM': 'racism news (George Floyd Jun 2020)',
 'TAX_RELIGION_ISLAM': 'Islam news (France Oct 2020)', 'TAX_RELIGION_CATHOLICISM': 'Catholic church news', 'TAX_RELIGION_CHRISTIANITY': 'Christianity news (Christmas, Easter, Sri Lanka Apr 2019)',
 'POVERTY': 'poverty news', 'TECH_VIRTUALREALITY': 'virtual reality news', 'GEN_HOLIDAY': 'holidays', 'MARITIME_INCIDENT': 'ship incidents', 'CYBER_ATTACK': 'cyber attacks (WannaCry May 2017)',
 'TECH_BIGDATA': 'big data news', 'EPU_CATS_SOVEREIGN_DEBT_CURRENCY_CRISES': 'currency crises (Turkey Aug 2018, Argentina Aug 2019)', 'IMMIGRATION': 'immigration (family separations Jun 2018)',
 'NATURAL_DISASTER_HURRICANE': 'hurricanes', 'CHARASMATIC_LEADERSHIP': 'charisma of leaders (the word is used literally)', 'ECON_FOREIGNINVEST': 'foreign investment news',
 'DISCRIMINATION_LGBT_ANTIGAY': 'anti-gay laws and attacks', 'DISABILITY': 'disability news', 'ENV_CLIMATECHANGE': 'climate news', 'CRISISLEX_T05_MONEY': 'money in crisis news',
 'UNGP_GENDER_EQUALITY': "gender equality (Women's Day, March)", 'HARASSMENT': 'sexual harassment (#MeToo 2017)', 'UNGP_CRIME_VIOLENCE': 'crime and violence news',
 'TAX_DISEASE_HIV': 'HIV news (World AIDS Day, Dec)', 'NATURAL_DISASTER_WINTER_STORM': 'winter storms (Texas Feb 2021)', 'RAPE': 'rape cases (Kavanaugh hearings Sep 2018)',
 'SOC_EARLYMARRIAGE': 'child marriage news', 'SOC_SLAVERY': 'slavery (statue debates Jun 2020, Juneteenth)', 'TAX_DISEASE_TRAUMATIC_STRESS_DISORDER': 'PTSD news',
 'TAX_DISEASE_FLU': 'flu seasons and COVID-19', 'MARITIME': 'shipping and sea news', 'LGBT': 'LGBT news', 'JUSTICE': 'justice news (George Floyd 2020)',
 'HUMAN_TRAFFICKING': 'human trafficking (Epstein 2019)', 'DISCRIMINATION': 'discrimination (George Floyd Jun 2020)', 'HEALTH_VACCINATION': 'COVID-19 vaccination',
 'NEGOTIATIONS': 'negotiations', 'PROTEST': 'protests (George Floyd)', 'NATURAL_DISASTER_VOLCANO': 'volcanoes (Kilauea May 2018)', 'SOC_FASCISM': 'fascism in politics (Charlottesville Aug 2017)',
 'TAX_DISEASE_EBOLA': 'Ebola outbreaks (DRC 2018-2019)', 'MANMADE_DISASTER_PLANE_CRASH': 'plane crashes', 'TAX_DISEASE_PNEUMONIA': 'COVID-19 pneumonia (Jan 2020)',
 'LITERACY': 'literacy news', 'DISCRIMINATION_RELIGION_ANTIISLAM': 'anti-Islam news', 'FREESPEECH': 'free speech debates', 'ELECTION': 'elections (US Nov 2020)',
 'DISCRIMINATION_RELIGION_ISLAMOPHOBIA': 'Islamophobia (Christchurch Mar 2019, France Oct 2020)', 'CRISISLEX_C01_CHILDREN_AND_EDUCATION': 'school closures (Mar 2020)',
}.items():
    FIGURATIVE.setdefault(c, ('literal', f'no URL sample; the word has no common figurative use here and its top weeks match news on the topic: {why}'))
FIGURATIVE['WB_615_GENDER'] = ('literal', f"{_WB}; top weeks: gender equality news (Women's Day, March)")
# mapping verdicts for driver codes that were only mapped automatically (checked during the figurative check)
_s('WB_939_NEGOTIATION WB_1234_BANKING_INSTITUTIONS WB_533_ENERGY_EFFICIENCY WB_769_INVESTMENT_POLICY WB_2286_GEOLOGICAL_SURVEY WB_2466_STATE_TERRORISM',
   'correct', None, 'checked as a shift driver')
_s('WB_730_MANAGEMENT_INFORMATION_SYSTEMS', 'borderline', None, 'information systems; kept on management')
REVIEW = R
