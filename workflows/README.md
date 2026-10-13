# Context-assisted QA workflow benchmark

**Historical API pilot.** New API/Playwright paired campaigns use
[framework-impact-v1](../impact/README.md). The unexecuted manager create/validate
entries in this older catalog were based on an incorrect missing-coverage
assumption and are retired; do not use them to grade agent performance.


Status: **runner, enforced budgets, grading and live dashboard implemented**.
API pilot protocol: `qa-context-workflow-v2-api-pilot-4`; public schema: `qa-context-workflow-v2`.
Implemented on 11–12 October 2026. The older catalog is retained for history, with incorrect UI entries retired;
this first campaign runs six API workflows (three tasks × two conditions).

The question is: **Does the framework's context and guidance help the same agent
complete realistic QA work correctly, with less avoidable effort?**

The [earlier pilot](../trials/README.md) measures one-response test generation
with selected helpers supplied in the prompt. Keep its results and protocol
unchanged. They are not measurements of this workflow. See the
[repository inspection](context-audit.md) for the actual entry points and
[task catalog](tasks.json) for concrete create, update and validate assignments.

## Results · 12 October 2026

Campaign `d3928716d37016d0`: six timing-valid attempts, one pair per task.
Both conditions completed **0/3 full tasks**. All attempts remain visible; none
was replaced inside this campaign. Human correction time and operating cost are
unmeasured. Local inference API fee was $0.

| Task | Baseline | Context-guided |
| --- | --- | --- |
| Create normalization coverage | 773.5 s; no edit; ran the original five tests; 6/13 gates | 357.7 s; truncated response after unsuccessful edit attempts; 6/13 gates |
| Strengthen high-risk assertions | 559.3 s; wrong-scope unit-test edits blocked; 7/10 gates | 375.1 s; failed to locate the owning API test; 7/10 gates |
| Validate proposed format rejection | 236.4 s; incorrectly treated format rejection as supported intent; 2/5 gates | 189.9 s; correctly rejected the unsupported expectation, but omitted the actual low-risk response; 4/5 gates |

Gate counts include preserved starting coverage and scope checks; they are not a
score for newly written tests or defect recall. No trial applied a source edit.
Only the baseline create attempt ran agent-requested verification; it passed the
unchanged original suite. No failed-to-passed compilation repair was demonstrated.

The context-guided validation used the real resolver and read its derived context.
The other two context attempts did not invoke it; one read the skill late. In total:
skill read 1/3, resolver invoked 1/3, resolved context read 1/3. Guidance availability
therefore did not guarantee adherence. The validation conclusion is a useful partial
finding, not a completed task or a general framework advantage. The context answer
also presented resolver metadata as OpenAPI fields and suggested an imprecise
format regex. Both scenario answers were independently reviewed by the supervising
assistant against the predeclared criteria and pinned source; this was not human review.

Median attempt time: baseline 559.331 s, context-guided 357.709 s. These are durations
of incomplete work on a shared development laptop with uncontrolled background
load. They do not establish faster successful completion or financial savings.
The first improvement target is reliable context routing and evidence use; any
changed bootstrap, model or budget must be evaluated as a new campaign. The original
single-response generation results remain separate.

