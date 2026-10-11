# Framework Benchmark Dashboard

[Live dashboard](https://framework-benchmarks-balaji.netlify.app) for synthetic
Role-Aware Mockserver, Agentic Playwright, Agentic API and JEV benchmark evidence.

## Automatic results

In any enrolled framework checkout, run **`npm run benchmark`**. Its complete
protocol executes, validates source artifacts and publishes only sanitised
aggregates to that repo's **`benchmark-results` branch**, in `latest.json`.
The deployed dashboard reads all four public feeds directly and refreshes every
minute while visible. GitHub CDN caching can add a few minutes. **No manual import
or Netlify deployment is needed when results change.** Reloading or returning to
the tab also refreshes. A disconnected feed is labelled, with previous evidence
retained rather than presented as a fresh success.

| Project | Source repo | CI benchmark trigger |
| --- | --- | --- |
| Mockserver | `balajiregt/plawright-role-aware-mockserver` | Relevant pushes to main; manual dispatch |
| Playwright | `balajiregt/playwright-harness-framework` | Relevant pushes to main; manual dispatch |
| API | `balajiregt/agentic-workspace` | Relevant pushes to main; manual dispatch |
| JEV | `balajiregt/jev-scope-qa` | Manual dispatch only, because live evaluation calls a provider |

Each framework documents dependencies, aliases and recovery in
`benchmarks/AUTOMATIC-PUBLICATION.md`. Direct ad hoc test commands are not watched.
`benchmark:collect` republishes trial aggregates after a complete API/harness run.
`BENCHMARK_PUBLISH=0 npm run benchmark` disables sending for a private/local run.
`npm run benchmark:publish` retries a failed publication without rerunning tests.
No credentials are shipped to browsers; no Netlify token or shared PAT is needed
in the framework repos. Actions uses its repository-scoped token; local runs use
the existing Git credential helper. CI cannot publish if organization policy or
branch protection disallows it, and reports failure rather than hiding it.

## Integrity and interpretation

The runner clears old protocol outputs before execution, records each attempt,
and checks freshness, source hashes, fixed case identities, denominators and retries.
Failed or incomplete attempts publish failed/unavailable evidence. Last 50 attempts
per repo are retained; duplicate sends do not add a commit. Concurrent publishers
merge with bounded, non-force retries; older-started attempts do not replace newer
ones. Forced termination/network loss can prevent publication; failed local
publication retains a pending aggregate and returns nonzero. No background daemon
uploads later. Download public snapshot exports the currently loaded combined data.

The exporter uses a closed public field/text vocabulary. Unexpected free text is
withheld and unknown keys reject export. Raw reports, traces, prompts, gold labels,
model output, credentials, absolute local paths and reviewer notes stay private.
The public vocabulary names/check IDs are only from the already published synthetic
protocol. New cases require a reviewed protocol/vocabulary update. Execution and
source checks are self-reported; the browser cannot independently inspect raw files.
Ordinary browser runtime does not establish AI productivity. Blocked JEV runs have
no accuracy result. Missing cost and human-effort measurements remain unavailable.

## Development and deployment

```sh
npm test
npm run build
npm run preview
```

Node 22, Python 3.10+ and Git are sufficient for dashboard validation. There are no
browser runtime dependencies. `automation/` contains the common publisher/runner;
`scripts/install-automation.py` synchronises it to four explicitly enrolled local
checkouts at `../work/repos/{mockserver,harness,api,jev}`. Update that explicit mapping
when maintaining from another checkout; do not scan arbitrary private projects.

The original `npm run import` command and ignored `sources.local.json` remain for
reviewed offline seed snapshots. The live feeds take precedence and feed failures
are visibly marked. The seed snapshot is a fallback, not a recent execution claim.

Only **dashboard code changes** need a Netlify build/deployment:

```sh
npx netlify-cli deploy --prod --no-build --dir=dist --site=995be9dd-6fcb-494d-8514-9e4f5c1055a4
```

Build and validate before deploying. Source pushes run validation; hosting source
is currently deployed through the existing authenticated Netlify CLI. Result-branch
updates bypass deployment entirely. `netlify.toml` permits read-only browser fetches
from `raw.githubusercontent.com`. Do not commit `.netlify/` or raw artifacts.

## Live baseline / framework pilot

The dashboard now has a separate **controlled model trial** view with interactive completion, quality, generation-time, token and API-equivalent-cost charts, all trial/check outcomes, hashes and a downloadable architecture diagram. See [the reproducible protocol](trials/README.md). This first pilot measures context-assisted test generation, not the complete autonomous workflow. Human corrections remain unmeasured. Actual spend is unavailable; token-derived API estimates are explicitly labelled.

The two application repositories expose `npm run benchmark:trials`. This runs a complete paired campaign and publishes `benchmark-results/trials.json` plus a campaign archive in each repository. Existing runtime publishers preserve these separate files. The dashboard reads the two campaign feeds alongside the four existing execution feeds, every minute while visible. A failed campaign-feed fetch retains the last loaded campaign and shows an explicit stale warning. The bundled seed is a fallback, never presented as a successful live fetch.

[Diagram (SVG)](public/benchmark-flow.svg) · [Editable Mermaid source](public/benchmark-flow.mmd)
