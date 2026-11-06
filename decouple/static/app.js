const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state=null,busy=false;
const pct=x=>(x*100).toFixed(1)+'%';
async function api(path,body){const r=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const j=await r.json();if(!r.ok)throw Error(j.error||'Request failed');return j}
async function action(fn){if(busy)return;busy=true;$('error').hidden=true;try{await fn()}catch(e){$('error').textContent=e.message;$('error').hidden=false}finally{busy=false}}
function modal(title,html){$('modalTitle').textContent=title;$('modalBody').innerHTML=html;$('modal').showModal()}
function specimen(id){return state.samples.find(s=>s.id===id)}
function label(d,cands){const nm=k=>k==='A'?cands[0].name:k==='B'?cands[1].name:k;const set=d.candidates||(d.candidate?[d.candidate]:[]);
 switch(d.kind){
  case 'nominate':return `Nominate ${nm(set[0])}`;
  case 'shortlist':return `Shortlist: ${set.map(nm).join(' or ')}`;
  case 'joint':return 'Both contribute. Do not fractionate.';
  case 'cytotoxic':return `Cytotoxic: do not isolate ${nm(set[0])}`;
  default:return 'Abstain. Preserve the uncertainty.';
 }}
function render(s){state=s;localStorage.setItem('decouple-session',s.session_id);$('loading').hidden=true;$('workbench').hidden=false;$('tier').textContent=s.tier.startsWith('Diagnostic')?'Diagnostic · contrasts withheld':s.tier;const lim=s.limitations||[];$('provenance').textContent=lim.length?lim[0]:'';$('zeroNote').textContent=lim.find(l=>/absence|unrecorded/i.test(l))||'A zero is not a confirmed biological absence.';
 $('episodeSelect').value=s.id;$('diagnostic').checked=s.tier.startsWith('Diagnostic');
 if(!$('candidates').children.length)$('candidates').innerHTML=[0,1].map(i=>`<div class="candidate ${i?'b':'a'}"><div class="candidate-title"><span class="letter">${i?'B':'A'}</span><button id="candidate${i}"></button><span class="probability" id="prob${i}"></span></div><div class="track"><span id="bar${i}"></span></div></div>`).join('');
 s.candidates.forEach((c,i)=>{$('candidate'+i).textContent=c.name;$('candidate'+i).onclick=()=>showCompound(i);$('prob'+i).textContent=pct(s.posterior[i]);$('bar'+i).style.transform=`scaleX(${s.posterior[i]})`});
 $('alternatives').innerHTML=`<span>Both <b>${pct(s.posterior[2])}</b></span><span>Neither <b>${pct(s.posterior[3])}</b></span>`;
 $('budgetValue').textContent=`${s.remaining} / 3`;$('budgetMarks').innerHTML=[0,1,2].map(i=>`<span class="${i>=s.remaining?'spent':''}"></span>`).join('');
 const rec=s.recommendation;const best=Math.max(...s.posterior);
 const tox=s.revealed_cytotox||{},hasTox=s.posterior_cytotox!=null;$('toxHeader').hidden=!hasTox;
 $('verdictTitle').textContent=s.decision?label(s.decision,s.candidates):(s.trace.length?`Leading explanation: ${['A only','B only','both','neither'][s.posterior.indexOf(best)]}`:'The starting assay cannot separate A and B.');
 $('verdictText').textContent=s.decision?s.decision.explanation:'One response is already visible. Choose a sample profile that distinguishes the explanations. Final nomination requires the configured support threshold.';
 $('sampleCount').textContent=`${s.samples.length} sample profiles`;
 $('samples').innerHTML=s.samples.length?[...s.samples].sort((a,b)=>Number(b.id===rec?.sample_id)-Number(a.id===rec?.sample_id)).map(x=>{const known=x.id in s.revealed;const selected=rec&&rec.sample_id===x.id;return `<tr class="${selected?'recommended':''}"><td><button class="species" data-evidence="${esc(x.id)}">${esc(x.name)}</button><span class="specimen-sub">${selected?'Recommended assay':known?(s.trace.some(t=>t.sample_id===x.id)?'Assay revealed':'Starting assay'):x.id}</span></td>${x.x.map(v=>`<td class="number">${v.toFixed(2)}<div class="cellbar"><i style="width:${v/1.5*100}%"></i></div></td>`).join('')}<td class="response">${known?s.revealed[x.id].toFixed(3):'—'}</td><td class="response" ${hasTox?'':'hidden'}>${known&&x.id in tox?tox[x.id].toFixed(3):'—'}</td><td><button data-reveal="${esc(x.id)}" ${known||s.remaining===0||s.decision?'disabled':''}>${known?'Revealed':'Reveal'}</button></td></tr>`}).join(''):'<tr><td colspan="5">Every specimen in this episode carries a contrast between A and B, so withholding contrasts leaves nothing to assay. The honest answer here is to abstain.</td></tr>';
 document.querySelectorAll('[data-reveal]').forEach(b=>b.onclick=()=>reveal(b.dataset.reveal));document.querySelectorAll('[data-evidence]').forEach(b=>b.onclick=()=>showSpecimen(b.dataset.evidence));
 $('recommendedButton').disabled=!!s.decision;
 $('abstainButton').disabled=!!s.decision;
 $('recommendedButton').textContent=s.decision?'Decision finalized':s.remaining===0?'Finalize decision':'Reveal assay';
 if(s.decision){$('recommendationTitle').textContent={nominate:'Nomination',shortlist:'Shortlist',joint:'Joint activity',cytotoxic:'Cytotoxicity veto'}[s.decision.kind]||'No justified single-compound choice';$('recommendationText').textContent='Export the evidence and decision trace, or compare the baseline on the same episode.'}
 else if(rec){const x=specimen(rec.sample_id);$('recommendationTitle').textContent=x.name;$('recommendationText').textContent=`Expected nomination utility gain ${rec.score.toFixed(3)} on a 0–1 scale. Predicted response under A ${rec.predictions.A.toFixed(2)} / B ${rec.predictions.B.toFixed(2)}.`}
 else{$('recommendationTitle').textContent='The assay budget is complete.';$('recommendationText').textContent='Apply the shared nomination threshold, or retain ambiguity.'}
 $('trail').innerHTML=s.trace.length?s.trace.map(t=>`<li>${esc(specimen(t.sample_id).name)} → parasite ${t.response.toFixed(3)}${t.response_cytotox!=null?` · host tox ${t.response_cytotox.toFixed(3)}`:''}</li>`).join(''):'<li>No new assays yet. Your three-assay budget is intact.</li>';
 $('baselineText').textContent=s.strongest?`Strongest-first would assay ${specimen(s.strongest.sample_id).name}, maximizing predicted response (${s.strongest.score.toFixed(3)}). DECOUPLE maximizes expected nomination utility gain.`:'Compare the complete strongest-first replay against your choices on identical archived outcomes.';
 $('compareButton').disabled=!s.decision;
}
function showCompound(i){const c=state.evidence[i];modal(c.name,`<p>Identity match: ${esc(c.identity_match_tier)}.</p><p><a href="${esc(c.source_url)}" target="_blank" rel="noopener">Open compound record ↗</a></p><p>${esc(c.inchikey)}</p><p>Published compound measurements become visible after finalization. ${esc((state.limitations||[])[0]||'')}</p>${c.activity_records?`<pre>${esc(JSON.stringify(c.activity_records,null,2))}</pre>`:''}`)}
function showSpecimen(id){const x=specimen(id);modal(x.name,`<p>${esc(x.units||'Relative concentration')}: A ${x.x[0]}, B ${x.x[1]}.</p>`+x.evidence.map((e,i)=>`<h3>${i?'B':'A'} · ${esc(state.candidates[i].name)}</h3>${e?`<p>Documented taxon–compound occurrence. <a href="${esc(e.compound_url)}" target="_blank" rel="noopener">Compound ↗</a> · <a href="${esc(e.url)}" target="_blank" rel="noopener">Taxon ↗</a></p><p>References: ${e.references.map(r=>`<a href="${esc(r.startsWith('http')?r:'https://doi.org/'+r)}" target="_blank" rel="noopener">${esc(r)}</a>`).join(', ')}</p>`:'<p>No record in the matched snapshot. A zero is not a confirmed biological absence.</p>'}`).join(''))}
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
async function reveal(id) {
 await action(() => mutate('/api/reveal', {sample_id: id}));
}
$('recommendedButton').onclick = () => {
 if (state.remaining && state.recommendation) return reveal(state.recommendation.sample_id);
 return action(() => mutate('/api/finalize'));
};
$('abstainButton').onclick = () => action(() => mutate('/api/abstain'));
$('startButton').onclick=()=>action(async()=>render(await api('/api/start',{episode_id:$('episodeSelect').value,diagnostic:$('diagnostic').checked})));
// picking an episode loads it; render() assigns .value programmatically, which does not fire change
$('episodeSelect').onchange=()=>$('startButton').click();
$('diagnostic').onchange=()=>$('startButton').click();
$('closeModal').onclick=()=>$('modal').close();
$('exportButton').onclick=()=>action(async()=>{if(!state)throw Error('Start an episode first');const j=await api('/api/export?session='+state.session_id);const blob=new Blob([JSON.stringify(j,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='decouple-decision-trace.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)});
$('compareButton').onclick=()=>action(async()=>{const r=await api('/api/compare?session='+state.session_id);modal('One episode. Equal assay budgets.',`<div class="comparison">${[['Your choices',r.you],['Strongest-first',r.baseline]].map(([name,v])=>`<div><h3>${name}</h3><ol>${v.trace.map(t=>`<li>${esc(specimen(t.sample_id).name)}<br>parasite ${t.response.toFixed(3)}${t.response_cytotox!=null?`<br>host tox ${t.response_cytotox.toFixed(3)}`:''}</li>`).join('')}</ol><h3>${esc(label(v.decision,v.candidates))}</h3><p>${esc(v.decision.explanation)}</p></div>`).join('')}</div>`)});
$('resultsButton').onclick=()=>action(async()=>{const r=await api('/api/results');const fmt=o=>o.estimate===null?'—':pct(o.estimate)+(o.ci95?` [${o.ci95.map(pct).join('–')}]`:'');modal(r.tier||'Benchmark comparison',`<p>${r.episodes} simulated episodes across ${r.unique_pairs} chemical pairs. The current pairs share a compound and a source assay. Repeats vary simulated noise; they provide no additional biological validation.</p><div class="tablewrap"><table><thead><tr><th>Policy</th><th>Correct nomination / all episodes</th><th>Abstention</th><th>Precision / nominated</th></tr></thead><tbody>${Object.entries(r.policies).map(([p,m])=>`<tr><td>${esc(p)}</td><td>${fmt(m.correct_nomination_rate)}</td><td>${fmt(m.abstention_rate)}</td><td>${fmt(m.precision_when_nominating)}</td></tr>`).join('')}</tbody></table></div><p>${esc(r.uncertainty)}</p><p>All policies use the same inference model and final nomination rule. The simulator and inference share a response family, so these results describe behavior under that assumption.</p><p>The contrast-withheld diagnostic abstained in ${r.indistinguishable_diagnostic.abstentions}/${r.indistinguishable_diagnostic.episodes} episodes. This reflects the programmed ambiguity rule.</p>${r.set_valued?`<h3>${esc(r.set_valued.label)}</h3><p>The shipped verdict returns the smallest set of explanations carrying the stated posterior mass, with the host-cytotoxicity veto applied. A size-1 set is a nomination; a size-2 set is a cheap discriminating experiment, not a hedge.</p><div class="tablewrap"><table><thead><tr><th>Answered</th><th>Contains the true driver</th><th>Mean set size</th><th>Vetoed as cytotoxic</th></tr></thead><tbody><tr><td>${pct(r.set_valued.coverage)}</td><td>${pct(r.set_valued.containment)}</td><td>${r.set_valued.mean_size.toFixed(2)}</td><td>${pct(r.set_valued.cytotoxic_rate)}</td></tr></tbody></table></div><p>${Object.entries(r.set_valued.kind_counts).map(([k,n])=>`${esc(k)} ${n}`).join(' · ')}</p>`:''}`)});
action(async()=>{const c=await api('/api/catalog');$('episodeSelect').innerHTML=c.episodes.map(e=>`<option value="${esc(e.id)}">${esc(e.names.join(' / '))}</option>`).join('');const sid=localStorage.getItem('decouple-session');if(sid){try{render(await api('/api/state?session='+sid));return}catch{localStorage.removeItem('decouple-session')}}render(await api('/api/start',{episode_id:c.episodes[0].id}))});
