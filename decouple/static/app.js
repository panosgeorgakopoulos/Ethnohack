const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state = null, busy = false, showAll = false;

const pct = x => (x * 100).toFixed(1) + '%';
const LIST_CAP = 10;

async function api(path, body) {
 const r = await fetch(path, body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {});
 const j = await r.json();
 if (!r.ok) throw Error(j.error || 'Request failed');
 return j;
}
async function action(fn) {
 if (busy) return;
 busy = true; $('error').hidden = true;
 try { await fn() } catch (e) { $('error').textContent = e.message; $('error').hidden = false } finally { busy = false }
}
function modal(title, html) { $('modalTitle').textContent = title; $('modalBody').innerHTML = html; $('modal').showModal() }
function specimen(id) { return state.samples.find(s => s.id === id) }

// "m/z 353.102 @ RT 3.38 · Rotenoids" -> {klass:"Rotenoids", mass:"353.102", rt:"3.38"}
function parseName(name) {
 const [left, right] = String(name).split('·').map(s => s.trim());
 const m = /m\/z\s*([\d.]+)/.exec(left || ''), t = /RT\s*([\d.]+)/.exec(left || '');
 return {klass: (right || left || 'Compound').replace(/_/g, ' '), mass: m ? m[1] : null, rt: t ? t[1] : null};
}
// Two candidates in a pair are often the same chemical class, so the mass disambiguates them.
function plain(name) { const p = parseName(name); return p.mass ? `${p.klass}, mass ${p.mass}` : p.klass }
function meta(name) {
 const p = parseName(name);
 return [p.mass ? `m/z ${p.mass}` : null, p.rt ? `elutes at ${p.rt} min` : null,
         'mass-spectrum annotation, not a confirmed identity'].filter(Boolean).join(' · ');
}
function organOf(x) {
 const o = (x.evidence || []).map(e => e && e.organ).find(Boolean);
 return o ? String(o).replace(/_/g, ' ') : null;
}
function speciesOf(x) {
 const sp = (x.evidence || []).map(e => e && e.species).find(Boolean);
 return sp || String(x.name).split('·')[0].trim();
}

/* The decision, in the words a chemist would use out loud. */
function verdict(d, cands) {
 const nm = k => k === 'A' ? plain(cands[0].name) : k === 'B' ? plain(cands[1].name)
                : k === 'both' ? 'both of them together' : 'neither of them';
 const set = d.candidates || (d.candidate ? [d.candidate] : []);
 switch (d.kind) {
  case 'nominate':  return {title: `Candidate for confirmation: ${nm(set[0])}`,
                            flag: 'Confirm experimentally', cls: 'go'};
  case 'shortlist': return {title: `Down to ${set.length}: ${set.map(nm).join(' or ')}`,
                            flag: 'A further contrast may help', cls: 'hold'};
  case 'joint':     return {title: 'Model favours joint activity',
                            flag: 'Test compounds separately and together', cls: 'hold'};
  case 'cytotoxic': return {title: `Potential cytotoxicity: ${nm(set[0])}`,
                            flag: 'Deprioritise pending confirmation', cls: 'toxic'};
  default:          return {title: 'Not enough evidence to name a compound',
                            flag: 'Retain the uncertainty', cls: 'hold'};
 }
}
const HYP = ['A', 'B', 'both', 'neither'];
const PHRASES = [[/purified-compound assays/gi, 'assays on purified compounds']];
// the server names compounds by mass spectrum; show the reader the plain name instead
function humanise(text, cands) {
 let t = String(text || '');
 cands.forEach(c => { t = t.split(c.name).join(plain(c.name)) });
 PHRASES.forEach(([re, to]) => { t = t.replace(re, to) });
 return t.charAt(0).toUpperCase() + t.slice(1);
}
function leading(s) {
 const i = s.posterior.indexOf(Math.max(...s.posterior));
 const nm = i < 2 ? plain(s.candidates[i].name) : i === 2 ? 'Both together' : 'Neither of them';
 return {i, nm, p: s.posterior[i]};
}

