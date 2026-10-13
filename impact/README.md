# Framework impact

The question is: **does this framework help the same agent make better decisions
and deliver the requested engineering work?** Generated tests are one possible
deliverable. They are not the subject of a new test-quality leaderboard.

The unit of comparison is a paired work request: same repository revision,
application, helpers, model, tools and budget; framework guidance is available in
one condition. A useful read-only conclusion can be a complete deliverable.

[Read the actual pilot results and infrastructure exclusions](RESULTS.md).

## Four evidence layers

1. **Context validity.** Run the real resolver/graph generators and compare their
   claims with application source and an independent live session probe. Record
   correct components, incorrect claims and unknown freshness separately.
2. **Agent decisions.** Did it find the owning files, select the right action
   (create/update/already-covered/unsupported), and justify that action with actual
   inspected evidence? Tool invocation alone earns no credit.
3. **Delivered work.** Freeze the submission, independently run the resulting
   work against the sample application, inspect its semantics and preservation of
   existing behavior. Complete means all required decisions and task criteria
   are met. A green unchanged suite is insufficient for a requested code change.
4. **Resources.** Record full attempt time, model calls, tools, edits, verification
   snapshots and provider-reported tokens. Show completed-task time separately.
   A fast failed attempt is not a productivity gain. Local inference has no
   external API fee; electricity, hardware and human correction time are unknown.

The task acceptance checks do not calculate mutation score, assertion count or
coverage percentage. Execution and source review establish whether the requested
work was delivered. Earlier mutation/generation evidence stays in its own view.

## Audited context and corrections

The API audit verifies nine components, including exact ownership paths, contract
constraints, normalization and the Maven command/port. Capture freshness is
unmeasured. The Playwright audit verifies four components and identifies two
authentication gaps: its manifest and capture recipe describe localStorage auth,
while authenticated API requests require the cookie established by real login.
These gaps remain in the framework condition; they are not silently corrected.

The manager flow already visits restricted Leads and Admin URLs and asserts the
denied path. An earlier inspection incorrectly said this was missing. The new
validation request expects the correct already-covered decision.

Reference execution found a login race in the shared CRM page helper. The helper
now waits for the dashboard after sign-in (Playwright commit `546c089`), in both
conditions. All five original flows passed. Independent reference implementations
confirmed all four coding tasks were feasible. One reference run timed out in an
existing admin test, while its new target scenario passed. Before freezing the
campaign, the runner used standard 30-second test / 5-second assertion timeouts
and scoped host wake prevention; both UI reference runs then passed. Those runs
are preflight evidence, not agent performance samples.

## Six requests, twelve attempts

| Framework | Create | Update | Validate |
| --- | --- | --- | --- |
| API | Add identifier normalization scenario | Add score/reason to existing high-risk test | Explain why a proposed format rejection is unsupported |
| Playwright | Add viewer direct Leads/Reports denial coverage | Add authenticated export denial to existing viewer flow | Establish whether manager direct-route coverage already exists |

The baseline receives source, tests/helpers, the request and execution setup.
The framework condition also receives the repository's actual AGENTS guidance
and API skill/resolver or Playwright contexts/source/coverage graph scripts.
There is no hand-selected answer bundle. Raw rubric criteria are not supplied to
the trial agent. Both conditions use the same confined read/edit/write/search
tools and fixed execution commands. Playwright can observe the live UI using
the same real-login browser adapter in either condition. This campaign measures
context-guided work with that adapter; it does not claim to exercise every MCP or
capture-recipe integration.

Local Gemma runs through Pi 0.73.1 with an 8,192-token context, 4,096 output-token
limit, temperature 0.2 and seed 1. Each attempt gets 15 minutes, 36 model calls,
80 tool calls and three distinct verification snapshots. Provider retries,
automatic compaction and test-runner retries are disabled. Arm order alternates
by task. A successful unrelated read/edit/read preflight verifies tool wiring.

The runner stores every start and refuses to silently replace an interrupted
attempt. After the first campaign exposed repeated host pauses, the launcher was
changed to halt remaining launches after any infrastructure-invalid result. A
halted campaign requires a new preparation after host recovery. The independent
clock receipt is now written even if process cleanup raises an error. The first
campaign used the runner committed at `10b4341`; later plans freeze this revised
launcher and the shared campaign utilities as well. Agent tools and budgets are
unchanged. A 100-ms watchdog and separate host-clock audit identify infrastructure
interruptions. Invalid attempts stay visible and are excluded from performance
totals. Completion differences use only matched pairs whose two timings are valid;
an unmatched valid attempt remains visible in its arm but cannot inflate that
paired difference. Frozen source/configuration/runner hashes are checked before execution.
Private projections, prompts, traces, model output and review notes are not
published. The public feed contains structured outcomes and evidence hashes.

## Review and limitations

Decision and semantic review is performed by the supervising assistant, separate
from trial Gemma. The reviewer authored this protocol and knows the conditions:
this is neither blind review nor a human judgment. Review records bind to both
the submission and rubric hashes. Unknown or pending review is never converted
into success. Independent grading time is outside the agent attempt clock.

One pair per task cannot establish a general effect, model ranking or statistically
reliable speedup. These are synthetic sample apps, and API tasks were used in an
earlier pilot. The shared M1 laptop and small local model limit generalization.
No new JEV or Mockserver outcome claim is made by this campaign.

## Reproduce and publish

Use clean clones at the revisions in `tasks.json`, dependencies already installed,
the existing local model server on port 8080, Java/Maven and Playwright Chromium.
The macOS sandbox restricts executed work to its projection and local app ports.
API Maven verification uses JDK 17; the service launcher inherits the installed
host Java. Model/runtime details are recorded in the frozen plan.

```sh
python3 impact/audit.py --api <api-repo> --harness <harness-repo> --output <audit-dir>
python3 impact/reference.py --api <api-repo> --harness <harness-repo> --output <new-reference-dir>
npm run impact:prepare -- --api <api-repo> --harness <harness-repo> \
  --audit <audit-dir>/audit.json --output <new-private-campaign-dir>
npm run impact:run -- --api <api-repo> --harness <harness-repo> \
  --output <prepared-private-campaign-dir>
```

`impact:run` publishes a structured campaign after execution; unreviewed decisions
stay pending. For a private run omit publication with `python3 impact/run.py run`
and the same arguments. After independent review, export and publish the exact
reviewed payload without rerunning the model:

```sh
python3 impact/export.py --campaign <private-campaign-dir> --output <public-summary.json>
npm run impact:publish -- --payload <public-summary.json>
```

The existing `agentic-workspace` benchmark-results branch hosts
`framework-impact.json` plus content-addressed campaign archives. Publication
preserves the other feeds, refuses rollback and does not force-push. An ambiguous
failure requires inspection before retry. Publishing the identical saved payload
is idempotent. The deployed dashboard reads the feed every minute while visible;
future result updates need no dashboard deployment. Dashboard code changes do.

The implementation borrows the separation of task success, execution traces and
resource accounting used in [SkillsBench](https://github.com/benchflow-ai/skillsbench),
[AWS context engineering](https://github.com/aws-samples/sample-context-engineering)
and [OpenHands evaluation](https://github.com/All-Hands-AI/OpenHands).
Those are methodological references, not external validation of this pilot.
