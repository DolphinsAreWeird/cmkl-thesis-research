# Facet lexicon for taxonomy v2 (hand-written; edit here, then rerun 05 onward).
# A phrase is lowercased, '-', '_' and '/' become spaces, '&' becomes 'and'. Each phrase is split into
# components (facet, value) by longest match against the tables below. Facets:
#   genre     a label for the kind of story or book (mystery, romance, memoir, self-help)
#   theme     what the book is about (grief, war, racism, climate change, dogs, space travel)
#   audience  who it is written for (children, middle grade, young adult, new adult, adult)
#   form      fiction / nonfiction / poetry / drama / short stories / comics / picture book ...
#   place     where it is set or where it comes from
#   period    when it is set (eras, centuries, decades)
#   other     subtype in the value: personal, author_series, franchise, award_list, language, mood,
#             trope, publisher, person, unclassified
import re

# ---------------------------------------------------------------- synonyms (whole phrase or sub-phrase)
SYNONYMS = {
    'ww2': 'world war ii', 'wwii': 'world war ii', 'ww ii': 'world war ii', 'world war 2': 'world war ii',
    'world war two': 'world war ii', 'second world war': 'world war ii', 'world war ii': 'world war ii',
    'ww1': 'world war i', 'wwi': 'world war i', 'ww i': 'world war i', 'world war 1': 'world war i',
    'world war one': 'world war i', 'first world war': 'world war i', 'great war': 'world war i',
    'us civil war': 'american civil war', 'history civil war': 'american civil war',
    'sci fi': 'science fiction', 'scifi': 'science fiction', 'sciencefiction': 'science fiction', 'sf': 'science fiction',
    'non fiction': 'nonfiction', 'nf': 'nonfiction', 'non fic': 'nonfiction', 'nonfic': 'nonfiction',
    'lgbt': 'lgbtq', 'glbt': 'lgbtq', 'lgbtqia': 'lgbtq', 'lgbtqa': 'lgbtq', 'lgbtq+': 'lgbtq', 'lgbtqia+': 'lgbtq',
    'lgbt+': 'lgbtq', 'queer': 'lgbtq', 'queer lit': 'lgbtq', 'gay lesbian': 'lgbtq', 'glbtq': 'lgbtq',
    'hist fic': 'historical fiction', 'histfic': 'historical fiction', 'historical fic': 'historical fiction',
    'childrens': 'children', 'children s': 'children', "children's": 'children', 'kids': 'children', 'kid': 'children',
    'juvenile': 'children', 'picturebooks': 'picture book', 'picture books': 'picture book', 'picturebook': 'picture book',
    'humour': 'humor', 'favourites': 'favorites', 'fairytales': 'fairy tales', 'fairytale': 'fairy tales',
    'fairy tale': 'fairy tales', 'mangas': 'manga', 'graphic novels': 'graphic novel', 'comic books': 'comics',
    'comic': 'comics', 'memoirs': 'memoir', 'biographies': 'biography', 'bio': 'biography', 'thrillers': 'thriller',
    'mysteries': 'mystery', 'romances': 'romance', 'westerns': 'western', 'essay': 'essays', 'poems': 'poetry',
    'poem': 'poetry', 'plays': 'drama', 'play': 'drama', 'theatre': 'drama', 'theater': 'drama',
    'short story': 'short stories', 'novellas': 'novella', 'anthologies': 'anthology', 'vampire': 'vampires',
    'werewolf': 'werewolves', 'shifter': 'shapeshifters', 'shifters': 'shapeshifters', 'shapeshifter': 'shapeshifters',
    'witch': 'witches', 'ghost': 'ghosts', 'demon': 'demons', 'angel': 'angels', 'dragon': 'dragons',
    'zombie': 'zombies', 'mermaid': 'mermaids', 'fairy': 'fairies', 'faeries': 'fairies', 'faerie': 'fairies', 'fae': 'fairies',
    'superhero': 'superheroes', 'alien': 'aliens', 'robot': 'robots', 'pirate': 'pirates', 'dog': 'dogs', 'cat': 'cats',
    'horse': 'horses', 'dinosaur': 'dinosaurs', 'bird': 'birds', 'cowboy': 'cowboys', 'biker': 'bikers',
    'dystopia': 'dystopian', 'post apocalypse': 'post apocalyptic', 'postapocalyptic': 'post apocalyptic',
    'apocalyptic': 'post apocalyptic', 'apocalypse': 'post apocalyptic', 'self improvement': 'self help',
    'selfhelp': 'self help', 'self development': 'self help', 'personal development': 'self help',
    'pnr': 'paranormal romance', 'm m': 'male male romance', 'mm': 'male male romance', 'm m romance': 'male male romance',
    'mm romance': 'male male romance', 'male male': 'male male romance', 'gay romance': 'male male romance',
    'chicklit': 'chick lit', 'chic lit': 'chick lit', 'womens fiction': 'womens fiction', 'women s fiction': 'womens fiction',
    'ya': 'young adult', 'teen': 'young adult', 'teens': 'young adult', 'mg': 'middle grade', 'na': 'new adult',
    'cozies': 'cozy mystery', 'cozy mysteries': 'cozy mystery', 'cosy mystery': 'cozy mystery', 'mystery cozy': 'cozy mystery',
    'cozy': 'cozy mystery', 'cosy': 'cozy mystery', 'technothriller': 'techno thriller', 'pop science': 'popular science',
    'popsci': 'popular science', 'pop sci': 'popular science', 'true story': 'true story', 'romcom': 'romantic comedy',
    'rom com': 'romantic comedy', 'african americans': 'african american', 'african american history': 'african american history',
    'mental illness': 'mental illness', 'death and dying': 'death and dying', 'global warming': 'climate change',
    'climate': 'climate change', 'transgender': 'transgender', 'trans': 'transgender', 'christian living': 'christian living',
    'atheism religion': 'atheism', 'gender and sexuality': 'gender and sexuality', 'gender sexuality': 'gender and sexuality',
    'hiv aids': 'hiv aids', 'aids': 'hiv aids', 'hiv': 'hiv aids', 'feminist': 'feminism', 'feminismo': 'feminism',
    'feminist theory': 'feminism', 'feminist lit': 'feminism', 'feminist books': 'feminism',
}

# ---------------------------------------------------------------- personal / task shelves (dropped)
PERSONAL_RE = [re.compile(p) for p in [
    r'^(to )?read$', r'\bto read\b', r'\btbr\b', r'currently', r'\bowned?\b', r'\bown it\b', r'\bi own\b', r'books i own', r'\bmy (books|library|shelf|bookshelf|collection|kindle)\b',
    r'favou?rites?', r'\bfaves?\b', r'\bfav\b', r'all time', r'\bkindle\b', r'\bnook\b', r'\be ?books?\b', r'\baudio ?books?\b', r'\baudio\b',
    r'\baudible\b', r'\blibrary\b', r'book ?club', r'book ?group', r'\bdefault\b', r'wish ?list', r'\bto buy\b', r'\bbuy\b', r'\bdnf\b',
    r'did not finish', r'didn t finish', r'abandoned', r'unfinished', r'gave up', r'^maybe', r'\bre ?read', r'\bborrowed\b', r'^physical',
    r'paperbacks?$', r'hardcovers?$', r'hardbacks?$', r'calibre', r'freebies?', r'^free$', r'\bfree\b', r'^arcs?$', r'\barc\b', r'netgalley', r'edelweiss',
    r'first reads', r'giveaways?', r'goodreads', r'shelfari', r'^have$', r'^books?$', r'^series$', r'part of (a )?series', r'first in (a )?series',
    r'stand ?alone', r'^waiting', r'awaiting', r'^available', r'on hold', r'read again', r'for school', r'^school$', r'classroom', r'class library',
    r'^in class', r'\bclass\b', r'^\d+ (and \d+ )?stars?\b', r'^stars?$', r'\bstar books\b', r'\bwant\b', r'wanted', r'^need', r'purchase', r'^signed', r'autograph', r'bookshelf', r'\bshelf\b',
    r'\bread\b', r'\breads\b', r'\breading\b', r'^done$', r'^finished', r'^unread', r'to review', r'reviewed', r'^recommend', r'^sold$', r'^donated',
    r'\bmine\b', r'^home$', r'^home library', r'^home shelf', r'^kobo', r'^ibooks', r'^scribd', r'^overdrive', r'^amazon', r'^bookbub', r'^dropped', r'not interested', r'^meh$',
    r'^on deck', r'^next', r'^soon', r'^later', r'^someday', r'^pending', r'^queue', r'^up next', r'^reread', r'^series to', r'^books to',
    r'^to get', r'^to find', r'^to check', r'wishlist', r'^bought', r'^gift', r'^loaned', r'^lent', r'^check out', r'^checked out',
    r'^tried', r'^started', r'^didn', r'^couldn', r'\bdid nt\b', r'^not finished', r'^not for me', r'^nope', r'^no$', r'^yes$',
    r'^own ', r' own$', r'^owned ', r'^audible', r'^audiobook', r'^e book', r'^digital', r'^pdf', r'^epub', r'^mobi', r'^print$',
    r'kindle unlimited', r'^ku$', r'prime', r'^nominee', r'^reviewed', r'^series i', r'^authors? i', r'^books i', r'^i ', r'^my ',
    r'^dad$', r'^mom$', r'^husband', r'^wife', r'^son s', r'^daughter s', r'\bbox\b', r'\bbin\b', r'storage', r'^attic', r'^basement',
]]
YEARISH_RE = re.compile(r'(^|\b)(19|20)\d\d(\b|$)')       # 'read in 2015', '2016 reads' (decades '1920s' are handled first)
DECADE_RE = re.compile(r'^(the )?((1[0-9]|20)\d0)s$|^((1[0-9]|20)\d0)s ')
CENTURY_RE = re.compile(r'(\d{1,2})(st|nd|rd|th)? (century|c)\b|^(1[0-9])00s$')
AWARD_RE = re.compile(r'award|prize|winners?\b|nominee|pulitzer|booker|newbery|newberry|caldecott|printz|hugo|nebula|edgar|carnegie|'
                      r'\b1001\b|bbc|\bnpr\b|must read|before you die|best of|top 100|top 10|bestsellers?|best ?sellers?|oprah|'
                      r'national book|costa|man booker|orange prize|women s prize|giller|alex award|stonewall|coretta|geisel|agatha award')
