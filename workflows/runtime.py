"""Confined API workspace projection, fixed execution gates, and independent grading."""
import contextlib, hashlib, http.client, http.server, json, os, pathlib, shutil, signal, subprocess, sys, threading, time, urllib.parse, xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent
API='projects/microservices'
QA=API+'/qa-projects/xyz-service-api-tests'
TESTROOT=QA+'/src/test/'
SUPPORT=API+'/qa-steps/src/main/java/'
PORT=4383
UPSTREAM=4384

def read(p):return json.loads(pathlib.Path(p).read_text())
def write(p,v):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def digest(b):return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def now():return __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
def files(root):return sorted(p for p in root.rglob('*') if p.is_file() and not p.is_symlink() and not any(x in p.relative_to(root).parts for x in ['target','.tmp','.home']))
def snapshot(root):return {str(p.relative_to(root)):digest(p.read_bytes()) for p in files(root)}
def checked(root,relative):
 p=(root/relative).resolve()
 if not p.is_relative_to(root.resolve()):raise ValueError('Outside workspace')
 if any(part in ['.git','target','.home','.tmp'] for part in p.relative_to(root.resolve()).parts):raise ValueError('Private/generated path')
 return p

def project(repo,dest,task,arm):
 if dest.exists():raise ValueError('Workspace exists')
 dest.mkdir(parents=True)
 names=subprocess.check_output(['git','-C',str(repo),'ls-files',API],text=True).splitlines()
 for n in names:
  src=repo/n
  if src.is_symlink() or not src.is_file():raise ValueError('Unsupported source link')
  target=dest/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
 (dest/'TASK.md').write_text(task['request']+'\n')
 (dest/'SETUP.md').write_text('The sample API is already running for this trial. Use repo tools to inspect and edit files.\nUse run with command="verify" to run the existing Maven API suite against the local service. It supplies api.baseUri and api.port.\nUse run with command="probe" and customerId to inspect a GET /xyz response.\nNo shell tool is provided. The controlled commands are the execution tools for this pilot.\nKeep product and configuration unchanged. Existing tests and shared Java helpers are available in both conditions.\nFinal answer: findings, evidence paths, changed files, verification and remaining gaps.\n')
 if arm=='context':
  for n in ['AGENTS.md','skills/microservice-change/SKILL.md','scripts/resolve_context.py']:
   target=dest/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/n,target)
  context={'service_name':'xyz-service','work_item':{'source':'benchmark','key':'WORKFLOW-TASK','summary':task['request'],'description':task['request'],'change_type':'analysis' if task['operation']=='validate' else 'test','affected_endpoints':['GET /xyz'],'in_scope':['analysis'] if task['operation']=='validate' else ['tests'],'out_of_scope':['service_code','openapi_contract','deployment_change']},'repository_topology':{'service_and_tests':'split-qa','deployment':'separate-repo'},'local_validation':{'service_port':PORT,'test_port_property':'api.port'},'quality_gates':{'require_hallucination_check':True}}
  write(dest/'contexts/current/service-context.yml',context) # JSON is valid YAML.
  write(dest/'package.json',{'private':True,'scripts':{'context:resolve':'python3 scripts/resolve_context.py'}})
 return snapshot(dest)

def sandbox(root,folder):
 root=root.resolve();folder=folder.resolve();tmp=root/'.tmp';home=root/'.home';tmp.mkdir(exist_ok=True);home.mkdir(exist_ok=True)
 # Generated Java inherits these OS restrictions, including subprocesses.
 reads=['/private/var/db/timezone','/private/preboot','/Library/Apple','/System','/usr','/bin','/sbin','/opt/homebrew','/Library/Java','/Library/Frameworks/Python.framework','/private/etc','/dev',str(root),str(pathlib.Path.home()/'.m2/repository')]
 lines=['(version 1)','(allow default)','(deny file-read*)','(deny file-write*)','(deny network*)','(allow file-read-metadata)','(allow file-read-data (literal "/"))']
 for p in reads:lines.append('(allow file-read* (subpath '+json.dumps(p)+'))')
 for p in [str(root),'/dev/null','/dev/urandom'] :lines.append('(allow file-write* (subpath '+json.dumps(p)+'))')
 lines += ['(allow network-outbound (remote tcp "localhost:'+str(PORT)+'"))','(allow network-inbound (local tcp "localhost:*"))']
 profile=folder/'execution.sb';profile.write_text('\n'.join(lines))
 env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin','HOME':str(home),'TMPDIR':str(tmp),'JAVA_HOME':'/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home','LANG':'en_US.UTF-8','PYTHONDONTWRITEBYTECODE':'1','MAVEN_OPTS':'-Djava.io.tmpdir='+str(tmp),'JAVA_TOOL_OPTIONS':'-Djava.net.preferIPv4Stack=true -XX:-UsePerfData -Djava.io.tmpdir='+str(tmp)}
 return profile,env

