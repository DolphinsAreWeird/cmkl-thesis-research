# Conversation sources review: where can we measure what people talk about, by topic, week by week?

Khant Phyo Wai, CMKL University, honors thesis
Prepared 14 October 2026 from live documentation, terms and pricing pages (all read on that date; list at the end). Status: for Khant's review. Nothing here has been collected; the only data touched were single test calls to public, no-login APIs, listed in section 3.

## 1. Summary table

| Source | What it measures | Usable history from | Access today | Cost | Terms allow our research? | Verdict |
|---|---|---|---|---|---|---|
| TweetsKB (English tweets, 1% sample, with Wikipedia entities and tone) | Conversation (counts and tone; no text) | Feb 2013 to Jun 2023 | Public SPARQL endpoint (5% sample); monthly files on Zenodo and GESIS | Free | Yes (CC BY 4.0; 2021-23 parts: non-commercial research) | USE NOW |
| Wikipedia talk pages and edits | Writing and arguing about a topic | 2001 | Wikimedia REST API, no key | Free | Yes | USE NOW |
| Stack Exchange (Literature, History, SciFi and others) | Questions | 2009-2017, by site | API, no login (free key for more quota) | Free | Yes (CC BY-SA, attribution) | USE NOW |
| Hacker News | Conversation (tech crowd) | 2007 | Algolia search API, no key | Free | Yes through the APIs; site scraping banned | USE NOW (side series) |
| AO3 fan fiction | Creation (new works per fandom and theme tag) | 2008 to Feb 2021 (official dump) | One-time official CSV dump, 417 MB | Free | Yes (only commercial scraping banned) | USE NOW (needs download OK) |
| Tumblr | Posts by tag | 2007 | API, key in hand | Free | Yes | USE NOW (continue) |
| Bluesky | Conversation | 2023, thin before Nov 2024 | Jetstream open; search needs a login | Free | Yes; honour deletions | USE NOW forward; LATER for backfill |
| YouTube | Video creation and comments | Comments go back to each video's upload | Data API; Researcher Program | Free | Yes, within API terms | APPLY (in progress) |
| Meta Content Library (Facebook, Instagram, Threads) | Conversation in public posts | Not documented ("all time" search) | Application in Meta Research Tools Manager, reviewed by CASD | Free in Meta's cleanroom | Yes, for approved projects | APPLY |
| Reddit for Researchers | Conversation | Rolling 5 years, 6-month lag (about Apr 2021 on) | Application with ethics letter and sponsor | Free | Yes, under Researcher Terms | APPLY |
| Reddit Data API | Conversation | n/a | Approval needed since Nov 2025 | Free | Non-commercial only | NO (use the program above) |
| Pushshift / Arctic Shift dumps | Conversation | 2005-2025 | Torrents | Free | No (Reddit policy) | NO |
| X API, counts only | Conversation volume | 2006 | Pay-per-use, USD 0.01 per 31-day request | About USD 1.31 per query for 2016-2026 | Gray: research allowed, but one clause on aggregate metrics | LATER (paid; decide) |
| Internet Archive Twitter Stream Grab | Raw tweets (1% sample) | 2011 to Jan 2023 | 130 items, 7.5 TB | Free | No licence; X terms | NO |
| Threads API keyword search | Conversation | Jul 2023 | Meta app review | Free | Yes, once approved | LATER |
| Mastodon | Conversation | 2016, tiny before Nov 2022 | Per-server API; search is opt-in | Free | Varies by server | LATER |
| Pantip (Thai) | Conversation and questions | Late 1990s | No public API; data licensed to certified partners | Unknown | Ask first | APPLY (written permission) |
| Google Trends API | Attention (searches) | Rolling 5 years (about Oct 2021 on) | Alpha application, already sent | Free | Yes | APPLY (waiting) |
| Podcast Index | Creation (new episodes) | Feed-dependent | Free key | Free | Yes | LATER |
| Common Crawl | Web pages (forums mixed in) | 2008 | Open files | Free, heavy compute | Yes, plus each site's terms | LATER |
| TikTok Research API | Video creation | n/a | Not open to Thai institutions | Free | Eligible regions only | NO |
| Quora | Questions | n/a | No API; robots.txt blocks all bots | n/a | No | NO |
| Goodreads, StoryGraph, LibraryThing groups | Book talk | n/a | No open API | n/a | No or unclear | NO |
| Lemmy, Telegram, Discord, Twitch, Pinterest | Various | Short or none | No suitable route | n/a | Mostly no | NO |
| Medium, Substack, Fandom wikis | Writers' posts, wiki edits | n/a | API closed or robots banned | n/a | No | NO |
| News comments (Guardian, NYT) | Comments | n/a | Not offered (Guardian) or deprecated (NYT) | n/a | n/a | NO |

## 2. Recommendations (in order)