LANGUAGE = {'francais', 'français', 'en francais', 'en français', 'french language', 'espanol', 'español', 'spanish language', 'en espanol',
            'deutsch', 'german language', 'italiano', 'classici', 'classiques', 'litterature', 'littérature', 'litterature francaise',
            'littérature française', 'portugues', 'português', 'nederlands', 'dutch language', 'svenska', 'norsk', 'dansk', 'suomi',
            'polski', 'russkiy', 'translated', 'translation', 'translations', 'in translation', 'translated fiction', 'foreign language',
            'english language', 'non english', 'bilingual', 'foreign', 'romanzi', 'libri', 'livres', 'bücher', 'buecher', 'roman', 'romans'}
MOOD = {'dark', 'sad', 'cute', 'emotional', 'heartbreaking', 'heart breaking', 'tear jerker', 'tearjerker', 'tear jerkers', 'tearjerkers',
        'creepy', 'scary', 'feel good', 'feelgood', 'uplifting', 'inspiring', 'intense', 'quirky', 'weird', 'sweet', 'steamy', 'hot',
        'sexy', 'clean', 'fluff', 'fluffy', 'angst', 'angsty', 'light', 'light reading', 'light reads', 'beach read', 'beach reads',
        'summer read', 'summer reads', 'summer reading', 'twisted', 'disturbing', 'gritty', 'thought provoking', 'mind blowing',
        'mindblowing', 'beautiful', 'lyrical', 'atmospheric', 'slow burn', 'page turner', 'page turners', 'fast paced', 'suspenseful',
        'heartwarming', 'heart warming', 'feels', 'swoon', 'swoony', 'hilarious', 'brilliant', 'amazing', 'awesome', 'boring', 'meh',
        'disappointing', 'loved it', 'love it', 'loved', 'liked', 'good', 'great', 'ok', 'okay', 'interesting', 'fun', 'entertaining',
        'serious', 'deep', 'melancholy', 'bittersweet', 'comfort', 'comfort reads', 'comfort read', 'guilty pleasure', 'guilty pleasures',
        'brain candy', 'mind candy', 'escapism', 'escapist', 'easy read', 'quick read', 'quick reads', 'short reads', 'long', 'chunksters',
        'epic', 'gripping', 'unputdownable', 'kick ass heroine', 'kick ass heroines', 'strong heroine', 'strong female lead',
        'strong female', 'strong female character', 'strong women', 'kickass heroine', 'tough heroine', 'smart heroine', 'bad ass',
        'badass', 'witty', 'clever', 'smart', 'quick', 'mature', 'heavy', 'tragic', 'tragedy', 'happy', 'happy ending', 'hea', 'hfn',
        'romantic', 'sensual', 'spicy', 'smut', 'smutty', 'raunchy', 'erotic heat', 'nsfw', 'violent', 'gory', 'gore', 'graphic violence',
        'realistic', 'unique', 'original', 'different', 'strange', 'surreal', 'bizarre', 'whimsical', 'magical', 'charming', 'dreamy',
        'haunting', 'eerie', 'spooky', 'chilling', 'cliffhanger', 'cliffhangers', 'cliff hanger', 'twist', 'twists', 'plot twist',
        'mind bending', 'mind fuck', 'mindfuck', 'mind games', 'tense', 'nail biter', 'edge of seat', 'adrenaline', 'action packed',
        'feisty heroine', 'sassy', 'snark', 'snarky', 'banter', 'cute and fluffy', 'sweet romance', 'clean romance', 'christian clean',
        'no sex', 'sex', 'sexual', 'adult content', 'mature content', 'explicit', 'triggers', 'trigger warning', 'tw', 'cw'}
TROPE = {'alpha male', 'alpha males', 'alpha', 'alpha hero', 'alpha heroes', 'bad boy', 'bad boys', 'billionaire', 'billionaires',
         'billionaire romance', 'billionaire bachelors', 'second chance', 'second chances', 'second chance romance', 'friends to lovers',
         'enemies to lovers', 'love triangle', 'love triangles', 'insta love', 'instalove', 'insta lust', 'virgin heroine', 'virgin',
         'virgins', 'menage', 'ménage', 'reverse harem', 'harem', 'dual pov', 'multiple pov', 'pov', 'first person', 'third person',
         'plain jane', 'mail order bride', 'mail order brides', 'marriage of convenience', 'fake relationship', 'fake dating',
         'forbidden love', 'forbidden', 'secret baby', 'older man', 'older hero', 'age gap', 'age difference', 'bodyguard', 'bodyguards',
         'bikers', 'mc', 'motorcycle club', 'mc romance', 'rockstar', 'rockstars', 'rock star', 'rock stars', 'rockstar romance',
         'cowboys', 'cowboy romance', 'sheikh', 'sheikhs', 'highlanders', 'highlander', 'dukes', 'duke', 'rakes', 'rake', 'rogue',
         'rogues', 'royalty', 'royals', 'prince', 'princes', 'princess', 'princesses', 'boss', 'office romance', 'workplace romance',
         'sports romance', 'military romance', 'hero', 'heroine', 'heroes', 'heroines', 'anti hero', 'antihero', 'villain', 'villains',
         'love story', 'love stories', 'unrequited love', 'soulmates', 'soul mates', 'mates', 'mate', 'fated mates', 'possessive',
         'possessive hero', 'jealous', 'jealous hero', 'kidnapping romance', 'captive', 'stalker', 'tortured hero', 'damaged hero',
         'wounded hero', 'beta hero', 'nerd', 'nerds', 'geek', 'geeks', 'book boyfriend', 'book boyfriends', 'book boyfriend material',
         'swoon worthy', 'hot guys', 'hot men', 'men in uniform', 'navy seals', 'navy seal', 'seals', 'marines', 'cops', 'firefighters',
         'doctors', 'nurses', 'teachers', 'student teacher', 'professor', 'roommates', 'neighbors', 'small town romance', 'small town',
         'holiday romance', 'christmas romance', 'vacation romance', 'summer romance', 'opposites attract', 'slow build', 'hate to love',
         'love hate', 'brother s best friend', 'best friend s brother', 'single dad', 'single father', 'single mom', 'single mother',
         'widow', 'widower', 'pregnancy romance', 'accidental pregnancy', 'baby', 'babies', 'twins'}
PUBLISHER = {'penguin classics', 'penguin', 'vintage', 'nyrb classics', 'nyrb', 'everyman s library', 'everyman', 'harlequin',
             'harlequin presents', 'harlequin romance', 'silhouette', 'mills and boon', 'mills boon', 'samhain', 'ellora s cave',
             'black library', 'angry robot', 'little black classics', 'harvard classics', 'great illustrated classics', 'oxford',
             'oxford world s classics', 'barnes and noble classics', 'dover', 'tor', 'baen', 'daw', 'ace', 'orbit', 'carina press',
             'entangled', 'loveswept', 'avon', 'avon romance', 'kensington', 'zebra', 'bantam', 'puffin', 'scholastic', 'usborne',
             'dorling kindersley', 'dk', 'lonely planet', 'rick steves', 'for dummies', 'dummies', 'very short introductions',
             'a very short introduction', 'penguin modern classics', 'modern library', 'library of america', 'folio society',
             'wordsworth classics', 'signet classics', 'bantam classics', 'puffin classics', 'vertigo', 'image comics', 'dark horse',
             'marvel comics', 'dc comics', 'viz', 'yen press', 'tokyopop', 'kodansha', 'seven seas', 'first second', 'graphix'}
