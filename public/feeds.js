// Public, repository-scoped result feeds. No tokens and no browser-side writes.
export const repos={mockserver:'plawright-role-aware-mockserver',harness:'playwright-harness-framework',api:'agentic-workspace'};
export const feedURL=id=>`https://raw.githubusercontent.com/balajiregt/${repos[id]}/benchmark-results/latest.json`;
export function validateRun(run,id){
  if(!run || run.project!==id || run.repository!==`https://github.com/balajiregt/${repos[id]}` || run.protocol!==run.repository+'/blob/main/benchmarks/README.md')throw Error('Feed identity or source link mismatch');
  if(!/^[a-f0-9]{16}$/.test(run.runId)||!['passed','failed','blocked','partial','completed','unavailable'].includes(run.status)||!['verified','invalid'].includes(run.integrity))throw Error('Invalid run identity or state');
  for(const key of ['checks','cases','metrics','limitations'])if(!Array.isArray(run[key])||run[key].length>2000)throw Error('Invalid result collection');
  if(!run.checks.every(c=>typeof c.ok==='boolean')||!run.metrics.every(m=>m.value===null||(typeof m.value==='number'&&Number.isFinite(m.value)&&m.value>=0)))throw Error('Invalid check or metric');
  if(run.integrity==='verified'&&!run.checks.every(c=>c.ok))throw Error('Contradictory integrity');
  if((run.evidence??[]).some(e=>!/^[a-f0-9]{64}$/.test(e.sha256)))throw Error('Invalid evidence fingerprint');
  if(run.runAt!==null&&!Number.isFinite(Date.parse(run.runAt)))throw Error('Invalid attempt timestamp');
  if(run.agentTrials){
    const t=run.agentTrials,number=v=>typeof v==='number'&&Number.isFinite(v)&&v>=0;
    if(!['liveTrials','scriptedValidations','pairedRepeats','invalidRecords'].every(k=>number(t[k]))||!Array.isArray(t.groups))throw Error('Invalid trial aggregates');
    for(const g of t.groups)for(const arm of ['baseline','framework']){
      const a=g[arm];if(!a||!number(a.trials)||!number(a.correct)||!['medianElapsedMs','medianHumanCorrectionMs','medianIncorrectChanges'].every(k=>a[k]===null||number(a[k]))||!a.estimatedCostByCurrency||!Object.entries(a.estimatedCostByCurrency).every(([c,v])=>/^[A-Z]{3}$/.test(c)&&number(v)))throw Error('Invalid trial measurement');
    }
  }
  return run;
}
export function validateFeed(data,id){
  if(data.schemaVersion!==1||data.project!==id||!Array.isArray(data.history)||data.history.length>50)throw Error('Invalid feed envelope');
  validateRun(data.run,id);data.history.forEach(r=>validateRun(r,id));
  if(!data.history.some(r=>r.runId===data.run.runId))throw Error('Latest attempt missing from history');
  return data;
}
export async function refreshFeeds(dataset,fetcher=fetch){
  const results=await Promise.all(Object.keys(repos).map(async id=>{
    try{
      const response=await fetcher(feedURL(id)+'?minute='+Math.floor(Date.now()/60000),{cache:'no-store',signal:AbortSignal.timeout(12000)});
      if(!response.ok)throw Error('HTTP '+response.status);
      const text=await response.text();if(text.length>2000000)throw Error('Oversized feed');
      return {id,feed:validateFeed(JSON.parse(text),id)};
    }catch{return {id,error:true};}
  }));
  const merged=structuredClone(dataset),states={};const history=new Map(merged.history.map(r=>[r.project+':'+r.runId,r]));
  for(const result of results){
    states[result.id]={connected:!result.error,checkedAt:new Date().toISOString()};
    if(result.error)continue;
    merged.runs=merged.runs.map(r=>r.project===result.id?result.feed.run:r);
    for(const r of result.feed.history)history.set(r.project+':'+r.runId,r);
  }
  merged.history=[...history.values()].sort((a,b)=>(a.runAt??'').localeCompare(b.runAt??'')).slice(-200);
  return {dataset:merged,states};
}
