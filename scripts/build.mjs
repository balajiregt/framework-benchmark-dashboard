import {registry,runtimeProjectIds} from '../public/platform-registry.mjs';
import {execFileSync} from 'node:child_process';
execFileSync(process.execPath,['scripts/sync-platform-contract.mjs','--check']);
execFileSync(process.execPath,['scripts/package-platform-skill.mjs','--check']);
import fs from 'node:fs';
import {validateDecisions} from '../public/decisions.js';
validateDecisions(JSON.parse(fs.readFileSync('public/data/decisions.json','utf8')));
import {validateImpact} from '../public/impact.js';
validateImpact(JSON.parse(fs.readFileSync('public/data/impact.json','utf8')));
const data=JSON.parse(fs.readFileSync('public/data/benchmarks.json','utf8'));
if(data.schemaVersion!==1||data.runs.length!==runtimeProjectIds.length||new Set(data.runs.map(r=>r.project)).size!==runtimeProjectIds.length||data.runs.some(r=>!runtimeProjectIds.includes(r.project)))throw Error('Require one unique record per registered runtime source');
for(const name of fs.readdirSync('public',{recursive:true})){const file='public/'+name;if(!fs.statSync(file).isFile())continue;if(/\/Users\/|AI_GATEWAY_API_KEY|resumeHash|reviewerEvidence|sk-[A-Za-z0-9]{15}/.test(fs.readFileSync(file,'utf8')))throw Error('Private content detected in deploy assets');}
for(const name of fs.readdirSync('public',{recursive:true})){if(name.endsWith('.svg')&&/<style\b|\sstyle\s*=/i.test(fs.readFileSync('public/'+name,'utf8')))throw Error('SVG inline styles are blocked by the site CSP; use presentation attributes: '+name);}
fs.rmSync('dist',{recursive:true,force:true});fs.cpSync('public','dist',{recursive:true});fs.mkdirSync('dist/contracts',{recursive:true});
fs.copyFileSync('.agents/skills/platform-publish/references/metrics-v1.schema.json','dist/contracts/metrics-v1.schema.json');
console.log('Built reviewed static dashboard: '+registry.projects.length+' registered projects, '+runtimeProjectIds.length+' legacy runtime feeds, '+data.history.length+' historical records.');
