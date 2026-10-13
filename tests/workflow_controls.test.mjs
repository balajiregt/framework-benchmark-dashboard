import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {Budget,confinedPath,skillInstructions} from '../workflows/controls.mjs';

test('budgets stop before the next model/tool call and count failed reservations',()=>{
 let clock=0;const b=new Budget({wallMs:100,modelResponses:2,toolCalls:1,verificationCycles:3},()=>clock);
 assert.equal(b.take('model'),1);assert.equal(b.take('model'),2);assert.throws(()=>b.take('model'),/model-budget/);
 assert.equal(b.take('tool'),1);assert.throws(()=>b.take('tool'),/tool-budget/);
 clock=100;assert.throws(()=>b.verification('new'),/wall-budget/);
});
test('verification retries count distinct snapshots and cannot bypass three-cycle limit',()=>{
 const b=new Budget({wallMs:100,verificationCycles:3},()=>0);
 assert.deepEqual(b.verification('A'),{cycle:1,reused:false});
 assert.deepEqual(b.verification('A'),{cycle:1,reused:true});
 assert.equal(b.verification('B').cycle,2);assert.equal(b.verification('C').cycle,3);
 assert.throws(()=>b.verification('D'),/verification-budget/);
 assert.equal(b.verification('B').reused,true);
});
test('path guard blocks traversal, symlinks, generated content and read-only edits',()=>{
 const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'workflow-controls-')),root=fs.realpathSync(tmp);
 try{
  fs.mkdirSync(path.join(root,'qa'));fs.symlinkSync(os.tmpdir(),path.join(root,'escape'));
  const edit={write:true,sourceEditsAllowed:true,allowedSourceRoots:['qa/']};
  assert.equal(confinedPath(root,'qa/Test.java',edit),path.join(root,'qa/Test.java'));
  for(const p of ['../grader.json','/etc/passwd','escape/grader.json','target/secret','qa/../product/X.java','qa-adjacent/X.java'])assert.throws(()=>confinedPath(root,p,edit));
  assert.throws(()=>confinedPath(root,'qa/Test.java',{...edit,sourceEditsAllowed:false}),/Read-only/);
  assert.throws(()=>confinedPath(root,'qa/pom.xml',edit),/scope/);
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});

test('skill discovery matches the bounded host tool and path interface',()=>{
 const stock="Use the read tool to load a skill's file when the task matches its description.\nWhen a skill file references a relative path, resolve it against the skill directory (parent of SKILL.md / dirname of the path) and use that absolute path in tool commands.";
 const adapted=skillInstructions(stock);assert.match(adapted,/repo_read/);assert.match(adapted,/repository-relative/);assert.doesNotMatch(adapted,/absolute path|Use the read tool/);
});

test('TypeScript writes require explicit extension and owning-root scope',()=>{
 const root=fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'impact-scope-')));
 try {
  assert.throws(()=>confinedPath(root,'tests/example.ts',{write:true,sourceEditsAllowed:true,allowedSourceRoots:['tests/']}));
  assert.equal(confinedPath(root,'tests/example.ts',{write:true,sourceEditsAllowed:true,allowedSourceRoots:['tests/'],allowedExtensions:['.ts']}),path.join(root,'tests/example.ts'));
  assert.throws(()=>confinedPath(root,'examples/app.ts',{write:true,sourceEditsAllowed:true,allowedSourceRoots:['tests/'],allowedExtensions:['.ts']}));
  assert.throws(()=>confinedPath(root,'.runtime/config.ts'));
 } finally {fs.rmSync(root,{recursive:true,force:true});}
});
