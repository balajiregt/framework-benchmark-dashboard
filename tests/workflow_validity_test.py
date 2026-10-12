import json,pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'workflows'))
from validity import assess
class TimingTests(unittest.TestCase):
 def make(self,root,elapsed=1000,response=900,gap=110):
  a={'elapsedMs':elapsed,'modelResponses':1,'toolCalls':0,'verificationCycles':0,'status':'response-timeout'}
  (root/'agent-result.json').write_text(json.dumps(a));(root/'host-clock.json').write_text(json.dumps({'maxClockGapMs':gap}))
  events=[{'type':'model_request','elapsedMs':0},{'type':'assistant','elapsedMs':response},{'type':'clock_watchdog','elapsedMs':elapsed,'maxClockGapMs':gap}]
  (root/'trace.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
  return {'wallMs':900000,'responseMs':180000,'modelResponses':36,'toolCalls':80,'verificationCycles':3}
 def test_timeout_within_budget_is_valid_failure(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);b=self.make(p,182000,181000);self.assertEqual(assess(p,b)['status'],'valid')
 def test_response_overrun_invalid_even_when_total_time_within_budget(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);b=self.make(p,210000,209000);self.assertIn('response-deadline-exceeded',assess(p,b)['reasons'])
 def test_overnight_run_and_pause_never_become_quality_failure(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);b=self.make(p,71099038,71098000,70000000);a=assess(p,b);self.assertEqual(a['status'],'invalid-infrastructure');self.assertIn('wall-deadline-exceeded',a['reasons']);self.assertIn('host-pause-detected',a['reasons'])
 def test_missing_telemetry_is_not_assumed_valid(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);b=self.make(p);(p/'host-clock.json').unlink();self.assertIn('missing-clock-watchdog',assess(p,b)['reasons'])
if __name__=='__main__':unittest.main()