function render(s) {
 state = s;
 localStorage.setItem('decouple-session', s.session_id);
 $('loading').hidden = true; $('workbench').hidden = false;

 const diag = s.tier.startsWith('Diagnostic');
 $('tier').textContent = diag ? 'Separating extracts hidden' : 'Measured extracts';
 $('provenance').textContent = 'Extract abundances and assay readouts come from ENPKG measurements. Probabilities and verdicts are model outputs. The toxicity readout is the L6 host-cell assay.';
 $('episodeSelect').value = s.id;
 $('diagnostic').checked = diag;

 const rec = s.recommendation;
 const tox = s.revealed_cytotox || {}, hasTox = s.posterior_cytotox != null;
 $('toxHeader').hidden = !hasTox;

 /* ---- the decision: the answer figure leads ---- */
 const lead = leading(s);
 if (s.decision) {
  const v = verdict(s.decision, s.candidates);
  const p = s.decision.mass != null ? s.decision.mass : s.decision.probability;
  $('verdictState').textContent = 'Final decision';
  $('verdictFigure').textContent = p != null ? pct(p) : '—';
  $('verdictFigureLabel').textContent = s.decision.kind === 'shortlist'
    ? 'model support for retained explanations' : 'model support, not biological confirmation';
  $('verdictTitle').textContent = v.title;
  $('verdictText').textContent = humanise(s.decision.explanation, s.candidates);
  $('verdictFlag').textContent = v.flag;
  $('verdictFlag').className = 'verdict-flag ' + v.cls;
  $('verdictFlag').hidden = false;
 } else {
  $('verdictState').textContent = 'Best explanation of the activity so far';
  $('verdictFigure').textContent = pct(lead.p);
  $('verdictFigureLabel').textContent = lead.nm;
  $('verdictTitle').textContent = lead.i === 2
    ? 'The model currently favours joint activity'
    : lead.i === 3 ? 'The assays so far point at neither compound'
    : `${lead.nm} currently has the most model support`;
  $('verdictText').textContent = s.remaining
    ? 'Assay an extract that holds one compound and not the other. That is what separates them.'
    : 'The budget is spent. Decide now, or stop and isolate nothing.';
  $('verdictFlag').hidden = true;
 }

 /* ---- the four explanations ---- */
 const vetoed = (s.decision && s.decision.vetoed) || [];
 $('candidates').innerHTML = s.candidates.map((c, i) => {
  const out = vetoed.includes(HYP[i]);
  return `<div class="candidate${out ? ' vetoed' : i === 0 ? ' is-a' : ''}">
   <div class="candidate-head"><span class="letter">${i ? 'B' : 'A'}</span>
    <button class="candidate-name" data-compound="${i}">${esc(plain(c.name))}</button>
    <span class="pct num">${pct(s.posterior[i])}</span></div>
   <p class="meta">${esc(meta(c.name))}${out ? ' · flagged by the host-toxicity model' : ''}</p>
   <div class="track"><span style="transform:scaleX(${s.posterior[i]})"></span></div>
  </div>`;
 }).join('');
 $('alternatives').innerHTML =
   `<span>Both together <b class="num">${pct(s.posterior[2])}</b></span>` +
   `<span>Neither of them <b class="num">${pct(s.posterior[3])}</b></span>`;

 $('budgetValue').textContent = `${s.remaining} of 3`;
 $('budgetMarks').innerHTML = [0,1,2].map(i => `<span class="${i >= s.remaining ? 'spent' : ''}"></span>`).join('');

 /* ---- the extracts, ranked by how well they separate the two ---- */
 const sep = x => Math.abs(x.x[0] - x.x[1]);
 const holdsOne = x => (x.x[0] > 0) !== (x.x[1] > 0);
 const pinned = s.samples.filter(x => x.id in s.revealed || (rec && rec.sample_id === x.id));
 const rest = s.samples.filter(x => !pinned.includes(x)).sort((a, b) => sep(b) - sep(a));
 const shown = showAll ? [...pinned, ...rest] : [...pinned, ...rest.slice(0, Math.max(0, LIST_CAP - pinned.length))];
 const separating = s.samples.filter(holdsOne).length;
 // one scale for both compounds, taken from the rows on screen, so the two bars are comparable
 const maxX = Math.max(0.01, ...shown.map(x => Math.max(x.x[0], x.x[1])));

 $('sampleCount').textContent = s.samples.length
   ? `${separating} of ${s.samples.length} hold just one of the two` : '';
 $('listNote').textContent = s.samples.length
   ? 'Recommended and assayed extracts appear first; others are ranked by abundance contrast. A zero means not detected, not proven absent. Raw assay values above 100% are retained without clipping.'
   : '';

 const bar = (v, cls, letter) => `<span class="lane"><b>${letter}</b>
   <span class="rail"><i class="${cls}" style="width:${v > 0 ? Math.max(3, v / maxX * 100) : 0}%"></i></span>
   <span class="amt num">${v.toFixed(2)}</span></span>`;
 $('samples').innerHTML = shown.length ? shown.map(x => {
  const known = x.id in s.revealed, next = rec && rec.sample_id === x.id;
  const cls = [next && !known ? 'next-up' : '', known ? 'done' : ''].filter(Boolean).join(' ');
  const toxv = known && x.id in tox ? tox[x.id] : null;
  return `<tr class="${cls}">
   <td class="ident"><button class="candidate-name plant" data-evidence="${esc(x.id)}">${esc(speciesOf(x))}</button>
     <span class="organ">${esc(organOf(x) || x.id)}${known ? ' · assayed' : next ? ' · recommended next' : ''}</span></td>
   <td class="strip"><span class="strip-rail${next && !known ? ' next' : ''}" role="img"
     aria-label="holds ${x.x[0].toFixed(2)} of compound A and ${x.x[1].toFixed(2)} of compound B">
     ${bar(x.x[0], 'a', 'A')}${bar(x.x[1], 'b', 'B')}</span></td>
   <td class="read num">${known ? pct(s.revealed[x.id]) : '<span class="dash">—</span>'}</td>
   <td class="read num" ${hasTox ? '' : 'hidden'}>${
     toxv == null ? '<span class="dash">—</span>'
     : `<span class="${toxv > 0.3 ? 'toxflag' : ''}">${pct(toxv)}</span>`}</td>
   <td class="act"><button data-reveal="${esc(x.id)}" ${known || s.remaining === 0 || s.decision ? 'disabled' : ''}>${known ? 'Done' : 'Assay'}</button></td>
  </tr>`;
 }).join('')
  : `<tr class="emptyrow"><td colspan="5">Every extract here holds both compounds in the same amount, so no assay can separate them. Stopping is the honest answer.</td></tr>`;

 $('listTotal').textContent = s.samples.length
   ? `Showing ${shown.length} of ${s.samples.length} extracts` : '';
 $('showAllButton').hidden = s.samples.length <= shown.length && !showAll;
 $('showAllButton').textContent = showAll ? `Show the best ${LIST_CAP}` : `Show all ${s.samples.length}`;

 document.querySelectorAll('[data-reveal]').forEach(b => b.onclick = () => reveal(b.dataset.reveal));
 document.querySelectorAll('[data-evidence]').forEach(b => b.onclick = () => showSpecimen(b.dataset.evidence));
 document.querySelectorAll('[data-compound]').forEach(b => b.onclick = () => showCompound(+b.dataset.compound));

 /* ---- next experiment ---- */
 $('recommendedButton').disabled = !!s.decision;
 $('abstainButton').disabled = !!s.decision;
 $('recommendedButton').textContent = s.decision ? 'Decided' : s.remaining === 0 ? 'Decide now' : 'Assay this extract';
 if (s.decision) {
  $('nextLabel').textContent = 'Your decision';
  $('recommendationTitle').textContent = verdict(s.decision, s.candidates).title;
  $('recommendationText').textContent = 'Download the full evidence trail, or see what a potency-ranked search would have done with the same three assays.';
 } else if (rec) {
  $('nextLabel').textContent = 'Recommended next assay';
  const x = specimen(rec.sample_id);
  $('recommendationTitle').textContent = `${speciesOf(x)}${organOf(x) ? ' · ' + organOf(x) : ''}`;
  $('recommendationText').textContent =
    `It holds ${x.x[0].toFixed(2)} of ${plain(s.candidates[0].name)} against ${x.x[1].toFixed(2)} of ${plain(s.candidates[1].name)}, and has the highest score under the configured acquisition rule. Its result may help distinguish the explanations.`;
 } else {
  $('nextLabel').textContent = 'Nothing left to spend';
  $('recommendationTitle').textContent = 'Budget spent';
  $('recommendationText').textContent = 'Make the call on what you have, or stop and isolate nothing.';
 }

 /* ---- spend and baseline ---- */
 $('trail').innerHTML = [0, 1, 2].map(i => {
  const t = s.trace[i];
  if (!t) return `<div class="spend empty"><span class="slot num">${i + 1}</span>
    <span class="what">Not spent yet</span></div>`;
  const x = specimen(t.sample_id);
  return `<div class="spend"><span class="slot num">${i + 1}</span>
    <span class="what"><b>${esc(speciesOf(x))}</b>${organOf(x) ? ` · ${esc(organOf(x))}` : ''}</span>
    <span class="res num">parasite inhibition ${pct(t.response)}</span>
    <span class="res num ${t.response_cytotox > 0.3 ? 'toxflag' : ''}">${
      t.response_cytotox != null ? `L6 inhibition ${pct(t.response_cytotox)}` : ''}</span></div>`;
 }).join('');

 $('baselineText').textContent = s.strongest
   ? `Standard practice is to chase the most potent extract. That would send you to ${speciesOf(specimen(s.strongest.sample_id))}, which maximises predicted response. DECOUPLE scores candidates by expected nomination utility; compare both on the same archived outcomes.`
   : 'Standard practice chases the most potent extract. This compares that against your three choices on the same archived measurements.';
 $('compareButton').disabled = !s.decision;
 $('compareNote').textContent = s.decision
   ? 'Both replay the same archived measurements.'
   : 'Both replay the same archived measurements. Available once you have decided.';
}

