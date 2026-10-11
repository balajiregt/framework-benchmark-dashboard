"""Controlled, one-response test-generation trials. Raw evidence stays ignored locally."""
import argparse, datetime as dt, hashlib, json, os, pathlib, shutil, signal, subprocess, time
ROOT = pathlib.Path(__file__).resolve().parents[1]
SCORING={'harness':['healthy','viewer-http-200','wrong-error-body','enabled-export-button','missing-read-only-banner'],'api':['healthy','wrong-low-category','wrong-medium-score','wrong-high-eligibility','wrong-customer-id','wrong-decision-reason','accept-missing','accept-blank']}
def sha(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def read(p):return json.loads(p.read_text())
def run(command,cwd,log,timeout=180,input=None):
 with log.open('w') as f:
  p=subprocess.Popen(command,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.PIPE if input else subprocess.DEVNULL,text=True,start_new_session=True)
  try:p.communicate(input,timeout=timeout);return p.returncode
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();return 124

def bundle(repo,paths):return '\n\n'.join('FILE '+p+'\n'+(repo/p).read_text() for p in paths)
def prepare(args):
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 if (out/'plan.json').exists():raise ValueError('Campaign already prepared; use generate/evaluate to resume')
 repos={'harness':args.harness.resolve(),'api':args.api.resolve()}
 plans=[]
 for project,repo in repos.items():
  if project=='harness':
   paths=['examples/sample-crm-app/api.mjs','examples/sample-crm-app/public/assets/app.js']
   helpers=['pages/sample-crm.page.ts','assertions/sample-crm.assertions.ts','fixtures/base.fixture.ts']
   target='tests/submission.spec.ts'
   task='Write Playwright TypeScript tests for viewer account-export restrictions. Sign in through the real UI as viewer@example.com / password; wait for the dashboard before navigating to accounts. Assert the Accounts page is visible, read-only banner is visible, export button is disabled, and a direct authenticated GET /api/accounts/export returns exactly status 403 and JSON {"error":"Access denied"}. Do not intercept/mock requests. Use fresh browser context provided by Playwright. Base URL is configured by the runner. Tests may import @playwright/test.'
   framework='Use the existing fixture from ../fixtures/base.fixture and its SampleCrmPage / SampleCrmAssertions helpers. Follow page-object actions, web-first assertions and explicit ready signals. The helper signInAs returns after click, not after authentication completes.'
  else:
   base='projects/microservices/xyz-service/'
   paths=[base+'src/main/resources/openapi/xyz-service.openapi.yml',base+'src/main/java/com/agentic/workspace/xyz/service/CustomerRiskService.java',base+'src/main/java/com/agentic/workspace/xyz/api/CustomerRiskController.java']
   shared='projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/'
   helpers=[shared+p+'.java' for p in ['client/RestClientFactory','config/ApiTestConfig','fixtures/CustomerFixtures','assertions/JsonFieldAssertions']]
   target='CustomerRiskTrialTest.java'
   task='Write Java 17 JUnit 5 / RestAssured API tests in package com.agentic.workspace.qa.xyz.tests, class CustomerRiskTrialTest. Cover GET /xyz for CUST-1001 LOW, CUST-5000 MEDIUM, CUST-9999 HIGH; for each assert status, exact customerId, eligible, riskCategory, score and decisionReason from source. Also test missing customerId and blank single-space customerId both return status 400. The runner supplies -Dapi.baseUri=http://127.0.0.1 and -Dapi.port=<port>; read those system properties. Do not use a fixed port. Dependencies are RestAssured, Hamcrest, JUnit 5. Do not mock HTTP or use an in-process service.'
   framework='Use existing qa-steps RestClientFactory, ApiTestConfig, CustomerFixtures and JsonFieldAssertions. Follow split-QA conventions: tests in service QA, support in qa-steps; use contract and service as source of truth, no guessed expectations.'
  common='You are the subject of a controlled test-generation experiment. Produce the requested executable test file using ONLY the supplied source and requirements. Do not call tools, browse, read files, run commands, or invoke other agents. No repair loop: an independent evaluator runs your unmodified output afterward. No skipped tests, retries, sleeps, environment-dependent branches, catching assertion failures or reading local files. Return JSON with only a code string containing the complete source file.\n\nTASK\n'+task+'\n\nAPP SOURCE\n'+bundle(repo,paths)
  snapshots={p:sha((repo/p).read_bytes()) for p in paths+helpers}
  targetHash=sha(json.dumps(snapshots,sort_keys=True))
  for repeat in range(3):
   for arm in (['baseline','framework'] if repeat%2==0 else ['framework','baseline']):
    ident=f'{project}-{repeat+1}-{arm}'
    prompt=common+'\n\nCONDITION\n'+(framework+'\n'+bundle(repo,helpers) if arm=='framework' else 'Use plain runner APIs. The framework helpers are not available in this condition.')
    p=out/ident;p.mkdir();(p/'prompt.txt').write_text(prompt)
    plans.append(dict(id=ident,project=project,arm=arm,repeat=repeat+1,target=target,sourceRevision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),targetSha256=targetHash,promptSha256=sha(prompt)))
  write(out/(project+'-source-hashes.json'),snapshots)
 plan=dict(schemaVersion=1,protocol='one-response-mutation-v1',createdAt=now(),model='gpt-6.1-sol',reasoning='low',cliVersion=subprocess.check_output(['codex','--version'],text=True).strip(),timeoutSeconds=180,repeats=3,order='alternating baseline/framework; CRM then API',scope='Context-assisted test generation only; not the full autonomous framework workflow.',scoring=SCORING,completionRule='Healthy suite passes, every required seeded fault produces at least one assertion failure, no execution errors, no tool use or forbidden test constructs.',repos={k:str(v) for k,v in repos.items()},trials=plans)
 write(out/'plan.json',plan);write(out/'schema.json',{'type':'object','properties':{'code':{'type':'string'}},'required':['code'],'additionalProperties':False})
 print(json.dumps({'prepared':len(plans),'planSha256':sha((out/'plan.json').read_bytes())}))

