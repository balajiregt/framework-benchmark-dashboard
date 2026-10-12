"""Closed public projection. Never export model text, code, paths or raw tool output."""
import argparse, json, pathlib, statistics
from runtime import read, write, digest
from validity import assess

STATUS={'agent-finished','context-limit','wall-budget','model-budget','tool-budget','verification-budget','response-timeout','output-limit','provider-error','host-error','host-failed','unexpected-compaction','host-interrupted'}
def export(folder):
 plan=read(folder/'plan.json');plan_hash=digest((folder/'plan.json').read_bytes());rows=[]
 for trial in plan['runs']:
  d=folder/trial['id'];a=read(d/'agent-result.json');g=read(d/'grade.json')
  if a['status'] not in STATUS:raise ValueError('Unknown operational status')
  trace=[json.loads(line) for line in (d/'trace.jsonl').read_text().splitlines()] if (d/'trace.jsonl').exists() else []
  events=lambda kind:[e for e in trace if e['type']==kind]
  reads=[{**r,'path':pathlib.PurePosixPath(r['path']).as_posix()} for r in a.get('filesRead',[])];evidence=[r for r in reads if r['path'] in trial['task']['evidence']]
  tools=events('tool_start');ends=events('tool_end');errors=events('tool_error')
  first=lambda seq:min((x['elapsedMs'] for x in seq),default=None)
  # Pair provider usage with recorded outbound requests. Pi may emit a final
  # controller stop message without another inference request; it is not usage.
  usage=[];pending=False
  for event in trace:
   if event['type']=='model_request':
    if pending:usage.append(None)
    pending=True
   elif event['type']=='assistant' and pending:
    message=event['message'];usage.append(None if message['stopReason'] in ['error','aborted'] else message.get('usage'));pending=False
  if pending:usage.append(None)
  complete=bool(usage) and len(usage)==a.get('modelResponses') and all(u is not None for u in usage)
  metric=lambda key:sum(u.get(key,0) for u in usage) if complete else None
  validity=assess(d,plan['budget']);valid=validity['status']=='valid'
  checks=[{'name':x['name'],'passed':x['passed'],'evaluated':not x.get('notEvaluated',False)} for x in g['checks']]
  entry={'instructions':any(r['path']=='AGENTS.md' for r in reads) or (trial['arm']=='context' and bool(events('bootstrap'))),
         'skill':any(r['path']=='skills/microservice-change/SKILL.md' for r in reads),
         'taskContext':any(r['path']=='contexts/current/service-context.yml' for r in reads),
         'resolver':any(e.get('name')=='run' and e.get('params',{}).get('command')=='context:resolve' for e in tools),
         'resolvedContext':any(r['path']=='contexts/current/resolved-context.yml' for r in reads)}
  rows.append({'taskId':trial['taskId'],'operation':trial['operation'],'arm':trial['arm'],'status':a['status'],
    'correct':g['correct'] if valid else None,'reviewStatus':g['reviewStatus'] if valid else 'invalid-infrastructure','checks':checks,'validity':validity,
    'elapsedMs':a.get('elapsedMs'),'gradingMs':g.get('gradingMs'),'modelResponses':a.get('modelResponses'),'toolCalls':a.get('toolCalls'),
    'verificationCycles':a.get('verificationCycles'),'repairs':a.get('repairs'),'sourceEdits':a.get('edits'),
    'changedFiles':len(g['changedSourceFiles']),'scopeViolations':len(g['outOfScopeChanges']),
    'uniqueFilesRead':len({r['path'] for r in reads}),'readCalls':len(reads),'returnedReadBytes':a.get('bytesRead'),
    'searches':a.get('searches'),'invalidReads':a.get('invalidPaths'),'toolErrors':len(errors),
    'truncatedOutputs':sum(e.get('truncated',False) for e in ends)+sum(r.get('truncated',False) for r in reads),
    'compactions':a.get('compactions'),'firstEvidenceMs':first(evidence),
    'firstEditMs':first([e for e in ends if e.get('name') in ['repo_edit','repo_write']]),
    'firstVerificationMs':first([e for e in tools if e.get('name')=='run' and e.get('params',{}).get('command')=='verify']),
    'inputTokens':metric('input'),'outputTokens':metric('output'),'cacheReadTokens':metric('cacheRead'),'usageComplete':complete,
    'humanCorrectionMs':None,'apiFeeUSD':0,'operatingCostUSD':None,'entrypoints':entry,
    'cycles':[{'cycle':v['cycle'],'passed':v['result']['passed'],'elapsedMs':v['result']['elapsedMs'],'sourceSha256':v['sourceHash']} for v in a.get('verification',[])],
    'evidence':{name:digest((d/file).read_bytes()) if (d/file).exists() else None for name,file in [('traceSha256','trace.jsonl'),('submissionSha256','agent-result.json'),('gradeSha256','grade.json')]}})
 arms={}
 for arm in ['baseline','context']:
  all_rs=[r for r in rows if r['arm']==arm];rs=[r for r in all_rs if r['validity']['status']=='valid']
  arms[arm]={'trials':len(all_rs),'validTrials':len(rs),'invalidTrials':len(all_rs)-len(rs),'confirmedCorrect':sum(r['correct'] is True for r in rs),'failed':sum(r['correct'] is False for r in rs),'pending':sum(r['correct'] is None for r in rs),
   'medianAttemptMs':statistics.median(r['elapsedMs'] for r in rs) if rs and all(r['elapsedMs'] is not None for r in rs) else None,
   'toolCalls':sum(r['toolCalls'] for r in rs) if rs and all(r['toolCalls'] is not None for r in rs) else None}
 return {'schemaVersion':1,'protocol':'qa-context-workflow-v2','campaignId':plan_hash[:16],'planSha256':plan_hash,'project':'api',
  'runnerProtocol':plan['protocol'],
  'updatedAt':max(read(folder/r['id']/'grade.json')['gradedAt'] for r in plan['runs']),
  'sourceRevision':plan['sourceRevision'],'model':plan['model'],'budget':plan['budget'],'plannedTrials':6,'pairedRepeats':1,
  'rows':rows,'arms':arms,'limitations':plan['limitations']}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--campaign',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();write(a.output,export(a.campaign.resolve()))
