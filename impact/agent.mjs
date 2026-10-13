/** Pi agent host with explicit resources, bounded tools and recorded provider requests. */
import fs from 'node:fs';
import {Budget,confinedPath,skillInstructions} from '../workflows/controls.mjs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const config=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const pkg=config.piPackage;
const pi=await import(pathToFileURL(path.join(pkg,'dist/index.js')));
const ai=await import(pathToFileURL(path.join(pkg,'node_modules/@mariozechner/pi-ai/dist/index.js')));
const {Type}=await import(pathToFileURL(path.join(pkg,'node_modules/typebox/build/index.mjs')));
const root=fs.realpathSync(config.workspace), privateDir=config.privateDir,start=Date.now();
const sha=v=>createHash('sha256').update(v).digest('hex');
const event=(type,data={})=>fs.appendFileSync(path.join(privateDir,'trace.jsonl'),JSON.stringify({type,elapsedMs:Date.now()-start,...data})+'\n');
const state={modelResponses:0,toolCalls:0,verificationCycles:0,repairs:0,filesRead:[],bytesRead:0,searches:0,invalidPaths:0,edits:0,usage:[],stopReason:null,verification:[],compactions:0};
const totalAbort=new AbortController(), deadline=totalAbort.signal;
let clockLast=Date.now(),maxClockGapMs=0,responseStarted=null,responseAbort=null,stopRequested=null,finished=false;
let finalText='',lastAssistant;
let session, responseDeadline;
let worker;
deadline.addEventListener('abort',()=>{state.stopReason??='wall-budget';session?.abort();});
function check(){budget.check();if(responseAbort?.signal.aborted)throw Error(state.stopReason??'response-timeout');if(deadline.aborted){state.stopReason='wall-budget';throw Error('Total wall-time budget exhausted');}if(state.stopReason)throw Error(state.stopReason);}
const budget=new Budget(config.budget);
function safe(relative,{write=false}={}){return confinedPath(root,relative,{write,...config});}
function walk(dir=root){return fs.readdirSync(dir,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name)).flatMap(d=>d.isSymbolicLink()||['target','.tmp','.home','.git','node_modules','.runtime','.reports','playwright-report','test-results'].includes(d.name)?[]:d.isDirectory()?walk(path.join(dir,d.name)):[path.join(dir,d.name)]);}
const sourceHash=()=>sha(walk().filter(p=>(config.allowedExtensions??['.java']).some(x=>p.endsWith(x))).map(p=>path.relative(root,p)+'\0'+sha(fs.readFileSync(p))).join('\n'));
function bounded(text,max=10000){return text.length<=max?{text,truncated:false}:{text:text.slice(0,max)+'\n[Tool output truncated; request a narrower range.]',truncated:true};}
async function fixedRun(params){
 const aliases={'npm run context:resolve':'context:resolve','npm run graph:view':'graph:refresh','npm run graph:coverage':'graph:refresh','npm run sample:crm:test':'verify','npm test':'verify'}; params={...params,command:aliases[params.command]??params.command};
 if(!config.commands.includes(params.command))throw Error('Supported commands: '+config.commands.join(', ')+'. No arbitrary shell.');
 let snapshot;
 if(params.command==='verify'){
  snapshot=sourceHash();
  const reserved=budget.verification(snapshot);state.verificationCycles=budget.snapshots.size;state.repairs=Math.max(0,state.verificationCycles-1);
  if(reserved.reused){const prior=state.verification.find(v=>v.sourceHash===snapshot);if(prior)return {...prior.result,reusedVerification:true};throw Error('This verification snapshot was already attempted');}
  const archive=path.join(privateDir,'snapshots',String(reserved.cycle));fs.mkdirSync(archive,{recursive:true});for(const file of walk().filter(p=>(config.allowedExtensions??['.java']).some(x=>p.endsWith(x)))){const dest=path.join(archive,path.relative(root,file));fs.mkdirSync(path.dirname(dest),{recursive:true});fs.copyFileSync(file,dest);}
 }
 const requestFile=path.join(privateDir,'command-'+state.toolCalls+'.json');
 fs.writeFileSync(requestFile,JSON.stringify({...params,timeoutSeconds:Math.max(.1,Math.min(120,budget.remaining()/1000))}));
 const result=await new Promise((resolve,reject)=>{
  const p=worker=spawn(config.python,[config.runtime,process.argv[2],requestFile],{env:{PATH:process.env.PATH,HOME:process.env.HOME,PYTHONDONTWRITEBYTECODE:'1'},stdio:['ignore','pipe','pipe']});let out='',err='';p.stdout.on('data',b=>out+=b);p.stderr.on('data',b=>err+=b);p.on('error',reject);p.on('close',code=>{if(code)reject(Error('Fixed execution adapter failed: '+err.slice(-1000)));else{try{resolve(JSON.parse(out));}catch(e){reject(e);}}});
 });
 if(snapshot){state.verification.push({sourceHash:snapshot,cycle:state.verificationCycles,result});event('verification',{sourceHash:snapshot,cycle:state.verificationCycles,result});}
 return result;
}
function tool(name,description,parameters,execute){return pi.defineTool({name,label:name,description,parameters,execute:async(id,params)=>{
 check();if(state.toolCalls>=config.budget.toolCalls){state.stopReason='tool-budget';throw Error('Tool budget exhausted');}
 try{budget.take('tool');}catch(e){state.stopReason=e.message;throw e;}state.toolCalls=budget.tools;const begin=Date.now();event('tool_start',{name,id,params});
 try{const raw=await execute(params),value=typeof raw==='string'?raw:JSON.stringify(raw);const b=bounded(value);event('tool_end',{name,id,elapsed:Date.now()-begin,result:raw,returnedBytes:Buffer.byteLength(b.text),truncated:b.truncated});return {content:[{type:'text',text:b.text}],details:{}};}
 catch(error){if(error.message.endsWith('-budget'))state.stopReason=error.message;event('tool_error',{name,id,message:error.message});return {content:[{type:'text',text:'Tool error: '+error.message}],details:{},isError:true};}
 }});}