### 2.1 TweetsKB: English Twitter conversation 2013 to mid 2023, already linked to Wikipedia (USE NOW)
What it adds beyond Wikipedia and YouTube: posts written by ordinary people (not reading), with a tone score, with history that covers all three fixed positive controls (#MeToo 2017-10, COVID-19 2020-03, race and racism 2020-06). Mentions are linked to the same Wikipedia articles our pageview series uses, so no new topic mapping is needed. A single test query (section 3) showed tweets about Racism in the 5% sample going from 2,358 in January 2020 to 14,264 in June 2020.

Next steps:
1. Write `code/tweetskb_counts.py`: for each Wikipedia article already mapped to a category, ask the SPARQL endpoint for weekly mention counts and the mean positive and negative sentiment, one query per article per year, one query every 3 seconds, project User-Agent, cached results, resume on restart.
2. Add one query per week for all tweets in the sample, so each category is a share of the week's total.
3. First check, before the full run: confirm that the 5% sample covers 2021 to June 2023 as well as 2013-2020 (the page says the corpus runs to June 2023; the sample's coverage was not tested, to keep to one test call).
4. Put dummies at the dates where the entity linker was re-run on a newer Wikipedia (April 2018 and January 2021, and September 2022) and check for level shifts there.
5. Only if small categories are too thin in the 5% sample: stream the full monthly files one at a time (download, count, delete). That needs Khant's permission per download (3 to 5 GB per month; about 219 GB for 2016-2020 on Zenodo, plus the 2021-2023 parts on GESIS).
6. Out of courtesy, email the TweetsKB team before running a few thousand queries.

### 2.2 Wikipedia talk-page and edit activity (USE NOW)
What it adds: a "writing" signal next to the "reading" signal. Page views say people looked; talk-page and article edits say people argued about the topic. Same pages, same API family, no key. Test: Talk:Racism had 1 to 19 edits a month in early 2020 and 64 in June 2020.

Next steps:
1. Extend the pageview script to call `metrics/edits/per-page/{project}/{page}/user/daily/{start}/{end}` for each mapped article and its `Talk:` page (`user` drops bot edits).
2. Sum by category and week. Keep counts only; this API returns no editor names.
3. Run it for English and Thai Wikipedia (Thai will be small).

### 2.3 Stack Exchange questions and Hacker News discussion, 2016 to now (USE NOW)
What they add: series that keep going after TweetsKB stops in mid 2023, with exact counts and no sign-up. Stack Exchange gives questions people ask by topic (Literature, Science Fiction and Fantasy, Writing for books; History, Politics, Philosophy, religion sites, Law, Health, Parenting for themes). Hacker News gives a tech crowd's discussion. Both are small and narrow, so they are side series, not main inputs.

Next steps:
1. Stack Exchange: for each chosen site, page through `/2.3/questions` with a custom filter that keeps only creation date, tags and title (no owner fields); bin by week; map tags to categories by hand (Khant reviews the tag map like the categories). A free Stack Apps key (Khant registers) raises the quota to 10,000 calls a day; without it the job takes about a week.
2. Hacker News: for each category, one OR-query of its terms per week to `search_by_date` with `hitsPerPage=0`, reading `nbHits`; about 1 request a second.
3. Before using either, plot each site's total weekly volume; Stack Exchange question numbers have been falling since about 2023, so use shares within a site, not raw counts.

### 2.4 AO3 official dump: fan works per book fandom and per theme tag, 2008 to February 2021 (USE NOW after download OK)
What it adds: creative engagement by readers and viewers, the closest of all these sources to reading itself. Fandom tags cover book series and classics; free-form tags cover themes (for example racism, pandemics, grief). History covers 2016 to early 2021, including two positive controls.

Next steps:
1. Khant approves the download (file below), saved under `data/raw/ao3/`.
2. Count new works per week per canonical fandom tag and per canonical free-form tag; map tags to categories (Khant reviews).
3. Remove known bulk-import spikes (archives moved into AO3 on one day) before use.
4. AO3 after February 2021 stays LATER: possible only from public tag pages, under the scraping checklist.

### 2.5 Two applications with Dr. Fawad: Meta Content Library and Reddit for Researchers (APPLY)
What they add: by far the largest pools of public conversation. Meta is the only route to Thai social conversation at scale (Facebook is the main Thai platform). Reddit has topic communities about books (r/books, r/suggestmeabook, r/audiobooks) and themes (r/AskHistorians and many more).

Meta Content Library, next steps:
1. Dr. Fawad applies as lead researcher in Meta Research Tools Manager (needs a Meta account), names Khant as collaborator; Khant then accepts the invitation and applies as collaborator. CASD reviews; no fee in Meta's own Secure Research Environment. No review time is published.
2. In the proposal, ask for the web tool's keyword trend graphs and the API, describe outputs as weekly counts by category, with no account-level data leaving the environment.
3. At onboarding, check the earliest date the search covers and whether trend counts can be exported as aggregates.

Reddit for Researchers, next steps:
1. Get a CMKL ethics approval or exemption letter for analysis of public posts (Dr. Fawad will know who issues it).
2. Khant applies with his CMKL email through Reddit's help ticket form, role "researcher", with Dr. Fawad's CMKL email as sponsor, a proposal naming the subreddits, and links to any prior work.
3. If approved: access for up to one year, queries in BigQuery Analytics Hub, all Reddit data deleted at the end, preprint sent to Reddit. Weekly counts per subreddit and keyword would be the only export.
4. Limitation to state up front: the data window is the last five years with a six-month lag, so 2020 is not covered.

Also worth a decision (not in the top five):
- X counts endpoint (paid, about USD 1.31 per keyword query for daily counts 2016-2026; counts only, no posts). It is the only route to full-population conversation counts through 2026, including Thai (`lang:th`). Needs Khant to open an X developer account, accept the Developer Agreement and buy credits. The project's ethics file currently lists X as excluded; this is a choice for Khant and Dr. Fawad.
- Pantip written permission for Thai (section 4.17).

## 3. Test calls made today (one per API, public and no login)

| Call | Result |
|---|---|
| TweetsKB SPARQL: monthly tweets mentioning dbr:Racism in 2020 (5% sample) | Jan 2,358; Feb 1,947; Mar 2,556; Apr 2,320; May 5,351; Jun 14,264; Jul 6,448; Aug 5,306; Sep 4,417; Oct 3,934; Nov 3,604; Dec 2,430. Answer in 2.6 s |
| Wikimedia edits per page, Talk:Racism, monthly 2020 | Jan 19, Feb 3, Mar 1, Apr 4, May 9, Jun 64, Jul 8, Aug 4, Sep 44 |
| Hacker News Algolia: stories and comments containing "racism", June 2020 | 1,699 (exact count) |
| Stack Exchange API: Literature questions created in 2020 | 1,129 |
| Bluesky public search (public.api.bsky.app searchPosts) | HTTP 403 without login |
| Internet Archive search, collection twitterstream | 130 items, 7.47 TB, 2011 to January 2023, no licence field |
| Zenodo records API, TweetsKB parts | Parts 1-9 open, CC BY 4.0; Parts 10-11 restricted on Zenodo but free on GESIS |
| AO3 dump, HEAD request only (no download) | 437,117,255 bytes, dated 21 Mar 2021 |

The first four all rise in June 2020, which matches the race and racism control. This is an informal look, not the pre-registered positive-control test.

## 4. Source by source

Each source answers the same seven points: (1) what it measures, (2) history, (3) access, (4) terms and ethics, (5) fit, (6) effort and size on the 8-core, 8 GB Mac, (7) verdict.

### 4.1 TweetsKB (GESIS and L3S Research Center)
1. Conversation. English tweets from Twitter's public 1% sample stream, with retweets removed and spam filtered out. For each tweet: date, linked Wikipedia/DBpedia entities, hashtags, and positive and negative sentiment scores (SentiStrength). No tweet text; user IDs are encrypted.
2. February 2013 to June 2023 (collection ended when Twitter closed its API). Weekly series are possible.
3. Public SPARQL endpoint holding a 5% sample of the corpus, no login. Full monthly N3 files: Zenodo for Parts 1-9 (to December 2020), GESIS for Parts 10-12 (2021 to June 2023), "free access (without registration)". No approval wait. No published rate limit, so keep to one query every few seconds.
4. Zenodo parts: CC BY 4.0. GESIS parts: "Data can only be used for non-commercial research". There is no text and no real user ID, so nothing has to be dropped. Weekly counts can be published with attribution.
5. Volume is ample for broad themes (test above). Users are Twitter users in English, so the sample leans to the US, younger and more political people. The entity linker finds 86% correct links but only 39% of all mentions (paper's evaluation), so counts are undercounts, consistent over time except at linker re-runs (Wikipedia dumps of November 2015 for Parts 1-6, April 2020 for 7-9, August 2022 or June 2023 for 10-12). Collection by mapping each category to its Wikipedia articles, which the project already has.
6. About 2.6 s per query; 500 articles over 8 years is about 4,000 queries, 3 to 4 hours, under 50 MB of results. Full files would be about 219 GB for 2016-2020 alone (3 to 5 GB per month), streamed and deleted month by month over several days.
7. USE NOW.

### 4.2 Wikipedia talk pages and edit activity
1. Editing and talk-page discussion by volunteer editors; writing activity, not reading.
2. 2001 to now, daily.
3. Wikimedia Analytics REST API (`metrics/edits/per-page`), no key, User-Agent required, same etiquette as the pageview calls. Full edit history dumps also exist but are not needed.
4. Official API for public data. Per-page counts carry no editor names.
5. Counts per page are small (test above), so sum across a category's pages. Editors are a narrow group (mostly experienced volunteers, English Wikipedia dominant). Edit wars and vandalism create spikes that are not public interest; use the `user` editor type to drop bots, and compare talk and article edits.
6. One call per page; about 5,000 pages is under 2 hours at 1 request a second; under 100 MB.
7. USE NOW.

### 4.3 Stack Exchange (API and data dumps)
1. Questions (and answers) asked by enthusiasts, organised into topic sites and tags.
2. Each site from its launch (Science Fiction and Fantasy and History from 2011, Literature from 2017) to today; the API serves full history.
3. API v2.3 without login. With a free app key from Stack Apps, 10,000 requests a day per IP; without a key the quota is lower (not stated on the throttle page). Data dumps: since July 2024 the official route is per-site, after logging in and accepting an agreement that bars LLM training; volunteers still mirror them on the Internet Archive (latest 2025-12-31), and the 2025-06-30 official dump contained watermark posts. The API is enough for us.
4. Content is CC BY-SA; the API terms ask for attribution and set no research limits. Keep date, tags and title words; use a filter that leaves out owner fields.
5. Literature had 1,129 questions in 2020 (test), so per-category weekly counts will be small; fine for broad themes on History, Politics, Philosophy, religion sites, Law, Health and Parenting. Users are English speaking and lean technical and male. Volume appears to have fallen across the network since about 2023 (check each site's totals first), so use within-site shares. Collection: full question metadata per chosen site, then tags and titles mapped to categories.
6. A few thousand calls; under 200 MB.
7. USE NOW.

### 4.4 Hacker News
1. Conversation (stories and comments) among people in software and startups.
2. 2007 to now.
3. Algolia search API (no key; `search_by_date` with date filters returns an exact `nbHits`), the official Firebase API ("no rate limit" per its README), and a BigQuery public table (Google describes it as 2006 to present; it would use the same 1 TB a month free quota as GDELT, so Algolia is the better route).
4. Y Combinator's site terms ban scraping the website itself, so use only the APIs. Keep counts, not usernames.
5. 1,699 items mentioned racism in June 2020. Book talk exists ("Ask HN" reading threads) but is small. Very narrow audience: tech workers, mostly US, mostly male.
6. 100 categories over 560 weeks is 56,000 count calls, about 16 hours at 1 request a second; tiny output.
7. USE NOW, as a side series.

### 4.5 AO3 (Archive of Our Own)
1. Creation activity: fan works posted, with fandom tags (books, films, TV) and free-form theme tags.
2. Official dump: works from 2008 to 26 February 2021. Nothing official after that.
3. One-time dump posted by the Organization for Transformative Works on 21 March 2021 for "students, scholars" and fan statisticians. works.csv: creation date, language, word count, restricted or not, complete or not, tag IDs. tags.csv: tag ID, type, name (hidden if under 5 uses), canonical or not, approximate uses, merger ID. No account needed.
4. Terms (effective 19 November 2024) ban scraping "in order to commercialize" content; research use of the dump is what it was released for. The dump has no author fields. robots.txt disallows `/works?` and search pages for all bots, so any later extension must stick to allowed paths.
5. Strong for fiction (book fandoms such as Sherlock Holmes or Harry Potter) and for themes as free-form tags. Writers are mostly young and mostly women and non-binary fans, writing in English; TV and anime fandoms dominate counts. Bulk imports of older archives create one-day spikes (reported by an independent analysis), which need removing.
6. Download 417 MB (437,117,255 bytes); a few GB unzipped; chunked reading fits in 8 GB; under an hour.
7. USE NOW (dump), once Khant approves the download. Extension after 2021: LATER.

### 4.6 Tumblr
1. Posts and reblogs by tag.
2. From 2007; the tagged endpoint pages back in time with a `before` timestamp.
3. Official API with the existing key: 1,000 calls an hour and 5,000 a day per key.
4. Used under the API licence agreement; keep tag, date and counts only.
5. Young, US-heavy, fandom-heavy users; good for fiction and identity themes, thin for others.
6. Current weekly-count method is light.
7. USE NOW (continue as planned).

### 4.7 Bluesky
1. Conversation.
2. Invite-only from early 2023, open to the public from February 2024, large growth from late 2024. Little usable volume before then.
3. Jetstream (open, no key) for posts going forward, already sampled daily. Past posts: `searchPosts` with `since` and `until` works only when logged in (the public endpoint returned 403 today), so it would need Khant's account and an app password; logged-in requests are limited to 3,000 per 5 minutes per IP. Other routes: full repository download through the relay (a 2024 study took 10 days for 5.5 million accounts; the network is now several times larger), the OSoMe archive at Indiana University (firehose from August 2023; "Day 1" archive November 2022 to April 2024; contains personal identifiers; access on request for academic researchers), and the Failla and Rossetti dataset on Zenodo (235 million posts from 4 million users up to early 2024, 22 GB, open access but no licence stated).
4. Terms of Service (updated 14 August 2025) say nothing about research; the developer guidelines require "a method for deleting content a user has requested to be deleted", so we must act on delete events and keep no DIDs or handles (current practice).
5. Book talk exists but most volume is 2024 on. Users are people who moved off X, not a general sample.
6. Current sampler is light. A search backfill per category per week is feasible for narrow terms, heavy for broad ones.
7. USE NOW (continue forward collection). LATER: 2023-2026 backfill through search or a request to OSoMe.

### 4.8 YouTube Data API and Researcher Program
1. Video creation (uploads matching a topic) and comments.
2. Comments: `commentThreads.list` returns every surviving comment on a video, ordered by time, with no date filter; so history goes back to the video's upload, minus deleted comments. Video search accepts `publishedAfter` and `publishedBefore`.
3. Standard quota: 10,000 units a day plus a separate bucket of 100 `search.list` calls a day (quota page updated 8 October 2026). The Researcher Program is open to students, staff and faculty at accredited degree-granting institutions; Thailand is on the list of countries. No approval time is published. Application already being prepared.
4. Programme terms: findings must be published and YouTube gets free access to the published research; standard API data rules (refresh or delete) still apply; the project already plans 90-day deletion.
5. Large and global, including Thai. Comments are attached to chosen videos, so the sample depends on how videos are picked; keyword video search per week is the cleaner topic measure, but needs the larger quota.
6. Light at current scale.
7. APPLY (in progress).

### 4.9 Meta Content Library (Facebook, Instagram, Threads, WhatsApp channels)
1. Conversation in public posts: Pages, groups, events, public profiles that are verified or have 100 or more followers; Instagram business, creator and larger personal accounts; Threads public profiles with 100 or more followers.
2. Search covers "all time"; the earliest date is not documented. View counts exist for Facebook posts from 1 January 2017, Instagram from 1 October 2022, Threads from 17 March 2024, so posts go back at least that far.
3. Apply in Meta Research Tools Manager; independent review by CASD (France); academics from any country not under US, UK, EU or UN sanctions; no education-level rule. The lead researcher invites collaborators. No fee in Meta's Secure Research Environment. SOMAR (ICPSR) charges USD 371 a month plus USD 1,000 setup from July 2026, but only if that enclave is used. Review time not published.
4. Research use is the purpose; results may be published without Meta's approval, with attribution and a notice. Data stays inside the environment, except CSV downloads of posts from widely known accounts. Limits: 60 searches a minute, 500,000 results per 7 days, only the top 1,000 results shown per search, comments viewable but not searched.
5. The "Trends in posts created" graph counts posts matching keywords over a date range on Facebook, Instagram and Threads: exactly the series we need. Thai coverage is strong. Bias: posts from organisations and larger accounts, not private individuals.
6. Nothing stored locally.
7. APPLY (Dr. Fawad as lead).

### 4.10 Reddit
Reddit for Researchers (page updated 6 October 2026):
1. Conversation: posts and comments with subreddit metadata, hashed user IDs (we would not use them).
2. "Historical data over a 5 year period with a six-month delay", updated monthly, deleted content removed. Today that is roughly April 2021 to April 2026. No 2016-2020.
3. Researchers and principal investigators at accredited universities, institutional email, detailed proposal naming subreddits, proof of ethics review (IRB or equivalent approval or exemption), sponsor's institutional email (faculty advisor qualifies), past publications help. Apply through a Reddit help ticket, role "researcher". Free. Access through BigQuery Analytics Hub, with a Google Cloud identity and two-factor login. Up to one year per project. No review time published.
4. Researcher Terms: no identifying users, no redistribution, delete all data at the end, check findings contain no deleted content, send a preprint. Queries and exports are logged. Compatible with our rules.
5. Large book communities and many theme communities; English, US-heavy, younger and male-leaning users. Collection by subreddit mapping plus keyword search.
6. Nothing stored locally beyond weekly aggregates.
7. APPLY (with Dr. Fawad as sponsor).

Reddit Data API: since the Responsible Builder Policy (11 November 2025) every new token needs approval, and researchers are pointed to the programme above. The earlier request from the project's bot account was refused. NO.

Pushshift and Arctic Shift dumps: Pushshift is limited to moderators since 2023; Arctic Shift redistributes the old dumps and new monthly files by torrent (2005 to 2025) and states no terms or Reddit permission. Reddit's Public Content Policy calls bulk collection by scraping or data brokers misuse and requires licensees to honour deletions, which dumps cannot do. NO.

### 4.11 X (Twitter)
API: pay-per-use with prepaid credits and no subscription (third-party reports date the switch to early 2026). Post reads cost USD 0.005 each, capped at 3 million a month, so reading posts is out of reach. The full-archive counts endpoint (`/2/tweets/counts/all`) is open to pay-per-use accounts: daily, hourly or minute counts back to 2006, 31 days per request, USD 0.010 per request, 300 requests per 15 minutes, queries up to 1,024 characters, with a `lang:` operator.
1. Conversation volume (counts only).
2. 2006 to now.
3. X developer account, accept the Developer Agreement, buy prepaid credits.
4. The Developer Policy supports academic research, but says not to "calculate aggregate X Post metrics, such as the total number of Posts posted per day" for "benchmarking, competitive, or commercial purposes". Topic counts for research are not benchmarking, but this needs a written note in the ethics file. No content or identities would be stored.
5. Full population of X, in English and Thai. Population and bot levels changed after 2022.
6. About 131 requests per query for 2016 to 2026 (USD 1.31); 300 queries would cost about USD 400 and take about 33 hours; tiny output.
7. LATER: a paid option for Khant and Dr. Fawad to decide; currently excluded in the ethics file.

Internet Archive Twitter Stream Grab: full tweet JSON from the 1% stream, 2011 to January 2023, 130 items, 7.47 TB, no licence on the items. Includes user identities and was redistributed outside X's terms. TweetsKB is the compliant derived version. NO.

### 4.12 Threads API keyword search
1. Conversation.
2. Searches cannot start before 5 July 2023 (timestamp 1688540400).
3. Meta developer app with `threads_basic` and `threads_keyword_search`; without approval only the user's own posts are searched. 2,200 queries per user per 24 hours; up to 100 posts per page; no count field, so counting means paging.
4. Allowed once approved; drop usernames.
5. Short history; overlaps with Meta Content Library, which also covers Threads.
6. Heavy paging for broad terms.
7. LATER (the Meta Content Library route is better).

### 4.13 Mastodon and other fediverse servers
1. Conversation.
2. Servers from 2016, but very small before the November 2022 move from Twitter.
3. Per-server API; public timelines may need a token where the server disables preview; full-text search needs login and only covers posts by users who opted in (8 to 10% of active accounts a year after it launched). OSoMe's archive from August 2023 covers more than 50 servers, on request.
4. Each server has its own rules; many communities object to research collection.
5. Small and tech-leaning.
6. Light, but scattered.
7. LATER.

### 4.14 Lemmy
Public API per server, IP rate limits, no documented keyword or date search; tiny before the June 2023 Reddit protests. NO.

### 4.15 TikTok Research API
Open to academics in the US, EEA, UK, Switzerland and Canada (Brazil for youth-safety work); Thailand is not eligible. NO.

### 4.16 Quora
No public API. Terms (effective 4 March 2024, section 4.4) forbid collecting data by automated means to make derivative works or train models, and allow crawling only to search engines, and robots.txt sets `Disallow: /` for all other bots. NO.

### 4.17 Pantip and other Thai sources
1. Conversation and questions in Thai, with a Library room for book talk.
2. Topics go back to the late 1990s.
3. No public API. Pantip's "Certified Developer" page lists social-listening companies (for example Wisesight, Zanroo, Mandala) with licensed access, and a phone number (02-357-1936 to 7).
4. Pantip's rules page has no clause on automated access, and robots.txt blocks only a few named bots, but the certified-partner scheme shows Pantip licenses its data. Ask for written permission first.
5. The best Thai conversation source if access is granted. Topics range from consumer reviews and entertainment to personal advice; a general Thai audience, not a book crowd.
6. Depends on the route.
7. APPLY: call or email Pantip for research permission for weekly counts by room or keyword, or ask a certified partner for academic access. Other Thai sites (Dek-D, ReadAWrite, Joylada) stay as in `context/terms_checks/README.md`. Thai Facebook comes through Meta Content Library; Thai X counts would come through the paid X route. The Wisesight Sentiment corpus (CC0, about 2016 to early 2019) can help train a Thai tone model but is not a time series.

### 4.18 Goodreads, StoryGraph and LibraryThing discussion
Goodreads stopped issuing API keys on 8 December 2020 and its groups have no API; scraping is excluded. StoryGraph has no API (listed on its roadmap with no date). LibraryThing's APIs need an account and do not cover Talk posts. NO.

### 4.19 Google Trends (official API, alpha)
1. Attention (searches), not conversation.
2. The API gives a rolling 5 years, daily to yearly, consistently scaled across requests.
3. Alpha by application (sent 12 October; no reply yet).
4. Allowed.
5. Global, including Thailand; does not reach 2016-2020.
6. Light.
7. APPLY (waiting).

### 4.20 Common Crawl
Open crawl archives since 2008 under terms that allow research. Forum pages appear, but the crawl date is not the post date, coverage per forum changes from crawl to crawl, and extracting dated posts per topic would mean processing terabytes. LATER (not for this thesis).

### 4.21 Podcasts (Podcast Index)
1. Creation activity: new episodes per topic (titles and descriptions), by creators rather than audiences.
2. Depends on how much of its back catalogue each feed keeps.
3. Free API key; search by term, episodes by feed; a weekly SQLite file of all feeds (about 1.8 GB compressed, per a 2026 blog post). Transcripts only where feeds publish them.
4. API terms (v1.1, 2 March 2021) allow use through documented means.
5. English-heavy; creators, not ordinary listeners.
6. Medium effort.
7. LATER.

### 4.22 News comment sections
Guardian Open Platform: free developer key for non-commercial use including "student dissertations", 500 calls a day, articles only; comments are not part of it. NYT Community API is marked deprecated in API catalogues and is not on NYT's API list. News articles are already covered by GDELT. NO for comments.

### 4.23 Pinterest
Trends API returns today's trending keywords only, not past dates, and access is limited to partners. Attention, not conversation. NO.

### 4.24 Twitch
Helix API has no past chat or past viewer counts. NO.

### 4.25 Discord
Developer Policy (effective 8 July 2024), point 20: "Do not mine or scrape any data". Servers are mostly private. NO.

### 4.26 Medium and Substack
Medium stopped issuing API tokens from January 2025. Substack's developer terms (8 January 2026) cover only creator profile data, and its terms of use ban scraping. Writers, not general conversation. NO.

### 4.27 Fandom wikis
Terms of use forbid any "robot, spider, site search and/or retrieval application" to "scrape, extract, retrieve or index" content, except text under the licensing page. NO without permission.

### 4.28 Telegram
API needs a phone-number account, mostly serves broadcast channels, bans using platform data to train AI, and Thai use is low. NO.

### 4.29 Other published research datasets
- TweetsKB: see 4.1; the one that fits.
- MigrationsKB (Zenodo, CC BY 4.0): TweetsKB-style data on migration only; a model for theme-specific sets.
- Bluesky Social Dataset (Failla and Rossetti; Zenodo, open, no licence stated; 235 million posts to early 2024): too early in Bluesky's life to be useful.
- OSoMe archives (Bluesky from November 2022, Mastodon from August 2023): on request; contain personal identifiers, so ethics review first.
- Tweet-ID datasets (for example COVID-19 chatter sets): need the paid X API to rebuild text. NO.

## 5. Downloads and sign-ups that need Khant

Downloads (none done):
- AO3 dump `20210226-stats.zip` from media.archiveofourown.org (link in the AO3 post "Selective data dump for fan statisticians"), 417 MB.
- Only if needed later: TweetsKB monthly files from Zenodo (Parts 4-9, 3 to 5 GB per month, about 219 GB for 2016-2020) and GESIS (Parts 10-12), one month at a time.

Sign-ups, applications or terms:
- Dr. Fawad: Meta Content Library (lead researcher, Meta account, Research Tools Terms); Reddit for Researchers sponsor.
- Khant: Reddit for Researchers application (CMKL email, ethics letter, Researcher Terms, Google Cloud identity with two-factor login); Meta collaborator invitation.
- Optional: Stack Apps key (more Stack Exchange quota); Bluesky app password (search backfill); X developer account and credit purchase; Meta developer app review for Threads.
- Pantip: phone or email request for written permission.

## 6. Pages opened (all on 14 October 2026)

Read directly:
- Reddit for Researchers Program: https://support.reddithelp.com/hc/en-us/articles/49381918834964-Reddit-for-Researchers-Program (page "updated 8 days ago")
- Reddit Public Content Policy: https://support.reddithelp.com/hc/en-us/articles/26410290525844-Public-Content-Policy
- Arctic Shift: https://github.com/ArthurHeitmann/arctic_shift
- X API pricing: https://docs.x.com/x-api/getting-started/pricing
- X post counts: https://docs.x.com/x-api/posts/counts/introduction and https://docs.x.com/x-api/posts/get-count-of-all-posts
- X rate limits: https://docs.x.com/x-api/fundamentals/rate-limits
- X query rules: https://docs.x.com/x-api/posts/search/integrate/build-a-query
- X Developer Agreement and Policy: https://developer.x.com/en/developer-terms/agreement-and-policy
- Internet Archive search API, collection twitterstream: https://archive.org/advancedsearch.php
- Bluesky Terms of Service: https://bsky.social/about/support/tos (updated 14 August 2025)
- Bluesky rate limits: https://bsky.network/docs/rate-limits/
- Bluesky developer guidelines: https://bsky.network/docs/developer-guidelines/
- Bluesky public search endpoint: https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts (test, 403)
- Failla and Rossetti paper: https://arxiv.org/abs/2404.18984 ; dataset: https://zenodo.org/records/14669616
- OSoMe data resources: https://osome.iu.edu/resources/data-resources
- Stack Exchange dumps, state in 2025: https://search.feep.dev/blog/post/2025-02-20-state-of-stackexchange
- Stack Exchange API terms: https://stackoverflow.com/legal/api-terms-of-use
- Stack Exchange API throttles: https://api.stackexchange.com/docs/throttle ; test: https://api.stackexchange.com/2.3/search/advanced
- Quora robots.txt: https://www.quora.com/robots.txt ; terms: https://www.quora.com/about/tos (effective 4 March 2024)
- Mastodon timelines: https://docs.joinmastodon.org/methods/timelines/ ; search: https://docs.joinmastodon.org/methods/search/
- Threads keyword search: https://developers.facebook.com/docs/threads/keyword-search
- Meta Content Library: https://transparency.meta.com/researchtools/meta-content-library/ (updated 30 April 2026)
- Meta Content Library docs: https://developers.facebook.com/docs/content-library-and-api/content-library ; changelog: https://developers.facebook.com/docs/content-library-and-api/changelog
- TikTok Research API: https://developers.tiktok.com/products/research-api/ ; FAQ: https://developers.tiktok.com/doc/research-api-faq
- YouTube Researcher Program: https://research.youtube/how-it-works/ and https://research.youtube/policies/
- YouTube search.list: https://developers.google.com/youtube/v3/docs/search/list ; quota: https://developers.google.com/youtube/v3/determine_quota_cost (updated 8 October 2026) ; commentThreads.list: https://developers.google.com/youtube/v3/docs/commentThreads/list (updated 14 September 2026)
- Tumblr API: https://www.tumblr.com/docs/en/api/v2
- Hacker News Algolia API (test): https://hn.algolia.com/api/v1/search_by_date ; HN API: https://github.com/HackerNews/API ; Y Combinator legal: https://www.ycombinator.com/legal/
- Wikimedia edits API (test): https://wikimedia.org/api/rest_v1/metrics/edits/per-page/
- Pantip robots.txt: https://pantip.com/robots.txt ; rules: https://pantip.com/about/tos ; certified developers: https://pantip.com/about/certified_developer
- Goodreads API page: https://www.goodreads.com/api
- Google Trends API: https://developers.google.com/search/apis/trends ; Trends data FAQ: https://support.google.com/trends/answer/4365533
- Common Crawl terms: https://commoncrawl.org/terms-of-use (updated 7 March 2024)
- Podcast Index API spec: https://raw.githubusercontent.com/Podcastindex-org/docs-api/master/api_src/root.yaml ; terms: https://github.com/Podcastindex-org/legal/blob/main/TermsOfService.md
- Guardian Open Platform access: https://open-platform.theguardian.com/access/
- Twitch API reference: https://dev.twitch.tv/docs/api/reference/
- Discord Developer Policy: https://support-dev.discord.com/hc/en-us/articles/8563934450327-Discord-Developer-Policy
- Fandom terms of use: https://www.fandom.com/terms-of-use
- AO3 terms: https://archiveofourown.org/tos ; data dump post: https://archiveofourown.org/admin_posts/18804 ; robots.txt: https://archiveofourown.org/robots.txt ; dump file (size only): https://media.archiveofourown.org/ao3/stats/2021/02/26/20210226-stats.zip
- AO3 data analysis: https://joellene.substack.com/p/data-science-x-ao3-1-spikes-in-published
- Telegram API terms: https://core.telegram.org/api/terms
- Lemmy API: https://join-lemmy.org/docs/contributors/04-api.html
- TweetsKB home and SPARQL endpoint (test): https://data.gesis.org/tweetskb/ ; paper: https://arxiv.org/pdf/1810.10308
- TweetsKB Zenodo records: https://zenodo.org/records/579601, https://zenodo.org/records/1095592, https://zenodo.org/records/1808741, https://zenodo.org/records/3828929, https://zenodo.org/records/3828949, https://zenodo.org/records/4420178, https://zenodo.org/records/7065612, https://zenodo.org/records/7065625
- TweetsKB Part 10 at GESIS: https://search.gesis.org/research_data/SDN-10.7802-2472

Known only from search-engine results (page blocked to automated readers or not opened):
- Reddit Responsible Builder Policy announcement, r/redditdev, 11 November 2025 (mirrors)
- SOMAR VDE fees, ICPSR SOMAR newsletters 2026 (page returned 403)
- Pinterest trends endpoint: https://developers.pinterest.com/docs/analytics-and-reports/trends/
- Substack Developer API Terms: https://substack.com/api-tos
- Medium help centre on API tokens
- NYT Community API status (third-party API catalogues)
- Mastodon search opt-in rate (fedi.tips, mjtsai.com)
- Goodreads API retirement (archived page, Goodreads developer forum)
- LibraryThing developer page (403)
- StoryGraph roadmap: https://roadmap.thestorygraph.com/features/posts/an-api
- Wisesight Sentiment corpus: https://github.com/PyThaiNLP/wisesight-sentiment
- Bluesky public opening and relay backfill studies (arXiv 2408.12449, 2408.03146)
