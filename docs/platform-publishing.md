# Reusable platform publishing — version 1.0.0

The platform now has a project/analysis registry and a portable publishing skill.
It retains the current benchmark page and its schema-specific result formats.
The visual redesign and routed page rendering are separate work: the registry
reserves routes but does not claim those pages exist yet.

## Ownership and flow

1. A project's tests/analysis produce results and retain private evidence.
2. Its adapter maps results to a closed numeric measurement input.
3. The publisher binds measurements to a reviewed public policy and prepares
   a local preview without networking.
4. Authorised publication writes to that public repository's
   `platform-results/metrics.json`, using its existing scoped Git access.
5. The registry declares descriptions, routes, related analyses and public feeds.
   The standard reader consumes `metrics-v1`; existing renderers retain their
   legacy validators. Routine publication works from a terminal or CI, without AI.

The publisher sends no source code, arbitrary report text or unknown keys.
Labels, methodology and limitations come from a deliberately reviewed policy.
Text checks are tripwires, not proof that arbitrary customer data is safe.
Content hashes and schema validation do not independently validate measurements.
Producer correctness and source freshness belong to the project's tested adapter.

## Reuse and maintenance

Use `$platform-publish` from `.agents/skills/platform-publish`. The complete
folder includes runnable scripts, examples, schema and integration instructions.
It has no npm dependencies. Its manifest records version and file hashes; pin a
reviewed archive digest or source commit when distributing it.

```sh
node .agents/skills/platform-publish/scripts/cli.mjs --help
npm run platform:check
```

The browser validator is a byte-identical copy of the canonical skill contract.
After changing the canonical contract or skill resources:

```sh
npm run platform:sync
npm run platform:bundle
npm run platform:check
npm test
npm run build
```

The build includes `/contracts/metrics-v1.schema.json`; that URL becomes live
only after a reviewed deployment. Use the bundled validator for semantic rules
and policy matching as well as the interchange JSON Schema.

## Registry and compatibility

`public/data/platform-registry.json` contains four projects and four analyses.
It centralises the runtime, generation, workflow, framework-impact, decision,
team and paired-comparison feed URLs. Analysis entries can reference several
projects. The application derives its runtime IDs, feed origins, links and
validation counts from the registered legacy sources.

No producer, legacy result branch, benchmark protocol or recorded metric was
rewritten. The new standard uses a separate branch and cannot overwrite the old
`latest.json`. New standard projects require a registry entry and a feed; they
do not become records in the legacy fixed benchmark snapshot. New result types
still require a supported renderer.

The standard reader returns `connected`, `stale`, `unavailable` or
`not-configured`. Failed, invalid and rolled-back refreshes preserve the caller's
accepted evidence with explicit stale state. Null is distinct from zero;
estimated and measured results stay separate. Publication retains up to 50 runs,
deduplicates repeated sends and orders results by observation time.

## Verification and rollout

Tests use local temporary bare Git repositories for duplicate and concurrent
publication, unrelated-file preservation and symlink-feed rejection. They also
cover new-project registration without renderer edits, existing source mappings,
policy changes, invalid measurements, unavailable data, tampering, bounded
history and stale refreshes. No public writes or paid model runs are needed.

Review and deploy the registry/reader code, then deliberately register each new
public producer and review its initial payload. Later approved CI publication
uses the same command. Failed publication retains its prepared export; retrying
does not rerun the experiment or invent a new observation timestamp.

No schedules, automatic benchmark triggers, application deployments, database
or MCP server are introduced by this integration.
