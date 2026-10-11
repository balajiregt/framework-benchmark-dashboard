# Context-assisted QA workflow benchmark

Status: **protocol design and task preparation; no agent trials executed**.
Protocol: `qa-context-workflow-v2-draft1`. Prepared on 11 October 2026.

The question is: **Does the framework's context and guidance help the same agent
complete realistic QA work correctly, with less avoidable effort?**

The [earlier pilot](../trials/README.md) measures one-response test generation
with selected helpers supplied in the prompt. Keep its results and protocol
unchanged. They are not measurements of this workflow. See the
[repository inspection](context-audit.md) for the actual entry points and
[task catalog](tasks.json) for concrete create, update and validate assignments.

## What the comparison changes

| Common to both conditions | Plain repository condition | Context-guided condition |
| --- | --- | --- |
| Same task facts, source snapshot, test inventory, reusable helpers, dependencies, runtime access and allowed edits | Normal source/test/config files plus a short neutral setup document | The same files plus the framework's actual instructions, task context, resolvers, maps, capture workflows and guidance |
| Same model, agent host, model settings, tools and total budget | Agent discovers relevant source and coverage through ordinary repository exploration | Agent follows the documented context entry point, derives paths, checks existing coverage and gathers task-relevant evidence |
| File reads, search, edits, local execution and feedback | Available | Available |
| Independent acceptance criteria and evaluator | Same | Same |

**Do not remove the existing Java or Playwright helper code from the baseline.**
This experiment isolates the added context/guidance layer. The prior helper-versus-
plain-library experiment changed a different variable. A later ablation can
separate instructions, resolvers, graphs and captures; this first comparison
measures their combined workflow, not each component's causal contribution.

The neutral task includes all behavioral requirements, scope and output rules in
both conditions. Framework YAML contains the same task facts, not extra answers.
Do not paste the relevant implementation files or evaluator answers into either
initial prompt. Let the agent find and read them through its assigned environment.

## Isolated trial environment

The future runner must materialize two disposable, manifest-listed projections
from the same pinned repository revision. Original working copies are read-only
inputs, never experimental workspaces. Preserve unrelated local edits.

Common files include application source, existing tests, fixtures, page objects,
assertions, dependencies, config and ordinary execution scripts. A neutral setup
document supplies identical application-start, typecheck and test commands. The
plain projection omits the custom agent bootstrap, workflow skills, context maps,
curated captures, graph/capture generators and context-oriented README/docs.
The context-guided projection includes those actual framework assets. Existing
helper and application bytes must be identical across conditions.

Both projections exclude previous benchmark tests/results/prompts, task catalog
acceptance criteria, evaluator code, gold labels, historical agent solutions,
loop run logs and generated reports. `benchmarks/`, old `trials/`, benchmark
scripts in package metadata and Git history must not leak solved tasks. The
evaluation material lives outside the agent's readable filesystem. This needs
an enforced filesystem/tool boundary; a prompt telling an unrestricted shell
not to read another folder is insufficient. Copied dependency trees must not
introduce symlinks back to evaluator or private workspace directories.

Global/parent AGENTS, Pi skills, extensions, prompt templates and old sessions
must not silently change one condition. Record the shared generic agent system
prompt separately from intentional framework bootstrap. In the framework API
condition reproduce the existing AGENTS + selected skill mechanism and update
the small task YAML. Resolve context within that trial's workspace. In the
Playwright condition follow its AGENTS/context/CLI-evidence path. Use the same
agent host for a paired comparison; never compare raw HTTP completion on one
side against a tool-enabled Pi agent on the other.

Framework validation tasks may write derived context/graph/report artifacts.
They must not change product, test or helper source. Track those artifact writes
separately from source edits. A scenario analysis with a correct no-change
decision is a successful outcome, not an incomplete coding task.

## Task set and sequence

Eight source-grounded tasks are in `tasks.json`: one create, one update and two
validation decisions per application. No product change is needed to manufacture
these tasks; the inspected samples already contain useful gaps and existing
coverage. Each starts from the original snapshot, never another task's solution.

