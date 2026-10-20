import importlib.util, json, pathlib, sys, tempfile, unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'automation'))
import publish as m
class AutomationTests(unittest.TestCase):
 def run_record(self,identity='a'*16,time='2026-10-11T10:00:00+00:00'):
  return {'project':'harness','runId':identity,'runAt':time,'execution':{'finishedAt':time}}
 def test_closed_vocabulary_excludes_free_text_and_rejects_unknown_keys(self):
  vocabulary=set(json.loads((ROOT/'automation/public-vocabulary.json').read_text()))
  safe=m.sanitize({'cases':[{'name':'private CRM customer Alice /Users/person/token','status':'passed'}],'limitations':['PRIVATE_PROMPT','a'*64],'revision':'f'*40},vocabulary)
  self.assertNotIn('private CRM',json.dumps(safe));self.assertNotIn('PRIVATE_PROMPT',json.dumps(safe));self.assertNotIn('a'*64,json.dumps(safe));self.assertEqual(safe['revision'],'f'*40)
  with self.assertRaises(ValueError):m.sanitize({'secret_key':'value'},vocabulary)
  with self.assertRaises(ValueError):m.sanitize({'metrics':[{'value':float('nan')}]},vocabulary)
 def test_history_dedup_and_late_old_run_do_not_replace_newer(self):
  newer=self.run_record('b'*16,'2026-10-11T11:00:00+00:00');data=m.merge(None,newer);data=m.merge(data,self.run_record());self.assertEqual(data['run'],newer);self.assertEqual(len(m.merge(data,newer)['history']),2)
 @patch.dict(m.os.environ,{'GITHUB_ACTIONS':'false'})
 def test_real_git_publication_is_idempotent_and_fast_forward(self):
  with tempfile.TemporaryDirectory() as folder:
   remote=str(pathlib.Path(folder)/'remote.git');m.git(['init','--bare',remote],folder)
   self.assertEqual(m.publish(self.run_record(),remote),'published')
   self.assertEqual(m.publish(self.run_record(),remote),'already published')
   newer=self.run_record('b'*16,'2026-10-11T11:00:00+00:00');m.publish(newer,remote)
   doc=json.loads(m.git(['show','benchmark-results:latest.json'],remote).stdout);self.assertEqual(len(doc['history']),2);self.assertEqual(doc['run']['runId'],newer['runId'])
 def test_stale_files_cannot_republish_success(self):
  oldhere=m.HERE
  try:
   with tempfile.TemporaryDirectory() as folder:
    root=pathlib.Path(folder);m.HERE=root/'benchmarks/dashboard';m.HERE.mkdir(parents=True)
    (m.HERE/'config.json').write_text(json.dumps({'expectedCases':[]}));(m.HERE/'public-vocabulary.json').write_bytes((ROOT/'automation/public-vocabulary.json').read_bytes())
    m.write(root/'benchmark-results/dashboard-execution.json',{'project':'harness','startedAt':'2026-10-11T12:00:00+00:00','finishedAt':'2026-10-11T12:01:00+00:00','exitCode':1})
    result=m.export(root,'harness');self.assertEqual(result['status'],'unavailable');self.assertEqual(result['integrity'],'invalid');self.assertEqual(result['metrics'],[])
  finally:m.HERE=oldhere
 def test_vendored_publishers_match_reviewed_source(self):
  for project in ['api','mockserver','harness']:
   for name in ['publish.py','run.py','import_benchmarks.py','public-vocabulary.json']:
    path=ROOT.parent/'work/repos'/project/'benchmarks/dashboard'/name
    if path.exists():self.assertEqual(path.read_bytes(),(ROOT/'automation'/name).read_bytes())
if __name__=='__main__':unittest.main()
