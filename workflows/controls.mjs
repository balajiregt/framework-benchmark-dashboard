import fs from 'node:fs';
import path from 'node:path';

/** Counters reserve budget before work begins. A failed attempt still consumes it. */
export class Budget {
 constructor(limits, clock=Date.now) { this.limits=limits;this.clock=clock;this.start=clock();this.models=0;this.tools=0;this.snapshots=new Map(); }
 remaining() { return Math.max(0,this.limits.wallMs-(this.clock()-this.start)); }
 check() { if(!this.remaining())throw Error('wall-budget'); }
 take(kind) {
  this.check();const key=kind==='model'?'models':'tools',cap=kind==='model'?this.limits.modelResponses:this.limits.toolCalls;
  if(this[key]>=cap)throw Error(kind+'-budget');return ++this[key];
 }
 verification(hash) {
  this.check();if(this.snapshots.has(hash))return {cycle:this.snapshots.get(hash),reused:true};
  if(this.snapshots.size>=this.limits.verificationCycles)throw Error('verification-budget');
  const cycle=this.snapshots.size+1;this.snapshots.set(hash,cycle);return {cycle,reused:false};
 }
}

export function confinedPath(root,relative,{write=false,sourceEditsAllowed=false,allowedSourceRoots=[]}={}) {
 if(typeof relative!=='string'||path.isAbsolute(relative)||relative.split(/[\\/]/).includes('..'))throw Error('Repository-relative path required');
 const p=path.resolve(root,relative);
 if(p!==root&&!p.startsWith(root+path.sep))throw Error('Outside workspace');
 if(relative.split(/[\\/]/).some(x=>['.git','target','.tmp','.home'].includes(x)))throw Error('Generated/private path is not exposed');
 let current=p;while(!fs.existsSync(current))current=path.dirname(current);
 const real=fs.realpathSync(current);if(real!==root&&!real.startsWith(root+path.sep))throw Error('External link blocked');
 if(write){
  if(!sourceEditsAllowed)throw Error('Read-only scenario validation: source edits prohibited');
  const normalized=path.relative(root,p);
  if(!normalized.endsWith('.java')||!allowedSourceRoots.some(x=>normalized.startsWith(x.endsWith('/')?x:x+'/')))throw Error('Source edit outside task scope');
 }
 return p;
}

/** Adapt only the host-specific discovery boilerplate; the framework skill is unchanged. */
export function skillInstructions(text) {
 return text.replace('Use the read tool', 'Use the repo_read tool')
  .replace("When a skill file references a relative path, resolve it against the skill directory (parent of SKILL.md / dirname of the path) and use that absolute path in tool commands.", "When a skill references a relative path, resolve it against the skill directory and express the result relative to this repository. Use repository-relative paths with repo_read.");
}
