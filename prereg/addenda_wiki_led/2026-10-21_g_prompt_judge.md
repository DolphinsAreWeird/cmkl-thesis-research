# Instructions for the independent judge of page-to-theme sorting (Test F, addendum g, check G1)

You are checking how well Wikipedia pages were assigned to themes of library books. You did not make the assignments. Read the theme guide file (code, theme, broader group, broadest group, example subject headings) in full.

For each page you get: an id, the title, the short description and the first sentence. Work slowly and carefully, one page at a time. Look up nothing; use the text given and your own knowledge.

For each page decide:
1. What the page is about, in a few words.
2. The themes whose books a reader interested in this topic would naturally look for: up to 3 codes, strongest first, or none.
3. Whether the title contains a word that could mislead a word-matching method (for example "The Bear" for a TV series about a chef): yes or no.

Use only codes in the guide.

## Output: one line per page, tab-separated
`id<TAB>about<TAB>code,code,code or none<TAB>misleading_title: yes|no`
