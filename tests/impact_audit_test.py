import importlib.util,json,pathlib,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'impact'/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
sys.path.insert(0,str(ROOT/'impact'))
audit=module('impact_audit','audit.py');export=module('impact_export','export.py')
class ImpactTests(unittest.TestCase):
 def test_missing_usage_does_not_become_free_or_zero(self):
  r=export.usage([{'type':'model_request'},{'type':'assistant','message':{'stopReason':'error','usage':{'input':0,'output':0,'cacheRead':0}}}],1)
  self.assertFalse(r['complete']);self.assertIsNone(r['input'])
 def test_controller_stop_is_not_an_inference(self):
  r=export.usage([{'type':'model_request'},{'type':'assistant','message':{'stopReason':'stop','usage':{'input':10,'output':2,'cacheRead':3}}},{'type':'assistant','message':{'stopReason':'error'}}],1)
  self.assertEqual(r,{'complete':True,'input':10,'output':2,'cacheRead':3})
 def test_failed_attempt_time_is_not_success_latency(self):
  row={'validity':{'status':'valid'},'elapsedMs':1000,'complete':False,'decisions':{'ownership':True,'action':False,'grounding':None}}
  r=export.summary([row]);self.assertEqual(r['medianAttemptMs'],1000);self.assertIsNone(r['medianCompletedMs']);self.assertEqual(r['decisions']['grounding']['reviewed'],0)
 def test_invalid_attempts_stay_visible_but_outside_outcomes(self):
  row={'validity':{'status':'invalid-infrastructure'},'elapsedMs':99999,'complete':True,'decisions':{'ownership':True,'action':True,'grounding':True}}
  r=export.summary([row]);self.assertEqual(r['invalid'],1);self.assertEqual(r['complete'],0);self.assertIsNone(r['medianAttemptMs'])
 def test_auth_mismatch_and_wrong_graph_are_detected(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp);(root/'scripts').mkdir();(root/'AGENTS.md').write_text('Inspect existing Playwright config, tests, fixtures, page objects');(root/'scripts/run-capture-recipe.mjs').write_text('localstorage-set')
   manifest={'routes':[{'path':'/crm/leads','roles':['admin','sales']},{'path':'/crm/reports','roles':['admin','manager']},{'path':'/crm/accounts','roles':['admin','manager','viewer']}],'auth':{'strategy':'localStorage'}}
   graph={'testCases':[],'nodes':[]};checks={x['id']:x['status'] for x in audit.ui_checks(root,manifest,graph,{'unauthenticatedStatus':401,'viewerStatus':403})}
   self.assertEqual(checks['role-routes'],'pass');self.assertEqual(checks['owning-files'],'fail');self.assertEqual(checks['api-auth-context'],'fail');self.assertEqual(checks['capture-api-session'],'fail');self.assertEqual(checks['capture-freshness'],'unmeasured')
 def test_catalog_uses_actual_existing_manager_coverage(self):
  data=json.loads((ROOT/'impact/tasks.json').read_text());t=next(x for x in data['tasks'] if x['id']=='ui-validate-manager-coverage');self.assertEqual(t['expectedAction'],'already-covered');self.assertEqual(len(data['tasks']),6)
