import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {validateConfig,validateAggregate,validateRegistry,validateMetricsFeed,sourceURL} from '../public/platform-contract.mjs';
import {prepare,validatePrepared,mergeFeed,publishToGit,digest} from '../.agents/skills/platform-publish/scripts/publisher.mjs';
import {registry,registeredSource,runtimeProjectIds} from '../public/platform-registry.mjs';
import {readStandardMetrics} from '../public/platform-client.mjs';

const root=path.resolve(import.meta.dirname,'..');
const skill=path.join(root,'.agents/skills/platform-publish');
const load=file=>JSON.parse(fs.readFileSync(path.join(skill,'references',file),'utf8'));
const policy=()=>load('example-policy.json'), input=()=>load('example-measurements.json');
const clone=structuredClone;
function git(args,cwd) {const r=spawnSync('git',args,{cwd,encoding:'utf8'});assert.equal(r.status,0,r.stderr);return r.stdout.trim();}
function fixtureEntry() {return {id:'example-project',title:'Example',description:'Synthetic integration fixture.',kind:'experiment',repository:policy().repository,demoUrl:null,route:'/projects/example-project',sources:[{id:'metrics',format:'metrics-v1',repository:policy().repository,branch:'platform-results',path:'metrics.json',legacyProject:null}]};}

