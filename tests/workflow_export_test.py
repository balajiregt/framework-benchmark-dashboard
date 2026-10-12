import importlib.util,json,pathlib,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'workflows'))
spec=importlib.util.spec_from_file_location('workflow_export_tested',ROOT/'workflows/export.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class ExportTests(unittest.TestCase):
 def test_closed_projection_keeps_private_text_out_and_retains_failed_usage(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);runs=[]
   for operation in ['create','update','validate']:
    for arm in ['baseline','context']:
     ident=operation+'-'+arm;d=root/ident;d.mkdir()
     runs.append({'id':ident,'taskId':'api-'+operation+'-sample','operation':operation,'arm':arm,'task':{'evidence':['private-source.java'],'request':'SECRET TASK','evaluatorCriteria':['SECRET GOLD']}})
     a={'status':'response-timeout','modelResponses':2,'toolCalls':1,'verificationCycles':0,'repairs':0,'usage':[{'input':10,'output':5},None],'filesRead':[{'path':'./private-source.java','elapsedMs':2,'bytes':10}],'bytesRead':10,'edits':0,'elapsedMs':180000,'finalText':'SECRET MODEL TEXT','searches':0,'invalidPaths':0,'compactions':0}
     g={'correct':False,'reviewStatus':'failed-automated-checks','gradedAt':'2026-10-11T12:00:00Z','changedSourceFiles':[],'outOfScopeChanges':[],'checks':[{'name':'healthy-suite','passed':False,'notEvaluated':True}],'gradingMs':10}
     for name,v in [('agent-result.json',a),('grade.json',g)]: (d/name).write_text(json.dumps(v))
     (d/'host-clock.json').write_text(json.dumps({'maxClockGapMs':100}))
     (d/'trace.jsonl').write_text(json.dumps({'type':'clock_watchdog','elapsedMs':180000,'maxClockGapMs':100})+'\n'+json.dumps({'type':'tool_start','name':'repo_read','elapsedMs':1,'params':{'path':'private-source.java'},'private':'SECRET TRACE'})+'\n')
   (root/'plan.json').write_text(json.dumps({'runs':runs,'sourceRevision':'a'*40,'model':{},'protocol':'test','budget':{'wallMs':900000,'responseMs':180000,'modelResponses':36,'toolCalls':80,'verificationCycles':3},'limitations':['fixture']}))
   c=mod.export(root);text=json.dumps(c)
   for forbidden in ['SECRET','private-source.java','finalText','evaluatorCriteria']:self.assertNotIn(forbidden,text)
   self.assertEqual(c['arms']['baseline']['failed'],3);self.assertEqual(c['arms']['context']['pending'],0)
   self.assertIsNone(c['rows'][0]['inputTokens']);self.assertIsNone(c['rows'][0]['operatingCostUSD']);self.assertEqual(c['rows'][0]['apiFeeUSD'],0)
   self.assertFalse(c['rows'][0]['checks'][0]['evaluated']);self.assertEqual(c['rows'][0]['firstEvidenceMs'],2)
   for d in root.iterdir():
    if not d.is_dir():continue
    events=[]
    for i in [1,2]:events += [{'type':'model_request','index':i,'elapsedMs':i*10},{'type':'assistant','elapsedMs':i*10+1,'message':{'stopReason':'length' if i==2 else 'toolUse','usage':{'input':10,'output':5,'cacheRead':0}}}]
    events.append({'type':'assistant','message':{'stopReason':'error','usage':{'input':0,'output':0}}})
    with (d/'trace.jsonl').open('a') as f:f.write(''.join(json.dumps(e)+'\n' for e in events))
   c=mod.export(root);self.assertTrue(c['rows'][0]['usageComplete']);self.assertEqual(c['rows'][0]['inputTokens'],20);self.assertEqual(c['rows'][0]['outputTokens'],10)
   d=root/runs[0]['id'];a=json.loads((d/'agent-result.json').read_text());a['elapsedMs']=71099038;(d/'agent-result.json').write_text(json.dumps(a));c=mod.export(root)
   self.assertEqual(c['rows'][0]['validity']['status'],'invalid-infrastructure');self.assertIsNone(c['rows'][0]['correct']);self.assertEqual(c['arms']['baseline']['failed'],2);self.assertEqual(c['arms']['baseline']['invalidTrials'],1)
if __name__=='__main__':unittest.main()