function showCompound(i) {
 const c = state.evidence[i], p = parseName(c.name);
 modal(plain(c.name), `
  <p>A ${esc(p.klass.toLowerCase())} of mass ${esc(p.mass || '—')}${p.rt ? `, eluting at ${esc(p.rt)} minutes` : ''}.</p>
  <h3>How sure are we this is the right molecule?</h3>
  <p>${esc(c.identity_match_tier)}. In plain terms: the mass spectrum matches this structure in a reference library, but nobody has run an authentic standard beside it. Isomers of the same mass are competing for the same peak.</p>
  <p><a href="${esc(c.source_url)}" target="_blank" rel="noopener">Open the compound record ↗</a> · <span class="num">${esc(c.inchikey)}</span></p>
  ${c.activity_records ? `<h3>Published measurements</h3><pre>${esc(JSON.stringify(c.activity_records, null, 2))}</pre>`
    : '<p>Published measurements for this compound stay hidden until you have decided, so they cannot steer your choice.</p>'}`);
}

function showSpecimen(id) {
 const x = specimen(id);
 modal(speciesOf(x) + (organOf(x) ? ' · ' + organOf(x) : ''), `
  <p>This extract holds <b class="num">${x.x[0]}</b> of ${esc(plain(state.candidates[0].name))} and
     <b class="num">${x.x[1]}</b> of ${esc(plain(state.candidates[1].name))}, as ${esc(x.units || 'relative peak area')}.</p>`
  + x.evidence.map((e, i) => `<h3>${i ? 'B' : 'A'} · ${esc(plain(state.candidates[i].name))}</h3>${
   e ? `<p>This plant is on record as carrying this compound.
         <a href="${esc(e.compound_url)}" target="_blank" rel="noopener">Compound ↗</a> ·
         <a href="${esc(e.url)}" target="_blank" rel="noopener">Plant ↗</a></p>
        <p>Sources: ${e.references.map(r => `<a href="${esc(r.startsWith('http') ? r : 'https://doi.org/' + r)}" target="_blank" rel="noopener">${esc(r)}</a>`).join(', ')}</p>`
     : '<p>No record of this compound in this plant in the matched snapshot. That is an absence of evidence, not evidence of absence.</p>'}`).join(''));
}

