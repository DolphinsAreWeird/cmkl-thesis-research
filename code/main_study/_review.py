# Hand decisions after reading the rule output of 05 (13 Oct 2026). Keys are canonical phrases (lowercase,
# '-' as space, synonyms applied). Value: 'facet:value + facet:value'. These win over every rule.
# Subtypes of 'other': personal, author_series, franchise, award_list, language, mood, trope, publisher, person,
# adaptation (book-to-film shelves), author_identity (about the writer, not the book), ambiguous.
_RAW = '''
picture=form:picture book+audience:children; anime=form:comics and graphic novels; urban=genre:urban fiction; stories=form:short stories;
vamps=theme:vampires; lendable=other:personal; short=other:personal; comix=form:comics and graphic novels; m f=genre:romance; 1=other:personal;
hist=genre:historical fiction; psych=theme:psychology; foodie=theme:food; theory=genre:academic; made me cry=other:mood; collection=form:anthology;
professional=theme:careers and work; uf=genre:urban fantasy; lds=theme:latter day saints; cómics=form:comics and graphic novels; creativity=theme:creativity;
musicians=theme:music; cultural=theme:culture; cookery=theme:cooking; school books=other:personal; unlimited=other:personal; downloaded=other:personal;
professional development=theme:careers and work; nobel=other:award_list; general=other:personal; athletes=theme:sports; narrativa=other:language;
youth=audience:young adult; mangá=form:comics and graphic novels; lds authors=theme:latter day saints; graphicnovels=form:comics and graphic novels;
rockers=other:trope; lds books=theme:latter day saints; fighter=other:trope; bios=genre:biography; animal=theme:animals; summer=other:mood;
sub=genre:erotica; female author=other:author_identity; other=other:personal; روايات=other:language; lds author=theme:latter day saints;
fighters=other:trope; net galley=other:personal; youngadult=audience:young adult; culinary=theme:cooking; rory gilmore challenge=other:award_list;
development=other:ambiguous; for review=other:personal; steam punk=genre:steampunk; assassins=other:trope; rhyming=form:poetry+audience:children;
bd=form:comics and graphic novels; single parent=theme:single parents; taboo=other:trope; fantascienza=genre:science fiction+other:language;
gfy=other:trope; middle grades=audience:middle grade; coming out=theme:coming out; rory gilmore=other:award_list; jane austen=other:author_series;
arts=theme:art; m f m=other:trope; autobiographies=genre:memoir; kidnapped=theme:kidnapping; can lit=place:canada; assassin=other:trope;
counseling=theme:therapy; financial=theme:finance; spirit=theme:spirituality; tattoos=other:trope; krimi=genre:crime+other:language;
arthurian=theme:arthurian legend; mfm=other:trope; cómic=form:comics and graphic novels; scripts=form:drama; austen=other:author_series;
biographical=genre:biography; metaphysics=theme:metaphysics; motorcycle=other:trope; shōjo=form:comics and graphic novels;
female authors=other:author_identity; gilmore girls=other:award_list; recipes=theme:cooking+form:cookbook; 1st in series=other:personal;
sonlight=other:award_list; illustrated=other:personal; banned books=other:award_list; movie=other:adaptation; serial=other:personal;
listened to=other:personal; life=other:ambiguous; shakespeare=other:person; omnibus=other:personal; verse=form:poetry; apologetics=theme:christianity;
true story=genre:narrative nonfiction; christianfiction=genre:christian fiction+theme:christianity; technical=theme:technology;
shorts=form:short stories; fantasia=genre:fantasy+other:language; new 52=other:franchise; 33 keepers=other:personal; théâtre=form:drama;
cartoons=form:comics and graphic novels; mmf=other:trope; craft=theme:crafts and hobbies; bbw=other:trope; classical=genre:classics;
ministry=theme:christianity; mma=other:trope; critical theory=theme:critical theory; hoopla=other:personal; nautical=theme:seafaring;
filosofia=theme:philosophy; shortstories=form:short stories; imagination=theme:imagination; computer=theme:computers; d d=other:franchise;
and=other:personal; arthurian legend=theme:arthurian legend; motivational=genre:self-help+theme:motivation; to be released=other:personal;
hr=theme:management; econ=theme:economics; psychological=theme:psychology; not yet released=other:personal; botm=other:personal;
rocker=other:trope; scanned=other:personal; guardian 1000=other:award_list; mind=theme:psychology; road trip=theme:road trips;
famous=theme:celebrity; collections=form:anthology; elves=theme:elves; slice of life=genre:slice of life; it=theme:technology;
strategy=theme:strategy; cinema=theme:film; around the world=theme:travel; wattpad=other:personal; cultural studies=theme:culture;
rock=theme:rock music; king arthur=theme:arthurian legend; musician=theme:music; coming soon=other:personal; personal mba=other:award_list;
battle of the books=other:award_list; jayne ann krentz=other:author_series; psychic=theme:psychic powers; discipleship=theme:christianity;
trilogy=other:personal; humble bundle=other:personal; lovecraftian=genre:cosmic horror; pagan=theme:paganism; self=theme:personal development;
startup=theme:startups; modernism=genre:modernism; vegan=theme:vegetarian and vegan; yaoi=genre:boys love+theme:gay men; mf=genre:romance;
animal books=theme:animals; bodice ripper=genre:historical romance; computing=theme:computers; teatro=form:drama; true stories=genre:narrative nonfiction;
biblical studies=theme:bible; uni=theme:college life; innovation=theme:innovation; f f=genre:romance+theme:lesbian; social=theme:society;
kindergarten=audience:children; winter=theme:seasons; non=form:nonfiction; social issues=theme:social issues; teacher student=other:trope;
lit=form:literature; naval=theme:naval warfare; novela=form:novel+other:language; healing=theme:healing; austen inspired=genre:retellings;
cornwell=other:author_series; metaphysical=theme:metaphysics; investment=theme:investing; austenesque=genre:retellings;
fumetti=form:comics and graphic novels; vegetarian=theme:vegetarian and vegan; educational=theme:education; coaching=theme:coaching;
poesia=form:poetry; sequels=other:personal; lifestyle=theme:lifestyle; kellerman=other:author_series; filosofía=theme:philosophy;
poc=theme:diversity; myth=theme:mythology; bedtime=audience:children; erótica=genre:erotica; monsters=theme:monsters; cook=theme:cooking;
finances=theme:personal finance; athlete=other:trope; beat=genre:beat literature; gospel=theme:christianity; highland=other:trope;
litrpg=genre:litrpg; bl=genre:boys love+theme:gay men; book of the month=other:personal; ciencia ficción=genre:science fiction+other:language;
gilmore=other:award_list; arabic=other:language; boys=other:ambiguous; gfy ofy=other:trope; wordless=form:picture book+audience:children;
dharma=theme:buddhism; brazen=other:publisher; kitchen=theme:cooking; magick=theme:occult; biblical=theme:bible; tom clancy=other:author_series;
1 owning=other:personal; trek=other:franchise; lit crit=genre:literary criticism; buddhist=theme:buddhism; entrepreneur=theme:entrepreneurship;
cs=theme:computer science; bodice rippers=genre:historical romance; pmba=other:award_list; ux=theme:user experience design; forgotten=other:ambiguous;
ff=other:ambiguous; clancy=other:author_series; drawing=theme:drawing; firefighter=other:trope; 311=other:personal; a=other:personal;
books on books=theme:books and reading; book of the month club=other:personal; historicalfiction=genre:historical fiction; colors=audience:children;
fantasía=genre:fantasy+other:language; rory gilmore book challenge=other:award_list; tattoo=other:trope; terjemahan=other:language;
esoteric=theme:occult; witchy=theme:witches; komik=form:comics and graphic novels; beat generation=genre:beat literature; d s=genre:erotica;
cook book=form:cookbook; shelved=other:personal; rock n roll=theme:rock music; italiani=other:language; tie in=other:adaptation;
whedonverse=other:franchise; lol=other:mood; trading=theme:investing; private=other:author_series; disaster=theme:disasters; realms=other:franchise;
pride and prejudice=genre:retellings; veganism=theme:vegetarian and vegan; beats=genre:beat literature; wh40k=other:franchise; grimdark=genre:dark fantasy;
relationship=theme:relationships; italia=place:italy; racconti=form:short stories+other:language; mba=theme:business; completed=other:personal;
clàssics=genre:classics; holmes=other:franchise; teacher books=theme:teaching; coffee table=other:personal; 7th grade=other:personal;
coffee table books=other:personal; interracial=theme:interracial relationships; dirty talk=other:mood; dirty talker=other:mood;
completed series=other:personal; microhistory=genre:narrative nonfiction+theme:history; 40k=other:franchise; fey=theme:fairies;
video game=theme:video games; sword and laser=other:award_list; chick=genre:chick lit; immortals=theme:immortality; new=other:personal;
artbooks=theme:art; rpg=theme:role playing games; urban books=genre:urban fiction; could not finish=other:personal; séries=other:personal;
startrek=other:franchise; còmics=form:comics and graphic novels; nobel laureates=other:award_list; age of sail=theme:seafaring;
grad school=other:personal; austen related=genre:retellings; laura ingalls wilder=other:author_series; lesfic=genre:romance+theme:lesbian;
farm=theme:farming; mormon=theme:latter day saints; w40k=other:franchise; indonesian=other:language; recipe books=form:cookbook+theme:cooking;
biblioteca=other:personal; wattpad books=other:personal; favs=other:personal; sword sorcery=genre:epic fantasy; shōnen=form:comics and graphic novels;
kindleunlimited=other:personal; forensics=theme:forensic science; missions=theme:missionaries; never finished=other:personal; urban lit=genre:urban fiction;
creative=theme:creativity; ibook=other:personal; beach=other:mood; wellness=theme:health; mma fighter=other:trope; wlw=theme:lesbian;
nostalgia=other:mood; time 100=other:award_list; authors of color=theme:diversity; misc=other:personal; biz=theme:business;
40 book challenge=other:personal; napoleonic=theme:napoleonic wars; lewis=other:author_series; celtic=theme:celtic culture; splatterpunk=genre:horror;
skepticism=theme:skepticism; poesía=form:poetry; dnd=other:franchise; cartoon=form:comics and graphic novels; mmm=other:trope; 2nd grade=other:personal;
rh=other:trope; international=other:ambiguous; punk=theme:punk; style=theme:fashion; foodie books=theme:food; professional books=theme:careers and work;
arte=theme:art; cinderella=genre:retellings; not out yet=other:personal; listened=other:personal; wanderlust=theme:travel; philosophie=theme:philosophy;
boxed set=other:personal; palmer=other:author_series; counting=audience:children; native=theme:native americans; ultimate=other:franchise;
little golden books=other:publisher; lawyer=theme:law; alice=other:franchise; bandes dessinées=form:comics and graphic novels; clancy tom=other:author_series;
gilmore challenge=other:award_list; ciencia ficcion=genre:science fiction+other:language; agile=theme:software; coding=theme:programming;
kennedy=other:person; photo=theme:photography; crafty=theme:crafts and hobbies; jane austen related=genre:retellings; mormonism=theme:latter day saints;
security=theme:cybersecurity; plantagenets=period:plantagenet era; historia=theme:history; growth=theme:personal development; truecrime=genre:true crime;
reincarnation=theme:reincarnation; tournament of books=other:award_list; unicorns=theme:unicorns; social studies=theme:society; artists=theme:artists;
book series=other:personal; parenthood=theme:parenting; southwest=place:american southwest; web=theme:internet; garden=theme:gardening;
conservative=theme:conservatism; true=other:ambiguous; lit rpg=genre:litrpg; lord of the rings=other:franchise; musica=theme:music;
watched=other:personal; ir=theme:international relations; classical studies=theme:classical studies; social commentary=theme:society;
march=other:personal; wordless books=form:picture book+audience:children; rhyme=form:poetry+audience:children; craft books=theme:crafts and hobbies;
aesthetics=theme:aesthetics; unsorted=other:personal; russians=place:russia; lost interest=other:personal; arthuriana=theme:arthurian legend;
opera=theme:opera; the 39 clues=other:franchise; cookery books=form:cookbook+theme:cooking; 9 11=theme:september 11 attacks;
non con=other:trope; books for sale=other:personal; 39 clues=other:franchise; golden books=other:publisher; crafting=theme:crafts and hobbies;
conservatism=theme:conservatism; families=theme:family; animal rights=theme:animal rights; appendix n=other:award_list; فلسفة=theme:philosophy;
arabic books=other:language; thieves=theme:heist; latin=other:language; policier=genre:crime+other:language; maritime=theme:seafaring;
world=other:ambiguous; simplicity=theme:minimalism; música=theme:music; academia=theme:college life; georgia=place:georgia; seminary=theme:theology;
paper=other:personal; surrealism=genre:surrealism; thor=other:franchise; ece 3601=other:personal; romanticism=genre:romanticism; caudill=other:award_list;
letteratura italiana=place:italy+other:language; motorcycle clubs=other:trope; pedagogy=theme:teaching; ks1=audience:children; superpowers=theme:superheroes;
historic=genre:historical fiction; midwifery=theme:childbirth; personal=other:personal; dev=theme:software; logos=other:personal;
little golden book=other:publisher; psicologia=theme:psychology; arthur=theme:arthurian legend; series books=other:personal; titanic=theme:titanic;
social theory=theme:sociology; youtubers=theme:internet celebrities; laugh out loud=other:mood; best=other:personal; the beats=genre:beat literature;
thinking=theme:critical thinking; school stories=theme:school life; jaff=genre:retellings; interactive=form:interactive fiction; game=theme:games;
illustration=theme:illustration; inklings=other:author_series; urban studies=theme:cities; btvs=other:franchise; brown=other:author_series;
beatles=other:person; blizzard=other:franchise; neurology=theme:neuroscience; rpgs=theme:role playing games; owls=theme:birds; kennedys=other:person;
folktales=genre:folklore and fables; green=theme:sustainability; rpg books=theme:role playing games; roleplaying=theme:role playing games;
new directions=other:publisher; youtube=theme:internet celebrities; novelizations=other:adaptation; girly=other:mood; rock and roll=theme:rock music;
ballet=theme:dance; animation=theme:film; brainpickings=other:award_list; pigs=theme:farm animals; slave=theme:slavery; wildstorm=other:franchise;
2=other:personal; hq=other:personal; book to movie=other:adaptation; minimalism=theme:minimalism; burroughs=other:author_series;
39 clues series=other:franchise; libertarian=theme:libertarianism; tenho=other:personal; روايات عربية=other:language; shamanism=theme:shamanism;
pregnant=theme:pregnancy; green lantern=other:franchise; 3rd grade=other:personal; red dress ink=other:publisher; geology=theme:geology;
book collection=other:personal; role playing=theme:role playing games; mice=theme:small animals; private series=other:author_series;
organization=theme:organizing; hellblazer=other:franchise; gelesen=other:personal; filmmaking=theme:film; all books=other:personal;
male lead=other:trope; 8th grade=other:personal; appalachian=place:appalachia; criminology=theme:criminology; intelligence=other:ambiguous;
united=other:ambiguous; mangás=form:comics and graphic novels; lost generation=genre:modernism; blinkist=other:personal; bowie=other:person;
racing=theme:motorsport; time=theme:time; italiana=other:language; grit lit=genre:literary fiction+place:american south; teacher=theme:teaching;
bwwm=theme:interracial relationships+genre:romance; fotografia=theme:photography; poets=theme:writers; astrophysics=theme:astrophysics;
gialli=genre:crime+other:language; eating disorder=theme:eating disorders; klassiker=genre:classics+other:language; avatar=other:franchise;
plantagenet=period:plantagenet era; webcomic=form:comics and graphic novels; alphabet=audience:children; birth=theme:childbirth;
youtuber books=theme:internet celebrities; pfaf=other:personal; owlcrate=other:personal; novelization=other:adaptation; شعر=form:poetry;
personalmba=other:award_list; stepbrother=other:trope; others in series=other:personal; contemp=genre:contemporary fiction;
grandparents=theme:grandparents; epistemology=theme:epistemology; favoritos=other:personal; languages=theme:language learning; urbanism=theme:cities;
michaels=other:author_series; norse=theme:norse mythology; atlantis=theme:atlantis; the beatles=other:person; presidential=theme:presidents;
abduction=theme:kidnapping; lemonade syllabus=other:award_list; wow=other:franchise; filipino=place:philippines; lotr=other:franchise;
not released yet=other:personal; evangelism=theme:christianity; international development=theme:international development; lincoln=other:person;
alice in wonderland=other:franchise; 4th grade=other:personal; pal=other:personal; riptide=other:publisher; théatre=form:drama;
states=other:ambiguous; people=other:ambiguous; wolf=theme:wolves; investments=theme:investing; saudi arabia=place:saudi arabia;
wiccan=theme:wicca; wattpad stories=other:personal; سيرة ذاتية=genre:memoir; financial crisis=theme:financial crisis; henry viii=other:person;
urban planning=theme:cities; philosophical=theme:philosophy; personality=theme:personality; climbing=theme:mountaineering;
the personal mba=other:award_list; stem=theme:science; storytelling=theme:storytelling; تاريخ=theme:history; deckare=genre:crime+other:language;
strips=form:comics and graphic novels; storybundle=other:personal; deadpool=other:franchise; ecclesiology=theme:theology;
cuentos=form:short stories+other:language; acting=theme:acting; the horus heresy=other:franchise; young=other:ambiguous; movie tie in=other:adaptation;
superheros=theme:superheroes; whoniverse=other:franchise; once upon a time=other:franchise; goblins=theme:goblins; literacy=theme:literacy;
storia=theme:history; web development=theme:programming; screenplays=form:drama; novela historica=genre:historical fiction+other:language;
ed=other:ambiguous; c=other:personal; rabbits=theme:small animals; iain banks=other:author_series; l=other:personal;
older woman younger man=other:trope; lineup 2=other:personal; 2 series=other:personal; gargoyles=theme:monsters; considering=other:personal;
wtf=other:mood; trivia=theme:trivia; decision making=theme:decision making; kinky=genre:erotica; training=other:ambiguous;
musicals=theme:musical theatre; boekenkast=other:personal; bookouture=other:publisher; religión=theme:religion; nantucket=place:nantucket;
ducks=theme:birds; advice=genre:self-help; prequel=other:personal; at home=other:personal; organizing=theme:organizing;
libertarianism=theme:libertarianism; indiespensable=other:award_list; data=theme:data science; hardy=other:author_series; virago=other:publisher;
rory=other:award_list; horus heresy=other:franchise; elizabeth i=other:person; allegory=genre:allegory; user experience=theme:user experience design;
kookboeken=form:cookbook+other:language; summer books=other:mood; islamic=theme:islam; simple living=theme:minimalism; saggi=form:essays+other:language;
kindness=theme:kindness; store=other:personal; poesie=form:poetry; abc=audience:children; abraham lincoln=other:person;
story collections=form:short stories; first time=other:trope; mpreg=other:trope; healthy living=theme:health; ensayo=form:essays+other:language;
actors=theme:acting; hood books=genre:urban fiction; phil=theme:philosophy; study=other:personal; reformed=theme:christianity; governess=other:trope;
stocks=theme:investing; comedians=theme:comedians; polygamy=theme:polygamy; robin hood=theme:robin hood; globalization=theme:globalization;
childbirth=theme:childbirth; new books=other:personal; celebrities=theme:celebrity; cheater=theme:infidelity; manners=theme:etiquette;
futurism=theme:future studies; biografie=genre:biography+other:language; engl 420=other:personal; cognition=theme:cognitive science;
311 books=other:personal; رمان=other:language; wall street=theme:investing; bundle=other:personal; january=other:personal;
west=place:american west; screenplay=form:drama; have it=other:personal; writers=theme:writers; cyber punk=genre:cyberpunk;
new jedi order=other:franchise; anne boleyn=other:person; keepers=other:personal; veg=theme:vegetarian and vegan; edrd 314=other:personal;
'''
_RAW2 = '''
roman=form:novel+other:language; english=other:ambiguous; stand alone=other:personal; standalone=other:personal; stand alones=other:personal;
standalones=other:personal; christian non fiction=genre:christian nonfiction+theme:christianity; christian nonfiction=genre:christian nonfiction+theme:christianity;
christian books=theme:christianity; christian life=theme:christianity; children s picture books=audience:children+form:picture book;
comics manga=form:comics and graphic novels; manga shoujo=form:comics and graphic novels; gay=theme:gay men; homesteading=theme:homesteading;
homemaking=theme:homemaking; homestead=theme:homesteading; homeless=theme:homelessness; diverse reads=theme:diversity; own voices=theme:diversity;
christmas reads=theme:christmas; dark reads=other:mood; dark read=other:mood; spiritual reading=theme:spirituality; professional reading=theme:careers and work;
professional reads=theme:careers and work; read aloud=audience:children; read alouds=audience:children; read to kids=audience:children;
printz=other:award_list; printz award=other:award_list; printz honor=other:award_list; rock star romance=other:trope;
super hero=theme:superheroes; super heroes=theme:superheroes; great books=other:award_list; romantic suspence=genre:romance+genre:suspense;
magical girl=form:comics and graphic novels; hurt comfort=other:trope; diversity=theme:diversity; diverse=theme:diversity;
women authors=other:author_identity; women writers=other:author_identity; female writers=other:author_identity; male authors=other:author_identity;
black authors=theme:black life; pop culture=theme:popular culture; law enforcement=theme:police; food cooking=theme:food and cooking;
murder mystery=genre:mystery+theme:murder; murder mysteries=genre:mystery+theme:murder; homeschool=theme:homeschooling;
picture books=audience:children+form:picture book; picture book=audience:children+form:picture book;
'''
OVERRIDE = {}
for _blk in (_RAW, _RAW2):
    for _item in _blk.replace('\n', ' ').split(';'):
        _item = _item.strip()
        if not _item or '=' not in _item:
            continue
        _k, _v = _item.split('=', 1)
        OVERRIDE[_k.strip()] = [tuple(x.strip().split(':', 1)) for x in _v.split('+')]

