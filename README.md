# Framework Benchmark Dashboard

One public Netlify dashboard for reviewed synthetic benchmark summaries from Role-Aware Mockserver, Agentic Playwright, Agentic API and JEV. It displays execution status, missing measurements, import integrity checks, source fingerprints, check outcomes and published run history. The site does not execute tests, call models or accept uploads.

## Refresh from all repositories

Run each framework's documented benchmark first. Create an ignored `sources.local.json` mapping exactly `mockserver`, `harness`, `api`, `jev` to their artifact-bearing checkout directories. Read only these explicit paths; do not point at credentials or private trackers.

```sh
npm run import
npm test
npm run build
npm run preview
```

The importer only publishes allowlisted aggregate fields. Raw Playwright/Surefire/JEV reports, token payloads, traces, source paths, prompts, gold labels, reviewer notes and credentials are not copied. It checks report hashes, outcome denominators, source XML provenance, retry counts and the seeded-defect report. Missing/malformed sources become unavailable evidence, not passes. The browser's Validate snapshot button checks structural consistency and recorded import results; it cannot recheck private raw files. Refresh published data fetches the deployed snapshot; it does not fetch files from your Mac.

## Publication

Review `public/data/benchmarks.json` after every import. Commit only reviewed public summaries and source code, then build/deploy `dist` to the existing Netlify site. `netlify.toml` supports Git-based deployment using `npm run build` and `dist`; no secrets are needed for site builds. Local imports require Python 3. The static build requires Node 22 and no third-party runtime dependencies. Do not commit `sources.local.json`, `.netlify/`, raw reports or credentials.

Up to 100 immutable imported records are retained in published history; identical imports deduplicate by public run fingerprint. History reflects published imports, not automatic continuous collection. Never claim AI improvement from ordinary browser runtime. JEV's HTTP 403 run has no model accuracy result. Initial content contains no paired live-agent experiment.

## Live site

https://framework-benchmarks-balaji.netlify.app

The initial site uses manual CLI deployment to the existing Free team. Future reviewed updates can be published with `npx netlify-cli deploy --prod --no-build --dir=dist --site=995be9dd-6fcb-494d-8514-9e4f5c1055a4`. Import, review, test and build first. Git pushes alone do not currently publish this site. CI validates public code and snapshot builds; it does not read local artifacts or call model providers.
