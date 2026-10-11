"""Execute untouched generated tests against real sample apps through loopback fault injection."""
import argparse, contextlib, http.client, http.server, json, os, pathlib, re, shutil, signal, subprocess, threading, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from run import read,write,sha,now,run,SCORING
FAULTS={k:v[1:] for k,v in SCORING.items()}
class Proxy(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):self.forward()
 def do_POST(self):self.forward()
 def do_DELETE(self):self.forward()
 def forward(self):
  body=self.rfile.read(int(self.headers.get('content-length',0)))
  conn=http.client.HTTPConnection('127.0.0.1',self.server.upstream,timeout=20)
  conn.request(self.command,self.path,body,{k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','accept-encoding')})
  r=conn.getresponse();status=r.status;raw=r.read();headers=r.getheaders();conn.close()
  fault=self.server.fault;url=urllib.parse.urlparse(self.path);changed=False
  self.server.requests.append(self.path)
  if self.server.project=='harness':
   if url.path=='/api/accounts/export' and status==403:
    if fault=='viewer-http-200':status=200;raw=b'{"format":"json","accounts":[]}';changed=True
    if fault=='wrong-error-body':raw=b'{"error":"Forbidden"}';changed=True
   if url.path=='/assets/app.js':
    source=raw.decode()
    if fault=='enabled-export-button':
     old='${readOnly ? \'disabled aria-disabled="true"\' : \'\'}>Export accounts'
     changed=old in source;source=source.replace(old,'>Export accounts')
    if fault=='missing-read-only-banner':
     old="${readOnly ? '<p data-testid=\"read-only-banner\">Viewer role can inspect accounts but cannot export them.</p>' : ''}"
     changed=old in source;source=source.replace(old,'')
    raw=source.encode()
  elif url.path=='/xyz':
   params=urllib.parse.parse_qs(url.query,keep_blank_values=True);cid=params.get('customerId',[None])[0]
   if status==200:
    data=json.loads(raw)
    changes={'wrong-low-category':('riskCategory','HIGH',cid=='CUST-1001'),'wrong-medium-score':('score',58,cid=='CUST-5000'),'wrong-high-eligibility':('eligible',True,cid=='CUST-9999'),'wrong-customer-id':('customerId','WRONG',True),'wrong-decision-reason':('decisionReason','Incorrect reason',True)}
    if fault in changes:
     key,value,applies=changes[fault]
     if applies:data[key]=value;changed=True;raw=json.dumps(data).encode()
   if status==400 and ((fault=='accept-missing' and cid is None) or (fault=='accept-blank' and cid is not None and not cid.strip())):
    status=200;raw=b'{"customerId":"CUST-1001","eligible":true,"riskCategory":"LOW","score":18,"decisionReason":"Customer is eligible with low risk signals."}';changed=True
  if changed:self.server.injected+=1
  self.send_response(status)
  for k,v in headers:
   if k.lower() not in ('content-length','transfer-encoding','connection','content-encoding'):self.send_header(k,v)
  self.send_header('content-length',str(len(raw)));self.end_headers();self.wfile.write(raw)
@contextlib.contextmanager
def app(project,repo,folder):
 upstream=4374 if project=='harness' else 4384;port=4373 if project=='harness' else 4383
 command=['node','examples/sample-crm-app/server.mjs'] if project=='harness' else ['mvn','spring-boot:run','-Dspring-boot.run.arguments=--server.port=4384 --server.address=127.0.0.1']
 cwd=repo if project=='harness' else repo/'projects/microservices/xyz-service'
 with (folder/'service.log').open('w') as log:
  p=subprocess.Popen(command,cwd=cwd,env=dict(os.environ,PORT=str(upstream)),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  proxy=None
  try:
   for _ in range(180):
    if p.poll() is not None:raise RuntimeError('Sample service exited')
    try:
     urllib.request.urlopen(f'http://127.0.0.1:{upstream}'+('/actuator/health' if project=='api' else '/'),timeout=1).close();break
    except OSError:time.sleep(1)
   else:raise RuntimeError('Service startup timeout')
   proxy=http.server.ThreadingHTTPServer(('127.0.0.1',port),Proxy);proxy.upstream=upstream;proxy.project=project;proxy.fault=None;proxy.requests=[];proxy.injected=0
   threading.Thread(target=proxy.serve_forever,daemon=True).start();yield proxy,port
  finally:
   if proxy:proxy.shutdown();proxy.server_close()
   if p.poll() is None:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def forbidden(code,project,arm):
 patterns=[r'\b(?:exec|spawn|readFile|writeFile)\s*\(',r'node:(?:fs|child_process)',r'java\.(?:nio\.file|io\.(?:File|FileInputStream))',r'Runtime\.',r'ProcessBuilder',r'System\.getenv',r'process\.env',r'\bcatch\s*\((?!\s*NumberFormatException\b)',r'\b(?:test|describe)\.(?:skip|only|fail|fixme)',r'@Disabled',r'waitForTimeout',r'Thread\.sleep',r'\.route\s*\(']
 if arm=='baseline':patterns += [r'fixtures/base.fixture',r'com\.agentic\.workspace\.qa\.(?:client|config|fixtures|assertions)']
 return any(re.search(p,code) for p in patterns)
def playwright_result(path):
 if not path.exists():return dict(tests=0,testsPassed=0,assertionFailures=0,errors=1,skipped=0)
 d=read(path);rows=[]
 def walk(s):
  for sub in s.get('suites',[]):walk(sub)
  for spec in s.get('specs',[]):
   for t in spec.get('tests',[]):rows.extend(t.get('results',[]))
 walk(d)
 failures=[r for r in rows if r.get('status')=='failed' and any('expect(' in e.get('message','') or 'Expected:' in e.get('message','') for e in r.get('errors',[]))]
 return dict(tests=len(rows),testsPassed=sum(r['status']=='passed' for r in rows),assertionFailures=len(failures),errors=len(d.get('errors',[]))+sum(r['status'] not in ('passed','skipped') for r in rows)-len(failures),skipped=sum(r['status']=='skipped' for r in rows))
def junit_result(folder):
 files=list(folder.glob('TEST-*CustomerRiskTrialTest.xml'));rows=[]
 for f in files:rows+=list(ET.parse(f).getroot().iter('testcase'))
 assertions=sum(any('Assertion' in c.get('type','') for c in t.findall('failure')) for t in rows)
 return dict(tests=len(rows),testsPassed=sum(not t.findall('failure') and not t.findall('error') and not t.findall('skipped') for t in rows),assertionFailures=assertions,errors=sum(len(t.findall('error'))+len(t.findall('failure')) for t in rows)-assertions,skipped=sum(len(t.findall('skipped')) for t in rows))
def evaluate(args):
 out=args.output.resolve();plan=read(out/'plan.json')
 if plan.get('scoring')!=SCORING:raise ValueError('Evaluator does not match frozen scoring plan')
 for project in ['harness','api']:
  repo=pathlib.Path(plan['repos'][project]);pending=[t for t in plan['trials'] if t['project']==project and (out/t['id']/'generation.json').exists() and not (out/t['id']/'evaluation.json').exists()]
  if not pending:continue
  snapshots=read(out/(project+'-source-hashes.json'))
  if any(sha((repo/p).read_bytes())!=h for p,h in snapshots.items()):raise ValueError('Frozen application/helper sources changed')
  with app(project,repo,out) as (proxy,port):
   for t in pending:
    folder=out/t['id'];gen=read(folder/'generation.json');response=folder/'response.json'
    if gen['exitCode']!=0 or not response.exists():continue
    code=read(response)['code'];valid=not forbidden(code,project,t['arm']) and gen['toolEvents']==0
    workspace=folder/'workspace';shutil.rmtree(workspace,ignore_errors=True);workspace.mkdir()
    if project=='harness':
     (workspace/'node_modules').symlink_to((repo/'node_modules').resolve(),target_is_directory=True)
     if t['arm']=='framework':
      for d in ['pages','fixtures','assertions']:shutil.copytree(repo/d,workspace/d)
     (workspace/'tests').mkdir();(workspace/'tests/submission.spec.ts').write_text(code)
     (workspace/'playwright.config.ts').write_text("import {defineConfig} from '@playwright/test'; export default defineConfig({testDir:'tests',workers:1,retries:0,timeout:20000,expect:{timeout:3000},reporter:[['json',{outputFile:'report.json'}]],use:{baseURL:'http://127.0.0.1:"+str(port)+"'}});")
     command=['node',str((repo/'node_modules/@playwright/test/cli.js').resolve()),'test','--config=playwright.config.ts'];cwd=workspace
    else:
     shutil.copytree(repo/'projects/microservices',workspace/'microservices',ignore=shutil.ignore_patterns('target','.git'))
     cwd=workspace/'microservices';tests=cwd/'qa-projects/xyz-service-api-tests/src/test/java';shutil.rmtree(tests);target=tests/'com/agentic/workspace/qa/xyz/tests/CustomerRiskTrialTest.java';target.parent.mkdir(parents=True);target.write_text(code)
     command=['mvn','-q','-pl','qa-projects/xyz-service-api-tests','-am','test','-Dtest=CustomerRiskTrialTest','-Dsurefire.failIfNoSpecifiedTests=false','-Dapi.baseUri=http://127.0.0.1',f'-Dapi.port={port}']
    phases=[];begin=time.monotonic()
    for fault in [None]+FAULTS[project]:
     name=fault or 'healthy';proxy.fault=fault;proxy.requests=[];proxy.injected=0
     if project=='harness':(workspace/'report.json').unlink(missing_ok=True)
     else:shutil.rmtree(cwd/'qa-projects/xyz-service-api-tests/target/surefire-reports',ignore_errors=True)
     exitCode=run(command,cwd,folder/(name+'.log'),120) if valid else 125
     evidence=playwright_result(workspace/'report.json') if project=='harness' else junit_result(cwd/'qa-projects/xyz-service-api-tests/target/surefire-reports')
     if project=='harness' and (workspace/'report.json').exists():shutil.copyfile(workspace/'report.json',folder/(name+'.json'))
     elif project=='api':
      reportDir=cwd/'qa-projects/xyz-service-api-tests/target/surefire-reports';shutil.copytree(reportDir,folder/(name+'-reports'),dirs_exist_ok=True) if reportDir.exists() else None
     healthy=exitCode==0 and evidence['tests']>0 and evidence['testsPassed']==evidence['tests'] and evidence['errors']==0
     detected=exitCode!=0 and evidence['assertionFailures']>0 and evidence['errors']==0 and evidence['skipped']==0 and proxy.injected>0
     phases.append(dict(phase=name,exitCode=exitCode,passed=healthy if fault is None else detected,injectedResponses=proxy.injected,**evidence))
    result=dict(evaluatedAt=now(),responseSha256=sha(response.read_bytes()),sourceSha256=sha(code),protocolValid=valid,phases=phases,correctCompletion=valid and all(p['passed'] for p in phases),qualityPassed=sum(p['passed'] for p in phases),qualityTotal=len(phases),evaluationMs=round((time.monotonic()-begin)*1000),humanCorrectionMs=None,incorrectChanges=None)
    write(folder/'evaluation.json',result);print(t['id'],json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);evaluate(p.parse_args())
