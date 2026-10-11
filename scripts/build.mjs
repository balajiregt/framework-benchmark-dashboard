import fs from 'node:fs';
const data=JSON.parse(fs.readFileSync('public/data/benchmarks.json','utf8'));
if(data.schemaVersion!==1||data.runs.length!==4||new Set(data.runs.map(r=>r.project)).size!==4)throw Error('Require four unique benchmark records');
for(const file of ['public/data/benchmarks.json','public/app.js','public/index.html'])if(/\/Users\/|AI_GATEWAY_API_KEY|resumeHash|reviewerEvidence|sk-[A-Za-z0-9]{15}/.test(fs.readFileSync(file,'utf8')))throw Error('Private content detected in deploy assets');
fs.rmSync('dist',{recursive:true,force:true});fs.cpSync('public','dist',{recursive:true});console.log('Built reviewed static dashboard: four projects, '+data.history.length+' historical records.');
