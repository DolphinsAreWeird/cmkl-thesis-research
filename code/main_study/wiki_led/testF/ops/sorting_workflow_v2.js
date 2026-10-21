export const meta = {
  name: 'testf-ai-sorting-v2',
  description: 'Test F: Opus sorters assign Wikipedia pages and books to book themes, one agent per job; saved parts are reused after a stop',
  phases: [{ title: 'Sort', detail: 'one sorter per job; each saves parts, joins its answer file and reports a check' }],
}
const ROOT = '/Users/mac/Documents/CMKL University/Thesis – Audiobook Performance Prediction/handoff'
const T = ROOT + '/data/db/wiki_led/testF/'
const SCRATCH = '/private/tmp/claude-501/-Users-mac-Documents-CMKL-University-Thesis---Audiobook-Performance-Prediction/3d7e599c-e8eb-44e0-8e7e-9c7619b7026a/scratchpad'
const INSTR = {
  pages: ROOT + '/prereg/addenda_wiki_led/2026-10-21_g_prompt_pages.md',
  books: ROOT + '/prereg/addenda_wiki_led/2026-10-21_g_prompt_books.md',
  judge: ROOT + '/prereg/addenda_wiki_led/2026-10-21_g_prompt_judge.md',
}
const GUIDE = ROOT + '/prereg/addenda_wiki_led/2026-10-21_g_theme_guide.tsv'
// thinking level of the sorters, chosen by the pilot (prereg/DEVIATIONS.md, Test F item 8); null = the session level (max)
const EFFORT = null
const COLS = {
  pages: 'id, title, description, first_sentence',
  books: 'id, title, author, headings, tags, description',
  judge: 'id, title, description, first_sentence',
}
const ROLE = {
  pages: 'one of several AI sorters of Wikipedia pages',
  books: 'one of several AI sorters of library books',
  judge: 'the independent judge of page sorting',
}
const SCHEMA = {
  type: 'object',
  properties: {
    job: { type: 'string' },
    lines: { type: 'integer' },
    none_count: { type: 'integer' },
    invalid_codes: { type: 'array', items: { type: 'string' } },
    ids_ok: { type: 'boolean' },
    reused_lines: { type: 'integer' },
  },
  required: ['job', 'lines', 'ids_ok'],
}
function prompt(j) {
  const dir = `${SCRATCH}/${j.job}/`
  return [
    `You are ${ROLE[j.kind]} in a research study (Test F). Work only on job ${j.job}.`,
    `1. Read the instructions \`${INSTR[j.kind]}\` and the full theme guide \`${GUIDE}\` (242 rows).`,
    `2. Your ${j.n} items are lines ${j.a} to ${j.b} of \`${T}${j.input}\` (tab-separated: ${COLS[j.kind]}; line 1 of the file is a header). Read them in parts of about 400 lines.`,
    `3. Work in the folder \`${dir}\` (create it if needed). An earlier attempt at this job may have been stopped and left answer files there. You may reuse their lines (some may use spaces or | instead of tabs; convert them to the output format of the instructions), but only lines whose ids are among your items and whose codes are in the guide; do every item not covered yourself. Save your own answers in that folder in files of at most 250 items (numbered after any files already there), one line per item, no header, so that a later attempt can reuse them if you are stopped.`,
    `4. Do every item yourself, by your own judgement, following the instructions exactly. Do not write or run any program, script, keyword list or rule that assigns themes, and do not open any other project file. Commands that only join or check files are fine.`,
    `5. At the end, write \`${T}${j.out}\` with exactly one line per item in input order, no header, replacing any file already there.`,
    `6. Check that the file has exactly ${j.n} lines, that each input id appears once in order, and that every code is in the guide.`,
    `Return the check: job, lines, none_count, invalid_codes (empty if none), ids_ok, reused_lines (lines taken from an earlier attempt, 0 if none).`,
  ].join('\n')
}
phase('Sort')
const jobs = args.map(([job, kind, input, a, b, out, n]) => ({ job, kind, input, a, b, out, n }))
const results = await pipeline(jobs, async (j) => {
  for (let attempt = 1; attempt <= 2; attempt++) {
    const r = await agent(prompt(j), Object.assign({ label: attempt === 1 ? j.job : j.job + ' (retry)', phase: 'Sort', schema: SCHEMA }, EFFORT ? { effort: EFFORT } : {}))
    if (r && r.ids_ok && r.lines === j.n && !(r.invalid_codes && r.invalid_codes.length)) return { job: j.job, ok: true, none: r.none_count, reused: r.reused_lines || 0, level: EFFORT || 'max' }
    log(`${j.job}: attempt ${attempt} not complete`)
  }
  return { job: j.job, ok: false }
})
const done = results.filter(r => r && r.ok)
log(`${done.length} of ${jobs.length} jobs complete`)
return { complete: done.length, total: jobs.length, not_complete: results.filter(r => !r || !r.ok).map(r => (r ? r.job : 'unknown')) }
