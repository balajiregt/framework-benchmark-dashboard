# Framework impact pilot · 12–13 October 2026 (IST)

Campaign `db8af4c03b14d269` started all twelve planned attempts. **Two attempts have
valid timing; ten are infrastructure-invalid.** Only the API normalization task
has a usable pair. There is no valid Playwright performance comparison, and no
general framework benefit or harm can be inferred from this campaign.

## Context audit

| Framework | Verified components | Gaps | Unmeasured |
| --- | --- | --- | --- |
| API | 9 | 0 | Capture/context freshness |
| Playwright | 4 | 2 authentication mismatches | Capture freshness |

The two Playwright gaps are its localStorage-only authentication manifest and
capture recipe, while the live API requires the real-login HttpOnly cookie.
Graph ownership and the existing manager direct-route checks were verified.
These component counts are not interchangeable accuracy scores.

## The one timing-valid pair

Request: create the missing lowercase/whitespace customer-ID normalization
scenario in the existing Java API project.

| Observed result | Baseline | Framework available |
| --- | --- | --- |
| Requested work delivered | No | No |
| Stop reason | Output limit | Output limit |
| Full attempt time | 690.240 seconds | 692.956 seconds |
| Model calls | 15 | 13 |
| Tool calls / tool errors | 14 / 2 | 12 / 0 |
| Applied source edits | 0 | 0 |
| Provider-reported input tokens | 38,942 | 57,089 |
| Provider-reported output tokens | 4,005 | 2,369 |
| First direct read of a listed source file | 198.847 seconds | 570.079 seconds |
| Framework context files read | 0 | 2 |
| Resolver invoked | No | No |

The baseline attempted two exact-text edits containing the read tool's displayed
line numbers. Neither matched the file. It also proposed a normalized identifier
with an incorrect trailing space. The assisted attempt read the task context and
the first 80 lines of the workflow skill, then explored files without invoking
the resolver. Neither supplied a final evidence-backed decision report.

Both found the owning test but failed the complete owner-plus-support criterion:
neither inspected the relevant service/contract/helper evidence. The strict
action and grounding criteria were also unmet. Missing evidence is not the same
as an explicitly wrong answer. Both preserved the original five passing tests,
but passing that unchanged suite did not deliver the requested scenario.

These incomplete attempts are not evidence of a time saving. Their token counts
describe the recorded requests, not general context efficiency. External
inference fee was $0; total operating cost and human correction time are unmeasured.

## Infrastructure exclusions

Both API update attempts, both API validation attempts and all six Playwright
attempts recorded host interruptions. Watchdog gaps were approximately 900
seconds. Those long wall durations are displayed for diagnosis but excluded from
quality and efficiency totals. They are not counted as model failures.

The first interruption also caused a process-cleanup PermissionError before the
outer host-clock receipt was written. Its agent watchdog and result survived;
the missing independent receipt is retained as a validity failure. No receipt
was fabricated and no started attempt was replaced. The original runner resumed
unstarted tasks and continued after subsequent interruptions; that behavior
consumed the remainder of this campaign on an unstable host.

A valid comparison of update/validation work and Playwright impact still requires
a fresh campaign on a continuously available host. It must keep this campaign
in history and stop further launches after an infrastructure interruption.

[Live dashboard](https://framework-benchmarks-balaji.netlify.app/#framework-impact)
· [Public structured evidence](https://raw.githubusercontent.com/balajiregt/agentic-workspace/benchmark-results/framework-impact.json)
· [Content-addressed campaign archive](https://github.com/balajiregt/agentic-workspace/tree/benchmark-results/impact-campaigns/db8af4c03b14d269)

The supervising assistant reviewed the two timing-valid submissions against the
frozen rubric. This was separate from trial Gemma, but was neither blind nor human
review. Private traces and review notes are represented publicly by hashes.
