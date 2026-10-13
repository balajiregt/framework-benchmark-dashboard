"""Isolated API/CRM projections and fixed, audited execution interfaces."""
import contextlib, importlib.util, json, os, pathlib, shutil, signal, subprocess, sys, time, urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'workflows'))
import runtime as api
read,write,digest,now=api.read,api.write,api.digest,api.now
UI_PORT=4393
SKIP={'.git','node_modules','target','.home','.tmp','.reports','.runtime','playwright-report','test-results','.playwright','__pycache__'}
def files(root):
 for parent,dirs,names in os.walk(root):
  dirs[:]=[d for d in dirs if d not in SKIP and not (pathlib.Path(parent)/d).is_symlink()]
  for n in names:
   p=pathlib.Path(parent)/n
   if not p.is_symlink():yield p

def snapshot(root):return {str(p.relative_to(root)):digest(p.read_bytes()) for p in sorted(files(root))}
def project(repo,dest,task,arm):
 if task['project']=='api':
  api.project(repo,dest,task,arm)
 else:
  dest.mkdir(parents=True)
  prefixes=['pages/','assertions/','fixtures/','data/','examples/sample-crm-app/']
  names=subprocess.check_output(['git','-C',str(repo),'ls-files'],text=True).splitlines()
  for n in names:
   common=n in ['tests/sample-crm.spec.ts','playwright.config.ts','tsconfig.json','package-lock.json','package.json'] or any(n.startswith(p) for p in prefixes)
   context=arm=='context' and (n=='AGENTS.md' or any(n.startswith(p) for p in ['contexts/','scripts/','specs/','.github/copilot-instructions.md']))
   if (common or context) and (repo/n).is_file() and not (repo/n).is_symlink():
    target=dest/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/n,target)
  (dest/'node_modules').symlink_to((repo/'node_modules').resolve(),target_is_directory=True)
  (dest/'TASK.md').write_text(task['request']+'\n')
 (dest/'SETUP.md').write_text('This is an isolated QA work task. The application is already running. Both conditions have the same source, existing tests/helpers and ordinary tools.\nUse read/edit/write/find/grep/ls with repository-relative paths. bash accepts the fixed commands listed below, not arbitrary shell code.\nverify: run the existing '+('Maven API suite' if task['project']=='api' else 'CRM Playwright suite (Chromium, one worker, zero retries, live base URL)')+'.\n'+('probe: GET /xyz for customerId. context:resolve: run the real resolver (framework condition).\n' if task['project']=='api' else 'observe: inspect a CRM route using a real logged-in role and a fresh browser. role and route are optional tool fields. graph:refresh: rebuild the real source/test/coverage/duplicate graphs (framework condition).\n')+'Do not edit application/configuration or hide failures. Read-only tasks must not edit source. Final report: decision, owning files, evidence, changes, actual verification and remaining gaps.\n')
 return snapshot(dest)