FRANCHISE = {'star wars', 'starwars', 'star wars legends', 'star wars books', 'star wars novels', 'star wars eu', 'star wars canon',
             'star wars new canon', 'star wars to read', 'star wars read', 'star wars comics', 'star trek', 'warhammer', 'warhammer 40k',
             'warhammer 40000', 'warhammer 40 000', 'warhammer40k', 'black library', 'doctor who', 'dr who', 'marvel', 'marvel comics',
             'marvel civil war', 'dc', 'dc comics', 'batman', 'superman', 'spider man', 'spiderman', 'x men', 'avengers', 'captain america',
             'wonder woman', 'justice league', 'disney', 'pokemon', 'minecraft', 'lego', 'warcraft', 'world of warcraft', 'forgotten realms',
             'dragonlance', 'dungeons and dragons', 'd and d', 'halo', 'star wars expanded universe', 'harry potter', 'hp', 'twilight',
             'sherlock holmes', 'sherlock', 'middle earth', 'tolkien', 'narnia', 'oz', 'wizard of oz', 'pern', 'discworld', 'xanth',
             'riftwar', 'riftwar cycle', 'sailor moon', 'death note', 'naruto', 'one piece', 'bleach', 'fairy tail', 'the walking dead',
             'walking dead', 'buffy', 'buffyverse', 'stargate', 'babylon 5', 'firefly', 'transformers', 'g i joe', 'my little pony',
             'scooby doo', 'barbie', 'thomas the tank engine', 'peppa pig', 'paw patrol', 'frozen', 'hello kitty', 'rainbow magic',
             'nancy drew', 'hardy boys', 'goosebumps', 'baby sitters club', 'babysitters club', 'berenstain bears', 'the berenstain bears',
             'captain underpants', 'magic tree house', 'warriors', 'warrior cats', 'warriors series', 'warriors books', 'animorphs',
             'redwall', 'percy jackson', 'hunger games', 'divergent', 'mortal instruments', 'shadowhunters', 'vampire academy',
             'house of night', 'sookie stackhouse', 'southern vampire mysteries', 'black dagger brotherhood', 'in death',
             'in death series', 'stephanie plum', 'jack reacher', 'alex cross', 'kinsey millhone', 'alphabet series', 'outlander',
             'game of thrones', 'a song of ice and fire', 'asoiaf', 'wheel of time', 'wot', 'dresden files', 'mercy thompson',
             'anita blake', 'repairman jack', 'elemental assassin', 'death on demand', 'alex delaware', 'alex delaware series',
             'roy grace', 'maisie dobbs', 'agatha raisin', 'elder races', 'black stallion', 'bobbsey twins', 'boxcar children',
             'american girl', 'dear america', 'royal diaries', 'magic school bus', 'little house', 'little house on the prairie',
             'anne of green gables', 'chronicles of narnia', 'oz books', 'tarzan', 'conan', 'james bond', '007', 'bond', 'jason bourne',
             'jurassic park', 'alien', 'predator', 'terminator', 'matrix', 'indiana jones', 'mass effect', 'dragon age', 'assassin s creed',
             'resident evil', 'the witcher', 'witcher', 'elder scrolls', 'fallout', 'diablo', 'starcraft', 'mechwarrior', 'battletech',
             'shadowrun', 'dune', 'foundation', 'culture series', 'honor harrington', 'honorverse', 'vorkosigan', 'vorkosigan saga',
             'ender', 'enders game', 'ender s game', 'hitchhiker s guide', 'hitchhikers guide', 'redwall', 'his dark materials'}
FILLER = {'books', 'book', 'about', 'on', 'the', 'and', 'of', 'in', 'set', 'with', 'related', 'stuff', 'reads', 'genre', 'genres',
          'themes', 'theme', 'topics', 'topic', 'type', 'for', 'a', 'an', 'to', 'by', 'from', 'general', 'misc', 'miscellaneous',
          'other', 'etc', 'various', 'subject', 'subjects', 'category', 'interest', 'interests', 'lit', 'literature', 'novels', 'novel',
          'stories', 'story', 'tales', 'titles', 'works', 'writing', 'writings', 'collection', 'collections', 'series', 'related'}

