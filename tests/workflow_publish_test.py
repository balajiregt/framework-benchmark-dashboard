import importlib.util,json,pathlib,subprocess,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'workflows'))
spec=importlib.util.spec_from_file_location('workflow_publisher_tested',ROOT/'workflows/publish.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class PublicationTests(unittest.TestCase):
 def test_feed_publication_preserves_older_tracks_is_idempotent_and_refuses_rollback(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp);remote=root/'remote.git';local=root/'seed';local.mkdir()
   def git(args,cwd=local):return subprocess.check_output(['git',*args],cwd=cwd,stderr=subprocess.DEVNULL,text=True).strip()
   git(['init','--bare',str(remote)]);git(['init']);git(['config','user.name','test']);git(['config','user.email','test@example.invalid']);git(['checkout','-b','benchmark-results'])
   for name in ['latest.json','trials.json','local-trials.json']:(local/name).write_text('{"preserved":true}')
   git(['add','.']);git(['commit','-m','seed']);git(['push',str(remote),'HEAD:benchmark-results'])
   c={'rows':[{}]*6,'campaignId':'a'*16,'updatedAt':'2026-10-11T12:00:00Z'}
   self.assertTrue(mod.publish(c,str(remote)).startswith('published'))
   self.assertEqual(mod.publish(c,str(remote)),'already published')
   for name in ['latest.json','trials.json','local-trials.json']:self.assertEqual(json.loads(git(['show','benchmark-results:'+name],remote)),{'preserved':True})
   self.assertEqual(json.loads(git(['show','benchmark-results:workflow-campaigns/'+c['campaignId']+'.json'],remote)),c)
   older={**c,'updatedAt':'2026-10-10T12:00:00Z'}
   with self.assertRaisesRegex(ValueError,'newer'):mod.publish(older,str(remote))
if __name__=='__main__':unittest.main()
