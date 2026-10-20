import importlib.util, pathlib, tempfile, unittest, json, hashlib
spec=importlib.util.spec_from_file_location('importer',pathlib.Path(__file__).resolve().parents[1]/'scripts/import_benchmarks.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class EvidenceTests(unittest.TestCase):
 def write(self,root,name,data):
  path=root/name;path.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(data).encode();path.write_bytes(raw);return hashlib.sha256(raw).hexdigest()
 def browser(self,status='passed',expected='passed'):
  return {'suites':[{'specs':[{'title':'viewer export denied in UI and API','tests':[{'expectedStatus':expected,'results':[{'status':status}]}]}]}]}
 def test_missing_source_is_unavailable(self):
  with tempfile.TemporaryDirectory() as d:
   for kind in m.REPOS:
    r=m.collect(kind,pathlib.Path(d));self.assertEqual(r['status'],'unavailable');self.assertEqual(r['integrity'],'invalid')
 def test_tampered_mutation_hash_and_expected_failures_are_invalid(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);self.write(root,'benchmark-results/oracle.json',self.browser());h=self.write(root,'benchmark-results/mutant.json',self.browser('failed'));self.write(root,'benchmark-results/mutation-summary.json',{'detected':True,'reportSha256':'0'*64});self.assertEqual(m.collect('harness',root)['integrity'],'invalid');self.write(root,'benchmark-results/mutation-summary.json',{'detected':True,'reportSha256':h});self.assertEqual(m.collect('harness',root)['integrity'],'verified');self.write(root,'benchmark-results/oracle.json',self.browser(expected='failed'));self.assertEqual(m.collect('harness',root)['integrity'],'invalid')

 def test_api_source_hash_mismatch_does_not_verify(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);r=self.browser();r['sourceReports']=[{'file':'TEST.xml','sha256':'0'*64}];self.write(root,'benchmark-results/api-oracle.json',r);self.assertEqual(m.collect('api',root)['integrity'],'invalid')
 def test_trial_pairs_separate_models_and_hide_review_notes(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);row={'evidenceKind':'live-agent','arm':'baseline','repeat':0,'taskId':'crm-viewer-export','model':'m','modelVersion':'v1','targetRevision':'a'*64,'reportSha256':'b'*64,'checks':[{'passed':True}],'correctCompletion':True,'elapsedMs':100,'humanCorrectionMs':None,'incorrectChanges':None,'reviewerEvidence':'PRIVATE_NOTE','cost':None}
   self.write(root,'benchmark-results/trials/a.json',row);self.write(root,'benchmark-results/trials/b.json',{**row,'arm':'framework','modelVersion':'v2'});r=m.trial_summary(root);self.assertEqual(r['pairedRepeats'],0);self.assertEqual(r['liveTrials'],2);self.assertNotIn('PRIVATE_NOTE',json.dumps(r));self.write(root,'benchmark-results/trials/b.json',{**row,'arm':'framework'});self.assertEqual(m.trial_summary(root)['pairedRepeats'],1);self.write(root,'benchmark-results/trials/c.json',row);self.assertEqual(m.trial_summary(root)['invalidRecords'],1)
if __name__=='__main__':unittest.main()