# ---------------------------------------------------------------- audience, form, genre, period, place
AUDIENCE = {
    'children': 'children', 'childhood books': 'children', 'childhood favorites': 'children', 'childhood reads': 'children',
    'childhood favourites': 'children', 'storytime': 'children', 'story time': 'children', 'toddler': 'children', 'toddlers': 'children',
    'preschool': 'children', 'baby books': 'children', 'board books': 'children', 'board book': 'children', 'early reader': 'children',
    'early readers': 'children', 'easy reader': 'children', 'easy readers': 'children', 'beginning reader': 'children',
    'beginning readers': 'children', 'chapter books': 'children', 'chapter book': 'children', 'picture book': 'children',
    'kids books': 'children', 'kidlit': 'children', 'kid lit': 'children', 'elementary': 'children',
    'middle grade': 'middle grade', 'middle school': 'middle grade', 'tween': 'middle grade', 'tweens': 'middle grade',
    'juvenile fiction': 'children', 'juvenile literature': 'children', 'juvenile nonfiction': 'children',
    'young adult': 'young adult', 'teen fiction': 'young adult', 'young adult fiction': 'young adult',
    'young adult literature': 'young adult', 'young adult nonfiction': 'young adult', 'ya lit': 'young adult',
    'new adult': 'new adult', 'adult': 'adult', 'adult fiction': 'adult', 'adult nonfiction': 'adult', 'grown up': 'adult',
    'grown ups': 'adult', 'adults': 'adult',
}
FORM = {
    'fiction': 'fiction', 'nonfiction': 'nonfiction', 'novella': 'novella', 'short stories': 'short stories',
    'anthology': 'anthology', 'literary anthologies': 'anthology', 'literary collections': 'anthology', 'poetry': 'poetry',
    'drama': 'drama', 'essays': 'essays', 'essays and short works': 'essays', 'short works': 'short stories',
    'graphic novel': 'comics and graphic novels', 'graphic': 'comics and graphic novels', 'comics': 'comics and graphic novels',
    'comics and graphic novels': 'comics and graphic novels', 'comic and graphic books': 'comics and graphic novels',
    'graphic novels and comics': 'comics and graphic novels', 'graphic novels comics': 'comics and graphic novels',
    'comics graphic novels': 'comics and graphic novels', 'comics graphic': 'comics and graphic novels',
    'manga': 'comics and graphic novels', 'manhwa': 'comics and graphic novels', 'manga comics': 'comics and graphic novels',
    'manga manhwa': 'comics and graphic novels', 'manga graphic novels': 'comics and graphic novels', 'webcomics': 'comics and graphic novels',
    'read manga': 'comics and graphic novels', 'manga read': 'comics and graphic novels', 'comics read': 'comics and graphic novels',
    'shoujo': 'comics and graphic novels', 'shojo': 'comics and graphic novels', 'shounen': 'comics and graphic novels',
    'shonen': 'comics and graphic novels', 'seinen': 'comics and graphic novels', 'josei': 'comics and graphic novels',
    'picture book': 'picture book', 'picture book fiction': 'picture book', 'picture book nonfiction': 'picture book',
    'chapter books': 'chapter book', 'chapter book': 'chapter book', 'board books': 'picture book', 'board book': 'picture book',
    'early reader': 'early reader', 'early readers': 'early reader', 'easy reader': 'early reader', 'easy readers': 'early reader',
    'beginning reader': 'early reader', 'beginning readers': 'early reader', 'transitional chapter': 'chapter book',
    'reference': 'reference', 'textbook': 'textbook', 'textbooks': 'textbook', 'text books': 'textbook', 'study aids and workbooks': 'textbook',
    'study aids': 'textbook', 'cookbook': 'cookbook', 'cookbooks': 'cookbook', 'cook books': 'cookbook', 'letters': 'letters',
    'epistolary': 'letters', 'epistolary fiction': 'letters', 'diary': 'diary', 'diaries': 'diary', 'speeches': 'speeches',
    'interviews': 'interviews', 'literature': 'literature', 'novel': 'novel', 'novels': 'novel', 'classic literature': 'literature',
    'non english fiction': 'fiction', 'non english nonfiction': 'nonfiction', 'lyric': 'poetry',
    'sonnets': 'poetry', 'ballads': 'poetry', 'epics': 'poetry', 'epic poetry': 'poetry', 'tragedy': 'drama', 'narratives': 'nonfiction',
    'informational': 'nonfiction', 'how to': 'how-to guide', 'guide': 'how-to guide', 'guides': 'how-to guide',
    'handbook': 'how-to guide', 'manual': 'how-to guide', 'workbook': 'textbook', 'sheet music': 'sheet music', 'music sheet': 'sheet music',
    'songbook': 'sheet music', 'single author collections': 'anthology', 'single author': 'anthology', 'quotes': 'quotations',
    'quotations': 'quotations', 'proverb': 'quotations', 'proverbs': 'quotations', 'aphorisms': 'quotations',
}
G = lambda *v: [('genre', x) for x in v]
GENRE = {
    'mystery': G('mystery'), 'whodunit': G('mystery'), 'whodunnit': G('mystery'), 'detective': G('mystery'), 'detectives': G('mystery'),
    'detective fiction': G('mystery'), 'crime': G('crime'), 'crime fiction': G('crime'), 'noir': G('crime'), 'hardboiled': G('crime'),
    'hard boiled': G('crime'), 'police procedural': G('crime'), 'police procedurals': G('crime'), 'procedural': G('crime'),
    'mystery crime': G('mystery', 'crime'), 'crime mystery': G('mystery', 'crime'), 'crime and mystery fiction': G('mystery', 'crime'),
    'cozy mystery': G('cozy mystery'), 'historical mystery': G('historical fiction', 'mystery'), 'historical mysteries': G('historical fiction', 'mystery'),
    'thriller': G('thriller'), 'techno thriller': G('thriller'), 'psychological thriller': G('psychological thriller'),
    'psychological thrillers': G('psychological thriller'), 'legal thriller': G('legal thriller'), 'legal thrillers': G('legal thriller'),
    'medical thriller': G('thriller'), 'political thriller': G('political thriller'), 'political thrillers': G('political thriller'),
    'suspense': G('suspense'), 'mystery suspense': G('mystery', 'suspense'), 'suspense thriller': G('suspense', 'thriller'),
    'mystery thriller': G('mystery', 'thriller'), 'thriller suspense': G('suspense', 'thriller'), 'suspense espionage political and thrillers': G('thriller', 'spy fiction'),
    'romantic suspense': G('romance', 'suspense'), 'romance suspense': G('romance', 'suspense'),
    'espionage': G('spy fiction'), 'spy': G('spy fiction'), 'spies': G('spy fiction'), 'spy thriller': G('spy fiction'), 'spy fiction': G('spy fiction'),
    'romance': G('romance'), 'contemporary romance': G('contemporary romance'), 'romance contemporary': G('contemporary romance'),
    'historical romance': G('historical romance'), 'romance historical': G('historical romance'), 'regency romance': G('historical romance'),
    'regency': G('historical romance'), 'paranormal romance': G('paranormal romance'), 'romance paranormal': G('paranormal romance'),
    'erotic romance': G('erotic romance'), 'erotica': G('erotica'), 'erotic': G('erotica'), 'erotic fiction': G('erotica'),
    'erotic literature': G('erotica'), 'bdsm': G('erotica'), 'kink': G('erotica'), 'passion': G('romance'),
    'christian romance': G('christian fiction', 'romance'), 'inspirational romance': G('christian fiction', 'romance'),
    'romantic comedy': G('romantic comedy'), 'male male romance': [('genre', 'romance'), ('theme', 'gay men')],
    'classic romance': G('romance', 'classics'), 'relationship novel': G('romance'), 'romance with more': G('romance'),
    'heart and home': G('romance'), 'chick lit': G('chick lit'), 'chick lit fiction': G('chick lit'), 'chick lit nonfiction': G('chick lit'),
    'womens fiction': G('womens fiction'), 'women fiction': G('womens fiction'),
    'fantasy': G('fantasy'), 'high fantasy': G('epic fantasy'), 'epic fantasy': G('epic fantasy'), 'urban fantasy': G('urban fantasy'),
    'dark fantasy': G('dark fantasy'), 'sword and sorcery': G('epic fantasy'), 'fantasy fiction': G('fantasy'),
    'fantastic fiction': G('fantasy'), 'paranormal': G('paranormal'), 'supernatural': G('paranormal'), 'paranormal fantasy': G('paranormal', 'fantasy'),
    'science fiction': G('science fiction'), 'speculative fiction': G('speculative fiction'), 'speculative': G('speculative fiction'),
    'space opera': G('space opera'), 'hard science fiction': G('science fiction'), 'military science fiction': [('genre', 'science fiction'), ('theme', 'military')],
    'military scifi': [('genre', 'science fiction'), ('theme', 'military')], 'cyberpunk': G('cyberpunk'), 'steampunk': G('steampunk'),
    'dystopian': G('dystopian'), 'post apocalyptic': G('post-apocalyptic'), 'science fantasy': G('science fiction', 'fantasy'),
    'sff': G('science fiction', 'fantasy'), 'science fiction and fantasy': G('science fiction', 'fantasy'),
    'science fiction fantasy': G('science fiction', 'fantasy'), 'fantasy science fiction': G('science fiction', 'fantasy'),
    'scifi fantasy': G('science fiction', 'fantasy'), 'fantasy scifi': G('science fiction', 'fantasy'),
    'alternate history': G('alternate history'), 'alternative history': G('alternate history'), 'alt history': G('alternate history'),
    'horror': G('horror'), 'horror and supernatural fiction': G('horror', 'paranormal'), 'gothic': G('gothic'), 'gothic fiction': G('gothic'),
    'southern gothic': [('genre', 'gothic'), ('place', 'american south')], 'ghost stories': [('genre', 'horror'), ('theme', 'ghosts')],
    'historical fiction': G('historical fiction'), 'historical': G('historical fiction'), 'historicals': G('historical fiction'),
    'literary fiction': G('literary fiction'), 'literary': G('literary fiction'), 'general fiction': G('general fiction'),
    'contemporary fiction': G('contemporary fiction'), 'contemporary': G('contemporary fiction'), 'realistic fiction': G('contemporary fiction'),
    'domestic fiction': G('domestic fiction'), 'family saga': G('family saga'), 'saga': G('family saga'), 'sagas': G('family saga'),
    'magical realism': G('magical realism'), 'magic realism': G('magical realism'), 'satire': G('satire'), 'humor': G('humor'),
    'funny': G('humor'), 'comedy': G('humor'), 'humorous': G('humor'), 'humorous fiction': G('humor'), 'humor fiction': G('humor'),
    'humor nonfiction': G('humor'), 'parody': G('satire'), 'classics': G('classics'), 'classic': G('classics'),
    'modern classics': G('classics'), 'classic fiction': G('classics'), 'classic lit': G('classics'), 'classical literature': G('classics'),
    'classic literature': G('classics'), 'american classics': [('genre', 'classics'), ('place', 'united states')],
    'russian classics': [('genre', 'classics'), ('place', 'russia')], 'russian classic': [('genre', 'classics'), ('place', 'russia')],
    'adventure': G('adventure'), 'action': G('action'), 'action adventure': G('adventure', 'action'), 'action and adventure': G('adventure', 'action'),
    'action and adventure fiction': G('adventure', 'action'), 'western': G('western'), 'christian fiction': G('christian fiction'),
    'religious fiction': G('christian fiction'), 'inspirational fiction': G('christian fiction'), 'urban fiction': G('urban fiction'),
    'street lit': G('urban fiction'), 'fairy tales': G('fairy tales'), 'fairy tale retellings': G('retellings'), 'retellings': G('retellings'),
    'retelling': G('retellings'), 'fractured fairy tales': G('retellings'), 'myths legends and fairy tales': [('genre', 'fairy tales'), ('theme', 'mythology')],
    'folklore': G('folklore and fables'), 'folk tales': G('folklore and fables'), 'fables': G('folklore and fables'), 'legends': G('folklore and fables'),
    'nursery rhymes': G('folklore and fables'), 'pulp': G('pulp fiction'), 'pulp fiction': G('pulp fiction'), 'transgressive': G('literary fiction'),
    'experimental': G('literary fiction'), 'postmodern': G('literary fiction'), 'postmodernism': G('literary fiction'),
    'memoir': G('memoir'), 'biography': G('biography'), 'autobiography': G('memoir'), 'biography memoir': G('biography', 'memoir'),
    'memoir biography': G('biography', 'memoir'), 'biography and autobiography': G('biography', 'memoir'),
    'biography and memoir': G('biography', 'memoir'), 'biography and autobiography nonfiction': G('biography', 'memoir'),
    'fictional biographies and memoirs': [('genre', 'historical fiction'), ('genre', 'biography')], 'true crime': G('true crime'),
    'self help': G('self-help'), 'popular science': G('popular science'), 'narrative nonfiction': G('narrative nonfiction'),
    'creative nonfiction': G('narrative nonfiction'), 'journalism': G('journalism'), 'travel writing': [('genre', 'travel writing'), ('theme', 'travel')],
    'travel literature': [('genre', 'travel writing'), ('theme', 'travel')], 'travelogue': [('genre', 'travel writing'), ('theme', 'travel')],
    'travel fiction': [('genre', 'adventure'), ('theme', 'travel')], 'nautical and marine fiction': [('genre', 'adventure'), ('theme', 'seafaring')],
    'nautical fiction': [('genre', 'adventure'), ('theme', 'seafaring')], 'sports fiction': [('genre', 'sports fiction'), ('theme', 'sports')],
    'war and military fiction': [('genre', 'war fiction'), ('theme', 'war')], 'war fiction': [('genre', 'war fiction'), ('theme', 'war')],
    'military fiction': [('genre', 'war fiction'), ('theme', 'military')], 'nature and animal fiction': [('genre', 'animal stories'), ('theme', 'animals')],
    'animal stories': G('animal stories'), 'literary criticism': G('literary criticism'), 'criticism': G('literary criticism'),
    'analysis': G('literary criticism'), 'scholarly': G('academic'), 'academic': G('academic'), 'research': G('academic'),
    'new age': [('genre', 'new age'), ('theme', 'spirituality')], 'inspirational': G('inspirational'), 'christian nonfiction': [('genre', 'christian nonfiction'), ('theme', 'christianity')],
    'devotional': [('genre', 'christian nonfiction'), ('theme', 'christianity')], 'devotionals': [('genre', 'christian nonfiction'), ('theme', 'christianity')],
    'christian living': [('genre', 'christian nonfiction'), ('theme', 'christianity')], 'christian': [('genre', 'christian fiction'), ('theme', 'christianity')],
    'amish fiction': [('genre', 'christian fiction'), ('theme', 'amish')], 'amish': [('genre', 'christian fiction'), ('theme', 'amish')],
    'culture and heritage fiction': [('genre', 'literary fiction'), ('theme', 'culture and heritage')], 'tall tales': G('folklore and fables'),
    'chick lit romance': G('chick lit', 'romance'), 'epic': G('epic fantasy'),
}
PERIOD = {
    'victorian': 'victorian era', 'victorian era': 'victorian era', 'victorian england': 'victorian era', 'edwardian': 'edwardian era',
    'georgian': 'georgian era', 'regency era': 'regency era', 'regency england': 'regency era', 'tudor': 'tudor period', 'tudors': 'tudor period',
    'tudor period': 'tudor period', 'tudor england': 'tudor period', 'elizabethan': 'elizabethan era', 'medieval': 'middle ages',
    'middle ages': 'middle ages', 'medieval history': 'middle ages', 'middle ages middle history': 'middle ages', 'renaissance': 'renaissance',
    'ancient': 'ancient world', 'antiquity': 'ancient world', 'ancient history': 'ancient world', 'ancient world': 'ancient world',
    'classical antiquity': 'ancient world', 'classics greek and latin antiquity': 'ancient world', 'asian antiquity': 'ancient world',
    'ancient rome': 'ancient rome', 'rome ancient': 'ancient rome', 'roman': 'ancient rome', 'romans': 'ancient rome', 'roman empire': 'ancient rome',
    'ancient greece': 'ancient greece', 'greek': 'ancient greece', 'ancient egypt': 'ancient egypt', 'egyptian': 'ancient egypt',
    'prehistoric': 'prehistory', 'prehistory': 'prehistory', 'stone age': 'prehistory', 'ice age': 'prehistory', 'bronze age': 'ancient world',
    'colonial': 'colonial era', 'colonial america': 'colonial era', 'antebellum': 'antebellum era', 'gilded age': 'gilded age',
    'jazz age': '1920s', 'roaring twenties': '1920s', 'belle epoque': 'belle epoque', 'early modern': 'early modern period',
    'modern 19th c': '19th century', 'modern 20th c': '20th century', 'modern': '20th century', 'published 1900 onward': '20th century',
    'published 1800 1900': '19th century', 'published before 1800': 'before 1800', 'viking age': 'viking age', 'vikings': 'viking age',
    'viking': 'viking age', 'edo period': 'edo period', 'meiji': 'meiji era', 'interwar': 'interwar period', 'postwar': 'postwar period',
    'post war': 'postwar period', 'futuristic': 'future', 'future': 'future', 'near future': 'future', 'historical england': 'england history',
}
PLACE_LIST = '''africa;asia;europe;north america;south america;latin america;central america;middle east;antarctica;arctic;australia;
oceania;caribbean;scandinavia;nordic;balkans;east asia;southeast asia;south asia;west africa;east africa;southern africa;
united states;usa;america;us;united kingdom;uk;great britain;britain;england;scotland;wales;ireland;northern ireland;france;germany;
italy;spain;portugal;greece;netherlands;holland;belgium;switzerland;austria;poland;czech republic;czechoslovakia;hungary;romania;
bulgaria;yugoslavia;serbia;croatia;bosnia;ukraine;russia;soviet union;ussr;sweden;norway;denmark;finland;iceland;estonia;latvia;
lithuania;turkey;ottoman empire;israel;palestine;lebanon;syria;iraq;iran;persia;afghanistan;pakistan;india;bangladesh;sri lanka;nepal;
tibet;china;japan;korea;north korea;south korea;taiwan;hong kong;vietnam;cambodia;laos;thailand;burma;myanmar;malaysia;singapore;
indonesia;philippines;egypt;libya;tunisia;algeria;morocco;sudan;ethiopia;somalia;kenya;uganda;rwanda;congo;nigeria;ghana;cameroon;
equatorial guinea;sierra leone;liberia;senegal;zimbabwe;zambia;botswana;south africa;madagascar;mexico;cuba;haiti;jamaica;
dominican republic;puerto rico;guatemala;el salvador;nicaragua;honduras;panama;colombia;venezuela;peru;ecuador;bolivia;chile;
argentina;brazil;uruguay;paraguay;canada;new zealand;greenland;hawaii;alaska;california;texas;florida;new york;new york city;nyc;
manhattan;brooklyn;chicago;boston;seattle;san francisco;los angeles;hollywood;new orleans;washington dc;washington;maine;vermont;
massachusetts;new england;appalachia;montana;wyoming;colorado;arizona;new mexico;utah;nevada;oregon;idaho;minnesota;wisconsin;
michigan;ohio;pennsylvania;virginia;north carolina;south carolina;georgia state;tennessee;kentucky;alabama;mississippi;louisiana;
arkansas;missouri;iowa;kansas;nebraska;oklahoma;dakota;north dakota;south dakota;indiana;illinois;new jersey;maryland;connecticut;
rhode island;delaware;west virginia;the south;american south;deep south;southern;midwest;the west;american west;wild west;old west;
pacific northwest;london;paris;rome;venice;florence;berlin;vienna;moscow;st petersburg;tokyo;kyoto;beijing;shanghai;delhi;mumbai;
bombay;calcutta;kolkata;istanbul;constantinople;cairo;jerusalem;dublin;edinburgh;glasgow;amsterdam;barcelona;madrid;prague;budapest;
warsaw;havana;toronto;montreal;vancouver;sydney;melbourne;cape town;nairobi;lagos;oxford;cambridge;cornwall;yorkshire;devon;
cotswolds;highlands;scottish highlands;provence;tuscany;sicily;bavaria;siberia;outback;sahara;amazon rainforest;himalayas;dresden;
pompeii;madeira;canary islands;cheshire;malmo;stockholm;oslo;copenhagen;helsinki;reykjavik;athens;lisbon;naples;milan;munich;
hamburg;brussels;geneva;zurich;krakow;kiev;kyiv;baghdad;tehran;kabul;karachi;lahore;bangkok;saigon;hanoi;seoul;singapore city;
manila;jakarta;bali;johannesburg;mexico city;buenos aires;rio de janeiro;sao paulo;lima;bogota;santiago;quebec;nova scotia;
newfoundland;british columbia;ontario;alberta;prince edward island;yukon;tasmania;queensland;new south wales;victoria australia'''
PLACES = {p.strip() for p in PLACE_LIST.replace('\n', '').split(';') if p.strip()}
DEMONYM = {'american': 'united states', 'british': 'united kingdom', 'english': 'england', 'scottish': 'scotland', 'scots': 'scotland',
           'irish': 'ireland', 'welsh': 'wales', 'french': 'france', 'german': 'germany', 'italian': 'italy', 'spanish': 'spain',
           'portuguese': 'portugal', 'russian': 'russia', 'soviet': 'soviet union', 'polish': 'poland', 'czech': 'czech republic',
           'hungarian': 'hungary', 'swedish': 'sweden', 'norwegian': 'norway', 'danish': 'denmark', 'finnish': 'finland',
           'icelandic': 'iceland', 'dutch': 'netherlands', 'belgian': 'belgium', 'swiss': 'switzerland', 'austrian': 'austria',
           'turkish': 'turkey', 'israeli': 'israel', 'iranian': 'iran', 'persian': 'iran', 'afghan': 'afghanistan', 'indian': 'india',
           'pakistani': 'pakistan', 'chinese': 'china', 'japanese': 'japan', 'korean': 'korea', 'vietnamese': 'vietnam', 'thai': 'thailand',
           'egyptian modern': 'egypt', 'nigerian': 'nigeria', 'kenyan': 'kenya', 'south african': 'south africa', 'mexican': 'mexico',
           'cuban': 'cuba', 'brazilian': 'brazil', 'argentinian': 'argentina', 'chilean': 'chile', 'colombian': 'colombia',
           'canadian': 'canada', 'canadiana': 'canada', 'canlit': 'canada', 'australian': 'australia', 'aussie': 'australia',
           'kiwi': 'new zealand', 'african': 'africa', 'asian': 'asia', 'european': 'europe', 'latin american': 'latin america',
           'caribbean': 'caribbean', 'scandinavian': 'scandinavia', 'nordic noir': 'scandinavia', 'middle eastern': 'middle east',
           'texan': 'texas', 'californian': 'california', 'new yorker': 'new york', 'southern': 'american south', 'the south': 'american south',
           'deep south': 'american south', 'usa': 'united states', 'us': 'united states', 'america': 'united states', 'uk': 'united kingdom',
           'great britain': 'united kingdom', 'britain': 'united kingdom', 'nyc': 'new york city', 'new york city': 'new york city',
           'ussr': 'soviet union', 'holland': 'netherlands', 'persia': 'iran', 'bombay': 'mumbai', 'calcutta': 'kolkata',
           'constantinople': 'istanbul', 'burma': 'myanmar', 'kiev': 'kyiv', 'americana': 'united states', 'old west': 'american west',
           'wild west': 'american west', 'the west': 'american west', 'britlit': 'united kingdom', 'brit lit': 'united kingdom',
           'american lit': 'united states', 'american literature': 'united states', 'british literature': 'united kingdom',
           'british lit': 'united kingdom', 'english literature': 'england', 'english lit': 'england', 'irish literature': 'ireland',
           'russian literature': 'russia', 'french literature': 'france', 'japanese literature': 'japan', 'canadian literature': 'canada',
           'australian literature': 'australia', 'german literature': 'germany', 'african literature': 'africa', 'indian literature': 'india',
           'latin american literature': 'latin america', 'scottish literature': 'scotland', 'southern fiction': 'american south',
           'southern lit': 'american south', 'southern literature': 'american south'}