# Wikidata subjects and LibriVox genres (source-specific keys 'source|phrase' are allowed)
_RAW3 = '''
wikidata|sentimentalism=genre:sentimental fiction; wikidata|castellology=theme:castles; wikidata|special collections=other:ambiguous;
wikidata|african studies=theme:african studies+place:africa; wikidata|virtue=theme:virtue; wikidata|mores=theme:customs;
wikidata|mary mother of jesus=theme:virgin mary; wikidata|jesus=theme:jesus; wikidata|passion of jesus=theme:jesus; wikidata|resurrection of jesus=theme:jesus;
wikidata|muhammad=theme:islam; wikidata|hadith=theme:islamic theology; wikidata|aqidah=theme:islamic theology; wikidata|fiqh=theme:islamic theology;
wikidata|kalam=theme:islamic theology; wikidata|tafsir=theme:islamic theology; wikidata|hadith sciences=theme:islamic theology;
wikidata|principles of islamic jurisprudence=theme:islamic theology; wikidata|woman=theme:women; wikidata|botany=theme:botany;
wikidata|melancholia=theme:melancholy; wikidata|antisemitism=theme:antisemitism; wikidata|volleyball=theme:volleyball; wikidata|badminton=theme:badminton;
wikidata|figure skating=theme:figure skating; wikidata|motorsport=theme:motorsport; wikidata|scuba diving=theme:scuba diving;
wikidata|wheelchair basketball=theme:disability sports; wikidata|night=theme:night; wikidata|library science=theme:libraries; wikidata|crime=theme:crime;
wikidata|mineralogy=theme:geology; wikidata|dream=theme:dreams; wikidata|mourning=theme:grief; wikidata|peace=theme:peace; wikidata|liberty=theme:liberty;
wikidata|sinbad the sailor=other:person; wikidata|seven wise masters=genre:folklore and fables; wikidata|mediation=theme:conflict resolution;
wikidata|trojan war=theme:trojan war; wikidata|royal court=theme:monarchy; wikidata|armenian genocide=theme:armenian genocide;
wikidata|amazing stories=other:publisher; wikidata|tumor=theme:cancer; wikidata|local history=theme:local history; wikidata|libertinism=theme:libertinism;
wikidata|trade=theme:trade; wikidata|new testament=theme:bible; wikidata|order of the solar temple=theme:cults; wikidata|nazi plunder=theme:nazis;
wikidata|interpersonal relationship=theme:relationships; wikidata|social criticism=theme:society; wikidata|eroticism=theme:sexuality;
wikidata|economic history=theme:economic history; wikidata|german resistance to nazism=theme:resistance to nazism+place:germany;
wikidata|apartheid=theme:apartheid; wikidata|tudor period=period:tudor period; wikidata|paris commune=theme:paris commune;
wikidata|kingdom of france=place:france; wikidata|landscape archaeology=theme:archaeology; wikidata|ethnology=theme:anthropology;
wikidata|asperger syndrome=theme:autism; wikidata|expectation=theme:philosophy; wikidata|last judgment=theme:end times;
wikidata|foreign policy of the united states=theme:foreign policy+place:united states; wikidata|romantic date=theme:dating;
wikidata|association football=theme:soccer; wikidata|popular culture=theme:popular culture; wikidata|eastern front=theme:world war ii;
wikidata|godey s lady s book=other:publisher; wikidata|pre colonial history of the canary islands=theme:history+place:canary islands;
wikidata|khasi people=theme:indigenous+place:india; wikidata|central intelligence agency=theme:intelligence agencies; wikidata|psalms=theme:bible;
wikidata|abortion=theme:abortion; wikidata|assassination of john f kennedy=theme:jfk assassination; wikidata|spring=theme:seasons;
wikidata|esperanto=theme:language; wikidata|rock music=theme:rock music; wikidata|destiny=theme:fate and destiny; wikidata|eating=theme:food;
wikidata|ornithology=theme:birds; wikidata|prostitution=theme:prostitution; wikidata|cosplay=theme:cosplay; wikidata|passion=theme:emotions;
wikidata|barlaam and josaphat=genre:folklore and fables; wikidata|life=other:ambiguous; wikidata|alien abduction=theme:ufos;
librivox|american standard version=theme:bible; librivox|king james version=theme:bible; librivox|young s literal translation=theme:bible;
librivox|douay rheims version=theme:bible; librivox|world english bible=theme:bible; librivox|weymouth new testament=theme:bible;
librivox|other religions=theme:religion; librivox|christianity commentary=theme:christianity; librivox|classics greek and latin antiquity=genre:classics+period:ancient world;
librivox|life sciences=theme:biology; librivox|earth sciences=theme:earth sciences; librivox|school=theme:school life; librivox|free verse=form:poetry;
librivox|house and home=theme:family life; librivox|short non fiction=form:nonfiction; librivox|elegies and odes=form:poetry;
librivox|dramatic readings=form:drama; librivox|general=other:ambiguous; librivox|sagas=genre:sagas and epics; librivox|epics=genre:sagas and epics;
'''
for _item in _RAW3.replace('\n', ' ').split(';'):
    _item = _item.strip()
    if _item and '=' in _item:
        _k, _v = _item.split('=', 1)
        OVERRIDE[_k.strip()] = [tuple(x.strip().split(':', 1)) for x in _v.split('+')]

