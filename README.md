# Framework Benchmark Dashboard

[Live dashboard](https://framework-benchmarks-balaji.netlify.app) for synthetic
Role-Aware Mockserver, Agentic Playwright, Agentic API and JEV benchmark evidence.

## Framework impact: context, decisions and delivered work

[Open the framework-impact view](https://framework-benchmarks-balaji.netlify.app/#framework-impact).
The new campaign first checks whether API and Playwright context agrees with
source and live authentication, then runs the same create/update/validate requests
with and without each framework. It reports ownership, action and evidence
judgments separately from completed work, elapsed time, provider usage and cost.

See [the protocol and reproduction commands](impact/README.md) and
[actual results](impact/RESULTS.md): two timing-valid attempts and ten host
interruptions; no valid Playwright comparison yet. One pair per task
is a descriptive pilot. Reading context, making edits or passing an unchanged
suite does not establish successful delivery. Human correction time and total
local operating cost remain unmeasured. Historical evidence below is retained.

## Context-assisted QA workflows

The new [workflow comparison](https://framework-benchmarks-balaji.netlify.app/#workflow-trials)
measures real repository work: creating tests, updating existing tests and assessing
whether a proposed scenario is supported. Both conditions keep the same helpers;
one adds the framework's actual context and guidance. A local Gemma agent can
inspect, edit, verify and repair within fixed limits. Independent grading checks
the resulting work; semantic conclusions remain pending until reviewed.

The first API pilot uses three paired tasks, one repeat each. Timing watchdogs and a separate validity audit exclude host interruptions from model performance while retaining every started attempt. It is distinct from
the earlier one-response generation campaigns and from runtime-only benchmarks.
The 12 October pilot completed 0/3 full tasks in each condition; context-guided
validation reached the correct central decision but missed a required behavior explanation.
See [results, setup, budgets and grading](workflows/README.md), the
[context audit](workflows/context-audit.md) and [flow diagram](public/workflow-flow.svg).

`npm run workflow:run -- --repo <pinned-api-repo> --output <prepared-campaign>`
executes a frozen campaign and publishes its closed summary to `workflow-results.json`
automatically. The deployed dashboard reads that feed every minute; new workflow
results need no manual import or dashboard redeploy. This local-model workflow
is not silently invoked by a framework's ordinary `npm run benchmark` or by cloud CI.

## Automatic runtime results

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

The [implemented workflow protocol](workflows/README.md) measures repository
work with context guidance. Its six-run API pilot is shown separately from the
historical generation results below. The eight-task catalog defines expansion
work, not additional completed trials.

The dashboard now has a separate **controlled model trial** view with interactive completion, quality, generation-time, token and API-equivalent-cost charts, all trial/check outcomes, hashes and a downloadable architecture diagram. See [the reproducible protocol](trials/README.md). This first pilot measures context-assisted test generation, not the complete autonomous workflow. Human corrections remain unmeasured. Actual spend is unavailable; token-derived API estimates are explicitly labelled.

The two application repositories expose `npm run benchmark:trials`. This runs a complete paired campaign and publishes `benchmark-results/trials.json` plus a campaign archive in each repository. Existing runtime publishers preserve these separate files. The dashboard reads the two campaign feeds alongside the four existing execution feeds, every minute while visible. A failed campaign-feed fetch retains the last loaded campaign and shows an explicit stale warning. The bundled seed is a fallback, never presented as a successful live fetch.

[Diagram (SVG)](public/benchmark-flow.svg) · [Editable Mermaid source](public/benchmark-flow.mmd)