# ---------------------------------------------------------------- themes: 'surface=canonical' or just 'canonical'
THEME_LIST = '''war;wars=war;warfare=war;military;military war=military;military history=military;history;histories=history;
politics;political=politics;political science=politics;politics current events=current events;politics economics=politics;
history politics=politics;political theory=political philosophy;political philosophy;geopolitics;international relations;
current affairs=current events;current events;government;democracy;elections;presidents;law;legal=law;lawyers=law;justice;
criminal justice;crime;murder;serial killers;serial killer=serial killers;police;fbi;cia=intelligence agencies;intelligence agencies;
mafia;organized crime;mob=organized crime;gangs;heist;heists=heist;prison;prisons=prison;terrorism;terror=terrorism;war on terror=terrorism;
violence;abuse;child abuse;domestic violence;domestic abuse=domestic violence;sexual abuse;rape=sexual violence;sexual assault=sexual violence;
sexual violence;sexual harassment;metoo=sexual harassment;incest;abused heroine=abuse;bullying;trauma;ptsd;mental health;mental illness;
mental=mental health;depression;anxiety;suicide;self harm;eating disorders;anorexia=eating disorders;bipolar;bipolar disorder=bipolar;
schizophrenia;ocd;addiction;alcoholism;drugs;drug addiction=addiction;recovery=addiction and recovery;addiction and recovery;grief;
loss=grief;bereavement=grief;death;death and dying;dying=death and dying;near death experience;afterlife;heaven;illness;cancer;disease;
diseases=disease;medicine;medical=medicine;hospital;health;nutrition;diet;weight loss;fitness;exercise;running;yoga;meditation;mindfulness;
spirituality;spiritual=spirituality;religion;religious=religion;religious studies=religion;religion spirituality=religion and spirituality;
religion and spirituality;spirituality religion=religion and spirituality;philosophy religion=religion;religion philosophy=religion;
faith;christianity;catholic=catholicism;catholicism;jesus;bible;bibles=bible;god;theology;church;christian theology=theology;saints;
islam;muslim=islam;judaism;judaica=judaism;jewish=jewish life;jews=jewish life;jewish history;buddhism;zen=buddhism;hinduism;atheism;
mythology;greek mythology;norse mythology;egyptian mythology;myths=mythology;gods=mythology;angels;demons;vampires;werewolves;
shapeshifters;witches;witchcraft=witches;wizards;magic;ghosts;fairies;dragons;zombies;mermaids;aliens;robots;artificial intelligence;
ai=artificial intelligence;time travel;space;outer space=space;space exploration;astronomy;physics;chemistry;biology;evolution;genetics;
neuroscience;brain=neuroscience;psychology;cognitive science;economics;economy=economics;business;entrepreneurship;startups;leadership;
management;marketing;finance;personal finance;money;investing;productivity;habits;happiness;motivation;success;work=careers and work;
career=careers and work;careers=careers and work;careers and work;technology;tech=technology;computers;computer science;programming;
software;software development=software;software engineering=software;internet;social media;science;sciences=science;general science=science;
nature;environment;environmental=environment;environmentalism=environment;ecology;climate change;sustainability;sustainable living=sustainability;
conservation;animals;dogs;cats;horses;birds;wildlife;pets;dinosaurs;ocean;sea=ocean;plants;trees;gardening;food;cooking;baking;wine;
travel;exploration;mountaineering;mountain climbing=mountaineering;mountains;sailing;seafaring;survival;wilderness;outdoors;sports;
sport=sports;baseball;football;basketball;soccer;hockey;boxing;cycling;golf;tennis;olympics;martial arts;music;art;painting;photography;
film;movies=film;television;tv=television;dance;fashion;architecture;design;books about books=books and reading;books and reading;
reading=books and reading;libraries;writing;writing craft=writing;language;linguistics;family;family life;parenting;motherhood;
fatherhood;mothers;fathers;siblings;sisters;brothers;childhood;adolescence;coming of age;growing up=coming of age;school life;
high school=school life;college=college life;college life;university=college life;boarding school;friendship;friends=friendship;
love;marriage;divorce;infidelity;adultery=infidelity;cheating=infidelity;relationships;dating;sexuality;human sexuality=sexuality;
gender;women;womens studies=women;women s studies=women;womens issues=women;feminism;men;masculinity;lgbtq;gay=gay men;gay men;lesbian;
lesbians=lesbian;lesbianism=lesbian;homosexuality=lgbtq;bisexual;bisexuality=bisexual;transgender;gender identity;gender studies=gender;
gender bender=gender identity;race;racism;race relations;anti racism=antiracism;antiracism;civil rights;civil rights movement;
segregation;slavery;slaves=slavery;african american=african american life;african american life;black=black life;black history;
black authors=black life;black fiction=black life;black lit=black life;black studies=black life;black books=black life;diversity;
multicultural;multi cultural=multicultural;immigration;immigrants=immigration;immigrant experience=immigration;human migration=immigration;
refugees;identity;culture;native american=native americans;native americans;indigenous;first nations=indigenous;latino;latinx=latino;
hispanic=latino;asian american;colonialism;imperialism;postcolonial=colonialism;poverty;homelessness;social class;class issues=social class;
inequality;social justice;activism;human rights;disability;disabilities=disability;autism;asperger=autism;deaf;blindness;aging;old age=aging;
dementia;alzheimers=dementia;pregnancy;adoption;foster care;orphans;orphan=orphans;holocaust;nazis;nazi germany=nazis;nazism=nazis;
world war ii;world war i;american civil war;civil war;vietnam war;cold war;korean war;iraq war;afghanistan war;american revolution;
revolutionary war=american revolution;french revolution;russian revolution;napoleonic wars;wars of the roses;war of the roses=wars of the roses;
spanish civil war;crusades;genocide;great depression;cults;conspiracy;conspiracy theories;secret societies;pirates;knights;samurai;
ninjas;castles;christmas;holidays;holiday=holidays;halloween;thanksgiving;easter;seasons;weather;natural disasters;disasters;plague;
pandemic=epidemics and pandemics;pandemics=epidemics and pandemics;epidemic=epidemics and pandemics;epidemics=epidemics and pandemics;
epidemics and pandemics;viruses;virus=viruses;infectious disease;infectious diseases=infectious disease;hiv aids;vaccines;public health;
nuclear war;end of the world;utopia;utopian=utopia;philosophy;ethics;morality;existentialism;stoicism;logic;mathematics;math=mathematics;
maths=mathematics;statistics;history of science;inventions;engineering;transportation;trains;cars;aviation;ships;society;social science;
social sciences=social science;sociology;anthropology;archaeology;geography;cities;urban life;rural life;farming;agriculture;hunting;
fishing;crafts=crafts and hobbies;crafts and hobbies;knitting;quilting;sewing;hobbies=crafts and hobbies;games;video games;gaming=video games;chess;puzzles;circus;memory;
dreams;consciousness;loneliness;revenge;betrayal;redemption;forgiveness;hope;courage;secrets;power;corruption;greed;fame;celebrity;
entertainment;entertainment industry;kidnapping;missing persons;amnesia;superheroes;body image;beauty;shopping;self esteem;
personal growth=personal development;personal development;self improvement=personal development;inspiration=personal development;
education;teaching;learning;homeschooling;homeschool=homeschooling;child development;psychiatry;therapy;psychotherapy;psychoanalysis;
emotions;feelings=emotions;feeling=emotions;love and relationships=relationships;family and relationships;home and family=family life;
family relationships=family;family drama=family;dysfunctional family=family;dysfunctional families=family;health and fitness;
sports and recreation;sports and recreations=sports and recreation;performing arts;food and cooking;cooking and food=food and cooking;
food and wine=food and cooking;home design and decor=home and interior design;home and interior design;interior design=home and interior design;
home improvement;diy;outdoor recreation;camping;hiking;photography;antiques and collectibles;antiques=antiques and collectibles;
collectibles=antiques and collectibles;genealogy;media;media studies=media;journalism history=media;propaganda;language learning;
foreign language study=language learning;grammar=grammar and language usage;grammar and language usage;rhetoric;communication;
public speaking;negotiation;persuasion;sales;marketing and sales;sales and marketing=marketing and sales;advertising;real estate;
retirement;wealth;capitalism;socialism;communism;marxism;anarchism;fascism;totalitarianism;nationalism;liberty;freedom=liberty;
revolution;revolutions=revolution;protest;civil disobedience;peace;nonviolence;conflict resolution;negotiation;diplomacy;espionage history=intelligence agencies;
royal family;monarchy;kings and queens=monarchy;british royal family=royal family;aristocracy;nobility=aristocracy;empire;
ancient civilizations;civilization;humanity;human nature;evolution of humans=human evolution;human evolution;prehistory humans=human evolution;
medieval life;chivalry;knighthood=knights;exorcism;occult;paganism;wicca;astrology;tarot;new religious movements;mysticism;
kabbalah;sufism;meditation practice=meditation;prayer;miracles;miracle=miracles;angels and demons=angels;heaven and hell=afterlife;
first contact=aliens;alien invasion=aliens;ufos=ufos;ufo=ufos;unidentified flying object=ufos;alien abduction=ufos;cloning;
genetic engineering;transhumanism;cyborgs;virtual reality;surveillance;privacy;cybersecurity;hacking;hackers=hacking;
climate fiction=climate change;cli fi=climate change;global warming fiction=climate change;deforestation;pollution;oceans=ocean;
marine life;whales;sharks;insects;bees;wolves;bears;elephants;primates;apes=primates;monkeys=primates;cats and dogs=pets;
horse racing;rodeo;ranching;cowboy life=ranching;frontier;pioneers;pioneer life=pioneers;westward expansion=pioneers;gold rush;
shipwrecks;shipwrecking=shipwrecks;polar exploration;arctic exploration=polar exploration;antarctic exploration=polar exploration;
spaceflight=space exploration;space travel=space exploration;moon landing=space exploration;nasa=space exploration;mars;
planets;universe;cosmology;quantum physics;relativity;mathematics history=history of science;medical history=medicine;
history of medicine=medicine;doctors and medicine=medicine;nursing;hospitals=hospital;surgery;emergency medicine;
aids epidemic=hiv aids;influenza;spanish flu=influenza;smallpox;tuberculosis;ebola;malaria;outbreaks=epidemics and pandemics;
outbreak=epidemics and pandemics;contagion=epidemics and pandemics;quarantine=epidemics and pandemics;covid=covid 19;covid 19;
coronavirus=covid 19;lockdown=covid 19'''
THEMES = {}
for item in THEME_LIST.replace('\n', '').split(';'):
    item = item.strip()
    if not item:
        continue
    if '=' in item:
        a, b = item.split('=', 1); THEMES[a.strip()] = b.strip()
    else:
        THEMES[item] = item