# partial matches where a leftover word changed the meaning, and theme-like shelves in the tail (< 20 works)
_RAW4 = '''
law of attraction=theme:law of attraction; ryan holiday=other:author_series; dark tower=other:franchise; the dark tower=other:franchise;
mad men=other:franchise; founding fathers=theme:american revolution; girl power=theme:feminism; beauty and the beast=genre:retellings;
cover love=other:personal; dying earth=genre:science fiction; arcane society=other:author_series; dungeons dragons=other:franchise;
çizgi roman=form:comics and graphic novels; alexander the great=other:person; social work=theme:social work; foreign policy=theme:foreign policy;
data science=theme:data science; natural history=theme:natural history; behavioral economics=theme:behavioral economics;
positive psychology=theme:positive psychology; social psychology=theme:social psychology; evolutionary biology=theme:evolution;
arranged marriage=theme:arranged marriage; interracial romance=theme:interracial relationships+genre:romance; interracial love=theme:interracial relationships;
ir romance=theme:interracial relationships+genre:romance; bw wm=theme:interracial relationships+genre:romance;
harlem renaissance=theme:harlem renaissance+theme:african american life; mothers and daughters=theme:mothers and daughters;
brothers best friend=other:trope; motorcycle men=other:trope; life after death=theme:afterlife; pre history=period:prehistory;
time management=theme:productivity; tartan noir=genre:crime+place:scotland; weird west=genre:western+genre:fantasy; new weird=genre:speculative fiction;
romantic comedies=genre:romantic comedy; simon romantic comedies=genre:romantic comedy; simon pulse romantic comedies=genre:romantic comedy;
presidential biographies=genre:biography+theme:presidents; presidential biography=genre:biography+theme:presidents; biblical fiction=genre:christian fiction+theme:bible;
american girls=other:franchise; english 420=other:personal; ultimate universe=other:franchise; sequential art=form:comics and graphic novels;
media tie in=other:adaptation; tv tie in=other:adaptation; gay for you=other:trope; vaginal fantasy=other:award_list; new york yankees=theme:baseball;
penguin great ideas=other:publisher; choose your own adventure=form:interactive fiction; quilt fiction=theme:quilting+form:fiction;
foodie fiction=theme:food+form:fiction; mythological fiction=theme:mythology+form:fiction; animal fiction=theme:animals+form:fiction;
biographical fiction=genre:historical fiction; naval fiction=theme:naval warfare+form:fiction; beat literature=genre:beat literature;
literary theory=genre:literary criticism; fan fiction=other:fanfiction; fanfiction=other:fanfiction; fanfic=other:fanfiction; fandom=other:fanfiction;
j fiction=audience:children+form:fiction; aa fiction=theme:african american life+form:fiction; home education=theme:homeschooling;
global health=theme:public health; lds fiction=theme:latter day saints+form:fiction; lds romance=theme:latter day saints+genre:romance;
lds non fiction=theme:latter day saints+form:nonfiction; lds nonfiction=theme:latter day saints+form:nonfiction; lds historical fiction=theme:latter day saints+genre:historical fiction;
mormon fiction=theme:latter day saints+form:fiction; amish mennonite=genre:christian fiction+theme:amish; cozy paranormal mystery=genre:cozy mystery+genre:paranormal;
human trafficking=theme:human trafficking; epidemiology=theme:epidemiology; apartheid=theme:apartheid; third reich=theme:nazis; gwot=theme:terrorism;
first ladies=theme:presidents; obama=other:person; jfk=other:person; hitler=other:person; churchill=other:person; anne frank=other:person;
romanovs=theme:monarchy+place:russia; puritans=theme:puritans; special needs=theme:disability; aspergers=theme:autism; asd=theme:autism;
blind=theme:blindness; bullies=theme:bullying; gambling=theme:gambling; psychedelics=theme:psychedelics; psychedelic=theme:psychedelics;
entheogens=theme:psychedelics; psychedelia=theme:psychedelics; permaculture=theme:sustainability; self sufficiency=theme:homesteading;
herbalism=theme:herbalism; herbs=theme:herbalism; paleo=theme:diet; coffee=theme:coffee; bread=theme:baking; desserts=theme:baking;
surfing=theme:surfing; swimming=theme:swimming; wrestling=theme:wrestling; pro wrestling=theme:wrestling; wwe=theme:wrestling;
walking=theme:walking; athletics=theme:sports; poker=theme:gambling; nba=theme:basketball; everest=theme:mountaineering; equine=theme:horses;
equestrian=theme:horses; labor=theme:labor; banking=theme:banking; markets=theme:investing; stock market=theme:investing;
consumerism=theme:consumerism; branding=theme:marketing; selling=theme:sales; consulting=theme:consulting; analytics=theme:data science;
museums=theme:museums; librarians=theme:libraries; quarter life crisis=theme:quarter life crisis; acceptance=theme:acceptance;
suffering=theme:suffering; wisdom=theme:wisdom; fear=theme:fear; enlightenment=theme:enlightenment; contemplation=theme:contemplation;
singularity=theme:singularity; cyborg=theme:cyborgs; vr=theme:virtual reality; haunted house=theme:haunted houses; dracula=theme:vampires;
cthulhu=genre:cosmic horror; sniper=theme:military; special forces=theme:special forces; marine corps=theme:military; submarines=theme:submarines;
firemen=other:trope; doula=theme:childbirth; wedding=theme:weddings; birthday=audience:children; first day of school=theme:school life+audience:children;
back to school=theme:school life; bugs=theme:insects; frogs=theme:frogs; penguins=theme:penguins; chickens=theme:farm animals; fish=theme:fish;
zoo=theme:zoos; zoology=theme:zoology; animal behavior=theme:animal behavior; primatology=theme:primates; paleontology=theme:dinosaurs;
anatomy=theme:anatomy; botany=theme:botany; snow=theme:winter; autumn=theme:seasons; fall=other:ambiguous; spring=theme:seasons; water=theme:water;
fire=other:ambiguous; energy=theme:energy; hip hop=theme:hip hop; jazz=theme:jazz; songs=theme:music; bob dylan=other:person; dylan=other:person;
screenwriting=theme:screenwriting; script=form:drama; journaling=theme:journaling; journals=theme:journaling; taoism=theme:taoism; buddha=theme:buddhism;
christology=theme:theology; soteriology=theme:theology; hermeneutics=theme:theology; preaching=theme:christianity; scripture=theme:bible;
doctrine=theme:theology; sanctification=theme:theology; biblical counseling=theme:christianity; pastoral=theme:christianity;
pastoral ministry=theme:christianity; new testament=theme:bible; mission=theme:missionaries; occultism=theme:occult; esoterica=theme:occult;
phenomenology=theme:phenomenology; complexity=theme:complexity science; systems=theme:systems thinking; chaos=theme:chaos theory;
worldview=theme:worldview; knowledge=theme:knowledge; information=theme:information; individuality=theme:individuality; aboriginal=theme:indigenous;
first north americans=theme:native americans; woc=theme:diversity; plus size=theme:body image; escort=other:trope; stripper=other:trope;
moving=other:ambiguous; royal=theme:monarchy; marie antoinette=other:person; cleopatra=other:person; eleanor of aquitaine=other:person;
richard iii=other:person; borgias=other:person; borgia=other:person; the kennedys=other:person; steve jobs=other:person; bill gates=other:person;
marilyn monroe=other:person; sylvia plath=other:person; plath=other:person; louisa may alcott=other:author_series; tim ferriss=other:author_series;
dave ramsey=other:author_series; tai lopez=other:award_list; hamilton=other:ambiguous; downton abbey=other:franchise; teotwawki=genre:post-apocalyptic;
etiquette=theme:etiquette; healthcare=theme:health care; med=theme:medicine; doctor=theme:medicine; anthro=theme:anthropology;
antropologia=theme:anthropology; ethnography=theme:anthropology; maps=theme:maps; numbers=audience:children; shapes=audience:children;
opposites=audience:children; color=audience:children; patterns=audience:children; alphabet books=audience:children; abc books=audience:children;
123 zzz=other:personal; tales=genre:folklore and fables; folktale=genre:folklore and fables; metafiction=genre:metafiction; bizarro=genre:bizarro fiction;
absurd=genre:absurdist fiction; game books=form:interactive fiction; ugly cry=other:mood; debut=other:personal; one night stand=other:trope;
multiple partners=other:trope; threesome=other:trope; m preg=other:trope; alphas=other:trope; weres=theme:werewolves; step brother=other:trope;
2nd chance=other:trope; female protagonist=other:trope; girl books=other:ambiguous; girls=other:ambiguous; kiddos=audience:children;
kinderboeken=audience:children+other:language; jeunesse=audience:children+other:language; childrensbooks=audience:children; ks2=audience:children;
teenlit=audience:young adult; ukya=audience:young adult+place:united kingdom; highschool=theme:school life; cult=theme:cults; avalon=theme:arthurian legend;
reapers=theme:death; podiobook=other:personal; podiobooks=other:personal; podcast=other:personal; image=other:publisher; indie=other:personal;
fic=form:fiction; sifi=genre:science fiction; bücherregal=other:personal; horus=other:franchise; herbert=other:author_series; bloomsbury=other:publisher;
archive=other:personal; hard copy=other:personal; filipiniana=place:philippines; well educated mind=other:award_list; artbook=theme:art;
europa editions=other:publisher; once upon a time series=other:franchise; comixology=other:personal; reinos olvidados=other:franchise;
all=other:personal; m=other:personal; forensic=theme:forensic science; cheaters=theme:infidelity; rory gilmore list=other:award_list;
saw the movie=other:adaptation; ed arg=other:personal; p p=genre:retellings; traditional lit=genre:folklore and fables; romanian=other:language;
quadrinhos=form:comics and graphic novels; instructional=form:how-to guide; graphics=theme:design; knit lit=theme:knitting+form:fiction;
stephen king recommendations=other:award_list; sharing=other:personal; peter pan=other:franchise; complete series=other:personal; traditional=other:ambiguous;
idw=other:publisher; three investigators=other:franchise; usability=theme:user experience design; critical thinking=theme:critical thinking;
neuro=theme:neuroscience; the three investigators=other:franchise; catalogued=other:personal; knit=theme:knitting; loa=theme:law of attraction;
bluford=other:franchise; bluford high=other:franchise; alternate=genre:alternate history; bluford series=other:franchise; saggistica=form:nonfiction+other:language;
funnies=form:comics and graphic novels; tay=other:personal; fiber arts=theme:crafts and hobbies; barthelme syllabus=other:award_list;
urania collezione=other:publisher; series complete=other:personal; daredevil=other:franchise; about books=theme:books and reading;
clásicos=genre:classics+other:language; s=other:personal; presidential bios=genre:biography+theme:presidents; body=theme:human body;
bibliophilia=theme:books and reading; rory gilmore book list=other:award_list; 9th grade=other:personal; of=other:personal; dfw=other:author_series;
bret=other:personal; filipino authors=place:philippines; eats=theme:food; jla=other:franchise; because 2=other:personal; 5th grade=other:personal;
economia=theme:economics; 3=other:personal; grace=other:ambiguous; vegetarian vegan=theme:vegetarian and vegan; book lust=other:award_list;
watched the movie=other:adaptation; detroit=place:detroit; candy apple=other:publisher; pride prejudice=genre:retellings; tos=other:franchise;
miscellaneous=other:personal; xmas=theme:christmas; artsy=other:mood; toread=other:personal; doctrine theology=theme:theology; romantica=genre:romance;
fyic=other:personal; lost=other:ambiguous; candy apple books=other:publisher; fantastique=genre:fantasy+other:language; keeper=other:personal;
books at home=other:personal; ted=other:award_list; improvement=theme:personal development; tng=other:franchise; change=theme:change;
online=theme:internet; outdoor=theme:outdoor recreation; atheist=theme:atheism; mind body spirit=theme:spirituality; philo=theme:philosophy;
grade 8 semester 2=other:personal; sequel=other:personal; pen faulkner=other:award_list; me=other:personal; it wikipedia=other:personal;
arch=theme:architecture; office=theme:careers and work; womanhood=theme:women; priority=other:personal; brazen collection=other:publisher;
1st grade=other:personal; anthro=theme:anthropology; south=place:american south; graphicnovel=form:comics and graphic novels; true crimes=genre:true crime;
história=theme:history; jennifer armentrout=other:author_series; bluestem=other:award_list; bluford high series=other:franchise;
novela histórica=genre:historical fiction+other:language; trashy=other:mood; behavior=theme:psychology; literatura=form:literature+other:language;
won=other:personal; toaster oven=other:personal; comp sci=theme:computer science; diverse books=theme:diversity; review=other:personal;
teacher resources=theme:teaching; community=theme:community; explorers=theme:exploration; jungian=theme:psychology; visual arts=theme:art;
cuisine=theme:cooking; trio detektif=other:franchise; elemental=other:author_series; sherlockiana=other:franchise; aa=theme:addiction and recovery;
cine=theme:film; musical=theme:musical theatre; sjc=other:personal; w=other:personal; roma=other:ambiguous; movie books=other:adaptation;
obob=other:award_list; edci 311=other:personal; farsi=other:language; die drei fragezeichen=other:franchise; ap lit=other:personal; داستان=other:language;
fiar=other:award_list; rebecca caudill=other:award_list; latinoamerica=place:latin america; trade=theme:trade; psychologie=theme:psychology;
commentary=theme:bible; child rearing=theme:parenting; 20s=other:ambiguous; elloras cave=other:publisher; banned=other:award_list;
others=other:personal; scripture study=theme:bible; pe project=other:personal; 0=other:personal; sfr=genre:science fiction+genre:romance;
mothering=theme:motherhood; clsc=other:personal; adyra=other:personal; rússia=place:russia; to acquire=other:personal; romantics=genre:romanticism;
spn=other:franchise; male author=other:author_identity; punya=other:personal; elementals=theme:magic; avalon books=other:publisher;
info bios=genre:biography; polar=theme:polar exploration; ux books=theme:user experience design; فلسفه=theme:philosophy; thief=theme:heist;
bookworm bitches=other:award_list; files eeee=other:personal; may=other:personal; to download=other:personal; photobooks=theme:photography;
yaoi bl=genre:boys love+theme:gay men; balkan=place:balkans; actor=theme:acting; skimm=other:award_list; 6th grade=other:personal; beat lit=genre:beat literature;
dalkey archive=other:publisher; no thanks=other:personal; first north americans=theme:native americans; films=theme:film; malory towers=other:franchise;
nederlandse literatuur=other:language; real life=genre:narrative nonfiction; علم نفس=theme:psychology; clasicos=genre:classics+other:language;
criminal=theme:crime; unavailable=other:personal; frankfurt school=theme:critical theory; سير ذاتية=genre:memoir; bengali=other:language;
1000 books before kindergarten=audience:children; knygynėlis=other:personal; arquitectura=theme:architecture; five in a row=other:award_list;
new series=other:personal; تطوير الذات=genre:self-help; october=other:personal; stephen king recommends=other:award_list; marie=other:personal;
john green recommends=other:award_list; celebs=theme:celebrity; influence=theme:persuasion; philadelphia=place:philadelphia; product=theme:management;
beach books=other:mood; bluebonnet=other:award_list; filipino books=place:philippines; booktopia=other:personal; nancy pearl s book lust=other:award_list;
role playing game=theme:role playing games; five stars=other:personal; non fictie=form:nonfiction+other:language; narrativa italiana=other:language;
jane austen inspired=genre:retellings; ed esp=other:personal; professional texts=theme:careers and work; kayla s book log=other:personal;
elly s choice=other:personal; reto rita la cantaora=other:personal; childrensbooks=audience:children; looking for=other:personal;
investment books=theme:investing; dw=other:franchise; youtubers books=theme:internet celebrities; sanctification=theme:theology;
drawing books=theme:drawing; inventory=other:personal; the secret=theme:law of attraction; sherlockian=other:franchise; potter=other:franchise;
literatura latinoamericana=place:latin america+other:language; letteratura francese=place:france+other:language; apple=other:ambiguous; 5=other:personal;
emergent=other:ambiguous; francia=place:france; batgirl=other:franchise; companion books=other:personal; k=other:personal; h=other:personal;
category=other:personal; best books ever=other:award_list; shelfie app books=other:personal; geschiedenis=theme:history; pinoy=place:philippines;
international affairs=theme:international relations; sarjakuvat=form:comics and graphic novels; harley quinn=other:franchise; natural=other:ambiguous;
hip hop music=theme:hip hop; haiku=form:poetry; girls books=other:ambiguous; weight=theme:weight loss; australiana=place:australia;
the fallen=other:ambiguous; latinoamérica=place:latin america; سياسة=theme:politics; anarchy=theme:anarchism; victoriana=period:victorian era;
beatniks=genre:beat literature; lost books=other:personal; fighting=theme:martial arts; eeee=other:personal; uppercase=other:personal; mmorpg=theme:video games;
svenskt=other:language; intrigue=other:mood; york=other:ambiguous; constantine=other:franchise; astérix=other:franchise; list of betterment=other:award_list;
romane=other:language; روانشناسی=theme:psychology; reddit top 200=other:award_list; artsy fartsy=other:mood; belletristik=form:fiction+other:language;
paused=other:personal; our books=other:personal; blog tour=other:personal; safe=other:ambiguous; covert one=other:franchise; private eye=genre:mystery;
b=other:personal; psychics=theme:psychic powers; videogames=theme:video games; biografia=genre:biography+other:language; flds=theme:latter day saints;
high=other:ambiguous; cape cod=place:cape cod; multiple partners=other:trope; nde=theme:near death experience; latinoamericanos=place:latin america;
snow white=genre:retellings; autobiographical=genre:memoir; readers=other:personal; pm=other:personal; o=other:personal; golden sower=other:award_list;
weres=theme:werewolves; guardians of the galaxy=other:franchise; adventures=genre:adventure; home school=theme:homeschooling; pacific=place:pacific;
problem solving=theme:problem solving; supers=theme:superheroes; fantastic four=other:franchise; torrey=other:personal; comicbooks=form:comics and graphic novels;
brasil=place:brazil; civil=other:ambiguous; interested=other:personal; authors=other:personal; performing=theme:performing arts; mindset=theme:mindset;
urania=other:publisher; story=form:short stories; hebrew=other:language; lds=theme:latter day saints; mormon=theme:latter day saints;
'''
for _item in _RAW4.replace('\n', ' ').split(';'):
    _item = _item.strip()
    if _item and '=' in _item:
        _k, _v = _item.split('=', 1)
        OVERRIDE[_k.strip()] = [tuple(x.strip().split(':', 1)) for x in _v.split('+')]

