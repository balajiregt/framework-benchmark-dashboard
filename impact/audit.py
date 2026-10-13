"""Check framework-provided context against separately specified source/runtime facts."""
import argparse,json,pathlib,sys,time,urllib.request,urllib.error
import yaml
from engine import *

def check(id,label,passed,evidence):return {'id':id,'label':label,'status':'pass' if passed else 'fail','evidence':evidence}
def api_checks(root,resolved):
 expected={
  'controller':'projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/api/CustomerRiskController.java',
  'service':'projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/service/CustomerRiskService.java',
  'openapi':'projects/microservices/xyz-service/src/main/resources/openapi/xyz-service.openapi.yml',
  'api_test':'projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java',
  'shared_fixtures':'projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/fixtures/CustomerFixtures.java',
  'shared_assertions':'projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/assertions/JsonFieldAssertions.java'}
 rows=[check('path-'+k,'Resolves '+k.replace('_',' '),resolved.get('resolved_files',{}).get(k)==v and (root/v).is_file(),v) for k,v in expected.items()]
 q=resolved.get('derived_validation',{}).get('query_parameter',{});src=resolved.get('derived_validation',{}).get('source',{})
 rows+=[check('query-contract','Required nonempty customerId; no format pattern',q.get('name')=='customerId' and q.get('required') is True and q.get('minLength')==1 and q.get('has_pattern') is False,'Compared with the OpenAPI customerId schema.'),check('normalization-signals','Trim/case normalization and no regex signal',src.get('implementation_signals',{}).get('normalizes_string_with_trim') is True and src.get('implementation_signals',{}).get('normalizes_string_case') is True and src.get('implementation_signals',{}).get('has_explicit_pattern_or_regex_check') is False,'Compared with the controller and CustomerRiskService implementation.'),check('verification-owner','Verification targets the separate QA project',any('qa-projects/xyz-service-api-tests' in c and 'api.port=4383' in c for c in resolved.get('verification',{}).get('commands',[])),'Compared with Maven module ownership and the frozen local runtime.')]
 rows.append({'id':'runtime-freshness','label':'Automatic staleness detection','status':'unmeasured','evidence':'Generated output has a timestamp but no complete dependency fingerprint. This audit regenerates it from the pinned source; no general freshness guarantee is inferred.'})
 return rows

def ui_checks(root,manifest,graph_data,session_evidence):
 routes={r['path']:r for r in manifest['routes']};cases=graph_data['testCases'];manager=next((t for t in cases if 'manager can use allowed action buttons' in t['title']),{})
 rows=[check('role-routes','Manifest preserves viewer and manager route permissions',routes['/crm/leads']['roles']==['admin','sales'] and routes['/crm/reports']['roles']==['admin','manager'] and routes['/crm/accounts']['roles']==['admin','manager','viewer'],'Compared with the current app routeConfig and seeded users.'),check('owning-files','Graph identifies the test, page and assertion owners',all(any(n.get('file')==p for n in graph_data['nodes']) for p in ['tests/sample-crm.spec.ts','pages/sample-crm.page.ts','assertions/sample-crm.assertions.ts']),'Compared with the actual imports and class implementations.'),check('existing-manager-routes','Graph records existing manager direct-route steps',manager.get('file')=='tests/sample-crm.spec.ts' and all(x in manager.get('methods',[]) for x in ['gotoLeads','gotoAdminUsers','expectPermissionDeniedForPath']) and all(x in manager.get('routes',[]) for x in ['/crm/leads','/crm/admin/users']),'The current manager test already contains both route visits and path-specific denial assertions.'),check('helper-evidence','Framework tells the agent to inspect helper implementations','existing Playwright config, tests, fixtures, page objects' in (root/'AGENTS.md').read_text(),'Graphs are navigation hints; body/helper inspection remains necessary.'),check('api-auth-context','Manifest describes the API session requirement',manifest.get('auth',{}).get('strategy')!='localStorage' or bool(manifest.get('auth',{}).get('apiSession')),'The manifest says localStorage only. Live API observation: unauthenticated export returns '+str(session_evidence['unauthenticatedStatus'])+', viewer login creates HttpOnly cookie, authenticated export returns '+str(session_evidence['viewerStatus'])+'.'),check('capture-api-session','Capture workflow establishes the API session',"/api/session" in (root/'scripts/run-capture-recipe.mjs').read_text(),'Current runner injects localStorage only; this can establish UI state but does not create the HttpOnly API session.')]
 rows.append({'id':'capture-freshness','label':'Existing captures tied to the current source revision','status':'unmeasured','evidence':'Committed capture existence does not establish freshness. No source fingerprint is available for the saved page snapshots.'})
 return rows