# very broad theme values: kept at the broad or middle level, never used as narrow nodes
GENERAL_THEMES = {'history', 'politics', 'science', 'religion', 'religion and spirituality', 'spirituality', 'philosophy', 'psychology',
                  'family', 'family and relationships', 'relationships', 'love', 'nature', 'animals', 'health', 'health and fitness',
                  'medicine', 'medical', 'art', 'music', 'sports', 'sports and recreation', 'travel', 'food', 'food and cooking',
                  'business', 'economics', 'technology', 'education', 'law', 'crime', 'society', 'sociology', 'social science',
                  'culture', 'war', 'military', 'performing arts', 'current events', 'personal development', 'women', 'faith',
                  'entertainment', 'humanity', 'emotions', 'environment', 'finance', 'death'}

# ---------------------------------------------------------------- SPL (OverDrive) subject terms: complete hand decomposition
def _c(s):
    out = []
    for part in s.split('+'):
        f, v = part.split(':', 1); out.append((f.strip(), v.strip()))
    return out

SPL_TERMS = {k: _c(v) for k, v in {
    'Fiction': 'form:fiction', 'Nonfiction': 'form:nonfiction', 'Literature': 'form:literature', 'Romance': 'genre:romance',
    'Thriller': 'genre:thriller', 'Mystery': 'genre:mystery', 'Fantasy': 'genre:fantasy', 'Historical Fiction': 'genre:historical fiction',
    'Suspense': 'genre:suspense', 'Juvenile Fiction': 'audience:children+form:fiction',
    'Biography & Autobiography': 'genre:biography+genre:memoir', 'Science Fiction': 'genre:science fiction',
    'Humor (Fiction)': 'genre:humor+form:fiction', 'Young Adult Fiction': 'audience:young adult+form:fiction', 'History': 'theme:history',
    'Self-Improvement': 'genre:self-help+theme:personal development', 'Juvenile Literature': 'audience:children+form:literature',
    'Sociology': 'theme:sociology', 'Business': 'theme:business', 'Psychology': 'theme:psychology',
    'Young Adult Literature': 'audience:young adult+form:literature', 'Politics': 'theme:politics',
    'Classic Literature': 'genre:classics+form:literature', 'Science': 'theme:science', 'Family & Relationships': 'theme:family and relationships',
    'Health & Fitness': 'theme:health and fitness', 'Short Stories': 'form:short stories', 'Religion & Spirituality': 'theme:religion and spirituality',
    'Cooking & Food': 'theme:food and cooking', 'Horror': 'genre:horror', 'Humor (Nonfiction)': 'genre:humor+form:nonfiction',
    'New Age': 'genre:new age+theme:spirituality', 'Essays': 'form:essays', 'Mythology': 'theme:mythology',
    'LGBTQIA+ (Fiction)': 'theme:lgbtq+form:fiction', 'Nature': 'theme:nature', 'African American Fiction': 'theme:african american life+form:fiction',
    'Travel': 'theme:travel', 'Comic and Graphic Books': 'form:comics and graphic novels', 'Erotic Literature': 'genre:erotica',
    'Performing Arts': 'theme:performing arts', 'Philosophy': 'theme:philosophy', 'Medical': 'theme:medicine', 'Military': 'theme:military',
    'Sports & Recreations': 'theme:sports and recreation', 'True Crime': 'genre:true crime+theme:crime',
    'Juvenile Nonfiction': 'audience:children+form:nonfiction', 'Literary Criticism': 'genre:literary criticism',
    'Picture Book Fiction': 'audience:children+form:picture book+form:fiction', "Women's Studies": 'theme:women', 'Economics': 'theme:economics',
    'African American Nonfiction': 'theme:african american life+form:nonfiction', 'Science Fiction & Fantasy': 'genre:science fiction+genre:fantasy',
    'Reference': 'form:reference', 'Self Help': 'genre:self-help+theme:personal development', 'Folklore': 'genre:folklore and fables',
    'Technology': 'theme:technology', 'Western': 'genre:western', 'Finance': 'theme:finance', 'Beginning Reader': 'audience:children+form:early reader',
    'Art': 'theme:art', 'Language Arts': 'theme:language', 'Education': 'theme:education', 'Poetry': 'form:poetry',
    'Home Design & Décor': 'theme:home and interior design', 'Computer Technology': 'theme:computers', 'Christian Fiction': 'genre:christian fiction+theme:christianity',
    'Music': 'theme:music', 'Foreign Language Study': 'theme:language learning', 'Crafts': 'theme:crafts and hobbies',
    'Christian Nonfiction': 'genre:christian nonfiction+theme:christianity', 'Drama': 'form:drama', 'Multi-Cultural': 'theme:multicultural',
    'Law': 'theme:law', 'Careers': 'theme:careers and work', 'Contemporary Romance': 'genre:contemporary romance', 'Pets': 'theme:pets',
    'Young Adult Nonfiction': 'audience:young adult+form:nonfiction', 'Gardening': 'theme:gardening', 'LGBTQIA+ (Nonfiction)': 'theme:lgbtq+form:nonfiction',
    'Mathematics': 'theme:mathematics', 'Architecture': 'theme:architecture', 'Literary Anthologies': 'form:anthology', 'Writing': 'theme:writing',
    'Gay/Lesbian': 'theme:lgbtq', 'Study Aids & Workbooks': 'form:textbook', 'Management': 'theme:management', 'Geography': 'theme:geography',
    'Transportation': 'theme:transportation', 'Games': 'theme:games', 'Entertainment': 'theme:entertainment', 'Physics': 'theme:physics',
    'Photography': 'theme:photography', 'Historical Romance': 'genre:historical romance', 'Non-English Fiction': 'form:fiction+other:language',
    'Psychiatry': 'theme:psychiatry', 'Engineering': 'theme:engineering', 'Classic Romance': 'genre:romance+genre:classics', 'Passion': 'genre:romance',
    'Paranormal Romance': 'genre:paranormal romance', 'Children': 'audience:children', 'Media Studies': 'theme:media',
    'Picture Book Nonfiction': 'audience:children+form:picture book+form:nonfiction', 'Current Events': 'theme:current events',
    'Chick Lit Fiction': 'genre:chick lit+form:fiction', 'Chemistry': 'theme:chemistry', 'Judaica': 'theme:judaism', 'Ethics': 'theme:ethics',
    'Teen': 'audience:young adult', 'Relationship Novel': 'genre:romance', 'Travel Literature': 'genre:travel writing+theme:travel',
    'Foreign Language': 'theme:language learning', 'Grammar & Language Usage': 'theme:grammar and language usage', 'Gender Studies': 'theme:gender',
    'Marketing & Sales': 'theme:marketing and sales', 'Sales & Marketing': 'theme:marketing and sales', 'Antiques': 'theme:antiques and collectibles',
    'Erotic Fiction': 'genre:erotica+form:fiction', 'Urban Fiction': 'genre:urban fiction', 'African-American': 'theme:african american life',
    'Outdoor Recreation': 'theme:outdoor recreation', 'Crime': 'theme:crime', 'Heart & Home': 'genre:romance',
    'Psychiatry & Psychology': 'theme:psychology+theme:psychiatry', 'Non-English Nonfiction': 'form:nonfiction+other:language',
    'Human Rights': 'theme:human rights', 'LGBTQIA+': 'theme:lgbtq', 'Design & UI': 'theme:design',
    'Inspirational Romance': 'genre:christian fiction+genre:romance', 'Professional': 'theme:careers and work', 'Biology': 'theme:biology',
    'Recovery': 'theme:addiction and recovery', 'Analysis': 'genre:literary criticism', 'Journalism': 'genre:journalism+theme:media',
    'Chick Lit': 'genre:chick lit', 'Research': 'genre:academic', 'Fitness and Diet': 'theme:health and fitness', 'Health': 'theme:health',
    'Inspirational': 'genre:inspirational', 'Child Development': 'theme:child development', 'Criticism': 'genre:literary criticism',
    'Genealogy': 'theme:genealogy', 'Scholarly': 'genre:academic', 'Holiday': 'theme:holidays', 'Erotic Romance': 'genre:erotic romance',
    'Food and Wine': 'theme:food and cooking', 'Cooking': 'theme:food and cooking', 'Romantic Suspense': 'genre:romance+genre:suspense',
    'Self-Help': 'genre:self-help+theme:personal development', 'Antiquarian': 'theme:antiques and collectibles', 'Home and Family': 'theme:family life',
    'Social Studies': 'theme:society', 'Relationships': 'theme:relationships', 'Historical': 'genre:historical fiction',
    'Environment': 'theme:environment', 'Biography and Memoir': 'genre:biography+genre:memoir', 'Feminist': 'theme:feminism',
    'Comedy': 'genre:humor', 'Male/Male': 'genre:romance+theme:gay men', 'Regency': 'genre:historical romance+period:regency era',
    'Family and Parenting': 'theme:parenting', 'Post Apocalyptic': 'genre:post-apocalyptic', 'Informational': 'form:nonfiction',
    'Ancient History': 'theme:history+period:ancient world', 'Fun and Games': 'theme:games', 'Songbook': 'form:sheet music',
    'Music-Sheet': 'form:sheet music', 'Romance with More': 'genre:romance',
}.items()}
for _lang in ['Spanish', 'French', 'Italian', 'Japanese', 'German', 'Russian', 'Portuguese', 'Chinese', 'Korean', 'English', 'Vietnamese', 'Latin']:
    SPL_TERMS[f'Foreign Language Study - {_lang}'] = [('theme', 'language learning'), ('other', 'language')]