1. Prepare and inspect task/evidence manifests with the offline command below.
2. Implement and verify the isolated runner, tool telemetry and independent
   evaluators. These are **not implemented by the preparation command**.
3. Perform a separate runtime preflight: actual read/edit/execute tool round trip
   in a throwaway directory, clean app startup, existing test health, correct
   context and usable reports. No counted task or answer is used in preflight.
4. Start with one paired local API run for each core operation (create, update,
   validate): six workflow runs. This is an engineering pilot, not a final
   comparison. Preserve failures and do not tune on a run then relabel it held-out.
5. After the runner is stable, freeze a campaign for all eight tasks, three
   paired repeats each (48 runs per model). Alternate arm order and rotate task
   order deterministically. Run sequentially on the local machine. Report each
   task and operation; three repeats of a task are not three independent tasks.

Local Gemma is the first model cohort. A cloud cohort uses the same tasks and
rules but remains separate because model, tokenizer and provider differ. Do not
interpret a local/cloud difference as the effect of the context framework.

## Proposed fixed work budget

Freeze these limits before collecting the first counted workflow run:

- 15 minutes total task wall time, including context discovery and execution.
- At most 36 model responses and 80 tool invocations, whichever stops first.
- At most three verification cycles: initial submission plus two repairs.
  A cycle evaluates one source snapshot using the task's prescribed focused
  gates; changing source after feedback consumes a repair. Multiple commands on
  the same unchanged snapshot belong to that cycle. Extra ad hoc test execution
  must not evade the limit through shell commands or nested processes.
- For Gemma, initially retain the existing long profile: 8192 context, maximum
  4096 output tokens per response, one slot. Use the same temperature and repeat
  seed in both arms if the agent adapter exposes them; otherwise record the
  effective settings as unsupported/unknown, not silently equal.
- A 180-second per-model-response deadline stays within the total deadline.
  No automatic replacement of timeout, truncation or tool-call failures.
- Validation-only tasks get the same overall budget but no source repair work.

These are planned controls, not evidence of an implemented enforcement mechanism.
The adapter must demonstrate that every model/tool call and verification cycle
can be observed and limited before the campaign starts. If the framework's real
bootstrap cannot fit the context window, report that condition rather than
silently summarizing it with a stronger model. Any revised budget creates a new
protocol/campaign for both arms. Log compaction, truncation and hidden retries.

## What counts as useful work

| Operation | Primary outcome | Independent checks |
| --- | --- | --- |
| Create | Adds the requested missing behaviour coverage in the right project | New scenario actually runs; required assertions detect targeted faults; existing coverage retained; no duplicate or unrelated edits |
| Update | Changes the owning test/helper to satisfy the request | Missing assertion added; old assertions preserved; intended healthy behaviour passes; targeted fault detected; no unnecessary new test |
| Validate | Correctly distinguishes a gap, unsupported expectation or existing coverage | Conclusion supported by actual source/contract/test/helper evidence; required nuance present; no unauthorized source edit |

All requirements are conjunctive for binary task success. Show individual criteria
and operational status rather than hiding tradeoffs in an arbitrary overall score.
Equivalent valid solutions must be accepted: do not require a particular helper
name or textual patch just because it is in a reference solution. Enforce the
user's scope and repository ownership, not arbitrary line-count minimality.

The agent sees compiler errors, focused healthy-test results and its own tool
outputs. It does not see final fault injections, expected classifications or
evaluator feedback. Freeze the last submission at completion/budget exhaustion;
evaluate it separately. A final healthy pass alone is insufficient. Mutation
checks are a downstream quality gate for relevant create/update tasks, not the
definition of context quality. Validation decisions require independently reviewed
evidence; until reviewed, mark them `pending-review`, not automatically correct.
JEV may supply advisory findings but must not be the sole grader of itself or the
agent. No human approval or assessment is fabricated.

## Measurements and denominators

Primary: correct tasks / all started tasks, split by operation and model. Retain
timeouts, tool failures and exhausted budgets. Separately show scheduled tasks
that could not start, with the preflight/infrastructure reason. Per-criterion
outcomes can be satisfied, unsatisfied, not evaluated or pending review. A missing
result is never silently dropped or counted as a pass.

