import contextlib,importlib.util,json,pathlib,sys,tempfile,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'impact'))
spec=importlib.util.spec_from_file_location('impact_runner',ROOT/'impact/run.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class StopTests(unittest.TestCase):
 def test_invalid_attempt_prevents_next_launch_and_preserves_stop_receipt(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=pathlib.Path(tmp);mod.write(out/'context-audit.json',{})
   runs=[]
   for ident in ['first','must-not-start']:
    d=out/ident;d.mkdir();mod.write(d/'config.json',{});mod.write(d/'initial.json',{})
    runs.append({'id':ident,'task':{},'configSha256':mod.digest((d/'config.json').read_bytes()),'initialSha256':mod.digest((d/'initial.json').read_bytes())})
   mod.write(out/'first/agent-result.json',{'status':'host-interrupted'})
   mod.write(out/'plan.json',{'implementationSha256':{},'contextAuditSha256':mod.digest((out/'context-audit.json').read_bytes()),'budget':{},'runs':runs})
   invalid={'status':'invalid-infrastructure','reasons':['host-pause-detected']}
   with patch.object(mod,'awake',return_value=contextlib.nullcontext()),patch.object(mod.api,'service',return_value=contextlib.nullcontext(None)),patch.object(mod,'ui_service',return_value=contextlib.nullcontext()),patch.object(mod,'assess',return_value=invalid),patch.object(mod,'grade',return_value={'automatedChecks':[]}),patch.object(mod,'run_agent') as launch:
    with self.assertRaisesRegex(RuntimeError,'halted'):mod.run({'api':out,'harness':out},out)
    launch.assert_not_called()
   self.assertEqual(mod.read(out/'halted.json')['trial'],'first')
   self.assertFalse((out/'must-not-start/started.json').exists())
   with self.assertRaisesRegex(RuntimeError,'already halted'):mod.run({'api':out,'harness':out},out)
 def test_valid_attempt_does_not_halt(self):
  with tempfile.TemporaryDirectory() as tmp:
   mod.halt_on_invalid(pathlib.Path(tmp),'valid',{'status':'valid'})
   self.assertFalse((pathlib.Path(tmp)/'halted.json').exists())
if __name__=='__main__':unittest.main()
