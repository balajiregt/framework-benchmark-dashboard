# Inspection of the real context mechanisms

11 October 2026. Read source and instructions in the original API/Playwright
workspaces and the explicitly enrolled publication checkouts. The latter are
clean pinned inputs for the proposed fixtures; original checkouts have local
changes and must not be reset. Findings below describe code inspection, not a
new live runtime validation.

| Project | Inspected publication revision |
| --- | --- |
| Agentic API workspace | `05307710c9568182507faedbceec5f2ce1c22c9f` |
| Playwright harness | `2ac1d1a13ddd3aab9282edbb91349c78d690cb35` |
| Role-Aware Mockserver | `9727b865bf8cb6d87cf7fb344c21cce95b0c5f13` |
| JEV review | `2ab090805177fc36544a5fca5d8a4489a2690e50` |

## Agentic API: route from a small ticket to exact evidence

Observed path:

`AGENTS.md` -> `contexts/current/service-context.yml` ->
`scripts/resolve_context.py` -> `resolved-context.yml` ->
`skills/microservice-change/SKILL.md` -> relevant source/contract/existing tests ->
small edit or evidence-backed gap report -> configured verification.

The resolver derives service/QA/deployment ownership and exact test, controller,
service, contract, fixture and assertion paths. It derives validation hints from
the OpenAPI schema and source signals. The skill checks existing coverage before
creation, preserves split-QA ownership and distinguishes a missing assertion from
a new scenario. For unsupported rejection expectations it requires a gap report,
not a changed assertion that merely makes a test green.

Source: [AGENTS](https://github.com/balajiregt/agentic-workspace/blob/05307710c9568182507faedbceec5f2ce1c22c9f/AGENTS.md),
[resolver](https://github.com/balajiregt/agentic-workspace/blob/05307710c9568182507faedbceec5f2ce1c22c9f/scripts/resolve_context.py),
[workflow skill](https://github.com/balajiregt/agentic-workspace/blob/05307710c9568182507faedbceec5f2ce1c22c9f/skills/microservice-change/SKILL.md).

The local launcher appends root AGENTS to the system prompt, registers the
selected API/UI skill and prompt templates, and starts Pi with read/bash/edit/
write/grep/find/ls. It also writes user-level Pi model configuration, can start a
model server and performs a tool-call doctor check. Do not invoke this wrapper
blindly from a benchmark: isolate configuration and instrument the actual Pi
tool loop. The previous raw chat-completion requests exercised none of this.

The existing context-efficiency report estimates token volume for selected files
versus a repository dump. Its own code says this is an approximate yardstick.
It is not observed agent retrieval, actual provider usage or a fair normal-agent
baseline. The new benchmark must collect actual reads and provider usage.

## Playwright: discover, capture, plan, edit and verify

Observed path:

`AGENTS.md` -> task + app/command/strategy context -> source manifest -> coverage
and duplicate hints -> existing tests/helpers/captures -> narrow capture workflow
when needed -> flow spec for a new workflow, or direct owning-layer update ->
focused Playwright run -> inspect evidence -> repair or report a gap.

`contexts/agent-loop.yml` describes mode routing, source analysis, coverage,
capture, planning, generation, healing and review. These are workflow instructions,
not proof that an autonomous state machine has executed. The runner must record
what the agent actually does. MCP is optional; CLI evidence is a documented path.

Source: [AGENTS](https://github.com/balajiregt/playwright-harness-framework/blob/2ac1d1a13ddd3aab9282edbb91349c78d690cb35/AGENTS.md),
[loop](https://github.com/balajiregt/playwright-harness-framework/blob/2ac1d1a13ddd3aab9282edbb91349c78d690cb35/contexts/agent-loop.yml),
[capture runner](https://github.com/balajiregt/playwright-harness-framework/blob/2ac1d1a13ddd3aab9282edbb91349c78d690cb35/scripts/run-capture-recipe.mjs).

Readiness observations:

- The capture runner currently supports localStorage-based auth only. The CRM's
  API now establishes an HttpOnly session through real login. A captured role
  page is not proof of an authenticated API session. Export API tasks must sign
  in through the real UI or the documented session API, and verify the session.
- Manifest/graph coverage uses source and textual heuristics. It proposes
  relevant work; it cannot certify that assertions prove a requirement.
- Curated capture freshness is not established by file existence. Bind each
  use to source/runtime evidence; flag stale/missing captures and record refresh.
- Playwright config can retry in CI and sample tests can skip without a base URL.
  The evaluator must set a real local URL, enforce no test retries, check nonempty
  executed test identities and distinguish agent repair from test-runner retry.
- **Correction, 12 October 2026:** the earlier inspection incorrectly described
  the manager flow as lacking direct-route checks. Its body already calls
  `gotoLeads` and `gotoAdminUsers`, followed by `expectPermissionDeniedForPath`.
  The new campaign verifies these helper bodies and expects an already-covered
  decision. The inaccurate earlier task is not reused as a missing-work example.

## Role-Aware Mockserver: deterministic environment, not prompt retrieval

The standalone repo supplies role/header helpers, token generation, role-specific
backend responses, page objects and assertions. `mockAgentRoles` continues token
requests with an `agent-roles` header; backend behaviour is owned by mockserver
routes. This provides controlled test conditions. The API workspace adds the
context-routing wrapper via `ui-context.yml`, the UI resolver and the UI skill.
These are distinct responsibilities; do not claim the standalone mockserver is
an agent context engine. Its existing environment benchmark remains separate.

Source: [helper](https://github.com/balajiregt/plawright-role-aware-mockserver/blob/9727b865bf8cb6d87cf7fb344c21cce95b0c5f13/playwright/helpers/api-mock.ts),
[UI skill](https://github.com/balajiregt/agentic-workspace/blob/05307710c9568182507faedbceec5f2ce1c22c9f/skills/playwright-ui-change/SKILL.md).

## JEV: bounded review packets and uncertainty

V2's `src/workflow.ts` constructs planning, duplication and implementation
questions from explicitly supplied sources, scenario inventory, code and helper
evidence. Completeness/conflict signals matter. Gold labels and reviewer decisions
are excluded from model packets. The handoff is documented, but there is no
automatic repository extraction, Jira connector or Playwright result import in
this v2 workflow. Do not describe that handoff as already automated.

JEV cannot create/repair tests or approve them for a lead. Evaluate its findings
against independent reviewed expectations, separately from coding-agent task
success. Existing live-provider failures must stay operational failures; no
new review accuracy is inferred from this inspection.

Source: [workflow](https://github.com/balajiregt/jev-scope-qa/blob/2ab090805177fc36544a5fca5d8a4489a2690e50/src/workflow.ts),
[handoff](https://github.com/balajiregt/jev-scope-qa/blob/2ab090805177fc36544a5fca5d8a4489a2690e50/docs/agent-handoff.md).

## Consequence for the redesign

Keep test quality as one downstream gate. Measure context discovery, correct
ownership, duplicate avoidance, supported gap decisions and actual execution
feedback as well. Both arms retain the same helpers and tools. Framework assets
must be consumed through their real entry points rather than a researcher-selected
source bundle. The full workflow runner and independent task evaluators are the
next implementation work, not completed capabilities of this design package.

The executed follow-up audit and paired campaign are documented in
[Framework impact](../impact/README.md). This historical design document is not
the current runner specification.
