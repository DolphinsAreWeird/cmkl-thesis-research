export const meta = {
  name: 'testf-effort-pilot',
  description: 'Test F: sort 250 already-sorted pages again at three thinking levels to measure the quality cost of less thinking',
  phases: [{ title: 'Pilot', detail: 'one sorter per thinking level on the same 250 pages' }],
}
const ROOT = '/Users/mac/Documents/CMKL University/Thesis – Audiobook Performance Prediction/handoff'
const T = ROOT + '/data/db/wiki_led/testF/'
const SCHEMA = {
  type: 'object',
  properties: { job: { type: 'string' }, lines: { type: 'integer' }, none_count: { type: 'integer' }, invalid_codes: { type: 'array', items: { type: 'string' } }, ids_ok: { type: 'boolean' } },
  required: ['job', 'lines', 'ids_ok'],
}
function prompt(level) {
  return [
    `You are one of several AI sorters of Wikipedia pages in a research study (Test F). Work only on job pilot_${level}.`,
    `1. Read the instructions \`${ROOT}/prereg/addenda_wiki_led/2026-10-21_g_prompt_pages.md\` and the full theme guide \`${ROOT}/prereg/addenda_wiki_led/2026-10-21_g_theme_guide.tsv\` (242 rows).`,
    `2. Your 250 items are lines 2 to 251 of \`${T}pages_chunk_05.tsv\` (tab-separated: id, title, description, first_sentence; line 1 of the file is a header).`,
    `3. Do every item yourself, by your own judgement, following the instructions exactly. Do not write or run any program, script, keyword list or rule that assigns themes, and do not open any other project file. Commands that only join or check files are fine.`,
    `4. Write \`${T}pilot_effort/${level}.tsv\` with exactly one line per item in input order, no header, replacing any file already there.`,
    `5. Check that the file has exactly 250 lines, that each input id appears once in order, and that every code is in the guide.`,
    `Return the check: job, lines, none_count, invalid_codes (empty if none), ids_ok.`,
  ].join('\n')
}
phase('Pilot')
const levels = ['max', 'high', 'medium']
const res = await parallel(levels.map(level => () => agent(prompt(level), { label: 'pilot_' + level, phase: 'Pilot', schema: SCHEMA, effort: level })))
return levels.map((l, i) => ({ level: l, result: res[i] }))