test('portable and browser validators are the same implementation',()=>{
 assert.equal(fs.readFileSync(path.join(skill,'scripts/contract.mjs'),'utf8'),fs.readFileSync(path.join(root,'public/platform-contract.mjs'),'utf8'));
});
test('a new project registers and its metrics load without changing renderer or legacy records',async()=>{
 const r=clone(registry), entry=fixtureEntry();r.projects.push(entry);validateRegistry(r);
 const aggregate=prepare(policy(),input()),feed=mergeFeed(null,aggregate);let requested;
 const result=await readStandardMetrics(entry,{fetcher:async url=>{requested=url;return {ok:true,text:async()=>JSON.stringify(feed)};}});
 assert.equal(result.state,'connected');assert.equal(result.feed.runs[0].projectId,entry.id);
 assert.equal(requested,'https://raw.githubusercontent.com/example-owner/example-project/platform-results/metrics.json');
 assert.deepEqual([...runtimeProjectIds].sort(),['api','harness','mockserver']);
});
test('registry rejects duplicate identities/routes, unknown related projects and unsafe origins',()=>{
 for (const mutate of [r=>r.projects.push(clone(r.projects[0])),r=>r.projects[0].route='/projects/wrong',r=>r.analyses[0].projectIds=['not-registered'],r=>r.projects[0].repository='https://github.com/example/repo?token=private',r=>r.projects[0].sources[0].path='../private.json',r=>r.projects[0].sources[0].repository='https://github.com/other/repo',r=>r.projects[1].sources[0].legacyProject='api']) {
  const r=clone(registry);mutate(r);assert.throws(()=>validateRegistry(r));
 }
});
test('all currently used source locations are registered, including specialised feeds',()=>{
 assert.equal(registeredSource('agentic-api','runtime').url,'https://raw.githubusercontent.com/balajiregt/agentic-workspace/benchmark-results/latest.json');
 assert.ok(registeredSource('playwright-decision-bench','comparison').url.endsWith('/comparison-metrics.json'));
 assert.ok(registeredSource('framework-impact','impact').url.endsWith('/framework-impact.json'));
 assert.throws(()=>registeredSource('unknown','runtime'));
});
test('prepare preserves unavailable values, measurement units and policy provenance',()=>{
 const p=policy(),d=prepare(p,input());assert.equal(d.metrics[2].value,null);assert.equal(d.metrics[2].state,'unavailable');
 assert.equal(d.metrics[0].sampleSize,5);assert.equal(d.policyHash,digest(p));assert.equal(validatePrepared(d,p),d);
});
test('source input is a closed numeric export and cannot carry report text or extra keys',()=>{
 for(const mutate of [d=>d.rawReport='private',d=>d.values['passed-cases'].value='private text',d=>d.values['passed-cases'].prompt='private',d=>delete d.values.duration,d=>d.values['unknown']={value:1,state:'measured',sampleSize:1}]) {const d=input();mutate(d);assert.throws(()=>prepare(policy(),d));}
});
test('policy rejects source branches, mismatched publisher versions and credential-bearing URLs',()=>{
 for(const mutate of [p=>p.branch='main',p=>p.feedPath='../latest.json',p=>p.publisherVersion='2.0.0',p=>p.repository='https://user:secret@github.com/owner/repo',p=>p.methodologyUrl='https://example.com?token=secret',p=>p.limitations=['api_key=private-value'],p=>p.metrics.push(clone(p.metrics[0]))]) {const p=policy();mutate(p);assert.throws(()=>validateConfig(p));}
});
test('invalid measurements are rejected rather than coerced or given guessed denominators',()=>{
 for(const mutate of [d=>d.values.duration.value=NaN,d=>d.values.duration.value=Infinity,d=>d.values.duration.value=-1,d=>d.values['passed-cases'].value=1.5,d=>d.values.accuracy={value:1.1,state:'measured',sampleSize:4},d=>d.values.duration.sampleSize=0,d=>d.values.duration.sampleSize=-1,d=>d.values.accuracy.value=0,d=>d.observedAt='2026-02-30T00:00:00.000Z']) {const d=input();mutate(d);assert.throws(()=>prepare(policy(),d));}
});
test('blocked evidence cannot claim results; failed evidence can retain real measurements',()=>{
 const d=input();d.status='blocked';assert.throws(()=>prepare(policy(),d));
 for(const key of Object.keys(d.values))d.values[key]={value:null,state:'unavailable',sampleSize:null};
 assert.equal(prepare(policy(),d).status,'blocked');d.status='failed';d.values.duration={value:100,state:'measured',sampleSize:1};assert.equal(prepare(policy(),d).metrics[1].value,100);
});
test('tampering or changing a reviewed policy invalidates prepared exports',()=>{
 const p=policy(),d=prepare(p,input());d.metrics[0].value=99;assert.throws(()=>validatePrepared(d,p));
 const original=prepare(p,input());p.metrics[0].label='Different meaning';assert.throws(()=>validatePrepared(original,p));
});
test('history is idempotent, bounded and ordered by observation rather than publishing time',()=>{
 const p=policy(),recent=prepare(p,input()),older=input();older.observedAt='2026-10-01T00:00:00.000Z';
 const first=mergeFeed(null,recent),second=mergeFeed(first,prepare(p,older));assert.equal(second.runs[0].runId,recent.runId);assert.equal(mergeFeed(second,recent).runs.length,2);
 let feed=null;for(let n=0;n<55;n++){const d=input();d.observedAt=new Date(Date.UTC(2026,8,1,n)).toISOString();feed=mergeFeed(feed,prepare(p,d));}assert.equal(feed.runs.length,50);
});
test('feeds reject wrong identities, mixed origins and duplicate rows',()=>{
 const d=prepare(policy(),input()),f=mergeFeed(null,d);
 assert.throws(()=>validateMetricsFeed(f,'other',policy().repository));
 const mixed=clone(f);mixed.runs[0].source.repository='https://github.com/other/repo';assert.throws(()=>validateMetricsFeed(mixed,d.projectId,policy().repository));
 f.runs.push(d);assert.throws(()=>validateMetricsFeed(f,d.projectId,policy().repository));
});
test('offline, malformed and rollback refreshes retain accepted data with explicit stale state',async()=>{
 const e=fixtureEntry(),f=mergeFeed(null,prepare(policy(),input()));
 for(const fetcher of [async()=>{throw Error('offline');},async()=>({ok:true,text:async()=>'{not json'}),async()=>({ok:true,text:async()=>JSON.stringify({...f,runs:[]})})]) {
  const r=await readStandardMetrics(e,{previous:f,fetcher});assert.equal(r.state,'stale');assert.deepEqual(r.feed,f);
 }
 assert.equal((await readStandardMetrics(e,{fetcher:async()=>{throw Error();}})).state,'unavailable');
 assert.equal((await readStandardMetrics({...e,sources:[]})).state,'not-configured');
});
test('real Git publication preserves unrelated files, deduplicates and handles a concurrent publisher',()=>{
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'platform-test-'));
 const actions=process.env.GITHUB_ACTIONS;delete process.env.GITHUB_ACTIONS;
 try {
  const remote=path.join(folder,'remote.git');git(['init','--bare',remote],folder);
  const p=policy(),d=prepare(p,input());
  assert.equal(publishToGit(p,d,{remote}).status,'published');const head=git(['rev-parse','platform-results'],remote);
  assert.equal(publishToGit(p,d,{remote}).status,'already-published');assert.equal(git(['rev-parse','platform-results'],remote),head);
  const competitor=input();competitor.observedAt='2026-10-31T00:01:00.000Z';const second=prepare(p,competitor);
  const late=input();late.observedAt='2026-10-30T00:00:00.000Z';const third=prepare(p,late);
  assert.equal(publishToGit(p,third,{remote,beforePush:n=>{if(n===0)publishToGit(p,second,{remote});}}).status,'published');
  const result=JSON.parse(git(['show','platform-results:metrics.json'],remote));assert.equal(result.runs.length,3);assert.equal(result.runs[0].runId,second.runId);
  // Add another producer's file and ensure the next metrics update preserves it.
  const checkout=path.join(folder,'checkout');git(['clone','--branch','platform-results',remote,checkout],folder);
  fs.writeFileSync(path.join(checkout,'other.json'),'{}\n');git(['add','other.json'],checkout);git(['-c','user.name=Test','-c','user.email=test@example.com','commit','-m','Other producer'],checkout);git(['push','origin','platform-results'],checkout);
  const fourth=input();fourth.observedAt='2026-10-31T00:02:00.000Z';publishToGit(p,prepare(p,fourth),{remote});assert.equal(git(['show','platform-results:other.json'],remote),'{}');
 } finally {if(actions!==undefined)process.env.GITHUB_ACTIONS=actions;fs.rmSync(folder,{recursive:true,force:true});}
});
test('a poisoned symlink feed fails before writing or pushing',()=>{
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'platform-link-test-'));
 const actions=process.env.GITHUB_ACTIONS;delete process.env.GITHUB_ACTIONS;
 try {
  const remote=path.join(folder,'remote.git'),repo=path.join(folder,'repo');git(['init','--bare',remote],folder);git(['init',repo],folder);git(['checkout','-b','platform-results'],repo);
  fs.symlinkSync('/tmp/private-metrics.json',path.join(repo,'metrics.json'));git(['add','.'],repo);git(['-c','user.name=Test','-c','user.email=test@example.com','commit','-m','Symlink'],repo);git(['remote','add','origin',remote],repo);git(['push','origin','platform-results'],repo);
  const head=git(['rev-parse','platform-results'],remote);assert.throws(()=>publishToGit(policy(),prepare(policy(),input()),{remote}),/regular JSON/);assert.equal(git(['rev-parse','platform-results'],remote),head);
 } finally {if(actions!==undefined)process.env.GITHUB_ACTIONS=actions;fs.rmSync(folder,{recursive:true,force:true});}
});
test('portable CLI previews offline, refuses overwrite and requires explicit publication flag',()=>{
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'platform-cli-test-'));
 try {
  const cli=path.join(skill,'scripts/cli.mjs'),config=path.join(skill,'references/example-policy.json'),measurements=path.join(skill,'references/example-measurements.json'),output=path.join(folder,'prepared.json');
  const call=args=>spawnSync(process.execPath,[cli,...args],{encoding:'utf8'});
  assert.equal(call(['prepare','--config',config,'--input',measurements,'--output',output]).status,0);
  assert.equal(call(['validate','--config',config,'--input',output]).status,0);
  assert.equal(call(['prepare','--config',config,'--input',measurements,'--output',output]).status,1);
  assert.equal(call(['publish','--config',config,'--input',output]).status,1);
  const d=input();d.privateNote='do-not-print-this-value';const bad=path.join(folder,'bad.json');fs.writeFileSync(bad,JSON.stringify(d));const r=call(['prepare','--config',config,'--input',bad,'--output',path.join(folder,'bad-output.json')]);assert.equal(r.status,1);assert.ok(!r.stderr.includes('do-not-print-this-value'));assert.ok(!fs.existsSync(path.join(folder,'bad-output.json')));
 } finally {fs.rmSync(folder,{recursive:true,force:true});}
});
