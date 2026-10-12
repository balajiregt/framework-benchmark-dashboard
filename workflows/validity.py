"""Audit timing separately from task quality; never clamp or hide invalid attempts."""
import json
from runtime import read
GRACE_MS=5000
PAUSE_MS=10000

def assess(folder,budget):
 a=read(folder/'agent-result.json');reasons=[]
 trace=[json.loads(line) for line in (folder/'trace.jsonl').read_text().splitlines()] if (folder/'trace.jsonl').exists() else []
 clock=[e for e in trace if e['type']=='clock_watchdog']
 host=read(folder/'host-clock.json') if (folder/'host-clock.json').exists() else None
 elapsed=a.get('elapsedMs')
 if not isinstance(elapsed,(int,float)) or elapsed<0:reasons.append('missing-elapsed-time')
 elif elapsed>budget['wallMs']+GRACE_MS:reasons.append('wall-deadline-exceeded')
 if not clock or not host:reasons.append('missing-clock-watchdog')
 gap=max([e.get('maxClockGapMs',0) for e in clock]+[host.get('maxClockGapMs',0) if host else 0])
 if gap>PAUSE_MS:reasons.append('host-pause-detected')
 if a['status'] in ['host-interrupted','host-error','host-failed']:reasons.append('host-failure')
 request=None;durations=[]
 for e in trace:
  timestamp=e.get('elapsedMs')
  if e['type'] in ['model_request','tool_start'] and isinstance(timestamp,(int,float)) and timestamp>budget['wallMs']:reasons.append('work-started-after-deadline')
  if e['type']=='model_request':
   if request is not None:reasons.append('overlapping-model-requests')
   request=timestamp
  if e['type']=='assistant' and request is not None:
   if isinstance(timestamp,(int,float)):durations.append(timestamp-request)
   else:reasons.append('missing-response-timing')
   request=None
 if request is not None and isinstance(elapsed,(int,float)):durations.append(elapsed-request)
 if any(d<0 for d in durations):reasons.append('non-monotonic-wall-clock')
 if any(d>budget['responseMs']+GRACE_MS for d in durations):reasons.append('response-deadline-exceeded')
 for key in ['modelResponses','toolCalls','verificationCycles']:
  value=a.get(key)
  if not isinstance(value,int) or value<0:reasons.append('missing-budget-counter')
  elif value>budget[key]:reasons.append('counter-budget-exceeded')
 return {'status':'invalid-infrastructure' if reasons else 'valid','reasons':sorted(set(reasons)),'maxClockGapMs':gap if clock and host else None,'maxResponseMs':max(durations,default=None),'cleanupGraceMs':GRACE_MS}
