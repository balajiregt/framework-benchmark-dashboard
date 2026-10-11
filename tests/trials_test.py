import importlib.util,json,pathlib,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'trials'))
from evaluate import playwright_result,junit_result,forbidden
from export import estimate
class TrialEvidenceTests(unittest.TestCase):
 def test_cost_separates_cache_categories(self):
  self.assertEqual(estimate({'input_tokens':1000,'cached_input_tokens':200,'cache_write_input_tokens':100,'output_tokens':100}),.00267)
  with self.assertRaises(ValueError):estimate({'input_tokens':100,'cached_input_tokens':200,'output_tokens':1})
 def test_missing_report_never_passes(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(playwright_result(pathlib.Path(d)/'missing')['errors'],1)
 def test_browser_execution_timeout_is_not_assertion(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'report.json';p.write_text(json.dumps({'suites':[{'specs':[{'tests':[{'results':[{'status':'timedOut','errors':[{'message':'Test timeout exceeded'}]}]}]}]}]}))
   r=playwright_result(p);self.assertEqual(r['assertionFailures'],0);self.assertEqual(r['errors'],1)
 def test_junit_errors_not_mutation_detection(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'TEST-a.CustomerRiskTrialTest.xml';p.write_text('<testsuite><testcase><error type="ConnectException"/></testcase><testcase><failure type="java.lang.AssertionError"/></testcase><testcase><system-out>request</system-out></testcase></testsuite>')
   r=junit_result(pathlib.Path(d));self.assertEqual((r['testsPassed'],r['assertionFailures'],r['errors']),(1,1,1))
 def test_baseline_cannot_import_framework_or_skip(self):
  self.assertTrue(forbidden("import {test} from '../fixtures/base.fixture'",'harness','baseline'))
  self.assertTrue(forbidden("test.skip('x')",'harness','framework'))
  self.assertFalse(forbidden("import {test} from '../fixtures/base.fixture'",'harness','framework'))
if __name__=='__main__':unittest.main()
