"""Publish validated campaign JSON to its project's results branch without changing runtime results."""
import argparse,json,pathlib,subprocess,tempfile,sys
from export import export
from run import write
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'automation'))
from publish import git  # loaded via script name? imported module is separate from __main__
REPOS={'harness':'playwright-harness-framework','api':'agentic-workspace'}
def publish_campaign(campaign,remote):
 with tempfile.TemporaryDirectory(prefix='trial-publication-') as folder:
  git(['init','--quiet',folder],folder);git(['config','user.name','Benchmark publisher'],folder);git(['config','user.email','benchmark-publisher@users.noreply.github.com'],folder);git(['remote','add','origin',remote],folder)
  for _ in range(3):
   git(['fetch','--quiet','origin','benchmark-results'],folder);git(['checkout','--quiet','-B','benchmark-results','FETCH_HEAD'],folder)
   filename='local-trials.json' if campaign.get('runtime')=='llama.cpp' else 'trials.json'
   dest=pathlib.Path(folder)/filename;old=json.loads(dest.read_text()) if dest.exists() else None
   if old==campaign:return 'already published'
   if old and old['updatedAt']>campaign['updatedAt']:raise ValueError('Refusing to replace a newer campaign')
   write(dest,campaign);archive=pathlib.Path(folder)/'campaigns'/(campaign['campaignId']+'.json');write(archive,campaign)
   git(['add',filename,'campaigns'],folder);git(['commit','--quiet','-m','Publish controlled '+campaign['project']+' trials '+campaign['campaignId']],folder)
   if git(['push','--quiet','origin','HEAD:refs/heads/benchmark-results'],folder,allowed=(0,1,128)).returncode==0:return 'published'
  raise RuntimeError('Publication conflict; retry explicitly')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--project',choices=REPOS,required=True);a=p.parse_args();c=export(a.output.resolve(),a.project)
 if len(c['rows'])!=6 or any(r['operationalStatus']=='awaiting-evaluation' for r in c['rows']):raise ValueError('Account for all six planned trials before publishing this protocol')
 print(publish_campaign(c,'https://github.com/balajiregt/'+REPOS[a.project]+'.git'))
