"""Synchronize the reviewed, dependency-free publisher to explicitly enrolled checkouts."""
import json,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'public/data/benchmarks.json').read_text())
words=set()
def visit(x):
 if isinstance(x,str):words.add(x)
 elif isinstance(x,dict):
  for k,v in x.items():words.add(k);visit(v)
 elif isinstance(x,list):
  for v in x:visit(v)
visit(DATA)
words.update(['Expected JUnit source','Exact fixed API suite required','execution','startedAt','finishedAt','exitCode','dirtySource','revision','benchmark attempt start','Evidence belongs to this attempt','All required source files were regenerated during this run','Current attempt did not produce complete fresh evidence. Previous results remain in history.','Evidence matches the fixed benchmark protocol','Case identities and counts checked against the versioned synthetic protocol','passed','failed','skipped','timedOut','interrupted','missing','unavailable','invalid','partial','blocked','completed','preview','live','evaluated','not_run','error','http_400','http_401','http_403','http_404','http_408','http_429','http_500','http_502','http_503','http_504','unknown','[withheld]','Source evidence available','FileNotFoundError','ValueError','KeyError','TypeError','Required source evidence is missing or malformed. Re-import after completing the documented benchmark.','Authored synthetic evaluation; inspect coverage before interpreting findings.','baseline','framework','trials','correct','medianElapsedMs','medianHumanCorrectionMs','medianIncorrectChanges','estimatedCostByCurrency','task','groupId','pairedRepeats','crm-viewer-export','crm-manager-export','crm-manager-direct-route','api-customer-risk'])
(ROOT/'automation/public-vocabulary.json').write_text(json.dumps(sorted(words),indent=2)+'\n')
configs={
 'mockserver':{'steps':[['node','node_modules/@playwright/test/cli.js','test','--config=benchmarks/playwright.config.ts'],['node','benchmarks/summarize.mjs']], 'outputs':['benchmark-results/playwright.json','benchmark-results/summary.json']},
 'harness':{'steps':[['node','node_modules/@playwright/test/cli.js','test','--config=benchmarks/playwright.config.ts'],['node','benchmarks/mutation.mjs']],'outputs':['benchmark-results/oracle.json','benchmark-results/mutant.json','benchmark-results/mutation-summary.json']},
 'api':{'steps':[['python3','benchmarks/dashboard/api-suite.py']],'outputs':['benchmark-results/api-oracle.json']},
 'jev':{'steps':[['node','--import','tsx','src/workflow-cli.ts','benchmark','--input','benchmarks/crm-inputs.json','--gold','benchmarks/crm-gold.json'],['node','--import','tsx','src/benchmark-metrics.ts']],'outputs':['artifacts/workflow-benchmark.json','artifacts/crm-benchmark-metrics.json']}}
