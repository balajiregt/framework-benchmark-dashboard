import test from 'node:test';
import assert from 'node:assert/strict';
import {renderComparisonMetrics,validateComparisonFeed} from '../public/comparisons.js';
const q={reviewedPairs:0,correct:0,accuracy:null,predictedCovered:0,referenceCovered:0,trueCovered:0,falseCovered:0,precision:null,recall:null};
function fixture(){
 const p={modelVersion:'unverified',modelConfigHash:'a'.repeat(64),counts:{pairs:1,valid:1,excluded:0,errors:0,notRun:0,uncertain:0,lowProbability:0},performance:{startupMs:10,wallMs:100,p50Ms:100,p95Ms:100,modelPeakRssBytes:1000,inputTokens:300,outputTokens:12,estimatedApiCostUsd:null},quality:{...q},commonQuality:{...q},smoke:{selected:0,reviewCandidates:1,critical:1,estimatedCovered:0,missing:1,dependencyConflicts:0,estimatedSerialMs:null,execution:null,approved:false}};
 return {schemaVersion:2,protocol:'jev-laya-comparison-v1',datasetKind:'synthetic-fixture',runId:'00000000-0000-4000-8000-000000000001',generatedAt:'2026-10-20T00:00:00.000Z',inventoryHash:'b'.repeat(64),requirementsHash:'c'.repeat(64),requirements:1,tests:1,hardware:{platform:'darwin',arch:'arm64',ramBytes:8589934592},policy:{minProbability:.8,minPassRate:.98,minRuns:3,budgetMs:300000},commonPairs:1,disagreements:0,providers:{laya:p,jev:structuredClone(p)}};
}
test('paired aggregate rendering separates missing accuracy, completion and unexecuted smoke',()=>{
 const html=renderComparisonMetrics(fixture());assert.match(html,/identically assessed pairs/);assert.match(html,/Unavailable/);assert.match(html,/Not executed/);assert.match(html,/No release approval/);
});
test('comparison feed rejects source leakage and duplicate or contradictory runs',()=>{
 const d=fixture();assert.equal(validateComparisonFeed({schemaVersion:1,runs:[d]}).runs.length,1);
 assert.throws(()=>validateComparisonFeed({schemaVersion:1,runs:[d,d]}));
 const privateData=structuredClone(d);privateData.providers.jev.performance.source='private';assert.throws(()=>renderComparisonMetrics(privateData));
 const inflated=structuredClone(d);inflated.commonPairs=2;assert.throws(()=>renderComparisonMetrics(inflated));
});
