# Test F operations: how the sorting jobs were run (21 Oct 2026)

These files ran the AI sorting of Test F (addendum g); they assign no themes themselves. They were run from `data/db/wiki_led/testF/` and are copied here for the record.

- `sorting_workflow_v1.js`: the first Claude Code workflow (03:35 to 04:15): one Opus sorter per job of `jobs.tsv`, with the fixed instructions `prereg/addenda_wiki_led/2026-10-21_g_prompt_{pages,books,judge}.md` and the theme guide; one retry when a job is not complete.
- `sorting_workflow_v2.js`: the workflow used from 09:27: the same instructions, plus saved parts of at most 250 items so that a sorter stopped by a usage limit can be continued; `EFFORT` stayed at the session level (full thinking) after the pilot.
- `thinking_level_pilot_workflow.js` and `pilot_compare.py`: the thinking-level pilot and its fixed rule (prereg/DEVIATIONS.md, Test F items 8 and 9; report data/reports/testF_effort_pilot.md).
- `track.py`: counts jobs whose answer file has one line per input item with the ids in order.
- `make_args.py`: lists the jobs not done, in the order judge, main pages, main books, reliability and one-day sample.
- `salvage_parts.py`: before a restart, collects the checked answer lines that stopped sorters had saved and gives each saved file to the job that holds most of its ids (Test F items 7 and 10).

Paths inside these files point to this Mac (the session scratchpad and the project folder).