Secondary measurements:

- Time to first relevant evidence read, first source edit, first executable
  verification and final submission; overall wall time and per-cycle history.
  A relevant read is a trace-backed file/range observation, not proof the model
  understood it. If timestamps/content are unavailable, keep the metric null.
- Files/ranges actually read, bytes returned, repeated reads, searches, invalid
  paths, framework entry points used, context conflicts noticed and resolved.
  Use the task's evidence list as a minimum reference, not an exhaustive whitelist
  of useful reads. Extra reads are descriptive, not automatically wasted work.
- Provider input/output/cache tokens per response and campaign, compaction and
  tool-output truncation. File bytes and the existing chars/4 context estimate
  are not real provider token counts and must never be presented as cost savings.
- Source diff, ownership/scope violations, new/updated scenario identities,
  preserved coverage and duplicate decisions. Human review needed for semantic
  judgements is explicitly recorded; no regex or self-report substitutes for it.
- Repairs attempted and successful recovery by attempt number. These are agent
  corrections, not human correction time. Human time remains unmeasured unless
  someone actually performs a timed review.
- Measured provider charge only when available; separately labeled rate-derived
  estimates when defensible. Local external API fee may be zero; electricity,
  hardware and total operating cost remain unknown unless instrumented.

Never claim faster completion by comparing only successful runs while dropping
timeouts. Show success within the fixed budget first, attempt duration separately,
and successful-task latency with its explicit denominator. Keep preparation/setup
time separate from task time. Initial context regeneration/capture needed during
the assigned task counts toward task time. Record any pre-existing capture cache
and its evidence timestamp/hash; warm and cold context are separate conditions.

## Mockserver and JEV roles

The standalone Mockserver controls deterministic identity/backend conditions; it
does not itself assemble agent prompts. For API-workspace UI routing experiments,
its real context path is `ui-context.yml` -> `resolved-ui-context.yml` -> the UI
skill. Keep Mockserver runtime behaviour constant in both agent arms. Its separate
runtime/environment comparison remains valid and separately reported.

JEV v2 consumes explicit requirement sources, scenario inventories, actual code
and helper evidence with completeness flags. It is a review stage, not a test
generator or repair agent. Keep its existing planning/duplication/implementation
evaluation separate. A later integration can ask whether adding JEV review helps
the same agent; that is a new intervention and must include review latency/cost.
Do not add JEV only to one arm of this context comparison.

## Dashboard contract

Add a future **QA workflow outcomes** view, distinct from existing model generation
and runtime views. Planned charts: task success by create/update/validate;
completion within budget; repair recovery by cycle; context discovery/read cost;
scope/duplicate decisions; time/tokens with observed denominators. Drill-down:
task -> condition -> evidence read -> action -> verification -> final outcome.

Use a new `workflow-results.json` feed and `qa-context-workflow-v2` schema. Do not
shoehorn workflow evidence into `trials.json` or overwrite original Gemma results.
Public exports should contain reviewed task identifiers, structured outcomes,
counts, costs and hashes only. Raw code, paths, prompts, tool traces, labels and
human reviews remain private. The future reader can use the existing automatic
feed pattern, but this design does not claim that feed or dashboard view exists.

## Offline preparation

```sh
python3 workflows/prepare.py --sources sources.local.json --output ../work/workflow-plan
```

This validates catalog/evidence references and fingerprints the explicit files.
It requires the clean inspected revisions recorded in the catalog; changed source
requires a new task/expectation review rather than silently reusing old answers.
It writes task-only agent prompts separately from evaluator criteria and a source
manifest. It never calls a model, starts a server, edits a source repo or publishes
results. Prepared prompts and criteria are siblings for organizer convenience;
**this output is not a sandbox or an agent working directory**. The runner must
enforce the projection/evaluator separation described above before execution.

The current fixtures are authored from known sample applications, not a blinded
holdout. After this pilot, add independently specified tasks and new application
revisions before making general productivity claims.