async function mutate(path, extra = {}) {
 const key = `decouple-request:${state.session_id}:${state.revision}:${path}:${extra.sample_id || ''}`;
 const requestId = localStorage.getItem(key) || crypto.randomUUID();
 localStorage.setItem(key, requestId);
 const response = await api(path, {
  session: state.session_id,
  expected_revision: state.revision,
  request_id: requestId,
  ...extra
 });
 localStorage.removeItem(key);
 render(response);
}
async function reveal(id) { await action(() => mutate('/api/reveal', {sample_id: id})) }

$('recommendedButton').onclick = () => {
 if (state.remaining && state.recommendation) return reveal(state.recommendation.sample_id);
 return action(() => mutate('/api/finalize'));
};
$('abstainButton').onclick = () => action(() => mutate('/api/abstain'));
$('startButton').onclick = () => action(async () => {
 showAll = false;
 render(await api('/api/start', {episode_id: $('episodeSelect').value, diagnostic: $('diagnostic').checked}));
});
// picking a pair loads it; render() assigns .value programmatically, which does not fire change
$('episodeSelect').onchange = () => $('startButton').click();
$('diagnostic').onchange = () => $('startButton').click();
$('showAllButton').onclick = () => { showAll = !showAll; render(state) };
$('closeModal').onclick = () => $('modal').close();

