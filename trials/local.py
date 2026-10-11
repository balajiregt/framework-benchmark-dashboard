"""Run the same API generation task on an existing loopback llama.cpp server; no server changes."""
import argparse,json,pathlib,shutil,time,urllib.request,urllib.error,subprocess
from run import read,write,sha,now
BASE='http://127.0.0.1:8080'
def get(path):return json.load(urllib.request.urlopen(BASE+path,timeout=10))
def prepare(a):
 out=a.output.resolve();source=a.cloud.resolve()
 if (out/'plan.json').exists():raise ValueError('Local campaign already exists')
 plan=read(source/'plan.json');props=get('/props');models=get('/v1/models');modelpath=pathlib.Path(props['model_path'])
 if 'gemma-4-E2B-it-qat-UD-Q4_K_XL.gguf'!=modelpath.name:raise ValueError('Running model does not match workspace profile')
 if props['default_generation_settings']['n_ctx']!=8192 or props['total_slots']!=1:raise ValueError('Expected existing 8192-context, one-slot profile')
 modelhash=__import__('hashlib').sha256()
 with modelpath.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):modelhash.update(block)
 trials=[t for t in plan['trials'] if t['project']=='api']
 out.mkdir(parents=True)
 for t in trials:
  (out/t['id']).mkdir();shutil.copyfile(source/t['id']/'prompt.txt',out/t['id']/'prompt.txt')
 for file in ['api-source-hashes.json','harness-source-hashes.json','schema.json']:shutil.copyfile(source/file,out/file)
 plan.update(createdAt=now(),trials=trials,model='Gemma 4 E2B IT QAT UD-Q4_K_XL',reasoning='server default; content-only',cliVersion=subprocess.check_output(['llama-server','--version'],stderr=subprocess.STDOUT,text=True).splitlines()[0],runtime='llama.cpp',sourceCampaignSha256=sha((source/'plan.json').read_bytes()),local=dict(modelFileSha256=modelhash.hexdigest(),modelSnapshot=modelpath.parent.name,contextWindow=8192,maxOutputTokens=4096,temperature=.2,seeds=[1,2,3],parallelSlots=1,cachePrompt=False,hardware=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),memoryBytes=int(subprocess.check_output(['sysctl','-n','hw.memsize'],text=True)),serverDefaultsSha256=sha(json.dumps(props['default_generation_settings'],sort_keys=True))))
 write(out/'plan.json',plan);write(out/'server-evidence.json',{'props':props,'models':models});print('Prepared six local API trials; model SHA256',modelhash.hexdigest(),flush=True)
def generate(a):
 out=a.output.resolve();plan=read(out/'plan.json')
 for t in plan['trials']:
  folder=out/t['id']
  if (folder/'generation.json').exists():continue
  prompt=(folder/'prompt.txt').read_text()
  if sha(prompt)!=t['promptSha256']:raise ValueError('Prompt changed')
  request=dict(model='local-model',messages=[{'role':'user','content':prompt}],temperature=.2,seed=t['repeat'],max_tokens=4096,cache_prompt=False,stream=False,response_format={'type':'json_schema','schema':read(out/'schema.json')})
  write(folder/'request.json',request);start=now();clock=time.monotonic();status=0;raw=None;response=None
  try:
   with urllib.request.urlopen(urllib.request.Request(BASE+'/v1/chat/completions',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'}),timeout=180) as r:raw=json.load(r)
   write(folder/'provider-response.json',raw)
   choice=raw['choices'][0];content=choice['message']['content'];response=json.loads(content)
   if choice.get('finish_reason')!='stop' or not isinstance(response.get('code'),str):status=1
   if response is not None:write(folder/'response.json',response)
  except Exception as error:
   status=1;write(folder/'provider-error.json',{'type':type(error).__name__,'message':str(error)})
  u=raw.get('usage') if raw else None;usage={'input_tokens':u['prompt_tokens'],'output_tokens':u['completion_tokens'],'cached_input_tokens':u.get('prompt_tokens_details',{}).get('cached_tokens',0),'cache_write_input_tokens':0} if u else None
  # Normalize into the shared evidence envelope without claiming a Codex CLI event.
  event={'type':'turn.completed' if status==0 else 'turn.failed','usage':usage,'source':'llama.cpp HTTP response','responseSha256':sha((folder/'provider-response.json').read_bytes()) if raw else None}
  (folder/'events.jsonl').write_text(json.dumps(event)+'\n')
  g=dict(startedAt=start,finishedAt=now(),elapsedMs=round((time.monotonic()-clock)*1000),exitCode=status,usage=usage,toolEvents=len(raw['choices'][0]['message'].get('tool_calls',[])) if raw else 0,responseSha256=sha((folder/'response.json').read_bytes()) if (folder/'response.json').exists() else None,eventsSha256=sha((folder/'events.jsonl').read_bytes()),humanCorrectionMs=None,actualCost=None,estimatedCost=None,provider='llama.cpp',providerResponseSha256=event['responseSha256'],timings=raw.get('timings') if raw else None,finishReason=raw['choices'][0].get('finish_reason') if raw else None)
  write(folder/'generation.json',g);print(t['id'],json.dumps({k:g[k] for k in ['elapsedMs','exitCode','usage','finishReason','timings']}),flush=True)
  if status:
   if a.continue_timeouts and (folder/'provider-error.json').exists() and read(folder/'provider-error.json')['type']=='TimeoutError':
    slots=get('/slots')
    if any(slot.get('is_processing') for slot in slots):raise SystemExit('Timed-out local request is still running; wait before continuing distinct trials.')
    print('Timeout retained; continuing to the next distinct planned trial, without retry.',flush=True)
   else:raise SystemExit('Local generation failed; evidence retained. Inspect before resuming.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','generate']);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--cloud',type=pathlib.Path);p.add_argument('--continue-timeouts',action='store_true');a=p.parse_args();globals()[a.command](a)
