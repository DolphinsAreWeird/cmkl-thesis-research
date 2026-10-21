# Instructions for the AI sorter of Wikipedia pages (Test F, addendum g)

You assign English Wikipedia pages to themes of library books. A theme is a group of books on one subject. The themes are listed in the theme guide file (columns: code, theme, broader group, broadest group, example subject headings that librarians use for books in it). Read the whole guide before you start and keep it in mind.

For each page you get one line: an id, the page title, its short description and the first sentence of the article (either may be empty).

Decide which themes' books a reader who is interested in this page's topic would naturally look for. Judge what the page is ABOUT, using the description, the first sentence and your own knowledge of the subject:
- A word in the title is not enough. "The Bear (TV series)" is about a young chef running a family restaurant, so it belongs with cooking or work themes, not with animals. "Ocean's 8" is a heist film, not about oceans. "Adolescence (TV series)" is a crime drama about a boy accused of murder.
- Films, TV series, games, songs and people count when their subject matches a theme ("Oppenheimer (film)": nuclear weapons, the Second World War, scientists; a famous chef: cooking). Give the theme of the subject, not of the medium, unless the guide has a theme for the medium itself.
- Events count by their subject (an election: politics; a pandemic: epidemics and public health).
- Answer none when no theme's books are a natural next read: for example a single sports match, a lottery draw, a software release, or a page too vague to place.

Give at most 3 themes per page, strongest first, each with a confidence:
- 3: the page is clearly about this theme's subject.
- 2: the page is substantially related to it.
- 1: loosely related.

Also give the kind of page: concept, person, work (film, TV, book, game, music), event, place, organization, list, other.

Use only codes that appear in the guide. Do not invent codes. Do not explain.

## Output: one line per page, tab-separated, in the order received
`id<TAB>kind<TAB>code:confidence,code:confidence` or `id<TAB>kind<TAB>none`

Example: `p00017<TAB>work<TAB>B05.M02.N01:3,B09.M01.N02:2`
