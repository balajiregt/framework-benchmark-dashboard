import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {validateFeed,refreshFeeds} from '../public/feeds.js';
const seed=JSON.parse(fs.readFileSync(new URL('../public/data/benchmarks.json',import.meta.url)));
const envelope=run=>({schemaVersion:1,project:run.project,run,history:[run]});
test('unavailable feeds retain previous data and visibly flag disconnection',async()=>{
 const result=await refreshFeeds(seed,async()=>{throw Error('offline');});assert.deepEqual(result.dataset.runs,seed.runs);assert.ok(Object.values(result.states).every(s=>!s.connected));
});
test('each successful feed replaces current data without a rebuild',async()=>{
 const result=await refreshFeeds(seed,async url=>{const run=seed.runs.find(r=>url.includes(r.repository.split('/').at(-1)+'/'));return {ok:true,text:async()=>JSON.stringify(envelope({...run,runId:'1234567890abcdef',status:'failed'}))};});
 assert.ok(result.dataset.runs.every(r=>r.status==='failed'));assert.ok(Object.values(result.states).every(s=>s.connected));assert.equal(seed.runs[0].status,'passed');
});
test('feed identity and unsafe links are rejected',()=>{
 const run=seed.runs[0];assert.throws(()=>validateFeed(envelope({...run,repository:'javascript:alert(1)'}),run.project));assert.throws(()=>validateFeed(envelope(run),'api'));
});
test('blocked evaluations cannot claim measured accuracy',()=>{
 const run=structuredClone(seed.runs.find(r=>r.project==='jev'));run.metrics.find(m=>m.label==='Issue precision').value=1;assert.throws(()=>validateFeed(envelope(run),'jev'));
});
