"""Public structured evidence only. Missing usage and reviews are never zero scores."""
import argparse,json,pathlib,statistics
from engine import *
from validity import assess

def usage(trace,calls):
 values=[];pending=False
 for e in trace:
  if e['type']=='model_request':
   if pending:values.append(None)
   pending=True
  elif e['type']=='assistant' and pending:
   m=e['message'];values.append(m.get('usage') if m['stopReason'] not in ['error','aborted'] else None);pending=False
 if pending:values.append(None)
 complete=bool(values) and len(values)==calls and all(v is not None and all(isinstance(v.get(k), (int,float)) and v[k]>=0 for k in ['input','output','cacheRead']) for v in values)
 return {'complete':complete,**{k:sum(v[k] for v in values) if complete else None for k in ['input','output','cacheRead']}}

def summary(rows):
 valid=[r for r in rows if r['validity']['status']=='valid'];times=[r['elapsedMs'] for r in valid];completed=[r for r in valid if r['complete'] is True]
 return {'started':len(rows),'valid':len(valid),'invalid':len(rows)-len(valid),'complete':len(completed),'incomplete':sum(r['complete'] is False for r in valid),'pending':sum(r['complete'] is None for r in valid),'medianAttemptMs':statistics.median(times) if times else None,'medianCompletedMs':statistics.median(r['elapsedMs'] for r in completed) if completed else None,'decisions':{key:{'correct':sum(r['decisions'].get(key) is True for r in valid),'reviewed':sum(r['decisions'].get(key) is not None for r in valid)} for key in ['ownership','action','grounding']}}

def export(out):
 plan=read(out/'plan.json');plan_hash=digest((out/'plan.json').read_bytes());rows=[]
 for trial in plan['runs']:
  folder=out/trial['id'];a=read(folder/'agent-result.json');g=read(folder/'grade.json');trace=[json.loads(l) for l in (folder/'trace.jsonl').read_text().splitlines()] if (folder/'trace.jsonl').exists() else []
  starts=[e for e in trace if e['type']=='tool_start'];ends=[e for e in trace if e['type']=='tool_end'];reads=a.get('filesRead',[]);validity=assess(folder,plan['budget']);review_path=folder/'review.json';review=read(review_path) if review_path.exists() else None
  if g['submissionSha256']!=digest((folder/'agent-result.json').read_bytes()) or g['finalSnapshotSha256']!=digest(json.dumps(snapshot(folder/'workspace'),sort_keys=True)):raise ValueError('Graded submission changed after acceptance')
  if review:
   if review['submissionSha256']!=digest((folder/'agent-result.json').read_bytes()) or review['rubricSha256']!=digest(json.dumps({'decisions':plan['decisionRubric'],'criteria':trial['task']['evaluatorCriteria']},sort_keys=True)):raise ValueError('Review does not match frozen submission/rubric')
   if set(review['decisions'])!=set(plan['decisionRubric']) or len(review['taskChecks'])!=len(trial['task']['evaluatorCriteria']):raise ValueError('Review incomplete')
   if not all(type(x['passed']) is bool and x['reason'].strip() for x in [*review['decisions'].values(),*review['taskChecks']]):raise ValueError('Review requires evidence-backed boolean checks')
   decisions={k:v['passed'] for k,v in review['decisions'].items()};task_checks=[v['passed'] for v in review['taskChecks']]
   complete=all(c['passed'] for c in g['automatedChecks']) and all(task_checks) and all(decisions.values())
  else:decisions={k:None for k in plan['decisionRubric']};task_checks=None;complete=False if not all(c['passed'] for c in g['automatedChecks']) else None
  if validity['status']!='valid':complete=None;decisions={k:None for k in decisions}
  first=lambda seq:min((e['elapsedMs'] for e in seq),default=None)
  context_read=[r for r in reads if r['path'].startswith(('contexts/','skills/','graphs/'))]
  evidence_read=[r for r in reads if r['path'] in trial['task']['evidence']]
  generation=[e for e in starts if e['name']=='bash' and e['params'].get('command') in ['context:resolve','npm run context:resolve','graph:refresh','npm run graph:view','npm run graph:coverage']]
  rows.append({'id':trial['id'],'taskId':trial['task']['id'],'title':trial['task']['title'],'project':trial['task']['project'],'operation':trial['task']['operation'],'arm':trial['arm'],'repeat':trial['repeat'],'status':a['status'],'validity':validity,'complete':complete,'decisions':decisions,'reviewed':review is not None,'reviewMethod':'supervising-assistant' if review else 'pending','automatedChecks':[{'id':c['id'],'label':c['label'],'passed':c['passed']} for c in g['automatedChecks']],'taskChecks':task_checks,'taskCriteria':trial['task']['evaluatorCriteria'],'elapsedMs':a.get('elapsedMs'),'modelCalls':a.get('modelResponses'),'toolCalls':a.get('toolCalls'),'toolErrors':sum(e['type']=='tool_error' for e in trace),'sourceEdits':a.get('edits'),'changedFiles':len(g['changedSourceFiles']),'verificationCycles':a.get('verificationCycles'),'repairs':a.get('repairs'),'usage':usage(trace,a.get('modelResponses')),'contextUse':{'instructionsAssigned':trial['arm']=='context','contextFilesRead':len({r['path'] for r in context_read}),'generationRequested':bool(generation),'firstContextReadMs':first(context_read),'firstDirectEvidenceReadMs':first(evidence_read)},'cost':{'externalInferenceUSD':0,'operatingUSD':None,'humanCorrectionMs':None},'evidence':{'submissionSha256':digest((folder/'agent-result.json').read_bytes()),'traceSha256':digest((folder/'trace.jsonl').read_bytes()) if (folder/'trace.jsonl').exists() else None,'gradeSha256':digest((folder/'grade.json').read_bytes()),'reviewSha256':digest(review_path.read_bytes()) if review else None}})
 audit=read(out/'context-audit.json')
 return {'schemaVersion':1,'protocol':'framework-impact-v1','campaignId':plan_hash[:16],'planSha256':plan_hash,'updatedAt':max([plan['createdAt']]+[read(out/r['id']/'grade.json')['gradedAt'] for r in plan['runs']]+[read(out/r['id']/'review.json')['reviewedAt'] for r in plan['runs'] if (out/r['id']/'review.json').exists()]),'sourceRevisions':plan['sourceRevisions'],'model':plan['model'],'budget':plan['budget'],'pairedRepeats':plan['pairedRepeats'],'plannedTrials':len(plan['runs']),'contextAudit':audit,'rows':rows,'summary':{project:{arm:summary([r for r in rows if r['project']==project and r['arm']==arm]) for arm in ['baseline','context']} for project in ['api','harness']},'limitations':plan['limitations']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--campaign',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();write(a.output,export(a.campaign.resolve()))
