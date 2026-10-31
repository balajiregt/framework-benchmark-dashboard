import data from './data/platform-registry.json' with {type:'json'};
import {validateRegistry,sourceURL} from './platform-contract.mjs';
export const registry=validateRegistry(data);
export const runtimeEntries=registry.projects.flatMap(project=>project.sources.filter(s=>s.format==='legacy-runtime-v1').map(source=>({project,source})));
export const runtimeProjectIds=runtimeEntries.map(({source})=>source.legacyProject);
export function registeredSource(entryId, sourceId) {
  const entry=[...registry.projects,...registry.analyses].find(p=>p.id===entryId);
  const source=entry?.sources.find(s=>s.id===sourceId);
  if (!source) throw Error('Unregistered result source');
  return {entry,source,url:sourceURL(entry,source)};
}
