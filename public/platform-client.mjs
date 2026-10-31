import {validateMetricsFeed,sourceURL} from './platform-contract.mjs';
// The caller supplies an entry already accepted by validateRegistry.
// Keep previous accepted evidence explicitly labelled when a refresh fails.
export async function readStandardMetrics(entry,{fetcher=fetch,previous=null}={}) {
  const source=entry.sources.find(s=>s.format==='metrics-v1');
  if (!source) return {state:'not-configured',feed:null};
  const url=sourceURL(entry,source);
  if (previous) validateMetricsFeed(previous,entry.id,source.repository);
  try {
    const response=await fetcher(url,{cache:'no-store',redirect:'error',signal:AbortSignal.timeout(12000)});
    if (!response.ok) throw Error('Feed unavailable');
    const body=await response.text(); if (body.length>500000) throw Error('Oversized feed');
    const feed=validateMetricsFeed(JSON.parse(body),entry.id,source.repository);
    if (previous?.runs.length && (!feed.runs.length || Date.parse(feed.runs[0].observedAt)<Date.parse(previous.runs[0].observedAt))) throw Error('Feed moved backwards');
    return {state:'connected',feed};
  } catch { return {state:previous?'stale':'unavailable',feed:previous}; }
}
