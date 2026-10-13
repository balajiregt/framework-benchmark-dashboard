"""Frozen paired API/Playwright trials with independent decision review."""
import argparse,json,os,pathlib,signal,subprocess,sys,time
from engine import *
from campaign import model_info,awake
from validity import assess
PI=pathlib.Path.home()/'.npm-global/lib/node_modules/@mariozechner/pi-coding-agent'
IMPLEMENTATION=['impact/agent.mjs','impact/engine.py','impact/run.py','impact/audit.py','impact/tasks.json','workflows/runtime.py','workflows/controls.mjs','workflows/validity.py']

def prepare(sources,out,audit_path):
 if out.exists():raise ValueError('Campaign already exists')
 catalog=read(ROOT/'tasks.json');audit=read(audit_path)
 if audit['sources']!=catalog['sourceRevisions']:raise ValueError('Audit and trial source revisions differ')
 for name,repo in sources.items():
  head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
  if head!=catalog['sourceRevisions'][name] or subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip():raise ValueError('Use clean pinned '+name+' source')
 model=model_info();out.mkdir(parents=True);runs=[]
 for i,task in enumerate(catalog['tasks']):
  common=None
  for arm in (['baseline','context'] if i%2==0 else ['context','baseline']):
   ident=task['id']+'-'+arm;folder=out/ident;folder.mkdir();snap=project(sources[task['project']],folder/'workspace',task,arm)
   app={k:v for k,v in snap.items() if k.startswith('projects/microservices/') or any(k.startswith(p) for p in ['examples/','tests/','pages/','assertions/','fixtures/','data/'])}
   if common is not None and app!=common:raise ValueError('Paired application/helper bytes differ')
   common=app;write(folder/'initial.json',snap)
   config={'project':task['project'],'workspace':str((folder/'workspace').resolve()),'privateDir':str(folder.resolve()),'arm':arm,'sourceEditsAllowed':task['sourceEditsAllowed'],'allowedSourceRoots':task['allowedSourceRoots'],'allowedExtensions':task['allowedExtensions'],'piPackage':str(PI),'python':sys.executable,'runtime':str(ROOT/'engine.py'),'seed':1,'budget':catalog['budget'],'commands':['verify','probe','context:resolve'] if task['project']=='api' else ['verify','observe','graph:refresh']}
   write(folder/'config.json',config);runs.append({'id':ident,'task':task,'arm':arm,'repeat':1,'initialSha256':digest((folder/'initial.json').read_bytes()),'configSha256':digest((folder/'config.json').read_bytes())})
 plan={'protocol':catalog['protocol'],'createdAt':now(),'sourceRevisions':catalog['sourceRevisions'],'model':model,'budget':catalog['budget'],'pairedRepeats':catalog['pairedRepeats'],'runs':runs,'contextAuditSha256':digest(audit_path.read_bytes()),'decisionRubric':catalog['decisionRubric'],'limitations':catalog['limitations'],'implementationSha256':{n:digest((ROOT.parent/n).read_bytes()) for n in IMPLEMENTATION}}
 write(out/'plan.json',plan);shutil.copyfile(audit_path,out/'context-audit.json')
 for n in IMPLEMENTATION:
  target=out/'runner-snapshot'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT.parent/n,target)
 print(json.dumps({'prepared':len(runs),'campaignId':digest((out/'plan.json').read_bytes())[:16]}),flush=True)

def run_agent(folder,budget):
 write(folder/'started.json',{'startedAt':now()})
 with (folder/'host.log').open('w') as f:
  p=subprocess.Popen(['/opt/homebrew/bin/node',str(ROOT/'agent.mjs'),str(folder/'config.json')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  began=last=time.time();max_gap=0
  try:
   while p.poll() is None:
    current=time.time();gap=current-last;last=current;max_gap=max(max_gap,gap)
    if current-began>budget['wallMs']/1000+3 or gap>10 or gap<0:
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=2)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
     break
    time.sleep(.1)
  except BaseException:
   if p.poll() is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=3)
   raise
 write(folder/'host-clock.json',{'elapsedMs':round((time.time()-began)*1000),'maxClockGapMs':round(max_gap*1000)})
 if not (folder/'agent-result.json').exists():write(folder/'agent-result.json',{'status':'host-failed','elapsedMs':round((time.time()-began)*1000),'finalText':'','modelResponses':None,'toolCalls':None,'verificationCycles':None,'repairs':None,'edits':None,'filesRead':[],'bytesRead':None})
 return read(folder/'agent-result.json')

