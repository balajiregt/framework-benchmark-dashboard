"""Publish the impact feed without replacing historical runtime/workflow evidence."""
import argparse,importlib.util,json,pathlib,subprocess,tempfile
from engine import read,write,digest
_spec=importlib.util.spec_from_file_location('impact_export',pathlib.Path(__file__).with_name('export.py'))
_module=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_module)
export=_module.export

def git(root,*args):return subprocess.run(['git',*args],cwd=root,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout.strip()
def publish(payload,remote='https://github.com/balajiregt/agentic-workspace.git'):
 if len(payload['rows'])!=payload['plannedTrials'] or len({r['id'] for r in payload['rows']})!=payload['plannedTrials']:raise ValueError('Account for every planned trial')
 with tempfile.TemporaryDirectory(prefix='impact-publish-') as temp:
  root=pathlib.Path(temp);git(root,'init','--quiet');git(root,'config','user.name','Benchmark publisher');git(root,'config','user.email','benchmark-publisher@users.noreply.github.com');git(root,'remote','add','origin',remote);git(root,'fetch','--quiet','origin','benchmark-results');git(root,'checkout','--quiet','-b','benchmark-results','FETCH_HEAD')
  dest=root/'framework-impact.json';old=read(dest) if dest.exists() else None
  if old==payload:return 'already published'
  if old and old['updatedAt']>payload['updatedAt']:raise ValueError('Refusing feed rollback')
  archive=root/'impact-campaigns'/payload['campaignId']/(digest(json.dumps(payload,sort_keys=True))+'.json')
  if archive.exists() and read(archive)!=payload:raise ValueError('Immutable evidence conflict')
  write(dest,payload);write(archive,payload);git(root,'add','framework-impact.json','impact-campaigns');git(root,'commit','--quiet','-m','Publish framework impact '+payload['campaignId']);git(root,'push','--quiet','origin','HEAD:refs/heads/benchmark-results');return 'published '+payload['campaignId']
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--campaign',type=pathlib.Path);p.add_argument('--payload',type=pathlib.Path);a=p.parse_args()
 if bool(a.campaign)==bool(a.payload):p.error('Choose --campaign or --payload')
 print(publish(read(a.payload) if a.payload else export(a.campaign.resolve())))
