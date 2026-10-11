import {repos} from './feeds.js';
let campaigns={},states={},chosen='harness',metric='completion';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number=v=>typeof v==='number'&&Number.isFinite(v)&&v>=0;
const nullable=v=>v===null||number(v);
const hex=v=>/^[a-f0-9]{64}$/.test(v);
if(typeof location!=='undefined'&&['harness','api','local'].includes(new URLSearchParams(location.search).get('trial')))chosen=new URLSearchParams(location.search).get('trial');
const titles={harness:'Cloud CRM · viewer permissions',api:'Cloud API · customer risk',local:'Local Gemma · customer risk'};
export function validateCampaign(c,id){
 const project=id==='local'?'api':id;
 if(id==='local'&&(c?.runtime!=='llama.cpp'||!hex(c?.localRuntime?.modelFileSha256)))throw Error('Invalid local model provenance');
 if(!c||c.schemaVersion!==1||c.project!==project||!['harness','api','local'].includes(id)||c.protocol!=='one-response-mutation-v1'||!hex(c.planSha256)||c.campaignId!==c.planSha256.slice(0,16)||!hex(c.targetSha256)||!Array.isArray(c.rows)||c.rows.length>6||c.plannedTrials!==6||!Array.isArray(c.limitations)||!Number.isFinite(Date.parse(c.updatedAt)))throw Error('Invalid controlled campaign');
 const seen=new Set,checks=id==='harness'?5:8;
 for(const r of c.rows){
  const key=r.arm+':'+r.repeat;if(!['baseline','framework'].includes(r.arm)||![1,2,3].includes(r.repeat)||seen.has(key))throw Error('Invalid paired trial');seen.add(key);
  if(!['evaluated','awaiting-evaluation','generation-failed'].includes(r.operationalStatus)||typeof r.correct!=='boolean'||!Number.isInteger(r.qualityPassed)||r.qualityPassed<0||r.qualityPassed>checks||r.qualityTotal!==checks||!['generationMs','evaluationMs','humanCorrectionMs','incorrectChanges','inputTokens','cachedInputTokens','outputTokens','apiEquivalentUSD','actualCostUSD'].every(k=>nullable(r[k]))||!hex(r.promptSha256))throw Error('Invalid measurement');
  if(r.operationalStatus==='evaluated'&&(!hex(r.responseSha256)||!hex(r.eventsSha256)||!hex(r.evaluationSha256)||r.checks.length!==checks||r.qualityPassed!==r.checks.filter(x=>x.passed===true).length||r.correct!==r.checks.every(x=>x.passed===true)))throw Error('Contradictory evaluation');
 }
 for(const arm of ['baseline','framework']){
  const a=c.arms[arm],rows=c.rows.filter(r=>r.arm===arm);
  if(!a||a.trials!==rows.length||a.correct!==rows.filter(r=>r.correct).length||a.qualityPassed!==rows.reduce((n,r)=>n+r.qualityPassed,0)||a.qualityTotal!==rows.length*checks||!['medianGenerationMs','medianEvaluationMs','medianHumanCorrectionMs','apiEquivalentUSD','actualCostUSD'].every(k=>nullable(a[k])))throw Error('Contradictory aggregate');
 }
 return c;
}
export async function fetchCampaigns(current={},fetcher=fetch){
 const next={...current},status={};
 await Promise.all(['harness','api','local'].map(async id=>{
  try{const response=await fetcher(`https://raw.githubusercontent.com/balajiregt/${repos[id==='local'?'api':id]}/benchmark-results/${id==='local'?'local-trials.json':'trials.json'}?minute=${Math.floor(Date.now()/60000)}`,{cache:'no-store',signal:AbortSignal.timeout(12000)});if(!response.ok)throw Error();const raw=await response.text();if(raw.length>200000)throw Error();next[id]=validateCampaign(JSON.parse(raw),id);status[id]=true;}catch{status[id]=false;}
 }));return {campaigns:next,states:status};
}
export async function loadTrials(){
 if(!document.getElementById('controlled-trials'))return;
 if(!Object.keys(campaigns).length){try{const seed=await (await fetch('/data/trials.json')).json();for(const id of ['harness','api','local'])if(seed[id])campaigns[id]=validateCampaign(seed[id],id);}catch{/* visible missing state below */}}
 const result=await fetchCampaigns(campaigns);campaigns=result.campaigns;states=result.states;render();
}
function values(c){
 return ['baseline','framework'].map(arm=>{
  const a=c.arms[arm];let value,display;
  if(metric==='completion'){value=a.trials?100*a.correct/a.trials:0;display=`${a.correct} / ${a.trials} complete`;}
  if(metric==='quality'){value=a.qualityTotal?100*a.qualityPassed/a.qualityTotal:0;display=`${a.qualityPassed} / ${a.qualityTotal} checks`;}
  if(metric==='time'){value=a.medianGenerationMs===null?null:a.medianGenerationMs/1000;display=value===null?'Unavailable':`${value.toFixed(2)} s median`;}
  if(metric==='tokens'){value=number(a.totalInputTokens)&&number(a.totalOutputTokens)?a.totalInputTokens+a.totalOutputTokens:null;display=value===null?'Unavailable: incomplete usage':`${value.toLocaleString()} total tokens`;}
  if(metric==='cost'){const local=c.runtime==='llama.cpp';value=local?a.apiFeeUSD:a.apiEquivalentUSD;display=value===null?'Unavailable':local?'$0 API fee; ops unmeasured':`$${value.toFixed(4)} API equivalent`;}
  return {arm,value,display};
 });
}
function render(){
 const root=document.getElementById('controlled-trials');if(!root)return;
 const c=campaigns[chosen];
 root.innerHTML=`<div class="detail-head"><div><div class="eyebrow">LIVE MODEL TRIALS / FIRST PILOT</div><h2>Does framework context change the result?</h2><p>One-response test generation · three repeats per arm · healthy app + hidden faults</p></div><a href="https://github.com/balajiregt/framework-benchmark-dashboard/blob/main/trials/README.md" target="_blank" rel="noopener noreferrer">Read trial protocol ↗</a></div><div class="trial-body"><div class="trial-toolbar"><div class="trial-tabs" role="group" aria-label="Trial application">${Object.entries(titles).map(([id,title])=>`<button data-trial="${id}" class="secondary" aria-pressed="${id===chosen}">${esc(title)}</button>`).join('')}</div><label>Chart <select id="trial-metric"><option value="completion">Correct completion</option><option value="quality">Quality checks</option><option value="time">Generation attempt time</option><option value="tokens">Token usage</option><option value="cost">${chosen==='local'?'Inference API fee':'API-equivalent cost'}</option></select></label></div>${!c?'<p>No verified campaign is available. This is missing evidence, not zero performance.</p>':content(c)}</div>`;
 root.querySelectorAll('[data-trial]').forEach(b=>b.addEventListener('click',()=>{chosen=b.dataset.trial;const url=new URL(location.href);url.searchParams.set('trial',chosen);history.replaceState(null,'',url);render();}));root.querySelector('#trial-metric').value=metric;root.querySelector('#trial-metric').addEventListener('change',e=>{metric=e.target.value;render();});
 root.querySelectorAll('[data-trial-width]').forEach(b=>b.style.width=b.dataset.trialWidth+'%');
}
function content(c){
 const local=c.runtime==='llama.cpp';
 const chart=values(c),max=['completion','quality'].includes(metric)?100:Math.max(...chart.map(v=>v.value??0),.001);
 const cost=Object.values(c.arms).reduce((n,a)=>n+(a.apiEquivalentUSD??0),0);
 const allComplete=c.rows.length===6&&c.rows.every(r=>r.correct);
 const failures=c.rows.filter(r=>!r.correct),timeouts=failures.filter(r=>r.timedOut).length,buildFailures=failures.filter(r=>r.failureKind==='build-or-runner-error').length;
 const outcome=allComplete?'Both arms passed every check in this pilot.':`${c.rows.filter(r=>r.correct).length} / ${c.rows.length} submissions completed all criteria.`;
 return `${states[chosen]===false?'<p class="notice">Trial feed unavailable. Showing the last loaded campaign; it may be out of date.</p>':'<p class="feed-ok">● Trial feed connected · refreshes with the application feeds</p>'}<div class="trial-chart" role="img" aria-label="${esc(chart.map(v=>v.arm+': '+v.display).join('; '))}">${chart.map(v=>`<div class="trial-bar-row"><strong>${v.arm==='baseline'?'Baseline':'Framework'}</strong><div class="trial-bar-track"><span class="trial-bar ${v.arm}" data-trial-width="${100*(v.value??0)/max}"></span></div><span>${esc(v.display)}</span></div>`).join('')}</div><div class="trial-takeaway"><strong>${esc(outcome)}</strong><p>${allComplete?'These tasks do not establish a quality advantage for framework context. A larger, harder task set is needed to distinguish the approaches.':`${timeouts} generation timeout(s); ${buildFailures} build/runner failure(s). Failures remain in the denominator and are not replaced with successful retries.`} Time and cost are descriptive. Human correction effort has not been measured. Unexecuted checks stay unsatisfied; quality checks are completion criteria, not defect recall.</p></div><div class="table-wrap"><table><caption>Measured trial summary · ${esc(c.model)} / ${esc(c.reasoning)} reasoning</caption><thead><tr><th>Arm</th><th>Correct</th><th>Quality checks</th><th>Attempt median</th><th>Evaluation median</th><th>${local?'Inference API fee':'API-equivalent total'}</th><th>Human correction</th></tr></thead><tbody>${['baseline','framework'].map(arm=>{const a=c.arms[arm];return `<tr><td>${arm}</td><td>${a.correct}/${a.trials}</td><td>${a.qualityPassed}/${a.qualityTotal}</td><td>${a.medianGenerationMs===null?'Unavailable':(a.medianGenerationMs/1000).toFixed(2)+' s'}</td><td>${a.medianEvaluationMs===null?'Unavailable':(a.medianEvaluationMs/1000).toFixed(2)+' s'}</td><td>${local?(a.apiFeeUSD===0?'$0 (operating cost unmeasured)':'Unavailable'):(a.apiEquivalentUSD===null?'Unavailable':'$'+a.apiEquivalentUSD.toFixed(4))}</td><td>Not measured</td></tr>`;}).join('')}</tbody></table></div><p class="trial-note">${local?'Local requests have no external inference API fee; electricity, hardware and total operating cost are unmeasured. The existing server uses an 8192-token context, max output 4096, one slot and temperature 0.2. Timeouts count as failures; their elapsed times stop at the 180-second deadline.':'Costs are estimates using standard <a href="https://developers.openai.com/api/docs/models/gpt-6.1-sol" target="_blank" rel="noopener noreferrer">API rates verified 11 Oct 2026</a> and reported CLI tokens. They are not bills. Actual spend, infrastructure cost and human effort are unavailable.'} ${c.pairedRepeats} matched repeats; ${c.rows.length}/${c.plannedTrials} planned trials recorded.</p><details><summary>Validate all ${c.rows.length} trials and fault outcomes</summary><div class="table-wrap"><table><thead><tr><th>Repeat / arm</th><th>Completion</th><th>Checks</th><th>Generation</th><th>Input / output tokens</th><th>${local?'Output tokens/s':'API equivalent'}</th></tr></thead><tbody>${c.rows.map(r=>`<tr><td>${r.repeat} / ${r.arm}</td><td>${r.correct?'Complete':r.operationalStatus==='evaluated'?'Incomplete · '+esc(r.failureKind??'check failure'):esc(r.failureKind??r.operationalStatus)}</td><td>${r.qualityPassed}/${r.qualityTotal}</td><td>${r.timedOut?'≥ ':''}${(r.generationMs/1000).toFixed(2)} s</td><td>${r.inputTokens??'—'} / ${r.outputTokens??'—'}</td><td>${local?(r.generationTokensPerSecond==null?'Unavailable':r.generationTokensPerSecond.toFixed(2)):(r.apiEquivalentUSD===null?'Unavailable':'$'+r.apiEquivalentUSD.toFixed(4))}</td></tr>`).join('')}</tbody></table></div>${c.rows.map(r=>`<details><summary>Repeat ${r.repeat}, ${r.arm}: individual checks and evidence</summary><ul>${r.checks.map(x=>`<li>${x.passed?'✓':'!'} ${esc(x.name)} · ${esc(x.outcome??(x.passed?'satisfied':'unsatisfied'))} · ${x.injectedResponses} injected response(s)</li>`).join('')}</ul><p>Prompt <code>${esc(r.promptSha256)}</code><br>Response <code>${esc(r.responseSha256)}</code><br>${local?'Provider evidence':'CLI events'} <code>${esc(r.eventsSha256)}</code><br>Evaluation <code>${esc(r.evaluationSha256)}</code></p></details>`).join('')}</details><details><summary>Conditions, limitations and campaign provenance</summary><ul>${c.limitations.map(l=>`<li>${esc(l)}</li>`).join('')}</ul><p>Campaign <code>${esc(c.campaignId)}</code><br>Source revision <code>${esc(c.sourceRevision)}</code><br>Frozen input hash <code>${esc(c.targetSha256)}</code><br>Model: ${esc(c.model)}. ${esc(c.modelVersion)}.<br>Runtime: ${esc(c.cliVersion)}.${local?'<br>Hardware: '+esc(c.localRuntime.hardware)+', '+(c.localRuntime.memoryBytes/1024**3).toFixed(0)+' GiB RAM.':''}<br>Generated ${esc(new Date(c.updatedAt).toLocaleString())}.</p><a href="https://raw.githubusercontent.com/balajiregt/${repos[chosen==='local'?'api':chosen]}/benchmark-results/${local?'local-trials.json':'trials.json'}" target="_blank" rel="noopener noreferrer">Open public trial data ↗</a></details>`;
}

export const getPublicCampaigns=()=>structuredClone(campaigns);