for project,config in configs.items():
 root=ROOT.parent/'work/repos'/project;dest=root/'benchmarks/dashboard';dest.mkdir(parents=True,exist_ok=True)
 for name in ['run.py','publish.py','import_benchmarks.py','public-vocabulary.json']+(['api-suite.py'] if project=='api' else []):shutil.copyfile(ROOT/'automation'/name,dest/name)
 config.update(project=project,expectedCases=sorted(set(c['name'] for r in DATA['runs'] if r['project']==project for c in r['cases'])))
 (dest/'config.json').write_text(json.dumps(config,indent=2)+'\n')
 package=root/'package.json';p=json.loads(package.read_text());s=p['scripts'];s['benchmark']='python3 benchmarks/dashboard/run.py';s['benchmark:publish']='python3 benchmarks/dashboard/publish.py'
 if project=='harness':s['benchmark:oracle']='npm run benchmark';s['benchmark:mutation']='npm run benchmark'
 if project=='jev':s['benchmark:crm:live']='npm run benchmark'
 if project in ('harness','api'):s['postbenchmark:collect']='python3 benchmarks/dashboard/publish.py --refresh-trials'
 package.write_text(json.dumps(p,indent=2)+'\n')
 ignore=root/'.gitignore';text=ignore.read_text();addition='\n# Private benchmark execution and publication state\nbenchmark-results/\nbenchmarks/dashboard/__pycache__/\n';ignore.write_text(text+addition) if 'benchmarks/dashboard/__pycache__/' not in text else None
 doc=root/'benchmarks/AUTOMATIC-PUBLICATION.md';doc.write_text('''# Automatic dashboard updates

Run `npm run benchmark`. The complete fixed protocol runs, validates source evidence,
and publishes sanitised aggregates to this repository's `benchmark-results` branch.
The shared [dashboard](https://framework-benchmarks-balaji.netlify.app) refreshes
all four feeds every minute while visible. GitHub CDN caching can add a few minutes.
No dashboard import, source commit or Netlify deployment is needed for data updates.

Requires Python 3.10+, Git with push access, and the project's existing benchmark
runtime/dependencies. Browser projects need `npx playwright install chromium`;
the API needs Java 17+ and Maven. JEV needs its existing provider configuration;
missing credentials, provider errors and incomplete runs are visible as unavailable
or blocked, never model accuracy. Only JEV's explicit manual CI dispatch attempts
live evaluation; ordinary source pushes do not initiate paid model calls.

`BENCHMARK_PUBLISH=0 npm run benchmark` runs privately and prepares the ignored
public aggregate without sending it. Use this for forks, sensitive experiments
and offline work. The configured public destination is Balaji's named repository,
including when the sample project is nested in a larger local workspace.

Publication failures retain evidence locally and return a nonzero exit code.
`npm run benchmark:publish` retries publication without rerunning the benchmark.
The retry uses the original receipt and hashes; it cannot manufacture fresh results.
A run killed before publication cannot update GitHub; CI's always-run publication
step captures an incomplete receipt when possible. Interrupted local runs may leave
`benchmark-results/dashboard-run.lock`; remove it only after confirming its process
has stopped. There is no background daemon watching arbitrary files.

The supported `npm run benchmark` entry point is the automatic path. Harness
`benchmark:oracle` and `benchmark:mutation` now invoke the complete protocol so a
partial rerun cannot mix old and new reports. JEV `benchmark:crm:live` is an alias.
`benchmark:collect` in API/harness also republishes validated trial aggregates after
a previous complete benchmark. Direct Playwright/Maven/evaluator commands, preview,
unit tests and metrics-only commands do not publish. A standalone collector without
a prior benchmark receipt must first run the complete benchmark.

## Evidence and privacy

The runner clears protocol outputs before execution, records start/finish, exit code,
source revision and dirty state, and verifies report hashes, fixed case identities,
denominators, retry counts and freshness. A failed or incomplete attempt replaces
the current status; earlier evidence stays in the last 50 attempts. This is
self-published synthetic evidence, not an independent audit or production claim.
Trial metadata remains self-reported; live-agent and scripted evidence stay separate.

Only the closed public schema and versioned text vocabulary leave the checkout.
Unexpected free text is withheld; unknown keys fail export. Raw reports, traces,
logs, prompts, model outputs, gold labels, local paths, tokens and reviewer notes
remain ignored. New cases require a reviewed protocol/vocabulary update.

GitHub Actions uses its own repository-scoped `GITHUB_TOKEN` with contents:write.
Local publication uses the existing Git credential helper. No shared PAT or Netlify
secret is copied into these repos. Each push is fast-forward only; bounded retries
merge concurrent histories and older-started runs cannot replace a newer attempt.
Repeated publication of the same receipt/data is idempotent. Branch protection or
Actions policy may prevent publication; those failures are not silently ignored.

The common implementation is maintained in `framework-benchmark-dashboard/automation`
and synchronised to these checked-in copies with its `scripts/install-automation.py`.
''')
 readme=root/'benchmarks/README.md';t=readme.read_text();link='\nSee [automatic dashboard publication](AUTOMATIC-PUBLICATION.md) for the canonical runner, CI, privacy controls and retry behaviour.\n';readme.write_text(t+link) if link not in t else None
 workflow=root/'.github/workflows/benchmark.yml';workflow.parent.mkdir(parents=True,exist_ok=True)
 paths={'mockserver':['app/**','mockserver/**','playwright/**'],'harness':['examples/sample-crm-app/**','tests/**'],'api':['projects/microservices/**'],'jev':['src/**']}[project]
 trigger='  workflow_dispatch:\n'
 if project!='jev':trigger+='  push:\n    branches: [main]\n    paths: '+json.dumps(['benchmarks/**','package*.json','.github/workflows/benchmark.yml']+paths)+'\n'
 setup=''
 if project=='api':setup+='      - uses: actions/setup-java@v4\n        with:\n          distribution: temurin\n          java-version: "17"\n          cache: maven\n'
 else:setup+='      - run: npm ci\n'
 if project in ('harness','mockserver'):setup+='      - run: npx playwright install --with-deps chromium\n'
 workflow.write_text('name: Publish benchmark evidence\non:\n'+trigger+'''permissions:
  contents: read
concurrency:
  group: benchmark-publication
  cancel-in-progress: false
jobs:
  benchmark:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
'''+setup+'''      - name: Run complete benchmark
        id: benchmark
        run: npm run benchmark
        env:
          BENCHMARK_PUBLISH: '0'
'''+("          AI_GATEWAY_API_KEY: ${{ secrets.AI_GATEWAY_API_KEY }}\n" if project=='jev' else '')+'''      - name: Publish this attempt even if benchmark failed
        if: always() && steps.benchmark.outcome != 'skipped'
        run: npm run benchmark:publish
        env:
          GH_BENCHMARK_TOKEN: ${{ github.token }}
''')
print('Synchronized automation to four enrolled repos')