def command(root,folder,args,cwd,seconds=120):
 profile,env=sandbox(root,folder);start=time.monotonic()
 log=folder/('exec-'+str(time.time_ns())+'.log')
 with log.open('w') as f:
  p=subprocess.Popen(['/usr/bin/sandbox-exec','-f',str(profile),*args],cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  def stop(signum,frame):
   if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
   raise SystemExit(128+signum)
  prior=signal.signal(signal.SIGTERM,stop)
  try:
   try:p.wait(timeout=seconds);code=p.returncode
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();code=124
   except BaseException:
    if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
    raise
  finally:signal.signal(signal.SIGTERM,prior)
 text=log.read_text(errors='replace')
 # Do not reveal host paths through tool results.
 visible=text.replace(str(root),'<workspace>').replace(str(pathlib.Path.home()),'<home>')
 return {'exitCode':code,'elapsedMs':round((time.monotonic()-start)*1000),'output':visible[-10000:],'outputTruncated':len(visible)>10000,'logSha256':digest(log.read_bytes())}

def junit(root):
 out=[]
 for p in (root/QA/'target/surefire-reports').glob('TEST-*.xml'):
  for t in ET.parse(p).getroot().iter('testcase'):
   errors=t.findall('error');fail=t.findall('failure');skip=t.findall('skipped')
   out.append({'id':t.get('classname','')+'#'+t.get('name',''),'passed':not(errors or fail or skip),'assertionFailure':any('Assertion' in x.get('type','') for x in fail),'error':bool(errors) or any('Assertion' not in x.get('type','') for x in fail),'skipped':bool(skip)})
 return out

def verify(root,folder,seconds=120):
 # Recompile every frozen snapshot; never reuse stale generated test classes.
 for module in [QA,API+'/qa-steps']:shutil.rmtree(root/module/'target',ignore_errors=True)
 args=['/opt/homebrew/bin/mvn','-o','-q','-Dmaven.repo.local='+str(pathlib.Path.home()/'.m2/repository'),'-pl','qa-projects/xyz-service-api-tests','-am','test','-Dapi.baseUri=http://127.0.0.1',f'-Dapi.port={PORT}','-Dsurefire.rerunFailingTestsCount=0']
 result=command(root,folder,args,root/API,seconds);result['cases']=junit(root)
 result['passed']=result['exitCode']==0 and bool(result['cases']) and all(t['passed'] for t in result['cases'])
 return result

class Proxy(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  c=http.client.HTTPConnection('127.0.0.1',UPSTREAM,timeout=10);c.request('GET',self.path);r=c.getresponse();raw=r.read();status=r.status;headers=r.getheaders();c.close()
  url=urllib.parse.urlsplit(self.path);cid=urllib.parse.parse_qs(url.query,keep_blank_values=True).get('customerId',[None])[0]
  self.server.requests.append(cid);fault=self.server.fault
  if status==200 and url.path=='/xyz':
   d=json.loads(raw);normalized=cid==' cust-1001 ';high=cid=='CUST-9999'
   changes={'normalize-id':('customerId',' cust-1001 ',normalized),'normalize-score':('score',19,normalized),'normalize-category':('riskCategory','HIGH',normalized),'normalize-eligible':('eligible',False,normalized),'normalize-reason':('decisionReason','Wrong',normalized),'high-score':('score',92,high),'high-reason':('decisionReason','Wrong',high),'old-medium-category':('riskCategory','LOW',cid=='CUST-5000'),'old-high-eligible':('eligible',True,high),'old-low-category':('riskCategory','HIGH',cid=='CUST-1001')}
   if fault in changes:
    key,value,apply=changes[fault]
    if apply:d[key]=value;raw=json.dumps(d).encode();self.server.injected+=1
  self.send_response(status)
  for k,v in headers:
   if k.lower() not in ['content-length','connection','transfer-encoding']:self.send_header(k,v)
  self.send_header('content-length',str(len(raw)));self.end_headers();self.wfile.write(raw)

@contextlib.contextmanager
def service(repo,folder):
 args=['/opt/homebrew/bin/mvn','-o','spring-boot:run',f'-Dspring-boot.run.arguments=--server.port={UPSTREAM} --server.address=127.0.0.1']
 with (folder/'service.log').open('w') as f:
  p=subprocess.Popen(args,cwd=repo/API/'xyz-service',stdout=f,stderr=subprocess.STDOUT,start_new_session=True);proxy=None
  try:
   for _ in range(120):
    if p.poll() is not None:raise RuntimeError('Service failed to start')
    try:
     c=http.client.HTTPConnection('127.0.0.1',UPSTREAM,timeout=1);c.request('GET','/actuator/health');r=c.getresponse();r.read();c.close()
     if r.status==200:break
    except OSError:pass
    time.sleep(1)
   else:raise RuntimeError('Service readiness timeout')
   proxy=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),Proxy);proxy.fault=None;proxy.requests=[];proxy.injected=0
   threading.Thread(target=proxy.serve_forever,daemon=True).start();yield proxy
  finally:
   if proxy:proxy.shutdown();proxy.server_close()
   if p.poll() is None:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()

if __name__=='__main__':
 # Trusted fixed-command adapter invoked by Pi host. No agent-provided shell text.
 config=read(sys.argv[1]);action=read(sys.argv[2]);root=pathlib.Path(config['workspace']);folder=pathlib.Path(config['privateDir'])
 if action['command']=='verify':result=verify(root,folder,action['timeoutSeconds'])
 elif action['command']=='context:resolve' and config['arm']=='context':result=command(root,folder,[sys.executable,'scripts/resolve_context.py'],root,min(30,action['timeoutSeconds']))
 elif action['command']=='probe':
  c=http.client.HTTPConnection('127.0.0.1',PORT,timeout=min(10,action['timeoutSeconds']));c.request('GET','/xyz?'+urllib.parse.urlencode({'customerId':action.get('customerId','')}));r=c.getresponse();result={'status':r.status,'body':r.read().decode()};c.close()
 else:raise ValueError('Unsupported command')
 print(json.dumps(result))
