const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state=null,busy=false;
const pct=x=>(x*100).toFixed(1)+'%';
async function api(path,body){const r=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const j=await r.json();if(!r.ok)throw Error(j.error||'Request failed');return j}
async function action(fn){if(busy)return;busy=true;$('error').hidden=true;try{await fn()}catch(e){$('error').textContent=e.message;$('error').hidden=false}finally{busy=false}}
function modal(title,html){$('modalTitle').textContent=title;$('modalBody').innerHTML=html;$('modal').showModal()}
function specimen(id){return state.samples.find(s=>s.id===id)}
function render(s){state=s;localStorage.setItem('decouple-session',s.session_id);$('loading').hidden=true;$('workbench').hidden=false;$('tier').textContent=s.tier.startsWith('Diagnostic')?'Simulation diagnostic · contrasts withheld':'Simulation diagnostic';
 $('episodeSelect').value=s.id;$('diagnostic').checked=s.tier.startsWith('Diagnostic');
 if(!$('candidates').children.length)$('candidates').innerHTML=[0,1].map(i=>`<div class="candidate ${i?'b':'a'}"><div class="candidate-title"><span class="letter">${i?'B':'A'}</span><button id="candidate${i}"></button><span class="probability" id="prob${i}"></span></div><div class="candidate-structure" id="structure${i}"></div><div class="track"><span id="bar${i}"></span></div></div>`).join('');
 s.candidates.forEach((c,i)=>{$('candidate'+i).textContent=c.name;$('candidate'+i).onclick=()=>showCompound(i);$('prob'+i).textContent=pct(s.posterior[i]);$('bar'+i).style.transform=`scaleX(${s.posterior[i]})`;if(!$('structure'+i).innerHTML||$('structure'+i).dataset.cid!==c.id){$('structure'+i).dataset.cid=c.id;$('structure'+i).innerHTML=`<img src="/api/structure?id=${esc(c.id)}" alt="${esc(c.name)}" loading="lazy">`}});
 $('alternatives').innerHTML=`<span>Both <b>${pct(s.posterior[2])}</b></span><span>Neither <b>${pct(s.posterior[3])}</b></span>`;
 $('budgetValue').textContent=`${s.remaining} / 3`;$('budgetMarks').innerHTML=[0,1,2].map(i=>`<span class="${i>=s.remaining?'spent':''}"></span>`).join('');
 const rec=s.recommendation;const best=Math.max(...s.posterior);
 $('verdictTitle').textContent=s.decision?(s.decision.kind==='nominate'?`Nominate ${s.candidates[s.decision.candidate==='A'?0:1].name}`:'Abstain. Preserve the uncertainty.'):(s.trace.length?`Leading explanation: ${['A only','B only','both','neither'][s.posterior.indexOf(best)]}`:'The starting assay cannot separate A and B.');
 $('verdictText').textContent=s.decision?s.decision.explanation:'One simulated response is already visible. Choose a sample profile that distinguishes the explanations. Final nomination requires the configured support threshold.';
 $('sampleCount').textContent=`${s.samples.length} sample profiles`;
 $('samples').innerHTML=[...s.samples].sort((a,b)=>Number(b.id===rec?.sample_id)-Number(a.id===rec?.sample_id)).map(x=>{const known=x.id in s.revealed;const selected=rec&&rec.sample_id===x.id;return `<tr class="${selected?'recommended':''}"><td><button class="species" data-evidence="${esc(x.id)}">${esc(x.name)}</button><span class="specimen-sub">${selected?'Recommended simulated assay':known?(s.trace.some(t=>t.sample_id===x.id)?'Simulation revealed':'Starting simulation'):x.id}</span></td>${x.x.map(v=>`<td class="number">${v.toFixed(2)}<div class="cellbar"><i style="width:${v/1.5*100}%"></i></div></td>`).join('')}<td class="response">${known?s.revealed[x.id].toFixed(3):'—'}</td><td><button data-reveal="${esc(x.id)}" ${known||s.remaining===0||s.decision?'disabled':''}>${known?'Revealed':'Reveal'}</button></td></tr>`}).join('');
 document.querySelectorAll('[data-reveal]').forEach(b=>b.onclick=()=>reveal(b.dataset.reveal));document.querySelectorAll('[data-evidence]').forEach(b=>b.onclick=()=>showSpecimen(b.dataset.evidence));
 $('recommendedButton').disabled=!!s.decision;
 $('abstainButton').disabled=!!s.decision;
 $('recommendedButton').textContent=s.decision?'Decision finalized':s.remaining===0?'Finalize decision':'Reveal simulated assay';
 if(s.decision){$('recommendationTitle').textContent=s.decision.kind==='abstain'?'No justified single-compound choice':'Simulation nomination';$('recommendationText').textContent='Export the evidence and decision trace, or compare the baseline on the same episode.'}
 else if(rec){const x=specimen(rec.sample_id);$('recommendationTitle').textContent=x.name;$('recommendationText').textContent=`Expected nomination utility gain ${rec.score.toFixed(3)} on a 0–1 scale. Simulated response under A ${rec.predictions.A.toFixed(2)} / B ${rec.predictions.B.toFixed(2)}.`}
 else{$('recommendationTitle').textContent='The assay budget is complete.';$('recommendationText').textContent='Apply the shared nomination threshold, or retain ambiguity.'}
 $('trail').innerHTML=s.trace.length?s.trace.map(t=>`<li>${esc(specimen(t.sample_id).name)} → ${t.response.toFixed(3)} simulated response units</li>`).join(''):'<li>No new assays yet. Your three-assay budget is intact.</li>';
 $('baselineText').textContent=s.strongest?`Strongest-first would assay ${specimen(s.strongest.sample_id).name}, maximizing predicted response (${s.strongest.score.toFixed(3)}). DECOUPLE maximizes expected nomination utility gain.`:'Compare the complete strongest-first replay against your choices on identical simulated outcomes.';
 $('compareButton').disabled=!s.decision;
}
function showCompound(i){const c=state.evidence[i];modal(c.name,`<div class="modal-structure"><img src="/api/structure?id=${esc(c.id)}&width=400&height=200" alt="${esc(c.name)}"></div><p>Identity match: ${esc(c.identity_match_tier)}.</p><p><a href="${esc(c.source_url)}" target="_blank" rel="noopener">Open compound record ↗</a></p><p>${esc(c.inchikey)}</p><p>Published compound measurements become visible after finalization. Sample concentrations and extract responses in this episode were generated by a simulator.</p>${c.activity_records?`<pre>${esc(JSON.stringify(c.activity_records,null,2))}</pre>`:''}`)}
function showSpecimen(id){const x=specimen(id);modal(x.name,`<p>Simulated relative concentrations: A ${x.x[0]}, B ${x.x[1]}.</p>`+x.evidence.map((e,i)=>`<h3>${i?'B':'A'} · ${esc(state.candidates[i].name)}</h3>${e?`<p>Documented taxon–compound occurrence. <a href="${esc(e.compound_url)}" target="_blank" rel="noopener">Compound ↗</a> · <a href="${esc(e.url)}" target="_blank" rel="noopener">Taxon ↗</a></p><p>References: ${e.references.map(r=>`<a href="${esc(r.startsWith('http')?r:'https://doi.org/'+r)}" target="_blank" rel="noopener">${esc(r)}</a>`).join(', ')}</p>`:'<p>No record in the matched snapshot. Zero is a simulation assumption. Biological absence is unmeasured.</p>'}`).join(''))}
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
$('closeModal').onclick=()=>$('modal').close();
$('exportButton').onclick=()=>action(async()=>{if(!state)throw Error('Start an episode first');const j=await api('/api/export?session='+state.session_id);const blob=new Blob([JSON.stringify(j,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='decouple-decision-trace.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)});
$('compareButton').onclick=()=>action(async()=>{const r=await api('/api/compare?session='+state.session_id);modal('One simulation. Equal assay budgets.',`<div class="comparison">${[['Your choices',r.you],['Strongest-first',r.baseline]].map(([name,v])=>`<div><h3>${name}</h3><ol>${v.trace.map(t=>`<li>${esc(specimen(t.sample_id).name)}<br>${t.response.toFixed(3)} simulated response</li>`).join('')}</ol><h3>${v.decision.kind==='nominate'?'Nominate '+esc(v.candidates[v.decision.candidate==='A'?0:1].name):'Abstain'}</h3><p>${esc(v.decision.explanation)}</p></div>`).join('')}</div>`)});
$('resultsButton').onclick=()=>action(async()=>{const r=await api('/api/results');const fmt=o=>o.estimate===null?'—':pct(o.estimate)+(o.ci95?` [${o.ci95.map(pct).join('–')}]`:'');modal('Benchmark comparison',`<p>${r.episodes} episodes across ${r.unique_pairs} unique chemical pairs from ${r.unique_source_documents} published scientific studies in ChEMBL.</p><div class="tablewrap"><table><thead><tr><th>Policy</th><th>Correct nomination</th><th>Single-driver recovery</th><th>Abstention</th><th>Precision</th></tr></thead><tbody>${Object.entries(r.policies).map(([p,m])=>`<tr><td>${esc(p)}</td><td>${fmt(m.correct_nomination_rate)}</td><td>${fmt(m.single_driver_recovery)}</td><td>${fmt(m.abstention_rate)}</td><td>${fmt(m.precision_when_nominating)}</td></tr>`).join('')}</tbody></table></div><p>${esc(r.uncertainty)}</p><p>All policies evaluate on identical candidates, sample profiles and assay budgets under the shared hypothesis model.</p><p>The contrast-withheld diagnostic correctly abstained in ${r.indistinguishable_diagnostic.abstentions}/${r.indistinguishable_diagnostic.episodes} episodes.</p>`)});
action(async()=>{const c=await api('/api/catalog');$('episodeSelect').innerHTML=c.episodes.map(e=>`<option value="${esc(e.id)}">${esc(e.names.join(' / '))} · [${esc(e.document)}] (${e.shared_species} shared plants)</option>`).join('');const sid=localStorage.getItem('decouple-session');if(sid){try{render(await api('/api/state?session='+sid));return}catch{localStorage.removeItem('decouple-session')}}render(await api('/api/start',{episode_id:c.episodes[0].id}))});