def session_probe():
 base=f'http://127.0.0.1:{UI_PORT}'
 def call(path,data=None,cookie=None):
  req=urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json',**({'Cookie':cookie} if cookie else {})})
  try:r=urllib.request.urlopen(req,timeout=5)
  except urllib.error.HTTPError as e:r=e
  with r:return r.status,r.read().decode(),r.headers
 unauth,_,_=call('/api/accounts/export');status,_,headers=call('/api/session',json.dumps({'email':'viewer@example.com','password':'password'}).encode());cookie=headers.get('Set-Cookie','')
 viewer,body,_=call('/api/accounts/export',cookie=cookie.split(';')[0])
 if status!=200 or 'HttpOnly' not in cookie or unauth!=401 or viewer!=403 or json.loads(body)!={'error':'Access denied'}:raise RuntimeError('CRM session preflight differs from reference behaviour')
 return {'unauthenticatedStatus':unauth,'loginStatus':status,'httpOnlyCookie':True,'viewerStatus':viewer,'viewerBody':json.loads(body)}

def run(sources,out):
 if out.exists():raise ValueError('Preserve prior audits; choose a fresh output')
 out.mkdir(parents=True);catalog=read(ROOT/'tasks.json');result={'schemaVersion':1,'protocol':'context-audit-v1','createdAt':now(),'sources':catalog['sourceRevisions'],'projects':[]}
 for name in ['api','harness']:
  repo=sources[name];revision=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
  if revision!=catalog['sourceRevisions'][name] or subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip():raise ValueError('Use clean pinned source for '+name)
  t=next(t for t in catalog['tasks'] if t['project']==name);folder=out/name;folder.mkdir();root=folder/'workspace';project(repo,root,t,'context');start=time.monotonic()
  if name=='api':
   execution=api.command(root,folder,[sys.executable,'scripts/resolve_context.py'],root)
   if execution['exitCode']:raise RuntimeError(execution['output'])
   artifact=root/'contexts/current/resolved-context.yml';checks=api_checks(root,yaml.safe_load(artifact.read_text()));artifacts=[artifact]
  else:
   execution=graph(root,folder)
   if execution['exitCode']:raise RuntimeError(execution['output'])
   with ui_service(repo,folder):runtime_evidence=session_probe()
   write(folder/'session-evidence.json',runtime_evidence)
   artifacts=[root/'examples/sample-crm-app/source-manifest.json',root/'graphs/data/test-graph.json',root/'graphs/data/coverage-graph.json']
   checks=ui_checks(root,read(artifacts[0]),read(artifacts[1]),runtime_evidence)
  write(folder/'execution.json',execution)
  result['projects'].append({'project':name,'revision':revision,'checks':checks,'generationMs':execution['elapsedMs'],'artifactSha256':[digest(p.read_bytes()) for p in artifacts],'sourceStatus':'pinned-clean','notes':'Source-grounded component audit; these checks do not establish agent productivity or generalisation.'})
 write(out/'audit.json',result);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--api',type=pathlib.Path,required=True);p.add_argument('--harness',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();r=run({'api':a.api.resolve(),'harness':a.harness.resolve()},a.output.resolve());print(json.dumps({'projects':[{'project':x['project'],'checks':[(c['id'],c['status']) for c in x['checks']]} for x in r['projects']]}))