def grade(folder,task,proxy=None):
 start=time.monotonic();root=folder/'workspace';before=read(folder/'initial.json');after=snapshot(root);changes=sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p))
 allowed=lambda p:any(p.startswith(x) for x in task['allowedSourceRoots']) and any(p.endswith(x) for x in task['allowedExtensions'])
 source=[p for p in changes if allowed(p)]
 generated=lambda p:p=='contexts/current/resolved-context.yml' or p.startswith('graphs/data/') or p=='examples/sample-crm-app/source-manifest.json'
 forbidden=[p for p in changes if not generated(p) and not (task['sourceEditsAllowed'] and allowed(p))]
 checks=[{'id':'scope','label':'Changes stay within task scope','passed':not forbidden}]
 if task['operation']=='validate':checks.append({'id':'read-only','label':'Source remains unchanged','passed':not source})
 else:
  checks.append({'id':'change','label':'Requested source change exists','passed':bool(source)})
  if task['project']=='api':
   proxy.fault=None;proxy.requests=[];result=api.verify(root,folder);requests=list(proxy.requests);write(folder/'verification-requests.json',requests)
  else:result=ui_verify(root,folder)
  write(folder/'acceptance-execution.json',result)
  checks.append({'id':'execution','label':'Work executes successfully against the sample app','passed':result['passed']})
  if task['project']=='api' and task['operation']=='create':checks.append({'id':'requested-input','label':'Execution includes the requested whitespace input','passed':' cust-1001 ' in requests})
  if task['operation']=='update':checks.append({'id':'no-duplicate','label':'Existing scenario count retained','passed':len(result['cases'])==5})
  # Code semantics and preservation are reviewed independently, not inferred from a green suite.
 result={'gradedAt':now(),'automatedChecks':checks,'changedSourceFiles':source,'outOfScopeChanges':forbidden,'decisionReview':None,'taskReview':None,'complete':False if not all(c['passed'] for c in checks) else None,'reviewStatus':'pending-independent-review','gradingMs':round((time.monotonic()-start)*1000),'submissionSha256':digest((folder/'agent-result.json').read_bytes()),'finalSnapshotSha256':digest(json.dumps(after,sort_keys=True))}
 write(folder/'grade.json',result);return result

def run(sources,out):
 plan=read(out/'plan.json')
 for n,h in plan['implementationSha256'].items():
  if digest((ROOT.parent/n).read_bytes())!=h:raise ValueError('Frozen runner changed: '+n)
 if digest((out/'context-audit.json').read_bytes())!=plan['contextAuditSha256']:raise ValueError('Audit changed')
 with awake(),api.service(sources['api'],out) as proxy,ui_service(sources['harness'],out):
  for trial in plan['runs']:
   folder=out/trial['id']
   if (folder/'grade.json').exists():continue
   for name,expected in [('config.json',trial['configSha256']),('initial.json',trial['initialSha256'])]:
    if digest((folder/name).read_bytes())!=expected:raise ValueError('Configuration changed')
   if not (folder/'agent-result.json').exists():
    if (folder/'started.json').exists():raise ValueError('Interrupted attempt must be reconciled, never replaced silently')
    if snapshot(folder/'workspace')!=read(folder/'initial.json'):raise ValueError('Initial projection changed')
    slots=json.load(urllib.request.urlopen('http://127.0.0.1:8080/slots',timeout=5))
    if any(s.get('is_processing') for s in slots):raise RuntimeError('Local model busy; no new attempt started')
    print('Starting '+trial['id'],flush=True);a=run_agent(folder,plan['budget']);print(json.dumps({'trial':trial['id'],**{k:a.get(k) for k in ['status','elapsedMs','modelResponses','toolCalls','edits']}}),flush=True)
   audit=assess(folder,plan['budget']);write(folder/'validity.json',audit);g=grade(folder,trial['task'],proxy);print(json.dumps({'trial':trial['id'],'validity':audit['status'],'automatedChecks':g['automatedChecks']}),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);p.add_argument('--api',type=pathlib.Path,required=True);p.add_argument('--harness',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--audit',type=pathlib.Path);p.add_argument('--publish',action='store_true');a=p.parse_args();sources={'api':a.api.resolve(),'harness':a.harness.resolve()};out=a.output.resolve()
 if a.command=='prepare':prepare(sources,out,a.audit.resolve())
 else:
  run(sources,out)
  if a.publish:subprocess.run([sys.executable,str(ROOT/'publish.py'),'--campaign',str(out)],check=True)
