"""Build a closed-schema public campaign; never serialize prompts, code, logs or local paths."""
import argparse, pathlib, statistics, json
from run import read,write,sha
from evaluate import FAULTS
RATE_SOURCE='https://developers.openai.com/api/docs/models/gpt-6.1-sol'
def estimate(usage):
 if not usage:return None
 total=usage['input_tokens'];cached=usage.get('cached_input_tokens',0);writes=usage.get('cache_write_input_tokens',0);output=usage['output_tokens']
 if any(not isinstance(n,int) or n<0 for n in [total,cached,writes,output]) or cached+writes>total or total>272000:raise ValueError('Usage outside verified short-context price assumptions')
 return round(((total-cached-writes)*2+cached*.1+writes*2.5+output*10)/1e6,8)
def export(out,project):
 plan=read(out/'plan.json');rows=[];local=plan.get('runtime')=='llama.cpp'
 for t in plan['trials']:
  if t['project']!=project:continue
  folder=out/t['id'];gpath=folder/'generation.json';epath=folder/'evaluation.json'
  if not gpath.exists():continue
  g=read(gpath);e=read(epath) if epath.exists() else None
  if sha((folder/'events.jsonl').read_bytes())!=g['eventsSha256']:raise ValueError('CLI event evidence changed')
  events=[]
  for line in (folder/'events.jsonl').read_text().splitlines():
   try:events.append(json.loads(line))
   except ValueError:pass
  usages=[ev.get('usage') for ev in events if ev.get('type') in ('turn.completed','turn.failed') and ev.get('usage') is not None]
  if g['usage']!=(usages[-1] if usages else None):raise ValueError('Usage does not match CLI event evidence')
  if e and (e['responseSha256']!=g['responseSha256'] or sha((folder/'response.json').read_bytes())!=g['responseSha256']):raise ValueError('Submission hash mismatch')
  if sha((folder/'prompt.txt').read_bytes())!=t['promptSha256']:raise ValueError('Prompt changed')
  phases=e['phases'] if e else []
  if e and [p['phase'] for p in phases]!=['healthy']+FAULTS[project]:raise ValueError('Wrong evaluation denominator')
  if e and e['correctCompletion']!=(e['protocolValid'] and all(p['passed'] for p in phases)):raise ValueError('Contradictory completion')
  timedOut=(folder/'provider-error.json').exists() and read(folder/'provider-error.json').get('type')=='TimeoutError'
  u=g['usage']
  if local and g.get('providerResponseSha256') and sha((folder/'provider-response.json').read_bytes())!=g['providerResponseSha256']:raise ValueError('Provider response changed')
  rows.append(dict(arm=t['arm'],repeat=t['repeat'],startedAt=g['startedAt'],finishedAt=g['finishedAt'],failureKind=('none' if e['correctCompletion'] else 'protocol-violation' if not e['protocolValid'] else 'build-or-runner-error' if e['phases'][0]['tests']==0 else 'healthy-check-failed' if not e['phases'][0]['passed'] else 'missed-fault') if e else 'generation-timeout' if timedOut else 'generation-failed' if g['exitCode'] else 'not-evaluated',operationalStatus='evaluated' if e else 'generation-failed' if g['exitCode'] else 'awaiting-evaluation',correct=e['correctCompletion'] if e else False,qualityPassed=e['qualityPassed'] if e else 0,qualityTotal=1+len(FAULTS[project]),timedOut=timedOut,generationMs=g['elapsedMs'],evaluationMs=e['evaluationMs'] if e else None,humanCorrectionMs=None,incorrectChanges=None,inputTokens=u['input_tokens'] if u else None,cachedInputTokens=u.get('cached_input_tokens',0) if u else None,outputTokens=u['output_tokens'] if u else None,apiEquivalentUSD=None if local else estimate(u),actualCostUSD=None,apiFeeUSD=0 if local else None,generationTokensPerSecond=(g.get('timings') or {}).get('predicted_per_second') if local else None,promptSha256=t['promptSha256'],responseSha256=g['responseSha256'],eventsSha256=g['eventsSha256'],evaluationSha256=sha(epath.read_bytes()) if e else None,checks=[dict(name=p['phase'],passed=p['passed'],outcome='satisfied' if p['passed'] else 'not-executed' if p['tests']==0 else 'healthy-failed' if p['phase']=='healthy' else 'fault-not-activated' if p['injectedResponses']==0 else 'execution-error' if p['errors'] else 'missed-fault',injectedResponses=p['injectedResponses']) for p in phases]))
 med=lambda values:statistics.median([v for v in values if v is not None]) if any(v is not None for v in values) else None
 arms={}
 for arm in ['baseline','framework']:
  selected=[r for r in rows if r['arm']==arm]
  arms[arm]=dict(trials=len(selected),evaluated=sum(r['operationalStatus']=='evaluated' for r in selected),correct=sum(r['correct'] for r in selected),qualityPassed=sum(r['qualityPassed'] for r in selected),qualityTotal=sum(r['qualityTotal'] for r in selected),medianGenerationMs=med([r['generationMs'] for r in selected]),medianEvaluationMs=med([r['evaluationMs'] for r in selected]),medianHumanCorrectionMs=None,totalInputTokens=sum(r['inputTokens'] or 0 for r in selected),totalOutputTokens=sum(r['outputTokens'] or 0 for r in selected),apiEquivalentUSD=round(sum(r['apiEquivalentUSD'] or 0 for r in selected),8) if selected and all(r['apiEquivalentUSD'] is not None for r in selected) else None,actualCostUSD=None)
 result=dict(schemaVersion=1,project=project,campaignId=sha((out/'plan.json').read_bytes())[:16],protocol='one-response-mutation-v1',runtime='llama.cpp' if local else 'codex-cli',createdAt=plan['createdAt'],updatedAt=max([r['finishedAt'] for r in rows],default=plan['createdAt']),model=plan['model'],modelVersion=('GGUF SHA256 '+plan['local']['modelFileSha256']) if local else 'Alias requested; backend snapshot not exposed by CLI',reasoning=plan['reasoning'],cliVersion=plan['cliVersion'],sourceRevision=next(t['sourceRevision'] for t in plan['trials'] if t['project']==project),targetSha256=next(t['targetSha256'] for t in plan['trials'] if t['project']==project),planSha256=sha((out/'plan.json').read_bytes()),plannedTrials=6,pairedRepeats=len(set(r['repeat'] for r in rows if r['arm']=='baseline') & set(r['repeat'] for r in rows if r['arm']=='framework')),arms=arms,rows=rows,pricing=dict(classification='API-equivalent estimate, not billed spend',source=RATE_SOURCE,asOf='2026-10-11',currency='USD',inputPerMillion=2,cachedInputPerMillion=.1,cacheWritePerMillion=2.5,outputPerMillion=10),limitations=['One task per application; three repeats per arm, descriptive pilot only.','Tests are generated in one response with tools disabled; full planning, capture, repair and review workflows were not measured.','The framework condition adds existing helpers and conventions; context size differs intentionally.','Generated tests run unchanged against the real sample app via controlled fault injection. Synthetic faults are not production defects.','Generation wall time includes CLI/provider overhead. Evaluation time is separate; background machine load was not controlled.','The same model alias and CLI configuration were requested; a fixed backend model snapshot is not exposed.','Human correction effort and incorrect changes require a human review; neither is inferred from automatic checks.','Cost is a counterfactual standard-tier API estimate from CLI tokens, including cache counts; actual billed spend, subscription allocation and infrastructure cost are unavailable.'])
 if local:
  result['pricing']=None;result['localRuntime']=plan['local']
  result['limitations']=[x for x in result['limitations'] if not any(word in x for word in ['CLI','alias','Cost is'])]+['Timeouts stay in the denominator; attempt durations are right-censored at the 180-second client deadline, not completed generation latency.','Local llama.cpp inference with the workspace Gemma model; Pi tool execution and the complete local agent loop were not tested.','Identical API task text and fault checks to the cloud pilot; provider wrappers, tokenizer and model differ, so this is not an isolated hardware comparison.','Existing 8192-token server; one slot; max output 4096; temperature 0.2; seed matches each repeat; cache_prompt=false. No model reload or hardware isolation.','No external inference API fee for these loopback requests. Electricity, hardware depreciation, subscription allocation and total operating cost are unmeasured.']
  for arm in ['baseline','framework']:
   selected=[r for r in rows if r['arm']==arm]
   result['arms'][arm]['medianGenerationTokensPerSecond']=med([r['generationTokensPerSecond'] for r in selected]);result['arms'][arm]['apiFeeUSD']=0 if selected and all(r['apiFeeUSD']==0 for r in selected) else None
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--project',choices=['harness','api'],required=True);p.add_argument('--destination',type=pathlib.Path,required=True);a=p.parse_args();value=export(a.output.resolve(),a.project);write(a.destination,value);print(a.project,value['campaignId'],value['arms'])
