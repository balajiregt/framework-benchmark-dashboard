import importlib.util,pathlib,tempfile,unittest
from unittest.mock import patch
R=pathlib.Path(__file__).resolve().parents[1]/'workflows'
spec=importlib.util.spec_from_file_location('workflow_runtime_tested',R/'runtime.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
class RuntimeTests(unittest.TestCase):
 def test_junit_distinguishes_assertions_errors_skips_and_empty(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp);reports=root/runtime.QA/'target/surefire-reports';reports.mkdir(parents=True)
   (reports/'TEST-sample.xml').write_text('<testsuite><testcase name="good"/><testcase name="fault"><failure type="java.lang.AssertionError"/></testcase><testcase name="broken"><error type="java.net.SocketException"/></testcase><testcase name="skip"><skipped/></testcase></testsuite>')
   cases=runtime.junit(root);self.assertTrue(cases[0]['passed']);self.assertTrue(cases[1]['assertionFailure']);self.assertTrue(cases[2]['error']);self.assertTrue(cases[3]['skipped'])
 def test_verification_clears_stale_compiled_classes_and_cannot_pass_empty_report(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp)
   for module in [runtime.QA,runtime.API+'/qa-steps']:
    target=root/module/'target';target.mkdir(parents=True);(target/'Stale.class').write_text('old')
   with patch.object(runtime,'command',return_value={'exitCode':0}) as command:
    result=runtime.verify(root,root);self.assertFalse(result['passed'])
    self.assertIn('-o',command.call_args.args[2]);self.assertTrue(all(not (root/m/'target/Stale.class').exists() for m in [runtime.QA,runtime.API+'/qa-steps']))
 def test_context_summary_cannot_leak_evaluator_title(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp);repo=base/'repo';repo.mkdir()
   for name in ['AGENTS.md','skills/microservice-change/SKILL.md','scripts/resolve_context.py']:
    f=repo/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('context asset')
   task={'title':'HIDDEN GOLD CLASSIFICATION','request':'Neutral request','operation':'validate'}
   with patch.object(runtime.subprocess,'check_output',return_value=''):runtime.project(repo,base/'workspace',task,'context')
   content=(base/'workspace/contexts/current/service-context.yml').read_text()
   self.assertNotIn(task['title'],content);self.assertEqual(runtime.read(base/'workspace/contexts/current/service-context.yml')['work_item']['summary'],task['request'])
 def test_private_paths_are_not_workspace_paths(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp)
   for p in ['../grading.json','target/result.xml','.home/settings']:
    with self.assertRaises(ValueError):runtime.checked(root,p)
if __name__=='__main__':unittest.main()