def generate(args):
 out=args.output.resolve();plan=read(out/'plan.json');empty=out/'empty';empty.mkdir(exist_ok=True)
 for t in plan['trials']:
  if args.only and t['id']!=args.only:continue
  folder=out/t['id'];receipt=folder/'generation.json'
  if receipt.exists():continue
  response=folder/'response.json';start=now();clock=time.monotonic()
  command=['codex','--no-daemon','exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','--sandbox','read-only','-c','approval_policy="never"','-c','project_doc_max_bytes=0','-c','features.shell_tool=false','-c','web_search="disabled"','-c','model_reasoning_effort="low"','--model',plan['model'],'--json','--output-schema',str(out/'schema.json'),'-o',str(response),'-']
  code=run(command,empty,folder/'events.jsonl',plan['timeoutSeconds'],(folder/'prompt.txt').read_text())
  events=[]
  for line in (folder/'events.jsonl').read_text().splitlines():
   try:events.append(json.loads(line))
   except ValueError:pass
  completions=[e for e in events if e.get('type')=='turn.completed'];usage=completions[-1].get('usage') if completions else None
  tools=[e for e in events if e.get('item',{}).get('type') in ('command_execution','mcp_tool_call','web_search','file_change')]
  result=dict(startedAt=start,finishedAt=now(),elapsedMs=round((time.monotonic()-clock)*1000),exitCode=code,usage=usage,toolEvents=len(tools),responseSha256=sha(response.read_bytes()) if response.exists() else None,eventsSha256=sha((folder/'events.jsonl').read_bytes()),humanCorrectionMs=None,actualCost=None,estimatedCost=None)
  write(receipt,result);print(t['id'],json.dumps(result),flush=True)
  if code!=0 or not completions:
   print('Stopping on provider/runtime failure; no blind retries or replacement trials.',flush=True);raise SystemExit(1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','generate']);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--harness',type=pathlib.Path);p.add_argument('--api',type=pathlib.Path);p.add_argument('--only');a=p.parse_args();globals()[a.command](a)
