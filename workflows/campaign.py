"""Local API workflow pilot orchestration. Source and evaluator never enter agent tools."""
import argparse, importlib.util, json, os, pathlib, shutil, signal, subprocess, sys, time, urllib.request
from runtime import *
PI=pathlib.Path.home()/'.npm-global/lib/node_modules/@mariozechner/pi-coding-agent'
BUDGET={'wallMs':900000,'modelResponses':36,'toolCalls':80,'verificationCycles':3,'responseMs':180000}
SELECTED=['api-create-normalization','api-update-high-score','api-validate-format']

def config(folder,task,arm):
 return {'workspace':str((folder/'workspace').resolve()),'privateDir':str(folder.resolve()),'arm':arm,'sourceEditsAllowed':task['sourceEditsAllowed'],'allowedSourceRoots':task['allowedSourceRoots'],'piPackage':str(PI),'python':sys.executable,'runtime':str(ROOT/'runtime.py'),'seed':1,'budget':BUDGET}

def model_info():
 props=json.load(urllib.request.urlopen('http://127.0.0.1:8080/props',timeout=5))
 if props['default_generation_settings']['n_ctx']!=8192 or props['total_slots']!=1:raise ValueError('Expected existing 8192-context one-slot server')
 model=pathlib.Path(props['model_path'])
 if model.name!='gemma-4-E2B-it-qat-UD-Q4_K_XL.gguf':raise ValueError('Unexpected model')
 h=hashlib.sha256()
 with model.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return {'name':'Gemma 4 E2B IT QAT UD-Q4_K_XL','modelSha256':h.hexdigest(),'contextWindow':8192,'maxOutputTokens':4096,'slots':1,'temperature':.2,'seed':1,'runtime':'Pi '+read(PI/'package.json')['version']+' / llama.cpp','hardware':subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),'memoryBytes':int(subprocess.check_output(['sysctl','-n','hw.memsize'],text=True))}

def setup(out,repo):
 if out.exists():raise ValueError('Campaign already exists')
 catalog=read(ROOT/'tasks.json')
 head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
 if head!=catalog['sourceRevisions']['api'] or subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip():raise ValueError('Use the clean pinned API snapshot')
 model=model_info();out.mkdir(parents=True)
 tasks=[next(t for t in catalog['tasks'] if t['id']==i) for i in SELECTED];runs=[]
 for index,task in enumerate(tasks):
  common=None
  for arm in (['baseline','context'] if index%2==0 else ['context','baseline']):
   ident=task['id']+'-'+arm;folder=out/ident;folder.mkdir();snap=project(repo,folder/'workspace',task,arm)
   app={k:v for k,v in snap.items() if k.startswith(API+'/')}
   if common is not None and app!=common:raise ValueError('Paired application/helper bytes differ')
   common=app;write(folder/'initial.json',snap);write(folder/'config.json',config(folder,task,arm));runs.append({'id':ident,'taskId':task['id'],'operation':task['operation'],'arm':arm,'task':task,'configSha256':digest((folder/'config.json').read_bytes()),'initialSha256':digest((folder/'initial.json').read_bytes())})
 plan={'protocol':'qa-context-workflow-v2-api-pilot-4','createdAt':now(),'model':model,'sourceRevision':head,'budget':BUDGET,'runs':runs,'implementationSha256':{p.name:digest(p.read_bytes()) for p in [ROOT/'runtime.py',ROOT/'agent.mjs',ROOT/'campaign.py',ROOT/'controls.mjs',ROOT/'validity.py']},'limitations':['One paired repeat per task; three tasks, descriptive engineering pilot.','Nine prior started attempts across three campaigns are excluded and retained privately: three setup-invalid attempts (context-summary leakage/tool-discovery mismatch), then a six-attempt campaign with violated response/wall deadlines after host interruption. No comparative claim uses those attempts. This campaign adds pause detection and wall-clock watchdogs; tasks and model settings are unchanged.','Pi host uses bounded repository tools and controlled Maven execution, not an unrestricted terminal.','The API context resolver and skill are exercised; UI capture and decision-model review review are outside this first batch.','Human corrections and operating cost are unmeasured.','Semantic task decisions require review; unreviewed outcomes remain pending.','Compaction and retries are disabled; context-limit failures remain in the denominator.']}
 write(out/'plan.json',plan);print('Prepared six isolated workflow trials',flush=True)

def run_agent(folder):
 write(folder/'started.json',{'startedAt':now()});log=folder/'host.log'
 with log.open('w') as f:
  p=subprocess.Popen(['/opt/homebrew/bin/node',str(ROOT/'agent.mjs'),str((folder/'config.json').resolve())],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  began=last=time.time();max_gap=0
  try:
   while p.poll() is None:
    current=time.time();gap=current-last;last=current;max_gap=max(max_gap,gap)
    if current-began>BUDGET['wallMs']/1000+3 or gap>10 or gap<0:
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=2)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
     break
    time.sleep(.1)
  except BaseException:
   if p.poll() is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=3)
   raise
 write(folder/'host-clock.json',{'elapsedMs':round((time.time()-began)*1000),'maxClockGapMs':round(max_gap*1000)})
 if not (folder/'agent-result.json').exists():
  write(folder/'agent-result.json',{'status':'host-failed','elapsedMs':None,'finalText':'','modelResponses':None,'toolCalls':None,'verificationCycles':None,'repairs':None,'usage':[],'filesRead':[],'bytesRead':None,'edits':None,'humanCorrectionMs':None})
 return read(folder/'agent-result.json')