SPL_TERMS['Chick Lit Nonfiction'] = [('genre', 'chick lit'), ('form', 'nonfiction')]

# ---------------------------------------------------------------- title matching (nonfiction titles only)
# Extra surface forms used only when matching theme words in nonfiction titles and subtitles.
TITLE_SURFACES = {
    'plague': ['pandemic', 'pandemics', 'epidemic', 'epidemics', 'plague', 'plagues', 'influenza', 'virus', 'viruses', 'outbreak',
               'outbreaks', 'contagion', 'quarantine', 'coronavirus', 'covid', 'covid 19', 'spanish flu', 'ebola', 'infectious disease'],
    'racism': ['racism', 'racist', 'racists', 'antiracist', 'anti racist', 'antiracism', 'racial', 'race relations', 'white supremacy', 'about race'],
    'sexual violence': ['rape', 'sexual assault', 'sexual violence', 'sexual abuse', 'sexual harassment', 'harassment', 'metoo', 'sexual consent'],
    'climate change': ['climate', 'global warming', 'climate change', 'warming'],
    'grief': ['grief', 'grieving', 'mourning', 'bereavement'],
}
# single words too often used loosely in titles to count as theme evidence
TITLE_STOP = {'magic', 'change', 'space', 'secrets', 'money', 'memory', 'dreams', 'night', 'water', 'energy', 'games', 'beauty',
              'design', 'media', 'identity', 'culture', 'justice', 'liberty', 'peace', 'happiness', 'wisdom', 'kindness', 'strategy',
              'survival', 'revenge', 'betrayal', 'forgiveness', 'heaven', 'monsters', 'ghosts', 'angels', 'demons', 'dragons', 'trees',
              'seasons', 'winter', 'circus', 'heist', 'teaching', 'learning', 'writing', 'language', 'information', 'knowledge',
              'planning', 'trivia', 'cities', 'community', 'mindset', 'motivation', 'success', 'acceptance', 'suffering', 'healing',
              'courage', 'secrets', 'power', 'prayer', 'miracles', 'virtue', 'ethics', 'logic', 'imagination', 'creativity', 'time',
              'friendship', 'dating', 'marriage', 'divorce', 'weddings', 'fashion', 'dance', 'opera', 'music', 'drawing', 'painting',
              'photography', 'television', 'celebrity', 'comedians', 'acting', 'storytelling', 'journaling', 'organizing', 'lifestyle',
              'productivity', 'innovation', 'leadership', 'management', 'marketing', 'sales', 'investing', 'banking', 'wealth', 'capitalism',
              'trade', 'labor', 'aging', 'childhood', 'adolescence', 'parenting', 'motherhood', 'sisters', 'brothers', 'siblings', 'orphans',
              'pioneers', 'knights', 'castles', 'monarchy', 'pirates', 'aliens', 'robots', 'vampires', 'zombies', 'witches', 'fairies',
              'mythology', 'cooking', 'baking', 'coffee', 'gardening', 'farming', 'plants', 'birds', 'insects', 'horses', 'wolves', 'bears',
              'fish', 'sharks', 'ocean', 'sailing', 'swimming', 'running', 'walking', 'hiking', 'fitness', 'exercise', 'nutrition', 'diet',
              'drugs', 'disease', 'illness', 'trauma', 'violence', 'murder', 'prison', 'police', 'corruption', 'conspiracy', 'revolution',
              'government', 'democracy', 'activism', 'diversity', 'immigration', 'slavery', 'poverty', 'disability', 'autism', 'cancer'}
