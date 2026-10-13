import importlib.util,json,pathlib,subprocess,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'impact'))
spec=importlib.util.spec_from_file_location('impact_publisher_tested',ROOT/'impact/publish.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class ImpactPublicationTests(unittest.TestCase):
 def test_preserve_idempotence_review_revision_and_rollback(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp);remote=root/'remote.git';local=root/'seed';local.mkdir()
   def git(args,cwd=local):return subprocess.check_output(['git',*args],cwd=cwd,stderr=subprocess.DEVNULL,text=True).strip()
   git(['init','--bare',str(remote)]);git(['init']);git(['config','user.name','test']);git(['config','user.email','test@example.invalid']);git(['checkout','-b','benchmark-results'])
   for name in ['latest.json','trials.json','workflow-results.json']:(local/name).write_text('{"preserved":true}')
   git(['add','.']);git(['commit','-m','seed']);git(['push',str(remote),'HEAD:benchmark-results'])
   c={'rows':[{'id':str(i)} for i in range(12)],'plannedTrials':12,'campaignId':'a'*16,'updatedAt':'2026-10-12T12:00:00Z'}
   self.assertTrue(mod.publish(c,str(remote)).startswith('published'))
   self.assertEqual(mod.publish(c,str(remote)),'already published')
   reviewed={**c,'updatedAt':'2026-10-12T13:00:00Z'}
   self.assertTrue(mod.publish(reviewed,str(remote)).startswith('published'))
   with self.assertRaisesRegex(ValueError,'rollback'):mod.publish(c,str(remote))
   for name in ['latest.json','trials.json','workflow-results.json']:self.assertEqual(json.loads(git(['show','benchmark-results:'+name],remote)),{'preserved':True})
   archives=git(['ls-tree','-r','--name-only','benchmark-results','impact-campaigns'],remote).splitlines();self.assertEqual(len(archives),2)
   self.assertEqual(mod.export.__module__,'impact_export')
if __name__=='__main__':unittest.main()
