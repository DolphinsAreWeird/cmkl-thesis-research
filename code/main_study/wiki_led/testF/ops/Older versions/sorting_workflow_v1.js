export const meta = {
  name: 'testf-ai-sorting',
  description: 'Test F: Opus sorters assign Wikipedia pages and books to book themes, one agent per job, retry once if incomplete',
  phases: [{ title: 'Sort', detail: 'one sorter per job; each writes its answer file and reports a check' }],
}
const ROOT = '/Users/mac/Documents/CMKL University/Thesis – Audiobook Performance Prediction/handoff'
const T = ROOT + '/data/db/wiki_led/testF/'
const INSTR = {
  pages: ROOT + '/prereg/addenda_wiki_led/2026-10-21_g_prompt_pages.md',
  books: ROOT + '/prereg/addenda_wiki_led/2026-10-21_g_prompt_books.md',
  judge: ROOT + '/prereg/addenda_wiki_led/2026-10-21_g_prompt_judge.md',
}
const GUIDE = ROOT + '/prereg/addenda_wiki_led/2026-10-21_g_theme_guide.tsv'
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
  },
  required: ['job', 'lines', 'ids_ok'],
}
function prompt(j, attempt) {
  return [
    `You are ${ROLE[j.kind]} in a research study (Test F). Work only on job ${j.job}.` + (attempt > 1 ? ' An earlier attempt at this job did not finish; start again from the beginning.' : ''),
    `1. Read the instructions \`${INSTR[j.kind]}\` and the full theme guide \`${GUIDE}\` (242 rows).`,
    `2. Read lines ${j.a} to ${j.b} of \`${T}${j.input}\` (tab-separated: ${COLS[j.kind]}; line 1 of the file is a header), in parts of about 400 lines.`,
    `3. Do every item yourself, by your own judgement, following the instructions exactly. Do not write or run any program, script, keyword list or rule that assigns themes, and do not open any other project file.`,
    `4. Write the complete answers, one line per item in input order, no header, to \`${T}${j.out}\`, replacing any file already there (never append to an existing file). If you prefer to write in parts, put the parts in a scratch folder and join them into that file at the end.`,
    `5. Check that the file has exactly ${j.n} lines, that each input id appears once in order, and that every code is in the guide.`,
    `Return the check: job, lines, none_count, invalid_codes (empty if none), ids_ok.`,
  ].join('\n')
}
phase('Sort')
const jobs = args.map(([job, kind, input, a, b, out, n]) => ({ job, kind, input, a, b, out, n }))
const results = await pipeline(jobs, async (j) => {
  for (let attempt = 1; attempt <= 2; attempt++) {
    const r = await agent(prompt(j, attempt), { label: attempt === 1 ? j.job : j.job + ' (retry)', phase: 'Sort', schema: SCHEMA })
    if (r && r.ids_ok && r.lines === j.n && !(r.invalid_codes && r.invalid_codes.length)) return { job: j.job, ok: true, none: r.none_count }
    log(`${j.job}: attempt ${attempt} not complete`)
  }
  return { job: j.job, ok: false }
})
const done = results.filter(r => r && r.ok)
log(`${done.length} of ${jobs.length} jobs complete`)
return { complete: done.length, total: jobs.length, not_complete: results.filter(r => !r || !r.ok).map(r => (r ? r.job : 'unknown')) }