# the 22 phrases left for the tail rule on 13 Oct (the rule misreads Arabic script, so all are decided by hand)
_RAW5 = '''
prostitution=theme:prostitution; ciencia=theme:science+other:language; علوم=theme:science+other:language; مكتبتي=other:personal;
travelogues=genre:travel writing+theme:travel; wolverine=other:franchise; أدب=form:literature+other:language; رواية=form:novel+other:language;
أدب عربي=form:literature+other:language; to listen=other:personal; study author series=other:personal; planning=theme:planning;
compsci=theme:computer science; february=other:personal; تنمية بشرية=genre:self-help+other:language; pd=other:ambiguous;
swords and sorcery=genre:epic fantasy; northwest=place:pacific northwest; runaways=theme:runaways; memior=genre:memoir; في مكتبتي=other:personal;
humblebundle=other:personal;
'''
for _item in _RAW5.replace('\n', ' ').split(';'):
    _item = _item.strip()
    if _item and '=' in _item:
        _k, _v = _item.split('=', 1)
        OVERRIDE[_k.strip()] = [tuple(x.strip().split(':', 1)) for x in _v.split('+')]

# after reading the example works per broad node (13 Oct): these shelves mostly mean 'read in high school / college'
# or 'made into a film', not books about school life or film
for _k, _v in {'high school': [('other', 'ambiguous')], 'highschool': [('other', 'ambiguous')], 'college': [('other', 'ambiguous')],
               'movies': [('other', 'adaptation')], 'films': [('other', 'adaptation')]}.items():
    OVERRIDE[_k] = _v
