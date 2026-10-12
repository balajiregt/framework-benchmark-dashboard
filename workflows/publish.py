"""Publish workflow summaries atomically, preserving all previous feed types."""
import argparse, json, pathlib, subprocess, tempfile
from export import export
from runtime import write

def git(args,cwd):return subprocess.run(['git',*args],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout.strip()
def publish(campaign,remote='https://github.com/balajiregt/agentic-workspace.git'):
 if len(campaign['rows'])!=6:raise ValueError('Account for all six planned workflow trials')
 with tempfile.TemporaryDirectory(prefix='workflow-publication-') as temp:
  root=pathlib.Path(temp);git(['init','--quiet'],root);git(['config','user.name','Benchmark publisher'],root);git(['config','user.email','benchmark-publisher@users.noreply.github.com'],root);git(['remote','add','origin',remote],root)
  git(['fetch','--quiet','origin','benchmark-results'],root);git(['checkout','--quiet','-b','benchmark-results','FETCH_HEAD'],root)
  dest=root/'workflow-results.json';old=json.loads(dest.read_text()) if dest.exists() else None
  if old==campaign:return 'already published'
  if old and old['updatedAt']>campaign['updatedAt']:raise ValueError('Refusing to overwrite newer evidence')
  archive=root/'workflow-campaigns'/(campaign['campaignId']+'.json')
  if archive.exists() and json.loads(archive.read_text())!=campaign:raise ValueError('Immutable campaign archive conflict')
  write(dest,campaign);write(archive,campaign);git(['add','workflow-results.json','workflow-campaigns'],root)
  git(['commit','--quiet','-m','Publish QA workflow pilot '+campaign['campaignId']],root)
  # A conflict fails visibly; do not force-push or blindly retry ambiguous delivery.
  git(['push','--quiet','origin','HEAD:refs/heads/benchmark-results'],root);return 'published '+campaign['campaignId']

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--campaign',type=pathlib.Path,required=True);a=p.parse_args();print(publish(export(a.campaign.resolve())))