def grade(folder,task,proxy):
 grade_started=time.monotonic();root=folder/'workspace';initial=read(folder/'initial.json');final=snapshot(root);diff=[p for p in set(initial)|set(final) if initial.get(p)!=final.get(p)]
 source=[p for p in diff if p.endswith('.java')];unauthorized=[p for p in diff if not (task['sourceEditsAllowed'] and any(p.startswith(x) for x in task['allowedSourceRoots']) and p.endswith('.java')) and p!='contexts/current/resolved-context.yml']
 result={'gradedAt':now(),'changedSourceFiles':source,'outOfScopeChanges':unauthorized,'sourceUnchanged':not source,'checks':[],'correct':None,'reviewStatus':'pending-independent-review'}
 if task['operation']=='validate':
  result['automatedStatus']='scope-pass' if not source and not unauthorized else 'scope-failed';result['checks']=[{'name':'source-unchanged','passed':not source and not unauthorized}]
  if source or unauthorized:result['correct']=False;result['reviewStatus']='failed-scope'
  if not read(folder/'agent-result.json').get('finalText','').strip():
   result['checks'].append({'name':'conclusion-present','passed':False});result['correct']=False;result['reviewStatus']='failed-automated-checks';result['automatedStatus']='checks-failed'
 else:
  proxy.fault=None;proxy.requests=[];proxy.injected=0
  healthy=verify(root,folder);write(folder/'grade-healthy.json',healthy)
  old={'getCustomerRiskReturnsLowRiskCustomer','getCustomerRiskReturnsMediumRiskCustomer','getCustomerRiskReturnsHighRiskCustomer','getCustomerRiskRejectsMissingCustomerId','getCustomerRiskRejectsBlankCustomerId'}
  observed={c['id'].split('#')[-1] for c in healthy['cases']}
  result['checks']=[{'name':'healthy-suite','passed':healthy['passed']},{'name':'existing-test-identities-preserved','passed':old.issubset(observed)},{'name':'source-change-present','passed':bool(source)},{'name':'scope','passed':not unauthorized}]
  required=['normalize-id','normalize-score','normalize-category','normalize-eligible','normalize-reason'] if task['operation']=='create' else ['high-score','high-reason']
  if task['operation']=='create':result['checks'].append({'name':'new-normalization-request-observed','passed':' cust-1001 ' in proxy.requests})
  if task['operation']=='update':result['checks'].append({'name':'no-new-test-identities','passed':observed==old})
  if healthy['passed']:
   for fault in required+['old-medium-category','old-high-eligible','old-low-category']:
    proxy.fault=fault;proxy.injected=0;proxy.requests=[];r=verify(root,folder);write(folder/('grade-'+fault+'.json'),r)
    detected=r['exitCode']!=0 and proxy.injected>0 and any(t['assertionFailure'] for t in r['cases']) and not any(t['error'] or t['skipped'] for t in r['cases'])
    result['checks'].append({'name':fault,'passed':detected,'activated':proxy.injected})
  else:
   result['checks'] += [{'name':fault,'passed':False,'notEvaluated':True} for fault in required+['old-medium-category','old-high-eligible','old-low-category']]
  proxy.fault=None
  all_pass=all(c['passed'] for c in result['checks']);result['automatedStatus']='checks-pass-review-pending' if all_pass else 'checks-failed'
  if not all_pass:result['correct']=False;result['reviewStatus']='failed-automated-checks'
  # Passing numerical gates is necessary but does not prove semantic preservation or minimality.
 result['gradingMs']=round((time.monotonic()-grade_started)*1000)
 result['finalSourceSha256']=digest(json.dumps(final,sort_keys=True));write(folder/'grade.json',result);return result

@__import__('contextlib').contextmanager
def awake():
 # Scoped to this campaign. Prevents idle sleep, not forced sleep or lid closure.
 p=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())])
 try:yield
 finally:p.terminate();p.wait()

def execute(out,repo):
 plan=read(out/'plan.json')
 for name,h in plan['implementationSha256'].items():
  if digest((ROOT/name).read_bytes())!=h:raise ValueError('Frozen runner changed; new campaign required')
 with awake(),service(repo,out) as proxy:
  for trial in plan['runs']:
   folder=out/trial['id']
   if (folder/'grade.json').exists():continue
   if digest((folder/'config.json').read_bytes())!=trial['configSha256'] or digest((folder/'initial.json').read_bytes())!=trial['initialSha256']:raise ValueError('Frozen configuration changed')
   if not (folder/'agent-result.json').exists():
    if (folder/'started.json').exists():raise ValueError('Interrupted trial must be reconciled, never rerun silently')
    if snapshot(folder/'workspace')!=read(folder/'initial.json'):raise ValueError('Initial workspace changed')
    # Do not overlap a previous cancelled inference with a distinct trial.
    slots=json.load(urllib.request.urlopen('http://127.0.0.1:8080/slots',timeout=5))
    if any(s.get('is_processing') for s in slots):raise RuntimeError('Local model is busy; no trial started')
    print('Starting '+trial['id'],flush=True);r=run_agent(folder);print(trial['id']+' '+json.dumps({k:r.get(k) for k in ['status','elapsedMs','modelResponses','toolCalls','edits','verificationCycles']}),flush=True)
   from validity import assess
   audit=assess(folder,plan['budget']);write(folder/'validity.json',audit)
   g=grade(folder,trial['task'],proxy);print('Graded '+trial['id']+' '+g['automatedStatus'],flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--publish',action='store_true',help='Publish the completed campaign after all six runs are graded');a=p.parse_args();a.output=a.output.resolve();a.repo=a.repo.resolve()
 if a.publish and a.command!='run':p.error('--publish is only valid with run')
 (setup if a.command=='prepare' else execute)(a.output,a.repo)
 if a.publish:
  from export import export
  from publish import publish
  print(publish(export(a.output)),flush=True)
