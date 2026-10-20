import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateDecisions,renderDecisions} from '../public/decisions.js';
const seed=JSON.parse(fs.readFileSync(new URL('../public/data/decisions.json',import.meta.url)));
test('measured decision pilot has bounded provenance and consistent denominators',()=>{assert.equal(validateDecisions(seed),seed);});
test('preview output cannot become a measured public comparison',()=>{assert.throws(()=>validateDecisions({...seed,mode:'preview'}));});
test('inflated scores and hidden operational failures are rejected',()=>{
 const d=structuredClone(seed);d.metrics.summaries[0].matched=999;assert.throws(()=>validateDecisions(d));
 const e=structuredClone(seed);e.metrics.summaries.find(s=>s.notRun>0).notRun=0;assert.throws(()=>validateDecisions(e));
});
test('infeasible smoke suites cannot be represented as approved',()=>{const d=structuredClone(seed);const s=d.metrics.suites.find(s=>!s.feasible);s.feasible=true;assert.throws(()=>validateDecisions(d));});
test('synthetic estimates cannot be upgraded to actual Playwright runtime',()=>{const d=structuredClone(seed);d.metrics.suites[0].runtimeReduction=.5;assert.throws(()=>validateDecisions(d));});
test('unavailable model answers remain unavailable and text is escaped',()=>{
 const d=structuredClone(seed);d.limitations.push('<script>alert(1)</script>');const html=renderDecisions(d,false);
 assert.ok(html.includes('No answers'));assert.ok(html.includes('Live feed unavailable'));assert.ok(html.includes('&lt;script&gt;'));assert.ok(!html.includes('<script>'));
});