# title patterns that use a theme word loosely; the listed value is not assigned when the title matches
TITLE_NEGATIVE = {
    'plague': [r'\bepidemic of\b', r'\b(opiate|opioid|drug|addiction|loneliness|obesity|wellness|overdose|kidnapping|gun|violence|suicide|crime) epidemic\b',
               r'\bplague of\b'],
    'depression': [r'\bdepression era\b', r'\bthe depression\b'],
    'anatomy': [r'\banatomy of\b'], 'architecture': [r'\barchitecture of\b'], 'abuse': [r'\babuse of\b'],
    'literacy': [r'\b(religious|financial|media|data|emotional|racial|cultural|digital|science|scientific) literacy\b'],
    'coming of age': [r'\bgrowing up (brave|with|in the|on|fast|global)\b', r'\bhelp(ing)? your child\b'],
    'evolution': [r'\bevolution (angel|of (a|an|the|my|your|our))\b'],
    'bible': [r'\b(pocket|wine|cook|cooking|baking|garden|gardening|knitting|business|marketing|writers|style|photography|food|beer|whisky|cocktail|crochet|sewing|quilting) bible\b'],
    'exploration': [r'\bexploration of\b'], 'hunting': [r'\bhunting (for|the|down|nature)\b', r'\b(treasure|ghost|house|job|bargain|fossil) hunting\b'],
    'sexual violence': [r'\bmanufacturing consent\b'],
    'holocaust': [r'\bmedical holocaust\b'],
}
