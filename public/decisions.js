const FEED='https://raw.githubusercontent.com/balajiregt/playwright-decision-bench/benchmark-results/decision-bench.json';
const providers=['laya','openai','qwen'],tasks=['coverage','smoke'],splits=['development','heldout'];
const esc=v=>String(v??'Unavailable').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const rate=v=>v===null?'Unavailable':(v*100).toFixed(1)+'%';
const millis=v=>v===null?'Unavailable':Math.round(v).toLocaleString()+' ms';
const count=v=>Number.isSafeInteger(v)&&v>=0;
const metric=v=>v===null||(typeof v==='number'&&Number.isFinite(v)&&v>=0);
let current=null;
export function validateDecisions(d){
 if(!d||d.schemaVersion!==1||d.project!=='playwright-decision-bench'||d.protocol!=='coverage-smoke-v1'||d.mode!=='live'||!count(d.repeats)||d.repeats<1||d.repeats>3||d.goldStatus!=='author-labeled-unreviewed')throw Error('Invalid decision protocol');
 if(![d.datasetHash,d.goldHash].every(x=>/^[a-f0-9]{64}$/.test(x))||!Number.isFinite(Date.parse(d.generatedAt)))throw Error('Missing decision provenance');
 if(!d.metrics||!Array.isArray(d.metrics.summaries)||d.metrics.summaries.length!==12||!Array.isArray(d.metrics.suites)||d.metrics.suites.length>100)throw Error('Invalid metric groups');
 const seen=new Set;
 for(const s of d.metrics.summaries){
  const key=[s.provider,s.task,s.split].join(':');
  if(seen.has(key)||!providers.includes(s.provider)||!tasks.includes(s.task)||!splits.includes(s.split))throw Error('Invalid comparison group');seen.add(key);
  for(const k of ['requested','uniqueCases','valid','matched','errors','refusals','excluded','notRun','neutral','routedReview','latencySamples','warmLatencySamples','costReportedCalls','repeatableCases','stableCases'])if(!count(s[k]))throw Error('Invalid count');
  if(s.requested!==s.uniqueCases*d.repeats||s.requested>150||s.valid+s.errors+s.refusals+s.excluded+s.notRun!==s.requested||s.matched>s.valid||s.routedReview>s.valid||s.neutral>s.valid||s.costReportedCalls>s.valid||s.latencySamples!==s.valid||s.warmLatencySamples>s.valid||s.stableCases>s.repeatableCases||s.repeatableCases>s.uniqueCases)throw Error('Contradictory denominators');
  const expected=s.valid?s.matched/s.valid:null,end=s.requested?s.matched/s.requested:null;
  if(s.accuracy!==expected||s.endToEndAccuracy!==end)throw Error('Contradictory accuracy');
  for(const k of ['p50Ms','p95Ms','warmP50Ms','failedLatencyP50Ms','reportedCostUsd','costPerValidAnswerUsd','maxProcessRssBytes'])if(!metric(s[k]))throw Error('Invalid measurement');
  if(s.valid===0&&(s.p50Ms!==null||s.p95Ms!==null)||s.p50Ms>s.p95Ms)throw Error('Invalid latency');
  for(const k of ['gapPrecision','gapRecall','includePrecision','includeRecall','repeatability'])if(!metric(s[k])||s[k]>1)throw Error('Invalid rate');
  if(s.task==='coverage'&&(!count(s.falseCovered)||!count(s.unknownAsCovered)||s.falseCovered+s.unknownAsCovered>s.valid))throw Error('Invalid false assurance count');
 }
 for(const s of d.metrics.suites){
  if(!providers.includes(s.provider)||!splits.includes(s.split)||!count(s.repeat)||s.repeat<1||s.repeat>d.repeats||typeof s.feasible!=='boolean'||!Array.isArray(s.selected)||s.selected.length>16||!count(s.totalTests)||!count(s.retainedJourneys)||!count(s.mandatoryJourneys)||s.retainedJourneys>s.mandatoryJourneys||!Array.isArray(s.missedJourneys)||!Array.isArray(s.dependencyViolations))throw Error('Invalid smoke suite');
  if(s.feasible&&(!s.selected.length||s.missedJourneys.length||s.dependencyViolations.length||s.budgetViolation||s.incompleteInventory))throw Error('Unsafe smoke approval');
  if(!metric(s.estimatedSerialMs)||s.measuredFullSuiteMs!==null||s.measuredSmokeSuiteMs!==null||s.runtimeReduction!==null)throw Error('Unverified runtime measurement');
 }
 if(!d.metrics.providerStatus||providers.some(p=>!d.metrics.providerStatus[p]||!count(d.metrics.providerStatus[p].valid)||!Array.isArray(d.metrics.providerStatus[p].errorCodes)))throw Error('Missing provider status');
 if(!Array.isArray(d.limitations)||d.limitations.length>20||d.limitations.some(x=>typeof x!=='string'||x.length>500))throw Error('Invalid limitations');
 return d;
}
export function renderDecisions(d,connected=true){
 const names={laya:'Local Laya',openai:'OpenAI Decisions',qwen:'Qwen + rubric proxy'};
 const groups=tasks.map(task=>{
  const rows=d.metrics.summaries.filter(s=>s.task===task&&s.split==='heldout');
  const bars=rows.map(s=>`<div class="bar-row"><span>${names[s.provider]}</span><div class="bar-track"><div class="bar" data-decision-width="${100*(s.endToEndAccuracy??0)}"></div></div><span>${s.valid?s.matched+'/'+s.requested:'No answers'}</span></div>`).join('');
  return `<div class="section"><h3>${task==='coverage'?'Requirement-to-test coverage':'Smoke candidate decisions'}</h3><p>Held-out exact label matches / requested. ${rows[0].uniqueCases} independent case(s), ${d.repeats} repetitions. Errors and unrun cases remain in the denominator.</p>${bars}<div class="table-wrap"><table><thead><tr><th>Model</th><th>Valid / requested</th><th>Valid-label accuracy</th><th>p50 / p95</th><th>Errors / refusals / excluded / unrun</th><th>Routed review</th></tr></thead><tbody>${rows.map(s=>`<tr><td>${names[s.provider]}</td><td>${s.valid}/${s.requested}</td><td>${rate(s.accuracy)}</td><td>${millis(s.p50Ms)} / ${millis(s.p95Ms)}</td><td>${s.errors} / ${s.refusals} / ${s.excluded} / ${s.notRun}</td><td>${s.routedReview}/${s.valid}</td></tr>`).join('')}</tbody></table></div>${task==='coverage'?`<p>${rows.map(s=>`${names[s.provider]}: gap precision ${rate(s.gapPrecision)}, recall ${rate(s.gapRecall)}, false-covered ${s.valid?s.falseCovered:'unavailable'}, unknown-as-covered ${s.valid?s.unknownAsCovered:'unavailable'}`).join('<br>')}</p>`:''}</div>`;
 }).join('');
 return `<div class="detail-head"><div><div class="eyebrow">PLAYWRIGHT DECISION BENCH / SYNTHETIC PILOT</div><h2>Coverage and smoke selection</h2><p>Local Laya · OpenAI Decisions · Qwen rubric proxy</p></div><a href="https://github.com/balajiregt/playwright-decision-bench" target="_blank" rel="noopener noreferrer">Project and protocol ↗</a></div><p class="notice">Author-labeled examples; independent review pending. This small pilot cannot establish a winner. ${d.metrics.providerStatus.openai.valid===0?'OpenAI has no valid answers in this run; direct API credentials are required for a new comparison.':''} Qwen is a model baseline, not a measured Copilot/Claude agent workflow. ${connected?'':'Live feed unavailable; showing a saved snapshot that may be out of date.'}</p>${groups}<div class="section"><h3>Whole-suite constraints</h3><p>Both development and held-out suites are shown. Feasible means a proposal preserves reviewed journey annotations, dependencies and the authored serial-time budget. Every proposal still needs lead review.</p><div class="table-wrap"><table><thead><tr><th>Provider</th><th>Suite / split / repeat</th><th>Result</th><th>Selected / total</th><th>Journey candidates</th><th>Estimated serial time</th></tr></thead><tbody>${d.metrics.suites.map(s=>`<tr><td>${names[s.provider]}</td><td>${esc(s.suiteId)} / ${s.split} / ${s.repeat}</td><td>${s.feasible?'Feasible proposal':'Needs review / infeasible'}</td><td>${s.selected.length}/${s.totalTests}</td><td>${s.retainedJourneys}/${s.mandatoryJourneys}</td><td>${millis(s.estimatedSerialMs)}</td></tr>`).join('')}</tbody></table></div><p>On infeasible rows, journey counts describe diagnostic candidates, not an approved suite. Duration values are synthetic estimates. Actual Playwright runtime reduction and fault-detection retention remain unmeasured.</p></div><details><summary>Cost, repeatability and provenance</summary><p>${providers.map(p=>`${names[p]}: ${d.metrics.providerStatus[p].attempted} attempted, ${d.metrics.providerStatus[p].valid} valid; errors ${esc(d.metrics.providerStatus[p].errorCodes.join(", ")||"none")}`).join("<br>")}</p><div class="table-wrap"><table><thead><tr><th>Model / task / split</th><th>Reported cost</th><th>Calls with cost</th><th>Stable / repeated cases</th><th>Warm p50 / samples</th></tr></thead><tbody>${d.metrics.summaries.map(s=>`<tr><td>${names[s.provider]} / ${s.task} / ${s.split}</td><td>${s.reportedCostUsd===null?'Unavailable':'$'+s.reportedCostUsd.toFixed(6)}</td><td>${s.costReportedCalls}/${s.valid}</td><td>${s.stableCases}/${s.repeatableCases}</td><td>${millis(s.warmP50Ms)} / ${s.warmLatencySamples}</td></tr>`).join('')}</tbody></table></div><ul>${d.limitations.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><p>Protocol ${esc(d.protocol)} · ${esc(d.generatedAt)}<br>Dataset <code>${esc(d.datasetHash)}</code><br>Gold labels <code>${esc(d.goldHash)}</code></p><a href="${FEED}" target="_blank" rel="noopener noreferrer">Public aggregate and runtime metadata ↗</a></details>`;
}
export async function loadDecisions(fetcher=fetch){
 let connected=false;
 try{const r=await fetcher(FEED+'?minute='+Math.floor(Date.now()/60000),{cache:'no-store',signal:AbortSignal.timeout(12000)});if(!r.ok)throw Error();const text=await r.text();if(text.length>100000)throw Error();current=validateDecisions(JSON.parse(text));connected=true;}catch{}
 if(!current)try{const r=await fetcher('/data/decisions.json');if(r.ok)current=validateDecisions(await r.json());}catch{}
 const panel=document.getElementById('decision-bench');if(current&&panel){panel.innerHTML=renderDecisions(current,connected);for(const bar of panel.querySelectorAll('[data-decision-width]'))bar.style.width=bar.dataset.decisionWidth+'%';}
 return connected;
}
export const getPublicDecisions=()=>current?structuredClone(current):null;