def ui_command(root,folder,args,seconds=120):
 profile,env=api.sandbox(root,folder)
 extra=['(allow file-read* (subpath '+json.dumps(str((root/'node_modules').resolve()))+'))','(allow file-read* (subpath '+json.dumps(str(pathlib.Path.home()/'Library/Caches/ms-playwright'))+'))','(allow network-outbound (remote tcp "localhost:'+str(UI_PORT)+'"))']
 profile.write_text(profile.read_text()+'\n'+'\n'.join(extra))
 env.update(APP_BASE_URL=f'http://127.0.0.1:{UI_PORT}',PLAYWRIGHT_BROWSERS_PATH=str(pathlib.Path.home()/'Library/Caches/ms-playwright'),NODE_PATH=str(root/'node_modules'))
 start=time.monotonic();log=folder/('ui-exec-'+str(time.time_ns())+'.log')
 with log.open('w') as f:
  p=subprocess.Popen(['/usr/bin/sandbox-exec','-f',str(profile),*args],cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
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
 text=log.read_text(errors='replace').replace(str(root),'<workspace>').replace(str(pathlib.Path.home()),'<home>')
 return {'exitCode':code,'elapsedMs':round((time.monotonic()-start)*1000),'output':text[-10000:],'outputTruncated':len(text)>10000,'logSha256':digest(log.read_bytes())}

def graph(root,folder,seconds=120):
 outputs=[];started=time.monotonic()
 for script in ['sync-source-manifest.mjs','graph-source.mjs','graph-tests.mjs','graph-coverage.mjs','graph-duplicates.mjs']:
  # Use the framework's own entry points; never insert evaluator-labelled facts.
  args=['/opt/homebrew/bin/node','scripts/'+script]
  if script=='sync-source-manifest.mjs':args+=['--adapter=scripts/source-adapters/sample-crm.mjs','--quiet']
  remaining=seconds-(time.monotonic()-started)
  if remaining<=0:raise TimeoutError('Context generation deadline')
  result=ui_command(root,folder,args,remaining);outputs.append(result)
  if result['exitCode']:break
 return {'exitCode':outputs[-1]['exitCode'],'elapsedMs':sum(x['elapsedMs'] for x in outputs),'output':'\n'.join(x['output'] for x in outputs),'artifacts':['examples/sample-crm-app/source-manifest.json','graphs/data/source-graph.json','graphs/data/test-graph.json','graphs/data/coverage-graph.json','graphs/data/duplicate-graph.json']}

def ui_verify(root,folder,seconds=120):
 report=root/'.reports/results.json';shutil.rmtree(root/'.reports',ignore_errors=True);(root/'.runtime').mkdir(exist_ok=True)
 config="import {defineConfig} from '@playwright/test'; export default defineConfig({testDir:'../tests',testMatch:'**/*.spec.ts',outputDir:'../.reports/artifacts',workers:1,retries:0,forbidOnly:true,timeout:30000,expect:{timeout:5000},reporter:[['json',{outputFile:"+json.dumps(str(report))+"}]],use:{baseURL:process.env.APP_BASE_URL,headless:true,launchOptions:{args:['--disable-gpu']}}});"
 (root/'.runtime/playwright.config.ts').write_text(config)
 result=ui_command(root,folder,['/opt/homebrew/bin/node','node_modules/@playwright/test/cli.js','test','--config=.runtime/playwright.config.ts'],seconds)
 # Report paths in Playwright are relative to cwd, while testDir is config-relative.
 if not report.exists() and (root.parent/'.reports/results.json').exists():raise RuntimeError('Unexpected report path')
 data=read(report) if report.exists() else {};cases=[]
 def visit(s):
  for c in s.get('suites',[]):visit(c)
  for spec in s.get('specs',[]):
   for t in spec.get('tests',[]):
    rs=t.get('results',[]);cases.append({'title':spec['title'],'passed':t.get('expectedStatus')=='passed' and len(rs)==1 and rs[0]['status']=='passed','status':rs[-1]['status'] if rs else 'missing','attempts':len(rs)})
 visit(data);result['cases']=cases;result['passed']=result['exitCode']==0 and len(cases)>=5 and all(c['passed'] for c in cases);return result

def observe(root,folder,action):
 role=action.get('role') or 'viewer';route=action.get('route') or '/crm/accounts'
 if role not in ['admin','manager','sales','viewer'] or route not in ['/login','/crm/dashboard','/crm/leads','/crm/accounts','/crm/opportunities','/crm/reports','/crm/admin/users']:raise ValueError('Unknown sample role/route')
 (root/'.runtime').mkdir(exist_ok=True)
 script="import {chromium} from 'playwright'; const browser=await chromium.launch({headless:true,args:['--disable-gpu']}); try { const context=await browser.newContext({baseURL:process.env.APP_BASE_URL}); const page=await context.newPage(); await page.goto('/login'); await page.getByLabel('Email').fill("+json.dumps(role+'@example.com')+"); await page.getByLabel('Password').fill('password'); await page.getByRole('button',{name:'Sign in'}).click(); await page.getByTestId('dashboard-page').waitFor(); await page.goto("+json.dumps(route)+"); console.log(await page.locator('body').ariaSnapshot()); } finally {await browser.close();}"
 (root/'.runtime/observe.mjs').write_text(script)
 return ui_command(root,folder,['/opt/homebrew/bin/node','.runtime/observe.mjs'],min(60,action['timeoutSeconds']))

@contextlib.contextmanager
def ui_service(repo,folder):
 with (folder/'crm-server.log').open('w') as f:
  p=subprocess.Popen(['/opt/homebrew/bin/node','examples/sample-crm-app/server.mjs'],cwd=repo,env={**os.environ,'PORT':str(UI_PORT)},stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   for _ in range(50):
    if p.poll() is not None:raise RuntimeError('CRM server exited')
    try:
     with urllib.request.urlopen(f'http://127.0.0.1:{UI_PORT}/login',timeout=1) as r:
      if r.status==200:break
    except OSError:pass
    time.sleep(.1)
   else:raise RuntimeError('CRM readiness timeout')
   yield
  finally:
   if p.poll() is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)

if __name__=='__main__':
 config=read(sys.argv[1]);action=read(sys.argv[2]);root=pathlib.Path(config['workspace']);folder=pathlib.Path(config['privateDir']);cmd=action['command'];seconds=action['timeoutSeconds']
 if config['project']=='api':
  # Delegate only to the existing fixed API adapter.
  p=subprocess.run([sys.executable,str(ROOT.parent/'workflows/runtime.py'),sys.argv[1],sys.argv[2]],capture_output=True,text=True,timeout=seconds+5)
  if p.returncode:raise RuntimeError(p.stderr)
  print(p.stdout,end='')
 else:
  if cmd=='verify':result=ui_verify(root,folder,seconds)
  elif cmd=='graph:refresh' and config['arm']=='context':result=graph(root,folder,seconds)
  elif cmd=='observe':result=observe(root,folder,action)
  else:raise ValueError('Unsupported UI command')
  print(json.dumps(result))