const customTools=[
 tool('ls','List files and folders at a repository-relative path.',Type.Object({path:Type.String()}),p=>fs.readdirSync(safe(p.path),{withFileTypes:true}).filter(d=>!['target','.tmp','.home','node_modules','.runtime','.reports','playwright-report','test-results'].includes(d.name)).map(d=>d.name+(d.isDirectory()?'/':'')).join('\n')),
 tool('find','Find file paths containing a literal substring; empty query lists all files.',Type.Object({query:Type.String()}),p=>walk().map(x=>path.relative(root,x)).filter(x=>x.includes(p.query)).slice(0,100).join('\n')),
 tool('read','Read a file. Lines are 1-based. Use offset/limit to keep context small.',Type.Object({path:Type.String(),offset:Type.Optional(Type.Number()),limit:Type.Optional(Type.Number())}),p=>{
  let file;try{file=safe(p.path);if(!fs.statSync(file).isFile())throw Error('Not a file');}catch(e){state.invalidPaths++;throw e;}
  const lines=fs.readFileSync(file,'utf8').split('\n'),offset=Math.max(1,Math.floor(p.offset??1)),limit=Math.max(1,Math.min(120,Math.floor(p.limit??80)));const text=lines.slice(offset-1,offset-1+limit).map((x,i)=>`${i+offset}: ${x}`).join('\n');
  const returned=bounded(`File ${p.path}; total lines ${lines.length}\n`+text);const row={path:p.path,offset,requestedLines:limit,bytes:Buffer.byteLength(returned.text),truncated:returned.truncated,elapsedMs:Date.now()-start};state.filesRead.push(row);state.bytesRead+=row.bytes;return returned.text;
 }),
 tool('grep','Search for literal text in repository files. Optional path narrows the search.',Type.Object({query:Type.String(),path:Type.Optional(Type.String())}),p=>{
  state.searches++;let base=safe(p.path??'.'),list=fs.statSync(base).isDirectory()?walk(base):[base],hits=[];
  for(const f of list){const text=fs.readFileSync(f,'utf8');for(const [i,line] of text.split('\n').entries())if(line.includes(p.query))hits.push(`${path.relative(root,f)}:${i+1}: ${line}`);if(hits.length>=60)break;}
  return hits.slice(0,60).join('\n');
 }),
 tool('edit','Replace one exact unique text occurrence in a permitted source file.',Type.Object({path:Type.String(),oldText:Type.String(),newText:Type.String()}),p=>{
  const file=safe(p.path,{write:true}),text=fs.readFileSync(file,'utf8');if(!p.oldText||text.split(p.oldText).length!==2)throw Error('oldText must match exactly once');fs.writeFileSync(file,text.replace(p.oldText,p.newText));state.edits++;return 'Edit applied';
 }),
 tool('write','Write a permitted source file; existing files can be replaced.',Type.Object({path:Type.String(),content:Type.String()}),p=>{const file=safe(p.path,{write:true});fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,p.content);state.edits++;return 'File written';}),
 tool('bash','Execute one documented command from SETUP.md. Commands: '+config.commands.join(', ')+'. No arbitrary shell.',Type.Object({command:Type.String(),customerId:Type.Optional(Type.String()),role:Type.Optional(Type.String()),route:Type.Optional(Type.String())}),fixedRun),
];
const common='You are a coding agent completing a bounded QA request. Read SETUP.md and TASK.md, inspect the actual source and existing coverage, perform the requested work and verify it. Use the provided tools for actual edits. bash is a controlled execution interface: use only commands in SETUP.md. Both conditions have the same application source, helpers and ordinary tools. Repository commands map to those documented commands. Always use repository-relative paths. Stay in scope; do not skip or weaken checks to hide errors. Report decision, owning files, supporting evidence, changes and actual verification. Budget: 15 minutes, 36 model calls, 80 tool calls, three verification snapshots. Stop when done or blocked; do not invent execution or human approval.';
const skill=config.arm==='context'&&config.project==='api'?pi.loadSkillsFromDir({dir:path.join(root,'skills/microservice-change'),source:'project'}):{skills:[],diagnostics:[]};
const discovery=pi.formatSkillsForPrompt(skill.skills.map(s=>({...s,filePath:'skills/microservice-change/SKILL.md'}))).replace('use that absolute path in tool commands','express the path relative to the repository in tool commands');
const loader={getExtensions:()=>({extensions:[],errors:[],runtime:pi.createExtensionRuntime()}),getSkills:()=>skill,getPrompts:()=>({prompts:[],diagnostics:[]}),getThemes:()=>({themes:[],diagnostics:[]}),getAgentsFiles:()=>({agentsFiles:[]}),getSystemPrompt:()=>common,getAppendSystemPrompt:()=>config.arm==='context'?[fs.readFileSync(path.join(root,'AGENTS.md'),'utf8'),discovery]:[],extendResources:()=>{},reload:async()=>{}};
const auth=pi.AuthStorage.create(path.join(privateDir,'auth-empty.json'));auth.setRuntimeApiKey('workflow-local','local-only');
const registry=pi.ModelRegistry.inMemory(auth);
registry.registerProvider('workflow-local',{baseUrl:'http://127.0.0.1:8080/v1',api:'openai-completions',apiKey:'local-only',models:[{id:'local-model',name:'Gemma local workflow',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:8192,maxTokens:4096,compat:{supportsDeveloperRole:false,supportsStore:false,supportsUsageInStreaming:true,maxTokensField:'max_tokens'}}]});
({session}=await pi.createAgentSession({cwd:root,agentDir:path.join(privateDir,'empty-agent'),model:registry.find('workflow-local','local-model'),thinkingLevel:'off',authStorage:auth,modelRegistry:registry,resourceLoader:loader,tools:customTools.map(t=>t.name),customTools,sessionManager:pi.SessionManager.inMemory(root),settingsManager:pi.SettingsManager.inMemory({compaction:{enabled:false},retry:{enabled:false,maxRetries:0}})}));
session.agent.toolExecution='sequential';
const failedStream=reason=>{const stream=new ai.AssistantMessageEventStream();const m={role:'assistant',content:[],api:'openai-completions',provider:'workflow-local',model:'local-model',usage:{input:0,output:0,cacheRead:0,cacheWrite:0,totalTokens:0,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}},stopReason:'error',errorMessage:reason,timestamp:Date.now()};queueMicrotask(()=>{stream.push({type:'error',reason:'error',error:m});stream.end(m);});return stream;};
session.agent.streamFn=(model,context,options)=>{
 if(state.stopReason||deadline.aborted||state.modelResponses>=config.budget.modelResponses){state.stopReason??=deadline.aborted?'wall-budget':'model-budget';return failedStream(state.stopReason);}
 try{budget.take('model');}catch(e){state.stopReason=e.message;return failedStream(e.message);}state.modelResponses=budget.models;const index=state.modelResponses;
 responseStarted=Date.now();responseAbort=new AbortController();responseDeadline=responseAbort.signal;
 return ai.streamOpenAICompletions(model,context,{...options,apiKey:'local-only',maxTokens:4096,temperature:.2,timeoutMs:180000,maxRetries:0,signal:AbortSignal.any([options.signal??new AbortController().signal,deadline,responseDeadline]),onPayload:payload=>{
  const request={...payload,seed:config.seed,cache_prompt:false};fs.writeFileSync(path.join(privateDir,`request-${index}.json`),JSON.stringify(request));event('model_request',{index,requestSha256:sha(JSON.stringify(request))});return request;
 }});
};
session.subscribe(e=>{
 if(e.type==='message_end'&&e.message.role==='assistant'){
  responseStarted=null;const m=e.message;lastAssistant=m;state.usage.push(m.stopReason==='error'||m.stopReason==='aborted'?null:m.usage);event('assistant',{message:m});
  finalText=m.content.filter(c=>c.type==='text').map(c=>c.text).join('\n');
  if(m.stopReason==='length')state.stopReason='output-limit';
  if(m.stopReason==='error'||m.stopReason==='aborted')state.stopReason??=(m.errorMessage??'provider-error').includes('context')?'context-limit':deadline.aborted?'wall-budget':responseDeadline?.aborted?'response-timeout':'provider-error';
 }
 if(e.type==='auto_compaction_start'){state.compactions++;state.stopReason='unexpected-compaction';}
});
event('bootstrap',{piVersion:JSON.parse(fs.readFileSync(path.join(pkg,'package.json'))).version,systemSha256:sha(session.systemPrompt),systemBytes:Buffer.byteLength(session.systemPrompt),tools:customTools.map(t=>t.name)});
fs.writeFileSync(path.join(privateDir,'system-prompt.txt'),session.systemPrompt);
function finish() {
 if(finished)return;finished=true;clearInterval(watchdog);
 event('clock_watchdog',{maxClockGapMs,intervalMs:100,pauseThresholdMs:10000});
 fs.writeFileSync(path.join(privateDir,'final.txt'),finalText);
 const result={...state,finalText,elapsedMs:Date.now()-start,finishedAt:new Date().toISOString(),sourceHash:sourceHash(),lastStopReason:lastAssistant?.stopReason??null,status:state.stopReason??'agent-finished',humanCorrectionMs:null};
 fs.writeFileSync(path.join(privateDir,'agent-result.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify({status:result.status,elapsedMs:result.elapsedMs,modelResponses:state.modelResponses,toolCalls:state.toolCalls,edits:state.edits,verificationCycles:state.verificationCycles}));
 worker?.kill('SIGTERM');session.dispose();
}
function stop(reason) {
 if(stopRequested!==null)return;stopRequested=Date.now();state.stopReason=reason;
 event('deadline_stop',{reason});responseAbort?.abort();totalAbort.abort();worker?.kill('SIGTERM');session.abort();
}
const watchdog=setInterval(()=>{
 const now=Date.now(),gap=now-clockLast;clockLast=now;maxClockGapMs=Math.max(maxClockGapMs,gap);
 if(gap>10000||gap<0){stop('host-interrupted');finish();process.exit(2);}
 if(now-start>=config.budget.wallMs)stop('wall-budget');
 else if(responseStarted!==null&&now-responseStarted>=config.budget.responseMs)stop('response-timeout');
 // Do not rely solely on provider cancellation settling its stream.
 if(stopRequested!==null&&now-stopRequested>=2000){finish();process.exit(2);}
},100);
process.on('SIGTERM',()=>{stop(Date.now()-start>=config.budget.wallMs?'wall-budget':'host-interrupted');finish();process.exit(2);});
try{await session.prompt(config.preflightPrompt??fs.readFileSync(path.join(root,'TASK.md'),'utf8'));}
catch(e){state.stopReason??='host-error';event('host_error',{message:e.message});}
finally{finish();}
