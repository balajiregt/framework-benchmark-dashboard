// The portable skill owns the contract; ship the exact same validator to browsers.
import fs from 'node:fs';
const root=new URL('../',import.meta.url);
const source=fs.readFileSync(new URL('.agents/skills/platform-publish/scripts/contract.mjs',root));
const destination=new URL('public/platform-contract.mjs',root);
if (process.argv.includes('--check')) {
  if (!fs.existsSync(destination)||!source.equals(fs.readFileSync(destination))) throw Error('Run npm run platform:sync before testing or packaging');
} else fs.writeFileSync(destination,source);