[Public evidence feed](https://raw.githubusercontent.com/balajiregt/agentic-workspace/benchmark-results/workflow-results.json)
· [Immutable campaign](https://raw.githubusercontent.com/balajiregt/agentic-workspace/benchmark-results/workflow-campaigns/d3928716d37016d0.json)

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

The API runner materializes two disposable, manifest-listed projections
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

## Enforced fixed work budget

Freeze these limits before collecting the first counted workflow run:

- 15 minutes total task wall time, including context discovery and execution.
- At most 36 model calls and 80 tool invocations, whichever stops first.
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

The Pi host enforces these controls before executing calls; the fixed command
adapter is the only test execution path. Unit tests cover counter exhaustion,
snapshot reuse, scope and traversal. Separate preflight checks exercised real
Gemma reads, edits and verification, the context resolver, filesystem/network
denials, and positive/negative grading controls before the counted campaign. If the framework's real
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

Primary: correct tasks / valid started tasks, split by operation and model. All started
attempts remain visible. Separately exclude infrastructure-invalid attempts from
quality and timing aggregates; never call them model failures. Retain properly
enforced timeouts, tool failures and exhausted budgets in the valid denominator. Separately show scheduled tasks
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

The deployed **QA workflow outcomes** view is separate from model generation
and runtime views. It reports: task success by create/update/validate;
completion within budget; repair recovery by cycle; context discovery/read cost;
scope/duplicate decisions; time/tokens with observed denominators. Drill-down:
task -> condition -> evidence read -> action -> verification -> final outcome.

Use a new `workflow-results.json` feed and `qa-context-workflow-v2` schema. Do not
shoehorn workflow evidence into `trials.json` or overwrite original Gemma results.
Public exports should contain reviewed task identifiers, structured outcomes,
counts, costs and hashes only. Raw code, paths, prompts, tool traces, labels and
human reviews remain private. The dashboard reads this feed every minute and retains the last known campaign
with a visible stale warning if a feed fails. A new result needs no site redeploy.

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


## Run and publish the API pilot

Requirements for this host: macOS `sandbox-exec`, Node 22, Python 3.12 + PyYAML,
Maven, Java 17, cached Maven dependencies, Pi coding agent 0.73.1 and the existing
local llama.cpp server at port 8080. The server must expose the expected Gemma
GGUF with 8192 context and one slot. This runner does not download a model,
reconfigure the server, load global Pi settings or call a cloud provider.
The host paths for these installed runtimes are explicit in the adapter; adjust
and re-freeze the protocol before using a different host.

```sh
npm test
npm run workflow:prepare -- --repo ../work/repos/api --output ../work/workflow-campaign
npm run workflow:run -- --repo ../work/repos/api --output ../work/workflow-campaign
```

Preparation refuses dirty/unpinned input and an existing output directory. It
hashes the model, runner, evaluator, configurations and initial projections.
The runner rechecks frozen inputs, alternates condition order and runs sequentially.
An interrupted started trial cannot silently resume as a fresh attempt. Finished,
graded trials are skipped on resume. A changed runner requires a new campaign.

`--publish` performs the closed public export after all six outcomes exist, then
commits `workflow-results.json` and an immutable `workflow-campaigns/<id>.json`
to the API repository's `benchmark-results` branch. It preserves runtime and
older generation feeds. Publication requires the existing authorized Git access;
no credentials belong in prompts or deployment assets. A failed publication is
reported and the local campaign remains available. Publish an already completed
campaign with `python3 workflows/publish.py --campaign <directory>`.

Both conditions expose the same seven bounded tools: directory listing, path
search, literal content search, paged file reads, exact edits, file writes and
controlled execution. The execution tool accepts only `verify`, `probe` and the
context condition's real `context:resolve`. It cannot execute model-supplied
shell text. Test/helper Java edits are scoped; validation tasks cannot edit source.
The original framework instructions and skill discovery bootstrap are installed
only in the context condition. The task YAML uses the neutral request verbatim,
never evaluator titles or classification labels.

The fixed test process inherits a macOS filesystem/network sandbox. Only the
trial workspace is writable; file-content reads are confined to it and installed
OS/Java/Maven/Python runtimes and dependency cache. Loader access to the literal
root directory does not permit reading its descendants. Synthetic denial checks
confirmed the sibling grading folder is unreadable/unwritable and the model
server port is inaccessible from tests. Java uses IPv4 and may reach only the
local API proxy on port 4383. This is a controlled engineering harness, not a
claim of a general adversarial security sandbox.

The sample application runs unchanged behind the proxy. During agent work it
returns healthy responses. After the submission freezes, the independent grader
injects one response fault at a time; an activated fault must produce an assertion
failure, not a compiler error, socket error or skipped test. Every verification
recompiles the test/support modules to prevent stale classes from passing a gate.
Full output stays private; bounded tool output explicitly identifies truncation.
There is no automatic context compaction or provider retry. Automated grading time
is recorded separately from the agent's task time; semantic review time is unmeasured. A small process-cleanup grace
period follows the deadline; no new agent work is allowed after the budget ends.

The preflight edit task hit its shorter infrastructure deadline after making an
edit; a separate verification-tool preflight executed that edited source and
passed. These checks are not performance samples. One initial campaign attempt
was interrupted when inspection found a validation summary that could reveal its
classification only to the context arm. Its evidence is retained as invalid protocol evidence. A second setup campaign
exposed a stock Pi discovery hint that requested `read` and absolute paths,
conflicting with this bounded host. Its two started attempts are retained as
setup-invalid. The final campaign uses neutral summaries, adapts only the
host-specific skill discovery boilerplate to `repo_read` and repository-relative
paths, and supplies identical execution-command mappings to both conditions.
Regression checks cover both issues. The framework skill file itself is unchanged.

See [the workflow diagram](../public/workflow-flow.svg) and its
[Mermaid source](../public/workflow-flow.mmd). Raw transcripts, source diffs,
per-verification snapshots, evaluator logs and review material stay in the private
campaign directory. Public hashes identify those artifacts; hashes are not an
independent audit or proof that an unreviewed conclusion is correct.

Provider finish reason `length` is recorded as `output-limit` and displayed as
“Truncated response.” It does not by itself distinguish the requested output cap
from a server context-capacity constraint. The raw provider response and usage
remain private evidence; no automatic continuation or replacement run is added.
The preflight server reported llama.cpp build `b10050-b15ca938a`. Pi compaction
is disabled; server-internal context handling is not separately instrumented.
This is a shared development machine, not a dedicated performance test host.

Token totals sum provider-reported usage across actual outbound requests; repeated
conversation history is charged again in those totals. A controller-only stop
message is excluded because it did not call the model. If any real request lacks
usage, the campaign row reports incomplete usage rather than inventing zero.
The repair counter denotes additional verified source snapshots after the first;
a recovered failure requires a recorded failed cycle followed by a passing cycle.
Successful write calls are actions, not proof of a useful source change.

## Timing validity and interruptions

Protocol revision 4 adds two wall-clock watchdogs: a 100 ms agent-host check and
an independent Python process monitor. It stops new work at a deadline, cancels
the provider request, and allows at most two seconds before forced shutdown when
cancellation does not settle. A temporary `caffeinate -i` assertion lasts only for
the campaign; it prevents idle sleep, not lid closure or forced sleep. A clock
jump/pause over ten seconds invalidates an attempt. No elapsed value is clamped.

The timing auditor requires clock telemetry, checks total and per-response elapsed
time with a five-second cleanup tolerance, and checks for work started after the
deadline. Cleanup tolerance is not extra model work. The public projection repeats
this audit from the raw artifacts; the browser refuses a valid label when wall time,
response time, pause telemetry or counters violate their limits. An invalid attempt
has no quality outcome. Its observed submission gates may still be inspected, but
it contributes to neither success/failure counts nor median attempt time.

Three earlier campaigns have nine started attempts retained outside this cohort:
one setup attempt with a context-summary defect; two setup attempts with a host
skill-discovery mismatch; and six runs with untrustworthy timing after interruption.
Five of the latter exceeded a response or total deadline; one lasted overnight.
The exact host/provider cause was not established. The entire paired campaign was
excluded, including its one apparently on-time baseline. This is disclosed attrition,
not replacement samples silently added to the same protocol. Revision 4 changes
runner controls only; tasks, model, context contents and nominal budgets are unchanged.
A separate one-second response-deadline preflight stopped at 1.244 seconds.

If the host is interrupted again, inspect retained artifacts and the validity audit.
Do not restart an incomplete trial under its old identity or publish a time overrun
as evidence that either context condition is slower. Frozen runner copies and plan
hashes preserve the executed implementation; any runner changes require a new campaign.

The retained field name `modelResponses` counts reserved model-call attempts,
including failed or cancelled calls; it does not imply 36 completed responses.

Semantic review records identify the supervising assistant separately from trial
Gemma, preserve the original automated grade, and hash a private `review.json`.
Each predeclared criterion is assessed against the frozen submission and actual
contract/controller/service evidence. Public rows expose `reviewMethod` and the
review fingerprint; this is an assistant assessment, not a human certification.
`gradingMs` covers automated gates only. Neither semantic review time nor human
correction time is inferred from it. A scope-only pass stays pending until reviewed.