$('exportButton').onclick = () => action(async () => {
 if (!state) throw Error('Start a pair first');
 const j = await api('/api/export?session=' + state.session_id);
 const blob = new Blob([JSON.stringify(j, null, 2)], {type: 'application/json'});
 const a = document.createElement('a');
 a.href = URL.createObjectURL(blob);
 a.download = 'decouple-decision-trace.json';
 a.click();
 setTimeout(() => URL.revokeObjectURL(a.href), 1000);
});

$('compareButton').onclick = () => action(async () => {
 const r = await api('/api/compare?session=' + state.session_id);
 modal('Same three assays, two ways of choosing them', `
  <p>Both runs replay the same archived measurements on the same compound pair with the same budget. The only difference is which extracts they spend it on.</p>
  <div class="comparison">${[['Your choices', r.you], ['Chasing the most potent extract', r.baseline]].map(([name, v]) => `
   <div><h3>${esc(name)}</h3><ol>${v.trace.map(t => {
    const x = specimen(t.sample_id);
    return `<li>${esc(speciesOf(x))}<br>parasite inhibition ${pct(t.response)}${
      t.response_cytotox != null ? `, L6 inhibition ${pct(t.response_cytotox)}` : ''}</li>`;
   }).join('')}</ol>
   <h3>${esc(verdict(v.decision, v.candidates).title)}</h3>
   <p>${esc(humanise(v.decision.explanation, v.candidates))}</p></div>`).join('')}</div>`);
});

