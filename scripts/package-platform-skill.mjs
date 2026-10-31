import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {CONTRACT_VERSION} from '../.agents/skills/platform-publish/scripts/contract.mjs';
const root=path.resolve(import.meta.dirname,'../.agents/skills/platform-publish');
const files={};
for (const file of fs.readdirSync(root,{recursive:true}).sort()) {
  const target=path.join(root,file), stat=fs.lstatSync(target);
  if (stat.isSymbolicLink()) throw Error('Skill bundle must not contain symlinks');
  if (!stat.isFile()||file==='bundle-manifest.json') continue;
  files[file]=createHash('sha256').update(fs.readFileSync(target)).digest('hex');
}
const manifest=JSON.stringify({name:'platform-publish',version:CONTRACT_VERSION,files},null,2)+'\n';
const location=path.join(root,'bundle-manifest.json');
if (process.argv.includes('--check')) {
  if (!fs.existsSync(location)||fs.readFileSync(location,'utf8')!==manifest) throw Error('Skill bundle changed; regenerate and review its manifest');
} else fs.writeFileSync(location,manifest);
console.log('Platform publishing bundle '+CONTRACT_VERSION+': '+Object.keys(files).length+' content-bound files');