$('resultsButton').onclick = () => action(async () => {
 const r = await api('/api/results');
 const fmt = o => o.estimate === null ? '—' : pct(o.estimate) + (o.ci95 ? ` [${o.ci95.map(pct).join('–')}]` : '');
 const POLICY = {
  no_budget: 'Spend no assays', random: 'Three extracts at random',
  'strongest-first': 'Chase the most potent extract', decouple: 'DECOUPLE, expected-information picks',
  adaptive_contrast: 'DECOUPLE, adaptive contrast'
 };
 modal('How well it does', `
  <p>Evaluated on ${r.episodes} semi-synthetic runs across ${r.unique_pairs} compound pairs taken from the real library. The extract chemistry and the co-occurrence are measured; the activity is simulated, providing known ground truth under the chosen simulation assumptions.</p>
  <h3>Which extracts to spend the budget on</h3><p>Hard stratum: 58 episodes from 16 pairs. Under the potency-only rule, adaptive contrast and strongest-first each correctly nominate in 19.0% of hard episodes (95% pair-clustered interval 6.9–34.4%). The table below instead reports overall developable accuracy with selectivity-aware nomination. These metrics are different.</p>
  <div class="tablewrap"><table><thead><tr>
    <th scope="col">Way of choosing</th><th scope="col">Correct developable nomination / all runs</th>
    <th scope="col">No single-compound nomination</th><th scope="col">Developable precision / nominated</th>
  </tr></thead><tbody>${Object.entries(r.policies).map(([p, m]) => `<tr>
    <td>${esc(POLICY[p] || p)}</td><td class="num">${fmt(m.correct_nomination_rate)}</td>
    <td class="num">${fmt(m.abstention_rate)}</td><td class="num">${fmt(m.precision_when_nominating)}</td>
  </tr>`).join('')}</tbody></table></div>
  <p>${esc(r.uncertainty)}</p>
  <p>These rows use the threshold-based single-compound rule with a host-toxicity veto. Abstentions count as misses. The simulator and inference share modelling assumptions.</p>
  ${r.set_valued ? `
  <h3>Answering with a short list instead of one name</h3>
  <p>The workbench uses a separate set-valued rule. It starts with the smallest set reaching 95% posterior mass, then applies a host-toxicity veto. The retained mass can be below 95%. Explanations can include both or neither. Set containment is not single-compound identification accuracy.</p>
  <div class="tablewrap"><table><thead><tr>
    <th scope="col">Gives an answer</th><th scope="col">True explanation contained</th>
    <th scope="col">Mean explanation-set size</th><th scope="col">Cytotoxicity verdict</th>
  </tr></thead><tbody><tr>
    <td class="num">${pct(r.set_valued.coverage)}</td><td class="num">${pct(r.set_valued.containment)}</td>
    <td class="num">${r.set_valued.mean_size.toFixed(2)}</td><td class="num">${pct(r.set_valued.cytotoxic_rate)}</td>
  </tr></tbody></table></div>
  <p>Of those ${r.episodes} runs: ${Object.entries(r.set_valued.kind_counts).map(([k, n]) =>
     `${n} ${esc({nominate: 'named one compound', shortlist: 'narrowed it to a short list',
       joint: 'favoured joint activity', cytotoxic: 'flagged potential cytotoxicity',
       abstain: 'declined to answer'}[k] || k)}`).join(' · ')}.</p>` : ''}
  <p>The set-valued rule abstained in ${r.indistinguishable_diagnostic.abstentions} of ${r.indistinguishable_diagnostic.episodes} benchmark runs. This is ordinary benchmark abstention, not a separately measured contrast-withheld control.</p>`);
});

action(async () => {
 const c = await api('/api/catalog');
 $('episodeSelect').innerHTML = c.episodes.map(e =>
   `<option value="${esc(e.id)}">${esc(e.names.map(plain).join('  vs  '))}</option>`).join('');
 const query = new URLSearchParams(window.location.search);
 const sid = query.get('session') || localStorage.getItem('decouple-session');
 if (sid) {
  try { render(await api('/api/state?session=' + sid)); if(query.get('modal')==='compare') $('compareButton').click(); if(query.get('modal')==='results') $('resultsButton').click(); return }
  catch { localStorage.removeItem('decouple-session') }
 }
 render(await api('/api/start', {episode_id: c.episodes[0].id}));
 if(query.get('modal')==='results') $('resultsButton').click();
});
